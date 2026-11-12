"""EMBASSY TYPING ROOM, Moscow 1984 (dramatization). Steel desks, typewriters, venetian blinds, fluorescent panels.
Variants: day (people at work) / night (empty, one desk lamp on the typewriter).

Intro 3A  typing     a secretary types; the ball whirls (3/4 front-left, slow push)
Intro 3B  notice     a clerk pins an "equipment upgrade" notice; a colleague stops to read it
Intro 8A  night_push push in on the lone typewriter under the desk lamp
Intro 8B  night_type no hands in frame: the ball types one short line, then stops
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph, paper_tex
import typewriter as T
import twp

EXPOSURE = -0.1
DUR = {"count": 5.0, "analyst": 5.0, "page_out": 5.0, "typing": 4.5, "notice": 5.0, "night_push": 4.5, "night_type": 5.0, "nsa_desk": 5.0, "nsa_plans": 5.0, "records_drawer": 4.5, "records_burn": 4.5,
       "attache": 5.0, "platen": 6.0}
VARIANT_FOR = {"count": "count", "analyst": "analyst", "night_push": "night", "night_type": "night", "page_out": "night", "nsa_desk": "nsa", "nsa_plans": "nsa",
               "records_drawer": "records", "records_burn": "records", "attache": "attache", "platen": "attache"}
DESK_Z = 0.79
DESK_A = Vector((0.9, 0.4, 0.0))
TEXT_G = "AGRICULTURAL OFFICE\n\nWheat and feed grains: position for\nthe next session. Price range and\nvolumes as discussed with the\ndelegation. Not for distribution."
TEXT_A = "The copier on the fourth floor will be replaced\nthis week. Please clear all papers from the"
TEXT_N = "Moscow, May 1984."
TEXT_P = "Moscow, May 1984.\n\nReference your cable of the 9th.\nThe meeting with the delegation is set\nfor Thursday. Our position on volumes\nand price remains as agreed.\n"


def notice_image(path):
    import skia
    W_, H_ = 850, 1100
    s = skia.Surface(W_, H_); c = s.getCanvas(); c.clear(skia.Color4f(0.92, 0.91, 0.87, 1))
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(0.08, 0.08, 0.09, 1))
    f = skia.Font(skia.Typeface.MakeFromFile(T.MONO_B), 46); f2 = skia.Font(skia.Typeface.MakeFromFile(T.MONO_B), 26)
    c.drawString("NOTICE TO ALL STAFF", 150, 160, f, p)
    c.drawString("EQUIPMENT UPGRADE", 190, 230, f, p)
    p.setColor4f(skia.Color4f(0.3, 0.3, 0.32, 1))
    rng = np.random.default_rng(4); y = 330
    for k in range(14):
        c.drawRect(skia.Rect.MakeXYWH(90, y, rng.uniform(450, 670), 9), p); y += 34
        if k % 5 == 4:
            y += 26
    s.makeImageSnapshot().save(path, skia.kPNG)
    return path


def build(variant=None):
    c = {"variant": variant}
    nsa = variant == "nsa"
    night = variant in ("night", "nsa", "analyst")
    rng = np.random.default_rng(5)
    if night:
        world_flat((0.004, 0.006, 0.011), 1.0)
    else:
        world_sky(sun_elev_deg=34, sun_rot_deg=70, strength=0.45, tint=(0.88, 0.92, 1.0))
    # ---------------------------------------------------------------- room shell: x -4..4, y -3..3, h 3.0
    box("Floor", (0, 0, -0.01), (8, 6, 0.02), ph.texture("old_linoleum_flooring_01", scale=0.5, tint=(0.55, 0.6, 0.62)))
    wall = ph.texture("painted_plaster_wall", scale=0.5, name="WallPaint", tint=(0.78, 0.8, 0.76))
    box("WallBack", (0, 3.05, 1.5), (8, 0.1, 3.0), wall); box("WallFront", (0, -3.05, 1.5), (8, 0.1, 3.0), wall)
    box("WallL", (-4.05, 0, 1.5), (0.1, 6, 3.0), wall)
    box("Ceiling", (0, 0, 3.02), (8, 6, 0.04), ph.texture("ceiling_interior", scale=0.5, name="CeilTile"))
    box("Skirting", (0, 2.995, 0.05), (8, 0.01, 0.1), pbr("Skirt", (0.12, 0.1, 0.08), 0.5))
    # +X wall: three tall windows with blinds, a brick building across the street
    for z, h in ((0.45, 0.9), (2.8, 0.4)):
        box("WallR", (4.05, 0, z), (0.1, 6, h), wall)
    for y in (-3.0, -1.0, 1.0, 3.0):
        box("WinPier", (4.05, y, 1.65), (0.1, 0.6, 1.5), wall)
    frame = pbr("WinFrame", (0.36, 0.34, 0.3), 0.5)
    for yc in (-2.0, 0.0, 2.0):
        box("Sash", (4.02, yc, 1.65), (0.04, 1.4, 0.04), frame)
        box("SashV", (4.02, yc, 1.65), (0.04, 0.04, 1.5), frame)
        box("Glass", (4.04, yc, 1.65), (0.01, 1.4, 1.5), glass("WinGlass", (0.9, 0.93, 0.95)))
    slat = pbr("Blind", (0.72, 0.71, 0.66), 0.5)
    for yc in (-2.0, 0.0, 2.0):
        twp.venetian(3.95, yc, 1.3 if not night else 0.95, 2.38, 1.36, "y", slat, tilt=-55)
    brick = ph.texture("brick_wall_02", scale=0.4)
    box("Across", (22, 0, 8), (0.5, 60, 24), brick)
    for k in range(5):
        for j in range(4):
            box("AcrossWin", (21.7, -12 + k * 6, 2.5 + j * 3.4), (0.05, 1.4, 1.8), pbr("AcrossGlass", (0.03, 0.035, 0.04), 0.15, 0.4))
    if not night:
        sn = bpy.data.lights.new("Sun", 'SUN'); sn.energy = 2.6; sn.angle = math.radians(1.5); sn.color = (1.0, 0.94, 0.86)
        so = bpy.data.objects.new("Sun", sn); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(58), math.radians(-35), math.radians(-90))
        pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 6.0; pt.size_y = 1.5; pt.cycles.is_portal = True
        po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (3.98, 0, 1.65); po.rotation_euler = (0, math.radians(-90), 0)
    else:
        mn = area_light((3.8, 0.5, 1.8), (0, 0, 0), 2.5, 18, (0.45, 0.55, 0.85)); point_at(mn, (0, 0.4, 0.5)); mn.visible_camera = False
    for x in (-2.2, 0.6, 3.0):
        for y in (-1.5, 1.2):
            ph.model("mounted_fluorescent_lights", loc=(x, y, 3.0), rot_z=math.radians(90))
            if not night:
                l = area_light((x, y, 2.92), (0, 0, 0), 0.9, 38, (0.9, 0.96, 1.0)); l.visible_camera = False
    # ---------------------------------------------------------------- desks with typewriters (typists sit at +Y, face -Y)
    c["tws"] = []
    desks = [(DESK_A, True), (Vector((-1.5, 0.4, 0)), True), (Vector((0.9, -1.9, 0)), True), (Vector((-1.5, -1.9, 0)), variant == "count")]
    if variant == "count":                      # every desk in the room has a typewriter on it, side desks too
        for k, (x, y) in enumerate(((3.25, 0.5), (3.25, -1.6), (-3.3, -2.2))):
            r_, ms_ = ph.model("SchoolDesk_01", loc=(x, y, 0), rot_z=math.pi if y > 0 else 0.0)
            lo_, hi_ = ph.bounds(ms_)
            tw_ = T.make(f"TWside{k}", loc=(x, y, hi_.z - 0.005), rot_z=math.pi if y > 0 else 0.0, color=(0.2, 0.25, 0.3), mechanism=False,
                         glyphs=False, legends=False, text=" ", seed=20 + k)
            tw_["paper"].hide_render = True
    paper = paper_tex.make_all()
    pages = [bpy.data.materials.new(f"Pg{k}") for k in range(3)]
    for k, m in enumerate(pages):
        m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(paper["pages"][k]); L.new(t.outputs[0], N["Principled BSDF"].inputs['Base Color'])
    for k, (p, has_tw) in enumerate(desks):
        ph.model("metal_office_desk", loc=(p.x, p.y, 0), rot_z=math.pi)
        if has_tw:
            tw = T.make(f"TW{k}", loc=(p.x - 0.15 + (0.55 if nsa and k < 2 else 0), p.y + 0.21 - (0.15 if nsa and k < 2 else 0), DESK_Z),
                        rot_z=math.pi + (0.5 if nsa and k < 2 else 0),
                        text=TEXT_P if (night and k == 0) else (TEXT_G if (variant == "attache" and k == 0) else (TEXT_A if k == 0 else "Please clear all papers from the")),
                        color=(0.11, 0.15, 0.2) if k != 1 else (0.32, 0.28, 0.22), mechanism=(k == 0), glyphs=(k == 0), legends=(k == 0), seed=k, dpi=400 if k == 0 else 160)
            c["tws"].append(tw)
        ph.model("office_notepads", loc=(p.x + 0.55, p.y - 0.05, DESK_Z), rot_z=rng.uniform(-0.3, 0.3), scale=0.45)
        for j in range(3):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(p.x + 0.5 + rng.uniform(-0.1, 0.1), p.y + rng.uniform(-0.2, 0.15), DESK_Z + 0.012 + j * 0.0005),
                                             rotation=(0, 0, rng.uniform(-0.4, 0.4)))
            o = bpy.context.active_object; o.scale = (0.21, 0.28, 1); o.data.materials.append(pages[(k + j) % 3])
        r, ms = twp.model_fit("painted_wooden_chair_01", (p.x - 0.15, p.y + 0.75, 0), rot_z=math.pi + rng.uniform(-0.15, 0.15), height=0.92)
    c["tw"] = c["tws"][0]
    ph.model("stationery_supplies", loc=(DESK_A.x + 0.35, DESK_A.y + 0.25, DESK_Z), rot_z=0.3)
    # desk lamp (on at night)
    lamp_r, lamp_ms = ph.model("desk_lamp_arm_01", loc=(DESK_A.x + 0.5, DESK_A.y + 0.25, DESK_Z), rot_z=math.radians(200))
    twp.tint_model(lamp_ms, (0.16, 0.2, 0.17), keep=0.1)
    if nsa:                                   # plans spread on desk B, a legal pad on desk A, lamps on
        import os
        pm = bpy.data.materials.new("Plans"); pm.use_nodes = True
        t = pm.node_tree.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(plans_image(os.path.join(T.GEN, "plans.png")))
        pm.node_tree.links.new(t.outputs[0], pm.node_tree.nodes["Principled BSDF"].inputs['Base Color'])
        bpy.ops.mesh.primitive_plane_add(size=1, location=(-1.5, 0.35, DESK_Z + 0.015), rotation=(0, 0, 0.08))
        o = bpy.context.active_object; o.scale = (0.9, 0.62, 1); o.data.materials.append(pm); c["plans"] = o
        bpy.ops.mesh.primitive_plane_add(size=1, location=(DESK_A.x - 0.15, DESK_A.y + 0.2, DESK_Z + 0.014), rotation=(0, 0, math.pi + 0.15))
        o = bpy.context.active_object; o.scale = (0.22, 0.3, 1); o.data.materials.append(pbr("LegalPad", (0.85, 0.8, 0.45), 0.8)); c["pad"] = o
        pen = cyl("Pen", (0, 0, 0), 0.004, 0.14, pbr("PenBlack", (0.02, 0.02, 0.02), 0.3), verts=8); c["pen"] = pen
        r2, ms2 = ph.model("desk_lamp_arm_01", loc=(-0.9, 0.55, DESK_Z), rot_z=math.radians(150)); twp.tint_model(ms2, (0.16, 0.2, 0.17), keep=0.1)
        sp2 = bpy.data.lights.new("Lamp2", 'SPOT'); sp2.energy = 40; sp2.spot_size = math.radians(95); sp2.spot_blend = 0.7; sp2.color = (1.0, 0.76, 0.5)
        l2 = bpy.data.objects.new("Lamp2", sp2); bpy.context.collection.objects.link(l2); l2.location = (-1.3, 0.4, DESK_Z + 0.75); point_at(l2, (-1.5, 0.35, DESK_Z))
        ceil = area_light((-0.3, 0.0, 2.9), (0, 0, 0), 2.0, 25, (0.9, 0.85, 0.75)); ceil.visible_camera = False
        up = area_light((-1.5, 0.35, DESK_Z + 0.05), (math.radians(180), 0, 0), 0.8, 6, (1.0, 0.85, 0.6)); up.visible_camera = False   # lamp light bouncing off the plans onto faces
    if night:
        sp = bpy.data.lights.new("Lamp", 'SPOT'); sp.energy = 22 if not nsa else 35; sp.spot_size = math.radians(85); sp.spot_blend = 0.6
        sp.color = (1.0, 0.74, 0.48); sp.shadow_soft_size = 0.04
        lo = bpy.data.objects.new("Lamp", sp); bpy.context.collection.objects.link(lo)
        lo.location = (DESK_A.x + 0.32, DESK_A.y + 0.05, DESK_Z + 0.5); point_at(lo, (DESK_A.x - 0.15, DESK_A.y + 0.05, DESK_Z + 0.05))
        kl = bpy.data.lights.new("BallKey", 'AREA'); kl.energy = 1.6; kl.size = 0.12; kl.color = (1.0, 0.8, 0.6)
        ko = bpy.data.objects.new("BallKey", kl); bpy.context.collection.objects.link(ko)
        ko.location = T.world(c["tws"][0], (0.12, -0.25, 0.35)) if c["tws"] else (0, 0, 2); point_at(ko, T.world(c["tws"][0], (-0.05, 0.0, 0.13)))
        ko.visible_camera = False
        bl = bpy.data.lights.new("Bounce", 'AREA'); bl.energy = 1.2; bl.size = 1.0; bl.color = (1.0, 0.8, 0.6)
        bo = bpy.data.objects.new("Bounce", bl); bpy.context.collection.objects.link(bo); bo.location = (DESK_A.x - 0.2, DESK_A.y - 0.6, DESK_Z + 0.4)
        point_at(bo, (DESK_A.x - 0.15, DESK_A.y, DESK_Z)); bo.visible_camera = False
    # ---------------------------------------------------------------- back wall: filing cabinets, clock; left wall: notice board
    import sc_invest
    steel = pbr("CabSteel", (0.3, 0.32, 0.3), 0.42, 0.55, **{'Coat Weight': 0.15}); hm = pbr("Chrome", (0.8, 0.8, 0.8), 0.2, 1.0)
    sc_invest.CAB_Y = 2.3
    for x in (-3.4, -2.92, -2.44, 1.9, 2.38, 2.86):
        ds = sc_invest.filing_cabinet(x, steel, hm, open_drawer=(variant == "records" and x == 2.38))
        if variant == "records" and x == 2.38:
            c["drawer"] = ds[2]; c["drawer_y"] = ds[2].location.y
            folders = sc_invest.hanging_folders(ds[2], np.random.default_rng(4))
            for k_, f in enumerate(folders):
                if k_ % 3 or k_ > 20:
                    f.hide_render = True                   # thinned out: many folders are simply gone
    ph.model("wall_clock", loc=(-0.4, 2.99, 2.25), rot_z=math.pi)
    ph.model("potted_plant_01", loc=(3.5, 2.5, 0))
    # dressing on the left wall: a framed picture, a plant, a flag on a floor stand, a coat stand of shelving
    for loc, aid in (((-3.98, 1.4, 1.75), "hanging_picture_frame_02"), ((-3.98, -2.2, 1.7), "hanging_picture_frame_01")):
        try:
            ph.model(aid, loc=loc, rot_z=-math.pi / 2)
        except Exception:
            pass
    ph.model("potted_plant_02", loc=(-3.6, 0.9, 0))
    ph.model("potted_plant_04", loc=(-3.55, -2.6, 0))
    import sc_twembassy
    cyl("FlagPoleO", (-3.6, -1.8, 1.15), 0.02, 2.3, pbr("BrassO", (0.75, 0.6, 0.35), 0.3, 1.0))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=16, y_subdivisions=24, size=1)
    fl_ = bpy.context.active_object; fl_.scale = (0.5, 0.85, 1); bpy.ops.object.transform_apply(scale=True)
    fl_.rotation_euler = (math.radians(90), 0, math.radians(60)); fl_.location = (-3.48, -1.6, 1.85); fl_.data.materials.append(sc_twembassy.flag_material())
    fdm = fl_.modifiers.new("drape", 'WAVE'); fdm.use_x = True; fdm.use_y = False; fdm.height = 0.03; fdm.width = 0.12; fdm.speed = 0.002
    if not night:
        for k, pos in enumerate(((-1.5 + 0.5, 0.65), (0.9 + 0.5, -1.65))):
            r_, ms_ = ph.model("desk_lamp_arm_01", loc=(pos[0], pos[1], DESK_Z), rot_z=math.radians(200)); twp.tint_model(ms_, (0.16, 0.2, 0.17), keep=0.1)
            ll = bpy.data.lights.new("DayLamp", 'SPOT'); ll.energy = 15; ll.spot_size = math.radians(80); ll.color = (1.0, 0.78, 0.5)
            lo_ = bpy.data.objects.new("DayLamp", ll); bpy.context.collection.objects.link(lo_); lo_.location = (pos[0] - 0.15, pos[1] - 0.15, DESK_Z + 0.48)
            point_at(lo_, (pos[0] - 0.4, pos[1] - 0.2, DESK_Z))
    cork = pbr("Cork", (0.4, 0.29, 0.18), 0.9)
    box("CorkBoard", (-3.985, -0.6, 1.55), (0.03, 1.6, 1.0), cork)
    box("CorkFrame", (-3.99, -0.6, 1.55), (0.02, 1.66, 1.06), pbr("CorkFrame", (0.15, 0.1, 0.06), 0.5))
    for k in range(5):
        y, z = -1.2 + k * 0.32 + rng.uniform(-0.04, 0.04), 1.7 + rng.uniform(-0.2, 0.15)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(-3.965, y, z), rotation=(math.radians(90), rng.uniform(-0.05, 0.05), math.radians(90)))
        o = bpy.context.active_object; o.scale = (0.2, 0.26, 1); o.data.materials.append(pages[k % 3])
    import os
    nm = bpy.data.materials.new("Notice"); nm.use_nodes = True
    t = nm.node_tree.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(notice_image(os.path.join(T.GEN, "notice.png")))
    nm.node_tree.links.new(t.outputs[0], nm.node_tree.nodes["Principled BSDF"].inputs['Base Color'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-3.6, 0.1, 1.3), rotation=(math.radians(90), 0, math.radians(90)))
    notice = bpy.context.active_object; notice.name = "NoticeSheet"; notice.scale = (0.21, 0.28, 1); notice.data.materials.append(nm)
    c["notice"] = notice
    # ---------------------------------------------------------------- people (day only)
    c["people"] = {}
    if variant == "count":
        cnt = twp.person("Counter", 1.0, 44, "male_casualsuit01", "short02", hv=0.35, cval=0.5, hue=0.1, sat=0.2)
        c["people"]["counter"] = cnt
        cb, _ = ph.model("clipboard"); c["clipboard"] = cb
    if variant == "analyst":                       # a Soviet analyst, late: a printout of run-together letters, a pencil
        import os
        a_img, b_img = analyst_images(os.path.join(T.GEN, "runon_a.png"), os.path.join(T.GEN, "runon_b.png"))
        pen = cyl("Pencil", (0, 0, 0), 0.0035, 0.17, pbr("PencilYellow", (0.6, 0.45, 0.1), 0.5), verts=6); c["pencil"] = pen
        m = bpy.data.materials.new("Printout"); m.use_nodes = True
        N = m.node_tree.nodes; L = m.node_tree.links; p_ = N["Principled BSDF"]
        uv = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs['UV'], sp.inputs[0])
        ia = N.new("ShaderNodeTexImage"); ia.image = bpy.data.images.load(a_img); ib = N.new("ShaderNodeTexImage"); ib.image = bpy.data.images.load(b_img)
        L.new(uv.outputs['UV'], ia.inputs['Vector']); L.new(uv.outputs['UV'], ib.inputs['Vector'])
        pv = N.new("ShaderNodeValue"); d = pv.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
        var = d.variables.new(); var.name = "x"; var.type = 'TRANSFORMS'; var.targets[0].id = pen; var.targets[0].transform_type = 'LOC_X'
        d.expression = f"(x - ({DESK_A.x - 0.15 - 0.15})) / 0.3"
        lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; L.new(sp.outputs[0], lt.inputs[0]); L.new(pv.outputs[0], lt.inputs[1])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(lt.outputs[0], mx.inputs['Factor']); L.new(ia.outputs[0], mx.inputs[6]); L.new(ib.outputs[0], mx.inputs[7])
        L.new(mx.outputs[2], p_.inputs['Base Color']); p_.inputs['Roughness'].default_value = 0.85
        bpy.ops.mesh.primitive_plane_add(size=1, location=(DESK_A.x - 0.15, DESK_A.y + 0.2, DESK_Z + 0.014), rotation=(0, 0, math.pi))
        o = bpy.context.active_object; o.scale = (0.3, 0.38, 1); o.data.materials.append(m); c["printout"] = o
        an = twp.person("Analyst", 1.0, 52, "male_casualsuit04", "short04", hv=0.55, cval=0.5, hue=0.12, sat=0.25)
        twp.seat(an, (DESK_A.x - 0.15, DESK_A.y + 0.66, 0), 0.0, lean=20)
        c["people"]["an"] = an
    if variant == "records":
        c["people"]["agent"] = twp.person("Agent", 1.0, 44, "male_elegantsuit01", "short03", hv=0.3, cval=0.5, hue=0.6, sat=0.15)
        c["people"]["clerkR"] = twp.person("ClerkR", 0.0, 50, "female_elegantsuit01", "bob01", hv=0.55, cval=0.6, hue=0.1, sat=0.2)
        bag_m = ph.texture("cardboard", scale=1.0, name="BurnBag") if False else pbr("BurnBag", (0.55, 0.42, 0.28), 0.85)
        stripe = pbr("BagRed", (0.45, 0.06, 0.05), 0.8)
        parts = [box("Bag", (0, 0, 0.33), (0.42, 0.28, 0.66), bag_m, bevel=0.01), box("BagFold", (0, 0, 0.67), (0.43, 0.29, 0.04), bag_m)]
        for k in range(5):
            parts.append(box("BagStripe", (-0.16 + k * 0.08, -0.141, 0.33), (0.025, 0.004, 0.62), stripe, rot=(0, math.radians(25), 0)))
        bag = join(parts, "BurnBagObj")
        bag.location = (-0.3, 1.8, 0); c["bag"] = bag
        bx, _ = ph.model("cardboard_box_01"); c["rbox"] = bx
        c["sheets"] = []
        for k in range(8):
            bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.active_object; o.scale = (0.21, 0.28, 1); o.data.materials.append(pages[k % 3])
            c["sheets"].append(o)
    if variant == "attache":
        at = twp.person("Attache", 1.0, 48, "male_elegantsuit01", "short02", hv=0.45, cval=0.55, hue=0.1, sat=0.25)
        twp.seat(at, (DESK_A.x - 0.15, DESK_A.y + 0.66, 0), 0.0, lean=12)
        c["people"]["sec"] = at
        jar = join([cyl("Jar", (0, 0, 0.09), 0.06, 0.18, glass("JarGlass", (0.9, 0.92, 0.9)), verts=24),
                    cyl("Grain", (0, 0, 0.065), 0.055, 0.13, ph.texture("dry_ground_01", scale=8.0, name="GrainMat", tint=(1.1, 0.9, 0.55)), verts=24),
                    cyl("Lid", (0, 0, 0.185), 0.062, 0.015, pbr("JarLid", (0.6, 0.55, 0.4), 0.3, 1.0), verts=24)], "GrainJar")
        jar.location = (DESK_A.x - 0.65, DESK_A.y + 0.05, DESK_Z)
        ph.model("wicker_basket_01", loc=(DESK_A.x + 0.6, DESK_A.y - 0.1, DESK_Z), scale=0.5)
    if nsa:
        off = twp.person("Official", 1.0, 58, "male_elegantsuit01", "short02", hv=0.7, cval=0.45, hue=0.6, sat=0.15, skin=twp.SKIN_OLD)
        twp.seat(off, (DESK_A.x - 0.15, DESK_A.y + 0.66, 0), 0.0, lean=16)
        c["people"]["off"] = off
        for k, (nm, g, yrs, cl, hr, cv, hu) in enumerate((("PlanA", 1.0, 45, "male_casualsuit02", "short03", 0.55, 0.1),
                                                          ("PlanB", 1.0, 38, "male_casualsuit04", "short01", 0.5, 0.6),
                                                          ("PlanC", 1.0, 51, "male_elegantsuit01", "short04", 0.45, 0.6))):
            c["people"][nm] = twp.person(nm, g, yrs, cl, hr, hv=0.3, cval=cv, hue=hu, sat=0.2)
    if variant in (None, "day"):
        sec = twp.person("Secretary", 0.0, 33, "female_elegantsuit01", "ponytail01", hv=0.22, cval=0.55, hue=0.58, sat=0.3)
        twp.seat(sec, (DESK_A.x - 0.15, DESK_A.y + 0.66, 0), 0.0, lean=12)
        c["people"]["sec"] = sec
        sec2 = twp.person("Secretary2", 0.0, 45, "female_elegantsuit01", "bob01", hv=0.4, cval=0.6, hue=0.1, sat=0.25)
        twp.seat(sec2, (-1.65, 1.06, 0), 0.0, lean=12)
        c["people"]["sec2"] = sec2
        clerk = twp.person("Clerk", 1.0, 40, "male_casualsuit03", "short02", hv=0.25, cval=0.5, hue=0.6, sat=0.2)
        c["people"]["clerk"] = clerk
        reader = twp.person("Reader", 1.0, 52, "male_elegantsuit01", "short04", hv=0.6, cval=0.42, hue=0.08, sat=0.3)
        c["people"]["reader"] = reader
    animate(c, 0.0)
    return c


# ============================================================================ animation
def animate(c, sec, shot=None):
    night = c["variant"] == "night"
    if c["variant"] == "count":
        from human import reach, fingers_curl
        h = c["people"]["counter"]
        twp.walk(h, (3.8, -0.75), (-3.5, -0.75), sec, speed=0.7)
        h.rot("head", (0, 0, 1), 40 * math.sin(sec * 1.3))                  # looking from desk to desk, counting
        fwd = twp.forward(h); cb = c["clipboard"]
        cb.location = h.bone_head("spine03") + fwd * 0.28 + Vector((0, 0, -0.12)); cb.rotation_euler = (math.radians(-50), 0, math.atan2(fwd.x, -fwd.y))
        side = fwd.cross(Vector((0, 0, 1)))
        reach(h, "L", cb.location + side * 0.1 + Vector((0, 0, -0.03)), Vector((side.x, side.y, -0.8)), fwd)
        reach(h, "R", cb.location - side * 0.05 + Vector((0, 0, 0.03)), Vector((-side.x, -side.y, -0.8)), fwd + Vector((0, 0, -0.6)))
        bpy.context.view_layer.update()
        return
    if c["variant"] == "analyst":
        from human import reach, fingers_curl
        an = c["people"]["an"]; pen = c["pencil"]
        x0 = DESK_A.x - 0.15 - 0.15                          # page left edge (page is rotated: its +u runs toward -x... keep simple)
        prog = min(1.0, sec / DUR["analyst"])
        line_y = DESK_A.y + 0.2 + 0.1 - 0.03 * int(prog * 4)
        px = x0 + 0.3 * ((prog * 4) % 1.0)
        tap = 0.004 * abs(math.sin(sec * 12))
        pen.location = (px, line_y, DESK_Z + 0.03 + tap + 0.06); pen.rotation_euler = (math.radians(30), 0, math.radians(10))
        reach(an, "R", Vector((px + 0.02, line_y + 0.06, DESK_Z + 0.06)), Vector((-0.5, 0.3, -0.8)), Vector((0, -1, -0.5)))
        reach(an, "L", Vector((x0 + 0.05, DESK_A.y + 0.2, DESK_Z + 0.04)), Vector((0.5, 0.3, -0.8)), Vector((0, -1, -0.3)))
        fingers_curl(an, 50, thumb=25); an.rot("head", (1, 0, 0), 20)
        bpy.context.view_layer.update()
        return
    if c["variant"] == "records":
        from human import reach, fingers_curl
        P = c["people"]
        ag = P["agent"]; d = c["drawer"]
        op = ease(min(1.0, sec / 1.2)) if shot == "records_drawer" else 1.0
        d.location.y = c["drawer_y"] - 0.5 * op
        bpy.context.view_layer.update()
        twp.stand(ag, (2.38 + 0.1, 1.45, 0), math.pi)
        hp = d.matrix_world @ Vector((0.0, 0.1 + 0.25 * ease(min(1.0, max(0.0, (sec - 1.5) / 2.5))), 0.16))
        reach(ag, "R", hp + Vector((0, -0.05, 0.05)), Vector((0.8, -0.2, -0.8)), Vector((0, 0.35, -1)))
        reach(ag, "L", d.matrix_world @ Vector((-0.17, -0.04, 0.13)), Vector((-0.8, -0.2, -0.8)), Vector((0.1, 0.5, -0.85)))
        fingers_curl(ag, 30, thumb=15); ag.rot("head", (1, 0, 0), 14)
        cl = P["clerkR"]; bag = c["bag"]; bx = c["rbox"]
        twp.stand(cl, (bag.location.x + 0.75, bag.location.y - 0.1, 0), math.radians(-95))
        tip = ease(min(1.0, max(0.0, (sec - 0.8) / 1.8))) if shot == "records_burn" else 0.0
        bx.location = bag.location + Vector((0.42, 0, 0.95)); bx.rotation_euler = (0, math.radians(-110) * tip, math.pi / 2)
        for k, sh in enumerate(c["sheets"]):
            f = min(1.0, max(0.0, tip * 1.4 - k * 0.06))
            sh.location = bx.location.lerp(bag.location + Vector((0.0, 0.0, 0.6)), f) + Vector((0.02 * k, 0, 0.01 * k))
            sh.rotation_euler = (0.3 * k, 0.9 * f + 0.2 * k, 0.1 * k)
            sh.hide_render = shot != "records_burn"
        twp.hide([bx] + list(bx.children_recursive) + [bag], shot != "records_burn")
        for sd, dy in (("L", 0.2), ("R", -0.2)):
            reach(cl, sd, bx.location + Vector((0.1, dy, -0.1)), Vector((0.3, dy * 3, -0.7)), Vector((-1, 0, 0)))
        fingers_curl(cl, 40, thumb=20)
        bpy.context.view_layer.update()
        return
    if c["variant"] == "attache":
        T.type_at(c["tw"], sec, start=0.3 if shot == "attache" else -16.0, cps=4.5)
        twp.type_pose(c["people"]["sec"], c["tw"], sec)
        bpy.context.view_layer.update()
        return
    if c["variant"] == "nsa":
        from human import reach, fingers_curl
        P = c["people"]; off = P["off"]
        pad = c["pad"].location
        wr = pad + Vector((0.05 * math.sin(sec * 2.3), 0.04 * math.sin(sec * 0.9), 0.03 + 0.008 * abs(math.sin(sec * 7))))
        reach(off, "R", wr + Vector((0.02, 0.1, 0.03)), Vector((-0.5, 0.3, -0.8)), Vector((0, -1, -0.5)))
        reach(off, "L", pad + Vector((0.2, 0.08, 0.05)), Vector((0.5, 0.3, -0.8)), Vector((0, -1, -0.3)))
        fingers_curl(off, 50, thumb=25)
        off.rot("neck01", (1, 0, 0), 10); off.rot("head", (1, 0, 0), 14)
        pen = c["pen"]; pen.location = wr + Vector((0, 0, 0.05)); pen.rotation_euler = (math.radians(25), math.radians(-15), 0)
        pl = c["plans"].location
        for k, (nm, ang) in enumerate((("PlanA", 0.0), ("PlanB", math.pi), ("PlanC", -math.pi / 2))):
            h = P[nm]
            d = Vector((math.sin(ang), -math.cos(ang), 0))
            pos = pl - d * (0.85 if k < 2 else 1.25)
            twp.stand(h, (pos.x, pos.y, 0), ang)
            h.rot("spine03", Vector((-d.y, d.x, 0)) * -1, 18); h.rot("head", Vector((-d.y, d.x, 0)) * -1, 18)
            side = d.cross(Vector((0, 0, 1)))
            edge = pl - d * (0.38 if k < 2 else 0.5)                      # hands flat on the desk edge, leaning in
            for sd, sg in (("L", -1), ("R", 1)):
                reach(h, sd, edge + side * 0.22 * sg + Vector((0, 0, 0.06)), Vector((sg * side.x, sg * side.y, -0.6)), d + Vector((0, 0, -1.2)))
            from human import fingers_curl as _fc
            _fc(h, 10, thumb=5)
        bpy.context.view_layer.update()
        return
    if night and shot == "page_out":
        tw = c["tw"]
        T.type_at(tw, sec, text=TEXT_P, start=-45.0, cps=5.5)              # a finished page
        k = ease(min(1.0, max(0.0, (sec - 0.6) / 3.2)))
        tw["feed"].location.z += 0.16 * k                                  # the knob turns, the page winds up and out
        tw["platen"].rotation_euler.x += 0.16 * k / T.PLATEN_R
        tw["paper"].location = (0, 0.03 * k, 0.12 * max(0.0, (k - 0.55) / 0.45))
        bpy.context.view_layer.update()
        return
    if night:
        T.type_at(c["tw"], sec, text=TEXT_N, start=0.6 if shot == "night_type" else 99.0, cps=2.6)
    else:
        for k, tw in enumerate(c["tws"]):
            T.type_at(tw, sec + k * 1.3, start=0.0, cps=7.0 if k == 0 else 6.0)
        P = c["people"]
        twp.type_pose(P["sec"], c["tws"][0], sec)
        twp.type_pose(P["sec2"], c["tws"][1], sec + 0.8)
        # the clerk walks to the board with the notice, pins it; the reader walks in and stops beside him
        cl = P["clerk"]; nt = c["notice"]
        moving = twp.walk(cl, (-2.2, 1.6), (-3.55, -0.2), sec, speed=1.0)
        if moving:
            hand = cl.bone_head("lowerarm02.R") + twp.forward(cl) * 0.1
            nt.location = hand + Vector((0, 0, -0.05)); nt.rotation_euler = (math.radians(90), 0, math.radians(90))
        else:
            from human import reach, fingers_curl
            twp.face(cl, -math.pi / 2)                       # faces -X, the board
            k = ease(min(1.0, max(0.0, (sec - 2.1) / 0.9)))
            start = Vector((-3.7, -0.15, 1.35)); tgt = Vector((-3.966, -0.25, 1.62))
            nt.location = start.lerp(tgt, k)
            reach(cl, "R", nt.location + Vector((0.07, 0.07, 0.06)), Vector((0.3, -0.6, -0.7)), Vector((-1, 0, 0.2)))
            reach(cl, "L", nt.location + Vector((0.07, -0.07, 0.06)) if sec > 2.6 else cl.bone_head("upperarm01.L") + Vector((0.05, 0.1, -0.55)),
                  Vector((0.3, 0.7, -0.6)), Vector((-1, 0, 0.0)))
            fingers_curl(cl, 25, thumb=15)
        rd = P["reader"]
        if sec < 1.2:
            twp.walk(rd, (-1.0, -2.5), (-3.2, -1.3), 0.0)
        else:
            m = twp.walk(rd, (-1.0, -2.5), (-3.2, -1.25), sec - 1.2, speed=1.1)
            if not m:
                twp.face(rd, -math.pi / 2 - 0.35)
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def _tw(c, p):
    return T.world(c["tw"], p)


def cam_typing(c, t):
    e = ease(t)
    hd = c["people"]["sec"].bone_head("head")
    tgt = _tw(c, (0.0, -0.05, 0.14)).lerp(hd, 0.4)
    a = _tw(c, (2.1, -0.32, 0.62)); b = _tw(c, (1.85, -0.3, 0.58))       # medium-wide, side-on: her, the desk, the machine
    return (a.lerp(b, e), tgt, 32)


def cam_notice(c, t):
    e = ease(t)
    return (Vector((-0.6, 0.9, 1.65)).lerp(Vector((-0.85, 0.75, 1.62)), e), Vector((-3.7, -0.6, 1.4)), 30)


def cam_night_push(c, t):
    e = ease(t)
    tgt = _tw(c, (0.0, -0.02, 0.1))
    a = _tw(c, (0.55, -1.6, 0.55)); b = _tw(c, (0.3, -0.95, 0.38))
    return (a.lerp(b, e), tgt, 40)


def cam_night_type(c, t):
    """The hero macro: low over the keyboard, the ball centred, a slow drift that keeps pace with the carrier."""
    e = ease(t)
    x0 = T.PAGE_LEFT + T.MARGIN; x1 = x0 + 10 * T.PITCH
    cx = x0 + (x1 - x0) * t
    a = _tw(c, (cx + 0.07, -0.21, 0.27)); b = _tw(c, (cx + 0.05, -0.18, 0.25))
    return (a.lerp(b, e), _tw(c, (cx - 0.004, T.BALL_Y + 0.008, T.BALL_Z + 0.008)), 55)


def analyst_images(pa, pb):
    """A printout of letters run together (no spaces), and the same with pencil slashes between the words."""
    import skia
    words = "theembassywillsendthecableonthursdaythedelegationholdsitspositiononvolumesandpricethemeeting".upper()
    W_, H_ = 900, 1140
    out = []
    for slash, path in ((False, pa), (True, pb)):
        sf = skia.Surface(W_, H_); cv = sf.getCanvas(); cv.clear(skia.Color4f(0.9, 0.88, 0.8, 1))
        p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(0.12, 0.12, 0.16, 1))
        f = skia.Font(skia.Typeface.MakeFromFile(T.MONO_B), 30)
        pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3); pen.setColor4f(skia.Color4f(0.25, 0.25, 0.3, 0.9))
        y = 120
        for ln in range(8):
            row = words[(ln * 37) % 60:(ln * 37) % 60 + 40]
            cv.drawString(row, 60, y, f, p)
            if slash:
                for k in range(3, 40, 5):
                    x = 60 + k * 18.0
                    cv.drawLine(x, y + 8, x + 6, y - 26, pen)
            y += 70
        sf.makeImageSnapshot().save(path, skia.kPNG); out.append(path)
    return out


def plans_image(path):
    """A building floor plan drawing (generic): walls as heavy lines, doors as arcs, a title block."""
    import skia
    W_, H_ = 1800, 1240
    s = skia.Surface(W_, H_); cv = s.getCanvas(); cv.clear(skia.Color4f(0.84, 0.86, 0.88, 1))
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7); p.setColor4f(skia.Color4f(0.14, 0.2, 0.35, 1))
    thin = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2); thin.setColor4f(skia.Color4f(0.2, 0.26, 0.4, 1))
    cv.drawRect(skia.Rect.MakeXYWH(100, 100, 1600, 900), p)
    cv.drawLine(100, 520, 1700, 520, p); cv.drawLine(100, 620, 1700, 620, p)
    for k in range(1, 8):
        x = 100 + k * 200
        cv.drawLine(x, 100, x, 520, p); cv.drawLine(x, 620, x, 1000, p)
        cv.drawArc(skia.Rect.MakeXYWH(x - 160, 440, 80, 80), 0, -90, False, thin)
        cv.drawArc(skia.Rect.MakeXYWH(x - 160, 620, 80, 80), 0, 90, False, thin)
    for k in range(12):
        cv.drawLine(1500, 640 + k * 30, 1700, 640 + k * 30, thin)
    cv.drawRect(skia.Rect.MakeXYWH(1300, 1060, 400, 120), thin)
    s.makeImageSnapshot().save(path, skia.kPNG)
    return path


def cam_nsa_desk(c, t):
    e = ease(t)
    return (Vector((DESK_A.x - 1.3, DESK_A.y - 0.6, 1.55)).lerp(Vector((DESK_A.x - 1.1, DESK_A.y - 0.45, 1.5)), e), Vector((DESK_A.x - 0.15, DESK_A.y + 0.45, 1.0)), 38)


def cam_nsa_plans(c, t):
    e = ease(t)
    return (Vector((-3.3, 0.6, 1.45)).lerp(Vector((-3.05, 0.55, 1.42)), e), Vector((-1.4, 0.35, 1.15)), 32)        # side-on, eye level


def cam_records_drawer(c, t):
    e = ease(t)
    return (Vector((0.9, 0.2, 1.65)).lerp(Vector((1.1, 0.35, 1.62)), e), Vector((2.45, 1.85, 1.05)), 32)


def cam_records_burn(c, t):
    e = ease(t); b = c["bag"].location
    return (b + Vector((-1.9, -2.2, 1.55)).lerp(Vector((-1.7, -1.95, 1.5)), e), b + Vector((0.4, 0, 0.75)), 30)


def cam_attache(c, t):
    e = ease(t)
    a = _tw(c, (2.1, -0.32, 0.62)); b = _tw(c, (1.85, -0.3, 0.58))
    return (a.lerp(b, e), _tw(c, (0.0, -0.05, 0.14)).lerp(c["people"]["sec"].bone_head("head"), 0.4), 32)


def cam_platen(c, t):
    e = ease(t); car = c["tw"]["carrier"].location.x
    a = _tw(c, (0.36, -0.1, 0.3)); b = _tw(c, (0.3, -0.08, 0.27))       # from the side, past the platen knob, onto the page
    return (a.lerp(b, e), _tw(c, (-0.02, 0.05, 0.19)), 50)


def cam_page_out(c, t):
    e = ease(t)
    a = _tw(c, (0.35, -0.55, 0.42)); b = _tw(c, (0.28, -0.45, 0.45))
    return (a.lerp(b, e), _tw(c, (0.0, 0.05, 0.22)), 42)


def cam_count(c, t):
    e = ease(t)
    return (Vector((-4.5, -3.0, 1.75)).lerp(Vector((-4.0, -2.7, 1.7)), e), Vector((2.0 - 3.5 * e, -0.6, 1.1)), 26)


MOVES = {
    "count": dict(kind="anim", dof=None, cam=cam_count, anim=anim("count")),
    "analyst": dict(kind="anim", dof=2.2, cam=lambda c, t: (Vector((DESK_A.x - 1.0, DESK_A.y - 0.6, 1.55)).lerp(Vector((DESK_A.x - 0.85, DESK_A.y - 0.45, 1.5)), ease(t)),
                                                         Vector((DESK_A.x - 0.15, DESK_A.y + 0.35, 0.95)), 35),
                    focus=lambda c, t: c["printout"].location, anim=anim("analyst")),
    "page_out": dict(kind="anim", dof=1.8, cam=cam_page_out, focus=lambda c, t: _tw(c, (0.0, 0.05, 0.22)), anim=anim("page_out")),
    "records_drawer": dict(kind="anim", dof=2.2, cam=cam_records_drawer, focus=lambda c, t: c["drawer"].matrix_world @ Vector((0, 0.3, 0.1)), anim=anim("records_drawer")),
    "records_burn": dict(kind="anim", dof=2.6, cam=cam_records_burn, focus=lambda c, t: c["bag"].location + Vector((0.2, 0, 0.7)), anim=anim("records_burn")),
    "attache": dict(kind="anim", dof=2.6, cam=cam_attache, focus=lambda c, t: _tw(c, (0.0, 0.0, 0.13)), anim=anim("attache")),
    "platen": dict(kind="anim", dof=1.6, cam=cam_platen, focus=lambda c, t: T.strike_point(c["tw"]) + Vector((0, 0, 0.03)), anim=anim("platen")),
    "nsa_desk": dict(kind="anim", dof=2.4, cam=cam_nsa_desk, focus=lambda c, t: c["pad"].location, anim=anim("nsa_desk")),
    "nsa_plans": dict(kind="anim", dof=3.0, cam=cam_nsa_plans, focus=lambda c, t: c["plans"].location, anim=anim("nsa_plans")),
    "typing": dict(kind="anim", dof=2.6, cam=cam_typing, focus=lambda c, t: _tw(c, (0.0, 0.03, 0.13)), anim=anim("typing")),
    "notice": dict(kind="anim", dof=3.2, cam=cam_notice, focus=lambda c, t: c["notice"].location, anim=anim("notice")),
    "night_push": dict(kind="anim", dof=2.0, cam=cam_night_push, focus=lambda c, t: _tw(c, (0, 0, 0.12)), anim=anim("night_push")),
    "night_type": dict(kind="anim", dof=6.3, cam=cam_night_type, focus=lambda c, t: T.world(c["tw"], (c["tw"]["carrier"].location.x, T.BALL_Y, T.BALL_Z)), anim=anim("night_type")),
}
