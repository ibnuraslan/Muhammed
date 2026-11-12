"""Sound building blocks copied from nvidia_doc/edit/sound_design.py (that file runs its whole mix on import):
filters, pink noise, envelopes, reverb, ambience beds, pad chords, bells, booms, swells, the sting and soft spot effects."""
import os, subprocess, tempfile
import numpy as np
from scipy import signal
SR = 48000
FPS = 24
rng = np.random.default_rng(42)


def db(x):
    return 10 ** (x / 20)


def sos(kind, fc, order=2):
    return signal.butter(order, fc, btype=kind, fs=SR, output="sos")


def filt(x, kind, fc, order=2):
    return signal.sosfiltfilt(sos(kind, fc, order), x) if len(x) > 30 else x


def pink(n):
    w = rng.standard_normal(n)
    X = np.fft.rfft(w); f = np.fft.rfftfreq(n, 1 / SR); f[0] = f[1]
    X /= np.sqrt(f)
    y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)


def env_ad(n, a, d, sustain=None):
    t = np.arange(n) / SR
    up = np.clip(t / max(a, 1e-3), 0, 1) ** 2 * (3 - 2 * np.clip(t / max(a, 1e-3), 0, 1))   # smoothstep attack
    return up * np.exp(-np.maximum(t - a, 0) / d)


def fade_edges(x, fi, fo):
    n = len(x); e = np.ones(n)
    a, b = int(fi * SR), int(fo * SR)
    if a: e[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if b: e[-b:] = np.cos(np.linspace(0, np.pi / 2, b)) ** 2
    return x * e


def lfo(n, rate, depth, phase=0.0):
    t = np.arange(n) / SR
    return 1 - depth * 0.5 * (1 + np.sin(2 * np.pi * rate * t + phase))


IR = None
def reverb(x, wet=0.35, length=3.2):
    global IR
    if IR is None:
        n = int(length * SR); t = np.arange(n) / SR
        ir = rng.standard_normal(n) * np.exp(-t / (length / 6.5))
        ir = filt(ir, "lowpass", 4500); ir[:int(0.012 * SR)] = 0; IR = ir / np.sqrt((ir ** 2).sum())
    y = signal.fftconvolve(x, IR)[:len(x)]
    return (1 - wet) * x + wet * y * 0.9


def place(buf, x, t0):
    i = int(round(t0 * SR))
    if i >= len(buf): return
    j = min(len(buf), i + len(x)); buf[i:j] += x[:j - i]


# ---------------------------------------------------------------------------------------------------- ambience
def amb(kind, dur):
    n = int(dur * SR)
    if n <= 0: return np.zeros(0)
    if kind == "room":
        return filt(pink(n), "lowpass", 220) * db(-42)
    if kind == "night":
        return filt(pink(n), "lowpass", 180) * db(-46)
    if kind == "city":
        return filt(pink(n), "lowpass", 380) * lfo(n, 0.07, 0.4) * db(-38) + amb("room", dur) * 0.5
    if kind == "wind":
        w = filt(filt(pink(n), "lowpass", 650), "highpass", 60) * lfo(n, 0.09, 0.6, rng.uniform(0, 6))
        return w * db(-37) + filt(pink(n), "lowpass", 300) * db(-44)
    if kind == "rain":
        hiss = filt(filt(pink(n), "highpass", 700), "lowpass", 5200) * db(-40)
        body = filt(filt(pink(n), "highpass", 150), "lowpass", 1400) * db(-38)
        return hiss + body
    if kind == "hall":
        t = np.arange(n) / SR
        hum = (np.sin(2 * np.pi * 110 * t) + 0.4 * np.sin(2 * np.pi * 220 * t)) * db(-52)
        fans = filt(filt(pink(n), "highpass", 900), "lowpass", 3500) * db(-47)
        return filt(pink(n), "lowpass", 260) * db(-38) + hum + fans
    if kind == "water":
        lap = filt(pink(n), "lowpass", 600) * lfo(n, 0.28, 0.7) * db(-37)
        return lap + amb("wind", dur) * 0.7
    if kind == "crowd":
        base = filt(filt(pink(n), "highpass", 250), "lowpass", 1800)
        mod = filt(np.abs(rng.standard_normal(n)), "lowpass", 4) ; mod = mod / (mod.max() + 1e-9)
        return base * (0.55 + 0.45 * mod) * db(-41) + amb("room", dur)
    if kind == "press":
        t = np.arange(n) / SR; out = filt(pink(n), "lowpass", 400) * db(-40)
        k = np.zeros(n)
        for t0 in np.arange(0.2, dur, 0.55):
            seg = int(0.25 * SR); i = int(t0 * SR)
            if i + seg < n:
                tt = np.arange(seg) / SR
                k[i:i + seg] += np.sin(2 * np.pi * 62 * tt) * env_ad(seg, 0.004, 0.07)
        return out + filt(k, "lowpass", 300) * db(-30)
    return amb("room", dur)


def amb_for(name):
    for key, kind in (("seldom", None), ("home_", "city"), ("invest", "room"), ("street", "rain"), ("cafe", "rain"),
                      ("capitol", "wind"), ("signing", "room"), ("dchall", "hall"), ("remote", "night"), ("port", "water"),
                      ("city", "city"), ("corp", "city"), ("police", "rain"), ("office_door", "room"), ("computex", "crowd"),
                      ("restaurant", "crowd"), ("press", "press"), ("warehouse", "hall"), ("courtroom", "room"),
                      ("courthouse", "wind"), ("doors", "room")):
        if key in name:
            return kind
    return "room"


# ---------------------------------------------------------------------------------------------------- score
NOTE = {"C": -9, "C#": -8, "D": -7, "Eb": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "Ab": -1, "A": 0, "Bb": 1, "B": 2}
def hz(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave - 4)) / 12)


