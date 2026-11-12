"""Post-anim fixes exec'd before 04_camera: print-free clothing, beanie over hair, cells growth, city look."""
import bpy, math, random
from mathutils import Vector, Matrix
# ---- clothing: rebuild every suit material from AO + normal (no prints); shirt/pants split on rest-pose height
TINTS = {"Fan": ((0.20, 0.26, 0.20), (0.06, 0.07, 0.10)), "Manager": ((0.08, 0.10, 0.20), (0.10, 0.10, 0.12)),
         "Doctor": ((0.90, 0.91, 0.92), (0.15, 0.17, 0.25)), "Nurse": ((0.20, 0.45, 0.48), (0.20, 0.45, 0.48)),
         "Crowd0": ((0.55, 0.10, 0.08), (0.10, 0.12, 0.20)), "Crowd1": ((0.95, 0.72, 0.10), (0.08, 0.08, 0.09)),
         "Crowd2": ((0.12, 0.22, 0.42), (0.25, 0.22, 0.18)), "Crowd3": ((0.15, 0.55, 0.30), (0.10, 0.10, 0.12)),
         "Crowd4": ((0.18, 0.18, 0.20), (0.12, 0.14, 0.22)), "Crowd5": ((0.55, 0.12, 0.22), (0.07, 0.07, 0.08)),
         "Player0": ((0.55, 0.05, 0.05), (0.06, 0.06, 0.07)), "Player1": ((0.05, 0.11, 0.38), (0.06, 0.06, 0.07))}
fab_n = bpy.data.images.load(f"{PH}/knitted_fleece/textures/" + [f for f in os.listdir(f"{PH}/knitted_fleece/textures") if "nor_gl" in f][0], check_existing=True)
fab_n.colorspace_settings.name = 'Non-Color'
done = {}
def suit_mat(old, top, bot):
    m = bpy.data.materials.new(old.name + "_clean"); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    ao = nrm = None
    for nd in old.node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.image:
            nm = nd.image.name.lower()
            if "_ao" in nm: ao = nd.image
            if "normal" in nm: nrm = nd.image
    tc = n.new('ShaderNodeTexCoord'); sp = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['Generated'], sp.inputs['Vector'])
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 30; l.new(tc.outputs['Generated'], nz.inputs['Vector'])
    ad = n.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.02; l.new(nz.outputs['Fac'], ad.inputs[0]); l.new(sp.outputs['Z'], ad.inputs[2])
    gt = n.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.52; l.new(ad.outputs[0], gt.inputs[0])
    mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*bot, 1); mx.inputs['B'].default_value = (*top, 1)
    l.new(gt.outputs[0], mx.inputs['Factor']); col = mx.outputs['Result']
    if ao:
        t = n.new('ShaderNodeTexImage'); t.image = ao; l.new(tc.outputs['UV'], t.inputs['Vector'])
        m2 = n.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 0.8
        l.new(col, m2.inputs['A']); l.new(t.outputs['Color'], m2.inputs['B']); col = m2.outputs['Result']
    l.new(col, p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.8; p.inputs['Sheen Weight'].default_value = 0.3
    fm = n.new('ShaderNodeMapping'); fm.inputs['Scale'].default_value = (40, 40, 40); l.new(tc.outputs['UV'], fm.inputs['Vector'])
    ft = n.new('ShaderNodeTexImage'); ft.image = fab_n; l.new(fm.outputs['Vector'], ft.inputs['Vector'])
    fn = n.new('ShaderNodeNormalMap'); fn.inputs['Strength'].default_value = 0.6; l.new(ft.outputs['Color'], fn.inputs['Color'])
    if nrm:
        t = n.new('ShaderNodeTexImage'); t.image = nrm; t.image.colorspace_settings.name = 'Non-Color'; l.new(tc.outputs['UV'], t.inputs['Vector'])
        nm2 = n.new('ShaderNodeNormalMap'); l.new(t.outputs['Color'], nm2.inputs['Color'])
        l.new(nm2.outputs['Normal'], p.inputs['Normal'])
    else:
        l.new(fn.outputs['Normal'], p.inputs['Normal'])
    return m
for o in bpy.data.objects:
    if o.type != 'MESH' or not any(k in o.name for k in ("suit",)): continue
    base = o.name.split(".")[0]
    src = o["src"] if "src" in o.keys() else (base if base in TINTS else None)
    if not src:
        # duplicates: find the source rig via the armature modifier's original name pattern
        for k in TINTS:
            if o.data.name.startswith(k): src = k
    if not src: src = "Crowd4"
    top, bot = TINTS[src]
    key = (o.data.name, src)
    if key not in done:
        done[key] = [suit_mat(m, top, bot) for m in o.data.materials]
    o.data.materials.clear()
    for m in done[key]: o.data.materials.append(m)
# ---- beanie: ribbed knit dome over the hair, parented to the head bone
old = bpy.data.objects["Beanie"]; anim_old = old.animation_data.action if old.animation_data else None
hair = bpy.data.objects["Fan.ponytail01"]
FR.data.pose_position = 'REST'; bpy.context.view_layer.update()
hv = [hair.matrix_world @ v.co for v in hair.data.vertices]
htop = max(v.z for v in hv)
eyez = FR.data.bones["eye.L"].head_local.z
top_v = [v for v in hv if v.z > eyez + 0.03]
cx = (max(v.x for v in top_v) + min(v.x for v in top_v)) / 2; cy = (max(v.y for v in top_v) + min(v.y for v in top_v)) / 2
rx = (max(v.x for v in top_v) - min(v.x for v in top_v)) / 2 + 0.008; ry = (max(v.y for v in top_v) - min(v.y for v in top_v)) / 2 + 0.008
bot = eyez + 0.062
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0)
bn = bpy.context.object; bn.name = "BeanieKnitMesh"
import bmesh as _bm2
bm = _bm2.new(); bm.from_mesh(bn.data)
_bm2.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context='VERTS')
bm.to_mesh(bn.data); bm.free()
hz = htop + 0.035 - bot
for v in bn.data.vertices:
    v.co = Vector((cx + v.co.x * rx, cy + v.co.y * ry * 1.04, bot + (v.co.z + 0.05) / 1.05 * hz))
    if v.co.z < bot + 0.03:      # folded cuff, thicker
        d = Vector((v.co.x - cx, v.co.y - cy, 0)); v.co += d.normalized() * 0.005
