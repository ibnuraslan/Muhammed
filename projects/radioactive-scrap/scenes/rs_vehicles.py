"""Adapters from the shared realistic vehicle kit (nvidia_doc/scenes/vehicles.py) to this film's animation code.

  truck(name, col)          -> (root, wheels, bed_z, (x0, x1))   flatbed_truck_1990s, deck at bed_z, bed from x0 to x1
  roll(root, distance)      spin the kit wheels for a distance travelled
  excavator(name, tool)     -> rig dict (base/swing/boom/stick/tool parts) for arm_ik / pose_arm / set_grab below
  arm_ik(rig, target)       swing the house and solve boom + stick so the tool pivot reaches a world point
  boom_truck(name)          -> dict for the detector-boom truck and the drum crane (turret, boom, ext, hook)
"""
import math
import bpy
from mathutils import Vector
import vehicles as V

BED_Z, BED_X0, BED_X1 = 1.25, -3.65, 1.62


def truck(name="Truck", col=(0.14, 0.24, 0.36), dirt=0.45, bed_len=None):
    r = V.make("flatbed_truck_1990s", color=col, dirt=dirt); r.name = name
    return r, V.wheels(r), BED_Z, (BED_X0, BED_X1)


def van(name="Van", col=(0.78, 0.78, 0.76)):
    r = V.make("van_1990s", color=col, dirt=0.25); r.name = name
    return r, V.wheels(r)


def car(name, col, kind="sedan_1990s_soviet"):
    r = V.make(kind, color=col, dirt=0.2); r.name = name
    return r


def roll(root, distance):
    V.spin_wheels(root, distance)


# ---------------------------------------------------------------------------- excavator / grab crane
def excavator(name="Excavator", col=None, tool="bucket"):
    kind = "excavator" if tool == "bucket" else "grab_crane"
    root = V.make(kind, color=col, dirt=0.55); root.name = name
    rig = dict(base=root, swing=V.part(root, "house"), boom=V.part(root, "boom"), stick=V.part(root, "stick"),
               tool=V.part(root, "bucket") or V.part(root, "grab"), kind=kind)
    # link lengths and rest angles in the arm plane (x forward, z up), from the parts' pivots
    u = Vector(rig["stick"].location); w = Vector(rig["tool"].location)
    rig["a"] = math.hypot(u.x, u.z); rig["a0"] = math.atan2(u.z, u.x)
    rig["b"] = math.hypot(w.x, w.z); rig["b0"] = math.atan2(w.z, w.x)
    return rig


def pose_arm(rig, swing, boom, stick, tool):
    """Radians, same sense as before: boom > 0 raises, stick > 0 curls in, swing about Z."""
    rig["swing"].rotation_euler[2] = swing
    rig["boom"].rotation_euler[1] = -boom
    rig["stick"].rotation_euler[1] = stick
    if rig["kind"] == "excavator":
        rig["tool"].rotation_euler[1] = tool
    hang_tool_level(rig)


def hang_tool_level(rig):
    if rig["kind"] != "excavator":
        rig["tool"].rotation_euler[1] = -(rig["boom"].rotation_euler[1] + rig["stick"].rotation_euler[1])


def set_grab(rig, openness):
    V.set_grab(rig["base"], openness)


def arm_ik(rig, target, elbow_up=True):
    bpy.context.view_layer.update()
    base = rig["base"].matrix_world
    tl = base.inverted() @ Vector(target)
    rig["swing"].rotation_euler[2] = math.atan2(tl.y, tl.x)
    bpy.context.view_layer.update()
    hm = rig["swing"].matrix_world
    P0 = rig["boom"].matrix_world.translation
    rel = hm.inverted().to_3x3() @ (Vector(target) - P0)
    d, h = max(0.3, rel.x), rel.z
    a, b = rig["a"], rig["b"]
    D = min(a + b - 1e-3, max(abs(a - b) + 1e-3, math.hypot(d, h)))
    ca = max(-1.0, min(1.0, (a * a + D * D - b * b) / (2 * a * D)))
    e1 = math.atan2(h, d) + math.acos(ca)
    e2 = math.atan2(h - a * math.sin(e1), d - a * math.cos(e1))
    th_b = rig["a0"] - e1                 # rotation about Y lowers +X by th
    th_s = rig["b0"] - th_b - e2
    rig["boom"].rotation_euler[1] = th_b
    rig["stick"].rotation_euler[1] = th_s
    hang_tool_level(rig)
    bpy.context.view_layer.update()


def tool_point(rig):
    bpy.context.view_layer.update()
    return rig["tool"].matrix_world.translation.copy()


# ---------------------------------------------------------------------------- boom trucks
def boom_truck(name="BoomTruck", col=(0.55, 0.57, 0.55)):
    root = V.make("boom_truck", color=col, dirt=0.35); root.name = name
    return dict(body=root, turret=V.part(root, "turret"), boom=V.part(root, "boom"), ext=V.part(root, "boom_ext"),
                ext2=V.part(root, "boom_ext2"), hook=V.part(root, "hook"), wheels=V.wheels(root),
                ext0=V.part(root, "boom_ext").location.x, ext20=V.part(root, "boom_ext2").location.x)


def boom_pose(bt, slew, luff, ext):
    """slew (rad, turret about Z, 0 = over the cab), luff (rad up), ext 0..1 telescoping."""
    bt["turret"].rotation_euler[2] = math.pi + slew
    bt["boom"].rotation_euler[1] = -luff
    bt["ext"].location.x = bt["ext0"] + 2.4 * ext
    bt["ext2"].location.x = bt["ext20"] + 2.2 * ext
    bpy.context.view_layer.update()


def boom_tip(bt):
    bpy.context.view_layer.update()
    return bt["hook"].matrix_world.translation.copy()


def aim_boom(bt, target_xy, height, ext=1.0):
    """Slew + luff so the boom tip sits above target_xy at roughly `height` (tip z)."""
    boom_pose(bt, 0.0, 0.0, ext)
    piv = bt["boom"].matrix_world.translation
    tgt = Vector((target_xy[0], target_xy[1], 0))
    d = tgt - Vector((piv.x, piv.y, 0))
    body_rz = bt["body"].rotation_euler.z
    # turret 0 points toward local -X (rear) once rotated by pi; find slew giving that direction
    slew = math.atan2(d.y, d.x) - body_rz
    boom_pose(bt, slew, 0.0, ext)
    tip = boom_tip(bt); L = (Vector((tip.x, tip.y, tip.z)) - piv).length
    horiz = d.length
    luff = math.acos(max(-1.0, min(1.0, horiz / max(L, 0.1))))
    boom_pose(bt, slew, luff, ext)
    tip = boom_tip(bt)
    if (Vector((tip.x, tip.y, 0)) - tgt).length > 1.0:          # wrong side: turn the other way
        boom_pose(bt, slew + math.pi, luff, ext)
    return boom_tip(bt)
