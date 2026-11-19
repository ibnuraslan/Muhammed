"""Part 1 environment: paths to the shared 3D library (mary_celeste_3d/lib, used as is), render setup, the warm
Atrium-style finish, and small helpers shared by every set.

Look rule for this part (hub brief): rich warm COLOUR, never desaturated. Exteriors: deep blue Atlantic under a
partly cloudy blue sky, warm early-afternoon sun. Interiors: lantern amber, walnut and oxblood, one cool daylight
accent through a skylight or a door."""
import os, sys, math, importlib.util
import bpy
from mathutils import Vector, Matrix, Quaternion

P1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(P1)
SHARED = os.path.join(REPO, "mary_celeste_3d")
LIB = os.path.join(SHARED, "lib")
for p in (LIB, os.path.join(P1, "p1")):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("MH_DATA", os.path.join(SHARED, "assets", "makehuman"))

PREVIEW = float(os.environ.get("PREVIEW", "0"))
RES = (2560, 1440)
FPS = 24

SKY_HDRI = os.environ.get("SKY_HDRI", "kloofendal_48d_partly_cloudy_puresky")


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    return sc


def render_setup(samples=128, noise=0.02, bounces=8):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = int(100 * PREVIEW) if PREVIEW else 100
    spp = int(os.environ.get("SPP", "0")) or samples
    sc.cycles.samples = spp
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = noise
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    sc.cycles.max_bounces = bounces; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 6; sc.cycles.volume_bounces = 0; sc.cycles.transparent_max_bounces = 12
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0; sc.cycles.sample_clamp_indirect = 6.0
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
    sc.render.fps = FPS
    try:
        sc.render.compositor_device = 'CPU'
    except Exception:
        pass
    return sc


def camera(loc, target, lens=50, fstop=None, focus=None, roll=0.0, sensor=36):
    cam = bpy.data.objects.get("Camera")
    if cam is None:
        cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
        bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.data.lens = lens; cam.data.sensor_width = sensor
    cam.data.clip_start = 0.02; cam.data.clip_end = 20000
    aim(cam, loc, target, roll)
    if fstop:
        cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop; cam.data.dof.aperture_blades = 7
        cam.data.dof.focus_distance = focus if focus else (Vector(target) - Vector(loc)).length
    else:
        cam.data.dof.use_dof = False
    return cam


def aim(obj, loc, target, roll=0.0):
    obj.location = Vector(loc)
    q = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    if roll:
        q = q @ Quaternion((0, 0, 1), math.radians(roll))
    obj.rotation_mode = 'QUATERNION'; obj.rotation_quaternion = q


WARM = dict(exposure=-0.1, contrast=1.16, sat=1.12, warm=(1.045, 1.0, 0.935), black=(0.0008, 0.0008, 0.0009))


def finish(out, cine=None, bloom=0.28, vignette=0.6):
    """House grade (lib/grade.py, cinematic chain) with the warm, saturated settings for this part."""
    import grade as G
    sc = bpy.context.scene
    k = dict(WARM); k.update(cine or {})
    G.add_grade(sc, bloom=bloom, look="cinematic", cine=k, vignette=vignette)
    sc.render.filepath = out
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", out, flush=True)


def area(name, loc, target, energy, size=1.0, color=(1, 1, 1), visible=False, size_y=None):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.size = size; d.color = color
    if size_y:
        d.shape = 'RECTANGLE'; d.size_y = size_y
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    o.visible_camera = visible; o.visible_glossy = False; o.visible_volume_scatter = False
    return o


def point(name, loc, energy, color=(1.0, 0.56, 0.24), radius=0.02):
    d = bpy.data.lights.new(name, 'POINT'); d.energy = energy; d.color = color; d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.visible_volume_scatter = False          # a practical close to camera must not fog the lens; daylight makes the haze
    return o


def sun(az_deg, el_deg, energy=3.2, color=(1.0, 0.86, 0.66), angle=1.5):
    o = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); bpy.context.scene.collection.objects.link(o)
    o.data.energy = energy; o.data.angle = math.radians(angle); o.data.color = color
    az, el = math.radians(az_deg), math.radians(el_deg)
    d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    o.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return o


def emission_mat(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes
    N.remove(N["Principled BSDF"]); e = N.new("ShaderNodeEmission")
    e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    m.node_tree.links.new(e.outputs[0], N["Material Output"].inputs['Surface'])
    return m


def principled(name, color, rough=0.5, metal=0.0, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    for k, v in kw.items():
        p.inputs[k].default_value = v
    return m


def hide(prefixes):
    for o in bpy.data.objects:
        if o.name.startswith(tuple(prefixes)):
            o.hide_render = True
