"""Shared Blender (bpy) helpers for the Iceman short film."""
import math, os, sys
import numpy as np
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def reset(res=(960, 408), samples=48, fps=24, exposure=0.0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.02
    s.cycles.use_denoising = True
    try:
        s.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    s.cycles.max_bounces = 6
    s.cycles.volume_bounces = 1
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.render.fps = fps
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_depth = '16'
    s.view_settings.view_transform = 'AgX'
    s.view_settings.look = 'AgX - Medium High Contrast'
    s.view_settings.exposure = exposure
    s.render.use_persistent_data = True
    s.render.film_transparent = False
    if '--lowres' in sys.argv:
        s.render.resolution_percentage = 50
    return s


def nodes_of(idblock):
    idblock.use_nodes = True
    nt = idblock.node_tree
    return nt, nt.nodes, nt.links


def world_sky(sun_elev_deg=8, sun_rot_deg=120, strength=1.0, tint=(1, 1, 1), sky_type='MULTIPLE_SCATTERING',
              air=1.0, aerosol=1.0):
    w = bpy.data.worlds.new("World"); bpy.context.scene.world = w
    nt, N, L = nodes_of(w)
    N.clear()
    sky = N.new("ShaderNodeTexSky"); sky.sky_type = sky_type
    sky.sun_elevation = math.radians(sun_elev_deg)
    sky.sun_rotation = math.radians(sun_rot_deg)
    sky.altitude = 2500
    sky.air_density = air
    sky.aerosol_density = aerosol
    sky.sun_disc = True
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    mix.inputs[7].default_value = (*tint, 1)
    bg = N.new("ShaderNodeBackground"); bg.inputs['Strength'].default_value = strength
    out = N.new("ShaderNodeOutputWorld")
    L.new(sky.outputs['Color'], mix.inputs[6])
    L.new(mix.outputs[2], bg.inputs['Color'])
    L.new(bg.outputs[0], out.inputs['Surface'])
    return w


def world_flat(color=(0.05, 0.07, 0.1), strength=1.0):
    w = bpy.data.worlds.new("World"); bpy.context.scene.world = w
    nt, N, L = nodes_of(w)
    N["Background"].inputs['Color'].default_value = (*color, 1)
    N["Background"].inputs['Strength'].default_value = strength
    return w


def sun(elev_deg, azim_deg, energy=3.0, color=(1, 0.9, 0.8), angle_deg=0.6):
    d = bpy.data.lights.new("Sun", 'SUN'); d.energy = energy; d.color = color
    d.angle = math.radians(angle_deg)
    o = bpy.data.objects.new("Sun", d); bpy.context.collection.objects.link(o)
    # Sun points along -Z of object. Rotate so it comes from given elevation/azimuth.
    o.rotation_euler = (math.radians(90 - elev_deg), 0, math.radians(azim_deg + 90))
    return o


def area_light(loc, rot, size, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new("Area", 'AREA'); d.energy = energy; d.size = size; d.color = color
    o = bpy.data.objects.new("Area", d); bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    return o


def grid_mesh(name, heights, size_x, size_y, z_scale, origin=(0, 0, 0)):
    """Build a mesh from a heightfield array (rows=y, cols=x)."""
    ny, nx = heights.shape
    xs = np.linspace(-size_x / 2, size_x / 2, nx, dtype=np.float32)
    ys = np.linspace(-size_y / 2, size_y / 2, ny, dtype=np.float32)
    X, Y = np.meshgrid(xs, ys)
    verts = np.stack([X + origin[0], Y + origin[1], heights * z_scale + origin[2]], -1).reshape(-1, 3)
    idx = np.arange(nx * ny).reshape(ny, nx)
    a = idx[:-1, :-1].ravel(); b = idx[:-1, 1:].ravel(); c = idx[1:, 1:].ravel(); d = idx[1:, :-1].ravel()
    quads = np.stack([a, b, c, d], -1)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel())
    nl = len(quads) * 4
    me.loops.add(nl); me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", np.arange(0, nl, 4, dtype=np.int32))
    me.polygons.foreach_set("use_smooth", np.ones(len(quads), bool))
    # UVs
    uv = me.uv_layers.new(name="UVMap")
    U = ((X - X.min()) / (X.max() - X.min())).ravel(); V = ((Y - Y.min()) / (Y.max() - Y.min())).ravel()
    uvs = np.stack([U, V], -1)[quads.ravel()]
    uv.data.foreach_set("uv", uvs.ravel())
    me.update(calc_edges=True); me.validate()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    return o


def snow_rock_material(name="SnowRock", snow_thresh=0.72, fog_color=(0.55, 0.65, 0.8), fog_density=0.00012,
                       rock_col=(0.06, 0.055, 0.05), snow_col=(0.82, 0.86, 0.92), bump_scale=1.0, fog_max=0.92):
    """Slope-based snow/rock blend with fake aerial perspective (distance haze)."""
    m = bpy.data.materials.new(name)
    nt, N, L = nodes_of(m)
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    geo = N.new("ShaderNodeNewGeometry")
    texc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], sep.inputs[0])
    # breakup noise
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.02 / bump_scale
    nz.inputs['Detail'].default_value = 8; nz.inputs['Roughness'].default_value = 0.6
    L.new(texc.outputs['Object'], nz.inputs['Vector'])
    add = N.new("ShaderNodeMath"); add.operation = 'MULTIPLY_ADD'
    L.new(nz.outputs['Fac'], add.inputs[0]); add.inputs[1].default_value = 0.25; L.new(sep.outputs['Z'], add.inputs[2])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = snow_thresh + 0.06
    ramp.color_ramp.elements[1].position = snow_thresh + 0.13
    L.new(add.outputs[0], ramp.inputs['Fac'])
    # rock colour variation
    rn = N.new("ShaderNodeTexNoise"); rn.inputs['Scale'].default_value = 0.4 / bump_scale; rn.inputs['Detail'].default_value = 10
    L.new(texc.outputs['Object'], rn.inputs['Vector'])
    rmix = N.new("ShaderNodeMix"); rmix.data_type = 'RGBA'
    L.new(rn.outputs['Fac'], rmix.inputs['Factor'])
    rmix.inputs[6].default_value = (*rock_col, 1)
    rmix.inputs[7].default_value = (rock_col[0] * 2.2, rock_col[1] * 2.0, rock_col[2] * 1.9, 1)
    rock = N.new("ShaderNodeBsdfPrincipled")
    L.new(rmix.outputs[2], rock.inputs['Base Color']); rock.inputs['Roughness'].default_value = 0.85
    snow = N.new("ShaderNodeBsdfPrincipled")
    snow.inputs['Base Color'].default_value = (*snow_col, 1)
    snow.inputs['Roughness'].default_value = 0.55
    snow.inputs['Subsurface Weight'].default_value = 0.25
    snow.inputs['Subsurface Radius'].default_value = (0.4, 0.7, 1.0)
    snow.inputs['Subsurface Scale'].default_value = 0.05 * bump_scale
    snow.inputs['Specular IOR Level'].default_value = 0.35
    # bump
    bn = N.new("ShaderNodeTexNoise"); bn.inputs['Scale'].default_value = 3.0 / bump_scale; bn.inputs['Detail'].default_value = 12
    L.new(texc.outputs['Object'], bn.inputs['Vector'])
    bump = N.new("ShaderNodeBump"); bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.2 * bump_scale
    L.new(bn.outputs['Fac'], bump.inputs['Height'])
    L.new(bump.outputs['Normal'], rock.inputs['Normal']); L.new(bump.outputs['Normal'], snow.inputs['Normal'])
    surf = N.new("ShaderNodeMixShader")
    L.new(ramp.outputs['Color'], surf.inputs['Fac']); L.new(rock.outputs[0], surf.inputs[1]); L.new(snow.outputs[0], surf.inputs[2])
    # Aerial perspective: mix with emission of fog colour by 1-exp(-d*k), camera rays only
    cam = N.new("ShaderNodeCameraData")
    k = N.new("ShaderNodeMath"); k.operation = 'MULTIPLY'; k.inputs[1].default_value = -fog_density
    L.new(cam.outputs['View Distance'], k.inputs[0])
    ex = N.new("ShaderNodeMath"); ex.operation = 'EXPONENT'; L.new(k.outputs[0], ex.inputs[0])
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(ex.outputs[0], inv.inputs[1])
    cl = N.new("ShaderNodeMath"); cl.operation = 'MULTIPLY'; cl.inputs[1].default_value = fog_max; L.new(inv.outputs[0], cl.inputs[0])
    lp = N.new("ShaderNodeLightPath")
    gate = N.new("ShaderNodeMath"); gate.operation = 'MULTIPLY'
    L.new(cl.outputs[0], gate.inputs[0]); L.new(lp.outputs['Is Camera Ray'], gate.inputs[1])
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*fog_color, 1); em.inputs['Strength'].default_value = 1.0
    fin = N.new("ShaderNodeMixShader")
    L.new(gate.outputs[0], fin.inputs['Fac']); L.new(surf.outputs[0], fin.inputs[1]); L.new(em.outputs[0], fin.inputs[2])
    L.new(fin.outputs[0], out.inputs['Surface'])
    m["fog_emission"] = em.name
    return m


