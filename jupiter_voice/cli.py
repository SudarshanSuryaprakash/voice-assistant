"""Main CLI entry point and orchestrator for Jupiter Voice."""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.panel import Panel

from jupiter_voice import __version__
from jupiter_voice.audio.capture import AudioCapture
from jupiter_voice.audio.cues import AudioCues
from jupiter_voice.audio.playback import AudioPlayback
from jupiter_voice.config import JupiterConfig, load_config
from jupiter_voice.gateway.openclaw import OpenClawError, OpenClawGateway
from jupiter_voice.state_machine import Event, State, StateMachine
from jupiter_voice.stt.close_phrase import ClosePhraseDetector
from jupiter_voice.stt.whisper_mlx import WhisperMLXEngine
from jupiter_voice.tts.kokoro_tts import KokoroTTSEngine
from jupiter_voice.tts.macos_fallback import MacOSFallbackTTS
from jupiter_voice.utils.health import HealthChecker
from jupiter_voice.wake.detector import WakeWordDetector

logger = logging.getLogger("jupiter_voice")

# Ensure espeak-ng can be found on macOS with Homebrew
if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
    if homebrew_lib not in dyld:
        os.environ["DYLD_LIBRARY_PATH"] = f"{homebrew_lib}:{dyld}" if dyld else homebrew_lib


