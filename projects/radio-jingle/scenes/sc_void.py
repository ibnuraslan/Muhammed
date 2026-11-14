"""VOID: evidence objects as heroes, on black under one hard top light (rj_case.void_spot), realistic Cycles.
The objects recur like characters: the radio (Ch1 kitchen, Ch2 box, B's chain), the letter, the money, the bolts.

  Rule 7: nothing moves by itself (no self-assembling letters, no bolts sliding on their own): the objects lie
  still; only the camera and the light move. The clock's hands are the one exception.
  letter  (Ch1 #17)  the cut-out letter alone on black, crooked newspaper letters "2 MILLIONEN / GEBRAUCHTE /
                      HUNDERTER"; top-down slow push.
  money   (Ch1 #20)  two hundred bundles of used notes as one block (2 million in hundreds, 100 notes a bundle);
                      low slow push and turn.
  bolts   (Ch2 #5)   seven barrel bolts shot home along the planked lid; low macro track along the row.
  items   (Ch2 #8)   what was in the box, laid out as evidence: water, orange soda, chocolate, books, the radio;
                      slow overhead track.
  span    (Ch2 #10)  the wall clock in the dark: its hands race through four and a half hours (half an hour to five),
                      the pendulum swinging; slow push to the face.
"""
import math, os, random
import numpy as np
import bpy
from mathutils import Vector
from kit import pbr, box, cyl, join
from common import ease
import rj
import rj_case as K

EXPOSURE = 0.0
BOUNCES = 6
DUR = {}
VARIANT_FOR = {}
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "..", "..", "nvidia_doc", "assets", "generated")


def sm(t, a, b):
    return ease(max(0.0, min(1.0, (t - a) / max(b - a, 1e-6))))


# ---------------------------------------------------------------------------------------------- letter
SHEET_W, SHEET_H = 0.21, 0.297
PX = SHEET_W / 1240.0


def glyph_tiles(seed=7):
    """Newsprint letter snippets as images (same recipe as letter.py) and their final places on the sheet (px)."""
    import letter as LT
    from PIL import Image, ImageDraw, ImageFont
    rnd = random.Random(seed)
    out = []
    y = 300
    for li, line in enumerate(LT.LINES):
        size_line = rnd.randint(84, 96)
        tiles = []
        for ch in line:
            if ch == " ":
                tiles.append(None); continue
            sz = int(size_line * rnd.uniform(0.85, 1.15))
            f = ImageFont.truetype(rnd.choice(LT.F), sz)
            bb = f.getbbox(ch); w, h = bb[2] - bb[0] + 26, bb[3] - bb[1] + 26
            bg = rnd.choice([(226, 222, 206), (238, 236, 226), (214, 210, 196), (60, 58, 56), (230, 226, 210)])
            fg = (24, 22, 22) if sum(bg) > 300 else (236, 232, 222)
            tile = Image.new("RGB", (w, h), bg); td = ImageDraw.Draw(tile)
            for _ in range(6):
                yy = rnd.randrange(h); td.line((0, yy, w, yy), fill=tuple(max(0, c - 18) for c in bg), width=1)
            td.text((13 - bb[0], 13 - bb[1]), ch, font=f, fill=fg)
            tiles.append((tile, rnd.uniform(-7, 7)))
        widths = [t[0].size[0] if t else 60 for t in tiles]
        x = (1240 - sum(widths) - 4 * len(tiles)) // 2
        for k, t in enumerate(tiles):
            if t is None:
                x += 60; continue
            tile, rot = t
            p = os.path.join(GEN, f"rj_glyph_{li}_{k}.png"); tile.save(p)
            out.append(dict(path=p, w=tile.size[0], h=tile.size[1], x=x + tile.size[0] / 2, y=y + rnd.randint(-10, 10) + tile.size[1] / 2, rot=rot))
            x += tile.size[0] + rnd.randint(0, 8)
        y += size_line + 90
    return out


