"""Archaeological human bone for the Cladh Hallan composites.

  Skeleton(sex="M")                 ZBrush anatomy-study skeleton (Sketchfab CC-BY, ruslangadzhiev), split into its bones,
                                    grouped into body segments, posed by rigid rotations about anatomical joint pivots.
  sk.pose_crouched(...)             tightly flexed burial pose (knees to chest), lying on one side
  sk.place(loc, heading, ground)    lay it in a grave; bones settle a few mm into the fill
  sk.swap(seg, other_skeleton)      composite: take a segment (pelvis, skull ...) from another individual
  sk.remove(names)                  e.g. the missing left knee (patella + femur condyles + tibial plateau fragments)
  hero_cranium(healed=True)         detailed cranium (Sketchfab CC-BY) with the upper back teeth lost long before death:
                                    sockets healed into a smooth resorbed ridge
  hero_mandible()                   detailed mandible scan (Sketchfab CC-BY, jagake) with a full, worn set of teeth
  bone_material(tone, stain)        dry archaeological bone: cream to tan, sand-stained, dirt in the crevices

Units: metres. Skeleton rest data (ZBrush units): front = -y, person's left = +x, up = +z, 15.9 units tall.
"""
import math, os
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import sf

MALE = "665890c542be433fb18ef235cf987cef"
FEMALE = "5f28b52cab3e439490727e0aede55a6b"
CRANIUM = "85c233c994a346bc92823d09e02cc56c"
MANDIBLE = "2667ab0d436840f58a82da7cefb8b5be"
SCALE = 1.70 / 15.9

TONES = {   # base, darker stain
    "A": ((0.50, 0.40, 0.27), (0.24, 0.17, 0.10)),
    "B": ((0.55, 0.46, 0.33), (0.30, 0.22, 0.13)),
    "C": ((0.46, 0.36, 0.24), (0.21, 0.15, 0.08)),
    "D": ((0.52, 0.44, 0.33), (0.28, 0.22, 0.15)),
}


def bone_material(tone="A", name=None, dirt=1.0):
    base, stain = TONES[tone] if isinstance(tone, str) else tone
    m = bpy.data.materials.new(name or f"Bone_{tone}"); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    n1 = N.new("ShaderNodeTexNoise"); n1.inputs['Scale'].default_value = 18; n1.inputs['Detail'].default_value = 8
    n1.inputs['Roughness'].default_value = 0.62; L.new(tc.outputs['Object'], n1.inputs['Vector'])
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs['Scale'].default_value = 140; n2.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], n2.inputs['Vector'])
    r1 = N.new("ShaderNodeValToRGB"); r1.color_ramp.elements[0].position = 0.42; r1.color_ramp.elements[1].position = 0.68
    r1.color_ramp.elements[0].color = (*base, 1); r1.color_ramp.elements[1].color = (*stain, 1)
    L.new(n1.outputs['Fac'], r1.inputs['Fac'])
    # cavity dirt: sand ground into the pores and the sutures (pointiness)
    geo = N.new("ShaderNodeNewGeometry")
    cav = N.new("ShaderNodeMapRange"); cav.inputs['From Min'].default_value = 0.47; cav.inputs['From Max'].default_value = 0.53
    cav.inputs['To Min'].default_value = 0.75 * dirt; cav.inputs['To Max'].default_value = 0.0
    L.new(geo.outputs['Pointiness'], cav.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    L.new(cav.outputs[0], mx.inputs['Factor']); L.new(r1.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = (0.35, 0.27, 0.18, 1)
    # fine speckle (grain of the cortex)
    sp = N.new("ShaderNodeMix"); sp.data_type = 'RGBA'; sp.blend_type = 'OVERLAY'; sp.inputs['Factor'].default_value = 0.25
    L.new(mx.outputs[2], sp.inputs[6]); L.new(n2.outputs['Color'], sp.inputs[7])
    L.new(sp.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.72
    p.inputs['Subsurface Weight'].default_value = 0.08
    p.inputs['Subsurface Radius'].default_value = (0.6, 0.4, 0.25); p.inputs['Subsurface Scale'].default_value = 0.004
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.25; bm.inputs['Distance'].default_value = 0.0006
    L.new(n2.outputs['Fac'], bm.inputs['Height']); L.new(bm.outputs['Normal'], p.inputs['Normal'])
    return m


def tooth_material(name="Enamel"):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.58, 0.5, 0.36, 1); p.inputs['Roughness'].default_value = 0.35
    p.inputs['Subsurface Weight'].default_value = 0.2; p.inputs['Subsurface Radius'].default_value = (0.5, 0.4, 0.3)
    p.inputs['Subsurface Scale'].default_value = 0.002
    return m


# ----------------------------------------------------------------------------- the posable skeleton
_CACHE = {}


def _islands(me):
    """Vertex islands of a mesh -> list of index arrays."""
    n = len(me.vertices)
    ev = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get("vertices", ev); ev = ev.reshape(-1, 2)
    parent = np.arange(n)
    def find(a):
        r = a
        while parent[r] != r:
            r = parent[r]
        while parent[a] != r:
            parent[a], a = r, parent[a]
        return r
    for a, b in ev:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(n)])
    _, lab = np.unique(roots, return_inverse=True)
    return lab


