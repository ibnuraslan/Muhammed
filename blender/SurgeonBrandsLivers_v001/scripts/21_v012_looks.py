"""v012 looks pass (client rejection, Nov 21: items 1, 10, 12, 13, 16, 20, 31; RECURRING_FAULTS 6, 7).
blender -b in.blend --python 21_v012_looks.py -- <out.blend>

- Soft cloth bouffant caps (gathered edge, wrinkles, fabric sheen) that sit above the hairline: real hair shows at the
  forehead, temples and nape. Every OR person now has hair.
- The woman (Patient): real clothes at home - a mustard knit top and blue jeans (two garments, seam at the waist,
  slightly loose) - and a ponytail with the face clear. Same hair in every scene.
- The clerk (PanelB): braided hair, nothing over the eyes.
- Surgeon 2: loose two-piece scrubs (top + darker trousers), soft cap.
- Eyes: batch-2 eye fix (cornea as straight transparency) + a camera-only catchlight."""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
from bl_ext.user_default.mpfb.services.humanservice import HumanService
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v12lib as VL
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
V = lambda *a: Vector(a)
MP = "/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data"

def copy_vis(src, dst):
    """dst gets src's hide_render keys (or its static state)"""
    VL.clear_keys(dst, ("hide_render",))
    fc = [f for f in VL.fcurves(src) if f.data_path == "hide_render"]
    if not fc:
        dst.hide_render = src.hide_render; return
    for kp in fc[0].keyframe_points:
        dst.hide_render = bool(kp.co.y); dst.keyframe_insert("hide_render", frame=int(kp.co.x))
    VL.constant(dst, ("hide_render",))

def add_asset(rig_name, rel, kind):
    body = bpy.data.objects[rig_name + ".body"]
    ob = HumanService.add_mhclo_asset(os.path.join(MP, rel), body, asset_type=kind, subdiv_levels=1, material_type="MAKESKIN")
    copy_vis(body, ob)
    print("ADDED", ob.name, "to", rig_name)
    return ob

def remove(name):
    o = bpy.data.objects.get(name)
    if o: bpy.data.objects.remove(o, do_unlink=True)

