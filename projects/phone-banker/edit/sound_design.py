"""Full-film sound for "The Phone That Killed a Banker", like nvidia_doc/edit/sound_design.py: soft score pads per part,
ambience per shot (crossfaded at the cuts), soft spot effects for what we see, a boom under each chapter title, the
Seldom sting, the bed ducked under the voice, -14 LUFS. Two files on the SAME timeline as phone_banker_film.blend:
  out/deliver/phone_banker_AUDIO_with_voice.wav / _no_voice.wav  (+ mp3 previews)
  python edit/sound_design.py        (reads edit/film_edl.json, written by edit/make_film.py)
"""
import os, sys, json, subprocess, re, wave
import numpy as np
from scipy import signal
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from sfx_lib import *
import sfx_lib

EDL = json.load(open(os.path.join(HERE, "film_edl.json")))
N = int(round(EDL["end"] / FPS * SR)) + SR
T = lambda f: (f - 1) / FPS
M = {k: T(v) for k, v in EDL["markers"].items()}
END = T(EDL["end"] + 1)
sec = {"intro": (0.0, M["STING"]), "sting": (M["STING"], M["CH1"]), "ch1": (M["CH1"], M["CH2"]),
       "ch2": (M["CH2"], M["CH3"]), "ch3": (M["CH3"], END)}


def load_audio(path):
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".raw") as f:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", f.name], check=True)
        return np.fromfile(f.name, dtype=np.float32).astype(np.float64)


# ------------------------------------------------------------------------------------------------ voice
vo = np.zeros(N)
for name, f0, f1 in EDL["vo"]:
    if name != "VO sting":
        place(vo, load_audio(os.path.join(ROOT, "vo", name.split()[1] + "_vo.mp3")), T(f0))
vo = vo / np.abs(vo).max() * db(-3)

# ------------------------------------------------------------------------------------------------ ambience per shot
AMB = [("seldom", None), ("_bankoffice_", "room"), ("bank_traffic", "city"), ("bank_arrive_bank", "city"),
       ("bank_pullup", "city"), ("bank_steps", "city"), ("bank_detain", "rain"), ("bank_release", "rain"),
       ("bank_doorbell", "wind"), ("bank_seasons", "wind"), ("hospital_arrive", "night"), ("hospital_nightward", "night"),
       ("_hospital_", "hall"), ("_forlab_", "room"), ("_memorial_", "crowd"), ("court_doors", "hall"), ("_court_", "room"),
       ("closedtown_institute", "hall"), ("closedtown_kitchen", "night"), ("_closedtown_", "wind"),
       ("_station_", "rain"), ("_apartment_", "city"), ("_salisbury_", "city")]
def amb_for(name):
    for key, kind in AMB:
        if key in name:
            return kind
    return "room"


ambb = np.zeros(N)
for f0, f1, name in EDL["shots"]:
    kind = amb_for(name)
    if kind is None:
        continue
    t0, t1 = T(f0), T(f1)
    x = amb(kind, t1 - t0 + 0.4)
    if "salisbury" in name:
        x = x * db(-4)                             # a quiet English street
    place(ambb, fade_edges(x, 0.35, 0.35), max(0, t0 - 0.2))

# ------------------------------------------------------------------------------------------------ score
Dm = [("D", 3), ("F", 3), ("A", 3)]; Bb = [("Bb", 2), ("D", 3), ("F", 3)]; F = [("F", 2), ("A", 2), ("C", 3)]
C = [("C", 3), ("E", 3), ("G", 3)]; Gm = [("G", 2), ("Bb", 2), ("D", 3)]; A = [("A", 2), ("C#", 3), ("E", 3)]
Am = [("A", 2), ("C", 3), ("E", 3)]; Em = [("E", 2), ("G", 2), ("B", 2)]
music = np.zeros(N)
place(music, score_section(*sec["intro"], [Am, F, Dm, Em], [("E", 5), ("A", 5), ("C", 6), ("B", 5)], False, -21), sec["intro"][0])
place(music, score_section(*sec["ch1"], [Dm, Bb, Gm, A], [("A", 4), ("D", 5), ("F", 5), ("E", 5)], True, -22), sec["ch1"][0])
place(music, score_section(*sec["ch2"], [Gm, Dm, Bb, A], [("D", 5), ("C", 5), ("Bb", 4), ("A", 4)], False, -22, 1000), sec["ch2"][0])
place(music, score_section(*sec["ch3"], [Dm, Am, Bb, Dm], [("F", 5), ("E", 5), ("D", 5), ("A", 4)], False, -21, 950), sec["ch3"][0])

