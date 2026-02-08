# Jupiter Voice

A fully local, open-source voice assistant for [OpenClaw](https://openclaw.dev) AI agents on Apple Silicon. Talk to your AI agent with natural speech and hear spoken responses — the entire audio pipeline runs locally at zero cost.

## Demo

```
You: "Hey Jarvis"                          [wake word activates]
     "What's the weather like today?"      [speech transcribed live]
     "Sudo out"                            [query sent to AI]

Jupiter: "It's currently 72 degrees and    [AI responds via speaker]
          sunny in your area..."
```

## Why Jupiter Voice?

- **Completely free** — No API keys for speech. The only cost is your AI model's token usage.
- **Fully local** — Wake word detection, speech-to-text, and text-to-speech all run on your Mac. Nothing leaves your machine (except the query to your AI agent).
- **Apple Silicon optimized** — Uses [MLX](https://github.com/ml-explore/mlx) for 10x faster Whisper transcription on M-series chips.
- **Modular** — Swap wake words, STT models, TTS voices, or AI backends via config.
- **Hackable** — Clean Python codebase, MIT licensed, easy to extend.

## How It Works

```
Microphone
    │
    ▼
┌──────────────┐     ┌─────────────┐     ┌──────────┐     ┌──────────┐
│  Wake Word   │────▶│  Speech to  │────▶│ OpenClaw │────▶│ Text to  │──▶ Speaker
│  Detection   │     │    Text     │     │    AI    │     │  Speech  │
│ (OpenWakeWord)     │  (Whisper)  │     │  Agent   │     │ (Kokoro) │
└──────────────┘     └─────────────┘     └──────────┘     └──────────┘
     "hey jarvis"     Records until       Processes        Speaks the
     activates        "sudo out"          your query       response
```

**State machine:** IDLE → LISTENING → PROCESSING → SPEAKING → IDLE

See [docs/architecture.md](docs/architecture.md) for a deep dive.

## Requirements

- **macOS on Apple Silicon** (M1, M2, M3, M4, or later)
- **[Homebrew](https://brew.sh)** — package manager for macOS
- **[OpenClaw](https://openclaw.dev)** — the AI agent that answers your queries
- ~1.5 GB of free disk space for AI models

The setup script handles everything else (Python, Rust, espeak-ng, all AI models).

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/SudarshanSuryaprakash/voice-assistant.git
cd voice-assistant

# 2. Run setup (installs deps, downloads ~1.1GB of AI models)
bash setup.sh

# 3. Activate the environment
source .venv/bin/activate

# 4. Start the voice assistant
jupiter-voice
```

On first run, the setup script will:
- Install Python 3.12, Rust, and espeak-ng via Homebrew (if missing)
- Create a Python virtual environment
- Install all Python dependencies
- Download the Whisper STT model (~750MB), Kokoro TTS model (~310MB), voice data (~27MB), and OpenWakeWord models (~10MB)
- Generate audio cue sounds

### Usage

1. Say **"hey jarvis"** (the default wake phrase) — you'll hear a chime
2. Speak your question or command naturally
3. Say **"sudo out"** to send your query to the AI
4. Listen to the spoken response
5. Repeat!

> **Tip:** You can train a custom "hey jupiter" (or any other phrase) wake word. See [Custom Wake Word](#custom-wake-word) below.

## Configuration

All settings live in `config.yaml`. Here are the key options:

```yaml
# Wake word detection
wake:
  model: "hey_jarvis"         # Built-in model, or path to custom .onnx file
  threshold: 0.5               # Sensitivity: 0.0 (loose) to 1.0 (strict)

# Speech-to-text (Whisper)
stt:
  model: "distil-medium.en"   # Options: tiny.en, small.en, medium, distil-medium.en, large-v3
  chunk_duration: 3.0          # Seconds of audio per transcription chunk

# Text-to-speech (Kokoro)
tts:
  voice: "af_heart"            # See docs/voices.md for all 14 available voices
  speed: 1.0                   # 0.5 = slow, 1.0 = normal, 2.0 = fast
  fallback_to_macos_say: true  # Use macOS `say` if Kokoro fails

# Close phrase (what you say to send the query)
close_phrase:
  primary: "sudo out"

# OpenClaw AI agent
gateway:
  session_id: "agent:main:main"  # Your OpenClaw session ID
  timeout: 120                    # Max wait for AI response (seconds)
```

Every config value can be overridden with an environment variable:

| Variable | Overrides |
|----------|-----------|
| `JUPITER_VOICE_SESSION_ID` | `gateway.session_id` |
| `JUPITER_VOICE_STT_MODEL` | `stt.model` |
| `JUPITER_VOICE_TTS_VOICE` | `tts.voice` |
| `JUPITER_VOICE_WAKE_MODEL` | `wake.model` |
| `JUPITER_VOICE_WAKE_THRESHOLD` | `wake.threshold` |
| `JUPITER_VOICE_LOG_LEVEL` | `logging.level` |

## Custom Wake Word

The default wake word is **"hey jarvis"** (a model bundled with OpenWakeWord). You can train any custom phrase — like "hey jupiter", "ok computer", or anything else.

### Training via Google Colab (recommended)

```bash
python scripts/train_wake_word.py --method colab
```

This prints step-by-step instructions for the [OpenWakeWord training notebook](https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb). Training takes ~45 minutes and requires no manual voice recordings (it generates synthetic speech automatically).

After training, drop the `.onnx` file into `assets/` and update your config:

```yaml
wake:
  model: "assets/hey_jupiter.onnx"
```

## Project Structure

```
voice-assistant/
├── jupiter_voice/           # Main Python package
│   ├── cli.py               # Entry point and main orchestrator
│   ├── config.py            # YAML + env config loader
│   ├── state_machine.py     # IDLE/LISTENING/PROCESSING/SPEAKING FSM
│   ├── audio/               # Microphone capture, speaker playback, audio cues
│   ├── stt/                 # Whisper MLX transcription + "sudo out" detection
│   ├── tts/                 # Kokoro TTS synthesis + macOS fallback
│   ├── wake/                # OpenWakeWord integration
│   ├── gateway/             # OpenClaw CLI client
│   └── utils/               # Health checks
├── tests/                   # Unit tests (pytest)
├── scripts/
│   ├── generate_cues.py     # Generate audio cue WAV files
│   └── train_wake_word.py   # Wake word training helper
├── config.yaml              # Configuration file
├── setup.sh                 # One-command setup script
├── models/                  # Kokoro TTS models (downloaded by setup.sh)
├── mlx_models/              # Whisper STT models (downloaded by setup.sh)
└── assets/                  # Audio cues + custom wake word models
```

## Troubleshooting

### "No microphone detected"
- **macOS permissions:** Go to System Settings > Privacy & Security > Microphone and ensure your terminal app has access.
- **No mic hardware:** Mac Minis don't have a built-in mic. Connect a USB microphone or headset.
- **Wrong device:** Set a specific device index in `config.yaml` under `audio.device`. Run `python -c "import sounddevice; print(sounddevice.query_devices())"` to list available devices.

### "OpenClaw CLI not found"
- Install OpenClaw from [openclaw.dev](https://openclaw.dev).
- Make sure `openclaw` is in your PATH: `which openclaw`
- Test connectivity: `openclaw doctor`

### Wake word not triggering
- Speak clearly and at a normal volume.
- Lower the threshold in `config.yaml`: `wake.threshold: 0.3`
- Ensure you're using the right phrase for your model ("hey jarvis" for the default).

### "sudo out" not detected
- Whisper sometimes misrecognizes it. The system fuzzy-matches variants like "pseudo out" and "sue do out" automatically.
- Speak it clearly with a brief pause before.
- You can add more alternatives in `config.yaml` under `close_phrase.alternatives`.

### TTS sounds robotic / uses macOS voice
- This means Kokoro TTS failed and it fell back to macOS `say`.
- Run `bash setup.sh` to ensure all models are downloaded.
- Check that espeak-ng is installed: `brew install espeak-ng`

### Whisper transcription is slow
- Try a smaller model: set `stt.model: "tiny.en"` in `config.yaml` (faster but less accurate).
- The default `distil-medium.en` is a good balance. `large-v3` is the most accurate but slowest.
- Ensure you're on Apple Silicon — Intel Macs won't get MLX acceleration.

### Response takes a long time
- This depends on your AI model. The voice pipeline itself is fast; the bottleneck is the LLM response time.
- Increase `gateway.timeout` in `config.yaml` if responses are being cut off.

## Development

```bash
# Install with dev dependencies
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check jupiter_voice/ tests/ scripts/

# Run with debug logging
jupiter-voice -v
```

See [docs/architecture.md](docs/architecture.md) for a walkthrough of the codebase.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas where help is especially appreciated:
- Linux support (PulseAudio/PipeWire audio capture)
- Windows support
- Additional TTS engine backends
- Wake word model sharing (pre-trained .onnx files for common phrases)
- Improved VAD (voice activity detection) for more natural close-phrase detection

## Tech Stack

| Component | Library | Size | Purpose |
|-----------|---------|------|---------|
| Wake Word | [OpenWakeWord](https://github.com/dscripka/openWakeWord) | ~10MB | Always-on keyword detection |
| Speech-to-Text | [Lightning Whisper MLX](https://github.com/mustafaaljadery/lightning-whisper-mlx) | ~750MB | Audio transcription (Apple Silicon optimized) |
| Text-to-Speech | [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx) | ~340MB | Natural voice synthesis |
| Audio I/O | [sounddevice](https://python-sounddevice.readthedocs.io/) | — | Microphone capture and speaker output |
| AI Backend | [OpenClaw](https://openclaw.dev) | — | AI agent that processes your queries |
| Terminal UI | [Rich](https://github.com/Textualize/rich) | — | Startup banner, progress indicators |

## License

[MIT](LICENSE) — use it however you want.
