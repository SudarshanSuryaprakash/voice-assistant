"""Audio playback via sounddevice."""

from __future__ import annotations

import logging
import threading
from typing import Optional

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioPlayback:
    """Play audio through speakers via sounddevice."""

    def __init__(self, device: Optional[int] = None):
        self.device = device
        self._playing = False
        self._done_event = threading.Event()
        self._done_event.set()

    def play(self, audio: np.ndarray, sample_rate: int, blocking: bool = True) -> None:
        """Play a numpy audio array through speakers."""
        self._playing = True
        self._done_event.clear()
        try:
            sd.play(audio, samplerate=sample_rate, device=self.device)
            if blocking:
                sd.wait()
        finally:
            if blocking:
                self._playing = False
                self._done_event.set()

    def play_async(self, audio: np.ndarray, sample_rate: int) -> None:
        """Play audio without blocking. Use wait() or is_playing to check completion."""

        def _run():
            try:
                sd.play(audio, samplerate=sample_rate, device=self.device)
                sd.wait()
            finally:
                self._playing = False
                self._done_event.set()

        self._playing = True
        self._done_event.clear()
        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def stop(self) -> None:
        """Stop current playback immediately."""
        sd.stop()
        self._playing = False
        self._done_event.set()

    @property
    def is_playing(self) -> bool:
        return self._playing

    def wait(self, timeout: Optional[float] = None) -> bool:
        """Block until playback completes. Returns True if completed, False on timeout."""
        return self._done_event.wait(timeout=timeout)
