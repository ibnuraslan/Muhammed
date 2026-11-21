"""v012 clothing fixes.
 1. The new outfits' MPFB "Delete" vertex groups (body skin under the clothes) are copied from build_clothes.py's bodies (same
    topology) with their MASK modifiers, so no skin pokes through the blouse, skirt or T-shirt.
 2. Man's T-shirt: the asset texture has a logo -> the shirt region (vertices not dominated by pelvis/leg bones) gets a plain
    sage-green colour; the jeans keep their texture. In the hospital bed (1478-1586) the shirt region becomes a pale blue checked
    hospital gown (keyed mix).
 3. A blanket over him from the waist down while he is in the bed (1478-1586).
blender -b film.blend --python clothes_fix.py -- newclothes.blend out.blend"""
import bpy, sys, bmesh
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; SRC, OUT = a[0], a[1]; sc = bpy.context.scene
with bpy.data.libraries.load(SRC, link=False) as (fr, to): to.objects = ["NEW_Man_Body", "NEW_Mom_Body"]
for nb in to.objects:
    nm = nb.name.split("_")[1]; fb = bpy.data.objects[nm + "_Body"]
    for g in [g for g in nb.vertex_groups if g.name.startswith("Delete")]:
        ng = fb.vertex_groups.get(g.name) or fb.vertex_groups.new(name=g.name)
        idx = [v.index for v in nb.data.vertices if any(x.group == g.index and x.weight > 0.5 for x in v.groups)]
        ng.add(idx, 1.0, "REPLACE")
        md = fb.modifiers.new(g.name, "MASK"); md.vertex_group = g.name; md.invert_vertex_group = True
        # keep the mask before the subdivision modifier
        while fb.modifiers.find(md.name) > 0 and fb.modifiers[fb.modifiers.find(md.name) - 1].type == "SUBSURF":
            bpy.ops.object.modifier_move_up({"object": fb}, modifier=md.name) if False else fb.modifiers.move(fb.modifiers.find(md.name), fb.modifiers.find(md.name) - 1)
        print("DELETE", nm, g.name, len(idx))
    bpy.data.objects.remove(nb, do_unlink=True)
# 2. T-shirt region attribute + material
M = bpy.data.objects["Man"]; tee = bpy.data.objects["Man_male_casualsuit06"]
gi = {g.index: g.name for g in tee.vertex_groups}
LEG = ("pelvis", "upperleg", "lowerleg", "foot", "toe")
vals = []
for v in tee.data.vertices:
    g = max(v.groups, key=lambda g: g.weight, default=None); n = gi.get(g.group, "") if g else ""
    vals.append(0.0 if n.startswith(LEG) else 1.0)
at = tee.data.attributes.get("shirt") or tee.data.attributes.new("shirt", "FLOAT", "POINT"); at.data.foreach_set("value", vals)
mat = tee.data.materials[0]; nt = mat.node_tree; P = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bl = [l for l in nt.links if l.to_node == P and l.to_socket.name == "Base Color"][0]; src = bl.from_socket; nt.links.remove(bl)
att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_name = "shirt"
tee_col = nt.nodes.new("ShaderNodeRGB"); tee_col.outputs[0].default_value = (0.32, 0.42, 0.30, 1)          # sage green T-shirt
chk = nt.nodes.new("ShaderNodeTexChecker"); chk.inputs["Scale"].default_value = 60.0
chk.inputs["Color1"].default_value = (0.62, 0.74, 0.86, 1); chk.inputs["Color2"].default_value = (0.78, 0.86, 0.93, 1)   # gown
gown = nt.nodes.new("ShaderNodeValue"); gown.name = "GownMix"
for f, v in ((1, 0.0), (1477, 0.0), (1478, 1.0), (1586, 1.0), (1587, 0.0)):
    gown.outputs[0].default_value = v; gown.outputs[0].keyframe_insert("default_value", frame=f)
ad = nt.animation_data
if ad and ad.action:
    for l in ad.action.layers:
        for st in l.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for k in fc.keyframe_points: k.interpolation = "CONSTANT"
m1 = nt.nodes.new("ShaderNodeMix"); m1.data_type = "RGBA"; nt.links.new(gown.outputs[0], m1.inputs["Factor"]); nt.links.new(tee_col.outputs[0], m1.inputs[6]); nt.links.new(chk.outputs["Color"], m1.inputs[7])
m2 = nt.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; nt.links.new(att.outputs["Fac"], m2.inputs["Factor"]); nt.links.new(src, m2.inputs[6]); nt.links.new(m1.outputs[2], m2.inputs[7])
nt.links.new(m2.outputs[2], P.inputs["Base Color"])
print("TEE shirt verts", int(sum(vals)), "of", len(vals))
# 3. blanket
sc.frame_set(1500)
pel = M.matrix_world @ M.pose.bones["pelvis.L"].head; ft = (M.matrix_world @ M.pose.bones["foot.L"].head + M.matrix_world @ M.pose.bones["foot.R"].head) / 2
mt = bpy.data.objects["BR_Mattress"]; bb = [mt.matrix_world @ Vector(c) for c in mt.bound_box]
x0, x1 = min(v.x for v in bb), max(v.x for v in bb); top = max(v.z for v in bb)
y_a, y_b = sorted((pel.y + (0.05 if ft.y < pel.y else -0.05), ft.y + (-0.12 if ft.y < pel.y else 0.12)))
bm_ = bmesh.new(); bmesh.ops.create_cube(bm_, size=1.0)
me = bpy.data.meshes.new("Blanket"); bm_.to_mesh(me); bm_.free()
bk = bpy.data.objects.new("BR_Blanket", me); sc.collection.objects.link(bk)
bk.scale = ((x1 - x0) + 0.08, (y_b - y_a), 0.16); bk.location = ((x0 + x1) / 2, (y_a + y_b) / 2, top + 0.03)
bv = bk.modifiers.new("bevel", "BEVEL"); bv.width = 0.06; bv.segments = 4; ss = bk.modifiers.new("sub", "SUBSURF"); ss.levels = 2; ss.render_levels = 2
bm2 = bpy.data.materials.new("M_Blanket"); bm2.use_nodes = True; pb = bm2.node_tree.nodes["Principled BSDF"]
pb.inputs["Base Color"].default_value = (0.55, 0.68, 0.80, 1); pb.inputs["Roughness"].default_value = 0.9
try: pb.inputs["Sheen Weight"].default_value = 0.4
except Exception: pass
me.materials.append(bm2)
for f, h in ((1, True), (1478, False), (1587, True)):
    bk.hide_render = h; bk.keyframe_insert("hide_render", frame=f); bk.hide_viewport = h; bk.keyframe_insert("hide_viewport", frame=f)
print("BLANKET", [round(x, 2) for x in bk.location], [round(x, 2) for x in bk.scale], "pelvis", [round(x, 2) for x in pel], "feet", [round(x, 2) for x in ft])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
