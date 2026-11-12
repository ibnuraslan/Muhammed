"""Look test: a woodland path (Radio Jingle: lakeside path and forest). Scanned Poly Haven trees, ferns, shrubs and
stumps scattered either side of a dirt path; the camera walks slowly up the path towards a low sun behind the trees.
Plain build: the old bright house daylight. With the house look: look.forest() (mist or low sun, shafts, dark floor).
  python run.py forest path_push --still --pct 40 --samples 16      (variant via VARIANT_FOR: mist)
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import look
import ph

EXPOSURE = -1.0
VARIANT_FOR = {"path_push": "mist", "path_sun": "low_sun"}
AZIM = 165              # the sun sits up the path, behind the trees (backlight: shafts towards camera)


def _template(aid, height=None, scale=1.0):
    """Import once into a hidden collection; returns (collection, natural height)."""
    root, ms = ph.model(aid, res="1k", scale=scale)
    lo, hi = ph.bounds(ms)
    col = bpy.data.collections.new("T_" + aid)
    objs = [root] + [o for o in bpy.data.objects if o.parent is not None and _under(o, root)]
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    root.location.z = -lo.z
    return col, hi.z - lo.z


def _under(o, root):
    while o.parent is not None:
        if o.parent == root:
            return True
        o = o.parent
    return False


def _place(col, loc, rz, s):
    e = bpy.data.objects.new(col.name + "_i", None); e.instance_type = 'COLLECTION'; e.instance_collection = col
    bpy.context.collection.objects.link(e); e.location = loc; e.rotation_euler = (0, 0, rz); e.scale = (s, s, s)
    return e


def build(variant=None):
    mood = variant or "mist"
    # the old house daylight (the 'before'); look.forest replaces sky and sun when the look is on
    world_sky(sun_elev_deg=35, sun_rot_deg=AZIM, strength=0.5, tint=(0.95, 0.97, 1.0))
    sun(35, AZIM, energy=3.0, color=(1.0, 0.96, 0.9), angle_deg=1.0)
    rng = np.random.default_rng(11)
    floor = ph.texture("forest_floor", scale=0.25, res="1k")
    box("Ground", (0, 10, -0.05), (120, 120, 0.1), floor)
    path = ph.texture("brown_mud_leaves_01", scale=0.4, res="1k")
    bm = bpy.data.meshes.new("Path")      # a gently winding dirt path up the middle
    vs, fs = [], []
    for k in range(60):
        y = -30 + k * 1.2; x = 0.8 * math.sin(y * 0.08)
        vs += [(x - 1.1, y, 0.005), (x + 1.1, y, 0.005)]
        if k:
            i = 2 * k; fs.append((i - 2, i - 1, i + 1, i))
    bm.from_pydata(vs, [], fs); po = bpy.data.objects.new("Path", bm); bpy.context.collection.objects.link(po)
    po.data.materials.append(path)
    trees = [_template("island_tree_02"), _template("island_tree_01"), _template("tree_small_02")]
    under = [_template("fern_02"), _template("shrub_02"), _template("tree_stump_01"), _template("dead_tree_trunk")]
    placed = 0
    while placed < 40:
        x, y = rng.uniform(-30, 30), rng.uniform(-24, 45)
        if abs(x - 0.8 * math.sin(y * 0.08)) < 3.0:
            continue
        col, h = trees[rng.integers(0, len(trees))]
        _place(col, (x, y, 0), rng.uniform(0, 6.28), rng.uniform(11, 16) / max(h, 0.1))
        placed += 1
    for k in range(140):
        x, y = rng.uniform(-18, 18), rng.uniform(-26, 30)
        if abs(x - 0.8 * math.sin(y * 0.08)) < 1.5:
            continue
        col, h = under[rng.integers(0, len(under))]
        target = 0.8 if col.name.endswith(("fern_02", "shrub_02")) else 0.6
        _place(col, (x, y, 0), rng.uniform(0, 6.28), rng.uniform(0.7, 1.4) * target / max(h, 0.05))
    look.forest(mood=mood, azim=AZIM, area=((0, 10), (70, 80)), canopy=16.0)
    return dict(path=Vector((0, 10, 1.2)))


def cam_path(c, t):
    y = -22 + 3.0 * ease(t)
    return (Vector((0.6, y, 1.65)), Vector((0.2, y + 20, 2.6)), 32)


MOVES = {
    "path_push": dict(kind="anim", dof=8.0, far=80.0, cam=cam_path, focus=lambda c, t: Vector((0.2, -8, 1.5))),
    "path_sun": dict(kind="anim", dof=8.0, far=80.0, cam=cam_path, focus=lambda c, t: Vector((0.2, -8, 1.5))),
}
