"""The house cinematic look for every phone-banker set (nvidia_doc/scenes/look.py recipes, README section 2).

Each set's build() wrapper calls apply(set_name, variant) before finish_scene(). It lights the set the
look.py way: exteriors get one low sky and one sun key plus haze, interiors by day one window key with the other
lights cut back and dark walls, night sets keep their own lights with warmer practicals. Set HOUSE_LOOK=plain
(run.py --plain) to get the old light for before/after sheets.
"""
import look

# set -> variant -> (recipe, kwargs). A variant of None is the set's default build.
EXT = "ext"; INT = "int"; NIGHT = "night"; KEEP = "keep"; FOREST = "forest"

OFFICE_WIN = dict(window=((-3.55, 0.3, 1.9), (0.2, 0.9, 0.6)), mood="low_sun", key_size=1.6, key_energy=2600, fill=0.35, sky_factor=0.6)
ANTE_WIN = dict(window=((7.55, -1.4, 1.9), (5.0, -1.2, 0.6)), mood="overcast", key_size=1.5, key_energy=900, fill=0.35, sky_factor=0.6)

PLAN = {
    "sc_bankoffice": {
        **{v: (INT, OFFICE_WIN) for v in ("empty", "search", "day", "brother", "sealed", "visit", "alone", "leave", "dust", None)},
        **{v: (INT, ANTE_WIN) for v in ("ante", "ledger")},
    },
    "sc_bank": {
        "dusk": (KEEP, {}),
        "summer": (EXT, dict(mood="mist", azim=115, haze_box=((0, -10, 12), (220, 60, 24)))),
        "autumn": (EXT, dict(mood="dusk", azim=150, haze_box=((0, -10, 12), (220, 60, 24)))),
        "winter": (EXT, dict(mood="mist", azim=150, haze_box=((0, -10, 12), (220, 60, 24)))),
        "seasons": (EXT, dict(mood="mist", azim=150, haze_box=((0, -10, 12), (220, 60, 24)))),
    },
    "sc_hospital": {
        None: (INT, dict(window=((0.0, -11.4, 1.9), (0.0, -5.0, 0.6)), mood="overcast", key_size=1.4, fill=0.35, sky_factor=0.6)),
        "corridor": (INT, dict(window=((0.0, -11.4, 1.9), (0.0, -5.0, 0.6)), mood="overcast", key_size=1.4, fill=0.35, sky_factor=0.6)),
        "dawn": (INT, dict(window=((0.0, -11.4, 1.9), (0.0, -5.0, 0.6)), mood="overcast", key_size=1.4, fill=0.35, sky_factor=0.6)),
        "ward": (INT, dict(window=((-3.9, 0.15, 1.8), (0.5, 1.0, 0.6)), mood="overcast", key_size=1.6, fill=0.35, sky_factor=0.6)),
        "path": (INT, dict(window=((-2.9, 0.0, 1.75), (-0.8, -1.0, 0.7)), mood="overcast", key_size=1.4, fill=0.35, sky_factor=0.6)),
        "night": (NIGHT, {}),
        "arrive": (KEEP, {}),
    },
    "sc_forlab": {
        **{v: (INT, dict(window=((-4.4, 0.2, 1.8), (0.0, 0.4, 0.7)), mood="overcast", key_size=1.6, fill=0.35, sky_factor=0.6)) for v in ("lab95", "evid", "y2018", None)},
        "end": (NIGHT, {}),
    },
    "sc_memorial": {None: (INT, dict(window=((0.0, 11.4, 3.6), (0.0, 4.0, 0.8)), mood="low_sun", key_size=2.4))},
    "sc_court": {
        "room": (INT, dict(window=((-6.5, 2.0, 2.7), (0.5, 3.0, 0.7)), mood="overcast", key_size=2.4, fill=0.35, sky_factor=0.6)),
        None: (INT, dict(window=((-6.5, 2.0, 2.7), (0.5, 3.0, 0.7)), mood="overcast", key_size=2.4, fill=0.35, sky_factor=0.6)),
        "hall": (INT, dict(window=((0.0, 8.5, 1.85), (0.0, 2.0, 0.6)), mood="overcast", key_size=1.3, fill=0.35, sky_factor=0.6)),
        "archive": (NIGHT, {}),
    },
    "sc_closedtown": {
        "checkpoint": (FOREST, dict(mood="mist", azim=140, area=((-20, 30), (220, 90)), canopy=20.0)),
        None: (FOREST, dict(mood="mist", azim=140, area=((-20, 30), (220, 90)), canopy=20.0)),
        "institute": (INT, dict(window=((0.0, 15.4, 1.8), (0.0, 8.0, 0.6)), mood="overcast", key_size=1.4, fill=0.35, sky_factor=0.6)),
        "kitchen": (NIGHT, {}), "blocks": (KEEP, {}),
    },
    "sc_apartment": {None: (EXT, dict(mood="mist", azim=105, haze_box=((0, -12, 12), (90, 50, 26))))},
    "sc_salisbury": {None: (EXT, dict(mood="mist", azim=140, haze_box=((-10, 0, 10), (120, 60, 22))))},
    "sc_station": {None: (NIGHT, {})},
}

# window cookies: office blind + mullions; court and hospital mullions
GOBOS = {
    ("sc_bankoffice", "office"): [dict(center=(-3.45, 1.4, 1.75), size=(1.4, 1.7), axis="x", bars=12, bar=0.05, kind="blinds"),
                                  dict(center=(-3.45, -0.8, 1.75), size=(1.4, 1.7), axis="x", bars=2, bar=0.08)],
    ("sc_court", "room"): [dict(center=(-6.3, -2.2 + k * 3.6, 2.7), size=(2.4, 3.4), axis="x", bars=2, bar=0.08) for k in range(4)],
}


def apply(set_name, variant=None):
    if not look.enabled():
        return
    plan = PLAN.get(set_name, {})
    recipe, kw = plan.get(variant, plan.get(None, (KEEP, {})))
    kw = dict(kw)
    if recipe == EXT:
        hz = kw.pop("haze_box", None)
        look.day_light(**kw)
        md = look.MOODS[kw.get("mood", "overcast")]
        if md.get("cine"):
            look.set_grade(**md["cine"])                                            # the mood's own tone (as look.forest does)
        if hz is not None:                                                          # haze that hugs the street, the sky stays clean
            look.ground_haze((hz[0][0], hz[0][1]), (hz[1][0], hz[1][1]), kw.get("mood", "overcast"), height=8.0,
                             density=0.008 if kw.get("mood") in ("mist", "dusk") else 0.004)
    elif recipe == FOREST:
        look.forest(**kw)
    elif recipe == INT:
        look.interior_day(**kw)
        w0, w1 = kw["window"]                                                       # a thin room haze so the window key reads as shafts
        cx, cy = (w0[0] + w1[0]) / 2, (w0[1] + w1[1]) / 2
        look.haze((cx, cy, 1.6), (abs(w0[0] - w1[0]) + 6, abs(w0[1] - w1[1]) + 6, 3.2), "mist", density=0.02)
        gk = "office" if set_name == "sc_bankoffice" and variant not in ("ante", "ledger") else (variant or "room")
        for g in GOBOS.get((set_name, gk), []):
            look.gobo(**g)
    elif recipe == NIGHT:
        look.night_interior()
