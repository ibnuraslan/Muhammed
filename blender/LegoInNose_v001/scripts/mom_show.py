"""v008f: limb_check PROPHEAD: the brick in the tweezer tips (and a tweezer arm) went into MOM's own face while she held them up
to show (1065-1075). Mom's right IK hand, the tweezers and the brick are pushed away from her head (horizontal, head -> brick),
every frame 1058-1084, until no brick/tweezer vertex is inside her head mesh and the brick is >= 2 cm off it.
blender -b in.blend --python mom_show.py -- out.blend"""
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
M = bpy.data.objects["Mom"]; MB = bpy.data.objects["Mom_Body"]
masks = [(m, m.show_viewport) for m in MB.modifiers if m.type in ("MASK", "SUBSURF", "MULTIRES")]
for m, _ in masks: m.show_viewport = False
gi = {g.index: g.name for g in MB.vertex_groups if g.name in M.data.bones}; dom = []
for v in MB.data.vertices:
    g = max((g for g in v.groups if g.group in gi), key=lambda g: g.weight, default=None); dom.append(gi[g.group].lower() if g else "")
HEAD = ("head", "neck", "jaw", "eye", "ear", "nose", "lip", "cheek", "brow", "temporal", "tongue", "levator", "oris", "risorius", "special", "orbicularis")
PR = [bpy.data.objects["Brick_Big"]] + [o for o in bpy.data.objects if o.name.startswith("Prop_TweezerArm")]
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if o.animation_data and o.animation_data.action else []
def shift(o, path, f, d):
    for fc in [c for c in fcs(o) if c.data_path == path]: fc.keyframe_points.insert(f, fc.evaluate(f) + d[fc.array_index], options={"FAST"})
for rnd in range(8):
    hits = []
    for f in range(1058, 1085):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        e = MB.evaluated_get(dg); me = e.to_mesh(); V = [e.matrix_world @ v.co for v in me.vertices]
        T = BVHTree.FromPolygons(V, [tuple(p.vertices) for p in me.polygons if all(dom[i].startswith(HEAD) for i in p.vertices)]); e.to_mesh_clear()
        worst = 0.0
        for o in PR:
            if o.hide_render: continue
            eo = o.evaluated_get(dg); mo = eo.to_mesh()
            for v in mo.vertices:
                p = eo.matrix_world @ v.co; loc, n, _, d = T.find_nearest(p, 0.2)
                if loc is None: continue
                sd = d if (p - loc).dot(n) >= 0 else -d
                need = (0.02 - sd) if o.name == "Brick_Big" else (0.005 - sd)
                worst = max(worst, need)
            eo.to_mesh_clear()
        if worst > 0:
            hc = M.matrix_world @ M.pose.bones["head"].head; b = bpy.data.objects["Brick_Big"].matrix_world.translation
            dirn = b - hc; dirn.z = 0; dirn.normalize(); hits.append((f, dirn * (worst + 0.01)))
    print("MOMSHOW round", rnd, "frames", len(hits), [f for f, _ in hits][:20])
    if not hits: break
    for f, d in hits:
        n = "IK_hand.R"; dl = M.data.bones[n].matrix_local.to_3x3().inverted() @ (M.matrix_world.to_3x3().inverted() @ d)
        shift(M, 'pose.bones["%s"].location' % n, f, dl)
        shift(bpy.data.objects["Prop_Tweezers"], "location", f, d); shift(bpy.data.objects["Brick_Big"], "location", f, d)
    for o in (M, bpy.data.objects["Prop_Tweezers"], bpy.data.objects["Brick_Big"]):
        for fc in fcs(o): fc.update()
for m, v in masks: m.show_viewport = v
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("MOMSHOW saved", OUT)
