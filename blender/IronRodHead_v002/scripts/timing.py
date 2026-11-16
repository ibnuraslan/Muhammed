# Shot timing for B12 (exec'd by 03_anim.py). Phase 2: shot starts at the VO word frames, 1 + round(seconds * 60)
# (pipeline/transcribe.py, review/vo.words.json). END_FRAME = 0.5 s after the last word (31.30 s).
# Every action is keyed at an offset from its shot's start at 1x speed (nothing is time-stretched).
VO_START = [("S01", 0.00, "In 1848"), ("S02", 1.58, "a huge iron rod"), ("S03", 2.90, "blasted"),
            ("S04", 3.83, "(man's) face and skull"), ("S05", 5.20, "while he was working on a railroad"),
            ("S06", 7.36, "It entered below his left eye"), ("S08", 9.28, "shot out through the top of his head"),
            ("S09", 11.60, "Somehow, he stayed conscious"), ("S11", 13.22, "and survived. But afterward,"),
            ("S12", 16.00, "wasn't really the same person anymore"), ("S13", 18.32, "You see, the rod destroyed part of"),
            ("S14", 20.28, "frontal lobe"), ("S15", 21.34, "controls things like judgment"), ("S16", 22.96, "and self-control"),
            ("S18", 24.40, "After the accident, his personality"), ("S19", 26.04, "completely changed"),
            ("S20", 27.44, "He became impulsive"), ("S21", 29.32, "unpredictable, and difficult to"), ("S22", 30.68, "control")]
VO_END_S = 31.30
START = {n: 1 + round(t * 60) for n, t, _ in VO_START}
END_FRAME = 1 + round((VO_END_S + 0.5) * 60)
SHOT_LEN = []
_names = [n for n, _, _ in VO_START]
for _i, _n in enumerate(_names):
    _e = START[_names[_i + 1]] if _i + 1 < len(_names) else END_FRAME + 1
    SHOT_LEN.append((_n, _e - START[_n]))
def shot_end(n):
    names = [s for s, _ in SHOT_LEN]; i = names.index(n)
    return (START[names[i + 1]] - 1) if i + 1 < len(names) else END_FRAME