def pad_voice(f, dur, bright=1100):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for det in (-0.004, 0.0, 0.0045):
        ff = f * (1 + det)
        for h, a in ((1, 1.0), (2, 0.35), (3, 0.18), (4, 0.08)):
            y += a * np.sin(2 * np.pi * ff * h * t + rng.uniform(0, 6.28))
    y = filt(y, "lowpass", bright)
    return y / 3.5


def chord(names, dur, bright=1100, sub=True):
    n = int(dur * SR); y = np.zeros(n)
    for nm, octv in names:
        y += pad_voice(hz(nm, octv), dur, bright)
    if sub:
        t = np.arange(n) / SR; y += 0.9 * np.sin(2 * np.pi * hz(names[0][0], 1) * t)
    return fade_edges(y, min(2.5, dur / 3), min(2.5, dur / 3))


def bell(f, dur=3.0):
    n = int(dur * SR); t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2.01 * f * t) * np.exp(-t * 1.5) +
         0.12 * np.sin(2 * np.pi * 3.0 * f * t) * np.exp(-t * 3))
    return y * env_ad(n, 0.006, 1.1)


def score_section(t0, t1, prog, motif, pulse=False, level=-20, bright=1100):
    dur = t1 - t0; out = np.zeros(int(dur * SR) + SR)
    step = 7.0; k = 0; t = 0.0
    while t < dur:
        c = prog[k % len(prog)]; L = min(step + 2.5, dur - t + 2.5)
        place(out, chord(c, L, bright), t); t += step; k += 1
    # sparse bell motif every ~14 s
    for i, tt in enumerate(np.arange(4.0, dur - 3, 14.0)):
        for j, (nm, o) in enumerate(motif):
            place(out, bell(hz(nm, o)) * 0.35, tt + j * 0.62)
    if pulse:                                      # a soft low heartbeat: lub-dub every 1.6 s
        for tt in np.arange(1.0, dur - 1, 1.6):
            for dt, a in ((0.0, 1.0), (0.24, 0.6)):
                seg = int(0.35 * SR); x = np.arange(seg) / SR
                place(out, np.sin(2 * np.pi * 52 * x) * env_ad(seg, 0.01, 0.09) * a * 0.55, tt + dt)
    out = filt(out, "highpass", 28)
    out = reverb(out, 0.42)
    out = fade_edges(out[:int(dur * SR)], 2.0, 2.5)
    return out / (np.abs(out).max() + 1e-9) * db(level)


