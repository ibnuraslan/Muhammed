"""Part 3 cue spec (salvage voyage, gale, Gibraltar court). Events: (t in shot s, sfx, kwargs, dB, pan)."""
from locs import LOC
SEED = 3
FADE_OUT = 3.0


def R(src, t, db_, pan=0.0, **kw):
    kw.setdefault("dur", 2.0)
    if "start" not in kw and "seg" not in kw:
        kw.setdefault("pick", "rand")
    return (t, "rec", dict(src=src, **kw), db_, pan)


HIT = lambda src, t, db_: (t, "rec", {"src": src, "pick": 0, "dur": 6.0}, db_, 0.0)
T = lambda src, t, db_, pan=0.0: (t, "rec", {"src": src, "pick": 0, "dur": 10.0}, db_, pan)

SHOTS = {
    "p3_01": dict(loc="dg_deck", space="deck", ev=[(1.4, "creak", {"kind": "hull"}, -8, -0.3), (2.6, "footsteps", {"times": [0.0, 0.35]}, -8, 0.2)]),
    "p3_02": dict(loc="dg_deck", space="deck", ev=[(0.5, "wood_tap", {}, -9, 0.4), (1.1, "whump", {}, -8, 0.0)]),
    "p3_03": dict(loc="dg_deck", space="deck", ev=[R("rope_394222", 0.1, -5, -0.3, seg=True, dur=2.0), (1.4, "footsteps", {"times": [0.0, 0.45, 0.9]}, -5, 0.2)]),
    "p3_04": dict(loc="deck_mc", space="deck", ev=[(0.35, "boot", {}, -1, 0.0), HIT("boom_408141", 0.35, -11)]),
    "p3_05": dict(loc="sea_low", space="out", ev=[R("rope_137711", 0.2, -6, -0.2, seg=True, dur=1.2), (1.4, "wood_set", {}, -4, 0.2),
                                                  (2.1, "knock", {"f0": 540, "dec": 0.03}, -6, 0.3), (2.6, "water_slap", {}, -6, -0.3)]),
    "p3_06": dict(loc="cabin", space="hold", beds={"r_drips": -16}, ev=[(0.3, "wood_set", {}, -3, 0.0), (1.3, "knock", {"f0": 1500, "dec": 0.015}, -7, 0.2)]),
    "p3_07": dict(loc="deck_mc", space="deck", ev=[R("pump_580670", 0.0, -3, 0.0, seg=True, dur=1.8), R("slosh_382649", 0.7, -6, 0.3, dur=1.0)]),
    "p3_08": dict(loc="deck_mc", space="deck", beds={"r_flag": -4}, ev=[R("rope_394222", 0.2, -4, -0.2, seg=True, dur=2.2), (2.2, "whump", {}, 0, 0.0), (2.9, "whump", {}, -4, 0.0)]),
    "p3_09": dict(loc="sea_wide", space="out", beds={"bowwash": -6}, ev=[]),
    "p3_10": dict(loc="studio", space="room", beds={"r_clock": -8}, ev=[(0.2, "nib", {"dur": 1.5}, -6, 0.0)]),
    "p3_11": dict(loc="storm", space="out", ev=[T("thunder_244053", 0.1, -2, -0.3), (0.4, "hull_groan", {}, -4, 0.3), (1.0, "wave_slam", {}, 0, -0.2)]),
    "p3_12": dict(loc="storm", space="night", beds={"r_rain_b": -2}, ev=[(0.3, "wheel", {"dur": 1.8}, -5, 0.0), (1.2, "creak", {"kind": "hull"}, -6, 0.4)]),
    "p3_13": dict(loc="storm", space="out", beds={"wind_storm": -2}, ev=[T("thunder_399656", 0.7, -4, 0.3), (1.6, "wave_slam", {}, -3, 0.0)]),
    "p3_14": dict(loc="anchorage", space="out", ev=[R("chain_347837", 0.6, -8, 0.2, seg=True, dur=1.5), (1.6, "gull", {}, -10, -0.4)]),
    "p3_15": dict(loc="anchorage", space="out", beds={"r_gulls": -6}, ev=[(0.2, "gull", {}, -6, 0.4), R("chain_347837", 0.9, -10, -0.2, seg=True, dur=0.8)]),
    "p3_16": dict(loc="harbour", space="out", ev=[R("bell_31107", 0.4, -7, 0.5, seg=True, dur=3.4), R("chain_477129", 1.4, -6, -0.3, seg=True, dur=2.4), (0.8, "gull", {}, -6, -0.5)]),
    "p3_17": dict(loc="harbour", space="out", ev=[(0.4, "wood_tap", {}, -12, 0.4), (1.2, "wood_tap", {}, -13, 0.4), (2.0, "wood_tap", {}, -12, 0.4), (1.0, "gull", {}, -9, -0.4)]),
    "p3_18": dict(loc="office", space="room", ev=[(0.3, "nib", {"dur": 2.8}, -4, 0.0), R("breath_569568", 1.4, -12, 0.0, start=0.0, dur=3.0),
                                                  R("chair_475493", 3.5, -10, 0.2, seg=True, dur=1.2), (2.4, "gull", {}, -18, 0.6)]),
    "p3_19": dict(loc="office", space="room", ev=[R("breath_615223", 0.3, -10, 0.0, start=0.0, dur=2.5), R("chair_159645", 1.9, -10, 0.2, seg=True, dur=1.0)]),
    "p3_20": dict(loc="office", space="room", ev=[(0.0, "nib", {"dur": 0.9}, -5, 0.0), (2.6, "nib", {"dur": 1.8}, -5, 0.0)]),
    "p3_21": dict(loc="harbour", space="deck", ev=[(0.05, "hull_knock", {}, -4, 0.3), (0.6, "boot", {}, -3, -0.1), (0.95, "boot", {}, -5, 0.0)]),
    "p3_22": dict(loc="harbour", space="deck", ev=[R("hammer_173941", 0.3, -3, 0.0, dur=0.7), R("hammer_173941", 0.95, -4, 0.0, dur=0.7), R("hammer_173941", 1.6, -3, 0.0, dur=0.7)]),
    "p3_23": dict(loc="court", space="room", ev=[R("cloth_475440", 0.8, -12, -0.3, seg=True, dur=1.5), R("cough_743360", 2.6, -12, 0.4, start=0.0, dur=1.1)]),
    "p3_24": dict(loc="court", space="room", ev=[(0.5, "nib", {"dur": 3.5}, -6, 0.2)]),
    "p3_25": dict(loc="court", space="room", ev=[(0.4, "nib", {"dur": 3.6}, -7, 0.2)]),
    "p3_26": dict(loc="court", space="room", ev=[R("chair_475493", 0.4, -6, -0.2, seg=True, dur=1.4), R("cloth_475440", 1.7, -9, 0.0, seg=True, dur=1.8),
                                                 (3.6, "footsteps", {"times": [0.0, 0.6]}, -10, 0.2)]),
    "p3_27": dict(loc="court_quiet", space="room", ev=[]),
    "p3_28": dict(loc="court_quiet", space="room", beds={"r_drone": -10}, ev=[HIT("boom_559529", 1.3, -15)]),
    "p3_29": dict(loc="harbour", space="deck", ev=[(0.3, "footsteps", {"times": [0.0, 0.5, 1.0, 1.5]}, -5, 0.0), (1.2, "gull", {}, -9, 0.5)]),
    "p3_29b": dict(loc="underwater", space="cut", ev=[R("underwater_539822", 0.3, -6, 0.0, seg=True, dur=2.5), (1.0, "grit", {"dur": 2.4}, -20, 0.0)]),
    "p3_30": dict(loc="underwater", space="cut", ev=[R("underwater_539822", 0.2, -7, 0.0, seg=True, dur=1.8), (1.4, "wood_tap", {}, -12, 0.0)], muffle=900),
    "p3_31": dict(loc="harbour", space="deck", beds={"r_harbour": -6}, ev=[(0.2, "nib", {"dur": 1.2}, -6, 0.0), (2.6, "gull", {}, -9, -0.5)]),
    "p3_32": dict(loc="deck_found", space="deck", beds={"r_harbour": -10}, ev=[(0.5, "thud", {"f0": 90, "dec": 0.06}, -4, 0.0), R("cloth_19291", 0.8, -9, 0.0, start=0.0, dur=1.5)]),
    "p3_33": dict(loc="deck_found", space="deck", beds={"r_harbour": -12, "r_drone": -8}, ev=[(1.8, "breath", {}, -10, 0.0)]),
    "p3_34": dict(loc="cabin_dry", space="room", ev=[(0.8, "iron_scrape", {"dur": 1.4}, -6, 0.0), (0.9, "wood_scrape", {}, -10, 0.0)]),
    "p3_35": dict(loc="cabin_dry", space="room", ev=[R("sword_320521", 1.2, -2, 0.0, start=0.0, dur=3.0)]),
    "p3_36": dict(loc="cabin_dry", space="room", ev=[R("sword_581594", 0.0, -6, 0.0, start=1.2, dur=1.6), (1.2, "drip", {"into": "wood"}, -6, 0.0)]),
    "p3_37": dict(loc="studio", space="room", ev=[(0.4, "chalk_scrape", {"dur": 1.2}, -10, 0.0), R("glass_104815", 2.2, -6, 0.2, start=0.0, dur=1.0)]),
    "p3_38": dict(loc="studio", space="room", ev=[R("glass_104815", 1.35, -6, 0.0, start=0.0, dur=1.0), (1.36, "wood_set", {}, -10, 0.0), HIT("boom_408141", 1.6, -13)]),
    "p3_39": dict(loc="court", space="room", beds={"r_rain": -12, "r_court": -6}, ev=[(0.5, "nib", {"dur": 2.0}, -8, 0.0)]),
    "p3_40": dict(loc="court", space="room", ev=[(0.4, "paper", {"dur": 1.0}, -5, 0.0), (2.0, "paper", {"dur": 0.7}, -8, 0.2)]),
    "p3_41": dict(loc="court_quiet", space="room", ev=[R("chair_159645", 0.6, -8, 0.0, seg=True, dur=1.0)]),
    "p3_42": dict(loc="harbour", space="deck", ev=[(0.3, "footsteps", {"times": [0.0, 0.5, 1.0]}, -5, -0.2), (1.9, "wood_set", {}, -3, 0.2), (3.0, "wood_set", {}, -5, -0.2)]),
    "p3_43": dict(loc="sea_wide", space="out", beds={"r_flag": -6}, ev=[(0.5, "whump", {}, -2, 0.0), (1.6, "whump", {}, -4, 0.0)]),
}

SILENCE = [
    (116.80, 118.90, -30, 0.5),  # "The examination finds no trace of blood." - silence, then glass on wood
    (126.60, 127.45, -16, 0.4),  # before "No murder is established."
    (79.20, 82.90, -10, 0.8),    # the court falls quiet under Flood's question
]
