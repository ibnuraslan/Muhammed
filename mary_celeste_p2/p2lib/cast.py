"""Part 2 cast, built on the shared character library (claude/mary-celeste-3d, mary_celeste_3d/lib).

Nothing in the shared library is changed: every person here is a subclass of deveau.Deveau that swaps the
body parameters, the clothes (shells grown off the same MakeHuman body, so they bend with it and never clip)
and the hair. Unlike Deveau.finish(), finish_live() keeps the armature live so poses can be keyed over time:
hair, eyes and buttons ride on the head / chest bones.

    b = Briggs(); P.stand(b.h); b.finish_live(look_at=(x, y, z), place=M)
"""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import human as H
import deveau as D
from deveau import _w, HEAD, HAND, FOOT, wool_material, linen_material, leather_material, hair_material, sailor_skin


def cotton_material(name, color, rough=0.75, sheen=0.5, pattern=None, scale=180.0):
    m, N, L, p = D._mat(name)
    tc = N.new("ShaderNodeTexCoord")
    base = N.new("ShaderNodeRGB"); base.outputs[0].default_value = (*color, 1); col = base.outputs[0]
    if pattern == "check":
        ck = N.new("ShaderNodeTexChecker"); ck.inputs['Scale'].default_value = scale
        ck.inputs['Color1'].default_value = (*color, 1)
        ck.inputs['Color2'].default_value = (*[c * 0.72 for c in color], 1)
        L.new(tc.outputs['Object'], ck.inputs['Vector']); col = ck.outputs['Color']
    elif pattern == "stripe":
        wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
        wv.inputs['Scale'].default_value = scale * 0.25; L.new(tc.outputs['Object'], wv.inputs['Vector'])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.45; mr.inputs['From Max'].default_value = 0.55
        L.new(wv.outputs['Fac'], mr.inputs['Value'])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (*color, 1)
        mx.inputs[7].default_value = (*[c * 0.6 for c in color], 1); L.new(mr.outputs[0], mx.inputs['Factor']); col = mx.outputs[2]
    fib = N.new("ShaderNodeTexNoise"); fib.inputs['Scale'].default_value = 500; fib.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], fib.inputs['Vector'])
    mx2 = N.new("ShaderNodeMix"); mx2.data_type = 'RGBA'; mx2.blend_type = 'MULTIPLY'; mx2.inputs['Factor'].default_value = 0.18
    L.new(col, mx2.inputs[6]); L.new(fib.outputs['Color'], mx2.inputs[7])
    L.new(mx2.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough; p.inputs['Sheen Weight'].default_value = sheen
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.15; L.new(fib.outputs['Fac'], bm.inputs['Height'])
    L.new(bm.outputs['Normal'], p.inputs['Normal'])
    return m


def silk_material(name, color, rough=0.35):
    m, N, L, p = D._mat(name)
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Sheen Weight'].default_value = 0.8; p.inputs['Sheen Tint'].default_value = (1, 1, 1, 1)
    p.inputs['Specular IOR Level'].default_value = 0.6
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 14
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.08; L.new(nz.outputs['Fac'], bm.inputs['Height'])
    L.new(bm.outputs['Normal'], p.inputs['Normal'])
    return m


def straw_material(name, color=(0.55, 0.42, 0.24)):
    m, N, L, p = D._mat(name)
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'RINGS'; wv.inputs['Scale'].default_value = 90
    wv.inputs['Distortion'].default_value = 1.5; L.new(tc.outputs['Object'], wv.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (*color, 1)
    mx.inputs[7].default_value = (*[c * 0.6 for c in color], 1); L.new(wv.outputs['Fac'], mx.inputs['Factor'])
    L.new(mx.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.7
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.4; L.new(wv.outputs['Fac'], bm.inputs['Height'])
    L.new(bm.outputs['Normal'], p.inputs['Normal'])
    return m


def fair_skin(name, base=(0.62, 0.42, 0.33), weather=0.15):
    return sailor_skin(name, base=base, weather=weather)


# ----------------------------------------------------------------------------- base person
class Person(D.Deveau):
    """A Deveau-built person with its own body, dress and hair. Subclasses set the class attributes."""
    GENDER = 1.0; YEARS = 35; MUSCLE = 0.55; WEIGHT = 0.5; HEIGHT = 0.5
    EXTRA = {}
    SKIN = dict(base=(0.47, 0.29, 0.2), weather=0.45)
    HAIR = dict(melanin=0.82, redness=0.38)

    def __init__(self, name=None, wet=0.0, expr=None, **kw):
        """expr: MakeHuman expression units for a small held expression, e.g. {"mouth-corner-puller": 0.3}."""
        name = name or self.__class__.__name__
        for k, v in kw.items():
            setattr(self, k.upper(), v)
        extra = dict(self.EXTRA)
        for k, v in (expr or {}).items():
            extra["targets/expression/units/caucasian/" + k] = v
        self.h = H.Human(name, gender=self.GENDER, years=self.YEARS, muscle=self.MUSCLE, weight=self.WEIGHT,
                         height=self.HEIGHT, extra=extra, eyebrows=None, eyelashes=None, skin=None)
        h = self.h
        h.body.data.materials[0] = sailor_skin(name + "_skin", **self.SKIN)
        if hasattr(self, "_skin_regions"):
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
        self.button_objs = []; self.extra_objs = []
        self._dress()
        # shared lib (9499317): fitted Sketchfab boots skinned to the legs, done at rest so they follow any pose
        self.asset_boots = False
        if self.BOOTS and getattr(self, "boots", None) is not None and hasattr(D.Deveau, "_skin_like_body"):
            self.asset_boots = self._asset_boots(skin=True)

    # ---- helpers for subclasses
    def _marks(self):
        h = self.h; co = self.rest_co
        hip_z = h.joint("upperleg01.L____head")[2]; neck_z = h.joint("neck01____head")[2]
        ankle_z = h.joint("foot.L____head")[2]; knee_z = h.joint("lowerleg01.L____head")[2]
        wrist = np.array(h.joint("wrist.L____head"))
        dist_wrist = np.minimum(np.linalg.norm(co - wrist, axis=1), np.linalg.norm(co - wrist * np.array([-1, 1, 1]), axis=1))
        self.marks = dict(hip=hip_z, neck=neck_z, ankle=ankle_z, knee=knee_z)
        return co, hip_z, neck_z, ankle_z, knee_z, dist_wrist

    def _attach(self, o, bone):
        """Parent a rigid accessory to a bone (keeps its world placement)."""
        mw = o.matrix_world.copy()
        o.parent = self.h.arm; o.parent_type = 'BONE'; o.parent_bone = bone
        bpy.context.view_layer.update(); o.matrix_world = mw
        self.extra_objs.append(o)

    # ---- hair: scalp / beard masks in the head frame (eye centre origin), from Deveau._grow_all
    def _head_masks(self):
        co = self.rest_co; h = self.h
        wh = _w(h, HEAD)
        ears = D._mask_at_uv(D.os.path.join(D.MASKS, "mpfb_ears.jpg"), self.uv)
        lips = D._mask_at_uv(D.os.path.join(D.MASKS, "mpfb_lips.jpg"), self.uv)
        eyeL = np.array(h.joint("eye.L____head")); eyeR = np.array(h.joint("eye.R____head"))
        ec = (eyeL + eyeR) / 2
        mouth = co[self.used & (lips > 0.5)].mean(0)
        rel = co - ec
        head = self.used & (wh > 0.55) & (ears < 0.2)
        return rel, head, lips, np.array(mouth)[2] - ec[2], ec

    def _grow_all(self, density):
        self._grow_hair(density)

    def _grow_hair(self, density):   # default: the Deveau groom (short hair, full beard)
        D.Deveau._grow_all(self, density)

    # ---- live finish
    def _posed_surface(self):
        body = self.h.body
        sub = [m for m in body.modifiers if m.type == 'SUBSURF']
        lv = [(m, m.levels) for m in sub]
        for m in sub:
            m.levels = 0
        dg = bpy.context.evaluated_depsgraph_get()
        oe = body.evaluated_get(dg); me = oe.to_mesh()
        M = body.matrix_world
        P = np.array([(M @ v.co)[:] for v in me.vertices])
        oe.to_mesh_clear()
        for m, l in lv:
            m.levels = l
        dg = bpy.context.evaluated_depsgraph_get()
        bvh = BVHTree.FromObject(body, dg)
        if M != Matrix.Identity(4):
            # BVH is in object space; our P is world. Rig sits at identity until place, so this is a no-op.
            pass
        return P, bvh

    def finish_live(self, look_at=None, hair=True, density=1.0, place=None, ground=True):
        """Grow hair on the posed body and keep the rig live; then move everything to `place`."""
        h = self.h
        for o in h.parts:
            for m in getattr(o, "modifiers", []):
                if m.type == 'SOLIDIFY':
                    m.thickness_clamp = 1.0          # even-offset spikes at sharp hem corners
        self._rest_fittings()
        bpy.context.view_layer.update()
        head_M = (h.arm.matrix_world @ h.arm.pose.bones["head"].matrix).copy()
        self.head_R = head_M.to_3x3() @ h.arm.data.bones["head"].matrix_local.to_3x3().inverted()
        self.hair_objs = []
        if hair:
            self._grow_all(density)
            for o in self.hair_objs:
                if o is not None:
                    self._attach_hair(o)
        self.place = place or Matrix.Identity(4)
        h.arm.matrix_world = self.place @ h.arm.matrix_world
        for o in self.objects:
            if o.parent is None and o is not h.arm:
                o.matrix_world = self.place @ o.matrix_world
        bpy.context.view_layer.update()
        if look_at is not None:
            self.look(look_at)
        h.arm.hide_render = True
        if ground:
            self.ground()
        self.tag()

    def ground(self, clearance=0.006, max_lift=0.25):
        """Stand on whatever is really underneath: ray-cast down under the soles (boots, shoes or the skirt hem) and lift
        the whole rig so the lowest point clears the surface below. Returns the lift applied."""
        import numpy as np
        bpy.context.view_layer.update()
        mine = set(o.name for o in self.objects) | set(o.name for o in (getattr(self, "sea_boots", []) or []))
        feet = [o for o in bpy.data.objects if o.name in mine and o.type == 'MESH' and
                any(k in o.name for k in (("boot", "shoes") if self.SEATED else ("boot", "shoes", "skirt")))]
        if not feet:
            return 0.0
        dg = bpy.context.evaluated_depsgraph_get()
        lows = []
        for o in feet:
            oe = o.evaluated_get(dg); me = oe.to_mesh()
            P = np.array([(oe.matrix_world @ v.co)[:] for v in me.vertices]); oe.to_mesh_clear()
            if len(P):
                low = P[P[:, 2] < P[:, 2].min() + 0.03]
                lows.append(low[np.linspace(0, len(low) - 1, min(len(low), 40)).astype(int)])
        hidden = []
        for o in bpy.data.objects:
            if o.name in mine or o.name.startswith(("air", "dust", "SeaHaze", "Ocean", "far_sea")):
                if not o.hide_viewport:
                    o.hide_viewport = True; hidden.append(o)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        sc = bpy.context.scene
        need = -1.0
        for low in lows:
            for p in low:
                hit = sc.ray_cast(dg, Vector((p[0], p[1], p[2] + 0.06)), Vector((0, 0, -1)), distance=0.5)
                if hit[0]:
                    need = max(need, hit[1].z + clearance - p[2])
        for o in hidden:
            o.hide_viewport = False
        bpy.context.view_layer.update()
        lift = min(max(need, 0.0), max_lift) if need > -1.0 else 0.0
        if lift > 0:
            self.h.arm.location.z += lift
            for o in self.objects:
                if o.parent is None and o is not self.h.arm:
                    o.location.z += lift
            bpy.context.view_layer.update()
        self.lifted = lift
        return lift

    def tag(self):
        """Tag meshes for clipcheck (o["person"]) with world hand points (wrists + knuckles)."""
        bpy.context.view_layer.update()
        hp = []
        for sd in ("L", "R"):
            for b in (f"wrist.{sd}", f"finger3-1.{sd}", f"finger3-3.{sd}"):
                if b in self.h.arm.pose.bones:
                    hp.append(self.h.bone_head(b))
        flat = [c for v in hp for c in v]
        for o in self.objects + list(getattr(self, "sea_boots", []) or []) + list(getattr(self, "corneas", []) or []):
            if getattr(o, "type", None) == 'MESH':
                o["person"] = self.name; o["hands"] = flat

    BOOTS = True
    SEATED = False

    def _hem(self, o, hip_z, drop=0.15, flare=0.028):
        """Seated men: the jacket skirt is kept short so it rests above the chair seat instead of through it."""
        return D.Deveau._hem(self, o, hip_z, drop=(0.03 if self.SEATED else drop), flare=flare)

    def _rest_fittings(self):
        """Shared-lib fittings that expect an unposed body: corneas (then ride on the eyes) and the fitted Sketchfab boots
        (then ride on the foot bones). Done at the rest pose, then the pose is put back."""
        h = self.h; pb = h.arm.pose.bones
        saved = {b.name: (b.rotation_mode, tuple(b.rotation_quaternion), tuple(b.rotation_euler), tuple(b.location)) for b in pb}
        for b in pb:
            b.rotation_quaternion = (1, 0, 0, 0); b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0)
        bpy.context.view_layer.update()
        if hasattr(self, "_corneas"):
            self._corneas()
            for c, e in zip(self.corneas, h.eyes):
                mw = c.matrix_world.copy(); c.parent = e; c.matrix_world = mw
        if False:
            try:
                ok = self._asset_boots()
            except Exception as ex:
                print("boots failed", ex); ok = False
            if ok:
                for o in self.sea_boots:
                    bone = "foot.L" if o.name.endswith("L") else "foot.R"
                    mw = o.matrix_world.copy(); o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = bone
                    bpy.context.view_layer.update(); o.matrix_world = mw
        for b in pb:
            m, q, e, l = saved[b.name]
            b.rotation_quaternion = q; b.rotation_euler = e; b.location = l
        bpy.context.view_layer.update()

    def _attach_hair(self, o):
        mw = o.matrix_world.copy()
        o.parent = self.h.arm; o.parent_type = 'BONE'; o.parent_bone = "head"
        bpy.context.view_layer.update(); o.matrix_world = mw

    def look(self, target):
        """Aim both eyes at a world point (eyes are children of the head bone)."""
        bpy.context.view_layer.update()
        for e in self.h.eyes:
            loc = e.matrix_world.to_translation(); sc = e.matrix_world.to_scale()
            d = (Vector(target) - loc).normalized()
            q = (-d).to_track_quat('Y', 'Z')
            e.matrix_world = Matrix.LocRotScale(loc, q, sc)

    @property
    def objects(self):
        return ([p for p in self.h.parts] + self.button_objs + self.extra_objs +
                [o for o in getattr(self, "hair_objs", []) if o])


# ----------------------------------------------------------------------------- men
class Sailor(Person):
    """Stevedore / seaman / pilot: Deveau's clothes with a different face, colours and a cap."""
    YEARS = 28; MUSCLE = 0.7; WEIGHT = 0.5; HEIGHT = 0.5
    JACKET = (0.05, 0.04, 0.03); SCARF = (0.3, 0.06, 0.03); CAP = True; BEARD = True
    EXTRA = {"targets/nose/nose-flaring-incr": 0.3, "targets/chin/chin-width-incr": 0.3}

    def _dress(self):
        D.Deveau._dress(self)
        self.jacket.data.materials[0] = wool_material(self.name + "_jk", self.JACKET, weave=380, dirt=0.3, sheen=0.3)
        self.scarf.data.materials[0] = wool_material(self.name + "_sc", self.SCARF, rough=0.8, sheen=0.3, weave=900, dirt=0.3)

    def _grow_hair(self, density):
        if self.BEARD:
            D.Deveau._grow_all(self, density)
        else:
            D.Deveau._grow_all(self, density)
            for o in list(self.hair_objs):
                if o is not None and ("beard" in o.name or "moustache" in o.name):
                    bpy.data.objects.remove(o); self.hair_objs.remove(o)
        if self.CAP:
            self._cap()

    def _cap(self):
        """A wool watch cap / peaked cap pulled on over the hair (a lathe shell, parented to the head)."""
        rel, head, lips, mz, ec = self._head_masks()
        R = self.head_R
        top = self.rest_co[head][:, 2].max()
        c = Vector(ec) + R @ Vector((0, 0.012, 0.0))
        verts, faces = [], []
        n = 36
        rings = [(0.103, 0.028), (0.104, 0.06), (0.098, 0.09), (0.082, 0.118), (0.05, 0.135), (0.0, 0.14)]
        for (r, zz) in rings:
            for k in range(n):
                a = 2 * math.pi * k / n
                verts.append(c + R @ Vector((r * math.cos(a), r * 1.08 * math.sin(a) + 0.004, zz - 0.012)))
        for j in range(len(rings) - 1):
            for k in range(n):
                a, b = j * n + k, j * n + (k + 1) % n
                faces.append([a, b, b + n, a + n])
        me = bpy.data.meshes.new(self.name + "_cap"); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
        o = bpy.data.objects.new(me.name, me); bpy.context.collection.objects.link(o)
        o.data.materials.append(wool_material(self.name + "_capm", (0.03, 0.03, 0.04), weave=700, sheen=0.4))
        so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.006; so.offset = 1
        o.modifiers.new("Sub", "SUBSURF").levels = 1
        # push the cap out of the skull: shrinkwrap onto the scalp + hair clearance
        sw = o.modifiers.new("Wrap", "SHRINKWRAP"); sw.target = self.h.body; sw.wrap_mode = 'OUTSIDE_SURFACE'; sw.offset = 0.016
        sw.wrap_method = 'NEAREST_SURFACEPOINT'
        o.modifiers.move(len(o.modifiers) - 1, 0)
        self.hair_objs.append(o)


class OldBriggs(Sailor):
    """Capt. Benjamin Spooner Briggs, 37: tall, straight, full dark beard; dark double-breasted coat, white shirt,
    black silk necktie; bareheaded below decks."""
    YEARS = 37; MUSCLE = 0.55; WEIGHT = 0.5; HEIGHT = 0.62
    EXTRA = {"targets/nose/nose-scale-vert-incr": 0.3, "targets/head/head-oval": 0.4,
             "targets/eyebrows/eyebrows-trans-down": 0.2, "targets/cheek/l-cheek-bones-incr": 0.2,
             "targets/cheek/r-cheek-bones-incr": 0.2, "targets/forehead/forehead-scale-vert-incr": 0.3}
    SKIN = dict(base=(0.5, 0.32, 0.23), weather=0.35)
    JACKET = (0.012, 0.013, 0.022); CAP = False; BEARD = True

    def _dress(self):
        Sailor._dress(self)
        self.scarf.data.materials[0] = silk_material(self.name + "_tie", (0.008, 0.008, 0.01))
        self.shirt.data.materials[0] = cotton_material(self.name + "_shirt", (0.75, 0.73, 0.68), sheen=0.3)

    def _grow_hair(self, density):
        """Dark hair, full on top, side-parted and combed back over the ears; full beard and moustache."""
        Sailor._grow_hair(self, density)
        for o in list(self.hair_objs):
            if o is not None and o.name.endswith("_hair"):
                bpy.data.objects.remove(o); self.hair_objs.remove(o)
        rel, head, lips, mz, ec = self._head_masks()
        x, y, z = rel[:, 0], rel[:, 1], rel[:, 2]
        line = np.interp(y, [-0.12, -0.07, -0.02, 0.05, 0.12], [0.045, 0.04, 0.0, -0.055, -0.085])
        scalp = head & (z > line)
        P, bvh = self._posed_surface(); R = self.head_R
        dark = hair_material(self.name + "_dark", 0.9, 0.3, rough=0.35)
        part = float(P[self.used, 0].mean()) + 0.035
        def comb(p):
            sx = 1.0 if p.x > part else -0.6
            return R @ Vector((0.5 * sx, 0.8, -0.3))
        self.hair_objs.append(self._strands("hair", scalp, P, bvh, int(80000 * density), (0.03, 0.05), 0.0011,
                                            comb=comb, lift=0.0026, mat=dark, curl=0.07, segs=8))
        for o in self.hair_objs:
            if o is not None and o.type == 'CURVES':
                o.data.materials[0] = dark


# ----------------------------------------------------------------------------- women and children
class Woman(Person):
    """1870s day dress: fitted bodice to a high neck, long sleeves, full skirt to the floor with a bustle behind.
    Hair centre-parted and drawn back into a low bun."""
    GENDER = 0.0; YEARS = 30; MUSCLE = 0.4; WEIGHT = 0.45; HEIGHT = 0.45
    EXTRA = {"targets/nose/nose-scale-horiz-decr": 0.2, "targets/chin/chin-prominent-decr": 0.2}
    SKIN = dict(base=(0.6, 0.4, 0.3), weather=0.12)
    HAIR = dict(melanin=0.75, redness=0.42)
    DRESS = (0.16, 0.05, 0.045); TRIM = (0.05, 0.02, 0.02); PATTERN = None
    SEATED = False; BONNET = False; SKIRT_R = 0.34

    def _dress(self):
        h = self.h
        co, hip_z, neck_z, ankle_z, knee_z, dist_wrist = self._marks()
        wh = _w(h, HEAD); whand = _w(h, HAND); z = co[:, 2]; u = self.used
        self.dress_mat = cotton_material(self.name + "_dress", self.DRESS, sheen=0.55, pattern=self.PATTERN)
        bod = u & (wh < 0.4) & (whand < 0.05) & (z > hip_z - 0.02) & (z < neck_z + 0.05) & (dist_wrist > 0.03)
        self.bodice, bv = self._shell("bodice", bod, 0.008, self.dress_mat, solid=0.002, drape=30,
                                      flare=lambda b: np.clip((b[:, 2] - (neck_z + 0.0)) / 0.05, 0, 1) * 0.004)
        # white collar band at the throat
        col = u & (z > neck_z + 0.03) & (z < neck_z + 0.055) & (wh < 0.7) & (whand < 0.1)
        self._shell("collar", col, 0.011, cotton_material(self.name + "_lace", (0.78, 0.76, 0.7), sheen=0.2), solid=0.002)
        self._buttons_front(bv)
        legs = u & (z < hip_z + 0.06)
        if self.SEATED:
            sk = u & (z < hip_z + 0.08) & (z > knee_z - 0.2) & (whand < 0.05)
            self.skirt, _ = self._shell("skirt", sk, 0.03, self.dress_mat, solid=0.003, drape=40, displace=0.008)
            ankle_z = self.marks["ankle"]
            st = u & (z <= knee_z - 0.15) & (z > ankle_z + 0.02)
            self._shell("stockings", st, 0.003, cotton_material(self.name + "_st", (0.08, 0.06, 0.05), sheen=0.4), solid=0.001)
            sh = u & (z <= ankle_z + 0.05)
            self._shell("shoes", sh, 0.006, leather_material(self.name + "_sh", wet=0.0, rough=0.35), solid=0.002, drape=60)
            self._hide_skin(bod | (u & (z < hip_z + 0.06) & (z > knee_z - 0.15)) | st | sh)
        else:
            self.skirt = self._bell_skirt(hip_z, co)
            self._hide_skin(bod | legs)

    def _buttons_front(self, bv):
        co = self.rest_co[bv] + self.rest_n[bv] * 0.009
        front = co[(co[:, 1] < -0.02)]
        mat = D.brass_material(self.name + "_jet"); p = mat.node_tree.nodes["Principled BSDF"]
        p.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1); p.inputs['Roughness'].default_value = 0.15
        zmin, zmax = self.marks["hip"] + 0.06, self.marks["neck"] + 0.02
        for k in range(7):
            zz = zmax - k * (zmax - zmin) / 6
            cand = front[np.abs(front[:, 2] - zz) < 0.01]
            if len(cand) == 0:
                continue
            p0 = cand[np.argmin(np.abs(cand[:, 0]))]
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.0045, location=tuple(p0))
            b = bpy.context.active_object; b.name = "button"; b.data.materials.append(mat)
            mw = b.matrix_world.copy()
            b.parent = self.h.arm; b.parent_type = 'BONE'; b.parent_bone = "spine03"
            bpy.context.view_layer.update(); b.matrix_world = mw
            self.button_objs.append(b)

    def _bell_skirt(self, hip_z, co):
        """Lathe skirt from the waist to the floor, fuller behind (bustle); rides on the pelvis bone."""
        waist_z = hip_z + 0.07
        tor = _w(self.h, ("spine", "pelvis", "upperleg01", "root")) > 0.6
        sel = self.used & tor & (np.abs(co[:, 2] - waist_z) < 0.012)
        ring = co[sel]
        cx, cy = ring[:, 0].mean(), ring[:, 1].mean()
        n = 64; nv = 26
        verts = []; faces = []
        ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
        # waist radius per angle from the body ring (+ ease)
        ra = np.arctan2(ring[:, 1] - cy, ring[:, 0] - cx); rr = np.hypot(ring[:, 0] - cx, ring[:, 1] - cy)
        wr = np.array([rr[np.argmin(np.abs(np.angle(np.exp(1j * (ra - a)))))] for a in ang]) + 0.012
        floor = 0.03
        rng = np.random.default_rng(3)
        ph = rng.uniform(0, 2 * np.pi, 3)
        for j in range(nv + 1):
            t = j / nv
            zz = waist_z + (floor - waist_z) * t
            for k, a in enumerate(ang):
                back = max(0.0, math.sin(a)) ** 2            # +Y is behind her
                bustle = 0.11 * back * math.exp(-((t - 0.18) / 0.16) ** 2) + 0.06 * back * t
                flare = (self.SKIRT_R - wr[k]) * (t ** 1.35)
                fold = 0.012 * t * sum(math.sin(a * (9 + 4 * q) + ph[q]) for q in range(3)) / 3
                r = wr[k] + flare + bustle + fold
                verts.append((cx + r * math.cos(a), cy + r * math.sin(a), zz))
        for j in range(nv):
            for k in range(n):
                a0, b0 = j * n + k, j * n + (k + 1) % n
                faces.append([a0, b0, b0 + n, a0 + n])
        me = bpy.data.meshes.new(self.name + "_skirt"); me.from_pydata(verts, [], faces); me.update()
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
        o = bpy.data.objects.new(me.name, me); bpy.context.collection.objects.link(o)
        o.data.materials.append(self.dress_mat)
        so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.004; so.offset = 1
        o.modifiers.new("Sub", "SUBSURF").levels = 1
        mw = o.matrix_world.copy()
        o.parent = self.h.arm; o.parent_type = 'BONE'; o.parent_bone = "spine05"
        bpy.context.view_layer.update(); o.matrix_world = mw
        self.extra_objs.append(o)
        return o

    def _grow_hair(self, density):
        rel, head, lips, mz, ec = self._head_masks()
        x, y, z = rel[:, 0], rel[:, 1], rel[:, 2]
        line = np.interp(y, [-0.12, -0.07, 0.0, 0.05, 0.12], [0.05, 0.045, 0.005, -0.06, -0.09])
        scalp = head & (z > line)
        brow = head & (z > 0.012) & (z < 0.026) & (y < -0.055) & (np.abs(x) > 0.014) & (np.abs(x) < 0.055)
        P, bvh = self._posed_surface()
        R = self.head_R
        mat = hair_material(self.name + "_hair", self.HAIR["melanin"], self.HAIR["redness"], rough=0.3)
        mid = float(P[self.used, 0].mean())
        # centre parting: strands comb away from the midline over the crown, then back and down to the bun
        def comb(p):
            sx = math.copysign(1.0, p.x - mid)
            return R @ Vector((0.55 * sx, 0.85, -0.35))
        self.hair_objs.append(self._strands("hair", scalp, P, bvh, int(60000 * density), (0.03, 0.06), 0.0011,
                                            comb=comb, lift=0.0028, mat=mat, curl=0.08, segs=8))
        self.hair_objs.append(self._strands("brows", brow, P, bvh, int(1800 * density), (0.005, 0.009), 0.0005,
                                            comb=lambda p: R @ Vector((math.copysign(1.0, p.x - mid), 0, 0.3)),
                                            lift=0.001, mat=mat, curl=0.1))
        self._bun(mat, density)

    def _bun(self, mat, density):
        rel, head, lips, mz, ec = self._head_masks()
        R = self.head_R
        P, bvh = self._posed_surface()
        hc = Vector(P[head].mean(0))
        d = (R @ Vector((0, 1.0, -0.55))).normalized()          # back of the head, below the crown
        hit = bvh.ray_cast(hc + d * 0.4, -d)
        loc = hit[0] if hit[0] is not None else hc + d * 0.1
        c = loc + d * 0.03
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.04, location=tuple(c))
        b = bpy.context.active_object; b.name = self.name + "_bun"; b.scale = (1.2, 0.75, 0.85)
        b.rotation_euler = (R.to_euler())
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        tw = b.modifiers.new("twist", "DISPLACE"); tx = bpy.data.textures.new("buntex", "WOOD")
        tx.wood_type = 'RINGNOISE'; tx.noise_scale = 0.02; tw.texture = tx; tw.strength = 0.006
        b.data.materials.append(self._bun_mat())
        self.hair_objs.append(b)

    def _bun_mat(self):
        m, N, L, p = D._mat(self.name + "_bunm")
        tc = N.new("ShaderNodeTexCoord")
        wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'RINGS'; wv.rings_direction = 'Z'; wv.inputs['Scale'].default_value = 60
        wv.inputs['Distortion'].default_value = 4; L.new(tc.outputs['Object'], wv.inputs['Vector'])
        base = (0.05, 0.022, 0.012) if self.HAIR["melanin"] > 0.6 else (0.3, 0.18, 0.08)
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (*base, 1)
        mx.inputs[7].default_value = (*[c * 2.2 for c in base], 1); L.new(wv.outputs['Fac'], mx.inputs['Factor'])
        L.new(mx.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.38
        p.inputs['Sheen Weight'].default_value = 0.6
        bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.6; L.new(wv.outputs['Fac'], bm.inputs['Height'])
        L.new(bm.outputs['Normal'], p.inputs['Normal'])
        return m

    def bonnet(self):
        """A straw bonnet with a brim, tied under the chin, sitting over the hair (call after finish_live)."""
        pass


class OldSarah(Woman):
    """Sarah Elizabeth Cobb Briggs, 30: a dark bottle-green wool day dress."""
    YEARS = 30; HEIGHT = 0.42
    EXTRA = {"targets/nose/nose-scale-horiz-decr": 0.25, "targets/chin/chin-prominent-decr": 0.2,
             "targets/head/head-oval": 0.5, "targets/mouth/mouth-scale-horiz-decr": 0.15}
    DRESS = (0.02, 0.055, 0.04)


class OldVisitor(Woman):
    YEARS = 45; WEIGHT = 0.6
    DRESS = (0.12, 0.035, 0.07)
    HAIR = dict(melanin=0.55, redness=0.5)
    EXTRA = {"targets/head/head-round": 0.4}


class OldChild(Woman):
    """Sophia Matilda Briggs, 2: a short cotton dress over pantalettes; fine light hair."""
    YEARS = 2; HEIGHT = 0.5; WEIGHT = 0.5; MUSCLE = 0.4
    EXTRA = {}
    SKIN = dict(base=(0.66, 0.45, 0.36), weather=0.25)
    HAIR = dict(melanin=0.45, redness=0.55)
    DRESS = (0.62, 0.55, 0.42); PATTERN = "check"; SKIRT_R = 0.2

    def _bell_skirt(self, hip_z, co):
        o = Woman._bell_skirt(self, hip_z, co)
        # cut the skirt at the knee: drop the lower rings
        knee = self.marks["knee"] - 0.02
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < knee], context='VERTS')
        bm.to_mesh(o.data); bm.free()
        return o

    def _dress(self):
        h = self.h
        co, hip_z, neck_z, ankle_z, knee_z, dist_wrist = self._marks()
        wh = _w(h, HEAD); whand = _w(h, HAND); wfoot = _w(h, FOOT); z = co[:, 2]; u = self.used
        self.dress_mat = cotton_material(self.name + "_dress", self.DRESS, sheen=0.55, pattern=self.PATTERN, scale=120)
        bod = u & (wh < 0.4) & (whand < 0.05) & (z > hip_z - 0.02) & (z < neck_z + 0.03) & (dist_wrist > 0.03)
        self.bodice, bv = self._shell("bodice", bod, 0.008, self.dress_mat, solid=0.002, drape=30)
        st = u & (z < knee_z + 0.05) & (z > ankle_z + 0.02) & (wfoot < 0.3)
        self._shell("stockings", st, 0.003, cotton_material(self.name + "_st", (0.7, 0.68, 0.62), sheen=0.3), solid=0.001)
        boot = u & (z < ankle_z + 0.05)
        self._shell("shoes", boot, 0.006, leather_material(self.name + "_sh", wet=0.0, rough=0.35), solid=0.002, drape=60)
        self.skirt = self._bell_skirt(hip_z, co)
        self._hide_skin(bod | (u & (z < hip_z + 0.06) & (z > knee_z - 0.05)) | st | boot)

    def _grow_hair(self, density):
        rel, head, lips, mz, ec = self._head_masks()
        y, z = rel[:, 1], rel[:, 2]
        line = np.interp(y, [-0.1, -0.05, 0.0, 0.05, 0.1], [0.04, 0.035, 0.0, -0.045, -0.06])
        scalp = head & (z > line)
        P, bvh = self._posed_surface()
        R = self.head_R
        mat = hair_material(self.name + "_hair", self.HAIR["melanin"], self.HAIR["redness"], rough=0.3)
        self.hair_objs.append(self._strands("hair", scalp, P, bvh, int(35000 * density), (0.02, 0.045), 0.0008,
                                            comb=lambda p: R @ Vector((0, 0.5, -0.8)), lift=0.002, mat=mat, curl=0.35, segs=8))


