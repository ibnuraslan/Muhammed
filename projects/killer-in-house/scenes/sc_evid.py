"""STORYBOARD v2 - the EVIDENCE world: physical facts instead of literal re-enactment (see STORYBOARD_v2.md).
One palette for this world: black void or a dark desk, one hard practical light (top spot, desk lamp, swinging bulb),
paper in warm cream, red used only for the investigators' pencil / string / pins.

  tool_black   (1-8B)  the iron stove shaker alone on black, one top light, tagged as an exhibit: the recurring object
  board        (1-9B)  the detectives' board: floor plan, scene prints, red string... and an empty SUSPECT card
  file_card    (2-8B)  a faceless file print slides in; the typed card fills in his real name
  calendar     (2-13B) Oct 1941 (17 circled) flips back to September; red ticks count five weeks
  plan_route   (3-6B)  red pencil draws his route on the floor plan: kitchen, front door, front bedroom
  tool_swing   (3-7B)  callback: the same tool, now under a swinging bulb
  cutaway      (3-9B..11B, HERO LONG TAKE ~36 s) a cut-away model of the house; seasons pass outside, the attic glow
                       never goes out; a date card counts the days
  clock        (3-14A) courtroom clock: the minute hand sweeps less than two hours
No faces, no hands: people appear only as a faceless silhouette print.
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import house as H
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "out", "generated")
PRINTS = os.path.join(HERE, "..", "assets", "prints")
MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
MONOB = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
SERIFB = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
HAND = "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"

DUR = {"tool_black": 5.0, "tool_swing": 5.0, "board": 7.0, "file_card": 5.0, "calendar": 6.0,
       "plan_route": 6.0, "cutaway": 36.0, "clock": 5.0}
VARIANT_FOR = {k: k for k in DUR}
EXPOSURE = 0.0
PAPER = (236, 228, 208)
INK = (40, 34, 30)
RED = (170, 28, 22)


# ============================================================================ textures (PIL, generated per build)
def F(path, size):
    return ImageFont.truetype(path, size)


def _save(im, name):
    os.makedirs(GEN, exist_ok=True)
    p = os.path.join(GEN, name); im.save(p); return p


def paper_img(w, h, seed=0, tone=PAPER):
    rng = np.random.default_rng(seed)
    a = np.ones((h, w, 3)) * np.array(tone, float)
    a *= (1 - 0.05 * rng.random((h, w, 1)))
    yy, xx = np.mgrid[0:h, 0:w]
    a *= (1 - 0.10 * (((xx / w - 0.5) ** 2 + (yy / h - 0.5) ** 2) * 2.0))[..., None]     # edges a little darker
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def tex_card(lines, name, w=900, h=540, seed=1, ruled=True):
    """Index card: red header rule, blue lines, typed text. lines = [(text, font, size, colour, y)]"""
    im = paper_img(w, h, seed, (240, 236, 222)); d = ImageDraw.Draw(im)
    if ruled:
        d.line([(0, 110), (w, 110)], fill=(190, 60, 55), width=3)
        for y in range(160, h, 52):
            d.line([(0, y), (w, y)], fill=(150, 175, 205), width=2)
    for txt, fp, sz, col, y in lines:
        d.text((40, y), txt, font=F(fp, sz), fill=col)
    return _save(im, name)


def tex_plan():
    """Ground-floor plan of the house, drafting ink on cream paper (top of the sheet = back of the house)."""
    w, h = 2000, 1400
    im = paper_img(w, h, 7, (232, 224, 200)); d = ImageDraw.Draw(im)
    X0, Y0, X1, Y1 = 260, 150, 1740, 1250          # outer walls
    ln = lambda a, b, wd=6: d.line([a, b], fill=INK, width=wd)
    d.rectangle([X0, Y0, X1, Y1], outline=INK, width=14)
    mx = 1000; my = 700
    ln((mx, Y0), (mx, Y1), 8)                        # centre partition
    ln((X0, my), (mx - 150, my), 8); ln((mx + 140, my), (X1, my), 8)     # back/front rooms, with doorways
    ln((mx - 280, my), (mx - 280, Y1), 6)            # stair hall
    for k in range(13):                              # stairs
        y = Y1 - 40 - k * 38; ln((mx - 270, y), (mx - 10, y), 2)
    # door gaps (paper-coloured) + swing arcs
    for (a, b) in (((mx, 820), (mx, 960)), ((mx, 380), (mx, 520))):
        d.line([a, b], fill=(232, 224, 200), width=12)
    d.line([(1130, Y1), (1290, Y1)], fill=(232, 224, 200), width=16)       # front door
    d.arc([1130 - 160, Y1 - 160, 1130 + 160, Y1 + 160], 270, 360, fill=INK, width=3)
    d.line([(1450, Y0), (1600, Y0)], fill=(232, 224, 200), width=16)      # back door
    for (x, y0) in ((X0, 900), (X0, 300), (X1, 900), (X1, 300)):          # windows
        d.rectangle([x - 8, y0, x + 8, y0 + 150], fill=(232, 224, 200), outline=INK, width=3)
    # labels
    f = F(SERIFB, 46); fs = F(SERIF, 34)
    d.text((1180, 300), "KITCHEN", font=f, fill=INK); d.text((1180, 360), "range  ·  icebox", font=fs, fill=INK)
    d.text((1180, 960), "FRONT ROOM", font=f, fill=INK)
    d.text((340, 960), "FRONT BEDROOM", font=f, fill=INK)
    d.text((340, 300), "DINING", font=f, fill=INK); d.text((mx - 260, 760), "HALL", font=fs, fill=INK)
    d.text((1150, Y1 + 30), "FRONT DOOR", font=fs, fill=INK); d.text((1420, Y0 - 70), "BACK DOOR", font=fs, fill=INK)
    d.text((X0, 40), "W. MONCRIEFF PLACE  ·  GROUND FLOOR", font=F(SERIFB, 52), fill=INK)
    d.text((X1 - 300, 40), "scale 1/4 in = 1 ft", font=fs, fill=INK)
    # range and icebox symbols
    d.rectangle([1560, 420, 1700, 520], outline=INK, width=4); d.rectangle([1100, 170, 1200, 250], outline=INK, width=4)
    PLAN_PX.update(dict(w=w, h=h, kitchen=(1350, 470), hall_k=(mx + 70, 450), hall=(mx - 140, 610), front=(1210, 1120),
                        door_in=(mx + 60, 890), bed=(620, 1030), bed_door=(mx - 280, 1000)))
    return _save(im, "plan_ground.png")


PLAN_PX = {}


def tex_calendar(year, month, name, circle=None):
    import calendar
    w, h = 1000, 1300
    im = paper_img(w, h, month, (238, 232, 216)); d = ImageDraw.Draw(im)
    d.text((w // 2, 120), calendar.month_name[month].upper(), font=F(SERIFB, 110), fill=INK, anchor="mm")
    d.text((w // 2, 215), str(year), font=F(SERIF, 60), fill=INK, anchor="mm")
    x0, x1, y0, y1 = 40, 960, 300, 1250
    cw = (x1 - x0) / 7; chh = 70; rh = (y1 - y0 - chh) / 6
    for i, dn in enumerate(("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT")):
        d.text((x0 + cw * (i + 0.5), y0 + 35), dn, font=F(SERIFB, 34), fill=(150, 30, 26) if i == 0 else INK, anchor="mm")
    calendar.setfirstweekday(6)
    cells = {}
    for r, wk in enumerate(calendar.monthcalendar(year, month)):
        for i, day in enumerate(wk):
            cx, cy = x0 + cw * i, y0 + chh + rh * r
            d.rectangle([cx, cy, cx + cw, cy + rh], outline=(120, 110, 95), width=2)
            if day:
                d.text((cx + 14, cy + 8), str(day), font=F(SERIFB, 52), fill=(150, 30, 26) if i == 0 else INK)
                cells[day] = ((cx + cw / 2) / w, (cy + rh / 2) / h, cw / w, rh / h)
    if circle in cells:
        u, v, cu, cv = cells[circle]
        cx, cy = u * w, v * h
        for k in range(3):     # red pencil circle, drawn three times slightly off
            d.ellipse([cx - 62 + k * 3, cy - 52 - k * 2, cx + 64 - k, cy + 50 + k], outline=RED, width=7)
    return _save(im, name), cells


def tex_clock():
    w = 1024
    im = Image.new("RGB", (w, w), (234, 228, 210)); d = ImageDraw.Draw(im)
    c = w / 2
    d.ellipse([20, 20, w - 20, w - 20], outline=INK, width=10)
    for k in range(60):
        a = math.radians(k * 6); r0 = 455 if k % 5 else 420
        d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + 475 * math.sin(a), c - 475 * math.cos(a))], fill=INK, width=8 if k % 5 == 0 else 3)
    for k in range(1, 13):
        a = math.radians(k * 30)
        d.text((c + 350 * math.sin(a), c - 350 * math.cos(a)), str(k), font=F(SERIFB, 92), fill=INK, anchor="mm")
    d.text((c, c + 180), "CITY & COUNTY OF DENVER", font=F(SERIF, 30), fill=INK, anchor="mm")
    return _save(im, "clock_face.png")


def tex_silhouette():
    """Faceless file print: a grey head-and-shoulders silhouette against a height chart. No likeness."""
    w, h = 600, 760
    im = Image.new("RGB", (w, h), (200, 196, 186)); d = ImageDraw.Draw(im)
    for k in range(0, h, 38):
        d.line([(0, k), (w, k)], fill=(150, 146, 138), width=2)
        d.text((10, k + 2), str(76 - k // 38), font=F(MONO, 20), fill=(110, 106, 100))
    d.ellipse([200, 150, 400, 400], fill=(38, 36, 34))           # head
    d.rectangle([265, 380, 335, 470], fill=(38, 36, 34))          # neck
    d.ellipse([60, 440, 540, 960], fill=(38, 36, 34))            # shoulders
    d.rectangle([0, 0, w - 1, h - 1], outline=(240, 236, 226), width=26)
    return _save(im, "file_print.png")


# ============================================================================ building blocks
def img_mat(name, path, rough=0.8, bump=0.15, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.extension = 'EXTEND'
    L.new(t.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = rough
    if bump:
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 900
        bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.0004
        L.new(nz.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    if emit:
        L.new(t.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = emit
    return m


def sheet(name, path, w, h, loc, rot=(0, 0, 0), rough=0.8, curl=0.0):
    """A sheet of paper w x h (m), image mapped, optional slight curl along its long side."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=16, size=1, location=(0, 0, 0))
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1)
    bpy.ops.object.transform_apply(scale=True)
    if curl:
        for v in o.data.vertices:
            v.co.z += curl * ((2 * v.co.x / w) ** 2 + 0.6 * (2 * v.co.y / h) ** 4)
    o.location = loc; o.rotation_euler = rot
    o.data.materials.append(img_mat(name + "M", path, rough))
    return o


