"""Set dressing that makes the interiors read as real 2003 buildings: worn wall paint with scuffs and a dirty
bottom band, skirting, cable trays with cables, ventilation grilles, fire extinguishers on brackets with their sign,
pictogram signs, ceiling CCTV domes, electrical boxes, number engraving for the safe-deposit doors."""
import math, random
import bpy
from mathutils import Vector, Matrix
import ship as S
from sets import flat, emit, brushed, box, enamel


def wall_paint(name, color, rough=0.8, scuff=1.0, z_dirty=0.35, tile=None):
    """Painted concrete / plaster: soft tonal patches, a fine roller texture, a grimy band near the floor and
    dark scuff marks (shoes, trolleys) between 0.1 and 1.1 m; scuffs are glossier."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); geo = N.new("ShaderNodeNewGeometry")
    sz = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sz.inputs[0])
    big = N.new("ShaderNodeTexNoise"); big.inputs['Scale'].default_value = 1.2; big.inputs['Detail'].default_value = 5
    L.new(geo.outputs['Position'], big.inputs['Vector'])
    fine = N.new("ShaderNodeTexNoise"); fine.inputs['Scale'].default_value = 260; fine.inputs['Detail'].default_value = 3
    L.new(geo.outputs['Position'], fine.inputs['Vector'])
    c = N.new("ShaderNodeRGB"); c.outputs[0].default_value = (*color, 1)
    # tonal patches
    mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 0.86; mr.inputs['To Max'].default_value = 1.06
    L.new(big.outputs['Fac'], mr.inputs['Value'])
    sc = N.new("ShaderNodeVectorMath"); sc.operation = 'SCALE'; L.new(c.outputs[0], sc.inputs[0]); L.new(mr.outputs[0], sc.inputs['Scale'])
    # grime band at the floor
    gb = N.new("ShaderNodeMapRange"); gb.inputs['From Min'].default_value = 0.0; gb.inputs['From Max'].default_value = z_dirty
    gb.inputs['To Min'].default_value = 0.55; gb.inputs['To Max'].default_value = 1.0; L.new(sz.outputs['Z'], gb.inputs['Value'])
    gn = N.new("ShaderNodeMath"); gn.operation = 'MULTIPLY_ADD'; L.new(fine.outputs['Fac'], gn.inputs[0])
    gn.inputs[1].default_value = 0.15; L.new(gb.outputs[0], gn.inputs[2])
    sc2 = N.new("ShaderNodeVectorMath"); sc2.operation = 'SCALE'; L.new(sc.outputs[0], sc2.inputs[0]); L.new(gn.outputs[0], sc2.inputs['Scale'])
    # scuffs: stretched voronoi blobs in a band 0.1..1.1 m
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (2.5, 2.5, 9.0); L.new(geo.outputs['Position'], mp.inputs['Vector'])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs['Scale'].default_value = 3.0; L.new(mp.outputs[0], vo.inputs['Vector'])
    sm = N.new("ShaderNodeMapRange"); sm.inputs['From Min'].default_value = 0.06; sm.inputs['From Max'].default_value = 0.02
    sm.inputs['To Min'].default_value = 0.0; sm.inputs['To Max'].default_value = 0.6 * scuff; L.new(vo.outputs['Distance'], sm.inputs['Value'])
    band = N.new("ShaderNodeMapRange"); band.inputs['From Min'].default_value = 1.2; band.inputs['From Max'].default_value = 0.9
    L.new(sz.outputs['Z'], band.inputs['Value'])
    smb = N.new("ShaderNodeMath"); smb.operation = 'MULTIPLY'; L.new(sm.outputs[0], smb.inputs[0]); L.new(band.outputs[0], smb.inputs[1])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; L.new(smb.outputs[0], mx.inputs['Factor'])
    L.new(sc2.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (0.35, 0.32, 0.3, 1)
    L.new(mx.outputs[2], p.inputs['Base Color'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = rough; rr.inputs['To Max'].default_value = rough - 0.3
    L.new(smb.outputs[0], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.12; b.inputs['Distance'].default_value = 0.001
    L.new(fine.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


_M = {}


def mats():
    if not _M:
        _M.update(skirt=flat("skirting", (0.08, 0.07, 0.065), 0.45), tray=brushed("cable_tray", (0.5, 0.5, 0.5), 0.4),
                  cable=flat("cable_grey", (0.12, 0.12, 0.13), 0.5), cable2=flat("cable_black", (0.02, 0.02, 0.02), 0.4),
                  red=flat("ext_red", (0.5, 0.02, 0.015), 0.25, coat=0.6), blk=flat("ext_black", (0.015, 0.015, 0.015), 0.5),
                  vent=brushed("vent", (0.45, 0.45, 0.44), 0.5), white=flat("sign_white", (0.8, 0.8, 0.78), 0.4),
                  green=emit("sign_green", (0.05, 0.55, 0.22), 0.5), redsign=flat("sign_red", (0.6, 0.03, 0.02), 0.4),
                  dome=flat("dome_smoke", (0.02, 0.02, 0.025), 0.05), domebase=flat("dome_base", (0.75, 0.74, 0.7), 0.4),
                  grey_box=flat("elec_box", (0.42, 0.42, 0.4), 0.45))
    return _M


def skirting(p0, p1, normal, h=0.1, t=0.015):
    """Skirting board along a wall from p0 to p1 (floor level), its face toward `normal`."""
    M = mats(); a, b = Vector(p0), Vector(p1); n = Vector(normal).normalized()
    c = (a + b) / 2 + n * (t / 2) + Vector((0, 0, h / 2)); L_ = (b - a).length
    o = box("skirting", c, (L_, t, h), M["skirt"], rot=(0, 0, math.atan2((b - a).y, (b - a).x)))
    return o


def cable_tray(p0, p1, z, n_cables=5, w=0.2):
    """Perforated steel cable tray hung under the ceiling with a bundle of cables lying in it."""
    M = mats(); a, b = Vector((p0[0], p0[1], z)), Vector((p1[0], p1[1], z)); d = (b - a); L_ = d.length; yaw = math.atan2(d.y, d.x)
    c = (a + b) / 2
    R = Matrix.Rotation(yaw, 3, 'Z')
    box("cable_tray_base", c, (L_, w, 0.004), M["tray"], rot=(0, 0, yaw))
    for s in (-1, 1):
        box("cable_tray_side", c + R @ Vector((0, s * w / 2, 0.025)), (L_, 0.004, 0.05), M["tray"], rot=(0, 0, yaw))
    rng = random.Random(int(L_ * 100))
    for k in range(n_cables):
        off = R @ Vector((0, -w / 2 + 0.03 + k * (w - 0.06) / max(1, n_cables - 1), 0.012 + (k % 2) * 0.012))
        S.cyl("cable", a + off, b + off, 0.009 + 0.003 * (k % 3), mat=M["cable"] if k % 2 else M["cable2"], verts=10)
    # hangers
    n = max(2, int(L_ / 1.2))
    for i in range(n + 1):
        p = a.lerp(b, i / n)
        for s in (-1, 1):
            S.cyl("tray_hanger", p + R @ Vector((0, s * (w / 2 + 0.01), 0)), p + R @ Vector((0, s * (w / 2 + 0.01), 0.25)), 0.004, mat=M["tray"], verts=6)


def vent(c, normal, w=0.4, h=0.2):
    """Ventilation grille on a wall or ceiling: frame and slats."""
    M = mats(); n = Vector(normal).normalized()
    q = n.to_track_quat('Y', 'Z') if abs(n.z) < 0.9 else n.to_track_quat('Y', 'X')
    R = q.to_matrix(); c = Vector(c)
    root = bpy.data.objects.new("vent", None); bpy.context.scene.collection.objects.link(root)
    parts = [box("vent_frame", (0, 0.006, 0), (w, 0.012, h), M["vent"], bevel=0.003),
             box("vent_hole", (0, 0.013, 0), (w - 0.03, 0.002, h - 0.03), flat("vent_dark", (0.01, 0.01, 0.01), 0.8))]
    k = 0; z = -h / 2 + 0.025
    while z < h / 2 - 0.02:
        parts.append(box("vent_slat", (0, 0.016, z), (w - 0.03, 0.002, 0.012), M["vent"], rot=(math.radians(35), 0, 0))); z += 0.022
    for o in parts:
        o.parent = root
    root.matrix_world = Matrix.Translation(c) @ R.to_4x4()
    return root


def extinguisher(c, normal):
    """6 kg powder extinguisher on a wall bracket, with the red square sign above it."""
    M = mats(); n = Vector(normal).normalized(); c = Vector(c)
    yaw = math.atan2(n.y, n.x)
    body = c + n * 0.09
    S.cyl("ext_body", body + Vector((0, 0, 0.0)), body + Vector((0, 0, 0.45)), 0.075, mat=M["red"], verts=24)
    S.cyl("ext_neck", body + Vector((0, 0, 0.45)), body + Vector((0, 0, 0.5)), 0.03, mat=M["blk"], verts=16)
    box("ext_handle", body + Vector((0, 0, 0.53)), (0.1, 0.025, 0.02), M["blk"], rot=(0, 0, yaw))
    S.cyl("ext_hose", body + Vector((0, 0, 0.48)) + n * 0.05, body + Vector((0, 0, 0.15)) + n * 0.08, 0.008, mat=M["blk"], verts=8)
    box("ext_bracket", c + n * 0.01 + Vector((0, 0, 0.3)), (0.06 if abs(n.x) < 0.5 else 0.02, 0.02 if abs(n.x) < 0.5 else 0.06, 0.12), M["blk"])
    sign = box("ext_sign", c + n * 0.004 + Vector((0, 0, 0.8)), (0.2 if abs(n.x) < 0.5 else 0.004, 0.004 if abs(n.x) < 0.5 else 0.2, 0.2), M["redsign"])
    box("ext_sign_icon", c + n * 0.007 + Vector((0, 0, 0.78)), (0.05 if abs(n.x) < 0.5 else 0.002, 0.002 if abs(n.x) < 0.5 else 0.05, 0.11), M["white"])


def sign(c, normal, kind="exit", w=0.3, h=0.15):
    """Pictogram sign (no lettering): 'exit' green with a white figure and arrow; 'notice' white with a blue disc."""
    M = mats(); n = Vector(normal).normalized(); c = Vector(c)
    flatx = abs(n.x) < 0.5
    sz = lambda a, b: (a, 0.004, b) if flatx else (0.004, a, b)
    off = lambda u, v: c + n * 0.006 + (Vector((u, 0, v)) if flatx else Vector((0, u, v)))
    if kind == "exit":
        box("sign_exit", c + n * 0.002, sz(w, h), M["green"])
        box("sign_fig", off(-w * 0.18, 0), sz(0.03, 0.08), M["white"])
        box("sign_arrow", off(w * 0.15, 0), sz(0.09, 0.02), M["white"])
        box("sign_door", off(-w * 0.35, 0), sz(0.03, 0.1), M["white"])
    else:
        box("sign_notice", c + n * 0.002, sz(w, h), M["white"])
        box("sign_disc", off(-w * 0.28, 0), sz(0.07, 0.07), flat("sign_blue", (0.02, 0.1, 0.45), 0.4))
        for k in range(3):
            box("sign_line", off(w * 0.1, h * 0.2 - k * 0.035), sz(w * 0.5, 0.012), flat("sign_grey", (0.15, 0.15, 0.15), 0.5))


def cctv_dome(c):
    """Ceiling CCTV dome: white base ring, smoked hemisphere."""
    M = mats(); c = Vector(c)
    S.cyl("dome_base", c, c - Vector((0, 0, 0.02)), 0.08, mat=M["domebase"], verts=32)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.065, location=c - Vector((0, 0, 0.02)))
    o = bpy.context.active_object; o.name = "dome_glass"
    import bmesh
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.001], context='VERTS'); bm.to_mesh(me); bm.free()
    me.materials.append(M["dome"]); bpy.ops.object.shade_smooth()
    return o


def elec_box(c, normal, w=0.3, h=0.4, d=0.12):
    M = mats(); n = Vector(normal).normalized(); c = Vector(c)
    size = (w, d, h) if abs(n.x) < 0.5 else (d, w, h)
    box("elec_box", c + n * d / 2, size, M["grey_box"], bevel=0.004)
    S.cyl("conduit", c + n * 0.03 + Vector((0, 0, h / 2)), c + n * 0.03 + Vector((0, 0, 2.6)), 0.012, mat=M["grey_box"], verts=8)


def number_text(txt, M, size=0.014, mat=None):
    """Engraved number (a text object) placed with matrix M (text faces local -y of M)."""
    cu = bpy.data.curves.new("num", 'FONT'); cu.body = txt; cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.extrude = 0.0003
    o = bpy.data.objects.new("num_" + txt, cu); bpy.context.scene.collection.objects.link(o)
    o.matrix_world = M @ Matrix.Rotation(math.radians(90), 4, 'X')
    if mat:
        cu.materials.append(mat)
    return o
