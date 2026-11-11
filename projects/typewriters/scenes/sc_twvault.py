"""COMMUNICATIONS VAULT (dramatization). A windowless secure room: painted steel walls, a vault door, racks of
cipher machines with indicator lamps, teletypes printing and punching tape.

Intro 7A  push   slow push past a teletype printing and punching tape beside a cipher machine (room lit)
Intro 7B  sweep  the room dark: a Marine's flashlight sweeps across the machines
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import machines as MC

EXPOSURE = 0.0
DUR = {"push": 4.5, "sweep": 5.0}
VARIANT_FOR = {"sweep": "dark"}


def build(variant=None):
    c = {"variant": variant}
    dark = variant == "dark"
    world_flat((0.003, 0.004, 0.006), 1.0)
    box("Floor", (0, 0, -0.01), (8, 6, 0.02), ph.texture("concrete_floor_painted", scale=0.5, name="VaultFloor", tint=(0.6, 0.65, 0.62)))
    steel = pbr("VaultWall", (0.32, 0.35, 0.33), 0.5, 0.3)
    N = steel.node_tree.nodes; L = steel.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = 1.2; br.inputs['Row Height'].default_value = 1.0
    br.inputs['Color1'].default_value = (0.32, 0.35, 0.33, 1); br.inputs['Color2'].default_value = (0.3, 0.33, 0.31, 1); br.inputs['Mortar'].default_value = (0.1, 0.11, 0.1, 1)
    L.new(tc.outputs['Object'], br.inputs['Vector']); L.new(br.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    for (x, y, sx, sy) in ((0, 3.05, 8, 0.1), (0, -3.05, 8, 0.1), (-4.05, 0, 0.1, 6), (4.05, 0, 0.1, 6)):
        box("Wall", (x, y, 1.4), (sx, sy, 2.8), steel)
    box("Ceiling", (0, 0, 2.82), (8, 6, 0.04), pbr("VaultCeil", (0.4, 0.4, 0.39), 0.8))
    # vault door (round-cornered steel slab with a wheel) on the -X wall
    door_m = pbr("VaultDoor", (0.5, 0.52, 0.5), 0.35, 0.9)
    box("VaultDoor", (-3.97, 0.8, 1.05), (0.12, 1.1, 2.0), door_m, bevel=0.04)
    cyl("Wheel", (-3.88, 0.8, 1.1), 0.22, 0.04, door_m, verts=32, rot=(0, math.radians(90), 0))
    for k in range(4):
        box("Spoke", (-3.86, 0.8, 1.1), (0.02, 0.46, 0.03), door_m, rot=(k * math.pi / 4, 0, 0))
    # racks of cipher machines along the back wall, teletypes in front, a terminal desk
    c["lamps"] = []
    for k in range(6):
        x = -3.0 + k * 0.75
        for j in range(3):
            MC.cipher(f"VC{k}{j}", (x, 2.65, j * 0.52), 0.0, height=0.48)
        box("RackFrame", (x, 2.7, 0.78), (0.6, 0.6, 1.58), pbr("Rack", (0.08, 0.08, 0.085), 0.4, 0.6))
    MC.lamp_blink(period=19, strength=8.0)
    c["tty"] = []
    for k, x in enumerate((-1.0, 0.5, 2.0)):
        r, p = MC.teletype(f"VTTY{k}", (x, 0.6, 0), math.radians(5 * (k - 1))); c["tty"].append(p)
    MC.cipher("VCdesk", (-1.0 + 0.62, 0.62, 0.72), 0.0, height=0.3)       # beside the first teletype
    ph.model("metal_office_desk", loc=(2.6, -1.8, 0), rot_z=0.0, scale=0.8)
    MC.terminal("VTerm", (2.6, -1.8, 0.632), 0.0)
    ph.model("SchoolChair_01", loc=(2.6, -2.4, 0), rot_z=0.0)
    if not dark:
        for x in (-2.0, 1.5):
            ph.model("mounted_fluorescent_lights", loc=(x, 0.5, 2.8), rot_z=math.radians(90))
            l = area_light((x, 0.5, 2.72), (0, 0, 0), 0.9, 45, (0.88, 0.95, 1.0)); l.visible_camera = False
    else:
        corr = area_light((-3.0, 1.9, 2.6), (0, 0, 0), 1.2, 25, (0.55, 0.65, 0.9)); point_at(corr, (-2.6, -0.4, 0.8)); corr.visible_camera = False
    # the Marine with a flashlight (dark variant)
    m = twp.person("Marine", 1.0, 24, "male_casualsuit06", "short01", hv=0.2, cval=0.35, hue=0.12, sat=0.35)
    c["marine"] = m
    fl, _ = ph.model("signal_flashlight")
    c["torch"] = fl
    sp = bpy.data.lights.new("Torch", 'SPOT'); sp.energy = 900 if dark else 0; sp.spot_size = math.radians(24); sp.spot_blend = 0.35
    sp.color = (1.0, 0.92, 0.8); sp.shadow_soft_size = 0.01
    so = bpy.data.objects.new("Torch", sp); bpy.context.collection.objects.link(so); c["beam"] = so
    if dark:
        haze((0, 0, 1.4), (8, 6, 2.8), density=0.05, color=(0.8, 0.85, 0.9), anis=0.6)
    twp.hide(twp.person_objs(m) + [fl] + list(fl.children_recursive), not dark)
    animate(c, 0.0)
    return c


def animate(c, sec):
    from human import reach, fingers_curl
    for k, p in enumerate(c["tty"]):
        MC.run_teletype(p, sec + k * 0.7)
    if c["variant"] == "dark":
        m = c["marine"]
        twp.stand(m, (-3.1, -0.6, 0.0), math.radians(-115))                 # just inside the door, facing into the room
        a = math.radians(-60) + math.radians(95) * ease(sec / DUR["sweep"])
        aim = Vector((-3.1 + 4.5 * math.sin(a), -0.6 + 4.5 * math.cos(a), 0.9))
        sh = m.bone_head("upperarm01.R")
        hand_p = sh + (aim - sh).normalized() * 0.55 + Vector((0, 0, -0.05))
        reach(m, "R", hand_p, Vector((0.6, -0.4, -0.6)), aim - sh)
        fingers_curl(m, 60, thumb=30)
        d = (aim - hand_p).normalized()
        fl = c["torch"]; fl.location = hand_p + d * 0.05
        fl.rotation_mode = 'QUATERNION'; fl.rotation_quaternion = d.to_track_quat('Z', 'Y')
        b = c["beam"]; b.location = hand_p + d * 0.2
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
        m.rot("head", (0, 0, 1), 10 * math.sin(sec * 0.4))
    bpy.context.view_layer.update()


MOVES = {
    "push": dict(kind="anim", dof=2.0, anim=lambda c, t: animate(c, t * DUR["push"]),
                 cam=lambda c, t: (Vector((-2.0, -0.9, 1.25)).lerp(Vector((-1.45, -0.35, 1.18)), ease(t)), Vector((-0.6, 0.8, 1.0)), 35),
                 focus=lambda c, t: Vector((-1.0, 0.6, 1.1))),
    "sweep": dict(kind="anim", dof=None, anim=lambda c, t: animate(c, t * DUR["sweep"]),
                  cam=lambda c, t: (Vector((2.2, -2.6, 1.6)).lerp(Vector((1.9, -2.45, 1.6)), ease(t)), Vector((-1.6, 0.4, 1.1)), 28)),
}
