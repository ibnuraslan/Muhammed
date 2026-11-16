# Shot table, Phase 2: start frames = 1 + round(word_start_s * 60) of the client VO (B21_DogBuriedAlive_VO.mp3,
# faster-whisper word timestamps); frame_end = 0.5 s after the last word ("horrified." ends 26.84 s -> f1641).
# Each shot's animation is keyed at 1x from its own start frame; a shot shorter than its action shows the action's tail.
VO_SHOTS = [
    ("G01", "grave",    1, "They buried the dog,"),
    ("G03", "grave",   81, "but as they walked away,"),
    ("G02", "grave",  193, "they didn't notice the dirt starting to move."),
    ("R04", "road",   365, "You see, the dog had been hit"),
    ("R05", "road",   452, "by a truck,"),
    ("Y06", "yard",   517, "and his owners thought he was dead."),
    ("Y07", "yard",   627, "So they buried him"),
    ("Y08", "yard",   695, "and left for the weekend."),
    ("U10", "grave",  770, "But he was actually only unconscious."),
    ("U11", "grave",  929, "When he woke up underground,"),
    ("U13", "grave", 1014, "he clawed his way back"),
    ("Y14", "yard",  1088, "to the surface."),
    ("Y15", "yard",  1155, "And when the family returned a few days later,"),
    ("P17", "porch", 1289, "they found him sitting on the porch,"),
    ("P18", "porch", 1389, "wagging his tail."),
    ("P19", "porch", 1464, "He was happy."),
    ("Y20", "yard",  1538, "They were"),
    ("Y21", "yard",  1591, "horrified."),
]
FRAME_END = 1641
SHOTS = [(sid, st, (VO_SHOTS[i + 1][2] if i + 1 < len(VO_SHOTS) else FRAME_END + 1) - f0)
         for i, (sid, st, f0, _) in enumerate(VO_SHOTS)]

def layout(shots=SHOTS, start=1):
    out = []; f = start
    for sid, st, n in shots:
        out.append((sid, st, f, f + n - 1)); f += n
    return out
