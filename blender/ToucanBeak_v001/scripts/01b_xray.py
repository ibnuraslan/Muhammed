"""X-ray film of the broken beak for the clinic lightbox (rendered from the real bird meshes, orthographic side view).
blender -b work/bird.blend -P 01b_xray.py -- assets/xray_beak.png"""
import bpy, sys
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; OB = bpy.data.objects
for o in OB:
    if o.type == 'MESH':
        o.hide_render = o.name not in ("Toucan_body", "Toucan_beak_upper_broken", "Toucan_beak_lower", "Toucan_eyeskin.L")
m = bpy.data.materials.new("xr"); m.use_nodes = True; nt = m.node_tree
for n in list(nt.nodes):
    if n.type == 'BSDF_PRINCIPLED': nt.nodes.remove(n)
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.85
em = nt.nodes.new("ShaderNodeEmission"); mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.35
nt.links.new(lw.outputs["Fresnel"], mul.inputs[0]); nt.links.new(mul.outputs[0], em.inputs["Strength"]); em.inputs[0].default_value = (0.85, 0.95, 1.0, 1)
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); ad = nt.nodes.new("ShaderNodeAddShader")
nt.links.new(em.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes["Material Output"].inputs[0])
for o in OB:
    if o.type == 'MESH' and not o.hide_render:
        o.modifiers.clear() if o.name != "Toucan_body" else None
        for i in range(len(o.data.materials)): o.data.materials[i] = m
        o.particle_systems and None
for o in OB:
    for ms in [x for x in o.modifiers if x.type == 'PARTICLE_SYSTEM']: o.modifiers.remove(ms)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.01, 0.025, 1)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.32; cam.location = (0.5, 0.06, 0.2); cam.rotation_euler = (1.5708, 0, 1.5708)
sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.render.resolution_x = 640; sc.render.resolution_y = 480
sc.view_settings.view_transform = 'Standard'; sc.render.filepath = out; sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True); print("XRAY", out)