def fabric(name, rgb, scale=60.0, rough=0.8, sheen=0.4, bump=0.25):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = rgb + (1,); b.inputs["Roughness"].default_value = rough
    b.inputs["Sheen Weight"].default_value = sheen
    tc = N.new("ShaderNodeTexCoord")
    w = N.new("ShaderNodeTexWave"); w.inputs["Scale"].default_value = scale; w.inputs["Distortion"].default_value = 2.0
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 3.0
    L.new(tc.outputs["Generated"], w.inputs["Vector"]); L.new(tc.outputs["Generated"], nz.inputs["Vector"])
    mx = N.new("ShaderNodeMath"); mx.operation = 'ADD'; L.new(w.outputs["Fac"], mx.inputs[0]); L.new(nz.outputs["Fac"], mx.inputs[1])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.004
    L.new(mx.outputs[0], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    # soft colour variation (folds catch darker tone)
    cr = N.new("ShaderNodeMapRange"); L.new(nz.outputs["Fac"], cr.inputs[0]); cr.inputs[3].default_value = 0.8; cr.inputs[4].default_value = 1.1
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1.0
    mul.inputs[6].default_value = rgb + (1,)
    cc = N.new("ShaderNodeCombineColor"); [L.new(cr.outputs[0], cc.inputs[i]) for i in range(3)]
    L.new(cc.outputs[0], mul.inputs[7]); L.new(mul.outputs[2], b.inputs["Base Color"])
    return m

def two_piece(ob, rig_name, top, bottom, loose=0.006):
    """faces above the waist get `top`, below get `bottom` (a real seam); pushed out a little so it hangs loose"""
    r = bpy.data.objects[rig_name]
    wz = (r.data.bones["spine05"].head_local.z + r.data.bones["spine04"].head_local.z) / 2 - 0.02
    ob.data.materials.clear(); ob.data.materials.append(top); ob.data.materials.append(bottom)
    for p in ob.data.polygons: p.material_index = 0 if p.center.z > wz else 1
    if loose > 0:
        d = ob.modifiers.new("Loose", 'DISPLACE'); d.strength = loose; d.mid_level = 0.0
        ob.modifiers.move(ob.modifiers.find(d.name), ob.modifiers.find("Armature") + 1)
        sm = ob.modifiers.new("LooseSmooth", 'CORRECTIVE_SMOOTH'); sm.factor = 0.5; sm.iterations = 4
        ob.modifiers.move(ob.modifiers.find(sm.name), ob.modifiers.find(d.name) + 1)

def body_mask_for(rig_name, clothes_ob, like=None):
    """mask the body under new clothes with the Delete.<name> group the asset added (keyed like `like` mask)"""
    body = bpy.data.objects[rig_name + ".body"]
    gname = "Delete." + clothes_ob.name.split(".", 1)[1]
    if gname not in body.vertex_groups: print("no delete group", gname); return
    m = body.modifiers.new(gname, 'MASK'); m.vertex_group = gname; m.invert_vertex_group = True
    if like:
        for fc in VL.fcurves(body):
            if fc.data_path == 'modifiers["%s"].show_render' % like:
                for kp in fc.keyframe_points:
                    m.show_render = bool(kp.co.y); body.keyframe_insert('modifiers["%s"].show_render' % gname, frame=int(kp.co.x))
        VL.constant(body)

# ------------------------------------------------------------------ woman: real clothes + ponytail
old_home = bpy.data.objects["Patient.female_casualsuit02"]
remove("Patient.bob02")
hair = add_asset("Patient", "hair/ponytail01/ponytail01.mhclo", "Hair")
suit = add_asset("Patient", "clothes/female_casualsuit01/female_casualsuit01.mhclo", "Clothes")
copy_vis(old_home, suit)
two_piece(suit, "Patient", fabric("WomanTop", (0.62, 0.42, 0.07), 90), fabric("WomanJeans", (0.08, 0.14, 0.30), 140, 0.7, 0.1, 0.35), 0.007)
body_mask_for("Patient", suit, like="Delete.female_casualsuit02")
remove("Patient.female_casualsuit02")
VL.clear_keys(bpy.data.objects["Patient.body"], ('modifiers["Delete.female_casualsuit02"]',))
m = bpy.data.objects["Patient.body"].modifiers.get("Delete.female_casualsuit02")
if m: bpy.data.objects["Patient.body"].modifiers.remove(m)

# ------------------------------------------------------------------ clerk: braid, face clear
remove("PanelB.bob01")
add_asset("PanelB", "hair/braid01/braid01.mhclo", "Hair")

# ------------------------------------------------------------------ OR staff: hair under the caps
add_asset("Surgeon2", "hair/ponytail01/ponytail01.mhclo", "Hair")
add_asset("Nurse", "hair/short04/short04.mhclo", "Hair")
add_asset("Anaesth", "hair/short01/short01.mhclo", "Hair")
h1 = bpy.data.objects["Surgeon1.short02"]; VL.clear_keys(h1, ("hide_render",)); h1.hide_render = False

# ------------------------------------------------------------------ Surgeon 2: loose two-piece scrubs
s2 = bpy.data.objects["Surgeon2.female_casualsuit01"]
two_piece(s2, "Surgeon2", fabric("S2Top", (0.10, 0.20, 0.52), 70, 0.85, 0.35), fabric("S2Trousers", (0.06, 0.12, 0.34), 70, 0.85, 0.35), 0.012)
for nm, rgb in (("Surgeon1", (0.10, 0.42, 0.40)), ("Nurse", (0.12, 0.30, 0.50)), ("Anaesth", (0.18, 0.38, 0.20))):
    ob = bpy.data.objects[nm + ".male_casualsuit01"]
    two_piece(ob, nm, fabric(nm + "Top", rgb, 70, 0.85, 0.35), fabric(nm + "Trousers", tuple(c * 0.8 for c in rgb), 70, 0.85, 0.35), 0.010)

def cap_fabric(name, rgb):
    """printed cotton: small light dots on the colour, weave bump, sheen"""
    m = fabric(name, rgb, 160, 0.9, 0.6, 0.45); nt = m.node_tree; N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]; src = b.inputs["Base Color"].links[0].from_socket
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 140
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["Object"], vo.inputs["Vector"])
    lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.16; L.new(vo.outputs["Distance"], lt.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(lt.outputs[0], mx.inputs[0]); L.new(src, mx.inputs[6])
    mx.inputs[7].default_value = tuple(min(1, c * 0.5 + 0.45) for c in rgb) + (1,)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    return m

# ------------------------------------------------------------------ soft cloth caps (replace the helmet shells)
CAPF = {"Surgeon1": 30, "Surgeon2": 960, "Nurse": 30, "Anaesth": 30}
CAPC = {"Surgeon1": (0.10, 0.42, 0.40), "Surgeon2": (0.42, 0.26, 0.55), "Nurse": (0.12, 0.30, 0.50), "Anaesth": (0.18, 0.38, 0.20)}
for nm, rgb in CAPC.items():
    cap = bpy.data.objects[nm + "_Cap"]; me0 = cap.data
    xs = [v.co.x for v in me0.vertices]; ys = [v.co.y for v in me0.vertices]; zs = [v.co.z for v in me0.vertices]
    rx = max(abs(x) for x in xs); cy = (max(ys) + min(ys)) / 2; ry = (max(ys) - min(ys)) / 2; rz = max(zs)
    rx += 0.008; ry += 0.010; rz += 0.006
    bm = bmesh.new(); NP, NT = 80, 24; rows = []
    top = bm.verts.new((0, cy, rz))
    for t_i in range(1, NT + 1):
        t = t_i / NT; row = []
        for p_i in range(NP):
            ph = 2 * math.pi * p_i / NP
            ze = -0.02375 + 0.0625 * math.cos(ph) - 0.01375 * math.cos(2 * ph)   # edge: above the forehead hairline, ear tops, nape
            z = rz - (rz - ze) * t
            rr = math.sqrt(max(0.0, 1 - (z / (rz + 0.01)) ** 2))
            puff = 1 + 0.035 * math.sin(math.pi * t) - 0.05 * t ** 8      # gathered elastic edge
            wob = 1 + 0.018 * math.sin(ph * 7 + t * 9) * math.sin(math.pi * t) + 0.012 * math.sin(ph * 26) * t ** 4   # folds + pleats at the band
            row.append(bm.verts.new((rx * rr * math.sin(ph) * puff * wob, cy - ry * rr * math.cos(ph) * puff * wob, z)))
        rows.append(row)
    for p_i in range(NP): bm.faces.new((top, rows[0][p_i], rows[0][(p_i + 1) % NP]))
    for t_i in range(NT - 1):
        for p_i in range(NP):
            bm.faces.new((rows[t_i][p_i], rows[t_i + 1][p_i], rows[t_i + 1][(p_i + 1) % NP], rows[t_i][(p_i + 1) % NP]))
    me = bpy.data.meshes.new(nm + "_SoftCap"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(cap_fabric(nm + "_CapFabric", rgb))
    cap.data = me
    for mo in list(cap.modifiers): cap.modifiers.remove(mo)
    tx = bpy.data.textures.new(nm + "_CapWrinkle", 'CLOUDS'); tx.noise_scale = 0.035
    d = cap.modifiers.new("Wrinkle", 'DISPLACE'); d.texture = tx; d.strength = 0.010; d.texture_coords = 'LOCAL'
    # hug the head: every vertex goes to the nearest head-surface point + 1.6 cm (hair room), sampled where visible
    body = bpy.data.objects[nm + ".body"]; hv = body.hide_viewport; body.hide_viewport = False
    sc.frame_set(CAPF[nm]); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); bme = ev.to_mesh(); Mi = cap.matrix_world.inverted() @ body.matrix_world
    pts = [Mi @ v.co for v in bme.vertices]
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromPolygons(pts, [tuple(p.vertices) for p in bme.polygons]); ev.to_mesh_clear(); body.hide_viewport = hv
    for v in me.vertices:
        loc, nrm, i, d = tree.find_nearest(v.co, 0.2)
        if loc is None: continue
        if v.index == 0: ph, t = 0.0, 0.0
        else: ph, t = 2 * math.pi * ((v.index - 1) % NP) / NP, ((v.index - 1) // NP + 1) / NT
        k = 0.015 + 0.006 * max(0.0, v.co.z / max(rz, 1e-3))                    # fuller on top (bouffant)
        k += 0.008 * max(0.0, math.sin(ph * 9 + 3.0 * t)) * math.sin(math.pi * min(1.0, t * 1.1))   # soft folds from the crown
        k += 0.003 * math.sin(ph * 31) * t ** 6                                  # gathered elastic band
        dv = v.co - loc
        v.co = loc + (dv.normalized() if dv.length > 1e-5 else nrm) * k
    tx = bpy.data.textures.new(nm + "_CapWrinkle", 'CLOUDS'); tx.noise_scale = 0.03
    d = cap.modifiers.new("Wrinkle", 'DISPLACE'); d.texture = tx; d.strength = 0.008; d.texture_coords = 'LOCAL'
    so = cap.modifiers.new("t", 'SOLIDIFY'); so.thickness = 0.002
    sub = cap.modifiers.new("s", 'SUBSURF'); sub.levels = 1; sub.render_levels = 1

# ------------------------------------------------------------------ masks: Surgeon 2's sized to the face
mk = bpy.data.objects["Surgeon2_Mask"]
mk.scale = (0.93, 0.93, 0.93)

# ------------------------------------------------------------------ eyes
if "EnhancedEye" in bpy.data.node_groups:
    _NO_SAVE = True
    exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "eye_fix.py")).read())
else:
    print("NO EnhancedEye group; eye materials:", sorted({m.name for o in bpy.data.objects if o.name.endswith(".high-poly") for m in o.data.materials}))
cam = sc.camera
ld = bpy.data.lights.new("Catchlight", 'POINT'); ld.energy = 0.6; ld.shadow_soft_size = 0.02
cl = bpy.data.objects.new("Catchlight", ld); sc.collection.objects.link(cl)
cl.parent = cam; cl.location = (0.12, 0.10, 0.0)
cl.visible_diffuse = False; cl.visible_transmission = False; cl.visible_volume_scatter = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("LOOKS_DONE", OUT)
