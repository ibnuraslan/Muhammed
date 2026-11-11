"""CH1 SET 4A (dramatization): somewhere else entirely. Night, a small apartment desk; a young engineer at a laptop.
Over his shoulder: a terminal; he hits Enter and the job goes off to a remote cluster. The screen switches by a
frame driver (works in any render). Medium shot, no hand close-up."""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from human import Human, add_asset, reset_pose, pose_sit, fingers_curl, _world_verts, reach
import skia

EXPOSURE = 0.0
DUR = {"enter": 4.0}
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")
PRESS_FRAME = 40
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"


def terminal(path, sent):
    W, H = 1440, 900
    s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.Color4f(0.05, 0.06, 0.07, 1))
    p = skia.Paint(AntiAlias=True); f = skia.Font(skia.Typeface.MakeFromFile(MONO), 26)
    lines = [("$ ssh train@remote-cluster", (0.6, 0.65, 0.7)), ("connected.  64 nodes available", (0.45, 0.8, 0.55)),
             ("$ ls", (0.6, 0.65, 0.7)), ("data/   model/   train.py   config.yaml", (0.75, 0.78, 0.8)),
             ("$ python train.py --nodes 64 --gpus-per-node 8", (0.92, 0.93, 0.95))]
    if sent:
        lines += [("job submitted.  status: RUNNING", (0.45, 0.8, 0.55)), ("[node 01..64]  loading shards ...", (0.6, 0.65, 0.7))]
    y = 80
    for t, col in lines:
        p.setColor4f(skia.Color4f(*col, 1)); c.drawString(t, 50, y, f, p); y += 46
    if not sent:
        p.setColor4f(skia.Color4f(0.9, 0.9, 0.92, 1)); c.drawRect(skia.Rect.MakeXYWH(50 + f.measureText(lines[-1][0]) + 8, y - 46 - 24, 14, 30), p)
    s.makeImageSnapshot().save(path, skia.kPNG); return path


