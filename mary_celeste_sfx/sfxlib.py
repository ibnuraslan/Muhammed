"""Procedural sound library for the Mary Celeste documentary.
Every sound here is synthesised from noise and oscillators in this file: no third-party samples."""
import numpy as np
from scipy import signal

SR = 48000
F32 = np.float32


# ---------------------------------------------------------------- helpers
def rng(seed):
    return np.random.default_rng(seed)


def n_(sec):
    return max(1, int(round(sec * SR)))


def white(n, r):
    return r.standard_normal(n).astype(F32)


def coloured(n, r, slope):
    """noise with power ~ 1/f^slope (1 pink, 2 brown)"""
    w = r.standard_normal(n)
    X = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    X *= f ** (-slope / 2)
    y = np.fft.irfft(X, n)
    return (y / (np.std(y) + 1e-12)).astype(F32)


def pink(n, r):
    return coloured(n, r, 1.0)


def brown(n, r):
    return coloured(n, r, 2.0)


def _sos(kind, f, order=2):
    if kind == "bp":
        lo, hi = f
        hi = min(hi, SR / 2 * 0.95)
        return signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return signal.butter(order, min(f, SR / 2 * 0.95), kind, fs=SR, output="sos")


def lp(x, f, order=2):
    return signal.sosfilt(_sos("lowpass", f, order), x, axis=-1).astype(F32)


def hp(x, f, order=2):
    return signal.sosfilt(_sos("highpass", f, order), x, axis=-1).astype(F32)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bp", (lo, hi), order), x, axis=-1).astype(F32)


def peak(x, f, q):
    b, a = signal.iirpeak(min(f, SR / 2 * 0.95), q, fs=SR)
    return signal.lfilter(b, a, x).astype(F32)


def smooth_rand(n, r, rate_hz, lo=0.0, hi=1.0):
    """slow random curve between lo and hi, changing about rate_hz times a second"""
    k = max(4, int(n / SR * rate_hz) + 4)
    pts = r.uniform(0, 1, k)
    xp = np.linspace(0, n, k)
    y = np.interp(np.arange(n), xp, pts)
    y = lp(y.astype(F32), max(rate_hz, 0.05), 1)
    y = (y - y.min()) / (y.max() - y.min() + 1e-9)
    return (lo + (hi - lo) * y).astype(F32)


def env_ad(n, att, dec, curve=1.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(att, 1e-4), 0, 1) ** curve
    d = np.exp(-np.maximum(t - att, 0) / max(dec, 1e-4))
    return (a * d).astype(F32)


def env_win(n, fade):
    e = np.ones(n, F32)
    k = min(n // 2, n_(fade))
    if k > 0:
        ramp = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, k))).astype(F32)
        e[:k] *= ramp
        e[-k:] *= ramp[::-1]
    return e


def damped(n, freqs, decays, amps, r=None, detune=0.0):
    t = np.arange(n) / SR
    y = np.zeros(n, F32)
    for f, d, a in zip(freqs, decays, amps):
        if r is not None and detune:
            f = f * (1 + r.uniform(-detune, detune))
        ph = 0 if r is None else r.uniform(0, 2 * np.pi)
        y += (a * np.exp(-t / d) * np.sin(2 * np.pi * f * t + ph)).astype(F32)
    return y


def norm(x, pk=1.0):
    m = np.max(np.abs(x)) + 1e-12
    return (x / m * pk).astype(F32)


def stereo(x, pan=0.0, width=0.0, r=None):
    """mono -> (2, n); pan -1..1 equal-power; width adds a short decorrelating delay"""
    p = (pan + 1) / 2 * np.pi / 2
    L, R = np.cos(p) * x, np.sin(p) * x
    if width and r is not None:
        d = int(SR * 0.0004 * width * r.uniform(0.5, 1.5))
        R = np.concatenate([np.zeros(d, F32), R[:len(R) - d]])
    return np.stack([L, R]).astype(F32)


def add(dst, src, at):
    """add (2,n) src into (2,N) dst at sample index at"""
    if src.ndim == 1:
        src = np.stack([src, src])
    a = int(at)
    if a < 0:
        src = src[:, -a:]
        a = 0
    b = min(dst.shape[1], a + src.shape[1])
    if b > a:
        dst[:, a:b] += src[:, :b - a]


