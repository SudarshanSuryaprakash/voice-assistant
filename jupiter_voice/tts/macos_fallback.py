"""Fallback TTS using macOS built-in `say` command."""

from __future__ import annotations

import logging
import platform
import subprocess

logger = logging.getLogger(__name__)


class MacOSFallbackTTS:
    """Speaks text using the macOS `say` command. Works on any Mac without dependencies."""

    @staticmethod
    def is_available() -> bool:
        return platform.system() == "Darwin"

    @staticmethod
    def speak(text: str, voice: str = "Samantha", rate: int = 200) -> None:
        """Speak text aloud. Blocks until speech completes."""
        if not MacOSFallbackTTS.is_available():
            logger.warning("macOS `say` is not available on this platform")
            return
        try:
            subprocess.run(
                ["say", "-v", voice, "-r", str(rate), text],
                check=True,
                timeout=120,
            )
        except subprocess.CalledProcessError as e:
            logger.error("macOS say failed: %s", e)
        except FileNotFoundError:
            logger.error("macOS `say` command not found")
