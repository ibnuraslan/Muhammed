"""CH1 corporate interiors (dramatization), house style.
  lobby : SET 6B - a double-height finance-tower lobby, marble floor, glass wall onto a plaza; Alice walks away across it
  pitch : SET 9  - a glass meeting room at night; Alice (from behind) presents a data-center slide; two investors across
          the table, one leans over to the other
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from human import Human, add_asset, reset_pose, pose_sit, pose_walk, fingers_curl, _world_verts, reach
from people import woman
from sc_home import facade, haze_mix
import ph
import skia

EXPOSURE = -0.4
VARIANT_FOR = {"lobby_walk": "lobby", "pitch_present": "pitch", "pitch_whisper": "pitch"}
DUR = {"lobby_walk": 5.0, "pitch_present": 4.5, "pitch_whisper": 4.0}     # estimates until the chapter 1 voiceover
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")


def arms_down(h, phase, swing):
    M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
    for sd, sg in (("L", 1), ("R", -1)):
        a = math.radians(swing) * math.sin(2 * math.pi * phase + (math.pi if sd == "L" else 0.0))
        up = (Vector((0, 0, -1)) * math.cos(a) + fwd * math.sin(a) + left * (0.12 * sg)).normalized()
        lo = (up + fwd * (0.25 + 0.15 * max(0.0, math.sin(a)))).normalized()
        h.aim(f"upperarm01.{sd}", up); h.aim(f"upperarm02.{sd}", up)
        h.aim(f"lowerarm01.{sd}", lo); h.aim(f"lowerarm02.{sd}", lo); h.aim(f"wrist.{sd}", lo + left * (0.1 * sg))


def slide_image(path, W=1600, H=900):
    """The pitch slide: a clean render-like diagram of a data hall and a headline bar (no real names)."""
    s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.Color4f(0.96, 0.97, 0.98, 1))
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(skia.Color4f(0.1, 0.14, 0.22, 1)); c.drawRect(skia.Rect.MakeXYWH(0, 0, W, 120), p)
    f = skia.Font(skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"), 44)
    p.setColor4f(skia.Color4f(1, 1, 1, 1)); c.drawString("NEW AI DATA CENTER  ·  PHASE 1", 60, 78, f, p)
    for r in range(4):                                   # rows of racks in perspective-ish blocks
        for k in range(10):
            x = 140 + k * 125 + r * 18; y = 260 + r * 120
            p.setColor4f(skia.Color4f(0.2 + 0.05 * r, 0.24 + 0.05 * r, 0.3 + 0.05 * r, 1)); c.drawRect(skia.Rect.MakeXYWH(x, y, 100, 90), p)
            p.setColor4f(skia.Color4f(0.3, 0.85, 0.5, 1)); c.drawRect(skia.Rect.MakeXYWH(x + 8, y + 10, 6, 6), p)
    p.setColor4f(skia.Color4f(0.4, 0.42, 0.45, 1))
    for k in range(3):
        c.drawRect(skia.Rect.MakeXYWH(140, 780 + k * 28, 900 - k * 200, 10), p)
    s.makeImageSnapshot().save(path, skia.kPNG); return path


def build(variant=None):
    c = {}
    if variant == "lobby":
        build_lobby(c)
    else:
        build_pitch(c)
    return c


# ============================================================================ lobby
def build_lobby(c):
    world_sky(sun_elev_deg=30, sun_rot_deg=150, strength=0.18, tint=(0.95, 0.97, 1.0))
    sun(30, 150, energy=0.9, color=(1.0, 0.95, 0.88), angle_deg=1.0)
    marble = ph.texture("marble_tiles", scale=0.3)
    box("Floor", (0, 6, -0.01), (16, 24, 0.02), marble)
    stone = pbr("LobbyStone", (0.6, 0.58, 0.55), 0.5)
    box("WallBack", (0, 17.5, 4.5), (16, 0.3, 9), stone)
    box("WallL", (-8, 6, 4.5), (0.3, 24, 9), stone)
    box("Ceiling", (0, 6, 9.0), (16, 24, 0.2), pbr("LobbyCeil", (0.72, 0.72, 0.7), 0.8))
    # right side: full-height glass curtain wall onto a plaza with trees and towers
    for k in range(9):
        box("Mullion", (8, -4 + k * 2.7, 4.5), (0.12, 0.12, 9.0), pbr("MullM", (0.12, 0.12, 0.13), 0.4, 0.8))
    box("Curtain", (8.0, 6, 4.5), (0.02, 24, 9.0), glass("LobbyGlass", (0.9, 0.93, 0.95), 0.01))
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 24; pt.size_y = 9; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (8.1, 6, 4.5); po.rotation_euler = (0, math.radians(-90), 0)
    box("Plaza", (40, 6, -0.05), (60, 80, 0.1), pbr("PlazaStone", (0.45, 0.44, 0.42), 0.7))
    tw = facade("PlazaTower", (0.05, 0.08, 0.1), (0.5, 0.5, 0.5), floor=4.0, bay=1.6, refl=0.4)
    for k, (y, hgt) in enumerate(((-10, 180), (14, 240), (34, 150))):
        box("Tower", (70, y, hgt / 2), (30, 30, hgt), tw)
    # reception desk, turnstiles, a large plant, a long bench
    desk = pbr("DeskStone", (0.15, 0.14, 0.13), 0.3, 0.0, **{'Coat Weight': 0.5})
    box("Reception", (-3.5, 13.0, 0.55), (5.0, 1.0, 1.1), desk, bevel=0.02)
    box("ReceptionTop", (-3.5, 13.0, 1.12), (5.2, 1.15, 0.04), pbr("Brass", (0.6, 0.45, 0.22), 0.25, 1.0))
    for k in range(5):
        box("Gate", (-1.5 + k * 1.1, 10.0, 0.5), (0.18, 1.2, 1.0), pbr("GateSteel", (0.6, 0.61, 0.63), 0.25, 1.0), bevel=0.02)
        box("GateGlass", (-1.5 + k * 1.1 + 0.5, 10.0, 0.7), (0.02, 0.9, 0.6), glass("GateG", (0.9, 0.93, 0.95)))
    ph.model("potted_plant_02", loc=(5.5, 12.0, 0.0), scale=2.4)
    ph.model("potted_plant_02", loc=(-6.5, 3.0, 0.0), scale=2.0)
    box("Bench", (5.6, 4.0, 0.25), (0.6, 4.0, 0.5), pbr("BenchWood", (0.25, 0.15, 0.08), 0.4), bevel=0.02)
    for x in (-4, 0, 4):
        for y in (2, 8, 14):
            l = area_light((x, y, 8.9), (0, 0, 0), 1.2, 35, (1.0, 0.95, 0.88)); l.visible_camera = False
    a = woman("Alice"); c["alice"] = a


def place_alice(c, sec):
    a = c["alice"]
    y = 1.0 + 1.05 * sec                       # she walks away from the camera (+Y), toward the gates
    bob = pose_walk(a, (1.05 * sec / 1.3) % 1.0, stride=24, arm_swing=14)
    a.arm.rotation_euler = (0, 0, math.pi); a.arm.location = (0.4, y, bob); bpy.context.view_layer.update()
    arms_down(a, (1.05 * sec / 1.3) % 1.0, 14)
    bpy.context.view_layer.update()
    return Vector((0.4, y, 1.2))


def anim_lobby(c, t):
    c["p"] = place_alice(c, t * DUR["lobby_walk"])


def cam_lobby(c, t):
    p = c["p"]; e = ease(t)
    return (Vector((-0.6, -4.5 + 2.0 * e, 1.5)), p + Vector((0.3, 4.0, 0.6)), 32)


# ============================================================================ pitch room
def build_pitch(c):
    world_flat((0.01, 0.012, 0.02), 1.0)
    os.makedirs(GEN, exist_ok=True)
    slide = slide_image(os.path.join(GEN, "pitch_slide.png"))
    box("Floor", (0, 0, -0.01), (10, 8, 0.02), fabric("Carpet", (0.1, 0.1, 0.11), 0.95, 0.2, 500))
    box("Ceiling", (0, 0, 3.0), (10, 8, 0.04), pbr("Ceil", (0.6, 0.6, 0.6), 0.8))
    box("WallScreen", (0, 3.2, 1.5), (6, 0.1, 3.0), pbr("WallDark", (0.12, 0.12, 0.13), 0.8))
    box("Glass", (-3.0, 0, 1.5), (0.02, 6.4, 3.0), glass("MeetGlass", (0.9, 0.93, 0.95), 0.01))
    box("GlassBack", (0, -3.2, 1.5), (6, 0.02, 3.0), glass("MeetGlass3", (0.9, 0.93, 0.95), 0.01))      # behind the investors: the city
    box("GlassR", (3.0, 0, 1.5), (0.02, 6.4, 3.0), glass("MeetGlass2", (0.9, 0.93, 0.95), 0.01))
    # city at night beyond the left glass: towers with a few lit offices (cells, not glitter)
    tw = facade("NightTower", (0.03, 0.04, 0.05), (0.15, 0.16, 0.17), floor=3.8, bay=1.6, lit_frac=0.18, refl=0.3)
    rng = np.random.default_rng(4)
    for k in range(18):
        hgt = rng.uniform(60, 220); box("Tower", (rng.uniform(-260, 260), -80 - rng.uniform(0, 320), hgt / 2 - 60), (35, 35, hgt), tw)
    # the screen with the slide
    m = bpy.data.materials.new("Slide"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(slide)
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['UV'], t.inputs['Vector'])
    p = N["Principled BSDF"]; L.new(t.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = 1.2
    p.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 3.13, 1.6), rotation=(math.radians(90), 0, 0))
    scr = bpy.context.active_object; scr.scale = (2.6, 1.46, 1); scr.data.materials.append(m)
    sl = area_light((0, 3.0, 1.6), (0, 0, 0), 2.6, 60, (0.95, 0.97, 1.0)); point_at(sl, (0, 0, 1.2)); sl.visible_camera = False; sl.visible_glossy = False
    # table and chairs
    box("Table", (0, 0.2, 0.74), (3.4, 1.3, 0.04), pbr("TableTop", (0.08, 0.06, 0.05), 0.25, 0.0, **{'Coat Weight': 0.7}), bevel=0.01)
    box("TableBase", (0, 0.2, 0.37), (2.4, 0.4, 0.72), pbr("TableBase", (0.05, 0.05, 0.05), 0.4, 0.8))
    for k in range(4):
        cyl("Glass", (-1.2 + k * 0.8, -0.1, 0.8), 0.035, 0.12, glass("Tumbler", (0.95, 0.97, 0.98)), verts=24)
    l = area_light((0, 0.2, 2.9), (0, 0, 0), 2.0, 140, (1.0, 0.9, 0.78)); l.visible_camera = False
    # investors seated on the far side facing the screen-side? No: they face Alice (toward -Y); she stands by the screen
    invs = []
    for k, (g, yrs, cl, hr, x) in enumerate(((1.0, 55, "male_elegantsuit01", "short04", -0.6), (1.0, 46, "male_casualsuit03", "short01", 0.6))):
        h = Human(f"Investor{k}", gender=g, years=yrs, muscle=0.5, weight=0.55, height=0.5, eyelashes="eyelashes01")
        add_asset(h, "clothes", cl, val=0.15 + 0.1 * k, rough=0.6); add_asset(h, "clothes", "shoes02", val=0.15); add_asset(h, "hair", hr, val=0.35 + 0.2 * k)
        reset_pose(h); pose_sit(h, lean=10)
        h.arm.rotation_euler = (0, 0, math.pi); h.arm.location = (x, -0.75, 0); bpy.context.view_layer.update()     # face +Y (the screen and Alice)
        w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
        h.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()
        box("Chair", (x, -0.85, 0.45), (0.55, 0.5, 0.08), pbr("ChairM", (0.04, 0.04, 0.045), 0.5), bevel=0.03)
        box("ChairBack", (x, -1.12, 0.9), (0.52, 0.08, 0.75), pbr("ChairM", (0.04, 0.04, 0.045), 0.5), bevel=0.03)
        invs.append(h)
    c["investors"] = invs
    a = woman("Alice"); c["alice"] = a
    reset_pose(a); pose_walk(a, 0.0, stride=0.0, arm_swing=0.0)
    a.arm.rotation_euler = (0, 0, 0); a.arm.location = (1.1, 2.4, 0); bpy.context.view_layer.update()         # faces -Y: the investors
    w = np.concatenate([_world_verts(o) for o in a.parts if o.type == 'MESH'])
    a.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()


def anim_pitch(c, t, whisper=False, seconds=4.5):
    sec = t * seconds
    a = c["alice"]
    # she gestures toward the slide with her right hand (hand rises, opens toward the screen)
    g = 0.5 + 0.5 * math.sin(sec * 1.4)
    reach(a, "R", a.bone_head("upperarm01.R") + Vector((-0.25 - 0.1 * g, 0.15 + 0.15 * g, -0.25 + 0.15 * g)), Vector((0.3, 0.5, -1)), Vector((-0.6, 0.6, 0.2)))
    arms_left = a.bone_head("upperarm01.L") + Vector((0.08, -0.05, -0.55))
    reach(a, "L", arms_left, Vector((0.5, 0.3, -1)), Vector((0, -0.2, -1)))
    a.rot("head", (0, 0, 1), -15 * g)
    i0, i1 = c["investors"]
    for k, h in enumerate((i0, i1)):
        chest = h.bone_head("spine03")
        for sd, sg in (("L", 1), ("R", -1)):
            reach(h, sd, chest + Vector((0.12 * sg, 0.42, -0.12)), Vector((sg * 0.6, 0, -0.8)), Vector((0, 1, -0.2)))
        fingers_curl(h, 30, thumb=10)
    if whisper:                                  # the investor on the right leans over to the other
        k = math.sin(math.pi * min(1.0, max(0.0, (t - 0.2) / 0.7)))
        i1.rot("spine04", (0, 1, 0), 10 * k); i1.rot("neck01", (0, 0, 1), 25 * k); i1.rot("head", (0, 0, 1), 15 * k)
        i0.rot("head", (0, 0, 1), -8 * k)
    bpy.context.view_layer.update()


def cam_present(c, t):
    e = ease(t)
    return (Vector((2.2, 3.0, 1.65)).lerp(Vector((1.95, 2.85, 1.62)), e), Vector((-0.2, -0.6, 1.0)), 32)     # behind Alice, toward the investors


def cam_whisper(c, t):
    e = ease(t)
    return (Vector((1.6, 1.6, 1.25)).lerp(Vector((1.3, 1.4, 1.22)), e), Vector((0.0, -0.75, 1.1)), 50)


MOVES = {
    "lobby_walk": dict(kind="anim", dof=4.0, far=60.0, cam=cam_lobby, focus=lambda c, t: c["p"], anim=anim_lobby),
    "pitch_present": dict(kind="anim", dof=2.8, far=20.0, cam=cam_present, focus=lambda c, t: Vector((0.0, -0.75, 1.1)),
                          anim=lambda c, t: anim_pitch(c, t, False, DUR["pitch_present"])),
    "pitch_whisper": dict(kind="anim", dof=2.4, far=20.0, cam=cam_whisper, focus=lambda c, t: Vector((0.3, -0.75, 1.15)),
                          anim=lambda c, t: anim_pitch(c, t, True, DUR["pitch_whisper"])),
}
