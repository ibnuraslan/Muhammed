"""CLOSED COURTROOM, Moscow, 2007 (dramatization; a generic Russian courtroom: a gold double-headed eagle relief, the tricolour). Variants:
  hall    : the corridor outside; a bailiff closes the doors on the waiting press (Ch3 1A, title)
  room    : the courtroom: the judge's bench on a dais, the steel dock, prosecution and defence tables, winter light
            (Ch3 1B prosecutor, 2A dock, 2B defence and the door photograph, 3A verdict, 3B led out)
  archive : the court archive: a clerk ties the case volumes; the lights go out row by row (Ch3 4A/4B)"""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
from pbkit import joinm, image_plane, ph_instances
from pbpeople import person, stand, seat, walk_at, nod, look, hand_to, hide, fwd, recolor, hold_flat
from sc_bankoffice import retint
from sc_hospital import two_tone

EXPOSURE = 0.4
BOUNCES = 6
HERE = os.path.dirname(os.path.abspath(__file__))
DOORPHOTO = os.path.join(HERE, "..", "assets", "photos", "office_door.jpg")
DUR = {"doors": 6.0, "prosecutor": 5.5, "dock": 5.5, "defence": 5.5, "verdict": 6.0, "led_out": 6.0, "volumes": 5.5, "archive_dark": 6.5}
VARIANT_FOR = {"doors": "hall", "prosecutor": "room", "dock": "room", "defence": "room", "verdict": "room", "led_out": "room",
               "volumes": "archive", "archive_dark": "archive"}
BENCH = Vector((0.0, 6.5, 0.0))
DOCK = Vector((4.6, 2.5, 0.0))
rng = np.random.default_rng(71)


def judges_chair(loc, wood):
    """A judge's chair: a tall buttoned leather back in a carved oak frame, leather seat, oak arms."""
    leather = pbr("JudgeLeather", (0.16, 0.05, 0.04), 0.45, 0.0, **{'Coat Weight': 0.3})
    x, y, z = loc
    parts = [box("JCSeat", (0, 0, 0.47), (0.62, 0.58, 0.1), leather, bevel=0.03),
             box("JCBase", (0, 0, 0.22), (0.56, 0.52, 0.44), wood, bevel=0.01),
             box("JCBack", (0, 0.27, 1.15), (0.6, 0.1, 1.3), leather, bevel=0.04),
             box("JCFrameL", (-0.33, 0.28, 1.1), (0.06, 0.12, 1.45), wood, bevel=0.01), box("JCFrameR", (0.33, 0.28, 1.1), (0.06, 0.12, 1.45), wood, bevel=0.01),
             box("JCCrest", (0, 0.28, 1.86), (0.74, 0.12, 0.12), wood, bevel=0.03),
             box("JCArmL", (-0.33, 0.0, 0.68), (0.07, 0.55, 0.06), wood, bevel=0.01), box("JCArmR", (0.33, 0.0, 0.68), (0.07, 0.55, 0.06), wood, bevel=0.01)]
    for (bx, bz) in ((-0.15, 0.85), (0.15, 0.85), (0.0, 1.1), (-0.15, 1.35), (0.15, 1.35)):
        parts.append(cyl("JCButton", (bx, 0.215, bz), 0.012, 0.01, leather, verts=10, rot=(math.radians(90), 0, 0)))
    o = joinm(parts, "JudgesChair"); o.location = (x, y, z)
    return o