# ---------------------------------------------------------------- primitives
def creak(r, dur=None, kind="hull"):
    """stick-slip friction creak: jittered pulse train through resonant body"""
    if kind == "hull":
        dur = dur or r.uniform(0.6, 1.8)
        rate = (r.uniform(12, 30), r.uniform(30, 70), r.uniform(15, 40))
        res = [(r.uniform(150, 220), 10), (r.uniform(380, 480), 12), (r.uniform(800, 1000), 14), (r.uniform(1600, 2000), 10)]
        gains = [1.0, 0.8, 0.45, 0.2]
    elif kind == "rope":
        dur = dur or r.uniform(0.4, 1.1)
        rate = (r.uniform(40, 80), r.uniform(80, 160), r.uniform(50, 100))
        res = [(r.uniform(500, 700), 14), (r.uniform(1100, 1500), 16), (r.uniform(2200, 2900), 12)]
        gains = [0.8, 1.0, 0.5]
    elif kind == "hawser":
        dur = dur or r.uniform(1.2, 2.5)
        rate = (r.uniform(8, 16), r.uniform(20, 35), r.uniform(10, 18))
        res = [(r.uniform(110, 150), 9), (r.uniform(260, 330), 11), (r.uniform(600, 720), 12)]
        gains = [1.0, 0.8, 0.4]
    else:  # metal ring / lantern bail
        dur = dur or r.uniform(0.3, 0.7)
        rate = (r.uniform(60, 120), r.uniform(150, 260), r.uniform(80, 140))
        res = [(r.uniform(1500, 1900), 25), (r.uniform(2900, 3500), 30), (r.uniform(4800, 5600), 25)]
        gains = [1.0, 0.7, 0.4]
    n = n_(dur)
    t = np.linspace(0, 1, n)
    f = np.interp(t, [0, 0.5, 1], rate) * (1 + 0.15 * smooth_rand(n, r, 12, -1, 1))
    ph = np.cumsum(f / SR)
    pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(F32)
    pulses *= r.uniform(0.4, 1.0, n).astype(F32)
    exc = pulses + 0.02 * white(n, r)
    y = np.zeros(n, F32)
    for (fr, q), g in zip(res, gains):
        y += g * peak(exc, fr, q)
    e = env_win(n, dur * 0.25) * (0.6 + 0.4 * smooth_rand(n, r, 6))
    return norm(y * e)


def knock(r, f0=420, dec=0.06, bright=1.0, n_modes=4):
    n = n_(dec * 8 + 0.02)
    ratios = [1, 1.58, 2.37, 3.6, 4.9][:n_modes]
    y = damped(n, [f0 * k for k in ratios], [dec / (1 + 0.6 * i) for i in range(n_modes)],
               [1, 0.6, 0.4 * bright, 0.25 * bright, 0.15 * bright], r, 0.03)
    click = hp(white(n_(0.004), r), 1500) * np.linspace(1, 0, n_(0.004)).astype(F32) * 0.6 * bright
    y[:len(click)] += click
    return norm(y)


def thud(r, f0=70, dec=0.08, body=0.6):
    n = n_(dec * 6 + 0.05)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.6 * np.exp(-t / 0.01))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec)
    nz = lp(white(n, r), 900) * env_ad(n, 0.002, dec * 0.6)
    return norm((s + body * nz).astype(F32))


def metal(r, f0=380, dec=0.6, strike=0.5):
    n = n_(dec * 5)
    ratios = [1, 2.76, 5.40, 8.93, 13.34]
    y = damped(n, [f0 * k for k in ratios], [dec, dec * 0.6, dec * 0.4, dec * 0.25, dec * 0.15],
               [1, 0.7, 0.45, 0.3, 0.2], r, 0.01)
    y += strike * hp(white(n, r), 2000) * env_ad(n, 0.001, 0.01)
    return norm(y)


def bubble(r, f0=None, dur=None, rise=None):
    f0 = f0 or r.uniform(500, 1400)
    dur = dur or r.uniform(0.03, 0.09)
    rise = rise if rise is not None else r.uniform(2, 6)
    n = n_(dur)
    t = np.arange(n) / SR
    f = f0 * (1 + rise * t)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (dur / 3))
    return norm(y.astype(F32))


def drip(r, into="water"):
    n = n_(0.4)
    y = np.zeros(n, F32)
    tick = knock(r, r.uniform(1800, 2600), 0.008, 1.0, 3) * 0.35
    y[:len(tick)] += tick
    if into == "water":
        b = bubble(r, r.uniform(700, 1300), r.uniform(0.05, 0.1), r.uniform(3, 8))
        o = n_(0.004)
        y[o:o + len(b)] += b
        y += 0.06 * bp(white(n, r), 2000, 8000) * env_ad(n, 0.001, 0.02)
    else:
        y += 0.15 * bp(white(n, r), 1500, 6000) * env_ad(n, 0.001, 0.015)
    return norm(y)


def burst(r, dur, lo, hi, att=0.01, dec=None, colour="white"):
    n = n_(dur)
    x = pink(n, r) if colour == "pink" else white(n, r)
    x = bp(x, lo, hi)
    e = env_ad(n, att, dec or dur / 3)
    return norm(x * e)


