"""CH4/CH5 (new): a real office desk, house style. Variants:
  night   : a dark office at night: wooden desk, brass lamp, papers, a laptop whose screen lights up with a generic
            news page (grey headline bars and columns of grey text, no masthead), a second monitor, and the desk
            phone from Ch1-3 (handset in its cradle, line light that blinks while it rings).
  customs : a daytime customs office: the same desk by a window, a male officer (seen from behind) checking a
            paper manifest; a stamp and a tray of forms.
Moves
  news_push   CH4 3A  push in as the laptop screen lights up with the news page
  news_second CH4 7A  a different angle: the second monitor, the page scrolling
  handset     CH4 3B  medium shot: the handset settles into its cradle (no hand in frame)
  ring        CH4 7C  the phone rings, its line light blinking, nobody answers
  manifest    CH5 9B  medium, from behind the officer as he checks the manifest
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
VARIANT_FOR = {"news_push": "night", "news_second": "night", "handset": "night", "ring": "night", "manifest": "customs"}
DESK_Z = 0.74
LIGHT_ON = 14                     # frame the laptop screen lights up (news_push)


def news_page(path, seed=0, W=1440, H=900):
    """A generic news web page: grey bars only, no masthead, no legible text."""
    r = np.random.default_rng(seed)
    im = Image.new("RGB", (W, H), (244, 244, 242)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 64], fill=(222, 223, 225))                              # plain nav bar, no logo
    for k in range(6):
        d.rectangle([60 + k * 150, 26, 60 + k * 150 + 90, 38], fill=(170, 172, 176))
    d.rectangle([60, 104, 1000, 136], fill=(60, 62, 66)); d.rectangle([60, 150, 760, 182], fill=(60, 62, 66))   # headline
    d.rectangle([60, 206, 640, 222], fill=(140, 142, 146))                        # standfirst
    d.rectangle([60, 250, 880, 560], fill=(196, 199, 203))                        # photo block (plain)
    for col in range(2):
        x0 = 60 + col * 440
        for k in range(10):
            w = int(r.uniform(330, 400)) if k % 4 != 3 else int(r.uniform(150, 260))
            d.rectangle([x0, 590 + k * 28, x0 + w, 600 + k * 28], fill=(150, 152, 156))
    d.rectangle([960, 250, 1380, 270], fill=(90, 92, 96))                         # sidebar
    for k in range(14):
        d.rectangle([960, 300 + k * 30, 960 + int(r.uniform(240, 400)), 310 + k * 30], fill=(170, 172, 176))
    im.save(path); return path


def manifest_page(path, W=1240, H=1754):
    """A generic shipping manifest: a ruled table of grey bars, a header block, no names or logos."""
    im = Image.new("RGB", (W, H), (238, 235, 226)); d = ImageDraw.Draw(im)
    d.rectangle([80, 80, 700, 120], fill=(70, 70, 72)); d.rectangle([80, 140, 520, 160], fill=(130, 130, 132))
    d.rectangle([800, 80, 1160, 220], outline=(90, 90, 92), width=4)
    y0 = 300
    for row in range(28):
        y = y0 + row * 46
        d.line([80, y, 1160, y], fill=(150, 150, 150), width=2)
        for cx, w in ((100, 180), (330, 300), (690, 120), (860, 140), (1040, 90)):
            if row:
                d.rectangle([cx, y + 14, cx + int(w * (0.5 + 0.5 * ((row * 7 + cx) % 5) / 4)), y + 26], fill=(110, 110, 112))
    for cx in (80, 310, 670, 840, 1020, 1160):
        d.line([cx, y0, cx, y0 + 27 * 46], fill=(150, 150, 150), width=2)
    im.save(path); return path


def screen_mat(name, img_path, on_frame=None, strength=1.25, scroll=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); L.new(tc.outputs['UV'], mp.inputs['Vector'])
    if scroll:                                                   # the page drifts up slowly (frame driver)
        d = mp.inputs['Location'].driver_add("default_value", 1).driver; d.type = 'SCRIPTED'; d.expression = f"-frame * {scroll}"
    tx = N.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(img_path); tx.extension = 'EXTEND'
    L.new(mp.outputs['Vector'], tx.inputs['Vector'])
    em = N.new("ShaderNodeEmission"); L.new(tx.outputs['Color'], em.inputs['Color'])
    v = N.new("ShaderNodeValue")
    d = v.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
    d.expression = (f"{strength} * min(1, max(0.02, (frame - {on_frame}) / 10))" if on_frame is not None else f"{strength}")
    L.new(v.outputs[0], em.inputs['Strength']); L.new(em.outputs[0], out.inputs['Surface'])
    return m


def screen_plane(name, loc, size, rot, mat):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1); o.data.materials.append(mat)
    return o


def desk_phone(c, loc):
    """The Ch1-3 desk phone: body, handset in the cradle, keypad, a line light that blinks (frame driver)."""
    phone_m = pbr("PhoneBody", (0.03, 0.03, 0.033), 0.35)
    x, y, z = loc
    box("DeskPhone", (x, y, z + 0.03), (0.22, 0.2, 0.05), phone_m, bevel=0.01, rot=(math.radians(-10), 0, 0))
    hs = box("Handset", (x - 0.07, y + 0.01, z + 0.075), (0.06, 0.21, 0.035), phone_m, bevel=0.012)
    hs.rotation_mode = 'XYZ'
    c["handset"] = hs; c["handset_rest"] = Vector(hs.location); c["phone"] = Vector((x, y, z + 0.05))
    keys = pbr("Keys", (0.12, 0.12, 0.13), 0.5)
    for i in range(3):
        for j in range(4):
            box("Key", (x + 0.02 + i * 0.03, y - 0.06 + j * 0.028, z + 0.058), (0.02, 0.018, 0.006), keys)
    lm = bpy.data.materials.new("RingLight"); lm.use_nodes = True
    N = lm.node_tree.nodes; L = lm.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.35, 0.15, 1)
    v = N.new("ShaderNodeValue"); d = v.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
    d.expression = "var * 8 * (1 if (frame % 24) < 12 else 0.02)"
    var = d.variables.new(); var.name = "var"; var.targets[0].id_type = 'SCENE'; var.targets[0].id = bpy.context.scene
    var.targets[0].data_path = '["ringing"]'
    L.new(v.outputs[0], em.inputs['Strength']); L.new(em.outputs[0], out.inputs['Surface'])
    box("RingLED", (x + 0.08, y + 0.075, z + 0.06), (0.025, 0.012, 0.01), lm)
    rl = bpy.data.lights.new("RingGlow", 'POINT'); rl.color = (1.0, 0.4, 0.2); rl.shadow_soft_size = 0.02
    dl = rl.driver_add("energy").driver; dl.type = 'SCRIPTED'; dl.expression = "var * 2.5 * (1 if (frame % 24) < 12 else 0.02)"
    v2 = dl.variables.new(); v2.name = "var"; v2.targets[0].id_type = 'SCENE'; v2.targets[0].id = bpy.context.scene
    v2.targets[0].data_path = '["ringing"]'
    ro = bpy.data.objects.new("RingGlow", rl); bpy.context.collection.objects.link(ro); ro.location = (x + 0.08, y + 0.06, z + 0.1)


def build(variant=None):
    c = {}
    os.makedirs(GEN, exist_ok=True)
    from sc_memo_desk import page_texture, page
    sc = bpy.context.scene
    sc["ringing"] = 0.0
    day = variant == "customs"
    if day:
        world_sky(sun_elev_deg=35, sun_rot_deg=200, strength=0.25, tint=(0.95, 0.97, 1.0))
    else:
        world_flat((0.004, 0.005, 0.008), 1.0)
    # room
    wall = pbr("OfficeWall", (0.42, 0.42, 0.4) if day else (0.05, 0.05, 0.055), 0.9)
    box("Floor", (0, 0, -0.01), (8, 8, 0.02), pbr("Carpet", (0.12, 0.12, 0.13) if day else (0.03, 0.03, 0.035), 0.95))
    box("WallBack", (0, 1.6, 1.5), (8, 0.1, 3.0), wall)
    box("WallL", (-2.2, 0, 1.5), (0.1, 8, 3.0), wall)
    box("Ceil", (0, 0, 3.0), (8, 8, 0.1), pbr("Ceil", (0.6, 0.6, 0.6) if day else (0.03, 0.03, 0.03), 0.9))
    # window on the back wall (cool night / daylight) with blinds
    box("Window", (1.1, 1.54, 1.6), (1.6, 0.02, 1.3), emissive("WinOut", (0.75, 0.82, 0.9) if day else (0.12, 0.16, 0.26), 2.2 if day else 0.5))
    for k in range(22):
        box("Blind", (1.1, 1.5, 1.0 + k * 0.056), (1.65, 0.05, 0.006), pbr("BlindM", (0.6, 0.6, 0.58), 0.5), rot=(math.radians(55), 0, 0))
    if day:
        area_light((1.1, 1.2, 1.6), (math.radians(90), 0, 0), 1.6, 160, (0.9, 0.95, 1.0))
        for yy in (-0.8, 0.8):
            area_light((0, yy, 2.9), (0, 0, 0), 1.2, 70, (1.0, 0.97, 0.92)).visible_camera = False
    # desk with drawers and a lamp
    desk = wood("Desk", (0.1, 0.06, 0.035), (0.24, 0.15, 0.08), scale=(0.3, 6, 6), rough=0.35, coat=0.3)
    box("DeskTop", (0, 0.6, DESK_Z), (1.6, 0.8, 0.04), desk, bevel=0.005)
    box("DeskPed", (0.6, 0.6, DESK_Z / 2), (0.42, 0.74, DESK_Z), desk)
    box("DeskLeg", (-0.75, 0.6, DESK_Z / 2), (0.05, 0.72, DESK_Z), desk)
    brass = brushed_metal("Brass", (0.75, 0.55, 0.3), (0.2, 0.35), 0.3)
    cyl("LampBase", (-0.6, 0.85, DESK_Z + 0.01), 0.08, 0.02, brass, verts=32)
    cyl("LampStem", (-0.6, 0.85, DESK_Z + 0.22), 0.01, 0.42, brass, verts=12)
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.12, radius2=0.05, depth=0.15, location=(-0.52, 0.78, DESK_Z + 0.45), rotation=(math.radians(-150), math.radians(20), 0))
    sh = bpy.context.active_object; sh.data.materials.append(pbr("Shade", (0.05, 0.12, 0.07), 0.35, 0.6)); sh.visible_shadow = False
    lamp = bpy.data.lights.new("Lamp", 'SPOT'); lamp.energy = 70 if not day else 20; lamp.spot_size = math.radians(80); lamp.spot_blend = 0.5
    lamp.color = (1.0, 0.82, 0.6); lamp.shadow_soft_size = 0.03
    lo = bpy.data.objects.new("Lamp", lamp); bpy.context.collection.objects.link(lo); lo.location = (-0.5, 0.76, DESK_Z + 0.42); point_at(lo, (-0.15, 0.55, DESK_Z))
    # papers
    memo = page_texture(os.path.join(GEN, "page_memo.png"), "memo", 4)
    memo2 = page_texture(os.path.join(GEN, "page_memo2.png"), "memo", 9)
    for k, (dx, dy, r_, tx) in enumerate(((-0.25, 0.45, 0.15, memo), (-0.3, 0.42, -0.05, memo2), (0.32, 0.38, 0.3, memo))):
        page(f"Paper{k}", (dx, dy, DESK_Z + 0.022 + 0.001 * k), r_, tx)
    box("Folder", (0.35, 0.82, DESK_Z + 0.025), (0.25, 0.33, 0.01), pbr("Manila", (0.52, 0.38, 0.2), 0.75), rot=(0, 0, -0.1))
    cyl("Mug", (-0.68, 0.45, DESK_Z + 0.07), 0.04, 0.1, pbr("Mug", (0.55, 0.55, 0.57), 0.3), verts=24)
    if not day:
        news = news_page(os.path.join(GEN, "news_page_a.png"), 1); news2 = news_page(os.path.join(GEN, "news_page_b.png"), 5)
        # laptop (screen lights up at LIGHT_ON)
        alu = pbr("LaptopAlu", (0.3, 0.31, 0.33), 0.35, 1.0)
        box("Base", (0.0, 0.5, DESK_Z + 0.027), (0.33, 0.23, 0.012), alu, bevel=0.004)
        box("Lid", (0.0, 0.62, DESK_Z + 0.13), (0.33, 0.008, 0.21), alu, bevel=0.004, rot=(math.radians(-12), 0, 0))
        scr = screen_plane("LaptopScreen", (0.0, 0.6155, DESK_Z + 0.13), (0.31, 0.195), (math.radians(78), 0, 0),
                           screen_mat("NewsA", news, on_frame=LIGHT_ON, strength=1.3))
        c["laptop"] = Vector((0.0, 0.615, DESK_Z + 0.13))
        sl = area_light((0.0, 0.59, DESK_Z + 0.13), (0, 0, 0), 0.25, 1.2, (0.85, 0.9, 1.0)); point_at(sl, (0.0, 0.0, 1.2))
        sl.visible_camera = False; sl.visible_glossy = False
        dsl = sl.data.driver_add("energy").driver; dsl.type = 'SCRIPTED'; dsl.expression = f"1.2 * min(1, max(0.02, (frame - {LIGHT_ON}) / 10))"
        # second monitor on the right, page scrolling
        bez = pbr("Bezel", (0.02, 0.02, 0.022), 0.4)
        box("Monitor", (0.55, 0.85, DESK_Z + 0.3), (0.56, 0.03, 0.34), bez, bevel=0.004, rot=(0, 0, math.radians(-18)))
        box("MonStand", (0.55, 0.88, DESK_Z + 0.08), (0.08, 0.1, 0.16), bez)
        screen_plane("MonScreen", (0.545, 0.833, DESK_Z + 0.3), (0.53, 0.31), (math.radians(90), 0, math.radians(-18)),
                     screen_mat("NewsB", news2, strength=1.2, scroll=0.0006))
        c["monitor"] = Vector((0.545, 0.833, DESK_Z + 0.3))
        desk_phone(c, (-0.38, 0.35, DESK_Z + 0.02))
        moon = area_light((1.1, 1.0, 1.7), (math.radians(90), 0, 0), 1.4, 6, (0.45, 0.6, 1.0)); point_at(moon, (0, 0.5, DESK_Z))
    else:
        mf = manifest_page(os.path.join(GEN, "manifest_page.png"))
        page("Manifest", (0.05, 0.42, DESK_Z + 0.024), 0.08, mf)
        page("Manifest2", (0.12, 0.47, DESK_Z + 0.023), -0.12, mf)
        box("Tray", (-0.42, 0.75, DESK_Z + 0.04), (0.32, 0.25, 0.06), pbr("Tray", (0.15, 0.15, 0.16), 0.5))
        cyl("Stamp", (0.45, 0.4, DESK_Z + 0.06), 0.025, 0.09, pbr("StampH", (0.08, 0.08, 0.09), 0.4), verts=16)
        box("StampPad", (0.52, 0.32, DESK_Z + 0.03), (0.1, 0.07, 0.015), pbr("Pad", (0.1, 0.12, 0.25), 0.5))
        box("Cabinet", (-0.95, 1.33, 0.5), (0.8, 0.45, 1.0), pbr("CabinetM", (0.55, 0.56, 0.57), 0.45, 0.6), bevel=0.01)
        for k in range(6):                                        # binders standing on the cabinet
            box("Binder", (-1.25 + k * 0.1, 1.35, 1.17), (0.07, 0.28, 0.32), pbr(f"Binder{k % 3}", ((0.15, 0.2, 0.32), (0.35, 0.12, 0.1), (0.2, 0.22, 0.2))[k % 3], 0.6))
        from sc_invest import person, seat_person, office_chair
        from human import reach, fingers_curl
        off = person("Officer", 1.0, 46, "male_casualsuit01", "short01", hv=0.2, cval=0.35)
        seat_person(off, (0.05, -0.05, 0), math.pi, lean=22)          # faces +Y, toward the desk (back to camera)
        office_chair((0.05, -0.13, 0), math.pi, fabric("ChairFab", (0.08, 0.09, 0.1), 0.85, 0.3, 300), pbr("Leg", (0.05, 0.05, 0.05), 0.4, 0.8))
        c["officer"] = off
        bpy.context.view_layer.update()
        for sd, sg in (("L", -1), ("R", 1)):                         # both hands resting flat on the manifest
            reach(off, sd, Vector((0.05 + 0.13 * sg, 0.36, DESK_Z + 0.03)), Vector((sg * 0.8, -0.3, -0.5)), Vector((0, 1, -0.15)))
        fingers_curl(off, 15, thumb=8)
        off.rot("head", (1, 0, 0), 18)
        bpy.context.view_layer.update()
        c["manifest"] = Vector((0.05, 0.42, DESK_Z + 0.03))
    return c


def anim_news(c, t):
    bpy.context.scene["ringing"] = 0.0


def anim_handset(c, t):
    """Handset lowered into the cradle over the first ~30% of the shot, a small settle, then still."""
    bpy.context.scene["ringing"] = 0.0
    hs = c["handset"]; rest = c["handset_rest"]
    k = min(1.0, t / 0.22); e = 1 - (1 - k) ** 3              # a short drop (3 cm) and a small rock as it seats
    hs.location = rest + Vector((0.0, -0.008, 0.032)) * (1 - e)
    hs.rotation_euler = (math.radians(7) * (1 - e) + math.radians(1.2) * math.sin(k * math.pi * 2) * (1 - k), 0, 0)


def anim_ring(c, t):
    bpy.context.scene["ringing"] = 1.0
    c["handset"].location = c["handset_rest"]; c["handset"].rotation_euler = (0, 0, 0)


def anim_manifest(c, t):
    off = c["officer"]
    off.rot("head", (0, 0, 1), 4 * math.sin(t * 3.0))                # reading across the lines
    bpy.context.view_layer.update()


MOVES = {
    "news_push": dict(kind="anim", dof=2.2, far=8.0, anim=anim_news,
                      cam=lambda c, t: (Vector((0.55, -0.75, 1.12)).lerp(Vector((0.22, -0.18, 1.0)), ease(t)), c["laptop"], 40),
                      focus=lambda c, t: c["laptop"]),
    "news_second": dict(kind="anim", dof=2.4, far=8.0, anim=anim_news,
                        cam=lambda c, t: (Vector((-0.35, -0.4, 1.18)).lerp(Vector((-0.15, -0.15, 1.12)), ease(t)), c["monitor"], 45),
                        focus=lambda c, t: c["monitor"]),
    "handset": dict(kind="anim", dof=2.6, far=8.0, anim=anim_handset,
                    cam=lambda c, t: (Vector((-1.15, -0.55, 1.28)).lerp(Vector((-1.0, -0.4, 1.24)), ease(t)), c["phone"] + Vector((0.12, 0.12, 0.0)), 38),
                    focus=lambda c, t: c["phone"]),
    "ring": dict(kind="anim", dof=2.6, far=8.0, anim=anim_ring,
                 cam=lambda c, t: (Vector((0.4, -0.7, 1.25)).lerp(Vector((0.22, -0.5, 1.2)), ease(t)), c["phone"] + Vector((0.05, 0.1, 0.0)), 40),
                 focus=lambda c, t: c["phone"]),
    "manifest": dict(kind="anim", dof=3.2, far=8.0, anim=anim_manifest,
                     cam=lambda c, t: (Vector((-1.45, -1.75, 1.62)).lerp(Vector((-1.3, -1.6, 1.58)), ease(t)), c["manifest"] + Vector((0.0, 0.05, 0.25)), 35),
                     focus=lambda c, t: c["manifest"]),
}