def eagle(loc, s=1.0):
    """A generic gilt relief of a double-headed eagle: spread wings of layered feathers, two crowned heads turned
    outward, a shield on the breast, tail feathers. No text, no likeness of any particular coat of arms."""
    gold = pbr("EagleGold", (0.75, 0.55, 0.2), 0.3, 1.0)
    parts = []
    parts.append(cyl("EBody", (0, 0, 0), 0.16 * s, 0.06 * s, gold, verts=24, rot=(math.radians(90), 0, 0)))
    parts.append(box("EShield", (0, -0.035 * s, -0.04 * s), (0.17 * s, 0.02 * s, 0.2 * s), pbr("EagleRed", (0.45, 0.06, 0.05), 0.4), bevel=0.02 * s))
    for sx in (-1, 1):
        for k in range(6):                                                   # wing feathers fanning up and out
            a = math.radians(20 + k * 13)
            L_ = (0.55 - 0.05 * k) * s
            cx = sx * (0.12 * s + math.cos(a) * L_ / 2); cz = 0.05 * s + math.sin(a) * L_ / 2
            parts.append(box("EFeather", (cx, 0.0, cz), (L_, 0.03 * s, 0.07 * s), gold, rot=(0, -sx * a, 0), bevel=0.01 * s))
        parts.append(cyl("ENeck", (sx * 0.09 * s, 0, 0.22 * s), 0.035 * s, 0.18 * s, gold, verts=12, rot=(0, sx * math.radians(25), 0)))
        parts.append(cyl("EHead", (sx * 0.14 * s, -0.01 * s, 0.32 * s), 0.05 * s, 0.05 * s, gold, verts=16, rot=(math.radians(90), 0, 0)))
        parts.append(box("EBeak", (sx * 0.2 * s, -0.01 * s, 0.31 * s), (0.06 * s, 0.03 * s, 0.025 * s), gold, rot=(0, sx * math.radians(-15), 0)))
        parts.append(cyl("ECrown", (sx * 0.14 * s, -0.01 * s, 0.39 * s), 0.035 * s, 0.05 * s, gold, verts=8))
        parts.append(box("ELeg", (sx * 0.06 * s, 0, -0.2 * s), (0.03 * s, 0.03 * s, 0.14 * s), gold, rot=(0, sx * math.radians(20), 0)))
    parts.append(cyl("ECrownTop", (0, -0.01 * s, 0.5 * s), 0.05 * s, 0.07 * s, gold, verts=8))
    for k in range(5):
        a = math.radians(-60 + k * 30)
        parts.append(box("ETail", (math.sin(a) * 0.08 * s, 0, -0.18 * s - math.cos(a) * 0.08 * s), (0.04 * s, 0.025 * s, 0.18 * s), gold, rot=(0, a, 0)))
    o = joinm(parts, "Eagle"); o.location = loc
    return o


def tricolour(loc):
    """The Russian tricolour hanging from a floor-standing pole with a gilt finial."""
    x, y, z = loc
    cyl("FlagPole", (x, y, z + 1.4), 0.02, 2.8, pbr("PoleWood", (0.25, 0.15, 0.08), 0.4), verts=12)
    cyl("FlagBase", (x, y, z + 0.03), 0.18, 0.06, pbr("PoleBase", (0.3, 0.25, 0.15), 0.4, 0.6), verts=24)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.045, location=(x, y, z + 2.86))
    fin = bpy.context.active_object; fin.data.materials.append(pbr("FinialGold", (0.75, 0.55, 0.2), 0.3, 1.0))
    fm = bpy.data.materials.new("Tricolour"); fm.use_nodes = True
    N = fm.node_tree.nodes; L = fm.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
    r1 = N.new("ShaderNodeValToRGB"); L.new(sep.outputs['Y'], r1.inputs['Fac']); r1.color_ramp.interpolation = 'CONSTANT'
    els = r1.color_ramp.elements
    els[0].position = 0.0; els[0].color = (0.55, 0.05, 0.05, 1)                                                  # red at the bottom
    els[1].position = 0.667; els[1].color = (0.85, 0.85, 0.83, 1)                                                # white at the top
    e = els.new(0.333); e.color = (0.04, 0.16, 0.5, 1)                                                           # blue in the middle
    assert len(els) == 3 and abs(sorted(x.position for x in els)[1] - 0.333) < 1e-3
    L.new(r1.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.7; p.inputs['Sheen Weight'].default_value = 0.4
    # the flag hangs down along the pole in soft vertical folds
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=30, size=1, location=(x + 0.33, y, z + 2.25), rotation=(math.radians(90), 0, 0))
    f = bpy.context.active_object; f.name = "Flag"; f.scale = (0.62, 0.9, 1); f.data.materials.append(fm)
    for v in f.data.vertices:
        v.co.z += 0.06 * math.sin((v.co.x + 0.5) * 14.0) * (0.3 + 0.7 * (v.co.x + 0.5))
    bpy.ops.object.shade_smooth()
    return f


def gown(h):
    recolor(h, "elegantsuit01", (0.02, 0.02, 0.025), 0.6)


def build(variant=None):
    variant = variant or "room"
    c = {"variant": variant}
    world_flat((0.62, 0.66, 0.74), 1.0)
    if variant == "hall":
        build_hall(c)
    elif variant == "archive":
        build_archive(c)
    else:
        build_room(c)
    animate(c, 0.0, {"hall": "doors", "room": "prosecutor", "archive": "volumes"}[variant])
    return c