fx = np.zeros(N)
place(fx, sting() * db(-4), sec["sting"][0])       # the 6 s evidence-bag sting (same sound as brand/seldom_sting_sfx.wav)
for key in ("ch1", "ch2", "ch3"):                  # boom under each chapter title (the card fades in from frame 12)
    place(fx, boom(-15), sec[key][0] + 0.55)
for key in ("ch2", "ch3"):                         # a soft swell into the later chapters
    place(fx, swell(2.2, -24), sec[key][0] - 2.2)


# ------------------------------------------------------------------------------------------------ spot effects (soft)
def ring(d=1.6):                                   # a muffled Russian phone ring (425 Hz, soft edges)
    n = int(d * SR); t = np.arange(n) / SR
    return filt(np.sin(2 * np.pi * 425 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 16 * t)), "lowpass", 2000) * fade_edges(np.ones(n), 0.04, 0.08) * 0.4


def dial(d=1.0):                                   # rotary dial: soft ratchet taps, then the return
    out = np.zeros(int(d * SR))
    for k, tt in enumerate(np.arange(0.05, d - 0.1, 0.075)):
        place(out, tap(0.05, 1500, 4500, 0.008) * (0.8 if k % 2 else 0.6), tt)
    return out


def ventilator(d):                                 # bellows breath every 4 s
    out = np.zeros(int(d * SR))
    for tt in np.arange(0.3, d - 1.0, 4.0):
        place(out, slide(1.6, 200, 1200) * 0.8, tt); place(out, slide(1.4, 150, 900) * 0.5, tt + 1.9)
    return out


def monitor(d, every=1.1, f=960):
    out = np.zeros(int(d * SR))
    for tt in np.arange(0.3, d - 0.2, every):
        place(out, beep(f, 0.12), tt)
    return out


