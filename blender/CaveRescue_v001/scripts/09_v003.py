"""v003 (director's D review): readable dark beats, banded mountain cutaway, detailed dive tanks + hoses, neoprene seams, diver rims.
blender -b final.blend --python 09_v003.py -- <out.blend>"""
import sys, math, bpy, bmesh
from mathutils import Vector as V, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; R_ = math.radians
def P(m): return m.node_tree.nodes.get("Principled BSDF") or next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
def scale_keys(idblock, k):
    ad = idblock.animation_data
    if not ad or not ad.action: return
    for fc in ad.action.layers[0].strips[0].channelbags[0].fcurves:
        for kp in fc.keyframe_points: kp.co.y *= k; kp.handle_left.y *= k; kp.handle_right.y *= k
# ---------- 1. dark beats read: stronger torches, more blue fill, rims on divers, exposure lift in 17-21 s and 29-31 s
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.name.endswith("_TorchLight"):
        diver = o.name.startswith("Diver")
        o.data.energy *= 2.5; scale_keys(o.data, 2.5); o.data.spot_size = R_(70)
f4 = bpy.data.objects["S4_Fill"].data; f4.animation_data_clear(); f4.energy = 700      # cavern normals fixed: fill can stay on underwater
scale_keys(bpy.data.objects["CAM_Fill"].data, 1.5)
# underwater: the camera fill (no volume scatter) and lighter murk on the rise back to the chamber, so divers and boys stay readable
cfd = bpy.data.objects["CAM_Fill"].data
for f, e in ((1215, 160), (1820, 160), (2440, 160), (2565, 160)):
    cfd.energy = e; cfd.keyframe_insert("energy", frame=f)
mv = bpy.data.materials["M_Murk"].node_tree.nodes["MurkVol"].inputs['Density']
for f, d in ((1, mv.default_value), (1700, mv.default_value), (1715, mv.default_value * 0.35), (1830, mv.default_value * 0.35), (1860, mv.default_value)):
    mv.default_value = d; mv.keyframe_insert("default_value", frame=f)
for o in bpy.data.objects:
    if o.name.startswith("S5_Ambient_"): o.data.energy = 90
for n in ("DiverA", "DiverB", "DiverC"):
    rig = bpy.data.objects[n]; hb = rig.data.bones["head"]
    L = bpy.data.objects.new(n + "_Rim", bpy.data.lights.new(n + "_Rim", 'POINT')); sc.collection.objects.link(L)
    L.data.energy = 18; L.data.color = (0.6, 0.85, 1.0); L.data.shadow_soft_size = 0.15; L.visible_volume_scatter = False
    L.location = hb.head_local + V((0.25, 0.55, 0.25))
    c = L.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "head"; c.inverse_matrix = hb.matrix_local.inverted()
ex = sc.view_settings
for f, e in ((1009, 1.7), (1212, 1.7), (1240, 2.1), (1700, 2.1), (1760, 2.2), (1850, 2.2), (1890, 1.7)):
    ex.exposure = e; ex.keyframe_insert("exposure", frame=f)
# ---------- 2. cutaway: clean colour strata bands, hollow tunnel, clear blue sumps, tiny figures, sky gradient
ms = bpy.data.materials["M_Strata"]; nt = ms.node_tree; p = P(ms)
wv = next(n for n in nt.nodes if n.type == 'TEX_WAVE'); wv.inputs['Scale'].default_value = 0.22; wv.inputs['Distortion'].default_value = 3.0
rp = nt.nodes.new('ShaderNodeValToRGB'); el = rp.color_ramp.elements; rp.color_ramp.interpolation = 'CONSTANT'
cols = [(0.0, (0.62, 0.48, 0.32)), (0.2, (0.78, 0.66, 0.46)), (0.4, (0.52, 0.5, 0.46)), (0.6, (0.72, 0.42, 0.26)), (0.8, (0.85, 0.78, 0.6))]
el[0].position, el[0].color = cols[0][0], (*cols[0][1], 1); el[1].position, el[1].color = cols[1][0], (*cols[1][1], 1)
for pos, c in cols[2:]:
    e_ = el.new(pos); e_.color = (*c, 1)
mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 0.35
src = p.inputs['Base Color'].links[0].from_socket
nt.links.new(wv.outputs['Fac'], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], mx.inputs['A']); nt.links.new(src, mx.inputs['B'])
nt.links.new(mx.outputs['Result'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.6
vd = bpy.data.materials["M_CaveVoid"]; pv = P(vd); pv.inputs['Base Color'].default_value = (0.2, 0.14, 0.1, 1)
pv.inputs['Emission Color'].default_value = (0.35, 0.22, 0.12, 1); pv.inputs['Emission Strength'].default_value = 0.4
sw = bpy.data.materials["M_SumpWater"]; ps = P(sw); ps.inputs['Base Color'].default_value = (0.05, 0.4, 1.0, 1)
ps.inputs['Emission Color'].default_value = (0.1, 0.45, 1.0, 1); ps.inputs['Emission Strength'].default_value = 1.2; ps.inputs['Alpha'].default_value = 0.9
rl = bpy.data.objects["S3_RouteLine"]; rl.data.bevel_depth = 0.11
for o in bpy.data.objects:
    if o.name.startswith("S3_RouteBlue_"): o.data.bevel_depth = 0.12
dm = bpy.data.materials["M_StudioDome"]
mr = next(n for n in dm.node_tree.nodes if n.type == 'MAP_RANGE'); mr.inputs['From Min'].default_value = -0.05; mr.inputs['From Max'].default_value = 0.35
next(n for n in dm.node_tree.nodes if n.type == 'EMISSION').inputs['Strength'].default_value = 1.3
P(bpy.data.materials["M_StudioFloor"]).inputs['Base Color'].default_value = (0.5, 0.72, 0.92, 1)
# warm glow + tiny figures in the chamber (body cone + head sphere), facing the cut
m_fig = bpy.data.materials.new("M_TinyFigure"); m_fig.use_nodes = True; P(m_fig).inputs['Base Color'].default_value = (0.95, 0.55, 0.2, 1)
P(m_fig).inputs['Emission Color'].default_value = (1.0, 0.6, 0.25, 1); P(m_fig).inputs['Emission Strength'].default_value = 3.0
DX = sc["DX"]
for i in range(13):
    d = bpy.data.objects["S3_Dot_%02d" % i]; d.scale = (0.55, 0.55, 0.55)     # dots stay as the travelling torch lights
for i in range(6):
    y = 36.2 + 0.32 * i; z = 1.55 + 0.05 * (i % 2)
    bpy.ops.mesh.primitive_cone_add(radius1=0.07, depth=0.2, location=(DX + 0.12, y, z)); b = bpy.context.active_object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(DX + 0.12, y, z + 0.14)); h = bpy.context.active_object
    for o in (b, h): o.data.materials.append(m_fig); o.name = "S3_TinyFigure_%d" % i
    for f, v in ((1, False), (2570, False), (2575, True)):
        for o in (b, h): o.hide_render = v; o.keyframe_insert("hide_render", frame=f)
gl = bpy.data.objects.new("S3_ChamberGlow", bpy.data.lights.new("S3_ChamberGlow", 'POINT')); gl.data.energy = 60; gl.data.color = (1.0, 0.6, 0.25)
gl.location = (DX - 0.6, 37.4, 2.0); sc.collection.objects.link(gl)
# ---------- 3. dive tanks: domed ends, valve heads, cam bands; regulator hoses from valve to mouth
tank_m = bpy.data.materials["M_Tank"]; P(tank_m).inputs['Roughness'].default_value = 0.35; P(tank_m).inputs['Metallic'].default_value = 0.2
m_metal = bpy.data.materials.new("M_Valve"); m_metal.use_nodes = True; P(m_metal).inputs['Base Color'].default_value = (0.8, 0.8, 0.82, 1); P(m_metal).inputs['Metallic'].default_value = 1.0; P(m_metal).inputs['Roughness'].default_value = 0.3
m_strap = bpy.data.materials.new("M_Strap"); m_strap.use_nodes = True; P(m_strap).inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1); P(m_strap).inputs['Roughness'].default_value = 0.6
m_hose = bpy.data.materials.new("M_Hose"); m_hose.use_nodes = True; P(m_hose).inputs['Base Color'].default_value = (0.03, 0.03, 0.035, 1); P(m_hose).inputs['Roughness'].default_value = 0.45
def tank_mesh(name):
    bm = bmesh.new(); r, L = 0.085, 0.62
    bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=r, radius2=r, depth=L - 2 * r)
    for zc, sgn in ((L / 2 - r, 1), (-(L / 2 - r), -1)):                       # domes
        g = bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
        kill = [v for v in g['verts'] if v.co.z * sgn < -1e-4]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        for v in [v for v in bm.verts if v.select is False]: pass
        bmesh.ops.translate(bm, vec=(0, 0, zc), verts=[v for v in bm.verts if v.tag is False and abs(v.co.z) <= r + 1e-4 and v.co.z * sgn >= -1e-4 and (v.co.z == v.co.z)] if False else [])
    bm.free()
    # simpler, robust build: lathe a profile
    prof = [(0.0, -0.31), (0.03, -0.308), (0.06, -0.298), (0.078, -0.28), (0.085, -0.25), (0.085, 0.22), (0.078, 0.255), (0.062, 0.28),
            (0.035, 0.298), (0.02, 0.305), (0.02, 0.33), (0.0, 0.33)]
    me = bpy.data.meshes.new(name); me.from_pydata([(x, 0, z) for x, z in prof], [(i, i + 1) for i in range(len(prof) - 1)], [])
    tmp = bpy.data.objects.new("tmp_" + name, me); sc.collection.objects.link(tmp)
    sc_ = tmp.modifiers.new("S", 'SCREW'); sc_.axis = 'Z'; sc_.steps = 32; sc_.render_steps = 32; sc_.use_merge_vertices = True; sc_.use_normal_calculate = True
    dg = bpy.context.evaluated_depsgraph_get(); new = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg)); bpy.data.objects.remove(tmp, do_unlink=True)
    for pg in new.polygons: pg.use_smooth = True
    return new
