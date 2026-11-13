"""CH4 hero sequence (chat B), labelled "Court reconstruction" on screen: how the court reconstructed the sound chain.
No hands at work in close-up, no faces: the figure at the booth is a faceless silhouette from behind and is
NOT any real person. Variants:
  table: a dim room at night. radio (A): a 1970s radio plays beside the reel recorder, reels turn, VU needle jumps.
                              copy  (B): track to a small cassette recorder beside it, record lamp on, spools turning.
  booth: a yellow public phone booth on a dark country road (generic 1981 style, no lettering).
                              booth (A): wide; a dark figure walks up from behind and steps to the booth.
                              mouth (B): from behind the figure inside: the little player held to the mouthpiece.
  line:  dusk fields.         poles (A): track along telephone wires on wooden poles toward a village.
(the last link, the police recorder in the family's hallway, is sc_b_hall "line_end")
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import world_flat, ease
from human import reach, fingers_curl
import ph
import b_common as B
import b_props as P

EXPOSURE = 0.0
DUR = {"radio": 5.0, "copy": 5.0, "booth": 6.0, "mouth": 5.0, "poles": 6.0}
VARIANT_FOR = {"radio": "table", "copy": "table", "booth": "booth", "mouth": "booth", "poles": "line"}
TOP = 0.8
LABEL = "Court reconstruction"


def sky(kind):
    try:
        import rj
        w, s = rj.sky(kind)
        return s
    except Exception as e:
        print("[chain] rj.sky unavailable:", e)
        world_flat((0.02, 0.03, 0.05), 1.0)
        return None


def cassette_recorder(name, loc, rot_z):
    """A small 1970s portable cassette recorder: black body, window with two spools (frame-driven spin), red lamp."""
    body = pbr(name + "Body", (0.03, 0.03, 0.032), 0.45)
    alu = brushed_metal(name + "Alu", (0.62, 0.62, 0.63), (0.2, 0.3), 0.4)
    parts = [box("CBody", (0, 0, 0.03), (0.26, 0.16, 0.06), body, bevel=0.008),
             box("CTop", (0, 0, 0.061), (0.25, 0.15, 0.003), alu)]
    for k in range(5):
        parts.append(box("CKey", (-0.09 + k * 0.035, -0.065, 0.068), (0.028, 0.03, 0.012), pbr(name + "K", (0.12, 0.12, 0.12), 0.4), bevel=0.002))
    root = join(parts, name)
    win = box(name + "Win", (0.02, 0.02, 0.064), (0.12, 0.07, 0.003), pbr(name + "WinG", (0.05, 0.05, 0.06), 0.05, **{'Coat Weight': 1.0}))
    win.parent = root
    spools = []
    for k, x in enumerate((-0.01, 0.05)):
        sp = cyl(name + f"Spool{k}", (x, 0.02, 0.066), 0.014, 0.003, pbr(name + "SpoolM", (0.85, 0.85, 0.85), 0.4), verts=6)
        sp.parent = root
        d = sp.driver_add("rotation_euler", 2).driver; d.type = 'SCRIPTED'; d.expression = f"-frame / 24 * 2.2 * 6.2832 + {k}"
        spools.append(sp)
    lamp = cyl(name + "Rec", (0.1, -0.06, 0.066), 0.005, 0.004, pbr(name + "RecM", (0.2, 0.0, 0.0), 0.3,
               **{'Emission Color': (1.0, 0.08, 0.04, 1), 'Emission Strength': 6.0}), verts=12)
    lamp.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    return root


def booth(loc, rot_z):
    """Yellow phone booth (1.0 x 1.0 x 2.3), glass on three sides and in the door, light tube under the roof."""
    yel = pbr("BoothYellow", (0.85, 0.42, 0.0), 0.4, **{'Coat Weight': 0.3})
    try:
        import rj
        gl = rj.window_glass()
    except Exception:
        gl = glass("BoothGlass", (0.9, 0.92, 0.9), 0.05)
    W, D, H = 1.0, 1.0, 2.3
    parts = [box("Roof", (0, 0, H - 0.06), (W + 0.06, D + 0.06, 0.12), yel, bevel=0.01),
             box("Base", (0, 0, 0.05), (W, D, 0.1), pbr("BoothBase", (0.25, 0.25, 0.25), 0.7)),
             box("Back", (0, D / 2 - 0.02, H / 2), (W, 0.04, H - 0.1), yel)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box("Post", (sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), H / 2), (0.06, 0.06, H), yel))
    for sx in (-1, 1):                                       # side panels: yellow below, glass above
        parts.append(box("SideLo", (sx * (W / 2 - 0.02), 0, 0.45), (0.03, D - 0.06, 0.7), yel))
        parts.append(box("SideRail", (sx * (W / 2 - 0.02), 0, 1.45), (0.03, D - 0.06, 0.05), yel))
    parts.append(box("DoorFrameT", (0, -D / 2 + 0.02, H - 0.17), (W - 0.06, 0.04, 0.1), yel))
    root = join(parts, "Booth")
    glasses = []
    for sx in (-1, 1):
        g = box("SideGlass", (sx * (W / 2 - 0.02), 0, 1.4), (0.01, D - 0.08, 1.5), gl); g.parent = root; glasses.append(g)
    door = box("DoorGlass", (0, -D / 2 + 0.02, 1.25), (W - 0.12, 0.01, 1.8), gl); door.parent = root
    box("DoorRail", (0, -D / 2 + 0.02, 0.6), (W - 0.12, 0.03, 0.05), yel).parent = root
    # the telephone on the back wall: grey box with a coin slot, handset in its cradle, a steel cord
    grey = pbr("PhoneGrey", (0.32, 0.33, 0.33), 0.4)
    tel = box("TelBox", (0.0, D / 2 - 0.1, 1.35), (0.22, 0.14, 0.42), grey, bevel=0.01); tel.parent = root
    hs = box("Handset", (0.0, 0, 0), (0.05, 0.05, 0.22), pbr("HandsetBlk", (0.03, 0.03, 0.03), 0.35), bevel=0.015)
    hs.parent = root; hs.location = (-0.14, D / 2 - 0.1, 1.4)
    tube = box("Tube", (0, 0, H - 0.14), (0.7, 0.05, 0.03), emissive("BoothTube", (0.85, 0.95, 0.9), 6.0)); tube.parent = root
    l = area_light((0, 0, H - 0.18), (0, 0, 0), 0.6, 60, (0.85, 0.95, 0.88)); l.visible_camera = False; l.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    return root, hs


def pole(name, loc, h=7.5):
    wd = pbr("PoleWood", (0.14, 0.1, 0.07), 0.85)
    parts = [cyl("Pole", (0, 0, h / 2), 0.11, h, wd, verts=16),
             box("Arm", (0, 0, h - 0.35), (1.3, 0.09, 0.09), wd)]
    for x in (-0.55, -0.2, 0.2, 0.55):
        parts.append(cyl("Ins", (x, 0, h - 0.25), 0.03, 0.1, pbr("Porcelain", (0.85, 0.85, 0.82), 0.2), verts=12))
    o = join(parts, name); o.location = loc
    return o


def wire(name, p0, p1, sag, m):
    pts = [Vector(p0).lerp(Vector(p1), k / 16) - Vector((0, 0, sag * 4 * (k / 16) * (1 - k / 16))) for k in range(17)]
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.006
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (*q, 1)
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o); o.data.materials.append(m)
    return o


def build(variant=None):
    variant = variant or "table"
    c = {"variant": variant}
    rng = np.random.default_rng(1981)
    if variant == "table":
        world_flat((0.006, 0.007, 0.01), 1.0)
        box("Floor", (0, 0, -0.01), (5, 5, 0.02), B.tex_mat("TFloor", "old_wooden_floor_02", scale=0.6, tint=(0.6, 0.55, 0.5)))
        wall = B.plaster("TWall", (0.36, 0.34, 0.3), dirt=0.3)
        box("WallB", (0, 1.2, 1.3), (5, 0.1, 2.6), wall); box("WallL", (-1.8, 0, 1.3), (0.1, 5, 2.6), wall)
        ph.model("wooden_table_02", loc=(0, 0.6, 0), rot_z=0)
        try:
            import rj
            r, dial = rj.kitchen_radio("ReconRadio")
            r.location = (-0.38, 0.75, TOP); r.rotation_euler = (0, 0, 0.25)
            dial.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = 3.0
        except Exception as e:
            print("[chain] rj radio unavailable:", e)
            ph.model("boombox", loc=(-0.38, 0.75, TOP), rot_z=0.25, scale=0.6)
        c["rec"] = P.reel_recorder("ReconRec", (0.12, 0.62, TOP), rot_z=-0.1, spin=0.45)
        c["cas"] = cassette_recorder("Cassette", (0.45, 0.42, TOP), -0.35)
        cab = pbr("Cable", (0.02, 0.02, 0.02), 0.5)
        wire("CableA", (-0.25, 0.72, TOP + 0.01), (-0.05, 0.62, TOP + 0.01), -0.0, cab)
        wire("CableB", (0.3, 0.55, TOP + 0.01), (0.4, 0.46, TOP + 0.01), -0.0, cab)
        ph.model("desk_lamp_arm_01", loc=(0.55, 0.85, TOP), rot_z=math.radians(-150))
        B.key_spot((0.3, 0.45, 1.5), (0.15, 0.55, TOP), 260, 85, (1.0, 0.74, 0.48), soft=0.04, name="Lamp")
        B.fill((-1.2, -1.5, 1.6), (0, 0.6, 0.9), 8, 1.2, (0.4, 0.55, 0.8))
        B.room_haze((0, 0, 1.2), (4.8, 4.8, 2.4), density=0.02)
    elif variant == "booth":
        sky("night")
        gr = B.tex_mat("Verge", "forest_ground_04", scale=0.3, tint=(0.35, 0.4, 0.3))
        box("Ground", (0, 0, -0.05), (120, 120, 0.1), gr)
        box("Road", (0, -3.0, 0.005), (120, 6.5, 0.02), B.tex_mat("Asph", "asphalt_02", scale=0.25, tint=(0.5, 0.5, 0.5)))
        box("Pave", (0, 1.0, 0.03), (6, 2.2, 0.06), B.tex_mat("Pave", "concrete_pavers", scale=0.5, tint=(0.6, 0.6, 0.6)))
        c["booth"], c["handset"] = booth((0.0, 1.2, 0.06), 0.0)
        # dark tree line behind, a street lamp further down the road
        B.ph_instances("fir_tree_01", [((-30 + k * 6.5 + rng.uniform(-1, 1), 12 + rng.uniform(0, 6), 0), rng.uniform(0, 6), 0.55) for k in range(10)])
        ph.model("street_lamp_01", loc=(7, 0.6, 0), rot_z=math.radians(90))
        B.key_spot((7, -0.6, 5.5), (5, -2.5, 0), 2500, 60, (1.0, 0.62, 0.3), soft=0.2, name="StreetLamp")
        B.fill((-6, -10, 4), (0, 1, 1), 600, 6, (0.35, 0.45, 0.8))
        B.room_haze((0, 0, 2.5), (60, 40, 5), density=0.006, color=(0.7, 0.75, 0.85))
        fig = B.person("Silhouette", 1.0, 40, "male_casualsuit05", "short02", hue=0.6, sat=0.1, val=0.12, hair_val=0.15)
        try:
            add_hat = __import__("human").add_asset
            add_hat(fig, "clothes", "fedora01", val=0.15, rough=0.6)
        except Exception as e:
            print("[chain] no hat:", e)
        c["fig"] = fig
        c["player"] = cassette_recorder("Pocket", (0, 0, -30), 0)
        c["player"].scale = (0.55, 0.55, 0.55)
    else:   # line
        sky("sunset")
        gr = B.tex_mat("Field", "farm_soil", scale=0.08, tint=(0.45, 0.42, 0.36))
        box("Field", (0, 0, -0.05), (600, 600, 0.1), gr)
        box("Lane", (0, 4.0, 0.01), (600, 4.0, 0.02), B.tex_mat("Lane", "gravel_road", scale=0.15, tint=(0.5, 0.48, 0.45)))
        wm = pbr("Wire", (0.02, 0.02, 0.02), 0.4, 0.6)
        c["wires"] = []
        n = 14
        for k in range(n):
            x = -60 + k * 42
            pole(f"Pole{k}", (x, 7.0, 0))
            if k:
                for wy, wz in ((-0.55, 7.25), (-0.2, 7.25), (0.2, 7.25), (0.55, 7.25)):
                    w = wire(f"W{k}{wy}", (x - 42, 7.0 + wy * 0 + 0.0, wz), (x, 7.0, wz), 0.6, wm)
                    w.location.x += wy * 0.0; w.location.y += 0.0
                    w.data.splines[0].points.foreach_get  # (keeps flake8 quiet)
                    w.location = (0, wy, 0)
                    c["wires"].append(w)
        # the village on the horizon: low roofs, a few lit windows, a church tower silhouette (generic)
        house_m = pbr("VillageDark", (0.05, 0.05, 0.06), 0.8)
        win_m = emissive("VillageWin", (1.0, 0.68, 0.35), 4.0)
        for k in range(18):
            x = 420 + rng.uniform(-60, 60); y = 7 + rng.uniform(-30, 30)
            w_, d_, h_ = rng.uniform(8, 14), rng.uniform(7, 11), rng.uniform(5, 8)
            box("House", (x, y, h_ / 2), (w_, d_, h_), house_m)
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=w_ * 0.75, depth=4, location=(x, y, h_ + 2), rotation=(0, 0, math.pi / 4))
            bpy.context.active_object.data.materials.append(house_m)
            if k % 3 == 0:
                box("Win", (x - w_ / 2 - 0.05, y, h_ * 0.5), (0.05, 1.0, 1.2), win_m)
        box("Tower", (430, 0, 14), (6, 6, 28), house_m)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=4.2, depth=10, location=(430, 0, 33)); bpy.context.active_object.data.materials.append(house_m)
        B.room_haze((200, 0, 15), (700, 300, 30), density=0.0012, color=(0.75, 0.7, 0.75))
    if variant == "table":
        B.finish_interior(lift=0.25)
    else:
        B.preview_cap()
    return c


def anim(c, t, move):
    sec = t * DUR[move]
    B.label(c, LABEL)
    if move == "booth":
        fig = c["fig"]
        u = ease(min(1.0, sec / (DUR["booth"] * 0.85)))
        B.walk_to(fig, (-3.5, -4.0, 0), (0.0, 0.25, 0), u, 4.5 * u + 0.001, stride=22, swing=12)
        if u >= 0.999:
            B.stand(fig, (0.0, 0.25, 0), math.atan2(0.0, -1.0) + math.pi)
    elif move == "mouth":
        fig = c["fig"]
        B.stand(fig, (0.0, 1.05, 0.06), math.pi)               # inside, facing the phone (+Y)
        fwd = B.fwd_of(fig); side = fwd.cross(Vector((0, 0, 1))).normalized()
        chest = fig.bone_head("neck01") + fwd * 0.3 + Vector((0, 0, -0.12))
        hs = c["handset"]; hs.parent = None
        hs.location = chest + side * 0.05 + Vector((0, 0, 0.02 * math.sin(sec * 0.8)))
        hs.rotation_euler = (0, math.radians(70), 0)
        pl = c["player"]; pl.location = hs.location + fwd * 0.03 + side * -0.08 + Vector((0, 0, -0.03))
        pl.rotation_euler = (math.radians(80), 0, 0)
        reach(fig, "R", hs.location + side * 0.06, Vector((0.2, -0.3, -1)), fwd)
        reach(fig, "L", pl.location - side * 0.04, Vector((-0.2, -0.3, -1)), fwd)
        B.curl(fig, 50, thumb=30)
        B.nod(fig, 14)
    elif move == "poles":
        for k, w in enumerate(c["wires"]):
            w.rotation_euler = (0.004 * math.sin(sec * 1.3 + k), 0, 0)
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


MOVES = {
    "radio": dict(kind="anim", dof=None, cam=cam((-0.95, -0.7, 1.4), (-0.75, -0.5, 1.33), (0.0, 0.6, TOP + 0.05), 35),
                  anim=lambda c, t: anim(c, t, "radio")),
    "copy": dict(kind="anim", dof=None, cam=cam((0.0, -0.3, 1.2), (0.15, -0.15, 1.15), (0.45, 0.42, TOP + 0.04), 40),
                 anim=lambda c, t: anim(c, t, "copy")),
    "booth": dict(kind="anim", dof=None, cam=cam((-6.0, -7.5, 1.7), (-5.2, -6.6, 1.65), (-0.3, 0.8, 1.3), 35),
                  anim=lambda c, t: anim(c, t, "booth")),
    "mouth": dict(kind="anim", dof=None, cam=cam((0.25, -0.75, 1.75), (0.15, -0.55, 1.72), (0.0, 1.4, 1.35), 35),
                  anim=lambda c, t: anim(c, t, "mouth")),
    "poles": dict(kind="anim", dof=None, cam=cam((-38, 4.0, 6.2), (-26, 4.3, 6.6), (60, 7.5, 5.0), 30),
                  anim=lambda c, t: anim(c, t, "poles")),
}
