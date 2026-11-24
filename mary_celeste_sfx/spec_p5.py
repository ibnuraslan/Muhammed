"""Part 5 cue spec (the yawl, the story vs the record, what came home). Events: (t in shot s, sfx, kwargs, dB, pan)."""
from locs import LOC
SEED = 5
FADE_OUT = 6.0


def R(src, t, db_, pan=0.0, **kw):
    kw.setdefault("dur", 2.0)
    if "start" not in kw and "seg" not in kw:
        kw.setdefault("pick", "rand")
    return (t, "rec", dict(src=src, **kw), db_, pan)


HIT = lambda src, t, db_: (t, "rec", {"src": src, "pick": 0, "dur": 6.0}, db_, 0.0)

SHOTS = {
    "S01": dict(loc="sea_low", space="out", beds={"r_laps": -1}, ev=[(0.6, "creak", {"kind": "rope"}, -7, 0.3), (1.5, "knock", {"f0": 540, "dec": 0.03}, -7, -0.2),
                                                                     (2.9, "knock", {"f0": 500, "dec": 0.03}, -9, -0.2), (2.0, "hull_knock", {}, -9, 0.4)]),
    "S02": dict(loc="sea_low", space="out", beds={"r_laps": 0}, ev=[(1.2, "gull", {}, -14, 0.6), R("toddler_209210", 2.6, -16, -0.1, start=0.0, dur=1.5)]),
    "S03": dict(loc="sea_low", space="out", ev=[R("rope_137711", 0.3, -5, 0.0, seg=True, dur=2.2), (1.9, "water_slap", {}, -6, -0.2)]),
    "S04": dict(loc="sea_wide", space="out", beds={"r_flag": -5}, ev=[(0.4, "creak", {"kind": "hull"}, -12, 0.4), (0.8, "oars", {"dur": 3.0}, -10, -0.3)]),
    "S05": dict(loc="sea_low", space="out", ev=[(0.0, "oars", {"dur": 4.8}, -2, 0.0), (1.0, "creak", {"kind": "rope"}, -11, 0.4),
                                                R("breath_569568", 2.2, -14, 0.0, start=0.0, dur=2.5)]),
    "S06": dict(loc="maquette", space="room", ev=[(0.8, "pulse", {}, -6, 0.0), (2.6, "pulse", {}, -7, 0.0), (4.0, "pulse", {}, -8, 0.0)]),
    "S07": dict(loc="sea_low", space="out", beds={"r_wind": -4}, ev=[(0.0, "oars", {"dur": 1.6}, -5, 0.0)]),
    "S08": dict(loc="sea_wide", space="out", beds={"r_wind": -1}, ev=[(0.1, "wind_gust", {"dur": 2.4}, -3, 0.0), (1.3, "wave_slam", {}, 0, 0.2), HIT("boom_559529", 1.3, -11)]),
    "S09": dict(loc="cabin_dry", space="room", beds={"r_clock": -8, "r_lamp": -16}, ev=[]),
    "S10": dict(loc="cabin_dry", space="room", beds={"r_clock": -8, "r_lamp": -16}, ev=[R("chair_475493", 1.6, -9, 0.2, seg=True, dur=1.2)]),
    "S11": dict(loc="cabin", space="hold", ev=[(0.4, "drip", {}, -5, 0.0), (1.2, "slosh", {"dur": 1.6}, -8, 0.3), (2.4, "lantern_creak", {}, -7, 0.0), (3.4, "drip", {}, -7, 0.0)]),
    "S12": dict(loc="galley", space="hold", ev=[(0.1, "slosh", {"dur": 2.6, "muffle": 1500}, -6, 0.0), (0.9, "pot_roll", {}, -7, 0.3)]),
    "S13": dict(loc="cabin", space="hold", beds={"r_cabin": -3}, ev=[(0.5, "drip", {"into": "wood"}, -4, 0.0), (1.6, "hull_groan", {}, -6, -0.4), (3.2, "drip", {"into": "wood"}, -6, 0.0)]),
    "S14": dict(loc="cabin", space="hold", ev=[(0.4, "chalk_scrape", {"dur": 1.2}, -12, 0.0), (2.5, "drip", {"into": "wood"}, -6, 0.0)]),
    "S15": dict(loc="parlour", space="room", ev=[]),
    "S16": dict(loc="parlour", space="room", ev=[R("tissue_320153", 0.4, -8, 0.0, seg=True, dur=1.5), (1.8, "creak", {"kind": "rope"}, -14, 0.0)]),
    "S17": dict(loc="parlour", space="room", ev=[R("wax_759526", 1.4, -3, 0.0, start=0.0, dur=1.3)]),
    "S18": dict(loc="parlour", space="room", ev=[R("tissue_320153", 0.3, -6, 0.0, seg=True, dur=1.8)]),
    "S19": dict(loc="parlour", space="room", ev=[(0.4, "wood_set", {}, -6, 0.0), (0.45, "metal", {"f0": 900, "dec": 0.3, "strike": 0.3}, -14, 0.0)]),
    "S20": dict(loc="parlour", space="room", ev=[R("tissue_320153", 0.4, -9, 0.0, seg=True, dur=1.4)]),
    "S21": dict(loc="parlour", space="room", beds={"r_clock": None, "r_fire": None, "r_wind_soft": None},
                ev=[R("clock_125968", 1.2, -8, 0.0, start=0.0, dur=0.6), HIT("boom_408141", 0.2, -16)]),
    "S22": dict(loc="parlour", space="room", beds={"r_wind_soft": -6}, ev=[]),
    "S23": dict(loc="parlour", space="room", ev=[(0.6, "paper", {"dur": 0.8}, -8, 0.0), R("breath_615223", 4.2, -14, 0.0, start=0.0, dur=2.5)]),
    "S24": dict(loc="harbour", space="out", ev=[R("bell_353232", 0.8, -7, 0.4, start=0.0, dur=2.9), (1.6, "gull", {}, -8, -0.4), (2.4, "creak", {"kind": "rope"}, -10, 0.2)]),
    "S25": dict(loc="quay", space="out", ev=[R("barrel_810894", 0.3, -5, -0.3, seg=True, dur=2.0), (2.2, "barrel_knock2", {}, -4, 0.2)]),
    "S26": dict(loc="parlour", space="room", ev=[R("cloth_475440", 0.6, -10, 0.0, seg=True, dur=1.5), (3.0, "breath", {}, -14, 0.0)]),
    "S27": dict(loc="sea_sunset", space="out", ev=[HIT("boom_408141", 4.0, -14)]),
    "S28": dict(loc="sea_sunset", space="out", beds={"drone": -20}, ev=[]),
}

SILENCE = [
    (66.40, 67.20, -24, 0.4),   # before "One had a broken arm."
]
