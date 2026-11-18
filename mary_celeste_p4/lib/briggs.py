"""Captain Benjamin Spooner Briggs (1835-1872?), master of the Mary Celeste: new shared character for Part 4.

Built on the shared Deveau character (mary_celeste_3d/lib/deveau.py: clothes grown as shells, strand hair and
beard) without changing it: only the face shape targets, age, build and hair colour differ. From his surviving
portrait: a broad, calm face, full dark beard trimmed close at the cheeks, dark hair parted and brushed back,
heavier brows. Aged 37 in 1872."""
import bpy
import human as H
import deveau as D

FACE = {"targets/chin/chin-prominent-decr": 0.2, "targets/nose/nose-scale-horiz-incr": 0.25,
        "targets/nose/nose-flaring-incr": 0.2, "targets/eyebrows/eyebrows-trans-down": 0.5,
        "targets/cheek/l-cheek-bones-incr": 0.1, "targets/cheek/r-cheek-bones-incr": 0.1,
        "targets/head/head-age-incr": 0.35,
        "targets/eyes/r-eye-scale-decr": 0.15, "targets/eyes/l-eye-scale-decr": 0.15,
        "targets/mouth/mouth-scale-horiz-incr": 0.15}


class Briggs(D.Deveau):
    def __init__(self, name="Briggs", years=37, wet=0.2):
        real_human = H.Human

        def human(*a, **kw):
            kw["extra"] = dict(FACE)
            kw["weight"] = 0.6; kw["muscle"] = 0.58; kw["height"] = 0.6; kw["years"] = years
            return real_human(*a, **kw)
        real_hair = D.hair_material

        def hair(nm, melanin=0.78, redness=0.35, rough=0.32, grey=0.0):
            return real_hair(nm, 0.93, 0.18, rough, grey)      # near-black brown, little red
        H.Human = human; D.hair_material = hair
        try:
            super().__init__(name, years=years, wet=wet)
        finally:
            H.Human = real_human
        self._hair_patch = (real_hair, hair)

    def finish(self, *a, **kw):
        real, mine = self._hair_patch
        D.hair_material = mine
        try:
            super().finish(*a, **kw)
        finally:
            D.hair_material = real
