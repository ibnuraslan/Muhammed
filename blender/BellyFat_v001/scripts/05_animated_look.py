"""v005 animated-CG look, applied after pipeline/anim_look.py (client direction 22:45 UTC).
blender -b in.blend --python 05_animated_look.py -- out.blend"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
M = bpy.data.materials
def bsdf(m): return m.node_tree.nodes.get("Principled BSDF")
def set_col(name, rgb, rough=None, coat=None, sss=None):
    m = M.get(name)
    if not m: return
    b = bsdf(m)
    bc = b.inputs["Base Color"]
    # follow the colour chain to its source mix (noise multiply / layer weight) and recolour the flat inputs
    def recolour(sock):
        if not sock.is_linked:
            sock.default_value = (*rgb, 1); return
        n = sock.links[0].from_node
        for nm in ("A", "Color1", "Color"):
            s = n.inputs.get(nm)
            if s is not None and s.type == 'RGBA':
                recolour(s); return
    recolour(bc)
    if rough is not None: b.inputs["Roughness"].default_value = rough
    if coat is not None: b.inputs["Coat Weight"].default_value = coat
    if sss is not None: b.inputs["Subsurface Weight"].default_value = sss
# explainer layers: peach skin, yellow-orange lumpy fat, red-pink muscle, glossy clean bowel
set_col("M_skin_epi", (1.0, 0.62, 0.45), 0.4, 0.3, 0.2)
set_col("M_dermis", (1.0, 0.5, 0.45), 0.4, 0.3, 0.2)
set_col("M_fat_lobule", (1.0, 0.45, 0.03), 0.35, 0.6, 0.25)
set_col("M_septa", (1.0, 0.8, 0.55), 0.4, 0.4)
set_col("M_fascia", (0.98, 0.92, 0.88), 0.4, 0.4)
set_col("M_muscle", (0.85, 0.12, 0.18), 0.4, 0.5, 0.15)
set_col("M_peritoneum", (1.0, 0.82, 0.82), 0.35, 0.6)
set_col("M_mesentery", (1.0, 0.62, 0.62), 0.4, 0.5)
set_col("M_cavity", (0.95, 0.6, 0.65), 0.6)
set_col("M_hole", (0.55, 0.05, 0.06), 0.5)
set_col("M_vessel_red", (0.9, 0.05, 0.08), 0.35)
set_col("M_vessel_blue", (0.1, 0.3, 0.95), 0.35)
# fat: less white septa rim, cleaner yellow-orange
fm = M.get("M_fat_lobule")
for n in fm.node_tree.nodes:
    if n.type == 'MIX' and n.inputs["B"].type == 'RGBA' and tuple(n.inputs["B"].default_value)[:3] == (0.96, 0.86, 0.66):
        n.inputs["B"].default_value = (1.0, 0.85, 0.45, 1)
# bowel serosa: clean glossy pink with red vessels
sm = M.get("M_serosa")
if sm:
    for n in sm.node_tree.nodes:
        if n.type == 'MIX' and n.data_type == 'RGBA':
            a = tuple(n.inputs["A"].default_value)[:3]
            if a == (0.30, 0.10, 0.11) or abs(a[0] - 0.30) < 1e-3:
                n.inputs["A"].default_value = (0.88, 0.36, 0.42, 1); n.inputs["B"].default_value = (0.97, 0.5, 0.55, 1)
    b = bsdf(sm); b.inputs["Roughness"].default_value = 0.35; b.inputs["Subsurface Weight"].default_value = 0.15
# studio dome: bright sky gradient (#E8F7FF bottom -> #4FC3F7 top), brighter
dm = M.get("M_dome")
for n in dm.node_tree.nodes:
    if n.type == 'VALTORGB':
        n.color_ramp.elements[0].color = (0.80, 0.93, 1.0, 1); n.color_ramp.elements[1].color = (0.08, 0.55, 0.93, 1)
        n.color_ramp.elements[0].position = 0.0; n.color_ramp.elements[1].position = 1.0
    if n.type == 'MAP_RANGE':
        n.inputs["From Min"].default_value = -18; n.inputs["From Max"].default_value = 18
    if n.type == 'EMISSION': n.inputs["Strength"].default_value = 1.0
# energy rings: bright stylised impact glow
rm = M.get("M_ring")
for n in rm.node_tree.nodes:
    if n.type == 'EMISSION': n.inputs["Color"].default_value = (1.0, 0.85, 0.3, 1)
# camera: f-stop keys >= 5.6 except true macro (stored >= 8 there already)
cam = bpy.data.objects["CAM_Film"]
ad = cam.data.animation_data
if ad and ad.action:
    for lay in ad.action.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == "dof.aperture_fstop":
                        for k in fc.keyframe_points: k.co.y = max(5.6, k.co.y)
                        fc.update()
sc = bpy.context.scene
sc.view_settings.exposure = -0.3
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("V005 saved", out)