def grains(r, dur, rate, lo, hi, glen=(0.002, 0.01), amp=(0.3, 1.0), envshape=None):
    """sparse granular noise (rustle, crunch, rain, scrape)"""
    n = n_(dur)
    y = np.zeros(n, F32)
    cnt = r.poisson(rate * dur)
    for _ in range(cnt):
        g = n_(r.uniform(*glen))
        a = r.integers(0, max(1, n - g))
        y[a:a + g] += r.uniform(*amp) * white(g, r) * np.hanning(g).astype(F32)
    y = bp(y, lo, hi)
    if envshape is not None:
        y *= envshape(n)
    return norm(y)


# ---------------------------------------------------------------- one-shot SFX (mono unless stated)
def sfx_barrel_knock(r, empty=True):
    n = n_(1.2)
    k = knock(r, r.uniform(380, 460), 0.05, 0.8)
    cav = damped(n, [r.uniform(105, 125), r.uniform(230, 260)], [0.35 if empty else 0.08, 0.18], [1, 0.4], r)
    y = np.zeros(n, F32)
    y[:len(k)] += 0.7 * k
    y += 0.9 * cav
    return norm(y)


def sfx_barrel_knock2(r):
    n = n_(1.6)
    y = np.zeros(n, F32)
    add2(y, sfx_barrel_knock(r), 0)
    add2(y, 0.8 * sfx_barrel_knock(r), n_(0.28))
    return norm(y)


def add2(y, s, a):
    b = min(len(y), a + len(s))
    y[a:b] += s[:b - a]


def sfx_chalk_scrape(r, dur=0.7):
    n = n_(dur)
    gr = grains(r, dur, 900, 1800, 7000, (0.001, 0.004))
    sq = np.sin(2 * np.pi * np.cumsum(2600 + 300 * smooth_rand(n, r, 8, -1, 1)) / SR).astype(F32)
    sq *= smooth_rand(n, r, 15) ** 3 * 0.15
    return norm((gr + sq) * env_win(n, 0.08))


def sfx_chalk_X(r):
    n = n_(1.3)
    y = np.zeros(n, F32)
    add2(y, sfx_chalk_scrape(r, 0.45), 0)
    add2(y, sfx_chalk_scrape(r, 0.45), n_(0.65))
    return y


def sfx_chalk_tap(r):
    k = knock(r, r.uniform(1400, 1800), 0.012, 1.2, 3)
    return norm(k + 0.3 * hp(white(len(k), r), 3000) * env_ad(len(k), 0.0005, 0.004))


def sfx_trickle(r, dur=6.0):
    n = n_(dur)
    y = 0.15 * bp(white(n, r), 800, 5000) * smooth_rand(n, r, 3, 0.4, 1.0)
    for _ in range(int(35 * dur)):
        b = bubble(r, r.uniform(900, 3500), r.uniform(0.01, 0.04), r.uniform(2, 10))
        add2(y, r.uniform(0.2, 1.0) * b, int(r.integers(0, n - len(b))))
    return norm(y * env_win(n, 0.6))


def sfx_flame(r, dur=4.0):
    n = n_(dur)
    x = lp(white(n, r), 260, 2) * smooth_rand(n, r, 7, 0.3, 1.0)
    x += 0.15 * bp(white(n, r), 1500, 5000) * smooth_rand(n, r, 20, 0, 1) ** 4  # crackle
    return norm(x * env_win(n, 0.3))


def sfx_lantern_creak(r):
    return creak(r, r.uniform(0.35, 0.6), "ring")


def sfx_sniff(r):
    n = n_(0.45)
    e = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return norm((bp(white(n, r), 1500, 6000) * e).astype(F32))


def sfx_breath(r, dur=1.4):
    n = n_(dur)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    x = bp(pink(n, r), 400, 3500) * e
    return norm(peak(x, 1100, 2) + 0.5 * x)


def sfx_boot(r, heavy=1.0):
    n = n_(0.35)
    y = np.zeros(n, F32)
    add2(y, heavy * thud(r, r.uniform(80, 100), 0.05, 0.4), 0)
    add2(y, 0.45 * knock(r, r.uniform(260, 340), 0.03, 0.5), n_(0.002))
    add2(y, 0.15 * burst(r, 0.08, 800, 4000, 0.005, 0.02), n_(0.01))  # leather scuff
    return norm(y)


def sfx_footsteps(r, times, heavy=1.0):
    n = n_(max(times) + 0.5)
    y = np.zeros(n, F32)
    for t in times:
        add2(y, r.uniform(0.75, 1.0) * sfx_boot(r, heavy), n_(t))
    return norm(y)


def sfx_wood_tap(r):
    return knock(r, r.uniform(600, 780), 0.025, 1.0)


def sfx_wood_set(r):
    n = n_(0.6)
    y = np.zeros(n, F32)
    add2(y, thud(r, r.uniform(85, 110), 0.07, 0.5), 0)
    add2(y, 0.6 * knock(r, r.uniform(300, 380), 0.05, 0.6), n_(0.003))
    add2(y, 0.25 * knock(r, r.uniform(420, 500), 0.03, 0.4), n_(0.09))  # small settle
    return norm(y)


