# Shot table. Phase 1: provisional lengths (about 1.3x the reference stretch). Phase 2: replace LEN with the VO frames.
# Each shot's animation is keyed at 1x from its own start frame, so changing a length only trims or extends the shot.
SHOTS = [
    ("01", "bog",   160),   # They placed (them) in the water
    ("02", "under", 150),   # with their arms tucked in
    ("03", "under", 140),   # and knees pulled close
    ("04", "bog",   160),   # Then they placed long wooden stakes
    ("05", "under", 150),   # around each of them
    ("06", "under", 150),   # to pin them to the bottom of the bog
    ("07", "under", 200),   # so the water didn't push them back to the surface
    ("08", "bank",  140),   # which prevented animals
    ("09", "bank",  140),   # from eating them
    ("10", "under", 200),   # Once the bodies (were in), a thick layer of dead plants
    ("11", "cut",   200),   # sealed them in like a lid
    ("12", "cut",   150),   # blocking out air
    ("13", "under", 200),   # and preventing the bodies from decaying
    ("14", "site",  150),   # But 8,000 years later
    ("15", "site",  150),   # a construction crew
    ("16", "site",  180),   # hit a human skull
    ("17", "dig",   180),   # Archaeologists (came) and uncovered
    ("18", "dig",   200),   # 168 burials
    ("19", "dig",   150),   # so well preserved that their stomachs
    ("20", "dig",   150),   # still held their last meals
    ("21", "dig",   200),   # their skulls still held their brain
    ("22", "dig",   150),   # their bones were still wrapped in burial cloth
    ("23", "dig",   150),   # and their bodies kept the curled shape
    ("24", "dig",   160),   # they were buried in 8,000 years ago
]

def layout(shots=SHOTS, start=1):
    out = []; f = start
    for sid, st, n in shots:
        out.append((sid, st, f, f + n - 1)); f += n
    return out