def build_room(c):
    oak = ph.texture("wooden_panels", scale=0.35, name="CourtPanels", tint=(1.15, 0.95, 0.75))     # real panel scan, no procedural moire
    plaster = pbr("CourtWall", (0.66, 0.64, 0.58), 0.85)
    box("Floor", (0, 2, -0.01), (12, 14, 0.02), ph.texture("herringbone_parquet", scale=0.7))
    box("Ceiling", (0, 2, 5.0), (12, 14, 0.1), pbr("CCeil", (0.7, 0.68, 0.64), 0.85))
    box("WallBack", (0, 9.0, 2.5), (12, 0.2, 5.0), plaster); box("Wainscot", (0, 8.88, 0.6), (12, 0.04, 1.2), oak)
    box("WallFront", (0, -5.0, 2.5), (12, 0.2, 5.0), plaster)
    box("WallR", (6.0, 2, 2.5), (0.2, 14, 5.0), plaster)
    # left wall: tall windows, winter light
    for k in range(4):
        box("Pier", (-6.0, -4.0 + k * 3.6, 2.5), (0.2, 1.2, 5.0), plaster)
        box("WinGlassC", (-6.05, -2.2 + k * 3.6, 2.7), (0.02, 2.4, 3.4), glass("CGlass", (0.9, 0.93, 0.95), 0.02))
        l = area_light((-6.6, -2.2 + k * 3.6, 2.7), (0, math.radians(-90), 0), 2.4, 140, (0.88, 0.93, 1.0))
        l.visible_camera = False; l.visible_glossy = False; l.visible_transmission = False
    box("WinLowC", (-6.0, 2, 0.5), (0.2, 14, 1.0), plaster); box("WinHighC", (-6.0, 2, 4.7), (0.2, 14, 0.6), plaster)
    # painted window frames with glazing bars, and the building across the street instead of a flat white sky
    bar_m = pbr("CWinBar", (0.62, 0.6, 0.55), 0.5)
    for k in range(4):
        y = -2.2 + k * 3.6
        for dy in (-1.17, 0.0, 1.17):
            box("WinMullion", (-6.04, y + dy, 2.7), (0.08, 0.07 if dy == 0 else 0.08, 3.4), bar_m)
        for z in (1.03, 2.15, 3.3, 4.37):
            box("WinTransom", (-6.04, y, z), (0.08, 2.4, 0.06 if z not in (1.03, 4.37) else 0.08), bar_m)
    from pbkit import masonry_facade
    box("Outside", (-22, 2, 10), (1, 60, 30), masonry_facade("CourtOpp", (0.62, 0.6, 0.57), 3.4, 2.8, 1.3, 1.8, 0.0, lit_strength=0.0))
    box("OutsideStreet", (-14, 2, -0.5), (16, 60, 0.2), pbr("OutStreet", (0.55, 0.57, 0.6), 0.9))
    # the bench on a dais, the judge's high-backed chair
    box("Dais", (0, BENCH.y + 0.6, 0.2), (5.0, 2.6, 0.4), oak)
    box("JudgeBench", (0, BENCH.y, 0.95), (4.4, 0.7, 1.1), oak, bevel=0.02); box("JudgeTop", (0, BENCH.y - 0.05, 1.52), (4.6, 0.85, 0.05), oak)
    for x in (-1.15, 0.0, 1.15):                                            # three judges' chairs with tall leather backs
        judges_chair((x, BENCH.y + 0.85, 0.4), oak)
    box("PanelBehind", (0, 8.85, 2.4), (3.0, 0.05, 2.6), oak)
    eagle((0.0, 8.82, 3.75), 1.05)                                          # the double-headed eagle relief above the bench
    tricolour((-2.6, 8.35, 0.4))
    # oak panelling to dado height round the room
    for (loc, size) in (((0, 8.87, 0.6), (12, 0.04, 1.2)), ((5.88, 2, 0.6), (0.04, 14, 1.2)), ((0, -4.88, 0.6), (12, 0.04, 1.2))):
        box("DadoPanel", loc, size, oak)
        box("DadoRail", (loc[0], loc[1], 1.22), (size[0] + 0.02 if size[0] > 1 else 0.07, size[1] + 0.02 if size[1] > 1 else 0.07, 0.06), oak)
    for k in range(4):                                                      # under the windows too, between the piers
        box("DadoPanelL", (-5.88, -2.2 + k * 3.6, 0.5), (0.04, 2.4, 1.0), oak)
    # the dock: a steel cage on the right
    steel = pbr("CageSteel", (0.35, 0.36, 0.38), 0.35, 0.9)
    for k in range(15):
        cyl("Bar", (DOCK.x - 1.0 + k * 0.14, DOCK.y - 1.0, 1.15), 0.012, 2.3, steel, verts=8)
        cyl("BarS", (DOCK.x - 1.05, DOCK.y - 1.0 + k * 0.14, 1.15), 0.012, 2.3, steel, verts=8)
    box("CageTop", (DOCK.x, DOCK.y, 2.3), (2.1, 2.1, 0.05), steel); box("CageRail", (DOCK.x, DOCK.y - 1.0, 1.1), (2.1, 0.05, 0.05), steel)
    box("CageBench", (DOCK.x + 0.3, DOCK.y + 0.4, 0.22), (1.2, 0.4, 0.44), oak)
    box("SideDoor", (5.94, DOCK.y + 0.5, 1.05), (0.06, 0.9, 2.1), pbr("SideDoorM", (0.3, 0.2, 0.12), 0.5))
    c["sidedoor"] = joinm([box("SideDoorLeaf", (0, 0.45, 1.05), (0.05, 0.9, 2.1), pbr("SDLeaf", (0.3, 0.2, 0.12), 0.5))], "SideDoorLeaf")
    c["sidedoor"].location = (5.9, DOCK.y + 0.05, 0)
    # prosecution (left) and defence (right) tables, the public benches
    for x, nm in ((-2.4, "pros"), (2.0, "def")):
        r, d = ph.model("metal_office_desk", loc=(x, 2.4, 0), rot_z=0.0, scale=0.8); retint(d, (0.6, 0.45, 0.3))
    ph_instances("painted_wooden_bench", [((x, y, 0), math.pi, 1.0) for x in (-3.5, -2.2, -0.9, 1.2, 2.5) for y in (-1.0, -2.4)])
    import paper_tex
    pages = paper_tex.make_all()["pages"]
    for x in (-2.4, 2.0):
        for k in range(3):
            image_plane("TablePage", pages[k], (x - 0.3 + k * 0.25, 2.4, 0.64 + k * 0.001), (0.21, 0.28), (0, 0, rng.uniform(-0.2, 0.2)), rough=0.8)
    # the easel with the photograph of the open office door (defence)
    easel = joinm([box("EaselLeg", (-0.35, 0, 0.8), (0.04, 0.04, 1.65), oak, rot=(0, math.radians(8), 0)), box("EaselLeg", (0.35, 0, 0.8), (0.04, 0.04, 1.65), oak, rot=(0, math.radians(-8), 0)),
                   box("EaselBack", (0, 0.35, 0.8), (0.04, 0.04, 1.65), oak, rot=(math.radians(-20), 0, 0)), box("EaselShelf", (0, -0.02, 0.85), (0.8, 0.08, 0.03), oak)], "Easel")
    easel.location = (1.0, 4.3, 0); easel.rotation_euler = (0, 0, math.radians(-10))
    board = image_plane("DoorPhotoBoard", DOORPHOTO, (0, 0, 0), (0.8, 0.64), (0, 0, 0), rough=0.5)
    board.location = (1.0, 4.28, 1.2); board.rotation_euler = (math.radians(95), 0, math.radians(-10))
    c["fol"] = joinm([box("ProsFolder", (0, 0, 0), (0.24, 0.32, 0.012), pbr("RedFolder", (0.4, 0.08, 0.06), 0.6), bevel=0.002)], "ProsFolder")
    for x in (-3.0, 3.0):
        for y in (-3.5, 2.5):
            ph.model("Chandelier_02", loc=(x, y, 4.2), scale=1.3)
            l = bpy.data.lights.new("CL", 'POINT'); l.energy = 80; l.color = (1.0, 0.86, 0.66)
            o = bpy.data.objects.new("CL", l); bpy.context.collection.objects.link(o); o.location = (x, y, 3.9)
    # people
    c["judge"] = person("Judge", 1.0, 56, "male_elegantsuit01", "short04", cval=0.05, hv=0.55, sat=0.0); gown(c["judge"])
    c["pros"] = person("ProsecutorC", 0.0, 45, "female_elegantsuit01", "bob02", cval=0.25, hue=0.6, sat=0.6)
    c["def"] = person("Defence", 1.0, 50, "male_elegantsuit01", "short02", cval=0.15, hv=0.4, sat=0.2)
    c["defendant"] = person("Defendant", 1.0, 54, "male_casualsuit03", "short01", cval=0.3, hv=0.35, sat=0.2)
    c["guards"] = [person(f"Guard{k}", 1.0, 28 + 6 * k, "male_casualsuit01", "short02", cval=0.6, hv=0.2, hue=0.58, sat=0.35) for k in range(2)]
    c["public"] = [person(f"Public{k}", g, y, cl, hr, cval=0.3, hv=0.3) for k, (g, y, cl, hr) in enumerate(((1.0, 60, "male_casualsuit05", "short04"), (0.0, 48, "female_elegantsuit01", "bob01")))]


