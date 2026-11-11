"""Score + sound design for the intro: rain bed, low pulse, phone taps, send whoosh, city swell, title boom.
Usage: intro_score.py out.wav duration "a:0,b:3.4,..." """
import sys, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

out, dur = sys.argv[1], float(sys.argv[2])
T0 = {k: float(v) for k, v in (kv.split(":") for kv in sys.argv[3].split(","))}
SR = 48000; N = int(dur * SR); t = np.arange(N) / SR
rng = np.random.default_rng(21)
lp = lambda x, f: sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)
hp = lambda x, f: sosfilt(butter(2, f, "high", fs=SR, output="sos"), x)
bp = lambda x, a, b: sosfilt(butter(2, [a, b], "band", fs=SR, output="sos"), x)
env = lambda pts: np.interp(t, *zip(*sorted(pts)))


def place(buf, x, at, g=1.0):
    i = int(at * SR); j = min(len(buf), i + len(x))
    if 0 <= i < len(buf):
        buf[i:j] += x[:j - i] * g


mix = np.zeros(N)
# rain: broadband hiss + droplet ticks, loud on the street shots, muffled behind glass in the bedroom
rain = bp(rng.normal(0, 1, N), 800, 9000) * 0.5 + hp(rng.normal(0, 1, N), 4000) * 0.2
ticks = np.zeros(N)
for _ in range(int(dur * 40)):
    n = int(0.004 * SR); place(ticks, rng.normal(0, 1, n) * np.exp(-np.arange(n) / (0.0008 * SR)), rng.uniform(0, dur), rng.uniform(0.1, 0.4))
rain_env = env([(0, 0.15), (T0["c"], 0.15), (T0["c"] + 0.3, 0.05), (T0["e"], 0.25), (T0["f"], 0.6), (T0["h"], 0.45), (T0["i"], 0.15), (T0["j"], 0.55), (dur, 0.0)])
mix += (lp(rain, 3500) * np.where(t < T0["c"], 1, 0) * 0.6 + rain * np.where(t >= T0["c"], 1, 0) + hp(ticks, 2000)) * rain_env * 0.25
# low pulse: 55 Hz heartbeat, every 1.25 s, building toward the title
pulse = np.zeros(N)
k = 0.6
while k < dur - 1:
    n = int(0.5 * SR); tt = np.arange(n) / SR
    place(pulse, np.sin(2 * np.pi * (48 + 20 * np.exp(-tt * 18)) * tt) * np.exp(-tt * 7), k, 1.0)
    place(pulse, np.sin(2 * np.pi * (48 + 20 * np.exp(-tt * 18)) * tt) * np.exp(-tt * 9), k + 0.32, 0.55)
    k += 1.25
mix += pulse * env([(0, 0), (1.0, 0.25), (T0["d"], 0.35), (T0["f"], 0.5), (T0["j"] - 0.2, 0.6), (T0["j"], 0.0), (dur, 0.0)]) * 0.5
# drone pad (D minor) under everything
pad = np.zeros(N)
for f0 in (73.42, 110.0, 146.83, 174.61):
    pad += np.sin(2 * np.pi * f0 * t + 0.3 * np.sin(2 * np.pi * 0.1 * t)) / (1 + f0 / 200)
mix += lp(pad, 900) * env([(0, 0), (2, 0.08), (T0["f"], 0.1), (T0["j"], 0.14), (dur - 0.5, 0.06), (dur, 0)])
# phone: soft keyboard taps while the line types, then the send whoosh
for k in range(30):
    at = T0["a"] + 0.4 + k * 2.0 / 30 + rng.uniform(-0.02, 0.02)
    n = int(0.012 * SR); place(mix, bp(rng.normal(0, 1, n), 2000, 7000) * np.exp(-np.arange(n) / (0.002 * SR)), at, 0.12)
n = int(0.6 * SR); place(mix, bp(rng.normal(0, 1, n), 600, 5000) * np.sin(np.pi * np.arange(n) / n) ** 2, T0["b"] + 0.5, 0.25)
# whoosh/swell into the city, sub hits on the HQ and on the title
def swell(end, d=1.6, g=0.15):
    n = int(d * SR); place(mix, bp(rng.normal(0, 1, n), 300, 6000) * (np.arange(n) / n) ** 2.5, end - d, g)
def boom(at, g=0.7):
    n = int(3 * SR); tt = np.arange(n) / SR
    place(mix, np.sin(2 * np.pi * np.cumsum(32 + 55 * np.exp(-tt * 7)) / SR) * np.exp(-tt * 1.4) + lp(rng.normal(0, 1, n), 600) * np.exp(-tt * 9) * 0.4, at, g)
swell(T0["c"]); boom(T0["d"], 0.35); swell(T0["j"], 2.2, 0.2); boom(T0["j"], 0.8)
# reverb + normalise
ir = rng.normal(0, 1, int(SR * 2.4)) * np.exp(-np.arange(int(SR * 2.4)) / SR * 2.6); ir /= np.sqrt((ir ** 2).sum()) * 5
mix = mix + fftconvolve(mix, ir)[:N] * 0.5
st = np.stack([mix, mix * 0.98 + np.roll(mix, 23) * 0.02], -1)
st *= 0.85 / max(np.abs(st).max(), 1e-6)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print("[intro score]", out)
