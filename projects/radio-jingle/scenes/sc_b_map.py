"""Chat B storyboard v2: a real printed map of West Germany on an incident-room desk (Natural Earth outlines),
lit by a desk lamp. Facts are physical: push pins, red thread.
  tips   3-10B  "The tips keep coming": red pins land city by city across the country, faster and faster
  north  4-3A   "moved to northern Germany": red thread runs from a pin in Bavaria up to a pin on the north coast
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import ease, world_flat
import b_common as B
import b_fx as F

EXPOSURE = 0.2
DUR = {"tips": 6.0, "north": 6.0}
VARIANT_FOR = {"tips": "tips", "north": "north"}
DZ = 0.76


def _inside(lon, lat, im, box):
    lon0, lon1, lat0, lat1 = box
    W, H = im.size
    x = int((lon - lon0) / (lon1 - lon0) * W); y = int((lat1 - lat) / (lat1 - lat0) * H)
    if not (0 <= x < W and 0 <= y < H):
        return False
    r, g, b = im.getpixel((x, y))[:3]
    return r > 232 and g > 222 and b < 220 and b > 195                 # the cream land of West Germany


def build(variant=None):
    variant = variant or "tips"
    c = {"variant": variant}
    rng = np.random.default_rng(81)
    world_flat((0.004, 0.004, 0.005), 1.0)
    box("Floor", (0, 0, -0.01), (8, 8, 0.02), pbr("RoomFloor", (0.06, 0.05, 0.045), 0.7))
    geo = F.map_on_desk(c, origin=(0, 0, DZ), width=0.62)
    # desk clutter at the edges: case folders, an ashtray, a pencil, slips of paper
    box("Folder1", (0.52, 0.28, DZ + 0.006), (0.24, 0.33, 0.012), pbr("Manila", (0.62, 0.5, 0.3), 0.8), rot=(0, 0, 0.2))
    box("Folder2", (0.5, 0.25, DZ + 0.019), (0.24, 0.33, 0.012), pbr("RedFile", (0.4, 0.08, 0.06), 0.7), rot=(0, 0, 0.12))
    cyl("Ashtray", (-0.52, 0.32, DZ + 0.012), 0.06, 0.024, pbr("Glass", (0.25, 0.28, 0.27), 0.1, **{'Transmission Weight': 0.6}), verts=24)
    cyl("Pencil", (0.42, -0.3, DZ + 0.004), 0.004, 0.17, pbr("PencilY", (0.75, 0.6, 0.15), 0.5), verts=6, rot=(0, math.radians(90), 0.6))
    for k in range(6):
        F.card_plane(f"Slip{k}", (-0.55 + rng.uniform(-0.06, 0.06), -0.25 + k * 0.05, DZ + 0.002 + k * 0.0006), 0.1, 0.14,
                     B.paper_mat(f"SlipM{k}", (0.9, 0.88, 0.78)), rot_z=rng.uniform(-0.4, 0.4))
    # desk lamp: a warm key raking across the paper from the top-left, the rest of the room dark
    try:
        import ph
        ph.model("desk_lamp_arm_01", loc=(-0.6, 0.55, DZ), rot_z=math.radians(-40))
    except Exception as e:
        print("[map] lamp", e)
    B.key_spot((-0.45, 0.45, DZ + 0.75), (0.0, -0.05, DZ), 38, 75, (1.0, 0.8, 0.55), soft=0.15, name="DeskLamp")
    B.fill((1.2, -1.4, 1.8), (0, 0, DZ), 12, 2.0, (0.55, 0.62, 0.8))
    if variant == "tips":
        from PIL import Image
        im = Image.open(F.map_png()).convert("RGB"); box_ = F.MAP_BOX
        cities = list(F.CITIES.values())
        pts = []
        while len(pts) < 70:
            if rng.random() < 0.55:
                lo, la = cities[rng.integers(len(cities))]; lo += rng.normal(0, 0.15); la += rng.normal(0, 0.12)
            else:
                lo, la = rng.uniform(5.8, 13.8), rng.uniform(47.3, 55.0)
            if _inside(lo, la, im, box_):
                pts.append((lo, la))
        c["pins"] = [F.push_pin(f"Pin{k}", geo(lo, la)) for k, (lo, la) in enumerate(pts)]
        n = len(c["pins"])
        c["t_in"] = [1.0 + 4.6 * (k / n) ** 0.6 for k in range(n)]        # accelerating arrivals
        for p in c["pins"]:
            p["home"] = tuple(p.location)
    else:
        a = geo(11.1, 48.0); b = geo(9.93, 54.66)
        c["pa"], c["pb"] = F.push_pin("PinSouth", a), F.push_pin("PinNorth", b)
        mid = (a + b) / 2
        pts = [a + Vector((0, 0, 0.022))]
        for i in range(1, 30):                                              # a thread, loosely following the land
            u = i / 30
            p = a.lerp(b, u) + Vector((0.025 * math.sin(u * math.pi * 1.5), 0, 0.022 + 0.004 * math.sin(u * math.pi)))
            pts.append(p)
        pts.append(b + Vector((0, 0, 0.022)))
        c["thread"] = F.curve("Thread", pts, pbr("ThreadRed", (0.55, 0.05, 0.035), 0.7), bevel=0.0012, smooth=True)
        F.draw(c["thread"], 0.0)
    B.finish_interior(lift=0.0, faces=0)
    return c


def anim(c, t, move):
    sec = t * DUR[move]
    if move == "tips":
        for p, t0 in zip(c["pins"], c["t_in"]):
            u = (sec - t0) / 0.18
            h = Vector(p["home"])
            if u <= 0:
                p.hide_render = True
            else:
                p.hide_render = False
                p.location = h + Vector((0, 0, 0.05 * (1 - ease(min(1.0, u)))))      # pressed into the paper
    else:
        for p, t0 in ((c["pa"], 0.3), (c["pb"], 4.3)):
            p.hide_render = sec < t0
        F.draw(c["thread"], ease(min(1.0, max(0.0, (sec - 0.8) / 3.6))))
    bpy.context.view_layer.update()


def cam_tips(c, t):
    e = ease(t)
    return (Vector((0.08, -0.62 + 0.18 * e, DZ + 0.78 - 0.12 * e)), Vector((0.0, 0.0 + 0.03 * e, DZ)), 32)


def cam_north(c, t):
    e = ease(t)
    a = c["geo"](11.1, 48.0); b = c["geo"](9.93, 54.66)
    tgt = a.lerp(b, 0.15 + 0.7 * e)
    return (tgt + Vector((0.12, -0.42, 0.42)), tgt, 40)


MOVES = {
    "tips": dict(kind="anim", dof=5.6, cam=cam_tips, anim=lambda c, t: anim(c, t, "tips"), focus=lambda c, t: Vector((0, 0.0, DZ))),
    "north": dict(kind="anim", dof=4.0, cam=cam_north, anim=lambda c, t: anim(c, t, "north"),
                  focus=lambda c, t: c["geo"](11.1, 48.0).lerp(c["geo"](9.93, 54.66), 0.15 + 0.7 * ease(t))),
}
