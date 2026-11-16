"""B09 ScaldingCoffee: build all sets into one file.  blender -b --python 02_sets.py -- out.blend
SetCar x=0, SetCafe x=40, SetHosp x=80, SetBoard x=120 (metres). Real models (CC-BY Sketchfab via Objaverse, CC0 Poly Haven)
plus our own cups, steam, dial, counter and rooms."""
import bpy, bmesh, sys, math, os
from mathutils import Vector, Matrix
W = "/tmp/claude-0/b09/"
A = W + "assets/"
BRAND = "/home/user/Muhammed/blender/assets/brand/"
R_ = math.radians
sc = bpy.context.scene
exec(open(W + "scripts/teal_fix.py").read().split('if __name__')[0])

def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c

def mat(name, rgb, rough=0.5, metal=0.0, emit=None, alpha=1.0, coat=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    P.inputs["Metallic"].default_value = metal
    P.inputs["Coat Weight"].default_value = coat
    if emit: P.inputs["Emission Color"].default_value = (*emit[0], 1); P.inputs["Emission Strength"].default_value = emit[1]
    if alpha < 1: P.inputs["Alpha"].default_value = alpha
    return m

def alive(lst):
    out = []
    for o in lst:
        try: o.name; out.append(o)
        except ReferenceError: pass
    return out

def link(o, c):
    for cc in o.users_collection: cc.objects.unlink(o)
    c.objects.link(o)

def box(name, c, loc, size, m, bevel=0.01, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    o.data.materials.append(m); link(o, c)
    for p in o.data.polygons: p.use_smooth = True
    return o

def plane(name, c, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); link(o, c); return o

def import_glb(path, name, c, scale=1.0, loc=(0, 0, 0), rotz=0.0, keep=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name, None); c.objects.link(root)
    for o in new:
        link(o, c)
        if o.parent is None: o.parent = root
    meshes = [o for o in new if o.type == 'MESH']
    if keep is not None:
        for o in meshes:
            if not keep(o): bpy.data.objects.remove(o)
        meshes = alive(meshes)
    root.scale = (scale,) * 3; root.location = loc; root.rotation_euler.z = rotz
    bpy.context.view_layer.update()
    return root, meshes

def bounds(obs):
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in obs:
        for cc in o.bound_box:
            w = o.matrix_world @ Vector(cc); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    return mn, mx

def lathe(name, c, prof, m, loc, segs=48, cap_bottom=True):
    """prof: list of (r, z) bottom->top; returns mesh object revolved around Z"""
    bm = bmesh.new(); rings = []
    for r, z in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            bm.faces.new((a[i], a[(i + 1) % segs], b[(i + 1) % segs], b[i]))
    if cap_bottom and prof[0][0] > 0: bm.faces.new(list(reversed(rings[0])))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.location = loc
    for p in me.polygons: p.use_smooth = True
    me.materials.append(m); return o

def logo_mat(name, dark=True):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(BRAND + ("DaKrasFilms_logo_dark.png" if dark else "DaKrasFilms_logo_white.png"))
    t.extension = 'CLIP'
    nt.links.new(t.outputs["Color"], P.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], P.inputs["Alpha"])
    P.inputs["Roughness"].default_value = 0.4
    m.blend_method = 'HASHED' if hasattr(m, "blend_method") else None
    return m

# ------------------------------------------------------------------ shared: paper cup, lid, coffee, steam
CUP_H = 0.118; CUP_R0 = 0.029; CUP_R1 = 0.044
def paper_cup(name, c, loc, with_logo=False):
    m_cup = mat("PaperCup", (0.95, 0.94, 0.9), 0.45)
    prof = [(CUP_R0, 0.0)] + [(CUP_R0 + (CUP_R1 - CUP_R0) * t / 10, CUP_H * t / 10) for t in range(1, 11)]
    outer = lathe(name, c, prof, m_cup, loc)
    sol = outer.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.0012; sol.offset = -1
    # sleeve band (warm brown) as a second, slightly larger lathe
    band = lathe(name + "_Band", c, [(CUP_R0 + (CUP_R1 - CUP_R0) * t + 0.0008, CUP_H * t) for t in (0.28, 0.5, 0.72)],
                 mat("CupBand", (0.55, 0.28, 0.12), 0.5), (0, 0, 0), cap_bottom=False)
    band.parent = outer
    rim = bpy.data.meshes.new(name + "_RimM"); bm = bmesh.new()
    bmesh.ops.create_circle(bm, segments=48, radius=CUP_R1); bm.to_mesh(rim); bm.free()
    bpy.ops.mesh.primitive_torus_add(major_radius=CUP_R1 + 0.0005, minor_radius=0.0018, major_segments=48, minor_segments=8,
                                     location=(0, 0, CUP_H))
    r = bpy.context.object; r.name = name + "_Rim"; r.data.materials.append(m_cup); link(r, c); r.parent = outer
    for p in r.data.polygons: p.use_smooth = True
    coffee = lathe(name + "_Coffee", c, [(CUP_R0 + (CUP_R1 - CUP_R0) * 0.88, CUP_H * 0.88 - 0.0002), (0.0, CUP_H * 0.88)],
                   mat("Coffee", (0.11, 0.05, 0.02), 0.08, coat=0.0), (0, 0, 0), cap_bottom=False)
    coffee.parent = outer
    if with_logo:
        # curved logo decal: a cylinder strip just outside the band, alpha from the logo image (967x414 -> ~2.34:1)
        bm = bmesh.new(); seg = 24; ang = R_(80); z0, z1 = CUP_H * 0.31, CUP_H * 0.69
        hgt = z1 - z0
        verts = []
        for i in range(seg + 1):
            a = -math.pi / 2 - ang / 2 + ang * i / seg
            for z in (z0, z1):
                rr = CUP_R0 + (CUP_R1 - CUP_R0) * (z / CUP_H) + 0.0016
                verts.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        for i in range(seg):
            bm.faces.new((verts[2 * i], verts[2 * i + 2], verts[2 * i + 3], verts[2 * i + 1]))
        me = bpy.data.meshes.new(name + "_LogoM"); bm.to_mesh(me); bm.free()
        uv = me.uv_layers.new()
        for p in me.polygons:
            for li in p.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                a = math.atan2(v.y, v.x); u = (a - (-math.pi / 2 - ang / 2)) / ang
                uv.data[li].uv = (u, (v.z - z0) / hgt)
        lo = bpy.data.objects.new(name + "_Logo", me); c.objects.link(lo); lo.parent = outer
        me.materials.append(logo_mat("LogoDark", True))
        for p in me.polygons: p.use_smooth = True
    return outer

def lid(name, c, loc):
    m = mat("CupLid", (0.97, 0.97, 0.96), 0.35)
    o = lathe(name, c, [(CUP_R1 + 0.003, -0.006), (CUP_R1 + 0.0035, 0.002), (CUP_R1 - 0.002, 0.006), (CUP_R1 - 0.008, 0.008),
                        (0.03, 0.009), (0.0, 0.0095)], m, loc, cap_bottom=False)
    o.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.001
    return o

def steam(name, c, loc, h=0.28, r=0.05, dens=0.6):
    """small volume steam column: noise density, fades upward; W keyed by the animation (no Scene Time)"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=h, location=(loc[0], loc[1], loc[2] + h / 2))
    o = bpy.context.object; o.name = name; link(o, c)
    m = bpy.data.materials.new(name + "_M"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    out = nt.nodes["Material Output"]
    vol = nt.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (1, 1, 1, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs["Scale"].default_value = 9.0
    nz.inputs["Detail"].default_value = 3.0
    wv = nt.nodes.new("ShaderNodeValue"); wv.name = "SteamW"; wv.outputs[0].default_value = 0.0
    up = nt.nodes.new("ShaderNodeValue"); up.name = "SteamRise"; up.outputs[0].default_value = 0.0
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = 'SUBTRACT'
    nt.links.new(sep.outputs["Z"], add.inputs[0]); nt.links.new(up.outputs[0], add.inputs[1])
    nt.links.new(sep.outputs["X"], comb.inputs["X"]); nt.links.new(sep.outputs["Y"], comb.inputs["Y"]); nt.links.new(add.outputs[0], comb.inputs["Z"])
    nt.links.new(comb.outputs[0], nz.inputs["Vector"]); nt.links.new(wv.outputs[0], nz.inputs["W"])
    # radial + vertical falloff
    rad = nt.nodes.new("ShaderNodeVectorMath"); rad.operation = 'DISTANCE'
    nt.links.new(tc.outputs["Generated"], rad.inputs[0])
    sepz = sep
    cx = nt.nodes.new("ShaderNodeCombineXYZ"); cx.inputs["X"].default_value = 0.5; cx.inputs["Y"].default_value = 0.5
    nt.links.new(sepz.outputs["Z"], cx.inputs["Z"]); nt.links.new(cx.outputs[0], rad.inputs[1])
    rf = nt.nodes.new("ShaderNodeMapRange"); rf.inputs["From Min"].default_value = 0.5; rf.inputs["From Max"].default_value = 0.1
    nt.links.new(rad.outputs["Value"], rf.inputs["Value"])
    vf = nt.nodes.new("ShaderNodeMapRange"); vf.inputs["From Min"].default_value = 1.0; vf.inputs["From Max"].default_value = 0.15
    nt.links.new(sepz.outputs["Z"], vf.inputs["Value"])
    nr = nt.nodes.new("ShaderNodeMapRange"); nr.inputs["From Min"].default_value = 0.5; nr.inputs["From Max"].default_value = 0.75
    nt.links.new(nz.outputs["Fac"], nr.inputs["Value"])
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; nt.links.new(rf.outputs[0], m1.inputs[0]); nt.links.new(vf.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(nr.outputs[0], m2.inputs[1])
    amt = nt.nodes.new("ShaderNodeValue"); amt.name = "SteamAmount"; amt.outputs[0].default_value = dens
    m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = 'MULTIPLY'; nt.links.new(m2.outputs[0], m3.inputs[0]); nt.links.new(amt.outputs[0], m3.inputs[1])
    m4 = nt.nodes.new("ShaderNodeMath"); m4.operation = 'MULTIPLY'; m4.inputs[1].default_value = 40.0 / max(r * 20, 1)
    nt.links.new(m3.outputs[0], m4.inputs[0]); nt.links.new(m4.outputs[0], vol.inputs["Density"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    o.visible_shadow = False
    return o

def key_steam(o, f0, f1, rate=0.9, rise=0.5):
    """linear keys on the steam material's W and rise values for frames f0..f1 (keyed, so a VO shift moves them)"""
    nt = o.active_material.node_tree
    for nm, per_s in (("SteamW", rate), ("SteamRise", rise)):
        v = nt.nodes[nm].outputs[0]
        for f in (f0, f1):
            v.default_value = per_s * (f - f0) / 60.0; v.keyframe_insert("default_value", frame=f)
    for fc in nt.animation_data.action.fcurves if hasattr(nt.animation_data.action, "fcurves") else []:
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'

