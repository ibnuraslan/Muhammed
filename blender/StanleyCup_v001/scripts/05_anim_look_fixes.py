"""After pipeline/anim_look.py: hand fixes for StanleyCup's animated look (v004).
blender -b look.blend --python 05_anim_look_fixes.py -- <out.blend>"""
import sys, bpy
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
def fcurves(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action: return []
    return [fc for l in ad.action.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
# 1) animated f-stop: keyed values override the tool's clamp. Min 5.6, true macro (impact, condensation) may go to 4.
cam = bpy.data.cameras["CAM_Film"]
for fc in fcurves(cam):
    if "aperture_fstop" in fc.data_path:
        for kp in fc.keyframe_points:
            macro = 955 <= kp.co.x <= 1000 or 690 <= kp.co.x <= 710
            kp.co.y = max(kp.co.y, 4.0 if macro else 5.6); kp.handle_left.y = max(kp.handle_left.y, kp.co.y * 0.9); kp.handle_right.y = max(kp.handle_right.y, kp.co.y * 0.9)
        fc.update()
# 2) bright daytime instead of dusk: white-warm sun, higher; street lamps/porch light off-ish; no dusk orange
sun = bpy.data.lights.get("SunDusk")
if sun:
    sun.color = (1.0, 0.95, 0.88); sun.energy = 3.2; sun.angle = 0.06
    bpy.data.objects["SunDusk"].rotation_euler = (0.85, 0.0, -2.1)
for L in bpy.data.lights:
    if L.name.startswith("StreetLamp"):
        ad = L.animation_data
        if ad: L.animation_data_clear()
        L.energy = 0.0
m = bpy.data.materials.get("M_StreetGlow")
if m:
    m.node_tree.animation_data_clear() if m.node_tree.animation_data else None
    m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.0
# warm window glow toned down for daylight
mw = bpy.data.materials.get("M_WarmWindow")
if mw: mw.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.4
# 3) exposure keys: street and room both bright and clean
ad = sc.animation_data
if ad and ad.action:
    for fc in fcurves(sc):
        if "exposure" in fc.data_path:
            for kp in fc.keyframe_points:
                kp.co.y = 0.25 if kp.co.x < 160 else -0.05
                kp.handle_left.y = kp.handle_right.y = kp.co.y
            fc.update()
# 4) interior fill: lift shadows (soft, even)
for n, e in (("CeilingFill", 1.35), ("KeyFace", 1.3), ("WallWash", 1.3)):
    L = bpy.data.lights.get(n)
    if L: L.energy *= e
# 5) cutaway x-ray: brighter clean cyan; sparks hot orange-white but not blowing out
xr = bpy.data.materials["M_Powdercoat"].node_tree.nodes
for n in xr:
    if n.type == "EMISSION": n.inputs[0].default_value = (0.31, 0.76, 0.97, 1); n.inputs[1].default_value = 1.2
sp = bpy.data.materials.get("M_Spark")
if sp: sp.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 7.0
# 6) wall cavity read as clean illustration: lighter studs/OSB tones
for nm, col in (("M_OSB", (0.78, 0.6, 0.36, 1)), ("M_Stud", (0.9, 0.74, 0.5, 1)), ("M_Insulation", (1.0, 0.62, 0.7, 1))):
    mm = bpy.data.materials.get(nm)
    if mm: mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = col
cav = bpy.data.lights.get("CavityFill")
if cav and cav.animation_data:
    for fc in fcurves(cav):
        for kp in fc.keyframe_points: kp.co.y *= 4.0; kp.handle_left.y *= 4.0; kp.handle_right.y *= 4.0
# 7) clean painted walls/ceiling instead of the gritty plaster scan
mp = bpy.data.materials.get("M_Plaster")
if mp:
    b = mp.node_tree.nodes["Principled BSDF"]
    for l in list(b.inputs["Base Color"].links): mp.node_tree.links.remove(l)
    b.inputs["Base Color"].default_value = (0.74, 0.84, 0.92, 1); b.inputs["Roughness"].default_value = 0.6
    for n in mp.node_tree.nodes:
        if n.type == "NORMAL_MAP": n.inputs["Strength"].default_value = 0.08
sc["anim_look_fixes"] = "v004"
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("FIXES_DONE", OUT)
