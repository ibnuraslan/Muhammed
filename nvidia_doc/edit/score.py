"""Original synthesized score + sound design, mixed under the voiceover with ducking.
Usage: python edit/score.py out/mix.wav     (reads edit/timeline.json; uses the VO it names, if any)

Score (D minor, 72 bpm): sub drone, pad chords (Dm-Bb-F-C), a muted ostinato in chapters 1-2, a clock tick
under the memo, glassy pings; hits + reverse swells into cards; the music falls away for the final question.
Sound design: typewriter clicks on typed quotes, stamp thumps, map whooshes, doors closing.
"""
import os, sys, json, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from beats import BEATS

SR = 48000
BEAT = {b["id"]: b for b in BEATS}
tl = json.load(open(os.path.join(HERE, "timeline.json")))
SPAN = {b["id"]: (b["start"], b["end"]) for b in tl["beats"]}
DUR = tl["beats"][-1]["end"] + 1.0
N = int(DUR * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(11)


def lp(x, f, o=2): return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], "band", fs=SR, output="sos"), x)


def env_points(pts):
    ts, gs = zip(*sorted(pts))
    return np.interp(t, ts, gs)


def note(f, dur, kind="pad"):
    n = int(dur * SR); tt = np.arange(n) / SR
    if kind == "pluck":
        x = sum(np.sin(2 * np.pi * f * k * tt) / k ** 1.5 for k in range(1, 6)) * np.exp(-tt * 3.2)
    elif kind == "ping":
        x = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 2.0)
    else:
        x = sum(np.sin(2 * np.pi * f * k * tt + rng.uniform(0, 6)) / k for k in (1, 2, 3)) * np.minimum(1, tt / 1.5) * np.minimum(1, (dur - tt) / 1.5)
    return x


def place(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    j = min(len(buf), i + len(x)); buf[max(i, 0):j] += x[max(0, -i):j - i] * gain


hz = lambda m: 440 * 2 ** ((m - 69) / 12)
first_ch = lambda c: next(b["id"] for b in BEATS if b.get("ch") == c)
T_TITLE = SPAN["o07"][0]; T_C1 = SPAN[first_ch("1")][0]; T_C2 = SPAN[first_ch("2")][0]; T_C3 = SPAN[first_ch("3")][0]
T_FINAL = SPAN["c3_18"][0]; T_END = SPAN["end"][0]

# ------------------------------------------------------------------ drone (D1 + A1), slow filter breathing
saw = lambda f: 2 * ((np.cumsum(np.full(N, f) / SR)) % 1) - 1
drone = lp(saw(hz(26)) + 0.7 * saw(hz(33)) + 0.5 * np.sin(2 * np.pi * hz(14) * t), 220)
drone *= 0.55 + 0.45 * np.sin(2 * np.pi * t / 23.0)
drone_env = env_points([(0, 0), (2, 0.6), (T_FINAL, 0.7), (T_FINAL + 0.4, 0.15), (T_END + 2, 0.12), (DUR, 0)])
music = drone * drone_env * 0.22

# ------------------------------------------------------------------ pad chords, 8 bars each (bar = 4 beats at 72 bpm)
bar = 4 * 60 / 72
prog = [[50, 53, 57, 62], [46, 50, 53, 58], [53, 57, 60, 65], [48, 52, 55, 60]]   # Dm Bb F C (midi)
pad = np.zeros(N)
k = 0; tt0 = 4.0
while tt0 < T_FINAL:
    for m in prog[k % 4]:
        place(pad, note(hz(m), bar * 2 + 1.5), tt0, 0.05)
    tt0 += bar * 2; k += 1
pad = lp(pad, 1800)
pad_env = env_points([(0, 0), (6, 0.9), (T_C1, 0.6), (T_C2, 0.8), (T_C3, 0.9), (T_FINAL, 0.9), (T_FINAL + 0.5, 0), (DUR, 0)])
music += pad * pad_env

# ------------------------------------------------------------------ ostinato (chapters 1-2): muted plucks on 8ths
ost = np.zeros(N); patt = [38, 38, 41, 38, 36, 38, 45, 41]
q = 60 / 72 / 2
tt0 = T_C1 + 3.5; j = 0
while tt0 < T_C3:
    place(ost, note(hz(patt[j % 8] + 12), 0.5, "pluck"), tt0, 0.10 * (0.7 + 0.3 * (j % 2 == 0)))
    tt0 += q; j += 1
ost = lp(ost, 1400)
music += ost * env_points([(0, 0), (T_C1 + 3, 0), (T_C1 + 10, 1), (T_C2 - 1, 1), (T_C2, 0.3), (T_C2 + 20, 0.7), (T_C3 - 0.5, 0.7), (T_C3, 0), (DUR, 0)])

# ------------------------------------------------------------------ clock tick under the memo (chapter 2, memo beats)
tick = np.zeros(N)
m0, m1 = SPAN["c2_09"][0], SPAN["c2_12"][1]
tt0 = m0
while tt0 < m1:
    c = hp(rng.normal(0, 1, int(0.012 * SR)), 3000) * np.exp(-np.arange(int(0.012 * SR)) / (0.003 * SR))
    place(tick, c, tt0, 0.18); tt0 += 60 / 72
music += tick

# ------------------------------------------------------------------ sparse glassy pings
for _ in range(int(DUR / 9)):
    at = rng.uniform(5, T_FINAL - 2)
    place(music, note(hz(rng.choice([74, 77, 81, 86])), 3.0, "ping"), at, 0.035)

# ------------------------------------------------------------------ hits + reverse swells into cards; final drop
sfx = np.zeros(N)


def boom(at, g=0.8):
    n = int(SR * 3.5); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-tt * 7)) / SR) * np.exp(-tt * 1.5)
    x += lp(rng.normal(0, 1, n), 700) * np.exp(-tt * 10) * 0.4
    place(sfx, x, at, g)


