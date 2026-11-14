"""COUNTS AS OBJECTS: a number shown as the things themselves, laid out on a dark warehouse floor (no on-screen text).

Ch1 4B  count    "roughly two hundred and fifty typewriters" - top-down on one machine, the camera rises straight up and
                 the frame fills with 250 of them in rows under work lights
Ch2 2B  cleared  "For weeks, they come up empty." - the floor of the test hall seen from above: checked equipment
                 (copiers, terminals, cipher boxes, teletypes) laid out in rows, each with a pale cleared tag; the camera drifts across
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import typewriter as T
import machines as MC
import look

DUR = {"count": 6.0, "cleared": 6.0}
VARIANT_FOR = {"cleared": "cleared"}
EXPOSURE = 0.0
COLS, ROWS, DX, DY = 25, 10, 0.62, 0.72


def _as_collection(name, objs):
    col = bpy.data.collections.new(name)
    for o in objs:
        for cl in list(o.users_collection):
            cl.objects.unlink(o)
        col.objects.link(o)
    return col


def _instance(col, loc, rot_z=0.0):
    e = bpy.data.objects.new("Inst", None); e.instance_type = 'COLLECTION'; e.instance_collection = col
    bpy.context.collection.objects.link(e); e.location = loc; e.rotation_euler = (0, 0, rot_z)
    return e


def build(variant=None):
    c = {"variant": variant}
    w = bpy.context.scene.world or bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.02
    box("Floor", (0, 0, -0.01), (40, 30, 0.02), ph.texture("concrete_floor_painted", scale=0.4, name="GridFloor", tint=(0.5, 0.5, 0.48)))
    rng = np.random.default_rng(3)
    if variant == "cleared":
        protos = []
        for k, fn in enumerate((lambda n: MC.copier(n), lambda n: MC.terminal(n)[0], lambda n: MC.cipher(n, height=0.4)[0], lambda n: MC.teletype(n, stand=False)[0])):
            r = fn(f"Proto{k}"); r.location = (0, 0, -50)
            tag = box(f"Tag{k}", (0.18, -0.3, 0.02), (0.07, 0.11, 0.002), pbr("ClearedTag", (0.78, 0.8, 0.7), 0.8)); tag.parent = r
            col = _as_collection(f"Gear{k}", [r] + list(r.children_recursive)); r.location = (0, 0, 0)
            protos.append(col)
        c["items"] = []
        for j in range(8):
            for i in range(12):
                e = _instance(protos[int(rng.integers(0, 4))], ((i - 5.5) * 1.15, (j - 3.5) * 1.15, 0), rng.uniform(-0.15, 0.15))
                c["items"].append((j, i, e))
    else:
        protos = []
        for k, col_ in enumerate(((0.17, 0.22, 0.28), (0.42, 0.40, 0.36), (0.30, 0.08, 0.07))):
            tw = T.make(f"GridTW{k}", loc=(0, 0, 0), color=col_, mechanism=False, glyphs=False, legends=False, text=" ")
            r = tw["root"]
            protos.append(_as_collection(f"TWs{k}", [r] + list(r.children_recursive)))
        for j in range(ROWS):
            for i in range(COLS):
                k = 0 if rng.random() < 0.7 else (1 if rng.random() < 0.7 else 2)
                _instance(protos[k], ((i - (COLS - 1) / 2) * DX, (j - (ROWS - 1) / 2) * DY, 0), rng.uniform(-0.06, 0.06))
    # work lights hanging over the floor: a few strong pools, dark between them (no flat even light)
    for x in (-6, 0, 6):
        for y in (-2.0, 2.0):
            l = bpy.data.lights.new("WorkLamp", 'SPOT'); l.energy = 1400; l.spot_size = math.radians(80); l.spot_blend = 0.7
            l.color = (1.0, 0.88, 0.7); o = bpy.data.objects.new("WorkLamp", l); bpy.context.collection.objects.link(o)
            o.location = (x, y, 6.0); point_at(o, (x, y, 0))
    animate(c, 0.0, variant or "count")
    return c


def animate(c, sec, shot):
    if shot == "cleared":
        for j, i, e in c["items"]:                                      # everything already laid out: only the camera moves
            e.hide_render = False
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_count(c, t):
    e = ease(t) ** 1.4                    # straight up from one machine until all 250 fill the frame
    z = 0.9 + 14.0 * e
    y0 = 0.5 * DY                         # centre of the row nearest the middle (10 rows: none sits on y = 0)
    return (Vector((0.0, y0 - 0.05, z)), Vector((0.0, y0, 0.0)), 35, (0, 1, 0))


def cam_cleared(c, t):
    e = ease(t)
    return (Vector((-1.0 + 1.5 * e, -0.2, 11.0 + 1.5 * e)), Vector((-1.0 + 1.5 * e, 0.3, 0.0)), 30, (0, 1, 0))


MOVES = {
    "count": dict(kind="anim", dof=None, cam=cam_count, anim=anim("count"), dur=DUR["count"]),
    "cleared": dict(kind="anim", dof=None, cam=cam_cleared, anim=anim("cleared"), dur=DUR["cleared"]),
}


_build_raw = build


def build(variant=None):
    c = _build_raw(variant)
    look.night_interior(lift=0.2)
    return c