def cloud_volume(name, loc, scale, density=0.6, scale_noise=0.0008, top_soft=0.35, color=(1, 1, 1), anisotropy=0.6):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    m = bpy.data.materials.new(name + "Mat")
    nt, N, L = nodes_of(m); N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    tc = N.new("ShaderNodeTexCoord")
    noise = N.new("ShaderNodeTexNoise"); noise.noise_dimensions = '4D'
    noise.inputs['Scale'].default_value = 2.2; noise.inputs['Detail'].default_value = 6
    noise.inputs['Roughness'].default_value = 0.55
    L.new(tc.outputs['Generated'], noise.inputs['Vector'])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    # vertical falloff: dense at bottom, soft top
    grad = N.new("ShaderNodeMapRange"); grad.inputs['From Min'].default_value = 1.0; grad.inputs['From Max'].default_value = 1 - top_soft
    L.new(sep.outputs['Z'], grad.inputs['Value'])
    sub = N.new("ShaderNodeMath"); sub.operation = 'MULTIPLY'
    L.new(noise.outputs['Fac'], sub.inputs[0]); L.new(grad.outputs[0], sub.inputs[1])
    thr = N.new("ShaderNodeMapRange"); thr.inputs['From Min'].default_value = 0.32; thr.inputs['From Max'].default_value = 0.62
    thr.inputs['To Max'].default_value = density
    L.new(sub.outputs[0], thr.inputs['Value'])
    vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs['Color'].default_value = (*color, 1); vol.inputs['Anisotropy'].default_value = anisotropy
    L.new(thr.outputs[0], vol.inputs['Density'])
    L.new(vol.outputs[0], out.inputs['Volume'])
    o.data.materials.append(m)
    o["noise_node"] = noise.name
    return o, noise


