"""Automated contact / penetration audit for the goat rescue film.
blender -b gr_anim.blend --python audit.py -- <report.txt> [step]

Checks (sampled every <step> frames):
  FARMER_HOVER   lying frames: lowest body point more than 2 cm above the heap surface
  FARMER_DEEP    more than 60 % of body samples below the surface (sunk too far)
  HAND_BURIED    wrist more than 5 cm under the surface
  HOOF_SINK/FLOAT goat/cow hooves > 2.5 cm into / > 3 cm above the surface while planted
  PROP_FLOAT/SINK bottle, pitchfork, clods resting off the surface
  BED_PENETRATION farmer vertices inside the hospital bed
  CAMERA_INSIDE  camera below the surface or inside an object
"""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 else 10
sc = bpy.context.scene
F = bpy.data.objects["Farmer"]; G = bpy.data.objects["goat_rig"]; C = bpy.data.objects["cow_rig"]
heap = bpy.data.objects["ManureHeap"]
issues = {}
def flag(kind, f, msg):
    issues.setdefault(kind, []).append((f, msg))

def bvh(obj, dg):
    return BVHTree.FromObject(obj, dg)

def surface(tree, x, y):
    hit = tree.ray_cast(Vector((x, y, 8.0)), Vector((0, 0, -1)))
    z = hit[0].z if hit[0] is not None else -1.0
    return max(0.0, z)

body_parts = [o for o in F.children if o.type == 'MESH' and o.name.split(".")[-1] in ("body", "male_worksuit01", "shoes03")]
props = [o for o in bpy.data.objects if o.name in ("MilkBottle", "Pitchfork") or o.name.startswith("Clod_")]
LYING = (100, 2010)
bed = bpy.data.objects.get("Hospital_Bed")
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ht = bvh(heap, dg)
    # ---------------- farmer vs heap
    if LYING[0] <= f <= LYING[1]:
        pts = []
        for o in body_parts:
            ev = o.evaluated_get(dg); me = ev.to_mesh()
            mw = o.matrix_world
            pts += [mw @ v.co for v in list(me.vertices)[::6]]
            ev.to_mesh_clear()
        below = 0; gaps = []
        for p in pts:
            sz = surface(ht, p.x, p.y)
            if p.z < sz: below += 1
            gaps.append(p.z - sz)
        frac = below / max(1, len(pts))
        lowest = min(gaps)
        if lowest > 0.02:
            flag("FARMER_HOVER", f, "lowest body point %.1f cm above surface" % (lowest * 100))
        if frac > 0.60:
            flag("FARMER_DEEP", f, "%.0f%% of body below surface" % (frac * 100))
        for s in "LR":
            w = F.matrix_world @ F.pose.bones["wrist." + s].head
            d = surface(ht, w.x, w.y) - w.z
            if d > 0.05:
                flag("HAND_BURIED", f, "%s hand %.1f cm under the surface" % (s, d * 100))
    # ---------------- hooves
    for rig, rng in ((G, (1, 2149)), (C, (1, 230))):
        if not (rng[0] <= f <= rng[1]):
            continue
        for k in ("FL", "FR", "HL", "HR"):
            pb = rig.pose.bones["hoof." + k]
            tip = rig.matrix_world @ pb.tail; heel = rig.matrix_world @ pb.head
            low = min(tip.z, heel.z - 0.09 * (rig.dimensions.z / 1.0 if rig is G else 1.0))
            sz = surface(ht, tip.x, tip.y)
            if sz - tip.z > 0.025:
                flag("HOOF_SINK", f, "%s %s %.1f cm into the surface" % (rig.name, k, (sz - tip.z) * 100))
            elif tip.z - sz > 0.03:
                # only report when the hoof is not mid-swing: compare with next frame
                sc.frame_set(min(f + 1, sc.frame_end)); t2 = rig.matrix_world @ rig.pose.bones["hoof." + k].tail; sc.frame_set(f)
                if (t2 - tip).length < 0.004:
                    flag("HOOF_FLOAT", f, "%s %s %.1f cm above the surface while planted" % (rig.name, k, (tip.z - sz) * 100))
    # ---------------- props
    for o in props:
        if o.hide_render or f > 2149:
            continue
        ev = o.evaluated_get(dg)
        if ev.type != 'MESH':
            continue
        me = ev.to_mesh(); mw = o.matrix_world
        ps = [mw @ v.co for v in me.vertices]
        ev.to_mesh_clear()
        lowp = min(ps, key=lambda p: p.z)
        sz = surface(ht, lowp.x, lowp.y)
        moving = False
        if o.animation_data:
            sc.frame_set(min(f + 1, sc.frame_end)); moving = (o.matrix_world.translation - mw.translation).length > 0.003; sc.frame_set(f)
        con = any(c.influence > 0.5 for c in getattr(o, "constraints", []) if c.type == 'CHILD_OF')
        if not moving and not con:
            if lowp.z - sz > 0.03:
                flag("PROP_FLOAT", f, "%s %.1f cm above the surface" % (o.name, (lowp.z - sz) * 100))
            if sz - lowp.z > 0.05 and not o.name.startswith("Clod_"):
                flag("PROP_SINK", f, "%s %.1f cm into the surface" % (o.name, (sz - lowp.z) * 100))
    # ---------------- bed
    if bed and f >= 2150:
        bt = bvh(bed, dg)
        inside = 0; total = 0
        for o in body_parts:
            ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
            for v in list(me.vertices)[::5]:
                p = mw @ v.co; total += 1
                loc, nrm, idx, dist = bt.find_nearest(p)
                if loc is not None and dist < 0.15 and (p - loc).dot(nrm) < -0.005:
                    inside += 1
            ev.to_mesh_clear()
        if inside > 0.01 * total:
            flag("BED_PENETRATION", f, "%d of %d body samples inside the bed" % (inside, total))
    # ---------------- camera
    cam = sc.camera
    if cam:
        cp = cam.matrix_world.translation
        if cp.x < 30 and cp.z < surface(ht, cp.x, cp.y) + 0.05:
            flag("CAMERA_INSIDE", f, "camera below/at the heap or ground surface")
        for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and o.visible_get()]:
            if o.name.startswith(("Ground", "Clod_", "Grass")) or o.name == "ManureHeap":
                continue
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            mn = Vector([min(p[i] for p in bb) for i in range(3)]); mx = Vector([max(p[i] for p in bb) for i in range(3)])
            if all(mn[i] - 0.02 <= cp[i] <= mx[i] + 0.02 for i in range(3)) and o.name.startswith(("Ambulance", "Barn", "Hospital_Bed", "Hosp_Wall", "Fence", "Hay")):
                flag("CAMERA_INSIDE", f, "camera inside the bounds of %s" % o.name)

def ranges(items):
    fr = sorted(set(f for f, _ in items)); out = []; start = prev = None
    for f in fr:
        if start is None: start = prev = f
        elif f - prev <= STEP: prev = f
        else: out.append((start, prev)); start = prev = f
    if start is not None: out.append((start, prev))
    return out
lines = ["AUDIT (step %d frames, 60 fps)" % STEP]
for kind in sorted(issues):
    its = issues[kind]
    lines.append("%-16s %4d samples | ranges (s): %s" % (kind, len(its), ", ".join("%.1f-%.1f" % ((a - 1) / 60, (b - 1) / 60) for a, b in ranges(its))))
    worst = its[:3]
    for f, m in worst:
        lines.append("      e.g. f%d (%.2fs): %s" % (f, (f - 1) / 60, m))
if not issues:
    lines.append("no issues found")
open(OUT, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
