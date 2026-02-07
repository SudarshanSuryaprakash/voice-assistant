"""Configuration loading for Jupiter Voice."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class WakeConfig:
    model: str = "hey_jarvis"
    threshold: float = 0.5
    inference_framework: str = "onnx"


@dataclass
class STTConfig:
    model: str = "distil-medium.en"
    batch_size: int = 12
    chunk_duration: float = 3.0
    chunk_overlap: float = 0.5


@dataclass
class TTSConfig:
    voice: str = "af_heart"
    speed: float = 1.0
    lang: str = "en-us"
    fallback_to_macos_say: bool = True


@dataclass
class ClosePhraseConfig:
    primary: str = "sudo out"
    alternatives: list[str] = field(
        default_factory=lambda: ["pseudo out", "sue do out", "sudo doubt", "su do out"]
    )


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1280
    device: Optional[int] = None


@dataclass
class GatewayConfig:
    session_id: str = "agent:main:main"
    timeout: int = 120
    openclaw_bin: Optional[str] = None  # auto-detect from PATH


@dataclass
class CuesConfig:
    enabled: bool = True
    wake_detected: str = "assets/ding.wav"
    sending: str = "assets/send.wav"
    error: str = "assets/error.wav"


@dataclass
class LoggingConfig:
    level: str = "INFO"


@dataclass
class JupiterConfig:
    wake: WakeConfig = field(default_factory=WakeConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    close_phrase: ClosePhraseConfig = field(default_factory=ClosePhraseConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    gateway: GatewayConfig = field(default_factory=GatewayConfig)
    cues: CuesConfig = field(default_factory=CuesConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def _apply_dict(dc: object, data: dict) -> None:
    """Apply a dict of values onto a dataclass instance."""
    for key, value in data.items():
        if hasattr(dc, key):
            current = getattr(dc, key)
            if isinstance(value, dict) and hasattr(current, "__dataclass_fields__"):
                _apply_dict(current, value)
            else:
                setattr(dc, key, value)


def _apply_env_overrides(config: JupiterConfig) -> None:
    """Override config values from JUPITER_VOICE_* environment variables."""
    env_map = {
        "JUPITER_VOICE_SESSION_ID": ("gateway", "session_id"),
        "JUPITER_VOICE_STT_MODEL": ("stt", "model"),
        "JUPITER_VOICE_TTS_VOICE": ("tts", "voice"),
        "JUPITER_VOICE_WAKE_MODEL": ("wake", "model"),
        "JUPITER_VOICE_WAKE_THRESHOLD": ("wake", "threshold"),
        "JUPITER_VOICE_LOG_LEVEL": ("logging", "level"),
    }
    for env_var, (section, field_name) in env_map.items():
        value = os.environ.get(env_var)
        if value is not None:
            section_obj = getattr(config, section)
            field_type = type(getattr(section_obj, field_name))
            if field_type is float:
                value = float(value)
            elif field_type is int:
                value = int(value)
            setattr(section_obj, field_name, value)
            logger.debug("Env override: %s = %s", env_var, value)


def load_config(path: str = "config.yaml") -> JupiterConfig:
    """Load configuration from YAML file with env var overrides and OpenClaw auto-discovery."""
    config = JupiterConfig()

    # Load YAML if it exists
    config_path = Path(path)
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        _apply_dict(config, data)
        logger.debug("Loaded config from %s", config_path)

    # Apply environment variable overrides
    _apply_env_overrides(config)

    return config
