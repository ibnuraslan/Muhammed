"""Contact / penetration audit for DrunkTrain.
blender -b anim.blend --python 04_audit.py -- <report.txt> [step]

Checks every <step> frames, only for visible objects:
  FOOT_SINK / FOOT_HOVER  shoe sole vs the walkable surface (hover only while the foot is planted, i.e. not moving)
  BODY_HOVER / BODY_SINK  Lad lying on the ballast: lowest point > 3 cm above / > 6 cm below the surface
  HEAD_ON_RAIL            beat 2-3: back of the head vs the railhead top (gap reported)
  HAND_BURIED             wrist > 4 cm under the surface
  PEN_TRAIN               Lad mesh triangles overlapping loco / wheels / plough (BVH overlap count)
  PEN_PEOPLE              people meshes overlapping each other
  PEN_HAT                 hard hat vs the worker's scalp/body (head poking through)
  PEN_PROP                bottle vs ballast/rails
  CAMERA_INSIDE           camera below the surface or within 3 cm of a surface
"""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 else 10
sc = bpy.context.scene
RAIL_H, GAUGE = sc["rail_h"], sc["gauge"]
PLAT = eval(sc["plat"]); RAMP = eval(sc["ramp"])
def ground_z(x, y):
    for tx in (0.0, -4.3):
        for sx in (-1, 1):
            if abs(x - (tx + sx * GAUGE)) < 0.04: return RAIL_H
    if PLAT["x0"] <= x <= PLAT["x1"] and PLAT["y0"] <= y <= PLAT["y1"]: return PLAT["h"]
    if RAMP["x0"] <= x <= RAMP["x1"] and RAMP["y0"] <= y <= RAMP["y1"]:
        return RAMP["h"] * (1 - (y - RAMP["y0"]) / (RAMP["y1"] - RAMP["y0"]))
    if x > 3.4 or x < -8.6: return -0.06
    return 0.0
issues = {}
def flag(k, f, m): issues.setdefault(k, []).append((f, m))
def visible(o): return not o.hide_render and o.visible_get() if False else not o.hide_render
def world_tree(o, dg, stride=1):
    ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
    vs = [mw @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps, epsilon=0.0), vs
LAD = bpy.data.objects["Lad"]
people = {n: bpy.data.objects[n] for n in ("Lad", "WitA", "WitB", "Worker")}
def part(rig, suffix):
    for c in rig.children:
        if c.name.endswith(suffix): return c
