"""Third library pass (director P1c notes): a real curled sleeping-dog scan (Sketchfab CC-BY "Sleeping dog 01" by thuberchs),
cut from its ground with extract (see scratch extract_dog.py), recoloured golden to match the Labrador, softened (no scan grit).
blender -b lib2.blend --python 01c_sleepdog.py -- <sleepdog.blend> <out_lib.blend>"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
with bpy.data.libraries.load(a[0]) as (src, dst):
    dst.objects = ["SleepDog"]
o = dst.objects[0]; bpy.data.collections["PROPS"].objects.link(o)
for m in o.data.materials:
    if not m or not m.node_tree: continue
    nt = m.node_tree
    tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
    tname = tex.name
    for n in list(nt.nodes):
        if n.name != tname: nt.nodes.remove(n)
    tex = nt.nodes[tname]
    out = nt.nodes.new('ShaderNodeOutputMaterial'); P = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(P.outputs[0], out.inputs['Surface'])
    hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
    gm = nt.nodes.new('ShaderNodeGamma'); gm.inputs[1].default_value = 0.78      # lift the baked shadows
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs['B'].default_value = (1.0, 0.60, 0.26, 1)
    nt.links.new(tex.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs[0], gm.inputs[0])
    nt.links.new(gm.outputs[0], mx.inputs['A']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    P.inputs['Roughness'].default_value = 0.7
    if 'Specular IOR Level' in P.inputs: P.inputs['Specular IOR Level'].default_value = 0.25
for img in bpy.data.images:
    if img.filepath and not img.packed_file:
        try: img.pack()
        except Exception: pass
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
bpy.ops.object.shade_smooth()
o.location = (0, 0, -60); o.hide_render = o.hide_viewport = True
bpy.ops.wm.save_as_mainfile(filepath=a[1]); print("LIB3_OK", tuple(round(v, 3) for v in o.dimensions))