def spot_events(name, d):
    at = lambda frac: frac * d
    ev = []
    def has(k): return k in name
    if has("bank_pullup"):
        ev += [(0.0, car_pass(min(d, 3.4), 0.55) * 0.9, -24), (at(0.8), thump(75, 0.6, 0.09) + tap(0.12, 300, 1500, 0.05) * 0.5, -22)]
    elif has("bank_steps") or has("bank_arrive_bank") or has("bank_release") or has("steps_out"):
        ev += [(0.0, steps(d, 0.55, 105, 0.8), -29)]
    elif has("bankoffice_search"):
        ev += [(0.1, slide(0.8, 200, 1400) + thump(80, 0.4, 0.06) * 0.4, -26), (at(0.65), paper(0.5), -28)]
    elif has("bank_traffic"):
        ev += [(at(0.1), car_pass(3.0, 0.5), -25), (at(0.55), car_pass(2.6, 0.5), -28)]
    elif has("bankoffice_dial"):
        ev += [(0.2, dial(min(1.2, d - 0.4)), -30)]
    elif has("bankoffice_note") or has("forlab_compare") or has("forlab_saratov") or has("court_prosecutor"):
        ev += [(at(0.45), paper(0.5, 0.16), -29)]
    elif has("brother_in"):
        ev += [(0.2, clank(520, 0.4) * 0.5 + tap(0.1, 500, 2000, 0.03), -29), (0.6, steps(min(3.0, d - 0.6), 0.6, 100, 0.7), -30)]
    elif has("brother_help") or has("visitor_in") or has("apartment_arrest") or has("court_led_out"):
        ev += [(0.0, steps(min(d, 5.0), 0.6, 100, 0.8), -29)]
        if has("arrest"):
            ev += [(at(0.85), thump(75, 0.6, 0.09) + tap(0.12, 300, 1500, 0.05) * 0.5, -24)]
        if has("led_out"):
            ev += [(at(0.85), thump(70, 0.8, 0.12) + clank(260, 0.8) * 0.3, -22)]
    elif has("hospital_gurney"):
        ev += [(0.0, slide(d, 150, 900) * 0.7 + steps(d, 0.5, 110, 0.5), -27)]
    elif has("hospital_ward") or has("hospital_doctor"):
        ev += [(0.0, monitor(d), -36)]
    elif has("hospital_arrive"):
        ev += [(0.0, car_pass(min(d, 4.0), 0.6), -26), (at(0.8), thump(75, 0.6, 0.09), -26)]
    elif has("hospital_dawn"):
        ev += [(at(0.6), slide(1.2, 600, 3500) * 0.8, -31)]
    elif has("path_read"):
        ev += [(at(0.3), paper(0.5, 0.16), -30), (at(0.7), paper(0.5, 0.16), -30)]
    elif has("path_light"):
        ev += [(1.6, thump(110, 0.4, 0.05, 0) * 0.5 + paper(0.4, 0.08), -27), (3.9, tap(0.06, 1200, 4000, 0.01) + thump(200, 0.1, 0.02, 0) * 0.4, -26)]
    elif has("forlab_recorder"):
        for k in range(int(d / 0.9)):
            ev += [(0.3 + k * 0.9, tap(0.04, 2000, 5000, 0.008), -38 - k * 0.6)]
    elif has("hospital_nightward"):
        ev += [(0.0, ventilator(d), -27), (0.0, monitor(d, 1.4, 880), -40)]
    elif has("bankoffice_sealed") or has("bankoffice_reads") or has("court_volumes"):
        ev += [(at(0.4), paper(0.5, 0.16), -30), (at(0.75), slide(0.4, 900, 4000), -32)]
    elif has("bankoffice_bag"):
        ev += [(at(0.35), slide(1.4, 1200, 6000) * 0.7, -30)]
    elif has("ante_trolley"):
        ev += [(at(0.4), clank(300, 1.0) * 0.6, -28)]
    elif has("bankoffice_ledger"):
        ev += [(at(0.3), paper(0.45, 0.14), -29), (at(0.65), paper(0.45, 0.14), -29)]
    elif has("bank_detain"):
        ev += [(at(0.3), steps(d * 0.5, 0.45, 110, 0.7), -29), (at(0.8), thump(75, 0.6, 0.09) + tap(0.12, 300, 1500, 0.05) * 0.5, -22)]
    elif has("gc_print"):
        ev += [(0.4, beep(1200, 0.15), -32), (1.0, slide(d - 1.6, 1500, 5000) * 0.35, -36)]
    elif has("closedtown_checkpoint"):
        ev += [(0.0, car_pass(min(d, 3.8), 0.6) + thump(45, 2.5, 0.8, 0) * 0.3, -24)]
    elif has("closedtown_institute"):
        for tt in (1.1, 1.18, 2.7, 2.76, 2.84, 4.9):
            if tt < d: ev += [(tt, tap(0.04, 2500, 6000, 0.006), -36)]
    elif has("station_platform"):
        ev += [(0.4, horn(110, 2.4), -34), (1.0, car_pass(d - 1.0, 0.35) * 0.9 + thump(40, d - 1.0, 3.0, 0) * 0.3, -24)]
    elif has("forlab_ampoules"):
        ev += [(at(0.4), glass(2600, 1.0), -32), (at(0.6), glass(3000, 1.0), -35)]
    elif has("slide_file") or has("forlab_specialists"):
        ev += [(at(0.35), slide(0.7, 900, 4500), -29)]
    elif has("bank_doorbell"):
        for t0 in (0.8, 3.6):
            if t0 + 0.6 < d: ev += [(t0, beep(660, 0.35) * 0.8, -32), (t0 + 0.38, beep(523, 0.5) * 0.8, -32)]
    elif has("court_doors"):
        ev += [(at(0.55), thump(70, 1.6, 0.18) + filt(rng.standard_normal(int(1.6 * SR)), "lowpass", 400) * env_ad(int(1.6 * SR), 0.003, 0.05) * 0.4, -18)]
    elif has("court_verdict"):
        ev += [(0.3, slide(1.6, 200, 1200) * 0.6, -31)]               # the room standing up
    elif has("archive_dark"):
        for k in range(4):
            ev += [(d * (0.22 + 0.6 * k / 3), thump(55, 1.2, 0.22, 0.1) + clank(140, 1.0) * 0.2, -24)]
    elif has("salisbury_street"):
        for k, tt in enumerate((1.0, 1.15, 3.4, 3.52, 6.2, 6.33, 8.0)):
            if tt < d: ev += [(tt, chirp(0.08, 3400 + 300 * (k % 3), 4300), -38)]
    elif has("photocopies"):
        for tt in (at(0.3), at(0.55), at(0.8)):
            ev += [(tt, tap(0.05, 1500, 5000, 0.01) + tap(0.08, 800, 3000, 0.02) * 0.6, -30)]
    elif has("case_close"):                         # designed 7 s, spread over the cut: lid, then the lights
        k = d / 7.0
        ev += [(0.8 * k, slide(2.4 * k, 200, 1200) * 0.5, -32), (3.2 * k, thump(70, 0.9, 0.12) + clank(260, 1.0) * 0.4, -19)]
        for i, s_ in enumerate((4.0, 4.5, 5.0, 5.8)):
            ev += [(s_ * k, thump(55, 1.2, 0.22, 0.1) + clank(140, 1.0) * 0.2, -24 - i)]
    return ev


