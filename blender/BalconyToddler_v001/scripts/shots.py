# Shot table. Phase 1: provisional lengths (about 1.3x the reference stretch). Phase 2: replace the lengths with the VO frames.
# Each shot's animation is keyed from its own start frame at 1x, so a new length only trims (or extends at 1x) the shot.
SHOTS = [
    ("01", 100),  # He slipped            - legs dangle below the floor bars, kicking
    ("02",  80),  # through the bars      - closer under the bars on the legs
    ("03",  90),  # of a second floor     - wide: facade, the boy on the balcony cage
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
    ("26", 150),  # Completely unharmed   - he looks up at her, she smiles, camera pushes in
]

def layout(shots=SHOTS, start=1):
    out = []; f = start
    for sid, n in shots:
        out.append((sid, f, f + n - 1)); f += n
    return out
