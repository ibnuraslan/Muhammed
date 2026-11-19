"""Real land for Part 5, from Part 4's code used as is (mary_celeste_p4/lib/terrain.py: AWS Terrain Tiles, open
data; mary_celeste_p4/shots/sets.py: santa_maria). This module only adds the Part 5 look: land seen across
kilometres of sea air, the far slopes fading into a warm haze (per-pixel, by distance from the camera).

    santa_maria(dist_km, bearing_deg)       the island at true scale, eastern point dist_km off (P4's function)
    gibraltar(origin_lonlat)                the Rock and the bay, true scale, origin_lonlat at world (0, 0)
"""
import os, sys, math
import numpy as np
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P4 = os.path.join(ROOT, "mary_celeste_p4")
for p in (os.path.join(P4, "lib"), os.path.join(P4, "shots")):
    if p not in sys.path:
        sys.path.append(p)


def hazed_land(name, rock=(0.36, 0.33, 0.29), scrub=(0.08, 0.11, 0.045), haze=(0.62, 0.66, 0.72), near=600.0, far=14000.0,
               max_haze=0.82):
    """Limestone and scrub by slope (flat ground green, steep faces bare rock), fine noise, and aerial perspective:
    the colour is mixed toward the haze colour with distance from the camera (and lit less: haze is emissive)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]; out = N["Material Output"]
    geo = N.new("ShaderNodeNewGeometry"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], sp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.02; nz.inputs['Detail'].default_value = 12
    L.new(geo.outputs['Position'], nz.inputs['Vector'])
    flat = N.new("ShaderNodeMapRange"); flat.inputs['From Min'].default_value = 0.6; flat.inputs['From Max'].default_value = 0.85
    L.new(sp.outputs['Z'], flat.inputs['Value'])
    f2 = N.new("ShaderNodeMath"); f2.operation = 'MULTIPLY'; L.new(flat.outputs[0], f2.inputs[0]); L.new(nz.outputs['Fac'], f2.inputs[1])
    f3 = N.new("ShaderNodeMath"); f3.operation = 'MULTIPLY'; f3.inputs[1].default_value = 1.6; L.new(f2.outputs[0], f3.inputs[0])
    f3.use_clamp = True
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    mx.inputs[6].default_value = (*rock, 1); mx.inputs[7].default_value = (*scrub, 1)
    L.new(f3.outputs[0], mx.inputs['Factor']); L.new(mx.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.95
    bump = N.new("ShaderNodeBump"); bump.inputs['Strength'].default_value = 0.3
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs['Scale'].default_value = 0.05; n2.inputs['Detail'].default_value = 8
    L.new(geo.outputs['Position'], n2.inputs['Vector']); L.new(n2.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs['Normal'], p.inputs['Normal'])
    # aerial perspective
    cd = N.new("ShaderNodeCameraData")
    hz = N.new("ShaderNodeMapRange"); hz.inputs['From Min'].default_value = near; hz.inputs['From Max'].default_value = far
    hz.inputs['To Max'].default_value = max_haze
    L.new(cd.outputs['View Distance'], hz.inputs['Value'])
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*haze, 1); em.inputs['Strength'].default_value = 1.0
    ms = N.new("ShaderNodeMixShader"); L.new(hz.outputs[0], ms.inputs[0]); L.new(p.outputs[0], ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2])
    L.new(ms.outputs[0], out.inputs['Surface'])
    return m


def santa_maria(dist_km=11.0, bearing_deg=90.0, haze=(0.66, 0.72, 0.8)):
    """Part 4's Santa Maria (real elevation, true scale), dressed in the hazed land material."""
    import sets as P4S                                   # mary_celeste_p4/shots/sets.py, as is
    o, size = P4S.santa_maria(dist_km=dist_km, bearing_deg=bearing_deg, z0=-0.5)
    o.data.materials.clear(); o.data.materials.append(hazed_land("santa_maria_land", haze=haze, near=2000, far=22000, max_haze=0.78))
    return o


GIB_BBOX = (-5.405, 36.100, -5.325, 36.170)


def gibraltar(origin=(-5.372, 36.132), haze=(0.85, 0.7, 0.58), zoom=13, out_w=700):
    """The Rock of Gibraltar and the head of the bay (real elevation, true scale; north = +Y, east = +X).
    `origin` (lon, lat) is placed at world (0, 0): the anchorage in the bay west of the town.
    Returns (land object, height(x, y) -> metres at a world point)."""
    import terrain as T                                   # mary_celeste_p4/lib/terrain.py, as is
    import bmesh
    e, lons, lats = T.grid(*GIB_BBOX, zoom=zoom, out_w=out_w)
    lat_m = 111320.0; lon_m = 111320.0 * math.cos(math.radians(36.135))
    sx = (GIB_BBOX[2] - GIB_BBOX[0]) * lon_m; sy = (GIB_BBOX[3] - GIB_BBOX[1]) * lat_m
    e = e.clip(-30, None)
    o = T.relief_mesh("Gibraltar", e, sx, sy, 1.0, 1.0, mat=hazed_land("gibraltar_land", rock=(0.42, 0.4, 0.37), scrub=(0.06, 0.09, 0.035), haze=haze, near=1500, far=14000, max_haze=0.45))
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if max(v.co.z for v in f.verts) < 1.0], context='FACES')   # the sea is the sea
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data); bm.free()
    ox, oy = T.lonlat_to_map(origin[0], origin[1], GIB_BBOX, (sx, sy))
    o.location = (-ox, -oy, -0.4)

    def height(x, y):
        lon = GIB_BBOX[0] + ((x + ox) / sx + 0.5) * (GIB_BBOX[2] - GIB_BBOX[0])
        lat = GIB_BBOX[1] + ((y + oy) / sy + 0.5) * (GIB_BBOX[3] - GIB_BBOX[1])
        return T.height_at(e, lons, lats, lon, lat) - 0.4

    def world(lon, lat):
        x, y = T.lonlat_to_map(lon, lat, GIB_BBOX, (sx, sy))
        return Vector((x - ox, y - oy, 0))
    return o, height, world
