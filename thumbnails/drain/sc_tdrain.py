"""Thumbnail set: a pitch-dark brick drain. A short stack of old bricks (one leaning against it), a big brilliant-cut
diamond on the top brick blazing under one narrow beam; wet floor, drips, haze; rats in the shadows (Poly Haven
street_rat, CC0)."""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Euler
from kit import pbr, box, cyl
from common import point_at
import ph

EXPOSURE = 0.0
BOUNCES = 12
TOP = Vector((0, 0, 0))          # set in build: the top face centre of the stack


def brick_mat(name, base=(0.30, 0.11, 0.065), seed=0):
    m = pbr(name, base, 0.55)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 55; nz.inputs['Detail'].default_value = 12; nz.inputs['Roughness'].default_value = 0.65
    nz.noise_dimensions = '4D'; nz.inputs['W'].default_value = seed * 3.7
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.9; bp.inputs['Distance'].default_value = 0.008
    L.new(nz.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 0.85
    mix.inputs[6].default_value = (*base, 1)
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[0].color = (0.12, 0.11, 0.1, 1)
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(nz.outputs['Fac'], cr.inputs[0]); L.new(cr.outputs[0], mix.inputs[7]); L.new(mix.outputs[2], p.inputs['Base Color'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.25; rr.inputs['To Max'].default_value = 0.8
    L.new(nz.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs['Result'], p.inputs['Roughness'])      # wet in the pits
    return m


HERE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))


def real_brick_mat(name, tint=(1, 1, 1), seed=0):
    """Scanned clay brick surface (cropped from Poly Haven red_brick_03, CC0, mirror-tiled so there is no mortar)."""
    import os, random
    rnd = random.Random(seed)
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    mp.inputs['Scale'].default_value = (4.6, 4.6, 4.6); mp.inputs['Location'].default_value = (rnd.random(), rnd.random(), rnd.random())
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    def img(f, color):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(HERE, f), check_existing=True)
        t.image.colorspace_settings.name = 'sRGB' if color else 'Non-Color'; t.projection = 'BOX'; t.projection_blend = 0.15
        L.new(mp.outputs[0], t.inputs['Vector']); return t
    d = img("brick_Diffuse.png", True)
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    L.new(d.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1)
    # grime blotches and crusts of old mortar
    def noise(scale, detail=6):
        n = N.new("ShaderNodeTexNoise"); n.noise_dimensions = '4D'; n.inputs['W'].default_value = seed * 5.1 + scale
        n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = 0.6
        L.new(tc.outputs['Object'], n.inputs['Vector']); return n
    def ramp(src, a, b, ca, cb):
        r = N.new("ShaderNodeValToRGB"); e = r.color_ramp.elements
        e[0].position = a; e[0].color = (*ca, 1); e[1].position = b; e[1].color = (*cb, 1); L.new(src.outputs['Fac'], r.inputs[0]); return r
    gr = ramp(noise(9), 0.35, 0.7, (0.35, 0.33, 0.32), (1, 1, 1))
    m2 = N.new("ShaderNodeMix"); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 1.0
    L.new(mx.outputs[2], m2.inputs[6]); L.new(gr.outputs[0], m2.inputs[7])
    mort = ramp(noise(22, 10), 0.6, 0.66, (0, 0, 0), (1, 1, 1))
    m3 = N.new("ShaderNodeMix"); m3.data_type = 'RGBA'; m3.inputs[7].default_value = (0.26, 0.25, 0.23, 1)
    L.new(mort.outputs[0], m3.inputs['Factor']); L.new(m2.outputs[2], m3.inputs[6]); L.new(m3.outputs[2], p.inputs['Base Color'])
    L.new(img("brick_Rough.png", False).outputs['Color'], p.inputs['Roughness'])
    nm = N.new("ShaderNodeNormalMap"); nm.inputs['Strength'].default_value = 2.2
    L.new(img("brick_nor_gl.png", False).outputs['Color'], nm.inputs['Color']); L.new(nm.outputs[0], p.inputs['Normal'])
    p.inputs['Coat Weight'].default_value = 0.25; p.inputs['Coat Roughness'].default_value = 0.2      # damp
    return m


def brick(name, loc, rot, mat):
    o = box(name, loc, (0.215, 0.102, 0.065), mat, bevel=0.006, rot=rot)
    o.modifiers["bevel"].segments = 3
    sub = o.modifiers.new("sub", 'SUBSURF'); sub.subdivision_type = 'SIMPLE'; sub.levels = 4; sub.render_levels = 5
    tx = bpy.data.textures.new(name + "Chip", 'CLOUDS'); tx.noise_scale = 0.018; tx.noise_depth = 4; tx.noise_type = 'HARD_NOISE'
    dp = o.modifiers.new("chip", 'DISPLACE'); dp.texture = tx; dp.strength = -0.005; dp.mid_level = 0.6; dp.texture_coords = 'OBJECT'
    bpy.ops.object.shade_smooth()
    return o


