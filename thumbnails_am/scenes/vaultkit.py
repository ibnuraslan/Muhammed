"""Shared pieces for the dark-premium Antwerp thumbnails: blue-grey monochrome materials, brushed steel,
brand-yellow paint, and a detailed round vault door."""
import math
import bpy
from mathutils import Vector
import sets as S, ship as SH

def s2l(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
BRAND = tuple(s2l(c) for c in (227, 255, 0))


def mono(name, v, rough=0.45, metal=0.0, var=0.12, scale=4.0):
    """Blue-grey at value v, with a little noise so surfaces are not flat."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]; p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 1 - var; mr.inputs['To Max'].default_value = 1 + var * 0.5
    L.new(nz.outputs['Fac'], mr.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs[6].default_value = (v * 0.78, v * 0.9, v * 1.12, 1)
    cm = N.new("ShaderNodeCombineColor")
    for k in range(3):
        L.new(mr.outputs[0], cm.inputs[k])
    L.new(cm.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


def yellow(name, mult=1.0, rough=0.42):
    """Brand yellow paint with form: AO pushes the cavities to olive, a light coat sheen."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]; p.inputs['Roughness'].default_value = rough
    p.inputs['Coat Weight'].default_value = 0.3; p.inputs['Coat Roughness'].default_value = 0.2
    c = tuple(x * mult for x in BRAND)
    ao = N.new("ShaderNodeAmbientOcclusion"); ao.inputs['Distance'].default_value = 0.03; ao.samples = 8
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (c[0] * 0.2, c[1] * 0.22, 0.005, 1)
    mx.inputs[7].default_value = (*c, 1); L.new(ao.outputs['AO'], mx.inputs['Factor']); L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


# brushed grain: fine stretched noise into roughness and a little into colour
def brush(m, scratch=0.0):
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp_ = N.new("ShaderNodeMapping"); mp_.inputs['Scale'].default_value = (400, 6, 400)
    L.new(tc.outputs['Object'], mp_.inputs['Vector'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 4; L.new(mp_.outputs[0], nz.inputs['Vector'])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 0.18; mr.inputs['To Max'].default_value = 0.34
    L.new(nz.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs[0], p.inputs['Roughness'])
    if scratch:
        # pry marks and scratches: bright bare-steel gouges near the lock edge
        sm = N.new("ShaderNodeMapping"); sm.inputs['Scale'].default_value = (60, 3, 60); sm.inputs['Rotation'].default_value = (0, 0, 0.5)
        L.new(tc.outputs['Object'], sm.inputs['Vector'])
        sn = N.new("ShaderNodeTexNoise"); sn.inputs['Scale'].default_value = 2.0; sn.inputs['Detail'].default_value = 10; L.new(sm.outputs[0], sn.inputs['Vector'])
        sr = N.new("ShaderNodeMapRange"); sr.inputs['From Min'].default_value = 0.62; sr.inputs['From Max'].default_value = 0.7
        L.new(sn.outputs['Fac'], sr.inputs['Value'])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[7].default_value = (0.75, 0.78, 0.82, 1)
        L.new(sr.outputs[0], mx.inputs['Factor']); L.new(p.inputs['Base Color'].links[0].from_socket, mx.inputs[6])
        L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


def vault_door(Rd, steel, plate, black, face=None, bolt=None, name="vault_door"):
    """Detailed round vault door. Local frame: hinge pin at the origin, door disc centred at x = -Rd, outer face
    toward -y. face/bolt: optional materials for the inner face (+y side) and the locking bolts."""
    leaf = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(leaf)
    def part(o):
        o.parent = leaf; return o
    for (y0, y1, rr) in ((0.0, -0.32, Rd), (-0.32, -0.52, Rd - 0.07), (-0.52, -0.62, Rd - 0.16)):
        part(SH.cyl("door_tier", (-Rd, y0, 0), (-Rd, y1, 0), rr, mat=steel, verts=128))
        bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.018, major_segments=128, minor_segments=8,
                                         location=(-Rd, y1, 0), rotation=(math.pi / 2, 0, 0))
        t_ = bpy.context.active_object; t_.data.materials.append(steel); part(t_)
    for rr in (Rd * 0.62, Rd * 0.42):
        bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.014, major_segments=96, minor_segments=8,
                                         location=(-Rd, -0.625, 0), rotation=(math.pi / 2, 0, 0))
        t_ = bpy.context.active_object; t_.data.materials.append(plate); part(t_)
    hub = Vector((-Rd, -0.62, 0))
    part(SH.cyl("hub", hub, hub + Vector((0, -0.1, 0)), 0.13, mat=steel, verts=48))
    for k in range(3):
        a_ = math.radians(90 + 120 * k)
        tip = hub + Vector((math.cos(a_) * 0.48, -0.09, math.sin(a_) * 0.48))
        part(SH.cyl("spoke", hub + Vector((0, -0.09, 0)), tip, 0.028, mat=steel, verts=16))
        part(SH.cyl("knob", tip, tip + Vector((0, -0.08, 0)), 0.04, mat=steel, verts=16))
    dial = hub + Vector((0.45, 0, 0.45))
    part(SH.cyl("dial", dial, dial + Vector((0, -0.04, 0)), 0.09, mat=black, verts=48))
    for k in range(18):
        a_ = 2 * math.pi * k / 18
        c0 = Vector((-Rd + math.cos(a_) * (Rd - 0.05), -0.16, math.sin(a_) * (Rd - 0.05)))
        c1 = Vector((-Rd + math.cos(a_) * (Rd + 0.18), -0.16, math.sin(a_) * (Rd + 0.18)))
        part(SH.cyl("bolt", c0, c1, 0.055, mat=bolt or steel, verts=24))
    # inner face: bolt-work cover plate with concentric rings and the bolt bars (the face seen when open)
    fm = face or plate
    part(SH.cyl("inner_plate", (-Rd, 0.0, 0), (-Rd, 0.04, 0), Rd * 0.86, mat=fm, verts=128))
    for rr in (Rd * 0.7, Rd * 0.45, Rd * 0.2):
        bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.025, major_segments=96, minor_segments=10,
                                         location=(-Rd, 0.045, 0), rotation=(math.pi / 2, 0, 0))
        t_ = bpy.context.active_object; t_.data.materials.append(bolt or steel); part(t_)
    for k in range(18):
        a_ = 2 * math.pi * k / 18
        part(SH.cyl("bolt_bar", (-Rd + math.cos(a_) * Rd * 0.2, 0.06, math.sin(a_) * Rd * 0.2),
                    (-Rd + math.cos(a_) * Rd * 0.82, 0.06, math.sin(a_) * Rd * 0.82), 0.022, mat=bolt or steel, verts=12))
    part(SH.cyl("gear", (-Rd, 0.04, 0), (-Rd, 0.11, 0), 0.16, mat=bolt or steel, verts=36))
    for dz in (-0.55, 0.55):
        part(S.box("hinge_arm", (0.12, -0.3, dz), (0.34, 0.22, 0.18), steel, bevel=0.02))
    part(SH.cyl("hinge_pin", (0.28, -0.3, -0.85), (0.28, -0.3, 0.85), 0.08, mat=steel, verts=32))
    return leaf
