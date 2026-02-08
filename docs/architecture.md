# Architecture

This document describes how Jupiter Voice works internally. It's aimed at contributors and anyone curious about the design decisions.

## Overview

Jupiter Voice is a pipeline of four stages connected by a state machine:

```
Microphone
    |
    v
+-----------------+     +----------------+     +-----------+     +----------+
|   Wake Word     |---->|  Speech-to-    |---->|  OpenClaw |---->| Text-to- |---> Speaker
|   Detection     |     |    Text        |     |    AI     |     |  Speech  |
| (OpenWakeWord)  |     |  (Whisper MLX) |     |   Agent   |     | (Kokoro) |
+-----------------+     +----------------+     +-----------+     +----------+
   "hey jarvis"          Records until          Processes         Speaks the
   activates             "sudo out"             your query        response
```

Audio flows left to right. The microphone is always on, but only the wake word detector runs during idle. The full STT pipeline only activates after a wake word is detected.

## State Machine

The core of the application is a finite state machine with four states:

```
         WAKE_WORD_DETECTED            CLOSE_PHRASE_DETECTED
IDLE ----------------------> LISTENING --------------------> PROCESSING
  ^                             |                                |
  |          CANCEL             |       RESPONSE_RECEIVED        |
  +-----------------------------+                                |
  |                                                              v
  +--------------------------------------------------------- SPEAKING
                          PLAYBACK_COMPLETE / ERROR
```

**States:**

| State | What's happening | Active components |
|-------|------------------|-------------------|
| IDLE | Waiting for wake word | Wake word detector, microphone |
| LISTENING | Recording and transcribing speech | Whisper STT, close phrase detector |
| PROCESSING | Waiting for AI response | OpenClaw gateway |
| SPEAKING | Playing back TTS audio | Kokoro TTS, speaker |

**Transitions:**

| From | Event | To |
|------|-------|----|
| IDLE | WAKE_WORD_DETECTED | LISTENING |
| LISTENING | CLOSE_PHRASE_DETECTED | PROCESSING |
| LISTENING | CANCEL | IDLE |
| PROCESSING | RESPONSE_RECEIVED | SPEAKING |
| PROCESSING | ERROR | IDLE |
| SPEAKING | PLAYBACK_COMPLETE | IDLE |
| SPEAKING | ERROR | IDLE |

Invalid transitions are logged and ignored. The state machine is thread-safe (uses a threading lock) and supports listener callbacks that fire on state entry.

**Source:** `jupiter_voice/state_machine.py`

## Components

### Audio Capture (`jupiter_voice/audio/capture.py`)

Uses `sounddevice.InputStream` with a callback that pushes audio chunks into a `deque` buffer.

- **Format:** 16kHz, mono, int16
- **Chunk size:** 1280 samples (80ms) — matched to what OpenWakeWord expects
- **Buffer:** deque with a max of 10,000 chunks (~800 seconds) to prevent unbounded memory growth
- `read_chunk()` — pops one chunk (used during IDLE for wake word detection)
- `read_seconds(duration)` — accumulates chunks until `duration` seconds of audio is collected (used during LISTENING for transcription)
- `drain()` — discards all buffered audio (used after SPEAKING to prevent self-triggering)

### Wake Word Detector (`jupiter_voice/wake/detector.py`)

