"""Captain Benjamin Spooner Briggs (37 in 1872), master of the Mary Celeste: shared character (promoted from Part 4,
mary_celeste_p4/lib/briggs.py; same face and colouring, now through Deveau's class attributes instead of patching).

From his surviving portrait: a broad, calm face, a full dark beard trimmed close at the cheeks, dark hair parted and
brushed back, heavier brows. Same clothes, boots and API as deveau.Deveau.

    b = Briggs(wet=0.2); poses.stand(b.h, ...); b.finish(look_at=..., place=M)
"""
import deveau as D


class Briggs(D.Deveau):
    EXTRA = {"targets/chin/chin-prominent-decr": 0.2, "targets/nose/nose-scale-horiz-incr": 0.25,
             "targets/nose/nose-flaring-incr": 0.2, "targets/eyebrows/eyebrows-trans-down": 0.5,
             "targets/cheek/l-cheek-bones-incr": 0.1, "targets/cheek/r-cheek-bones-incr": 0.1,
             "targets/head/head-age-incr": 0.35,
             "targets/eyes/r-eye-scale-decr": 0.15, "targets/eyes/l-eye-scale-decr": 0.15,
             "targets/mouth/mouth-scale-horiz-incr": 0.15}
    WEIGHT = 0.6; MUSCLE = 0.58; HEIGHT = 0.6
    HAIR_COLOR = (0.93, 0.18); BEARD_COLOR = (0.93, 0.18)      # near-black brown, little red

    def __init__(self, name="Briggs", years=37, wet=0.2, cap=False):
        super().__init__(name, years=years, wet=wet, cap=cap)
