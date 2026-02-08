#!/bin/bash
# Jupiter Voice - One-Command Setup
# Usage: bash setup.sh
#
# This script installs all dependencies, downloads all AI models (~1.1GB),
# and prepares the project to run. It is idempotent — safe to run multiple times.
set -e

PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║        Jupiter Voice Setup           ║"
echo "  ║  Local voice assistant for OpenClaw  ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# ── System dependencies ──────────────────────────────────────

# 1. Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "[ERROR] Homebrew is required. Install from https://brew.sh"
    exit 1
fi

# 2. Check for OpenClaw
if ! command -v openclaw &> /dev/null; then
    echo "[WARN] OpenClaw CLI not found in PATH."
    echo "       Jupiter Voice needs OpenClaw to process queries."
    echo "       Install from: https://openclaw.dev"
    echo ""
fi

# 3. Install Python 3.12 if needed
if ! command -v python3.12 &> /dev/null; then
    echo "[*] Installing Python 3.12 via Homebrew..."
    brew install python@3.12
else
    echo "[OK] Python 3.12 found"
fi

# 4. Install Rust (needed to build tiktoken, a dependency of whisper)
if ! command -v rustc &> /dev/null; then
    echo "[*] Installing Rust via Homebrew..."
    brew install rust
else
    echo "[OK] Rust found"
fi

# 5. Install espeak-ng (needed by Kokoro TTS for grapheme-to-phoneme)
if ! command -v espeak-ng &> /dev/null; then
    echo "[*] Installing espeak-ng via Homebrew..."
    brew install espeak-ng
else
    echo "[OK] espeak-ng found"
fi

# ── Python environment ───────────────────────────────────────

# 6. Create virtual environment
if [ ! -d "$PROJ_DIR/.venv" ]; then
    echo "[*] Creating virtual environment..."
    python3.12 -m venv "$PROJ_DIR/.venv"
else
    echo "[OK] Virtual environment exists"
fi

source "$PROJ_DIR/.venv/bin/activate"

# 7. Install the project and dependencies
echo "[*] Installing jupiter-voice and dependencies..."
pip install --upgrade pip -q
pip install -e "$PROJ_DIR" -q

# ── AI model downloads (~1.1GB total) ────────────────────────

echo ""
echo "[*] Downloading AI models (this may take a few minutes)..."
echo ""

# 8. Kokoro TTS model (~310MB) + voices (~27MB)
echo "── Kokoro TTS (text-to-speech) ──"
mkdir -p "$PROJ_DIR/models"

if [ ! -f "$PROJ_DIR/models/kokoro-v1.0.onnx" ]; then
    echo "    Downloading kokoro-v1.0.onnx (~310MB)..."
    curl -L --progress-bar -o "$PROJ_DIR/models/kokoro-v1.0.onnx" \
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
else
    echo "    [OK] kokoro-v1.0.onnx"
fi

if [ ! -f "$PROJ_DIR/models/voices-v1.0.bin" ]; then
    echo "    Downloading voices-v1.0.bin (~27MB)..."
    curl -L --progress-bar -o "$PROJ_DIR/models/voices-v1.0.bin" \
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
else
    echo "    [OK] voices-v1.0.bin"
fi

# 9. Whisper STT model (~750MB) — pre-download so first run is fast
echo ""
echo "── Whisper MLX (speech-to-text) ──"

STT_MODEL=$(python -c "import yaml; c=yaml.safe_load(open('$PROJ_DIR/config.yaml')); print(c.get('stt',{}).get('model','distil-medium.en'))" 2>/dev/null || echo "distil-medium.en")

if [ ! -f "$PROJ_DIR/mlx_models/$STT_MODEL/weights.npz" ]; then
    echo "    Downloading $STT_MODEL model (~750MB)..."
    cd "$PROJ_DIR"
    python -c "
from lightning_whisper_mlx import LightningWhisperMLX
print('    Loading model (downloads on first use)...')
LightningWhisperMLX(model='$STT_MODEL', batch_size=12)
print('    [OK] Model downloaded')
"
    cd - > /dev/null
else
    echo "    [OK] $STT_MODEL"
fi

# 10. OpenWakeWord base models (~10MB)
echo ""
echo "── OpenWakeWord (wake word detection) ──"
python -c "import openwakeword; openwakeword.utils.download_models()" 2>/dev/null || true
echo "    [OK] Base models downloaded"

# ── Audio cues ───────────────────────────────────────────────

echo ""
echo "[*] Generating audio cues..."
python "$PROJ_DIR/scripts/generate_cues.py"

# ── Summary ──────────────────────────────────────────────────

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║           Setup complete!                ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# Wake word status
if [ -f "$PROJ_DIR/assets/hey_jupiter.onnx" ]; then
    echo "  Wake word:  'hey jupiter' (custom model)"
else
    echo "  Wake word:  'hey jarvis' (built-in default)"
    echo "              Train 'hey jupiter': python scripts/train_wake_word.py"
fi

echo ""
echo "  To run:"
echo "    cd $PROJ_DIR"
echo "    source .venv/bin/activate"
echo "    jupiter-voice"
echo ""
echo "  Usage:"
echo "    1. Say the wake phrase to activate"
echo "    2. Speak your question or command"
echo "    3. Say 'sudo out' to send"
echo "    4. Listen to the response"
echo ""
