"""Macro of a generic AI accelerator package (no brand features): silicon die with thin-film sheen, six memory
stacks on an interposer, an organic substrate and hundreds of passives. Real scale (metres)."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.0


def build_package(origin=(0, 0, 0), with_passives=True):
    ox, oy, oz = origin
    sub = box("Substrate", (ox, oy, oz + 0.00075), (0.055, 0.055, 0.0015), pcb("Substrate", (0.006, 0.008, 0.007)), bevel=0.0003)
    inter = box("Interposer", (ox, oy, oz + 0.0018), (0.036, 0.029, 0.0006), pbr("Interposer", (0.012, 0.012, 0.014), 0.25, 0.6), bevel=0.0001)
    die = box("Die", (ox - 0.0035, oy, oz + 0.0025), (0.0265, 0.0205, 0.0008), silicon("Die"), bevel=0.00008)
    hbm_m = silicon("HBM")
    p = hbm_m.node_tree.nodes["Principled BSDF"]; p.inputs['Base Color'].default_value = (0.03, 0.03, 0.035, 1)
    hbm = []
    for sx in (0, 1, 2):
        for sy in (-1, 1):
            hbm.append(box(f"HBM{sx}{sy}", (ox + 0.0128, oy + sy * (0.0052 + sx * 0.0) + (sx - 1) * 0.0, oz + 0.0025), (0.0078, 0.0098, 0.0008), hbm_m, bevel=0.00006))
    # arrange the 6 stacks: 3 rows on the right side of the die
    for k, h in enumerate(hbm):
        col, row = k // 2, k % 2
        h.location = (ox + 0.0122 + 0.0 * col, oy - 0.0105 + col * 0.0105, oz + 0.0025)
        h.location.x += (row - 0.5) * 0.0084
        h.scale = (0.98, 0.98, 1)
    # underfill fillet: a slightly larger, rounded dark rim under the die
    box("Underfill", (ox - 0.0035, oy, oz + 0.0021), (0.0272, 0.0212, 0.0004), pbr("Underfill", (0.05, 0.045, 0.04), 0.6), bevel=0.00015)
    if with_passives:
        cer = pbr("Ceramic", (0.32, 0.25, 0.16), 0.45)
        term = brushed_metal("Term", (0.75, 0.75, 0.76), (0.2, 0.35), 0.0)
        cap = box("Cap", (0, 0, -1), (0.0010, 0.0005, 0.0005), cer, bevel=0.00004)
        endA = box("CapEnd", (0, 0, -1), (0.0002, 0.00052, 0.00052), term, bevel=0.00002)
        r = np.random.default_rng(3)
        k = 0
        for side in range(4):
            for j in range(34):
                u = -0.024 + j * 0.00145
                if side == 0: x, y, rot = u, -0.0235, 0
                elif side == 1: x, y, rot = u, 0.0235, 0
                elif side == 2: x, y, rot = -0.0235, u, math.pi / 2
                else: x, y, rot = 0.0235, u, math.pi / 2
                for ring in (0, 1):
                    off = 0.0016 * ring
                    xx = x + (off if side == 3 else -off if side == 2 else 0); yy = y + (off if side == 1 else -off if side == 0 else 0)
                    instance(cap, (ox + xx, oy + yy, oz + 0.00175), (0, 0, rot))
                    for e in (-1, 1):
                        dx, dy = (0.0004 * e, 0) if rot == 0 else (0, 0.0004 * e)
                        instance(endA, (ox + xx + dx, oy + yy + dy, oz + 0.00175), (0, 0, rot))
                    k += 1
    return dict(die=die, sub=sub, hbm=hbm)


def build(variant=None):
    world_flat((0.004, 0.005, 0.007), 1.0)
    bpy.context.scene.cycles.max_bounces = 10
    pk = build_package()
    # black velvet ground far below for subtle bounce
    box("Ground", (0, 0, -0.002), (0.6, 0.6, 0.002), pbr("Velvet", (0.004, 0.004, 0.005), 0.95))
    key = area_light((-0.08, -0.05, 0.09), (0, 0, 0), 0.03, 0.9, (0.9, 0.95, 1.0)); point_at(key, (0, 0, 0.002))
    key.data.shape = 'RECTANGLE'; key.data.size = 0.12; key.data.size_y = 0.012
    rim = area_light((0.08, 0.1, 0.03), (0, 0, 0), 0.04, 0.6, (0.35, 0.85, 1.0)); point_at(rim, (0, 0, 0.002))
    fill = area_light((0.05, -0.12, 0.05), (0, 0, 0), 0.08, 0.08, (1.0, 0.85, 0.7)); point_at(fill, (0, 0, 0.002))
    cam = bpy.data.objects.get("Cam")
    return dict(key=key, rim=rim, pkg=pk, die_c=Vector((-0.0035, 0, 0.0029)))


def _sweep(ctx, t):
    # a light bar sweeps across the die: the thin film flares through the spectrum
    k = ctx["key"]; x = -0.12 + 0.24 * ease(t)
    k.location = (x, -0.05, 0.08); point_at(k, (x * 0.2, 0, 0.002))


MOVES = {
    "drift_dark": dict(kind="plate", dof=11.0, far=0.4,
                       cam=lambda c, t: ((0.075, -0.06, 0.026), c["die_c"] + Vector((-0.004, 0.002, 0)), 85),
                       focus=lambda c, t: c["die_c"]),
    "sweep_reveal": dict(kind="anim", dof=16.0, far=0.4,
                         cam=lambda c, t: (Vector((0.10, -0.085, 0.055)).lerp(Vector((0.07, -0.06, 0.04)), ease(t)), c["die_c"], 85),
                         focus=lambda c, t: c["die_c"], anim=_sweep),
    "dark_orbit": dict(kind="anim", dof=8.0, far=0.4,
                       cam=lambda c, t: ((0.08 * math.cos(-0.9 + 0.5 * t), 0.08 * math.sin(-0.9 + 0.5 * t), 0.03), c["die_c"], 70),
                       focus=lambda c, t: c["die_c"]),
}