class OldBoy(Sailor):
    """Arthur Briggs, 7."""
    YEARS = 7; MUSCLE = 0.45; WEIGHT = 0.45; HEIGHT = 0.5
    EXTRA = {}
    SKIN = dict(base=(0.62, 0.42, 0.33), weather=0.2)
    JACKET = (0.09, 0.07, 0.05); SCARF = (0.5, 0.45, 0.38); CAP = False; BEARD = False


class Deveau2(Person):
    """Oliver Deveau exactly as the shared library builds him (deveau.Deveau), but with a live rig."""
    YEARS = 34; MUSCLE = 0.66; WEIGHT = 0.52; HEIGHT = 0.56
    EXTRA = {"targets/chin/chin-prominent-incr": 0.3, "targets/nose/nose-hump-incr": 0.4,
             "targets/nose/nose-scale-vert-incr": 0.2, "targets/eyebrows/eyebrows-trans-down": 0.3,
             "targets/cheek/l-cheek-bones-incr": 0.35, "targets/cheek/r-cheek-bones-incr": 0.35,
             "targets/head/head-age-incr": 0.25, "targets/chin/chin-bones-incr": 0.3}
    SKIN = dict(base=(0.43, 0.25, 0.16), weather=0.6)

    def __init__(self, name="Deveau", wet=0.35, **kw):
        Person.__init__(self, name, wet=wet, **kw)

    def _dress(self):
        D.Deveau._dress(self)

    def _grow_hair(self, density):
        D.Deveau._grow_all(self, density)