def boom(level=-10):
    d = 3.2; n = int(d * SR); t = np.arange(n) / SR
    f = 48 * np.exp(-t * 0.25)                     # gentle downward glide
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * env_ad(n, 0.02, 0.9) + 0.25 * np.sin(2 * ph) * env_ad(n, 0.02, 0.4)
    y += filt(rng.standard_normal(n), "lowpass", 180) * env_ad(n, 0.015, 0.25) * 0.25
    return reverb(y, 0.3) * db(level)


def swell(d=2.2, level=-22):
    n = int(d * SR); t = np.arange(n) / SR
    y = pad_voice(hz("D", 3), d, 1600) + pad_voice(hz("A", 3), d, 1600)
    air = filt(pink(n), "bandpass", [250, 2200]) * 0.25
    e = (t / d) ** 2.2
    return (y + air) * e * db(level)


# ---------------------------------------------------------------------------------------------------- sting (6 s)
def sting():
    d = 6.0; n = int(d * SR); out = np.zeros(n); t = np.arange(n) / SR
    out += filt(pink(n), "lowpass", 200) * db(-40)                                   # quiet room
    out += (np.sin(2 * np.pi * 100 * t) * 0.6 + np.sin(2 * np.pi * 200 * t) * 0.25) * db(-44) * lfo(n, 0.5, 0.2)   # tube hum
    w = int(1.1 * SR)                                                                # whoosh as the bag falls (0.6-1.4 s)
    wn = filt(pink(w), "bandpass", [300, 1800]) * np.sin(np.linspace(0, np.pi, w)) ** 2
    place(out, wn * db(-24), 0.35)
    imp = int(2.5 * SR); x = np.arange(imp) / SR                                     # warm impact at 1.4 s
    hit = np.sin(2 * np.pi * 50 * np.exp(-x * 0.3) * x) * env_ad(imp, 0.006, 0.45)
    hit += filt(rng.standard_normal(imp), "lowpass", 260) * env_ad(imp, 0.004, 0.08) * 0.35
    place(out, reverb(hit, 0.35) * db(-9), 1.4)
    pr = int(0.7 * SR)                                                               # paper settling, soft
    pap = filt(rng.standard_normal(pr), "bandpass", [1500, 5000]) * env_ad(pr, 0.03, 0.18)
    place(out, pap * db(-34), 1.45)
    # the logo lights at 2.4 s: a warm minor chord blooms (gentle flutter instead of a buzz) + a soft bell
    c = chord([("D", 2), ("A", 2), ("D", 3), ("F", 3)], 3.6, bright=1500, sub=True)
    flutter = 1 - 0.25 * np.exp(-np.arange(len(c)) / SR / 0.35) * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * np.arange(len(c)) / SR))
    place(out, reverb(c * flutter, 0.4) * db(-17), 2.4)
    place(out, reverb(bell(hz("D", 5), 3.0), 0.5) * db(-24), 2.45)
    place(out, boom(-14), 2.4)
    out = fade_edges(out, 0.25, 1.6)
    return out


class Snd(np.ndarray):
    """Audio snippets that can be added even when their lengths differ (shorter one is zero-padded)."""
    __array_priority__ = 1000
    def _pad(a, b):
        a = np.asarray(a); b = np.asarray(b)
        if a.ndim == 0 or b.ndim == 0 or len(a) == len(b): return a, b
        n = max(len(a), len(b)); A = np.zeros(n); B = np.zeros(n); A[:len(a)] = a; B[:len(b)] = b; return A, B
    def __add__(self, o):
        a, b = Snd._pad(self, o); return (a + b).view(Snd)
    __radd__ = __add__
def S_(x): return np.asarray(x).view(Snd)

# ---------------------------------------------------------------------------------------------------- spot effects
# all smooth: raised-cosine attacks (no clicks), filtered noise only in short soft bursts, tonal where possible
def _n(d): return int(d * SR)
def soft_env(n, a=0.004, d=0.05):
    return env_ad(n, a, d)