shoes = {n: [c for c in r.children if ".shoes" in c.name][0] for n, r in people.items()}
bodies = {n: part(r, ".body") for n, r in people.items()}
train = [o for o in bpy.data.collections["Train"].all_objects if o.type == 'MESH' and (o.name in ("Loco", "Plough") or o.name.startswith("wheel"))]
hat = bpy.data.objects["HardHat"]; bottle = bpy.data.objects["Bottle"]
cam = sc.camera
T_IMP, f_rest, f_stir = sc["T_IMP"], sc["f_rest"], sc["f_stir"]
STUDIO = eval(sc["replay"]); f_x0 = eval(sc["swig"])[-1]
LIE = [(280, T_IMP - 1), (f_rest + 10, f_stir)]
prev_soles = {}
stats = dict(frames=0, pen_train=0, pen_people=0, pen_hat=0)
near_objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name in ("Loco", "Wagon1", "Wagon2", "Platform", "Ramp", "Lad.body", "WitA.body", "WitB.body", "Worker.body", "Plough")]
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); stats["frames"] += 1
    in_studio = f_x0 <= f <= STUDIO[3]
    # ---- feet
    for n, sh in shoes.items():
        if sh.hide_render or in_studio: continue
        ev = sh.evaluated_get(dg); me = ev.to_mesh(); mw = sh.matrix_world
        pts = [mw @ v.co for v in list(me.vertices)[::3]]; ev.to_mesh_clear()
        # split left/right by side of the rig's root
        for side in "LR":
            ank = people[n].matrix_world @ people[n].pose.bones["foot." + side].head
            sp = [p for p in pts if (p - ank).length < 0.25]
            if not sp: continue
            low = min(sp, key=lambda p: p.z - ground_z(p.x, p.y))
            gap = low.z - ground_z(low.x, low.y)
            key = (n, side); moving = key in prev_soles and (ank - prev_soles[key]).length > 0.01 * STEP
            prev_soles[key] = ank.copy()
            if gap < -0.03: flag("FOOT_SINK", f, "%s %s %.1f cm under" % (n, side, -gap * 100))
            elif gap > 0.03 and not moving and not (n == "Lad" and T_IMP <= f <= f_stir + 60): flag("FOOT_HOVER", f, "%s %s %.1f cm above while planted" % (n, side, gap * 100))
        # hands
        for side in "LR":
            w = people[n].matrix_world @ people[n].pose.bones["wrist." + side].head
            d = ground_z(w.x, w.y) - w.z
            if d > 0.04: flag("HAND_BURIED", f, "%s %s wrist %.1f cm under" % (n, side, d * 100))
    # ---- lying body
    if any(a <= f <= b for a, b in LIE):
        bt, vs = world_tree(bodies["Lad"], dg)
        gaps = [v.z - ground_z(v.x, v.y) for v in vs[::5]]
        lo = min(gaps)
        if lo > 0.03: flag("BODY_HOVER", f, "lowest point %.1f cm above" % (lo * 100))
        if lo < -0.06: flag("BODY_SINK", f, "%.1f cm below" % (-lo * 100))
        if f < T_IMP:
            near_rail = [v for v in vs if abs(v.x - GAUGE) < 0.036 and abs(v.y) < 0.15 and v.z < 0.45]
            if near_rail:
                g = min(v.z for v in near_rail) - RAIL_H
                if abs(g) > 0.02: flag("HEAD_ON_RAIL", f, "head %.1f cm %s the railhead" % (abs(g) * 100, "above" if g > 0 else "into"))
            else: flag("HEAD_ON_RAIL", f, "no head contact over the railhead")
    # ---- Lad vs train
    if not bodies["Lad"].hide_render and not train[0].hide_render and f >= T_IMP - 30:
        lt, _ = world_tree(bodies["Lad"], dg)
        for o in train:
            ot, _ = world_tree(o, dg)
            ov = lt.overlap(ot)
            if ov: stats["pen_train"] += 1; flag("PEN_TRAIN", f, "Lad x %s: %d tri pairs" % (o.name, len(ov)))
    # ---- people vs people
    vis_p = [n for n in people if not bodies[n].hide_render]
    trees = {n: world_tree(bodies[n], dg)[0] for n in vis_p}
    for i, a in enumerate(vis_p):
        for b in vis_p[i + 1:]:
            ov = trees[a].overlap(trees[b])
            if ov: stats["pen_people"] += 1; flag("PEN_PEOPLE", f, "%s x %s: %d" % (a, b, len(ov)))
    if not hat.hide_render:
        ht, _ = world_tree(hat, dg)
        for c in (bodies["Worker"], part(people["Worker"], ".short01")):
            if c is None: continue
            ov = ht.overlap(world_tree(c, dg)[0])
            if ov: stats["pen_hat"] += 1; flag("PEN_HAT", f, "hat x %s: %d" % (c.name, len(ov)))
    if not bottle.hide_render:
        bw = bottle.matrix_world
        lo = min((bw @ Vector(c)).z - ground_z((bw @ Vector(c)).x, (bw @ Vector(c)).y) for c in bottle.bound_box)
        if lo < -0.02: flag("PEN_PROP", f, "bottle %.1f cm into the ground" % (-lo * 100))
    # ---- camera
    cp = cam.matrix_world.translation
    if not in_studio and cp.z < ground_z(cp.x, cp.y) + 0.04: flag("CAMERA_INSIDE", f, "camera %.1f cm above ground" % ((cp.z - ground_z(cp.x, cp.y)) * 100))
    for o in near_objs:
        if o.hide_render: continue
        t, _ = world_tree(o, dg)
        loc, nrm, idx, dist = t.find_nearest(cp)
        if dist is not None and dist < 0.03: flag("CAMERA_INSIDE", f, "camera %.1f cm from %s" % (dist * 100, o.name))
        # inside a closed mesh: odd number of hits on a ray going up
        n_hit = 0; p0 = cp.copy()
        for _ in range(20):
            hit = t.ray_cast(p0, Vector((0.0013, 0.0007, 1.0)))
            if hit[0] is None: break
            n_hit += 1; p0 = hit[0] + Vector((0, 0, 1e-4))
        if n_hit % 2 == 1 and o.name in ("Platform", "Ramp", "Loco", "Wagon1", "Wagon2"): flag("CAMERA_INSIDE", f, "camera inside %s" % o.name)
with open(OUT, "w") as fh:
    fh.write("DrunkTrain audit, every %d frames (%d frames sampled)\n" % (STEP, stats["frames"]))
    fh.write("penetration counts (frames with overlap): Lad-train %d, people-people %d, hat-head %d\n\n" % (stats["pen_train"], stats["pen_people"], stats["pen_hat"]))
    for k in sorted(issues):
        fh.write("%s: %d\n" % (k, len(issues[k])))
        for f, m in issues[k][:40]: fh.write("   f%d  %s\n" % (f, m))
print(open(OUT).read())
