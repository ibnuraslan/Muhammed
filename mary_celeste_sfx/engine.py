"""Render the SFX stem and the VO mix for one part from a cue spec.
python3 -I engine.py <spec.py> <timings.json> <vo.mp3> <frames> <outdir> <tag>"""
import sys, os, json, subprocess, importlib.util
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfxlib as L

SR, FPS = L.SR, 24

BEDS = {
    "sea_calm": lambda N, r: L.bed_sea(N, r, False),
    "sea_heavy": lambda N, r: L.bed_sea(N, r, True),
    "wind_light": lambda N, r: L.bed_wind(N, r, 0.15, 0.08),
    "wind_mid": lambda N, r: L.bed_wind(N, r, 0.45, 0.25),
    "wind_storm": lambda N, r: L.bed_wind(N, r, 1.0, 0.7),
    "rigging": lambda N, r: L.bed_events(N, r, lambda q: L.creak(q, kind="rope") if q.uniform() < 0.7 else L.knock(q, q.uniform(700, 950), 0.03, 0.7), 0.9, (0.2, 0.9)),
    "hull": lambda N, r: L.bed_events(N, r, lambda q: L.creak(q, kind="hull"), 0.45, (0.3, 1.0), 0.6),
    "hawser": lambda N, r: L.bed_events(N, r, lambda q: L.creak(q, kind="hawser"), 0.5, (0.4, 1.0), 0.6),
    "harbour": L.bed_harbour,
    "hold": L.bed_hold,
    "room": L.bed_room,
    "drone": L.bed_drone,
    "rain": lambda N, r: L.bed_rain(N, r, False),
    "rain_heavy": lambda N, r: L.bed_rain(N, r, True),
    "flog": L.bed_flog,
    "bowwash": L.bed_bowwash,
    "gulls_far": lambda N, r: L.bed_events(N, r, lambda q: L.gull(q, far=True), 0.25, (0.3, 1.0), 1.0),
    "lamp": lambda N, r: np.stack([L.bp(L.white(N, r), 2500, 9000), L.bp(L.white(N, r), 2500, 9000)]) * L.smooth_rand(N, r, 4, 0.7, 1.0),
    "drips": lambda N, r: L.bed_events(N, r, lambda q: L.drip(q), 0.8, (0.2, 1.0), 0.6),
    "laps": lambda N, r: L.bed_events(N, r, lambda q: L.sfx_slosh(q, q.uniform(0.4, 0.9), 1000), 1.5, (0.3, 1.0), 0.5),
    "flame": lambda N, r: np.stack([L.sfx_flame(r, N / SR), L.sfx_flame(r, N / SR)]),
}
BED_REF_RMS_DB = -30.0

SPACES = {  # rt60, damping Hz, wet
    "out": (0.25, 6000, 0.06),
    "deck": (0.45, 5000, 0.12),
    "hold": (1.1, 2500, 0.35),
    "room": (0.55, 4500, 0.18),
    "cut": (1.6, 3500, 0.3),
    "night": (0.5, 4000, 0.15),
}


def db(x):
    return 10 ** (x / 20)


def load_spec(path):
    spec = importlib.util.spec_from_file_location("spec", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)


def gain_curve(N, segments, xf=0.25):
    """segments: list of (start_s, end_s, gain_lin). raised-cosine crossfades centred on each boundary"""
    g = np.zeros(N, np.float32)
    for (a, b, v) in segments:
        if v <= 0:
            continue
        ia, ib = L.n_(a), L.n_(b)
        e = np.zeros(N, np.float32)
        h = L.n_(xf / 2)
        lo, hi = max(0, ia - h), min(N, ib + h)
        e[lo:hi] = 1
        if ia > 0:
            ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, 2 * h))
            s0 = ia - h
            idx = np.arange(s0, s0 + 2 * h)
            ok = (idx >= 0) & (idx < N)
            e[idx[ok]] = ramp[ok]
        if ib < N:
            ramp = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, 2 * h))
            s0 = ib - h
            idx = np.arange(s0, s0 + 2 * h)
            ok = (idx >= 0) & (idx < N)
            e[idx[ok]] = ramp[ok]
        g += v * e
    return g