def camera(loc, look_at, lens=35, dof_dist=None, fstop=2.8, sensor=36):
    c = bpy.data.cameras.new("Cam"); c.lens = lens; c.sensor_width = sensor
    c.clip_end = 100000; c.clip_start = 0.0005
    if dof_dist:
        c.dof.use_dof = True; c.dof.focus_distance = dof_dist; c.dof.aperture_fstop = fstop
    o = bpy.data.objects.new("Cam", c); bpy.context.collection.objects.link(o)
    o.location = loc
    point_at(o, look_at)
    bpy.context.scene.camera = o
    return o


def point_at(obj, target):
    from mathutils import Vector
    d = Vector(target) - Vector(obj.location)
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def render_frames(outdir, frame_fn, frames, step=1, start_index=0):
    """frame_fn(i, t) mutates the scene for frame index i (t in [0,1]); render each to PNG."""
    os.makedirs(outdir, exist_ok=True)
    s = bpy.context.scene
    for i in range(start_index, frames, step):
        path = os.path.join(outdir, f"f{i:04d}.png")
        if os.path.exists(path):
            continue
        frame_fn(i, i / max(frames - 1, 1))
        s.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print(f"[render] {path}", flush=True)


def snow_material(scale=1.0, glint=0.985):
    """Fresh snow: subsurface scattering, granular bump, sparse ice-crystal glints (clear-coat facets)."""
    m = bpy.data.materials.new("Snow"); nt, N, L = nodes_of(m); N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    tc = N.new("ShaderNodeTexCoord")
    p = N.new("ShaderNodeBsdfPrincipled")
    p.inputs['Base Color'].default_value = (0.86, 0.9, 0.97, 1)
    p.inputs['Roughness'].default_value = 0.42
    p.inputs['Subsurface Weight'].default_value = 1.0
    p.inputs['Subsurface Radius'].default_value = (0.6, 0.85, 1.0)
    p.inputs['Subsurface Scale'].default_value = 0.012 * scale
    p.inputs['Specular IOR Level'].default_value = 0.5
    bn = N.new("ShaderNodeTexNoise"); bn.inputs['Scale'].default_value = 900 / scale; bn.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], bn.inputs['Vector'])
    bn2 = N.new("ShaderNodeTexNoise"); bn2.inputs['Scale'].default_value = 90 / scale; bn2.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], bn2.inputs['Vector'])
    mx = N.new("ShaderNodeMath"); mx.operation = 'MULTIPLY_ADD'; mx.inputs[1].default_value = 0.4
    L.new(bn.outputs['Fac'], mx.inputs[0]); L.new(bn2.outputs['Fac'], mx.inputs[2])
    bump = N.new("ShaderNodeBump"); bump.inputs['Strength'].default_value = 0.6; bump.inputs['Distance'].default_value = 0.0015 * scale
    L.new(mx.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], p.inputs['Normal'])
    # ice-crystal glints: sparse voronoi cells get a near-mirror specular
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs['Scale'].default_value = 700 / scale
    vor.feature = 'F1'
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    sel = N.new("ShaderNodeMath"); sel.operation = 'GREATER_THAN'; sel.inputs[1].default_value = glint
    sep = N.new("ShaderNodeSeparateColor"); L.new(vor.outputs['Color'], sep.inputs[0])
    L.new(sep.outputs[0], sel.inputs[0])
    rnd = N.new("ShaderNodeVectorMath"); rnd.operation = 'MULTIPLY_ADD'
    L.new(vor.outputs['Color'], rnd.inputs[0]); rnd.inputs[1].default_value = (1.4, 1.4, 0.3); rnd.inputs[2].default_value = (-0.7, -0.7, 1.0)
    nrm = N.new("ShaderNodeVectorMath"); nrm.operation = 'NORMALIZE'; L.new(rnd.outputs[0], nrm.inputs[0])
    L.new(sel.outputs[0], p.inputs['Coat Weight'])
    p.inputs['Coat Roughness'].default_value = 0.02; p.inputs['Coat IOR'].default_value = 1.8
    L.new(nrm.outputs[0], p.inputs['Coat Normal'])
    L.new(p.outputs[0], out.inputs['Surface'])
    return m
