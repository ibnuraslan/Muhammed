"""Full-film sound design for the Nvidia film: voiceover + soft score bed + per-shot ambience + title hits + logo sting.
Everything is smooth and tonal (no hard clicks, no raw white noise): pads, sub booms, filtered air/rain/room tones,
ducked under the voice.  ->  out/deliver/nvidia_film_AUDIO_v2.wav  (+ an mp3 preview)

  python edit/sound_design.py
"""
import os, json, subprocess, tempfile
import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ND = os.path.abspath(os.path.join(HERE, ".."))
SR = 48000
FPS = 24
rng = np.random.default_rng(42)
def build_edl():
    """The exact timeline of the film uploaded to the farm (exported from nvidia_film.blend)."""
    old = json.load(open(os.path.join(HERE, "film_edl.json")))
    if os.environ.get("FROM_EDL", "1") == "1":
        return old
    shots = [s for s in old["shots"] if not s[2].startswith("c1_") and not s[2].startswith("c2_") and not s[2].startswith("c3_")]
    vo = [v for v in old["vo"] if v[0] in ("VO intro", "VO sting")]
    from chapter_shots import LEAD
    tim = json.load(open(os.path.join(ND, "vo", "ch_timing.json")))
    f = shots[-1][1]
    for c in ("1", "2", "3"):
        start = f
        for sh in tim[c]:
            shots.append([f, f + sh["frames"], sh["name"]]); f += sh["frames"]
        vo.append([f"VO chapter{c}", start + int(round(LEAD * FPS)), f])
    return dict(shots=shots, vo=vo, end=f - 1)
import sys; sys.path.insert(0, HERE)
EDL = build_edl()
N = int(round(EDL["end"] / FPS * SR)) + SR
T = lambda f: (f - 1) / FPS                      # timeline frame -> seconds


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


# ---------------------------------------------------------------------------------------------------- build the mix
def load_audio(path):
    with tempfile.NamedTemporaryFile(suffix=".raw") as f:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", f.name], check=True)
        return np.fromfile(f.name, dtype=np.float32).astype(np.float64)


vo = np.zeros(N)
VOF = {"VO intro": "vo/intro_vo.mp3", "VO chapter1": "vo/ch1_vo.mp3", "VO chapter2": "vo/ch2_vo.mp3", "VO chapter3": "vo/ch3_vo.mp3"}
for name, f0, f1 in EDL["vo"]:
    if name in VOF:
        place(vo, load_audio(os.path.join(ND, VOF[name])), T(f0))
vo_peak = np.abs(vo).max(); vo = vo / vo_peak * db(-3)

# ambience per shot, crossfaded at the cuts
ambb = np.zeros(N)
for f0, f1, name in EDL["shots"]:
    kind = amb_for(name)
    if kind is None: continue
    t0, t1 = T(f0), T(f1)
    place(ambb, fade_edges(amb(kind, t1 - t0 + 0.4), 0.35, 0.35), max(0, t0 - 0.2))

# sections: intro / sting / ch1 / ch2 / ch3 from the shot list
start = {}
for f0, f1, name in EDL["shots"]:
    key = "sting" if name == "seldom_sting" else ("intro" if not name.startswith("c") or name.startswith("cafe") else name[:2])
    start.setdefault(key, f0)
sec = {"intro": (T(1), T(start["sting"])), "sting": (T(start["sting"]), T(start["c1"])),
       "c1": (T(start["c1"]), T(start["c2"])), "c2": (T(start["c2"]), T(start["c3"])), "c3": (T(start["c3"]), T(EDL["end"] + 1))}

music = np.zeros(N)
Dm = [("D", 3), ("F", 3), ("A", 3)]; Bb = [("Bb", 2), ("D", 3), ("F", 3)]; F = [("F", 2), ("A", 2), ("C", 3)]
C = [("C", 3), ("E", 3), ("G", 3)]; Gm = [("G", 2), ("Bb", 2), ("D", 3)]; A = [("A", 2), ("C#", 3), ("E", 3)]
Am = [("A", 2), ("C", 3), ("E", 3)]
place(music, score_section(*sec["intro"], [Dm, Bb, F, C], [("D", 5), ("F", 5), ("A", 5), ("E", 5)], False, -21), sec["intro"][0])
place(music, score_section(*sec["c1"], [Dm, Bb, Gm, A], [("A", 4), ("D", 5), ("F", 5), ("E", 5)], True, -22), sec["c1"][0])
place(music, score_section(*sec["c2"], [Gm, Dm, Bb, A], [("D", 5), ("C", 5), ("Bb", 4), ("A", 4)], True, -22, 1000), sec["c2"][0])
place(music, score_section(*sec["c3"], [Dm, Am, Bb, Dm], [("F", 5), ("E", 5), ("D", 5), ("A", 4)], False, -21, 950), sec["c3"][0])

