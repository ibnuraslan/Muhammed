"""THE MECHANISM (Chapter Three's showpiece). The hero typewriter on a dark lab bench under a work lamp. No hands:
the keys go down by themselves and we watch the machine.

Ch3 1A  strike   a key goes down; the ball tilts, turns and strikes the ribbon (chapter title over it)
Ch3 1B  platen   low along the platen: the carrier steps and crisp letters appear on the page
Ch3 2A  sink     the camera sinks from the ball down into the mechanism as the housing goes clear
Ch3 2B  arms     the six selection arms rise and fall in patterns as the keys are struck
Ch3 3A  magnets  close on the arm tips: small dark magnets pass over the long bar (altered machine)
Ch3 3B  xray     one continuous shot: the housing fades to X-ray clear, the bar's hidden circuit beneath the arms
Ch3 8A  space    the space bar drops; the carrier steps but the ball does not move
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import typewriter as T

EXPOSURE = 0.2
DUR = {"coil": 4.0, "strike": 6.0, "platen": 5.0, "sink": 6.0, "arms": 5.0, "magnets": 5.0, "xray": 6.0, "space": 4.5}
TEXT = "the quick brown fox jumps over the lazy dog\nnow is the time for all good men to come"
SPACE_TEXT = "now is the time"
FPS = 24


def build(variant=None):
    c = {}
    world_flat((0.006, 0.007, 0.009), 1.0)
    top = ph.texture("oak_veneer_01", scale=1.0, name="MacroBench", tint=(0.7, 0.66, 0.6))
    box("Bench", (0, 0, -0.025), (1.6, 0.9, 0.05), top)
    box("BackWall", (0, 0.8, 0.6), (3, 0.05, 1.6), ph.texture("painted_plaster_wall", scale=0.6, name="MacroWall", tint=(0.4, 0.42, 0.42)))
    ph.model("retro_multimeter", loc=(0.45, 0.25, 0.0), rot_z=math.pi + 0.3)
    ph.model("screwdriver", loc=(-0.35, -0.25, 0.0), rot_z=0.4)
    ph.model("circuit_board", loc=(0.4, -0.2, 0.0), rot_z=-0.3)
    r, ms = ph.model("desk_lamp_arm_01", loc=(-0.5, 0.25, 0.0), rot_z=math.radians(-40)); twp.tint_model(ms, (0.2, 0.22, 0.2), 0.1)
    key = bpy.data.lights.new("Key", 'AREA'); key.energy = 3.5; key.size = 0.35; key.color = (1.0, 0.86, 0.68)
    ko = bpy.data.objects.new("Key", key); bpy.context.collection.objects.link(ko); ko.location = (-0.35, -0.2, 0.55); point_at(ko, (0, 0, 0.1))
    rim = bpy.data.lights.new("Rim", 'AREA'); rim.energy = 2.5; rim.size = 0.5; rim.color = (0.6, 0.75, 1.0)
    ro = bpy.data.objects.new("Rim", rim); bpy.context.collection.objects.link(ro); ro.location = (0.45, 0.45, 0.4); point_at(ro, (0, 0, 0.1))
    fill = area_light((0.3, -0.7, 0.3), (0, 0, 0), 0.8, 1.5, (0.85, 0.9, 1.0)); point_at(fill, (0, 0, 0.1)); fill.visible_camera = False
    tw = T.make("Hero", loc=(0, 0, 0), color=(0.17, 0.22, 0.28), bugged=True, text=TEXT, dpi=400, seed=5)
    c["tw"] = tw
    # the X-ray fade (only the shots that call for it switch it on via their expression)
    c["fade_expr"] = {"sink": "1", "coil": "1", "xray": "min(1, max(0, (frame - 24) / 72))", "arms": "0.93", "magnets": "1"}
    return c


def fade(c, shot):
    if shot in c["fade_expr"] and not c.get("_faded"):
        T.xray_shell(c["tw"], c["fade_expr"][shot])
        c["_faded"] = True


def anim(shot):
    def f(c, t):
        fade(c, shot)
        sec = t * DUR[shot]
        if shot == "space":
            T.type_at(c["tw"], sec, text=SPACE_TEXT, start=-0.9, cps=2.2)     # "now" typed, the space comes ~0.5 s in
        elif shot in ("strike", "platen"):
            T.type_at(c["tw"], sec, start=0.4, cps=2.4 if shot == "strike" else 3.2)
        else:
            T.type_at(c["tw"], sec, start=0.2, cps=3.0)
        bpy.context.scene.frame_set(int(t * DUR[shot] * FPS) + 1)              # drivers (X-ray fade) follow in stills too
    return f


W = lambda c, p: T.world(c["tw"], p)


def ball(c):
    return W(c, (c["tw"]["carrier"].location.x, T.BALL_Y, T.BALL_Z))


def cam_strike(c, t):
    e = ease(t); b = ball(c)
    return (b + Vector((0.32, -0.5, 0.28)).lerp(Vector((0.26, -0.42, 0.23)), e), b + Vector((-0.02, -0.04, -0.03)), 50)        # medium-close: ball, keys, page


def cam_platen(c, t):
    e = ease(t); x0 = T.PAGE_LEFT + T.MARGIN
    a = W(c, (x0 - 0.05, -0.06, T.PLATEN_Z + 0.07)); b = W(c, (x0 + 0.02, -0.055, T.PLATEN_Z + 0.065))
    return (a.lerp(b, e) + Vector((0, -0.06, 0.03)), W(c, (x0 + 0.05, T.PLATEN_Y - T.PLATEN_R, T.PLATEN_Z + 0.008)), 50)


def cam_sink(c, t):
    e = ease(t)
    a = W(c, (0.16, -0.32, 0.26)); b = W(c, (0.13, -0.36, 0.06))
    ta = ball(c); tb = W(c, (0.0, T.BAR_Y + 0.03, 0.04))
    return (a.lerp(b, e), ta.lerp(tb, e), 50)


def cam_arms(c, t):
    e = ease(t)
    return (W(c, (0.3, -0.42, 0.3)).lerp(W(c, (0.25, -0.36, 0.26)), e), W(c, (0.0, -0.085, 0.04)), 45)


def cam_magnets(c, t):
    e = ease(t)
    return (W(c, (0.16, -0.36, 0.2)).lerp(W(c, (0.13, -0.31, 0.17)), e), W(c, (0.0, T.BAR_Y + 0.004, T.BAR_Z + 0.012)), 60)


def cam_xray(c, t):
    e = ease(t)
    return (W(c, (-0.3, -0.42, 0.32)).lerp(W(c, (-0.24, -0.36, 0.26)), e), W(c, (0.0, -0.05, 0.05)), 42)


def cam_space(c, t):
    e = ease(t); b = ball(c)
    return (W(c, (-0.26, -0.44, 0.11)).lerp(W(c, (-0.22, -0.39, 0.1)), e), W(c, (-0.02, -0.12, 0.06)), 40)       # low, front-left: the long bar and the still ball beyond


MOVES = {
    "strike": dict(kind="anim", dof=7.1, cam=cam_strike, focus=lambda c, t: ball(c), anim=anim("strike"), title=("CHAPTER 3", "THE SIGNAL", 10, 130)),
    "platen": dict(kind="anim", dof=6.3, cam=cam_platen, focus=lambda c, t: W(c, (T.PAGE_LEFT + T.MARGIN + 0.03, T.PLATEN_Y - T.PLATEN_R, T.PLATEN_Z)), anim=anim("platen")),
    "sink": dict(kind="anim", dof=None, cam=cam_sink, focus=lambda c, t: ball(c).lerp(W(c, (0.0, T.BAR_Y + 0.03, 0.04)), ease(t)), anim=anim("sink")),
    "arms": dict(kind="anim", dof=5.6, cam=cam_arms, focus=lambda c, t: W(c, (0.0, -0.085, 0.04)), anim=anim("arms")),
    "magnets": dict(kind="anim", dof=16.0, cam=cam_magnets, focus=lambda c, t: W(c, (0.0, T.BAR_Y + 0.004, T.BAR_Z + 0.012)), anim=anim("magnets")),
    "xray": dict(kind="anim", dof=8.0, cam=cam_xray, focus=lambda c, t: W(c, (0.0, -0.06, 0.06)), anim=anim("xray")),
    "coil": dict(kind="anim", dof=None, cam=lambda c, t: (W(c, (0.3, -0.24, 0.2)).lerp(W(c, (0.26, -0.2, 0.17)), ease(t)), W(c, (0.162, -0.066, 0.036)), 60),
                 anim=anim("coil")),                       # Ch2 4B: the open power switch and its extra coil, housing faded away
    "space": dict(kind="anim", dof=8.0, cam=cam_space, focus=lambda c, t: W(c, (0.0, -0.17, 0.05)), anim=anim("space")),
}