class JupiterVoice:
    """Main application orchestrator — ties all components together via the state machine."""

    def __init__(self, config: JupiterConfig, base_dir: Path) -> None:
        self.config = config
        self.base_dir = base_dir
        self.console = Console()
        self.sm = StateMachine()
        self._shutdown = threading.Event()

        # Components (initialized in startup)
        self.capture = AudioCapture(
            sample_rate=config.audio.sample_rate,
            channels=config.audio.channels,
            chunk_size=config.audio.chunk_size,
            device=config.audio.device,
        )
        self.playback = AudioPlayback()
        self.cues = AudioCues(config.cues, self.playback, base_dir)
        self.wake_detector = WakeWordDetector(
            model=config.wake.model,
            threshold=config.wake.threshold,
            inference_framework=config.wake.inference_framework,
        )
        self.stt = WhisperMLXEngine(
            model=config.stt.model,
            batch_size=config.stt.batch_size,
        )
        self.close_detector = ClosePhraseDetector(
            primary=config.close_phrase.primary,
            alternatives=config.close_phrase.alternatives,
        )
        self.tts = KokoroTTSEngine(
            voice=config.tts.voice,
            speed=config.tts.speed,
            lang=config.tts.lang,
            model_dir=str(base_dir / "models"),
        )
        self.gateway = OpenClawGateway(
            session_id=config.gateway.session_id,
            timeout=config.gateway.timeout,
            openclaw_bin=config.gateway.openclaw_bin,
        )

        # Runtime state
        self._transcript_parts: list[str] = []
        self._current_query: str = ""
        self._current_response: str = ""

    def startup(self) -> None:
        """Initialize all components with progress feedback."""
        self._print_banner()

        # Health checks
        checker = HealthChecker(self.config, self.base_dir)
        if not checker.run_all():
            self.console.print("[yellow]Some checks failed — continuing anyway...[/yellow]")
        self.console.print()

        # Load models
        with self.console.status("[bold green]Loading wake word model..."):
            self.wake_detector.load()
        self.console.print("[green]  Wake word model loaded[/green]")

        with self.console.status("[bold green]Loading speech-to-text model..."):
            self.stt.load()
        self.console.print("[green]  STT model loaded[/green]")

        with self.console.status("[bold green]Loading text-to-speech model..."):
            self.tts.load()
        self.console.print("[green]  TTS model loaded[/green]")

        # Start audio capture
        self.capture.start()
        self.console.print()

        wake_name = self.config.wake.model.replace("_", " ")
        self.console.print(
            f'[bold green]Ready.[/bold green] Say [bold cyan]"{wake_name}"[/bold cyan] to begin.\n'
        )

    def run(self) -> None:
        """Main event loop. Blocks until shutdown."""
        self.startup()

        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            while not self._shutdown.is_set():
                state = self.sm.state
                if state == State.IDLE:
                    self._idle_tick()
                elif state == State.LISTENING:
                    self._listening_tick()
                elif state == State.PROCESSING:
                    self._processing_tick()
                elif state == State.SPEAKING:
                    self._speaking_tick()
        except Exception:
            logger.exception("Unhandled error in main loop")
        finally:
            self.shutdown()

    # ── State handlers ──────────────────────────────────────────

    def _idle_tick(self) -> None:
        """Process one chunk looking for wake word."""
        chunk = self.capture.read_chunk()
        if chunk is None:
            time.sleep(0.01)
            return

        if self.wake_detector.process_chunk(chunk):
            self.console.print("[bold cyan]Wake word detected![/bold cyan]")
            self.cues.play_wake()
            time.sleep(0.15)  # Let the cue play briefly
            self._transcript_parts.clear()
            self.capture.drain()  # Discard buffered audio from before wake
            self.sm.transition(Event.WAKE_WORD_DETECTED)
            close = self.config.close_phrase.primary
            self.console.print(f'[dim]Listening... say "{close}" when done.[/dim]')

    def _listening_tick(self) -> None:
        """Record and transcribe a chunk, checking for close phrase."""
        # Accumulate audio for one transcription chunk
        audio = self.capture.read_seconds(self.config.stt.chunk_duration)

        # Convert to float32 for Whisper
        audio_float = audio.astype(np.float32) / 32768.0

        # Skip silent/near-silent chunks (energy gate)
        rms = np.sqrt(np.mean(audio_float ** 2))
        if rms < 0.008:  # Silence threshold — tune if needed
            return

        # Transcribe
        text = self.stt.transcribe(audio_float)
        if text:
            self._transcript_parts.append(text)
            self.console.print(f"[dim]  > {text}[/dim]")

        # Check for close phrase in accumulated transcript
        full_text = " ".join(self._transcript_parts)
        detected, clean_text = self.close_detector.detect_and_strip(full_text)

        if detected:
            if not clean_text.strip():
                self.console.print("[yellow]No query detected. Returning to idle.[/yellow]")
                self.sm.transition(Event.CANCEL)
                return

            self.console.print(f"\n[bold yellow]Sending:[/bold yellow] {clean_text}\n")
            self.cues.play_send()
            self._current_query = clean_text
            self.sm.transition(Event.CLOSE_PHRASE_DETECTED)

    def _processing_tick(self) -> None:
        """Send query to OpenClaw and get response."""
        with self.console.status("[bold green]Jupiter is thinking..."):
            try:
                response = self.gateway.send_message(self._current_query)
                if not response:
                    response = "I received your message but got an empty response."
                self.console.print(f"\n[bold green]Jupiter:[/bold green] {response}\n")
                self._current_response = response
                self.sm.transition(Event.RESPONSE_RECEIVED)
            except OpenClawError as e:
                self.console.print(f"[red]Error: {e}[/red]")
                self.cues.play_error()
                self._speak_error(str(e))
                self.sm.transition(Event.ERROR)

    def _speaking_tick(self) -> None:
        """Speak the response via TTS."""
        try:
            samples, sr = self.tts.synthesize(self._current_response)
            # Pause wake detection by draining audio during playback
            self.playback.play(samples, sr, blocking=True)
        except Exception as e:
            logger.error("TTS synthesis failed: %s", e)
            if self.config.tts.fallback_to_macos_say:
                self.console.print("[dim]Using macOS fallback voice...[/dim]")
                MacOSFallbackTTS.speak(self._current_response)

        # Clear any audio that was captured during playback (avoids self-trigger)
        self.capture.drain()
        self.wake_detector.reset()
        time.sleep(0.3)  # Brief pause before listening again
        self.capture.drain()

        self.sm.transition(Event.PLAYBACK_COMPLETE)
        self.console.print(
            f'[dim]Say "{self.config.wake.model.replace("_", " ")}" to ask again.[/dim]\n'
        )

    # ── Helpers ─────────────────────────────────────────────────

    def _speak_error(self, message: str) -> None:
        """Speak an error message via TTS."""
        error_text = f"Sorry, there was an error. {message}"
        try:
            samples, sr = self.tts.synthesize(error_text)
            self.playback.play(samples, sr, blocking=True)
        except Exception:
            if self.config.tts.fallback_to_macos_say:
                MacOSFallbackTTS.speak("Sorry, there was an error communicating with Jupiter.")

    def _print_banner(self) -> None:
        wake_name = self.config.wake.model.replace("_", " ")
        banner = Panel(
            f"[bold cyan]Jupiter Voice[/bold cyan] v{__version__}\n"
            "[dim]Local voice assistant powered by OpenClaw[/dim]\n\n"
            f'Say [bold]"{wake_name}"[/bold] to start listening\n'
            f'Say [bold]"{self.config.close_phrase.primary}"[/bold] to send your query',
            title="[bold]Jupiter Voice[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )
        self.console.print(banner)
        self.console.print()

    def _signal_handler(self, sig: int, frame: object) -> None:
        self.console.print("\n[yellow]Shutting down...[/yellow]")
        self._shutdown.set()

    def shutdown(self) -> None:
        """Clean up all resources."""
        self.capture.stop()
        self.playback.stop()
        self.console.print("[dim]Goodbye.[/dim]")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Jupiter Voice — local voice assistant powered by OpenClaw",
        prog="jupiter-voice",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    # Resolve base directory (where config.yaml lives)
    config_path = Path(args.config)
    if config_path.is_absolute():
        base_dir = config_path.parent
    else:
        base_dir = Path.cwd()

    # Set up logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Load config
    config = load_config(str(config_path))

    if args.verbose:
        config.logging.level = "DEBUG"

    # Run
    app = JupiterVoice(config, base_dir)
    app.run()


if __name__ == "__main__":
    main()
