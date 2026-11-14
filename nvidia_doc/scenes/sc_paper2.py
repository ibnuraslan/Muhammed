"""CH4/CH5 redo: varied paperwork inserts, house style (generic documents only: grey text bars, no readable names,
no real seals or mastheads). Variants (one environment each):
  binder   CH4 4B (114 f) a ring binder of a code of conduct open on a desk; a highlighter pen draws a yellow mark
           along one clause (the pen leaves frame at the top: whoever holds it stays off-screen)
  printer  CH4 4C (297 f) an office laser printer feeds a filing out into its tray, page after page
  letter   CH5 10C (159 f) a congressional-style letter on letterhead (abstract crest, no readable seal) on a desk
  clipboard CH5 11A (291 f) a shipping manifest on a clipboard in a port office at dusk; cranes outside the window
  ledger   CH5 11B (251 f) a customer ledger on a monitor; the camera pulls back to the empty office chair
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from PIL import Image, ImageDraw
from kit import *
from common import area_light, world_flat, world_sky, sun

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "assets", "generated")
EXPOSURE = 0.0
VARIANT_FOR = {"binder": "binder", "printer": "printer", "letter": "letter", "clipboard": "clipboard", "ledger": "ledger"}
FRAMES = {"binder": 114, "printer": 297, "letter": 159, "clipboard": 291, "ledger": 251}
DZ = 0.74


def text_page(path, seed, header=None, W=1240, H=1754, hl_row=None):
    """Grey text bars; optional header block ('code' = section title bar, 'letter' = abstract crest + rule)."""
    r = np.random.default_rng(seed)
    im = Image.new("RGB", (W, H), (240, 237, 229)); d = ImageDraw.Draw(im)
    y = 150
    if header == "letter":
        cx = W // 2
        d.ellipse([cx - 70, 70, cx + 70, 210], outline=(70, 70, 90), width=6)            # abstract crest, no detail
        d.ellipse([cx - 40, 100, cx + 40, 180], fill=(90, 92, 110))
        d.rectangle([cx - 260, 240, cx + 260, 256], fill=(60, 62, 80))
        d.rectangle([cx - 180, 274, cx + 180, 284], fill=(120, 120, 135))
        d.line([(120, 320), (W - 120, 320)], fill=(80, 80, 95), width=3); y = 400
        d.rectangle([W - 420, y, W - 120, y + 12], fill=(130, 130, 130)); y += 80
    elif header == "code":
        d.rectangle([120, y, 700, y + 38], fill=(30, 52, 92)); y += 70
        d.rectangle([120, y, 420, y + 16], fill=(110, 110, 110)); y += 70
    rows = []
    while y < H - 200:
        if r.random() < 0.12:
            y += 44; continue
        x = 120; lw = r.uniform(0.62, 1.0) * (W - 240)
        while x < 120 + lw:
            seg = min(r.uniform(50, 210), 120 + lw - x)
            d.rectangle([x, y + 3, x + seg, y + 11], fill=(118, 116, 110)); x += seg + 14
        rows.append(y); y += 44
    if header == "letter":
        d.line([(W - 520, H - 300), (W - 220, H - 330)], fill=(30, 40, 90), width=5)       # an illegible signature stroke
        d.line([(W - 480, H - 320), (W - 300, H - 290)], fill=(30, 40, 90), width=4)
    im.save(path); return path, rows


def ledger_screen(path, W=1920, H=1080):
    """A spreadsheet-like customer ledger: header bar, column headers, rows of grey cells, one highlighted row."""
    im = Image.new("RGB", (W, H), (246, 247, 249)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 70], fill=(44, 62, 88)); d.rectangle([30, 25, 330, 45], fill=(190, 200, 215))
    cols = [(40, 180), (240, 420), (680, 300), (1000, 220), (1240, 240), (1500, 360)]
    d.rectangle([0, 90, W, 140], fill=(225, 229, 236))
    for x, w in cols:
        d.rectangle([x, 108, x + int(w * 0.55), 122], fill=(90, 95, 105))
    r = np.random.default_rng(4)
    for k in range(22):
        y = 160 + k * 40
        if k == 9: d.rectangle([0, y - 8, W, y + 28], fill=(255, 236, 170))
        d.line([(0, y + 30), (W, y + 30)], fill=(220, 223, 228), width=1)
        for x, w in cols:
            d.rectangle([x, y + 4, x + int(w * r.uniform(0.3, 0.8)), y + 16], fill=(150, 152, 158))
    im.save(path); return path


def tex_mat(name, path, rough=0.8, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path)
    L.new(t.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = rough
    if emit:
        L.new(t.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = emit
    return m


def plane(name, loc, size, rot, mat):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1); o.data.materials.append(mat)
    return o


def desk_room(day=False, wall_col=(0.09, 0.09, 0.095), desk_dark=True, window=False):
    box("Floor", (0, 0, -0.01), (10, 10, 0.02), fabric("Carpet", (0.05, 0.05, 0.055) if not day else (0.12, 0.12, 0.13), 0.95, 0.2, 400))
    wall = pbr("Wall", wall_col, 0.85)
    if window:                                       # back wall with a 2.8 x 1.3 m window opening (x -1.4..1.4, z 0.95..2.25)
        box("WallBackL", (-3.2, 1.6, 1.5), (3.6, 0.1, 3.0), wall); box("WallBackR", (3.2, 1.6, 1.5), (3.6, 0.1, 3.0), wall)
        box("WallBackLo", (0, 1.6, 0.475), (2.8, 0.1, 0.95), wall); box("WallBackHi", (0, 1.6, 2.625), (2.8, 0.1, 0.75), wall)
    else:
        box("WallBack", (0, 1.6, 1.5), (10, 0.1, 3.0), wall)
    box("WallL", (-2.5, 0, 1.5), (0.1, 10, 3.0), wall)
    box("Ceil", (0, 0, 3.0), (10, 10, 0.05), pbr("Ceil", (0.2, 0.2, 0.2), 0.9))
    w = wood("Desk", (0.035, 0.022, 0.014) if desk_dark else (0.25, 0.18, 0.12), (0.09, 0.055, 0.03) if desk_dark else (0.42, 0.32, 0.22),
             scale=(6, 0.35, 0.35), rough=0.3, coat=0.6)
    box("Desk", (0, 0.4, DZ), (1.8, 0.85, 0.04), w, bevel=0.005)
    box("DeskSide", (0.75, 0.4, DZ / 2), (0.05, 0.8, DZ), w); box("DeskSide", (-0.75, 0.4, DZ / 2), (0.05, 0.8, DZ), w)


def lamp(loc, target, energy=70):
    brass = brushed_metal("Brass", (0.75, 0.55, 0.3), (0.2, 0.35), 0.3)
    cyl("LampBase", (loc[0], loc[1], DZ + 0.01), 0.08, 0.02, brass, verts=32)
    cyl("LampStem", (loc[0], loc[1], DZ + 0.22), 0.01, 0.42, brass, verts=12)
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.12, radius2=0.05, depth=0.15, location=(loc[0] + 0.08, loc[1] - 0.06, DZ + 0.45),
                                    rotation=(math.radians(-150), math.radians(20), 0))
    sh = bpy.context.active_object; sh.data.materials.append(pbr("Shade", (0.05, 0.12, 0.07), 0.35, 0.6)); sh.visible_shadow = False
    l = bpy.data.lights.new("Lamp", 'SPOT'); l.energy = energy; l.spot_size = math.radians(85); l.spot_blend = 0.5
    l.color = (1.0, 0.82, 0.6); l.shadow_soft_size = 0.03
    o = bpy.data.objects.new("Lamp", l); bpy.context.collection.objects.link(o); o.location = (loc[0] + 0.1, loc[1] - 0.08, DZ + 0.42); point_at(o, target)


def build(variant=None):
    os.makedirs(GEN, exist_ok=True)
    c = {}
    if variant == "binder":
        world_flat((0.004, 0.005, 0.008), 1.0)
        desk_room()
        pg, rows = text_page(os.path.join(GEN, "coc_page_l.png"), 11, "code")
        pg2, rows2 = text_page(os.path.join(GEN, "coc_page_r.png"), 12)
        cover = pbr("BinderCover", (0.05, 0.12, 0.28), 0.45, 0.0, **{'Coat Weight': 0.3})
        box("CoverL", (-0.17, 0.35, DZ + 0.026), (0.32, 0.33, 0.006), cover, bevel=0.003, rot=(0, math.radians(-3), 0))
        box("CoverR", (0.17, 0.35, DZ + 0.026), (0.32, 0.33, 0.006), cover, bevel=0.003, rot=(0, math.radians(3), 0))
        box("Spine", (0, 0.35, DZ + 0.03), (0.045, 0.33, 0.012), cover)
        ring = brushed_metal("Ring", (0.75, 0.75, 0.77), (0.15, 0.3), 0.4)
        for y in (0.25, 0.35, 0.45):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.016, minor_radius=0.0025, location=(0, 0.35 + (y - 0.35) * 0.9, DZ + 0.048), rotation=(math.radians(90), 0, 0))
            bpy.context.active_object.data.materials.append(ring)
        for k in range(8):                                                  # page stack edges
            box("Stack", (0.155, 0.35, DZ + 0.033 + k * 0.0012), (0.29, 0.31, 0.001), pbr("PageEdge", (0.85, 0.84, 0.8), 0.8))
        plane("PageL", (-0.155, 0.35, DZ + 0.034), (0.29, 0.31), (0, math.radians(-3), 0), tex_mat("PgL", pg))
        plane("PageR", (0.155, 0.35, DZ + 0.044), (0.29, 0.31), (0, math.radians(3), 0), tex_mat("PgR", pg2))
        # the highlight: a yellow translucent strip whose length grows with the pen (frame-driven via anim)
        hl = bpy.data.materials.new("Highlight"); hl.use_nodes = True;
        p = hl.node_tree.nodes["Principled BSDF"]; p.inputs['Base Color'].default_value = (1.0, 0.85, 0.05, 1); p.inputs['Alpha'].default_value = 0.55
        p.inputs['Roughness'].default_value = 0.6
        row_y = 0.35 + 0.155 - (rows2[6] + 8) / 1754 * 0.31                  # world y of the 7th text row on the right page
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0.02, row_y, DZ + 0.0455))
        h = bpy.context.active_object; h.name = "HL"; h.data.materials.append(hl)
        h.data.transform(__import__("mathutils").Matrix.Translation((0.5, 0, 0)))  # grow from the left edge
        h.scale = (0.001, 0.009, 1)
        c["hl"] = h; c["hl_x0"] = 0.02; c["hl_len"] = 0.24
        # the highlighter: barrel + cap, tilted, its far end leaves frame at the top of shot
        body = pbr("HLBody", (0.95, 0.8, 0.05), 0.4); cap = pbr("HLCap", (0.08, 0.08, 0.08), 0.4)
        pen = join([cyl("HLBarrel", (0, 0, 0.07), 0.009, 0.12, body, verts=16), cyl("HLTip", (0, 0, 0.004), 0.004, 0.012, cap, verts=8)], "Highlighter")
        pen.rotation_euler = (math.radians(-35), math.radians(25), 0)
        c["pen"] = pen; c["row_y"] = row_y
        cyl("Mug", (0.62, 0.62, DZ + 0.06), 0.045, 0.1, pbr("Mug", (0.55, 0.55, 0.57), 0.3), verts=24)
        lamp((-0.6, 0.75, 0), (0.0, 0.35, DZ))
        area_light((1.2, -0.8, 2.2), (0, 0, 0), 1.5, 6, (0.5, 0.62, 0.9)).visible_camera = False
        c["focus"] = Vector((0.13, row_y, DZ + 0.045))
    elif variant == "printer":
        world_flat((0.006, 0.007, 0.01), 1.0)
        desk_room(wall_col=(0.14, 0.145, 0.15))
        bodym = pbr("PrinterBody", (0.75, 0.76, 0.77), 0.4); darkm = pbr("PrinterDark", (0.08, 0.085, 0.09), 0.45)
        x0, y0 = 0.1, 0.5
        box("PBody", (x0, y0, DZ + 0.2), (0.44, 0.4, 0.36), bodym, bevel=0.015)
        box("PTop", (x0, y0 + 0.02, DZ + 0.385), (0.4, 0.34, 0.012), darkm, bevel=0.004)
        box("POutBay", (x0, y0 - 0.12, DZ + 0.33), (0.36, 0.16, 0.05), darkm)                 # output bay recess
        box("PTray", (x0, y0 - 0.26, DZ + 0.27), (0.34, 0.22, 0.008), darkm, rot=(math.radians(-8), 0, 0))
        box("PPanel", (x0 + 0.13, y0 - 0.2, DZ + 0.36), (0.12, 0.05, 0.02), darkm, rot=(math.radians(-25), 0, 0))
        box("PScreen", (x0 + 0.13, y0 - 0.222, DZ + 0.368), (0.06, 0.03, 0.002), emissive("PScreen", (0.4, 0.75, 1.0), 2.0), rot=(math.radians(-25), 0, 0))
        led = bpy.data.materials.new("PLed"); led.use_nodes = True
        n_ = led.node_tree.nodes; l_ = led.node_tree.links; n_.clear(); o_ = n_.new("ShaderNodeOutputMaterial"); em = n_.new("ShaderNodeEmission")
        em.inputs['Color'].default_value = (0.3, 1.0, 0.4, 1); v = n_.new("ShaderNodeValue")
        dd = v.outputs[0].driver_add("default_value").driver; dd.type = 'SCRIPTED'; dd.expression = "6 * (1 if (frame % 20) < 10 else 0.2)"
        l_.new(v.outputs[0], em.inputs['Strength']); l_.new(em.outputs[0], o_.inputs['Surface'])
        box("PLed", (x0 + 0.19, y0 - 0.215, DZ + 0.37), (0.008, 0.008, 0.004), led, rot=(math.radians(-25), 0, 0))
        for k in range(4):
            box("PaperIn", (x0, y0 + 0.05, DZ + 0.045 + k * 0.004), (0.3, 0.28, 0.002), pbr("PaperIn", (0.9, 0.9, 0.88), 0.8))
        pages = []
        for k in range(7):
            pth, _ = text_page(os.path.join(GEN, f"filing_page_{k}.png"), 30 + k, "code" if k == 0 else None)
            pg = plane(f"Out{k}", (x0, y0 - 0.06, DZ + 0.31), (0.21, 0.297), (math.radians(-8), 0, 0), tex_mat(f"Out{k}", pth))
            pages.append(pg)
        c["pages"] = pages; c["out0"] = Vector((x0, y0 - 0.06, DZ + 0.31)); c["tray"] = Vector((x0, y0 - 0.27, DZ + 0.285))
        cyl("Mug", (-0.55, 0.3, DZ + 0.06), 0.045, 0.1, pbr("Mug", (0.3, 0.32, 0.36), 0.3), verts=24)
        lamp((-0.65, 0.75, 0), (0.0, 0.3, DZ), energy=55)
        area_light((0.9, -1.1, 2.3), (0, 0, 0), 2.0, 45, (0.6, 0.7, 0.9)).visible_camera = False
        area_light((0.1, 0.5, 2.9), (0, 0, 0), 1.2, 18, (1.0, 0.95, 0.9)).visible_camera = False
    elif variant == "letter":
        world_flat((0.004, 0.005, 0.008), 1.0)
        desk_room()
        lt, _ = text_page(os.path.join(GEN, "house_letter.png"), 21, "letter")
        plane("Letter", (0.0, 0.32, DZ + 0.022), (0.216, 0.279), (0, 0, 0.06), tex_mat("Letter", lt))
        plane("Envelope", (0.25, 0.48, DZ + 0.021), (0.24, 0.11), (0, 0, -0.15), pbr("Envelope", (0.9, 0.88, 0.82), 0.8))
        box("Blotter", (0.0, 0.35, DZ + 0.021), (0.6, 0.45, 0.002), pbr("Blotter", (0.12, 0.18, 0.13), 0.9))
        cyl("Pen", (-0.2, 0.25, DZ + 0.026), 0.005, 0.15, pbr("Pen", (0.03, 0.03, 0.04), 0.2, 0.8), verts=12, rot=(math.radians(90), 0, 0.4))
        lamp((-0.6, 0.75, 0), (0.0, 0.3, DZ))
        area_light((1.2, -0.8, 2.2), (0, 0, 0), 1.5, 6, (0.5, 0.62, 0.9)).visible_camera = False
        c["focus"] = Vector((0.0, 0.32, DZ + 0.022))
    elif variant == "clipboard":
        world_sky(sun_elev_deg=1.5, sun_rot_deg=250, strength=0.22, tint=(1.0, 0.7, 0.55), aerosol=5.0)
        desk_room(day=True, wall_col=(0.38, 0.39, 0.4), desk_dark=False, window=True)
        # window wall with the port outside: crane silhouettes against a dusk sky, stacks, floodlights
        fr = pbr("WinFrame", (0.2, 0.2, 0.22), 0.4, 0.6)
        for z in (0.95, 2.25):
            box("WinSill", (0, 1.55, z), (2.9, 0.12, 0.05), fr)
        for x in (-1.42, 0, 1.42):
            box("WinMull", (x, 1.55, 1.6), (0.05, 0.1, 1.35), fr)
        box("WinGlass", (0, 1.56, 1.6), (2.8, 0.01, 1.3), glass("WinG", (0.9, 0.93, 0.95), 0.0))
        steel = pbr("CraneSteel", (0.08, 0.08, 0.09), 0.5, 0.5)
        for k, x in enumerate((-30, 5, 40)):
            for sx in (-4, 4):
                box("CraneLeg", (x + sx, 90 + k * 10, 18), (0.8, 0.8, 36), steel)
            box("CraneBoom", (x, 80 + k * 10, 38), (1.2, 60, 1.6), steel)
            box("CraneLamp", (x, 70 + k * 10, 37), (0.4, 0.4, 0.4), emissive("CraneLamp", (1.0, 0.65, 0.3), 80))
        cols = [(0.25, 0.05, 0.035), (0.04, 0.1, 0.2), (0.06, 0.14, 0.08), (0.3, 0.2, 0.06)]
        r = np.random.default_rng(5)
        for k in range(26):
            box("Stack", (r.uniform(-60, 60), r.uniform(40, 80), 1.3 + 2.6 * r.integers(0, 3)), (12.2, 2.44, 2.6), pbr(f"C{k%4}", cols[k % 4], 0.6))
        box("Yard", (0, 70, -0.6), (300, 120, 1), pbr("Yard", (0.12, 0.12, 0.12), 0.8))
        mf = os.path.join(GEN, "manifest_page.png")
        if not os.path.exists(mf):
            from sc_newsdesk import manifest_page
            manifest_page(mf)
        board = pbr("Clipboard", (0.35, 0.25, 0.15), 0.6)
        box("Board", (0.0, 0.56, DZ + 0.025), (0.24, 0.33, 0.006), board, bevel=0.003, rot=(0, 0, 0.1))
        clip = brushed_metal("Clip", (0.7, 0.7, 0.72), (0.15, 0.3), 0.4)
        box("Clip", (-0.016, 0.72, DZ + 0.034), (0.1, 0.03, 0.012), clip, rot=(0, 0, 0.1))
        plane("Manifest", (0.0, 0.55, DZ + 0.0295), (0.21, 0.297), (0, 0, 0.1), tex_mat("Manifest", mf))
        box("Radio", (0.42, 0.7, DZ + 0.09), (0.06, 0.035, 0.16), pbr("Radio", (0.05, 0.05, 0.05), 0.5), bevel=0.006)
        box("Antenna", (0.43, 0.7, DZ + 0.22), (0.008, 0.008, 0.1), pbr("Ant", (0.05, 0.05, 0.05), 0.5))
        vest = pbr("Vest", (0.85, 0.55, 0.02), 0.7)
        box("Vest", (-0.55, 0.5, DZ + 0.03), (0.35, 0.3, 0.02), vest, rot=(0, 0, 0.3))
        box("VestStripe", (-0.55, 0.5, DZ + 0.041), (0.35, 0.03, 0.002), pbr("Reflect", (0.8, 0.8, 0.8), 0.2, 0.8), rot=(0, 0, 0.3))
        cyl("Mug", (0.55, 0.25, DZ + 0.06), 0.045, 0.1, pbr("Mug", (0.6, 0.6, 0.6), 0.3), verts=24)
        area_light((0, 1.2, 1.7), (math.radians(90), 0, 0), 2.6, 120, (1.0, 0.72, 0.55)).visible_camera = False
        area_light((0, 0, 2.9), (0, 0, 0), 1.6, 35, (0.95, 0.97, 1.0)).visible_camera = False
        c["focus"] = Vector((0.0, 0.55, DZ + 0.03))
    else:   # ledger
        world_flat((0.005, 0.006, 0.009), 1.0)
        desk_room(wall_col=(0.12, 0.125, 0.13))
        scr = ledger_screen(os.path.join(GEN, "ledger_screen.png"))
        bez = pbr("Bezel", (0.02, 0.02, 0.022), 0.4)
        box("Monitor", (0.0, 0.62, DZ + 0.34), (0.62, 0.03, 0.37), bez, bevel=0.005)
        plane("Screen", (0.0, 0.603, DZ + 0.34), (0.59, 0.335), (math.radians(90), 0, 0), tex_mat("Ledger", scr, rough=0.3, emit=1.3))
        box("Stand", (0.0, 0.66, DZ + 0.1), (0.08, 0.08, 0.2), bez); box("StandFoot", (0.0, 0.62, DZ + 0.03), (0.25, 0.18, 0.012), bez)
        box("Keyboard", (0.0, 0.3, DZ + 0.03), (0.44, 0.14, 0.015), bez, bevel=0.003)
        box("Mouse", (0.32, 0.3, DZ + 0.035), (0.06, 0.1, 0.03), bez, bevel=0.01)
        sl = area_light((0.0, 0.5, DZ + 0.34), (math.radians(90), 0, 0), 0.6, 4, (0.9, 0.95, 1.0)); sl.visible_camera = False
        # the empty office chair, pushed back, turned a little
        fab = fabric("ChairFab", (0.06, 0.065, 0.07), 0.85, 0.3, 300); legm = pbr("Leg", (0.05, 0.05, 0.05), 0.4, 0.8)
        from sc_invest import office_chair
        office_chair((0.15, -0.35, 0), math.radians(200), fab, legm)
        lamp((-0.65, 0.75, 0), (0.0, 0.3, DZ), energy=60)
        area_light((1.4, -1.6, 2.4), (0, 0, 0), 2.0, 45, (0.55, 0.65, 0.9)).visible_camera = False
        k = area_light((-0.6, -1.2, 1.4), (0, 0, 0), 0.8, 18, (1.0, 0.85, 0.7)); point_at(k, (0.15, -0.35, 0.6)); k.visible_camera = False
        c["screen"] = Vector((0.0, 0.6, DZ + 0.34))
    return c


def anim_binder(c, t):
    k = min(1.0, max(0.0, (t - 0.12) / 0.7))                     # the mark is drawn over the middle of the shot
    L_ = c["hl_len"] * ease(k)
    c["hl"].scale = (max(0.001, L_), 0.009, 1)
    tip = Vector((c["hl_x0"] + L_, c["row_y"], DZ + 0.046))
    pen = c["pen"]; pen.location = tip + Vector((0, 0, 0.002))
    pen.location.z += 0.012 * (1 - min(1.0, t / 0.12)) + 0.012 * max(0.0, (t - 0.82) / 0.18)    # lands, draws, lifts


def anim_printer(c, t):
    sec = t * FRAMES["printer"] / 24
    for k, pg in enumerate(c["pages"]):
        t0 = 0.8 + k * 1.6                                         # a page every 1.6 s
        u = min(1.0, max(0.0, (sec - t0) / 1.1))                   # slides out over 1.1 s, then drops onto the stack
        a = c["out0"]; b = c["tray"] + Vector((0, 0, 0.002 * k))
        if sec < t0:
            pg.location = a + Vector((0, 0.16, -0.06))             # still inside the printer body (not visible)
        else:
            pg.location = (a + Vector((0, 0.16, -0.06))).lerp(a, min(1.0, (sec - t0) / 0.35)) if sec - t0 < 0.35 else a.lerp(b, ease(min(1.0, (sec - t0 - 0.35) / 0.75)))


def anim_none(c, t):
    pass


MOVES = {
    "binder": dict(kind="anim", dof=2.0, far=6.0, anim=anim_binder,
                   cam=lambda c, t: (Vector((0.38, -0.12, 1.02)).lerp(Vector((0.3, -0.02, 0.98)), ease(t)), c["focus"] + Vector((0.02, 0, 0)), 50),
                   focus=lambda c, t: c["focus"]),
    "printer": dict(kind="anim", dof=2.4, far=6.0, anim=anim_printer,
                    cam=lambda c, t: (Vector((0.48, -0.62, 1.32)).lerp(Vector((0.38, -0.5, 1.27)), ease(t)), c["tray"] + Vector((0, 0.12, 0.02)), 40),
                    focus=lambda c, t: c["tray"] + Vector((0, 0.1, 0.03))),
    "letter": dict(kind="anim", dof=2.2, far=6.0, anim=anim_none,
                   cam=lambda c, t: (Vector((0.32, -0.32, 1.12)).lerp(Vector((0.2, -0.18, 1.06)), ease(t)), c["focus"] + Vector((0, 0.04, 0)), 45),
                   focus=lambda c, t: c["focus"]),
    "clipboard": dict(kind="anim", dof=2.8, far=200.0, anim=anim_none,
                      cam=lambda c, t: (Vector((-0.36, -0.55, 1.22)).lerp(Vector((-0.26, -0.43, 1.18)), ease(t)), Vector((0.04, 0.7, 0.98)), 28),
                      focus=lambda c, t: c["focus"]),
    "ledger": dict(kind="anim", dof=3.2, far=8.0, anim=anim_none,
                   cam=lambda c, t: (Vector((0.08, 0.05, 1.12)).lerp(Vector((1.0, -2.4, 1.45)), ease(t)), c["screen"].lerp(Vector((0.05, 0.05, 0.8)), ease(t) ** 1.5), 38 - 6 * ease(t)),
                   focus=lambda c, t: c["screen"].lerp(Vector((0.15, -0.35, 0.6)), ease(t))),
}