def sfx_iron_clank(r):
    n = n_(2.0)
    y = np.zeros(n, F32)
    add2(y, metal(r, r.uniform(330, 420), 0.5), 0)
    add2(y, 0.5 * metal(r, r.uniform(500, 620), 0.25), n_(0.11))
    add2(y, 0.4 * thud(r, 90, 0.05, 0.3), 0)
    return norm(y)


def sfx_hammers(r, dur, rate=1.2):
    n = n_(dur)
    y = np.zeros(n, F32)
    t = r.uniform(0, 0.5)
    while t < dur - 0.5:
        s = metal(r, r.uniform(700, 900), 0.12, 0.8) * 0.5 if r.uniform() < 0.4 else knock(r, r.uniform(350, 450), 0.04)
        add2(y, r.uniform(0.5, 1.0) * s, n_(t))
        t += r.uniform(0.6, 1.4) / rate
    return norm(lp(y, 3500))


def sfx_saw(r, dur, strokes_hz=1.1):
    n = n_(dur)
    t = np.arange(n) / SR
    stroke = np.abs(np.sin(np.pi * strokes_hz * t)) ** 0.7
    teeth = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * (90 + 40 * stroke) * t))
    x = bp(white(n, r), 1200, 5000) * stroke * teeth
    return norm((x * env_win(n, 0.2)).astype(F32))


def sfx_paper(r, dur=0.8):
    n = n_(dur)
    e = lambda m: np.sin(np.linspace(0, np.pi, m)) ** 0.8
    y = grains(r, dur, 500, 1200, 9000, (0.002, 0.015), envshape=e)
    y += 0.25 * bp(white(n, r), 500, 3000) * e(n).astype(F32)
    return norm(y)


def sfx_grit(r, dur=1.0):
    return grains(r, dur, 1800, 900, 6000, (0.0008, 0.004), (0.2, 1.0), lambda m: env_win(m, 0.1))


def sfx_valve_slap(r):
    n = n_(0.4)
    y = thud(r, 140, 0.04, 0.8)
    y2 = np.zeros(n, F32)
    add2(y2, y, 0)
    add2(y2, 0.3 * metal(r, 520, 0.08, 0.2)[:n], n_(0.003))
    return norm(y2)


def sfx_rod_scrape(r, dur=3.0):
    n = n_(dur)
    exc = bp(white(n, r), 300, 6000) * smooth_rand(n, r, 9, 0.2, 1.0)
    # comb resonance of the bore
    d = int(SR / r.uniform(180, 240))
    y = exc.copy()
    for _ in range(3):
        y[d:] += 0.75 * y[:-d]
    y = peak(y, r.uniform(1800, 2400), 6) + 0.5 * y
    stick = creak(r, dur, "ring")
    y = norm(y) + 0.3 * stick[:n]
    return norm(y * env_win(n, 0.15))


def sfx_line_hands(r, dur=1.6):
    n = n_(dur)
    y = grains(r, dur, 1200, 500, 3500, (0.003, 0.012), envshape=lambda m: env_win(m, 0.2))
    return norm(y + 0.4 * creak(r, dur, "rope")[:n])


def sfx_pin_tap(r):
    n = n_(0.4)
    y = damped(n, [r.uniform(2800, 3200), r.uniform(5100, 5600), 7900], [0.05, 0.03, 0.02], [1, 0.6, 0.3], r)
    k = knock(r, 900, 0.01, 1.0, 2)
    y[:len(k)] += 0.4 * k[:n]
    return norm(y)


def sfx_pulse(r):
    n = n_(1.6)
    t = np.arange(n) / SR
    f = 70 - 20 * t / t[-1]
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(n, 0.25, 0.45, 2)
    nz = lp(pink(n, r), 400) * env_ad(n, 0.3, 0.3, 2) * 0.3
    return norm((s + nz).astype(F32))


def sfx_nib(r, dur=6.0):
    n = n_(dur)
    y = grains(r, dur, 700, 2500, 9000, (0.001, 0.005), (0.1, 1.0))
    y *= smooth_rand(n, r, 4, 0.4, 1.0) * env_win(n, 0.3)
    return norm(y)


def sfx_stop_click(r):
    n = n_(0.3)
    y = np.zeros(n, F32)
    add2(y, knock(r, 820, 0.018, 0.9, 3), 0)
    add2(y, 0.4 * knock(r, 1100, 0.01, 0.8, 2), n_(0.045))
    return norm(y)


def sfx_whump(r, dur=1.2):
    """sail filling with wind"""
    n = n_(dur)
    x = lp(pink(n, r), 350) * env_ad(n, 0.12, 0.35, 1.5)
    s = np.sin(2 * np.pi * np.cumsum(np.full(n, 55.0)) / SR) * env_ad(n, 0.1, 0.25, 1.5)
    x2 = 0.3 * bp(white(n, r), 800, 3000) * env_ad(n, 0.05, 0.12)
    return norm((x + 0.5 * s + x2).astype(F32))


