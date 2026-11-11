"""v004 hand fixes after pipeline/anim_look.py (bright clean 3D-animation look).
blender -b anim_look.blend --python scripts/04_anim_look_fixes.py -- out.blend"""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
SKY_TOP = (0.08, 0.55, 0.93, 1); SKY_BOT = (0.80, 0.93, 1.0, 1)
# x-ray void (local Y ramp: low = top colour, high = bottom) -> sky gradient
vn = bpy.data.materials["M_XR_Void"].node_tree
cr = next(n for n in vn.nodes if n.type == "VALTORGB")
cr.color_ramp.elements[0].color = SKY_BOT; cr.color_ramp.elements[1].color = SKY_TOP
mr = next(n for n in vn.nodes if n.type == "MAP_RANGE"); mr.inputs["From Min"].default_value = -0.4; mr.inputs["From Max"].default_value = 0.4
next(n for n in vn.nodes if n.type == "EMISSION").inputs["Strength"].default_value = 1.35
bm = bpy.data.materials.get("Bone")
if bm:
    pb = next(n for n in bm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    pb.inputs["Emission Color"].default_value = (1.0, 0.92, 0.75, 1); pb.inputs["Emission Strength"].default_value = 1.6
# glow behind the frosted partition
gn = bpy.data.materials["M_CyanGlow"].node_tree
g = next(n for n in gn.nodes if n.type == "VALTORGB")
g.color_ramp.elements[0].color = SKY_TOP; g.color_ramp.elements[1].color = SKY_BOT
# brighter, cleaner room: lighter floor + walls, brighter ceiling panels and fills
def tint(mat, rgb):
    nt = bpy.data.materials[mat].node_tree
    mx = next((n for n in nt.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY"), None)
    if mx: mx.inputs["B"].default_value = rgb
for m, rgb in (("M_Floor", (1.25, 1.22, 1.15, 1)), ("M_WallTiles", (0.82, 0.96, 0.92, 1))):
    if bpy.data.materials.get(m): tint(m, rgb)
for m in bpy.data.materials:
    if m.name.startswith("M_Floor") and m.name != "M_Floor": tint(m.name, (1.25, 1.22, 1.15, 1))
for o in bpy.data.objects:
    if o.type == "LIGHT" and o.name.startswith(("Fill_", "Rim_")): o.data.energy *= 1.6
# exposure: keep the story dim at the end, but never dark (was -0.9)
fc = None
ad = sc.animation_data
if ad and ad.action:
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for f in cb.fcurves:
                    if f.data_path == "view_settings.exposure":
                        for kp in f.keyframe_points:
                            if kp.co.y < -0.3: kp.co.y = -0.35; kp.handle_left.y = kp.handle_right.y = -0.35
print("FIXES done", sc.view_settings.look)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
