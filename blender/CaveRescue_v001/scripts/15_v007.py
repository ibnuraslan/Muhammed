"""v007 (director: watch the MOVING preview and fix every fault, LESSONS_LEARNED section 1).
- Eye fix on every MPFB character (14_eye_fix.py: no black-hole eyes).
- DOF at f/11 (LESSONS 2.12: nothing blurred).
- Camera clearance in the ranges where the preview showed a body, rock, rope or wall filling the lens: the camera is
  pushed away from the nearest obstacle (character bones as capsules, static meshes by nearest surface) to a clearance,
  the push is smoothed over time and eased in/out, so beat frames and the path shape stay as they were.
blender -b in.blend --python 15_v007.py -- out.blend"""
import bpy, sys, os, math
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
sc = bpy.context.scene; cam = sc.camera
_NO_SAVE = True; exec(open(os.path.join(HERE, "14_eye_fix.py")).read())
cam.data.dof.aperture_fstop = 11.0
# (start, end, clearance m, include env walls)   ranges from preview pv1 (film frames)
RANGES = [(120, 152, 1.4, False), (280, 300, 0.9, False), (386, 406, 0.9, False), (496, 556, 0.9, True),
          (1712, 1740, 0.45, True), (1996, 2020, 0.75, False), (2098, 2122, 0.9, False), (2528, 2544, 0.8, False), (2848, 2862, 0.8, False)]
ENV = ("S5_Passage", "S2_Tunnel", "S4_Cavern")
SKIP = ("FX_", "Rain", "Water", "Flood", "S3_", "CAM_", "Murk", "Silt", "Dome", "Sky", "Ground", "Floor", "Terrain")
rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE']
def rig_points(r):
    pts = []
    for pb in r.pose.bones:
        if not pb.bone.use_deform: continue
        h = r.matrix_world @ pb.head; t = r.matrix_world @ pb.tail
        for k in (0.0, 0.5, 1.0): pts.append(h.lerp(t, k))
    return pts
static = {}
def bvh_static(o):
    if o.name not in static:
        dg = bpy.context.evaluated_depsgraph_get(); static[o.name] = BVHTree.FromObject(o, dg)
    return static[o.name]
def push_at(f, clear, env):
    sc.frame_set(f); c = cam.matrix_world.translation.copy(); best = V((0, 0, 0))
    for r in rigs:
        if r.hide_render: continue
        for p in rig_points(r):
            d = c - p; L = d.length
            if L < clear and L > 1e-4:
                v = d.normalized() * (clear - L)
                if v.length > best.length: best = v
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render or o.parent is not None and o.parent.type == 'ARMATURE': continue
        if any(s in o.name for s in SKIP): continue
        isenv = any(o.name.startswith(e) for e in ENV)
        if isenv and not env: continue
        lo = [o.matrix_world @ V(b) for b in o.bound_box]
        if not isenv and min((c - p).length for p in lo) > 6: continue
        bv = bvh_static(o); loc, nr, i, dd = bv.find_nearest(o.matrix_world.inverted() @ c, clear)
        if loc is None: continue
        lw = o.matrix_world @ loc; d = c - lw; L = d.length
        cl = clear if not isenv else 0.45
        if L < cl and L > 1e-4:
            v = d.normalized() * (cl - L)
            if v.length > best.length: best = v
    return best
def fcs(o):
    ad = o.animation_data
    return [fc for lay in ad.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves if fc.data_path == "location"]
locf = sorted(fcs(cam), key=lambda fc: fc.array_index)
aim = cam.constraints[0].target if cam.constraints else None
aimf = sorted(fcs(aim), key=lambda fc: fc.array_index) if aim else []
for f0, f1, clear, env in RANGES:
    raw = {}
    total = V((0, 0, 0))
    for it in range(3):
        for f in range(f0, f1 + 1):
            raw[f] = raw.get(f, V((0, 0, 0)))
        # sample pushes at the current (already offset) path
        add = {f: push_at(f, clear, env) for f in range(f0, f1 + 1)}
        if max(v.length for v in add.values()) < 0.01: break
        # temporal smoothing (gaussian, 6 frames) and ease to 0 at the range ends
        sm = {}
        for f in range(f0, f1 + 1):
            acc = V((0, 0, 0)); w = 0
            for g in range(f - 8, f + 9):
                if g in add: k = math.exp(-((g - f) / 4.0) ** 2); acc += add[g] * k; w += k
            e = min(1.0, (f - f0) / 8.0, (f1 - f) / 8.0); e = e * e * (3 - 2 * e)
            sm[f] = acc / w * e * 1.3
        for f in range(f0, f1 + 1):
            for i in range(3):
                kp = [k for k in locf[i].keyframe_points if int(round(k.co.x)) == f]
                if kp: kp[0].co.y += sm[f][i]; kp[0].handle_left.y += sm[f][i]; kp[0].handle_right.y += sm[f][i]
                kq = [k for k in aimf[i].keyframe_points if int(round(k.co.x)) == f] if aimf else []
                if kq: kq[0].co.y += sm[f][i]; kq[0].handle_left.y += sm[f][i]; kq[0].handle_right.y += sm[f][i]   # aim moves with it: same view direction
        for fc in locf + aimf: fc.update()
        mx = max(v.length for v in sm.values())
        print("CLEAR", f0, f1, "iter", it, "max push cm", round(mx * 100, 1))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("V007_OK")
