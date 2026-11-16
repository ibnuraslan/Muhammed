# Shot timing for B23 (exec'd by 03_anim.py). Phase 1: reference pacing + ~30%, laid end to end.
# Phase 2: set START to the VO beat frames (1 + round(seconds * 60)) and END_FRAME ~0.5 s after the last word.
# Every action is keyed at an offset from its shot's start, at 1x speed, so retiming = editing this table and rebuilding.
SHOT_LEN = [("S01", 117), ("S02", 108), ("S03", 150), ("S04", 120), ("S05", 150), ("S06", 156), ("S07", 120), ("S08", 120),
            ("S09", 156), ("S10", 90), ("S11", 156), ("S12", 156), ("S13", 120), ("S14", 180), ("S15", 120), ("S16", 156),
            ("S17", 350)]
START = {}
_f = 1
for _n, _l in SHOT_LEN:
    START[_n] = _f; _f += _l
END_FRAME = _f - 1
def shot_end(n):
    names = [s for s, _ in SHOT_LEN]; i = names.index(n)
    return (START[names[i + 1]] - 1) if i + 1 < len(names) else END_FRAME

# ---------------------------------------------------------------- Phase 2: VO timing (HandlessWarrior_v002_VO.mp3)
# beat frame = 1 + round(word_seconds * 60).  TRIM = offset into the 1x P1 clip where the shown window starts (no stretch).
VO_BEATS = [("S01", 0.00, "They cut off", 0), ("S02", 1.50, "as punishment", 20), ("S03", 2.56, "then sent him back to his people", 10),
            ("S05", 4.08, "with orders to surrender", 0), ("S06", 5.94, "But instead, the warrior convinced them", 0),
            ("S07", 8.00, "to keep fighting", 10), ("S08", 9.40, "He sealed the wounds", 20), ("S09", 10.24, "with hot metal", 20),
            ("S10", 11.48, "then strapped knives", 10), ("S11", 12.40, "onto his wrists", 10), ("S12", 13.74, "When the battle began", 40),
            ("S13", 14.86, "he charged straight into the enemy", 0), ("S14", 16.60, "and even killed the general second-in-command", 0),
            ("S15", 19.10, "Eventually", 30), ("S16", 20.24, "his people were defeated", 40),
            ("S17", 21.22, "But despite losing both hands, the warrior continued fighting until the very end", 0)]
VO_LAST_WORD_END = 26.40
VO_START = {n: 1 + round(t * 60) for n, t, _, _ in VO_BEATS}
VO_TRIM = {n: a for n, _, _, a in VO_BEATS}
VO_END = 1 + round((VO_LAST_WORD_END + 0.5) * 60)
def vo_end(n):
    names = [b[0] for b in VO_BEATS]; i = names.index(n)   # S04 (walk across the meadow) is not used: S03 carries the walk-off
    return (VO_START[names[i + 1]] - 1) if i + 1 < len(names) else VO_END
