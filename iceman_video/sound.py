"""Procedural score: alpine wind, low drone, sub-boom on the title. Usage: sound.py out.wav duration shot_starts_csv"""
import sys, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

out, dur = sys.argv[1], float(sys.argv[2])
starts = [float(x) for x in sys.argv[3].split(",")]
SR = 48000
n = int(SR * dur)
t = np.arange(n) / SR
rng = np.random.default_rng(7)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def env_lin(points):
    """points: list of (time, gain); linear interpolation."""
    ts, gs = zip(*points)
    return np.interp(t, ts, gs)


def smooth_noise(rate, seed):
    r = np.random.default_rng(seed)
    k = int(dur * rate) + 4
    v = r.random(k)
    x = np.linspace(0, k - 3, n)
    i = x.astype(int); f = x - i
    f = f * f * (3 - 2 * f)
    return v[i] * (1 - f) + v[i + 1] * f


# --- wind: two decorrelated noise beds whose band centre and level follow slow gusts
def wind(seed):
    w = np.random.default_rng(seed).normal(0, 1, n)
    gust = smooth_noise(0.35, seed + 1) * 0.7 + smooth_noise(1.3, seed + 2) * 0.3
    low = bp(w, 80, 500) * (0.6 + 0.8 * gust)
    whistle = bp(w, 700, 1800, 2) * (gust ** 3) * 0.35
    return low + whistle

L = wind(1); R = wind(11)
# storm shot gets more wind, macro/title less
s3, s4, s5 = starts[2], starts[3], starts[4]
wind_env = env_lin([(0, 0.0), (1.5, 0.55), (starts[1], 0.45), (s3, 0.5), (s3 + 0.6, 1.0), (s4 - 0.2, 0.9),
                    (s4 + 0.6, 0.35), (s5, 0.3), (dur - 3, 0.25), (dur, 0.0)])
L *= wind_env; R *= wind_env

# --- drone: low fifths with slow beating, filtered saws for body
def saw(f):
    ph = np.cumsum(f / SR)
    return 2 * (ph % 1) - 1
vib = 1 + 0.002 * np.sin(2 * np.pi * 0.11 * t)
drone = np.zeros(n)
for f0, g in ((55.0, 1.0), (82.41, 0.55), (110.0, 0.35), (164.81, 0.12)):
    drone += g * (lp(saw(f0 * vib), 380) + 0.6 * np.sin(2 * np.pi * f0 * 0.5 * t))
drone_env = env_lin([(0, 0), (4, 0.6), (starts[1], 0.7), (s3, 0.55), (s4, 0.8), (s5 - 0.1, 0.9), (s5 + 0.05, 0.25),
                     (s5 + 2.5, 0.6), (dur - 2.5, 0.5), (dur, 0)])
drone *= drone_env * 0.16

# --- high glassy pad on the axe shot (bowed-glass feel)
pad = np.zeros(n)
for f0 in (659.26, 987.77, 1318.5):
    pad += np.sin(2 * np.pi * f0 * t + 2 * np.sin(2 * np.pi * 0.3 * t))
pad *= env_lin([(0, 0), (s4, 0), (s4 + 1.5, 0.03), (s5, 0.02), (s5 + 3, 0.0), (dur, 0)])

# --- sub boom + reverb tail on the title cut
boom = np.zeros(n)
i0 = int(s5 * SR)
m = int(SR * 4)
tt = np.arange(m) / SR
f = 32 + 55 * np.exp(-tt * 6)
b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.4)
b += lp(np.random.default_rng(3).normal(0, 1, m), 900) * np.exp(-tt * 9) * 0.5
end = min(n, i0 + m)
boom[i0:end] = b[:end - i0] * 0.75

# --- a soft riser into the title
rise = bp(rng.normal(0, 1, n), 400, 6000) * env_lin([(0, 0), (s5 - 2.5, 0), (s5 - 0.05, 0.18), (s5, 0), (dur, 0)])

mixL = L * 0.22 + drone + pad + boom + rise
mixR = R * 0.22 + drone * 0.97 + pad * 0.9 + boom + rise * 0.9

# --- simple convolution reverb (exponentially decaying noise) for space
ir_n = int(SR * 2.2)
ir = np.random.default_rng(5).normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 3.0)
ir /= np.abs(ir).sum() ** 0.5 * 30
wetL = fftconvolve(mixL, ir)[:n]; wetR = fftconvolve(mixR, ir[::-1].copy() * 0 + np.roll(ir, 37))[:n]
mixL = mixL + wetL * 0.5; mixR = mixR + wetR * 0.5

st = np.stack([mixL, mixR], -1)
st /= np.max(np.abs(st)) / 0.89
pcm = (st * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("[sound]", out, f"{dur:.1f}s")