def build_hall(c):
    walls = two_tone("CourtHall", low=(0.45, 0.4, 0.33), high=(0.72, 0.7, 0.64), dado=1.2)
    box("HFloor", (0, 0, -0.01), (4, 16, 0.02), ph.texture("worn_tile_floor", scale=0.8)); box("HCeil", (0, 0, 3.4), (4, 16, 0.04), pbr("HC", (0.7, 0.7, 0.66), 0.9))
    box("HWallL", (-2.05, 0, 1.7), (0.1, 16, 3.4), walls)
    for (y0, y1) in ((-8, 4.6), (6.4, 8)):
        box("HWallR", (2.05, (y0 + y1) / 2, 1.7), (0.1, y1 - y0, 3.4), walls)
    box("HWallROver", (2.05, 5.5, 3.0), (0.1, 1.8, 0.8), walls)
    box("CourtroomGlow", (3.5, 5.5, 1.3), (0.05, 1.8, 2.6), emissive("CourtInside", (0.9, 0.92, 0.95), 1.3))
    # far end of the corridor: a wall with a tall window (glazing bars, winter light); a plain wall behind the camera
    box("HEndBack", (0, -8.05, 1.7), (4.2, 0.1, 3.4), walls)
    for (x0, x1, z0, z1) in ((-2.05, -0.65, 0, 3.4), (0.65, 2.05, 0, 3.4), (-0.65, 0.65, 0, 0.9), (-0.65, 0.65, 2.8, 3.4)):
        box("HEnd", ((x0 + x1) / 2, 8.05, (z0 + z1) / 2), (x1 - x0, 0.1, z1 - z0), walls)
    hbar = pbr("HWinBar", (0.6, 0.58, 0.52), 0.5)
    for x in (-0.62, 0.0, 0.62):
        box("HMullion", (x, 8.03, 1.85), (0.07, 0.08, 1.9), hbar)
    for z in (0.92, 1.55, 2.2, 2.78):
        box("HTransom", (0, 8.03, z), (1.3, 0.08, 0.06), hbar)
    box("HWinGlass", (0, 8.06, 1.85), (1.3, 0.01, 1.9), glass("HGlass", (0.9, 0.93, 0.95), 0.02))
    from pbkit import masonry_facade
    box("HOutside", (0, 20, 8), (40, 1, 30), masonry_facade("HallOpp", (0.6, 0.58, 0.55), 3.3, 2.6, 1.2, 1.7, 0.0, lit_strength=0.0))
    hl = area_light((0, 8.6, 1.85), (math.radians(-90), 0, 0), 1.3, 60, (0.88, 0.93, 1.0))
    hl.visible_camera = False; hl.visible_glossy = False; hl.visible_transmission = False
    leaves = []
    for sy in (-1, 1):
        lf = joinm([box("CDoor", (0, -sy * 0.45, 1.3), (0.06, 0.88, 2.6), pbr("CDoorM", (0.3, 0.18, 0.09), 0.4, 0.0, **{'Coat Weight': 0.3}), bevel=0.01),
                    cyl("CDoorKnob", (-0.06, -sy * 0.8, 1.1), 0.03, 0.05, pbr("Brass", (0.6, 0.45, 0.2), 0.3, 1.0), verts=12, rot=(0, math.radians(90), 0))], "CourtDoor")
        lf.location = (2.05, 5.5 + sy * 0.9, 0); leaves.append(lf)
    c["leaves"] = leaves
    ph_instances("painted_wooden_bench", [((-1.75, y, 0), math.radians(90), 1.0) for y in (-2.0, 0.5)])
    for y in (-5, -1, 3, 7):
        ph.model("mounted_fluorescent_lights", loc=(0, y, 3.38), rot_z=0.0)
        l = area_light((0, y, 3.28), (0, 0, 0), 1.0, 12, (0.92, 0.97, 1.0)); l.visible_camera = False
    c["bailiff"] = person("Bailiff", 1.0, 35, "male_casualsuit01", "short02", cval=0.6, hv=0.2, hue=0.58, sat=0.35)
    c["press"] = [person(f"Press{k}", g, y, cl, hr, cval=v, hv=0.3) for k, (g, y, cl, hr, v) in
                  enumerate(((1.0, 32, "male_casualsuit02", "short01", 0.5), (0.0, 29, "female_casualsuit01", "ponytail01", 0.4), (1.0, 44, "male_casualsuit03", "short04", 0.3)))]
    r, cam = ph.model("Camera_01"); c["pcam"] = r


