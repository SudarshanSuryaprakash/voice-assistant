#!/usr/bin/env python3
"""Generate audio cue WAV files for Jupiter Voice.

Creates three short sound effects:
  - ding.wav:  Wake word confirmation (ascending chime)
  - send.wav:  Query sending notification (rising tone)
  - error.wav: Error notification (descending tone)

Usage:
    python scripts/generate_cues.py
"""

from pathlib import Path

import numpy as np
import soundfile as sf

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
SAMPLE_RATE = 44100


def _envelope(t: np.ndarray, decay: float = 10.0) -> np.ndarray:
    """Exponential decay envelope."""
    return np.exp(-t * decay)


def generate_ding(path: Path) -> None:
    """Two-tone ascending chime for wake word detection."""
    duration = 0.18
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    tone = 0.4 * np.sin(2 * np.pi * 880 * t) + 0.25 * np.sin(2 * np.pi * 1320 * t)
    audio = (tone * _envelope(t, 12)).astype(np.float32)
    sf.write(str(path), audio, SAMPLE_RATE)


def generate_send(path: Path) -> None:
    """Rising tone for sending query."""
    duration = 0.22
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.linspace(440, 880, len(t))
    tone = 0.35 * np.sin(2 * np.pi * freq * t / SAMPLE_RATE * SAMPLE_RATE)
    # Correct instantaneous frequency integration
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    tone = 0.35 * np.sin(phase)
    audio = (tone * _envelope(t, 8)).astype(np.float32)
    sf.write(str(path), audio, SAMPLE_RATE)


def generate_error(path: Path) -> None:
    """Descending tone for error notification."""
    duration = 0.3
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.linspace(440, 220, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    tone = 0.35 * np.sin(phase)
    audio = (tone * _envelope(t, 6)).astype(np.float32)
    sf.write(str(path), audio, SAMPLE_RATE)


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    generators = [
        ("ding.wav", generate_ding),
        ("send.wav", generate_send),
        ("error.wav", generate_error),
    ]

    for filename, gen_fn in generators:
        path = ASSETS_DIR / filename
        gen_fn(path)
        print(f"  Generated {path}")


if __name__ == "__main__":
    main()
