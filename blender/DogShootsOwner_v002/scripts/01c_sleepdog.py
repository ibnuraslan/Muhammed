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
    # uniform golden-lab coat: the scan's luminance only drives a narrow golden->cream ramp (no dark patches)
    bw = nt.nodes.new('ShaderNodeRGBToBW')
    rp = nt.nodes.new('ShaderNodeValToRGB')
    rp.color_ramp.elements[0].position = 0.0; rp.color_ramp.elements[0].color = (0.86, 0.48, 0.15, 1)
    rp.color_ramp.elements[1].position = 1.0; rp.color_ramp.elements[1].color = (1.0, 0.74, 0.38, 1)
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.10; mr.inputs['From Max'].default_value = 0.65
    nt.links.new(tex.outputs['Color'], bw.inputs[0]); nt.links.new(bw.outputs[0], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], P.inputs['Base Color'])
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
