"""SET 2 / INVESTIGATION ROOM (dramatization). Cool daylight through blinds, fluorescent panels.
A: close behind a woman at a filing cabinet: her fingers walk the folder tabs and she lifts one out.
B: the camera cranes up and back to reveal the room: work tables piled with document boxes and paper,
   three investigators reading, one at two monitors, an evidence wall of pinned pages and photos.

Timing from the voiceover: A 7.90-11.12 (3.22 s)  "The same day, Nvidia opens an independent investigation"
                           B 11.12-14.60 (3.48 s) "into whether a foreign intelligence service targeted him."
"""
import os, sys, math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion
from kit import *
from common import grid_mesh
from human import Human, add_asset, reset_pose, fingers_curl, pose_walk, pose_sit, _world_verts, SIDE, reach
import ph
import paper_tex

EXPOSURE = -0.6
DUR = {"drawer": 3.22, "reveal": 3.48, "filing": 4.0, "chart": 4.0, "pinning": 4.5}
CAB_Y = 3.3                       # cabinet fronts (they stand against the back wall y = 4)


# ============================================================================ helpers
def img_mat(name, path, rough=0.7, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['UV'], t.inputs['Vector'])
    L.new(t.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = rough
    if emit:
        L.new(t.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = emit
    return m


def sheet(name, loc, size, mat, rot=(0, 0, 0)):
    """A sheet of paper (UV plane), size (w, h) in metres, lying in its local XY plane."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    o.data.materials.append(mat)
    return o


def office_chair(loc, rot_z, fab, metal):
    parts = [box("Seat", (0, 0, 0.47), (0.5, 0.48, 0.08), fab, bevel=0.03),
             box("Back", (0, 0.24, 0.85), (0.46, 0.06, 0.55), fab, bevel=0.03),
             cyl("Stem", (0, 0, 0.25), 0.025, 0.42, metal, verts=16)]
    for k in range(5):
        a = k / 5 * 2 * math.pi
        parts.append(box("Leg", (0.17 * math.cos(a), 0.17 * math.sin(a), 0.04), (0.34, 0.035, 0.03), metal, rot=(0, 0, a)))
    c = join(parts, "Chair"); c.location = loc; c.rotation_euler = (0, 0, rot_z)
    return c


def stand(h, loc, face_z):
    """Standing, arms relaxed. face_z: rotation about Z (0 = facing -Y)."""
    pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = loc; bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()


def seat_person(h, loc, face_z, lean=12):
    reset_pose(h); pose_sit(h, lean=lean)
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = loc; bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()


def person(name, gender, years, cloth, hair, hv=0.35, skin=None, cval=0.3):
    h = Human(name, gender=gender, years=years, muscle=0.5, weight=0.45, height=0.5, eyelashes="eyelashes01",
              skin=skin or ("middleage_lightskinned_female_diffuse.png" if gender < 0.5 else "middleage_lightskinned_male_diffuse.png"))
    add_asset(h, "clothes", cloth, val=cval, rough=0.7)
    add_asset(h, "clothes", "shoes02", val=0.2, rough=0.4)
    add_asset(h, "hair", hair, val=hv, rough=0.45)
    return h


# ============================================================================ build
def filing_cabinet(x, steel, handle_m, open_drawer=False):
    """4-drawer vertical file. Returns the open drawer (an object you can slide along -Y) and its folders."""
    W, D, Hh = 0.47, 0.7, 1.33
    box("CabBody", (x, CAB_Y + D / 2, Hh / 2), (W, D, Hh), steel, bevel=0.006)
    drawers = []
    for k in range(4):
        z = 0.08 + k * 0.31 + 0.15
        front = box("DrawerFront", (0, 0, 0), (W - 0.02, 0.025, 0.29), steel, bevel=0.004)
        hnd = box("Handle", (0, -0.03, 0.06), (0.16, 0.02, 0.025), handle_m, bevel=0.005)
        lbl = box("Label", (0, -0.014, 0.1), (0.09, 0.004, 0.04), pbr("LabelCard", (0.85, 0.84, 0.8), 0.8))
        parts = [front, hnd, lbl]
        if open_drawer and k == 2:
            parts += [box("DrawerSideL", (-0.2, 0.3, -0.02), (0.012, 0.6, 0.24), steel),
                      box("DrawerSideR", (0.2, 0.3, -0.02), (0.012, 0.6, 0.24), steel),
                      box("DrawerBack", (0, 0.6, -0.02), (0.41, 0.012, 0.24), steel),
                      box("DrawerBottom", (0, 0.3, -0.14), (0.41, 0.6, 0.01), steel)]
            for sx in (-0.185, 0.185):        # hanging-folder rails
                parts.append(box("Rail", (sx, 0.3, 0.09), (0.012, 0.6, 0.012), handle_m))
        d = join(parts, f"Drawer{k}")
        d.location = (x, CAB_Y - 0.012, z)
        drawers.append(d)
    return drawers


def hanging_folders(drawer, rng):
    """~34 hanging folders in the open drawer, as children of the drawer (they slide with it)."""
    green = pbr("HangGreen", (0.07, 0.2, 0.12), 0.75)
    manila = [pbr(f"Manila{k}", col, 0.8) for k, col in enumerate(((0.66, 0.53, 0.32), (0.6, 0.48, 0.28), (0.7, 0.58, 0.38)))]
    tabw = pbr("TabWhite", (0.88, 0.88, 0.85), 0.7)
    folders = []
    for k in range(34):
        y = 0.04 + k * 0.016
        f = box("Folder", (0, 0, 0), (0.37, 0.003, 0.22), green if k % 3 == 0 else manila[k % 3])
        tab = box("Tab", ((k % 4 - 1.5) * 0.08, -0.001, 0.125), (0.06, 0.004, 0.028), tabw)
        tab.parent = f                                   # local coordinates (identity parent inverse)
        f.parent = drawer; f.location = (0, y, -0.03)
        f.rotation_euler = (rng.uniform(-0.06, 0.06), 0, rng.uniform(-0.02, 0.02))
        folders.append(f)
    return folders


def build(variant=None):
    c = {}
    rng = np.random.default_rng(12)
    paper = paper_tex.make_all()
    world_sky(sun_elev_deg=28, sun_rot_deg=95, strength=0.5, tint=(0.85, 0.9, 1.0))
    # ---------------------------------------------------------------- room
    fl = pbr("PolishedConcrete", (0.42, 0.43, 0.44), 0.32, 0.0, **{'Coat Weight': 0.3, 'Coat Roughness': 0.2})
    N = fl.node_tree.nodes; L = fl.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 1.2; nz.inputs['Detail'].default_value = 8; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (0.36, 0.37, 0.38, 1); rp.color_ramp.elements[1].color = (0.48, 0.49, 0.5, 1)
    L.new(nz.outputs['Fac'], rp.inputs['Fac']); L.new(rp.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    box("Floor", (0, 0, -0.01), (12, 8, 0.02), fl)
    wall = pbr("WallWhite", (0.62, 0.63, 0.64), 0.85)
    box("WallBack", (0, 4.05, 1.5), (12, 0.1, 3.0), wall); box("WallFront", (0, -4.05, 1.5), (12, 0.1, 3.0), wall)
    box("WallL", (-6.05, 0, 1.5), (0.1, 8, 3.0), wall)
    box("Ceiling", (0, 0, 3.02), (12, 8, 0.04), pbr("CeilTile", (0.7, 0.7, 0.7), 0.9))
    # right wall: windows with blinds (cool daylight raking across the tables)
    frame = pbr("WinFrame", (0.6, 0.6, 0.62), 0.4, 0.6)
    box("WallR_low", (6.05, 0, 0.45), (0.1, 8, 0.9), wall); box("WallR_high", (6.05, 0, 2.75), (0.1, 8, 0.5), wall)
    for k in range(5):
        box("WinPier", (6.05, -3.6 + k * 1.8, 1.65), (0.1, 0.3, 1.6), wall)
    slat = pbr("Blind", (0.75, 0.75, 0.74), 0.5)
    for k in range(32):
        box("Slat", (5.95, 0, 0.92 + k * 0.05), (0.05, 7.6, 0.006), slat, rot=(0, math.radians(-50), 0))
    sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 3.2; sun.angle = math.radians(1.2); sun.color = (1.0, 0.95, 0.88)
    so = bpy.data.objects.new("Sun", sun); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(55), math.radians(-38), math.radians(-90))
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 7.6; pt.size_y = 1.6; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (6.0, 0, 1.65); po.rotation_euler = (0, math.radians(-90), 0)
    # fluorescent panels (scanned fixture) + soft area lights under them
    for x in (-3, 0, 3):
        for y in (-2, 1):
            ph.model("mounted_fluorescent_lights", loc=(x, y, 3.0), rot_z=math.radians(90))
            l = area_light((x, y, 2.9), (0, 0, 0), 0.9, 55, (0.9, 0.96, 1.0)); l.rotation_euler = (0, 0, 0); l.visible_camera = False
    # ---------------------------------------------------------------- filing cabinets along the back wall
    steel = pbr("SteelGrey", (0.42, 0.43, 0.44), 0.42, 0.55, **{'Coat Weight': 0.15})
    handle_m = pbr("Chrome", (0.8, 0.8, 0.8), 0.2, 1.0)
    for k, x in enumerate((-2.2, -1.72, -1.24, -0.48, 0.0, 0.48, 1.24, 1.72)):
        ds = filing_cabinet(x, steel, handle_m, open_drawer=(x == 0.0))
        if x == 0.0:
            c["drawer"] = ds[2]; c["drawer_closed_y"] = ds[2].location.y
            c["folders"] = hanging_folders(ds[2], rng)
    # ---------------------------------------------------------------- work tables, boxes, paper
    top = pbr("Laminate", (0.72, 0.72, 0.7), 0.35)
    legm = pbr("TableLeg", (0.15, 0.15, 0.16), 0.4, 0.8)
    page_m = [img_mat(f"Page{k}", p, 0.75) for k, p in enumerate(paper["pages"])]
    photo_m = [img_mat(f"Photo{k}", p, 0.3) for k, p in enumerate(paper["photos"])]
    for tx in (-1.7, 1.7):
        box("TableTop", (tx, -0.6, 0.74), (1.2, 3.6, 0.04), top, bevel=0.004)
        for sx in (-0.55, 0.55):
            for sy in (-2.3, 1.1):
                box("TLeg", (tx + sx, sy, 0.37), (0.04, 0.04, 0.72), legm)
        for k in range(5):                      # document boxes, some open
            bx, by = tx + rng.uniform(-0.35, 0.35), -2.0 + k * 0.75 + rng.uniform(-0.1, 0.1)
            ph.model("cardboard_box_01", loc=(bx, by, 0.76), rot_z=rng.uniform(-0.3, 0.3))
            if rng.random() < 0.6:
                ph.model("cardboard_box_01", loc=(bx + rng.uniform(-0.03, 0.03), by, 1.1), rot_z=rng.uniform(-0.3, 0.3))
        for k in range(14):                     # loose pages and photos fanned on the table
            m = photo_m[k % len(photo_m)] if k % 4 == 0 else page_m[k % len(page_m)]
            size = (0.2, 0.15) if k % 4 == 0 else (0.21, 0.28)
            sheet("Paper", (tx + rng.uniform(-0.5, 0.5), rng.uniform(-2.3, 1.1), 0.762 + k * 0.0006), size, m, rot=(0, 0, rng.uniform(-0.6, 0.6)))
        for k in range(3):
            ph.model("binder_notebook", loc=(tx + rng.uniform(-0.4, 0.4), rng.uniform(-2.0, 1.0), 0.762), rot_z=rng.uniform(0, 3))
    # evidence wall on the left: cork board with pinned pages and photos
    cork = pbr("Cork", (0.42, 0.3, 0.19), 0.9)
    N = cork.node_tree.nodes; L = cork.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 300; nz.inputs['Detail'].default_value = 4; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.3; L.new(nz.outputs['Fac'], bm.inputs['Height']); L.new(bm.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    box("Cork", (-5.98, -0.3, 1.6), (0.03, 4.2, 1.5), cork)
    pin_m = pbr("Pin", (0.8, 0.1, 0.08), 0.3)
    for k in range(26):
        m = photo_m[k % len(photo_m)] if k % 3 == 0 else page_m[k % len(page_m)]
        size = (0.22, 0.165) if k % 3 == 0 else (0.2, 0.26)
        y, z = -2.2 + (k % 9) * 0.47 + rng.uniform(-0.06, 0.06), 1.05 + (k // 9) * 0.45 + rng.uniform(-0.05, 0.05)
        sheet("Pinned", (-5.955, y, z), size, m, rot=(math.radians(90), rng.uniform(-0.06, 0.06), math.radians(90)))
        cyl("PinHead", (-5.94, y, z + size[1] / 2 - 0.02), 0.006, 0.012, pin_m, verts=8, rot=(0, math.radians(90), 0))
    # monitor desk on the right (scanned metal desk) with two screens of records
    ph.model("metal_office_desk", loc=(4.4, 0.6, 0.0), rot_z=math.radians(90))
    scr_m = [img_mat(f"Screen{k}", p, 0.2, emit=1.4) for k, p in enumerate(paper["screens"])]
    bez = pbr("Bezel", (0.02, 0.02, 0.022), 0.35)
    for k, dy in enumerate((-0.32, 0.32)):
        box("Monitor", (4.85, 0.6 + dy, 1.12), (0.03, 0.6, 0.36), bez, bevel=0.004, rot=(0, 0, math.radians(-10 if dy < 0 else 10)))
        sheet("Screen", (4.83, 0.6 + dy, 1.12), (0.57, 0.33), scr_m[k], rot=(math.radians(90), 0, math.radians(-90 + (-10 if dy < 0 else 10))))
        box("MonStand", (4.88, 0.6 + dy, 0.88), (0.08, 0.16, 0.12), bez)
    box("Keyboard", (4.55, 0.6, 0.8), (0.16, 0.44, 0.015), bez)
    fab = fabric("ChairFab", (0.08, 0.09, 0.1), 0.85, 0.3, 300)
    # ---------------------------------------------------------------- people
    people = {}
    w = person("Investigator", 0.0, 34, "female_casualsuit01", "ponytail01", hv=0.25, cval=0.35)
    stand(w, (0.05, 2.42, 0), math.pi)            # facing the cabinet (+Y)
    people["woman"] = w
    readers = [("ReaderA", 1.0, 52, "male_casualsuit03", "short04", (-2.45, -1.4), math.pi / 2),     # faces +X (table)
               ("ReaderB", 0.0, 41, "female_elegantsuit01", "bob02", (-0.95, 0.1), -math.pi / 2),   # faces -X (table)
               ("ReaderC", 1.0, 45, "male_worksuit01", "short01", (2.45, -0.9), -math.pi / 2)]      # faces -X (table)
    for nm, g, yrs, cl, hr, (x, y), fz in readers:
        h = person(nm, g, yrs, cl, hr, hv=0.3 + 0.1 * g)
        seat_person(h, (x, y, 0), fz, lean=14)
        office_chair((x - 0.08 * math.sin(fz), y + 0.08 * math.cos(fz), 0), fz, fab, legm)
        people[nm] = h
    typer = person("Analyst", 1.0, 30, "male_casualsuit02", "short03", hv=0.2)
    seat_person(typer, (4.05, 0.6, 0), math.pi / 2, lean=10)    # facing +X, the monitors
    office_chair((3.97, 0.6, 0), math.pi / 2, fab, legm)
    people["typer"] = typer
    c["people"] = people
    # the paper each reader holds (follows the hands every frame)
    c["held"] = {nm: sheet("Held" + nm, (0, 0, -5), (0.21, 0.28), page_m[k]) for k, nm in enumerate(("ReaderA", "ReaderB", "ReaderC"))}
    c["lift"] = None
    # SET 8B: the analyst's right monitor shows total assets: the 2024 bar grows bottom-to-top (frame driver wipe)
    mon = Vector((4.83, 0.92, 1.12))
    import skia as _sk
    def chart(path, full):
        W, Hh = 1600, 900
        sf = _sk.Surface(W, Hh); cv = sf.getCanvas(); cv.clear(_sk.Color4f(0.035, 0.045, 0.06, 1))
        pp = _sk.Paint(AntiAlias=True); f1 = _sk.Font(_sk.Typeface.MakeFromFile(paper_tex.SANS_SB), 46); f2 = _sk.Font(_sk.Typeface.MakeFromFile(paper_tex.SANS_SB), 64)
        pp.setColor4f(_sk.Color4f(0.85, 0.88, 0.92, 1)); cv.drawString("TOTAL ASSETS", 90, 110, f1, pp)
        pp.setColor4f(_sk.Color4f(0.3, 0.32, 0.36, 1)); cv.drawRect(_sk.Rect.MakeXYWH(90, 780, 1420, 3), pp)
        pp.setColor4f(_sk.Color4f(0.3, 0.55, 1.0, 1)); cv.drawRect(_sk.Rect.MakeXYWH(330, 772, 260, 8), pp)
        pp.setColor4f(_sk.Color4f(0.85, 0.88, 0.92, 1)); cv.drawString("2023", 400, 850, f1, pp); cv.drawString("$33M", 370, 740, f2, pp)
        cv.drawString("2024", 1060, 850, f1, pp)
        if full:
            pp.setColor4f(_sk.Color4f(1.0, 0.38, 0.28, 1)); cv.drawRect(_sk.Rect.MakeXYWH(990, 190, 260, 590), pp)
            pp.setColor4f(_sk.Color4f(0.95, 0.96, 0.98, 1)); cv.drawString("$3B", 1060, 165, f2, pp)
        sf.makeImageSnapshot().save(path, _sk.kPNG); return path
    c0 = chart(os.path.join(paper_tex.GEN, "chart_base.png"), False); c1 = chart(os.path.join(paper_tex.GEN, "chart_full.png"), True)
    cm = bpy.data.materials.new("ChartScreen"); cm.use_nodes = True
    N = cm.node_tree.nodes; L = cm.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    i0 = N.new("ShaderNodeTexImage"); i0.image = bpy.data.images.load(c0); i1 = N.new("ShaderNodeTexImage"); i1.image = bpy.data.images.load(c1)
    L.new(tc.outputs['UV'], i0.inputs['Vector']); L.new(tc.outputs['UV'], i1.inputs['Vector'])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
    rv = N.new("ShaderNodeValue"); dr = rv.outputs[0].driver_add("default_value").driver; dr.type = 'SCRIPTED'
    dr.expression = "0.13 + 0.8 * min(1, max(0, (frame - 25) / 50))"
    lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; L.new(sep.outputs['Y'], lt.inputs[0]); L.new(rv.outputs[0], lt.inputs[1])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(lt.outputs[0], mx.inputs['Factor']); L.new(i0.outputs['Color'], mx.inputs[6]); L.new(i1.outputs['Color'], mx.inputs[7])
    em = N.new("ShaderNodeEmission"); em.inputs['Strength'].default_value = 1.4; L.new(mx.outputs[2], em.inputs['Color']); L.new(em.outputs[0], out.inputs['Surface'])
    for o in bpy.data.objects:                       # put the chart on the right-hand monitor
        if o.name.startswith("Screen") and o.location.y > 0.7 and o.location.x > 4.5:
            o.data = o.data.copy(); o.data.materials.clear(); o.data.materials.append(cm)
    c["mon"] = mon
    # SET 11A: an investigator standing at the evidence wall, pinning one more page
    pinner = person("Pinner", 1.0, 39, "male_casualsuit01", "short02", hv=0.25)
    stand(pinner, (-5.35, 0.4, 0), -math.pi / 2)                  # faces -X, the wall
    c["people"]["pinner"] = pinner
    c["pin_page"] = sheet("PinPage", (-5.6, 0.45, 1.5), (0.2, 0.26), page_m[2], rot=(math.radians(90), 0, math.radians(90)))
    animate(c, 0.0, {})
    return c


# ============================================================================ animation
def _forward(h):
    return (h.arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def pose_reader(c, nm, sec, ph_):
    h = c["people"][nm]; fwd = _forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    chest = h.bone_head("spine03") + Vector((0, 0, 0.05))
    hold = chest + fwd * 0.34 + Vector((0, 0, -0.08 + 0.01 * math.sin(sec * 0.8 + ph_)))
    for sd, sg in (("L", -1), ("R", 1)):
        reach(h, sd, hold + side * (0.11 * sg), Vector((sg * side.x, sg * side.y, -0.8)), fwd + Vector((0, 0, 0.3)))
    fingers_curl(h, 25, thumb=10)
    h.rot("head", side, 10 + 3 * math.sin(sec * 0.6 + ph_))          # reading, small nods
    ps = c["held"][nm]
    ps.location = hold + Vector((0, 0, 0.03)); bpy.context.view_layer.update()
    # sheet faces the reader's eyes, tilted back
    look = (h.bone_head("head") - ps.location).normalized()
    ps.rotation_mode = 'QUATERNION'; ps.rotation_quaternion = look.to_track_quat('Z', 'Y')


def pose_typer(c, sec):
    h = c["people"]["typer"]; fwd = _forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    kb = Vector((4.55, 0.6, 0.83))
    for sd, sg in (("L", -1), ("R", 1)):
        tap = 0.008 * max(0.0, math.sin(sec * 22 + (0 if sd == "L" else 1.7)))
        reach(h, sd, kb + side * (0.1 * sg) - fwd * 0.05 + Vector((0, 0, 0.05 - tap)), Vector((sg * side.x, sg * side.y, -0.7)), fwd + Vector((0, 0, -0.4)))
    fingers_curl(h, 35, thumb=10)
    h.rot("head", (0, 0, 1), 6 * math.sin(sec * 0.5))


def pose_woman(c, sec, lift):
    """Right hand walks along the tabs (sec), then pinches one folder and lifts it (lift 0..1)."""
    h = c["people"]["woman"]
    d = c["drawer"]; M = d.matrix_world
    k_target = 22
    walk = min(1.0, sec / 2.0)
    yk = 0.04 + (6 + walk * (k_target - 6)) * 0.016           # along the drawer (local +Y = into the cabinet)
    hand = M @ Vector((0.02, yk, 0.16 + 0.015 * abs(math.sin(sec * 9)) * (1 - lift)))
    hand += Vector((0, 0, 0.35 * ease(lift)))
    reach(h, "R", hand + Vector((0, -0.04, 0.05)), Vector((0.8, -0.3, -0.4)), Vector((0, 0.35, -1)))
    reach(h, "L", M @ Vector((-0.16, -0.03, 0.15)), Vector((-0.8, -0.3, -0.5)), Vector((0, 0.6, -0.8)))
    fingers_curl(h, 20 + 30 * min(1.0, lift * 3), thumb=20)
    h.rot("spine04", (1, 0, 0), -6); h.rot("head", (1, 0, 0), -14)
    f = c["folders"][k_target]
    if lift > 0:
        f.location.z = -0.03 + 0.35 * ease(lift) / max(d.scale.z, 1e-6)
    else:
        f.location.z = -0.03


def animate(c, sec, phase):
    """sec = time since the start of Set 2 (A starts at 0)."""
    d = c["drawer"]
    d.location.y = c["drawer_closed_y"] - 0.5 - 0.04 * ease(min(1.0, sec / 0.8))     # drawer already open, eases the last bit
    bpy.context.view_layer.update()
    lift = phase.get("lift", 0.0)
    pose_woman(c, sec, lift)
    for k, nm in enumerate(("ReaderA", "ReaderB", "ReaderC")):
        pose_reader(c, nm, sec, k * 1.7)
    pose_typer(c, sec)
    bpy.context.view_layer.update()


def anim_pinning(c, t):
    s_ = t * DUR["pinning"]
    animate(c, s_, {"lift": 0.0})
    h = c["people"]["pinner"]; pg = c["pin_page"]
    k = ease(min(1.0, s_ / 2.2))
    target = Vector((-5.955, 0.45, 1.72)); start = Vector((-5.55, 0.42, 1.35))
    pg.location = start.lerp(target, k)
    reach(h, "R", pg.location + Vector((0.08, -0.06, 0.05)), Vector((0.2, -0.8, -0.6)), Vector((-1, 0, 0.2)))
    reach(h, "L", pg.location + Vector((0.08, 0.1, -0.05)) if s_ < 2.4 else h.bone_head("upperarm01.L") + Vector((0.05, 0.1, -0.55)),
          Vector((0.2, 0.8, -0.6)), Vector((-1, 0, 0.0)))
    fingers_curl(h, 30, thumb=15)
    bpy.context.view_layer.update()


def anim_drawer(c, t):
    s = t * DUR["drawer"]
    animate(c, s, {"lift": ease(max(0.0, (s - 2.2) / 1.0)) * 0.35})


def anim_reveal(c, t):
    s = DUR["drawer"] + t * DUR["reveal"]
    animate(c, s, {"lift": 0.35 + 0.65 * ease(min(1.0, t / 0.7))})


# ============================================================================ cameras
def cam_drawer(c, t):
    e = ease(t)
    sh = c["people"]["woman"].bone_head("upperarm01.R")
    tgt = c["drawer"].matrix_world @ Vector((0.0, 0.32, 0.05))
    loc = (sh + Vector((0.2, -0.42, 0.22))).lerp(sh + Vector((0.14, -0.3, 0.16)), e)
    return (loc, tgt, 50)


def cam_reveal(c, t):
    e = ease(t)
    sh = c["people"]["woman"].bone_head("upperarm01.R")
    start = sh + Vector((0.14, -0.3, 0.16)); end = Vector((0.5, -3.75, 2.45))
    tgt0 = c["drawer"].matrix_world @ Vector((0.0, 0.32, 0.05)); tgt1 = Vector((0.4, 0.5, 0.75))
    loc = start.lerp(end, e)
    return (loc, tgt0.lerp(tgt1, ease(min(1.0, t * 1.4))), 50 - 26 * e)


def anim_filing(c, t):
    """Her shot only: clear the document boxes between the camera and her (they stay in every other shot)."""
    if not c.get("_cleared"):
        hd = c["people"]["ReaderB"].bone_head("head")
        for o in bpy.data.objects:
            if (o.name.startswith("cardboard_box") or (o.parent and o.parent.name.startswith("cardboard_box"))) and o.type == 'MESH':
                p = o.matrix_world.translation
                if (Vector((p.x, p.y)) - Vector((hd.x, hd.y))).length < 1.6:
                    o.hide_render = True; o.hide_viewport = True
        c["_cleared"] = True
    animate(c, t * DUR["filing"], {"lift": 0.0})


def cam_filing(c, t):
    h = c["people"]["ReaderB"]; e = ease(t)
    fwd = _forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    hd = h.bone_head("head")
    off0 = fwd * 1.2 - side * 0.85 + Vector((0, 0, 0.35)); off1 = fwd * 1.05 - side * 0.75 + Vector((0, 0, 0.32))
    tgt = hd + fwd * 0.25 + Vector((0, 0, -0.08))
    return (hd + off0.lerp(off1, e), tgt, 35)     # three-quarter front: her face over the filing she is reading


def cam_chart(c, t):
    e = ease(t); m = c["mon"]
    return (m + Vector((-0.75, -0.7, 0.12)).lerp(Vector((-0.62, -0.6, 0.1)), e), m + Vector((0, 0.02, 0.0)), 40)      # beside the analyst, not over his head


def cam_pinning(c, t):
    e = ease(t)
    return (Vector((-3.6, -1.4, 1.6)).lerp(Vector((-3.9, -1.0, 1.6)), e), Vector((-5.9, 0.4, 1.55)), 32)


MOVES = {
    "filing": dict(kind="anim", dof=2.4, far=10.0, cam=cam_filing, focus=lambda c, t: c["held"]["ReaderB"].location, anim=lambda c, t: anim_filing(c, t)),
    "chart": dict(kind="anim", dof=2.8, far=10.0, cam=cam_chart, focus=lambda c, t: c["mon"],
                  anim=lambda c, t: animate(c, t * DUR["chart"], {"lift": 0.0})),
    "pinning": dict(kind="anim", dof=3.2, far=20.0, cam=cam_pinning, focus=lambda c, t: Vector((-5.8, 0.42, 1.6)), anim=anim_pinning),
    "drawer": dict(kind="anim", dof=2.4, far=10.0, cam=cam_drawer, focus=lambda c, t: c["drawer"].matrix_world @ Vector((0.02, 0.35, 0.1)), anim=anim_drawer),
    "reveal": dict(kind="anim", dof=4.0, far=20.0, cam=cam_reveal,
                   focus=lambda c, t: (c["drawer"].matrix_world @ Vector((0.0, 0.32, 0.05))).lerp(Vector((-0.2, 0.2, 0.8)), ease(t)), anim=anim_reveal),
}
