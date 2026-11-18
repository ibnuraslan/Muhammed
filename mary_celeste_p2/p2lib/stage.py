"""Render setup, props and placement helpers shared by the Part 2 sets."""
import os, sys, math
import env
import common as C
import bpy
from mathutils import Vector, Matrix
import ph, ship

PREVIEW = float(os.environ.get("PREVIEW", "0"))
SPP = int(os.environ.get("SPP", "0"))
NOVOL = bool(os.environ.get("NOVOL"))


def setup(samples=192, noise=0.02, bounces=8):
    sc = C.render_setup(samples=samples, noise=noise, bounces=bounces)
    if SPP:
        sc.cycles.samples = SPP
    sc.render.fps = 24
    return sc


def place_model(aid, at, size=None, axis=2, rot_z=0.0, ground=True, res="2k"):
    """Import a Poly Haven model, scale it so its extent along `axis` is `size` metres, sit it on `at`."""
    root, meshes = ph.model(aid, res=res)
    lo, hi = ph.bounds(meshes)
    s = 1.0 if size is None else size / max(1e-6, (hi - lo)[axis])
    root.scale = (s, s, s); root.rotation_euler = (0, 0, rot_z)
    bpy.context.view_layer.update()
    lo, hi = ph.bounds(meshes)
    c = (lo + hi) / 2
    root.location += Vector(at) - Vector((c.x, c.y, lo.z if ground else c.z))
    bpy.context.view_layer.update()
    return root, meshes


def look_at_q(loc, target, roll=0.0):
    q = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    if roll:
        from mathutils import Quaternion
        q = q @ Quaternion((0, 0, 1), math.radians(roll))
    return q


def cam(loc, target, lens=35, fstop=None, focus=None, roll=0.0, shift=(0, 0)):
    c = C.camera(loc, target, lens=lens, fstop=fstop, focus=focus, roll=roll)
    c.data.shift_x, c.data.shift_y = shift
    return c


def point(name, loc, energy, color=(1.0, 0.7, 0.42), radius=0.05):
    l = bpy.data.lights.new(name, 'POINT'); l.energy = energy; l.color = color; l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    return o


def area(name, loc, target, energy, size=1.0, color=(1, 1, 1), size_y=None):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = color; l.size = size
    if size_y:
        l.shape = 'RECTANGLE'; l.size_y = size_y
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = look_at_q(loc, target)
    o.visible_camera = False
    return o


def spot(name, loc, target, energy, angle=40, blend=0.6, color=(1, 1, 1), radius=0.1):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color; l.spot_size = math.radians(angle)
    l.spot_blend = blend; l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = look_at_q(loc, target)
    return o


def emissive(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; p = N["Principled BSDF"]
    p.inputs['Emission Color'].default_value = (*color, 1); p.inputs['Emission Strength'].default_value = strength
    p.inputs['Base Color'].default_value = (*color, 1)
    return m


def flame(name, loc, h=0.03, strength=60.0, color=(1.0, 0.55, 0.18)):
    """A lamp flame: a small emissive teardrop (plus the point light that does the lighting)."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=h * 0.35, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = (0.6, 0.6, 1.6)
    o.data.materials.append(emissive(name + "_m", color, strength))
    o.visible_shadow = False
    return o


def probe():
    """Print what the camera sees at 9 points (nearest hit object), for layout checks without rendering."""
    sc = bpy.context.scene; cam = sc.camera
    for o in bpy.data.objects:
        if o.name.startswith(("SeaHaze", "air", "dust", "Haze", "haze")) or "plume" in o.name:
            o.hide_viewport = True
    dg = bpy.context.evaluated_depsgraph_get()
    fr = cam.data.view_frame(scene=sc); tr, br, bl, tl = fr[0], fr[1], fr[2], fr[3]
    print("PROBE cam", tuple(round(c, 2) for c in cam.matrix_world.translation), "lens", cam.data.lens)
    for v in (0.85, 0.5, 0.15):
        row = []
        for u in (0.15, 0.5, 0.85):
            p = bl + (br - bl) * u + (tl - bl) * v
            if cam.data.type == 'ORTHO':
                o = cam.matrix_world @ p; d = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
            else:
                o = cam.matrix_world.translation; d = (cam.matrix_world.to_3x3() @ p).normalized()
            hit = sc.ray_cast(dg, o, d)
            row.append(f"{hit[4].name[:18] if hit[0] else 'SKY'}@{(hit[1]-o).length:.1f}" if hit[0] else "SKY")
        print("PROBE", " | ".join(row))


def finish(out, cine=None, bloom=0.3, exposure=0.0):
    if os.environ.get("PROBE"):
        probe(); print("RENDERED probe"); return
    sc = bpy.context.scene
    sc.view_settings.exposure += exposure
    C.finish(out, cine=cine, bloom=bloom)
    print("RENDERED", out)


def out_path(shot):
    d = os.environ.get("OUTDIR", os.path.join(env.P2, "out", "frames"))
    return os.path.join(d, f"{shot}.png")


def shot_arg():
    for a in sys.argv:
        if a.startswith("SHOT="):
            return a[5:]
    return os.environ.get("SHOT")


def frame(targets, direction, lens=50, fill=0.7, bounds=None, aim_offset=(0, 0, 0), fstop=None, min_lens=16):
    """Place a camera looking along -direction at the group `targets` so they fill `fill` of the frame height.
    bounds = (x0, x1, y0, y1, z0, z1): keep the camera inside (a room); the lens widens if it has to come closer."""
    pts = [Vector(t) for t in targets]
    c = sum(pts, Vector()) / len(pts) + Vector(aim_offset)
    r = max([(p - c).length for p in pts] + [0.15]) + 0.08
    d = Vector(direction).normalized()
    def dist_for(ln):
        vfov = 2 * math.atan(18 * 9 / 16 / ln)
        return r / math.tan(vfov / 2) / fill
    dist = dist_for(lens)
    loc = c + d * dist
    if bounds:
        x0, x1, y0, y1, z0, z1 = bounds
        t = 1.0
        for i, (lo, hi) in enumerate(((x0, x1), (y0, y1), (z0, z1))):
            if d[i] > 1e-6 and c[i] + d[i] * dist > hi:
                t = min(t, (hi - c[i]) / (d[i] * dist))
            if d[i] < -1e-6 and c[i] + d[i] * dist < lo:
                t = min(t, (lo - c[i]) / (d[i] * dist))
        if t < 1.0:
            dist *= max(t, 0.05); loc = c + d * dist
            ln = lens
            while ln > min_lens and dist_for(ln) > dist:
                ln -= 1
            lens = ln
    return cam(loc, c, lens=lens, fstop=fstop, focus=(c - loc).length)


def ots(head, target, side=1.0, back=0.38, out=0.3, up=0.12, lens=45, fstop=2.8):
    """Over-the-shoulder: behind the head (away from the target) and off to one side, looking at the target."""
    h = Vector(head); t = Vector(target)
    b = h - t; b.z = 0; b.normalize()
    s = Vector((-b.y, b.x, 0)) * side
    loc = h + b * back + s * out + Vector((0, 0, up))
    return cam(loc, t, lens=lens, fstop=fstop, focus=(t - loc).length)


if os.environ.get("LAYOUT"):
    _setup0 = setup
    def setup(samples=192, noise=0.02, bounces=8):
        sc = _setup0(samples, noise, bounces)
        sc.render.engine = 'BLENDER_EEVEE'
        return sc
