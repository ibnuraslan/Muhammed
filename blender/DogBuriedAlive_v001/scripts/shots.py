# Shot table. Phase 1: provisional lengths (about 1.3-1.5x the reference stretch). Phase 2: replace the lengths with the VO frames.
# Each shot's animation is keyed at 1x from its own start frame, so changing a length only trims or extends the shot.
SHOTS = [
    ("G01", "grave", 110),   # They buried                 (dirt falls in over the dog)
    ("G02", "grave",  90),   # but didn't notice           (close: dog breathing under the falling dirt)
    ("G03", "grave", 200),   # the dirt moving / walked away (family turns and walks away above)
    ("R04", "road",   90),   # the dog had been hit        (dog runs on the road, pickup behind)
    ("R05", "road",  100),   # by a truck                  (soft cut: dog lying at the road edge, truck stopped)
    ("Y06", "yard",  110),   # thinking he was dead        (dad kneels by the dog on the lawn, mom + son behind)
    ("Y07", "yard",  110),   # buried him                  (fresh mound + shovel, family heads bowed)
    ("Y08", "yard",  120),   # then left                   (SUV backs out of the driveway, logo on door)
    ("Y09", "yard",  110),   # for the weekend             (SUV drives off down the street)
    ("U10", "grave", 110),   # he was actually just unconscious (close-up, eyes closed, breathing)
    ("U11", "grave", 100),   # when he woke up             (eyes open, ears twitch)
    ("U12", "grave", 100),   # underground                 (head lifts, looks up)
    ("U13", "grave", 200),   # he clawed his way back up   (tunnel: paws dig, dirt falls, body rises)
    ("Y14", "yard",  120),   # to the surface              (pops out of the mound)
    ("Y15", "yard",  120),   # the family, days later      (SUV pulls into the driveway)
    ("Y16", "yard",  110),   # they found him              (dog on the porch in the foreground, SUV stops)
    ("P17", "porch", 110),   # on the porch                (dog in front of the french doors)
    ("P18", "porch", 110),   # wagging his tail            (side: tail wags)
    ("P19", "porch", 110),   # he was happy                (face close-up, head tilt)
    ("Y20", "yard",  130),   # horrified                   (family by the SUV, dog trots to them)
    ("Y21", "yard",  120),   # horrified                   (closer on mom and dad's faces)
]

def layout(shots=SHOTS, start=1):
    out = []; f = start
    for sid, st, n in shots:
        out.append((sid, st, f, f + n - 1)); f += n
    return out