def _classify(c, size, nv):
    """Body segment of a bone from its rest-pose centroid (ZBrush units; front -y, left +x)."""
    x, y, z = c; ax = abs(x); side = "L" if x > 0 else "R"
    if z > 6.55 and nv > 1500:
        return "skull"
    if 5.9 < z < 6.7 and y < -0.3:
        return "mandible"
    if ax > 2.75 and z < 0.6:
        return "hand" + side
    if ax > 2.3 and -0.3 < z < 2.5:
        return "forearm" + side
    if ax > 1.35 and 1.9 < z < 5.2 and size[2] > 1.5:
        return "upperarm" + side
    if z > 5.55 and ax < 0.25:
        return "neck"
    if 2.3 < z <= 5.6 and ax < 2.0:
        return "thorax"
    if 0.9 < z <= 2.9 and ax < 0.4:
        return "lumbar"
    if -0.9 < z <= 1.05 and ax < 1.4:
        return "pelvis"
    if -3.45 < z <= -0.9:
        return ("patella" if nv < 260 else "femur") + side
    if -7.3 < z <= -3.45:
        return "shank" + side
    if z <= -7.3:
        return "foot" + side
    if ax > 1.35:
        return "upperarm" + side
    return "thorax"


SEGMENTS = ["skull", "mandible", "neck", "thorax", "lumbar", "pelvis",
            "upperarmL", "forearmL", "handL", "upperarmR", "forearmR", "handR",
            "femurL", "patellaL", "shankL", "footL", "femurR", "patellaR", "shankR", "footR"]

PARENT = {"lumbar": "pelvis", "thorax": "lumbar", "neck": "thorax", "skull": "neck", "mandible": "skull",
          "upperarmL": "thorax", "forearmL": "upperarmL", "handL": "forearmL",
          "upperarmR": "thorax", "forearmR": "upperarmR", "handR": "forearmR",
          "femurL": "pelvis", "patellaL": "shankL", "shankL": "femurL", "footL": "shankL",
          "femurR": "pelvis", "patellaR": "shankR", "shankR": "femurR", "footR": "shankR"}

PIVOT = {   # rest-pose joint centres (ZBrush units)
    "lumbar": (0, 0.35, 1.05), "thorax": (0, 0.45, 2.95), "neck": (0, 0.35, 5.6), "skull": (0, 0.2, 6.35), "mandible": (0, 0.0, 6.55),
    "upperarmL": (1.62, 0.25, 4.95), "forearmL": (2.2, 0.32, 2.05), "handL": (2.92, 0.22, 0.02),
    "upperarmR": (-1.62, 0.25, 4.95), "forearmR": (-2.2, 0.32, 2.05), "handR": (-2.92, 0.22, 0.02),
    "femurL": (0.78, 0.05, 0.18), "shankL": (0.72, 0.0, -3.25), "patellaL": (0.72, 0.0, -3.25), "footL": (0.62, 0.05, -7.35),
    "femurR": (-0.78, 0.05, 0.18), "shankR": (-0.72, 0.0, -3.25), "patellaR": (-0.72, 0.0, -3.25), "footR": (-0.62, 0.05, -7.35),
}


