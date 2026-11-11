"""CH1 SET 1B (dramatization): a federal office in the morning. An official in a dark suit sits at a desk and signs
the printed rule; a flag on a stand in the corner, window light through tall windows. Medium shot, slow push.
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from human import Human, add_asset, reset_pose, fingers_curl, pose_sit, _world_verts, reach
import ph
import skia

EXPOSURE = 0.2
DUR = {"sign": 6.0}            # estimate until the chapter 1 voiceover arrives
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")


def rule_page(path, W=850, H=1100):
    s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.Color4f(0.95, 0.94, 0.91, 1))
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(skia.Color4f(0.12, 0.16, 0.3, 1)); c.drawCircle(W / 2, 110, 46, p)          # a generic round seal
    p.setColor4f(skia.Color4f(0.95, 0.94, 0.91, 1)); c.drawCircle(W / 2, 110, 36, p)
    p.setColor4f(skia.Color4f(0.12, 0.16, 0.3, 1)); c.drawCircle(W / 2, 110, 28, p)
    f = skia.Font(skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"), 22)
    t = "EXPORT ADMINISTRATION REGULATIONS"; c.drawString(t, W / 2 - f.measureText(t) / 2, 200, f, p)
    p.setColor4f(skia.Color4f(0.4, 0.4, 0.42, 1))
    rng = np.random.default_rng(2); y = 260
    while y < H - 220:
        for k in range(rng.integers(3, 6)):
            c.drawRect(skia.Rect.MakeXYWH(80, y, (W - 160) * rng.uniform(0.85, 1.0), 7), p); y += 20
        y += 18
    p.setColor4f(skia.Color4f(0.2, 0.2, 0.22, 1)); c.drawRect(skia.Rect.MakeXYWH(W - 380, H - 150, 300, 2), p)
    s.makeImageSnapshot().save(path, skia.kPNG); return path


def build(variant=None):
    c = {}
    world_sky(sun_elev_deg=18, sun_rot_deg=120, strength=0.6, tint=(0.9, 0.93, 1.0))
    os.makedirs(GEN, exist_ok=True)
    # room: wood panelling, carpet, tall windows on the left
    panel = ph.texture("wood_table_001", scale=1.2) if False else wood("Panel", (0.09, 0.05, 0.03), (0.2, 0.12, 0.07), scale=(0.3, 6, 6), rough=0.35, coat=0.3)
    box("Floor", (0, 0, -0.01), (8, 8, 0.02), fabric("Carpet", (0.12, 0.1, 0.09), 0.95, 0.2, 500))
    box("WallBack", (0, 3.0, 1.6), (8, 0.1, 3.2), panel)
    box("WallFront", (0, -2.9, 1.6), (8, 0.1, 3.2), panel)                       # behind him, seen in the shot
    for k in range(5):                                                         # framed portraits/certificates on the panelling
        box("Frame", (-1.6 + k * 0.8, -2.83, 1.75), (0.5, 0.03, 0.62), pbr("FrameGold", (0.5, 0.38, 0.18), 0.35, 0.9))
        box("FrameArt", (-1.6 + k * 0.8, -2.81, 1.75), (0.42, 0.02, 0.54), pbr(f"Art{k}", (0.35 + 0.05 * k, 0.32, 0.28), 0.8))
    box("WallR", (3.4, 0, 1.6), (0.1, 8, 3.2), panel)
    wall = pbr("WallCream", (0.6, 0.57, 0.5), 0.85)
    for y in (-2.6, -0.2, 2.2):
        box("WinPier", (-3.4, y, 1.6), (0.12, 0.8, 3.2), wall)
    for y in (-1.4, 1.0):
        box("WinGlass", (-3.42, y, 1.75), (0.02, 1.6, 2.4), glass("Win", (0.9, 0.93, 0.95), 0.01))
        box("Sill", (-3.35, y, 0.5), (0.2, 1.7, 0.08), wall)
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 4.0; pt.size_y = 2.4; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (-3.45, -0.2, 1.75); po.rotation_euler = (0, math.radians(90), 0)
    sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 3.0; sun.angle = math.radians(1.5); sun.color = (1.0, 0.93, 0.82)
    so = bpy.data.objects.new("Sun", sun); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(58), math.radians(-35), math.radians(80))
    box("Ceiling", (0, 0, 3.22), (8, 8, 0.04), pbr("Ceil", (0.7, 0.68, 0.64), 0.9))
    # desk (scanned), lamp, papers
    ph.model("metal_office_desk", loc=(0.2, 0.6, 0.0))
    cyl("LampBase", (0.85, 0.85, 0.81), 0.08, 0.03, pbr("LampBrass", (0.55, 0.42, 0.22), 0.3, 1.0), verts=24)
    cyl("LampStem", (0.85, 0.85, 1.05), 0.012, 0.48, pbr("LampBrass", (0.55, 0.42, 0.22), 0.3, 1.0), verts=12)
    cyl("LampShade", (0.8, 0.8, 1.28), 0.075, 0.12, pbr("LampGreen", (0.04, 0.2, 0.1), 0.25, 0.0, **{'Coat Weight': 0.8}), verts=32, rot=(0, math.radians(70), math.radians(45)))
    pg = rule_page(os.path.join(GEN, "rule_page.png"))
    pm = bpy.data.materials.new("RulePage"); pm.use_nodes = True
    N = pm.node_tree.nodes; L = pm.node_tree.links; t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(pg)
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['UV'], t.inputs['Vector']); L.new(t.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0.25, 0.42, 0.795)); page = bpy.context.active_object
    page.scale = (0.21, 0.28, 1); page.rotation_euler = (0, 0, math.radians(8)); page.data.materials.append(pm)
    for k in range(4):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0.7 + k * 0.004, 0.55, 0.792 + k * 0.001))
        o = bpy.context.active_object; o.scale = (0.21, 0.28, 1); o.rotation_euler = (0, 0, math.radians(-6 + k * 3)); o.data.materials.append(pm)
    pen = cyl("Pen", (0.3, 0.4, 0.82), 0.0055, 0.14, pbr("PenBlack", (0.01, 0.01, 0.012), 0.2, 0.0, **{'Coat Weight': 1.0}), verts=16)
    c.update(page=page, pen=pen)
    # flag on a stand in the corner (gentle sway)
    fimg = os.path.join(GEN, "us_flag.png")
    if not os.path.exists(fimg):
        import sc_capitol; sc_capitol.flag_image(fimg)
    fm = bpy.data.materials.new("Flag"); fm.use_nodes = True
    N = fm.node_tree.nodes; L = fm.node_tree.links; t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(fimg)
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['UV'], t.inputs['Vector']); L.new(t.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    N["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.5; N["Principled BSDF"].inputs['Roughness'].default_value = 0.7
    cyl("FlagPole", (1.35, -2.25, 1.1), 0.02, 2.2, pbr("Brass", (0.6, 0.45, 0.22), 0.3, 1.0), verts=12)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=30, size=1, location=(1.35, -2.25, 1.5), rotation=(math.radians(90), 0, math.radians(150)))
    f = bpy.context.active_object; f.scale = (0.5, 0.95, 1); f.data.materials.append(fm)
    f.location.x += 0.25 * math.cos(math.radians(150)); f.location.y += 0.25 * math.sin(math.radians(150))
    wv = f.modifiers.new("wave", 'WAVE'); wv.height = 0.03; wv.width = 0.4; wv.speed = 0.02
    sub = f.modifiers.new("sub", 'SUBSURF'); sub.levels = 1
    # window-side key and the desk lamp's warm pool
    k = area_light((-2.6, 0.9, 2.1), (0, 0, 0), 1.8, 260, (0.9, 0.94, 1.0)); point_at(k, (0.2, 0.1, 1.0)); k.visible_camera = False
    dl = bpy.data.lights.new("DeskLamp", 'SPOT'); dl.energy = 60; dl.spot_size = math.radians(70); dl.spot_blend = 0.6; dl.color = (1.0, 0.75, 0.48)
    dlo = bpy.data.objects.new("DeskLamp", dl); bpy.context.collection.objects.link(dlo); dlo.location = (0.55, 0.65, 1.45); point_at(dlo, (0.3, 0.45, 0.8))
    fill = area_light((1.5, -2.0, 2.4), (0, 0, 0), 2.0, 40, (1.0, 0.85, 0.7)); point_at(fill, (0.2, 0.0, 1.0)); fill.visible_camera = False
    # the official
    h = Human("Official", gender=1.0, years=58, muscle=0.5, weight=0.55, height=0.5, eyelashes="eyelashes01",
              skin="old_lightskinned_male_diffuse.png")
    add_asset(h, "clothes", "male_elegantsuit01", val=0.12, rough=0.55); add_asset(h, "clothes", "shoes02", val=0.15)
    add_asset(h, "hair", "short04", sat=0.0, val=0.6)
    reset_pose(h); pose_sit(h, lean=18)
    h.arm.rotation_euler = (0, 0, math.pi); h.arm.location = (0.2, -0.05, 0); bpy.context.view_layer.update()   # faces +Y (the desk)
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()
    c["h"] = h
    chair_m = pbr("ChairLeather", (0.03, 0.02, 0.015), 0.4, 0.0, **{'Coat Weight': 0.4})
    box("ChairSeat", (0.2, -0.12, 0.45), (0.56, 0.52, 0.1), chair_m, bevel=0.04)
    cb = box("ChairBack", (0.2, -0.42, 0.95), (0.58, 0.14, 0.95), chair_m, bevel=0.07)
    s_ = cb.modifiers.new("s", 'SUBSURF'); s_.levels = 2; s_.render_levels = 2
    animate(c, 0.0)
    return c


def animate(c, sec):
    """He reads, then signs: the pen traces a quick signature on the line at the bottom of the page."""
    h = c["h"]; page = c["page"]; M = page.matrix_world
    sign = min(1.0, max(0.0, (sec - 1.8) / 2.4))
    if 0 < sign < 1:
        u = -0.1 + 0.55 * sign; v = -0.37 + 0.03 * math.sin(sign * 38) * (1 - abs(2 * sign - 1)) ** 0.3
        lift = 0.0
    else:
        u, v = (-0.1, -0.37) if sign == 0 else (0.45, -0.37); lift = 0.04
    tip = M @ Vector((u, v, 0.0)) + Vector((0, 0, 0.002 + lift))
    pen = c["pen"]; axis = Vector((0.15, -0.35, 0.92)).normalized()
    pen.location = tip + axis * 0.07; pen.rotation_mode = 'QUATERNION'; pen.rotation_quaternion = axis.to_track_quat('Z', 'Y')
    reach(h, "R", tip + axis * 0.09 + Vector((0.02, -0.05, 0.0)), Vector((-0.6, -0.4, -0.6)), Vector((0.1, 0.8, -0.6)))
    reach(h, "L", M @ Vector((-0.42, 0.05, 0.0)) + Vector((-0.05, -0.04, 0.05)), Vector((0.6, -0.4, -0.6)), Vector((0.2, 0.9, -0.3)))
    fingers_curl(h, 40, thumb=25)
    h.rot("neck01", (-1, 0, 0), 4); h.rot("head", (-1, 0, 0), 11 + 2 * math.sin(sec * 0.9))      # eyes on the page (he faces +Y)
    bpy.context.view_layer.update()


def anim_sign(c, t):
    animate(c, t * DUR["sign"])


def cam_sign(c, t):
    e = ease(t)
    loc = Vector((-1.55, 2.25, 1.4)).lerp(Vector((-1.2, 1.85, 1.35)), e)      # three-quarter front, across the desk
    return (loc, Vector((0.2, 0.05, 1.0)), 40)


MOVES = {"sign": dict(kind="anim", dof=2.8, far=12.0, cam=cam_sign, focus=lambda c, t: Vector((0.25, 0.25, 1.0)), anim=anim_sign)}
