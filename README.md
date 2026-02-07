# Jupiter Voice

A fully local, free voice assistant that interfaces with [OpenClaw](https://openclaw.dev) AI agents. Speak naturally, get spoken responses — zero ongoing costs for the audio pipeline.

## How it Works

```
You speak → Wake Word Detection → Speech-to-Text → OpenClaw AI → Text-to-Speech → You hear the response
```

1. Say **"hey jupiter"** (or "hey jarvis" with the default model) to activate
2. Speak your question or command naturally
3. Say **"sudo out"** to send your query
4. Jupiter processes your request and speaks the response

## Tech Stack

All free, all local, optimized for Apple Silicon:

| Component | Tool | Purpose |
|-----------|------|---------|
| Wake Word | [OpenWakeWord](https://github.com/dscripka/openWakeWord) | Always-on listener for activation phrase |
| Speech-to-Text | [Lightning Whisper MLX](https://github.com/mustafaaljadery/lightning-whisper-mlx) | Fast transcription on Apple Silicon |
| Text-to-Speech | [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx) | Natural-sounding voice synthesis |
| Audio I/O | [sounddevice](https://python-sounddevice.readthedocs.io/) | Microphone capture and speaker output |
| AI Backend | [OpenClaw](https://openclaw.dev) | AI agent that processes your queries |

## Requirements

- macOS on Apple Silicon (M1/M2/M3/M4)
- Python 3.10+
- [Homebrew](https://brew.sh)
- OpenClaw running locally with gateway enabled

## Quick Start

```bash
# Clone the repository
git clone https://github.com/jupiter/jupiter-voice.git
cd jupiter-voice

# Run the setup script (installs everything)
bash setup.sh

# Activate the virtual environment
source .venv/bin/activate

# Start Jupiter Voice
jupiter-voice
```

## Configuration

Edit `config.yaml` to customize:

```yaml
wake:
  model: "hey_jarvis"       # or "assets/hey_jupiter.onnx" for custom
  threshold: 0.5             # Detection sensitivity (0.0 - 1.0)

stt:
  model: "distil-medium.en"  # Whisper model (tiny, small, medium, large)

tts:
  voice: "af_heart"          # Kokoro voice name
  speed: 1.0                 # Speech speed

gateway:
  session_id: "agent:main:main"  # OpenClaw session
  timeout: 120                    # Max response time (seconds)
```

### OpenClaw Integration

Jupiter Voice uses the `openclaw` CLI to communicate with the AI agent. It must be installed and available in your PATH. The gateway must be running (`openclaw` handles this automatically).

## Custom Wake Word

The default wake word is "hey jarvis" (built into OpenWakeWord). To train a custom "hey jupiter" model:

```bash
python scripts/train_wake_word.py --method colab
```

This guides you through the Google Colab training notebook (~45 minutes). After training, update `config.yaml`:

```yaml
wake:
  model: "assets/hey_jupiter.onnx"
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Jupiter Voice                         │
│                                                          │
│  State Machine: IDLE → LISTENING → PROCESSING → SPEAKING │
│                   ↑                                ↓     │
│                   └────────────────────────────────┘     │
│                                                          │
│  IDLE:       OpenWakeWord listens for wake phrase        │
│  LISTENING:  Whisper transcribes in 3s chunks            │
│              Detects "sudo out" close phrase              │
│  PROCESSING: Sends transcript to OpenClaw gateway        │
│  SPEAKING:   Kokoro TTS speaks the response              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JUPITER_VOICE_SESSION_ID` | Override OpenClaw session ID |
| `JUPITER_VOICE_STT_MODEL` | Override Whisper model |
| `JUPITER_VOICE_TTS_VOICE` | Override TTS voice |
| `JUPITER_VOICE_WAKE_MODEL` | Override wake word model |
| `JUPITER_VOICE_WAKE_THRESHOLD` | Override wake threshold |
| `JUPITER_VOICE_LOG_LEVEL` | Override log level |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check jupiter_voice/
```

## Troubleshooting

**"No microphone detected"**
- Check System Preferences > Security & Privacy > Microphone
- Ensure your mic is connected and set as default input

**"OpenClaw CLI not found"**
- Ensure OpenClaw is installed and `openclaw` is in your PATH
- Test with: `openclaw doctor`

**TTS sounds robotic**
- The macOS `say` fallback is used when Kokoro fails
- Run `bash setup.sh` to ensure Kokoro models are downloaded
- Check that `espeak-ng` is installed: `brew install espeak-ng`

**Whisper is slow**
- Try a smaller model in config.yaml: `stt.model: "tiny.en"`
- Ensure you're using Apple Silicon (MLX acceleration)

## License

MIT