spot = np.zeros(N)
for f0, f1, name in EDL["shots"]:
    d = T(f1) - T(f0)
    for tt, x, lvl in spot_events(name, d):
        if tt < d:
            place(spot, reverb(np.asarray(x, dtype=float), 0.22) * db(lvl), T(f0) + tt)

# the intro fades into the sting; nothing but the sting under the logo; Chapter 1 fades in from black
for buf in (music, ambb, spot):
    a, b = int((sec["sting"][0] - 1.0) * SR), int(sec["sting"][0] * SR)
    buf[a:b] *= np.cos(np.linspace(0, np.pi / 2, b - a)) ** 2
    buf[b:int((sec["ch1"][0] + 0.3) * SR)] = 0
a = int(sec["ch1"][0] * SR); b = a + SR
for buf in (music, ambb):
    buf[a:b] *= np.sin(np.linspace(0, np.pi / 2, b - a)) ** 2
# the voice fades with the intro picture (as the VO strip does in the film file)
a, b = int((sec["sting"][0] - 1.0) * SR), int(sec["sting"][0] * SR)
vo[a:b] *= np.linspace(1, 0, b - a); vo[b:int(sec["ch1"][0] * SR)] = 0
# film end: everything out over the last 2 s
a = int((END - 2.0) * SR)
for buf in (music, ambb, spot, fx):
    buf[a:] *= np.cos(np.linspace(0, np.pi / 2, len(buf) - a)) ** 2

# duck the bed under the voice (about 7 dB), smooth attack and release
env = np.abs(vo); env = signal.sosfiltfilt(sos("lowpass", 3), env); env = env / (env.max() + 1e-9)
duck = 1 - 0.6 * np.clip(env * 4, 0, 1)
music *= duck; ambb *= 0.5 + 0.5 * duck; spot *= 0.75 + 0.25 * duck


def stereo(with_vo):
    bed = music + ambb * db(2)
    wide = np.roll(music * 0.5 + ambb * 0.5, int(0.011 * SR))
    v = vo if with_vo else 0.0
    Lc = v + fx + spot + bed
    Rc = v + fx + np.roll(spot, int(0.004 * SR)) + bed * 0.5 + wide
    return np.stack([Lc, Rc], 1)[:int(round(EDL["end"] / FPS * SR))]


outdir = os.path.join(ROOT, "out", "deliver"); os.makedirs(outdir, exist_ok=True)
full = stereo(True); pk = np.abs(full).max() / 0.95
def write(path, st):
    st = np.tanh(st / pk * 1.05) / np.tanh(1.05)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
raw_v, raw_n = os.path.join(outdir, "_v.wav"), os.path.join(outdir, "_n.wav")
write(raw_v, full); write(raw_n, stereo(False))
# one gain for both (measured on the voice version -> -14 LUFS), so the two files line up and swap cleanly
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw_v, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", m)[-1]); g = -14.0 - I
for src, dst in ((raw_v, "phone_banker_AUDIO_with_voice"), (raw_n, "phone_banker_AUDIO_no_voice")):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", f"volume={g:.2f}dB,alimiter=limit=0.89:level=false", "-ar", str(SR),
                    os.path.join(outdir, dst + ".wav")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(outdir, dst + ".wav"), "-b:a", "256k", os.path.join(outdir, dst + ".mp3")], check=True)
    os.remove(src)
print("saved", outdir, round(len(full) / SR, 3), "s,", EDL["end"], "frames")
