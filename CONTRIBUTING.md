# Contributing to Jupiter Voice

Thanks for your interest in contributing! Jupiter Voice is a community project and we welcome all kinds of contributions.

## Getting Started

1. Fork the repository
2. Clone your fork and set up the dev environment:

```bash
git clone https://github.com/SudarshanSuryaprakash/voice-assistant.git
cd voice-assistant
bash setup.sh
source .venv/bin/activate
pip install -e ".[dev]"
```

3. Create a branch for your work:

```bash
git checkout -b my-feature
```

## Development Workflow

### Running the Project

```bash
source .venv/bin/activate
jupiter-voice          # normal mode
jupiter-voice -v       # verbose/debug mode
```

### Running Tests

```bash
pytest -v
```

### Linting

```bash
ruff check jupiter_voice/ tests/ scripts/
ruff check --fix jupiter_voice/ tests/ scripts/  # auto-fix
```

### Project Structure

See [docs/architecture.md](docs/architecture.md) for a walkthrough of how the codebase is organized and how the components interact.

## What to Work On

### Good First Issues

Look for issues labeled `good first issue` on GitHub. These are scoped to be approachable for newcomers.

### Areas Where Help Is Appreciated

- **Linux support** — porting audio capture to PulseAudio/PipeWire
- **Windows support** — porting audio and path handling
- **Additional TTS backends** — Piper, Coqui, or other local engines
- **Wake word model sharing** — pre-trained `.onnx` files for common phrases
- **Improved VAD** — voice activity detection for more natural close-phrase handling
- **Better transcription** — handling accents, noise, and edge cases
- **Documentation** — tutorials, translations, usage examples

## Submitting Changes

1. Make sure tests pass: `pytest -v`
2. Make sure lint is clean: `ruff check jupiter_voice/ tests/ scripts/`
3. Commit with a clear message describing what changed and why
4. Push to your fork and open a pull request
5. Describe what your PR does and link any related issues

## Code Style

- Python 3.10+ syntax
- Line length: 100 characters
- Linter: [Ruff](https://docs.astral.sh/ruff/) with `E`, `F`, `W`, `I` rules
- Use type annotations for function signatures
- Keep imports sorted (Ruff handles this)

## Adding a New TTS Backend

If you want to add support for a different TTS engine:

1. Create a new file in `jupiter_voice/tts/` (e.g., `piper_tts.py`)
2. Implement a class with `load()` and `synthesize(text) -> (np.ndarray, int)` methods matching `KokoroTTSEngine`'s interface
3. Add a config option to select the backend
4. Add tests

## Adding a New STT Backend

Similar pattern — create a file in `jupiter_voice/stt/`, implement `load()` and `transcribe(audio) -> str`, and wire it up through config.

## Reporting Bugs

When reporting bugs, please include:

- Your macOS version and chip (e.g., macOS 15.2, M2 Pro)
- Python version (`python --version`)
- Steps to reproduce
- Error output (run with `jupiter-voice -v` for verbose logs)

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
