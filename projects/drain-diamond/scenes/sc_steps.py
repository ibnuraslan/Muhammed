"""STEPS: generic Parisian law-court steps (no exact landmark): a wide flight of pale stone steps up to a colonnade
under a grey February sky; reporters and a few people walking down after the verdict.
  steps (ch4 5B): slow crane down as reporters walk down the wide steps
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import dd
from dd import person, walk_to
from sc_boutique import haussmann

EXPOSURE = 0.6
DUR = {"steps": 9.0}
NST, RISE, RUN = 16, 0.16, 0.42
TOP_Y = NST * RUN


def step_z(y):
    return max(0.0, min(NST * RISE, (y / RUN) * RISE)) if y > 0 else 0.0


def build(variant=None):
    c = {}
    w = world_flat((0.5, 0.53, 0.58), 1.0)
    N = w.node_tree.nodes; L = w.node_tree.links
    lp = N.new("ShaderNodeLightPath"); bg2 = N.new("ShaderNodeBackground"); bg2.inputs['Color'].default_value = (0.36, 0.38, 0.42, 1)
    mx = N.new("ShaderNodeMixShader"); L.new(lp.outputs['Is Camera Ray'], mx.inputs[0]); L.new(N["Background"].outputs[0], mx.inputs[1])
    L.new(bg2.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["World Output"].inputs['Surface'])
    stone = dd.tex_mat("white_sandstone_blocks_02", 0.3, tint=(0.88, 0.86, 0.82), name="CourtStone", sat=0.5)
    stepm = dd.wet(dd.tex_mat("concrete_floor_02", 0.8, tint=(1.08, 1.06, 1.02), name="StepStone", sat=0.3), 0.45, ripples=False)
    B = dd.Builder("Steps")
    for k in range(NST):
        B.box((0, k * RUN + RUN / 2, (k + 1) * RISE / 2), (30, RUN, (k + 1) * RISE), stepm)
    B.box((0, TOP_Y + 4, NST * RISE / 2), (34, 8, NST * RISE), stepm)
    # colonnade and a pediment-free stone front
    for k in range(10):
        B.cyl((-13.5 + k * 3.0, TOP_Y + 2.0, NST * RISE + 5.0), 0.55, 10.0, stone, verts=24)
    B.box((0, TOP_Y + 2.0, NST * RISE + 10.6), (32, 1.6, 1.2), stone)
    B.box((0, TOP_Y + 6.0, NST * RISE + 6.0), (32, 1.0, 12.0), stone)
    for k in range(9):
        B.box((-12.0 + k * 3.0, TOP_Y + 5.45, NST * RISE + 3.0), (1.6, 0.1, 5.0), pbr("TallDoor", (0.05, 0.05, 0.05), 0.5))
    B.box((0, -12, -0.06), (80, 24, 0.1), dd.tex_mat("asphalt_02", 0.35, tint=(0.5, 0.5, 0.52), name="Square", sat=0.4))
    B.done()
    for x in (-15.6, 15.6):
        box("Cheek", (x, TOP_Y / 2, NST * RISE / 2 + 0.3), (1.2, TOP_Y + 0.4, NST * RISE + 0.6), stone)
    haussmann(-60, -20, seed=51, origin=(0, 10, 0)); haussmann(20, 60, seed=52, origin=(0, 10, 0))
    # a TV crew at the foot of the steps: a camera on a tripod, the operator behind it
    T = dd.Builder("TVTripod"); tm = pbr("TripodM", (0.05, 0.05, 0.05), 0.4, 0.7)
    for k in range(3):
        a_ = k * 2 * math.pi / 3
        T.cyl((0.22 * math.cos(a_), 0.22 * math.sin(a_), 0.7), 0.012, 1.45, tm, verts=8,
              rot=(-0.3 * math.sin(a_), 0.3 * math.cos(a_), 0))
    T.box((0, 0.05, 1.5), (0.16, 0.45, 0.22), pbr("TVCam", (0.06, 0.06, 0.065), 0.35, 0.3))
    T.cyl((0, -0.22, 1.52), 0.06, 0.12, pbr("TVLens", (0.01, 0.01, 0.01), 0.15, 0.2), verts=16, rot=(math.radians(90), 0, 0))
    T.done((2.4, -0.6, 0), rot_z=math.radians(160))
    op = person("TVOp", 1.0, 38, "male_casualsuit03", "short01", cval=0.9)
    from human import pose_walk
    dd.zero(op); pose_walk(op, 0.0, stride=0.0, arm_swing=0.0); dd.place(op, (2.6, -1.15, 0), math.radians(160)); dd.arms_relaxed(op)
    c["op"] = op
    rng = np.random.default_rng(3)
    c["people"] = []
    looks = [("male_elegantsuit01", 2.4, (0.72, 0.58, 0.42)), ("male_casualsuit05", 1.2, (1, 1, 1)), ("female_elegantsuit01", 1.9, (0.3, 0.32, 0.42)),
             ("male_elegantsuit01", 1.8, (0.45, 0.47, 0.5)), ("male_casualsuit03", 1.1, (1, 1, 1)), ("female_elegantsuit01", 2.2, (0.7, 0.3, 0.25)),
             ("male_casualsuit01", 1.2, (1, 1, 1))]
    props = ["camera", "mic", None, "camera", "mic", None, "camera"]
    for k in range(7):
        cl, v, tn = looks[k]; g = 0.0 if cl.startswith("female") else 1.0
        h = person(f"Rep{k}", g, int(rng.integers(26, 60)), cl, ("short02", "short04", "bob01", "short01", "short03", "ponytail01", "short02")[k],
                   cval=v, tint=tn, sat=0.3)
        x = -5.0 + k * 1.6 + float(rng.uniform(-0.5, 0.5))
        y0 = TOP_Y + 0.4 + float(rng.uniform(0, 1.8))
        prop = None
        if props[k] == "camera":
            prop = dd.model_h("Camera_01", (0, 0, 0), 0.16)
        elif props[k] == "mic":
            prop = cyl(f"RepMic{k}", (0, 0, 0), 0.012, 0.2, pbr("RepMicM", (0.03, 0.03, 0.03), 0.4), verts=10)
        c["people"].append((h, Vector((x, y0, 0)), float(rng.uniform(0, 2.0)), prop, float(rng.uniform(-0.6, 0.6))))
    # LOOK: grade only (the person's pick, "more soul"): the set keeps its own grey-sky light, no relight
    return c


def anim_steps(c, t):
    sec = t * DUR["steps"]
    for h, start, delay, prop, drift in c["people"]:
        end = Vector((start.x + drift * 3.0, -3.0, 0))
        walk_to(h, start, end, max(0.0, sec - delay), speed=0.7, cadence=1.5)
        dd.ground(h, step_z(h.arm.location.y))
        if prop is not None:
            prop.location = h.bone_tail("lowerarm02.R") - Vector((0, 0, 0.08)); prop.rotation_euler = (0, 0, h.arm.rotation_euler.z)


MOVES = {"steps": dict(kind="anim", dof=8.0, anim=anim_steps,
                       cam=lambda c, t: (Vector((4.6, -3.6, 1.55)).lerp(Vector((4.0, -3.1, 1.5)), ease(t)), Vector((-0.6, 4.0, 2.5)), 35),
                       focus=lambda c, t: Vector((-0.3, 3.0, 1.2)))}
