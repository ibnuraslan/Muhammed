"""Contact / penetration audit for Tsunami2004.
blender -b film.blend --python audit.py -- <report.txt> [step]
Checks (sampled every <step> frames while each person is visible):
  FOOT_HOVER / FOOT_SINK   lowest shoe point > 3 cm above / below the ground while the foot is planted
  FOOT_SLIDE               planted foot moving > 1.5 cm between samples
  HAND_BODY                hand triangles intersecting the same person's torso/legs (BVH overlap)
  HAND_PROP / FOOT_PROP    hand or foot triangles intersecting scene props (boats, fish, rocks, furniture, other people)
  PERSON_PERSON            two people's bodies intersecting
  HAND_FLOAT               holding the fish: palm more than 4 cm from the fish surface
  CAMERA_UNDER_GROUND / CAMERA_UNDER_WATER / CAMERA_INSIDE
"""
import sys, math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
exec(open("/home/user/Muhammed/blender/Tsunami2004_v001/scripts/lib.py").read())
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 else 6
sc = bpy.context.scene
issues = {}; counts = {}
def flag(kind, f, msg):
    issues.setdefault(kind, []).append((f, msg))
rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.children]
def part(rig, key):
    return [c for c in rig.children if c.type == 'MESH' and key in c.name]
HAND_GROUPS = ("wrist", "finger", "metacarpal")
def vgroup_mask(ob, keys, thr=0.5):
    names = {g.index: g.name for g in ob.vertex_groups}
    m = np.zeros(len(ob.data.vertices), bool)
    for v in ob.data.vertices:
        w = sum(g.weight for g in v.groups if any(k in names[g.group] for k in keys))
        m[v.index] = w > thr
    return m
masks = {}
for r in rigs:
    body = part(r, ".body")[0]
    masks[r.name] = (vgroup_mask(body, HAND_GROUPS), vgroup_mask(body, ("spine", "pelvis", "upperleg", "breast")))
terr = bpy.data.objects["Terrain"]
PROP_PREFIX = ("Longtail_", "Rowboat_", "Fish_", "Rock_", "Coral_", "Lounger_", "Umbrella_", "Car_", "Palm_")
def mesh_world(ob, dg):
    ev = ob.evaluated_get(dg); me = ev.to_mesh()
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
    tris = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear(); return co, tris
def wbvh(ob, dg):
    co, tris = mesh_world(ob, dg)
    return BVHTree.FromPolygons([tuple(c) for c in co], tris)
from bpy_extras.object_utils import world_to_camera_view
def in_view(p):
    v = world_to_camera_view(sc, cam, p)
    return 0 <= v.x <= 1 and -0.1 <= v.y <= 1.1 and 0 < v.z < 80
def sub_bvh(co, tris, mask):
    keep = [t for t in tris if all(mask[i] for i in t)]
    return BVHTree.FromPolygons([tuple(c) for c in co], keep) if keep else None
