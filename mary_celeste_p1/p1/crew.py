"""The people of Part 1, all built with the shared character code (lib/deveau.py + lib/human.py), unchanged.

    deveau()        Oliver Deveau, first mate (the shared Deveau, as designed)
    morehouse()     Captain David Morehouse: older, greyer, fuller beard, a brown coat
    sailor(k)       Dei Gratia hands (k = 0..2): younger, different faces and jackets, some clean-shaven

Every person is posed with lib/poses.py on the rig, then finish()ed (pose baked, strand hair grown, placed).
`place(x, y, z, heading_deg)`: a world matrix; heading 0 = facing -Y (the rig's rest), +90 = facing +X."""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
import human as H, deveau as D, poses as P


def place(x, y, z, heading_deg, parent=None):
    """Rig rest faces -Y; heading turns him so he faces (sin h, -cos h) rotated: 0 -> -Y, 90 -> +X."""
    M = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(heading_deg), 4, 'Z')
    return (parent @ M) if parent is not None else M


class Sailor(D.Deveau):
    """A Deveau-built man with his own face, age, build and clothes colours (subclass: the shared class untouched)."""

    def __init__(self, name, years=28, extra=None, muscle=0.6, weight=0.5, height=0.5, wet=0.3,
                 jacket=None, trousers=None, scarf=None, shirt=None, skin=(0.43, 0.25, 0.16), hair=(0.82, 0.38),
                 grey=0.0, beard=True, moustache=True, no_jacket=False):
        tg = {"targets/head/head-age-incr": 0.1}
        tg.update(extra or {})
        self.h = H.Human(name, gender=1.0, years=years, muscle=muscle, weight=weight, height=height,
                         extra=tg, eyebrows=None, eyelashes=None, skin=None)
        h = self.h
        h.body.data.materials[0] = D.sailor_skin(name + "_skin", base=skin)
        self.name = name; self.wet = wet
        self.rest_co = H.to_bl(h.hc)
        me = h.body.data
        self.rest_n = np.array([v.normal[:] for v in me.vertices], np.float64)
        uvs = np.zeros((len(me.vertices), 2)); uvl = me.uv_layers[0].data
        for l in me.loops:
            uvs[l.vertex_index] = uvl[l.index].uv
        self.uv = uvs
        self.used = np.zeros(len(me.vertices), bool)
        for pl in me.polygons:
            self.used[list(pl.vertices)] = True
        self.faces = [tuple(pl.vertices) for pl in me.polygons]
        self._dress()
        self._recolour(jacket, trousers, scarf, shirt)
        if no_jacket:                                   # in shirt sleeves: drop the reefer jacket and its buttons
            for o in [self.jacket] + self.button_objs:
                if o in h.parts:
                    h.parts.remove(o)
                bpy.data.objects.remove(o)
            self.button_objs = []
        self._hair_cfg = dict(hair=hair, grey=grey, beard=beard, moustache=moustache)

    def _recolour(self, jacket, trousers, scarf, shirt):
        n = self.name
        if jacket:
            self.jacket.data.materials[0] = D.wool_material(n + "_jk", jacket, weave=380, wet=self.wet, dirt=0.2, sheen=0.3)
        if trousers:
            self.trousers.data.materials[0] = D.wool_material(n + "_tr", trousers, weave=500, wet=self.wet, sheen=0.25)
        if scarf:
            self.scarf.data.materials[0] = D.wool_material(n + "_sc", scarf, rough=0.8, sheen=0.3, weave=900, dirt=0.3)
        if shirt:
            self.shirt.data.materials[0] = D.linen_material(n + "_sh", shirt, wet=self.wet)

    def _grow_all(self, density):
        super()._grow_all(density)
        cfg = self._hair_cfg
        for o in list(self.hair_objs):
            if o is None:
                continue
            lab = o.name.split("_")[-1]
            if (lab == "beard" and not cfg["beard"]) or (lab == "moustache" and not cfg["moustache"]):
                bpy.data.objects.remove(o); self.hair_objs.remove(o); continue
        for o in self.hair_objs:
            if o is None:
                continue
            for m in o.data.materials:
                for nd in m.node_tree.nodes:
                    if nd.type == 'BSDF_HAIR_PRINCIPLED':
                        for nm, v in (("Melanin", cfg["hair"][0]), ("Melanin Redness", cfg["hair"][1])):
                            if nm in nd.inputs:
                                nd.inputs[nm].default_value = v
                        if "Random Color" in nd.inputs and cfg["grey"]:
                            nd.inputs["Random Color"].default_value = cfg["grey"]
                        if "Melanin" in nd.inputs and cfg["grey"]:
                            nd.inputs["Melanin"].default_value = cfg["hair"][0] * (1 - 0.45 * cfg["grey"])


