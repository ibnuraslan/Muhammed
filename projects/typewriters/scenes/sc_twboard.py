"""THE INVESTIGATORS' BOARD (Ch4 8B): what is known, pinned up; what is not, left as empty pins.

Ch4 8B  board  "The full list ... is beyond what investigators can reconstruct." - a real cork board in a wooden frame
               under a warm desk lamp: printed photos of earlier scenes (typewriters, the X-ray film, customs crates),
               typed index cards with places and dates, a red string pinned from item to item with a slight sag
               (already up: nothing on the board moves by itself), running on to three empty pins with torn paper
               corners. The camera drifts along the string and settles on the empty pins.
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import typewriter as T
import look

DUR = {"board": 7.0}
EXPOSURE = 0.0
ART = os.path.join(T.GEN, "board_v2")
BOARD_Z, BOARD_W, BOARD_H = 1.45, 2.2, 1.2
FACE_Y = -0.0255                                   # front face of the cork

# (kind, source or text lines, x, z, w, tilt deg)
ITEMS = [
    ("photo", "twmacro_strike",          -0.86, 1.74, 0.24, -3),
    ("card",  ["MOSCOW EMBASSY", "IBM SELECTRIC  No. 14", "ALTERED - BAR + COILS", "IN SERVICE 1976-84"], -0.52, 1.76, 0.20, 2),
    ("photo", "twlab_sixteen",          -0.12, 1.73, 0.25, 1),
    ("card",  ["LENINGRAD CONSULATE", "3 MACHINES", "SAME MODIFICATION"], 0.30, 1.76, 0.19, -2),
    ("photo", "twmeade_film",            0.58, 1.71, 0.24, 3),
    ("photo", "twhangar_customs_clock", -0.80, 1.42, 0.24, 2),
    ("card",  ["CUSTOMS HOLD", "SHEREMETYEVO", "OVERNIGHT - UNGUARDED", "1976 / 1982"], -0.42, 1.40, 0.20, -3),
    ("photo", "twgrid_count",           -0.02, 1.43, 0.25, -1),
    ("card",  ["23 JUL 1984", "FIRST BUG FOUND", "FT MEADE - X-RAY"], 0.36, 1.41, 0.18, 2),
    ("photo", "twoffice_typing",        -0.62, 1.12, 0.24, -2),
    ("photo", "twmeade_motorfilm",      -0.18, 1.13, 0.24, 2),
    ("card",  ["16 FOUND", "13 MOSCOW - 3 LENINGRAD", "OTHERS ?"], 0.20, 1.11, 0.19, -1),
]
EMPTY = [(0.80, 1.42), (0.93, 1.70), (0.86, 1.14)]           # pins whose photos were taken down: torn corners only
ORDER = [0, 1, 2, 3, 4, 8, 7, 6, 5, 9, 10, 11, 7, 2, 12, 13, 14]   # item index (>= len(ITEMS): empty pins)


def _font(size):
    from PIL import ImageFont
    for f in ("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf", "/usr/share/fonts/truetype/freefont/FreeMono.ttf", "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def make_art():
    """Prints (our own renders, as photos with a white border) and typed index cards, written once into ART."""
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(ART, exist_ok=True)
    rng = np.random.default_rng(5)
    for k, (kind, src, *_r) in enumerate(ITEMS):
        out = os.path.join(ART, f"item{k}.png")
        if os.path.exists(out):
            continue
        if kind == "photo":
            p = next((q for q in (f"/tmp/claude-0/sb/{src}.png", f"/tmp/claude-0/st/{src}.png") if os.path.exists(q)), None)
            im = Image.open(p).convert("RGB") if p else Image.new("RGB", (900, 600), (60, 58, 55))
            w, h = im.size; cw = int(h * 1.5)                                   # 3:2 print crop
            im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h)).resize((900, 600), Image.LANCZOS)
            pr = Image.new("RGB", (960, 660), (236, 232, 222)); pr.paste(im, (30, 30))
            pr.save(out)
        else:
            card = Image.new("RGB", (900, 560), (238, 232, 214)); d = ImageDraw.Draw(card)
            d.line((0, 92, 900, 92), fill=(205, 80, 80), width=3)               # index card: red head rule, blue lines
            for y in range(150, 560, 58):
                d.line((0, y, 900, y), fill=(160, 180, 210), width=2)
            f = _font(66)
            for i, line in enumerate(src):
                x0, y0 = 40 + int(rng.integers(-3, 4)), 24 + i * 118 + (0 if i == 0 else 6)
                d.text((x0, y0), line, fill=(28, 26, 30), font=f)
                for dx in (1, 2):
                    d.text((x0 + dx, y0), line, fill=(20, 18, 24), font=f)                 # typewriter strike weight
            card = card.filter(ImageFilter.GaussianBlur(0.4))
            card.save(out)


def cork_mat():
    """Real cork: fine dark-brown granules with lighter flecks, slightly worn and paler in broad patches."""
    m = bpy.data.materials.new("Cork"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs['Scale'].default_value = 420; vo.inputs['Randomness'].default_value = 1.0
    L.new(tc.outputs['Object'], vo.inputs['Vector'])
    vo2 = N.new("ShaderNodeTexVoronoi"); vo2.inputs['Scale'].default_value = 1100
    L.new(tc.outputs['Object'], vo2.inputs['Vector'])
    sep = N.new("ShaderNodeSeparateColor"); L.new(vo.outputs['Color'], sep.inputs[0])
    sep2 = N.new("ShaderNodeSeparateColor"); L.new(vo2.outputs['Color'], sep2.inputs[0])
    mix = N.new("ShaderNodeMath"); mix.operation = 'MULTIPLY_ADD'; mix.inputs[1].default_value = 0.6
    L.new(sep.outputs[0], mix.inputs[0]); L.new(sep2.outputs[0], mix.inputs[2])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    wear = N.new("ShaderNodeMath"); wear.operation = 'MULTIPLY_ADD'; wear.inputs[1].default_value = 0.35
    L.new(nz.outputs['Fac'], wear.inputs[0]); L.new(mix.outputs[0], wear.inputs[2])
    cr = N.new("ShaderNodeValToRGB"); E = cr.color_ramp.elements
    E[0].position = 0.15; E[0].color = (0.085, 0.045, 0.02, 1)
    E[1].position = 0.95; E[1].color = (0.42, 0.26, 0.13, 1)
    mid = E.new(0.55); mid.color = (0.24, 0.135, 0.06, 1)
    nrm = N.new("ShaderNodeMath"); nrm.operation = 'MULTIPLY'; nrm.inputs[1].default_value = 0.62
    L.new(wear.outputs[0], nrm.inputs[0]); L.new(nrm.outputs[0], cr.inputs[0]); L.new(cr.outputs[0], p.inputs['Base Color'])
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.55; bm.inputs['Distance'].default_value = 0.0008
    L.new(vo.outputs['Distance'], bm.inputs['Height']); L.new(bm.outputs[0], p.inputs['Normal'])
    p.inputs['Roughness'].default_value = 0.85
    return m


def print_mat(name, path, gloss=0.25):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); L.new(t.outputs[0], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = gloss
    return m


def pin(name, loc, mat):
    """A round map pin: a glossy red head on a short steel needle into the cork."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.0075, location=loc + Vector((0, -0.012, 0)))
    hd = bpy.context.active_object; hd.name = name; hd.data.materials.append(mat); bpy.ops.object.shade_smooth()
    cyl(name + "Needle", loc + Vector((0, -0.004, 0)), 0.0008, 0.012, pbr("PinSteel", (0.7, 0.7, 0.72), 0.25, 1.0), verts=8,
        rot=(math.radians(90), 0, 0))
    return loc + Vector((0, -0.006, -0.004))                       # where the string wraps, just under the head