def swell(end, dur=2.0, g=0.12):
    n = int(SR * dur); x = bp(rng.normal(0, 1, n), 300, 7000) * (np.arange(n) / n) ** 2.5
    place(sfx, x, end - dur, g)


for c in ("o07", first_ch("1"), first_ch("2"), first_ch("3")):
    swell(SPAN[c][0]); boom(SPAN[c][0], 0.85 if c == "o07" else 0.6)
boom(T_FINAL, 0.5)

# typewriter clicks on typed quotes / the final question
def clicks(a, b, rate=14, g=0.07):
    tt0 = a
    while tt0 < b:
        n = int(0.01 * SR); c = bp(rng.normal(0, 1, n), 1500, 6000) * np.exp(-np.arange(n) / (0.002 * SR))
        place(sfx, c, tt0, g * rng.uniform(0.6, 1.0)); tt0 += 1 / rate * rng.uniform(0.6, 1.4)


s, e = SPAN["o01"]; clicks(s + 0.6, s + 0.6 + max(0.8, (e - s) * 0.45))
s, e = SPAN["c3_18"]; clicks(s + 0.3, s + 2.2, 11, 0.05)
# stamp thumps on documents, whooshes on maps
for b in BEATS:
    if b["id"] not in SPAN:
        continue
    s, e = SPAN[b["id"]]
    tpl = b["shot"].get("template")
    if tpl == "document_stamp":
        n = int(0.25 * SR); x = lp(rng.normal(0, 1, n), 400) * np.exp(-np.arange(n) / (0.04 * SR)); place(sfx, x, s + 1.2, 0.5)
    if tpl == "map":
        n = int(0.9 * SR); env = np.sin(np.pi * np.arange(n) / n) ** 2
        place(sfx, bp(rng.normal(0, 1, n), 200, 2500) * env, s - 0.2, 0.06)
    if b["shot"].get("move") == "doors_close":
        n = int(1.4 * SR); x = lp(rng.normal(0, 1, n), 180) * np.exp(-np.arange(n) / (0.25 * SR))
        place(sfx, x, e - 0.8, 0.7)

# ------------------------------------------------------------------ voiceover from the audio EDL
vo = np.zeros(N)
if tl["meta"].get("mode") == "vo" and os.path.exists(tl["meta"]["vo"]):
    import subprocess
    raw = os.path.join(HERE, "..", "vo", "_vo48k.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tl["meta"]["vo"], "-ac", "1", "-ar", str(SR), raw], check=True)
    with wave.open(raw) as w:
        src = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    for a in tl["audio"]:
        if a["kind"] != "vo":
            continue
        seg = src[int(a["src_start"] * SR):int(a["src_end"] * SR)].copy()
        f = min(len(seg), int(0.02 * SR))
        if f:
            seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        place(vo, seg, a["at"], 1.0)
    peak = np.max(np.abs(vo)) or 1
    vo = vo / peak * 0.9

# ------------------------------------------------------------------ mix: reverb on music, duck under VO
ir_n = int(SR * 2.6)
ir = rng.normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 2.4); ir /= np.sqrt((ir ** 2).sum()) * 6
mus = music + fftconvolve(music, ir)[:N] * 0.6
venv = lp(np.abs(vo), 6.0) * 6.0
duck = 1.0 - 0.55 * np.clip(venv, 0, 1)
mix_m = (mus * duck + sfx * (1 - 0.3 * np.clip(venv, 0, 1)))
L = mix_m + vo; R = mix_m * 0.97 + vo
st = np.stack([L, R], -1)
st *= 0.89 / max(np.max(np.abs(st)), 1e-6)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "out", "mix.wav")
os.makedirs(os.path.dirname(out), exist_ok=True)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print("[score]", out, f"{DUR:.1f}s", "with VO" if tl["meta"].get("mode") == "vo" else "music only (estimate timeline)")
