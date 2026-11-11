"""After pipeline/anim_look.py: fix keyframed values it can't reach and brighten the prison (bright, clean 3D animation look).
blender -b work/film_anim0.blend --python scripts/06_animlook_fix.py -- work/film_anim.blend"""
import sys, bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; OB = bpy.data.objects
def fcs(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    out = []
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out.extend(cb.fcurves)
    return out
def scale_keys(idb, path_sub, k, floor=None):
    for fc in fcs(idb):
        if path_sub in fc.data_path:
            for kp in fc.keyframe_points:
                kp.co.y *= k; kp.handle_left.y *= k; kp.handle_right.y *= k
                if floor is not None and kp.co.y < floor: kp.co.y = floor
            fc.update()
# camera f-stop: >= 5.6, macro moments (lens >= 45) >= 4
cam = sc.camera.data
lensf = next((fc for fc in fcs(cam) if fc.data_path == "lens"), None)
for fc in fcs(cam):
    if "aperture_fstop" in fc.data_path:
        for kp in fc.keyframe_points:
            lens = lensf.evaluate(kp.co.x) if lensf else 24
            kp.co.y = max(kp.co.y, 4.0 if lens >= 45 else 5.6); kp.handle_left.y = kp.handle_right.y = kp.co.y
        fc.update()
# lights: keyed energies x1.25 for sun/area/spot (anim_look only scaled static values); interiors much brighter
for L in bpy.data.lights:
    if L.type in ("SUN", "AREA", "SPOT"): scale_keys(L, "energy", 1.25)
BOOST = {"L_Candle": 1.8, "L_CellFill": 4.0, "L_Window": 2.0, "L_DoorFill": 1.8, "L_CorrLantern0": 2.0, "L_CorrLantern1": 2.0,
         "L_ShopLamp0": 1.6, "L_ShopLamp1": 1.6, "L_PassingLantern": 1.5, "L_PatrolLantern": 1.5, "L_YardLamp0": 1.5, "L_YardLamp1": 1.5, "L_YardLamp2": 1.5}
for n, k in BOOST.items():
    if n in OB:
        L = OB[n].data; L.energy *= k; scale_keys(L, "energy", k)
fill = OB["L_CellFill"].data; fill.shadow_soft_size = 1.2
# soft bounce lights: cell, corridor, foundry (high-key interiors)
def bounce(name, loc, size, energy, color, rot=(0, 0, 0)):
    L = bpy.data.lights.new(name, 'AREA'); L.shape = 'RECTANGLE'; L.size = size[0]; L.size_y = size[1]; L.energy = energy; L.color = color
    o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    return L
bounce("L_CellBounce", (0.0, 0.0, 2.95), (3.6, 3.6), 260, (1.0, 0.93, 0.85))
bounce("L_CorrBounce", (5.3, 0.0, 2.75), (5.5, 1.6), 220, (1.0, 0.92, 0.82))
bounce("L_ShopBounce", (17.0, 6.0, 3.9), (7.0, 7.0), 520, (1.0, 0.9, 0.78))
# night stays readable: a cool fill in the cell at night, faces lit
nf = bounce("L_CellNightFill", (0.6, -1.4, 2.2), (1.5, 1.0), 0, (0.55, 0.7, 1.0))
o = OB["L_CellNightFill"]; o.rotation_euler = (Vector((1.2, 0.8, 1.2)) - o.location).to_track_quat('-Z', 'Y').to_euler()
for f, e in ((1, 0), (860, 0), (880, 90), (1700, 90), (1730, 0)):
    nf.energy = e; nf.keyframe_insert("energy", frame=f)
# world: keyed background strength x1.6; camera sky gradient dims to readable blue at night
w = sc.world; nt = w.node_tree
scale_keys(w.node_tree, "Strength", 1.6)
skyb = [n for n in nt.nodes if n.type == 'BACKGROUND' and n.inputs['Color'].is_linked and n.inputs['Color'].links[0].from_node.type == 'VALTORGB']
for sb in skyb:
    for f, v in ((1, 1.0), (845, 1.0), (868, 0.3), (1728, 0.3), (1760, 1.0)):
        sb.inputs['Strength'].default_value = v; sb.inputs['Strength'].keyframe_insert("default_value", frame=f)
# exposure: brighter overall (day 0.55, night 1.2, final day 0.25)
for fc in fcs(sc):
    if fc.data_path == "view_settings.exposure":
        for kp in fc.keyframe_points:
            v = kp.co.y; kp.co.y = 0.9 if v > 0.5 else (0.55 if v > 0.1 else 0.25); kp.handle_left.y = kp.handle_right.y = kp.co.y
        fc.update()
# no haze: dust volume hidden
for n in ("CellDust",):
    if n in OB:
        o = OB[n]; o.animation_data_clear(); o.hide_render = True; o.hide_viewport = True
# cleaner, brighter set surfaces (brick, stone, floors, plaster-like)
def tint(mat_name, rgb, bump_k=0.6):
    m = bpy.data.materials.get(mat_name)
    if not m: return
    N = m.node_tree.nodes; bs = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    mx = next((n for n in N if n.type == 'MIX' and n.blend_type == 'MULTIPLY' and n.outputs['Result'].is_linked), None)
    if mx: mx.inputs['B'].default_value = (*rgb, 1)
    else:
        src = bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].links else None
        if src:
            m2 = N.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 1.0
            m2.inputs['B'].default_value = (*rgb, 1); m.node_tree.links.new(src, m2.inputs['A']); m.node_tree.links.new(m2.outputs['Result'], bs.inputs['Base Color'])
    for n in N:
        if n.type in ('BUMP', 'NORMAL_MAP'): n.inputs['Strength'].default_value *= bump_k
    bs.inputs['Roughness'].default_value = max(0.5, bs.inputs['Roughness'].default_value) if not bs.inputs['Roughness'].is_linked else bs.inputs['Roughness'].default_value
tint("M_CellBrick", (1.35, 1.28, 1.15)); tint("M_CellFloor", (1.3, 1.25, 1.18)); tint("M_YardWall", (1.25, 1.2, 1.1)); tint("M_Cobble", (1.15, 1.12, 1.08))
tint("M_ShopBrick", (1.15, 0.85, 0.65)); tint("M_Planks", (1.2, 1.1, 1.0))
sc["anim_look_fix"] = "06_animlook_fix"
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("FIXED", OUT)