def build_archive(c):
    walls = two_tone("ArchWall", low=(0.4, 0.42, 0.42), high=(0.66, 0.66, 0.62), dado=1.2)
    box("AFloor", (0, 0, -0.01), (8, 12, 0.02), ph.texture("worn_tile_floor", scale=0.8)); box("ACeil", (0, 0, 3.2), (8, 12, 0.04), pbr("AC", (0.65, 0.65, 0.62), 0.9))
    for (loc, size) in (((-4.05, 0, 1.6), (0.1, 12, 3.2)), ((4.05, 0, 1.6), (0.1, 12, 3.2)), ((0, 6.05, 1.6), (8, 0.1, 3.2)), ((0, -6.05, 1.6), (8, 0.1, 3.2))):
        box("AWall", loc, size, walls)
    # rows of shelving full of bound case volumes
    vol_ms = [pbr(f"Vol{k}", col, 0.7) for k, col in enumerate(((0.35, 0.28, 0.2), (0.25, 0.22, 0.18), (0.4, 0.33, 0.22), (0.18, 0.2, 0.22)))]
    ph_instances("wooden_bookshelf_worn", [((x, y, 0), 0.0, 1.0) for x in (-2.6, -1.25, 0.1) for y in (-3.0, -0.5, 2.0, 4.5)])
    vols = []
    for x in (-2.6, -1.25, 0.1):
        for y in (-3.0, -0.5, 2.0, 4.5):
            for sh in range(4):
                for k in range(9):
                    vols.append(box("Volume", (x - 0.55 + k * 0.125 + rng.uniform(-0.01, 0.01), y - 0.08, 0.22 + sh * 0.47 + 0.15), (0.09, 0.32, 0.3 + rng.uniform(-0.03, 0.03)), vol_ms[(k + sh) % 4]))
    c["lights"] = []
    for k, y in enumerate((4.5, 2.0, -0.5, -3.0)):
        ph.model("mounted_fluorescent_lights", loc=(-1.25, y + 1.2, 3.18), rot_z=0.0)
        l = area_light((-1.25, y + 1.2, 3.08), (0, 0, 0), 1.2, 30, (0.92, 0.97, 1.0)); l.visible_camera = False
        c["lights"].append(l)
    # the clerk's table with the volumes being tied, a trolley
    r, d = ph.model("metal_office_desk", loc=(2.5, -1.0, 0), rot_z=math.radians(90))
    r, cart = ph.model("tool_cart", loc=(2.4, 1.2, 0), rot_z=0.0)
    c["stack"] = [box("CaseVol", (2.5 + rng.uniform(-0.02, 0.02), -1.0, 0.8 + 0.05 + k * 0.1), (0.32, 0.24, 0.09), vol_ms[k % 4], bevel=0.004) for k in range(5)]
    c["twine"] = box("Twine", (2.5, -1.0, 1.05), (0.012, 0.26, 0.5), pbr("TwineM", (0.7, 0.62, 0.45), 0.8))
    c["clerk"] = person("Clerk", 0.0, 50, "female_elegantsuit01", "bob01", cval=0.35, hv=0.4, hue=0.55, sat=0.4)


