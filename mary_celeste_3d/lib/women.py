"""Sarah Briggs (31) and Sophia Briggs (2), 1872: the shared women/child cast, built on deveau.Deveau.

Sarah: a structured day bodice (smoothed over the corseted torso, so it never clings), a high band collar with a
white linen edge and jet buttons down the front, full coat sleeves, a bell skirt to the floor that is fuller behind,
a knitted wool shawl over the shoulders, and a soft brimmed bonnet with ribbon ties under the chin. Hair centre-parted
and drawn back. Boots under the skirt.
Sophia: a toddler's wool frock (yoke, short puffed sleeves, full skirt to below the knee) with a white pinafore over
it (bib, shoulder straps, apron), cream stockings and little ankle boots; soft curls.

    s = Sarah(wet=0.2);  P.stand(s.h, ...);  s.finish(look_at=..., place=M)
    k = Sophia();        ...;               k.finish(...)

Standing and walking poses: the skirt rides on the pelvis (it is not split over the legs). For seated poses pass
seated=True: the skirt is then a draped shell over the thighs instead of a bell.
"""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import human as H
import deveau as D


def cloth(name, color, rough=0.8, sheen=0.4, weave=600.0, bump=0.25, wet=0.0, knit=False):
    m = D.wool_material(name, color, rough=rough, sheen=sheen, weave=weave, bump=bump, wet=wet, dirt=0.15)
    if knit:                                   # knitted: bold rib texture in the bump
        N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
        wv.inputs['Scale'].default_value = 140; wv.inputs['Distortion'].default_value = 1.5; L.new(tc.outputs['Object'], wv.inputs['Vector'])
        b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.6; L.new(wv.outputs['Fac'], b.inputs['Height'])
        L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def jet(name="jet"):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1); p.inputs['Roughness'].default_value = 0.15
    p.inputs['Coat Weight'].default_value = 0.6
    return m


