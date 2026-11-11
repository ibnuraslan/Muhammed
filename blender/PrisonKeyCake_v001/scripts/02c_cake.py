# Procedural dark fruit cake (exec'd in 02_build_scene.py): Cake1 (foundry, whole), Cake2_Main + Cake2_Slice + crumbs (cell, beat 8).
import bmesh
def fruit_crumb_mat():
    m = bpy.data.materials.new("M_FruitCrumb"); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links
    bs = N["Principled BSDF"]; tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 160; nz.inputs['Detail'].default_value = 6
    cr = N.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.07, 0.03, 0.015, 1); cr.color_ramp.elements[1].color = (0.22, 0.11, 0.05, 1)
    vo = N.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 55
    vr = N.new('ShaderNodeMapRange'); vr.inputs['From Min'].default_value = 0.08; vr.inputs['From Max'].default_value = 0.0
    vc = N.new('ShaderNodeValToRGB'); vc.color_ramp.elements[0].color = (0.25, 0.02, 0.02, 1); vc.color_ramp.elements[1].color = (0.7, 0.35, 0.05, 1)
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.7
    for a, b in ((tc.outputs['Object'], nz.inputs['Vector']), (tc.outputs['Object'], vo.inputs['Vector']), (nz.outputs['Fac'], cr.inputs['Fac']),
                 (vo.outputs['Distance'], vr.inputs['Value']), (vo.outputs['Color'], vc.inputs['Fac']), (vr.outputs['Result'], mx.inputs['Factor']),
                 (cr.outputs['Color'], mx.inputs['A']), (vc.outputs['Color'], mx.inputs['B']), (mx.outputs['Result'], bs.inputs['Base Color']),
                 (nz.outputs['Fac'], bp.inputs['Height']), (bp.outputs['Normal'], bs.inputs['Normal'])):
        L.new(a, b)
    bs.inputs['Roughness'].default_value = 0.8
    return m
def icing_mat():
    m = bpy.data.materials.new("M_Icing"); m.use_nodes = True; bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs['Base Color'].default_value = (0.92, 0.89, 0.82, 1); bs.inputs['Roughness'].default_value = 0.35
    bs.inputs['Subsurface Weight'].default_value = 0.3; bs.inputs['Subsurface Radius'].default_value = (0.01, 0.008, 0.006)
    nt = m.node_tree; nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60; bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], bs.inputs['Normal'])
    return m
M_FC = fruit_crumb_mat(); M_IC = icing_mat()
CR, CH, IH = 0.11, 0.075, 0.012
def sector(name, a0, a1, segs, coll_name, loc):
    """cake sector from angle a0..a1 (degrees): crumb body + iced top with drips"""
    bm = bmesh.new()
    def ring(r, z, n): return [bm.verts.new((r * math.cos(R_(a0 + (a1 - a0) * i / n)), r * math.sin(R_(a0 + (a1 - a0) * i / n)), z)) for i in range(n + 1)]
    full = (a1 - a0) >= 359.9
    b0 = ring(CR, 0, segs); t0 = ring(CR, CH, segs)
    c0 = bm.verts.new((0, 0, 0)); c1 = bm.verts.new((0, 0, CH))
    side = []
    for i in range(segs):
        side.append(bm.faces.new((b0[i], b0[i + 1], t0[i + 1], t0[i])))
    for i in range(segs):
        bm.faces.new((c0, b0[i + 1], b0[i])); bm.faces.new((c1, t0[i], t0[i + 1]))
    cut = []
    if not full:
        cut.append(bm.faces.new((c0, b0[0], t0[0], c1))); cut.append(bm.faces.new((c1, t0[-1], b0[-1], c0)))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    # icing: a thin cap with drips over the rim
    it = ring(CR + 0.002, CH + IH, segs); ib = ring(CR + 0.002, CH - 0.004, segs); ci = bm.verts.new((0, 0, CH + IH))
    random.seed(hash(name) % 1000)
    for i, v in enumerate(ib):
        v.co.z -= max(0.0, math.sin(i * 1.7) * 0.012 + random.uniform(-0.004, 0.006))
    ice = []
    for i in range(segs):
        ice.append(bm.faces.new((ib[i], ib[i + 1], it[i + 1], it[i]))); ice.append(bm.faces.new((ci, it[i], it[i + 1])))
    if not full:
        ice.append(bm.faces.new((ci, it[0], ib[0], bm.verts.new((0, 0, CH - 0.004)))))
    me = bpy.data.meshes.new(name); bm.normal_update(); bm.to_mesh(me); bm.free()
    me.materials.append(M_FC); me.materials.append(M_IC)
    nf = len(me.polygons); n_ice = len(ice)
    for p in me.polygons[nf - n_ice:]: p.material_index = 1
    for p in me.polygons: p.use_smooth = False
    o = bpy.data.objects.new(name, me); coll(coll_name).objects.link(o); o.location = loc
    return o
cake_old = bpy.data.objects.get("Cake1")
loc1 = cake_old.location.copy() if cake_old else CAKE_P
if cake_old: bpy.data.objects.remove(cake_old)
for o in [o for o in bpy.data.objects if o.name.startswith("Cake2_")]: bpy.data.objects.remove(o)
sector("Cake1", 0, 360, 48, "Foundry", loc1)
SL = (160, 200)
sector("Cake2_Main", SL[1], SL[0] + 360, 44, "Cell", CAKE2_P)
sector("Cake2_Slice", SL[0], SL[1], 6, "Cell", CAKE2_P)
for i in range(26):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.003, 0.008))
    for v in bm.verts: v.co *= random.uniform(0.7, 1.3)
    me = bpy.data.meshes.new("Crumb%02d" % i); bm.to_mesh(me); bm.free(); me.materials.append(M_FC)
    c = bpy.data.objects.new("Crumb%02d" % i, me); coll("Cell").objects.link(c)
    a = R_(random.uniform(140, 220)); r = random.uniform(0.12, 0.2)
    c.location = CAKE2_P + Vector((r * math.cos(a), r * math.sin(a), 0.004)); c["rest"] = c.location.copy()
print("CAKE built")
