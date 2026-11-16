# Shot table. Phase 1: provisional lengths (about 1.3x the reference stretch). Phase 2: replace the lengths with the VO frames.
# Each shot's animation is keyed from its own start frame at 1x, so a new length only trims (or extends at 1x) the shot.
SHOTS = [
    ("01", 100),  # He slipped            - legs dangle below the floor bars, kicking
    ("02",  80),  # through the bars      - closer under the bars on the legs
    ("03", 100),  # of a second floor     - wide: facade, the boy on the balcony cage
    ("04",  80),  # balcony               - low wide from the street, crane down
    ("05", 100),  # His body fell         - front of the cage: he slides down until the head stops
    ("06",  80),  # through the gap       - closer, he settles, hands on the bar
    ("07",  80),  # But his head          - close on his face above the bars
    ("08",  80),  # got stuck             - 3/4 side: head resting between the two bars
    ("09", 140),  # Leaving him hanging   - from below: the boy hanging under the cage
    ("10",  90),  # on the street         - people on the street look up, one points
    ("11",  80),  # saw him               - a man hurries toward the building
    ("12",  90),  # And rushed to stack   - a young man carries a chair by the seat
    ("13",  90),  # nearby chairs         - the old man lowers a chair onto another
    ("14",  80),  # into a tower          - the woman steadies the tower, looks up
    ("15",  80),  # Then one man          - the man steps to the tower, hand on the backrest, looks up
    ("16", 100),  # climbed up            - low: he rises from a crouch on the top chair
    ("17",  80),  # and grabbed           - close on his face looking up, arms rising
    ("18", 150),  # the boy's legs. Holding - from below: his hands on the boy's shins
    ("19", 150),  # to keep his neck from being crushed - close on the boy, lifted a little, calm
    ("20", 150),  # For several minutes   - close on the man's watch hand on the shin
    ("21",  90),  # Until the boy's       - outside the cage: boy's head in front, grandma at the far door
    ("22",  80),  # got inside            - inside: grandma comes through the apartment door
    ("23",  80),  # the apartment         - grandma hurries toward the balcony
    ("24", 110),  # And pulled            - grandma kneels and lifts him under his arms
    ("25",  90),  # the toddler back up   - he stands on the slab, her hands at his sides
    ("26", 175),  # Completely unharmed   - he looks up at her, she smiles, camera pushes in
]

def layout(shots=SHOTS, start=1):
    out = []; f = start
    for sid, n in shots:
        out.append((sid, f, f + n - 1)); f += n
    return out

# ---------------------------------------------------------------- Phase 2: the VO cut (05_vo_cut.py)
# Film frame = 1 + round(seconds * 60) of the VO word that starts the shot (pipeline/transcribe.py, B35_BalconyToddler_VO.mp3).
# Each kept shot plays its own 1x animation from its start: the cut shifts keys, never scales them. A shot longer than its
# P1 animation holds its last pose for the extra frames (only 03: +7 f... see VO_HOLD below).
VO_CUT = [  # (sid, first film frame, first words)
    ("01",    1, "A toddler slipped"),
    ("02",   57, "between the bars"),
    ("03",  127, "of a second-floor balcony."),
    ("05",  224, "His body fell through,"),
    ("07",  314, "but his head"),
    ("08",  369, "became trapped,"),
    ("09",  421, "leaving him hanging above the ground."),
    ("10",  554, "People on the street saw"),
    ("11",  633, "what happened and quickly"),
    ("12",  692, "stacked chairs"),
    ("13",  743, "beneath him."),
    ("16",  807, "One man climbed up"),
    ("17",  871, "and grabbed"),
    ("18",  915, "the boy's legs, holding his weight"),
    ("19", 1016, "so the bars wouldn't crush his neck."),
    ("20", 1147, "He stayed like that for several minutes"),
    ("21", 1256, "until the child's"),
    ("22", 1307, "grandmother got"),
    ("23", 1353, "inside the apartment"),
    ("24", 1405, "and pulled him back through the railing."),
    ("25", 1497, "Somehow,"),
    ("26", 1581, "the toddler escaped completely unharmed."),
]
VO_END = 1751     # last word ends 28.66 s; + 0.5 s
def vo_layout():
    out = []
    for i, (sid, f0, w) in enumerate(VO_CUT):
        f1 = (VO_CUT[i + 1][1] - 1) if i + 1 < len(VO_CUT) else VO_END
        out.append((sid, f0, f1, w))
    return out
