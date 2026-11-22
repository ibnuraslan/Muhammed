import sys, os
sys.path.insert(0, "/home/user/Muhammed/seldom_intro_p4/lib")
import si; si.C.reset()
import bpy, p4
from mathutils import Vector
sc = si.C.render_setup(samples=16, noise=0.1, bounces=4); sc.render.resolution_percentage = 25
cands = []
for hue in (0.0, 0.04, 0.08):
    for sat in (1.0, 1.3):
        for val in (1.0, 0.7, 0.45):
            cands.append((hue, sat, val))
for i, (hu, sa, va) in enumerate(cands):
    m = bpy.data.materials.new(f"c{i}"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = (0.768, 1.0, 0.0, 1)
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Hue"].default_value = 0.5 + hu; hs.inputs["Saturation"].default_value = sa; hs.inputs["Value"].default_value = va
    nt.links.new(rgb.outputs[0], hs.inputs["Color"]); nt.links.new(hs.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.4
    x = (i % 6) * 0.25 - 0.625; y = (i // 6) * 0.25 - 0.25
    bpy.ops.mesh.primitive_plane_add(size=0.22, location=(x, y, 0)); bpy.context.active_object.data.materials.append(m)
p4.world_color((0.02, 0.02, 0.02))
p4.light('AREA', "k", 10, (1, 0.97, 0.92), loc=(0.3, -0.4, 0.8), target=(0, 0, 0), size=0.8)
si.cam((0, 0, 1.9), (0, 0.001, 0), lens=35)
sc.render.filepath = sys.argv[-1]
import grade as G; G.add_grade(sc, bloom=0.3, look="cinematic", cine={"sat": 1.08})
bpy.ops.render.render(write_still=True)