def _thump(f=60, d=0.6, decay=0.12, glide=0.25):
    n = _n(d); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f * np.exp(-t * glide)) / SR
    return np.sin(ph) * soft_env(n, 0.005, decay)
def _tap(d=0.12, lo=900, hi=3200, decay=0.025):
    n = _n(d); return filt(rng.standard_normal(n), "bandpass", [lo, hi]) * soft_env(n, 0.002, decay)
def _paper(d=0.45, decay=0.14):
    n = _n(d); return filt(filt(rng.standard_normal(n), "bandpass", [1400, 6500]), "lowpass", 7000) * soft_env(n, 0.02, decay)
def _slide(d=0.8, lo=250, hi=1800):
    n = _n(d); return filt(pink(n), "bandpass", [lo, hi]) * np.sin(np.linspace(0, np.pi, n)) ** 2
def _clank(f0=170, d=1.6):
    n = _n(d); t = np.arange(n) / SR; y = np.zeros(n)
    for r, a, dec in ((1, 1, 0.5), (2.76, 0.5, 0.3), (5.4, 0.25, 0.18), (8.9, 0.1, 0.1)):
        y += a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t / dec)
    return y * soft_env(n, 0.003, 3.0) * 0.5
def _horn(f=98, d=3.2):
    n = _n(d); t = np.arange(n) / SR; y = sum(np.sin(2 * np.pi * f * h * t) / h for h in range(1, 7))
    return filt(y, "lowpass", 800) * fade_edges(np.ones(n), 0.6, 1.2) * 0.4
def _beep(f=1000, d=0.22):
    n = _n(d); t = np.arange(n) / SR; return np.sin(2 * np.pi * f * t) * fade_edges(np.ones(n), 0.012, 0.05) * 0.5
def _glass(f=2400, d=1.2):
    n = _n(d); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.32 * t)) * soft_env(n, 0.002, 0.35) * 0.4
def _car_pass(d=3.0, peak=0.5):
    n = _n(d); t = np.arange(n) / SR
    bell_ = np.exp(-((t / d - peak) / 0.18) ** 2)
    y = filt(pink(n), "lowpass", 2200) * bell_ + filt(pink(n), "bandpass", [80, 400]) * bell_ * 0.8
    return y
def _chirp(d=0.09, f1=3600, f2=4400):
    n = _n(d); t = np.arange(n) / SR; f = np.linspace(f1, f2, n)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.linspace(0, np.pi, n)) ** 2 * 0.4
def _steps(d, every=0.55, f=95, lvl=1.0):
    out = np.zeros(_n(d))
    for k, tt in enumerate(np.arange(0.1, d - 0.2, every)):
        x = thump(f + 8 * (k % 2), 0.18, 0.04, 0) * 0.8 + tap(0.1, 700, 2600, 0.02) * 0.35
        i = _n(tt); out[i:i + len(x)] += x[:len(out) - i]
    return out * lvl
def _club(d, bpm=118):
    out = np.zeros(_n(d)); beat = 60 / bpm
    for tt in np.arange(0, d - 0.3, beat):
        x = thump(55, 0.3, 0.09, 0.4); i = _n(tt); out[i:i + len(x)] += x[:len(out) - i]
    return filt(out, "lowpass", 140)

thump = lambda *a, **k: S_(_thump(*a, **k))
tap = lambda *a, **k: S_(_tap(*a, **k))
paper = lambda *a, **k: S_(_paper(*a, **k))
slide = lambda *a, **k: S_(_slide(*a, **k))
clank = lambda *a, **k: S_(_clank(*a, **k))
horn = lambda *a, **k: S_(_horn(*a, **k))
beep = lambda *a, **k: S_(_beep(*a, **k))
glass = lambda *a, **k: S_(_glass(*a, **k))
car_pass = lambda *a, **k: S_(_car_pass(*a, **k))
chirp = lambda *a, **k: S_(_chirp(*a, **k))
steps = lambda *a, **k: S_(_steps(*a, **k))
club = lambda *a, **k: S_(_club(*a, **k))

