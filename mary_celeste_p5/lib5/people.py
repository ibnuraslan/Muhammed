"""Part 5 cast, built on the shared character code (mary_celeste_3d/lib/deveau.py + human.py), not a fork:
`Person` subclasses `deveau.Deveau` and only changes the body parameters, the outfit colours/cut and the hair.

  sailor(name, seed)        Mary Celeste crew: reefer jacket or a plain wool frock, caps on some
  Person("Briggs", ...)     Captain Benjamin Briggs (37): dark frock coat, full beard
  Person("Sarah", ...)      Sarah Briggs (31): dark wool dress, a shawl over head and shoulders
  Person("Sophia", ...)     Sophia (2): wrapped in a knitted shawl, curls
  Person("Arthur", ...)     Arthur (7): boy's jacket, short trousers, stockings, boots

Same rules as Deveau: clothes are shells off the skinned body (bend with it, never clip); hair is strands.
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
import human as H
import deveau as D

HEAD, HAND, FOOT = D.HEAD, D.HAND, D.FOOT


class Person(D.Deveau):
    def __init__(self, name, gender=1.0, years=34, muscle=0.6, weight=0.5, height=0.5, extra=None, wet=0.3,
                 outfit="sailor", skin=(0.43, 0.25, 0.16), weather=0.6, hair=None, colours=None):
        self.outfit = outfit
        self.hair_cfg = dict(melanin=0.82, redness=0.38, grey=0.0, beard=True, tache=True, style="short", density=1.0)
        self.hair_cfg.update(hair or {})
        self.col = dict(jacket=(0.010, 0.012, 0.02), trousers=(0.022, 0.02, 0.019), shirt=(0.62, 0.57, 0.48),
                        scarf=(0.20, 0.035, 0.025), dress=(0.03, 0.018, 0.02), shawl=(0.18, 0.06, 0.035))
        self.col.update(colours or {})
        self.h = H.Human(name, gender=gender, years=years, muscle=muscle, weight=weight, height=height,
                         extra=extra or {}, eyebrows=None, eyelashes=None, skin=None)
        h = self.h
        h.body.data.materials[0] = D.sailor_skin(name + "_skin", base=skin, weather=weather)
        if hasattr(self, "_skin_regions"):          # shared lib >= 50560c7: per-region skin variation
            self._skin_regions()
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
        self.button_objs = []
        self._dress()
        if self.hair_cfg.get("cap"):
            self._cap(self.hair_cfg["cap"])
        elif self.hair_cfg.get("style") == "short" and outfit not in ("toddler", "dress"):
            # hair-coloured scalp under the strands (as in film grooms), so short hair reads at any distance
            c = self.hair_cfg
            col = (0.02 + 0.2 * (1 - c["melanin"]) * (0.6 + c["redness"]), 0.012 + 0.12 * (1 - c["melanin"]), 0.008)
            self.scalpcap, _ = self._shell("scalp", self._scalp_mask(0.0), 0.0012, D.wool_material(name + "_scalpcol", col, rough=0.6,
                                           sheen=0.2, weave=2000, bump=0.1, dirt=0.0), solid=0.0, drape=2)
        # even-offset solidify explodes on creased/degenerate shell vertices once posed (seen: 44 m spikes on
        # the toddler's frock); plain offset is visually the same at these thicknesses
        for o in h.parts:
            for md in o.modifiers:
                if md.type == 'SOLIDIFY':
                    md.use_even_offset = False

    # ------------------------------------------------------------------ shared-lib hooks (50560c7)
    def _asset_boots(self):
        # the shared fitted leather boots suit the men (sailors, captain) and the boy; Sarah's boots are under
        # her skirt and Sophia wears none, so they keep their own shells
        if self.outfit in ("sailor", "captain", "boy"):
            return D.Deveau._asset_boots(self)
        return True

    def _sea_boots(self):
        if self.outfit in ("sailor", "captain"):
            return D.Deveau._sea_boots(self)

    # ------------------------------------------------------------------ outfits
    def _marks(self):
        h = self.h; co = self.rest_co
        m = dict(hip=h.joint("upperleg01.L____head")[2], neck=h.joint("neck01____head")[2],
                 ankle=h.joint("foot.L____head")[2], knee=h.joint("lowerleg01.L____head")[2],
                 wrist=np.array(h.joint("wrist.L____head")))
        self.marks = m
        return m

    def _dress(self):
        o = self.outfit
        if o == "sailor":
            D.Deveau._dress(self)
            self._recolour()
        elif o == "captain":
            self._captain()
        elif o == "dress":
            self._woman()
        elif o == "toddler":
            self._toddler()
        elif o == "boy":
            self._boy()

    def _recolour(self):
        w = self.wet
        self.jacket.data.materials[0] = D.wool_material(self.name + "_jacket", self.col["jacket"], weave=380, wet=w, dirt=0.2, sheen=0.3)
        self.trousers.data.materials[0] = D.wool_material(self.name + "_trousers", self.col["trousers"], weave=500, wet=w, sheen=0.25)
        self.shirt.data.materials[0] = D.linen_material(self.name + "_shirt", self.col["shirt"], wet=w)
        self.scarf.data.materials[0] = D.wool_material(self.name + "_scarf", self.col["scarf"], rough=0.8, sheen=0.3, weave=900, dirt=0.3)

    def _base_masks(self):
        h = self.h; co = self.rest_co; m = self._marks()
        wh = D._w(h, HEAD); whand = D._w(h, HAND); wfoot = D._w(h, FOOT)
        z = co[:, 2]
        dist_wrist = np.minimum(np.linalg.norm(co - m["wrist"], axis=1), np.linalg.norm(co - m["wrist"] * np.array([-1, 1, 1]), axis=1))
        return co, z, wh, whand, wfoot, dist_wrist, m

    def _captain(self):
        """Briggs: shirt, dark waistcoat under a long dark frock coat to mid-thigh, trousers, boots."""
        co, z, wh, whand, wfoot, dw, m = self._base_masks(); u = self.used; w = self.wet
        shirt = u & (wh < 0.35) & (whand < 0.25) & (z > m["hip"] - 0.06) & (z < m["neck"] + 0.035)
        self.shirt, _ = self._shell("shirt", shirt, 0.004, D.linen_material("shirt", (0.66, 0.63, 0.56), wet=w), solid=0.0015, displace=0.002)
        nk = u & (z > m["neck"] - 0.02) & (z < m["neck"] + 0.04) & (wh < 0.6) & (whand < 0.1)
        self.scarf, _ = self._shell("stock", nk, 0.010, D.wool_material("stock", (0.012, 0.01, 0.01), rough=0.6, sheen=0.4, weave=900), solid=0.003)
        trous = u & (z < m["hip"] + 0.11) & (z > m["ankle"] + 0.05) & (wfoot < 0.2) & (whand < 0.05)
        self.trousers, _ = self._shell("trousers", trous, 0.012, D.wool_material("trousers", self.col["trousers"], weave=500, wet=w, sheen=0.25),
                                       solid=0.002, displace=0.004, drape=14)
        boot = u & (z < m["ankle"] + 0.27)
        self.boots, _ = self._shell("boots", boot, 0.011, D.leather_material("boots", wet=w + 0.2), solid=0.0025, drape=90,
                                    flare=lambda b: np.clip((m["ankle"] - b[:, 2]) / 0.06, 0, 1) * 0.006)
        coat = u & (wh < 0.2) & (whand < 0.05) & (z > m["hip"] - 0.36) & (z < m["neck"] + 0.01) & (dw > 0.045)
        self.jacket, jv = self._shell("coat", coat, 0.016, D.wool_material("coat", self.col["jacket"], weave=420, wet=w, dirt=0.12, sheen=0.35),
                                      solid=0.005, displace=0.003, drape=12,
                                      flare=lambda b: np.clip((m["hip"] + 0.05 - b[:, 2]) / 0.3, 0, 1) * 0.035)
        self._collar(self.jacket); self._buttons(jv)
        self._hide_skin(shirt | trous | boot | coat)

    def _woman(self):
        """Sarah: a dark wool dress (fitted bodice, long sleeves, full skirt to the ankle) and a knitted shawl
        over the head and shoulders, tied at the throat. The skirt is a shell over the legs with a strong
        drape and flare, so it hangs as cloth rather than following each leg."""
        co, z, wh, whand, wfoot, dw, m = self._base_masks(); u = self.used; w = self.wet
        rel_head = co - np.array(self.h.joint("head____head"))
        bod = u & (wh < 0.25) & (whand < 0.05) & (z > m["hip"] - 0.05) & (z < m["neck"] + 0.03) & (dw > 0.03)
        dress_m = D.wool_material(self.name + "_dress", self.col["dress"], weave=700, wet=w, dirt=0.12, sheen=0.45, rough=0.85)
        self.shirt, _ = self._shell("bodice", bod, 0.009, dress_m, solid=0.002, displace=0.0015, drape=24)
        skirt = u & (z < m["hip"] + 0.02) & (z > m["ankle"] - 0.02) & (whand < 0.05)
        self.trousers, _ = self._shell("skirt", skirt, 0.03, dress_m, solid=0.003, displace=0.008, drape=60,
                                       flare=lambda b: np.clip((m["hip"] - b[:, 2]) / (m["hip"] - m["ankle"]), 0, 1) ** 1.3 * 0.11
                                       + np.clip(-b[:, 1] * 0.0, 0, 1))
        boot = u & (z < m["ankle"] + 0.06)
        self.boots, _ = self._shell("boots", boot, 0.008, D.leather_material("boots", wet=w), solid=0.002, drape=60)
        # shawl: crown, back of head and neck, shoulders and upper back/chest; the face stays open
        ec = (np.array(self.h.joint("eye.L____head")) + np.array(self.h.joint("eye.R____head"))) / 2
        r = co - ec
        hs = float(np.linalg.norm(np.array(self.h.joint("eye.L____head")) - np.array(self.h.joint("eye.R____head")))) / 0.064
        face = (r[:, 1] < 0.012 * hs) & (r[:, 2] < 0.05 * hs) & (r[:, 2] > -0.17 * hs) & (np.abs(r[:, 0]) < 0.082 * hs)
        hood = u & (wh > 0.3) & ~face & (r[:, 2] > -0.2)
        cape = u & (wh < 0.6) & (whand < 0.05) & (z > m["neck"] - 0.24) & (z < m["neck"] + 0.06) & (dw > 0.2)
        self.scarf, _ = self._shell("shawl", hood | cape, 0.022, D.wool_material(self.name + "_shawl", self.col["shawl"], weave=160, bump=0.8,
                                    wet=w, dirt=0.15, sheen=0.5), solid=0.006, displace=0.006, drape=30)
        self.jacket = self.shirt
        self._hide_skin(bod | skirt | boot | (cape & (wh < 0.2)))

    def _toddler(self):
        """Sophia: a long woollen frock and a knitted shawl wrapped round her, bonnet-like over the head."""
        co, z, wh, whand, wfoot, dw, m = self._base_masks(); u = self.used; w = self.wet
        frock = u & (wh < 0.3) & (whand < 0.05) & (wfoot < 0.05) & (z < m["neck"] + 0.02) & (z > m["ankle"] + 0.04) & (dw > 0.02)
        self.shirt, _ = self._shell("frock", frock, 0.012, D.wool_material(self.name + "_frock", self.col["dress"], weave=900, wet=w, sheen=0.5),
                                    solid=0.002, drape=10,
                                    flare=lambda b: np.clip((m["hip"] - b[:, 2]) / 0.25, 0, 1) * 0.05)
        ec = (np.array(self.h.joint("eye.L____head")) + np.array(self.h.joint("eye.R____head"))) / 2
        r = co - ec
        hs = float(np.linalg.norm(np.array(self.h.joint("eye.L____head")) - np.array(self.h.joint("eye.R____head")))) / 0.064
        face = (r[:, 1] < 0.012 * hs) & (r[:, 2] < 0.05 * hs) & (r[:, 2] > -0.17 * hs) & (np.abs(r[:, 0]) < 0.082 * hs)
        hood = u & (wh > 0.3) & ~face & (r[:, 2] > -0.15)
        cape = u & (wh < 0.6) & (whand < 0.05) & (z > m["hip"] - 0.05) & (z < m["neck"] + 0.05) & (dw > 0.06)
        self.scarf, _ = self._shell("shawl", hood | cape, 0.02, D.wool_material(self.name + "_shawl", self.col["shawl"], weave=200, bump=0.9,
                                    wet=w, sheen=0.6), solid=0.005, displace=0.004, drape=14)
        self.trousers = self.jacket = self.shirt
        self._hide_skin(frock | (cape & (wh < 0.2)))

    def _boy(self):
        """Arthur: linen shirt with a soft collar, brown wool jacket, knee breeches, dark stockings, boots."""
        co, z, wh, whand, wfoot, dw, m = self._base_masks(); u = self.used; w = self.wet
        shirt = u & (wh < 0.35) & (whand < 0.25) & (z > m["hip"] - 0.06) & (z < m["neck"] + 0.03)
        self.shirt, _ = self._shell("shirt", shirt, 0.004, D.linen_material("shirt", self.col["shirt"], wet=w), solid=0.0015, displace=0.0015)
        breeches = u & (z < m["hip"] + 0.08) & (z > m["knee"] - 0.04) & (whand < 0.05)
        self.trousers, _ = self._shell("breeches", breeches, 0.01, D.wool_material("breeches", self.col["trousers"], weave=600, wet=w),
                                       solid=0.002, displace=0.002, drape=12)
        stock = u & (z <= m["knee"] - 0.04) & (z > m["ankle"] + 0.03)
        self.stock, _ = self._shell("stockings", stock, 0.003, D.wool_material("stockings", (0.03, 0.028, 0.03), weave=1400, sheen=0.4), solid=0.001)
        boot = u & (z <= m["ankle"] + 0.05)
        self.boots, _ = self._shell("boots", boot, 0.007, D.leather_material("boots", wet=w), solid=0.002, drape=60)
        jacket = u & (wh < 0.2) & (whand < 0.05) & (z > m["hip"] - 0.06) & (z < m["neck"] + 0.0) & (dw > 0.04)
        self.jacket, jv = self._shell("jacket", jacket, 0.012, D.wool_material("jacket", self.col["jacket"], weave=420, wet=w, dirt=0.15, sheen=0.35),
                                      solid=0.004, displace=0.002, drape=10)
        self._collar(self.jacket)
        self.scarf = None
        self._hide_skin(shirt | breeches | stock | boot | jacket)

    def _scalp_mask(self, margin=0.0):
        h = self.h; co = self.rest_co
        wh = D._w(h, HEAD); ears = D._mask_at_uv(D.os.path.join(D.MASKS, "mpfb_ears.jpg"), self.uv)
        eyeL = np.array(h.joint("eye.L____head")); eyeR = np.array(h.joint("eye.R____head"))
        ec = (eyeL + eyeR) / 2; hs = float(np.linalg.norm(eyeL - eyeR)) / 0.064
        rel = (co - ec) / hs
        line = np.interp(rel[:, 1], [-0.12, -0.06, 0.0, 0.05, 0.12], [0.06, 0.05, 0.02, -0.05, -0.085])
        return self.used & (wh > 0.55) & (ears < 0.2) & (rel[:, 2] > line + margin)

    def _cap(self, colour):
        """A knitted wool watch cap, pulled down to the top of the ears (sailors, November)."""
        m = self._scalp_mask(0.012)
        self.cap, _ = self._shell("cap", m, 0.014, D.wool_material(self.name + "_cap", colour, weave=260, bump=0.9, sheen=0.5,
                                  wet=self.wet, dirt=0.2), solid=0.004, displace=0.003, drape=8)
        for md in self.cap.modifiers:
            if md.type == 'SOLIDIFY':
                md.use_even_offset = False

    # ------------------------------------------------------------------ hair
    def _grow_all(self, density):
        cfg = self.hair_cfg
        density *= cfg.get("density", 1.0)
        co = self.rest_co; h = self.h
        wh = D._w(h, HEAD)
        ears = D._mask_at_uv(D.os.path.join(D.MASKS, "mpfb_ears.jpg"), self.uv)
        lips = D._mask_at_uv(D.os.path.join(D.MASKS, "mpfb_lips.jpg"), self.uv)
        eyeL = np.array(h.joint("eye.L____head")); eyeR = np.array(h.joint("eye.R____head"))
        ec = (eyeL + eyeR) / 2
        hs = float(np.linalg.norm(eyeL - eyeR)) / 0.064            # head scale (children are smaller)
        mouth = co[self.used & (lips > 0.5)].mean(0)
        rel = (co - ec) / hs
        x, y, z = rel[:, 0], rel[:, 1], rel[:, 2]
        head = self.used & (wh > 0.55) & (ears < 0.2)
        line = np.interp(y, [-0.12, -0.06, 0.0, 0.05, 0.12], [0.06, 0.05, 0.02, -0.05, -0.085])
        scalp = head & (z > line)
        P, bvh = self._posed_surface(); R = self.head_R
        mat = D.hair_material(self.name + "_hair", cfg["melanin"], cfg["redness"], grey=cfg.get("grey", 0.0))
        self.hair_objs = []
        st = cfg["style"]
        if cfg.get("cap"):
            scalp = scalp & ~self._scalp_mask(0.03)       # only the hair that shows under the cap
        if st == "short":
            self.hair_objs.append(self._strands("hair", scalp, P, bvh, int(60000 * density), (0.014 * hs, 0.03 * hs), 0.001,
                                                comb=lambda p: R @ Vector((0, 0.8, -0.45)), lift=0.0022, mat=mat, curl=0.25))
        elif st == "parted":
            # centre parting, combed down and back toward a knot under the shawl (only the front shows)
            front = scalp & (y < 0.0)
            self.hair_objs.append(self._strands("hair", front, P, bvh, int(40000 * density), (0.05 * hs, 0.08 * hs), 0.0008,
                                                comb=lambda p: R @ Vector((math.copysign(0.75, p.x - self._mid_x), 0.55, -0.4)),
                                                lift=0.0015, mat=mat, curl=0.06, segs=9))
        elif st == "curls":
            self.hair_objs.append(self._strands("hair", scalp, P, bvh, int(30000 * density), (0.03 * hs, 0.05 * hs), 0.0009,
                                                comb=lambda p: R @ Vector((0, 0.3, -1)), lift=0.003, mat=mat, curl=0.9, segs=9))
        if cfg.get("beard"):
            mz = (np.array(mouth)[2] - ec[2]) / hs
            beard = head & (y < 0.03) & (z < -0.035) & (lips < 0.1) & ~((np.abs(x) < 0.03) & (y < -0.06) & (z > mz - 0.012) & (z < mz + 0.008))
            beard &= ~((z > -0.06) & (np.abs(x) < 0.045) & (y < -0.07) & (z > mz + 0.012))
            beard &= ((z < mz + 0.02) | (np.abs(x) > 0.035))
            beard &= ~((z > mz - 0.004) & (z < mz + 0.009) & (np.abs(x) < 0.026))
            neck = self.used & (wh > 0.3) & (z < -0.11) & (z > -0.16) & (y < 0.0)
            bl = cfg.get("beard_len", (0.014, 0.03))
            self.hair_objs.append(self._strands("beard", beard | neck, P, bvh, int(46000 * density), bl, 0.0009,
                                                comb=lambda p: R @ Vector((0, -0.25, -1)), lift=0.003, mat=mat, curl=0.45))
            if cfg.get("tache", True):
                tache = head & (lips < 0.1) & (y < -0.06) & (z > mz + 0.004) & (z < mz + 0.026) & (np.abs(x) < 0.04)
                self.hair_objs.append(self._strands("moustache", tache, P, bvh, int(5000 * density), (0.012, 0.02), 0.0008,
                                                    comb=lambda p: R @ Vector((math.copysign(0.7, p.x - self._mid_x), -0.2, -1)),
                                                    lift=0.002, mat=mat, curl=0.2))
        brow = head & (z > 0.012) & (z < 0.03) & (y < -0.055) & (np.abs(x) > 0.012) & (np.abs(x) < 0.058)
        self.hair_objs.append(self._strands("brows", brow, P, bvh, int(2600 * density), (0.006 * hs, 0.011 * hs), 0.0006,
                                            comb=lambda p: R @ Vector((math.copysign(1.0, p.x - self._mid_x), 0, 0.35)),
                                            lift=0.0012, mat=mat, curl=0.1))


# ----------------------------------------------------------------------------- the crew
CREW = [  # name, years, weight, height, hair melanin/redness, beard, jacket colour, scarf colour
    ("Richardson", 28, 0.5, 0.6, (0.9, 0.3), True, (0.012, 0.014, 0.025), (0.05, 0.05, 0.06)),
    ("Gilling", 25, 0.45, 0.5, (0.5, 0.6), False, (0.035, 0.022, 0.014), (0.25, 0.12, 0.03)),
    ("Head", 23, 0.55, 0.45, (0.35, 0.5), False, (0.05, 0.05, 0.045), (0.08, 0.1, 0.16)),
    ("Lorenzen_V", 29, 0.55, 0.6, (0.3, 0.45), True, (0.014, 0.018, 0.03), (0.2, 0.035, 0.025)),
    ("Lorenzen_B", 25, 0.5, 0.58, (0.3, 0.45), False, (0.02, 0.016, 0.012), (0.14, 0.03, 0.02)),
    ("Martens", 35, 0.6, 0.52, (0.7, 0.4), True, (0.012, 0.012, 0.016), (0.06, 0.08, 0.05)),
    ("Goodschaad", 23, 0.45, 0.55, (0.45, 0.55), False, (0.04, 0.03, 0.02), (0.18, 0.15, 0.1)),
]


def sailor(i, wet=0.4):
    n, yrs, wt, ht, (mel, red), beard, jc, sc = CREW[i]
    rng = np.random.default_rng(i + 3)
    extra = {"targets/chin/chin-prominent-incr": float(rng.uniform(0, 0.4)), "targets/nose/nose-hump-incr": float(rng.uniform(0, 0.5)),
             "targets/nose/nose-scale-vert-incr": float(rng.uniform(-0.1, 0.3)),
             "targets/cheek/l-cheek-bones-incr": float(rng.uniform(0, 0.4)), "targets/cheek/r-cheek-bones-incr": float(rng.uniform(0, 0.4)),
             "targets/eyebrows/eyebrows-trans-down": float(rng.uniform(0, 0.4))}
    caps = [(0.02, 0.025, 0.05), (0.25, 0.05, 0.03), (0.03, 0.03, 0.03), (0.05, 0.06, 0.09), (0.2, 0.16, 0.1), (0.03, 0.035, 0.05), (0.12, 0.03, 0.02)]
    return Person(n, 1.0, yrs, muscle=0.62, weight=wt, height=ht, extra=extra, wet=wet, outfit="sailor",
                  skin=(0.45 + rng.uniform(-0.04, 0.04), 0.26, 0.17), hair=dict(melanin=mel, redness=red, beard=beard, cap=caps[i]),
                  colours=dict(jacket=jc, scarf=sc))


def briggs(wet=0.4):
    extra = {"targets/chin/chin-prominent-incr": 0.2, "targets/nose/nose-scale-vert-incr": 0.25,
             "targets/eyebrows/eyebrows-trans-down": 0.35, "targets/head/head-age-incr": 0.2}
    return Person("Briggs", 1.0, 37, muscle=0.6, weight=0.5, height=0.58, extra=extra, wet=wet, outfit="captain",
                  hair=dict(melanin=0.88, redness=0.3, beard=True, beard_len=(0.03, 0.06), cap=(0.012, 0.014, 0.024)),
                  colours=dict(jacket=(0.008, 0.009, 0.012), trousers=(0.012, 0.012, 0.014)))


def sarah(wet=0.4):
    extra = {"targets/nose/nose-scale-horiz-decr": 0.2, "targets/chin/chin-width-decr": 0.2}
    return Person("Sarah", 0.0, 31, muscle=0.45, weight=0.45, height=0.45, extra=extra, wet=wet, outfit="dress",
                  skin=(0.55, 0.36, 0.28), weather=0.25, hair=dict(melanin=0.85, redness=0.35, beard=False, style="parted"),
                  colours=dict(dress=(0.035, 0.02, 0.028), shawl=(0.075, 0.03, 0.022)))


def sophia(wet=0.3):
    return Person("Sophia", 0.0, 2, muscle=0.5, weight=0.55, height=0.5, wet=wet, outfit="toddler",
                  skin=(0.6, 0.4, 0.32), weather=0.1, hair=dict(melanin=0.55, redness=0.6, beard=False, style="curls"),
                  colours=dict(dress=(0.25, 0.22, 0.18), shawl=(0.5, 0.42, 0.3)))


def arthur(wet=0.0):
    return Person("Arthur", 1.0, 7, muscle=0.5, weight=0.5, height=0.5, wet=wet, outfit="boy",
                  skin=(0.58, 0.39, 0.3), weather=0.15, hair=dict(melanin=0.7, redness=0.45, beard=False, style="short"),
                  colours=dict(jacket=(0.07, 0.04, 0.022), trousers=(0.03, 0.03, 0.035), shirt=(0.7, 0.67, 0.6)))
