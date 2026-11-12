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
        "summer": (EXT, dict(mood="low_sun", elev=30, sky="blue", azim=70, exposure=1.0, sky_strength=0.5, sun_energy=9.0, haze_box=((0, -10, 12), (220, 60, 24)))),
        "autumn": (KEEP, {}),                                                     # rain/snow: the relight lost the figures; grade only
        "winter": (KEEP, {}),                                                     # rain/snow: the relight lost the figures; grade only
        "seasons": (KEEP, {}),                                                     # rain/snow: the relight lost the figures; grade only
    },
    "sc_hospital": {
        None: (INT, dict(window=((0.0, -11.4, 1.9), (0.0, -5.0, 0.6)), mood="overcast", key_size=1.4, fill=0.35, sky_factor=0.6)),
        "corridor": (INT, dict(window=((0.0, -11.4, 1.9), (0.0, -5.0, 0.6)), mood="overcast", key_size=1.4, fill=0.35, sky_factor=0.6)),
        "dawn": (INT, dict(window=((0.0, -11.4, 1.9), (0.0, -5.0, 0.6)), mood="overcast", key_size=1.4, fill=0.35, sky_factor=0.6)),
        "ward": (INT, dict(window=((-3.9, 0.15, 1.8), (0.5, 1.0, 0.6)), mood="overcast", key_size=1.6, fill=0.35, sky_factor=0.6)),
        "path": (INT, dict(window=((-2.9, 0.0, 1.75), (-0.8, -1.0, 0.7)), mood="overcast", key_size=1.4, key_energy=160, fill=0.35, sky_factor=0.6)),
        "night": (NIGHT, {}),
        "arrive": (KEEP, {}),
    },
    "sc_forlab": {
        **{v: (INT, dict(window=((-4.4, 0.2, 1.8), (0.0, 0.4, 0.7)), mood="overcast", key_size=1.6, fill=0.35, sky_factor=0.6)) for v in ("lab95", "evid", "y2018", None)},
        "end": (NIGHT, {}),
    },
    "sc_memorial": {None: (KEEP, {}), "_relit": (INT, dict(window=((0.0, 11.4, 3.6), (0.0, 4.0, 0.8)), mood="low_sun", key_size=2.4))},
    "sc_court": {
        "room": (INT, dict(window=((-6.5, 2.0, 2.7), (0.5, 3.0, 0.7)), mood="overcast", key_size=2.4, fill=0.35, sky_factor=0.6)),
        None: (INT, dict(window=((-6.5, 2.0, 2.7), (0.5, 3.0, 0.7)), mood="overcast", key_size=2.4, fill=0.35, sky_factor=0.6)),
        "hall": (INT, dict(window=((0.0, 8.5, 1.85), (0.0, 2.0, 0.6)), mood="overcast", key_size=1.3, fill=0.35, sky_factor=0.6)),
        "archive": (NIGHT, {}),
    },
    "sc_closedtown": {
        "checkpoint": (EXT, dict(mood="overcast", azim=60, haze_box=((-20, 30, 10), (220, 90, 20)))),
        None: (EXT, dict(mood="overcast", azim=60, haze_box=((-20, 30, 10), (220, 90, 20)))),
        "institute": (INT, dict(window=((0.0, 15.4, 1.8), (0.0, 8.0, 0.6)), mood="overcast", key_size=1.4, fill=0.35, sky_factor=0.6)),
        "kitchen": (NIGHT, {}), "blocks": (KEEP, {}),
    },
    "sc_apartment": {None: (EXT, dict(mood="low_sun", elev=34, sky="blue", azim=70, exposure=1.0, sky_strength=0.5, sun_energy=9.0, haze_box=((0, -12, 12), (90, 50, 26))))},
    "sc_salisbury": {None: (EXT, dict(mood="low_sun", elev=28, sky="blue", azim=65, exposure=1.0, sky_strength=0.5, sun_energy=9.0, haze_box=((-10, 0, 10), (120, 60, 22))))},
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
                             density={"mist": 0.008, "dusk": 0.008, "low_sun": 0.0015}.get(kw.get("mood"), 0.004))
    elif recipe == FOREST:
        look.forest(**kw)
    elif recipe == INT:
        look.interior_day(**kw)
        gk = "office" if set_name == "sc_bankoffice" and variant not in ("ante", "ledger") else (variant or "room")
        for g in GOBOS.get((set_name, gk), []):
            look.gobo(**g)
    elif recipe == NIGHT:
        look.night_interior()
