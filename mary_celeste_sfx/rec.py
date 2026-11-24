"""CC0 recordings: load, loop into beds, slice one-shots."""
import os, subprocess, glob
import numpy as np
from scipy import signal
import sfxlib as L

SR = L.SR
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib_cc0")
CACHE = os.path.join(LIB, "_npy")
_mem = {}


def path(name):
    """name like 'creak_195193' or just '195193'"""
    hits = glob.glob(os.path.join(LIB, f"{name}.mp3")) or glob.glob(os.path.join(LIB, f"*_{name}.mp3"))
    if not hits:
        raise FileNotFoundError(name)
    return hits[0]


def load(name):
    """(2, n) float32 at 48 kHz"""
    if name in _mem:
        return _mem[name]
    p = path(name)
    os.makedirs(CACHE, exist_ok=True)
    c = os.path.join(CACHE, os.path.basename(p) + ".npy")
    if not os.path.exists(c):
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", p, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32).reshape(-1, 2).T.copy()
        np.save(c, x)
    x = np.load(c)
    _mem[name] = x
    return x


def rms(x):
    return float(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)


def trim(x, start=0.0, dur=None):
    a = int(start * SR)
    b = x.shape[1] if dur is None else min(x.shape[1], a + int(dur * SR))
    return x[:, a:b]


def loop_bed(N, r, name, start=0.0, end=None, xf=2.0, hp=None, lp=None, mono=False):
    """loop a recording (or part of it) to N samples with equal-power crossfades and random segment order"""
    x = load(name)
    x = x[:, int(start * SR): (x.shape[1] if end is None else int(end * SR))]
    if mono:
        m = x.mean(0)
        x = np.stack([m, m])
    if hp:
        x = L.hp(x, hp)
    if lp:
        x = L.lp(x, lp)
    n = x.shape[1]
    k = int(xf * SR)
    seg = max(k * 3, min(n, int(SR * 20)))
    out = np.zeros((2, N + seg), np.float32)
    fade_in = np.sin(np.linspace(0, np.pi / 2, k)).astype(np.float32)
    fade_out = np.cos(np.linspace(0, np.pi / 2, k)).astype(np.float32)
    pos = 0
    while pos < N:
        L_ = int(r.integers(seg // 2, seg + 1)) if n > seg else n
        a = int(r.integers(0, max(1, n - L_)))
        s = x[:, a:a + L_].copy()
        if s.shape[1] < 2 * k + 1:
            s = x.copy()
        s[:, :k] *= fade_in
        s[:, -k:] *= fade_out
        if r.uniform() < 0.5 and not mono:
            s = s[::-1]  # swap channels for variety
        e = min(out.shape[1], pos + s.shape[1])
        out[:, pos:e] += s[:, :e - pos]
        pos += s.shape[1] - k
    return out[:, :N]


def onsets(name, min_gap=0.15, thresh_db=12.0, start=0.0, end=None):
    """sample indices of transients in a recording"""
    x = load(name)
    m = np.abs(x.mean(0))
    a, b = int(start * SR), (len(m) if end is None else int(end * SR))
    m = m[a:b]
    w = int(0.01 * SR)
    env = np.sqrt(np.convolve(m ** 2, np.ones(w) / w, "same"))
    edb = 20 * np.log10(env + 1e-9)
    floor = np.percentile(edb, 30)
    rise = edb - np.concatenate([np.full(w * 3, edb[0]), edb[:-w * 3]])
    cand = np.where((edb > floor + thresh_db) & (rise > 6))[0]
    out, last = [], -10 ** 9
    for c in cand:
        if c - last > min_gap * SR:
            out.append(a + c - int(0.005 * SR))
            last = c
    return out


def shot(name, r, pick=None, start=None, dur=1.0, fade=0.01, rate=1.0, onset_kw=None):
    """one-shot from a recording: by onset index (pick='rand' or int) or fixed start time. returns mono-summed? no: (2,n)"""
    x = load(name)
    if start is None:
        on = onsets(name, **(onset_kw or {}))
        if not on:
            a = 0
        else:
            i = int(r.integers(0, len(on))) if pick in (None, "rand") else min(int(pick), len(on) - 1)
            a = max(0, on[i])
    else:
        a = int(start * SR)
    s = x[:, a:a + int(dur * SR)].copy()
    if rate != 1.0:
        up, down = int(round(1000 / rate)), 1000
        s = signal.resample_poly(s, up, down, axis=1).astype(np.float32)
    n = s.shape[1]
    k = min(n // 2, int(fade * SR))
    if k > 0:
        s[:, :k] *= np.linspace(0, 1, k)
        k2 = min(n // 2, int(max(fade, 0.05) * SR))
        s[:, -k2:] *= np.linspace(1, 0, k2)
    return s.astype(np.float32)