def true_peak_limit(x, ceiling_db=-1.0, look=0.004, rel=0.12):
    """x (2,N). gain from 4x-oversampled peak; lookahead min-filter + window smooth stays <= needed gain"""
    from scipy.ndimage import minimum_filter1d
    ceil = db(ceiling_db - 0.2)
    up = signal.resample_poly(x, 4, 1, axis=1)
    n = x.shape[1]
    pk = np.max(np.abs(up[:, :n * 4]), axis=0).reshape(-1, 4).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    if need.min() >= 1.0:
        return x
    w = L.n_(look)
    g = minimum_filter1d(need, 2 * w + 1)
    k = np.hanning(2 * w + 3)[1:-1]
    k /= k.sum()
    gs = np.convolve(g, k, "same")
    inv = 1 - gs
    a = np.exp(-1 / (rel * SR))
    inv = np.maximum(inv, signal.lfilter([1 - a], [1, -a], inv) * 1.0)
    gs = np.minimum(1 - inv, gs)
    return (x * gs).astype(np.float32)


def measure_tp(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    tail = out[out.rfind("Summary:"):]
    I = float(tail.split("I:")[1].split("LUFS")[0])
    TP = float(tail.split("Peak:")[1].split("dBFS")[0])
    return I, TP


def render(spec_path, tim_path, vo_path, frames, outdir, tag):
    sp = load_spec(spec_path)
    tim = json.load(open(tim_path))
    if not isinstance(next(iter(tim.values())), dict):  # P1 style: {shot: seconds} in edit order
        st, t2 = 0, {}
        for k, v in tim.items():
            n = int(round(v * FPS))
            t2[k] = {"start": st, "frames": n}
            st += n
        tim = t2
    N = int(round(frames / FPS * SR))
    T = N / SR
    order = sorted(tim, key=lambda k: tim[k]["start"])
    shots = [(k, tim[k]["start"] / FPS, (tim[k]["start"] + tim[k]["frames"]) / FPS) for k in order]
    shots[-1] = (shots[-1][0], shots[-1][1], T)
    seed = sp.SEED

    for k in sp.SHOTS:
        for ev in sp.SHOTS[k].get("ev", []):
            assert getattr(L, "sfx_" + ev[1], None) or getattr(L, ev[1], None), ev[1]
        assert k in tim, k
    # ---- beds
    used = sorted({b for k, a, e in shots for b in sp.LOC[sp.SHOTS[k]["loc"]]} | {b for k in sp.SHOTS for b in sp.SHOTS[k].get("beds", {})})
    beds = np.zeros((2, N), np.float32)
    for i, name in enumerate(used):
        r = L.rng(seed * 100 + i)
        x = BEDS[name](N, r).astype(np.float32)
        x *= db(BED_REF_RMS_DB - rms_db(x))
        segs = []
        for k, a, e in shots:
            levels = dict(sp.LOC[sp.SHOTS[k]["loc"]])
            levels.update(sp.SHOTS[k].get("beds", {}))
            if name in levels and levels[name] is not None:
                segs.append((a, e, db(levels[name])))
        g = gain_curve(N, segs, getattr(sp, "XFADE", 0.25))
        beds += x * g
        print("bed", name, flush=True)
    # fade in / out of the part
    beds *= L.env_win(N, 0.5)

    # ---- events into space buses
    buses = {s: np.zeros((2, N), np.float32) for s in SPACES}
    cues = []
    r = L.rng(seed * 7 + 3)
    for k, a, e in shots:
        s = sp.SHOTS[k]
        space = s.get("space", "deck")
        for ev in s.get("ev", []):
            t, name = ev[0], ev[1]
            kw = ev[2] if len(ev) > 2 else {}
            gdb = ev[3] if len(ev) > 3 else 0
            pan = ev[4] if len(ev) > 4 else 0.0
            fn = getattr(L, "sfx_" + name, None) or getattr(L, name)
            m = fn(r, **kw)
            muffle = s.get("muffle")
            if muffle:
                m = L.lp(m, muffle)
            m = m / (np.sqrt(np.mean(m ** 2)) + 1e-9) * db(-24 + gdb)
            ta = a + t
            L.add(buses[ev[5] if len(ev) > 5 else space], L.stereo(m, pan, 0.5, r), L.n_(ta))
            cues.append((ta, k, name.replace("_", " ") + (f" ({', '.join(f'{x}={y}' for x, y in kw.items())})" if kw else "")))
    ev_out = np.zeros((2, N), np.float32)
    for sname, x in buses.items():
        if not np.any(x):
            continue
        rt, damp, wet = SPACES[sname]
        h = L.ir(L.rng(seed + len(sname)), rt, damp)
        w = np.stack([signal.fftconvolve(x[c], h[c])[:N] for c in range(2)])
        ev_out += x * (1 - wet * 0.5) + w * wet * 3
    # ---- silences before reveals (beds only; events inside stay)
    sil = np.ones(N, np.float32)
    for (t0, t1, depth, fade) in getattr(sp, "SILENCE", []):
        segs = gain_curve(N, [(t0, t1, 1.0)], fade)
        sil *= (1 - segs * (1 - db(depth))).astype(np.float32)
    stem = beds * sil + ev_out
    # end: everything fades over the last seconds
    fo = getattr(sp, "FADE_OUT", 2.0)
    k = L.n_(fo)
    stem[:, -k:] *= np.linspace(1, 0, k) ** 2

    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(stem.T.astype(np.float64))
    stem *= db(-20.0 - lufs)
    stem = true_peak_limit(stem, -1.0)
    os.makedirs(outdir, exist_ok=True)
    p_sfx = os.path.join(outdir, f"MaryCeleste_{tag}_SFX.wav")
    sf.write(p_sfx, stem.T, SR, subtype="PCM_24")

    # ---- VO mix
    vo_wav = os.path.join(outdir, "_vo48.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vo_path, "-ar", str(SR), "-ac", "1", vo_wav], check=True)
    vo, _ = sf.read(vo_wav, dtype="float32")
    os.remove(vo_wav)
    v = np.zeros(N, np.float32)
    v[:min(N, len(vo))] = vo[:N]
    vl = meter.integrated_loudness(v.astype(np.float64))
    v *= db(-15.0 - vl)
    # sidechain ducking from the VO envelope
    env = np.sqrt(signal.lfilter([1 - np.exp(-1 / (0.03 * SR))], [1, -np.exp(-1 / (0.03 * SR))], v ** 2))
    edb = 20 * np.log10(env + 1e-9)
    amt = np.clip((edb + 50) / 12, 0, 1)
    duck_db = getattr(sp, "DUCK_DB", 6.0)
    gr = -duck_db * amt
    # attack 60 ms, release 450 ms on the gain-reduction curve
    from scipy.ndimage import maximum_filter1d
    gr_hold = -maximum_filter1d(-gr, L.n_(0.25))
    a_r = np.exp(-1 / (0.45 * SR))
    sm = signal.lfilter([1 - a_r], [1, -a_r], gr_hold)
    sm = np.minimum(sm, signal.lfilter([1 - np.exp(-1 / (0.06 * SR))], [1, -np.exp(-1 / (0.06 * SR))], gr_hold))
    duck = db(sm).astype(np.float32)
    sfx_in_mix = stem * duck * db(getattr(sp, "SFX_IN_MIX_DB", 0.0))
    mix = sfx_in_mix + np.stack([v, v]) * 1.0
    lm = meter.integrated_loudness(mix.T.astype(np.float64))
    mix *= db(-14.0 - lm)
    mix = true_peak_limit(mix, -1.0)
    for _ in range(3):
        lm = meter.integrated_loudness(mix.T.astype(np.float64))
        if abs(lm + 14) < 0.15:
            break
        mix = true_peak_limit(mix * db(-14.0 - lm), -1.0)
    p_mix = os.path.join(outdir, f"MaryCeleste_{tag}_MIX.wav")
    sf.write(p_mix, mix.T, SR, subtype="PCM_24")

    # ---- cue sheet
    cues.sort()
    with open(os.path.join(outdir, f"MaryCeleste_{tag}_CUES.txt"), "w") as fh:
        def tc(x):
            m, s = divmod(x, 60)
            return f"{int(m):02d}:{s:05.2f}"
        fh.write(f"Mary Celeste {tag} - SFX cue sheet (mm:ss.ss, from 00:00 of the part; 48 kHz)\n\n")
        fh.write("AMBIENCE BEDS by shot (dB relative; crossfaded at cuts)\n")
        for k, a, e in shots:
            levels = dict(sp.LOC[sp.SHOTS[k]["loc"]])
            levels.update(sp.SHOTS[k].get("beds", {}))
            bl = ", ".join(f"{b}" for b, v in levels.items() if v is not None)
            fh.write(f"  {tc(a)}  {k:4s} [{sp.SHOTS[k]['loc']}] {bl}\n")
        if getattr(sp, "SILENCE", None):
            fh.write("\nSILENCES (beds pulled down before a reveal)\n")
            for t0, t1, d, f in sp.SILENCE:
                fh.write(f"  {tc(t0)} - {tc(t1)}  beds {d:+.0f} dB\n")
        for note in getattr(sp, "NOTES", []):
            fh.write("\nNOTE: " + note + "\n")
        fh.write("\nSPOT EFFECTS\n")
        for ta, k, name in cues:
            fh.write(f"  {tc(ta)}  {k:4s} {name}\n")
    for p in (p_sfx, p_mix):
        I, TP = measure_tp(p)
        print(os.path.basename(p), f"I={I} LUFS  TP={TP} dBTP  {os.path.getsize(p) / 1e6:.1f} MB  {sf.info(p).frames} samples")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6])
