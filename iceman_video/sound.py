"""Procedural score: alpine wind, lab room tone, fire crackle, low drone, glass pad, sub-boom on the title.
Usage: sound.py out.wav duration "shotname:start,shotname:start,..." """
import sys, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

out, dur = sys.argv[1], float(sys.argv[2])
starts = {}
for kv in sys.argv[3].split(","):
    k, v = kv.split(":"); starts[k] = float(v)
order = sorted(starts, key=starts.get)
ends = {k: (starts[order[i + 1]] if i + 1 < len(order) else dur - 4.0) for i, k in enumerate(order)}
SR = 48000
n = int(SR * dur)
t = np.arange(n) / SR
rng = np.random.default_rng(7)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def smooth_noise(rate, seed):
    r = np.random.default_rng(seed)
    k = int(dur * rate) + 4
    v = r.random(k)
    x = np.linspace(0, k - 3, n)
    i = x.astype(int); f = x - i
    f = f * f * (3 - 2 * f)
    return v[i] * (1 - f) + v[i + 1] * f


def level(per_shot, xf=0.6, tail=0.0):
    """Piecewise level per shot with crossfades; shots missing from the dict are silent."""
    pts = [(0.0, 0.0)]
    for k in order:
        a, b = starts[k], ends[k]
        v = per_shot.get(k, 0.0)
        pts += [(a + xf * 0.5, v), (b - xf * 0.5, v)]
    pts += [(dur - 3.5, tail), (dur, 0.0)]
    ts, gs = zip(*sorted(pts))
    return np.interp(t, ts, gs)


def has(k):
    return k in starts


# --- wind: decorrelated noise beds; band and level follow slow gusts
def wind(seed):
    w = np.random.default_rng(seed).normal(0, 1, n)
    gust = smooth_noise(0.35, seed + 1) * 0.7 + smooth_noise(1.3, seed + 2) * 0.3
    low = bp(w, 80, 500) * (0.6 + 0.8 * gust)
    whistle = bp(w, 700, 1800, 2) * (gust ** 3) * 0.35
    return low + whistle

wl = level({"shot1_peaks": 0.55, "shot2_map": 0.45, "shot7_discovery": 0.55, "shot3_trail": 1.0, "shot9_walk": 1.05,
            "shot8_fire": 0.25, "shot4_axe": 0.35, "shot5_name": 0.3}, tail=0.2)
L = wind(1) * wl; R = wind(11) * wl

# --- lab room tone: mains hum + ventilation hiss
lab = level({"shot6_lab": 1.0})
hum = (np.sin(2 * np.pi * 50 * t) * 0.5 + np.sin(2 * np.pi * 100 * t) * 0.25 + np.sin(2 * np.pi * 150 * t) * 0.08)
hiss = bp(rng.normal(0, 1, n), 300, 4000) * 0.4
room = (hum * 0.05 + hiss * 0.12) * lab

# --- fire: low roar + random crackles/pops
fire = level({"shot8_fire": 1.0}, xf=0.8)
roar = lp(rng.normal(0, 1, n), 260) * (0.7 + 0.3 * smooth_noise(3, 31)) * 0.45
crack = np.zeros(n)
if has("shot8_fire"):
    a, b = int(starts["shot8_fire"] * SR), int(ends["shot8_fire"] * SR)
    for _ in range(int((b - a) / SR * 9)):
        p = rng.integers(a, b); m = int(SR * rng.uniform(0.004, 0.02))
        if p + m < n:
            crack[p:p + m] += rng.normal(0, 1, m) * np.exp(-np.arange(m) / (m / 4)) * rng.uniform(0.3, 1.0)
    crack = bp(crack, 900, 9000) * 0.9
firemix = (roar + crack) * fire

# --- drone: low fifths with slow beating
def saw(f):
    ph = np.cumsum(f / SR)
    return 2 * (ph % 1) - 1
vib = 1 + 0.002 * np.sin(2 * np.pi * 0.11 * t)
drone = np.zeros(n)
for f0, g in ((55.0, 1.0), (82.41, 0.55), (110.0, 0.35), (164.81, 0.12)):
    drone += g * (lp(saw(f0 * vib), 380) + 0.6 * np.sin(2 * np.pi * f0 * 0.5 * t))
dl = level({"shot1_peaks": 0.6, "shot2_map": 0.7, "shot7_discovery": 0.75, "shot6_lab": 0.8, "shot3_trail": 0.55,
            "shot9_walk": 0.65, "shot8_fire": 0.55, "shot4_axe": 0.8, "shot5_name": 0.5}, tail=0.45)
drone *= dl * 0.16

# --- glassy pad on the axe
pad = np.zeros(n)
for f0 in (659.26, 987.77, 1318.5):
    pad += np.sin(2 * np.pi * f0 * t + 2 * np.sin(2 * np.pi * 0.3 * t))
pad *= level({"shot4_axe": 0.03, "shot6_lab": 0.012})

# --- sub boom + riser into the title
boom = np.zeros(n); rise = np.zeros(n)
if has("shot5_name"):
    s5 = starts["shot5_name"]
    i0 = int(s5 * SR); m = int(SR * 4); tt = np.arange(m) / SR
    f = 32 + 55 * np.exp(-tt * 6)
    b_ = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.4)
    b_ += lp(np.random.default_rng(3).normal(0, 1, m), 900) * np.exp(-tt * 9) * 0.5
    e = min(n, i0 + m); boom[i0:e] = b_[:e - i0] * 0.75
    env = np.interp(t, [0, s5 - 2.5, s5 - 0.05, s5, dur], [0, 0, 0.18, 0, 0])
    rise = bp(rng.normal(0, 1, n), 400, 6000) * env
# a softer hit on the discovery cut
if has("shot7_discovery"):
    i0 = int(starts["shot7_discovery"] * SR); m = int(SR * 3); tt = np.arange(m) / SR
    h_ = np.sin(2 * np.pi * np.cumsum(40 + 30 * np.exp(-tt * 5)) / SR) * np.exp(-tt * 1.8) * 0.35
    e = min(n, i0 + m); boom[i0:e] += h_[:e - i0]

mixL = L * 0.22 + room + firemix + drone + pad + boom + rise
mixR = R * 0.22 + room * 0.95 + firemix * 0.9 + drone * 0.97 + pad * 0.9 + boom + rise * 0.9

ir_n = int(SR * 2.2)
ir = np.random.default_rng(5).normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 3.0)
ir /= np.abs(ir).sum() ** 0.5 * 30
wetL = fftconvolve(mixL, ir)[:n]; wetR = fftconvolve(mixR, np.roll(ir, 37))[:n]
mixL = mixL + wetL * 0.5; mixR = mixR + wetR * 0.5

st = np.stack([mixL, mixR], -1)
st /= np.max(np.abs(st)) / 0.89
pcm = (st * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("[sound]", out, f"{dur:.1f}s")