fx = np.zeros(N)
place(fx, sting() * db(-4), sec["sting"][0])
for key in ("c1", "c2", "c3"):                     # chapter title hits (title card fades in ~0.75 s into the shot)
    place(fx, boom(-15), sec[key][0] + 0.7)
for key in ("c2", "c3"):                           # a soft swell into each later chapter
    place(fx, swell(2.2, -24), sec[key][0] - 2.2)
# the phone that rings and rings (Ch2 7B) and the hearing-room doors (Ch3 6A)
for f0, f1, name in EDL["shots"]:
    if "phone_ring" in name:
        t0 = T(f0) + 0.8; d = 1.8; n = int(d * SR); tt = np.arange(n) / SR
        ring = (np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * (0.5 + 0.5 * np.sin(2 * np.pi * 20 * tt)) * 0.5
        ring = filt(ring, "lowpass", 2500) * fade_edges(np.ones(n), 0.03, 0.06)
        for k in range(3):
            if t0 + k * 4.0 + d < T(f1):
                place(fx, reverb(ring, 0.35) * db(-30), t0 + k * 4.0)
    if "doors_close" in name:
        t0 = T(f0) + (T(f1) - T(f0)) * 0.55; n = int(1.8 * SR); x = np.arange(n) / SR
        th = np.sin(2 * np.pi * 70 * x) * env_ad(n, 0.004, 0.18) + filt(rng.standard_normal(n), "lowpass", 400) * env_ad(n, 0.003, 0.05) * 0.4
        place(fx, reverb(th, 0.45) * db(-16), t0)


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

def spot_events(name, d):
    """(time in seconds within the shot, sound, level dB) for what we see happen on screen."""
    ev = []
    at = lambda frac: frac * d
    if name == "invest_drawer":
        ev += [(0.0, slide(0.9, 200, 1400) + thump(80, 0.4, 0.06) * 0.4, -26), (at(0.68), paper(0.5), -27)]
    elif name == "invest_reveal":
        ev += [(0.15, paper(0.6, 0.2), -30)]
    elif name == "street_bus_reveal":
        ev += [(0.0, car_pass(min(3.2, d + 0.2), 0.45) + thump(45, 2.5, 0.8, 0) * 0.3, -21)]
    elif name == "street_walk_track":
        ev += [(at(0.25), car_pass(2.6, 0.5), -27)]
    elif name.endswith("cafe_title_push") or name == "cafe_title_push":
        ev += [(at(0.55), glass(2600), -30), (at(0.8), glass(3100), -33)]
    elif "capitol_dawn_push" in name:
        for k, tt in enumerate((1.2, 1.35, 3.0, 3.12, 3.26, 5.6, 5.72)):
            if tt < d: ev += [(tt, chirp(0.08, 3400 + 300 * (k % 3), 4300), -38)]
    elif "capitol_night_push" in name or "capitol_slow_push" in name:
        ev += [(at(0.3), horn(130, 2.2), -40)]
    elif "signing_sign" in name:
        for tt in (0.42, 0.5, 0.58):
            ev += [(at(tt), filt(rng.standard_normal(_n(0.35)), "bandpass", [2000, 6000]) * np.sin(np.linspace(0, np.pi, _n(0.35))) ** 2, -36)]
    elif "signing_transfer" in name:
        ev += [(at(0.55), thump(110, 0.5, 0.05, 0) + tap(0.12, 400, 1600, 0.03) * 0.6, -20), (at(0.62), paper(0.4), -30)]
    elif "signing_memo_pass" in name:
        ev += [(at(0.35), slide(0.7, 900, 4500), -30)]
    elif "signing_memo_read" in name:
        ev += [(at(0.5), paper(0.5, 0.16), -29)]
    elif "signing_letter_seal" in name:
        ev += [(at(0.45), paper(0.5), -29), (at(0.7), slide(0.35, 1500, 5000), -31)]
    elif "dchall_tray" in name:
        ev += [(at(0.15), slide(1.0, 300, 2500) * 0.8, -25), (at(0.55), clank(900, 0.4) * 0.7 + tap(0.1) * 0.5, -25)]
    elif "dchall_install" in name:
        ev += [(at(0.6), thump(90, 0.5, 0.07) + clank(600, 0.6) * 0.4, -22)]
    elif "dchall_wake" in name:
        ev += [(at(0.35), beep(880, 0.18), -30), (at(0.35) + 0.2, beep(1320, 0.25), -30),
               (at(0.35), filt(pink(_n(2.5)), "bandpass", [300, 2500]) * np.linspace(0, 1, _n(2.5)) ** 2, -32)]
    elif "dchall_ripple" in name:
        for k in range(5):
            ev += [(0.3 + k * 0.45, beep(1046 * 2 ** (k / 12 * 3), 0.16), -36)]
    elif "remote_enter" in name:
        ev += [((40 - 3) / FPS, tap(0.1, 1200, 4000, 0.02) * 0.8 + thump(180, 0.12, 0.02, 0) * 0.4, -24), (40 / FPS + 0.05, beep(1500, 0.12), -36)]
    elif "port_ship_lift" in name:
        ev += [(0.2, horn(98, 3.4), -27), (at(0.25), filt(np.sin(2 * np.pi * 90 * np.arange(_n(d * 0.6)) / SR), "lowpass", 400) * fade_edges(np.ones(_n(d * 0.6)), 0.5, 0.5) * 0.4, -30),
               (at(0.8), clank(160, 1.8), -22)]
    elif "port_tropical_dock" in name:
        ev += [(at(0.3), horn(87, 3.6), -31)]
    elif "port_scan_gate" in name:
        ev += [(at(0.5), beep(1000, 0.25), -28), (at(0.5) + 0.35, beep(1000, 0.25), -28), (0.0, thump(40, d, 3.0, 0) * 0.3, -26)]
    elif "corp_lobby_walk" in name:
        ev += [(0.0, steps(d, 0.55, 110, 1.0), -26)]
    elif "invest_filing" in name:
        ev += [(at(0.3), paper(0.6, 0.2), -29)]
    elif "invest_chart" in name:                  # the 2024 stack drops onto the desk
        t0 = 1.0 / 4.0 * d
        ev += [(t0, thump(65, 1.2, 0.18, 0.2) + paper(0.4, 0.06) * 0.7, -15), (t0 + 0.16, thump(80, 0.4, 0.05, 0) * 0.35, -20),
               (t0 + 0.3, thump(80, 0.3, 0.04, 0) * 0.2, -22)]
    elif "invest_pinning" in name:
        ev += [(at(0.45), tap(0.1, 800, 2500, 0.02) + thump(160, 0.15, 0.03, 0) * 0.4, -26)]
    elif "police_pull_up" in name:
        ev += [(0.0, car_pass(min(d, 0.42 * d + 1.0), 0.75) * 0.9, -22), (0.42 * d, tap(0.15, 500, 2000, 0.04) * 0.6, -28),
               (0.74 * d, thump(75, 0.7, 0.09) + tap(0.15, 300, 1500, 0.05) * 0.5, -18), (0.5 * d, steps(d * 0.5, 0.5, 120, 0.8), -30)]
    elif "office_door_door_push" in name:
        ev += [(at(0.35), clank(520, 0.4) * 0.6 + tap(0.1, 500, 2000, 0.03), -27), (at(0.35) + 0.18, clank(520, 0.4) * 0.5, -29)]
    elif "computex_crowd" in name:
        ev += [(0.0, club(d), -30)]
        for tt in np.arange(1.5, d - 1, 3.1):
            ev += [(tt, glass(2300 + 400 * ((int(tt) % 3)), 1.0), -38)]
    elif "computex_flash" in name:
        ev += [(0.0, club(d) * 0.7, -32), (70 / FPS - 0.06, tap(0.06, 1500, 5000, 0.01), -30), (70 / FPS, tap(0.09, 800, 3500, 0.02), -28)]
    elif "restaurant" in name:
        for tt in np.arange(0.8, d - 0.5, 1.7):
            ev += [(tt, glass(2000 + 500 * (int(tt * 3) % 3), 0.9), -37)]
    elif "warehouse_lights_off" in name:
        for r in range(6):
            fr = 30 + (5 - r) * 14
            if fr / FPS < d: ev += [(fr / FPS, thump(55, 1.4, 0.25, 0.1) + clank(140, 1.2) * 0.25, -20)]
    elif "press_press_run" in name:
        pass                                       # the press ambience already carries the rhythm
    elif "invest_shelving" in name:
        ev += [(at(0.5), thump(85, 0.5, 0.08) + slide(0.4, 300, 1500) * 0.5, -24)]
    elif "courthouse_lawyer_climb" in name:
        ev += [(0.0, steps(d, 0.5, 100, 0.9), -27)]
    elif "courtroom_clerk" in name:
        for k in range(5):
            tt = 0.8 * k / 4.5 * d
            if tt < d - 0.3: ev += [(tt + 0.6, thump(120, 0.3, 0.04, 0) * 0.6 + paper(0.25, 0.05), -28)]
    elif "invest_lights_out" in name:
        for fr in (30, 39, 48, 57, 66):
            if fr / FPS < d: ev += [(fr / FPS, tap(0.08, 600, 2200, 0.015) + thump(140, 0.2, 0.03, 0) * 0.5, -27)]
    elif "invest_drawer_close" in name:
        ev += [(0.15 * d, slide(0.6 * d, 200, 1500), -27), (0.75 * d, thump(70, 0.9, 0.12) + clank(260, 1.0) * 0.4, -18)]
    elif "street_walk_away" in name:
        ev += [(0.0, steps(d, 0.6, 105, 0.6), -31)]
    return ev

spot = np.zeros(N)
for f0, f1, name in EDL["shots"]:
    d = T(f1) - T(f0)
    for tt, x, lvl in spot_events(name, d):
        if tt < d:
            place(spot, reverb(x, 0.22) * db(lvl), T(f0) + tt)

# intro tail: everything fades with the picture into the sting; music/ambience silent under the sting
for buf in (music, ambb, spot):
    a, b = int((sec["sting"][0] - 1.0) * SR), int(sec["sting"][0] * SR)
    buf[a:b] *= np.cos(np.linspace(0, np.pi / 2, b - a)) ** 2
    buf[b:int((sec["c1"][0] + 0.3) * SR)] = 0
# Chapter 1 fades in from black
a = int(sec["c1"][0] * SR); b = a + SR
for buf in (music, ambb):
    buf[a:b] *= np.sin(np.linspace(0, np.pi / 2, b - a)) ** 2

# duck the bed under the voice (about 7 dB), smooth attack/release
env = np.abs(vo); env = signal.sosfiltfilt(sos("lowpass", 3), env); env = env / (env.max() + 1e-9)
duck = 1 - 0.6 * np.clip(env * 4, 0, 1)
music *= duck; ambb *= 0.5 + 0.5 * duck; spot *= 0.75 + 0.25 * duck

def stereo(with_vo):
    bed = music + ambb * db(2)
    wide = np.roll(music * 0.5 + ambb * 0.5, int(0.011 * SR))
    v = vo if with_vo else 0.0
    L = v + fx + spot + bed
    R = v + fx + np.roll(spot, int(0.004 * SR)) + bed * 0.5 + wide
    return np.stack([L, R], 1)[:int(round(EDL["end"] / FPS * SR))]

outdir = os.path.join(ND, "out", "deliver"); os.makedirs(outdir, exist_ok=True)
import wave, re
full = stereo(True); pk = np.abs(full).max() / 0.95
def write(path, st):
    st = np.tanh(st / pk * 1.05) / np.tanh(1.05)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
raw_v, raw_n = os.path.join(outdir, "_v.wav"), os.path.join(outdir, "_n.wav")
write(raw_v, full); write(raw_n, stereo(False))
# one loudness gain for both (measured on the version with voice -> -14 LUFS), same gain on the no-voice version
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw_v, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", m)[-1]); g = -14.0 - I
for src, dst in ((raw_v, "nvidia_film_AUDIO_v3_with_voice"), (raw_n, "nvidia_film_AUDIO_v3_no_voice")):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", f"volume={g:.2f}dB,alimiter=limit=0.89:level=false", "-ar", str(SR),
                    os.path.join(outdir, dst + ".wav")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(outdir, dst + ".wav"), "-b:a", "256k", os.path.join(outdir, dst + ".mp3")], check=True)
    os.remove(src)
final = os.path.join(outdir, "nvidia_film_AUDIO_v3_with_voice.wav")
st = full
# the new sting sound on its own as well
sti = sting(); sti = sti / np.abs(sti).max() * 0.9
with wave.open(os.path.join(ND, "..", "brand", "seldom_sting_sfx.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([sti, np.roll(sti, 200)], 1) * 32767).astype(np.int16).tobytes())
print("saved", final, round(len(st) / SR, 2), "s")
