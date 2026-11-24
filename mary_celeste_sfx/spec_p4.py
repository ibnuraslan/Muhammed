"""Part 4 cue spec. Bed levels are dB relative (0 = lead bed). Events: (t in shot s, sfx, kwargs, dB, pan[, bus])."""
SEED = 4
DUCK_DB = 6.0
SFX_IN_MIX_DB = -1.0
FADE_OUT = 3.0

from locs import LOC

SHOTS = {
    "S01": dict(loc="quay", space="out", ev=[(0.0, "cart", {"dur": 5.5}, -2, -0.6), (0.4, "gull", {}, -6, 0.5)]),
    "S02": dict(loc="quay", space="out", ev=[(0.25, "barrel_knock2", {}, 2, 0.1), (1.05, "chalk_X", {}, -3, 0.0)]),
    "S03": dict(loc="deck_dusk", space="deck", ev=[(1.5, "wind_gust", {"dur": 3.0}, -6, 0.3)]),
    "S05": dict(loc="cutaway", space="cut", ev=[(0.6, "trickle", {"dur": 7.0}, -9, 0.2), (2.2, "creak", {"kind": "hull"}, -4, -0.4),
                                                (5.6, "creak", {"kind": "hawser"}, -6, 0.4)]),
    "S06": dict(loc="hold", space="hold", ev=[(0.0, "flame", {"dur": 4.0}, -9, 0.0), (0.6, "lantern_creak", {}, -6, 0.1),
                                              (2.4, "lantern_creak", {}, -7, -0.1)]),
    "S07": dict(loc="sea_dusk", space="out", ev=[(0.8, "whump", {}, -2, 0.2), (4.5, "whump", {}, -5, -0.2), (2.5, "creak", {"kind": "rope"}, -10, 0.3)]),
    "S08": dict(loc="sea_found", space="out", ev=[]),
    "S09": dict(loc="deck_day", space="deck", ev=[(1.0, "sniff", {}, -6, 0.0)]),
    "S10": dict(loc="deck_day", space="deck", ev=[(0.3, "boot", {}, 0, 0.0), (1.7, "wood_tap", {}, -3, 0.1), (2.3, "wood_tap", {}, -5, 0.1)]),
    "S11": dict(loc="studio", space="room", ev=[(0.4, "wood_set", {}, 0, -0.3), (1.5, "wood_set", {}, -2, 0.3)]),
    "S12": dict(loc="studio", space="room", beds={"room": 2}, ev=[(1.8, "drip", {"into": "wood"}, -5, 0.0), (5.4, "drip", {"into": "wood"}, -7, 0.1)]),
    "S13": dict(loc="hold", space="hold", ev=[(0.5, "drip", {}, -4, 0.0), (1.8, "drip", {}, -6, 0.05), (3.0, "drip", {}, -5, -0.05)]),
    "S14": dict(loc="hold", space="hold", ev=[(0.1, "creak", {"kind": "hull"}, -5, -0.5), (0.9, "slosh", {"dur": 2.0}, -10, 0.3)]),
    "S15": dict(loc="deck_found", space="deck", beds={"wind_mid": -2}, ev=[(0.3, "wind_gust", {"dur": 3.0}, -2, 0.0)]),
    "S16": dict(loc="deck_day", space="deck", ev=[(0.0, "footsteps", {"times": [0.0, 0.55]}, -2, 0.0), (1.6, "head_turn", {}, -12, 0.0)]),
    "S17": dict(loc="deck_day", space="deck", ev=[(1.5, "iron_clank", {}, 0, -0.2)]),
    "S18": dict(loc="hold_ny", space="hold", ev=[(0.0, "hammers", {"dur": 4.8}, -11, -0.4), (0.8, "saw", {"dur": 3.6}, -14, 0.5)]),
    "S19": dict(loc="studio", space="room", ev=[(1.2, "paper", {}, -4, 0.2), (5.8, "paper", {"dur": 0.6}, -6, -0.2)]),
    "S20": dict(loc="xray", space="room", ev=[(0.2, "grit", {"dur": 1.6}, -4, 0.0), (2.4, "valve_slap", {}, -1, 0.0), (3.2, "grit", {"dur": 0.6}, -9, 0.0)]),
    "S21": dict(loc="night", space="night", ev=[(0.6, "rod_scrape", {"dur": 3.8}, -2, 0.0), (4.6, "iron_clank", {}, -6, 0.1)]),
    "S22": dict(loc="deck_found", space="deck", beds={"rigging": -14, "flog": -14}, ev=[]),
    "S23": dict(loc="studio", space="room", ev=[(1.0, "chalk_tap", {}, -4, 0.0), (1.3, "chalk_tap", {}, -6, 0.0)]),
    "S24": dict(loc="studio", space="room", ev=[(0.2, "paper", {"dur": 1.0}, -6, 0.0)]),
    "S25": dict(loc="studio", space="room", ev=[(0.5, "pin_tap", {}, -3, -0.2), (0.75, "pulse", {}, -6, 0.0)]),
    "S26": dict(loc="studio", space="room", ev=[(0.5, "pin_tap", {}, -3, 0.2), (0.75, "pulse", {}, -6, 0.0)]),
    "S27": dict(loc="studio", space="room", ev=[(0.4, "nib", {"dur": 6.0}, -9, 0.0), (0.2, "wind_gust", {"dur": 5.5}, -12, 0.0)]),
    "S28": dict(loc="studio", space="room", beds={"room": -12, "lamp": -40}, ev=[(0.12, "stop_click", {}, -4, 0.15)]),
    "S29": dict(loc="dawn", space="out", ev=[]),
    "S30": dict(loc="storm", space="out", ev=[(0.3, "wave_slam", {}, 4, -0.3), (1.6, "wave_slam", {}, 2, 0.4)]),
    "S31": dict(loc="night_mcu", space="night", ev=[(0.3, "line_hands", {"dur": 1.9}, -2, 0.0), (2.4, "drip", {"into": "wood"}, -7, 0.0),
                                                     (3.1, "drip", {"into": "wood"}, -8, 0.0), (4.0, "drip", {"into": "wood"}, -9, 0.0)]),
    "S32": dict(loc="cutaway", space="cut", beds={"drone": -3}, muffle=900, ev=[(1.5, "slosh", {"dur": 4.5, "muffle": 400}, -5, 0.0)]),
    "S33": dict(loc="dawn", space="out", ev=[(5.2, "breath", {}, -8, 0.0)]),
    "S34": dict(loc="studio", space="room", beds={"lamp": -16}, ev=[]),
    "S35": dict(loc="deck_day", space="deck", ev=[(0.3, "line_hands", {"dur": 1.0}, -6, 0.0), (1.3, "drip", {"into": "wood"}, -6, 0.0),
                                                  (2.2, "drip", {"into": "wood"}, -8, 0.0)]),
    "S36": dict(loc="deck_found", space="out", beds={"rigging": -16}, ev=[]),
}

# real silence before reveals: (start s, end s, depth dB, fade s)
SILENCE = [
    (29.7, 30.65, -20, 0.5),    # beat before "There are problems with that explanation." (S08)
    (119.30, 119.95, -40, 0.45),  # drift path complete -> silence -> "It could." (S28)
]

HIT = lambda src, db_, t=0.0: (t, "rec", {"src": src, "pick": 0, "dur": 6.0}, db_, 0.0)
SHOTS["S08"]["ev"].append(HIT("boom_559529", -11, 0.1))    # "There are problems with that explanation."
SHOTS["S28"]["ev"].append(HIT("boom_408141", -14, 0.15))   # "It could."
SHOTS["S30"]["ev"].append((0.1, "rec", {"src": "thunder_244053", "pick": 0, "dur": 8.0}, -3, -0.3))
SHOTS["S21"]["ev"].append((2.5, "rec", {"src": "thunder_193170", "pick": 0, "dur": 6.0}, -12, 0.4))
SHOTS["S36"].setdefault("beds", {})["r_drone"] = -10
