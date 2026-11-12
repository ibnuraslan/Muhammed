"""CH3 (chat B): a 1981 television repair workshop at dusk. Low amber sun rakes through a grimy side window,
haze, CRT sets glowing on a shelf, an oscilloscope trace moving. A generic man (unnamed, seen from behind)
works at the soldering bench. No act of any crime is shown.
  solder  (A): slow push from behind the man at the bench; smoke curls from the iron, screens flicker
  letters (B): slow push past a pile of unopened final-notice envelopes, the man soft behind
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

EXPOSURE = -0.3
DUR = {"solder": 5.5, "letters": 5.0}
VARIANT_FOR = {"letters": "away"}
BENCH_Y = 2.15
TOP = 0.83


def tv(loc, rot_z, seed, base):
    r, ms = ph.model("Television_01", loc=loc, rot_z=rot_z)
    # glowing tube just in front of the (dark) screen glass of the scanned set
    M = r.matrix_world
    scr = B.sheet("CRT", (0, 0, 0), (0.37, 0.27), B.crt_material(f"CRT{seed}", base=base, strength=1.3, seed=seed),
                  rot=(math.radians(90), 0, 0))
    scr.parent = r; scr.location = (-0.065, -0.214, 0.272)
    return r


def scope(loc, rot_z, steel):
    body = box("ScopeBody", (0, 0, 0.11), (0.34, 0.38, 0.22), pbr("ScopeGrey", (0.18, 0.19, 0.2), 0.45), bevel=0.01)
    bez = box("ScopeBezel", (-0.06, -0.192, 0.12), (0.16, 0.01, 0.13), pbr("ScopeBlack", (0.01, 0.01, 0.01), 0.4))
    scr = B.sheet("ScopeScreen", (-0.06, -0.198, 0.12), (0.13, 0.1), B.scope_material("Scope"), rot=(math.radians(90), 0, 0))
    knobs = [cyl("Knob", (0.06 + 0.045 * (k % 2), -0.2, 0.06 + 0.05 * (k // 2)), 0.013, 0.02, steel, verts=16, rot=(math.radians(90), 0, 0)) for k in range(6)]
    o = join([body, bez] + knobs, "Scope")
    o.location = loc; o.rotation_euler = (0, 0, rot_z)
    scr.parent = o
    return o


def build(variant=None):
    c = {}
    rng = np.random.default_rng(81)
    world_flat((0.012, 0.014, 0.018), 1.0)
    # ------------------------------------------------------------------ room
    floor = B.tex_mat("ShopFloor", "concrete_floor_worn_001", scale=0.6, tint=(0.55, 0.52, 0.48))
    box("Floor", (0, 0, -0.01), (7, 7, 0.02), floor)
    wall = B.plaster("ShopWall", (0.38, 0.36, 0.31), dirt=0.35)
    box("WallBack", (0, 2.65, 1.5), (7, 0.1, 3.0), wall)
    box("WallR", (3.05, 0, 1.5), (0.1, 7, 3.0), wall)
    box("WallFront", (0, -3.3, 1.5), (7, 0.1, 3.0), wall)
    box("Ceiling", (0, 0, 2.85), (7, 7, 0.05), B.plaster("ShopCeil", (0.3, 0.29, 0.26)))
    # left wall with one grimy window: the dusk key comes through it
    box("WallL_lo", (-3.05, 0, 0.5), (0.1, 7, 1.0), wall); box("WallL_hi", (-3.05, 0, 2.55), (0.1, 7, 0.7), wall)
    box("WallL_a", (-3.05, -2.0, 1.55), (0.1, 3.0, 1.1), wall); box("WallL_b", (-3.05, 2.4, 1.55), (0.1, 1.0, 1.1), wall)
    frame = pbr("WinFrame", (0.22, 0.2, 0.17), 0.6)
    for y in (-0.5, 0.35, 1.2, 1.9):
        box("Mullion", (-3.05, y, 1.55), (0.08, 0.05, 1.1), frame)
    box("Transom", (-3.05, 0.7, 1.55), (0.08, 2.4, 0.05), frame)
    wg = box("WinGlass", (-3.04, 0.7, 1.55), (0.01, 2.4, 1.1), glass("Grimy", (0.75, 0.72, 0.62), 0.25)); wg.visible_shadow = False
    # exterior: dusk sky glow behind the window
    sky = box("DuskSky", (-6.5, 0.7, 1.8), (0.05, 12, 6), emissive("DuskGlow", (1.0, 0.55, 0.3), 1.2))
    sky.visible_shadow = False
    B.key_sun(11, 180 + 14, 14.0, color=(1.0, 0.62, 0.34), angle=1.5)        # low sun from -X, through the window
    B.fill((2.5, -2.5, 2.4), (0, 1.5, 1.0), 60, 2.5, (0.45, 0.6, 0.8))     # cold faint negative-side fill
    B.room_haze((0, 0, 1.4), (6.0, 6.0, 2.8), density=0.012, color=(0.95, 0.9, 0.85))
    # ------------------------------------------------------------------ the bench
    ph.model("WoodenTable_03", loc=(-0.35, BENCH_Y, 0), rot_z=0)
    ph.model("wooden_table_02", loc=(1.05, BENCH_Y - 0.03, 0), rot_z=0)
    pegboard = pbr("Pegboard", (0.42, 0.34, 0.24), 0.8)
    box("Pegboard", (0.3, 2.58, 1.12), (2.8, 0.03, 0.5), pegboard)
    shelf_w = wood("ShelfWood", (0.12, 0.07, 0.04), (0.25, 0.15, 0.08), scale=(0.3, 6, 6), rough=0.6, coat=0.0)
    box("Shelf", (0.3, 2.4, 1.43), (3.0, 0.42, 0.04), shelf_w)
    steel = pbr("Steel", (0.5, 0.5, 0.52), 0.35, 1.0)
    for x in (-1.1, 0.3, 1.7):
        box("Bracket", (x, 2.5, 1.35), (0.03, 0.3, 0.12), steel)
    # CRT sets glowing on the shelf (repairs waiting) and one on the bench end
    c["tvs"] = [tv((-0.95, 2.38, 1.45), 0.05, 0.3, (0.45, 0.55, 0.62)),
                tv((0.3, 2.4, 1.45), -0.04, 1.7, (0.5, 0.48, 0.42)),
                tv((1.35, 2.38, 1.45), 0.08, 3.1, (0.36, 0.46, 0.56)),
                tv((-2.4, 1.0, 0.65), math.pi / 2, 5.2, (0.42, 0.5, 0.6))]
    ph.model("Television_01", loc=(2.55, 1.6, 0.0), rot_z=math.radians(-70))          # an old set on the floor
    ph.model("Television_01", loc=(2.6, 1.6, 0.46), rot_z=math.radians(-80))
    scope((-1.25, BENCH_Y + 0.02, TOP), 0.25, steel)
    ph.model("circuit_board", loc=(-0.25, BENCH_Y - 0.1, TOP + 0.005), rot_z=0.1)
    ph.model("retro_multimeter", loc=(0.35, BENCH_Y + 0.05, TOP), rot_z=-0.3)
    lamp_r, _ = ph.model("desk_lamp_arm_01", loc=(-0.85, BENCH_Y + 0.12, TOP), rot_z=math.radians(-25))
    B.key_spot((-0.6, BENCH_Y - 0.05, 1.45), (-0.25, BENCH_Y - 0.1, TOP), 220, 70, (1.0, 0.75, 0.48), soft=0.05, name="LampBulb")
    ph.model("metal_toolbox", loc=(0.75, BENCH_Y + 0.12, TOP), rot_z=0.2)
    ph.model("screwdrivers_02", loc=(0.15, BENCH_Y - 0.12, TOP), rot_z=1.2)
    ph.model("vintage_radio_transceiver", loc=(-2.3, 2.2, 0.0), rot_z=0.3)
    ph.model("metal_tool_chest", loc=(-2.4, 1.0, 0.0), rot_z=math.radians(90))
    # the soldering iron (held over the board) with a thin curl of rosin smoke
    iron_m = pbr("IronGrip", (0.05, 0.05, 0.05), 0.5)
    iron = join([cyl("IronGripC", (0, 0, 0), 0.012, 0.12, iron_m, verts=16, rot=(0, math.radians(90), 0)),
                 cyl("IronShaft", (0.1, 0, 0), 0.004, 0.09, steel, verts=12, rot=(0, math.radians(90), 0))], "Iron")
    c["iron"] = iron
    c["smoke"] = B.smoke((-0.2, BENCH_Y - 0.12, TOP + 0.02), density=0.6, size=(0.25, 0.25, 0.9))
    # ------------------------------------------------------------------ the debt letters on the right end
    env = [B.stamp_mat(f"Env{k}", base=(0.86 - 0.04 * k, 0.83 - 0.04 * k, 0.75 - 0.05 * k)) for k in range(3)] + [B.paper_mat("EnvPlain", (0.8, 0.78, 0.7), lines=False)]
    c["letters"] = B.envelope_pile((-0.62, BENCH_Y + 0.0, TOP + 0.002), 22, rng, env, spread=0.08)
    # ------------------------------------------------------------------ the man, standing at the bench, back to camera
    h = B.mazurek("Repairman", 1981)
    if variant == "away":                                   # B: he has stepped to the far end, looking at a set on the shelf
        B.stand(h, (1.3, BENCH_Y - 0.75, 0), math.pi + 0.15)
        c["iron"].location = (-0.3, BENCH_Y - 0.12, TOP + 0.012); c["iron"].rotation_euler = (0, 0, 0.6)
        c["smoke"].location = (-0.2, BENCH_Y - 0.08, TOP + 0.47)
    else:
        B.stand(h, (-0.2, BENCH_Y - 0.62, 0), math.pi)      # facing +Y, the bench
    c["man"] = h
    c["variant"] = variant
    B.finish_interior(lift=-0.1)
    return c


def pose_man(c, sec):
    h = c["man"]; fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    B.nod(h, 9, "spine03"); B.nod(h, 7, "spine02"); B.nod(h, 10, "neck01"); B.nod(h, 16)
    bpy.context.view_layer.update()
    board = Vector((-0.22, BENCH_Y - 0.12, TOP + 0.08))
    tip = board + Vector((0.03 * math.sin(sec * 0.9), 0.02 * math.sin(sec * 0.6), 0.012 * abs(math.sin(sec * 1.7))))
    # right hand holds the iron over the board, left steadies the board
    reach(h, "R", tip + Vector((0.12, -0.12, 0.06)), Vector((0.6, -0.2, -0.6)), Vector((-0.6, 0.6, -0.4)))
    reach(h, "L", board + Vector((-0.14, -0.08, 0.03)), Vector((-0.6, -0.2, -0.6)), Vector((0.2, 0.8, -0.5)))
    fingers_curl(h, 40, thumb=20)
    h.rot("head", (0, 0, 1), 4 * math.sin(sec * 0.4))
    bpy.context.view_layer.update()
    w = h.bone_tail("wrist.R") if "wrist.R" in h.arm.pose.bones else h.bone_tail("lowerarm02.R")
    ir = c["iron"]; d = (tip - w); ir.location = w
    ir.rotation_mode = 'QUATERNION'; ir.rotation_quaternion = d.to_track_quat('X', 'Z')


def anim(c, t, dur):
    if c.get("variant") == "away":
        h = c["man"]; sec = t * dur
        B.arms_down(h)
        B.nod(h, 8); h.rot("head", (0, 0, 1), 6 * math.sin(sec * 0.5))
        h.rot("spine03", (0, 1, 0), 2 * math.sin(sec * 0.4))
        bpy.context.view_layer.update()
        return
    pose_man(c, t * dur)


def cam_solder(c, t):
    e = ease(t)
    return (Vector((0.8, -1.25, 1.62)).lerp(Vector((0.6, -0.55, 1.56)), e), Vector((-0.2, BENCH_Y, 1.25)), 30)


def cam_letters(c, t):
    e = ease(t)
    return (Vector((-1.55, 1.3, 1.38)).lerp(Vector((-1.35, 1.45, 1.3)), e), Vector((-0.35, BENCH_Y - 0.08, 0.9)), 35)


MOVES = {
    "solder": dict(kind="anim", dof=2.8, cam=cam_solder, anim=lambda c, t: anim(c, t, DUR["solder"]),
                   focus=lambda c, t: c["man"].bone_head("head")),
    "letters": dict(kind="anim", dof=2.0, cam=cam_letters, anim=lambda c, t: anim(c, t, DUR["letters"]),
                    focus=lambda c, t: Vector((-0.62, BENCH_Y, TOP))),
}