def sfx_wave_slam(r):
    n = n_(3.5)
    y = np.zeros(n, F32)
    add2(y, thud(r, 48, 0.25, 0.8)[:n], 0)
    body = lp(pink(n, r), 1200) * env_ad(n, 0.01, 0.6)
    spray = hp(white(n, r), 2500) * env_ad(n, 0.15, 0.9, 1.5) * 0.5
    y[:len(body)] += body + spray
    return norm(y)


def sfx_slosh(r, dur=3.0, muffle=500):
    n = n_(dur)
    sl = lp(white(n, r), muffle) * (np.sin(np.linspace(0, np.pi * dur / 1.4, n)) ** 2) * env_win(n, 0.4)
    y = sl.astype(F32)
    for _ in range(int(10 * dur)):
        b = bubble(r, r.uniform(200, 600), r.uniform(0.04, 0.12), r.uniform(1, 4))
        add2(y, 0.3 * b, int(r.integers(0, n - len(b))))
    return norm(lp(y, muffle * 1.5))


def sfx_head_turn(r):
    """cloth rustle of a small head / shoulder movement"""
    n = n_(0.6)
    return norm(bp(pink(n, r), 600, 5000) * np.sin(np.linspace(0, np.pi, n)) ** 2)


def sfx_cart(r, dur=6.0):
    n = n_(dur)
    t = np.arange(n) / SR
    bumps = np.zeros(n, F32)
    tt = 0.0
    while tt < dur:
        a = n_(tt)
        if a < n:
            bumps[a] = r.uniform(0.3, 1.0)
        tt += r.uniform(0.06, 0.16)
    rumble = signal.lfilter([1], [1, -0.995], bumps).astype(F32)
    rumble = lp(rumble, 400) + 0.3 * bp(signal.lfilter([1], [1, -0.9], bumps).astype(F32), 800, 3000)
    y = norm(rumble) + 0.3 * creak(r, dur, "hawser")[:n]
    return norm(y * env_win(n, dur * 0.35))


def sfx_wind_gust(r, dur=3.0):
    n = n_(dur)
    x = bp(pink(n, r), 200, 2500) * np.sin(np.linspace(0, np.pi, n)) ** 2
    return norm(peak(x, 700, 1.5) + x)


# ---------------------------------------------------------------- beds (return (2, N))
def bed_sea(N, r, heavy=False):
    base = np.stack([lp(brown(N, r), 350 if not heavy else 600), lp(brown(N, r), 350 if not heavy else 600)])
    base *= 0.25 if not heavy else 0.5
    y = base.astype(F32)
    t = 0.0
    dur_total = N / SR
    while t < dur_total:
        d = r.uniform(3.5, 6.0) if not heavy else r.uniform(2.5, 4.5)
        n = n_(d)
        att = r.uniform(0.25, 0.45) * d
        e = env_ad(n, att, d * 0.25, 1.6)
        lo, hi = (120, r.uniform(1200, 2600)) if not heavy else (90, r.uniform(2500, 6000))
        for ch in range(2):
            w = bp(pink(n, r), lo, hi)
            fizz = hp(white(n, r), 3000) * env_ad(n, att * 1.1, d * 0.12, 3) * (0.25 if not heavy else 0.5)
            g = r.uniform(0.5, 1.0) * (1.0 if not heavy else 1.8)
            seg = (w * e + fizz) * g
            a = n_(t)
            b = min(N, a + n)
            y[ch, a:b] += seg[:b - a] * (0.7 + 0.3 * r.uniform())
        t += r.uniform(1.5, 3.5) if not heavy else r.uniform(1.0, 2.2)
    return y


def bed_wind(N, r, strength=0.3, whistle=0.2):
    gust = smooth_rand(N, r, 0.15, 0.25, 1.0)
    gust2 = smooth_rand(N, r, 0.6, 0.6, 1.0)
    out = []
    for ch in range(2):
        x = pink(N, r)
        bands = [(80, 250), (250, 600), (600, 1400), (1400, 3500)]
        weights = [lambda g: 1.0, lambda g: 0.5 + 0.6 * g, lambda g: 0.15 + 0.7 * g ** 2, lambda g: 0.05 + 0.4 * g ** 3]
        g = gust * gust2
        y = np.zeros(N, F32)
        for (lo, hi), wf in zip(bands, weights):
            y += bp(x, lo, hi) * wf(g)
        y *= (0.3 + 0.7 * g) * (0.5 + strength)
        if whistle:
            wn = white(N, r)
            for f in (r.uniform(500, 700), r.uniform(900, 1200), r.uniform(1500, 1900)):
                wh = peak(wn, f, 45) * np.clip(g - 0.55, 0, 1) ** 2 * whistle * 6
                y += wh
        out.append(y)
    return np.stack(out).astype(F32)


