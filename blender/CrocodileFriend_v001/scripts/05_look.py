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
# --- catchlights: a tiny light near every shot camera, light-linked to the eyes only (no glints on the water)
EYES = bpy.data.collections.new("CatchlightReceivers")
for o in OB:
    if o.type == 'MESH' and ("high-poly" in o.name): EYES.objects.link(o)
for c in [o for o in OB if o.name.startswith("CAM_")]:
    l = bpy.data.objects.new("Catch_" + c.name, bpy.data.lights.new("Catch_" + c.name, 'POINT')); sc.collection.objects.link(l)
    l.data.energy = 6.0; l.data.shadow_soft_size = 0.05; l.parent = c; l.location = (0.15, 0.25, 0.0)
    l.visible_diffuse = False; l.visible_glossy = True
    l.light_linking.receiver_collection = EYES
# --- render settings (the farm renders these)
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps = 60; sc.render.use_motion_blur = False
for c in [o for o in OB if o.name.startswith("CAM_")]:
    c.data.dof.use_dof = False
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("LOOK done", "decal", ok)

# --- director P1 checklist (Nov 16): real hair on everyone, two-tone loose clothes in contrasting colours (no one-piece / beige)
def two_tone(rig, top, bottom, split=0.60):
    for ch in rig.children:
        if ch.type != 'MESH' or "suit" not in ch.name: continue
        for i, m in enumerate(ch.data.materials):
            if not m: continue
            m2 = m.copy(); ch.data.materials[i] = m2; nt = m2.node_tree
            b = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
            for l in list(b.inputs["Base Color"].links): nt.links.remove(l)
            tc = nt.nodes.new("ShaderNodeTexCoord"); sz = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sz.inputs[0])
            mr = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(sz.outputs["Z"], mr.inputs[0])
            mr.inputs[1].default_value = split - 0.01; mr.inputs[2].default_value = split + 0.01
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; nt.links.new(mr.outputs[0], mx.inputs[0])
            mx.inputs[6].default_value = bottom + (1,); mx.inputs[7].default_value = top + (1,)
            nt.links.new(mx.outputs[2], b.inputs["Base Color"])
for ch in OB["Keeper"].children:
    if "short02" in ch.name: ch.hide_render = ch.hide_viewport = False
two_tone(OB["Keeper"], (0.62, 0.10, 0.08), (0.10, 0.09, 0.08))          # teal-blue shirt, dark brown trousers
PAL = [((0.70, 0.12, 0.12), (0.10, 0.12, 0.25)), ((0.95, 0.75, 0.10), (0.15, 0.25, 0.45)), ((0.12, 0.45, 0.20), (0.25, 0.22, 0.20)),
       ((0.45, 0.18, 0.55), (0.12, 0.12, 0.14)), ((0.90, 0.45, 0.10), (0.20, 0.30, 0.20)), ((0.10, 0.30, 0.70), (0.55, 0.50, 0.42)),
       ((0.80, 0.20, 0.40), (0.15, 0.15, 0.30))]
FUN = {"Crowd1", "Crowd2", "Crowd3", "Crowd4"}
for i, n in enumerate(sorted(o.name for o in OB if o.type == 'ARMATURE' and o.name not in ("Keeper", "Croc"))):
    top, bot = PAL[i % len(PAL)]
    if n in FUN or n in ("SpecB", "SpecE"): top, bot = (top[0] * 0.45, top[1] * 0.45, top[2] * 0.45), (0.06, 0.06, 0.08)   # sober funeral colours
    two_tone(OB[n], top, bot)
# water: dark green-brown with sharp reflections (anim_look raised roughness / saturation on it)
w = bpy.data.materials["Water"]; b = [n for n in w.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
for l in list(b.inputs["Base Color"].links): w.node_tree.links.remove(l)
b.inputs["Base Color"].default_value = (0.045, 0.085, 0.05, 1); b.inputs["Roughness"].default_value = 0.04
b.inputs["Specular IOR Level"].default_value = 0.35; b.inputs["Alpha"].default_value = 0.92
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("LOOK2 done")
