# Shot table. Phase 1: provisional lengths (about 1.3x the reference stretch). Phase 2: VO frames replace LEN.
# Every shot's animation is keyed at 1x from its own start frame, so a new length only trims or extends it.
SHOTS = [   # Phase 2: lengths from the VO word frames (1 + round(s * 60)), frame_end = last word + 0.5 s = 1887
    ("01", "sky",   89),  # f1    "In 1990,"
    ("02", "nose", 108),  # f90   "a pilot was sucked halfway out"
    ("03", "nose",  78),  # f198  "of his cockpit in mid-air,"
    ("04", "cock",  79),  # f276  "with only his legs"
    ("05", "cock", 146),  # f355  "keeping him from disappearing completely."
    ("06", "nose", 126),  # f501  "The windshield suddenly blew out,"
    ("07", "nose",  75),  # f627  "causing the cabin to rapidly"
    ("08", "nose",  79),  # f702  "depressurize."
    ("09", "cock", 109),  # f781  "A flight attendant grabbed the pilot's legs"
    ("10", "cock",  85),  # f890  "and refused to let go"
    ("11", "cock",  77),  # f975  "while the co-pilot fought"
    ("12", "cock",  83),  # f1052 "to control the plane."
    ("14", "nose", 191),  # f1135 "His body kept smashing against the outside of the aircraft,"
    ("15", "nose", 111),  # f1326 "and the crew thought he was dead."
    ("16", "cock",  70),  # f1437 "But they held on anyway."
    ("17", "nose",  58),  # f1507 "Around"
    ("20", "land",  79),  # f1565 "20 minutes later,"
    ("21", "land",  74),  # f1644 "the plane landed."
    ("22", "land",  57),  # f1718 "And somehow,"
    ("23", "land",  66),  # f1775 "the pilot was" (rolls past the van, logo)
    ("24", "land",  47),  # f1841 "still alive."  the captain, still out of the window, lifts his head -> 1887
]
P1LEN = {"01": 156, "02": 110, "03": 156, "04": 150, "05": 150, "06": 140, "07": 170, "08": 110, "09": 160, "10": 190,
         "11": 156, "12": 120, "13": 100, "14": 180, "15": 150, "16": 130, "17": 110, "18": 150, "19": 110, "20": 170,
         "21": 150, "22": 140, "23": 170, "24": 60}
def layout(shots=SHOTS, start=1):
    out = []; f = start
    for sid, st, n in shots:
        out.append((sid, st, f, f + n - 1)); f += n
    return out