def bed_events(N, r, maker, rate, gain=(0.3, 1.0), pan=1.0, width=1.0):
    """random one-shots across the bed: maker(r) -> mono"""
    y = np.zeros((2, N), F32)
    t = r.uniform(0, 1 / rate)
    while t < N / SR:
        s = maker(r) * r.uniform(*gain)
        add(y, stereo(s, r.uniform(-pan, pan), width, r), n_(t))
        t += r.exponential(1 / rate) + 0.2
    return y


def gull(r, far=False):
    calls = r.integers(1, 4)
    out = np.zeros(n_(2.2), F32)
    t = 0
    for _ in range(calls):
        d = r.uniform(0.22, 0.45)
        n = n_(d)
        tt = np.linspace(0, 1, n)
        f0 = r.uniform(1100, 1500)
        f = f0 * (1 + 0.5 * np.sin(np.pi * tt ** 0.7)) * (1 + 0.02 * np.sin(2 * np.pi * 28 * tt * d))
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph) + 0.12 * np.sin(4 * ph)
        x = x * (np.sin(np.pi * tt) ** 0.6) + 0.15 * bp(white(n, r), 1500, 5000) * np.sin(np.pi * tt)
        add2(out, x.astype(F32), n_(t))
        t += d + r.uniform(0.05, 0.15)
    out = bp(out, 700, 6000)
    if far:
        out = lp(out, 2500)
    return norm(out)


def bed_harbour(N, r):
    y = np.zeros((2, N), F32)
    # lapping against the quay and hull
    lap = bed_events(N, r, lambda q: sfx_slosh(q, q.uniform(0.3, 0.8), 900), 2.5, (0.3, 0.8), 0.7, 1)
    y += lap
    y += 0.25 * bed_events(N, r, lambda q: gull(q, far=True), 0.35, (0.2, 0.7), 1.0, 1)
    # distant town / quay murmur
    m = np.stack([bp(pink(N, r), 250, 1400), bp(pink(N, r), 250, 1400)]) * smooth_rand(N, r, 1.5, 0.5, 1.0)
    y += 0.08 * m
    y += 0.25 * np.stack([lp(brown(N, r), 200), lp(brown(N, r), 200)])
    return y.astype(F32)


def bed_hold(N, r):
    base = np.stack([lp(brown(N, r), 180), lp(brown(N, r), 180)]) * 0.5
    outside = bed_sea(N, r) * 0.6
    outside = np.stack([lp(outside[0], 250), lp(outside[1], 250)])
    cr = bed_events(N, r, lambda q: lp(creak(q, kind="hull"), 1200), 0.35, (0.2, 0.7), 0.8, 1)
    return (base + outside + 0.6 * cr).astype(F32)


def bed_room(N, r):
    tone = np.stack([lp(brown(N, r), 250), lp(brown(N, r), 250)]) * 0.35
    hiss = np.stack([bp(white(N, r), 3000, 9000), bp(white(N, r), 3000, 9000)]) * 0.04 * smooth_rand(N, r, 3, 0.8, 1.0)
    return (tone + hiss).astype(F32)


def bed_drone(N, r):
    t = np.arange(N) / SR
    hum = (np.sin(2 * np.pi * 43.6 * t) + 0.6 * np.sin(2 * np.pi * 44.1 * t + 1) + 0.25 * np.sin(2 * np.pi * 87.3 * t)).astype(F32)
    rum = lp(brown(N, r), 120)
    m = smooth_rand(N, r, 0.2, 0.6, 1.0)
    y = (0.35 * hum + rum) * m
    return np.stack([y, np.roll(y, 300)]).astype(F32)


def bed_rain(N, r, heavy=False):
    out = []
    for ch in range(2):
        drops = np.zeros(N, F32)
        cnt = int(N / SR * (2500 if heavy else 1200))
        idx = r.integers(0, N - 64, cnt)
        drops[idx] = r.uniform(0.1, 1.0, cnt).astype(F32)
        d = signal.lfilter([1], [1, -0.7], drops).astype(F32)
        y = hp(d, 1500) + 0.5 * bp(pink(N, r), 800, 6000) * 0.3
        out.append(y)
    return np.stack(out).astype(F32)


def bed_flog(N, r):
    """torn canvas flogging: irregular flaps modulated by gusts"""
    g = smooth_rand(N, r, 0.3, 0.2, 1.0)
    y = np.zeros((2, N), F32)
    t = 0.0
    while t < N / SR:
        a = n_(t)
        gi = g[min(a, N - 1)]
        s = burst(r, r.uniform(0.05, 0.12), 150, 3500, 0.004, r.uniform(0.02, 0.05), "pink") * gi
        add2(s, 0.4 * gi * thud(r, r.uniform(70, 110), 0.03, 0.2)[:len(s)], 0)
        add(y, stereo(s, r.uniform(-0.5, 0.5), 1, r), a)
        t += r.uniform(0.08, 0.25) / (0.4 + gi)
    return y


