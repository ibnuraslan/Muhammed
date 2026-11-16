# Shot table. Phase 1: provisional lengths (about 1.3x the reference stretch). Phase 2: replace LEN with the VO frames.
# Each shot's animation is keyed at 1x from its own start frame, so changing a length only trims or extends the shot.
# Phase 2: built to the client VO (B01_DogShootsOwner_VO.mp3, 26.4 s). Beat frame = 1 + round(word_seconds * 60).
# (sid, set, CLIP = authored 1x clip length from Phase 1, VO start frame, first words). Each clip is keyed at 1x from its
# start and simply cut at the next shot's start (never time-stretched). End frame = 0.5 s after the last word (26.02 s).
SHOTS_VO = [
    ("01",  "truck",   80,    1, "The dog"),
    ("02",  "truck",  156,   61, "on a loaded shotgun in the backseat of a"),
    ("03",  "truck",   80,  176, "truck and accidentally"),
    ("04",  "truck",  140,  245, "fired it."),
    ("05",  "truck",  150,  321, "The bullet ripped through the front"),
    ("06",  "truck",   80,  402, "seat and into"),
    ("07a", "anat",   150,  453, "the man's back,"),
    ("07b", "anat",   150,  519, "breaking several ribs and"),
    ("07c", "anat",   150,  597, "tearing a hole in his lung."),
    ("08a", "truck",  110,  716, "Somehow, he managed to call"),
    ("08b", "truck",  110,  805, "911 and"),
    ("09",  "ambi",   100,  870, "was rushed to the hospital,"),
    ("12",  "road",   100,  949, "where he eventually recovered."),
    ("13a", "kennel",  90, 1056, "The dog was taken to animal"),
    ("13b", "kennel",  90, 1111, "control,"),
    ("14a", "hosp",   100, 1171, "but later returned to its"),
    ("14b", "hosp",   100, 1248, "owner."),
    ("15a", "clear",  110, 1298, "Unfortunately,"),
    ("15b", "clear",  130, 1353, "the dog was killed only a few"),
    ("15c", "clear",  120, 1449, "weeks later in an"),
    ("15d", "clear",  130, 1508, "unrelated incident."),
]
VO_END = 1 + round((26.02 + 0.5) * 60)        # 1592
SHOTS = [(s, st, n) for s, st, n, _, _ in SHOTS_VO]

def layout(shots=None, start=1):
    """(sid, set, f0, f1) at the VO frames; f1 = next start - 1 (last shot ends at VO_END)."""
    out = []
    for i, (sid, st, n, f0, _) in enumerate(SHOTS_VO):
        f1 = SHOTS_VO[i + 1][3] - 1 if i + 1 < len(SHOTS_VO) else VO_END
        out.append((sid, st, f0, f1))
    return out

def clip_len(sid):
    return next(n for s, st, n, f0, w in SHOTS_VO if s == sid)
