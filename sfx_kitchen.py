#!/usr/bin/env python3
"""sfx-kitchen: procedural sound effect synthesizer with zero dependencies.

Generates WAV files from basic waveforms (sine, square, sawtooth, noise)
with ADSR envelopes and frequency sweeps. Built for placeholder game SFX
when you don't have a sample library yet and your mouth isn't a synthesizer.

Usage:
    python3 sfx_kitchen.py --list
    python3 sfx_kitchen.py jump -o jump.wav
    python3 sfx_kitchen.py --waveform sine --sweep 200,600 --dur 0.15 -o blip.wav
    python3 sfx_kitchen.py --waveform noise --sweep 80,30 --dur 0.5 --release 0.3 -o boom.wav
"""

import argparse
import math
import random
import struct
import sys
import wave

SR = 44100  # sample rate


def _sweep_freqs(f0, f1, n):
    """Linear frequency sweep from f0 to f1 over n samples."""
    for i in range(n):
        yield f0 + (f1 - f0) * (i / max(n, 1))


def gen_sweep(waveform, f0, f1, dur, sr=SR):
    """Generate a frequency-sweeping waveform using a phase accumulator."""
    n = int(dur * sr)
    phase = 0.0
    out = []
    freqs = list(_sweep_freqs(f0, f1, n))
    for i, f in enumerate(freqs):
        phase += 2.0 * math.pi * f / sr
        if waveform == "sine":
            out.append(math.sin(phase))
        elif waveform == "square":
            out.append(1.0 if math.sin(phase) >= 0.0 else -1.0)
        elif waveform == "sawtooth":
            p = phase % (2.0 * math.pi)
            out.append(p / math.pi - 1.0)
        elif waveform == "noise":
            hold = max(1, int(sr / max(f, 1)))
            if i % hold == 0:
                out.append(random.uniform(-1.0, 1.0))
            else:
                out.append(out[-1] if out else 0.0)
        else:
            out.append(0.0)
    return out


def gen_noise(dur, sr=SR):
    n = int(dur * sr)
    random.seed(42)
    return [random.uniform(-1.0, 1.0) for _ in range(n)]


def apply_adsr(samples, attack, decay, sustain, release, sr=SR):
    """Apply an ADSR envelope to a list of samples."""
    n = len(samples)
    a = int(attack * sr)
    d = int(decay * sr)
    r = int(release * sr)
    s = max(0, n - a - d - r)

    env = []
    # Attack: 0 -> 1
    env.extend(i / max(a, 1) for i in range(a))
    # Decay: 1 -> sustain
    env.extend(1.0 - (1.0 - sustain) * (i / max(d, 1)) for i in range(d))
    # Sustain: hold
    env.extend([sustain] * s)
    # Release: sustain -> 0
    env.extend(sustain * (1.0 - i / max(r, 1)) for i in range(r))

    # Pad or truncate to match sample length
    env = env[:n]
    while len(env) < n:
        env.append(0.0)

    return [sample * e for sample, e in zip(samples, env)]


def normalize(samples, target=0.8):
    if not samples:
        return samples
    peak = max(abs(s) for s in samples) or 1.0
    return [s * target / peak for s in samples]


def save_wav(samples, filename, sr=SR):
    """Write 16-bit mono WAV."""
    samples = normalize(samples)
    int_data = [max(-32768, min(32767, int(s * 32767))) for s in samples]
    packed = struct.pack("<" + "h" * len(int_data), *int_data)
    with wave.open(filename, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(packed)


# --- Presets ---

PRESETS = {
    "jump":      {"wave": "sine",     "f0": 200,  "f1": 600,  "dur": 0.15, "a": 0.005, "d": 0.05, "s": 0.6, "r": 0.08},
    "coin":      {"wave": "square",   "f0": 988,  "f1": 1319, "dur": 0.12, "a": 0.005, "d": 0.03, "s": 0.7, "r": 0.07},
    "explosion": {"wave": "noise",    "f0": 80,   "f1": 30,   "dur": 0.50, "a": 0.01,  "d": 0.15, "s": 0.4, "r": 0.30},
    "laser":     {"wave": "sawtooth", "f0": 1200, "f1": 150,  "dur": 0.30, "a": 0.002, "d": 0.10, "s": 0.3, "r": 0.15},
    "step":      {"wave": "noise",    "f0": 200,  "f1": 100,  "dur": 0.08, "a": 0.001, "d": 0.02, "s": 0.3, "r": 0.05},
    "hurt":      {"wave": "square",   "f0": 400,  "f1": 100,  "dur": 0.25, "a": 0.005, "d": 0.08, "s": 0.5, "r": 0.12},
    "powerup":   {"wave": "sine",     "f0": 300,  "f1": 1200, "dur": 0.30, "a": 0.01,  "d": 0.05, "s": 0.8, "r": 0.10},
}


def gen_preset(name):
    p = PRESETS[name]
    if p["wave"] == "noise" and p["f0"] == p["f1"]:
        samples = gen_noise(p["dur"])
    else:
        samples = gen_sweep(p["wave"], p["f0"], p["f1"], p["dur"])
    return apply_adsr(samples, p["a"], p["d"], p["s"], p["r"])


# --- CLI ---

def main():
    ap = argparse.ArgumentParser(
        description="sfx-kitchen: zero-dependency procedural SFX synthesizer"
    )
    ap.add_argument("preset", nargs="?", help="preset name (see --list)")
    ap.add_argument("-o", "--out", default="sfx.wav", help="output WAV file")
    ap.add_argument("--list", action="store_true", help="list available presets")
    ap.add_argument("--waveform", choices=["sine", "square", "sawtooth", "noise"],
                    default="sine", help="waveform type (default: sine)")
    ap.add_argument("--freq", type=float, default=440.0, help="frequency in Hz (no sweep)")
    ap.add_argument("--sweep", help="frequency sweep: start,end in Hz (e.g. 200,600)")
    ap.add_argument("--dur", type=float, default=0.3, help="duration in seconds (default: 0.3)")
    ap.add_argument("--attack", type=float, default=0.01, help="attack time in seconds")
    ap.add_argument("--decay", type=float, default=0.1, help="decay time in seconds")
    ap.add_argument("--sustain", type=float, default=0.7, help="sustain level (0.0-1.0)")
    ap.add_argument("--release", type=float, default=0.1, help="release time in seconds")
    args = ap.parse_args()

    if args.list:
        print("Presets:")
        for name, p in PRESETS.items():
            print(f"  {name:12s} {p['wave']:8s} {p['f0']:>5.0f}->{p['f1']:<5.0f}Hz  {p['dur']:.2f}s")
        return

    if args.preset:
        if args.preset not in PRESETS:
            print(f"Unknown preset '{args.preset}'. Try: {', '.join(PRESETS)}", file=sys.stderr)
            sys.exit(1)
        samples = gen_preset(args.preset)
        label = f"preset={args.preset}"
    else:
        f0 = f1 = args.freq
        if args.sweep:
            parts = args.sweep.split(",")
            f0 = float(parts[0])
            f1 = float(parts[1])
        if args.waveform == "noise" and f0 == f1:
            samples = gen_noise(args.dur)
        else:
            samples = gen_sweep(args.waveform, f0, f1, args.dur)
        samples = apply_adsr(samples, args.attack, args.decay, args.sustain, args.release)
        label = f"wave={args.waveform} {f0:.0f}->{f1:.0f}Hz"

    save_wav(samples, args.out)
    print(f"Generated {args.out} ({len(samples)} samples, {len(samples)/SR:.2f}s, {label})")


if __name__ == "__main__":
    main()
