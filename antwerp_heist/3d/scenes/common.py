"""Shared scene setup: paths, render settings, camera, grade."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "lib")
if LIB not in sys.path:
    sys.path.insert(0, LIB)
os.environ.setdefault("MH_DATA", os.path.join(HERE, "..", "assets", "makehuman"))
import bpy
from mathutils import Vector

PREVIEW = float(os.environ.get("PREVIEW", "0"))   # 0 = final; e.g. 0.25 = quarter resolution, few samples


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def render_setup(samples=256, noise=0.015, bounces=10, res=(2560, 1440)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = int(100 * PREVIEW) if PREVIEW else 100
    sc.cycles.samples = max(16, int(samples * (0.15 if PREVIEW else 1)))
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = noise * (3 if PREVIEW else 1)
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    sc.cycles.max_bounces = bounces; sc.cycles.diffuse_bounces = 4; sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 8; sc.cycles.volume_bounces = 1; sc.cycles.transparent_max_bounces = 16
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.cycles.sample_clamp_indirect = 6.0
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '16'
    try:
        sc.render.compositor_device = 'CPU'
    except Exception:
        pass
    return sc


def camera(loc, target, lens=50, fstop=None, focus=None, sensor=36, roll=0.0):
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera = cam
    cam.location = loc; cam.data.lens = lens; cam.data.sensor_width = sensor
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat('-Z', 'Y')
    if roll:
        from mathutils import Quaternion
        q = q @ Quaternion((0, 0, 1), math.radians(roll))
    cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = q
    cam.data.clip_start = 0.05; cam.data.clip_end = 20000
    if fstop:
        cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop
        cam.data.dof.focus_distance = focus if focus else d.length
        cam.data.dof.aperture_blades = 7
    return cam


def finish(out, grade=True, cine=None, bloom=0.3):
    sc = bpy.context.scene
    if grade:
        import grade as G
        G.add_grade(sc, bloom=bloom, look="cinematic", cine=cine)
    sc.render.filepath = out
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.render.render(write_still=True)
