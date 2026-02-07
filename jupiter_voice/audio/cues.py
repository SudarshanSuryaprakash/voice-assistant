"""Audio cue management — load and play short sound effects."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import soundfile as sf

from jupiter_voice.audio.playback import AudioPlayback
from jupiter_voice.config import CuesConfig

logger = logging.getLogger(__name__)


class AudioCues:
    """Manages and plays audio cue sounds (ding, send, error)."""

    def __init__(self, config: CuesConfig, playback: AudioPlayback, base_dir: Path) -> None:
        self.enabled = config.enabled
        self.playback = playback
        self._cache: dict[str, tuple[np.ndarray, int]] = {}

        if self.enabled:
            self._load("wake", base_dir / config.wake_detected)
            self._load("send", base_dir / config.sending)
            self._load("error", base_dir / config.error)

    def _load(self, name: str, path: Path) -> None:
        """Pre-load a WAV file into memory."""
        if path.exists():
            try:
                data, sr = sf.read(str(path), dtype="float32")
                self._cache[name] = (data, sr)
                logger.debug("Loaded cue '%s' from %s", name, path)
            except Exception as e:
                logger.warning("Failed to load cue '%s' from %s: %s", name, path, e)
        else:
            logger.debug("Cue file not found: %s (will be silent)", path)

    def play_wake(self) -> None:
        """Play the wake word detection sound."""
        self._play("wake")

    def play_send(self) -> None:
        """Play the 'sending query' sound."""
        self._play("send")

    def play_error(self) -> None:
        """Play the error notification sound."""
        self._play("error")

    def _play(self, name: str) -> None:
        if not self.enabled or name not in self._cache:
            return
        audio, sr = self._cache[name]
        self.playback.play_async(audio, sr)
