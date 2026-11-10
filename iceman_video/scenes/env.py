"""Shared outdoor-environment pieces: fractured boulders, rock material, camera-distance haze."""
import math
import numpy as np
import bpy, bmesh
from common import nodes_of
from terrain import perlin


def add_fog(mat, color, density=0.012, fog_max=1.0):
    """Wrap a material's surface output with camera-distance haze (cheap aerial perspective)."""
    nt = mat.node_tree; N = nt.nodes; L = nt.links
    out = [n for n in N if n.type == 'OUTPUT_MATERIAL'][0]
    src = out.inputs['Surface'].links[0].from_socket
    cam = N.new("ShaderNodeCameraData")
    k = N.new("ShaderNodeMath"); k.operation = 'MULTIPLY'; k.inputs[1].default_value = -density
    L.new(cam.outputs['View Distance'], k.inputs[0])
    ex = N.new("ShaderNodeMath"); ex.operation = 'EXPONENT'; L.new(k.outputs[0], ex.inputs[0])
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = fog_max; L.new(ex.outputs[0], inv.inputs[1])
    inv.use_clamp = True
    lp = N.new("ShaderNodeLightPath")
    g = N.new("ShaderNodeMath"); g.operation = 'MULTIPLY'; L.new(inv.outputs[0], g.inputs[0]); L.new(lp.outputs['Is Camera Ray'], g.inputs[1])
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1)
    mx = N.new("ShaderNodeMixShader"); L.new(g.outputs[0], mx.inputs['Fac']); L.new(src, mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])


def rock_material(name="Rock", snow=True):
    m = bpy.data.materials.new(name); nt, N, L = nodes_of(m); N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord"); geo = N.new("ShaderNodeNewGeometry")
    n1 = N.new("ShaderNodeTexNoise"); n1.inputs['Scale'].default_value = 9; n1.inputs['Detail'].default_value = 14
    L.new(tc.outputs['Object'], n1.inputs['Vector'])
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs['Scale'].default_value = 4; vor.feature = 'DISTANCE_TO_EDGE'
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.018, 0.018, 0.02, 1)
    cr.color_ramp.elements[1].color = (0.13, 0.12, 0.11, 1)
    L.new(n1.outputs['Fac'], cr.inputs['Fac'])
    rock = N.new("ShaderNodeBsdfPrincipled"); L.new(cr.outputs['Color'], rock.inputs['Base Color'])
    rock.inputs['Roughness'].default_value = 0.8
    hb_ = N.new("ShaderNodeMath"); hb_.operation = 'MULTIPLY_ADD'; hb_.inputs[1].default_value = 0.6
    L.new(n1.outputs['Fac'], hb_.inputs[0]); L.new(vor.outputs['Distance'], hb_.inputs[2])
    bump = N.new("ShaderNodeBump"); bump.inputs['Strength'].default_value = 1.0; bump.inputs['Distance'].default_value = 0.05
    L.new(hb_.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], rock.inputs['Normal'])
    if not snow:
        L.new(rock.outputs[0], out.inputs['Surface']); return m
    sn = N.new("ShaderNodeBsdfPrincipled"); sn.inputs['Base Color'].default_value = (0.82, 0.86, 0.93, 1)
    sn.inputs['Roughness'].default_value = 0.6; sn.inputs['Subsurface Weight'].default_value = 0.5
    sn.inputs['Subsurface Radius'].default_value = (0.5, 0.8, 1.0); sn.inputs['Subsurface Scale'].default_value = 0.02
    L.new(bump.outputs['Normal'], sn.inputs['Normal'])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], sep.inputs[0])
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs['Scale'].default_value = 3; n2.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], n2.inputs['Vector'])
    ad = N.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.5
    L.new(n2.outputs['Fac'], ad.inputs[0]); L.new(sep.outputs['Z'], ad.inputs[2])
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].position = 0.95; rp.color_ramp.elements[1].position = 1.02
    L.new(ad.outputs[0], rp.inputs['Fac'])
    mx = N.new("ShaderNodeMixShader"); L.new(rp.outputs['Color'], mx.inputs['Fac']); L.new(rock.outputs[0], mx.inputs[1]); L.new(sn.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    return m


def make_rock(seed, mat):
    """Fractured boulder: lumpy sphere clamped by random half-spaces (angular facets)."""
    r = np.random.default_rng(seed)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    V = np.array([v.co[:] for v in bm.verts])
    n = (perlin(V[:, 0] * 1.3 + seed, V[:, 1] * 1.3, seed) + perlin(V[:, 1] * 1.3, V[:, 2] * 1.3 + seed, seed + 1)) * 0.18
    V *= (1 + n)[:, None]
    for _ in range(r.integers(6, 11)):
        nrm = r.normal(size=3); nrm /= np.linalg.norm(nrm)
        dist = r.uniform(0.55, 0.85)
        dd = V @ nrm - dist
        V -= np.maximum(dd, 0)[:, None] * nrm[None, :]
    V *= r.uniform(0.6, 1.4, 3)
    V[:, 2] = np.maximum(V[:, 2], -0.3)
    fine = perlin(V[:, 0] * 7, V[:, 1] * 7 + V[:, 2] * 3, seed + 7) * 0.03 + perlin(V[:, 0] * 23 + V[:, 2] * 5, V[:, 1] * 23, seed + 9) * 0.012
    lens = np.linalg.norm(V, axis=1, keepdims=True)
    V += V / np.maximum(lens, 1e-6) * fine[:, None]
    for v, p in zip(bm.verts, V): v.co = p
    me = bpy.data.meshes.new(f"rock{seed}"); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    me.materials.append(mat)
    return me
