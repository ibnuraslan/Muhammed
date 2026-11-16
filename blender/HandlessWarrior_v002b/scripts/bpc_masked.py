"""Run pipeline/body_prop_cross.py on what actually renders for the warrior: body_prop_cross disables MASK modifiers
(to keep vertex order for its labels), which would re-add the hands our HandsOff mask removes. This wrapper deletes the
masked vertices (HandsOff, Hide helpers, clothes delete groups) from the warrior body in memory first (the file on disk is not changed), then runs the check.
blender -b film.blend --python bpc_masked.py -- <pipeline dir> <f0> <f1> out.json STEP Props [Rigs]"""
import bpy, bmesh, sys, os
a = sys.argv[sys.argv.index("--") + 1:]
PIPE, f0, f1 = a[0], int(a[1]), int(a[2])
body = next(c for c in bpy.data.objects["Warrior"].children if c.name.endswith("body"))
bm = bmesh.new(); bm.from_mesh(body.data); dl = bm.verts.layers.deform.active
kill = set()
for m in body.modifiers:          # apply every Mask modifier's effect (HandsOff, Hide helpers, clothes delete groups)
    if m.type != 'MASK' or not m.vertex_group or m.vertex_group not in body.vertex_groups: continue
    gi = body.vertex_groups[m.vertex_group].index
    for v in bm.verts:
        inside = gi in v[dl] and v[dl][gi] > m.threshold
        if inside == m.invert_vertex_group: kill.add(v)
bmesh.ops.delete(bm, geom=list(kill), context='VERTS'); bm.to_mesh(body.data); bm.free()
for m in body.modifiers:
    if m.type == 'MASK': m.show_viewport = False; m.show_render = False
print("MASKED VERTS REMOVED", len(kill))
sc = bpy.context.scene; sc.frame_start, sc.frame_end = f0, f1
sys.argv = sys.argv[:sys.argv.index("--") + 1] + a[3:]
exec(open(os.path.join(PIPE, "body_prop_cross.py")).read())