def black_void(floor=(0.012, 0.012, 0.013), rough=0.32):
    world_flat((0.0, 0.0, 0.0), 0.0)
    return box("VoidFloor", (0, 0, -0.01), (30, 30, 0.02), pbr("VoidFloor", floor, rough, 0.0, **{'Coat Weight': 0.3}))


def spot(loc, tgt, energy, size_deg=40, blend=0.35, col=(1.0, 0.86, 0.68), radius=0.03, name="Spot"):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.spot_size = math.radians(size_deg); l.spot_blend = blend
    l.color = col; l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt)
    return o


def polyline(name, pts, radius, mat_):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = radius; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p_, q in zip(sp.points, pts):
        p_.co = (q[0], q[1], q[2], 1)
    cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o); o.data.materials.append(mat_)
    return o


def path_at(pts, u):
    """Point at arc-length fraction u along a polyline."""
    pts = [Vector(p) for p in pts]; seg = [(b - a).length for a, b in zip(pts, pts[1:])]; L_ = sum(seg); s = u * L_
    for a, b, l in zip(pts, pts[1:], seg):
        if s <= l:
            return a.lerp(b, s / max(l, 1e-6)), (b - a).normalized()
        s -= l
    return pts[-1], (pts[-1] - pts[-2]).normalized()


def smooth(a, b, x):
    return ease(min(1.0, max(0.0, (x - a) / (b - a))))


def motes(n, center, size, seed=3, r=0.0012):
    """Dust motes drifting in a light beam (tiny emissive-free specks, they read in the spot)."""
    rng = np.random.default_rng(seed); src = None; out = []
    m = pbr("Mote", (0.9, 0.88, 0.82), 0.6)
    for k in range(n):
        p0 = Vector(center) + Vector(((rng.random() - 0.5) * size[0], (rng.random() - 0.5) * size[1], (rng.random() - 0.5) * size[2]))
        if src is None:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=p0); src = bpy.context.active_object; src.data.materials.append(m); o = src
        else:
            o = instance(src, p0)
        out.append((o, p0, rng.random() * 6.28, 0.3 + rng.random()))
    return out


def drift_motes(ms, sec, amp=0.03):
    for o, p0, ph_, sp in ms:
        o.location = p0 + Vector((amp * math.sin(0.4 * sp * sec + ph_), amp * math.cos(0.3 * sp * sec + 2 * ph_), -0.01 * sp * sec + 0.6 * amp * math.sin(0.2 * sec + ph_)))


def flat_tool(name):
    """house.shaker_tool keeps its first part's rotation after the join: bake it, so the tool lies along X."""
    o = H.shaker_tool(name)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    bpy.context.view_layer.update()
    from mathutils import Vector as V
    zmin = min((o.matrix_world @ V(b)).z for b in o.bound_box); o.location.z -= zmin
    return o