Wraps [OpenWakeWord](https://github.com/dscripka/openWakeWord), which runs small ONNX models for keyword spotting.

- Accepts 1280-sample int16 chunks (80ms at 16kHz)
- Returns `True` when the wake word score exceeds the configured threshold
- Supports both built-in model names (like `hey_jarvis`) and custom `.onnx` file paths
- Resets its internal prediction buffer after each detection to avoid double-triggers

### Speech-to-Text (`jupiter_voice/stt/whisper_mlx.py`)

Wraps [Lightning Whisper MLX](https://github.com/mustafaaljadery/lightning-whisper-mlx) for Apple Silicon-optimized transcription.

- During LISTENING, the orchestrator reads 3-second chunks of audio and feeds them to Whisper
- Whisper returns partial transcriptions that accumulate into a growing transcript
- The close phrase detector checks the accumulated text after each chunk
- Auto-detects whether the Whisper library accepts numpy arrays directly or needs a temp WAV file (caches the result after the first attempt)

**Model options:** `tiny.en` (fastest, least accurate) through `large-v3` (slowest, most accurate). Default is `distil-medium.en` — a good balance for English.

### Close Phrase Detector (`jupiter_voice/stt/close_phrase.py`)

Detects when the user says "sudo out" to end their query. This is harder than it sounds because Whisper frequently misrecognizes "sudo out" as similar-sounding phrases.

**Strategy:** Fuzzy regex matching against 7+ patterns:

```
sudo out, pseudo out, sue do out, sudo doubt,
su do out, sudah out, sudu out
```

Plus any additional alternatives from `config.yaml`. When a match is found, everything before the close phrase becomes the query, and everything including and after it is stripped.

### OpenClaw Gateway (`jupiter_voice/gateway/openclaw.py`)

Sends the transcribed query to [OpenClaw](https://openclaw.dev) and returns the AI's response.

- Uses the `openclaw agent` CLI via `subprocess.run` (not HTTP — the gateway is WebSocket-based internally)
- Command: `openclaw agent --message "..." --session-id agent:main:main --json`
- Parses JSON output, extracts `result.payloads[0].text`
- Handles non-JSON prefix noise (CLI warnings) by finding the first `{` in stdout
- Configurable timeout with a buffer beyond OpenClaw's own timeout

### Text-to-Speech (`jupiter_voice/tts/kokoro_tts.py`)

Wraps [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx) for natural voice synthesis.

- 82M parameter model, ~0.3s synthesis time for typical responses
- 14 available voices (see [voices.md](voices.md))
- Outputs float32 audio at 24kHz
- Auto-downloads model files (~340MB total) on first use if not present
- Falls back to macOS `say` command if Kokoro fails (`jupiter_voice/tts/macos_fallback.py`)

### Audio Playback (`jupiter_voice/audio/playback.py`)

Plays audio through the system speakers via `sounddevice.play()`.

- `play()` — blocking playback
- `play_async()` — non-blocking (spawns a thread)
- `stop()` — immediately stop playback

### Audio Cues (`jupiter_voice/audio/cues.py`)

Short sound effects that provide feedback:

| Cue | When | Sound |
|-----|------|-------|
| `ding.wav` | Wake word detected | Rising chime |
| `send.wav` | Query sent to AI | Soft ping |
| `error.wav` | Error occurred | Low tone |

Generated by `scripts/generate_cues.py` using numpy sine waves. Not checked into git — regenerated by `setup.sh`.

## Configuration (`jupiter_voice/config.py`)

Configuration is loaded in this order (later overrides earlier):

1. **Defaults** — hardcoded in dataclass fields
2. **`config.yaml`** — user-editable YAML file
3. **Environment variables** — `JUPITER_VOICE_*` prefix

The config is structured as nested dataclasses: `JupiterConfig` contains `WakeConfig`, `STTConfig`, `TTSConfig`, `ClosePhraseConfig`, `AudioConfig`, `GatewayConfig`, `CuesConfig`, and `LoggingConfig`.

## Self-Trigger Prevention

A critical design challenge: the TTS audio output can be picked up by the microphone and trigger the wake word detector or contaminate the next transcription.

**Solution (in `cli.py` SPEAKING handler):**

1. Playback is blocking — the main loop waits for TTS to finish
2. After playback completes, `capture.drain()` discards all buffered audio captured during playback
3. `wake_detector.reset()` clears prediction buffers
4. A 300ms sleep provides an additional gap
5. A second `capture.drain()` catches any audio from the gap
6. Only then does the state transition back to IDLE

## Orchestrator (`jupiter_voice/cli.py`)

The `JupiterVoice` class ties everything together:

1. **Startup:** prints banner, runs health checks, loads all models with progress indicators, starts audio capture
2. **Main loop:** polls `StateMachine.state` and calls the appropriate tick handler (`_idle_tick`, `_listening_tick`, `_processing_tick`, `_speaking_tick`)
3. **Shutdown:** stops audio capture, stops playback, handles SIGINT/SIGTERM gracefully

The orchestrator is deliberately single-threaded in its main loop (audio capture uses a callback thread, but decision-making is sequential). This keeps the logic simple and avoids race conditions.

## Thread Safety

- **Audio capture callback** runs on a sounddevice thread, pushes to a thread-safe `deque`
- **State machine** uses a `threading.Lock` for transitions; callbacks fire outside the lock
- **Main loop** is single-threaded — reads from the deque, makes decisions, dispatches actions
- **Playback** can run async (separate thread) but TTS playback in the main flow is blocking

## Directory Layout

```
jupiter_voice/
├── cli.py               # Entry point + orchestrator (JupiterVoice class)
├── config.py            # YAML + env config loader (dataclass-based)
├── state_machine.py     # State/Event enums, transition table, StateMachine class
├── audio/
│   ├── capture.py       # Microphone InputStream with deque buffer
│   ├── playback.py      # Speaker output via sounddevice
│   └── cues.py          # WAV sound effects loader + player
├── stt/
│   ├── whisper_mlx.py   # Lightning Whisper MLX wrapper
│   └── close_phrase.py  # "sudo out" fuzzy regex detection
├── tts/
│   ├── kokoro_tts.py    # Kokoro ONNX wrapper + auto-download
│   └── macos_fallback.py# macOS `say` command fallback
├── wake/
│   └── detector.py      # OpenWakeWord integration
├── gateway/
│   └── openclaw.py      # OpenClaw CLI subprocess client
└── utils/
    └── health.py        # Startup health checks (Rich table output)
```
