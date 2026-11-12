"""CH4 (chat B): forensic phonetics lab, 2007-08 (state criminal police, generic: no crest, no readable text).
Late low sun knifes through blinds; the rest is lit by monitor glow. An expert in headphones studies waveforms;
along the right wall eleven comparable reel-to-reel recorders sit on a long test bench.
  listen   (A): slow push from behind the expert in headphones toward her waveform screens
  segments (B): over her shoulder: three call waveforms line up, a playback cursor sweeps them
  eleven   (A): slow track along the eleven recorders as their reels start one by one
  pause    (B): the seized recorder at the end, a microphone in front; its pause key drops, the waveform behind jumps
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
DUR = {"listen": 5.5, "segments": 5.0, "eleven": 6.0, "pause": 5.0}
DESK_TOP = 0.79
BENCH_X = 3.25


def build(variant=None):
    c = {}
    rng = np.random.default_rng(7)
    world_flat((0.01, 0.012, 0.016), 1.0)
    floor = B.tex_mat("LabFloor", "grey_tiles", scale=0.5, tint=(0.6, 0.62, 0.64))
    box("Floor", (0, 0, -0.01), (9, 8, 0.02), floor)
    wall = B.plaster("LabWall", (0.5, 0.52, 0.52), dirt=0.15)
    box("WallBack", (0, 3.05, 1.5), (9, 0.1, 3.0), wall); box("WallR", (4.05, 0, 1.5), (0.1, 8, 3.0), wall)
    box("WallFront", (0, -3.6, 1.5), (9, 0.1, 3.0), wall)
    box("Ceiling", (0, 0, 2.9), (9, 8, 0.05), B.plaster("LabCeil", (0.45, 0.46, 0.46)))
    # left wall: a long window with half-closed blinds; the low sun cuts hard stripes across the room
    box("WallL_lo", (-4.05, 0, 0.45), (0.1, 8, 0.9), wall); box("WallL_hi", (-4.05, 0, 2.6), (0.1, 8, 0.6), wall)
    box("WallL_a", (-4.05, -2.6, 1.6), (0.1, 2.8, 1.4), wall)
    slat = pbr("Blind", (0.7, 0.7, 0.68), 0.5)
    for k in range(26):
        box("Slat", (-3.95, 0.8, 0.93 + k * 0.052), (0.045, 4.4, 0.005), slat, rot=(0, math.radians(-38), 0))
    sky = box("Outside", (-7, 0.8, 1.6), (0.05, 10, 5), emissive("OutsideGlow", (1.0, 0.7, 0.45), 0.8)); sky.visible_shadow = False
    B.key_sun(12, 180 + 25, 11.0, color=(1.0, 0.66, 0.4), angle=0.6)
    B.fill((2.5, -3.0, 2.5), (0, 1.5, 1.0), 40, 3.0, (0.4, 0.55, 0.75))
    B.room_haze((0, 0, 1.45), (8.0, 7.0, 2.9), density=0.01, color=(0.9, 0.92, 0.95))
    # ------------------------------------------------------------------ the expert's desk
    ph.model("metal_office_desk", loc=(-0.6, 2.3, 0), rot_z=0)
    wf = [P.waveform_image(f"{B.GEN}/b_wave_{k}.png", segments=3 if k == 0 else 2, seed=k + 3) for k in range(3)]
    c["mon_main"], c["scr_main"] = P.lcd_monitor("MonMain", (-0.6, 2.45, DESK_TOP), 0.0, P.screen_mat("WaveMain", wf[0], 1.3, cursor_speed=0.09), w=0.52, h=0.32)
    P.lcd_monitor("MonLeft", (-1.25, 2.38, DESK_TOP), math.radians(18), P.screen_mat("WaveL", wf[1], 1.0, cursor=False), w=0.44, h=0.28)
    P.lcd_monitor("MonRight", (0.08, 2.38, DESK_TOP), math.radians(-18), P.screen_mat("WaveR", wf[2], 1.0, cursor=False), w=0.44, h=0.28)
    bez = pbr("KB", (0.03, 0.03, 0.035), 0.4)
    box("Keyboard", (-0.6, 2.08, DESK_TOP + 0.012), (0.44, 0.15, 0.022), bez, bevel=0.004)
    box("Mouse", (-0.25, 2.06, DESK_TOP + 0.015), (0.06, 0.1, 0.03), bez, bevel=0.012)
    ph.model("office_notepads", loc=(-1.35, 2.0, DESK_TOP), rot_z=0.2, scale=0.5)
    ph.model("binder_notebook", loc=(0.15, 2.05, DESK_TOP), rot_z=2.6)
    P.reel_recorder("DeskRec", (0.95, 2.3, DESK_TOP), rot_z=0.2, spin=0.35)
    # the expert: seated, facing the screens (+Y), headphones on
    from sc_invest import office_chair
    fab = fabric("ChairFab", (0.08, 0.09, 0.1), 0.85, 0.3, 300); legm = pbr("ChairLeg", (0.12, 0.12, 0.13), 0.4, 0.8)
    h = B.person("Expert", 0.0, 46, "female_elegantsuit01", "bob02", hue=0.55, sat=0.4, val=0.55, hair_val=0.25)
    B.seat(h, (-0.6, 1.62, 0), math.pi, lean=10)
    office_chair((-0.6, 1.54, 0), math.pi, fab, legm)
    c["expert"] = h
    c["phones"] = P.headphones(h)
    # ------------------------------------------------------------------ the test bench: eleven recorders
    for y in (-2.0, 0.0, 2.0):
        ph.model("metal_office_desk", loc=(BENCH_X, y, 0), rot_z=math.radians(90))
    c["recs"] = []
    for k in range(11):
        y = -2.75 + k * 0.49
        r = P.reel_recorder(f"Rec{k}", (BENCH_X + 0.05, y, DESK_TOP), rot_z=-math.pi / 2 + rng.uniform(-0.04, 0.04),
                            spin=0.45, start_frame=10 + 9 * k, lid_wood=(k % 3 != 1))
        c["recs"].append(r)
    # the seized machine is the last one: a microphone stands in front of it, a monitor behind shows its test
    last = c["recs"][-1]
    c["mic"] = P.mic_stand("TestMic", (BENCH_X - 0.05, 2.5, DESK_TOP), (BENCH_X, 2.12, DESK_TOP + 0.17), h=0.22)
    wfx = P.waveform_image(f"{B.GEN}/b_wave_test.png", segments=2, seed=21)
    P.lcd_monitor("MonTest", (BENCH_X + 0.25, 2.62, DESK_TOP), math.radians(-125), P.screen_mat("WaveT", wfx, 1.2, cursor_speed=0.12), w=0.44, h=0.28)
    # the pause key drops at frame 48 (frame driver), and its reels stop
    pk = last["keys"][3]
    d = pk.driver_add("location", 2).driver; d.type = 'SCRIPTED'; d.expression = f"{last['top'] + 0.006} - 0.007 * min(1, max(0, (frame - 48) / 3))"
    for rl in last["reels"]:
        d = rl.driver_add("rotation_euler", 2).driver; d.type = 'SCRIPTED'
        d.expression = "-min(frame, 48) / 24 * 0.45 * 6.2832"
    for o in (bpy.data.objects.get("WallClock"),):
        pass
    ph.model("wall_clock", loc=(1.8, 3.0, 2.2), rot_z=0)
    # overhead fluorescent fixtures (off, it's late) and one practical desk lamp
    for x in (-1.5, 1.5):
        ph.model("mounted_fluorescent_lights", loc=(x, 0.5, 2.88), rot_z=math.radians(90))
    ph.model("desk_lamp_arm_01", loc=(-1.5, 2.55, DESK_TOP), rot_z=math.radians(30))
    B.key_spot((-1.3, 2.3, 1.45), (-1.0, 2.1, DESK_TOP), 120, 70, (1.0, 0.76, 0.5), soft=0.05, name="DeskLamp")
    # a hard raking work light along the test bench (from the room side, high), and a cool rim on the expert
    for y in (-2.2, -0.2, 1.8):
        B.key_spot((1.6, y - 0.6, 2.6), (BENCH_X, y + 0.3, DESK_TOP), 380, 45, (1.0, 0.8, 0.58), soft=0.08, blend=0.6, name="BenchKey")
    B.key_spot((0.6, 3.0, 2.4), (-0.6, 1.6, 1.3), 90, 25, (0.55, 0.7, 0.95), soft=0.1, name="Rim")
    return c


def anim_expert(c, sec):
    h = c["expert"]; fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    kb = Vector((-0.6, 2.06, DESK_TOP + 0.05))
    reach(h, "R", Vector((-0.25, 2.03, DESK_TOP + 0.06)) + Vector((0.004 * math.sin(sec * 2), 0, 0)), Vector((0.7, -0.3, -0.6)), fwd + Vector((0, 0, -0.5)))
    reach(h, "L", kb + side * (-0.12) - fwd * 0.03, Vector((-0.7, -0.3, -0.6)), fwd + Vector((0, 0, -0.5)))
    fingers_curl(h, 30, thumb=10)
    h.rot("head", side, 4 + 3 * math.sin(sec * 0.7))       # listening: small slow nods
    h.rot("head", (0, 0, 1), 3 * math.sin(sec * 0.35))
    bpy.context.view_layer.update()


def anim(c, t, dur):
    anim_expert(c, t * dur)


def cam_listen(c, t):
    e = ease(t)
    return (Vector((0.35, -0.35, 1.62)).lerp(Vector((-0.1, 0.6, 1.5)), e), Vector((-0.6, 2.4, 1.05)), 32)


def cam_segments(c, t):
    e = ease(t)
    return (Vector((-0.2, 1.35, 1.42)).lerp(Vector((-0.28, 1.52, 1.38)), e), Vector((-0.6, 2.45, 1.0)), 40)


def cam_eleven(c, t):
    e = ease(t)
    y = -3.0 + 2.2 * e
    return (Vector((2.25, y, 1.55)), Vector((BENCH_X, y + 1.7, 0.82)), 30)


def cam_pause(c, t):
    e = ease(t)
    return (Vector((2.5, 1.45, 1.42)).lerp(Vector((2.62, 1.62, 1.36)), e), Vector((BENCH_X, 2.12, DESK_TOP + 0.12)), 45)


MOVES = {
    "listen": dict(kind="anim", dof=2.8, cam=cam_listen, anim=lambda c, t: anim(c, t, DUR["listen"]),
                   focus=lambda c, t: c["expert"].bone_head("head")),
    "segments": dict(kind="anim", dof=2.4, cam=cam_segments, anim=lambda c, t: anim(c, t, DUR["segments"]),
                     focus=lambda c, t: Vector((-0.6, 2.45, 1.07))),
    "eleven": dict(kind="anim", dof=4.0, cam=cam_eleven, anim=lambda c, t: anim(c, t, DUR["eleven"]),
                   focus=lambda c, t: Vector((BENCH_X, -3.0 + 2.2 * ease(t) + 1.6, 0.9))),
    "pause": dict(kind="anim", dof=2.0, cam=cam_pause, anim=lambda c, t: anim(c, t, DUR["pause"]),
                  focus=lambda c, t: Vector((BENCH_X + 0.05, 2.1, DESK_TOP + 0.12))),
}