class _Woman(D.Deveau):
    GENDER = 0.0; MUSCLE = 0.4; WEIGHT = 0.45; HEIGHT = 0.45
    EXTRA = {}
    SKIN = dict(base=(0.5, 0.32, 0.23), weather=0.3)        # warm, natural (same SSS/colour range as Deveau)
    ASSET_BOOTS = False
    HAIR = (0.7, 0.4)                          # melanin, redness
    HAIR_LIFT = 0.0025

    def __init__(self, name, years, wet=0.0, seated=False, bonnet=True, shawl=True):
        self.seated = seated; self.want_bonnet = bonnet; self.want_shawl = shawl
        self.button_objs = []
        super().__init__(name=name, years=years, wet=wet)

    def relaxed(self, lean=2.0, look_down=4.0, hands="waist"):
        """Natural default: weight on one leg, soft elbows, hands loosely together in front at the waist, lids relaxed."""
        import poses as P
        h = self.h; m = self.marks
        P.stand(h, lean=lean, weight="L", twist=-2)
        P.head(h, pitch=look_down, yaw=-4, tilt=2)
        hs = self.head_scale
        front = float(self.rest_co[self.used & (np.abs(self.rest_co[:, 2] - (m["hip"] + 0.1 * hs)) < 0.03), 1].min())
        cx = float(self.rest_co[self.used, 0].mean())
        zt = m["hip"] + (0.1 if hands == "waist" else 0.02) * hs
        for sd, sg in (("L", 1), ("R", -1)):
            P.hand_reach(h, sd, Vector((cx + sg * 0.035 * hs, front - 0.1 * hs, zt)), elbow=(sg * 1.0, 0.25, -0.5))
            h.aim(f"wrist.{sd}", Vector((-sg * 0.8, -0.35, -0.3)))
            P.rest_hand(h, sd, curl=34)
        self.lids(0.3)

    # ---------------------------------------------------------------- shared helpers
    def _m(self):
        h = self.h; co = self.rest_co
        m = dict(hip=h.joint("upperleg01.L____head")[2], neck=h.joint("neck01____head")[2],
                 ankle=h.joint("foot.L____head")[2], knee=h.joint("lowerleg01.L____head")[2],
                 waist=h.joint("spine04____head")[2] if "spine04____head" in h.rig.joint else h.joint("upperleg01.L____head")[2] + 0.12)
        self.marks = m
        wh = D._w(h, D.HEAD); whand = D._w(h, D.HAND); wfoot = D._w(h, D.FOOT)
        warm = D._w(h, ("upperarm", "lowerarm"))
        return m, wh, whand, wfoot, warm

    def _band_collar(self, m, wh, whand, top, mat, offset=0.012):
        u = self.used; z = self.rest_co[:, 2]
        band = u & (z > top - 0.012) & (z < top + 0.004) & (wh < 0.75) & (whand < 0.1)
        o, _ = self._shell("collar_edge", band, offset, mat, solid=0.002)
        Sarah._soft_edge(self, o, iters=20)
        return o

    def _bell(self, label, mat, z_top, z_bottom, R, back=0.06, folds=9, arc=None, offset=0.02, nr=72, nh=26):
        """Lathe skirt from z_top to z_bottom around the body, fuller behind (bustle). It always clears the body by
        `offset`. arc=(a0, a1) in degrees makes an open panel (an apron) instead of a full ring. Rides on the pelvis."""
        h = self.h
        limbs = (D._w(h, ("upperarm", "lowerarm", "wrist", "metacarpal", "finger", "clavicle", "shoulder")) > 0.2)
        co = self.rest_co[self.used & ~limbs]
        cx = float(co[:, 0].mean()); cy = float(co[(co[:, 2] > z_bottom) & (co[:, 2] < z_top), 1].mean())
        a0, a1 = (0.0, 360.0) if arc is None else arc
        full = arc is None
        n_a = nr if full else max(8, int(nr * (a1 - a0) / 360))
        V = []; F = []; rows = []
        for j in range(nh + 1):
            t = j / nh; z = z_top + (z_bottom - z_top) * t
            band = co[np.abs(co[:, 2] - z) < 0.03]
            row = []
            for i in range(n_a + (0 if full else 1)):
                a = math.radians(a0 + (a1 - a0) * i / (n_a if not full else n_a))
                d = np.array([math.sin(a), -math.cos(a)])          # a = 0 is the front (-Y)
                need = 0.0
                if len(band):
                    rel = band[:, :2] - [cx, cy]; proj = rel @ d
                    side = np.abs(rel @ np.array([-d[1], d[0]])) < 0.06
                    if side.any():
                        need = float(proj[side].max())
                behind = max(0.0, -d[1])                              # 1 at the back
                base = need + offset
                bell = (R - base) * (t ** 1.35) if R > base else 0.0
                r = base + bell + back * behind * t ** 0.8
                r += 0.016 * t ** 1.4 * math.cos(a * folds + 0.7 * math.sin(a * 3)) * (0.3 + 0.7 * t)
                row.append(len(V)); V.append((cx + d[0] * r, cy + d[1] * r, z))
            rows.append(row)
        for j in range(nh):
            cols = len(rows[j])
            for i in range(cols if full else cols - 1):
                i2 = (i + 1) % cols
                F.append([rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]])
        o = D.mesh_obj(f"{self.name}_{label}", V, F, mat)
        sm = o.modifiers.new("Smooth", "SMOOTH"); sm.factor = 0.7; sm.iterations = 12        # even out the bell
        so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.004; so.offset = 1; so.thickness_clamp = 1.0
        sb = o.modifiers.new("Sub", "SUBSURF"); sb.levels = 1; sb.render_levels = 2
        vg = o.vertex_groups.new(name="spine05"); vg.add(list(range(len(V))), 1.0, 'REPLACE')
        mod = o.modifiers.new("Armature", "ARMATURE"); mod.object = self.h.arm
        o.modifiers.move(len(o.modifiers) - 1, 0)
        o.parent = self.h.arm
        self.h.parts.append(o)
        return o

    def _front_buttons(self, jv, z_lo, z_hi, n, offset, r=0.0055, mat=None):
        h = self.h; co = self.rest_co[jv] + self.rest_n[jv] * offset
        front = co[(np.abs(co[:, 0] - self.rest_co[self.used, 0].mean()) < 0.012) & (co[:, 1] < 0)]
        self.button_objs = getattr(self, "button_objs", [])
        mat = mat or jet(self.name + "_jet")
        for k in range(n):
            z = z_hi - (z_hi - z_lo) * k / max(1, n - 1)
            cand = front[np.abs(front[:, 2] - z) < 0.01]
            if not len(cand):
                continue
            p = cand[np.argmin(cand[:, 1])]
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=r, location=tuple(p))
            b = bpy.context.active_object; b.name = "button"; b.scale = (1, 0.6, 1)
            bpy.ops.object.shade_smooth(); b.data.materials.append(mat)
            bpy.context.view_layer.update(); mw = b.matrix_world.copy()
            bone = "neck01" if z > self.marks["neck"] - 0.03 else ("spine03" if z > self.marks["hip"] + 0.25 else "spine05")
            b.parent = h.arm; b.parent_type = 'BONE'; b.parent_bone = bone
            bpy.context.view_layer.update(); b.matrix_world = mw
            self.button_objs.append(b)

    def _stockings_and_shoes(self, m, wh, whand, wfoot, color, top):
        u = self.used; z = self.rest_co[:, 2]
        st = u & (z < top) & (whand < 0.05)
        self.trousers, _ = self._shell("stockings", st, 0.003, cloth(self.name + "_stockings", color, rough=0.7, sheen=0.5, weave=1400),
                                       solid=0.001)
        boot = u & (z < m["ankle"] + 0.27)
        self.boot_mask = boot.copy()
        self.boots, _ = self._shell("boots", boot, 0.011, D.leather_material(self.name + "_bootshell"), solid=0.0025, drape=60)
        return st

    def _head_frame(self):
        h = self.h
        ec = (np.array(h.joint("eye.L____head")) + np.array(h.joint("eye.R____head"))) / 2
        return ec

    # ---------------------------------------------------------------- hair (no beard)
    def _grow_all(self, density):
        co = self.rest_co; h = self.h
        wh = D._w(h, D.HEAD); ears = D._mask_at_uv(D.os.path.join(D.MASKS, "mpfb_ears.jpg"), self.uv)
        ec = self._head_frame(); rel = co - ec; x, y, z = rel[:, 0], rel[:, 1], rel[:, 2]
        hs = self.head_scale
        head = self.used & (wh > 0.55) & (ears < 0.2)
        line = np.interp(y / hs, [-0.06, -0.03, 0.0, 0.05, 0.12], [0.085, 0.075, 0.045, -0.05, -0.08]) * hs
        scalp = head & (z > line)
        brow = head & (z > 0.014 * hs) & (z < (0.03 - 0.12 * np.abs(np.abs(x) / hs - 0.03)) * hs) & (y < -0.012 * hs) & \
               (self.rest_n[:, 1] < -0.45) & (np.abs(x) > 0.011 * hs) & (np.abs(x) < 0.05 * hs)
        P, bvh = self._posed_surface(); R = self.head_R
        self._mid_x = float(P[self.used, 0].mean())
        hm = D.hair_material(self.name + "_hair", *self.HAIR, rough=0.3)
        self.hair_objs = []
        bun = self._bun_point(P) if isinstance(self, Sarah) else None
        self.hair_objs.append(self._strands("hair", scalp, P, bvh, int(self.HAIR_N * density), self.HAIR_LEN, 0.0009,
                                            comb=self._comb(R), lift=self.HAIR_LIFT, mat=hm, curl=self.CURL, clump=0.45, segs=10,
                                            attract=bun))
        if isinstance(self, Sarah):
            self._bun(P, R, hm, density)
        self.hair_objs.append(self._strands("brows", brow, P, bvh, int(900 * density), (0.005, 0.008), 0.0005,
                                            comb=lambda p: R @ Vector((math.copysign(1.0, p.x - self._mid_x), 0, 0.2)),
                                            lift=0.0006, mat=hm, curl=0.05))

    @property
    def head_scale(self):
        h = self.h
        return float(np.linalg.norm(np.array(h.joint("eye.L____head")) - np.array(h.joint("eye.R____head")))) / 0.064


