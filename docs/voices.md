# Available Voices

Jupiter Voice uses [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx) for text-to-speech. Kokoro ships with 14 built-in voices.

## Voice List

| Voice ID | Gender | Accent | Description |
|----------|--------|--------|-------------|
| `af_heart` | Female | American | Warm and natural (default) |
| `af_bella` | Female | American | Soft and clear |
| `af_nicole` | Female | American | Bright and expressive |
| `af_sarah` | Female | American | Calm and professional |
| `af_sky` | Female | American | Light and youthful |
| `am_adam` | Male | American | Deep and steady |
| `am_michael` | Male | American | Warm baritone |
| `bf_emma` | Female | British | Clear and articulate |
| `bf_isabella` | Female | British | Elegant and composed |
| `bm_george` | Male | British | Classic and authoritative |
| `bm_lewis` | Male | British | Friendly and natural |
| `af_aoede` | Female | American | Melodic and smooth |
| `af_kore` | Female | American | Crisp and modern |
| `am_echo` | Male | American | Resonant and clear |

> Voice naming convention: `{accent}{gender}_{name}` where `a` = American, `b` = British, `f` = female, `m` = male.

## Changing the Voice

Edit `config.yaml`:

```yaml
tts:
  voice: "am_adam"    # any voice ID from the table above
  speed: 1.0          # 0.5 = slow, 1.0 = normal, 2.0 = fast
```

Or use an environment variable:

```bash
JUPITER_VOICE_TTS_VOICE=bf_emma jupiter-voice
```

## Tips

- **`af_heart`** (the default) is a good all-around choice — natural, warm, and easy to listen to.
- **Male voices** (`am_adam`, `am_michael`, `bm_george`) work well if you prefer a deeper tone.
- **British voices** (`bf_emma`, `bm_george`, `bm_lewis`) have distinct pronunciation differences.
- **Speed:** Adjust `tts.speed` in `config.yaml`. Values between 0.8 and 1.2 sound the most natural.

## Fallback Voice

If Kokoro TTS fails (missing models, espeak-ng not installed), Jupiter Voice falls back to the macOS built-in `say` command using the Samantha voice. This sounds more robotic but ensures you always get spoken responses.

To fix the fallback triggering unexpectedly:
1. Run `bash setup.sh` to re-download models
2. Install espeak-ng: `brew install espeak-ng`
