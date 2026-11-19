# Copied unchanged from branch claude/mary-celeste-p4, mary_celeste_p4/lib/p4.py (shared cutaway look across the film).
"""Part 4 helpers: paths into the shared library (mary_celeste_3d/lib, used as-is), scene setup, small utilities.
Everything new for Part 4 lives in this folder; the shared library is imported, never copied or changed."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SHARED = os.path.join(ROOT, "mary_celeste_3d")
for p in (HERE, os.path.join(SHARED, "lib"), os.path.join(SHARED, "scenes")):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("MH_DATA", os.path.join(SHARED, "assets", "makehuman"))
import bpy
from mathutils import Vector, Matrix
import common as C          # shared scenes/common.py: reset, render_setup, camera, finish
import ship

OUT = os.path.join(ROOT, "mary_celeste_p4", "out")


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = strength
    if alpha < 1:
        p.inputs['Alpha'].default_value = alpha
    return m


def light(kind, name, energy, color=(1, 1, 1), loc=(0, 0, 0), target=None, size=None, spot=None, blend=0.3):
    l = bpy.data.lights.new(name, kind); l.energy = energy; l.color = color
    if size is not None:
        if kind == 'AREA':
            l.size = size
        else:
            l.shadow_soft_size = size
    if spot is not None:
        l.spot_size = math.radians(spot); l.spot_blend = blend
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    if target is not None:
        d = Vector(target) - Vector(loc)
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    return o


def sun(azim, elev, energy, color=(1.0, 0.9, 0.78), angle=3.0):
    s = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); bpy.context.scene.collection.objects.link(s)
    s.data.energy = energy; s.data.angle = math.radians(angle); s.data.color = color
    az, el = math.radians(azim), math.radians(elev)
    s.rotation_euler = (Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * -1).to_track_quat('-Z', 'Y').to_euler()
    return s


def world_color(col, strength=1.0):
    w = bpy.data.worlds.new("W"); w.use_nodes = True; bpy.context.scene.world = w
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*col, 1); bg.inputs[1].default_value = strength
    return w


def hide(names_contain=(), objs=()):
    for o in list(bpy.data.objects):
        if o in objs or any(s in o.name for s in names_contain):
            bpy.data.objects.remove(o, do_unlink=True)


def look_at(obj, target, roll=0.0):
    d = Vector(target) - obj.location
    obj.rotation_mode = 'QUATERNION'; obj.rotation_quaternion = d.to_track_quat('-Z', 'Y')


def key_cam(cam, frame, loc, target, lens=None):
    cam.location = loc; look_at(cam, target)
    cam.keyframe_insert("location", frame=frame); cam.keyframe_insert("rotation_quaternion", frame=frame)
    if lens:
        cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=frame)


def boxes(name, items, material=None):
    """Many boxes as ONE mesh (fast; bpy.ops per box gets slow in big scenes). items: (center, size, rot_z)."""
    import numpy as np
    V = []; F = []
    cube = np.array([[x, y, z] for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)])
    faces = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    for c, s, rz in items:
        R = Matrix.Rotation(rz, 3, 'Z')
        b = len(V)
        for v in cube:
            V.append(tuple(Vector(c) + R @ Vector((v[0] * s[0], v[1] * s[1], v[2] * s[2]))))
        F += [[b + i for i in f] for f in faces]
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    if material:
        me.materials.append(material)
    return o


def lamp_glass_passes(meshes):
    """Glass in a lantern/lamp must not block its own flame light (Cycles with caustics off): no shadow from glass parts."""
    for o in meshes:
        if o.type == 'MESH' and any(m and ("glass" in m.name.lower() or "flame" in m.name.lower()) for m in o.data.materials):
            o.visible_shadow = False