TM = tank_mesh("TankBody"); TM.materials.append(tank_m)
for o in [o for o in bpy.data.objects if "_Tank" in o.name and o.type == 'MESH' and o.name.split("_")[0].startswith("Diver")]:
    o.data = TM
    # valve head + knob, two cam bands, parented to the tank
    for nm, kind, loc, dims, mat in (("Valve", 'CYL', (0, 0, 0.35), (0.022, 0.05), m_metal), ("Knob", 'CYL', (0.03, 0, 0.36), (0.018, 0.02), m_strap),
                                      ("BandA", 'TOR', (0, 0, 0.12), (0.088, 0.008), m_strap), ("BandB", 'TOR', (0, 0, -0.14), (0.088, 0.008), m_strap)):
        if kind == 'CYL':
            bpy.ops.mesh.primitive_cylinder_add(radius=dims[0], depth=dims[1], vertices=16, rotation=(0, R_(90) if nm == "Knob" else 0, 0))
        else:
            bpy.ops.mesh.primitive_torus_add(major_radius=dims[0], minor_radius=dims[1], major_segments=32, minor_segments=8)
        q = bpy.context.active_object; q.name = o.name + "_" + nm; q.data.materials.append(mat)
        q.parent = o; q.location = loc; q.matrix_parent_inverse = Matrix.Identity(4)
# hoses: curve with two hooks (valve of the left tank -> mouth), hooks on empties that ride the tank and the head
for n in ("DiverA", "DiverB", "DiverC"):
    rig = bpy.data.objects[n]; tank = bpy.data.objects.get(n + "_Tank1") or bpy.data.objects.get(n + "_Tank-1")
    if tank is None: continue
    e1 = bpy.data.objects.new(n + "_HoseA", None); sc.collection.objects.link(e1); e1.parent = tank; e1.location = (0, 0, 0.36)
    hb = rig.data.bones["head"]; mouth = hb.head_local.lerp(hb.tail_local, 0.25) + V((0, -0.11, -0.02))
    e2 = bpy.data.objects.new(n + "_HoseB", None); sc.collection.objects.link(e2); e2.location = mouth
    c = e2.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "head"; c.inverse_matrix = hb.matrix_local.inverted()
    cu = bpy.data.curves.new(n + "_Hose", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.009; cu.bevel_resolution = 2
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
    for bp in sp.bezier_points: bp.handle_left_type = bp.handle_right_type = 'AUTO'
    ho = bpy.data.objects.new(n + "_Hose", cu); sc.collection.objects.link(ho); cu.materials.append(m_hose)
    for i, e in enumerate((e1, e2)):
        hk = ho.modifiers.new("Hook%d" % i, 'HOOK'); hk.object = e
        hk.vertex_indices_set([i * 3, i * 3 + 1, i * 3 + 2])
    # regulator second stage at the mouth
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.035, vertices=16, rotation=(R_(90), 0, 0))
    rg = bpy.context.active_object; rg.name = n + "_Regulator"; rg.data.materials.append(m_hose); rg.parent = e2; rg.location = (0, 0, 0); rg.matrix_parent_inverse = Matrix.Identity(4)
# ---------- 4. neoprene: panel seams + slight sheen so the suits read in close-up
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.split(".")[-1] == "male_worksuit01":
        for m in o.data.materials:
            if m.get("seams"): continue
            m["seams"] = 1; nt = m.node_tree; p = P(m)
            tc = nt.nodes.new('ShaderNodeTexCoord'); w1 = nt.nodes.new('ShaderNodeTexWave'); w1.wave_type = 'BANDS'; w1.bands_direction = 'Z'
            w1.inputs['Scale'].default_value = 1.6; w1.wave_profile = 'SAW'
            r = nt.nodes.new('ShaderNodeMapRange'); r.inputs['From Min'].default_value = 0.97; r.inputs['From Max'].default_value = 0.985
            mxc = nt.nodes.new('ShaderNodeMix'); mxc.data_type = 'RGBA'; mxc.inputs['A'].default_value = (0.012, 0.014, 0.018, 1); mxc.inputs['B'].default_value = (0.09, 0.2, 0.32, 1)
            nt.links.new(tc.outputs['Object'], w1.inputs['Vector']); nt.links.new(w1.outputs['Fac'], r.inputs['Value']); nt.links.new(r.outputs['Result'], mxc.inputs['Factor'])
            nt.links.new(mxc.outputs['Result'], p.inputs['Base Color'])
            if 'Sheen Weight' in p.inputs: p.inputs['Sheen Weight'].default_value = 0.12; p.inputs['Sheen Tint'].default_value = (0.2, 0.3, 0.45, 1)
            p.inputs['Roughness'].default_value = 0.4
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("V003_OK")
