"""Part 1 cue spec. Events: (t in shot s, sfx, kwargs, dB, pan)."""
SEED = 1
DUCK_DB = 6.0
SFX_IN_MIX_DB = -1.0
FADE_OUT = 3.0

LOC = {
    "sea_low":  {"sea_calm": 0, "wind_light": -4, "flog": -12, "hull": -9, "laps": -8},
    "sea_wide": {"sea_calm": 0, "wind_mid": -4, "bowwash": -6, "flog": -10, "rigging": -12},
    "sea_far":  {"sea_calm": -2, "wind_mid": -4},
    "sea_dg":   {"sea_calm": 0, "wind_mid": -3, "bowwash": -4, "rigging": -10},
    "deck_mc":  {"sea_calm": -3, "wind_mid": -4, "rigging": -6, "hull": -7, "flog": -9},
    "dg_deck":  {"sea_calm": -3, "wind_mid": -2, "rigging": -5, "hull": -7, "bowwash": -10},
    "cabin":    {"hold": 0, "drips": -8, "hull": -14},
    "galley":   {"hold": -1, "drips": -5, "laps": -10},
    "dg_cabin": {"hold": -1, "hull": -10, "lamp": -28},
    "studio":   {"room": 0, "lamp": -22},
}

SHOTS = {
    "S01": dict(loc="sea_low", space="out", ev=[(0.2, "knock", {"f0": 560, "dec": 0.03}, -4, 0.4), (0.9, "knock", {"f0": 520, "dec": 0.03}, -6, 0.4)]),
    "S02": dict(loc="deck_mc", space="deck", ev=[(0.0, "water_slap", {}, -6, -0.4), (0.45, "boot", {}, 0, 0.0), (1.0, "hand_slap", {}, -2, 0.3)]),
    "S03": dict(loc="deck_mc", space="deck", ev=[(0.0, "footsteps", {"times": [0.0, 0.45, 0.9]}, -2, 0.0), (0.6, "creak", {"kind": "rope"}, -10, 0.5)]),
    "S04": dict(loc="cabin", space="hold", beds={"sea_calm": -8, "wind_mid": -12}, ev=[(0.1, "ladder", {"steps": 3}, -7, 0.0)]),
    "S05": dict(loc="cabin", space="hold", ev=[(0.3, "drip", {}, -5, 0.1), (0.8, "lantern_creak", {}, -6, 0.0), (1.9, "hull_groan", {}, -4, -0.4), (2.6, "drip", {}, -7, 0.1)]),
    "S06": dict(loc="cabin", space="hold", ev=[(0.25, "lantern_creak", {}, -6, 0.0), (1.0, "drip", {}, -5, 0.0)]),
    "S07": dict(loc="cabin", space="hold", ev=[(0.5, "lantern_creak", {}, -8, 0.1), (1.6, "breath", {}, -8, 0.0), (2.8, "hull_groan", {}, -8, 0.5)]),
    "S08": dict(loc="cabin", space="hold", ev=[(0.2, "lantern_creak", {}, -6, 0.0), (0.9, "foot_water", {}, -3, 0.1)]),
    "S09": dict(loc="cabin", space="hold", ev=[(0.28, "drip", {}, -3, 0.0), (1.3, "hull_groan", {}, -9, -0.5), (1.6, "drip", {}, -6, 0.0)]),
    "S10": dict(loc="deck_mc", space="deck", ev=[(0.4, "water_slap", {}, -4, 0.4), (1.6, "creak", {"kind": "rope"}, -8, -0.3), (3.0, "wood_tap", {}, -6, -0.2)]),
    "S11": dict(loc="deck_mc", space="deck", beds={"sea_calm": 0, "laps": -6}, ev=[(0.4, "water_slap", {}, -2, 0.0), (2.2, "water_slap", {}, -4, 0.1)]),
    "S12": dict(loc="deck_mc", space="deck", ev=[(0.0, "wind_gust", {"dur": 2.2}, -4, 0.2), (0.9, "wood_tap", {}, -9, 0.0), (1.6, "wood_tap", {}, -11, 0.0)]),
    "S13": dict(loc="sea_low", space="out", ev=[(0.0, "oars", {"dur": 2.7}, -2, 0.0)]),
    "S14": dict(loc="deck_mc", space="deck", ev=[(0.3, "boot", {}, 0, -0.1), (0.7, "hand_slap", {}, -3, 0.3), (1.2, "hull_knock", {}, -3, 0.4)]),
    "S15": dict(loc="sea_wide", space="out", ev=[(0.4, "whump", {}, -3, 0.0), (1.6, "creak", {"kind": "hull"}, -8, 0.2)]),
    "S16": dict(loc="cabin", space="hold", ev=[(0.2, "lantern_creak", {}, -7, 0.0), (0.7, "drip", {}, -7, 0.2)]),
    "S16b": dict(loc="cabin", space="hold", ev=[(0.4, "drip", {}, -5, 0.0), (1.0, "creak", {"kind": "hull"}, -8, -0.3)]),
    "S17": dict(loc="deck_mc", space="deck", ev=[(0.8, "creak", {"kind": "rope"}, -6, 0.3), (2.6, "creak", {"kind": "rope"}, -8, -0.3)]),
    "S18": dict(loc="sea_dg", space="out", ev=[(0.4, "whump", {}, -4, 0.0)]),
    "S19": dict(loc="dg_cabin", space="room", ev=[(0.3, "nib", {"dur": 2.6}, -6, 0.0), (2.0, "lantern_creak", {}, -8, 0.3)]),
    "S20": dict(loc="sea_dg", space="out", ev=[(0.7, "creak", {"kind": "hull"}, -9, 0.0)]),
    "S21": dict(loc="dg_deck", space="deck", ev=[(0.3, "wheel", {"dur": 1.6}, -4, 0.0)]),
    "S22": dict(loc="dg_deck", space="deck", beds={"wind_mid": 0}, ev=[]),
    "S23": dict(loc="dg_deck", space="deck", ev=[(1.4, "ladder", {"steps": 3, "gap": 0.35}, -10, 0.2)]),
    "S24": dict(loc="dg_deck", space="deck", ev=[(0.0, "wheel", {"dur": 0.95, "spin": True}, -1, 0.0), (0.15, "chain", {"dur": 0.8}, -6, -0.3)]),
    "S25": dict(loc="sea_dg", space="out", ev=[(0.3, "whump", {}, 0, -0.2), (1.2, "whump", {}, -2, 0.2)]),
    "S26": dict(loc="dg_deck", space="deck", ev=[(1.4, "wind_gust", {"dur": 2.6}, -3, 0.3)]),
    "S27": dict(loc="sea_far", space="out", ev=[]),
    "S28": dict(loc="deck_mc", space="deck", beds={"flog": -14}, ev=[(0.3, "whump", {}, -2, 0.0), (1.3, "creak", {"kind": "rope"}, -6, 0.2)]),
    "S29": dict(loc="deck_mc", space="deck", beds={"flog": 0, "wind_mid": -2}, ev=[]),
    "S30": dict(loc="sea_low", space="out", ev=[(0.0, "oars", {"dur": 3.1}, -2, 0.0), (1.5, "water_slap", {}, -5, -0.2)]),
    "S31": dict(loc="deck_mc", space="deck", ev=[(0.1, "footsteps", {"times": [0.0, 0.5, 1.0]}, -2, 0.0), (1.5, "glass", {"dur": 0.6}, -6, 0.0)]),
    "S32": dict(loc="deck_mc", space="deck", ev=[(0.3, "glass", {"dur": 0.9}, -3, 0.0), (1.4, "card_tick", {}, -8, 0.0)]),
    "S33": dict(loc="deck_mc", space="deck", ev=[(0.6, "wood_scrape", {}, -4, -0.2)]),
    "S34": dict(loc="galley", space="hold", ev=[(0.1, "slosh", {"dur": 2.6, "muffle": 1500}, -8, 0.0), (1.0, "pot_roll", {}, -5, 0.3), (2.3, "drip", {}, -6, 0.0)]),
    "S35": dict(loc="galley", space="hold", ev=[(0.4, "water_slap", {}, -7, 0.0), (1.8, "water_slap", {}, -9, 0.0)]),
    "S36": dict(loc="galley", space="hold", ev=[(0.5, "iron_scrape", {"dur": 1.2}, -5, 0.0), (1.8, "slosh", {"dur": 1.2, "muffle": 1200}, -7, 0.0)]),
    "S37": dict(loc="deck_mc", space="deck", ev=[(0.2, "line_hands", {"dur": 1.8}, -3, 0.0), (1.7, "wood_tap", {}, -9, 0.0), (2.3, "splash_below", {}, -6, 0.0)]),
    "S38": dict(loc="deck_mc", space="deck", ev=[(0.32, "drip", {"into": "wood"}, -4, 0.0), (1.0, "drip", {"into": "wood"}, -6, 0.0), (1.3, "line_hands", {"dur": 0.5}, -12, 0.0)]),
    "S39": dict(loc="sea_low", space="out", beds={"bowwash": -4}, ev=[(0.8, "creak", {"kind": "hull"}, -8, 0.0)]),
    "S40": dict(loc="deck_mc", space="deck", ev=[(0.2, "mast_creak", {}, -3, 0.0)]),
    "S41": dict(loc="sea_wide", space="out", ev=[(0.5, "whump", {}, -4, 0.0)]),
    "S42": dict(loc="deck_mc", space="deck", ev=[(0.6, "creak", {"kind": "rope"}, -7, 0.4), (1.8, "breath", {}, -8, 0.0)]),
    "S43": dict(loc="studio", space="room", ev=[(0.3, "paper", {"dur": 1.0}, -5, 0.0), (2.4, "pin_tap", {}, -3, 0.2)]),
    "S44": dict(loc="cabin", space="hold", beds={"drips": -14}, ev=[(0.2, "door_latch", {}, -3, -0.3), (1.3, "footsteps", {"times": [0.0, 0.5]}, -4, 0.0), (2.5, "lantern_creak", {}, -7, 0.0)]),
    "S45": dict(loc="cabin", space="hold", beds={"drips": -14, "lamp": -24}, ev=[(1.5, "creak", {"kind": "hull"}, -9, 0.3)]),
    "S46": dict(loc="cabin", space="hold", beds={"drips": -14, "lamp": -24}, ev=[(0.6, "page", {}, -3, 0.0)]),
    "S47": dict(loc="cabin", space="hold", beds={"drips": -14, "lamp": -24}, ev=[(0.5, "chalk_tap", {}, -4, 0.0)]),
    "S48": dict(loc="cabin", space="hold", beds={"drips": -14, "lamp": -24}, ev=[(0.4, "breath", {}, -9, 0.0), (1.5, "creak", {"kind": "hull"}, -9, -0.4), (2.4, "brush", {}, -8, 0.0)]),
    "S49": dict(loc="cabin", space="hold", beds={"drips": -14, "lamp": -24}, ev=[(0.3, "paper", {"dur": 0.4}, -9, 0.0)]),
    "S50": dict(loc="cabin", space="hold", beds={"drips": -14, "lamp": -24}, ev=[(0.4, "chalk_scrape", {"dur": 0.9}, -5, 0.0)]),
    "S51": dict(loc="studio", space="room", ev=[(2.6, "pin_tap", {}, -3, -0.2)]),
    "S52": dict(loc="studio", space="room", ev=[(0.1, "whoosh", {"dur": 2.0}, -5, 0.0), (2.7, "pin_tap", {}, -3, 0.3)]),
    "S53": dict(loc="studio", space="room", beds={"drone": 0, "lamp": -16}, ev=[]),
}

SILENCE = [
    (18.62, 19.40, -30, 0.4),   # beat before "He finds no one." -> lone drip
    (73.40, 74.50, -24, 0.45),  # hail, then silence: "Nobody answers."
    (104.60, 105.45, -26, 0.4), # before "Three and a half feet." -> rod drips
]

NOTES = ["S23 Morehouse calling down and S26 the crew's hail are voices, so they are NOT synthesised. Add a real recorded shout there if you want one (the wind gust at S26 is placed to carry it)."]