def diamond(name, r=0.024):
    """A round brilliant: table, 16-facet crown, girdle, pavilion to a point. Origin at the girdle centre."""
    n = 16
    bm = bmesh.new()
    t_r, c_h, g_h, p_h = r * 0.56, r * 0.32, r * 0.03, r * 0.86
    table = [bm.verts.new((t_r * math.cos(2 * math.pi * (k + 0.5) / n), t_r * math.sin(2 * math.pi * (k + 0.5) / n), c_h + g_h)) for k in range(n)]
    gt = [bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), g_h)) for k in range(n)]
    gb = [bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), -g_h)) for k in range(n)]
    tip = bm.verts.new((0, 0, -p_h))
    bm.faces.new(table)
    for k in range(n):
        k1 = (k + 1) % n
        bm.faces.new((table[k], gt[k1], table[k1])); bm.faces.new((table[k], gt[k], gt[k1]))      # crown facets
        bm.faces.new((gt[k], gb[k], gb[k1], gt[k1]))                                              # girdle
        mid = bm.verts.new(((gb[k].co + gb[k1].co) / 2) * 0.62 + Vector((0, 0, -p_h * 0.38)))  # pavilion: two facets per segment
        bm.faces.new((gb[k1], gb[k], mid)); bm.faces.new((gb[k], tip, mid)); bm.faces.new((mid, tip, gb[k1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    m = bpy.data.materials.new(name + "Glass"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n_ in list(N):
        if n_.type != 'OUTPUT_MATERIAL':
            N.remove(n_)
    g = N.new("ShaderNodeBsdfGlass"); g.inputs['IOR'].default_value = 2.42; g.inputs['Roughness'].default_value = 0.0
    g.inputs['Color'].default_value = (1, 1, 1, 1)
    if 'Dispersion' in g.inputs:
        g.inputs['Dispersion'].default_value = 0.06
    L.new(g.outputs[0], next(n_ for n_ in N if n_.type == 'OUTPUT_MATERIAL').inputs['Surface'])
    me.materials.append(m)
    return o


def build(variant=None):
    global TOP
    c = {}
    w = bpy.context.scene.world or bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs['Color'].default_value = (0.0, 0.0, 0.0, 1); w.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.0
    # tunnel: wet mud floor, brick walls arching up into black
    floor = ph.texture("brown_mud_02", scale=1.2, tint=(0.35, 0.33, 0.3))
    pb = floor.node_tree.nodes["Principled BSDF"]; pb.inputs['Coat Weight'].default_value = 0.8; pb.inputs['Coat Roughness'].default_value = 0.08
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.8, 0)); f = bpy.context.active_object; f.scale = (4, 4, 1); f.data.materials.append(floor)
    wall = ph.texture("brick_wall_02", scale=1.6, tint=(0.22, 0.19, 0.17))
    pw = wall.node_tree.nodes["Principled BSDF"]; pw.inputs['Coat Weight'].default_value = 0.5; pw.inputs['Coat Roughness'].default_value = 0.15
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.15, depth=12, location=(0, 4.0, 0.75), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.active_object; t.name = "Tunnel"; t.data.materials.append(wall); t.data.shade_smooth()
    bm = bmesh.new(); bm.from_mesh(t.data)
    bmesh.ops.delete(bm, geom=[f_ for f_ in bm.faces if abs(f_.normal.y) > 0.9], context='FACES')       # open ends
    bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(t.data); bm.free()
    # a shallow water channel down the middle, glossy black
    water = pbr("Water", (0.004, 0.005, 0.005), 0.12); water.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.3
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0.0, 1.2, 0.004)); wa = bpy.context.active_object; wa.scale = (0.7, 5, 1); wa.data.materials.append(water)
    # the stack: three bricks, a fourth leaning on it
    mats = [real_brick_mat(f"Brick{k}", (0.5 + 0.06 * k, 0.36 + 0.03 * k, 0.33), k) for k in range(4)]
    h = 0.065
    brick("B0", (0.0, 0.0, h / 2), (0, 0, 0.08), mats[0])
    brick("B1", (0.012, -0.006, h * 1.5 + 0.001), (0, 0, -0.12), mats[1])
    brick("B2", (-0.006, 0.004, h * 2.5 + 0.002), (0, 0, 0.21), mats[2])
    lean = brick("B3", (0.19, 0.02, 0.085), (0, math.radians(-52), 0.35), mats[3])
    brick("B4", (-0.34, 0.12, h / 2), (0, 0, -0.18), mats[1])           # a loose one front-left
    brick("B5", (-0.55, 0.9, h / 2), (0, 0, 0.7), mats[0])               # and one far back in the dark
    TOP = Vector((-0.006, 0.004, h * 3 + 0.003))
    d = diamond("Diamond", 0.055); d.location = TOP + Vector((0, 0, 0.055 * 0.86 - 0.005)); d.rotation_euler = (0, 0, 0.2)
    # tipped onto a pavilion facet slightly so the table faces the camera a little
    d.rotation_euler = (math.radians(-10), math.radians(4), 0.2)
    c["diamond"] = d; c["top"] = TOP
    # rats, in the dark around it
    rats = []
    for k, (loc, rz, s) in enumerate((((-0.22, -0.2, 0), 0.6, 1.7), ((0.3, 0.13, 0), -2.3, 1.6), ((-0.14, 0.5, 0), 2.4, 1.4))):
        try:
            r, ms = ph.model("street_rat", loc=loc, rot_z=rz, scale=s)
            rats.append((r, ms))
        except Exception as e:
            print("rat failed", e)
    c["rats"] = rats
    # sewer junk in the dark
    for aid, loc, rz, sc in ():
        try:
            ph.model(aid, loc=loc, rot_z=rz, scale=sc)
        except Exception as e:
            print("junk failed", aid, e)
    return c


MOVES = {}
