"""Mummy thumbnail B1 v2, "pulled from three people": the pale composite skull hangs in black, its wrong jaw torn
away below it, and deep-red hands reach in out of the dark from every side, gripping the skull and the jaw.
Real cranium + mandible scans (mummy/3d lib/bones.py); hands are a CC-BY scan-style forearm (Sketchfab "ZOMBIE HAND",
Colin.Greenall) in glossy blood red. Hard white key on the bone, red rims, the left of the frame kept dark for text.
No clipping: every hand is backed off along its own reach until it no longer touches the bone.
    PREVIEW=0.4 SPP=48 blender -b --python mummy_hands.py"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
C = T.use("mummy")
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
import bones as B, sets as S, sf
E = os.environ.get
sc = T.res_setup(int(E("SPP", "256")), noise=0.01)
rng = random.Random(int(E("SEED", "5")))
HAND = "66ca5bfb6aeb421a8cbccd6db0ae1458"

# ---------------------------------------------------------------- skull and the wrong jaw
cr = B.hero_cranium(tone=((0.78, 0.72, 0.6), (0.42, 0.36, 0.27)))
md = B.hero_mandible(tone=((0.55, 0.42, 0.28), (0.25, 0.17, 0.1)))
SK = Vector((float(E("SKX", "0.11")), 0.0, float(E("SKZ", "0.06"))))
cr.location = SK
cr.rotation_euler = (math.radians(float(E("CRX", "-6"))), math.radians(float(E("CRY", "7"))), math.radians(float(E("CRZ", "-14"))))
# the jaw torn down and away: a gap, turned off-true (it belongs to someone else)
md.location = SK + Vector((float(E("MDX", "0.012")), -0.012, -0.07 - float(E("GAP", "0.075"))))
md.rotation_euler = (math.radians(float(E("MDRX", "14"))), math.radians(float(E("MDRY", "-9"))), math.radians(float(E("MDRZ", "-4"))))
bpy.context.view_layer.update()


def bvh(o):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(o.matrix_world); t = BVHTree.FromBMesh(bm); bm.free(); oe.to_mesh_clear()
    return t


BONES = [bvh(cr), bvh(md)]

# ---------------------------------------------------------------- the hand template
r_, ms = sf.model(HAND)
bpy.context.view_layer.update()
src = ms[0]
me = src.data.copy(); me.transform(src.matrix_world)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
lo, hi = co.min(0), co.max(0)
L_HAND = float(E("HLEN", "0.42"))
s = L_HAND / (hi[2] - lo[2])
co = (co - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * s      # origin at the elbow end, fingers +z
me.vertices.foreach_set("co", co.ravel()); me.update()
for pl in me.polygons:
    pl.use_smooth = True
for o in list(r_.children_recursive) + [r_]:
    bpy.data.objects.remove(o)
red = bpy.data.materials.new("blood_red"); red.use_nodes = True; p = red.node_tree.nodes["Principled BSDF"]
p.inputs['Base Color'].default_value = (*[float(x) for x in E("RED", "0.2,0.006,0.012").split(",")], 1)
p.inputs['Roughness'].default_value = 0.32; p.inputs['Coat Weight'].default_value = 0.4; p.inputs['Coat Roughness'].default_value = 0.2
p.inputs['Subsurface Weight'].default_value = 0.15; p.inputs['Subsurface Radius'].default_value = (0.9, 0.15, 0.1)
p.inputs['Subsurface Scale'].default_value = 0.01
tc = red.node_tree.nodes.new("ShaderNodeTexNoise"); tc.inputs['Scale'].default_value = 60
bmp = red.node_tree.nodes.new("ShaderNodeBump"); bmp.inputs['Strength'].default_value = 0.15
red.node_tree.links.new(tc.outputs['Fac'], bmp.inputs['Height']); red.node_tree.links.new(bmp.outputs['Normal'], p.inputs['Normal'])
me.materials.clear(); me.materials.append(red)
hands = []


def on_bone(aim, frm):
    """First hit on the bone along the ray from `frm` toward `aim` (else aim)."""
    d = (Vector(aim) - Vector(frm)).normalized(); best = None
    for b in BONES:
        hit = b.ray_cast(Vector(frm), d)
        if hit[0] is not None and (best is None or hit[3] < best[1]):
            best = (hit[0], hit[3])
    return best[0] if best else Vector(aim)


def hand(target, frm, roll=0.0, scale=1.0, back=True, name="hand"):
    """A forearm reaching from direction `frm` (a point it comes from) so its fingertips meet `target`; then backed
    off along its reach until it no longer intersects the bone."""
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    d = (Vector(target) - Vector(frm)).normalized()
    q = d.to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), roll)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = q; o.scale = (scale,) * 3
    o.location = Vector(target) - d * L_HAND * scale * 0.97
    if back:
        for k in range(80):
            bpy.context.view_layer.update()
            t = bvh(o)
            if not any(t.overlap(b) for b in BONES):
                break
            o.location -= d * 0.004
        print('BACKOFF', name, k)
    hands.append(o)
    return o


# hero hands: gripping the cranium (top, both sides) and dragging the jaw down and away
c = SK
hero = [  # aim point (snapped onto the bone along the reach), where the arm comes from, roll
    (c + Vector((0.0, -0.02, 0.06)), c + Vector((0.15, -0.25, 0.6)), 3.0),        # fingers over the crown, from above
    (c + Vector((0.07, -0.02, 0.02)), c + Vector((0.6, -0.15, 0.12)), -1.5),      # gripping the right side of the vault
    (c + Vector((-0.06, 0.02, 0.04)), c + Vector((-0.5, 0.25, 0.3)), 1.5),        # left side, from behind
    (c + Vector((0.035, -0.03, -0.18)), c + Vector((0.22, -0.3, -0.6)), -0.5),    # jaw: dragged down from below right
    (c + Vector((-0.035, -0.03, -0.18)), c + Vector((-0.2, -0.25, -0.62)), 0.7),  # jaw: from below left
    (c + Vector((0.05, 0.0, -0.12)), c + Vector((0.55, 0.15, -0.3)), -1.0),       # jaw angle from the right
]
for i, (tg, fr, rl) in enumerate(hero[:int(E("NHERO", "6"))]):
    hand(on_bone(tg, fr), fr, rl, scale=rng.uniform(0.95, 1.08), name=f"hero{i}")
# the crowd: more arms reaching out of the dark behind, all round
for i in range(int(E("NCROWD", "22"))):
    a = rng.uniform(-1.6, 1.7) if i % 4 else rng.uniform(1.9, 4.4); rad = rng.uniform(0.17, 0.4)
    tg = c + Vector((math.cos(a) * rad, rng.uniform(0.15, 0.6) + (0.35 if math.cos(a) < 0 else 0), math.sin(a) * rad * 0.8 - 0.06))
    fr = tg + Vector((math.cos(a) * 0.3, rng.uniform(0.35, 0.7), math.sin(a) * 0.3))
    hand(tg, fr, rng.uniform(0, 6.28), scale=rng.uniform(0.9, 1.15), name=f"crowd{i}")

# ---------------------------------------------------------------- light: black world, hard key on the bone, red rims
S.world((0, 0, 0), 0.0)
key = bpy.data.lights.new("key", 'SPOT'); key.energy = float(E("KEY_E", "60")); key.spot_size = math.radians(float(E("KEY_ANG", "28")))
key.spot_blend = 0.6; key.shadow_soft_size = 0.06; key.color = (1.0, 0.96, 0.9)
ko = bpy.data.objects.new("key", key); sc.collection.objects.link(ko); ko.location = c + Vector((-0.35, -0.95, 0.55))
ko.rotation_euler = (c + Vector((0, 0, -0.04)) - ko.location).to_track_quat('-Z', 'Y').to_euler()
T.area("rimL", c + Vector((-0.6, 0.6, 0.3)), c, 0.6, float(E("RIM_E", "22")), color=(1.0, 0.18, 0.12))
T.area("rimR", c + Vector((0.6, 0.5, 0.1)), c, 0.6, float(E("RIM_E", "22")), color=(1.0, 0.25, 0.15))
T.area("fill", c + Vector((0.3, -1.0, -0.2)), c, 1.0, float(E("FILL_E", "0")), color=(0.85, 0.9, 1.0))

# ---------------------------------------------------------------- camera: skull and jaw right of centre, dark left for text
cam = c + Vector((float(E("CAMX", "-0.08")), float(E("CAMY", "-0.9")), float(E("CAMZ", "0.0"))))
tgt = c + Vector((float(E("AX", "-0.14")), 0, float(E("AZ", "-0.03"))))
C.camera(cam, tgt, lens=float(E("LENS", "50")), fstop=float(E("FSTOP", "5.6")), focus=(c - cam).length)

if E("CLIP"):
    import clipcheck
    clipcheck.check("mummy_hands", limit=40); sys.exit(0)
T.grade(sc, sat=float(E("SAT", "1.2")), con=float(E("CON", "1.12")), expo=float(E("EXPO", "0.0")), vig=float(E("VIG", "0.35")))
T.render(sc, "mummy_hands")
