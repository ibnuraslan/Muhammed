# Shot timing for B12 (exec'd by 03_anim.py). Phase 1: reference pacing + ~30%, laid end to end.
# Phase 2: replace SHOT_LEN with the VO beat lengths (start = 1 + round(seconds * 60)), END_FRAME ~0.5 s after the last word.
# Every action is keyed at an offset from its shot's start, at 1x speed, so retiming = editing this table and rebuilding.
SHOT_LEN = [("S01", 156), ("S02", 120), ("S03", 84), ("S04", 156), ("S05", 156), ("S06", 156), ("S07", 96), ("S08", 156),
            ("S09", 234), ("S10", 156), ("S11", 234), ("S12", 156), ("S13", 156), ("S14", 156), ("S15", 234), ("S16", 156),
            ("S17", 108), ("S18", 108), ("S19", 156), ("S20", 120), ("S21", 156), ("S22", 156)]
START = {}
_f = 1
for _n, _l in SHOT_LEN:
    START[_n] = _f; _f += _l
END_FRAME = _f - 1
def shot_end(n):
    names = [s for s, _ in SHOT_LEN]; i = names.index(n)
    return (START[names[i + 1]] - 1) if i + 1 < len(names) else END_FRAME