prev_feet = {}
TERR = BVHTree.FromObject(terr, bpy.context.evaluated_depsgraph_get())
cam = sc.camera
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    t = (f - 1) / 60.0
    # ---------------- camera
    cp = cam.matrix_world.translation
    gz = terrain_h(cp.x, cp.y)
    if cp.z < gz + 0.15 and not (12.9 < t < 15.7):
        flag("CAMERA_UNDER_GROUND", f, "camera %.2f m above ground" % (cp.z - gz))
    if not (12.9 < t < 15.7):
        for wn in ("SeaPlane", "Wave"):
            w = bpy.data.objects[wn]
            if w.hide_render: continue
            tree = wbvh(w, dg)
            hit = tree.ray_cast(Vector((cp.x, cp.y, cp.z)), Vector((0, 0, 1)))
            if hit[0] is not None and hit[3] < 60:
                # under the surface only if the face we hit faces up (we are below its top side)
                if hit[1].z > 0.2:
                    flag("CAMERA_UNDER_WATER", f, "%s surface %.2f m above camera" % (wn, hit[3]))
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render or o.name in ("Terrain", "DeepFloor", "SeaPlane", "Wave", "WaveSpray", "DustVolume", "StudioBowl"): continue
        if (o.matrix_world.translation - cp).length > 30: continue
        if o.name.startswith(("D_",)) and not (12.9 < t < 15.7): continue
        if o.name.startswith("LIB_"): continue
        try: tree = wbvh(o, dg)
        except Exception: continue
        n_in = 0
        for d in (Vector((0, 0, 1)), Vector((1, 0, 0)), Vector((0, 1, 0))):
            hit = tree.ray_cast(cp, d, 200)
            if hit[0] is not None and hit[1].dot(d) > 0: n_in += 1
        if n_in >= 2:
            flag("CAMERA_INSIDE", f, o.name)
    # ---------------- people
    live = [r for r in rigs if not part(r, ".body")[0].hide_render and in_view(r.matrix_world @ r.pose.bones["root"].head)]
    if not live: continue
    props = [o for o in bpy.data.objects if o.name.startswith(PROP_PREFIX) and not o.hide_render and o.type == 'MESH']
    bodies = {}
    for r in live:
        body = part(r, ".body")[0]; co, tris = mesh_world(body, dg)
        root = r.matrix_world @ r.pose.bones["root"].head
        bodies[r.name] = (co, tris, root)
    for r in live:
        co, tris, root = bodies[r.name]; hm, tm = masks[r.name]
        # feet
        for s in "LR":
            shoe = [c for c in r.children if c.type == 'MESH' and "shoes" in c.name][0]
            sco, _ = mesh_world(shoe, dg)
            fb = r.matrix_world @ r.pose.bones["foot." + s].head
            side = sco[(sco[:, 0] - fb.x) ** 2 + (sco[:, 1] - fb.y) ** 2 < 0.2 ** 2]
            if not len(side): continue
            low = side[:, 2].min(); lx, ly = side[side[:, 2].argmin()][:2]
            key = (r.name, s); planted = False
            g = terrain_h(lx, ly)
            hit = TERR.ray_cast(Vector((lx, ly, 50)), Vector((0, 0, -1)))
            if hit[0] is not None: g = hit[0].z
            on_ground = low - g < 0.012
            if key in prev_feet:
                pf, pg = prev_feet[key]
                planted = (fb - pf).length < 0.03 * STEP / 2
                # a slide = the foot stays on the ground at both samples yet moves sideways
                if on_ground and pg and 0.015 < (Vector((fb.x, fb.y)) - pf.to_2d()).length < 0.15:
                    sc.frame_set(f - STEP // 2); dg2 = bpy.context.evaluated_depsgraph_get()
                    mid, _ = mesh_world(shoe, dg2); fm = r.matrix_world @ r.pose.bones["foot." + s].head
                    ms_ = mid[(mid[:, 0] - fm.x) ** 2 + (mid[:, 1] - fm.y) ** 2 < 0.2 ** 2]
                    g2 = terrain_h(fm.x, fm.y)
                    if len(ms_) and ms_[:, 2].min() - g2 < 0.02:
                        flag("FOOT_SLIDE", f, "%s %s %.1f cm" % (r.name, s, (Vector((fb.x, fb.y)) - pf.to_2d()).length * 100))
                    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
            prev_feet[key] = (fb.copy(), on_ground)
            if planted and low - g > 0.03: flag("FOOT_HOVER", f, "%s %s %.1f cm" % (r.name, s, (low - g) * 100))
            if low - g < -0.03: flag("FOOT_SINK", f, "%s %s %.1f cm" % (r.name, s, (g - low) * 100))
        hb = sub_bvh(co, tris, hm); tb = sub_bvh(co, tris, tm)
        if hb and tb:
            ov = hb.overlap(tb)
            if len(ov) > 3: flag("HAND_BODY", f, "%s %d tri pairs" % (r.name, len(ov)))
        for o in props:
            if (o.matrix_world.translation - root).length > 8: continue
            try: pt = wbvh(o, dg)
            except Exception: continue
            if hb:
                ov = hb.overlap(pt)
                if len(ov) > 2 and not (o.name == "Fish_00" and len(ov) < 25): flag("HAND_PROP", f, "%s x %s %d" % (r.name, o.name, len(ov)))
        for r2 in live:
            if r2.name <= r.name: continue
            co2, tris2, root2 = bodies[r2.name]
            if (root2 - root).length > 1.6: continue
            ov = BVHTree.FromPolygons([tuple(c) for c in co], tris).overlap(BVHTree.FromPolygons([tuple(c) for c in co2], tris2))
            if len(ov) > 3: flag("PERSON_PERSON", f, "%s x %s %d" % (r.name, r2.name, len(ov)))
    # fish in hand
    fisher = bpy.data.objects["Fisher"]
    if F(6.95) <= f <= F(9.0):
        fish = bpy.data.objects["Fish_00"]; ft = wbvh(fish, dg)
        palm = fisher.matrix_world @ fisher.pose.bones["finger3-1.R"].head
        loc, nrm, idx, dist = ft.find_nearest(palm)
        if dist is None or dist > 0.04: flag("HAND_FLOAT", f, "palm %.1f cm from fish" % ((dist or 9) * 100))
with open(OUT, "w") as fh:
    fh.write("Tsunami2004 audit, step %d frames\n" % STEP)
    total = 0
    for k in ("FOOT_HOVER", "FOOT_SINK", "FOOT_SLIDE", "HAND_BODY", "HAND_PROP", "PERSON_PERSON", "HAND_FLOAT", "CAMERA_UNDER_GROUND", "CAMERA_UNDER_WATER", "CAMERA_INSIDE"):
        v = issues.get(k, []); total += len(v)
        fh.write("%-20s %4d\n" % (k, len(v)))
        for f, m in v[:25]: fh.write("    f%4d (%.2fs) %s\n" % (f, (f - 1) / 60, m))
    fh.write("TOTAL %d\n" % total)
print(open(OUT).read())