def sag_curve(name, pts, mat, radius=0.0016, sag=0.018):
    """One length of string through the pins, hanging in a shallow curve between each pair (and a little off the cork)."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = radius; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); P = []
    for a, b in zip(pts[:-1], pts[1:]):
        span = (b - a).length
        for i in range(12):
            s = i / 12
            q = a.lerp(b, s); q.z -= sag * span * 4 * s * (1 - s); q.y -= 0.004 * 4 * s * (1 - s)
            P.append(q)
    P.append(pts[-1])
    sp.points.add(len(P) - 1)
    for i, q in enumerate(P):
        sp.points[i].co = (q.x, q.y, q.z, 1)
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o); o.data.materials.append(mat)
    return o


def build(variant=None):
    c = {}
    make_art()
    w = bpy.context.scene.world or bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.01
    box("Wall", (0, 0.05, 1.5), (5, 0.1, 3), ph.texture("painted_plaster_wall", scale=0.5, name="BoardWall", tint=(0.55, 0.52, 0.47)))
    box("Cork", (0, -0.01, BOARD_Z), (BOARD_W, 0.031, BOARD_H), cork_mat())
    frame = ph.texture("dark_wood", scale=1.0, name="BoardFrame")
    for (x, z, sx, sz) in ((0, BOARD_Z + 0.625, 2.3, 0.05), (0, BOARD_Z - 0.625, 2.3, 0.05), (-1.125, BOARD_Z, 0.05, 1.3), (1.125, BOARD_Z, 0.05, 1.3)):
        box("Frame", (x, -0.022, z), (sx, 0.05, sz), frame, bevel=0.006)
    red = pbr("PinRed", (0.62, 0.03, 0.02), 0.18)
    anchors = []
    for k, (kind, src, x, z, wd, tilt) in enumerate(ITEMS):
        ht = wd * (660 / 960 if kind == "photo" else 560 / 900)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, FACE_Y - 0.0006 - 0.0002 * k, z), rotation=(math.radians(90), math.radians(tilt), 0))
        o = bpy.context.active_object; o.name = f"Item{k}"; o.scale = (wd, ht, 1)
        o.data.materials.append(print_mat(f"ItemM{k}", os.path.join(ART, f"item{k}.png"), 0.22 if kind == "photo" else 0.7))
        top = Vector((x - math.sin(math.radians(tilt)) * ht * 0.4, FACE_Y, z + ht * 0.4))
        anchors.append(pin(f"Pin{k}", top, red))
    paper = pbr("TornCorner", (0.8, 0.77, 0.7), 0.8)
    for k, (x, z) in enumerate(EMPTY):
        for j, (dx, dz, r) in enumerate(((-0.012, -0.012, 0.3), (0.01, -0.008, -0.5))[: 1 + (k % 2)]):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(x + dx, FACE_Y - 0.0006, z + dz), rotation=(math.radians(90), r + 0.4 * k, 0))
            o = bpy.context.active_object; o.scale = (0.032, 0.026, 1); o.data.materials.append(paper)
        anchors.append(pin(f"EmptyPin{k}", Vector((x, FACE_Y, z)), red))
    string = pbr("RedString", (0.72, 0.035, 0.03), 0.55); string.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.4
    c["string"] = sag_curve("String", [anchors[i] for i in ORDER], string)
    # a desk lamp low and to the side: warm raking light across the cork, soft shadows, the far end falls off
    l = bpy.data.lights.new("BoardLamp", 'SPOT'); l.energy = 300; l.spot_size = math.radians(75); l.spot_blend = 0.7
    l.color = (1.0, 0.8, 0.56); l.shadow_soft_size = 0.18
    lo = bpy.data.objects.new("BoardLamp", l); bpy.context.collection.objects.link(lo); lo.location = (-1.5, -1.1, 1.05); point_at(lo, (0.0, 0.0, 1.45))
    f = area_light((1.6, -2.2, 2.3), (0, 0, 0), 1.6, 14, (0.95, 0.9, 0.85)); point_at(f, (0, 0, 1.4)); f.visible_camera = False
    animate(c, 0.0, "board")
    return c


def animate(c, sec, shot):
    bpy.context.view_layer.update()                  # the string is already up: nothing on the board moves by itself


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_board(c, t):
    e = ease(t)
    x = -0.3 + 0.75 * e                   # drifts along the string, ends with the empty pins (x ~0.8-0.95) on the right third
    return (Vector((x - 0.15, -2.35 + 0.25 * e, 1.5)), Vector((x, 0.0, 1.44)), 38)


MOVES = {"board": dict(kind="anim", dof=3.5, cam=cam_board, focus=lambda c, t: Vector((-0.3 + 0.75 * ease(t), FACE_Y, 1.44)), anim=anim("board"), dur=DUR["board"])}