class Sarah(_Woman):
    HAIR_N = 90000; HAIR_LEN = (0.08, 0.13); CURL = 0.1; HAIR_LIFT = 0.0055
    HAIR = (0.88, 0.3)
    DRESS = (0.075, 0.035, 0.045)     # deep plum-brown wool
    SHAWL = (0.2, 0.17, 0.13)         # undyed grey-brown knitted wool
    BONNET = (0.06, 0.06, 0.075)      # dark slate silk-cotton
    EXTRA = {"targets/cheek/l-cheek-bones-incr": 0.2, "targets/cheek/r-cheek-bones-incr": 0.2,
             "targets/nose/nose-scale-horiz-decr": 0.2,
             # corseted 1870s figure: a smooth single curve under the bodice, no separate bust shapes
             "targets/breast/female-young-averagemuscle-averageweight-mincup-averagefirmness": 0.8,
             "targets/breast/breast-point-decr": 1.0, "targets/breast/breast-dist-decr": 0.6}

    def __init__(self, name="Sarah", years=31, wet=0.0, seated=False, bonnet=True, shawl=True):
        """bonnet=False indoors (hair then shows whole: centre parting drawn back to a low knot); shawl optional."""
        super().__init__(name, years, wet=wet, seated=seated, bonnet=bonnet, shawl=shawl)

    def _comb(self, R):
        mid = lambda: self._mid_x
        return lambda p: R @ Vector((math.copysign(0.45, p.x - mid()), 0.9, -0.3))    # centre parting, drawn back

    def _bun_point(self, P):
        h = self.h; hs = self.head_scale
        hd = P[self.used & (D._w(h, D.HEAD) > 0.6)]
        # back of the head, low (posed positions; the head may be turned: use the head rotation)
        ctr = hd.mean(0); back = self.head_R @ Vector((0, 1, 0)); down = self.head_R @ Vector((0, 0, -1))
        return tuple(Vector(ctr) + back * 0.085 * hs + down * 0.035 * hs)

    def _bun(self, P, R, hm, density):
        """A low bun at the nape: a coiled core of hair wound with clumped strands (rides with the head)."""
        h = self.h; hs = self.head_scale
        c = Vector(self._bun_point(P))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.032 * hs, location=c)
        core = bpy.context.active_object; core.name = self.name + "_bun"; core.scale = (1.25, 0.85, 0.9)
        bpy.ops.object.shade_smooth()
        bm_ = bpy.data.materials.new(self.name + "_buncore"); bm_.use_nodes = True
        bp = bm_.node_tree.nodes["Principled BSDF"]; bp.inputs['Base Color'].default_value = (0.03, 0.018, 0.012, 1)
        bp.inputs['Roughness'].default_value = 0.45; bp.inputs['Sheen Weight'].default_value = 0.6
        tc = bm_.node_tree.nodes.new("ShaderNodeTexCoord"); wv = bm_.node_tree.nodes.new("ShaderNodeTexWave")
        wv.wave_type = 'RINGS'; wv.inputs['Scale'].default_value = 25; wv.inputs['Distortion'].default_value = 6
        bm_.node_tree.links.new(tc.outputs['Object'], wv.inputs['Vector'])
        bb = bm_.node_tree.nodes.new("ShaderNodeBump"); bb.inputs['Strength'].default_value = 0.8
        bm_.node_tree.links.new(wv.outputs['Fac'], bb.inputs['Height']); bm_.node_tree.links.new(bb.outputs['Normal'], bp.inputs['Normal'])
        core.data.materials.append(bm_)
        self.button_objs.append(core)
        # coiled strands wound round the core
        rng = np.random.default_rng(11); n = int(4000 * density); segs = 14
        pts = np.zeros((n, segs, 3), np.float32)
        rad = 0.033 * hs
        for i in range(n):
            a0 = rng.uniform(0, 2 * math.pi); el = rng.uniform(-1.1, 1.1); tilt = rng.uniform(-0.3, 0.3)
            for k in range(segs):
                a = a0 + k * 0.32
                r = rad * (1.02 + 0.06 * rng.random())
                v = Vector((math.cos(a) * math.cos(el + tilt * math.sin(a)) * 1.25, math.sin(el + tilt * math.sin(a)) * 0.85,
                            math.sin(a) * math.cos(el) * 0.9)) * r
                pts[i, k] = c + v
        cv = bpy.data.hair_curves.new(self.name + "_bunhair"); cv.add_curves([segs] * n)
        cv.position_data.foreach_set("vector", pts.reshape(-1))
        try:
            cv.attributes["radius"].data.foreach_set("value", np.full(n * segs, 0.00005, np.float32))
        except Exception:
            pass
        ob = bpy.data.objects.new(cv.name, cv); bpy.context.collection.objects.link(ob); cv.materials.append(hm)
        self.hair_objs.append(ob)

    def _dress(self):
        m, wh, whand, wfoot, warm = self._m()
        u = self.used; co = self.rest_co; z = co[:, 2]; y = co[:, 1]
        wrist = np.array(self.h.joint("wrist.L____head"))
        dist_wrist = np.minimum(np.linalg.norm(co - wrist, axis=1), np.linalg.norm(co - wrist * np.array([-1, 1, 1]), axis=1))
        dress = cloth(self.name + "_dress", self.DRESS, rough=0.7, sheen=0.35, weave=700, wet=self.wet)
        top = m["neck"] + 0.06
        # bodice: corseted torso -> heavy drape smoothing (no cling), full coat sleeves to the wrist
        bod = u & (wh < 0.6) & (whand < 0.04) & (z > m["hip"] + 0.02) & (z < top) & (dist_wrist > 0.03)
        self.bodice, bv = self._shell("bodice", bod, 0.009, dress, solid=0.003, drape=45, displace=0.0015,
                                      flare=lambda b: 0.0)
        self._corset_front(self.bodice, bv, m)
        # fuller sleeves: push the arm part of the shell out, most at the forearm
        self._fill_sleeves(self.bodice, bv, warm, 0.012)
        self._folds(self.bodice)
        linen = D.linen_material(self.name + "_collar", color=(0.78, 0.75, 0.68))
        self._band_collar(m, wh, whand, top, linen, offset=0.013)
        self._front_buttons(bv, m["hip"] + 0.08, top - 0.02, 11, 0.012)
        # skirt: bell from the waist to the floor (standing) or a draped shell (seated)
        st = self._stockings_and_shoes(m, wh, whand, wfoot, (0.03, 0.028, 0.03), m["knee"] + 0.1)
        if self.seated:
            sk = u & (z < m["hip"] + 0.09) & (z > m["ankle"] - 0.02) & (whand < 0.05)
            self.skirt, _ = self._shell("skirt", sk, 0.045, dress, solid=0.003, drape=70, displace=0.008,
                                        flare=lambda b: np.clip(1 - np.abs(b[:, 2] - m["knee"]) / 0.12, 0, 1) * 0.02)
        else:
            self.skirt = self._bell("skirt", dress, m["hip"] + 0.09, 0.012, R=0.36, back=0.07, folds=11)
        # shawl: knitted wool over the shoulders, deeper at the back, ends crossing on the chest
        back = np.clip((y - self.rest_co[u, 1].mean()) / 0.08 + 0.5, 0, 1)
        cxm = self.rest_co[u, 0].mean()
        vfront = (y < self.rest_co[u, 1].mean()) * np.exp(-((co[:, 0] - cxm) / 0.07) ** 2)
        sh_lo = top - 0.2 - 0.18 * back - 0.16 * vfront             # to mid-back behind, ends crossed low in front
        elbow_z = self.h.joint("lowerarm01.L____head")[2]
        shawl = u & (wh < 0.5) & (whand < 0.05) & (z > sh_lo) & (z < top - 0.035) & (warm < 0.5) | \
                (u & (warm >= 0.5) & (z > elbow_z - 0.07) & (z < top - 0.03) & (whand < 0.05))      # over the arms past the elbow
        if not self.want_shawl:
            shawl = np.zeros_like(shawl)
        self.shawl = None if not shawl.any() else self._shell("shawl", shawl, 0.026, cloth(self.name + "_shawl", self.SHAWL, rough=0.9, sheen=0.6, knit=True,
                                                                  wet=self.wet), solid=0.006, drape=30, displace=0.006)[0]
        if self.shawl is not None:
            self._soft_edge(self.shawl)
        self.bonnet = None
        if self.want_bonnet:
            self._bonnet(m, wh)
        self._hide_skin(bod | st | (shawl & (wh < 0.2)))

    def _soft_edge(self, o, iters=40):
        """Knitted edge: the stair-stepped boundary of the shell is relaxed along itself into a smooth curve."""
        me = o.data; bm = bmesh.new(); bm.from_mesh(me)
        bnd = [v for v in bm.verts if v.is_boundary]
        nb = {v: [e.other_vert(v) for e in v.link_edges if e.is_boundary] for v in bnd}
        for _ in range(iters):
            new = {v: (v.co * 0.4 + sum((w.co for w in nb[v]), Vector()) / max(1, len(nb[v])) * 0.6) for v in bnd if len(nb[v]) == 2}
            for v, p in new.items():
                v.co = p
        bm.to_mesh(me); bm.free(); me.update()

    def _fringe(self, o, length=0.07, step=0.004):
        """Wool fringe hanging from the shawl's lower edge (after the pose is baked)."""
        bm = bmesh.new(); bm.from_mesh(o.data)          # base (baked) mesh: the solidify would close the open edge
        edges = [e for e in bm.edges if e.is_boundary]
        roots = []
        for e in edges:
            a = o.matrix_world @ e.verts[0].co; b = o.matrix_world @ e.verts[1].co
            if (a.z + b.z) / 2 > o.matrix_world.translation.z + 1e9:
                continue
            n = max(1, int((b - a).length / step))
            for k in range(n):
                roots.append(a.lerp(b, (k + 0.5) / n))
        bm.free()
        if not roots:
            return
        zs = np.array([r.z for r in roots]); lowcut = np.percentile(zs, 55)
        roots = [r for r in roots if r.z < lowcut]                      # only the hanging lower edge
        rng = np.random.default_rng(3); segs = 6
        pts = np.zeros((len(roots), segs, 3), np.float32)
        for i, r in enumerate(roots):
            ln = length * rng.uniform(0.7, 1.1); sw = Vector((rng.normal(0, 0.004), rng.normal(0, 0.004), 0))
            for k in range(segs):
                t = k / (segs - 1); pts[i, k] = r + Vector((0, 0, -ln * t)) + sw * t
        cv = bpy.data.hair_curves.new(self.name + "_fringe"); cv.add_curves([segs] * len(roots))
        cv.position_data.foreach_set("vector", pts.reshape(-1))
        try:
            cv.attributes["radius"].data.foreach_set("value", np.full(len(roots) * segs, 0.0014, np.float32))
        except Exception:
            pass
        ob = bpy.data.objects.new(cv.name, cv); bpy.context.collection.objects.link(ob)
        cv.materials.append(o.data.materials[0])
        self.hair_objs.append(ob)

    def _corset_front(self, o, used_idx, m):
        """Bodice front over a corset: across the chest the cloth spans the bust as one smooth surface (each front
        vertex is lifted to a smooth convex sheet in x), so no cleavage or separate shapes read through."""
        me = o.data
        co = np.array([v.co[:] for v in me.vertices])
        if len(co) != len(used_idx):
            return
        cx = float(self.rest_co[self.used, 0].mean())
        band = (co[:, 2] > m["hip"] + 0.15) & (co[:, 2] < m["neck"] - 0.03) & (co[:, 1] < -0.02) & (np.abs(co[:, 0] - cx) < 0.14)
        if band.sum() < 10:
            return
        idx = np.nonzero(band)[0]
        zs = np.round(co[idx, 2] / 0.01).astype(int)
        for zz in np.unique(zs):
            row = idx[zs == zz]
            if len(row) < 3:
                continue
            y_front = co[row, 1].min()                      # most forward point of this horizontal slice
            dx = np.abs(co[row, 0] - cx) / 0.14
            sheet = y_front + 0.035 * dx ** 2               # one smooth curve across the front
            co[row, 1] = np.minimum(co[row, 1], sheet)
        me.vertices.foreach_set("co", co.astype(np.float32).ravel()); me.update()

    def _fill_sleeves(self, o, used_idx, warm, amount):
        me = o.data
        w = warm[used_idx]
        if len(w) != len(me.vertices):
            return
        nrm = self.rest_n[used_idx]
        co = np.array([v.co[:] for v in me.vertices]) + nrm * (amount * np.clip(w, 0, 1))[:, None]
        me.vertices.foreach_set("co", co.astype(np.float32).ravel()); me.update()

    def _bonnet(self, m, wh):
        """Soft brimmed bonnet: a smooth cap over the back, top and sides of the head (clear of the hair), open round
        the face, its edge rolled out into a soft brim; ribbon ties from the brim down to a bow under the chin.
        Built around the head and skinned to the head bone."""
        h = self.h; co = self.rest_co; ec = self._head_frame(); hs = self.head_scale
        head = self.used & (wh > 0.6)
        Hc = co[head]; c = Hc.mean(0); c[2] = ec[2] + 0.02 * hs
        dirs = Hc - c; dist = np.linalg.norm(dirs, axis=1); dn = dirs / dist[:, None]
        mat = cloth(self.name + "_bonnet", self.BONNET, rough=0.6, sheen=0.5, weave=900, wet=self.wet)
        fwd = np.array([0, -1.0, 0.18]); fwd /= np.linalg.norm(fwd)
        nu, nv = 48, 20
        open_deg = 70.0                     # face opening half-angle round the forward axis
        V = []; F = []
        up = np.array([0, 0, 1.0]); side = np.cross(fwd, up); side /= np.linalg.norm(side); up2 = np.cross(side, fwd)
        for j in range(nv + 1):
            t = j / nv
            th = math.radians(open_deg + (178 - open_deg) * t)         # angle from the forward axis
            for i in range(nu):
                ph = 2 * math.pi * i / nu
                d = fwd * math.cos(th) + (side * math.cos(ph) + up2 * math.sin(ph)) * math.sin(th)
                near = (dn @ d) > math.cos(math.radians(14))
                r = float(dist[near].max()) if near.any() else float(dist.max())
                r += 0.03 * hs
                if math.sin(ph) < -0.2:                              # lower half: stop at the nape / under the ears
                    r *= 1.0
                # structured brim: a stiff band standing out and forward round the face (straight, not rolled)
                brim = 1.0 if t < 0.05 else max(0.0, 1 - (t - 0.05) / 0.05)
                p = c + d * (r + 0.022 * hs * brim) + fwd * 0.014 * hs * brim
                V.append(tuple(p))
        rows = nu
        for j in range(nv):
            for i in range(nu):
                a_ = j * rows + i; b_ = j * rows + (i + 1) % nu
                F.append([a_, b_, b_ + rows, a_ + rows])
        # cut away the part under the chin/jaw: drop faces whose centre is low and in front
        keep = []
        for f in F:
            pc = sum(np.array(V[k]) for k in f) / 4
            if pc[2] < ec[2] - 0.045 * hs:                       # sides end at the ears (ties take over)
                continue
            if pc[1] > c[1] + 0.025 * hs and pc[2] < ec[2] + 0.005 * hs:   # crown sits above the bun at the back
                continue
            keep.append(f)
        o = D.mesh_obj(f"{self.name}_bonnet", V, keep, mat)
        self._soft_edge(o, iters=30)
        so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.003; so.offset = 1; so.thickness_clamp = 1.0
        sb = o.modifiers.new("Sub", "SUBSURF"); sb.levels = 1; sb.render_levels = 2
        vg = o.vertex_groups.new(name="head"); vg.add(list(range(len(V))), 1.0, 'REPLACE')
        mod = o.modifiers.new("Armature", "ARMATURE"); mod.object = h.arm; o.modifiers.move(len(o.modifiers) - 1, 0)
        o.parent = h.arm; h.parts.append(o)
        self.bonnet = o
        # ribbon ties: from the brim below each ear down along the jaw to a bow under the chin
        rib = cloth(self.name + "_ribbon", (0.05, 0.05, 0.065), rough=0.35, sheen=0.8, weave=2000)
        chin = ec + np.array([0, -0.05, -0.115]) * hs
        U = np.nonzero(self.used)[0]
        for sg in (1, -1):
            ear = ec + np.array([sg * 0.07, 0.012, -0.01]) * hs      # starts under the bonnet's side (no visible end)
            pts = []
            for t in np.linspace(0, 1, 12):
                p = ear * (1 - t) + chin * t
                i = int(np.argmin(np.linalg.norm(co[U] - p, axis=1))); vi = U[i]
                pts.append(Vector(co[vi] + self.rest_n[vi] * 0.007))
            pts[-1] = Vector(chin + np.array([sg * 0.01, -0.012, 0]) * hs)
            cu = bpy.data.curves.new(f"{self.name}_tie", 'CURVE'); cu.dimensions = '3D'
            cu.bevel_depth = 0.0018 * hs; cu.extrude = 0.006 * hs; cu.bevel_resolution = 1; cu.use_fill_caps = False
            sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
            for k, p in enumerate(pts):
                sp.points[k].co = (*p, 1)
            ob = bpy.data.objects.new(cu.name, cu); bpy.context.collection.objects.link(ob); cu.materials.append(rib)
            ob.parent = h.arm; ob.parent_type = 'BONE'; ob.parent_bone = "head"
            bpy.context.view_layer.update(); ob.matrix_world = Matrix.Identity(4)
            self.button_objs.append(ob)
        # ribbon bow under the chin: two flat loops and a knot (no ring)
        kc = Vector(chin + np.array([0, -0.014, 0]) * hs)
        for sgn in (1, -1):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.009 * hs, minor_radius=0.0025 * hs, major_segments=24, minor_segments=8,
                                             location=tuple(kc + Vector((sgn * 0.011 * hs, 0, 0))), rotation=(math.pi / 2, 0, sgn * 0.35))
            lp = bpy.context.active_object; lp.name = f"{self.name}_bowloop"; lp.scale = (1.0, 1.0, 0.45)
            lp.data.materials.append(rib); bpy.ops.object.shade_smooth()
            bpy.context.view_layer.update(); mw = lp.matrix_world.copy()
            lp.parent = h.arm; lp.parent_type = 'BONE'; lp.parent_bone = "head"; bpy.context.view_layer.update(); lp.matrix_world = mw
            self.button_objs.append(lp)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.004 * hs, location=tuple(kc))
        kn = bpy.context.active_object; kn.name = f"{self.name}_bowknot"; kn.scale = (1.0, 0.7, 1.2); kn.data.materials.append(rib)
        bpy.ops.object.shade_smooth()
        bpy.context.view_layer.update(); mw = kn.matrix_world.copy()
        kn.parent = h.arm; kn.parent_type = 'BONE'; kn.parent_bone = "head"; bpy.context.view_layer.update(); kn.matrix_world = mw
        self.button_objs.append(kn)

    def finish(self, *a, **k):
        r = super().finish(*a, **k)
        if self.shawl is not None:
            self._fringe(self.shawl)
        return r