for u in list(bn.users_collection): u.objects.unlink(bn)
C_CHAR.objects.link(bn)
bpy.ops.object.shade_smooth()
rib = bpy.data.textures.new("Rib", 'WOOD'); rib.wood_type = 'BANDS'; rib.noise_basis_2 = 'SIN'
rd = bn.modifiers.new("rib", 'DISPLACE'); rd.texture = rib; rd.strength = 0.0045; rd.texture_coords = 'LOCAL'
bn.data.materials.append(bpy.data.materials["BeanieKnit"])
uvbox(bn, 0.08)
FR.data.pose_position = 'POSE'
bone_parent(bn, FR, "head", FR.matrix_world @ Matrix.Identity(4))
bpy.data.objects.remove(old)
for _f, _v in ((F(34.0) - 1, 1), (F(34.0), 0.001), (F(37.9), 0.001), (F(37.9) + 1, 1)):
    bn.scale = (_v,) * 3; bn.keyframe_insert("scale", frame=_f)
# knit material: red wool, vertical ribs + stitch noise
km = bpy.data.materials.new("BeanieWool"); km.use_nodes = True
kn, kl = km.node_tree.nodes, km.node_tree.links; kp = kn["Principled BSDF"]
ktc = kn.new('ShaderNodeTexCoord')
kw = kn.new('ShaderNodeTexWave'); kw.wave_type = 'BANDS'; kw.bands_direction = 'X'; kw.inputs['Scale'].default_value = 60; kw.inputs['Distortion'].default_value = 1.5
kl.new(ktc.outputs['Generated'], kw.inputs['Vector'])
kv = kn.new('ShaderNodeTexVoronoi'); kv.inputs['Scale'].default_value = 400; kl.new(ktc.outputs['Object'], kv.inputs['Vector'])
kcr = kn.new('ShaderNodeValToRGB'); kcr.color_ramp.elements[0].color = (0.22, 0.02, 0.03, 1); kcr.color_ramp.elements[1].color = (0.62, 0.08, 0.07, 1)
kl.new(kw.outputs['Fac'], kcr.inputs['Fac']); kl.new(kcr.outputs['Color'], kp.inputs['Base Color'])
kp.inputs['Roughness'].default_value = 0.9; kp.inputs['Sheen Weight'].default_value = 0.8; kp.inputs['Sheen Tint'].default_value = (1, 0.6, 0.6, 1)
kad = kn.new('ShaderNodeMath'); kad.operation = 'MULTIPLY_ADD'; kad.inputs[1].default_value = 0.4
kl.new(kv.outputs['Distance'], kad.inputs[0]); kl.new(kw.outputs['Fac'], kad.inputs[2])
kbp = kn.new('ShaderNodeBump'); kbp.inputs['Strength'].default_value = 0.8; kbp.inputs['Distance'].default_value = 0.002
kl.new(kad.outputs[0], kbp.inputs['Height']); kl.new(kbp.outputs['Normal'], kp.inputs['Normal'])
bn.data.materials.clear(); bn.data.materials.append(km)
rib.noise_scale = 0.006
sw = bpy.data.objects["Scarf"].modifiers["fit"]; sw.offset = 0.03
# ---- melanoma cells grow during beat 3
for o in CELLS:
    t0 = F(5.0) + int(o["t"] * 140)
    o.scale = (0.001,) * 3; o.keyframe_insert("scale", frame=t0)
    s_ = o["s"]; o.scale = (s_, s_ * 0.8, s_ * 0.9); o.keyframe_insert("scale", frame=t0 + 40)
    o.scale = (s_ * 1.2, s_, s_ * 1.1); o.keyframe_insert("scale", frame=F(8.6))
