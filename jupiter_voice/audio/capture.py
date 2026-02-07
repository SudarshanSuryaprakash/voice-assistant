"""Microphone audio capture via sounddevice."""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Optional

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioCapture:
    """Captures audio from the microphone using a sounddevice callback stream."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1280,
        device: Optional[int] = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device = device
        self._buffer: deque[np.ndarray] = deque(maxlen=10000)
        self._stream: Optional[sd.InputStream] = None
        self._running = False

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info: object, status: sd.CallbackFlags
    ) -> None:
        """Called by sounddevice for each audio chunk."""
        if status:
            logger.warning("Audio callback status: %s", status)
        self._buffer.append(indata[:, 0].copy())

    def start(self) -> None:
        """Start the audio capture stream."""
        if self._running:
            return
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=self.chunk_size,
            device=self.device,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._running = True
        logger.info(
            "Audio capture started: %dHz, %dch, chunk=%d",
            self.sample_rate, self.channels, self.chunk_size,
        )

    def stop(self) -> None:
        """Stop the audio capture stream."""
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._running = False
        logger.info("Audio capture stopped")

    def read_chunk(self) -> Optional[np.ndarray]:
        """Read a single chunk from the buffer. Returns None if empty."""
        try:
            return self._buffer.popleft()
        except IndexError:
            return None

    def read_seconds(self, duration: float) -> np.ndarray:
        """Accumulate audio for `duration` seconds. Blocks until enough data is available."""
        samples_needed = int(duration * self.sample_rate)
        accumulated: list[np.ndarray] = []
        total = 0
        while total < samples_needed:
            chunk = self.read_chunk()
            if chunk is not None:
                accumulated.append(chunk)
                total += len(chunk)
            else:
                time.sleep(0.01)
        audio = np.concatenate(accumulated)
        return audio[:samples_needed]

    def drain(self) -> None:
        """Discard all buffered audio."""
        self._buffer.clear()

    @property
    def is_running(self) -> bool:
        return self._running

    @staticmethod
    def check_microphone() -> tuple[bool, str]:
        """Check if a microphone is available. Returns (ok, detail)."""
        try:
            default_input = sd.query_devices(kind="input")
            if isinstance(default_input, dict):
                name = default_input.get("name", "Unknown")
            else:
                name = "Unknown"
            return True, f"Default input: {name}"
        except Exception as e:
            return False, str(e)
