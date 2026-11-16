# Shot table. Phase 1: provisional lengths (about 1.3x the reference stretch). Phase 2: VO frames replace LEN.
# Every shot's animation is keyed at 1x from its own start frame, so a new length only trims or extends it.
SHOTS = [
    ("01", "sky",  156),  # In 1990: the 737 in the clouds, push toward the nose
    ("02", "nose", 110),  # a pilot got sucked: he is pulled up out of the open windscreen
    ("03", "nose", 156),  # out of the cockpit mid-air: out to the waist, arms thrown up
    ("04", "cock", 150),  # his legs: low inside the cockpit, legs up into the windscreen
    ("05", "cock", 150),  # preventing him from being fully ejected: legs over the glareshield, feet at the yoke
    ("06", "nose", 140),  # windshield had suddenly broken off: close on the empty frame, papers whip out
    ("07", "nose", 170),  # causing the cabin to become rapidly depressurized: low exterior, wind pushes him back
    ("08", "nose", 110),  # (depressurized) close: head back, shouting
    ("09", "cock", 160),  # A flight attendant managed: she steps in and grabs his legs
    ("10", "cock", 190),  # the pilot's legs and held on: closer, she hugs his shins
    ("11", "cock", 156),  # as the co-pilot attempted: FO flying, both hands on the yoke
    ("12", "cock", 120),  # to stabilize: FO close
    ("13", "cock", 100),  # His head was repeatedly: attendant holding, looks up
    ("14", "nose", 180),  # striking the fuselage: close profile, head rocks near the skin
    ("15", "nose", 150),  # the crew thought he was dead: limp, arms trailing
    ("16", "cock", 130),  # But they kept holding: attendant braces, FO glances
    ("17", "nose", 110),  # so his body wouldn't fly off: wide front of the nose
    ("18", "sky",  150),  # and damage an engine: along the fuselage to the wing and engine
    ("19", "sky",  110),  # or wing: engine close, fan spinning
    ("20", "land", 170),  # twenty minutes later: descending over the hills to the runway
    ("21", "land", 150),  # the plane landed: touchdown, tyre smoke
    ("22", "land", 140),  # and miraculously: nose rolls toward camera
    ("23", "land", 170),  # the pilot ended up surviving: rolls past the ambulance (logo)
]
def layout(shots=SHOTS, start=1):
    out = []; f = start
    for sid, st, n in shots:
        out.append((sid, st, f, f + n - 1)); f += n
    return out