def img_mat(name, path, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    L.new(t.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = rough
    return m


def card(name, w, h, m, thick=0.00025):
    """A thin paper card with the image on top (UV 0..1 over the top face)."""
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.object; o.name = name
    o.scale = (w, h, 1); bpy.ops.object.transform_apply(scale=True)
    sol = o.modifiers.new("Thick", 'SOLIDIFY'); sol.thickness = thick; sol.offset = -1
    o.data.materials.append(m)
    return o


def build_letter(c):
    sheet_m = pbr("SheetPaper", (0.80, 0.78, 0.71), 0.85)
    N = sheet_m.node_tree.nodes; L = sheet_m.node_tree.links
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 700
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.1; L.new(nz.outputs['Fac'], bp.inputs['Height'])
    L.new(bp.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    sh = card("Sheet", SHEET_W, SHEET_H, sheet_m, 0.0003); sh.location = (0, 0, 0.0003)
    c["glyphs"] = []
    rnd = random.Random(3)
    for k, g in enumerate(glyph_tiles()):
        o = card(f"Glyph{k:02d}", g["w"] * PX, g["h"] * PX, img_mat(f"GlyphM{k}", g["path"]), 0.00018)
        home = Vector((-SHEET_W / 2 + g["x"] * PX, SHEET_H / 2 - g["y"] * PX, 0.0008))
        o["home"] = tuple(home); o["rot"] = math.radians(g["rot"])
        a = rnd.uniform(0, 2 * math.pi)
        o["from"] = tuple(home + Vector((math.cos(a) * 0.35, math.sin(a) * 0.30, 0.04 + rnd.uniform(0, 0.06))))
        o["spin"] = rnd.uniform(-2.5, 2.5)
        c["glyphs"].append(o)


def anim_letter(c, t):
    n = len(c["glyphs"])
    for i, o in enumerate(c["glyphs"]):
        t0 = 0.04 + 0.70 * i / n
        k = sm(t, t0, t0 + 0.16)
        a, b = Vector(o["from"]), Vector(o["home"])
        p = a.lerp(b, k); p.z = b.z + (a.z - b.z) * (1 - k) ** 2 + 0.006 * math.sin(math.pi * k)
        o.location = p
        o.rotation_euler = (0.25 * (1 - k) * math.sin(i), 0.2 * (1 - k), o["rot"] + o["spin"] * (1 - k))


def cam_letter(c, t):
    e = ease(t)
    tgt = Vector((0.0, 0.07 - 0.005 * e, 0.0))
    loc = tgt + Vector((0.0, -0.12 + 0.05 * e, 0.40 - 0.10 * e))
    return (loc, tgt, 35, (0, 1, 0))


# ---------------------------------------------------------------------------------------------- money
def build_money(c):
    import sc_house as SH
    m, band = SH._note_paper()
    th = 0.011                                         # a bundle of 100 used notes
    parts = [box("BdlBody", (0, 0, th / 2), (0.16, 0.085, th), m, bevel=0.0008),
             box("BdlBand", (0, 0, th / 2), (0.03, 0.0865, th + 0.0008), band)]
    tpl = join(parts, "BundleTpl"); tpl.location = (0, 0, -50)
    me = tpl.data
    rnd = random.Random(5)
    c["bundles"] = []
    nx, ny, nz = 5, 4, 10
    for k in range(nx * ny * nz):
        i, j, l = k % nx, (k // nx) % ny, k // (nx * ny)
        o = bpy.data.objects.new(f"Bundle{k:03d}", me); bpy.context.collection.objects.link(o)
        home = Vector(((i - (nx - 1) / 2) * 0.163 + rnd.uniform(-0.002, 0.002), (j - (ny - 1) / 2) * 0.088 + rnd.uniform(-0.002, 0.002), l * (th + 0.0004)))
        o["home"] = tuple(home); o["rz"] = rnd.uniform(-0.03, 0.03); o["k"] = k
        c["bundles"].append(o)


def anim_money(c, t):
    n = len(c["bundles"])
    for o in c["bundles"]:
        k0 = o["k"] / n
        t0 = 0.03 + 0.78 * k0
        k = sm(t, t0, t0 + 0.07)
        home = Vector(o["home"])
        if k <= 0:
            o.location = home + Vector((0, 0, 3.0)); continue
        o.location = home + Vector((0, 0, 0.25 * (1 - k) ** 2))
        o.rotation_euler = (0.0, 0.0, o["rz"] + 0.4 * (1 - k))


def cam_money(c, t):
    e = ease(t)
    tgt = Vector((0.0, 0.0, 0.05 + 0.03 * e))
    a = math.radians(-35 + 12 * e)
    loc = tgt + Vector((1.15 * math.sin(a), -1.15 * math.cos(a), 0.42 - 0.08 * e)) * (1.0 - 0.18 * e)
    return (loc, tgt, 50)


# ---------------------------------------------------------------------------------------------- bolts
BOLT_X = [(-0.48 + 0.16 * i) for i in range(7)]


def build_bolts(c):
    from kit import wood
    plank = wood("LidPlank", dark=(0.05, 0.035, 0.02), light=(0.16, 0.11, 0.06), scale=(1, 30, 30), rough=0.75, coat=0.0)
    rim = wood("RimPlank", dark=(0.04, 0.03, 0.018), light=(0.13, 0.09, 0.05), scale=(1, 30, 30), rough=0.8, coat=0.0)
    for k in range(3):                                  # the lid: three boards with gaps
        box(f"Lid{k}", (0, 0.06 + 0.115 * k, 0.03), (1.3, 0.11, 0.028), plank, bevel=0.002, rot=(0, 0, 0.003 * (k - 1)))
    box("Rim", (0, -0.04, 0.012), (1.32, 0.085, 0.024), rim, bevel=0.002)      # the box's top edge beside the lid
    steel = pbr("BoltSteel", (0.32, 0.30, 0.28), 0.42, 1.0)
    rust = pbr("BoltRust", (0.20, 0.10, 0.05), 0.8, 0.3)
    c["bolts"] = []
    for i, x in enumerate(BOLT_X):
        parts = [box(f"BPlate{i}", (x, 0.045, 0.0455), (0.036, 0.11, 0.003), steel, bevel=0.0008)]
        for gy in (0.012, 0.072):
            parts.append(box(f"BGuide{i}", (x, gy, 0.052), (0.026, 0.016, 0.013), steel, bevel=0.001))
        for sy in (0.0, 0.092):
            parts.append(cyl(f"BScrew{i}", (x, sy, 0.048), 0.0035, 0.002, rust, 12))
        join(parts, f"BoltBase{i}")
        kp = join([box(f"BKeeper{i}", (x, -0.035, 0.0255), (0.036, 0.04, 0.003), steel, bevel=0.0008),
                   box(f"BKeep2{i}", (x, -0.035, 0.034), (0.026, 0.016, 0.013), steel, bevel=0.001)], f"Keeper{i}")
        # the sliding rod with its handle: a separate object (slides along -Y into the keeper, then the handle drops)
        rod = cyl(f"BRod{i}", (0, 0, 0), 0.0055, 0.10, steel, 16, rot=(math.radians(90), 0, 0))
        hd = cyl(f"BHandle{i}", (0, 0.03, 0.013), 0.0035, 0.024, steel, 12)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0055, location=(0, 0.03, 0.027)); kb = bpy.context.object
        kb.data.materials.append(steel)
        r = join([rod, hd, kb], f"BoltRod{i}")
        rj.apply_rot(r)
        r.location = (0, 0, 0)
        r["x"] = x; c["bolts"].append(r)


def anim_bolts(c, t):
    for i, r in enumerate(c["bolts"]):
        t0 = 0.06 + 0.115 * i
        k = sm(t, t0, t0 + 0.07); d = sm(t, t0 + 0.07, t0 + 0.10)
        y = 0.050 - 0.058 * k                         # retracted on the lid -> through the keeper on the rim
        r.location = (r["x"], y, 0.052)
        r.rotation_euler = (0.0, -math.radians(85) * d, 0.0)


def cam_bolts(c, t):
    e = ease(t)
    x = -0.55 + 1.05 * e
    tgt = Vector((x + 0.08, 0.0, 0.04))
    loc = Vector((x - 0.05, -0.32, 0.17))
    return (loc, tgt, 50)


# ---------------------------------------------------------------------------------------------- items
def build_items(c):
    import sc_box as SB
    water = pbr("Water", (0.8, 0.85, 0.85), 0.02, 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.33})
    soda = pbr("Soda", (0.95, 0.42, 0.04), 0.05, 0.0, **{'Transmission Weight': 0.6, 'IOR': 1.34})
    c["items"] = []

    def grp(objs, home):
        root = bpy.data.objects.new("Item", None); bpy.context.collection.objects.link(root)
        for o in objs:
            o.parent = root
        root["home"] = tuple(home); c["items"].append(root); return root
    grp(SB.bottle("BtlW1", (0, 0, 0), water, 0.5), (-0.36, 0.10, 0))
    grp(SB.bottle("BtlW2", (0, 0, 0), water, 0.45), (-0.28, 0.13, 0))
    grp(SB.bottle("BtlS1", (0, 0, 0), soda, 0.5), (-0.18, 0.12, 0))
    grp(SB.bottle("BtlS2", (0, 0, 0), soda, 0.45), (-0.10, 0.15, 0))
    for k in range(3):
        grp([SB.chocolate(f"Choc{k}", (0, 0, 0), 0.0)], (0.02 + 0.0 * k, -0.05 + 0.0 * k, 0.012 * k))
    for k, col in enumerate(((0.32, 0.10, 0.06), (0.10, 0.18, 0.28), (0.30, 0.26, 0.10))):
        b = SB.paperback(f"Book{k}", (0, 0, 0), col)
        b.rotation_euler = (0, math.radians(90), math.radians(8 * k)); b.location = (0, 0, 0.012)
        grp([b], (0.20, 0.02 - 0.0 * k, 0.025 * k))
    r, dial = rj.portable_radio("BoxRadio")
    grp([r], (0.40, 0.08, 0))
    rj.emission_driven(dial, "0.0")


def anim_items(c, t):
    n = len(c["items"])
    for i, o in enumerate(c["items"]):
        t0 = 0.04 + 0.72 * i / n
        k = sm(t, t0, t0 + 0.08)
        home = Vector(o["home"])
        if k <= 0:
            o.location = home + Vector((0, 0, 3.0)); continue
        o.location = home + Vector((0, 0, 0.08 * (1 - k) ** 2))
        o.rotation_euler = (0, 0, 0.15 * (1 - k))


def cam_items(c, t):
    e = ease(t)
    tgt = Vector((-0.20 + 0.42 * e, 0.06, 0.05))
    loc = tgt + Vector((-0.04, -0.78, 0.66))
    return (loc, tgt, 40)


# ---------------------------------------------------------------------------------------------- span (the clock)
def build_span(c):
    """The Poly Haven wall clock (separate hour, minute and second hands, pivots at the centre, face toward -Y)."""
    import ph
    root, parts = ph.model("wall_clock")
    hands = {}
    for o in parts:
        for k in ("hours", "minute", "second"):
            if k in o.name:
                hands[k] = o
    init = {}
    for k, o in hands.items():                       # the angle each hand points at in the model (clockwise from 12)
        vs = [v.co for v in o.data.vertices]
        tip = max(vs, key=lambda v: v.x * v.x + v.z * v.z)
        init[k] = math.atan2(tip.x, tip.z)
        o.rotation_mode = 'XYZ'
    root.location = (0, 0, 0.0)
    c["clock"] = (root, hands, init)


def anim_span(c, t):
    root, hands, init = c["clock"]
    # from 7:45 to 12:15 (half an hour to five hours after a quarter past seven)
    mins = 7 * 60 + 45 + 270 * sm(t, 0.08, 0.92)
    want = {"minute": (mins % 60) / 60.0 * 2 * math.pi, "hours": ((mins / 60.0) % 12) / 12.0 * 2 * math.pi,
            "second": (t * 40.0) % 1.0 * 2 * math.pi}
    for k, o in hands.items():
        o.rotation_euler = (0, want[k] - init[k], 0)


def cam_span(c, t):
    e = ease(t)
    tgt = Vector((0.0, 0, -0.01 * (1 - e)))
    loc = tgt + Vector((0.30 - 0.10 * e, -0.80 + 0.22 * e, 0.06))
    return (loc, tgt, 50)


# ---------------------------------------------------------------------------------------------- build
BUILD = {"letter": build_letter, "money": build_money, "bolts": build_bolts, "items": build_items, "span": build_span}
LIGHT = {"letter": dict(key_energy=2.4, key_size=0.35, height=1.0, spread=30), "money": dict(key_energy=22, key_size=0.9, height=1.6, rim=14),
         "bolts": dict(key_energy=5.5, key_size=0.5, height=1.2, rim=4), "items": dict(key_energy=7.5, key_size=0.6, height=1.3, rim=4),
         "span": dict(key_energy=3.0, key_size=0.35, height=1.1, rim=5, key_off=(0.25, -0.75, 0.55), spread=35)}


def build(variant=None):
    c = dict(variant=variant)
    for k, fn in BUILD.items():                      # only the object of the shot (variant = shot name)
        if k == variant:
            fn(c)
    K.void_spot((0, 0, 0), **LIGHT.get(variant, {}))
    if variant == "span":                            # the clock hangs in the dark: no floor under it, light it frontally
        f = bpy.data.objects.get("VoidFloor")
        if f:
            f.location.z = -0.9
    rj.finish_scene()
    return c


ANIM = {"letter": anim_letter, "money": anim_money, "bolts": anim_bolts, "items": anim_items, "span": anim_span}
CAM = {"letter": cam_letter, "money": cam_money, "bolts": cam_bolts, "items": cam_items, "span": cam_span}
FOCUS = {"bolts": lambda c, t: cam_bolts(c, t)[1], "items": lambda c, t: cam_items(c, t)[1],
         "money": lambda c, t: Vector((0, -0.17, 0.06)), "span": lambda c, t: Vector((0, -0.03, 0.0))}
SECS = {"letter": 6.0, "money": 6.0, "bolts": 6.5, "items": 6.0, "span": 6.0}
MOVES = {}
for _k in BUILD:
    DUR[_k] = SECS[_k]
    # Rule 7: nothing acts by itself. The objects lie still in their final state; only the camera (and light) moves.
    # The clock is the one exception: its hands run on their own, as a clock's do.
    MOVES[_k] = dict(kind="anim", cam=CAM[_k], anim=(lambda k: (lambda c, t: ANIM[k](c, t if k == "span" else 1.0)))(_k))
    if _k in FOCUS:
        MOVES[_k]["focus"] = FOCUS[_k]; MOVES[_k]["dof"] = 2.8
    VARIANT_FOR[_k] = _k
