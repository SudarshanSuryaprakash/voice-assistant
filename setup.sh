#!/bin/bash
# Jupiter Voice - One-Command Setup
# Usage: bash setup.sh
set -e

PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║        Jupiter Voice Setup           ║"
echo "  ║  Local voice assistant for OpenClaw  ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# 1. Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "[ERROR] Homebrew is required. Install from https://brew.sh"
    exit 1
fi

# 2. Install Python 3.12 if needed
if ! command -v python3.12 &> /dev/null; then
    echo "[*] Installing Python 3.12 via Homebrew..."
    brew install python@3.12
else
    echo "[OK] Python 3.12 found"
fi

# 3. Install Rust (needed to build tiktoken, a dependency of whisper)
if ! command -v rustc &> /dev/null; then
    echo "[*] Installing Rust via Homebrew..."
    brew install rust
else
    echo "[OK] Rust found"
fi

# 4. Install espeak-ng (needed by Kokoro's G2P as fallback)
if ! command -v espeak-ng &> /dev/null; then
    echo "[*] Installing espeak-ng via Homebrew..."
    brew install espeak-ng
else
    echo "[OK] espeak-ng found"
fi

# 4. Create virtual environment
if [ ! -d "$PROJ_DIR/.venv" ]; then
    echo "[*] Creating virtual environment..."
    python3.12 -m venv "$PROJ_DIR/.venv"
else
    echo "[OK] Virtual environment exists"
fi

source "$PROJ_DIR/.venv/bin/activate"

# 5. Install the project
echo "[*] Installing jupiter-voice and dependencies..."
pip install --upgrade pip -q
pip install -e "$PROJ_DIR[dev]" -q

# 6. Download Kokoro TTS model files
echo "[*] Checking Kokoro TTS models..."
mkdir -p "$PROJ_DIR/models"

if [ ! -f "$PROJ_DIR/models/kokoro-v1.0.onnx" ]; then
    echo "    Downloading kokoro-v1.0.onnx (~300MB)..."
    curl -L --progress-bar -o "$PROJ_DIR/models/kokoro-v1.0.onnx" \
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
else
    echo "    [OK] kokoro-v1.0.onnx"
fi

if [ ! -f "$PROJ_DIR/models/voices-v1.0.bin" ]; then
    echo "    Downloading voices-v1.0.bin..."
    curl -L --progress-bar -o "$PROJ_DIR/models/voices-v1.0.bin" \
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
else
    echo "    [OK] voices-v1.0.bin"
fi

# 7. Download OpenWakeWord base models
echo "[*] Downloading OpenWakeWord base models..."
python -c "import openwakeword; openwakeword.utils.download_models()" 2>/dev/null || true

# 8. Generate audio cues
echo "[*] Generating audio cues..."
python "$PROJ_DIR/scripts/generate_cues.py"

# 9. Wake word model status
echo ""
if [ -f "$PROJ_DIR/assets/hey_jupiter.onnx" ]; then
    echo "[OK] Custom 'hey jupiter' wake word model found"
else
    echo "┌──────────────────────────────────────────────────────┐"
    echo "│  Wake Word: Using built-in 'hey jarvis' by default  │"
    echo "│                                                      │"
    echo "│  To train a custom 'hey jupiter' model:             │"
    echo "│  python scripts/train_wake_word.py --help            │"
    echo "│                                                      │"
    echo "│  Or update config.yaml:                             │"
    echo "│    wake.model: 'assets/hey_jupiter.onnx'            │"
    echo "└──────────────────────────────────────────────────────┘"
fi

echo ""
echo "  Setup complete!"
echo ""
echo "  To run:"
echo "    source $PROJ_DIR/.venv/bin/activate"
echo "    jupiter-voice"
echo ""
echo "  Usage:"
echo "    Say 'hey jupiter' (or 'hey jarvis') to start"
echo "    Speak your question"
echo "    Say 'sudo out' to send"
echo ""
