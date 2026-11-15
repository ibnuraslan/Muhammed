# Shot timing for B04 (exec'd by 03_anim.py). Phase 1: reference pacing + ~30%, laid end to end.
# Phase 2: replace START with the VO beat frames (1 + round(seconds * 60)) and END_FRAME with ~0.5 s after the last word.
# Every action is keyed at an offset from its shot's start, at 1x speed, so retiming = editing this table and rebuilding.
SHOT_LEN = [("S01", 198), ("S02", 120), ("S03", 156), ("S04", 78), ("S05", 102), ("S06", 96), ("S07", 156), ("S08", 144),
            ("S09", 78), ("S10", 120), ("S11", 198), ("S12", 198), ("S13", 174), ("S14", 198), ("S15", 198)]
START = {}
_f = 1
for _n, _l in SHOT_LEN:
    START[_n] = _f; _f += _l
END_FRAME = _f - 1
def shot_end(n):
    names = [s for s, _ in SHOT_LEN]; i = names.index(n)
    return (START[names[i + 1]] - 1) if i + 1 < len(names) else END_FRAME
