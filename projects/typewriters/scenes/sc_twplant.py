"""TYPEWRITER PLANT, Kentucky, 1984 (dramatization; generic, no brand). A long assembly line under rows of fluorescent
panels: machines ride a belt between work stations; at the end, boxed machines are stacked onto a pallet.

Ch1 5A  line    typewriters move down the line; a worker fits a carriage cover on one as it passes
Ch1 5B  pallet  a worker stacks the boxed machines onto a pallet; a forklift waits
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import typewriter as T

EXPOSURE = 0.0
DUR = {"line": 5.0, "pallet": 4.5}
LINE_Y = 0.0
BELT_Z = 0.85
SPEED = 0.18               # belt speed m/s
PITCH = 0.9                # machine spacing on the belt


def box_label(path):
    import skia
    sf = skia.Surface(800, 600); cv = sf.getCanvas(); cv.clear(skia.Color4f(0.62, 0.5, 0.34, 1))
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(0.16, 0.12, 0.08, 1))
    f = skia.Font(skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"), 44)
    cv.drawString("ELECTRIC TYPEWRITER", 150, 250, f, p)
    p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(4); cv.drawRect(skia.Rect.MakeXYWH(120, 180, 560, 120), p)
    for k in range(4):
        cv.drawLine(150, 380 + k * 40, 600, 380 + k * 40, p)
    sf.makeImageSnapshot().save(path, skia.kPNG)
    return path


def build(variant=None):
    import os
    c = {}
    rng = np.random.default_rng(56)
    world_flat((0.05, 0.06, 0.07), 1.0)
    box("Floor", (0, 0, -0.01), (40, 20, 0.02), ph.texture("concrete_floor_painted", scale=0.3, name="PlantFloor", tint=(0.62, 0.66, 0.6)))
    wall = ph.texture("painted_concrete", scale=0.3, name="PlantWall", tint=(0.8, 0.8, 0.76))
    box("WallBack", (0, 8.0, 3.5), (40, 0.2, 7), wall)
    box("WallL", (-20, 0, 3.5), (0.2, 20, 7), wall)
    for k in range(8):
        box("HighWin", (-17 + k * 5, 7.88, 5.5), (3.2, 0.05, 1.4), glass("HighGlass", (0.88, 0.9, 0.92), 0.15))
    box("Ceiling", (0, 0, 7.0), (40, 20, 0.1), ph.texture("corrugated_iron_02", scale=0.4, name="PlantRoof", tint=(0.6, 0.6, 0.6)))
    for k in range(10):
        box("Beam", (-18 + k * 4, 0, 6.6), (0.25, 20, 0.5), pbr("BeamGrey", (0.35, 0.36, 0.35), 0.5, 0.6))
    for x in np.arange(-15, 15, 2.6):
        for y in (-2.2, 0.0, 2.2):
            ph.model("mounted_fluorescent_lights", loc=(x, y, 3.6), rot_z=0)
            l = area_light((x, y, 3.52), (0, 0, 0), 0.9, 30, (0.9, 0.96, 1.0)); l.visible_camera = False
            cyl("Hanger", (x, y, 5.3), 0.008, 3.4, pbr("Hang", (0.2, 0.2, 0.2), 0.5), verts=6)
    sky = area_light((0, 7.5, 5.5), (0, 0, 0), 30.0, 900, (0.85, 0.9, 1.0)); point_at(sky, (0, 0, 0)); sky.visible_camera = False
    # ---------------------------------------------------------------- the line: belt, rollers, frame, stations
    frame = pbr("LineFrame", (0.25, 0.32, 0.3), 0.45, 0.5)
    belt = pbr("Belt", (0.04, 0.045, 0.045), 0.7)
    box("Belt", (0, LINE_Y, BELT_Z - 0.02), (24, 0.7, 0.04), belt)
    for sy in (-1, 1):
        box("Rail", (0, LINE_Y + sy * 0.38, BELT_Z - 0.03), (24, 0.06, 0.12), frame)
    for k in range(25):
        for sy in (-1, 1):
            box("Leg", (-12 + k * 1.0, LINE_Y + sy * 0.36, (BELT_Z - 0.09) / 2), (0.06, 0.06, BELT_Z - 0.09), frame)
    for k in range(6):
        x = -9 + k * 3.4
        for sy in (-1, 1):
            box("StationTop", (x, LINE_Y + sy * 0.95, 0.9), (1.4, 0.55, 0.04), ph.texture("oak_veneer_01", scale=1.0, name="StationWood"))
            box("StationFrame", (x, LINE_Y + sy * 0.95, 0.45), (1.3, 0.5, 0.88), frame)
            if (k + (sy > 0)) % 2 == 0:
                ph.model("retro_multimeter", loc=(x - 0.35, LINE_Y + sy * 0.95, 0.92), rot_z=0 if sy < 0 else math.pi)
            ph.model("screwdriver", loc=(x + 0.3, LINE_Y + sy * 0.9, 0.92), rot_z=rng.uniform(0, 3))
            r, ms = ph.model("desk_lamp_arm_01", loc=(x + 0.55, LINE_Y + sy * 1.15, 0.92), rot_z=0 if sy < 0 else math.pi); twp.tint_model(ms, (0.2, 0.22, 0.2), 0.1)
    # parts bins and shelving along the back wall
    for k in range(10):
        ph.model("steel_frame_shelves_02", loc=(-14 + k * 0.65, 6.9, 0), rot_z=math.pi)
    for k in range(20):
        ph.model("plastic_crate_01" if k % 2 else "cardboard_box_01", loc=(-14.1 + (k % 10) * 0.65, 6.9, 0.5 + (k // 10) * 0.8), rot_z=math.pi, scale=0.6)
    # ---------------------------------------------------------------- machines on the belt (cheap typewriters: no glyphs)
    c["tws"] = []
    cols = [(0.11, 0.15, 0.2), (0.32, 0.28, 0.22), (0.2, 0.25, 0.3), (0.42, 0.12, 0.1)]
    for k in range(10):
        tw = T.make(f"PL{k}", loc=(0, 0, 0), rot_z=-math.pi / 2, color=cols[k % 4], mechanism=False, glyphs=False, legends=False, text=" ")
        tw["paper"].hide_render = True
        c["tws"].append(tw)
    # ---------------------------------------------------------------- the end of the line: boxes, a pallet, a forklift
    lab = tex_box_material(box_label(os.path.join(T.GEN, "carton.png")))
    c["boxes"] = []
    for k in range(10):
        b = box("Carton", (0, 0, 0), (0.6, 0.5, 0.32), lab, bevel=0.006); c["boxes"].append(b)
    ph.model("wooden_crate_02", loc=(15.8, 2.4, 0), scale=0.0001) if False else None
    pal_wood = ph.texture("brown_planks_03", scale=1.0, name="PalletWood")
    pal = join([box("PalTop", (0, 0, 0.13), (1.25, 1.05, 0.03), pal_wood)] + [box("PalSkid", (0, dy, 0.06), (1.25, 0.1, 0.1), pal_wood) for dy in (-0.45, 0, 0.45)], "Pallet")
    pal.location = (14.5, 1.6, 0); c["pallet"] = pal
    import sc_twhangar
    fk, fw = sc_twhangar.forklift("PlantFork"); fk.location = (16.6, 1.6, 0); fk.rotation_euler = (0, 0, math.pi); c["fork"] = fk
    # people
    P = {}
    P["fitter"] = twp.person("Fitter", 0.0, 42, "female_casualsuit01", "bob02", hv=0.35, cval=0.6, hue=0.55, sat=0.25)
    P["fitter2"] = twp.person("Fitter2", 1.0, 30, "male_worksuit01", "short01", hv=0.25, cval=0.55, hue=0.58, sat=0.2)
    P["fitter3"] = twp.person("Fitter3", 0.0, 55, "female_casualsuit02", "ponytail01", hv=0.55, cval=0.55, hue=0.08, sat=0.25)
    P["stacker"] = twp.person("Stacker", 1.0, 36, "male_worksuit01", "short03", hv=0.25, cval=0.5, hue=0.1, sat=0.2)
    c["P"] = P
    animate(c, 0.0, "line")
    return c


def tex_box_material(path):
    m = bpy.data.materials.new("Carton"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.projection = 'BOX'; t.projection_blend = 0.2
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1.6, 1.6, 1.6)
    mp.inputs['Location'].default_value = (0.5, 0.5, 0.5)
    L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], t.inputs['Vector'])
    L.new(t.outputs[0], N["Principled BSDF"].inputs['Base Color']); N["Principled BSDF"].inputs['Roughness'].default_value = 0.85
    return m


def animate(c, sec, shot):
    from human import reach, fingers_curl
    P = c["P"]
    for k, tw in enumerate(c["tws"]):
        x = -11.0 + k * PITCH * 1.3 + SPEED * sec
        tw["root"].location = (x, LINE_Y, BELT_Z)
        for o in [tw["root"]] + list(tw["root"].children_recursive):
            o.hide_render = shot != "line"
    # the fitter at station 2 lowers a cover onto the machine passing in front of her
    f = P["fitter"]; x0 = -9 + 2 * 3.4
    twp.stand(f, (x0, LINE_Y - 1.45, 0), math.pi)
    near = min(c["tws"], key=lambda tw: abs(tw["root"].location.x - x0))
    tgt = near["root"].location + Vector((0, -0.05, 0.25 - 0.08 * ease(min(1.0, (sec % 2.5) / 1.2))))
    for sd, dx in (("L", 0.16), ("R", -0.16)):
        reach(f, sd, tgt + Vector((dx, -0.25, 0.0)), Vector((dx * 4, -0.4, -0.6)), Vector((0, 1, -0.4)))
    fingers_curl(f, 40, thumb=20); f.rot("head", (1, 0, 0), -14)
    for nm, xs, sy, ph_ in (("fitter2", -9 + 3.4, 1, 0.0), ("fitter3", -9 + 4 * 3.4, -1, 1.3)):
        h = P[nm]
        twp.stand(h, (xs, LINE_Y + sy * 1.45, 0), 0.0 if sy > 0 else math.pi)
        fwd = twp.forward(h)
        reach(h, "R", Vector((xs, LINE_Y + sy * 1.0, 1.0 + 0.05 * math.sin(sec * 2 + ph_))), Vector((-0.5 * sy, 0, -0.8)), fwd)
        reach(h, "L", Vector((xs - 0.25 * sy, LINE_Y + sy * 1.0, 0.98)), Vector((0.5 * sy, 0, -0.8)), fwd)
        h.rot("head", (1, 0, 0), -12 * sy)
    # pallet stacking: boxes 0..5 already placed, the stacker lifts box 6 onto the second layer
    pal = c["pallet"].location
    slots = [Vector((-0.31, -0.26, 0)), Vector((0.31, -0.26, 0)), Vector((-0.31, 0.26, 0)), Vector((0.31, 0.26, 0))]
    for k, b in enumerate(c["boxes"]):
        b.hide_render = k > 6 or shot == "line" and False
        lay = k // 4; sl = slots[k % 4]
        b.location = pal + sl + Vector((0, 0, 0.145 + 0.16 + lay * 0.32))
    st = P["stacker"]
    lift = ease(min(1.0, max(0.0, (sec - 0.6) / 2.6)))
    src = pal + Vector((-1.6, 0.0, 0.45)); dst = pal + slots[2] + Vector((0, 0, 0.145 + 0.16 + 0.32))
    b6 = c["boxes"][6]; b6.location = src.lerp(dst, lift) + Vector((0, 0, 0.25 * math.sin(math.pi * lift)))
    pos = Vector((pal.x - 1.25 + 0.5 * lift, pal.y + 0.35 - 0.1 * lift, 0))
    d = b6.location - pos; ang = math.atan2(d.x, -d.y)
    twp.stand(st, (pos.x, pos.y, 0), ang)
    side = Vector((math.cos(ang), math.sin(ang), 0))
    for sd, sg in (("L", 1), ("R", -1)):
        reach(st, sd, b6.location + side * 0.27 * sg - Vector((d.x, d.y, 0)).normalized() * 0.05, Vector((sg * side.x, sg * side.y, -0.6)), Vector((d.x, d.y, 0)))
    fingers_curl(st, 40, thumb=20)
    for k in (7, 8, 9):
        c["boxes"][k].location = pal + Vector((-1.6, -0.6 + (k - 7) * 0.62, 0.16 + 0.32 * (k == 9)))
        c["boxes"][k].hide_render = False
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_line(c, t):
    e = ease(t); x0 = -9 + 2 * 3.4
    return (Vector((x0 + 3.0, LINE_Y - 2.4, 1.75)).lerp(Vector((x0 + 2.4, LINE_Y - 2.1, 1.7)), e), Vector((x0 - 0.6, LINE_Y, 1.0)), 30)


def cam_pallet(c, t):
    e = ease(t); p = c["pallet"].location
    return (p + Vector((-2.6, -2.8, 1.6)).lerp(Vector((-2.2, -2.4, 1.55)), e), p + Vector((-0.5, 0.1, 0.7)), 30)


MOVES = {
    "line": dict(kind="anim", dof=3.5, cam=cam_line, focus=lambda c, t: Vector((-2.2, LINE_Y, 1.0)), anim=anim("line")),
    "pallet": dict(kind="anim", dof=3.5, cam=cam_pallet, focus=lambda c, t: c["pallet"].location + Vector((-0.6, 0, 0.6)), anim=anim("pallet")),
}
