"""Thumbnail scenes: reuse the Mary Celeste 3D library (mary_celeste_3d/lib, mary_celeste_3d/scenes/common.py)."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
MC3D = os.path.join(HERE, "..", "..", "mary_celeste_3d")
for p in (os.path.join(MC3D, "scenes"), os.path.join(MC3D, "lib"), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import importlib.util as _iu  # noqa: E402
_spec = _iu.spec_from_file_location("mc_scene_common", os.path.join(MC3D, "scenes", "common.py"))
C = _iu.module_from_spec(_spec); _spec.loader.exec_module(C)   # mary_celeste_3d/scenes/common.py
import bpy                  # noqa: E402
import numpy as np          # noqa: E402
from mathutils import Vector  # noqa: E402

OUTDIR = os.path.join(HERE, "..", "out")


def hdri_sun_azimuth(aid, res="4k"):
    """World-space azimuth (deg, from +X toward +Y) of the brightest region of an equirect HDRI at rot_z = 0,
    and its elevation."""
    import ph
    im = bpy.data.images.load(ph.hdri(aid, res), check_existing=True)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, :3].sum(2)
    a = a[::4, ::4]; hh, ww = a.shape
    j, i = np.unravel_index(np.argmax(a), a.shape)          # row j from the bottom (pixels start at the bottom)
    u = (i + 0.5) / ww; v = (j + 0.5) / hh
    phi = (u - 0.5) * 2 * math.pi                            # Blender: dir = (-cos phi, sin phi) ... see below
    d = Vector((-math.cos(phi), math.sin(phi), 0))
    # Blender equirect: u = atan2(dir.y, -dir.x) / (2 pi) + 0.5
    az = math.degrees(math.atan2(d.y, d.x)); el = (v - 0.5) * 180
    return az, el


def sky_with_sun_at(aid, want_az, strength=1.0, res="4k"):
    """Load the HDRI as the world, rotated so its sun sits at world azimuth want_az. Returns (rot_deg, el)."""
    import ph
    az, el = hdri_sun_azimuth(aid, res)
    rot = az - want_az        # lookup(Rz d): the bright texture direction appears at az - rot
    ph.world_hdri(aid, strength=strength, rot_z=math.radians(rot), res=res)
    return rot, el


def sun(az_deg, el_deg, energy=3.0, color=(1.0, 0.8, 0.6), angle=1.5):
    sc = bpy.context.scene
    s = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(s)
    s.data.energy = energy; s.data.angle = math.radians(angle); s.data.color = color
    az, el = math.radians(az_deg), math.radians(el_deg)
    toward = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    s.rotation_euler = (-toward).to_track_quat('-Z', 'Y').to_euler()
    return s


def res_setup(spp, noise=0.02, final=False):
    full = (1920, 1080)
    sc = C.render_setup(samples=spp, noise=noise, res=full)
    pv = float(os.environ.get("PREVIEW", "0"))
    if pv:
        sc.render.resolution_percentage = int(100 * pv)
    return sc


def shaft(src, target, energy, deg, haze=0.01, color=(1.0, 0.88, 0.7), soft=3.0, widen=1.5, noise_scale=0.035):
    """A spot from `src` onto `target` plus a cone of murk around its beam only (lit by nothing else when the other
    lights have visible_volume_scatter off), with noisy density so the beam breaks into rays."""
    sc = bpy.context.scene
    sp = bpy.data.lights.new("shaft", 'SPOT'); sp.energy = energy; sp.color = color
    sp.spot_size = math.radians(deg); sp.spot_blend = 1.0; sp.shadow_soft_size = soft
    so = bpy.data.objects.new("shaft", sp); sc.collection.objects.link(so)
    src = Vector(src); target = Vector(target); axis = target - src; ln = axis.length
    so.location = src; so.rotation_euler = axis.to_track_quat('-Z', 'Y').to_euler()
    if haze <= 0:
        return so, None
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.1, radius2=ln * math.tan(math.radians(deg) / 2) * widen,
                                    depth=ln * 1.15, location=src + axis * 0.575)
    hz = bpy.context.active_object; hz.name = "shaft_haze"
    hz.rotation_euler = axis.to_track_quat('-Z', 'Y').to_euler()
    hm = bpy.data.materials.new("shaft_haze"); nt = hm.node_tree; HN = nt.nodes; HN.remove(HN["Principled BSDF"])
    vv = HN.new("ShaderNodeVolumePrincipled"); vv.inputs['Color'].default_value = (0.85, 0.85, 0.85, 1)
    vv.inputs['Anisotropy'].default_value = 0.5
    nt.links.new(vv.outputs[0], HN["Material Output"].inputs['Volume'])
    htc = HN.new("ShaderNodeTexCoord"); hn = HN.new("ShaderNodeTexNoise"); hn.inputs['Scale'].default_value = noise_scale
    hn.inputs['Detail'].default_value = 3; nt.links.new(htc.outputs['Object'], hn.inputs['Vector'])
    hmr = HN.new("ShaderNodeMapRange"); hmr.inputs['From Min'].default_value = 0.35; hmr.inputs['From Max'].default_value = 0.65
    hmr.inputs['To Min'].default_value = 0.2 * haze; hmr.inputs['To Max'].default_value = 1.6 * haze
    nt.links.new(hn.outputs['Fac'], hmr.inputs['Value']); nt.links.new(hmr.outputs[0], vv.inputs['Density'])
    hz.data.materials.append(hm); hz.visible_shadow = False
    return so, hz


def lights_skip_haze(keep=("shaft",)):
    for o in bpy.context.scene.objects:
        if o.type == 'LIGHT' and not o.name.startswith(keep):
            o.visible_volume_scatter = False
