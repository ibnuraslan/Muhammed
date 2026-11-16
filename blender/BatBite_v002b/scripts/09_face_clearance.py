"""Bat-to-face clearance on the packed film, every frame of a range (director: bite tip 6-8 mm off the lips,
nothing touches the face on the way in). Face = Singer.body polygons weighted to the head bone tree, posed by the
armature only (no subdivision, so the measured surface is slightly OUTSIDE the rendered one: real clearance >= this).
blender -b BatBite_v002b_60fps.blend --python 09_face_clearance.py -- out.txt F0 F1"""
import bpy, sys
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, F0, F1 = a[0], int(a[1]), int(a[2])
sc = bpy.context.scene
body = bpy.data.objects["Singer.body"]; bat = bpy.data.objects["Bat"]; arm = body.find_armature().data.bones
hair = bpy.data.objects.get("Singer.long01")
headb = {b.name for b in arm if b.name == "head" or any(p.name == "head" for p in b.parent_recursive)}
gn = {g.index: g.name for g in body.vertex_groups}
def is_head(v):
    gs = [g for g in v.groups if gn[g.group] in arm and g.weight > 0]
    return bool(gs) and gn[max(gs, key=lambda g: g.weight).group] in headb
HV = {v.index for v in body.data.vertices if is_head(v)}
HP = [list(p.vertices) for p in body.data.polygons if all(i in HV for i in p.vertices)]
for m in body.modifiers:
    if m.type != 'ARMATURE': m.show_viewport = False
rows = []
for f in range(F0, F1 + 1):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    e = body.evaluated_get(dg); me = e.to_mesh(); vs = [body.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
    t = BVHTree.FromPolygons(vs, HP)
    eb = bat.evaluated_get(dg); mb = eb.to_mesh(); pts = [bat.matrix_world @ v.co for v in mb.vertices]; eb.to_mesh_clear()
    d = min(t.find_nearest(p)[3] for p in pts)
    rows.append((f, d * 1000))
with open(OUT, "w") as fo:
    fo.write("frame  bat-to-face clearance (mm)\n")
    for f, d in rows: fo.write(f"{f:5d}  {d:6.1f}\n")
    lo = min(rows, key=lambda r: r[1]); fo.write(f"MIN {lo[1]:.1f} mm at frame {lo[0]}\n")
print("FACECLEAR min", min(rows, key=lambda r: r[1]))
