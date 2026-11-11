"""v003 hand-tuning after pipeline/anim_look.py (client look change, Nov 11 22:45):
bright readable blue night cabin, sky-blue studio gradient, clean stylised putty, warm-but-bright dusk, brighter airport.
blender -b film_anim.blend --python 06_v003_look.py -- <out.blend>"""
import sys, bpy
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects; M = bpy.data.materials
def lin(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)
# studio cyclorama: cyan #4FC3F7 top -> near-white #E8F7FF bottom, softly self-lit
cm = M["CycGradient"]; nt = cm.node_tree
rp = [n for n in nt.nodes if n.type == 'VALTORGB'][0]
els = rp.color_ramp.elements
while len(els) > 2: els.remove(els[1])
els[0].position = 0.0; els[0].color = lin("#E8F7FF")
els[1].position = 0.6; els[1].color = lin("#4FC3F7")
nt.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.55
O["StudioCyanRim"].data.color = (0.75, 0.95, 1.0)
# putty: clean, smooth, stylised mid grey
pm = M["Putty"]; b = pm.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.28, 0.29, 0.31, 1); b.inputs["Roughness"].default_value = 0.5
for n in pm.node_tree.nodes:
    if n.type == 'BUMP': n.inputs["Strength"].default_value = 0.05
for o in O:
    if o.name.startswith("Slab_"):
        for md in o.modifiers:
            if md.type == 'DISPLACE': md.strength = 0.0015
# cabin: readable blue night, brighter fill, faces lit
for o in O:
    if o.type == 'LIGHT' and o.name.startswith("CabinFill_"): o.data.energy = 22.0; o.data.color = (0.6, 0.72, 1.0)
    if o.type == 'LIGHT' and o.name.startswith("ReadingPool_"): o.data.energy = 30.0
O["KeyFaceAisle"].data.energy = 14.0
O["GalleyWarm"].data.energy = 30.0
M["CoveGlow"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0
M["CabinWall"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.78, 0.8, 0.84, 1)
M["WindowNight"].node_tree.nodes["Emission"].inputs["Strength"].default_value = 4.0
# stylised flame: brighter, saturated core
for m in M:
    if m.name.startswith("Flame_"):
        e = [n for n in m.node_tree.nodes if n.type == 'EMISSION'][0]
        e.inputs["Color"].default_value = (1.0, 0.45, 0.05, 1); e.inputs["Strength"].default_value = 40
# smoke: light, stylised wisps
sm = M.get("Smoke")
if sm:
    for n in sm.node_tree.nodes:
        if n.type == 'VOLUME_PRINCIPLED': n.inputs["Color"].default_value = (0.85, 0.87, 0.92, 1); n.inputs["Density"].default_value = 0.25
# exposure per set: bright but no blowout
ad = sc.animation_data
for layer in ad.action.layers:
    for st in layer.strips:
        for cb in st.channelbags:
            for fc in cb.fcurves:
                if fc.data_path == "view_settings.exposure":
                    for kp in fc.keyframe_points:
                        f = kp.co.x
                        kp.co.y = 0.9 if f < 1069 else (0.0 if f < 1249 else (0.35 if f < 1393 else -0.4))
                        kp.handle_left.y = kp.handle_right.y = kp.co.y
                    fc.update()
# airport: lift the terminal (clean, bright)
for o in O:
    if o.type == 'LIGHT' and o.name.startswith("TerminalSky_"): o.data.energy = 420
M["CeilingWhite"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.82, 0.85, 1)
# no film blur on the farm either
sc.render.use_motion_blur = False
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("V003_LOOK_SAVED", OUT)
