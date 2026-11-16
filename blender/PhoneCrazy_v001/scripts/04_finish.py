"""After anim_look: water and screen surfaces keep their own values. blender -b work/look.blend -P 04_finish.py -- work/p1.blend"""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
m = bpy.data.materials["PitWater"]; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
P.inputs["Roughness"].default_value = 0.06; P.inputs["Specular IOR Level"].default_value = 0.12
cr = next(n for n in nt.nodes if n.type == "VALTORGB"); cr.color_ramp.elements[0].color = (0.006, 0.03, 0.045, 1); cr.color_ramp.elements[1].color = (0.03, 0.11, 0.14, 1)
next(n for n in nt.nodes if n.type == "BUMP").inputs["Strength"].default_value = 0.5
w = bpy.data.materials["Whirlpool"].node_tree.nodes["Principled BSDF"]; w.inputs["Roughness"].default_value = 0.3
s = bpy.data.materials["Stream"].node_tree.nodes["Principled BSDF"]; s.inputs["Roughness"].default_value = 0.1
bpy.context.scene.cycles.samples = 48
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("FINISH OK")
