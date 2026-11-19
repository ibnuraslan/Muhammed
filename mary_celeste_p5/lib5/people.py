"""Part 5 cast, built on the shared character code (mary_celeste_3d/lib/deveau.py + human.py), not a fork:
`Person` subclasses `deveau.Deveau` and only changes the body parameters, the outfit colours/cut and the hair.

  sailor(name, seed)        Mary Celeste crew: reefer jacket or a plain wool frock, caps on some
  Person("Briggs", ...)     Captain Benjamin Briggs (37): dark frock coat, full beard
  Person("Sarah", ...)      Sarah Briggs (31): dark wool dress, a shawl over head and shoulders
  Person("Sophia", ...)     Sophia (2): wrapped in a knitted shawl, curls
  Person("Arthur", ...)     Arthur (7): boy's jacket, short trousers, stockings, boots

Same rules as Deveau: clothes are shells off the skinned body (bend with it, never clip); hair is strands.
"""
import math, os
import numpy as np
import bpy, bmesh
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
        self.asset_boots = self._asset_boots(skin=True)
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

    def finish(self, *a, **k):
        place = k.get("place")
        M = place if place is not None else Matrix.Identity(4)
        hp = []
        for sd in ("L", "R"):                        # wrist and knuckles, world space after placing
            for b in (f"wrist.{sd}", f"finger3-1.{sd}"):
                if b in self.h.arm.pose.bones:
                    hp.append(M @ self.h.bone_head(b))
        self.hand_pts = hp
        D.Deveau.finish(self, *a, **k)
        flat = [c for v in self.hand_pts for c in v]
        for o in self.objects:                       # tag for lib5.clipcheck
            if o.type == 'MESH':
                o["person"] = self.name; o["hands"] = flat
        for o in getattr(self, "sea_boots", []) or []:
            if getattr(o, "type", None) == 'MESH':
                o["person"] = self.name
        for o in bpy.data.objects:                   # fitted boots/corneas created during finish carry the name
            if o.type == 'MESH' and o.name.startswith(self.name + "_") and "person" not in o:
                o["person"] = self.name; o["hands"] = flat

    # ------------------------------------------------------------------ shared-lib hooks (50560c7)
    def _asset_boots(self, skin=False):
        # shared fitted leather boots (lib >= 9499317: skinned to the legs, so they follow seated poses) for the men
        # and the boy; Sarah's boots are under her skirt and Sophia wears none, so they keep their own shells
        if self.outfit in ("sailor", "captain", "boy"):
            return D.Deveau._asset_boots(self, skin=skin)
        return True

    def _sea_boots(self):
        if self.outfit in ("sailor", "captain", "boy"):
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
        """Sarah, 1870s: a structured bodice (smoothed over the figure: corseted, no modelled bust), high standing
        collar, jet buttons down the front, full sleeves; a full skirt; a wool cloak over the shoulders to the waist,
        open in a narrow band at the front; a soft bonnet over the hair with a brim round the face and ribbons tied
        under the chin."""
        co, z, wh, whand, wfoot, dw, m = self._base_masks(); u = self.used; w = self.wet
        x, y = co[:, 0], co[:, 1]
        dress_m = D.wool_material(self.name + "_dress", self.col["dress"], weave=700, wet=w, dirt=0.12, sheen=0.45, rough=0.85)
        arm = np.abs(x) > 0.17                                        # beyond the shoulder line: the sleeves
        bod = u & (wh < 0.25) & (whand < 0.05) & (z > m["hip"] - 0.05) & (z < m["neck"] + 0.005) & (dw > 0.03)
        # corseted bodice: heavy smoothing bridges the figure into one surface; sleeves cut full (gathered)
        self.shirt, bv = self._shell("bodice", bod, 0.014, dress_m, solid=0.002, displace=0.001, drape=140,
                                     flare=lambda b: np.where(np.abs(b[:, 0]) > 0.17, 0.016, 0.0) + np.clip((b[:, 2] - (m["neck"] - 0.3)) / 0.25, 0, 1) * 0.004)
        coll = u & (z > m["neck"] - 0.03) & (z < m["neck"] + 0.07) & (wh < 0.75) & (whand < 0.05) & (dw > 0.2)
        self.collar, _ = self._shell("collar", coll, 0.007, dress_m, solid=0.003, drape=6)
        skirt = u & (z < m["hip"] + 0.02) & (z > m["ankle"] - 0.02) & (whand < 0.05)
        self.trousers, _ = self._shell("skirt", skirt, 0.03, dress_m, solid=0.003, displace=0.008, drape=60,
                                       flare=lambda b: np.clip((m["hip"] - b[:, 2]) / (m["hip"] - m["ankle"]), 0, 1) ** 1.3 * 0.07)
        boot = u & (z < m["ankle"] + 0.06)
        self.boots, _ = self._shell("boots", boot, 0.008, D.leather_material("boots", wet=w), solid=0.002, drape=60)
        # cloak over the shoulders: a lofted bell from the collar to below the elbows, hanging straight from the
        # widest point (radius never shrinks going down), so it falls over the figure instead of following it
        self.scarf = self._cape(m, D.wool_material(self.name + "_cloak", self.col["shawl"], weave=160, bump=0.7,
                                wet=w, dirt=0.15, sheen=0.5))
        self.jacket = self.shirt
        self._buttons_front(bv, n=7)
        self._bonnet()
        self._hide_skin(bod | skirt | boot | coll)

    def _cape(self, m, mat, n=72, margin=0.014):
        from mathutils.kdtree import KDTree
        h = self.h; co = self.rest_co; u = self.used
        wh = D._w(h, HEAD); whand = D._w(h, HAND)
        body = u & (wh < 0.2) & (whand < 0.02)
        top, bot = m["neck"] - 0.01, m["hip"] + 0.2
        levels = np.linspace(top, bot, 26)
        c0 = co[body & (np.abs(co[:, 2] - (top + bot) / 2) < 0.15)][:, :2].mean(0)
        ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
        dirs = np.stack([np.cos(ang), np.sin(ang)], 1)
        R = []
        for k, zl in enumerate(levels):
            sl = co[body & (np.abs(co[:, 2] - zl) < 0.012)][:, :2] - c0
            if len(sl) < 8:
                R.append(R[-1] if R else np.full(n, 0.08)); continue
            # support function of the slice in each direction = convex-hull radius along that direction
            proj = sl @ dirs.T                                     # (pts, n)
            r = proj.max(0) + margin
            if k <= 2:
                r = r + (2 - k) * 0.004                            # the collar end: snug round the neck
            R.append(r)
        R = np.array(R)
        for k in range(1, len(R)):                                 # hangs: never narrower than the level above
            R[k] = np.maximum(R[k], R[k - 1] * 0.995)
        R = sum(np.roll(R, k, axis=1) for k in (-2, -1, 0, 1, 2)) / 5.0   # soft round the body, no corners
        verts = []
        for k, zl in enumerate(levels):
            for j in range(n):
                verts.append((c0[0] + dirs[j, 0] * R[k, j], c0[1] + dirs[j, 1] * R[k, j], zl))
        faces = [[k * n + j, k * n + (j + 1) % n, (k + 1) * n + (j + 1) % n, (k + 1) * n + j] for k in range(len(levels) - 1) for j in range(n)]
        me = bpy.data.meshes.new(self.name + "_cloak"); me.from_pydata(verts, [], faces); me.update()
        o = bpy.data.objects.new(me.name, me); bpy.context.collection.objects.link(o); o.data.materials.append(mat)
        for pl in me.polygons:
            pl.use_smooth = True
        # skin: each cloak vertex takes the weights of the nearest torso/arm vertex
        idx = np.nonzero(body)[0]; kd = KDTree(len(idx))
        for i in idx:
            kd.insert(Vector(co[i]), int(i))
        kd.balance()
        near = np.array([kd.find(Vector(v))[1] for v in verts])
        h.rig.skin(o, h.W[near])
        so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.005; so.offset = -1
        sub = o.modifiers.new("Sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
        tx = bpy.data.textures.new(self.name + "_cloakfolds", "CLOUDS"); tx.noise_scale = 0.08
        d = o.modifiers.new("Folds", "DISPLACE"); d.texture = tx; d.strength = 0.006; d.texture_coords = 'OBJECT'
        o["src_verts"] = [int(i) for i in near]
        h.parts.append(o)
        return o

    def _buttons_front(self, jv, n=7):
        """Small jet buttons down the centre front of the bodice (seen in the cloak's front opening)."""
        h = self.h; co = self.rest_co[jv] + self.rest_n[jv] * 0.018
        front = co[(co[:, 1] < -0.02) & (np.abs(co[:, 0]) < 0.02)]
        mat = D._mat(self.name + "_jet")[0]; pp = mat.node_tree.nodes["Principled BSDF"]
        pp.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1); pp.inputs['Roughness'].default_value = 0.15
        zs = np.linspace(self.marks["neck"] - 0.04, self.marks["hip"] + 0.06, n)
        for zz in zs:
            cand = front[np.abs(front[:, 2] - zz) < 0.012]
            if len(cand) == 0:
                continue
            p = cand[np.argmin(cand[:, 1])]
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.005, location=tuple(p))
            bt = bpy.context.active_object; bt.name = "button"; bt.data.materials.append(mat)
            mw = bt.matrix_world.copy(); bt.parent = h.arm; bt.parent_type = 'BONE'; bt.parent_bone = "spine03"
            bpy.context.view_layer.update(); bt.matrix_world = mw
            self.button_objs.append(bt)

    def _bonnet(self):
        """A soft wool bonnet built round the skull: a hood (ellipsoidal shell fitted to contain the scalp, ears and
        back of the head with a margin), open at the face and below the nape; its front edge flares and rolls into a
        brim framing the face; ribbons from its lower front corners run under the jaw to a bow. Skinned to the head."""
        from mathutils.bvhtree import BVHTree
        h = self.h; co = self.rest_co
        wh = D._w(h, HEAD)
        eyeL = np.array(h.joint("eye.L____head")); eyeR = np.array(h.joint("eye.R____head")); ec = (eyeL + eyeR) / 2
        hs = float(np.linalg.norm(eyeL - eyeR)) / 0.064
        hc = ec + np.array([0.0, 0.045, 0.02]) * hs
        head = co[self.used & (wh > 0.6)] - hc
        # ellipsoid radii that contain the skull (x lateral, y front-back, z up), plus a cloth margin
        rx, ry, rz = [float(np.percentile(np.abs(head[:, i]), 99.5)) for i in range(3)]
        rx += 0.018 * hs; ry += 0.016 * hs; rz += 0.02 * hs
        front = -0.07 * hs                                       # the opening: this far in front of the skull centre
        nu, nv = 40, 18
        verts = []
        for j in range(nv + 1):                                  # j = 0 at the face opening .. nv at the back
            t = j / nv
            yy = front + t * (ry - front) * 0.98
            k = math.sqrt(max(0.0, 1 - (yy / ry) ** 2))          # ellipsoid cross-section scale at that depth
            k = max(k, 0.25)
            for i in range(nu + 1):
                a = math.radians(-118 + 236 * i / nu)            # from under one ear, over the top, to the other
                verts.append((hc[0] + math.sin(a) * rx * k, hc[1] + yy, hc[2] + math.cos(a) * rz * k))
        # brim: three rings in front of the opening, flaring out then rolling back
        brim = [(0.012, -0.016), (0.022, -0.026), (0.026, -0.024)]
        base = [Vector(verts[i]) for i in range(nu + 1)]
        rings = []
        for out_, fwd in brim:
            ring = []
            for i, p0 in enumerate(base):
                d = Vector((p0.x - hc[0], 0.0, p0.z - hc[2])).normalized()
                ring.append(tuple(p0 + d * out_ * hs + Vector((0, fwd * hs, 0))))
            rings.append(ring)
        allv = []
        for ring in reversed(rings):
            allv += ring
        allv += verts
        rows = len(rings) + nv + 1
        faces = [[r_ * (nu + 1) + i, r_ * (nu + 1) + i + 1, (r_ + 1) * (nu + 1) + i + 1, (r_ + 1) * (nu + 1) + i]
                 for r_ in range(rows - 1) for i in range(nu)]
        me = bpy.data.meshes.new(self.name + "_bonnet"); me.from_pydata(allv, [], faces); me.update()
        o = bpy.data.objects.new(me.name, me); bpy.context.collection.objects.link(o)
        mat = D.wool_material(self.name + "_bonnetwool", self.col.get("bonnet", (0.05, 0.035, 0.04)), rough=0.95, weave=1100, bump=0.25, sheen=0.7, dirt=0.05)
        o.data.materials.append(mat)
        for pl in me.polygons:
            pl.use_smooth = True
        so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.004; so.offset = 0
        sb = o.modifiers.new("Sub", "SUBSURF"); sb.levels = 1; sb.render_levels = 2
        self.bonnet = o
        self._skin_to(o, "head")
        # ribbons from the lower front corners of the hood, pressed onto the skin, under the jaw to a bow
        bvh = BVHTree.FromPolygons(co.tolist(), [list(f) for f in self.faces])
        def onskin(p, lift=0.004):
            loc, n, _, _ = bvh.find_nearest(Vector(p))
            return (loc + n.normalized() * lift) if loc is not None else Vector(p)
        corners = [Vector(verts[0]), Vector(verts[nu])]
        c = Vector(ec.tolist())
        chin = onskin(c + Vector((0, -0.055, -0.15)) * hs, 0.006)
        rib = D._mat(self.name + "_ribbon")[0]; rp = rib.node_tree.nodes["Principled BSDF"]
        rp.inputs['Base Color'].default_value = (*self.col.get("bonnet", (0.05, 0.035, 0.04)), 1); rp.inputs['Roughness'].default_value = 0.7
        pts = []
        for a0, sx in ((corners[0], -1), (corners[1], 1)):
            jaw = c + Vector((sx * 0.05, -0.02, -0.135)) * hs
            ctrl = [a0, jaw, chin] if not pts else [chin, jaw, a0]
            for i in range(len(ctrl) - 1):
                for t in np.linspace(0, 1, 7, endpoint=False):
                    pts.append(onskin(ctrl[i].lerp(ctrl[i + 1], float(t))))
        pts.append(onskin(corners[1]))
        import ship
        tie = ship.rope(self.name + "_ties", pts, 0.003, rib); self._skin_to(tie, "head")
        for sgn in (1, -1):
            loop = [chin + Vector((sgn * (0.006 + 0.009 * math.sin(a)), -0.004, -0.004 - 0.005 * math.cos(a) + 0.005))
                    for a in np.linspace(0, 2 * math.pi, 14)]
            bow = ship.rope(self.name + "_bow", loop, 0.0028, rib); self._skin_to(bow, "head")

    def _skin_to(self, o, bone):
        if o.type == 'CURVE':                                  # ribbons are made as curves: make them meshes to skin
            for ob in bpy.context.selected_objects:
                ob.select_set(False)
            bpy.context.view_layer.objects.active = o; o.select_set(True)
            bpy.ops.object.convert(target='MESH'); o = bpy.context.active_object
        if bone not in [b.name for b in self.h.arm.data.bones]:
            bone = "head"
        vg = o.vertex_groups.new(name=bone); vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
        md = o.modifiers.new("Armature", "ARMATURE"); md.object = self.h.arm
        self.h.parts.append(o)

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


