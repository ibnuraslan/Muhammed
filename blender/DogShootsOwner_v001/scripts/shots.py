# Shot table. Phase 1: provisional lengths (about 1.3x the reference stretch). Phase 2: replace LEN with the VO frames.
# Each shot's animation is keyed at 1x from its own start frame, so changing a length only trims or extends the shot.
SHOTS = [
    ("01",  "truck",  80),   # The dog
    ("02",  "truck", 156),   # stepped on a loaded shotgun
    ("03",  "truck",  80),   # in the back seat of a truck
    ("04",  "truck", 140),   # and accidentally pulled the trigger (flash)
    ("05",  "truck", 150),   # tore through the front seat (hole, man jolts)
    ("06",  "truck",  80),   # the front seat (hole close-up)
    ("07a", "anat",  150),   # into a man's back
    ("07b", "anat",  150),   # several ribs
    ("07c", "anat",  150),   # tearing a hole in his lung
    ("08a", "truck", 110),   # he managed to call
    ("08b", "truck", 110),   # 911
    ("09",  "ambi",  100),   # and was taken
    ("10",  "ambi",   80),   # to hospital, where he
    ("11",  "road",  150),   # eventually recovered
    ("12",  "road",  100),   # (logo) the dog was taken
    ("13a", "kennel", 90),   # to animal control
    ("13b", "kennel", 90),   # to animal control
    ("14a", "hosp",  100),   # back to his owner
    ("14b", "hosp",  100),   # back to his owner
    ("15a", "clear", 110),   # but unfortunately
    ("15b", "clear", 130),   # this dog, a few weeks later
    ("15c", "clear", 120),   # in an unrelated...
    ("15d", "clear", 130),   # end
]

def layout(shots=SHOTS, start=1):
    out = []; f = start
    for sid, st, n in shots:
        out.append((sid, st, f, f + n - 1)); f += n
    return out