def animate(c, sec, move):
    v = c["variant"]
    if v == "hall":
        k = ease(min(1.0, max(0.0, (sec - 1.0) / 2.5)))
        for sy, lf in zip((-1, 1), c["leaves"]):
            lf.rotation_euler = (0, 0, math.radians(sy * 75 * (1 - k)))
        b = c["bailiff"]
        stand(b, (1.65, 5.5, 0), math.radians(90))                       # faces +X, the doors
        hand_to(b, "R", c["leaves"][1].matrix_world @ Vector((-0.06, -0.8, 1.1)), curl=50)
        hand_to(b, "L", c["leaves"][0].matrix_world @ Vector((-0.06, 0.8, 1.1)), curl=50)
        for j, h in enumerate(c["press"]):
            stand(h, (0.4 - j * 0.65, 3.6 - 0.4 * j, 0), math.radians(180 - 30 + j * 15))
            look(h, Vector((2.0, 5.5, 1.6)), 0.8)
        cp = c["press"][0]
        c["pcam"].location = cp.bone_head("head") + fwd(cp) * 0.15 + Vector((0, 0, -0.05)); c["pcam"].rotation_euler = (0, 0, math.radians(-150))
        hand_to(cp, "R", c["pcam"].location + Vector((0.06, 0, -0.03)), curl=50)
    elif v == "archive":
        cl = c["clerk"]
        stand(cl, (1.95, -1.0, 0), math.radians(90))                     # faces +X, the desk
        nod(cl, "spine04", 14); nod(cl, "head", 18)
        tie = math.sin(sec * 2.0)
        hand_to(cl, "R", Vector((2.45, -0.88 + 0.06 * tie, 1.32)), curl=40); hand_to(cl, "L", Vector((2.45, -1.12 - 0.06 * tie, 1.32)), curl=40)
        if move == "archive_dark":
            hide(cl, True)
            n = len(c["lights"]); D = DUR["archive_dark"]                         # row by row, spread over the cut
            for k, l in enumerate(c["lights"]):
                l.data.energy = 30 if sec < D * (0.22 + 0.6 * k / max(1, n - 1)) else 0
    else:
        J, P, D, X = c["judge"], c["pros"], c["def"], c["defendant"]
        g0, g1 = c["guards"]
        seat(J, (0, BENCH.y + 0.7, 0), 0.0, lean=12, floor_z=0.65)           # faces -Y, into the room
        nod(J, "head", 14)
        hand_to(J, "R", Vector((0.25, BENCH.y - 0.05, 1.6)), hand_dir=Vector((0, -0.6, -0.8)), curl=20)
        hand_to(J, "L", Vector((-0.25, BENCH.y - 0.05, 1.6)), hand_dir=Vector((0, -0.6, -0.8)), curl=20)
        seat(P, (-2.4, 1.85, 0), math.pi, lean=12); seat(D, (2.0, 1.85, 0), math.pi, lean=12)
        stand(X, (DOCK.x + 0.1, DOCK.y + 0.3, 0), math.radians(180 + 20))     # in the dock, facing the bench
        stand(g0, (DOCK.x - 1.5, DOCK.y + 1.2, 0), math.radians(180 + 70)); stand(g1, (DOCK.x + 1.4, DOCK.y + 1.6, 0), math.radians(180 - 60))
        for k, h in enumerate(c["public"]):
            seat(h, (-2.2 + 3.4 * k, -1.4, 0), math.pi, lean=10)
        c["sidedoor"].rotation_euler = (0, 0, 0)
        c["fol"].location = (-2.3, 2.3, 0.65); c["fol"].rotation_euler = (0, 0, 0)
        if move == "prosecutor":
            stand(P, (-2.4, 1.75, 0), math.pi)
            hold_flat(P, c["fol"], dist=0.3, drop=0.05, tilt_deg=55, spread=0.13, wobble=0.005 * math.sin(sec))
            nod(P, "head", 6); look(P, Vector((0, BENCH.y, 1.8)), 0.4)
        elif move == "dock":
            nod(X, "head", 6 + 4 * math.sin(sec * 0.4))
            hand_to(X, "R", Vector((DOCK.x + 0.3, DOCK.y - 0.95, 1.12)), curl=55); hand_to(X, "L", Vector((DOCK.x - 0.1, DOCK.y - 0.95, 1.12)), curl=55)
        elif move == "defence":
            stand(D, (1.9, 3.6, 0), math.radians(180 + 60))
            k = ease(min(1.0, max(0.0, (sec - 0.6) / 1.5)))
            rest = D.bone_head("spine02") + fwd(D) * 0.15 + Vector((0, 0, -0.2))
            toward = (Vector((1.25, 4.2, 1.1)) - D.bone_head("spine03")); toward.z = 0; toward.normalize()
            gesture = D.bone_head("spine03") + toward * 0.38 + Vector((0, 0, -0.18))     # an open hand at waist height, toward the photo
            hp = rest.lerp(gesture, k)
            hand_to(D, "R", hp, hand_dir=toward + Vector((0, 0, -0.3)), curl=45)          # holding a page, not an empty hand
            if "def_doc" not in c:
                import paper_tex
                from pbkit import image_plane
                c["def_doc"] = image_plane("DefencePage", paper_tex.make_all()["pages"][3], (0, 0, 0), (0.21, 0.28), (0, 0, 0), rough=0.8)
            bpy.context.view_layer.update()
            tipw = D.arm.matrix_world @ D.arm.pose.bones["finger3-1.R"].head
            ang = math.atan2(toward.y, toward.x)
            c["def_doc"].location = tipw + toward * 0.02 + Vector((0, 0, -0.13))
            camp = Vector((-1.05, 0.35, 1.55))                                            # the defence shot camera (it barely moves)
            nrm = (camp - c["def_doc"].location); nrm.z *= 0.3                             # the page faces the lens, not edge-on
            c["def_doc"].rotation_mode = 'QUATERNION'
            c["def_doc"].rotation_quaternion = nrm.normalized().to_track_quat('Z', 'Y')
            look(D, Vector((0, BENCH.y, 1.8)), 0.7)
        elif move in ("verdict", "led_out"):
            for h in (P, D) + tuple(c["public"]):
                stand(h, (h.arm.location.x, h.arm.location.y, 0), math.pi)
            stand(J, (0, BENCH.y + 0.7, 0.4), 0.0)
            nod(J, "neck01", 8); nod(J, "head", 18)
            if "verdict_sheet" not in c:
                import paper_tex
                c["verdict_sheet"] = image_plane("VerdictSheet", paper_tex.make_all()["pages"][0], (0, 0, 0), (0.21, 0.297), (0, 0, 0), rough=0.8)
            hold_flat(J, c["verdict_sheet"], dist=0.3, drop=0.02, tilt_deg=60, spread=0.1, wobble=0.004 * math.sin(sec))
            if move == "led_out":
                c["sidedoor"].rotation_euler = (0, 0, math.radians(-80))
                p = Vector((DOCK.x + 0.1, DOCK.y + 0.3, 0)).lerp(Vector((5.6, DOCK.y + 0.5, 0)), min(1.0, sec / 5.5))
                walk_at(X, sec * 0.8, p, math.radians(-90), stride=16, swing=4); nod(X, "head", 14)
                walk_at(g1, sec * 0.8 + 0.5, p + Vector((0.6, 0.5, 0)), math.radians(-90), stride=16, swing=8)
                walk_at(g0, sec * 0.8, p + Vector((-0.7, -0.2, 0)), math.radians(-90), stride=16, swing=8)
    bpy.context.view_layer.update()


