#!/usr/bin/env python3
"""Train a custom 'hey jupiter' wake word model for OpenWakeWord.

This script helps you train a custom wake word model. There are two methods:

Method 1 (Recommended): Google Colab notebook
    - Fast, free, no local GPU needed
    - Uses synthetic speech generation (no manual recording)
    - Takes ~45 minutes

Method 2: Local training
    - Requires local GPU and training setup
    - Uses the openwakeword training pipeline

Usage:
    python scripts/train_wake_word.py --method colab
    python scripts/train_wake_word.py --method local --target "hey jupiter"
"""

import argparse
import sys
from pathlib import Path

COLAB_URL = "https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "assets"


def show_colab_instructions(target_word: str) -> None:
    """Print step-by-step instructions for training via Google Colab."""
    print(
        f"""
╔══════════════════════════════════════════════════════════════╗
║         Train Custom Wake Word: "{target_word}"             ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Method: Google Colab (Recommended)                          ║
║                                                              ║
║  Steps:                                                      ║
║  1. Open the training notebook:                              ║
║     {COLAB_URL}                                              ║
║                                                              ║
║  2. In the notebook, set:                                    ║
║     target_word = "{target_word}"                            ║
║                                                              ║
║  3. Run all cells (takes ~45 minutes)                        ║
║                                                              ║
║  4. Download the generated .onnx model file                  ║
║                                                              ║
║  5. Save it as:                                              ║
║     {OUTPUT_DIR}/hey_jupiter.onnx                            ║
║                                                              ║
║  6. Update config.yaml:                                      ║
║     wake:                                                    ║
║       model: "assets/hey_jupiter.onnx"                       ║
║                                                              ║
║  7. Restart jupiter-voice                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    )


def train_locally(target_word: str) -> None:
    """Train a wake word model locally using openwakeword's training pipeline."""
    try:
        import importlib.util

        if importlib.util.find_spec("openwakeword.train") is None:
            raise ImportError("openwakeword.train not found")
    except ImportError:
        print("Error: Local training requires additional dependencies.")
        print("Install with: pip install openwakeword[train]")
        print()
        print("Alternatively, use the Colab method: --method colab")
        sys.exit(1)

    print(f"Training wake word model for: '{target_word}'")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    print("This may take 30-60 minutes depending on your hardware...")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # The actual training API depends on openwakeword version
    # This is a placeholder for the training pipeline
    print("Local training is not yet fully automated.")
    print("Please use the Colab method for now: --method colab")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train a custom wake word model for Jupiter Voice",
        prog="train_wake_word",
    )
    parser.add_argument(
        "--method",
        choices=["colab", "local"],
        default="colab",
        help="Training method (default: colab)",
    )
    parser.add_argument(
        "--target",
        default="hey jupiter",
        help='Target wake word (default: "hey jupiter")',
    )
    args = parser.parse_args()

    if args.method == "colab":
        show_colab_instructions(args.target)
    else:
        train_locally(args.target)


if __name__ == "__main__":
    main()
