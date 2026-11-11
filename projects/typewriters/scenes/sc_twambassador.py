"""AMBASSADOR'S OFFICE, Moscow 1984 (dramatization; the ambassador is an unnamed figure, back to camera or in silhouette).
Wood panelling, a partner desk, tall windows with sheer curtains, soft May light.

Intro 2A  handover  a courier crosses the office and hands over an envelope
Intro 2B  note      the ambassador, back to us, unfolds a handwritten note at the window
Ch1 8A    pocket    he reads it, folds it, pockets it (later)
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import typewriter as T

EXPOSURE = 0.0
DUR = {"handover": 4.5, "note": 5.0, "pocket": 4.5, "sign": 5.0, "folder": 4.5}
VARIANT_FOR = {"sign": "oval", "folder": "oval"}
OVAL_DESK = Vector((-1.25, 2.05, 0.0))
WIN_Y = 3.0


def note_image(path, seed=11):
    """A handwritten note: a few lines of loose pen strokes (illegible by design)."""
    import skia
    W_, H_ = 900, 1200
    s = skia.Surface(W_, H_); c = s.getCanvas(); c.clear(skia.Color4f(0.93, 0.92, 0.88, 1))
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.2, StrokeCap=skia.Paint.kRound_Cap)
    p.setColor4f(skia.Color4f(0.08, 0.1, 0.22, 0.9))
    rng = np.random.default_rng(seed)
    y = 170
    for line in range(9):
        x = 90 + (40 if line == 0 else 0)
        end = 820 if line < 8 else 420
        path_ = skia.Path(); path_.moveTo(x, y)
        while x < end:
            n = rng.integers(3, 8)                       # one "word" of loops
            for _ in range(n):
                dx = rng.uniform(10, 18); h = rng.uniform(10, 26) * (1.8 if rng.random() < 0.15 else 1)
                path_.cubicTo(x + dx * 0.2, y - h, x + dx * 0.9, y - h, x + dx, y + rng.uniform(-2, 4))
                x += dx
            c.drawPath(path_, p); x += rng.uniform(16, 28); path_ = skia.Path(); path_.moveTo(x, y)
        y += 92
    s.makeImageSnapshot().save(path, skia.kPNG)
    return path


def tex_mat(name, path, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True
    t = m.node_tree.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    m.node_tree.links.new(t.outputs[0], m.node_tree.nodes["Principled BSDF"].inputs['Base Color'])
    m.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = rough
    return m


def build(variant=None):
    c = {}
    w_ = world_sky(sun_elev_deg=30, sun_rot_deg=60, strength=0.5, tint=(0.88, 0.92, 1.0))
    w_.node_tree.nodes["Sky Texture"].sun_disc = False
    # ---------------------------------------------------------------- room x -3.5..3.5, y -3..3, h 3.2
    box("Floor", (0, 0, -0.01), (7, 6, 0.02), ph.texture("herringbone_parquet", scale=0.6, tint=(0.75, 0.72, 0.7)))
    box("Rug", (0, 0.3, 0.004), (3.6, 2.8, 0.008), fabric("Rug", (0.2, 0.12, 0.1), 0.95, 0.4, 600))
    panel = ph.texture("dark_paneled_wood", scale=0.8, name="Panel", tint=(0.7, 0.62, 0.55))
    plaster = ph.texture("beige_wall_001", scale=0.5, name="OfficePlaster", tint=(0.85, 0.83, 0.78))
    for (x, y, sx, sy) in ((0, -3.05, 7, 0.1), (-3.55, 0, 0.1, 6), (3.55, 0, 0.1, 6)):
        box("Wainscot", (x, y, 0.6), (sx, sy, 1.2), panel)
        box("Wall", (x, y, 2.2), (sx, sy, 2.0), plaster)
    box("Ceiling", (0, 0, 3.22), (7, 6, 0.04), plaster)
    box("Cornice", (0, 2.98, 3.12), (7, 0.08, 0.12), plaster)
    # window wall: two tall windows with sheer curtains; a garden and a plaster building outside
    for x0, w0 in ((-3.5, 0.9), (-1.0, 0.6), (1.6, 0.6), (3.0, 1.0)):
        pass
    for x, wdt in ((-2.75, 1.5), (0.3, 1.6), (3.0, 1.0)):
        box("WinPier", (x, WIN_Y + 0.05, 1.6), (wdt, 0.1, 3.2), plaster)
        box("WinPierPanel", (x, WIN_Y - 0.0, 0.6), (wdt, 0.12, 1.2), panel)
    frame = pbr("WinFrameO", (0.82, 0.8, 0.75), 0.4)
    gl = glass("OfficeGlass", (0.92, 0.94, 0.96))
    sheer = pbr("Sheer", (0.85, 0.84, 0.8), 0.9, 0.0, **{'Transmission Weight': 0.65, 'Subsurface Weight': 0.0})
    c["sheers"] = []
    for xc in (-1.25, 1.85):
        box("Sill", (xc, WIN_Y - 0.08, 0.9), (1.25, 0.25, 0.05), frame)
        box("Head", (xc, WIN_Y, 2.95), (1.0, 0.1, 0.5), plaster)
        box("Glass", (xc, WIN_Y + 0.04, 1.8), (1.0, 0.01, 1.8), gl)
        for dx in (-0.5, 0.0, 0.5):
            box("Mull", (xc + dx, WIN_Y + 0.02, 1.8), (0.05, 0.06, 1.8), frame)
        for dz in (0.9, 1.5, 2.1, 2.7):
            box("Trans", (xc, WIN_Y + 0.02, dz), (1.0, 0.06, 0.04), frame)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=2, size=1, location=(xc + 0.35, WIN_Y - 0.12, 1.75))
        sh = bpy.context.active_object; sh.scale = (0.55, 2.0, 1); sh.rotation_euler = (math.radians(90), 0, 0)
        sh.data.materials.append(sheer)
        wv = sh.modifiers.new("folds", 'WAVE'); wv.use_x = True; wv.use_y = False; wv.height = 0.025; wv.width = 0.08; wv.speed = 0.004; wv.narrowness = 0.6
        c["sheers"].append(sh)
        pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 1.0; pt.size_y = 1.8; pt.cycles.is_portal = True
        po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (xc, WIN_Y + 0.1, 1.8); po.rotation_euler = (math.radians(-90), 0, 0)
    sn = bpy.data.lights.new("Sun", 'SUN'); sn.energy = 2.2; sn.angle = math.radians(2); sn.color = (1.0, 0.93, 0.84)
    so = bpy.data.objects.new("Sun", sn); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(-55), math.radians(-20), 0)
    fill = area_light((1.5, -1.5, 2.4), (0, 0, 0), 2.0, 120, (1.0, 0.88, 0.74)); point_at(fill, (0, 0.5, 1.0)); fill.visible_camera = False
    box("Outside", (0, 18, 8), (60, 1, 20), ph.texture("beige_wall_001", scale=0.2, name="Across"))
    for k in range(8):
        for j in range(4):
            box("OWin", (-14 + k * 4, 17.45, 2 + j * 3.5), (1.4, 0.05, 2.0), pbr("OGlass", (0.04, 0.045, 0.05), 0.1, 0.4))
    # door on the left wall
    box("Door", (-3.49, -1.6, 1.1), (0.05, 1.0, 2.2), ph.texture("dark_wood", scale=1.0, name="DoorWood"))
    box("DoorFrame", (-3.48, -1.6, 1.15), (0.04, 1.15, 2.3), frame)
    # ---------------------------------------------------------------- furniture (scanned)
    oval = variant == "oval"
    c["oval"] = oval
    if oval:                                   # a Washington office: the desk in front of the window, the figure backlit
        fill.data.energy = 14
        ph.model("dining_table", loc=OVAL_DESK, rot_z=0.0, scale=0.85)
        ph.model("ArmChair_01", loc=(0.3, 0.6, 0.0), rot_z=0.4)
        ph.model("Sofa_01", loc=(1.6, -1.6, 0.0), rot_z=math.pi / 2) if False else None
        ph.model("vintage_suitcase", loc=(OVAL_DESK.x + 0.45, OVAL_DESK.y - 0.15, 0.74), rot_z=0.1, scale=0.32)
    else:
        ph.model("dining_table", loc=(0.3, 1.0, 0.0), rot_z=0.0, scale=0.85)          # partner desk
        ph.model("ArmChair_01", loc=(0.3, 1.75, 0.0), rot_z=math.pi)
    for x in (-0.4, 1.0):
        ph.model("GreenChair_01", loc=(x, -0.2, 0.0), rot_z=math.radians(10 if x > 0 else -10))
    ph.model("wooden_bookshelf_worn", loc=(-3.2, 1.2, 0.0), rot_z=-math.pi / 2)
    for k, z in enumerate((0.42, 0.82, 1.22, 1.62)):
        for j in range(2):
            ph.model("book_encyclopedia_set_01", loc=(-3.3, 0.72 + j * 0.55, z), rot_z=-math.pi / 2)
    ph.model("potted_plant_02", loc=(-3.0, -2.6, 0.0))
    ph.model("hanging_picture_frame_02", loc=(0.0, -2.99, 1.9), rot_z=0.0)
    ph.model("Chandelier_01", loc=(0.3, 0.6, 3.2))
    ph.model("potted_plant_01", loc=(3.05, 2.4, 0.0))
    ph.model("fancy_picture_frame_01", loc=(3.47, 0.2, 1.9), rot_z=math.pi / 2)
    ph.model("mantel_clock_01", loc=(-0.15, 0.95, 0.74), rot_z=0.2)
    ph.model("office_notepads", loc=(0.55, 0.95, 0.74), scale=0.4, rot_z=0.1)
    tw = None if oval else T.make("AmbTW", loc=(1.15, 1.15, 0.74), rot_z=math.pi + 0.3, color=(0.14, 0.16, 0.18), mechanism=False, glyphs=False, legends=False, text=" ")
    # flag on a floor stand (generic stripes) in the corner
    cyl("FlagPole", (-2.6, 2.5, 1.2), 0.02, 2.4, pbr("Brass", (0.75, 0.6, 0.35), 0.3, 1.0))
    import sc_twembassy
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=16, y_subdivisions=24, size=1, location=(0, 0, 0))
    fl = bpy.context.active_object; fl.scale = (0.5, 0.9, 1); bpy.ops.object.transform_apply(scale=True)
    fl.rotation_euler = (math.radians(90), 0, math.radians(30)); fl.location = (-2.36, 2.36, 1.78)
    fl.data.materials.append(sc_twembassy.flag_material())
    fd = fl.modifiers.new("drape", 'WAVE'); fd.use_x = True; fd.use_y = False; fd.height = 0.03; fd.width = 0.12; fd.speed = 0.0
    # ---------------------------------------------------------------- the note and the envelope
    note_m = tex_mat("Note", note_image(os.path.join(T.GEN, "handnote.png")), 0.85)
    note_m.node_tree.nodes["Principled BSDF"].inputs['Subsurface Weight'].default_value = 0.0
    note_m.node_tree.nodes["Principled BSDF"].inputs['Transmission Weight'].default_value = 0.25
    bpy.ops.mesh.primitive_plane_add(size=1); note = bpy.context.active_object; note.name = "Note"
    note.scale = (0.2, 0.26, 1); bpy.ops.object.transform_apply(scale=True); note.data.materials.append(note_m)
    note.modifiers.new("thick", 'SOLIDIFY').thickness = 0.0004
    c["note"] = note
    env = box("Envelope", (0, 0, 0), (0.23, 0.115, 0.004), pbr("EnvelopePaper", (0.78, 0.74, 0.64), 0.8))
    c["env"] = env
    # ---------------------------------------------------------------- people: the ambassador (unnamed), a courier
    amb = twp.person("Ambassador", 1.0, 60, "male_elegantsuit01", "short02", hv=0.72, cval=0.34, hue=0.6, sat=0.18, skin=twp.SKIN_OLD)
    cou = twp.person("Courier", 1.0, 34, "male_casualsuit04", "short01", hv=0.22, cval=0.5, hue=0.08, sat=0.3)
    c["amb"] = amb; c["cou"] = cou
    if oval:
        import skia
        path = os.path.join(T.GEN, "folder_label.png")
        sf = skia.Surface(900, 640); cv = sf.getCanvas(); cv.clear(skia.Color4f(0.72, 0.6, 0.38, 1))
        pp = skia.Paint(AntiAlias=True); pp.setColor4f(skia.Color4f(0.9, 0.88, 0.82, 1))
        cv.drawRect(skia.Rect.MakeXYWH(250, 230, 400, 120), pp)
        pp.setColor4f(skia.Color4f(0.1, 0.1, 0.12, 1)); f = skia.Font(skia.Typeface.MakeFromFile(T.MONO_B), 40)
        cv.drawString("PROJECT GUNMAN", 280, 305, f, pp)
        sf.makeImageSnapshot().save(path, skia.kPNG)
        fm = tex_mat("FolderLabel", path, 0.7)
        bpy.ops.mesh.primitive_plane_add(size=1); fo = bpy.context.active_object; fo.name = "Folder"
        fo.scale = (0.24, 0.31, 1); bpy.ops.object.transform_apply(scale=True); fo.data.materials.append(fm)
        fo.modifiers.new("thick", 'SOLIDIFY').thickness = 0.006
        c["folder"] = fo
        aide = twp.person("Aide", 1.0, 37, "male_elegantsuit01", "short03", hv=0.25, cval=0.45, hue=0.6, sat=0.15)
        c["aide"] = aide
        for o in [c["note"], c["env"]] + twp.person_objs(c["cou"]):
            o.hide_render = True
        animate(c, 0.0, "sign")
        return c
    animate(c, 0.0, "handover")
    return c


# ============================================================================ animation
def hand(h, side="R"):
    return h.bone_tail(f"lowerarm02.{side}")


def animate(c, sec, shot):
    from human import reach, fingers_curl
    amb, cou, env, note = c["amb"], c["cou"], c["env"], c["note"]
    if c.get("oval"):
        d = OVAL_DESK
        twp.seat(amb, (d.x, d.y + 0.62, 0), 0.0, lean=18)                    # behind the desk, back to the window
        paper = d + Vector((0.0, 0.2, 0.765))
        sw = Vector((0.06 * math.sin(sec * 2.8) + 0.04 * sec / 5, 0.0, 0.03 + 0.006 * abs(math.sin(sec * 9))))
        reach(amb, "R", paper + sw + Vector((0.03, 0.12, 0.03)), Vector((-0.5, 0.3, -0.8)), Vector((0, -1, -0.5)))
        reach(amb, "L", paper + Vector((-0.22, 0.1, 0.04)), Vector((0.5, 0.3, -0.8)), Vector((0, -1, -0.3)))
        fingers_curl(amb, 45, thumb=20)
        amb.rot("head", (1, 0, 0), 16)
        aide = c["aide"]; fo = c["folder"]
        twp.stand(aide, (d.x + 0.95, d.y - 0.35, 0), math.radians(135) if shot == "folder" else math.radians(120))
        if shot == "folder":
            k = ease(min(1.0, max(0.0, (sec - 0.8) / 2.2)))
            case = d + Vector((0.45, -0.15, 0.95))
            start = d + Vector((0.6, -0.55, 1.1))
            fo.location = start.lerp(case, k); fo.rotation_euler = (math.radians(80 - 10 * k), 0, math.radians(15))
            reach(aide, "R", fo.location + Vector((0.08, -0.08, 0.1)), Vector((0.5, -0.4, -0.7)), Vector((-0.6, 0.6, -0.4)))
            reach(aide, "L", fo.location + Vector((-0.1, -0.12, 0.05)), Vector((-0.5, -0.4, -0.7)), Vector((0.6, 0.6, -0.4)))
        else:
            fo.location = aide.bone_head("spine03") + Vector((-0.1, -0.2, -0.15)); fo.rotation_euler = (math.radians(85), 0, math.radians(135))
            reach(aide, "L", fo.location + Vector((0.05, 0.1, 0.12)), Vector((-0.5, 0.4, -0.7)))
        fingers_curl(aide, 45, thumb=20)
        bpy.context.view_layer.update()
        return
    if shot == "handover":
        twp.hide(twp.person_objs(cou), False)
        twp.stand(amb, (0.55, 0.15, 0.0), -math.pi / 2 + 0.35)              # beside the desk, turned toward the door
        moving = twp.walk(cou, (-2.9, -1.4), (-0.35, -0.2), sec, speed=1.05)
        give = ease(min(1.0, max(0.0, (sec - 2.8) / 0.8)))
        if not moving:
            d = amb.arm.location - cou.arm.location; twp.face(cou, math.atan2(d.x, -d.y))
            mid = (cou.bone_head("upperarm01.R") + amb.bone_head("upperarm01.R")) / 2 + Vector((0, 0, -0.22))
            reach(cou, "R", hand(cou).lerp(mid, give) if give < 1 else mid, Vector((0.3, -0.5, -0.8)), (amb.arm.location - cou.arm.location))
            take = ease(min(1.0, max(0.0, (sec - 3.3) / 0.7)))
            if take > 0:
                reach(amb, "R", amb.bone_head("upperarm01.R").lerp(mid, 0.0) + (mid - amb.bone_head("upperarm01.R")) * take + Vector((0, 0, -0.25 * (1 - take))),
                      Vector((0.3, 0.5, -0.8)), (cou.arm.location - amb.arm.location))
            fingers_curl(cou, 40, thumb=25)
            env.location = hand(cou) + (cou.arm.location - amb.arm.location).normalized() * -0.08
        else:
            env.location = hand(cou) + Vector((0, 0, -0.02))
        env.rotation_euler = (math.radians(70), 0, cou.arm.rotation_euler.z)
        note.hide_render = True
    else:
        twp.hide(twp.person_objs(cou), True); env.hide_render = True; note.hide_render = False
        twp.stand(amb, (1.75, 2.35, 0.0), math.pi)                            # at the window, back to the room
        unfold = ease(min(1.0, max(0.0, (sec - 0.6) / 1.4))) if shot == "note" else 1.0
        fold = ease(min(1.0, max(0.0, (sec - 2.4) / 1.0))) if shot == "pocket" else 0.0
        chest = amb.bone_head("spine03") + Vector((0, 0.36, 0.08))
        nloc = chest + Vector((0, 0, 0.02 * math.sin(sec)))
        if shot == "pocket" and sec > 3.3:
            nloc = amb.bone_head("spine03").lerp(nloc, 1 - ease(min(1.0, (sec - 3.3) / 0.9))) + Vector((0.1, 0.06, -0.05))
        note.location = nloc
        note.rotation_euler = (math.radians(70), 0, 0)
        note.scale = (1, max(0.35, unfold * (1 - 0.6 * fold)), 1)
        for sd, sg in (("L", -1), ("R", 1)):
            reach(amb, sd, nloc + Vector((sg * 0.15, -0.09, -0.05)), Vector((sg * 1, -0.3, -0.7)), Vector((-sg * 0.6, 1, 0.3)))
        fingers_curl(amb, 60, thumb=40)
        amb.rot("neck01", (1, 0, 0), 10); amb.rot("head", (1, 0, 0), 12)
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_handover(c, t):
    e = ease(t)
    return (Vector((2.05, 1.05, 1.62)).lerp(Vector((1.85, 0.9, 1.6)), e), Vector((-0.45, -0.3, 1.3)), 32)


def cam_note(c, t):
    e = ease(t); a = c["amb"]
    sh = a.bone_head("upperarm01.R")
    n = c["note"].location; hd = a.bone_head("head")
    return (hd + Vector((-0.34, -0.42, 0.2)).lerp(Vector((-0.3, -0.36, 0.17)), e), n, 42)


def cam_sign(c, t):
    e = ease(t); d = OVAL_DESK
    return (d + Vector((0.9, -3.2, 1.05)).lerp(Vector((0.7, -2.7, 1.08)), e), d + Vector((0.0, 0.6, 1.05)), 35)


def cam_folder(c, t):
    e = ease(t); d = OVAL_DESK
    return (d + Vector((2.0, -1.7, 1.5)).lerp(Vector((1.75, -1.45, 1.45)), e), d + Vector((0.5, -0.2, 0.95)), 35)


MOVES = {
    "sign": dict(kind="anim", dof=3.0, cam=cam_sign, focus=lambda c, t: OVAL_DESK + Vector((0, 0.5, 1.0)), anim=anim("sign")),
    "folder": dict(kind="anim", dof=2.0, cam=cam_folder, focus=lambda c, t: c["folder"].location, anim=anim("folder")),
    "handover": dict(kind="anim", dof=3.0, cam=cam_handover, focus=lambda c, t: c["env"].location, anim=anim("handover")),
    "note": dict(kind="anim", dof=2.0, cam=cam_note, focus=lambda c, t: c["note"].location, anim=anim("note")),
    "pocket": dict(kind="anim", dof=2.0, cam=cam_note, focus=lambda c, t: c["note"].location, anim=anim("pocket")),
}
