"""Shared case devices for both halves of the film (A: Cold Open-Ch2, B: Ch3-5). Import, don't copy.
Realistic 3D only (Cycles, look v5): no flat, vector or illustrated graphics.

  ink_mat / ribbon / ctrl_empty / set_reveal : a line laid on real ground or paper that draws itself on as its control
                                             empty moves (a transform, so it bakes)
  thread(...)   red wool string between two points, revealed the same way
  void_spot     object-on-black: black world, one hard top light, glossy black floor fading into the dark
"""
import math, os
import bpy
from mathutils import Vector
from kit import pbr

def _reveal_value(m, ctrl):
    """A Value node in m driven by ctrl.location.x (0..1 = how much of the stroke is drawn)."""
    N = m.node_tree.nodes
    val = N.new("ShaderNodeValue"); val.name = "Reveal"
    fc = val.outputs[0].driver_add("default_value"); d = fc.driver; d.type = 'SCRIPTED'
    var = d.variables.new(); var.name = "r"; var.type = 'TRANSFORMS'
    var.targets[0].id = ctrl; var.targets[0].transform_type = 'LOC_X'; var.targets[0].transform_space = 'WORLD_SPACE'
    d.expression = "r"
    return val


def ink_mat(name, color=(0.42, 0.015, 0.012), ctrl=None, rough=0.45, emit=0.0):
    """Felt-marker ink: slightly glossy, a darker core; transparent beyond the drawn length (UV.x > reveal)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]; out = N["Material Output"]
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough
    if emit:
        p.inputs['Emission Color'].default_value = (*color, 1); p.inputs['Emission Strength'].default_value = emit
    if ctrl is None:
        return m
    uv = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs['UV'], sep.inputs[0])
    val = _reveal_value(m, ctrl)
    lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'
    L.new(sep.outputs['X'], lt.inputs[0]); L.new(val.outputs[0], lt.inputs[1])
    tr = N.new("ShaderNodeBsdfTransparent"); mix = N.new("ShaderNodeMixShader")
    L.new(lt.outputs[0], mix.inputs['Fac']); L.new(tr.outputs[0], mix.inputs[1]); L.new(p.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m


def ribbon(name, pts, width, mat_, dz=0.00025):
    """A flat strip on the paper along pts (world, already lifted); UV.x runs 0..1 along its length."""
    P = [Vector(p) for p in pts]
    L = [0.0]
    for a, b in zip(P, P[1:]):
        L.append(L[-1] + (b - a).length)
    tot = max(L[-1], 1e-6)
    verts, faces, us = [], [], []
    for k, p in enumerate(P):
        t = (P[min(k + 1, len(P) - 1)] - P[max(k - 1, 0)]); t.z = 0; t.normalize()
        n = Vector((-t.y, t.x, 0)) * (width / 2)
        verts += [tuple(p - n + Vector((0, 0, dz))), tuple(p + n + Vector((0, 0, dz)))]; us.append(L[k] / tot)
    for k in range(len(P) - 1):
        faces.append((2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; uvl.data[li].uv = (us[vi // 2], vi % 2)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat_)
    return o


def ctrl_empty(name):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    e.empty_display_size = 0.01; e.location = (0.0, 0.0, -5.0)
    return e


def set_reveal(ctrl, f):
    ctrl.location.x = max(0.0, min(1.001, f))



def thread(name, a, b, lift=0.010, sag=0.006, r=0.0007, color=(0.50, 0.02, 0.02), n=60):
    """Red wool between two world points (pin heads), sagging a little; revealed from a to b like ink."""
    ctrl = ctrl_empty(name + "Ctrl")
    a = Vector(a); b = Vector(b)
    pts = []
    for k in range(n + 1):
        t = k / n; p = a.lerp(b, t); p.z += lift - sag * 4 * t * (1 - t) * 0 - sag * math.sin(math.pi * t)
        pts.append(p)
    # a thin tube with UV.x along the length
    seg = 8; verts, faces, uvs = [], [], []
    for k, p in enumerate(pts):
        t = (pts[min(k + 1, n)] - pts[max(k - 1, 0)]).normalized()
        u = t.cross(Vector((0, 0, 1))); u = u.normalized() if u.length > 1e-6 else Vector((1, 0, 0)); w_ = t.cross(u)
        for s in range(seg):
            ang = 2 * math.pi * s / seg; verts.append(tuple(p + (u * math.cos(ang) + w_ * math.sin(ang)) * r))
    for k in range(n):
        for s in range(seg):
            a_ = k * seg + s; b_ = k * seg + (s + 1) % seg
            faces.append((a_, b_, b_ + seg, a_ + seg))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; uvl.data[li].uv = ((vi // seg) / n, (vi % seg) / seg)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    m = ink_mat(name + "M", color, ctrl, rough=0.9)
    m.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.6
    o.data.materials.append(m)
    return o, ctrl


# ---------------------------------------------------------------------------------------------- object on black
def void_spot(center=(0, 0, 0), key_energy=420.0, key_size=0.6, height=1.6, warm=(1.0, 0.92, 0.82), rim=0.0, floor=True, spread=40.0, key_off=None):
    """Black world, one hard area light straight above (a little behind), a glossy black floor that fades out."""
    import common
    common.world_flat((0.0, 0.0, 0.0), 0.0)
    c = Vector(center)
    l = bpy.data.lights.new("VoidKey", 'AREA'); l.energy = key_energy; l.size = key_size; l.color = warm
    lo = bpy.data.objects.new("VoidKey", l); bpy.context.scene.collection.objects.link(lo)
    lo.location = c + (Vector(key_off) if key_off else Vector((0.0, 0.25, height))); lo.rotation_euler = (c - lo.location).to_track_quat('-Z', 'Y').to_euler()
    l.spread = math.radians(spread)
    if rim:
        r_ = bpy.data.lights.new("VoidRim", 'AREA'); r_.energy = rim; r_.size = 0.3; r_.color = (0.8, 0.88, 1.0)
        ro = bpy.data.objects.new("VoidRim", r_); bpy.context.scene.collection.objects.link(ro)
        ro.location = c + Vector((0.9, 1.0, 0.5)); ro.rotation_euler = (c - ro.location).to_track_quat('-Z', 'Y').to_euler()
    if floor:
        m = bpy.data.materials.new("VoidFloor"); m.use_nodes = True
        N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        p.inputs['Base Color'].default_value = (0.004, 0.004, 0.0045, 1); p.inputs['Roughness'].default_value = 0.22
        # fade the floor's reflection out with distance from the centre (radial falloff to pure black)
        tc = N.new("ShaderNodeTexCoord"); gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
        mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (0.9, 0.9, 0.9)
        L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], gr.inputs['Vector'])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 0.9; mr.inputs['To Max'].default_value = 0.35
        L.new(gr.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs[0], p.inputs['Roughness'])
        sp = N.new("ShaderNodeMath"); sp.operation = 'MULTIPLY'; sp.inputs[1].default_value = 0.35
        L.new(gr.outputs['Fac'], sp.inputs[0]); L.new(sp.outputs[0], p.inputs['Specular IOR Level'])
        bpy.ops.mesh.primitive_plane_add(size=8, location=(c.x, c.y, c.z)); f = bpy.context.object; f.name = "VoidFloor"
        f.data.materials.append(m)
    return lo
