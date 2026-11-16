"""Look pass after pipeline/anim_look.py: portrait painting, logo on the crate, easel, camera catchlights, render settings.
blender -b work/look_base.blend -P 05_look.py -- work/look.blend"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = sys.argv[-1]
sc = bpy.context.scene; OB = bpy.data.objects; HX = 45.0
# --- portrait: frame on the easel, our own painting (man + croc, no text)
img = bpy.data.images.load(os.path.join(HERE, "assets", "portrait.png"))
fr = OB["PortraitFrame"]
for m in fr.data.materials:
    if m and ("aiStandard" in m.name):
        nt = m.node_tree; b = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
        for l in list(b.inputs["Base Color"].links): nt.links.remove(l)
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; nt.links.new(t.outputs[0], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.6
        if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value = 0.0
fr.location = (HX + 1.2, 2.82, 0.78); fr.rotation_euler = (math.radians(-6), 0, 0)
# easel: plain wood everywhere (its stock canvas had a red smear picture)
ea = OB["Easel"]; wood = bpy.data.materials.new("EaselWood"); wood.use_nodes = True
wood.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.36, 0.2, 1)
wood.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
for i in range(len(ea.data.materials)): ea.data.materials[i] = wood
# --- logo decal on the crate's -Y side (placement 1)
cr = OB["Crate"]; bb = [cr.matrix_world @ Vector(c) for c in cr.bound_box]
mn = Vector([min(p[i] for p in bb) for i in range(3)]); mx = Vector([max(p[i] for p in bb) for i in range(3)])
m = bpy.data.materials.new("LogoCrate"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(HERE, "..", "assets", "brand", "DaKrasFilms_logo_white.png"))
t.extension = 'CLIP'; L.new(t.outputs["Color"], b.inputs["Base Color"]); L.new(t.outputs["Alpha"], b.inputs["Alpha"])
b.inputs["Roughness"].default_value = 0.7
w = (mx.x - mn.x) * 0.85
bpy.ops.mesh.primitive_plane_add(size=1); d = bpy.context.object; d.name = "LogoCrate_Decal"
d.scale = (w, w * 414 / 967, 1); bpy.ops.object.transform_apply(scale=True); d.data.materials.append(m)
d.rotation_euler = (math.radians(90), 0, 0)
# put the decal 4 mm off the crate face that looks toward -Y (crate is yawed: use its local frame)
cy = cr.matrix_world.to_3x3() @ Vector((0, -1, 0))
ctr = (mn + mx) / 2
d.location = ctr; d.rotation_euler = (math.radians(90), 0, cr.rotation_euler.z)
# find the face by ray cast from outside
dg = bpy.context.evaluated_depsgraph_get()
o0 = ctr + cy * 2.0; inv = cr.matrix_world.inverted()
ok, loc, nrm, idx = cr.evaluated_get(dg).ray_cast(inv @ o0, (inv.to_3x3() @ -cy).normalized())
if ok: d.location = cr.matrix_world @ loc + cy * 0.004
d.parent = cr; d.matrix_parent_inverse = cr.matrix_world.inverted()
# --- catchlights: a tiny light near every shot camera (eyes read white/iris/pupil)
for c in [o for o in OB if o.name.startswith("CAM_")]:
    l = bpy.data.objects.new("Catch_" + c.name, bpy.data.lights.new("Catch_" + c.name, 'POINT')); sc.collection.objects.link(l)
    l.data.energy = 6.0; l.data.shadow_soft_size = 0.05; l.parent = c; l.location = (0.15, 0.25, 0.0)
    l.visible_diffuse = False; l.visible_glossy = True
# --- render settings (the farm renders these)
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps = 60; sc.render.use_motion_blur = False
for c in [o for o in OB if o.name.startswith("CAM_")]:
    c.data.dof.use_dof = False
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("LOOK done", "decal", ok)
