import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
out = sys.argv[sys.argv.index("--")+1]; spp = int(sys.argv[sys.argv.index("--")+2])
reset(samples=spp)
world((0,0,0), 0)
# a rusted cast-iron sign bolted to an old brick wall; the logo plate is the only shape the flame finds
brick = bpy.data.materials.new("Brick"); brick.use_nodes=True; nt=brick.node_tree; p=nt.nodes["Principled BSDF"]
bt = nt.nodes.new("ShaderNodeTexBrick"); bt.inputs["Scale"].default_value = 16; bt.inputs["Color1"].default_value=(0.18,0.06,0.03,1); bt.inputs["Color2"].default_value=(0.1,0.04,0.025,1); bt.inputs["Mortar"].default_value=(0.06,0.055,0.05,1)
nt.links.new(bt.outputs["Color"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value=0.9
bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value=0.5; nt.links.new(bt.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], p.inputs["Normal"])
plane("Wall", 8, (0, 0.2, 0), (math.radians(90),0,0), brick)
rust = noise_bump(color_noise(mat("Rust", rough=0.7, metal=0.3), (0.62,0.8,0.02,1), (0.35,0.3,0.05,1), 12), 25, 0.4)
lg = logo(width=2.4, depth=0.06, loc=(0, 0.17, 0.05), fill_mat=rust, edge_mat=noise_bump(mat("E",(0.02,0.018,0.015,1),0.5,0.6),30,0.3))
# the match: stick + head + flame + a thin curl of smoke
cyl("Stick", 0.006, 0.42, (0.55, -0.55, -0.55), mat("Wd",(0.5,0.35,0.15,1),0.8), rot=(math.radians(-15),math.radians(12),0), verts=8)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=(0.505, -0.5, -0.345)); bpy.context.active_object.data.materials.append(mat("Head",(0.05,0.01,0.01,1),0.6))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(0.502, -0.505, -0.30)); fl=bpy.context.active_object; fl.scale=(1,1,2.4)
fl.data.materials.append(mat("Flame",(1,0.6,0.2,1),0.5, emit=(1.0,0.55,0.15,1), estr=60)); bpy.ops.object.shade_smooth()
light('POINT', "FlameL", (0.502, -0.52, -0.28), energy=40, color=(1.0,0.55,0.2), size=0.03)
fog("Smoke", (0.25, 0.25, 1.6), (0.47, -0.5, 0.55), density=0.35, color=(0.8,0.75,0.7), aniso=0.4, noise=6)
fog("Air", (6, 4, 4), (0, -1, 0), density=0.01, color=(1,0.9,0.8))
camera((0.05, -4.3, -0.25), (0.12, 0, 0.05), lens=36, fstop=2.2, focus=3.8)
render(out)
