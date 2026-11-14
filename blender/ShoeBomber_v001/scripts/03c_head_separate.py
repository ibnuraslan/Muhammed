"""Head separation pass (v006d): heads must never merge. Every STEP frames, any two characters whose head centres are closer
than MIN apart: the lower-priority character's root is moved horizontally away (bomber never moves; passengers yield before
crew). Hands and feet are IK targets in world space, so contacts stay where they are.
blender -b anim.blend --python 03c_head_separate.py -- <out.blend> [f0] [f1] [step]"""
import bpy, sys, itertools
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; F0 = int(a[1]) if len(a) > 1 else 1; F1 = int(a[2]) if len(a) > 2 else 1068; STEP = int(a[3]) if len(a) > 3 else 3
MIN = 0.28
sc = bpy.context.scene; O = bpy.data.objects
YIELD = ["PaxC", "PaxD", "PaxB", "PaxA", "Steward", "Attendant", "Bomber"]   # earlier = moves first
R = [O[n] for n in YIELD if n in O]
def hc(r):
    hb = r.pose.bones["head"]; return r.matrix_world @ hb.head.lerp(hb.tail, 0.5)
moved = 0
for it in range(3):
    for f in range(F0, F1 + 1, STEP):
        sc.frame_set(f)
        for x, y in itertools.combinations(R, 2):
            d = hc(x) - hc(y); d.z = 0 if abs(d.z) < MIN else d.z
            dist = (hc(x) - hc(y)).length
            if dist >= MIN: continue
            mv = x if YIELD.index(x.name) < YIELD.index(y.name) else y
            other = y if mv is x else x
            away = hc(mv) - hc(other); away.z = 0
            if away.length < 1e-3: away = Vector((0, 0.1, 0))
            off = away.normalized() * (MIN - dist + 0.02)
            pb = mv.pose.bones["root"]
            M = mv.matrix_world @ pb.matrix; M.translation += off
            pb.matrix = mv.matrix_world.inverted() @ M
            bpy.context.view_layer.update()
            pb.keyframe_insert("location", frame=f, group="root")
            moved += 1
            print("SEP it%d f%d %s from %s %.2f" % (it, f, mv.name, other.name, dist))
print("SEPARATED", moved)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SEP_SAVED", OUT)