# ---- city: textured facades, dark night sky instead of the station HDRI
nt = sc.world.node_tree; m2 = nt.nodes["WMIX2"]
for lk in list(m2.inputs['B'].links): nt.links.remove(lk)
m2.inputs['B'].default_value = (0.004, 0.006, 0.015, 1)
M_fac = pbr("Facade", "concrete_wall_006", 3.0, coords='Object', tint=(0.55, 0.5, 0.48))
src = bpy.data.objects["CityBlockSrc"]
for i, sl in enumerate(src.material_slots):
    if "Glass" in (sl.material.name if sl.material else ""):
        g = sl.material; g.use_nodes = True; pp = g.node_tree.nodes.get("Principled BSDF")
        if pp: pp.inputs['Emission Color'].default_value = (1.0, 0.7, 0.4, 1); pp.inputs['Emission Strength'].default_value = 0.25 if i % 2 else 0.06
    else:
        sl.material = M_fac
print("FIX_OK")

for _m in ("BeanieKnit",):
    _mt = bpy.data.materials[_m]
    for _n in _mt.node_tree.nodes:
        if _n.type == 'MIX' and _n.blend_type == 'MULTIPLY': _n.inputs['B'].default_value = (0.55, 0.07, 0.06, 1)
# bigger, darker moles on the neck decals
for _o in ("NeckMoleA", "NeckMoleB"):
    _mt = bpy.data.objects[_o].data.materials[0]; _mt.node_tree.nodes["SkinMap"].inputs['Scale'].default_value = (650,) * 3

