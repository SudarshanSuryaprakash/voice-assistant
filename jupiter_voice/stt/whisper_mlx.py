"""Speech-to-text engine using Lightning Whisper MLX."""

from __future__ import annotations

import logging
import tempfile
from typing import Optional

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class WhisperMLXEngine:
    """Transcribes audio to text using Lightning Whisper MLX (optimized for Apple Silicon)."""

    def __init__(
        self,
        model: str = "distil-medium.en",
        batch_size: int = 12,
    ) -> None:
        self.model_name = model
        self.batch_size = batch_size
        self._whisper = None
        self._accepts_numpy: Optional[bool] = None

    def load(self) -> None:
        """Load the Whisper model. Downloads on first use."""
        from lightning_whisper_mlx import LightningWhisperMLX

        logger.info("Loading Whisper model: %s (batch_size=%d)", self.model_name, self.batch_size)
        self._whisper = LightningWhisperMLX(
            model=self.model_name,
            batch_size=self.batch_size,
        )
        logger.info("Whisper model loaded")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribe audio to text.

        Args:
            audio: Numpy array of audio samples (int16 or float32, mono).
            sample_rate: Sample rate of the audio (default 16000).

        Returns:
            Transcribed text string.
        """
        if self._whisper is None:
            raise RuntimeError("Whisper model not loaded. Call load() first.")

        # Convert int16 to float32 normalized
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0

        # Try numpy array directly first, then fall back to temp file
        if self._accepts_numpy is not False:
            try:
                result = self._whisper.transcribe(audio)
                self._accepts_numpy = True
                return result.get("text", "").strip()
            except (TypeError, AttributeError):
                if self._accepts_numpy is None:
                    logger.debug("Whisper wrapper doesn't accept numpy arrays, using temp file")
                    self._accepts_numpy = False
                else:
                    raise

        # Fallback: write to temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
            sf.write(f.name, audio, sample_rate)
            result = self._whisper.transcribe(f.name)
            return result.get("text", "").strip()

    @property
    def is_loaded(self) -> bool:
        return self._whisper is not None
