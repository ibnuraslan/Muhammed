# Shot timing for B23 (exec'd by 03_anim.py). Phase 1: reference pacing + ~30%, laid end to end.
# Phase 2: set START to the VO beat frames (1 + round(seconds * 60)) and END_FRAME ~0.5 s after the last word.
# Every action is keyed at an offset from its shot's start, at 1x speed, so retiming = editing this table and rebuilding.
SHOT_LEN = [("S01", 117), ("S02", 108), ("S03", 150), ("S04", 120), ("S05", 150), ("S06", 156), ("S07", 120), ("S08", 120),
            ("S09", 156), ("S10", 90), ("S11", 156), ("S12", 156), ("S13", 120), ("S14", 180), ("S15", 120), ("S16", 156),
            ("S17", 240)]
START = {}
_f = 1
for _n, _l in SHOT_LEN:
    START[_n] = _f; _f += _l
END_FRAME = _f - 1
def shot_end(n):
    names = [s for s, _ in SHOT_LEN]; i = names.index(n)
    return (START[names[i + 1]] - 1) if i + 1 < len(names) else END_FRAME
