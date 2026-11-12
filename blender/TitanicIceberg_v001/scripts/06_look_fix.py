"""After pipeline/anim_look.py (--no-sky): restore the few things the generic pass should not touch.
blender -b look.blend --python 06_look_fix.py -- <out.blend>"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
sea = bpy.data.materials["M_Sea"].node_tree.nodes["Principled BSDF"]
for n in bpy.data.materials["M_Sea"].node_tree.nodes:
    if n.type == 'BSDF_PRINCIPLED' and n.name == "Principled BSDF":
        for l in list(n.inputs['Roughness'].links): bpy.data.materials["M_Sea"].node_tree.links.remove(l)
        n.inputs['Roughness'].default_value = 0.07
for m in ("M_Developer", "M_PortGlow"):
    if m in bpy.data.materials:
        for n in bpy.data.materials[m].node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                for l in list(n.inputs['Roughness'].links): bpy.data.materials[m].node_tree.links.remove(l)
                n.inputs['Roughness'].default_value = 0.05
# no prints/logos on clothes: MakeHuman casual shirts carry a chest print -> solid colour
for ob in bpy.data.objects:
    if ob.type == 'MESH' and "casualsuit" in ob.name:
        for m in ob.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    for l in list(n.inputs['Base Color'].links): m.node_tree.links.remove(l)
                    n.inputs['Base Color'].default_value = (0.09, 0.16, 0.36, 1); n.inputs['Roughness'].default_value = 0.85
            print("PATCHED print-free", ob.name, m.name)
bpy.context.scene.render.use_motion_blur = False
bpy.ops.wm.save_as_mainfile(filepath=out)
print("LOOKFIX done")
