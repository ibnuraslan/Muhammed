"""Thumbnail 1 - WATCHED. Rainy night street (the film's shophouse street). The man in the leather jacket stands in
the foreground on the right, half in shadow, lit from below by his phone, eyes down. Across the street, soft and red-lit
under her umbrella, the woman stands still and watches him. Left third: dark arcade bokeh for the title."""
import math
import bpy
from mathutils import Vector, Matrix
import sc_street
from sc_street import STREET_W
from kit import pbr, emissive, box, cyl, haze
from human import reach, fingers_curl, rotate_bone
from people import man
from thumbkit import *

EXPOSURE = 0.2
LOOK = 'AgX - High Contrast'
VIGNETTE = 0.75

CAM = Vector((-0.35, -6.55, 1.62))
MAN = Vector((0.05, -4.95, 0.16))           # on the near pavement, just in front of the camera
WOMAN = Vector((-1.0, STREET_W / 2 + 1.1, 0.16))


def pose_woman(c):
    h = c["h"]
    stand(h, 0.6)
    # right hand up holding the umbrella shaft by her shoulder (as in the street set)
    aim_bone(h.arm, "upperarm01.R", (-0.15, -0.55, -0.82)); aim_bone(h.arm, "upperarm02.R", (-0.15, -0.55, -0.82))
    aim_bone(h.arm, "lowerarm01.R", (0.2, -0.4, 0.9)); aim_bone(h.arm, "lowerarm02.R", (0.2, -0.4, 0.9))
    fingers_curl(h, 70, side=("R",), thumb=40)
    place(h, WOMAN, 12)                       # faces across the street toward him
    ground(h, 0.16)
    look_at(h, MAN + Vector((0, 0, 1.6)), 0.8)
    gaze(h, MAN + Vector((0, 0, 1.6)))
    hand = h.bone_tail("wrist.R"); head = h.bone_head("head")
    top = Vector((hand.x + 0.03, hand.y - 0.05, head.z + 0.40))
    can, shaft = c["umbrella"]
    can.location = top + Vector((0, 0, -0.14)); shaft.location = top + Vector((0, 0, -0.45))
    can.rotation_euler = (math.radians(-10), math.radians(4), 0); shaft.rotation_euler = can.rotation_euler


def pose_man(m, ph):
    stand(m, 0.3)
    place(m, MAN, -38)                        # three-quarter toward camera-left
    ground(m, 0.16)
    sh = m.bone_head("upperarm01.R")
    fd = face_dir(-38)
    hold = m.bone_head("neck01") + fd * 0.30 + Vector((0, 0, -0.12)) + Vector((-fd.y, fd.x, 0)) * -0.04
    reach(m, "R", hold, Vector((0.3, 0.2, -1.0)), fd + Vector((0, 0, 0.9)))
    fingers_curl(m, 45, side=("R",), thumb=10)
    # left hand in the jacket pocket area, arm relaxed
    look_at(m, hold + Vector((0, 0, -0.02)), 0.75)
    rotate_bone(m.arm, "head", Vector((-fd.y, fd.x, 0)), 6)       # chin down onto the screen
    gaze(m, hold)
    bpy.context.view_layer.update()
    w = m.bone_tail("wrist.R")
    # phone in the palm, screen toward his face
    body, scr = ph
    eye = m.bone_head("head") + Vector((0, 0, 0.1))
    n = (eye - w).normalized()
    pc = w + fd * 0.02 + Vector((0, 0, 0.05))
    up = Vector((0, 0, 1)); up = (up - n * up.dot(n)).normalized()
    x = up.cross(n)
    body.matrix_world = Matrix.Translation(pc) @ Matrix((x, up, n)).transposed().to_4x4()
    return pc, n


def build(variant=None):
    c = sc_street.build("haze")
    strip_lettering()
    pose_woman(c)
    # hide the passing traffic and bus: a still frame on an empty wet street
    for v in c["traffic"]:
        v["o"].location = (v["x0"] + 25, v["y"], 0) if not v.get("bus") else (-200, 0, -50)
    m = man("Man")
    ph = phone((0.75, 0.88, 1.0), 4.0)
    pc, n = pose_man(m, ph)
    # ---- lighting: phone glow on his face, red rim from the street, a red sign wash behind her
    face = m.bone_head("head") + Vector((0, 0, 0.08))
    k = soft(pc + n * 0.02, face, 2.5, (0.7, 0.85, 1.0), size=0.08, name="PhoneKey")
    light_only(k, m.parts)
    rim = spot(MAN + Vector((1.6, 3.2, 2.6)), face + Vector((0, 0, -0.1)), 900, (1.0, 0.08, 0.06), 18, 0.6, 0.3, "RedRim")
    light_only(rim, m.parts)
    rim2 = spot(MAN + Vector((-1.8, 2.6, 2.2)), face, 250, (0.4, 0.55, 1.0), 16, 0.6, 0.3, "CoolRim")
    light_only(rim2, m.parts)
    # the red sign glow over her: a lit shop front behind, and a red spill on her coat
    glow_card((WOMAN.x + 0.6, STREET_W / 2 + 2.15, 3.0), (2.6, 0.05, 0.6), (1.0, 0.05, 0.04), 10, name="RedSign")
    point((WOMAN.x + 0.2, WOMAN.y + 0.6, 2.6), 300, (1.0, 0.08, 0.05), 0.4, "RedSpill")
    spot((WOMAN.x - 1.0, WOMAN.y - 2.0, 3.5), WOMAN + Vector((0, 0, 1.4)), 120, (1.0, 0.15, 0.1), 25, 0.7, 0.3, "RedKeyHer")
    for mt in bpy.data.materials:              # shop interiors down: a darker, punchier frame
        if mt.name.startswith(("Interior", "Tube", "ShopWin")) and mt.use_nodes and "Principled BSDF" in mt.node_tree.nodes:
            p = mt.node_tree.nodes["Principled BSDF"]; p.inputs['Emission Strength'].default_value *= 0.35
    rain_curtains([-4.2, -2.0, 0.5, 3.0], width=20, height=9, density=0.94, strength=0.5)
    c["cam"] = (CAM, MAN + Vector((-0.42, 0, 1.5)), 50)
    c["focus"] = face
    c["fstop"] = 4.0
    return c
