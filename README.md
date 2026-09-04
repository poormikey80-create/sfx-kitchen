# sfx-kitchen

Procedural sound effect synthesizer in pure Python. Zero dependencies — just
the standard library. Generates WAV files from basic waveforms (sine, square,
sawtooth, noise) with ADSR envelopes and frequency sweeps.

This exists because I make all my placeholder SFX with my own mouth in
Audacity, and while that has a certain charm, sometimes I need something that
is not my mouth making explosion noises at 1am.

## Install

No install. It is one file.

```bash
python3 sfx_kitchen.py --list
python3 sfx_kitchen.py jump -o jump.wav
python3 sfx_kitchen.py coin -o coin.wav
python3 sfx_kitchen.py explosion -o boom.wav
```

## Presets

| Name | Waveform | Sweep | Duration | Description |
|------|----------|-------|----------|-------------|
| jump | sine | 200→600 Hz | 0.15s | Short upward blip |
| coin | square | 988→1319 Hz | 0.12s | Two-tone pickup |
| explosion | noise | 80→30 Hz | 0.50s | Low rumble |
| laser | sawtooth | 1200→150 Hz | 0.30s | Descending sci-fi shot |
| step | noise | 200→100 Hz | 0.08s | Soft footstep |
| hurt | square | 400→100 Hz | 0.25s | Damage taken |
| powerup | sine | 300→1200 Hz | 0.30s | Rising sweep |

## Custom

```bash
# Simple tone
python3 sfx_kitchen.py --waveform sine --freq 440 --dur 0.3 -o tone.wav

# Frequency sweep
python3 sfx_kitchen.py --waveform square --sweep 800,200 --dur 0.2 -o drop.wav

# Full ADSR control
python3 sfx_kitchen.py --waveform sawtooth --sweep 200,50 --dur 0.5 \
  --attack 0.01 --decay 0.1 --sustain 0.5 --release 0.2 -o rumble.wav
```

## How it works

- **Waveforms**: sine, square, sawtooth, and noise generated sample-by-sample
  using a phase accumulator for smooth frequency sweeps.
- **ADSR**: attack-decay-sustain-release envelope applied per-sample. Defaults
  are short and punchy because games are not symphonies.
- **Noise**: pseudo-random with a fixed seed (42), so the same preset always
  sounds the same. Reproducibility matters more than entropy here.
- **Output**: 16-bit mono WAV at 44100 Hz. Godot imports it natively, no
  conversion needed.

## License

MIT. Use the code in your game, no credit needed.
