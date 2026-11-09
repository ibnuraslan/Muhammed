#!/usr/bin/env python3
"""
sound_design.py - synthesise a horror/suspense sound bed for a project (no audio files needed).

  python3 tools/sound_design.py projects/<slug>

Reads  <project>/timings.txt   (run make_short.py --timings-only first)
       <project>/sound.json    cue list, e.g.
         {"drone": 1.0,
          "heartbeat": {"from": "06", "to": "09", "gain": 0.9},
          "cues": [{"shot": "09", "at": 0.2, "type": "sting"},
                   {"shot": "19", "at": 0.45, "type": "glass"}]}
         cue types: sting, hit, glass, thud, zap, whoosh, shimmer
Writes <project>/music.wav (drone bed, gets ducked under the voice)
       <project>/sfx.wav   (cues + heartbeat, mixed at full level)
"""
import json, re, sys, wave
from pathlib import Path
import numpy as np

SR = 44100
rng = np.random.default_rng(7)

def env(n, a=0.01, d=1.0):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def tone(f, dur, d=1.0, a=0.01, harm=(1,)):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * h * t) / h for h in harm)
    return x * env(n, a, d)

def noise(dur): return rng.standard_normal(int(dur * SR))

def lowpass(x, k):   # one-pole
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc += k * (v - acc); y[i] = acc
    return y

def cue(kind):
    if kind == "sting":       # dissonant cluster + whoosh
        x = sum(tone(f, 2.4, d=0.9, a=0.005, harm=(1, 2, 3)) for f in (110, 116.5, 155.6, 233))
        w = lowpass(noise(1.2), 0.05) * env(int(1.2 * SR), 0.2, 0.35) * 3
        x[:len(w)] += w; return x * 0.22
    if kind == "hit":         # short low impact
        return tone(55, 1.2, d=0.35, a=0.002, harm=(1, 2)) * 0.6 + np.pad(lowpass(noise(0.3), 0.3) * env(int(0.3 * SR), 0.001, 0.06), (0, int(0.9 * SR))) * 0.5
    if kind == "glass":       # bright shatter + tinkles
        n = noise(0.7); hp = np.diff(n, prepend=0) * env(len(n), 0.001, 0.12)
        for _ in range(14):
            s = int(rng.uniform(0.02, 0.6) * SR); tk = tone(rng.uniform(2500, 6000), 0.15, d=0.04)
            hp[s:s + len(tk)] += tk[:len(hp) - s] * 0.5
        return hp * 0.45
    if kind == "thud":        # gavel / door
        n = int(0.5 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * (70 - 30 * t) * t) * env(n, 0.002, 0.12) * 0.8
    if kind == "zap":         # taser buzz
        n = int(0.35 * SR); t = np.arange(n) / SR
        return np.sign(np.sin(2 * np.pi * 120 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t)) * env(n, 0.002, 0.15) * 0.18
    if kind == "whoosh":
        n = int(1.0 * SR); return lowpass(noise(1.0), 0.08) * np.sin(np.linspace(0, np.pi, n)) * 1.2
    if kind == "shimmer":     # glint
        return tone(2637, 0.9, d=0.3, a=0.03) * 0.12 + tone(3520, 0.9, d=0.25, a=0.05) * 0.08
    raise SystemExit(f"unknown cue type {kind}")

def heartbeat(t0, t1, gain):
    out = []; t = t0
    while t < t1:
        k = (t - t0) / max(t1 - t0, 1e-3); gap = 1.05 - 0.45 * k
        out.append((t, gain)); out.append((t + 0.16, gain * 0.7)); t += gap
    beat = tone(52, 0.35, d=0.08, a=0.004, harm=(1, 2)) * 0.9
    return out, beat

def write(path, x):
    x = np.clip(x, -1, 1); st = np.stack([x, x], 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype("<i2").tobytes())

def main():
    proj = Path(sys.argv[1]); txt = (proj / "timings.txt").read_text()
    total = float(re.search(r"TOTAL\s+([\d.]+)s", txt).group(1)) + 1.0
    starts = {m.group(1): float(m.group(2)) for m in re.finditer(r"shot \[(\w+)\] starts\s+([\d.]+)", txt)}
    ids = sorted(starts, key=lambda k: starts[k]); ends = {k: (starts[ids[i + 1]] if i + 1 < len(ids) else total) for i, k in enumerate(ids)}
    cfg = json.loads((proj / "sound.json").read_text())
    N = int(total * SR); t = np.arange(N) / SR
    # drone: brown-ish rumble + two low tones with a slow swell
    rumble = lowpass(rng.standard_normal(N), 0.02); rumble /= np.abs(rumble).max() + 1e-9
    drone = rumble * 0.5 + np.sin(2 * np.pi * 49 * t) * 0.25 + np.sin(2 * np.pi * 73.4 * t + 1) * 0.15
    drone *= (0.75 + 0.25 * np.sin(2 * np.pi * t / 9.0)) * cfg.get("drone", 1.0)
    fade = np.minimum(1, t / 1.5) * np.minimum(1, (total - t) / 1.0)
    write(proj / "music.wav", drone * fade * 0.6)
    sfx = np.zeros(N)
    hb = cfg.get("heartbeat")
    if hb:
        hits, beat = heartbeat(starts[hb["from"]], starts[hb["to"]], hb.get("gain", 0.8))
        for at, g in hits:
            s = int(at * SR); sfx[s:s + len(beat)] += beat[:N - s] * g
    for c in cfg.get("cues", []):
        at = starts[c["shot"]] + c.get("at", 0) * (ends[c["shot"]] - starts[c["shot"]])
        x = cue(c["type"]) * c.get("gain", 1.0); s = int(at * SR)
        sfx[s:s + len(x)] += x[:N - s]
    write(proj / "sfx.wav", sfx * 0.9)
    print(f"wrote {proj/'music.wav'} and {proj/'sfx.wav'} ({total:.1f}s, {len(cfg.get('cues', []))} cues)")

if __name__ == "__main__":
    main()
