# Shot table, Phase 2: built to the client VO (B33_BogBurials_VO.mp3, transcribed with pipeline/transcribe.py).
# Beat frame = 1 + round(word_start_s * 60); frame_end = 0.5 s after the last word ("bones." ends 35.94 s).
# Every shot is keyed at 1x from its own start frame; lengths only trim or extend, never stretch.
# The VO has no animal line and no closing "curled shape / 8,000 years ago" line: P1 shots 06, 08, 09 and 24 are dropped.
BEATS = [
    # sid, stage, start_s, first words
    ("01", "bog",   0.00, "They placed the dead in the water"),
    ("02", "under", 1.48, "with their knees"),
    ("03", "under", 2.62, "toward their chests"),
    ("04", "bog",   3.98, "then drove wooden stakes"),
    ("05", "under", 5.36, "around the bodies to keep them"),
    ("07", "under", 6.92, "from floating back to the surface"),
    ("10", "under", 8.96, "Once they settled, layers of dead plants"),
    ("11", "cut",  11.38, "covered them like a lid"),
    ("12", "cut",  12.94, "blocking out air"),
    ("13", "under", 14.00, "slowing decomposition"),
    ("14", "site", 15.74, "Then, around 8,000 years later"),
    ("15", "site", 18.38, "construction workers"),
    ("16", "site", 19.50, "a human skull"),
    ("17", "dig",  21.30, "Archaeologists eventually uncovered"),
    ("18", "dig",  22.92, "168 ancient burials"),
    ("19", "dig",  25.36, "Some were preserved so well"),
    ("20", "dig",  27.62, "their stomachs still contained their final meals"),
    ("21", "dig",  30.52, "Pieces of brain tissue remained inside their skulls"),
    ("22", "dig",  33.60, "and burial cloth was still wrapped"),
    ("23", "dig",  35.26, "around their bones"),
]
LAST_WORD_END = 35.94
FEND = 1 + round((LAST_WORD_END + 0.5) * 60)
SHOTS = [(sid, st, 1 + round(t * 60)) for sid, st, t, _ in BEATS]

def layout(shots=SHOTS, start=1):
    out = []
    for i, (sid, st, f0) in enumerate(shots):
        f1 = shots[i + 1][2] - 1 if i + 1 < len(shots) else FEND
        out.append((sid, st, f0, f1))
    return out