def deveau(wet=0.4):
    return D.Deveau(wet=wet)


def morehouse():
    return Sailor("Morehouse", years=42, muscle=0.55, weight=0.6, height=0.52,
                  extra={"targets/nose/nose-scale-horiz-incr": 0.3, "targets/chin/chin-width-incr": 0.3,
                         "targets/head/head-age-incr": 0.5, "targets/eyebrows/eyebrows-trans-down": 0.4,
                         "targets/cheek/l-cheek-inner-incr": 0.3, "targets/cheek/r-cheek-inner-incr": 0.3},
                  jacket=(0.045, 0.028, 0.016), trousers=(0.03, 0.026, 0.022), scarf=(0.02, 0.03, 0.06),
                  skin=(0.47, 0.29, 0.19), hair=(0.55, 0.25), grey=0.6, wet=0.15)


SAILORS = [
    dict(years=24, extra={"targets/nose/nose-scale-vert-decr": 0.3, "targets/chin/chin-prominent-decr": 0.2,
                          "targets/head/head-oval": 0.4},
         jacket=(0.08, 0.075, 0.07), trousers=(0.05, 0.045, 0.04), scarf=(0.25, 0.16, 0.04), shirt=(0.42, 0.07, 0.04),
         skin=(0.48, 0.3, 0.2), hair=(0.35, 0.6), beard=False, moustache=False, no_jacket=True),
    dict(years=31, extra={"targets/nose/nose-hump-incr": 0.6, "targets/cheek/l-cheek-bones-incr": 0.5,
                          "targets/cheek/r-cheek-bones-incr": 0.5, "targets/head/head-square": 0.4},
         jacket=(0.02, 0.035, 0.03), trousers=(0.03, 0.03, 0.04), scarf=(0.3, 0.05, 0.03),
         skin=(0.40, 0.23, 0.14), hair=(0.95, 0.2), beard=True, moustache=True),
    dict(years=38, extra={"targets/nose/nose-scale-horiz-incr": 0.4, "targets/head/head-round": 0.3,
                          "targets/eyebrows/eyebrows-trans-down": 0.3},
         jacket=(0.16, 0.11, 0.05), trousers=(0.02, 0.02, 0.025), scarf=(0.05, 0.08, 0.12),
         skin=(0.45, 0.27, 0.17), hair=(0.7, 0.5), grey=0.2, beard=False, moustache=True),
]


def sailor(k, wet=0.3):
    cfg = dict(SAILORS[k % len(SAILORS)]); cfg.setdefault("wet", wet)
    return Sailor(f"Sailor{k}", **cfg)


# ----------------------------------------------------------------------------- pose helpers (rig frame)
def look(dv, M, target_w):
    """Eyes and a little head turn toward a world point are handled at finish(look_at=...)."""
    return target_w


def stand_relaxed(dv, pitch=0.0, yaw=0.0, lean=3, weight="L"):
    h = dv.h
    P.stand(h, lean=lean, weight=weight)
    P.head(h, pitch=pitch, yaw=yaw)
    P.arm_down(h, "L", out=0.1, fwd=0.05, bend=14); P.rest_hand(h, "L", curl=24)
    P.arm_down(h, "R", out=0.1, fwd=0.05, bend=14); P.rest_hand(h, "R", curl=24)


def hands_on(dv, M, left_w=None, right_w=None, elbow_l=(0.8, 0.4, -0.5), elbow_r=(-0.8, 0.4, -0.5), grip=True, curl=30):
    """Put the wrists on world points (a rail, a wheel spoke, a table edge) with simple two-bone IK."""
    h = dv.h; Mi = M.inverted()
    for side, w, el in (("L", left_w, elbow_l), ("R", right_w, elbow_r)):
        if w is None:
            continue
        P.hand_reach(h, side, Mi @ Vector(w), elbow=el)
        if grip:
            P.grip(h, side, 0.85)
        else:
            P.rest_hand(h, side, curl=curl)