# ----------------------------------------------------------------------------- the Briggs family: the shared cast
# (mary_celeste_3d/lib/briggs.py, women.py: v2, approved by the hub at d503977). The Person variants above are kept
# only as a reference; every shot uses these.
def briggs(wet=0.4):
    import briggs as _B
    return _B.Briggs(wet=wet, cap=True)


def sarah(wet=0.3, seated=True):
    import women as _W

    class _Sarah(_W.Sarah):
        SHAWL = (0.072, 0.064, 0.055)          # dark brown-grey wool: no pale chest that shades as anatomy

    p = _Sarah(wet=wet, seated=seated, bonnet=True, shawl=True)
    _loose_front(p)
    _tie_without_bow(p)
    return p


def _loose_front(p, half_w=0.12, drop=0.32):
    """The shawl hangs loosely over the chest: below its most forward point each front column falls straight down
    (cloth bridges the hollow under the bust instead of following it). Rest coordinates, front = -Y."""
    import numpy as np
    for o, dz in ((p.shawl, drop), (getattr(p, "bodice", None), 0.08)):
        if o is None:
            continue
        me = o.data; n = len(me.vertices)
        co = np.zeros(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        cx = float(p.rest_co[p.used, 0].mean()); cy = float(p.rest_co[p.used, 1].mean())
        front = (co[:, 1] < cy) & (np.abs(co[:, 0] - cx) < half_w)
        idx = np.nonzero(front)[0]
        new = co.copy()
        for i in idx:
            col = idx[(np.abs(co[idx, 0] - co[i, 0]) < 0.014) & (co[idx, 2] > co[i, 2]) & (co[idx, 2] < co[i, 2] + dz)]
            if len(col):
                fall = np.clip(1 - (np.abs(co[i, 0] - cx) - half_w * 0.7) / (half_w * 0.3), 0, 1)   # fade out at the sides
                y = min(co[i, 1], float(co[col, 1].min()) - 0.004)
                new[i, 1] = co[i, 1] + (y - co[i, 1]) * fall
        me.vertices.foreach_set("co", new.ravel()); me.update()


def _tie_without_bow(p):
    """Bonnet ribbons lie along the jaw and meet under the chin (no bow loops standing off the chin)."""
    import bpy, numpy as np
    from mathutils import Vector
    keep = []
    for ob in list(p.button_objs):
        if "_bowloop" in ob.name or "_bowknot" in ob.name:
            bpy.data.objects.remove(ob, do_unlink=True); continue
        if "_tie" in ob.name and ob.type == 'CURVE':
            # the last third of the ribbon runs under the jaw to a point under the chin, tight to the skin: no end
            # standing forward of the chin in profile
            U = np.nonzero(p.used)[0]; pts = ob.data.splines[0].points; n = len(pts)
            ec = np.array(p._head_frame()); hs = p.head_scale
            end = ec + np.array([0.0, -0.025, -0.125]) * hs
            k0 = n - 5; a0 = np.array(pts[k0].co[:3])
            for k in range(k0 + 1, n):
                t = (k - k0) / (n - 1 - k0); q = a0 * (1 - t) + end * t
                vi = U[int(np.argmin(np.linalg.norm(p.rest_co[U] - q, axis=1)))]
                pts[k].co = (*Vector(p.rest_co[vi] + p.rest_n[vi] * 0.005), 1)
        keep.append(ob)
    p.button_objs[:] = keep


def sophia(wet=0.2, seated=True):
    import women as _W
    return _W.Sophia(wet=wet, seated=seated, shawl=True)


def arthur(wet=0.0, seated=True):
    import women as _W
    return _W.Arthur(wet=wet, seated=seated)
