"""Open Atlantic: Blender Ocean (FFT) surface with foam, a far-field sea to the horizon, a Poly Haven sky,
sea haze, hull foam (geometry proximity) and bow spray (a point cloud Cycles renders as droplets)."""
import math, random
import numpy as np
import bpy
from mathutils import Vector
import ph

SKY = "kloppenheim_06_puresky"


def sky(strength=1.0, rot_deg=0.0, res="8k", aid=SKY):
    w, bg, mp = ph.world_hdri(aid, strength=strength, rot_z=math.radians(rot_deg), res=res)
    return w


def water_material(name="sea", deep=(0.0012, 0.017, 0.03), crest=(0.006, 0.1, 0.1), foam_attr="foam", hull_attr="hullfoam",
                   fog_color=(0.42, 0.5, 0.58)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; Lk = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(geo.outputs['Position'], sep.inputs[0])
    # light through the wave crests: brighter green-blue where the surface is high and steep
    hz = N.new("ShaderNodeMapRange"); hz.inputs['From Min'].default_value = 0.2; hz.inputs['From Max'].default_value = 1.6
    Lk.new(sep.outputs['Z'], hz.inputs['Value'])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'; col.inputs[6].default_value = (*deep, 1); col.inputs[7].default_value = (*crest, 1)
    Lk.new(hz.outputs[0], col.inputs['Factor'])
    # foam: ocean foam attribute + hull wash, broken up by noise into streaks and lace
    fa = N.new("ShaderNodeAttribute"); fa.attribute_name = foam_attr
    ha = N.new("ShaderNodeAttribute"); ha.attribute_name = hull_attr
    lace = N.new("ShaderNodeTexVoronoi"); lace.feature = 'DISTANCE_TO_EDGE'; lace.inputs['Scale'].default_value = 1.6
    Lk.new(tc.outputs['Object'], lace.inputs['Vector'])
    ln = N.new("ShaderNodeTexNoise"); ln.inputs['Scale'].default_value = 0.35; ln.inputs['Detail'].default_value = 10; ln.inputs['Roughness'].default_value = 0.65
    Lk.new(tc.outputs['Object'], ln.inputs['Vector'])
    fsum = N.new("ShaderNodeMath"); fsum.operation = 'ADD'; Lk.new(fa.outputs['Fac'], fsum.inputs[0]); Lk.new(ha.outputs['Fac'], fsum.inputs[1])
    fm = N.new("ShaderNodeMath"); fm.operation = 'MULTIPLY'; Lk.new(fsum.outputs[0], fm.inputs[0]); Lk.new(ln.outputs['Fac'], fm.inputs[1])
    lm = N.new("ShaderNodeMapRange"); lm.inputs['From Min'].default_value = 0.0; lm.inputs['From Max'].default_value = 0.12
    lm.inputs['To Min'].default_value = 1.0; lm.inputs['To Max'].default_value = 0.35
    Lk.new(lace.outputs['Distance'], lm.inputs['Value'])
    # streaky foam: stretched fine noise along the wind instead of a cellular pattern
    st_map = N.new("ShaderNodeMapping"); st_map.inputs['Scale'].default_value = (0.35, 1.6, 1.0)
    Lk.new(tc.outputs['Object'], st_map.inputs['Vector'])
    stn = N.new("ShaderNodeTexNoise"); stn.inputs['Scale'].default_value = 1.4; stn.inputs['Detail'].default_value = 14
    stn.inputs['Roughness'].default_value = 0.7; Lk.new(st_map.outputs[0], stn.inputs['Vector'])
    stm = N.new("ShaderNodeMapRange"); stm.inputs['From Min'].default_value = 0.35; stm.inputs['From Max'].default_value = 0.75
    stm.inputs['To Min'].default_value = 0.35; stm.inputs['To Max'].default_value = 1.25
    Lk.new(stn.outputs['Fac'], stm.inputs['Value'])
    fm2 = N.new("ShaderNodeMath"); fm2.operation = 'MULTIPLY'; Lk.new(fm.outputs[0], fm2.inputs[0]); Lk.new(stm.outputs[0], fm2.inputs[1])
    ramp = N.new("ShaderNodeMapRange"); ramp.inputs['From Min'].default_value = 0.2; ramp.inputs['From Max'].default_value = 0.5
    Lk.new(fm2.outputs[0], ramp.inputs['Value'])
    p.inputs['Roughness'].default_value = 0.075; p.inputs['IOR'].default_value = 1.333
    p.inputs['Specular IOR Level'].default_value = 0.5
    foam = N.new("ShaderNodeBsdfPrincipled"); foam.inputs['Base Color'].default_value = (0.78, 0.8, 0.8, 1)
    foam.inputs['Roughness'].default_value = 0.6; foam.inputs['Subsurface Weight'].default_value = 0.3
    Lk.new(col.outputs[2], p.inputs['Base Color'])
    # fine capillary ripples on top of the FFT waves
    rn = N.new("ShaderNodeTexNoise"); rn.inputs['Scale'].default_value = 4.0; rn.inputs['Detail'].default_value = 12
    Lk.new(tc.outputs['Object'], rn.inputs['Vector'])
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.08; bm.inputs['Distance'].default_value = 0.05
    Lk.new(rn.outputs['Fac'], bm.inputs['Height']); Lk.new(bm.outputs['Normal'], p.inputs['Normal'])
    mix = N.new("ShaderNodeMixShader"); Lk.new(ramp.outputs[0], mix.inputs[0])
    Lk.new(p.outputs[0], mix.inputs[1]); Lk.new(foam.outputs[0], mix.inputs[2])
    # aerial perspective: toward the horizon the sea fades into the grey of the sky (camera rays only)
    cd = N.new("ShaderNodeCameraData")
    fd = N.new("ShaderNodeMapRange"); fd.inputs['From Min'].default_value = 150; fd.inputs['From Max'].default_value = 5000
    fd.inputs['To Max'].default_value = 0.92; fd.interpolation_type = 'SMOOTHSTEP'
    Lk.new(cd.outputs['View Distance'], fd.inputs['Value'])
    lp = N.new("ShaderNodeLightPath"); fm_ = N.new("ShaderNodeMath"); fm_.operation = 'MULTIPLY'
    Lk.new(fd.outputs[0], fm_.inputs[0]); Lk.new(lp.outputs['Is Camera Ray'], fm_.inputs[1])
    fog = N.new("ShaderNodeEmission"); fog.inputs['Color'].default_value = (*fog_color, 1); fog.inputs['Strength'].default_value = 1.0
    mix2 = N.new("ShaderNodeMixShader"); Lk.new(fm_.outputs[0], mix2.inputs[0])
    Lk.new(mix.outputs[0], mix2.inputs[1]); Lk.new(fog.outputs[0], mix2.inputs[2])
    Lk.new(mix2.outputs[0], N["Material Output"].inputs['Surface'])
    return m


def ocean(size=220.0, res=24, scale=1.4, chop=1.6, wind=13.0, seed=7, repeat=3, foam=0.55, mat=None, time=11.0,
          direction=0.0, hulls=(), loc=(0, 0, 0), cut=None):
    bpy.ops.mesh.primitive_plane_add(size=2, location=loc)
    o = bpy.context.active_object; o.name = "Ocean"
    md = o.modifiers.new("Ocean", "OCEAN")
    md.geometry_mode = 'GENERATE'; md.size = 1.0; md.spatial_size = int(size); md.resolution = res
    md.repeat_x = repeat; md.repeat_y = repeat
    md.wave_scale = scale; md.choppiness = chop; md.wind_velocity = wind; md.random_seed = seed
    md.time = time; md.wave_alignment = 0.45; md.wave_direction = direction; md.damping = 0.5
    md.use_foam = True; md.foam_coverage = foam; md.foam_layer_name = "foam"
    md.use_normals = True
    o.location = (loc[0] - size * repeat / 2, loc[1] - size * repeat / 2, loc[2])
    if hulls:
        _hull_foam(o, hulls, cut=cut)
    sm = o.modifiers.new("Smooth", "SMOOTH") if False else None
    o.data.materials.append(mat or water_material())
    bpy.ops.object.shade_smooth()
    return o


def _hull_foam(o, hulls, reach=1.4, cut=None):
    """Geometry nodes: store 'hullfoam' = how close the sea surface is to each hull (wash along the waterline)."""
    ng = bpy.data.node_groups.new("HullFoam", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; Lk = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    cur = gi.outputs[0]
    acc = None
    for h in hulls:
        oi = N.new("GeometryNodeObjectInfo"); oi.inputs['Object'].default_value = h; oi.transform_space = 'RELATIVE'
        px = N.new("GeometryNodeProximity"); px.target_element = 'FACES'
        Lk.new(oi.outputs['Geometry'], px.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = reach
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        Lk.new(px.outputs['Distance'], mr.inputs['Value'])
        if acc is None:
            acc = mr.outputs[0]
        else:
            mx = N.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'; Lk.new(acc, mx.inputs[0]); Lk.new(mr.outputs[0], mx.inputs[1]); acc = mx.outputs[0]
    st = N.new("GeometryNodeStoreNamedAttribute"); st.data_type = 'FLOAT'; st.domain = 'POINT'
    st.inputs['Name'].default_value = "hullfoam"
    Lk.new(cur, st.inputs['Geometry']); Lk.new(acc, st.inputs['Value'])
    last = st.outputs['Geometry']
    if cut:
        # keep the sea out of the hull we stand in: delete surface inside an ellipse (world x/y)
        cx, cy, rx, ry = cut
        pos = N.new("GeometryNodeInputPosition"); sp = N.new("ShaderNodeSeparateXYZ"); Lk.new(pos.outputs[0], sp.inputs[0])
        def term(sock, c, r):
            a = N.new("ShaderNodeMath"); a.operation = 'SUBTRACT'; a.inputs[1].default_value = c; Lk.new(sock, a.inputs[0])
            b = N.new("ShaderNodeMath"); b.operation = 'DIVIDE'; b.inputs[1].default_value = r; Lk.new(a.outputs[0], b.inputs[0])
            q = N.new("ShaderNodeMath"); q.operation = 'POWER'; q.inputs[1].default_value = 2.0; Lk.new(b.outputs[0], q.inputs[0])
            return q.outputs[0]
        # the ocean object is offset: Position here is in object space, so add its location back
        ox, oy = o.location.x, o.location.y
        sx_ = N.new("ShaderNodeMath"); sx_.operation = 'ADD'; sx_.inputs[1].default_value = ox; Lk.new(sp.outputs['X'], sx_.inputs[0])
        sy_ = N.new("ShaderNodeMath"); sy_.operation = 'ADD'; sy_.inputs[1].default_value = oy; Lk.new(sp.outputs['Y'], sy_.inputs[0])
        e = N.new("ShaderNodeMath"); e.operation = 'ADD'; Lk.new(term(sx_.outputs[0], cx, rx), e.inputs[0]); Lk.new(term(sy_.outputs[0], cy, ry), e.inputs[1])
        lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 1.0; Lk.new(e.outputs[0], lt.inputs[0])
        dg = N.new("GeometryNodeDeleteGeometry"); dg.domain = 'POINT'
        Lk.new(last, dg.inputs['Geometry']); Lk.new(lt.outputs[0], dg.inputs['Selection']); last = dg.outputs[0]
    Lk.new(last, go.inputs[0])
    md = o.modifiers.new("HullFoam", "NODES"); md.node_group = ng


def far_sea(r0, r1=9000.0, mat=None, z=-0.05, center=(0, 0)):
    """Annulus of sea from the edge of the FFT patch to the horizon (normal-mapped, same water)."""
    n = 96; V = []; F = []
    for k, r in enumerate((r0, r0 * 1.6, r0 * 3, r1)):
        for i in range(n):
            a = 2 * math.pi * i / n
            V.append((center[0] + r * math.cos(a), center[1] + r * math.sin(a), z))
    for k in range(3):
        for i in range(n):
            a = k * n + i; b = k * n + (i + 1) % n
            F.append([a, b, b + n, a + n])
    me = bpy.data.meshes.new("FarSea"); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new("FarSea", me); bpy.context.collection.objects.link(o)
    m = (mat or water_material()).copy(); m.name = "far_sea"
    N = m.node_tree.nodes; Lk = m.node_tree.links
    # bigger swell normals at distance
    tc = [n_ for n_ in N if n_.type == 'TEX_COORD'][0]
    sw = N.new("ShaderNodeTexNoise"); sw.inputs['Scale'].default_value = 0.06; sw.inputs['Detail'].default_value = 12
    Lk.new(tc.outputs['Object'], sw.inputs['Vector'])
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.5; bm.inputs['Distance'].default_value = 0.6
    Lk.new(sw.outputs['Fac'], bm.inputs['Height'])
    p = N["Principled BSDF"]; Lk.new(bm.outputs['Normal'], p.inputs['Normal'])
    o.data.materials.append(m)
    return o


def haze(center, size, density=0.0009, color=(0.75, 0.8, 0.85), aniso=0.55):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center); o = bpy.context.active_object; o.name = "SeaHaze"
    o.scale = size
    m = bpy.data.materials.new("haze"); m.use_nodes = True; N = m.node_tree.nodes; Lk = m.node_tree.links
    N.remove(N["Principled BSDF"])
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs['Density'].default_value = density; v.inputs['Color'].default_value = (*color, 1)
    v.inputs['Anisotropy'].default_value = aniso
    # thicker toward the water
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(geo.outputs['Position'], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0; mr.inputs['From Max'].default_value = size[2] / 2 + center[2]
    mr.inputs['To Min'].default_value = density * 1.6; mr.inputs['To Max'].default_value = density * 0.3
    Lk.new(sep.outputs['Z'], mr.inputs['Value']); Lk.new(mr.outputs[0], v.inputs['Density'])
    Lk.new(v.outputs[0], N["Material Output"].inputs['Volume'])
    o.data.materials.append(m)
    o.visible_shadow = False
    return o


def spray(name, center, spread, count=6000, rmin=0.004, rmax=0.02, up=2.5, seed=5, dirv=(0, -1, 0)):
    """Droplets thrown off a bow wave: points in a fan that rises and falls (ballistic arcs, frozen)."""
    rng = np.random.default_rng(seed)
    c = np.array(center); d = np.array(dirv, float); d /= np.linalg.norm(d)
    t = rng.random(count) ** 0.7
    side = rng.normal(0, spread[0], count); fwd = rng.normal(0, spread[1], count)
    h = up * 4 * t * (1 - t) * rng.uniform(0.3, 1.0, count)
    P = np.stack([c[0] + fwd + d[0] * t * spread[2], c[1] + side + d[1] * t * spread[2], c[2] + h], 1)
    me = bpy.data.meshes.new(name); me.from_pydata(P.tolist(), [], []); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    # geometry nodes: mesh -> points with random radii (rendered natively by Cycles)
    ng = bpy.data.node_groups.new(name + "_pts", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; Lk = ng.links; gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    mp = N.new("GeometryNodeMeshToPoints"); rv = N.new("FunctionNodeRandomValue"); rv.data_type = 'FLOAT'
    rv.inputs['Min'].default_value = rmin; rv.inputs['Max'].default_value = rmax
    Lk.new(gi.outputs[0], mp.inputs['Mesh']); Lk.new(rv.outputs['Value'], mp.inputs['Radius'])
    sm = N.new("GeometryNodeSetMaterial")
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.9, 0.93, 0.95, 1); p.inputs['Roughness'].default_value = 0.15
    p.inputs['Transmission Weight'].default_value = 0.7; p.inputs['IOR'].default_value = 1.33
    sm.inputs['Material'].default_value = m
    Lk.new(mp.outputs['Points'], sm.inputs['Geometry']); Lk.new(sm.outputs['Geometry'], go.inputs[0])
    md = o.modifiers.new("pts", "NODES"); md.node_group = ng
    return o


def mist_puff(name, center, size, density=0.25, seed=0):
    """A cloud of fine spray as a noisy volume (the white veil over a breaking bow wave)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1, location=center)
    o = bpy.context.active_object; o.name = name; o.scale = size
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; Lk = m.node_tree.links
    N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 2.5
    nz.inputs['Detail'].default_value = 6
    try:
        nz.noise_dimensions = '4D'; nz.inputs['W'].default_value = seed
    except Exception:
        pass
    Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'; Lk.new(tc.outputs['Object'], gr.inputs['Vector'])
    mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; Lk.new(nz.outputs['Fac'], mm.inputs[0]); Lk.new(gr.outputs['Fac'], mm.inputs[1])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.12; mr.inputs['From Max'].default_value = 0.4
    mr.inputs['To Max'].default_value = density; Lk.new(mm.outputs[0], mr.inputs['Value'])
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs['Color'].default_value = (0.92, 0.94, 0.95, 1); v.inputs['Anisotropy'].default_value = 0.4
    Lk.new(mr.outputs[0], v.inputs['Density']); Lk.new(v.outputs[0], N["Material Output"].inputs['Volume'])
    o.data.materials.append(m)
    return o
