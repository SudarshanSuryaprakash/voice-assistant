"""Wake word detection using OpenWakeWord."""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Detects wake words (e.g., 'hey jupiter') using OpenWakeWord."""

    def __init__(
        self,
        model: str = "hey_jarvis",
        threshold: float = 0.5,
        inference_framework: str = "onnx",
    ) -> None:
        self.model_name = model
        self.threshold = threshold
        self.inference_framework = inference_framework
        self._oww_model = None

    def load(self) -> None:
        """Load the wake word model. Downloads base models if needed."""
        import openwakeword
        from openwakeword.model import Model as OWWModel

        # Download shared preprocessing models (melspectrogram, embedding)
        openwakeword.utils.download_models()

        # Determine if this is a built-in model name or a file path
        model_arg = self.model_name
        if "/" in model_arg or model_arg.endswith((".onnx", ".tflite")):
            # Custom model file path
            self._oww_model = OWWModel(
                wakeword_models=[model_arg],
                inference_framework=self.inference_framework,
            )
            logger.info("Loaded custom wake word model: %s", model_arg)
        else:
            # Built-in model name (e.g., "hey_jarvis")
            self._oww_model = OWWModel(
                wakeword_models=[model_arg],
                inference_framework=self.inference_framework,
            )
            logger.info("Loaded wake word model: %s", model_arg)

    def process_chunk(self, audio_chunk: np.ndarray) -> bool:
        """
        Process an audio chunk and check for wake word.

        Args:
            audio_chunk: int16 numpy array, 16kHz mono. Should be 1280 samples (80ms).

        Returns:
            True if wake word detected above threshold.
        """
        if self._oww_model is None:
            raise RuntimeError("Wake word model not loaded. Call load() first.")

        self._oww_model.predict(audio_chunk)

        for model_name in self._oww_model.prediction_buffer:
            scores = list(self._oww_model.prediction_buffer[model_name])
            if scores and scores[-1] > self.threshold:
                logger.info("Wake word detected: %s (score=%.3f)", model_name, scores[-1])
                self._oww_model.reset()
                return True

        return False

    def reset(self) -> None:
        """Reset internal prediction buffers."""
        if self._oww_model:
            self._oww_model.reset()

    @property
    def is_loaded(self) -> bool:
        return self._oww_model is not None
