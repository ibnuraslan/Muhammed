"""MEMORIAL HALL, Moscow City Hall, August 1995 (dramatization). A marble hall with columns and chandeliers; a stand
draped in black and red with a framed photograph turned to the light (no likeness: the glass catches the chandeliers)
and a growing bank of carnations.
  11A: mourners in dark coats file past; one lays carnations below the stand.
  11B: wide: two dignitaries (unnamed) stand before the stand, heads bowed, backlit by the tall windows."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
from pbkit import joinm, glazed_window, masonry_facade
from pbpeople import person, stand, walk_at, nod, look, hand_to, hide, fwd

EXPOSURE = 0.2
BOUNCES = 6
DUR = {"mourners": 6.0, "dignitaries": 6.0}
VARIANT_FOR = {"mourners": None, "dignitaries": None}
STAND = Vector((0.0, 6.0, 0.0))
rng = np.random.default_rng(23)


def carnation(loc, col):
    head = pbr("Carn" + str(col), col, 0.7, 0.0, **{'Subsurface Weight': 0.3})
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.03, location=loc)
    h = bpy.context.active_object; h.data.materials.append(head)
    tx = bpy.data.textures.get("Petals") or bpy.data.textures.new("Petals", 'CLOUDS'); tx.noise_scale = 0.01
    d = h.modifiers.new("petals", 'DISPLACE'); d.texture = tx; d.strength = 0.012
    stem = cyl("Stem", (loc[0], loc[1] - 0.15, loc[2] - 0.01), 0.003, 0.3, pbr("StemGreen", (0.1, 0.25, 0.08), 0.6), verts=6, rot=(math.radians(90), 0, 0))
    return [h, stem]


def build(variant=None):
    c = {}
    world_flat((0.75, 0.78, 0.82), 0.6)
    marble = ph.texture("marble_tiles", scale=0.5)
    W, D, H = 14.0, 18.0, 7.5
    box("Floor", (0, 2, -0.01), (W, D, 0.02), marble)
    wall = pbr("HallWall", (0.72, 0.68, 0.6), 0.6)
    box("Ceiling", (0, 2, H), (W, D, 0.1), pbr("HallCeil", (0.8, 0.77, 0.7), 0.7))
    box("WallL", (-W / 2, 2, H / 2), (0.2, D, H), wall); box("WallR", (W / 2, 2, H / 2), (0.2, D, H), wall)
    # back wall behind the stand: three tall windows (the light source), heavy drapes
    for x in (-4.5, 0.0, 4.5):
        glazed_window("TallWin", (x, D / 2 + 2.0, 3.6), 2.0, 5.0, normal="y", cols=2, rows=5, frame_col=(0.82, 0.8, 0.74))
    for (x0, x1) in ((-W / 2, -5.5), (-3.5, -1.0), (1.0, 3.5), (5.5, W / 2)):
        box("BackPier", ((x0 + x1) / 2, D / 2 + 2.05, H / 2), (x1 - x0, 0.2, H), wall)
    box("BackTop", (0, D / 2 + 2.05, 6.6), (W, 0.2, 1.8), wall)
    for x in (-4.5, 0.0, 4.5):
        l = area_light((x, D / 2 + 1.75, 3.6), (math.radians(-90), 0, 0), 2.0, 260, (0.9, 0.94, 1.0)); l.visible_camera = False; l.visible_glossy = False; l.visible_transmission = False
        l.data.size_y = 5.0; l.data.shape = 'RECTANGLE'
    # outside the windows: a square with a row of buildings across it, under a pale summer sky
    box("MemOutside", (0, D / 2 + 26, 10), (70, 1, 30), masonry_facade("MemOpp", (0.66, 0.62, 0.55), 3.4, 2.8, 1.3, 1.8, 0.0, lit_strength=0.0))
    box("MemSquare", (0, D / 2 + 14, -0.3), (70, 24, 0.2), pbr("MemSquareM", (0.5, 0.5, 0.48), 0.9))
    box("FrontWall", (0, -D / 2 + 2, H / 2), (W, 0.2, H), wall)
    # columns along both sides
    col_m = pbr("ColumnMarble", (0.82, 0.8, 0.75), 0.25)
    for sx in (-1, 1):
        for k in range(5):
            y = -4 + k * 3.2
            cyl("Column", (sx * 5.2, y, H / 2), 0.38, H, col_m, verts=32)
            box("ColBase", (sx * 5.2, y, 0.15), (0.95, 0.95, 0.3), col_m)
            box("ColCap", (sx * 5.2, y, H - 0.2), (0.95, 0.95, 0.4), col_m)
    for y in (-2.0, 3.0, 8.0):
        ph.model("Chandelier_01", loc=(0, y, H), rot_z=0.3, scale=2.2)
        l = bpy.data.lights.new("Chand", 'POINT'); l.energy = 300; l.color = (1.0, 0.85, 0.6)
        o = bpy.data.objects.new("Chand", l); bpy.context.collection.objects.link(o); o.location = (0, y, H - 1.4)
    # the memorial stand: a draped table, a framed photograph on an easel turned to the window light, black ribbon
    drape = fabric("BlackDrape", (0.02, 0.02, 0.025), 0.9, 0.5, 300)
    red = fabric("RedDrape", (0.35, 0.03, 0.03), 0.85, 0.6, 300)
    box("StandTable", (STAND.x, STAND.y, 0.45), (2.6, 0.9, 0.9), drape, bevel=0.05)
    box("StandRunner", (STAND.x, STAND.y - 0.46, 0.6), (2.0, 0.02, 0.6), red)
    frame = joinm([box("PhotoFrame", (0, 0, 0), (0.6, 0.04, 0.8), pbr("FrameDark", (0.05, 0.03, 0.02), 0.3), bevel=0.01),
                   box("PhotoGlass", (0, -0.025, 0), (0.5, 0.005, 0.7), pbr("PhotoGlass", (0.02, 0.02, 0.025), 0.03, 0.0, **{'Coat Weight': 1.0})),
                   box("Ribbon", (0.18, -0.03, 0.26), (0.05, 0.005, 0.38), pbr("Ribbon", (0.0, 0.0, 0.0), 0.5), rot=(0, math.radians(45), 0))], "Portrait")
    frame.location = (STAND.x, STAND.y + 0.1, 1.45); frame.rotation_euler = (math.radians(-8), 0, 0)
    # flowers already laid along the front of the stand
    flowers = []
    for k in range(120):
        p = (STAND.x + rng.uniform(-1.2, 1.2), STAND.y - 0.6 - rng.uniform(0, 0.35), 0.03 + rng.uniform(0, 0.06))
        flowers += carnation(p, (0.6, 0.04, 0.05) if k % 5 else (0.85, 0.82, 0.78))
    for k in range(60):                                                       # flowers on the table too
        flowers += carnation((STAND.x + rng.uniform(-1.1, 1.1), STAND.y - rng.uniform(-0.3, 0.3), 0.93), (0.6, 0.04, 0.05) if k % 4 else (0.85, 0.82, 0.78))
    # people
    c["mourners"] = [person(f"Mourner{k}", g, y, cl, hr, cval=v, hv=0.25)
                     for k, (g, y, cl, hr, v) in enumerate(((1.0, 60, "male_elegantsuit01", "short04", 0.1), (0.0, 52, "female_elegantsuit01", "bob01", 0.08),
                                                             (1.0, 45, "male_casualsuit05", "short02", 0.1), (0.0, 38, "female_elegantsuit01", "long01", 0.12),
                                                             (1.0, 70, "male_elegantsuit01", "short04", 0.15)))]
    c["dignitaries"] = [person("Dig1", 1.0, 64, "male_elegantsuit01", "short04", cval=0.08, hv=0.65, sat=0.0),
                        person("Dig2", 1.0, 58, "male_elegantsuit01", "short01", cval=0.08, hv=0.5, sat=0.0)]
    c["bouquet"] = joinm(sum([carnation((rng.uniform(-0.05, 0.05), rng.uniform(-0.04, 0.04), rng.uniform(0, 0.06)), (0.6, 0.04, 0.05)) for _ in range(5)], []), "Bouquet")
    haze((0, 4, H / 2), (W - 0.5, 14, H - 0.2), density=0.0015, color=(0.9, 0.92, 0.95), anis=0.6)
    animate(c, 0.0, "mourners")
    return c


def animate(c, sec, move):
    if move == "mourners":
        for h in c["dignitaries"]:
            hide(h, True)
        # a slow line of mourners walks up the hall toward the stand; the first lays her flowers
        for k, h in enumerate(c["mourners"]):
            y = STAND.y - 1.3 - k * 1.15 + 0.22 * sec
            x = 0.2 * math.sin(k * 1.7)
            if k == 0:
                stand(h, (0.3, STAND.y - 1.25, 0), math.pi)                                  # faces +Y, the stand
                kneel = ease(min(1.0, max(0.0, (sec - 0.8) / 2.0))) * (1 - ease(min(1.0, max(0.0, (sec - 4.2) / 1.5))))
                nod(h, "spine04", 30 * kneel); nod(h, "spine03", 15 * kneel); nod(h, "head", 18)
                tgt = Vector((0.3, STAND.y - 0.8, 0.9 - 0.75 * kneel))
                hand_to(h, "R", tgt, curl=50)
                bq = c["bouquet"]
                bq.location = tgt + Vector((0, 0.05, 0.02)) if sec < 3.0 else Vector((0.3, STAND.y - 0.75, 0.05))
                bq.rotation_euler = (math.radians(90), 0, 0) if sec < 3.0 else (0, 0, 0)
            else:
                walk_at(h, sec * 0.45 + k * 0.3, (x + 0.3, y, 0), math.pi, stride=10, swing=4)
                nod(h, "head", 12)
    else:
        for h in c["mourners"]:
            hide(h, True)
        for h in c["dignitaries"]:
            hide(h, False)
        c["bouquet"].location = (0.3, STAND.y - 0.75, 0.05)
        for k, h in enumerate(c["dignitaries"]):
            stand(h, (-0.5 + k * 1.0, STAND.y - 1.8, 0), math.pi)
            bow = 10 + 8 * ease(min(1.0, max(0.0, (sec - 1.0) / 2.5)))
            nod(h, "neck01", bow * 0.5); nod(h, "head", bow)
            hand_to(h, "L", h.bone_head("spine02") + fwd(h) * 0.12 + Vector((0.05, 0, -0.1)), curl=40)
            hand_to(h, "R", h.bone_head("spine02") + fwd(h) * 0.12 + Vector((-0.05, 0, -0.1)), curl=40)
    bpy.context.view_layer.update()


def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


MOVES = {
    "mourners": dict(kind="anim", dof=3.2, far=30.0, anim=lambda c, t: animate(c, t * DUR["mourners"], "mourners"),
                     cam=_push((-3.4, STAND.y - 4.0, 1.6), (-3.0, STAND.y - 3.6, 1.55), (0.0, STAND.y - 1.4, 0.9), (0.2, STAND.y - 1.0, 0.8), 30),
                     focus=lambda c, t: Vector((0.3, STAND.y - 1.1, 0.9))),
    "dignitaries": dict(kind="anim", dof=5.6, far=40.0, anim=lambda c, t: animate(c, t * DUR["dignitaries"], "dignitaries"),
                        cam=_push((0.6, -6.0, 1.7), (0.4, -4.6, 1.7), (0.0, STAND.y, 2.2), (0.0, STAND.y, 2.0), 30),
                        focus=lambda c, t: Vector((0.0, STAND.y - 1.8, 1.4))),
}


_build_set = build


def build(variant=None):
    c = _build_set(variant)
    from pbkit import finish_scene
    finish_scene()
    return c
