"""Contact + camera audit. blender -b film.blend --python 06_audit.py -- <report.txt>"""
import sys, json, math
import bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; C = bpy.data.objects["Composer"]; PB = C.pose.bones
piano = bpy.data.objects["Piano"]; KEY_Z = sc["key_z"]; KX0, KX1 = sc["kx"]
L = []
def log(*a): s = " ".join(str(x) for x in a); print(s); L.append(s)
def ray_down(o, x, y):
    ok, loc, n, i = o.ray_cast(o.matrix_world.inverted() @ Vector((x, y, 3)), Vector((0, 0, -1)))
    return (o.matrix_world @ loc).z if ok else None
TIPS = ["finger%d-3.%s" % (k, s) for k in range(1, 6) for s in "LR"]
# 1. fingertips at key strikes
down = json.loads(sc["down"]); err = []
for s, f, x in down:
    sc.frame_set(f); best = 9
    for k in range(1, 6):
        t = C.matrix_world @ PB["finger%d-3.%s" % (k, s)].tail; kz = ray_down(piano, t.x, t.y) or KEY_Z; best = min(best, t.z - kz)
    err.append((best - 0.004, f, s))
e = [abs(a) for a, _, _ in err]
log("STRIKES", len(err), "lowest fingertip (tip bone end, ~4 mm pad) vs key top: max |err| %.4f m, mean %.4f m" % (max(e), sum(e) / len(e)))
worst = sorted(err, key=lambda t: -abs(t[0]))[:5]; log("  worst", [(round(a, 4), f, s) for a, f, s in worst])
# 2. no fingertip below the key tops / inside the fallboard, every 2 frames
pen = []; fb = []
for f in range(1, sc.frame_end + 1, 2):
    sc.frame_set(f)
    for b in TIPS:
        t = C.matrix_world @ PB[b].tail
        if KX0 - 0.05 < t.x < KX1 + 0.05 and 0.0 < t.y < 0.16:
            kz = ray_down(piano, t.x, t.y)
            if kz and t.z < kz - 0.008: pen.append((f, b, round(kz - t.z, 4)))
        if -0.7 < t.x < 0.7 and 0.16 < t.y < 0.5 and 0.8 < t.z < 1.0: fb.append((f, b))
log("FINGERTIPS below key top > 8 mm:", len(pen), pen[:6])
log("FINGERTIPS inside fallboard/case:", len(fb), fb[:6])
# 3. seat + feet + bench (evaluated meshes, sampled)
dg = bpy.context.evaluated_depsgraph_get()
bench = bpy.data.objects["Bench"]; bx, by = bench.location.x, bench.location.y
seat = []; feet = []
for f in range(1, sc.frame_end + 1, 40):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    for name, store in (("Composer.male_elegantsuit01", seat), ("Composer.shoes03", feet)):
        ob = bpy.data.objects[name].evaluated_get(dg); me = ob.to_mesh(); M = ob.matrix_world
        if name.endswith("suit01"):
            zs = [(M @ v.co).z for v in me.vertices if abs((M @ v.co).x - bx) < 0.35 and abs((M @ v.co).y - by) < 0.22 and (M @ v.co).z < 0.7]
            if zs: store.append((f, round(min(zs) - 0.4507, 4)))
        else:
            zs = [(M @ v.co).z for v in me.vertices]
            store.append((f, round(min(zs), 4)))
        ob.to_mesh_clear()
log("SEAT trousers lowest point minus seat top (neg = sinks into cushion):", seat)
log("FEET shoe sole lowest z (0 = floor):", feet)
# 4. rod clamped in the teeth
bite, tip = bpy.data.objects["Bite"], bpy.data.objects["RodTip"]; dd = []
for f in range(32, sc.frame_end + 1, 10):
    sc.frame_set(f); dd.append((bite.matrix_world.translation - tip.matrix_world.translation).length)
log("ROD tip-to-bite distance after the clamp: max %.5f m" % max(dd))
# 5. pages on the floor
pg = []
for o in bpy.data.objects:
    if o.name.startswith(("FloorPage", "DeskPage")):
        sc.frame_set(sc.frame_end); z = o.matrix_world.translation.z
        if o.name.startswith("DeskPage") and z > 0.5: continue
        pg.append(round(z, 4))
log("PAGES on floor, origin z range:", min(pg), max(pg), "(page thickness 0.8 mm; floor at 0)")
# 6. camera inside geometry (6-direction back-face test), skipping intended enclosures
cam = sc.camera; inside = []; near = []
DIRS = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
for f in range(1, sc.frame_end + 1, 4):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); p = cam.matrix_world.translation
    back = 0; mind = 9; hitn = set()
    for d in DIRS:
        start = p
        for _ in range(4):
            ok, loc, n, i, ob, mx = sc.ray_cast(dg, start, d)
            if not ok: break
            if ob.hide_render or ob.name.startswith(("XRay_Backdrop", "Composer", "Cravat", "Ring", "Mote", "Pulse", "Trace", "Flame", "Window_Cut")):
                start = loc + d * 1e-4; continue
            mind = min(mind, (loc - p).length)
            if n.dot(d) > 0: back += 1; hitn.add(ob.name)
            break
    if back >= 4: inside.append((f, hitn))
    near.append((mind, f))
log("CAMERA inside solid geometry (>=4/6 back-face hits):", inside or "none")
log("CAMERA closest clearance to a solid surface: %s" % [(round(a, 3), f) for a, f in sorted(near)[:6]])
open(OUT, "w").write("\n".join(L) + "\n"); print("AUDIT_DONE")