class Skeleton:
    def __init__(self, sex="M", tone="A", name=None):
        self.name = name or f"Skel{sex}{tone}"
        uid = MALE if sex == "M" else FEMALE
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=sf.fetch(uid))
        new = [o for o in bpy.data.objects if o not in before]
        src = [o for o in new if o.type == 'MESH'][0]
        M = src.matrix_world.copy()
        me = src.data
        co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        co = (np.array(M)[:3, :3] @ co.T).T + np.array(M)[:3, 3]
        lab = _islands(me)
        seg_of_vert = np.empty(len(co), object)
        for k in range(lab.max() + 1):
            idx = np.where(lab == k)[0]
            P = co[idx]; lo, hi = P.min(0), P.max(0)
            seg_of_vert[idx] = _classify((lo + hi) / 2, hi - lo, len(idx))
        self.mat = bone_material(tone, name=self.name + "_bone")
        self.parts = {}
        # one object per segment (geometry in rest-pose world units, scaled to metres, origin at its pivot)
        fv = np.empty(sum(len(p.vertices) for p in me.polygons), np.int32)
        me.polygons.foreach_get("vertices", fv) if all(len(p.vertices) == 3 for p in me.polygons[:50]) else None
        polys = [tuple(p.vertices) for p in me.polygons]
        by_seg = {}
        for pi, pv in enumerate(polys):
            by_seg.setdefault(seg_of_vert[pv[0]], []).append(pv)
        self.root = bpy.data.objects.new(self.name, None); bpy.context.scene.collection.objects.link(self.root)
        for seg, faces in by_seg.items():
            used = np.unique(np.concatenate([np.array(f) for f in faces]))
            remap = -np.ones(len(co), np.int64); remap[used] = np.arange(len(used))
            piv = np.array(PIVOT.get(seg, (0, 0, 0)), np.float32)
            V = ((co[used] - piv) * SCALE).tolist()
            F = [tuple(int(remap[v]) for v in f) for f in faces]
            m2 = bpy.data.meshes.new(f"{self.name}_{seg}"); m2.from_pydata(V, [], F); m2.update()
            for poly in m2.polygons:
                poly.use_smooth = True
            o = bpy.data.objects.new(f"{self.name}_{seg}", m2); bpy.context.scene.collection.objects.link(o)
            o.data.materials.append(self.mat)
            o["bone"] = True; o["segment"] = seg; o["individual"] = self.name
            self.parts[seg] = o
        for o in new:
            bpy.data.objects.remove(o)
        # hierarchy: each segment parented to its parent segment at the joint
        self.rest = {s: Vector(PIVOT.get(s, (0, 0, 0))) * SCALE for s in self.parts}
        for s, o in self.parts.items():
            par = PARENT.get(s)
            while par and par not in self.parts:
                par = PARENT.get(par)
            if par:
                o.parent = self.parts[par]; o.location = self.rest[s] - self.rest[par]
            else:
                o.parent = self.root; o.location = self.rest[s]

    # rotations are in the segment's rest frame: x = person's left, y = back, z = up
    def bend(self, seg, x=0.0, y=0.0, z=0.0):
        if seg in self.parts:
            o = self.parts[seg]; o.rotation_mode = 'YXZ'      # y (ab/adduction) first, then x (flexion), then z (twist)
            o.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))

    def pose_crouched(self, tight=1.0, side="R", arms="face"):
        """Tightly flexed: hips ~120 deg, knees folded, spine and neck curled, forearms drawn up (hands apart, never crossed)."""
        t = tight
        self.bend("lumbar", 22 * t); self.bend("thorax", 12 * t); self.bend("neck", 18 * t); self.bend("skull", 16 * t)
        self.bend("mandible", 3)
        for s, sg in (("L", 1), ("R", -1)):
            self.bend("femur" + s, -132 * t, 0, sg * 3)
            self.bend("shank" + s, 152 * t)
            self.bend("foot" + s, 25 * t)
            if arms == "face":          # forearms drawn up, hands in front of the face, apart (never crossed)
                self.bend("upperarm" + s, -38 * t, sg * 14, 0)
                self.bend("forearm" + s, -132 * t, sg * 21, 0)
                self.bend("hand" + s, 20, 0, 0)
            else:                       # hands resting toward the knees
                self.bend("upperarm" + s, -35 * t, sg * 12, 0)
                self.bend("forearm" + s, -60 * t, sg * 19, 0)
                self.bend("hand" + s, 8)
        # lie on one side: left side up (side R down) -> rotate about the body's front axis
        self.root.rotation_mode = 'XYZ'
        self.side = side
        return self

    def place(self, loc, heading=0.0, sink=0.012, ground_fn=None):
        """Lay the posed body: rotate onto its side, turn to `heading` (deg, head direction), drop onto the ground."""
        roll = Matrix.Rotation(math.radians(-90 if self.side == "R" else 90), 4, 'Y')
        yaw = Matrix.Rotation(math.radians(heading + 180), 4, 'Z')
        self.root.matrix_world = Matrix.Translation(Vector(loc)) @ yaw @ roll
        bpy.context.view_layer.update()
        # drop: lowest vertex of each bone near the ground; settle the whole body so it rests with weight
        zmin = 1e9
        for o in self.parts.values():
            M = np.array(o.matrix_world)
            co = np.empty(len(o.data.vertices) * 3, np.float32); o.data.vertices.foreach_get("co", co)
            W = co.reshape(-1, 3)[::5] @ M[:3, :3].T + M[:3, 3]
            g = np.array([ground_fn(a, b) for a, b in W[:, :2]]) if ground_fn else loc[2]
            zmin = min(zmin, float((W[:, 2] - g).min()))
        self.root.location.z -= zmin + sink
        bpy.context.view_layer.update()
        return self

    def remove(self, *segs):
        for s in segs:
            o = self.parts.pop(s, None)
            if o:
                for ch in list(o.children):
                    ch.parent = o.parent
                bpy.data.objects.remove(o)

    def retone(self, seg, tone):
        if seg in self.parts:
            o = self.parts[seg]; o.data.materials.clear(); o.data.materials.append(bone_material(tone, name=f"{self.name}_{seg}_{tone}"))

    def objects(self):
        return list(self.parts.values())

    def world_pivot(self, seg):
        return self.parts[seg].matrix_world.translation.copy()


