"""Startup health checks for Jupiter Voice."""

from __future__ import annotations

import logging
from pathlib import Path

from rich.console import Console
from rich.table import Table

from jupiter_voice.config import JupiterConfig

logger = logging.getLogger(__name__)


class HealthChecker:
    """Runs startup health checks on all system components."""

    def __init__(self, config: JupiterConfig, base_dir: Path) -> None:
        self.config = config
        self.base_dir = base_dir
        self.console = Console()

    def run_all(self) -> bool:
        """Run all health checks. Returns True if all critical checks pass."""
        checks = [
            ("Microphone", self._check_mic),
            ("OpenClaw Gateway", self._check_gateway),
            ("Wake Word Model", self._check_wake_model),
            ("STT Model", self._check_stt),
            ("TTS Models", self._check_tts),
            ("Audio Cues", self._check_cues),
        ]

        table = Table(title="System Health Check", show_lines=False, padding=(0, 1))
        table.add_column("Component", style="cyan", min_width=18)
        table.add_column("Status", justify="center", min_width=6)
        table.add_column("Details", min_width=30)

        all_ok = True
        for name, check_fn in checks:
            try:
                ok, detail = check_fn()
                status = "[green]OK[/green]" if ok else "[yellow]WARN[/yellow]"
                if not ok:
                    all_ok = False
            except Exception as e:
                status = "[red]FAIL[/red]"
                detail = str(e)
                all_ok = False
            table.add_row(name, status, detail)

        self.console.print(table)
        return all_ok

    def _check_mic(self) -> tuple[bool, str]:
        from jupiter_voice.audio.capture import AudioCapture

        return AudioCapture.check_microphone()

    def _check_gateway(self) -> tuple[bool, str]:
        from jupiter_voice.gateway.openclaw import OpenClawGateway

        gw = OpenClawGateway(
            session_id=self.config.gateway.session_id,
            timeout=self.config.gateway.timeout,
            openclaw_bin=self.config.gateway.openclaw_bin,
        )
        return gw.health_check()

    def _check_wake_model(self) -> tuple[bool, str]:
        model = self.config.wake.model
        # Built-in models are always available
        if not ("/" in model or model.endswith((".onnx", ".tflite"))):
            return True, f"Built-in model: {model}"
        # Custom model — check file exists
        model_path = self.base_dir / model
        if model_path.exists():
            return True, f"Custom model: {model_path.name}"
        return False, f"Model file not found: {model_path}"

    def _check_stt(self) -> tuple[bool, str]:
        return True, f"Model: {self.config.stt.model} (loads on demand)"

    def _check_tts(self) -> tuple[bool, str]:
        model_dir = self.base_dir / "models"
        model_exists = (model_dir / "kokoro-v1.0.onnx").exists()
        voices_exists = (model_dir / "voices-v1.0.bin").exists()
        if model_exists and voices_exists:
            return True, f"Voice: {self.config.tts.voice}"
        missing = []
        if not model_exists:
            missing.append("kokoro-v1.0.onnx")
        if not voices_exists:
            missing.append("voices-v1.0.bin")
        return False, f"Missing: {', '.join(missing)} (will auto-download)"

    def _check_cues(self) -> tuple[bool, str]:
        if not self.config.cues.enabled:
            return True, "Disabled"
        cue_files = [
            self.config.cues.wake_detected,
            self.config.cues.sending,
            self.config.cues.error,
        ]
        missing = [f for f in cue_files if not (self.base_dir / f).exists()]
        if not missing:
            return True, "All cue files present"
        return False, f"Missing: {', '.join(missing)} (run scripts/generate_cues.py)"
