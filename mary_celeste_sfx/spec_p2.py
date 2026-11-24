"""Part 2 cue spec (New York -> Azores -> what is missing). Events: (t in shot s, sfx, kwargs, dB, pan)."""
from locs import LOC
SEED = 2
FADE_OUT = 3.0


def R(src, t, db_, pan=0.0, **kw):
    kw.setdefault("dur", 2.0)
    if "start" not in kw and "seg" not in kw:
        kw.setdefault("pick", "rand")
    return (t, "rec", dict(src=src, **kw), db_, pan)


HIT = lambda src, t, db_: (t, "rec", {"src": src, "pick": 0, "dur": 6.0}, db_, 0.0)

SHOTS = {
    "01": dict(loc="harbour", space="out", beds={"r_gulls": -6}, ev=[(0.4, "cart", {"dur": 4.5}, -4, -0.5), R("bell_31107", 1.6, -9, 0.6, seg=True, dur=3.0),
                                                                     (2.8, "gull", {}, -6, 0.4)]),
    "02": dict(loc="cabin_pier", space="room", ev=[(0.3, "nib", {"dur": 2.3}, -4, 0.0), R("barrel_675975", 1.4, -18, -0.3, dur=0.8)]),
    "03": dict(loc="cabin_pier", space="room", ev=[(0.0, "nib", {"dur": 1.5}, -3, 0.0), R("glass_104815", 1.7, -14, 0.2, start=0.0, dur=0.6), (1.95, "nib", {"dur": 0.6}, -6, 0.0)]),
    "04": dict(loc="harbour", space="out", beds={"r_laps": 0}, ev=[(0.6, "gull", {}, -8, -0.5), (1.8, "creak", {"kind": "hull"}, -10, 0.3)]),
    "06": dict(loc="harbour", space="deck", beds={"r_rope": -4, "r_creak": -6, "r_wind": -6}, ev=[(0.8, "creak", {"kind": "rope"}, -6, 0.3), (2.6, "creak", {"kind": "rope"}, -8, -0.3)]),
    "07": dict(loc="cabin_pier", space="room", ev=[R("toddler_209210", 1.3, -12, 0.2, start=0.0, dur=1.5), (2.2, "creak", {"kind": "hull"}, -12, -0.4)]),
    "08": dict(loc="cabin_pier", space="room", ev=[R("toddler_625686", 0.3, -12, 0.1, start=0.0, dur=1.6), R("cloth_19291", 0.9, -12, 0.0, start=0.0, dur=1.2)]),
    "09": dict(loc="parlour", space="room", beds={"r_fire": None, "r_wind_soft": -8}, ev=[]),
    "10": dict(loc="school", space="room", ev=[(0.3, "chalk_scrape", {"dur": 0.6}, -8, 0.0), (1.2, "chalk_scrape", {"dur": 0.5}, -9, 0.0)]),
    "11": dict(loc="cabin_pier", space="room", ev=[(0.0, "nib", {"dur": 0.5}, -5, 0.0), (1.6, "creak", {"kind": "hull"}, -10, 0.3)]),
    "12": dict(loc="cabin_pier", space="room", ev=[(0.1, "creak", {"kind": "hull"}, -8, 0.0), R("breath_615223", 0.8, -12, 0.0, start=0.0, dur=2.0)]),
    "13": dict(loc="maquette", space="room", beds={"r_harbour": -12}, ev=[]),
    "14": dict(loc="cabin_pier", space="room", ev=[(0.2, "ladder", {"steps": 3, "gap": 0.5}, -6, -0.2), (1.9, "wood_tap", {}, -5, 0.0),
                                                   R("cloth_475440", 2.3, -10, 0.2, seg=True, dur=2.0), (4.0, "footsteps", {"times": [0.0, 0.5]}, -8, 0.3)]),
    "15": dict(loc="harbour", space="out", ev=[R("rope_394222", 0.2, -4, -0.2, seg=True, dur=3.0), R("rope_137711", 1.0, -8, 0.2, seg=True, dur=1.5),
                                               R("barrel_810894", 2.4, -6, 0.4, seg=True, dur=2.0)]),
    "16": dict(loc="hold_ny", space="hold", ev=[R("barrel_675975", 0.3, -3, -0.3, dur=1.2), R("barrel_675975", 1.3, -5, 0.3, dur=1.2), (2.2, "wood_set", {}, -6, 0.0)]),
    "17": dict(loc="cabin_pier", space="room", ev=[(0.0, "nib", {"dur": 0.9}, -6, 0.0), R("barrel_675975", 1.0, -6, 0.0, dur=1.2)]),
    "18": dict(loc="harbour", space="deck", ev=[R("hammer_535629", 0.0, -3, 0.1, seg=True, dur=1.0)]),
    "19": dict(loc="cabin_pier", space="room", muffle=1200, ev=[R("hammer_535629", 0.1, -6, 0.0, seg=True, dur=2.2)]),
    "20": dict(loc="harbour", space="out", beds={"r_harbour_b": 0}, ev=[R("steam_587171", 0.0, -8, -0.3, seg=True, dur=3.0), (1.5, "gull", {}, -10, 0.5)]),
    "21": dict(loc="anchorage", space="out", ev=[R("chain_477129", 0.2, -4, 0.2, seg=True, dur=2.2), R("slosh_637974", 1.6, -8, 0.2, dur=1.5)]),
    "22": dict(loc="deck_mc", space="deck", beds={"r_flag": -3}, ev=[(0.4, "wind_gust", {"dur": 3.0}, -4, 0.3), (2.8, "wind_gust", {"dur": 2.0}, -6, -0.3)]),
    "23": dict(loc="cabin_dry", space="room", beds={"r_wind_soft": -10}, ev=[(0.3, "nib", {"dur": 2.4}, -5, 0.0), (1.8, "creak", {"kind": "hull"}, -10, -0.3)]),
    "24": dict(loc="deck_mc", space="deck", beds={"r_flag": -2}, ev=[(0.3, "whump", {}, -2, 0.0), (1.5, "creak", {"kind": "rope"}, -8, 0.3)]),
    "25": dict(loc="deck_mc", space="deck", ev=[(0.5, "paper", {"dur": 0.8}, -4, 0.0), (1.6, "wind_gust", {"dur": 1.2}, -8, 0.2)]),
    "26": dict(loc="sea_low", space="out", ev=[(0.0, "oars", {"dur": 4.0}, -4, -0.3), (1.2, "whump", {}, -6, 0.3), HIT("boom_559529", 0.15, -14)]),
    "28": dict(loc="dawn", space="out", beds={"bowwash": -8}, ev=[]),
    "29": dict(loc="deck_mc", space="deck", ev=[(1.0, "creak", {"kind": "rope"}, -9, 0.3)]),
    "30": dict(loc="cabin_dry", space="room", ev=[(0.3, "chalk_scrape", {"dur": 1.0}, -4, 0.0), (1.6, "chalk_scrape", {"dur": 1.0}, -5, 0.0)]),
    "31": dict(loc="cabin_dry", space="room", ev=[(0.2, "chalk_tap", {}, -4, 0.0), HIT("boom_408141", 1.1, -11)]),
    "32": dict(loc="cabin_dry", space="room", beds={"r_creak": -6}, ev=[(1.4, "creak", {"kind": "hull"}, -8, 0.3)]),
    "33": dict(loc="sea_low", space="out", beds={"r_wind": -3}, ev=[(0.6, "water_slap", {}, -6, 0.0)]),
    "34": dict(loc="cabin", space="hold", ev=[R("drawer_552153", 1.0, -4, -0.2, start=0.0, dur=2.0), R("drawer_146805", 3.4, -6, 0.2, start=0.0, dur=2.5),
                                              (5.2, "slosh", {"dur": 1.4}, -10, 0.0)]),
    "35": dict(loc="cabin", space="hold", ev=[(0.3, "knock", {"f0": 1700, "dec": 0.012}, -6, 0.0), HIT("boom_177242", 0.4, -16)]),
    "36": dict(loc="cabin_dry", space="room", beds={"r_clock": -6}, ev=[(0.5, "wheel", {"dur": 1.6, "spin": True}, -10, 0.0)]),
    "37": dict(loc="deck_dusk", space="deck", ev=[(0.7, "knock", {"f0": 2100, "dec": 0.01}, -8, 0.0)]),
    "38": dict(loc="cabin", space="hold", ev=[(0.4, "wood_set", {}, -6, 0.0), HIT("boom_177242", 0.6, -16)]),
    "39": dict(loc="cabin", space="hold", ev=[R("drawer_552153", 0.6, -5, 0.0, start=0.0, dur=2.0), (2.2, "lantern_creak", {}, -9, 0.3), R("cloth_475440", 4.4, -12, 0.0, seg=True, dur=1.5)]),
    "41": dict(loc="maquette", space="room", beds={"r_drone": -2, "drone": -6}, ev=[(3.1, "pin_tap", {}, -5, -0.3), (3.2, "pulse", {}, -9, 0.0),
                                                                                    (5.0, "pin_tap", {}, -5, 0.0), (5.1, "pulse", {}, -9, 0.0),
                                                                                    (6.5, "pin_tap", {}, -5, 0.3), (6.6, "pulse", {}, -9, 0.0)]),
    "42": dict(loc="deck_mc", space="deck", beds={"r_sea_soft": 0}, ev=[R("slosh_637974", 0.3, -4, 0.0, dur=2.5)]),
    "43": dict(loc="deck_mc", space="deck", ev=[R("rope_394222", 0.5, -5, -0.2, seg=True, dur=3.0), (4.4, "splash_below", {}, -6, 0.3)]),
    "44": dict(loc="deck_mc", space="deck", ev=[(0.5, "wood_tap", {}, -7, 0.0), (1.2, "wood_tap", {}, -9, 0.0), (2.2, "drip", {"into": "wood"}, -6, 0.0), (3.0, "drip", {"into": "wood"}, -8, 0.0)]),
    "45": dict(loc="deck_mc", space="deck", ev=[R("pump_588629", 0.5, -8, 0.2, seg=True, dur=2.5)]),
}

SILENCE = [
    (76.05, 76.70, -18, 0.4),    # beat before "That's the last letter anyone receives from the ship."
    (94.50, 95.50, -26, 0.4),    # "...the record goes blank." -> silence
    (126.20, 127.05, -18, 0.4),  # before "Look at what's missing together."
]