def desk(size=(1.6, 0.9), z=0.0, tone=(0.11, 0.06, 0.03)):
    return box("Desk", (0, 0, z - 0.02), (size[0], size[1], 0.04), wood("DeskWood", tuple(c * 0.5 for c in tone), tone, scale=(0.4, 8, 8), rough=0.45, coat=0.4))


# ============================================================================ build
def build(variant=None):
    c = {"v": variant}
    s = bpy.context.scene
    s.view_settings.exposure = 0.0
    globals()["_b_" + variant](c)
    return c


def _b_tool_black(c, swing=False):
    black_void()
    tool = flat_tool("StoveTool"); tool.location = (0, 0, 0.0); tool.rotation_euler = (0, 0, math.radians(-18))
    c["tool"] = tool
    # an evidence tag tied to the loop with red string
    tag = tex_card([("EXHIBIT  4", MONOB, 92, INK, 18), ("found: front bedroom", MONO, 54, INK, 170),
                    ("10 - 17 - 41", MONO, 54, INK, 240)], "tag_tool.png", w=700, h=340, ruled=False)
    lp = Vector((-0.35, 0, 0.0)); lp.rotate(tool.rotation_euler)
    tg = sheet("Tag", tag, 0.085, 0.042, lp + Vector((-0.07, -0.06, 0.0015)), (0, 0, math.radians(-35)), curl=0.002)
    polyline("TagString", [lp + Vector((0.0, 0.0, 0.006)), lp + Vector((-0.03, -0.035, 0.004)), tg.location + Vector((0.03, 0.012, 0.0025))], 0.0008, pbr("RedString", (0.45, 0.03, 0.02), 0.7))
    if swing:
        c["bulb"] = H.point((0, 0, 0.95), 260, (1.0, 0.74, 0.46), 0.02)
        c["bulb_glass"] = cyl("Bulb", (0, 0, 1.0), 0.03, 0.06, emissive("BulbE", (1.0, 0.7, 0.4), 30), 16)
        c["cord"] = cyl("Cord", (0, 0, 1.6), 0.003, 1.2, H.mat("black"), 6)
    else:
        spot((0.03, 0.0, 1.5), (-0.05, 0.0, 0.0), 300, 40, 0.3, radius=0.04)
        rim = spot((-0.2, 1.4, 0.35), (0.0, 0.0, 0.02), 25, 30, 0.4, col=(0.9, 0.92, 1.0)); rim.data.shadow_soft_size = 0.2
        # no haze here: the side-lit cone flared at the end of the arc; the motes carry the beam
        c["motes"] = motes(70, (0, 0, 0.45), (0.5, 0.5, 0.8))


def _b_tool_swing(c):
    _b_tool_black(c, swing=True)
    haze((0, 0, 0.6), (1.6, 1.6, 1.2), density=0.015, color=(1, 1, 1), anis=0.4)