# ----------------------------------------------------------------------------- hero cranium and mandible
def _import(uid):
    """Import a glb and merge all its meshes (world transforms applied) into one new object."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=sf.fetch(uid))
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    bm = bmesh.new()
    for o in new:
        if o.type == 'MESH':
            m2 = o.data.copy(); m2.transform(o.matrix_world); bm.from_mesh(m2); bpy.data.meshes.remove(m2)
    me = bpy.data.meshes.new(uid[:8]); bm.to_mesh(me); bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    for o in new:
        bpy.data.objects.remove(o)
    ob = bpy.data.objects.new(uid[:8], me); bpy.context.scene.collection.objects.link(ob)
    return ob


def hero_cranium(healed=True, length=0.19, tone="A", name="Cranium"):
    """Cranium (face toward +x in the source; turned here to face -y like everything else), scaled to `length` m.
    healed: the upper premolars and molars are gone and their sockets have filled in (smooth resorbed ridge)."""
    o = _import(CRANIUM); o.name = name
    me = o.data
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    # source: face +x, up +z. Rotate -90 about z so the face looks -y.
    R = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], np.float32)
    co = co @ R.T
    lo, hi = co.min(0), co.max(0)
    s = length / (hi[1] - lo[1])
    co = (co - (lo + hi) / 2) * s
    if healed:
        co = _heal_maxilla(co)
    me.vertices.foreach_set("co", co.ravel()); me.update()
    o.data.materials.clear(); o.data.materials.append(bone_material(tone, name=name + "_bone"))
    o["bone"] = True
    return o


def _heal_maxilla(co, keep=0.021, crown=0.0085):
    """Behind the canines, flatten every upper crown into the alveolar bone: a smooth, resorbed ridge (teeth lost years
    before death). keep: distance (m) behind the incisor tips that stays toothed (incisors + canines)."""
    z = co[:, 2]; y = co[:, 1]
    front = y.min()
    face = y < front + 0.07                         # the dental arch lies in the front 7 cm
    zocc = float(np.percentile(z[face], 0.2))       # occlusal plane (lowest crowns)
    sel = face & (y > front + keep) & (z < zocc + crown)
    ridge = zocc + crown
    co[sel, 2] = ridge + (co[sel, 2] - ridge) * 0.05
    return co


def hero_mandible(length=0.105, tone="B", name="Mandible"):
    """Mandible scan (teeth up, chin toward -y), body length ~10.5 cm (gonion to chin), wear on the molar crowns."""
    o = _import(MANDIBLE); o.name = name
    me = o.data
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    lo, hi = co.min(0), co.max(0)
    co = co - (lo + hi) / 2
    s = length / (hi[1] - lo[1])
    co = co * s
    me.vertices.foreach_set("co", co.ravel()); me.update()
    o.data.materials.clear(); o.data.materials.append(bone_material(tone, name=name + "_bone"))
    o["bone"] = True
    return o
