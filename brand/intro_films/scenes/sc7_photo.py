"""The photograph that develops in intro 7: the official Seldom art painted on a brick wall, shot at night under
one street lamp. Rendered once to assets/seldom_sign_photo.png (3:2), then printed onto the paper in sc7_darkroom.py."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
C.reset()
import bpy
from mathutils import Vector
import ship
import intro_common as I

sc = I.setup(spp=int(os.environ.get("SPP", "96")))
sc.render.resolution_x, sc.render.resolution_y = 1800, 1200
brick = I.tex("red_brick_03" if False else "brick_wall_001", 0.9, name="brick", fallback=(0.35, 0.12, 0.08))
wall = ship.box("wall", (0, 0.1, 2.0), (9, 0.2, 5), brick)
# sign-writer's paint on brick: the art follows the brick relief (displacement of the same texture's bump is
# inherited through the shading normal); a matte layer with weathered flakes
paint = bpy.data.materials.new("sign_paint"); paint.use_nodes = True
N = paint.node_tree.nodes; L = paint.node_tree.links; p = N["Principled BSDF"]
p.inputs["Roughness"].default_value = 0.7
im = I.logo_layer(paint, kind="paint", wear=0.2)
tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
L.new(im.outputs["Alpha"], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(p.outputs[0], mx.inputs[2])
L.new(mx.outputs[0], N["Material Output"].inputs["Surface"])
bn = N.new("ShaderNodeTexBrick"); bn.inputs["Scale"].default_value = 4.0
bb = N.new("ShaderNodeBump"); bb.inputs["Strength"].default_value = 0.4; bb.invert = True
L.new(bn.outputs["Fac"], bb.inputs["Height"]); L.new(bb.outputs[0], p.inputs["Normal"])
I.logo_card("sign", (0, -0.003, 2.3), 3.4, paint, rot=(math.radians(90), 0, 0), thick=0)
# pavement, a drainpipe, a wet gutter
pave = I.tex("brick_pavement_02" if False else "brick_pavement", 1.0, name="pave", fallback=(0.15, 0.15, 0.15), rough=0.3)
ship.box("pavement", (0, -2.5, -0.05), (12, 5.2, 0.1), pave)
iron = I.principled("pipe", (0.04, 0.05, 0.05), 0.4, 0.6)
ship.cyl("drainpipe", (-2.6, -0.06, 0), (-2.6, -0.06, 4.5), 0.05, mat=iron, verts=16)
# street lamp off frame right, warm sodium; a cool spill from the far street
I.spot("streetlamp", (3.2, -2.2, 4.6), (0.2, 0, 2.2), 1500, (1.0, 0.78, 0.5), size_deg=70, blend=0.8, radius=0.1)
I.area("skyglow", (-4, -6, 5), (0, 0, 1.5), 60, (0.45, 0.55, 0.85), 4)
w = bpy.context.scene.world or bpy.data.worlds.new("World"); bpy.context.scene.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.02, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1
I.haze((0, -3, 2.5), (12, 8, 5), density=0.01, color=(0.9, 0.85, 0.8))
C.camera(Vector((-1.1, -6.2, 1.7)), Vector((0.05, 0, 2.25)), lens=42)
C.finish(os.path.join(C.HERE, "..", "assets", "seldom_sign_photo.png"), cine={"exposure": 0.0, "sat": 1.3})
