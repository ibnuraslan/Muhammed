"""Contact / camera audit for NoPilotPlane.  blender -b anim.blend --python audit.py -- report.txt
- camera: inside geometry (first hit is a back face) or closer than 3 cm to a surface, every 3rd frame
- YOU feet: planted-foot hover/sink against the floor (z=0), and foot sliding while planted
- hands: wrist distance to the grasp targets (handset, yoke grips, throttle, door) during holds
- seated passengers / pilots: body vertices sunk into the seat cushion or the floor"""
import sys, math, bpy
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; YOU = bpy.data.objects["YOU"]
L = []
def log(s): print(s); L.append(s)
dg = bpy.context.evaluated_depsgraph_get()
lc = bpy.context.view_layer.layer_collection.children["PASSENGERS"]
# ---------------------------------------------------------------- camera
dirs = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
inside, close = [], []
for f in range(1, 4351, 3):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); p = cam.matrix_world.translation.copy()
    fwd = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    hit, loc, nrm, idx, ob, M = sc.ray_cast(dg, p, fwd, distance=0.6)
    if hit and nrm.dot(fwd) > 0.2 and ob.type == 'MESH' and "SHELL" not in ob.name:
        inside.append((f, ob.name))
    dmin = 9
    for d in dirs:
        h, lo, n, i, o, m = sc.ray_cast(dg, p, d, distance=0.2)
        if h and not o.name.startswith("YOU") and (lo - p).length < dmin: dmin = (lo - p).length; on = o.name
    if dmin < 0.03: close.append((f, on, round(dmin, 3)))
def spans(lst):
    if not lst: return "none"
    out_, s0, prev = [], lst[0][0], lst[0][0]
    for x in lst[1:]:
        if x[0] - prev > 3: out_.append((s0, prev)); s0 = x[0]
        prev = x[0]
    out_.append((s0, prev))
    return ", ".join("%.1f-%.1fs" % ((a - 1) / 60, (b - 1) / 60) for a, b in out_)
log("CAMERA inside geometry (forward ray hits a back face): " + spans(inside))
if inside: log("   objects: " + ", ".join(sorted({o for f, o in inside})))
log("CAMERA closer than 3 cm to a surface: " + spans(close))
if close: log("   objects: " + ", ".join(sorted({o for f, o, d in close})))
# ---------------------------------------------------------------- feet
lc.exclude = True
REST_ANK = {s: YOU.data.bones["foot." + s].head_local.z for s in "LR"}
prev = {}; hov, sink, slide = [], [], []
ground = lambda h: 0.206 if (1.86 < h.y < 2.08 and 0.31 < abs(h.x) < 0.73) else 0.0
for f in range(1, 4351):
    sc.frame_set(f)
    for s in "LR":
        pb = YOU.pose.bones["foot." + s]; h = YOU.matrix_world @ pb.head; t = YOU.matrix_world @ pb.tail
        if s in prev:
            v = (h - prev[s]).length * 60
            if v < 0.05:   # planted
                dz = h.z - REST_ANK[s]
                if dz - ground(h) > 0.03: hov.append((f, s, round(dz, 3)))
                if dz - ground(h) < -0.03: sink.append((f, s, round(dz, 3)))
            if 0.05 <= v < 0.25 and h.z - REST_ANK[s] - ground(h) < 0.01: slide.append((f, s, round(v, 3)))
        prev[s] = h.copy()
seated = lambda f: f < 541 or f > 2329
log("FEET planted hover >3 cm: %d frames (%s); worst %s" % (len(hov), spans(hov), max((x[2] for x in hov), default=0)))
log("   (seated beats excluded below)")
log("FEET planted hover >3 cm while standing: %d frames (%s)" % (len([x for x in hov if not seated(x[0])]), spans([x for x in hov if not seated(x[0])])))
log("FEET sink >3 cm: %d frames (%s)" % (len(sink), spans(sink)))
log("FEET slow slide on the floor (5-25 cm/s): %d frames (%s)" % (len(slide), spans(slide)))
# ---------------------------------------------------------------- hands
def wrist(s): return YOU.matrix_world @ YOU.pose.bones["wrist." + s].head
def chk(name, frames, s, target_fn, tol=0.12):
    bad = []
    for f in frames:
        sc.frame_set(f); d = (wrist(s) - target_fn()).length
        if d > tol: bad.append((f, round(d, 3)))
    log("HAND %-28s %s: %s" % (name, s, "ok" if not bad else "%d frames off (worst %.2f m) %s" % (len(bad), max(b[1] for b in bad), spans(bad))))
O = bpy.data.objects
chk("handset (20.9-26.3 s)", range(1255, 1579, 6), "R", lambda: O["HANDSET"].matrix_world.translation)
YR = O["YOKE_R"]
for s, x in (("L", -0.16), ("R", 0.16)):
    chk("yoke grip (39.2-56.5 s)", range(2353, 3391, 12), s, lambda: YR.matrix_world @ Vector((x, -0.2, 0.79)))
chk("throttle touch (59.2-59.8 s)", range(3553, 3589, 6), "R", lambda: O["THROTTLE_1"].matrix_world @ Vector((0, 0, 0.19)))
chk("door push (12.9-13.7 s)", range(775, 823, 6), "R", lambda: O["DOOR"].matrix_world @ Vector((0.45, -0.07, 1.12)), tol=0.15)
lc.exclude = False
# ---------------------------------------------------------------- seated bodies vs cushions / floor
sc.frame_set(100); dg = bpy.context.evaluated_depsgraph_get()
worst = []
for o in O:
    if o.type != 'MESH' or not o.name.endswith(".body") and ".body" not in o.name: continue
    if not o.parent or o.parent.name.startswith("YOU"): continue
    e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
    zs = [(M @ v.co).z for i, v in enumerate(me.vertices) if i % 7 == 0]
    e.to_mesh_clear()
    worst.append((min(zs), o.name))
worst.sort()
log("BODIES lowest point (floor = 0): " + ", ".join("%s %.3f" % (n, z) for z, n in worst[:6]))
open(out, "w").write("\n".join(L) + "\n"); print("AUDIT", out)
