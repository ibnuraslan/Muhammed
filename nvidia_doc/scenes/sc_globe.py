"""Earth at night (Natural Earth land + generated city lights): the camera turns from the United States across the
Pacific toward China while an amber route of chips draws on and is cut off by a red barrier short of China."""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.2
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")
R = 1.0


def ll(lon, lat, r=R):
    lo, la = math.radians(lon), math.radians(lat)
    return Vector((r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)))


def img_node(N, name, colorspace="Non-Color"):
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(GEN, name)); t.image.colorspace_settings.name = colorspace
    t.interpolation = 'Cubic'
    return t


def earth_material():
    m = bpy.data.materials.new("Earth"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    # equirect mapping from object coordinates (lon = atan2(y, x), lat = asin(z))
    sep = N.new("ShaderNodeSeparateXYZ"); nrm = N.new("ShaderNodeVectorMath"); nrm.operation = 'NORMALIZE'
    L.new(tc.outputs['Object'], nrm.inputs[0]); L.new(nrm.outputs[0], sep.inputs[0])
    at = N.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; L.new(sep.outputs['Y'], at.inputs[0]); L.new(sep.outputs['X'], at.inputs[1])
    u = N.new("ShaderNodeMath"); u.operation = 'MULTIPLY_ADD'; u.inputs[1].default_value = 1 / (2 * math.pi); u.inputs[2].default_value = 0.5
    L.new(at.outputs[0], u.inputs[0])
    asn = N.new("ShaderNodeMath"); asn.operation = 'ARCSINE'; L.new(sep.outputs['Z'], asn.inputs[0])
    v = N.new("ShaderNodeMath"); v.operation = 'MULTIPLY_ADD'; v.inputs[1].default_value = 1 / math.pi; v.inputs[2].default_value = 0.5
    L.new(asn.outputs[0], v.inputs[0])
    uv = N.new("ShaderNodeCombineXYZ"); L.new(u.outputs[0], uv.inputs[0]); L.new(v.outputs[0], uv.inputs[1])
    land = img_node(N, "earth_land.png"); lines = img_node(N, "earth_lines.png"); lights = img_node(N, "earth_lights.png")
    for t_ in (land, lines, lights):
        L.new(uv.outputs[0], t_.inputs['Vector'])
    base = N.new("ShaderNodeMix"); base.data_type = 'RGBA'
    L.new(land.outputs['Color'], base.inputs['Factor']); base.inputs[6].default_value = (0.004, 0.008, 0.016, 1); base.inputs[7].default_value = (0.03, 0.035, 0.045, 1)
    L.new(base.outputs[2], p.inputs['Base Color'])
    rough = N.new("ShaderNodeMapRange"); rough.inputs['To Min'].default_value = 0.25; rough.inputs['To Max'].default_value = 0.85
    L.new(land.outputs['Color'], rough.inputs['Value']); L.new(rough.outputs[0], p.inputs['Roughness'])   # ocean glossy, land matte
    em = N.new("ShaderNodeMix"); em.data_type = 'RGBA'; em.blend_type = 'ADD'; em.inputs['Factor'].default_value = 1.0
    c1 = N.new("ShaderNodeMix"); c1.data_type = 'RGBA'; c1.blend_type = 'MULTIPLY'; c1.inputs['Factor'].default_value = 1.0
    L.new(lights.outputs['Color'], c1.inputs[6]); c1.inputs[7].default_value = (1.0, 0.72, 0.38, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = 'RGBA'; c2.blend_type = 'MULTIPLY'; c2.inputs['Factor'].default_value = 1.0
    L.new(lines.outputs['Color'], c2.inputs[6]); c2.inputs[7].default_value = (0.08, 0.12, 0.18, 1)
    L.new(c1.outputs[2], em.inputs[6]); L.new(c2.outputs[2], em.inputs[7])
    L.new(em.outputs[2], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = 0.55
    return m


def build(variant=None):
    world_flat((0.0, 0.0, 0.0), 1.0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=256, ring_count=128, radius=R, location=(0, 0, 0))
    earth = bpy.context.active_object; earth.data.materials.append(earth_material()); bpy.ops.object.shade_smooth()
    # atmosphere: thin shell, fresnel-weighted blue emission (limb glow)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=R * 1.018, location=(0, 0, 0))
    atm = bpy.context.active_object; bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new("Atmo"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); lw = N.new("ShaderNodeLayerWeight"); lw.inputs['Blend'].default_value = 0.35
    pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 3.0; L.new(lw.outputs['Facing'], pw.inputs[0])
    emi = N.new("ShaderNodeEmission"); emi.inputs['Color'].default_value = (0.25, 0.5, 1.0, 1); L.new(pw.outputs[0], emi.inputs['Strength'])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeAddShader")
    L.new(emi.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(mx.outputs[0], out.inputs['Surface'])
    atm.data.materials.append(m)
    # stars
    star = emissive("Star", (1, 1, 1), 6)
    rng = np.random.default_rng(1)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.006, location=(0, 0, -100)); sp = bpy.context.active_object; sp.data.materials.append(star)
    for k in range(900):
        d = Vector(rng.normal(0, 1, 3)).normalized() * 40
        o = instance(sp, tuple(d)); s_ = rng.uniform(0.3, 1.6); o.scale = (s_, s_, s_)
    # the route: Washington -> Beijing across the Pacific, as a glowing tube (bevel_factor_end animates)
    a, b = (-77.04, 38.91), (116.40, 39.90)
    pts = []
    dl = (b[0] - a[0] + 540) % 360 - 180          # shortest way: west over the Pacific
    for k in range(121):
        t = k / 120
        lon = a[0] + dl * t; lat = a[1] + (b[1] - a[1]) * t + 14 * math.sin(math.pi * t)
        pts.append(ll(lon, lat, R * (1.004 + 0.09 * math.sin(math.pi * t))))
    cu = bpy.data.curves.new("Route", 'CURVE'); cu.dimensions = '3D'
    spl = cu.splines.new('POLY'); spl.points.add(len(pts) - 1)
    for p_, q in zip(spl.points, pts): p_.co = (*q, 1)
    cu.bevel_depth = 0.0045; cu.bevel_resolution = 3; cu.bevel_factor_end = 0.0
    route = bpy.data.objects.new("Route", cu); bpy.context.collection.objects.link(route)
    route.data.materials.append(emissive("RouteGlow", (1.0, 0.55, 0.15), 4.0))
    # the barrier, 62% of the way: a thin red ring standing across the route
    cut = 0.86; k = int(cut * 120); bp = pts[k]; tan = (pts[k + 1] - pts[k - 1]).normalized()   # just short of the China coast; bp = pts[k]; tan = (pts[k + 1] - pts[k - 1]).normalized()
    bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.0035, location=tuple(bp))
    ring = bpy.context.active_object; ring.data.materials.append(emissive("Barrier", (1.0, 0.08, 0.06), 30))
    ring.rotation_euler = tan.to_track_quat('Z', 'Y').to_euler(); ring.scale = (0, 0, 0)
    for lon, lat, name in ((-77.04, 38.91, "WashingtonDot"), (116.40, 39.90, "BeijingDot")):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.008, location=tuple(ll(lon, lat, R * 1.003)))
        bpy.context.active_object.data.materials.append(emissive(name, (1, 1, 1), 25))
    sunl = bpy.data.lights.new("Sun", 'SUN'); sunl.energy = 0.4; sunl.color = (0.6, 0.7, 1.0)
    so = bpy.data.objects.new("Sun", sunl); bpy.context.collection.objects.link(so); so.rotation_euler = (0.6, 0.3, 2.6)
    return dict(route=route, cu=cu, ring=ring, cut=cut, pts=pts)


def _anim(c, t):
    draw = ease(min(1.0, (t - 0.1) / 0.7))
    c["cu"].bevel_factor_end = min(draw, c["cut"])
    s = ease((t - 0.74) / 0.1)
    c["ring"].scale = (s, s, s)


def _cam(c, t):
    e = ease(t)
    lon = -92 - 128 * e                     # from over the US, west across the Pacific, ending on the China coast
    lat = 40 + 8 * math.sin(math.pi * e)
    pos = ll(lon + 6, lat - 14, 2.9 - 0.35 * e)
    target = ll(lon - 22, lat + 4, 0.35)
    return (pos, target, 35)


MOVES = {"pacific_turn": dict(kind="anim", far=60.0, cam=_cam, anim=_anim)}