# ============================================================================= shared cast (claude/mary-celeste-3d lib)
# The approved shared characters (briggs.Briggs, women.Sarah / Sophia / Arthur) bake their pose in finish(). This adapter
# keeps the scenes' API: finish_live() = shared finish() + the rig moved to its place (so bone positions are world
# positions for cameras and hand props) + ground() + look() that re-aims eyes and corneas together.
import briggs as _B
import women as _W


class _SharedLive:
    def __init__(self, *a, seated=False, expr=None, **kw):
        self.SEATED = seated
        super().__init__(*a, **kw)

    def _hem(self, o, hip_z, drop=0.15, flare=0.028):
        return super()._hem(o, hip_z, drop=(0.03 if getattr(self, "SEATED", False) else drop), flare=flare)

    def finish_live(self, look_at=None, hair=True, density=1.0, place=None, ground=True):
        place = place or Matrix.Identity(4)
        self.finish(look_at=look_at, place=place, density=density, hair=hair)
        h = self.h
        h.arm.matrix_world = place @ h.arm.matrix_world          # meshes are baked: moving the rig only moves the bones
        bpy.context.view_layer.update()
        if ground:
            Person.ground(self)
        Person.tag(self)                    # wrists + knuckles + fingertips as hand points (P5's convention)
        return self

    def ground(self, *a, **k):
        lift = Person.ground(self, *a, **k)
        return lift

    def look(self, target):
        bpy.context.view_layer.update()
        cor = list(getattr(self, "corneas", []) or [])
        for i, e in enumerate(self.h.eyes):
            loc = e.matrix_world.to_translation(); sc = e.matrix_world.to_scale()
            q = (-(Vector(target) - loc).normalized()).to_track_quat('Y', 'Z')
            e.matrix_world = Matrix.LocRotScale(loc, q, sc)
            if i < len(cor):
                c = cor[i]; c.matrix_world = Matrix.LocRotScale(c.matrix_world.to_translation(), q, c.matrix_world.to_scale())