class Sophia(_Woman):
    HAIR_N = 40000; HAIR_LEN = (0.03, 0.06); CURL = 0.6
    HAIR = (0.55, 0.4)
    SKIN = dict(base=(0.55, 0.36, 0.27), weather=0.2)
    MUSCLE = 0.5; WEIGHT = 0.62; HEIGHT = 0.5
    EXTRA = {"targets/eyes/l-eye-scale-decr": 0.35, "targets/eyes/r-eye-scale-decr": 0.35,
             "targets/cheek/l-cheek-volume-incr": 0.5, "targets/cheek/r-cheek-volume-incr": 0.5,
             "targets/eyes/l-eye-height2-decr": 0.3, "targets/eyes/r-eye-height2-decr": 0.3}
    BOOT_TOP = 0.11
    FROCK = (0.11, 0.06, 0.06)        # rust-red wool
    PINAFORE = (0.82, 0.8, 0.74)

    def __init__(self, name="Sophia", years=2, wet=0.0, seated=False, bonnet=False, shawl=False):
        """shawl=True wraps a small knitted shawl round her shoulders (out on deck)."""
        super().__init__(name, years, wet=wet, seated=seated, bonnet=bonnet, shawl=shawl)

    def _comb(self, R):
        return lambda p: R @ Vector((math.copysign(0.4, p.x - self._mid_x), 0.6, -0.6))

    def _dress(self):
        m, wh, whand, wfoot, warm = self._m()
        u = self.used; co = self.rest_co; z = co[:, 2]
        elbow = np.array(self.h.joint("lowerarm01.L____head"))
        frock = cloth(self.name + "_frock", self.FROCK, rough=0.8, sheen=0.4, weave=900, wet=self.wet)
        top = m["neck"] + 0.02
        chest = m["neck"] - 0.11 * self.head_scale
        dist_el = np.minimum(np.linalg.norm(co - elbow, axis=1), np.linalg.norm(co - elbow * np.array([-1, 1, 1]), axis=1))
        upperarm_only = (warm < 0.5) | (dist_el > 0.04)
        waist = m["hip"] + 0.05 * self.head_scale
        yoke = u & (wh < 0.6) & (whand < 0.05) & (z > waist - 0.02) & (z < top) & ((warm < 0.3) | (z > elbow[2] + 0.02))
        self.bodice, bv = self._shell("yoke", yoke, 0.008, frock, solid=0.003, drape=30)
        Sarah._fill_sleeves(self, self.bodice, bv, warm, 0.02)          # puffed short sleeves
        st = self._stockings_and_shoes(m, wh, whand, wfoot, (0.75, 0.72, 0.64), m["knee"] + 0.06)
        hem = m["knee"] - 0.04
        if self.seated:
            sk = u & (z < waist + 0.01) & (z > hem) & (whand < 0.05)
            self.skirt, _ = self._shell("frock_skirt", sk, 0.02, frock, solid=0.003, drape=40, displace=0.005)
        else:
            self.skirt = self._bell("frock_skirt", frock, waist, hem, R=0.19, back=0.02, folds=8, offset=0.02)
        pin = cloth(self.name + "_pinafore", self.PINAFORE, rough=0.85, sheen=0.3, weave=1200, wet=self.wet)
        if self.seated:
            front = u & (z < waist + 0.01) & (z > hem + 0.03) & (co[:, 1] < co[u, 1].mean()) & (whand < 0.05)
            self.pinafore, _ = self._shell("pinafore", front, 0.028, pin, solid=0.002, drape=40)
        else:
            self.pinafore = self._bell("pinafore", pin, waist + 0.005, hem + 0.03, R=0.2, back=0.0, folds=6, offset=0.032,
                                       arc=(-115, 115))
        if self.want_shawl:
            shl = u & (wh < 0.5) & (whand < 0.05) & (z > chest - 0.02) & (z < top - 0.01) & ((warm < 0.5) | (z > elbow[2]))
            self._shell("shawl", shl, 0.03, cloth(self.name + "_shawl", (0.6, 0.55, 0.45), rough=0.9, sheen=0.6, knit=True),
                        solid=0.006, drape=25, displace=0.004)
        # bib + shoulder straps
        straps = u & (wh < 0.4) & (z > waist - 0.01) & (z < top - 0.01) & (warm < 0.2) & \
                 ((np.abs(np.abs(co[:, 0] - co[u, 0].mean()) - 0.045 * self.head_scale) < 0.012) | (co[:, 1] < co[u, 1].mean() - 0.03))
        bib, _ = self._shell("pinafore_bib", straps, 0.013, pin, solid=0.002)
        Sarah._soft_edge(self, bib, iters=30)
        self._hide_skin(yoke | st)