def _b_board(c):
    world_flat((0.0, 0.0, 0.0), 0.0)
    wall = box("Wall", (0, 0.03, 1.2), (5, 0.04, 3), pbr("OfficeWall", (0.12, 0.13, 0.11), 0.85))
    cork_m = bpy.data.materials.new("Cork"); cork_m.use_nodes = True
    N = cork_m.node_tree.nodes; L = cork_m.node_tree.links; p = N["Principled BSDF"]
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 300; nz.inputs['Detail'].default_value = 8
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.18, 0.1, 0.05, 1); cr.color_ramp.elements[1].color = (0.42, 0.27, 0.14, 1)
    L.new(nz.outputs['Fac'], cr.inputs[0]); L.new(cr.outputs[0], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.9
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.4; L.new(nz.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    box("Cork", (0, 0, 1.45), (1.5, 0.02, 0.95), cork_m)
    box("Frame", (0, 0.008, 1.45), (1.58, 0.015, 1.03), H.mat("oak"))
    R90 = (math.radians(90), 0, 0); y = -0.012
    pin_m = pbr("PinRed", (0.55, 0.03, 0.02), 0.3)
    plan = tex_plan()
    pw, ph_ = 0.62, 0.434
    sheet("Plan", plan, pw, ph_, (0.0, y, 1.45), R90, curl=0.004)
    def plan_pt(key):      # a plan pixel -> world point on the pinned plan
        px, py = PLAN_PX[key]; return Vector(((px / PLAN_PX["w"] - 0.5) * pw, y - 0.004, 1.45 + (0.5 - py / PLAN_PX["h"]) * ph_))
    prints = [("aftermath", (-0.56, 1.72), "bed"), ("tool", (-0.58, 1.2), "bed"), ("latch", (0.56, 1.74), "kitchen"),
              ("hall", (0.57, 1.18), "hall")]
    c["prints"] = []
    for k, (nm, (x, z), room) in enumerate(prints):
        o = sheet("Print_" + nm, os.path.join(PRINTS, nm + ".jpg"), 0.24, 0.186, (x, y - 0.002 * k, z), R90, rough=0.35, curl=0.002)
        o.rotation_euler = (math.radians(90), math.radians((-3, 2, 4, -2)[k]), 0)
        pin = Vector((x, y - 0.012, z + 0.075)); cyl("Pin", pin, 0.006, 0.012, pin_m, 12, rot=R90)
        polyline("String%d" % k, [pin, plan_pt(room)], 0.0011, pin_m)
        cyl("Pin", plan_pt(room) + Vector((0, -0.004, 0)), 0.006, 0.012, pin_m, 12, rot=R90)
        c["prints"].append(o)
    # index cards: the facts, and the empty one
    card1 = tex_card([("FORCED ENTRY", MONOB, 64, INK, 30), ("none found.", MONO, 56, INK, 170), ("doors & windows locked", MONO, 50, INK, 222)], "card_entry.png")
    card2 = tex_card([("STRUGGLE", MONOB, 64, INK, 30), ("more than one room", MONO, 56, INK, 170)], "card_struggle.png")
    card3 = tex_card([("SUSPECT", MONOB, 72, (150, 28, 22), 26), ("", MONO, 56, INK, 170)], "card_suspect.png")
    sheet("Card1", card1, 0.15, 0.09, (-0.22, y - 0.002, 1.08), (math.radians(90), math.radians(2), 0))
    sheet("Card2", card2, 0.15, 0.09, (0.0, y - 0.002, 1.09), (math.radians(90), math.radians(-3), 0))
    c["suspect"] = sheet("Card3", card3, 0.15, 0.09, (0.27, y - 0.004, 1.06), (math.radians(90), math.radians(1.5), 0))
    cyl("Pin", (0.27, y - 0.014, 1.095), 0.006, 0.012, pin_m, 12, rot=R90)
    for (x, z) in ((-0.22, 1.115), (0.0, 1.125)):
        cyl("Pin", (x, y - 0.014, z), 0.006, 0.012, pin_m, 12, rot=R90)
    # the desk in front and the desk lamp that lights the board from low right
    box("DeskTop", (0, -0.45, 0.76), (2.0, 0.8, 0.04), H.mat("oak"))
    shade = cyl("LampShade", (0.75, -0.35, 1.05), 0.09, 0.12, pbr("LampGreen", (0.05, 0.16, 0.08), 0.3, 0.2), 24, rot=(math.radians(-60), 0, 0))
    spot((0.72, -0.5, 1.02), (0.05, 0.0, 1.35), 160, 70, 0.6, radius=0.05)
    H.point((0.0, -1.5, 2.2), 6, (0.8, 0.85, 1.0), 0.5)      # a whisper of cool room light
    haze((0, -0.6, 1.4), (2.4, 1.4, 1.6), density=0.01, color=(1, 1, 1), anis=0.4)


def _b_file_card(c):
    world_flat((0.0, 0.0, 0.0), 0.0)
    desk((2.0, 1.2))
    folder_m = pbr("Manila", (0.62, 0.48, 0.28), 0.8)
    box("Folder", (-0.1, 0.02, 0.002), (0.48, 0.32, 0.004), folder_m, rot=(0, 0, math.radians(3)))
    card = tex_card([("DENVER POLICE  -  RECORD", MONOB, 50, INK, 30), ("Name given:", MONO, 46, INK, 140),
                     ("Identified as:", MONO, 46, INK, 260), ("Arrested: 7-30-42", MONO, 46, INK, 440)], "card_id.png", ruled=False)
    cd = sheet("IDCard", card, 0.20, 0.12, (-0.18, 0.0, 0.006), (0, 0, math.radians(2)))
    # the false name: struck through with a typed row of X
    blk = pbr("TypeInk", (0.03, 0.03, 0.035), 0.6)
    c["xs"] = text_obj("XRow", "XXXXXXXXXXXX", (-0.19, 0.0215, 0.0062), 0.011, blk, rot=(0, 0, math.radians(2)), extrude=0.0, font_path=MONOB, align='LEFT')
    c["name"] = text_obj("Name", "", (-0.265, -0.0215, 0.0062), 0.0125, blk, rot=(0, 0, math.radians(2)), extrude=0.0, font_path=MONOB, align='LEFT')
    c["photo"] = sheet("FilePrint", tex_silhouette(), 0.10, 0.127, (0.5, 0.02, 0.008), (0, 0, 0), rough=0.3, curl=0.002)
    spot((0.0, 0.05, 1.3), (0.0, 0.0, 0.0), 120, 50, 0.6, radius=0.08)
    cyl("Shade", (0, 0.05, 1.42), 0.22, 0.1, pbr("ShadeMetal", (0.12, 0.14, 0.12), 0.4, 0.8), 32)
    haze((0, 0, 0.7), (1.6, 1.2, 1.4), density=0.012, color=(1, 1, 1), anis=0.5)


def _b_calendar(c):
    world_flat((0.0, 0.0, 0.0), 0.0)
    wp = H.wallpaper("CalWall", (0.62, 0.55, 0.42), (0.55, 0.2, 0.18), (0.3, 0.38, 0.22), seed=4, scale=6.0)
    box("Wall", (0, 0.02, 1.5), (3, 0.04, 3), wp)
    box("Wainscot", (0, 0.0, 0.5), (3, 0.03, 1.0), H.mat("oak"))
    sep, sep_cells = tex_calendar(1941, 9, "cal_sep.png")
    octp, _ = tex_calendar(1941, 10, "cal_oct.png", circle=17)
    head = paper_img(1000, 520, 9, (225, 205, 170)); d = ImageDraw.Draw(head)
    d.rectangle([30, 30, 970, 490], outline=(120, 40, 30), width=8)
    d.text((500, 170), "1941", font=F(SERIFB, 150), fill=(120, 40, 30), anchor="mm")
    d.text((500, 330), "ICE  ·  COAL  ·  FUEL OIL", font=F(SERIF, 56), fill=INK, anchor="mm")
    d.text((500, 410), "Denver, Colo.", font=F(SERIF, 44), fill=INK, anchor="mm")
    hp = _save(head, "cal_head.png")
    W, Hh = 0.30, 0.39; top = 1.55
    R90 = (math.radians(90), 0, 0)
    sheet("CalHead", hp, W, 0.156, (0, -0.002, top + 0.078), R90)
    sheet("CalSep", sep, W, Hh, (0, -0.003, top - Hh / 2), R90)
    # the October page hangs from a hinge at the top edge, so it can flip up and over
    hinge = bpy.data.objects.new("OctHinge", None); bpy.context.collection.objects.link(hinge); hinge.location = (0, -0.006, top)
    pg = sheet("CalOct", octp, W, Hh, (0, 0, -Hh / 2), R90, curl=0.0)
    pg.parent = hinge
    bd = pg.modifiers.new("bend", 'SIMPLE_DEFORM'); bd.deform_method = 'BEND'; bd.deform_axis = 'X'; bd.angle = 0.0
    c["hinge"], c["oct"], c["bend"] = hinge, pg, bd
    cyl("Nail", (0, -0.01, top + 0.17), 0.004, 0.02, H.mat("chrome"), 8, rot=R90)
    # red pencil ticks, one per day from Sept 12 to Sept 30 (five weeks before October 17)
    red = pbr("RedPencil", (0.5, 0.04, 0.03), 0.7)
    c["ticks"] = []
    for day in range(12, 31):
        u, v, cu, cv = sep_cells[day]
        p = Vector(((u - 0.5) * W, -0.0045, top - v * Hh))
        o = box("Tick%d" % day, p, (cu * W * 0.75, 0.0006, 0.0025), red, rot=(0, math.radians(-38), 0))
        o.scale = (0.0, 1, 1); c["ticks"].append(o)
    u, v, cu, cv = sep_cells[12]
    c["mark"] = text_obj("FiveWeeks", "five weeks", (0.075, -0.0047, top - 0.88 * Hh), 0.028, red, rot=R90, extrude=0.0, font_path=HAND)
    c["mark"].scale = (0, 0, 0)
    # raking late light from a window at left, through mullions (gobo bars) + a soft fill
    spot((-1.6, -0.9, 1.9), (0.0, 0.0, 1.35), 900, 22, 0.15, col=(1.0, 0.8, 0.58), radius=0.02)
    for k in range(2):
        box("Mullion", (-0.8, -0.5, 1.62 + 0.0 * k), (0.03, 0.03, 0.7), H.mat("black"), rot=(0, 0, math.radians(-30)))
    box("MullionH", (-0.8, -0.5, 1.62), (0.6, 0.03, 0.03), H.mat("black"), rot=(0, 0, math.radians(-30)))
    area_light((0.6, -1.4, 1.4), (math.radians(80), 0, math.radians(20)), 1.0, 12, (0.85, 0.9, 1.0))
    c["motes"] = motes(50, (-0.4, -0.3, 1.5), (0.8, 0.5, 0.6), seed=8)
    haze((-0.4, -0.4, 1.5), (2.2, 1.4, 1.4), density=0.008, color=(1, 1, 1), anis=0.5)


def _b_plan_route(c):
    world_flat((0.0, 0.0, 0.0), 0.0)
    desk((2.0, 1.4))
    plan = tex_plan(); pw, ph_ = 0.62, 0.434
    sheet("Plan", plan, pw, ph_, (0, 0, 0.002), (0, 0, math.radians(4)), curl=0.003)
    rz = math.radians(4)
    def P2(key):
        px, py = PLAN_PX[key]; v = Vector(((px / PLAN_PX["w"] - 0.5) * pw, (0.5 - py / PLAN_PX["h"]) * ph_, 0.0058)); v.rotate(bpy.context.scene.objects["Plan"].rotation_euler); return v
    route = [P2(k) for k in ("kitchen", "hall_k", "hall", "door_in", "front", "door_in", "bed_door", "bed")]
    c["route_pts"] = route
    red = pbr("RedPencil", (0.5, 0.035, 0.025), 0.75)
    ln = polyline("Route", route, 0.0012, red); ln.data.bevel_factor_mapping_end = 'SPLINE'; ln.data.bevel_factor_end = 0.0
    c["route"] = ln
    # an X where it ends
    end = route[-1]
    c["x"] = [box("X%d" % k, end, (0.03, 0.002, 0.0012), red, rot=(0, 0, math.radians(45 + 90 * k))) for k in range(2)]
    for o in c["x"]:
        o.scale = (0, 1, 1)
    # the red pencil itself, riding the line tip (no hand)
    pen = join([cyl("PencilBody", (0, 0, 0.09), 0.0045, 0.16, pbr("PencilRed", (0.55, 0.05, 0.03), 0.5), 6),
                cyl("PencilWood", (0, 0, 0.005), 0.0035, 0.012, pbr("PencilWood", (0.75, 0.55, 0.35), 0.7), 12)], "Pencil")
    c["pencil"] = pen
    # props at the edge of frame: the iron tool (recurring), a pair of reading glasses (detective), a cup
    tool = flat_tool("StoveToolDesk"); tool.location = (0.18, -0.36, 0.0); tool.rotation_euler = (0, 0, math.radians(8))
    cyl("Cup", (-0.42, 0.24, 0.045), 0.04, 0.09, pbr("CupEnamel", (0.75, 0.73, 0.68), 0.3), 24)
    spot((-0.5, 0.35, 0.9), (0.0, 0.0, 0.0), 160, 60, 0.6, radius=0.06)
    area_light((0.6, -0.8, 1.2), (math.radians(40), 0, math.radians(35)), 1.0, 6, (0.85, 0.9, 1.0))


def _b_clock(c):
    black_void((0.02, 0.016, 0.012))
    box("Panel", (0, 0.05, 1.9), (3.0, 0.04, 3.0), wood("CourtPanel", (0.05, 0.025, 0.012), (0.15, 0.08, 0.04), scale=(0.3, 6, 6), rough=0.4, coat=0.4))
    face = img_mat("ClockFace", tex_clock(), 0.4, 0.0)
    cyl("ClockRim", (0, 0.0, 2.2), 0.34, 0.06, wood("ClockRim", (0.04, 0.02, 0.01), (0.12, 0.06, 0.03), rough=0.3, coat=0.8), 64, rot=(math.radians(90), 0, 0))
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=0.3, fill_type='NGON', location=(0, -0.031, 2.2), rotation=(math.radians(90), 0, 0))
    fc = bpy.context.active_object; fc.data.materials.append(face)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.unwrap(); bpy.ops.object.mode_set(mode='OBJECT')
    import bmesh
    bm = bmesh.new(); bm.from_mesh(fc.data); uv = bm.loops.layers.uv.verify()
    for f_ in bm.faces:
        for l in f_.loops:
            co = l.vert.co; l[uv].uv = (0.5 + co.x / 0.6, 0.5 + co.y / 0.6)
    bm.to_mesh(fc.data); bm.free()
    blk = pbr("Hands", (0.02, 0.02, 0.02), 0.4, 0.6)
    def hand_(name, L_, w_):
        piv = bpy.data.objects.new(name + "Piv", None); bpy.context.collection.objects.link(piv); piv.location = (0, -0.036, 2.2)
        hd = box(name, (0, 0, L_ / 2 - 0.03), (w_, 0.003, L_), blk); hd.parent = piv
        return piv
    c["min"] = hand_("MinHand", 0.27, 0.012); c["hour"] = hand_("HourHand", 0.18, 0.018)
    cyl("Boss", (0, -0.04, 2.2), 0.014, 0.006, blk, 16, rot=(math.radians(90), 0, 0))
    spot((0.0, -1.1, 3.9), (0.0, 0.0, 2.1), 900, 24, 0.3, radius=0.03)
    spot((-0.9, -0.6, 1.0), (0.0, 0.0, 2.1), 30, 40, 0.6, col=(0.85, 0.9, 1.0), radius=0.3)
    haze((0, -0.8, 2.4), (2.4, 1.6, 2.6), density=0.01, color=(1, 1, 1), anis=0.6)


# ---------------------------------------------------------------------------- the cut-away model (hero long take)
MONTHS = [("OCTOBER", 1941), ("NOVEMBER", 1941), ("DECEMBER", 1941), ("JANUARY", 1942), ("FEBRUARY", 1942),
          ("MARCH", 1942), ("APRIL", 1942), ("MAY", 1942), ("JUNE", 1942), ("JULY", 1942)]


def _b_cutaway(c):
    world_flat((0.0, 0.0, 0.0), 0.0)
    box("Floor", (0, 0, -0.01), (40, 40, 0.02), pbr("StudioFloor", (0.01, 0.01, 0.011), 0.4))
    plinth = box("Plinth", (0, 0, 0.35), (2.2, 1.6, 0.7), pbr("Plinth", (0.03, 0.03, 0.032), 0.5), bevel=0.01)
    Z = 0.7
    c["ground_m"] = pbr("Ground", (0.3, 0.2, 0.08), 0.9)
    box("Ground", (0, 0, Z + 0.01), (2.18, 1.58, 0.02), c["ground_m"])
    plas = pbr("ModelPlaster", (0.62, 0.55, 0.42), 0.8); wood_ = H.mat("oak"); roof = pbr("ModelRoof", (0.12, 0.1, 0.09), 0.8)
    # house 0.9 (x) by 1.0 (y), front (-y) cut away; floors at 0.0, 0.3; eave 0.6; ridge 0.82 (model metres)
    W, D, F2m, EA, RI = 0.9, 1.0, 0.3, 0.6, 0.84
    b = Z + 0.02
    sec_m = pbr("CutFace", (0.75, 0.7, 0.6), 0.9)     # the cut faces read as a clean light section
    brk = model_brick()
    wp1 = H.wallpaper("ModelPaper1", (0.62, 0.55, 0.42), (0.55, 0.2, 0.18), (0.3, 0.38, 0.22), seed=2, scale=40.0)
    wp2 = H.wallpaper("ModelPaper2", (0.5, 0.56, 0.5), (0.6, 0.5, 0.3), (0.3, 0.38, 0.22), seed=5, scale=40.0)
    for (nm, loc, sz) in (("BackWall", (0, D / 2, b + EA / 2), (W, 0.03, EA)), ("SideL", (-W / 2, 0, b + EA / 2), (0.03, D, EA)),
                          ("SideR", (W / 2, 0, b + EA / 2), (0.03, D, EA))):
        box(nm, loc, sz, brk)
        inset = Vector((0, -0.016, 0)) if nm == "BackWall" else Vector((0.016 if nm == "SideL" else -0.016, 0, 0))
        for k, (z0, hh, m_) in enumerate(((0.02, F2m - 0.02, wp1), (F2m + 0.025, EA - F2m - 0.025, wp2))):
            box(nm + "Paper%d" % k, Vector((loc[0], loc[1], b + z0 + hh / 2)) + inset, (sz[0] if nm == "BackWall" else 0.002, 0.002 if nm == "BackWall" else sz[1], hh), m_)
    for (x, z) in ((-0.45, 0.15), (0.45, 0.15), (-0.45, 0.45), (0.45, 0.45)):         # windows in the side walls
        box("ModelWin", (x, -0.1, b + z), (0.035, 0.16, 0.12), pbr("ModelGlass", (0.02, 0.02, 0.025), 0.1))
    box("Floor1", (0, 0, b + 0.01), (W, D, 0.02), wood_); box("Floor2", (0, 0, b + F2m), (W, D, 0.025), sec_m)
    box("Ceil2", (0, 0, b + EA), (W, D, 0.025), sec_m)
    box("Part1", (0, 0.05, b + F2m / 2), (0.02, D * 0.9, F2m), plas); box("Part2", (-0.12, 0.05, b + F2m + 0.15), (0.02, D * 0.9, F2m), plas)
    # gable roof (cut at the front) + gable end at the back
    import bmesh
    for sg in (-1, 1):
        ang = math.atan2(RI - EA, W / 2)
        bx = box("Roof%d" % sg, (sg * W / 4, 0.0, b + (EA + RI) / 2), (W / 2 / math.cos(ang) + 0.06, D + 0.08, 0.025), roof, rot=(0, sg * ang, 0))
    me = bpy.data.meshes.new("Gable"); me.from_pydata([(-W / 2, D / 2, b + EA), (W / 2, D / 2, b + EA), (0, D / 2, b + RI)], [], [(0, 1, 2)])
    gb = bpy.data.objects.new("Gable", me); bpy.context.collection.objects.link(gb); gb.data.materials.append(plas)
    gb.modifiers.new("s", 'SOLIDIFY').thickness = 0.03
    # tiny rooms: beds, table, range, stairs
    for (n_, loc, sz, m_) in (("Bed", (-0.28, -0.2, b + 0.05), (0.18, 0.3, 0.05), pbr("Spread", (0.5, 0.42, 0.33), 0.9)),
                              ("Table", (0.25, 0.25, b + 0.08), (0.16, 0.12, 0.01), wood_),
                              ("Range", (0.36, 0.42, b + 0.05), (0.1, 0.07, 0.08), H.mat("iron")),
                              ("Bed2", (-0.3, -0.15, b + F2m + 0.05), (0.18, 0.3, 0.05), pbr("Spread2", (0.4, 0.4, 0.45), 0.9))):
        box(n_, loc, sz, m_)
    for k in range(9):
        box("Step", (0.08, -0.25 + k * 0.05, b + 0.02 + k * 0.032), (0.12, 0.05, 0.012), wood_)
    # the closet and the hatch, the attic boards, the hot plate and the glow
    box("Closet", (-0.18, 0.05, b + F2m + 0.135), (0.1, 0.12, 0.25), plas)
    for k in range(6):
        box("Board", (-0.32 + k * 0.025, 0.05, b + EA + 0.02), (0.022, 0.36, 0.006), H.mat("raw"))
    c["hotplate"] = box("HotPlate", (-0.25, 0.12, b + EA + 0.03), (0.03, 0.03, 0.01), H.mat("iron"))
    c["glow"] = H.point((-0.25, 0.1, b + EA + 0.06), 4.0, (1.0, 0.62, 0.3), 0.01)
    c["coil"] = cyl("Coil", (-0.25, 0.12, b + EA + 0.0365), 0.009, 0.002, emissive("CoilE", (1.0, 0.35, 0.1), 6), 16)
    # lit rooms below (on while someone lives here)
    c["room_lights"] = [H.point((0.25, 0.2, b + 0.2), 0.5, (1.0, 0.75, 0.48), 0.02), H.point((-0.25, -0.1, b + 0.2), 0.4, (1.0, 0.75, 0.48), 0.02)]
    # outside: two model trees, the street lamp; snow motes
    c["canopies"] = []
    for (x, y) in ((-0.85, -0.45), (0.8, -0.5)):
        cyl("Trunk", (x, y, Z + 0.15), 0.012, 0.28, pbr("Bark", (0.12, 0.08, 0.05), 0.9), 8)
        # foliage as a lumpy cluster (model-railway style clump foliage): several noisy blobs, leaf-scale bump
        tx = bpy.data.textures.get("FoliageClouds") or bpy.data.textures.new("FoliageClouds", 'CLOUDS')
        tx.noise_scale = 0.025; tx.noise_depth = 2
        mt = foliage_mat("Canopy%d" % len(c["canopies"]))
        rng2 = np.random.default_rng(len(c["canopies"]) + 11); blobs = []
        for k in range(7):
            off = Vector(((rng2.random() - 0.5) * 0.16, (rng2.random() - 0.5) * 0.16, (rng2.random() - 0.3) * 0.14))
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.06 + 0.03 * rng2.random(), location=Vector((x, y, Z + 0.34)) + off)
            bl = bpy.context.active_object; d_ = bl.modifiers.new("d", 'DISPLACE'); d_.texture = tx; d_.strength = 0.035
            bpy.ops.object.modifier_apply(modifier="d"); blobs.append(bl)
        cp = join(blobs, "Canopy"); cp.data.materials.append(mt)
        bpy.context.scene.cursor.location = (x, y, Z + 0.3); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        c["canopies"].append(cp)
    rng = np.random.default_rng(4); snow_m = pbr("Snow", (0.9, 0.9, 0.92), 0.7)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.005, location=(0, 0, -5)); s0 = bpy.context.active_object; s0.data.materials.append(snow_m)
    c["snow"] = [(instance(s0, (0, 0, -5)), Vector(((rng.random() - 0.5) * 2.1, (rng.random() - 0.5) * 1.5, rng.random()))) for _ in range(220)]
    c["snow_cap"] = box("SnowCap", (0, 0, Z + 0.021), (2.18, 1.58, 0.004), snow_m)
    for sg in (-1, 1):
        ang = math.atan2(RI - EA, W / 2)
        o = box("RoofSnow%d" % sg, (sg * W / 4, 0.0, b + (EA + RI) / 2 + 0.016), (W / 2 / math.cos(ang) + 0.06, D + 0.08, 0.006), snow_m, rot=(0, sg * ang, 0))
        c.setdefault("roof_snow", []).append(o)
    # the museum-style date card at the plinth front (facts written into the set)
    paper_m = pbr("CardPaper", (0.85, 0.82, 0.74), 0.8)
    box("DateCard", (0.0, -0.81, 0.45), (0.62, 0.006, 0.2), paper_m)
    ink = pbr("CardInk", (0.03, 0.025, 0.02), 0.6)
    c["month"] = text_obj("Month", "OCTOBER 1941", (0.0, -0.815, 0.48), 0.06, ink, font_path=SERIFB)
    c["days"] = text_obj("Days", "day 1", (0.0, -0.815, 0.39), 0.04, pbr("CardRed", (0.5, 0.05, 0.03), 0.6), font_path=SERIF)
    # light: a key from high front-left whose colour and angle follow the season, + a cool rim behind
    c["key"] = spot((-2.0, -2.2, 3.0), (0, 0, 1.0), 900, 40, 0.5, radius=0.2)
    rim = spot((1.5, 2.5, 2.2), (0, 0, 1.0), 300, 40, 0.5, col=(0.8, 0.86, 1.0), radius=0.3)
    c["sky"] = box("Sky", (0, 3.2, 1.6), (8, 0.05, 4), emissive("SkyCard", (0.2, 0.25, 0.35), 0.15))


