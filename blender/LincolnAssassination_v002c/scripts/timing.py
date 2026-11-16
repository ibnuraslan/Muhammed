# Shot timing for B04 v002, built to the client VO (LincolnAssassination_v002_VO.mp3, transcribed with pipeline/transcribe.py).
# Shot start = 1 + round(word_start_seconds * 60). END_FRAME = ~0.5 s after the last word (24.54 s).
SHOTS = [("S01", 1, "He pulled out a small pistol"), ("S02", 107, "and aimed it directly"),
         ("S03", 174, "at the back of Lincoln's head"), ("S04", 285, "Then, he waited"),
         ("S05A", 362, "loud moment in the play"), ("S05", 455, "and pulled the trigger"),
         ("S06", 534, "After firing,"), ("S07", 589, "he jumped down onto the stage,"),
         ("S08", 687, "breaking his leg"), ("S09", 750, "when he landed"),
         ("S10", 801, "But despite the injury,"), ("S11", 893, "he escaped the theater on"),
         ("S12", 962, "horseback"), ("S13", 1025, "A massive manhunt followed,"),
         ("S14", 1131, "and he managed to hide for 12 days before"),
         ("S14B", 1271, "authorities finally"),
         ("S15", 1325, "found him hiding inside a barn and killed him")]
END_FRAME = 1503
EV_FIRE = 480        # "trigger"
EV_LOUD = 420        # "moment in the play": the audience laugh peaks
EV_FOUND = 1271      # "authorities": the soldiers step in
START = {n: f for n, f, _ in SHOTS}
SHOT_LEN = [(n, (SHOTS[i + 1][1] if i + 1 < len(SHOTS) else END_FRAME + 1) - f) for i, (n, f, _) in enumerate(SHOTS)]
def shot_end(n):
    names = [s for s, _, _ in SHOTS]; i = names.index(n)
    return (SHOTS[i + 1][1] - 1) if i + 1 < len(SHOTS) else END_FRAME
