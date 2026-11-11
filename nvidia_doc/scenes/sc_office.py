"""Dramatization: an open-plan tech office at night. Rows of desks with monitors and laptops; as the camera
glides down the aisle the screens wake one after another, each showing the same email. A few employees
(seen from behind) at their desks; city lights through the window wall."""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from human import Human, add_asset, pose_sit, aim_bone, fingers_curl, rotate_bone, _world_verts

EXPOSURE = 0.6
HERE = os.path.dirname(os.path.abspath(__file__))
ROWS, PER_ROW = 4, 7


def screen_material(name):
    """Monitor: dark until the shot clock passes this object's wake time (Object Info random), then the email."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); oi = N.new("ShaderNodeObjectInfo")
    tex = N.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(os.path.join(HERE, "..", "assets", "generated", "screen_email.png"))
    L.new(tc.outputs['UV'], tex.inputs['Vector'])
    clock = N.new("ShaderNodeValue"); clock.outputs[0].default_value = 0.0; clock.name = "Clock"
    # wake time = 0.15 + 0.7 * (distance-ordered random): stored per object as a custom property, read by Attribute
    wake = N.new("ShaderNodeAttribute"); wake.attribute_type = 'OBJECT'; wake.attribute_name = "wake"
    on = N.new("ShaderNodeMath"); on.operation = 'SUBTRACT'; L.new(clock.outputs[0], on.inputs[0]); L.new(wake.outputs['Fac'], on.inputs[1])
    ramp = N.new("ShaderNodeMapRange"); ramp.inputs['From Min'].default_value = 0.0; ramp.inputs['From Max'].default_value = 0.04
    L.new(on.outputs[0], ramp.inputs['Value'])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 1.6; L.new(ramp.outputs[0], st.inputs[0])
    L.new(tex.outputs['Color'], p.inputs['Emission Color']); L.new(st.outputs[0], p.inputs['Emission Strength'])
    p.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1); p.inputs['Roughness'].default_value = 0.15
    m["clock"] = clock.name
    return m


def uv_plane(name, loc, size, rot, mat):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    o.data.materials.append(mat)
    return o


def build(variant=None):
    world_flat((0.006, 0.009, 0.016), 1.0)
    box("Floor", (0, 6, -0.01), (16, 20, 0.02), fabric("Carpet", (0.05, 0.052, 0.058), 0.95, 0.2, 400))
    box("Ceiling", (0, 6, 3.0), (16, 20, 0.04), pbr("Ceil", (0.12, 0.12, 0.125), 0.8))
    for k in range(6):
        box("CeilLight", (0, 1 + k * 2.6, 2.97), (6, 0.12, 0.02), emissive("CeilLight", (0.9, 0.95, 1.0), 0.25))   # night mode: dimmed
    # window wall with the city
    box("WindowWall", (7.0, 6, 1.5), (0.02, 20, 3.0), glass("Win", (0.9, 0.93, 0.95), 0.01))
    win = window_material("City", lit=(1.0, 0.82, 0.55), density=0.25, floor=3.6, bay=1.6, strength=0.8)
    skyline(17, (220, 6, 0), (120, 220), 80, (30, 160), None, win, footprint=(20, 45), z0=-40)
    desk = pbr("Desk", (0.75, 0.74, 0.72), 0.35)
    leg = pbr("DeskLeg", (0.05, 0.05, 0.055), 0.4, 0.8)
    bezel = pbr("Bezel", (0.015, 0.015, 0.017), 0.3, 0.5)
    chair_m = fabric("ChairFab", (0.04, 0.045, 0.05), 0.85, 0.3, 300)
    screens = []
    rng = np.random.default_rng(8)
    smat = screen_material("Screen")
    for r in range(ROWS):
        for k in range(PER_ROW):
            x = -4.5 + r * 2.6; y = 0.5 + k * 1.7
            box("Desk", (x, y, 0.73), (0.8, 1.6, 0.03), desk)
            for dy in (-0.75, 0.75):
                box("DeskLeg", (x, y + dy, 0.36), (0.7, 0.04, 0.72), leg)
            # monitor faces -X (toward the aisle side where the chair is)
            mx = x + 0.25
            box("Monitor", (mx, y, 1.08), (0.03, 0.62, 0.38), bezel)
            box("Stand", (mx + 0.06, y, 0.86), (0.05, 0.08, 0.26), leg)
            scr = uv_plane("Scr", (mx - 0.017, y, 1.08), (0.58, 0.34), (math.radians(90), 0, math.radians(-90)), smat)
            # wake order: the camera dollies along +Y in the aisle at x ~ -3.2, so wake follows y with jitter
            scr["wake"] = 0.12 + 0.6 * (y / (PER_ROW * 1.7)) + rng.uniform(-0.06, 0.06) + 0.03 * r
            screens.append(scr)
            box("Keyboard", (x - 0.12, y, 0.755), (0.16, 0.45, 0.015), bezel)
            ch = join([box("Seat", (0, 0, 0.47), (0.5, 0.5, 0.08), chair_m, bevel=0.03),
                       box("Back", (0.24, 0, 0.82), (0.08, 0.48, 0.6), chair_m, bevel=0.04),
                       cyl("Stem", (0, 0, 0.24), 0.025, 0.44, leg)], "Chair")
            ch.location = (x - 0.75, y + rng.uniform(-0.1, 0.1), 0); ch.rotation_euler = (0, 0, rng.uniform(-0.3, 0.3))
    # a few late workers at their desks, from behind
    people = []
    for (r, k, g) in ((1, 2, 1.0), (2, 4, 0.0), (0, 5, 1.0)):
        x = -4.5 + r * 2.6 - 0.75; y = 0.5 + k * 1.7
        h = Human(f"Worker{r}{k}", gender=g, years=30 + 6 * r, muscle=0.5, weight=0.45, height=0.5, eyelashes=None)
        add_asset(h, "clothes", "male_casualsuit01" if g > 0.5 else "female_casualsuit01", val=0.5, rough=0.7)
        add_asset(h, "hair", "short02" if g > 0.5 else "ponytail01", val=0.3)
        pose_sit(h, lean=10)
        for sd, sg in (("L", 1), ("R", -1)):
            aim_bone(h.arm, f"lowerarm01.{sd}", (-0.2 * sg, -0.95, 0.15)); aim_bone(h.arm, f"lowerarm02.{sd}", (-0.2 * sg, -0.95, 0.15))
        h.arm.rotation_euler = (0, 0, math.radians(90))      # facing +X (their monitor)
        h.arm.location = (x - 0.05, y, 0); bpy.context.view_layer.update()
        w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
        h.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()
        people.append(h)
    return dict(screens=screens, mat=smat)


def _tick(c, t):
    c["mat"].node_tree.nodes[c["mat"]["clock"]].outputs[0].default_value = t


MOVES = {
    "dolly": dict(kind="anim", dof=2.8, far=40.0,
                  cam=lambda c, t: (Vector((-3.25, -1.2, 1.35)).lerp(Vector((-3.15, 3.2, 1.3)), ease(t)), (2.0, 8.0 + 2 * t, 0.95), 32),
                  focus=lambda c, t: (-1.6, 3.0 + 2 * t, 1.0), anim=_tick),
}