def bed_bowwash(N, r):
    out = []
    for ch in range(2):
        x = bp(white(N, r), 400, 7000) * smooth_rand(N, r, 0.5, 0.4, 1.0)
        x += lp(pink(N, r), 500) * smooth_rand(N, r, 0.3, 0.3, 1.0)
        out.append(x)
    return np.stack(out).astype(F32)


# ---------------------------------------------------------------- spaces
def ir(r, rt=0.8, damp=4000, pre=0.01, er=0.3):
    n = n_(rt * 1.5 + pre)
    out = []
    for ch in range(2):
        t = np.arange(n) / SR
        x = white(n, r) * np.exp(-6.9 * t / rt)
        x = lp(x, damp)
        x[:n_(pre)] = 0
        for _ in range(6):
            k = n_(pre + r.uniform(0.003, 0.04))
            if k < n:
                x[k] += er * r.uniform(-1, 1)
        out.append(x / (np.sqrt(np.sum(x ** 2)) + 1e-9))
    return np.stack(out).astype(F32)


def sfx_gull(r, far=False):
    return gull(r, far)


def sfx_creak(r, kind="hull", dur=None):
    return creak(r, dur, kind)


# ---------------------------------------------------------------- added for Part 1
def sfx_oars(r, dur=3.0, rate=0.75):
    """oar strokes: blade dip + pull swirl + thole-pin knock"""
    n = n_(dur)
    y = np.zeros(n, F32)
    t = r.uniform(0.0, 0.3)
    while t < dur - 0.3:
        add2(y, 0.7 * knock(r, r.uniform(500, 650), 0.03, 0.8), n_(t))          # oar in the thole
        sw = sfx_slosh(r, 0.7, 1400) * 0.8
        add2(y, sw, n_(t + 0.08))                                                  # blade dip and pull
        add2(y, 0.3 * bubble(r, r.uniform(300, 500), 0.08, 2), n_(t + 0.12))
        t += 1 / rate * r.uniform(0.9, 1.1)
    return norm(y)


def sfx_hand_slap(r, wet=True):
    n = n_(0.3)
    y = np.zeros(n, F32)
    add2(y, burst(r, 0.06, 300, 5000, 0.001, 0.012), 0)
    add2(y, 0.5 * knock(r, r.uniform(250, 330), 0.03, 0.4), 0)
    if wet:
        add2(y, 0.35 * burst(r, 0.12, 2000, 9000, 0.002, 0.03), n_(0.004))
    return norm(y)


def sfx_ladder(r, steps=3, gap=0.42):
    n = n_(steps * gap + 0.9)
    y = np.zeros(n, F32)
    for i in range(steps):
        t = i * gap * r.uniform(0.9, 1.1)
        add2(y, sfx_boot(r, 0.8), n_(t))
        add2(y, 0.5 * creak(r, r.uniform(0.25, 0.45), "hull"), n_(t + 0.03))
    return norm(y)


def sfx_glass(r, dur=0.8):
    """glass grit / crunch underfoot"""
    n = n_(dur)
    y = grains(r, dur, 600, 2500, 12000, (0.0005, 0.003), (0.1, 1.0), lambda m: env_ad(m, 0.01, dur / 3))
    for _ in range(int(8 * dur)):
        tink = damped(n_(0.08), [r.uniform(3500, 7000), r.uniform(7000, 11000)], [0.02, 0.012], [1, 0.5], r)
        add2(y, 0.25 * tink, int(r.integers(0, n - n_(0.08))))
    return norm(y)


def sfx_card_tick(r, count=4):
    n = n_(count * 0.25 + 0.2)
    y = np.zeros(n, F32)
    for i in range(count):
        add2(y, r.uniform(0.5, 1) * knock(r, r.uniform(2400, 3000), 0.006, 1.0, 2), n_(i * r.uniform(0.18, 0.3)))
    return norm(y)


def sfx_wood_scrape(r, dur=0.9):
    n = n_(dur)
    exc = bp(white(n, r), 200, 4000) * smooth_rand(n, r, 14, 0.3, 1.0)
    y = peak(exc, r.uniform(300, 400), 4) + peak(exc, r.uniform(900, 1100), 5) + 0.3 * exc
    y += 0.4 * creak(r, dur, "hull")[:n]
    return norm(y * env_win(n, 0.1))


def sfx_iron_scrape(r, dur=1.0):
    n = n_(dur)
    exc = bp(white(n, r), 400, 8000) * smooth_rand(n, r, 18, 0.2, 1.0)
    y = 0.3 * exc
    for f in (r.uniform(700, 900), r.uniform(1800, 2300), r.uniform(3500, 4200)):
        y += peak(exc, f, 25)
    return norm(y * env_win(n, 0.08))