class Briggs(_SharedLive, _B.Briggs):
    def __init__(self, name="Briggs", wet=0.0, seated=False, expr=None, **kw):
        _SharedLive.__init__(self, name=name, wet=wet, seated=seated)


class Sarah(_SharedLive, _W.Sarah):
    def __init__(self, name="Sarah", seated=False, bonnet=False, shawl=False, expr=None, wet=0.0, **kw):
        self.SEATED = seated
        _W.Sarah.__init__(self, name=name, seated=seated, bonnet=bonnet, shawl=shawl, wet=wet)


class Visitor(Sarah):
    """A lady visiting the ship in New York (shot 14). lib Sarah's construction, but her own person: older (48), a
    rounder, heavier face, light greying hair, a dark blue dress under a short wool mantle with a white lace collar,
    and a brown bonnet. (Shawl off: the mantle replaces it.)"""
    DRESS = (0.025, 0.04, 0.08)           # dark blue wool
    BONNET = (0.12, 0.07, 0.035)          # brown
    MANTLE = (0.05, 0.03, 0.025)          # dark brown wool mantle
    HAIR = (0.4, 0.05)                    # light, greying
    WEIGHT = 0.62; HEIGHT = 0.4
    EXTRA = {"targets/head/head-round": 0.6, "targets/cheek/l-cheek-volume-incr": 0.5, "targets/cheek/r-cheek-volume-incr": 0.5,
             "targets/nose/nose-scale-vert-incr": 0.35, "targets/nose/nose-hump-incr": 0.3, "targets/chin/chin-width-incr": 0.4,
             "targets/eyebrows/eyebrows-trans-down": 0.3, "targets/head/head-age-incr": 0.6,
             "targets/breast/female-young-averagemuscle-averageweight-mincup-averagefirmness": 0.8,
             "targets/breast/breast-point-decr": 1.0, "targets/breast/breast-dist-decr": 0.6}

    def __init__(self, name="Visitor", expr=None, **kw):
        self.SEATED = False
        _W.Sarah.__init__(self, name=name, years=48, seated=False, bonnet=True, shawl=False, wet=0.0)

    def _dress(self):
        _W.Sarah._dress(self)
        m = self.marks; co = self.rest_co; z = co[:, 2]; u = self.used
        wh = D._w(self.h, D.HEAD); whand = D._w(self.h, D.HAND)
        sh = np.array(self.h.joint("upperarm01.L____head"))
        # short mantle: shoulders and upper back/chest, down over the upper arms (a cape, open at the front edge)
        top = m["neck"] + 0.02
        mant = u & (wh < 0.5) & (whand < 0.02) & (z < top) & (z > sh[2] - 0.2) & ~((co[:, 1] < -0.02) & (np.abs(co[:, 0] - float(co[u, 0].mean())) < 0.13) & (z < m["neck"] - 0.06))
        mm = D.wool_material(self.name + "_mantle", self.MANTLE, weave=300, sheen=0.3, dirt=0.15)
        self.mantle, _ = self._shell("mantle", mant, 0.034, mm, solid=0.004, drape=140, displace=0.003,
                                     flare=lambda b: np.clip((top - b[:, 2]) / 0.25, 0, 1) * 0.035)
        lace = cotton_material(self.name + "_lace", (0.82, 0.8, 0.74), sheen=0.3)
        col = u & (z > m["neck"] - 0.01) & (z < m["neck"] + 0.07) & (wh < 0.7) & (whand < 0.05)
        self._shell("lacecollar", col, 0.042, lace, solid=0.002, drape=10)


class Child(_SharedLive, _W.Sophia):
    def __init__(self, name="Sophia", seated=False, expr=None, wet=0.0, **kw):
        self.SEATED = seated
        _W.Sophia.__init__(self, name=name, seated=seated, wet=wet)


class Boy(_SharedLive, _W.Arthur):
    def __init__(self, name="Arthur", seated=False, expr=None, wet=0.0, **kw):
        self.SEATED = seated
        _W.Arthur.__init__(self, name=name, seated=seated, wet=wet)