def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


def _anim(move):
    return lambda c, t: animate(c, t * DUR[move], move)


MOVES = {
    "doors": dict(kind="anim", dof=4.0, far=30.0, anim=_anim("doors"), cam=_push((-1.3, -3.5, 1.6), (-1.1, -2.6, 1.58), (1.8, 5.5, 1.4), (2.0, 5.5, 1.4), 30),
                  focus=lambda c, t: Vector((1.9, 5.5, 1.4)), title=("CHAPTER 3", "THE POISON WITHOUT A NAME", 12, 120)),
    "prosecutor": dict(kind="anim", dof=4.0, far=30.0, anim=_anim("prosecutor"), cam=_push((-4.3, -1.0, 1.6), (-4.0, -0.6, 1.58), (-1.2, 4.5, 1.4), (-1.0, 4.6, 1.4), 30),
                       focus=lambda c, t: Vector((-2.4, 1.75, 1.4))),
    "dock": dict(kind="anim", dof=4.0, far=30.0, anim=_anim("dock"), cam=_push((DOCK.x + 0.6, DOCK.y + 2.6, 1.7), (DOCK.x + 0.4, DOCK.y + 2.2, 1.65), (0.0, 3.0, 1.4), (-0.3, 3.0, 1.4), 30),
                 focus=lambda c, t: DOCK + Vector((0.1, 0.3, 1.5))),
    "defence": dict(kind="anim", dof=4.0, far=30.0, anim=_anim("defence"), cam=_push((-1.2, 0.2, 1.55), (-0.9, 0.5, 1.55), (1.3, 4.1, 1.3), (1.4, 4.1, 1.3), 30),
                    focus=lambda c, t: Vector((1.4, 4.0, 1.3))),
    "verdict": dict(kind="anim", dof=5.6, far=30.0, anim=_anim("verdict"), cam=_push((0.3, -4.0, 1.75), (0.2, -3.0, 1.75), (0.0, BENCH.y, 1.75), (0.0, BENCH.y, 1.8), 36),
                    focus=lambda c, t: Vector((0, BENCH.y + 0.7, 1.9))),
    "led_out": dict(kind="anim", dof=4.0, far=30.0, anim=_anim("led_out"), cam=_push((0.4, -3.6, 1.75), (0.9, -3.3, 1.75), (5.0, 3.0, 1.3), (5.5, 3.0, 1.3), 30),
                    focus=lambda c, t: Vector((5.2, 2.8, 1.4))),
    "volumes": dict(kind="anim", dof=3.2, far=20.0, anim=_anim("volumes"), cam=_push((3.8, -2.9, 1.6), (3.6, -2.6, 1.58), (2.4, -1.0, 1.0), (2.45, -1.0, 1.0), 32),
                    focus=lambda c, t: Vector((2.45, -1.0, 1.1))),
    "archive_dark": dict(kind="anim", dof=5.6, far=20.0, anim=_anim("archive_dark"), cam=_push((1.3, -5.5, 1.7), (1.2, -5.0, 1.68), (-1.2, 3.0, 1.2), (-1.25, 3.0, 1.2), 26),
                         focus=lambda c, t: Vector((-0.6, 0.0, 1.2))),
}


_build_set = build


def build(variant=None):
    c = _build_set(variant)
    from pbkit import finish_scene
    import pblook
    pblook.apply("sc_court", variant)                 # the house cinematic light (HOUSE_LOOK=plain for the old)
    finish_scene()
    return c
