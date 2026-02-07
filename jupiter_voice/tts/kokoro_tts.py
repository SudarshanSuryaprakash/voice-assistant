"""Text-to-speech engine using Kokoro ONNX."""

from __future__ import annotations

import logging
import urllib.request
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

MODEL_FILE = "kokoro-v1.0.onnx"
VOICES_FILE = "voices-v1.0.bin"
DOWNLOAD_BASE_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
)


class KokoroTTSEngine:
    """Synthesizes speech from text using Kokoro ONNX (local, free)."""

    def __init__(
        self,
        voice: str = "af_heart",
        speed: float = 1.0,
        lang: str = "en-us",
        model_dir: str = "models",
    ) -> None:
        self.voice = voice
        self.speed = speed
        self.lang = lang
        self.model_dir = Path(model_dir)
        self._kokoro = None

    def load(self) -> None:
        """Load the Kokoro TTS model. Downloads model files if missing."""
        model_path = self.model_dir / MODEL_FILE
        voices_path = self.model_dir / VOICES_FILE

        if not model_path.exists() or not voices_path.exists():
            self._download_models()

        from kokoro_onnx import Kokoro

        logger.info("Loading Kokoro TTS: voice=%s, speed=%.1f", self.voice, self.speed)
        self._kokoro = Kokoro(str(model_path), str(voices_path))
        logger.info("Kokoro TTS loaded")

    def _download_models(self) -> None:
        """Download Kokoro model files from GitHub."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        for filename in [MODEL_FILE, VOICES_FILE]:
            dest = self.model_dir / filename
            if not dest.exists():
                url = f"{DOWNLOAD_BASE_URL}/{filename}"
                logger.info("Downloading %s...", filename)
                urllib.request.urlretrieve(url, str(dest))
                logger.info("Downloaded %s", filename)

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        """
        Convert text to speech audio.

        Returns:
            (audio_samples, sample_rate) — audio is float32, sample_rate is 24000.
        """
        if self._kokoro is None:
            raise RuntimeError("Kokoro TTS not loaded. Call load() first.")

        samples, sample_rate = self._kokoro.create(
            text,
            voice=self.voice,
            speed=self.speed,
            lang=self.lang,
        )
        return samples, sample_rate

    @property
    def is_loaded(self) -> bool:
        return self._kokoro is not None
