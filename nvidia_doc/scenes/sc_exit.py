"""CH4 5C redo (196 f): night. Inside a quiet, warmly lit glass lobby the man (the film's recurring figure, seen only
from behind) walks away toward the entrance; the automatic glass doors slide open, he steps out onto the wet
plaza where a car waits with its lights on, and the doors slide shut behind him. Camera behind, slow push."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import area_light, world_flat
from human import pose_walk, _world_verts
from people import man
from sc_corp import arms_down

EXPOSURE = 0.0
FRAMES = {"walkout": 196}
DOOR_Y = 6.0
SPEED = 1.15                  # m/s


def build(variant=None):
    c = {}
    world_flat((0.01, 0.014, 0.025), 1.0)
    # interior: polished stone floor, stone walls, wooden reception, warm downlights
    stone = pbr("LobbyFloor", (0.32, 0.3, 0.28), 0.12, 0.0, **{'Coat Weight': 0.5})
    N = stone.node_tree.nodes; L = stone.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.offset = 0.5; br.inputs['Scale'].default_value = 0.6
    br.inputs['Brick Width'].default_value = 1.2; br.inputs['Row Height'].default_value = 0.6; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Color1'].default_value = (0.33, 0.31, 0.29, 1); br.inputs['Color2'].default_value = (0.28, 0.27, 0.25, 1); br.inputs['Mortar'].default_value = (0.15, 0.15, 0.15, 1)
    L.new(tc.outputs['Object'], br.inputs['Vector']); L.new(br.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    box("Floor", (0, 0, -0.01), (14, 14, 0.02), stone)
    wall = pbr("LobbyWall", (0.42, 0.4, 0.37), 0.7)
    box("WallL", (-5, -1, 2.5), (0.2, 14, 5.0), wall); box("WallR", (5, -1, 2.5), (0.2, 14, 5.0), wall)
    box("Ceil", (0, -1, 5.0), (10, 14, 0.1), pbr("Ceil", (0.2, 0.2, 0.2), 0.8))
    oak = wood("Reception", (0.18, 0.11, 0.06), (0.32, 0.2, 0.11), scale=(0.3, 6, 6), rough=0.35, coat=0.3)
    box("Reception", (-3.2, 1.0, 0.55), (1.0, 3.2, 1.1), oak, bevel=0.02)
    box("RecTop", (-3.2, 1.0, 1.12), (1.15, 3.35, 0.04), pbr("RecTop", (0.1, 0.1, 0.1), 0.2, 0.0, **{'Coat Weight': 0.6}))
    for k in range(4):
        for x in (-2.0, 2.0):
            box("Downlight", (x, -4 + k * 2.6, 4.97), (0.25, 0.25, 0.02), emissive("Downlight", (1.0, 0.85, 0.65), 12))
            l = bpy.data.lights.new("Down", 'SPOT'); l.energy = 420; l.spot_size = math.radians(80); l.spot_blend = 0.6; l.color = (1.0, 0.82, 0.62)
            o = bpy.data.objects.new("Down", l); bpy.context.collection.objects.link(o); o.location = (x, -4 + k * 2.6, 4.9); point_at(o, (x, -4 + k * 2.6, 0))
    for x in (-4.2, 4.2):
        import ph
        try:
            ph.model("potted_plant_02", loc=(x, 3.8, 0.0), scale=2.0)
        except Exception:
            pass
    # the glass front: fixed panes + a pair of sliding doors (open as he approaches, shut behind him)
    gl = glass("FrontGlass", (0.88, 0.92, 0.95), 0.01)
    frame = pbr("DoorFrame", (0.08, 0.08, 0.085), 0.35, 0.8)
    for x in (-3.4, 3.4):
        box("FixedPane", (x, DOOR_Y, 2.5), (3.2, 0.03, 5.0), gl)
        box("Mullion", (x + (1.6 if x < 0 else -1.6), DOOR_Y, 2.5), (0.08, 0.1, 5.0), frame)
    box("Transom", (0, DOOR_Y, 2.4), (10, 0.12, 0.1), frame)
    box("Header", (0, DOOR_Y, 2.65), (3.4, 0.25, 0.35), frame)
    doors = []
    for s in (-1, 1):
        d = box("SlideDoor", (0, 0, 0), (0.88, 0.025, 2.3), gl)
        e = box("SlideEdge", (0, 0, 0), (0.88, 0.04, 0.06), frame); e.parent = d; e.location = (0, 0, -1.12)
        d.location = (s * 0.45, DOOR_Y, 1.17); doors.append((d, s))
    c["doors"] = doors
    # outside: wet plaza, bollards, streetlight, the waiting car with its lights on
    wet = pbr("Plaza", (0.03, 0.03, 0.035), 0.08, 0.0, **{'Coat Weight': 0.6})
    box("Plaza", (0, 18, -0.02), (60, 24, 0.04), wet)
    for k in range(-4, 5):
        cyl("Bollard", (k * 1.6, 9.5, 0.45), 0.08, 0.9, pbr("Bollard", (0.1, 0.1, 0.11), 0.4, 0.6), verts=12)
    cyl("Pole", (6.5, 12, 4.0), 0.1, 8.0, frame, verts=10)
    box("Head", (6.5, 12, 8.0), (0.5, 1.5, 0.2), emissive("Sodium", (1.0, 0.72, 0.45), 30))
    l = bpy.data.lights.new("StreetL", 'SPOT'); l.energy = 3000; l.spot_size = math.radians(100); l.color = (1.0, 0.75, 0.48)
    o = bpy.data.objects.new("StreetL", l); bpy.context.collection.objects.link(o); o.location = (6.5, 12, 7.8); point_at(o, (3, 12, 0))
    import vehicles
    vehicles.make("sedan_modern", loc=(2.2, 14.5, 0), heading_deg=180, color=(0.02, 0.02, 0.025), lamps=True, real_lights=True)
    win = window_material("Far", density=0.22, floor=3.6, bay=1.8, strength=0.7)
    skyline(8, (0, 520, 0), (900, 200), 70, (40, 200), None, win, footprint=(25, 50))
    # the man
    h = man("Exec"); c["h"] = h
    return c


def anim(c, t):
    sec = t * FRAMES["walkout"] / 24
    h = c["h"]
    y = -1.0 + SPEED * sec
    y = min(y, 9.0)
    walking = y < 9.0
    ph_ = (SPEED * sec / 1.35) % 1.0
    bob = pose_walk(h, ph_ if walking else 0.0, stride=26 if walking else 0.0, arm_swing=16 if walking else 0.0)
    h.arm.rotation_euler = (0, 0, math.pi); h.arm.location = (0.15, y, bob); bpy.context.view_layer.update()
    if walking:
        arms_down(h, ph_, 16)
    # doors: open when he is within 2.2 m of the line, close 1.0 s after he has passed it (+0.9 m clear)
    dy = DOOR_Y - y
    if dy > 2.2:
        k = 0.0
    elif dy > -0.9:
        k = min(1.0, (2.2 - dy) / 1.0)
    else:
        k = max(0.0, 1.0 - (-0.9 - dy) / 1.3)
    for d, s in c["doors"]:
        d.location.x = s * (0.45 + 0.85 * ease(k))
    c["p"] = Vector((0.15, y, 1.2))
    bpy.context.view_layer.update()


def cam(c, t):
    e = ease(t)
    return (Vector((0.6, -5.2, 1.55)).lerp(Vector((0.4, -3.2, 1.6)), e), Vector((0.1, 8.0, 1.35)), 30)


MOVES = {"walkout": dict(kind="anim", dof=4.0, far=200.0, anim=anim, cam=cam, focus=lambda c, t: c["p"])}
