"""Modern men (2000-2003) for the Antwerp Diamond Center film, built on deveau.Deveau / women._Woman.

Same body, rig, shell-clothes and strand-hair machinery as the Mary Celeste cast; new wardrobe:
  shirt (cotton, optional tie), jacket kind = "blazer" | "leather" | "bomber" | "coat" (knee-length) | None,
  full-length trousers with a break over low leather shoes, optional leather gloves (night work).
Hair: short, with a hairline that can recede (HAIRLINE) and a thinning crown (CROWN); optional stubble / moustache.

    m = Leonardo(night=False);  P.stand(m.h, ...);  m.finish(look_at=..., place=M)

Faces are never shown close (house rule): each man reads by build, hair, silhouette and wardrobe colour.
"""
import math
import numpy as np
import bpy
from mathutils import Vector
import human as H
import deveau as D
import women as W


def cotton(name, color, rough=0.75, weave=1600.0):
    return W.cloth(name, color, rough=rough, sheen=0.25, weave=weave, bump=0.12)


def leather_jacket(name, color):
    m = D.leather_material(name, color=color, rough=0.48, wet=0.15)
    return m


class ModernMan(W._Woman):
    GENDER = 1.0; MUSCLE = 0.55; WEIGHT = 0.55; HEIGHT = 0.5
    EXTRA = {}
    SKIN = dict(base=(0.47, 0.29, 0.2), weather=0.3)
    HAIR = (0.85, 0.25); HAIR_N = 110000; HAIR_LEN = (0.012, 0.028); CURL = 0.12; HAIR_LIFT = 0.0018
    HAIRLINE = 0.0        # >0 raises the front hairline (m), receding temples
    CROWN = 0.0           # radius (m) of a thinning crown
    FACIAL = None         # None | "stubble" | "moustache" | "beard"
    BEARD = (0.8, 0.25)
    # wardrobe
    SHIRT = (0.55, 0.6, 0.68); TIE = None
    JACKET = "blazer"; JACKET_COL = (0.03, 0.035, 0.06)
    TROUSERS = (0.05, 0.05, 0.055); SHOES = (0.03, 0.02, 0.012)
    GLOVES = False; GLOVE_COL = (0.012, 0.012, 0.012)

    def __init__(self, name, years=45, night=False, seated=False, **kw):
        self.night = night
        for k, v in kw.items():
            setattr(self, k.upper(), v)
        if night:
            self.GLOVES = True
        super().__init__(name, years, wet=0.0, seated=seated, bonnet=False, shawl=False)
        self._scalp_tint()

    BOOT_TOP = 0.075          # procedural low shoes (deveau._sea_boots): welt, sole, heel, short shaft under the trouser hem

    def _comb(self, R):
        part = 0.022 * self.head_scale
        return lambda p: R @ Vector((-0.8 if (p.x - self._mid_x) < part else 0.55, 0.65, -0.25))

    # ------------------------------------------------------------------ wardrobe
    def _dress(self):
        m, wh, whand, wfoot, warm = self._m()
        u = self.used; co = self.rest_co; z = co[:, 2]; y = co[:, 1]; x = co[:, 0]
        wrist = np.array(self.h.joint("wrist.L____head"))
        dist_wrist = np.minimum(np.linalg.norm(co - wrist, axis=1), np.linalg.norm(co - wrist * np.array([-1, 1, 1]), axis=1))
        hs = self.head_scale
        self.button_objs = getattr(self, "button_objs", [])
        hide = np.zeros(len(u), bool)
        # shirt: torso and arms to the wrist, a collar band at the neck
        shirt = u & (wh < 0.5) & (whand < 0.12) & (z > m["hip"] - 0.05) & (z < m["neck"] + 0.03 * hs)
        self.shirt, _ = self._shell("shirt", shirt, 0.004, cotton(self.name + "_shirt", self.SHIRT), solid=0.0015, displace=0.0015)
        hide |= shirt
        if self.TIE:
            front = co[:, 0] - float(co[u, 0].mean())
            tie = shirt & (np.abs(front) < 0.022 + 0.02 * np.clip((m["neck"] - z) / 0.4, 0, 1)) & (y < -0.02) & \
                (z > m["hip"] + 0.12) & (z < m["neck"] + 0.0)
            self.tie, _ = self._shell("tie", tie, 0.008, W.cloth(self.name + "_tie", self.TIE, rough=0.5, sheen=0.6, weave=2000),
                                      solid=0.002)
        # trousers: waist to the shoe, a slight break at the hem
        trous = u & (z < m["hip"] + 0.12) & (z > m["ankle"] + 0.01) & (wfoot < 0.6) & (whand < 0.05)
        self.trousers, _ = self._shell("trousers", trous, 0.007, W.cloth(self.name + "_trousers", self.TROUSERS, rough=0.8, weave=900, sheen=0.15),
                                       solid=0.002, displace=0.004, drape=30,
                                       flare=lambda b: np.clip((m["hip"] - 0.04 - b[:, 2]) / 0.12, 0, 1) * 0.007 + np.clip((m["knee"] + 0.1 - b[:, 2]) / 0.45, 0, 1) * 0.014)
        hide |= trous
        # shoes: deveau._sea_boots builds them in finish() (low, BOOT_TOP); the foot skin under them is hidden
        shoe = u & (z < m["ankle"] + 0.03) & (wfoot > 0.3)
        self.boot_mask = (u & (z < m["ankle"] + 0.27))
        self.boots, _ = self._shell("shoeshell", u & (z < m["ankle"] + 0.06), 0.011, D.leather_material(self.name + "_shoeshell"), solid=0.0)
        hide |= shoe
        # jacket
        if self.JACKET:
            low = {"blazer": m["hip"] - 0.015, "leather": m["hip"] - 0.015, "bomber": m["hip"] + 0.04, "coat": m["hip"] - 0.015}[self.JACKET]
            jk = u & (wh < 0.2) & (whand < 0.04) & (z > low) & (z < m["neck"] + 0.01 * hs) & (dist_wrist > 0.035)
            vz = {"blazer": m["hip"] + 0.22, "coat": m["hip"] + 0.3, "leather": m["neck"] - 0.14, "bomber": m["neck"] - 0.06}[self.JACKET]
            cx = float(co[u, 0].mean())
            vee = (y < -0.04) & (z > vz) & (np.abs(x - cx) < 0.012 + (z - vz) * 0.42)
            jk &= ~vee
            if self.JACKET in ("leather",):
                mat = leather_jacket(self.name + "_jacket", self.JACKET_COL)
            else:
                mat = W.cloth(self.name + "_jacket", self.JACKET_COL, rough=0.82, weave=520, sheen=0.25)
            off = {"blazer": 0.012, "leather": 0.014, "bomber": 0.02, "coat": 0.016}[self.JACKET]
            self.jacket, jv = self._shell("jacket", jk, off, mat, solid=0.004, displace=0.002, drape=10)
            drop = {"blazer": 0.14, "leather": 0.08, "bomber": 0.0, "coat": 0.5}[self.JACKET]
            if drop:
                self._hem(self.jacket, m["hip"], drop=drop * hs, flare=0.03 if self.JACKET != "coat" else 0.06)
            if self.JACKET != "bomber":
                self._collar(self.jacket)
            self._folds(self.jacket)
            hide |= jk
        # gloves: thin leather shells over the hands (night work; also keeps prints off the boxes)
        if self.GLOVES:
            gl = u & (whand > 0.35) | (u & (dist_wrist < 0.05) & (wh < 0.1))
            self.gloves, _ = self._shell("gloves", gl, 0.0025, D.leather_material(self.name + "_gloves", color=self.GLOVE_COL, rough=0.5, wet=0.1),
                                         solid=0.0012)
            hide |= gl
        self._hide_skin(hide)

    def _sea_boots(self):
        """Low modern shoes in SHOES colour (deveau's lofted boot with a short shaft hidden by the trouser hem)."""
        orig = D.boot_leather
        D.boot_leather = lambda name, color=None, **k: orig(name, color=(color if "sole" in name and color else self.SHOES), **k)
        try:
            super()._sea_boots()
        finally:
            D.boot_leather = orig

    # ------------------------------------------------------------------ hair
    def _scalp(self, soft=False):
        co = self.rest_co; h = self.h
        wh = D._w(h, D.HEAD); ears = D._mask_at_uv(D.os.path.join(D.MASKS, "mpfb_ears.jpg"), self.uv)
        ec = self._head_frame(); rel = co - ec; x, y, z = rel[:, 0], rel[:, 1], rel[:, 2]
        hs = self.head_scale
        head = self.used & (wh > 0.55) & (ears < 0.2)
        line = np.interp(y / hs, [-0.06, -0.03, 0.0, 0.05, 0.12], [0.088 + self.HAIRLINE, 0.078 + self.HAIRLINE * 0.8, 0.05, -0.04, -0.075]) * hs
        # receding temples: the line climbs more at the sides of the forehead
        line = line + self.HAIRLINE * 1.4 * np.clip(np.abs(x) / 0.05, 0, 1) * (y < 0.0)
        if soft:                                   # 0..1 fade over 8 mm above the line (scalp tint under the strands)
            f = np.clip((z - line) / 0.008, 0, 1) * head
        else:
            f = head & (z > line)
        if self.CROWN:
            top = np.array([0.0, 0.03, 0.12]) * hs
            f = f * (np.linalg.norm(rel - top, axis=1) > self.CROWN)
        return f

    def _scalp_tint(self):
        """Hair-coloured scalp under the strands (as in a real head of short hair, no skin shows through)."""
        h = self.h; f = self._scalp(soft=True).astype(np.float32)
        ca = h.body.data.color_attributes.new("scalp", 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set("color", np.stack([f, f, f, np.ones_like(f)], 1).ravel())
        m = h.body.data.materials[0]; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        src = p.inputs['Base Color'].links[0].from_socket
        at = N.new("ShaderNodeAttribute"); at.attribute_name = "scalp"
        mel = self.HAIR[0]
        col = tuple(max(0.004, c) for c in ((0.42 * (1 - mel) ** 1.6 + 0.012), (0.3 * (1 - mel) ** 1.7 + 0.009), (0.18 * (1 - mel) ** 1.9 + 0.006)))
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MIX'; mx.inputs[7].default_value = (*col, 1)
        L.new(at.outputs['Fac'], mx.inputs['Factor']); L.new(src, mx.inputs[6]); L.new(mx.outputs[2], p.inputs['Base Color'])

    def _grow_all(self, density):
        co = self.rest_co; h = self.h
        wh = D._w(h, D.HEAD); ears = D._mask_at_uv(D.os.path.join(D.MASKS, "mpfb_ears.jpg"), self.uv)
        lips = D._mask_at_uv(D.os.path.join(D.MASKS, "mpfb_lips.jpg"), self.uv)
        ec = self._head_frame(); rel = co - ec; x, y, z = rel[:, 0], rel[:, 1], rel[:, 2]
        hs = self.head_scale
        head = self.used & (wh > 0.55) & (ears < 0.2)
        scalp = self._scalp()
        P, bvh = self._posed_surface(); R = self.head_R
        self._mid_x = float(P[self.used, 0].mean())
        hm = D.hair_material(self.name + "_hair", *self.HAIR, rough=0.32)
        self.hair_objs = []
        self.hair_objs.append(self._strands("hair", scalp, P, bvh, int(self.HAIR_N * density), self.HAIR_LEN, 0.0016,
                                            comb=self._comb(R), lift=self.HAIR_LIFT, mat=hm, curl=self.CURL, clump=0.4, segs=8))
        brow = head & (z > 0.014 * hs) & (z < (0.03 - 0.12 * np.abs(np.abs(x) / hs - 0.03)) * hs) & (y < -0.012 * hs) & \
            (self.rest_n[:, 1] < -0.45) & (np.abs(x) > 0.011 * hs) & (np.abs(x) < 0.052 * hs)
        bm = D.hair_material(self.name + "_brows", *self.BEARD, rough=0.38)
        self.hair_objs.append(self._strands("brows", brow, P, bvh, int(1300 * density), (0.006, 0.01), 0.0006,
                                            comb=lambda p: R @ Vector((math.copysign(1.0, p.x - self._mid_x), 0, 0.2)),
                                            lift=0.0007, mat=bm, curl=0.06))
        if self.FACIAL:
            mouth = co[self.used & (lips > 0.5)].mean(0); mz = mouth[2] - ec[2]
            beard = head & (y < 0.03) & (z < -0.035) & (lips < 0.1)
            beard &= ~((z > -0.06) & (np.abs(x) < 0.045) & (y < -0.07) & (z > mz + 0.012))
            beard &= ((z < mz + 0.02) | (np.abs(x) > 0.035))
            beard &= ~((z > mz - 0.004) & (z < mz + 0.009) & (np.abs(x) < 0.026))
            tache = head & (lips < 0.1) & (y < -0.06) & (z > mz + 0.004) & (z < mz + 0.026) & (np.abs(x) < 0.04)
            if self.FACIAL in ("stubble", "beard"):
                ln = (0.002, 0.004) if self.FACIAL == "stubble" else (0.008, 0.016)
                self.hair_objs.append(self._strands("beard", beard | tache, P, bvh, int(30000 * density), ln, 0.0005,
                                                    comb=lambda p: R @ Vector((0, -0.25, -1)), lift=0.0008, mat=bm, curl=0.3, segs=4))
            if self.FACIAL == "moustache":
                self.hair_objs.append(self._strands("moustache", tache, P, bvh, int(5000 * density), (0.008, 0.014), 0.0007,
                                                    comb=lambda p: R @ Vector((math.copysign(0.7, p.x - self._mid_x), -0.2, -1)),
                                                    lift=0.0015, mat=bm, curl=0.15))

    def relaxed(self, lean=1.5, look_down=3.0, hands="sides"):
        """Natural stance: weight on one leg, arms hanging with soft elbows (hands='sides'), or hands loosely in
        front (hands='front')."""
        import poses as P
        h = self.h
        if hands == "front":
            return super().relaxed(lean=lean, look_down=look_down, hands="waist")
        P.stand(h, lean=lean, weight="L", twist=-2)
        P.head(h, pitch=look_down, yaw=-3, tilt=1.5)
        for sd in ("L", "R"):
            P.arm_down(h, sd, out=0.16, fwd=0.05, bend=14)
            P.rest_hand(h, sd, curl=28)
        self.lids(0.2)


# ----------------------------------------------------------------------------- the cast
class Leonardo(ModernMan):
    """Leonardo Notarbartolo (b. 1952, ~50): stocky Turin jeweller. Swept-back salt-and-pepper hair receding at the
    temples, navy blazer over an open pale-blue shirt, grey trousers, brown shoes. Night: dark wool coat, gloves."""
    MUSCLE = 0.5; WEIGHT = 0.78; HEIGHT = 0.42
    EXTRA = {"targets/head/head-age-incr": 0.4, "targets/neck/neck-scale-horiz-incr": 0.3}
    SKIN = dict(base=(0.5, 0.31, 0.21), weather=0.35)
    HAIR = (0.6, 0.12); HAIR_LEN = (0.018, 0.035); HAIRLINE = 0.018; CROWN = 0.0
    SHIRT = (0.42, 0.52, 0.66); JACKET = "blazer"; JACKET_COL = (0.018, 0.024, 0.05)
    TROUSERS = (0.09, 0.09, 0.095); SHOES = (0.07, 0.035, 0.015)

    def __init__(self, name="Leonardo", night=False, **kw):
        if night:
            kw.setdefault("jacket", "coat"); kw.setdefault("jacket_col", (0.025, 0.025, 0.028)); kw.setdefault("shirt", (0.05, 0.05, 0.06))
        super().__init__(name, years=50, night=night, **kw)

    def _comb(self, R):
        return lambda p: R @ Vector((0.0, 1.0, -0.15))             # swept straight back


class DOnorio(ModernMan):
    """Elio D'Onorio (~50): the alarm man. Tall and lean, dark hair worn a little longer and combed back, a brown
    leather jacket over a charcoal knit, black trousers."""
    MUSCLE = 0.45; WEIGHT = 0.38; HEIGHT = 0.68
    EXTRA = {"targets/head/head-age-incr": 0.3}
    SKIN = dict(base=(0.45, 0.28, 0.19), weather=0.3)
    HAIR = (0.92, 0.2); HAIR_LEN = (0.03, 0.05); HAIRLINE = 0.006
    SHIRT = (0.06, 0.06, 0.065); JACKET = "leather"; JACKET_COL = (0.11, 0.055, 0.025)
    TROUSERS = (0.015, 0.015, 0.017); SHOES = (0.012, 0.01, 0.01)

    def __init__(self, name="DOnorio", night=False, **kw):
        super().__init__(name, years=50, night=night, **kw)


class Finotto(ModernMan):
    """Ferdinando Finotto (~50): the heavy. Broad and muscular, close-cropped grey hair, stubble, a dark olive
    bomber jacket over a grey sweatshirt, dark jeans, black work shoes."""
    MUSCLE = 0.9; WEIGHT = 0.7; HEIGHT = 0.58
    EXTRA = {"targets/neck/neck-scale-horiz-incr": 0.6, "targets/head/head-age-incr": 0.2}
    SKIN = dict(base=(0.5, 0.3, 0.2), weather=0.45)
    HAIR = (0.5, 0.12); HAIR_N = 140000; HAIR_LEN = (0.004, 0.008); HAIRLINE = 0.004; FACIAL = "stubble"
    SHIRT = (0.2, 0.2, 0.2); JACKET = "bomber"; JACKET_COL = (0.06, 0.07, 0.035)
    TROUSERS = (0.03, 0.04, 0.07); SHOES = (0.01, 0.01, 0.01)

    def __init__(self, name="Finotto", night=False, **kw):
        super().__init__(name, years=50, night=night, **kw)


class Guard(ModernMan):
    """Diamond Center staff upstairs: pale-blue uniform shirt, navy tie, navy trousers, short dark-blond hair."""
    MUSCLE = 0.5; WEIGHT = 0.6; HEIGHT = 0.52
    HAIR = (0.55, 0.3); HAIR_LEN = (0.01, 0.02)
    SHIRT = (0.5, 0.6, 0.75); TIE = (0.02, 0.03, 0.07); JACKET = None
    TROUSERS = (0.02, 0.025, 0.05); SHOES = (0.01, 0.01, 0.01)

    def __init__(self, name="Guard", **kw):
        super().__init__(name, years=38, **kw)


class Porter(ModernMan):
    """The Monday-morning man who walks down to the vault: grey hair, beige raincoat over a grey suit."""
    MUSCLE = 0.45; WEIGHT = 0.55; HEIGHT = 0.5
    HAIR = (0.2, 0.05); HAIR_LEN = (0.012, 0.022); HAIRLINE = 0.012
    SHIRT = (0.8, 0.8, 0.78); TIE = (0.15, 0.03, 0.03); JACKET = "coat"; JACKET_COL = (0.32, 0.25, 0.15)
    TROUSERS = (0.08, 0.08, 0.085); SHOES = (0.02, 0.012, 0.008)

    def __init__(self, name="Porter", **kw):
        super().__init__(name, years=58, **kw)


class Investigator(ModernMan):
    """Police investigator on the Monday: dark hair, dark-green field jacket, jeans."""
    MUSCLE = 0.6; WEIGHT = 0.55; HEIGHT = 0.6
    HAIR = (0.9, 0.3); HAIR_LEN = (0.008, 0.016)
    SHIRT = (0.7, 0.68, 0.62); JACKET = "leather"; JACKET_COL = (0.02, 0.02, 0.022)
    TROUSERS = (0.04, 0.05, 0.08); SHOES = (0.02, 0.015, 0.01)

    def __init__(self, name="Investigator", **kw):
        super().__init__(name, years=40, **kw)


class Manager(ModernMan):
    """The Diamond Center's building manager (rents out the offices): tall, thinning light-brown hair, charcoal suit,
    white shirt, burgundy tie."""
    MUSCLE = 0.45; WEIGHT = 0.5; HEIGHT = 0.62
    HAIR = (0.6, 0.35); HAIR_LEN = (0.01, 0.02); HAIRLINE = 0.015; CROWN = 0.04
    SHIRT = (0.82, 0.82, 0.8); TIE = (0.22, 0.03, 0.05); JACKET = "blazer"; JACKET_COL = (0.05, 0.05, 0.055)
    TROUSERS = (0.05, 0.05, 0.055); SHOES = (0.01, 0.01, 0.01)

    def __init__(self, name="Manager", **kw):
        super().__init__(name, years=52, **kw)


class Police(ModernMan):
    """Belgian police, 2003: dark navy jacket, navy trousers, black boots (seen only as backlit silhouettes)."""
    MUSCLE = 0.7; WEIGHT = 0.55; HEIGHT = 0.6
    HAIR = (0.8, 0.3); HAIR_LEN = (0.006, 0.012)
    SHIRT = (0.3, 0.4, 0.55); JACKET = "bomber"; JACKET_COL = (0.015, 0.02, 0.045)
    TROUSERS = (0.015, 0.02, 0.04); SHOES = (0.008, 0.008, 0.008)

    def __init__(self, name="Police", **kw):
        super().__init__(name, years=34, **kw)


class Operator(ModernMan):
    """Alarm-company operator on the night shift: cardigan-grey sweater, dark hair."""
    MUSCLE = 0.45; WEIGHT = 0.6; HEIGHT = 0.5
    HAIR = (0.88, 0.2); HAIR_LEN = (0.015, 0.03)
    SHIRT = (0.2, 0.22, 0.25); JACKET = None
    TROUSERS = (0.06, 0.06, 0.07); SHOES = (0.02, 0.02, 0.02)

    def __init__(self, name="Operator", **kw):
        super().__init__(name, years=33, **kw)


class Trader(ModernMan):
    """Diamond traders on the Monday (several, varied): suits and coats in greys, browns and navies; one in a
    Hasidic black coat and hat brim is NOT used (no hats on the rig); distinct by build and colour only."""
    VARIANTS = [
        dict(MUSCLE=0.45, WEIGHT=0.7, HEIGHT=0.45, HAIR=(0.3, 0.1), HAIRLINE=0.02, SHIRT=(0.8, 0.8, 0.78), TIE=(0.05, 0.08, 0.2),
             JACKET="coat", JACKET_COL=(0.12, 0.1, 0.08), TROUSERS=(0.1, 0.09, 0.08)),
        dict(MUSCLE=0.5, WEIGHT=0.45, HEIGHT=0.62, HAIR=(0.95, 0.2), SHIRT=(0.55, 0.62, 0.72), TIE=None,
             JACKET="blazer", JACKET_COL=(0.14, 0.14, 0.15), TROUSERS=(0.14, 0.14, 0.15)),
        dict(MUSCLE=0.5, WEIGHT=0.6, HEIGHT=0.52, HAIR=(0.7, 0.35), FACIAL="beard", SHIRT=(0.85, 0.85, 0.83), TIE=None,
             JACKET="coat", JACKET_COL=(0.015, 0.015, 0.02), TROUSERS=(0.02, 0.02, 0.025)),
        dict(MUSCLE=0.4, WEIGHT=0.55, HEIGHT=0.48, HAIR=(0.15, 0.05), HAIRLINE=0.025, SHIRT=(0.7, 0.66, 0.6), TIE=(0.3, 0.05, 0.04),
             JACKET="blazer", JACKET_COL=(0.2, 0.15, 0.1), TROUSERS=(0.18, 0.15, 0.12)),
        dict(MUSCLE=0.55, WEIGHT=0.5, HEIGHT=0.58, HAIR=(0.85, 0.3), SHIRT=(0.3, 0.3, 0.35), TIE=None,
             JACKET="leather", JACKET_COL=(0.04, 0.03, 0.025), TROUSERS=(0.05, 0.06, 0.1)),
    ]

    def __init__(self, k=0, **kw):
        for a, v in self.VARIANTS[k % len(self.VARIANTS)].items():
            setattr(self, a, v)
        super().__init__(f"Trader{k}", years=40 + 6 * (k % 4), **kw)


CAST = {"Leonardo": Leonardo, "DOnorio": DOnorio, "Finotto": Finotto, "Guard": Guard, "Porter": Porter, "Investigator": Investigator,
        "Manager": Manager, "Police": Police, "Operator": Operator}