def foliage_mat(name):
    """Clump foliage: fine noise bump, colour varied per clump, a little translucency."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 400; nz.inputs['Detail'].default_value = 6
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.8; L.new(nz.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Roughness'].default_value = 0.9
    try:
        p.inputs['Subsurface Weight'].default_value = 0.15
    except Exception:
        pass
    return m


def model_brick():
    """Brick at model scale: a brick-tex procedural (red-brown, mortar), so the model reads as the real house."""
    m = bpy.data.materials.new("ModelBrick"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    bt = N.new("ShaderNodeTexBrick"); bt.inputs['Scale'].default_value = 25.0
    bt.inputs['Color1'].default_value = (0.33, 0.12, 0.07, 1); bt.inputs['Color2'].default_value = (0.24, 0.09, 0.05, 1)
    bt.inputs['Mortar'].default_value = (0.5, 0.47, 0.42, 1); bt.inputs['Mortar Size'].default_value = 0.012
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['Object'], bt.inputs['Vector'])
    L.new(bt.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.85
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.3; L.new(bt.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def season(u):
    """Month index (0..9) and blend weights for autumn / winter / summer over the hero take (u = 0..1)."""
    m = min(9, int(u * 10))
    w_win = smooth(0.12, 0.2, u) * (1 - smooth(0.52, 0.6, u))
    w_sum = smooth(0.6, 0.75, u)
    return m, w_win, w_sum


# ============================================================================ animation
def anim_tool(c, t):
    sec = t * DUR["tool_black"]
    if "motes" in c:
        drift_motes(c["motes"], sec)


def anim_tool_swing(c, t):
    sec = t * DUR["tool_swing"]
    a = math.radians(14) * math.cos(2 * math.pi * sec / 2.6) * (1 - 0.15 * t)        # damped pendulum, ~2.6 s period
    p = Vector((math.sin(a) * 0.9, 0.25 * math.sin(a) * 0.4, 1.9 - math.cos(a) * 0.9))
    c["bulb"].location = p; c["bulb_glass"].location = p + Vector((0, 0, 0.03))
    c["cord"].location = (Vector((0, 0, 1.9)) + p) / 2; c["cord"].rotation_euler = (0, -a, 0); c["cord"].scale = (1, 1, 0.9 / 1.2)
    c["bulb"].data.energy = 260 * (1 + 0.06 * math.sin(31 * sec) * math.sin(7 * sec))


def anim_board(c, t):
    sec = t * DUR["board"]
    # the last print was just pinned: it still sways on its pin, settling
    o = c["prints"][2]; o.rotation_euler.y = math.radians(4 + 3.5 * math.exp(-0.7 * sec) * math.sin(4.2 * sec))


def anim_file(c, t):
    sec = t * DUR["file_card"]
    u = smooth(0.0, 1.6, sec)
    c["photo"].location = Vector((0.55, 0.06, 0.008)).lerp(Vector((0.1, 0.0, 0.0085)), u)
    c["photo"].rotation_euler = (0, 0, math.radians(-14 + 18 * u))
    full = "THEODORE CONEYS"
    n = int(max(0.0, min(1.0, (sec - 2.0) / 2.2)) * len(full) + 0.001)
    c["name"].data.body = full[:n]


def anim_calendar(c, t):
    sec = t * DUR["calendar"]
    u = smooth(1.0, 2.6, sec)
    c["hinge"].rotation_euler = (math.radians(-172 * u), 0, 0)
    c["bend"].angle = math.radians(-50) * math.sin(math.pi * u)
    if "motes" in c:
        drift_motes(c["motes"], sec)
    nt = len(c["ticks"])
    for k, o in enumerate(c["ticks"]):
        a = 2.8 + k * (2.4 / nt)
        o.scale = (smooth(a, a + 0.15, sec), 1, 1)
    s_ = smooth(5.2, 5.8, sec); c["mark"].scale = (s_, s_, s_)


def anim_plan(c, t):
    sec = t * DUR["plan_route"]
    u = smooth(0.4, 4.8, sec)
    c["route"].data.bevel_factor_end = max(0.001, u)
    p, d = path_at(c["route_pts"], u)
    side = Vector((-d.y, d.x, 0))
    c["pencil"].location = p + Vector((0, 0, -0.0005))
    c["pencil"].rotation_euler = (0, 0, 0)
    tilt = Vector((0.35, -0.5, 1.0)).normalized()          # held from the lower right
    c["pencil"].rotation_mode = 'QUATERNION'; c["pencil"].rotation_quaternion = Vector((0, 0, 1)).rotation_difference(tilt)
    c["pencil"].location += Vector((0, 0, 0.002 * math.sin(40 * sec) * (0 < u < 1)))
    if sec > 5.0:
        c["pencil"].location += Vector((0.06, -0.08, 0.05)) * smooth(5.0, 5.6, sec)
    for k, o in enumerate(c["x"]):
        o.scale = (smooth(4.9 + 0.3 * k, 5.2 + 0.3 * k, sec), 1, 1)


def anim_cutaway(c, t):
    sec = t * DUR["cutaway"]
    m, w_win, w_sum = season(t)
    name, yr = MONTHS[m]
    c["month"].data.body = f"{name} {yr}"
    day = 1 + int(t * 286)
    c["days"].data.body = f"day {day}" if day < 286 else "day 286  ·  more than nine months"
    # ground and trees through the seasons
    aut, win, sumr = Vector((0.3, 0.19, 0.07)), Vector((0.8, 0.8, 0.82)), Vector((0.12, 0.22, 0.06))
    g = aut.lerp(win, w_win).lerp(sumr, w_sum)
    c["ground_m"].node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (*g, 1)
    leaf = (1 - smooth(0.06, 0.16, t)) + smooth(0.62, 0.74, t)
    col = Vector((0.5, 0.22, 0.05)).lerp(Vector((0.1, 0.25, 0.05)), w_sum)
    for cp in c["canopies"]:
        cp.scale = (max(0.001, leaf),) * 3
        cp.active_material.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (*col, 1)
    c["snow_cap"].scale = (1, 1, max(0.001, w_win)); c["snow_cap"].hide_render = w_win < 0.02
    for o in c["roof_snow"]:
        o.hide_render = w_win < 0.3
    fall = smooth(0.12, 0.16, t) * (1 - smooth(0.5, 0.55, t))
    for o, p0 in c["snow"]:
        if fall <= 0:
            o.location = (0, 0, -5); continue
        z = (p0.z - sec * 0.08) % 1.0
        o.location = (p0.x + 0.02 * math.sin(sec + p0.y * 9), p0.y, 0.72 + z * 1.2)
    # who lives here: lights on with Helen (first weeks), then the house is dark; only the attic glows
    on = 1 - smooth(0.08, 0.12, t)
    for k, l in enumerate(c["room_lights"]):
        l.data.energy = (0.5 - 0.1 * k) * on
    c["glow"].data.energy = 4.0 * (1 + 0.15 * math.sin(9 * sec) * math.sin(2.3 * sec))
    # the key follows the seasons: low warm autumn, pale winter, high summer
    kc = Vector((1.0, 0.78, 0.55)).lerp(Vector((0.85, 0.9, 1.0)), w_win).lerp(Vector((1.0, 0.93, 0.8)), w_sum)
    c["key"].data.color = kc; c["key"].data.energy = 900 * (1 - 0.35 * w_win)
    sk = Vector((0.25, 0.18, 0.12)).lerp(Vector((0.3, 0.33, 0.4)), w_win).lerp(Vector((0.18, 0.3, 0.5)), w_sum)
    c["sky"].active_material.node_tree.nodes["Principled BSDF"].inputs['Emission Color'].default_value = (*sk, 1)


def anim_clock(c, t):
    sec = t * DUR["clock"]
    mins = 2 * 60 + 12 + 106 * smooth(0.3, 4.4, sec)          # 2:12 -> 3:58, less than two hours
    c["min"].rotation_euler = (0, math.radians((mins % 60) * 6), 0)
    c["hour"].rotation_euler = (0, math.radians((mins / 60.0) * 30), 0)


def _cam_tool(c, t):
    e = ease(t); a = math.radians(-40 + 22 * e); r = 1.65 - 0.4 * e
    return (Vector((math.sin(a) * r, -math.cos(a) * r, 0.55 - 0.15 * e)), Vector((0.0, -0.03, 0.0)), 50)


def _cam_tool_swing(c, t):
    e = ease(t); a = math.radians(30 + 20 * e)
    return (Vector((0.9 * math.sin(a), -0.9 * math.cos(a), 1.0 - 0.1 * e)), Vector((0.0, 0.0, 0.0)), 40)


def _cam_board(c, t):
    e = ease(t)
    p0, p1 = Vector((-0.2, -2.3, 1.45)), Vector((0.2, -0.62, 1.12))
    tg0, tg1 = Vector((0.0, 0.0, 1.4)), Vector((0.27, 0.0, 1.07))
    return (p0.lerp(p1, e), tg0.lerp(tg1, e), 40)


def _cam_file(c, t):
    e = ease(t)
    return (Vector((0.1, -0.55, 0.62)).lerp(Vector((-0.08, -0.32, 0.36)), e), Vector((0.0, 0.0, 0.0)).lerp(Vector((-0.12, 0.0, 0.0)), e), 40)


def _cam_calendar(c, t):
    e = ease(t)
    return (Vector((-0.2, -1.2, 1.45)).lerp(Vector((-0.06, -0.78, 1.38)), e), Vector((0.0, 0.0, 1.38)).lerp(Vector((0.0, 0.0, 1.33)), e), 45)


def _cam_plan(c, t):
    e = ease(t); a = math.radians(-8 + 10 * e)
    loc = Vector((0.05 * math.sin(a), -0.32 + 0.1 * e, 0.95 - 0.2 * e))
    return (loc, Vector((0.0, 0.0, 0.0)), 35, (math.sin(a), math.cos(a), 0))


def _cam_cutaway(c, t):
    e = ease(t)
    a = math.radians(-38 + 50 * smooth(0.0, 0.8, t))
    r = 3.0 - 0.95 * smooth(0.72, 1.0, t)
    z = 1.75 - 0.3 * smooth(0.72, 1.0, t)
    tgt = Vector((0, 0, 1.05)).lerp(Vector((-0.2, 0.1, 1.35)), smooth(0.72, 1.0, t))
    return (Vector((math.sin(a) * r, -math.cos(a) * r, z)), tgt, 40 + 8 * smooth(0.72, 1.0, t))


def _cam_clock(c, t):
    e = ease(t)
    return (Vector((0.5, -3.4, 1.75)).lerp(Vector((0.22, -2.3, 2.0)), e), Vector((0, 0, 2.15)), 50)


MOVES = {
    "tool_black": dict(kind="anim", dof=2.8, far=10, anim=anim_tool, cam=_cam_tool, focus=lambda c, t: Vector((0.1, 0.0, 0.02))),
    "tool_swing": dict(kind="anim", dof=None, far=10, anim=anim_tool_swing, cam=_cam_tool_swing),
    "board": dict(kind="anim", dof=2.0, far=10, anim=anim_board, cam=_cam_board,
                  focus=lambda c, t: Vector((0.0, 0.0, 1.45)).lerp(Vector((0.27, 0.0, 1.07)), smooth(0.45, 0.85, t))),
    "file_card": dict(kind="anim", dof=2.8, far=10, anim=anim_file, cam=_cam_file, focus=lambda c, t: Vector((-0.15, 0.0, 0.0))),
    "calendar": dict(kind="anim", dof=2.8, far=10, anim=anim_calendar, cam=_cam_calendar, focus=lambda c, t: Vector((0, 0, 1.35))),
    "plan_route": dict(kind="anim", dof=2.8, far=10, anim=anim_plan, cam=_cam_plan, focus=lambda c, t: Vector((0, 0, 0))),
    "cutaway": dict(kind="anim", dof=4.0, far=20, anim=anim_cutaway, cam=_cam_cutaway, focus=lambda c, t: Vector((0, 0, 1.1)).lerp(Vector((-0.2, 0.1, 1.35)), smooth(0.72, 1.0, t))),
    "clock": dict(kind="anim", dof=2.8, far=10, anim=anim_clock, cam=_cam_clock, focus=lambda c, t: Vector((0, 0, 2.2))),
}