class Arthur(_Woman):
    """Arthur Briggs (7), at school in Massachusetts in 1872: a boy's wool jacket buttoned high over a white shirt
    collar, knickerbockers gathered below the knee, dark stockings, ankle boots; short side-parted hair.
    (Shares the civilian base class with Sarah and Sophia: no beard, own clothes.)"""
    GENDER = 1.0; MUSCLE = 0.5; WEIGHT = 0.45; HEIGHT = 0.5
    SKIN = dict(base=(0.53, 0.34, 0.25), weather=0.25)
    HAIR = (0.7, 0.35); HAIR_N = 50000; HAIR_LEN = (0.02, 0.04); CURL = 0.15
    BOOT_TOP = 0.16
    JACKET = (0.07, 0.065, 0.06)      # brown-grey tweedy wool
    BREECHES = (0.05, 0.05, 0.055)

    EXTRA = {"targets/eyes/l-eye-scale-decr": 0.25, "targets/eyes/r-eye-scale-decr": 0.25}

    def __init__(self, name="Arthur", years=7, wet=0.0, seated=False, cap=False):
        super().__init__(name, years, wet=wet, seated=seated, bonnet=False, shawl=False)

    def _comb(self, R):
        part = 0.025 * self.head_scale
        return lambda p: R @ Vector((-0.9 if (p.x - self._mid_x) < part else 0.6, 0.5, -0.2))   # side parting

    def _dress(self):
        m, wh, whand, wfoot, warm = self._m()
        u = self.used; co = self.rest_co; z = co[:, 2]
        wrist = np.array(self.h.joint("wrist.L____head"))
        dist_wrist = np.minimum(np.linalg.norm(co - wrist, axis=1), np.linalg.norm(co - wrist * np.array([-1, 1, 1]), axis=1))
        hs = self.head_scale
        shirt = u & (wh < 0.5) & (whand < 0.1) & (z > m["hip"]) & (z < m["neck"] + 0.04 * hs)
        self.shirt, _ = self._shell("shirt", shirt, 0.004, D.linen_material(self.name + "_shirt", color=(0.8, 0.78, 0.72)), solid=0.0015)
        jk = u & (wh < 0.2) & (whand < 0.04) & (z > m["hip"] - 0.01) & (z < m["neck"] + 0.005) & (dist_wrist > 0.03)
        self.jacket, jv = self._shell("jacket", jk, 0.009, cloth(self.name + "_jacket", self.JACKET, rough=0.85, weave=500, wet=self.wet),
                                      solid=0.004, drape=10, displace=0.002)
        self._hem(self.jacket, m["hip"], drop=0.08 * hs, flare=0.015)
        self._collar(self.jacket)
        self._folds(self.jacket)
        self._front_buttons(jv, m["hip"] + 0.05 * hs, m["neck"] - 0.04 * hs, 5, 0.011, r=0.006, mat=D.brass_material(self.name + "_brass"))
        kb = u & (z < m["hip"] + 0.08 * hs) & (z > m["knee"] - 0.05 * hs) & (wfoot < 0.2) & (whand < 0.05)
        self.trousers_kb, _ = self._shell("knickerbockers", kb, 0.012, cloth(self.name + "_breeches", self.BREECHES, rough=0.85, weave=600),
                                          solid=0.003, drape=14, displace=0.003,
                                          flare=lambda b: np.clip(1 - np.abs(b[:, 2] - (m["knee"] + 0.02)) / 0.08, 0, 1) * 0.012)
        st = self._stockings_and_shoes(m, wh, whand, wfoot, (0.03, 0.03, 0.035), m["knee"] + 0.02)
        self._hide_skin(shirt | jk | kb | st)


__all__ = ["Sarah", "Sophia", "Arthur"]
