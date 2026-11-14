"""Chat B storyboard v2, 3-10A: "A television appeal puts the case in front of viewers across West Germany."
A dark 1981 living room: the TV plays the appeal (the studio frame from sc_b_media on its screen). The camera pulls
back from the set, out through the window, and keeps going: up and down the street every window flickers with the
same blue light. One broadcast, many homes. No faces (the room is empty, the street is at night).
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import ease, world_flat, area_light, point_at
import b_common as B

EXPOSURE = 0.3
DUR = {"tvstreet": 7.0}
VARIANT_FOR = {"tvstreet": "tvstreet"}
WY = -1.0                     # the front wall of the room (window), street side is -Y


def crt(name, loc, screen_img):
    body = pbr(name + "Wood", (0.2, 0.12, 0.06), 0.45, **{'Coat Weight': 0.5})
    parts = [box(name + "Case", (0, 0, 0.27), (0.66, 0.5, 0.54), body, bevel=0.02),
             box(name + "Bezel", (-0.06, -0.252, 0.29), (0.5, 0.01, 0.4), pbr(name + "Bezel", (0.05, 0.05, 0.05), 0.4), bevel=0.02),
             box(name + "Panel", (0.25, -0.252, 0.29), (0.1, 0.008, 0.4), pbr(name + "PanelM", (0.55, 0.55, 0.56), 0.35, 0.8))]
    for k in range(3):
        parts.append(cyl(name + "Knob", (0.25, -0.258, 0.4 - k * 0.09), 0.018, 0.012, pbr("KnobB", (0.08, 0.08, 0.08), 0.4), verts=16, rot=(math.radians(90), 0, 0)))
    o = join(parts, name); o.location = loc
    scr_m = B.img_mat(name + "Scr", screen_img, 0.4)
    p = scr_m.node_tree.nodes.get("Principled BSDF")
    tex = next((n for n in scr_m.node_tree.nodes if n.type == 'TEX_IMAGE'), None)
    if p and tex:
        scr_m.node_tree.links.new(tex.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = 1.6
    bpy.ops.mesh.primitive_plane_add(size=1, location=(loc[0] - 0.06, loc[1] - 0.258, loc[2] + 0.29), rotation=(math.radians(90), 0, 0))
    scr = bpy.context.active_object; scr.scale = (0.44, 0.33, 1); scr.data.materials.append(scr_m)
    return o, scr_m


def build(variant=None):
    c = {"variant": "tvstreet"}
    rng = np.random.default_rng(10)
    world_flat((0.006, 0.008, 0.016), 1.0)
    # ---------------------------------------------------------------- the room
    paper = B.plaster("Room81", (0.4, 0.33, 0.24))
    box("RFloor", (0, 0.5, -0.01), (4.2, 3.2, 0.02), B.tex_mat("RCarpet", "dirty_carpet", scale=0.5, tint=(0.5, 0.38, 0.28)))
    box("RBack", (0, 2.05, 1.3), (4.2, 0.1, 2.6), paper); box("RLeft", (-2.05, 0.5, 1.3), (0.1, 3.2, 2.6), paper)
    box("RRight", (2.05, 0.5, 1.3), (0.1, 3.2, 2.6), paper); box("RCeil", (0, 0.5, 2.62), (4.2, 3.2, 0.04), paper)
    # front wall with a real window opening x -0.65..0.65, z 0.9..2.1
    ext = B.tex_mat("Render", "grey_plaster_02", scale=0.4, tint=(0.62, 0.6, 0.56))
    for (x, z, sx, sz) in ((-1.825, 1.3, 2.35, 2.6), (1.825, 1.3, 2.35, 2.6), (0, 0.45, 1.3, 0.9), (0, 2.35, 1.3, 0.5)):
        box("FrontWall", (x, WY, z), (sx, 0.2, sz), ext)
    fr = pbr("WinFrame81", (0.85, 0.84, 0.8), 0.45)
    for (x, z, sx, sz) in ((0, 2.08, 1.3, 0.06), (0, 0.92, 1.3, 0.06), (-0.62, 1.5, 0.06, 1.2), (0.62, 1.5, 0.06, 1.2), (0, 1.5, 0.05, 1.2)):
        box("WFrame", (x, WY - 0.08, z), (sx, 0.08, sz), fr)
    box("WSill", (0, WY - 0.16, 0.87), (1.45, 0.24, 0.05), pbr("Sill", (0.6, 0.58, 0.55), 0.6))
    cm = fabric("Curt81", (0.42, 0.3, 0.18), 0.92, 0.3, 220)
    for sx in (-1, 1):
        box("Curtain", (sx * 0.85, WY + 0.15, 1.45), (0.4, 0.05, 1.6), cm, bevel=0.01)
    import ph
    ph.model("Sofa_01", loc=(0.0, 0.0, 0), rot_z=math.pi)                  # sofa faces the TV (+Y)
    box("TVStand", (0, 1.65, 0.25), (0.9, 0.45, 0.5), pbr("Stand", (0.18, 0.11, 0.06), 0.5))
    img = "/home/user/Muhammed/projects/radio-jingle/assets/generated/b_appeal_screen.png"
    tv, scr_m = crt("CRT", (0, 1.65, 0.5), img)
    c["scr_m"] = scr_m
    glow = area_light((0, 1.2, 0.8), (0, 0, 0), 0.5, 18, (0.7, 0.8, 1.0)); point_at(glow, (0, -0.5, 0.6)); glow.visible_camera = False
    c["glow"] = glow
    # ---------------------------------------------------------------- the street outside, many homes, same glow
    box("Street", (0, -8, -0.02), (80, 12, 0.02), B.tex_mat("Asph", "asphalt_02", scale=0.25, tint=(0.4, 0.4, 0.4)))
    box("Pavement", (0, -2.0, 0.04), (80, 2.0, 0.08), B.tex_mat("Pav", "concrete_pavers", scale=0.5, tint=(0.5, 0.5, 0.5)))
    c["tvmats"] = []
    for k, x0 in enumerate((-14.5, -7.3, 7.3, 14.5)):                   # neighbours either side, gables to the street
        w = 6.5
        box(f"House{k}", (x0, WY + 4.0, 3.2), (w, 8.0, 6.4), ext if k % 2 else B.tex_mat("Brick", "brick_wall_02", scale=0.35, tint=(0.55, 0.42, 0.36)))
        for fl in range(2):
            for j in range(2):
                parts = B.facade_window(x0 - 1.4 + j * 2.8, WY, 1.5 + fl * 2.8, 1.1, 1.25, lit=True, name=f"N{k}{fl}{j}")
                lm = bpy.data.materials.get(f"N{k}{fl}{j}Lit")
                if lm:
                    pp = lm.node_tree.nodes["Principled BSDF"]; pp.inputs['Emission Color'].default_value = (0.55, 0.68, 1.0, 1)
                    c["tvmats"].append((pp, rng.uniform(0.25, 0.9)))
    box("OwnHouse", (0, WY + 4.0, 4.3), (6.0, 0.2, 3.8), ext)                 # upper storey of our house, dark windows
    for j in (-1.6, 1.6):
        B.facade_window(j, WY - 0.1, 3.9, 1.0, 1.2, lit=False, name=f"Own{j}")
    try:
        ph.model("street_lamp_01", loc=(5.0, -2.8, 0.0), rot_z=math.radians(90))
    except Exception as e:
        print("[tv] lamp", e)
    B.key_spot((5.0, -3.4, 4.8), (2.0, -1.5, 0.5), 900, 60, (1.0, 0.66, 0.36), soft=0.2, name="Sodium")
    B.fill((0, -14, 6), (0, 0, 2), 260, 14, (0.35, 0.45, 0.8))
    B.room_haze((0, -4, 3), (40, 12, 6), density=0.004, color=(0.6, 0.65, 0.8))
    B.finish_interior(lift=0.0, faces=0)
    return c


def anim(c, t, move):
    sec = t * DUR[move]
    f = 0.85 + 0.15 * math.sin(sec * 11.0) * math.sin(sec * 3.7)        # one broadcast, the same flicker everywhere
    c["scr_m"].node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = 1.6 * f
    c["glow"].data.energy = 18 * f
    for pp, base in c["tvmats"]:
        pp.inputs['Emission Strength'].default_value = 0.9 * base * f
    bpy.context.view_layer.update()


def cam_pull(c, t):
    """Pull back from the screen, through the window, out across the street, rising."""
    path = [Vector((0.0, 1.0, 0.85)), Vector((0.0, 0.2, 1.25)), Vector((0.0, WY + 0.4, 1.45)), Vector((0.0, WY - 0.6, 1.5)),
            Vector((0.6, -5.0, 2.3)), Vector((1.0, -17.0, 4.2))]
    u = ease(t) * (len(path) - 1); k = min(len(path) - 2, int(u)); f = u - k
    pos = path[k].lerp(path[k + 1], f)
    tgt = Vector((0.0, 1.85, 0.8)).lerp(Vector((0.0, WY + 2.0, 2.4)), ease(max(0.0, (t - 0.45) / 0.55)))
    return pos, tgt, 30 - 6 * ease(max(0.0, (t - 0.5) / 0.5))


MOVES = {"tvstreet": dict(kind="anim", dof=None, cam=cam_pull, anim=lambda c, t: anim(c, t, "tvstreet"))}