def sfx_pot_roll(r, dur=1.6):
    n = n_(dur)
    y = np.zeros(n, F32)
    t = 0.0
    while t < dur - 0.2:
        add2(y, r.uniform(0.3, 0.8) * metal(r, r.uniform(600, 800), 0.15, 0.3)[:n_(0.5)], n_(t))
        t += r.uniform(0.12, 0.3)
    y += 0.4 * sfx_slosh(r, dur, 700)[:n]
    return norm(y * env_win(n, 0.1))


def sfx_splash_below(r):
    n = n_(1.0)
    y = np.zeros(n, F32)
    add2(y, thud(r, 120, 0.04, 0.6), 0)
    add2(y, sfx_slosh(r, 0.8, 1200), n_(0.01))
    for _ in range(5):
        add2(y, 0.3 * bubble(r), int(r.integers(n_(0.02), n_(0.4))))
    return norm(lp(y, 2500))


def sfx_foot_water(r):
    n = n_(0.7)
    y = np.zeros(n, F32)
    add2(y, 0.6 * sfx_boot(r, 0.7), 0)
    add2(y, sfx_slosh(r, 0.5, 2500), n_(0.01))
    return norm(y)


def sfx_door_latch(r):
    n = n_(1.2)
    y = np.zeros(n, F32)
    add2(y, metal(r, r.uniform(1200, 1500), 0.05, 0.6)[:n_(0.4)], 0)
    add2(y, 0.6 * metal(r, r.uniform(1600, 1900), 0.04, 0.5)[:n_(0.4)], n_(0.09))
    add2(y, 0.7 * creak(r, 0.7, "hawser"), n_(0.2))  # door swings
    return norm(y)


def sfx_wheel(r, dur=1.0, spin=False):
    """ship's wheel: spoke/axle creak, pawl clicks when spun"""
    n = n_(dur)
    y = 0.6 * creak(r, dur, "hull")[:n]
    if spin:
        t, rate = 0.0, 9.0
        while t < dur - 0.05:
            add2(y, 0.5 * knock(r, r.uniform(1500, 1900), 0.008, 1.2, 2), n_(t))
            t += 1 / rate
            rate = max(4, rate * 0.97)
    return norm(y)


def sfx_chain(r, dur=1.2):
    n = n_(dur)
    y = np.zeros(n, F32)
    t = 0.0
    while t < dur - 0.1:
        add2(y, r.uniform(0.3, 1) * metal(r, r.uniform(1800, 2600), 0.03, 0.8)[:n_(0.2)], n_(t))
        t += r.uniform(0.02, 0.07)
    return norm(y * env_win(n, 0.1))


def sfx_whoosh(r, dur=1.6):
    n = n_(dur)
    x = pink(n, r)
    t = np.linspace(0, 1, n)
    e = np.sin(np.pi * t) ** 2
    lo = bp(x, 150, 600)
    mid = bp(x, 600, 2000)
    hi = bp(x, 2000, 7000)
    y = lo * e + mid * e * (0.3 + 0.7 * t) + hi * e * t ** 2 * 0.7
    return norm(y)


def sfx_brush(r, dur=0.6):
    n = n_(dur)
    return norm(bp(white(n, r), 2000, 9000) * smooth_rand(n, r, 10, 0.3, 1.0) * np.sin(np.linspace(0, np.pi, n)))


def sfx_hull_knock(r):
    """boat bumping the hull alongside"""
    n = n_(0.8)
    y = np.zeros(n, F32)
    add2(y, thud(r, r.uniform(60, 80), 0.12, 0.6), 0)
    add2(y, 0.6 * knock(r, r.uniform(180, 240), 0.08, 0.4), 0)
    add2(y, 0.4 * sfx_slosh(r, 0.5, 1200), n_(0.02))
    return norm(y)


def sfx_water_slap(r):
    n = n_(0.8)
    y = np.zeros(n, F32)
    add2(y, burst(r, 0.3, 200, 3000, 0.003, 0.06, "pink"), 0)
    add2(y, 0.6 * sfx_slosh(r, 0.6, 1600), n_(0.03))
    return norm(y)


def sfx_page(r, dur=0.9):
    """page turn: lift rustle then a soft flap"""
    n = n_(dur)
    y = np.zeros(n, F32)
    add2(y, sfx_paper(r, dur * 0.7), 0)
    add2(y, 0.6 * burst(r, 0.12, 200, 2500, 0.01, 0.04, "pink"), n_(dur * 0.65))
    return norm(y)


def sfx_mast_creak(r):
    return norm(lp(creak(r, r.uniform(1.0, 1.8), "hawser"), 900))


def sfx_hull_groan(r):
    return norm(lp(creak(r, r.uniform(1.5, 2.5), "hawser"), 700))