def build(variant=None):
    c = {}
    world_flat((0.01, 0.012, 0.018), 1.0)
    os.makedirs(GEN, exist_ok=True)
    t0 = terminal(os.path.join(GEN, "term_before.png"), False); t1 = terminal(os.path.join(GEN, "term_after.png"), True)
    # room: dark walls, a window with blinds (cool night outside), a warm desk lamp
    wall = pbr("WallDark", (0.12, 0.12, 0.13), 0.85)
    box("Floor", (0, 0, -0.01), (6, 6, 0.02), wood("Floor", (0.05, 0.035, 0.025), (0.12, 0.08, 0.05), scale=(0.4, 8, 8), rough=0.4))
    box("WallFront", (0, 1.3, 1.4), (6, 0.1, 2.8), wall); box("WallL", (-1.6, 0, 1.4), (0.1, 6, 2.8), wall)
    box("Window", (0.9, 1.24, 1.5), (1.2, 0.02, 1.3), emissive("NightOut", (0.15, 0.2, 0.32), 0.6))
    for k in range(24):
        box("Blind", (0.9, 1.2, 0.9 + k * 0.052), (1.25, 0.04, 0.006), pbr("BlindM", (0.5, 0.5, 0.5), 0.5), rot=(math.radians(60), 0, 0))
    desk = wood("Desk", (0.14, 0.1, 0.07), (0.3, 0.22, 0.15), scale=(0.3, 6, 6), rough=0.35, coat=0.2)
    box("DeskTop", (0, 0.85, 0.74), (1.5, 0.7, 0.035), desk)
    for sx in (-0.7, 0.7):
        box("DeskLeg", (sx, 0.85, 0.37), (0.04, 0.6, 0.72), pbr("Leg", (0.05, 0.05, 0.05), 0.4, 0.8))
    # laptop: aluminium base, keyboard well, hinged screen with the terminal (switches at PRESS_FRAME)
    alu = pbr("LaptopAlu", (0.3, 0.31, 0.33), 0.35, 1.0)
    box("Base", (0.05, 0.75, 0.765), (0.31, 0.22, 0.012), alu, bevel=0.004)
    box("Keys", (0.05, 0.73, 0.772), (0.27, 0.1, 0.002), pbr("KeysBlack", (0.02, 0.02, 0.02), 0.6))
    lid = box("Lid", (0.05, 0.865, 0.87), (0.31, 0.008, 0.2), alu, bevel=0.004, rot=(math.radians(-12), 0, 0))
    m = bpy.data.materials.new("Terminal"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    a = N.new("ShaderNodeTexImage"); a.image = bpy.data.images.load(t0); b = N.new("ShaderNodeTexImage"); b.image = bpy.data.images.load(t1)
    L.new(tc.outputs['UV'], a.inputs['Vector']); L.new(tc.outputs['UV'], b.inputs['Vector'])
    sw = N.new("ShaderNodeValue"); d = sw.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = f"1 if frame >= {PRESS_FRAME} else 0"
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(sw.outputs[0], mx.inputs['Factor']); L.new(a.outputs['Color'], mx.inputs[6]); L.new(b.outputs['Color'], mx.inputs[7])
    em = N.new("ShaderNodeEmission"); em.inputs['Strength'].default_value = 1.3; L.new(mx.outputs[2], em.inputs['Color']); L.new(em.outputs[0], out.inputs['Surface'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0.05, 0.86, 0.87), rotation=(math.radians(90 - 12), 0, 0))
    scr = bpy.context.active_object; scr.scale = (0.29, 0.18, 1); scr.data.materials.append(m)
    scr.location.y -= 0.0045
    sl = area_light((0.05, 0.84, 0.87), (0, 0, 0), 0.25, 1.5, (0.75, 0.85, 1.0)); point_at(sl, (0.05, 0.3, 1.25)); sl.visible_camera = False; sl.visible_glossy = False
    cyl("Mug", (0.42, 0.8, 0.8), 0.04, 0.1, pbr("Mug", (0.3, 0.32, 0.35), 0.3), verts=24)
    lamp = bpy.data.lights.new("DeskLamp", 'SPOT'); lamp.energy = 45; lamp.spot_size = math.radians(80); lamp.color = (1.0, 0.72, 0.45)
    lo = bpy.data.objects.new("DeskLamp", lamp); bpy.context.collection.objects.link(lo); lo.location = (-0.55, 0.9, 1.4); point_at(lo, (-0.1, 0.8, 0.75))
    cyl("LampShade", (-0.55, 0.9, 1.43), 0.08, 0.1, pbr("LampShade", (0.05, 0.05, 0.05), 0.4), verts=24)
    cyl("LampStem", (-0.55, 0.95, 1.08), 0.01, 0.66, pbr("LampStem", (0.05, 0.05, 0.05), 0.4, 0.8), verts=8)
    # the engineer
    h = Human("Engineer", gender=1.0, years=27, muscle=0.5, weight=0.45, height=0.5, eyelashes="eyelashes01",
              skin="young_lightskinned_male_diffuse.png")
    add_asset(h, "clothes", "male_casualsuit06", val=0.25, rough=0.8); add_asset(h, "hair", "short03", val=0.15)
    reset_pose(h); pose_sit(h, lean=14)
    h.arm.rotation_euler = (0, 0, math.pi); h.arm.location = (0.05, 0.25, 0); bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()
    box("Chair", (0.05, 0.12, 0.45), (0.5, 0.48, 0.08), pbr("ChairM", (0.05, 0.05, 0.06), 0.6), bevel=0.03)
    c.update(h=h, kb=Vector((0.05, 0.73, 0.78)))
    animate(c, 0.0)
    return c


def animate(c, sec):
    h = c["h"]; kb = c["kb"]
    f = sec * 24
    press = max(0.0, 1 - abs(f - (PRESS_FRAME - 3)) / 4.0)          # right hand dips onto Enter just before the switch
    reach(h, "L", kb + Vector((-0.08, -0.07, 0.025)), Vector((0.7, -0.4, -0.6)), Vector((0.05, 0.55, -0.83)))
    reach(h, "R", kb + Vector((0.09, -0.06, 0.025 - 0.015 * press)), Vector((-0.7, -0.4, -0.6)), Vector((-0.05, 0.55, -0.83)))
    fingers_curl(h, 55, thumb=20)
    h.rot("head", (-1, 0, 0), 8)
    if f > PRESS_FRAME + 6:                                        # he sits back a little and watches it run
        k = min(1.0, (f - PRESS_FRAME - 6) / 20)
        h.rot("spine03", (1, 0, 0), 6 * k)
    bpy.context.view_layer.update()


def anim_enter(c, t):
    animate(c, t * DUR["enter"])


def cam_enter(c, t):
    e = ease(t)
    return (Vector((-0.75, -0.55, 1.45)).lerp(Vector((-0.6, -0.4, 1.42)), e), Vector((0.08, 0.85, 0.9)), 35)


MOVES = {"enter": dict(kind="anim", dof=2.8, far=6.0, cam=cam_enter, focus=lambda c, t: Vector((0.05, 0.86, 0.87)), anim=anim_enter)}