for g in {sl.material for o in BUILDINGS for sl in o.material_slots if sl.material and "Glass" in sl.material.name}:
    nt_ = g.node_tree; pp = nt_.nodes.get("Principled BSDF")
    if not pp: continue
    tc_ = nt_.nodes.new('ShaderNodeTexCoord'); vo = nt_.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 0.6
    nt_.links.new(tc_.outputs['Object'], vo.inputs['Vector'])
    cr_ = nt_.nodes.new('ShaderNodeValToRGB'); e_ = cr_.color_ramp.elements; cr_.color_ramp.interpolation = 'CONSTANT'
    e_[0].color = (0.0, 0.0, 0.0, 1); e_[1].position = 0.55; e_[1].color = (1.0, 0.62, 0.32, 1); e_.new(0.85).color = (0.35, 0.6, 1.0, 1)
    nt_.links.new(vo.outputs['Color'], cr_.inputs['Fac'])
    nt_.links.new(cr_.outputs['Color'], pp.inputs['Emission Color']); pp.inputs['Emission Strength'].default_value = 1.2
    pp.inputs['Base Color'].default_value = (0.02, 0.02, 0.03, 1); pp.inputs['Roughness'].default_value = 0.1
m2.inputs['B'].default_value = (0.008, 0.012, 0.035, 1)
# ---- body under clothes: sink covered skin 5 mm along normals so the shirt never shows skin at bends
COVER = ("spine", "clavicle", "upperarm01", "upperarm02", "breast", "pelvis", "upperleg", "shoulder")
for an in ("Fan", "Manager", "Doctor", "Nurse"):
    b = bpy.data.objects[an + ".body"]
    if "UnderShirt" in b.vertex_groups: continue
    names = {g.index: g.name for g in b.vertex_groups}
    vg = b.vertex_groups.new(name="UnderShirt")
    for v in b.data.vertices:
        w = sum(g.weight for g in v.groups if names.get(g.group, "").startswith(COVER))
        if w > 0.05: vg.add([v.index], min(1.0, w), 'REPLACE')
    d = b.modifiers.new("UnderShirt", 'DISPLACE'); d.vertex_group = "UnderShirt"; d.strength = -0.005; d.mid_level = 0.0
    bpy.context.view_layer.objects.active = b
    while b.modifiers.find("UnderShirt") > 0:
        bpy.ops.object.modifier_move_up(modifier="UnderShirt")

# pompom on the crown + ribs strong
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.032, location=(cx, cy, bot + hz + 0.018))
pp = bpy.context.object; pp.name = "BeaniePompom"
for u in list(pp.users_collection): u.objects.unlink(pp)
C_CHAR.objects.link(pp)
ptx = bpy.data.textures.new("Fluff", 'CLOUDS'); ptx.noise_scale = 0.004
pd = pp.modifiers.new("fluff", 'DISPLACE'); pd.texture = ptx; pd.strength = 0.012
bpy.ops.object.shade_smooth(); pp.data.materials.append(km)
FR.data.pose_position = 'REST'; bpy.context.view_layer.update()
bone_parent(pp, FR, "head", pp.matrix_world.copy())
for _f, _v in ((F(34.0) - 1, 1), (F(34.0), 0.001), (F(37.9), 0.001), (F(37.9) + 1, 1)):
    pp.scale = (_v,) * 3; pp.keyframe_insert("scale", frame=_f)
# ---- delete MPFB helper geometry (normally hidden by the MASK modifier) from every body mesh
import bmesh as _bmh
_done = set()
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.endswith(".body") or o.data.name in _done: continue
    _done.add(o.data.name)
    me = o.data
    if me.shape_keys: continue
    gi = {g.index for g in o.vertex_groups if g.name.lower().startswith(("helper", "joint")) or g.name in ("HelperGeometry", "JointCubes")}
    kill = [v.index for v in me.vertices if any(g.group in gi and g.weight > 0.5 for g in v.groups)]
    if not kill: continue
    bm = _bmh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    _bmh.ops.delete(bm, geom=[bm.verts[i] for i in kill], context='VERTS'); bm.to_mesh(me); bm.free()
    for m in o.modifiers:
        if m.type == 'MASK': m.show_viewport = m.show_render = False
print("HELPERS_DELETED", len(_done))
