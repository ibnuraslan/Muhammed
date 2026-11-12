"""İkitelli, western Istanbul, December 1998: a muddy street of low plastered houses, and the family yard beside the
house, open to the street. Overcast winter light (dusk for the last intro shot).

Intro moves:
  truck_drive   (1A) the truck rolls down the street toward us, two grey containers in its bed
  truck_rope    (1B) low track along the parked bed as a brother pulls a rope tight over the containers
  torch         (2A) a cutting torch bites into a container shell, sparks spray across the frozen mud
  peel          (2B) wide: the excavator bucket peels a shell back while two men step clear
  steady        (3A) a worker stops, steadies himself on the truck's side, head bowed
  relatives     (3B) two relatives at the street edge; one turns away, a tea glass steams untouched on the wall
  bury          (4A) a man shovels earth over the dull lead block in a shallow pit
  dusk          (4B) slow push across the empty dusk yard to the scrap pile, laundry stirring, a neighbour passing
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Euler
from kit import *
from rs_kit import *
from human import reset_pose, pose_walk, reach, fingers_curl, aim_bone, pose_sit
from rs_env import sky, periphery, puddles, smoke
from durs import dur

EXPOSURE = 0.0
BOUNCES = 6

YARD = Vector((0, 10, 0))             # centre of the family yard
C1 = Vector((-1.6, 9.0, 0))           # container positions in the yard
C2 = Vector((1.4, 9.6, 0))


def curved_panel(name, r, a0, a1, h, mat, z0=0.0, thick=0.02, seg=16):
    """A partial cylindrical shell (outer casing of a container), axis = Z, from angle a0 to a1."""
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rows = []
    for rr in (r, r - thick):
        ring = []
        for k in range(seg + 1):
            a = a0 + (a1 - a0) * k / seg
            ring.append((bm.verts.new((rr * math.cos(a), rr * math.sin(a), z0)), bm.verts.new((rr * math.cos(a), rr * math.sin(a), z0 + h))))
        rows.append(ring)
    o_, i_ = rows
    for k in range(seg):
        bm.faces.new((o_[k][0], o_[k + 1][0], o_[k + 1][1], o_[k][1]))
        bm.faces.new((i_[k][1], i_[k + 1][1], i_[k + 1][0], i_[k][0]))
        bm.faces.new((o_[k][1], o_[k + 1][1], i_[k + 1][1], i_[k][1]))
        bm.faces.new((i_[k][0], i_[k + 1][0], o_[k + 1][0], o_[k][0]))
    for k in (0, seg):
        bm.faces.new((o_[k][0], o_[k][1], i_[k][1], i_[k][0]))
    bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.data.materials.append(mat)
    return o


def electricity_pole(loc, mat):
    cyl("Pole", (loc[0], loc[1], 4.5), 0.13, 9.0, mat, verts=12)
    box("CrossArm", (loc[0], loc[1], 8.6), (0.12, 1.6, 0.12), mat)


def wire(a, b, sag=0.6, mat=None):
    cu = bpy.data.curves.new("Wire", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.008
    sp = cu.splines.new('POLY'); n = 12; sp.points.add(n - 1)
    a = Vector(a); b = Vector(b)
    for k in range(n):
        t = k / (n - 1); p = a.lerp(b, t); p.z -= sag * 4 * t * (1 - t)
        sp.points[k].co = (*p, 1)
    o = bpy.data.objects.new("Wire", cu); bpy.context.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    return o


def tulip_glass(loc, tea=True):
    """Turkish tea glass on a saucer (lathe of a few rings)."""
    g = glass("TeaGlass", (0.95, 0.95, 0.93), 0.02)
    tea_m = pbr("Tea", (0.35, 0.08, 0.02), 0.05, 0.0, **{'Transmission Weight': 0.6})
    sau = cyl("Saucer", (loc[0], loc[1], loc[2] + 0.005), 0.055, 0.01, pbr("Saucer", (0.8, 0.78, 0.74), 0.3), verts=24)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.022, radius2=0.03, depth=0.09, location=(loc[0], loc[1], loc[2] + 0.055))
    gl = bpy.context.active_object; gl.name = "Glass"; gl.data.materials.append(g)
    tv = cyl("TeaBody", (loc[0], loc[1], loc[2] + 0.045), 0.022, 0.065, tea_m, verts=24)
    return sau


def steam(name, loc, n=5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); v = N.new("ShaderNodeVolumePrincipled"); v.inputs['Density'].default_value = 3.0
    v.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1); L.new(v.outputs[0], out.inputs['Volume'])
    puffs = []
    for k in range(n):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.018, location=loc)
        o = bpy.context.active_object; o.name = f"{name}{k}"; o.data.materials.append(m); o.visible_shadow = False
        puffs.append(o)
    return puffs


def pose_steam(puffs, base, sec):
    for k, o in enumerate(puffs):
        a = (sec * 0.35 + k / len(puffs)) % 1.0
        o.location = Vector(base) + Vector((0.012 * math.sin(sec * 1.7 + k * 2), 0.01 * math.cos(sec * 1.3 + k), 0.02 + a * 0.16))
        s = 0.6 + a * 1.8; o.scale = (s, s, s * 1.4)


def laundry(origin, n=6, rng=None):
    """Washing line between a post and the house: a few garments that sway (rotation about the line)."""
    rng = rng or np.random.default_rng(4)
    cols = [(0.55, 0.12, 0.1), (0.75, 0.75, 0.72), (0.15, 0.22, 0.4), (0.6, 0.5, 0.3), (0.3, 0.35, 0.3), (0.8, 0.8, 0.8)]
    items = []
    for k in range(n):
        p = Vector(origin) + Vector((k * 0.55, 0, 0))
        e = bpy.data.objects.new("Peg", None); bpy.context.collection.objects.link(e); e.location = p
        w_ = rng.uniform(0.35, 0.5); h_ = rng.uniform(0.4, 0.7)
        cl = box("Cloth", (0, 0, 0), (w_, 0.01, h_), fabric(f"Cloth{k}", cols[k % len(cols)], 0.9, 0.3, 300))
        cl.parent = e; cl.location = (0, 0, -h_ / 2)
        items.append(e)
    return items



LOT = Vector((0.0, -10.0, 0))          # the open lot across the street (Dec 10)
FAM = Vector((11.5, 10.5, 0))          # family house centre (hollow; kitchen on the yard side)
KITCHEN_WIN = Vector((7.25, 11.0, 1.55))
SIGNS = ["BAKKAL", "BERBER", "TERZİ", "KASAP", "NALBUR", "ELEKTRİKÇİ", "KAHVEHANE", "FIRIN"]


def snowfall_material(name, rate=1.0, dense=0.985):
    """Falling flakes/streaks drawn on transparent planes (like the reference rain) - white dots for snow."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (90 * rate, 90 * rate if rate > 1 else 40, 1)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '2D'
    L.new(mp.outputs[0], wn.inputs['Vector'])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = dense; L.new(wn.outputs['Value'], gt.inputs[0])
    fade = N.new("ShaderNodeValue"); fade.name = "Fade"
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; L.new(gt.outputs[0], sc.inputs[0]); L.new(fade.outputs[0], sc.inputs[1])
    tr = N.new("ShaderNodeBsdfTransparent"); gl = N.new("ShaderNodeEmission"); gl.inputs['Color'].default_value = (0.85, 0.88, 0.92, 1); gl.inputs['Strength'].default_value = 0.5
    mx = N.new("ShaderNodeMixShader"); L.new(sc.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    return m, fade


def precip(c, kind, ys, x0=0.0, width=40.0, fade_in=None):
    """Rain (streaks) or snow (dots) curtains facing the camera axis (-Y); scrolled per frame by precip_fall()."""
    m, fade = snowfall_material("Rain" if kind == "rain" else "Snow", rate=1.0 if kind == "snow" else 1.0, dense=0.94 if kind == "rain" else 0.996)
    if kind == "rain":
        mp = [n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeMapping"][0]; mp.inputs['Scale'].default_value = (30 * 45, 8 * 3.5, 1)
    d = fade.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
    d.expression = f"(0.35 if '{kind}' == 'rain' else 0.9) * min(1, max(0, (frame - {fade_in or -100}) / 30))"
    curt = []
    for k, y in enumerate(ys):
        for j in range(2):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(x0, y, 4 + j * 8), rotation=(math.radians(90), 0, 0))
            o = bpy.context.active_object; o.name = kind.title(); o.scale = (width, 8, 1); o.data.materials.append(m)
            o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False
            curt.append((o, y, j))
    c["precip"] = (kind, curt, x0)


def precip_fall(c, sec):
    if "precip" not in c:
        return
    kind, curt, x0 = c["precip"]
    v = 8.0 if kind == "rain" else 0.9
    for o, y, j in curt:
        o.location = (x0 + (0.0 if kind == "rain" else 0.25 * math.sin(sec * 0.6 + y)), y, 4 + j * 8 - (sec * v) % 8.0)


def shop_sign(word, loc, rot_z, w=2.6, col=(0.55, 0.12, 0.08)):
    """Painted shop signboard (no brands): coloured board with white lettering, mounted above a door."""
    bd = box("SignBoard", (0, 0, 0), (w, 0.04, 0.55), noisy("SignPaint" + word, col, 0.6, dirt=0.5, scale=3), bevel=0.01)
    tx = text_obj("SignTxt", word, (0, -0.025, -0.12), 0.32, pbr("SignLetter", (0.85, 0.83, 0.78), 0.5),
                  font_path="/usr/share/fonts/opentype/inter/Inter-Bold.otf", extrude=0.004)
    tx.parent = bd
    bd.location = loc; bd.rotation_euler = (0, 0, rot_z)
    return bd


def hollow_house(name, loc, w, d, h, plaster, roof, win_at, rng):
    """The family house as a real shell: four walls, ceiling, a window cut into the yard-side (west) wall,
    a kitchen inside (table, chair, stove, shelf, a hanging bulb), a warm lamp that lights the window."""
    x, y, _ = loc; t = 0.25
    walls = [box(name + "WallN", (x, y + d / 2 - t / 2, h / 2), (w, t, h), plaster), box(name + "WallS", (x, y - d / 2 + t / 2, h / 2), (w, t, h), plaster),
             box(name + "WallE", (x + w / 2 - t / 2, y, h / 2), (t, d, h), plaster)]
    west = box(name + "WallW", (x - w / 2 + t / 2, y, h / 2), (t, d, h), plaster)
    cut = box("WinCut", (win_at.x, win_at.y, win_at.z), (1.0, 1.0, 1.15))
    bm_ = west.modifiers.new("Win", 'BOOLEAN'); bm_.object = cut; bm_.operation = 'DIFFERENCE'
    bpy.context.view_layer.objects.active = west; bpy.ops.object.modifier_apply(modifier="Win"); bpy.data.objects.remove(cut)
    frame = pbr("WinFrameWood", (0.42, 0.37, 0.3), 0.7)
    for dz in (-0.58, 0.58):
        box("WinFrameH", (win_at.x - 0.02, win_at.y, win_at.z + dz), (0.3, 1.0, 0.06), frame)
    for dy in (-0.5, 0.0, 0.5):
        box("WinFrameV", (win_at.x - 0.02, win_at.y + dy, win_at.z), (0.3, 0.05, 1.15), frame)
    box("WinGlass", (win_at.x - 0.05, win_at.y, win_at.z), (0.01, 0.98, 1.12), glass("KitchenGlass", (0.9, 0.92, 0.9), 0.05))
    box("Sill", (win_at.x - 0.2, win_at.y, win_at.z - 0.62), (0.3, 1.2, 0.05), plaster)
    box(name + "Ceiling", (x, y, h - 0.05), (w, d, 0.1), plaster)
    box(name + "Floor", (x, y, 0.02), (w, d, 0.04), ph_mat("worn_brick_floor", 0.6, (0.35, 0.25, 0.2), name="KitchenFloor"))
    inner = noisy("KitchenWall", (0.62, 0.58, 0.48), 0.85, dirt=0.4, scale=2)
    box("InnerW", (x - w / 2 + t + 0.01, y, h / 2), (0.01, d - 2 * t, h - 0.1), inner).hide_render = True
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.0, radius2=0.25, depth=1.0, location=(x, y, h + 0.65), rotation=(0, 0, math.radians(45)))
    r = bpy.context.active_object; r.scale = (w * 0.76, d * 0.76, 1.3); r.data.materials.append(roof)
    box(name + "Chimney", (x + w * 0.25, y + d * 0.15, h + 1.3), (0.45, 0.45, 1.4), plaster)
    box(name + "Door", (x - w / 2 + 2.6, y - d / 2 - 0.01, 1.05), (0.95, 0.04, 2.1), pbr("DoorWood", (0.22, 0.14, 0.08), 0.7))
    # kitchen: table, chairs, stove, shelf with jars, a curtain, a hanging bulb
    k0 = Vector((win_at.x + 2.0, win_at.y, 0))
    wood_m = wood("KTable", (0.12, 0.07, 0.04), (0.3, 0.18, 0.1), rough=0.6, coat=0.1)
    box("KTableTop", k0 + Vector((0, 0, 0.74)), (0.9, 1.3, 0.04), wood_m)
    for dx in (-0.4, 0.4):
        for dy in (-0.6, 0.6):
            box("KTableLeg", k0 + Vector((dx, dy, 0.37)), (0.04, 0.04, 0.74), wood_m)
    box("Oilcloth", k0 + Vector((0, 0, 0.762)), (0.95, 1.35, 0.004), noisy("Oilcloth", (0.6, 0.55, 0.45), 0.4, dirt=0.4, scale=8))
    ph_model("SchoolChair_01", loc=(k0.x + 0.75, k0.y + 0.1, 0), rot_z=math.radians(90))
    stove = join([box("Stove", (k0.x + 1.7, k0.y + 1.4, 0.45), (0.5, 0.5, 0.9), painted_steel("Stove", (0.2, 0.2, 0.2), 0.5, 0.5)),
                  cyl("StovePipe", (k0.x + 1.7, k0.y + 1.4, 1.9), 0.06, 2.0, pbr("StovePipe", (0.08, 0.08, 0.08), 0.5, 0.6), verts=12)], "Stove")
    box("Shelf", (k0.x + 1.9, k0.y - 1.0, 1.6), (0.25, 1.2, 0.03), wood_m)
    for j in range(5):
        cyl("Jar", (k0.x + 1.9, k0.y - 1.45 + j * 0.22, 1.7), 0.05, 0.16, glass("Jar", (0.8, 0.75, 0.55), 0.05), verts=12)
    glass_t = tulip_glass((k0.x - 0.15, k0.y + 0.25, 0.765))
    cord = cyl("BulbCord", (k0.x, k0.y, h - 0.5), 0.004, 0.9, pbr("Cord", (0.02, 0.02, 0.02), 0.6), verts=6)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.045, location=(k0.x, k0.y, h - 1.0))
    bulb = bpy.context.active_object; bulb.data.materials.append(pbr("Bulb", (1, 1, 1), 0.2, 0.0, **{'Emission Color': (1.0, 0.75, 0.45, 1), 'Emission Strength': 25.0}))
    l = bpy.data.lights.new("KitchenBulb", 'POINT'); l.energy = 450; l.color = (1.0, 0.72, 0.42); l.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("KitchenBulb", l); bpy.context.collection.objects.link(lo); lo.location = (k0.x, k0.y, h - 1.08)
    curtain = box("Curtain", (win_at.x + 0.12, win_at.y + 0.3, win_at.z + 0.1), (0.02, 0.45, 1.25), fabric("CurtainF", (0.6, 0.45, 0.3), 0.9, 0.4, 600))
    return dict(table=k0, bulb=lo, window=win_at)


def build(variant=None):
    c = {}
    v = variant or "yard"
    rng = np.random.default_rng(12)
    day = {"drive": "overcast", "lot": "overcast", "rain": "rain", "yard": "afternoon", "yard_dusk": "dusk", "yard_morning": "morning",
           "late": "afternoon", "night": "dusk", "dusk": "dusk", "scrapload": "overcast"}[v]
    w_, sun_ = sky(day)
    if v == "late":
        sun_.rotation_euler = (math.radians(90 - 5), 0, math.radians(250)); sun_.data.energy = 2.6; sun_.data.color = (1.0, 0.78, 0.55)
    if v == "night":
        bg = w_.node_tree.nodes["Background"]; bg.inputs['Strength'].default_value = 0.25; sun_.data.energy = 0.0
        bpy.context.scene.view_settings.exposure = 1.2
    if v in ("dusk", "yard_dusk"):
        bpy.context.scene.view_settings.exposure = 1.4
    mud = ph_mat("muddy_tracks", 0.25, (0.25, 0.21, 0.17), name="Mud")
    road = ph_mat("road_damaged", 0.2, (0.18, 0.18, 0.18), name="Road")
    box("Ground", (0, 0, -0.05), (240, 200, 0.1), mud)
    box("Street", (0, 0, -0.035), (240, 6.5, 0.08), road)
    puddles(rng, ((-40, -3.0), (40, 3.0)), 18, size=(0.5, 1.6), z=0.01)
    puddles(rng, ((-9, -15), (9, -5)), 6, size=(0.5, 1.2))
    # houses: plaster in faded ochres, greys and pinks; clay roofs; shop signs; one unfinished upper storey
    plasters = [ph_mat("plastered_wall_04", 0.4, (0.6, 0.55, 0.47), name="PlasterA", tint=(0.95, 0.86, 0.72)),
                ph_mat("plastered_wall_04", 0.4, (0.55, 0.55, 0.52), name="PlasterB", tint=(0.78, 0.8, 0.8)),
                ph_mat("plastered_wall_04", 0.4, (0.62, 0.5, 0.45), name="PlasterC", tint=(0.95, 0.78, 0.7)),
                ph_mat("plastered_wall_04", 0.4, (0.62, 0.5, 0.45), name="PlasterD", tint=(0.8, 0.86, 0.78))]
    brick = ph_mat("red_brick", 0.6, (0.4, 0.2, 0.15), name="Brick")
    roof = ph_mat("clay_roof_tiles_02", 0.5, (0.45, 0.2, 0.12), name="RoofTiles")
    lit = 1.2 if v in ("dusk", "night", "yard_dusk") else 0.0
    c["fam"] = hollow_house("FamilyHouse", FAM, 8.5, 8.0, 2.9, plasters[0], roof, KITCHEN_WIN, rng)
    house("Neighbour", (-12.5, 10.0, 0), 9.0, 8.5, 2, plasters[1], roof)
    sign_i = 0
    for k, x in enumerate((-36, -24, 24, 35, 47, -48)):
        f_ = int(rng.integers(1, 3)); hx = x + rng.uniform(-1, 1); hy = 10.5 + rng.uniform(-1, 2)
        house(f"North{k}", (hx, hy, 0), rng.uniform(7, 10), 8, f_, plasters[k % 4], roof)
        if k % 2 == 0:
            shop_sign(SIGNS[sign_i % len(SIGNS)], (hx, hy - 4.08, 2.55), 0.0, col=[(0.55, 0.12, 0.08), (0.1, 0.25, 0.45), (0.15, 0.35, 0.2)][sign_i % 3]); sign_i += 1
    for k, x in enumerate((-40, -28, -16, 20, 32, 44)):
        f_ = int(rng.integers(1, 3)); hx = x + rng.uniform(-1, 1); hy = -10.5 - rng.uniform(0, 2)
        house(f"South{k}", (hx, hy, 0), rng.uniform(7, 10.5), 8, f_, plasters[(k + 1) % 4], roof, rot_z=math.pi)
        if k % 2 == 1:
            shop_sign(SIGNS[sign_i % len(SIGNS)], (hx, hy + 4.08, 2.55), math.pi, col=[(0.55, 0.12, 0.08), (0.1, 0.25, 0.45), (0.15, 0.35, 0.2)][sign_i % 3]); sign_i += 1
    box("Unfinished", (-16, -11.0, 2.9 + 1.4), (7, 7, 2.8), brick)
    rebar = pbr("Rebar", (0.15, 0.08, 0.05), 0.7, 0.6)
    for k in range(10):
        cyl("Rebar", (-19.2 + k * 0.7, -7.6, 6.6), 0.012, 1.0, rebar, verts=6)
    # the open lot across the street: rough ground, weeds, rubble, a low broken wall
    for k in range(40):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(rng.uniform(-9, 9), rng.uniform(-15, -6), 0.0))
        o = bpy.context.active_object; o.scale = (rng.uniform(0.1, 0.35), rng.uniform(0.1, 0.3), rng.uniform(0.05, 0.12)); o.data.materials.append(plasters[1])
    wall("LotWall", (-9.5, -15.5), (-3.0, -15.5), 0.8, 0.2, brick)
    # Istanbul periphery: hills of apartment blocks, minarets, a smoking factory stack
    periphery(rng, center=(0, 0), r_min=190, r_max=560, n_blocks=320, hill_h=34, minarets=2, smokes=1)
    for (hx, hy) in ((-36, 13), (24, 13), (-40, -12), (32, -12), (FAM.x + 2.1, FAM.y + 1.2)):
        smoke((hx + 2, hy, 6.5 if (hx, hy) != (FAM.x + 2.1, FAM.y + 1.2) else 4.6), height=8, radius=0.35, density=0.5)
    haze((0, 150, 30), (1400, 700, 80), density=0.0024 if day != "rain" else 0.004, color=(0.85, 0.88, 0.92) if day not in ("dusk",) else (0.5, 0.55, 0.72), anis=0.3)
    haze((0, 5, 6), (90, 60, 14), density=0.0008, color=(0.86, 0.88, 0.92), anis=0.3)
    # electricity poles and sagging wires along the street
    pole_m = pbr("PoleWood", (0.22, 0.18, 0.14), 0.85)
    wire_m = pbr("WireM", (0.02, 0.02, 0.02), 0.6)
    poles = [(-30, 4.0), (-12, 4.0), (6, 4.0), (24, 4.0), (42, 4.0)]
    for p in poles:
        electricity_pole(p, pole_m)
    for a, b in zip(poles[:-1], poles[1:]):
        for dy in (-0.6, 0.6):
            wire((a[0], a[1] + dy, 8.7), (b[0], b[1] + dy, 8.7), 0.7, wire_m)
    wire((6, 4.0, 8.4), (8.5, 6.6, 2.7), 0.25, wire_m)
    if v in ("dusk", "night", "yard_dusk"):
        for k, x in enumerate((-12, 6, 24)):
            l = bpy.data.lights.new("StreetLamp", 'SPOT'); l.energy = 900; l.color = (1.0, 0.65, 0.35); l.spot_size = math.radians(110); l.spot_blend = 0.6
            o = bpy.data.objects.new("StreetLamp", l); bpy.context.collection.objects.link(o); o.location = (x + 0.9, 3.6, 6.3)
            box("LampArm", (x + 0.5, 3.8, 6.55), (0.9, 0.06, 0.06), pole_m)
            bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.22, depth=0.18, location=(x + 0.95, 3.6, 6.45))
            bpy.context.active_object.data.materials.append(pbr("LampShade", (0.2, 0.2, 0.2), 0.5, 0.6))
            cyl("LampBulb", (x + 0.95, 3.6, 6.36), 0.06, 0.04, pbr("LampBulbM", (1, 1, 1), 0.2, 0.0, **{'Emission Color': (1.0, 0.7, 0.4, 1), 'Emission Strength': 30.0}), verts=12)
    for (hx, hy, ang) in ((-12.5, 5.7, 0), (24.0, 6.5, 0), (-28.0, -6.5, math.pi)):   # a couple of neighbours' lit windows (real lamps behind glass)
        if lit:
            l = bpy.data.lights.new("NeighbourLamp", 'POINT'); l.energy = 60; l.color = (1.0, 0.72, 0.45)
            o = bpy.data.objects.new("NeighbourLamp", l); bpy.context.collection.objects.link(o); o.location = (hx + 1.3, hy + (0.7 if ang == 0 else -0.7), 1.6)
    # yard frontage: breeze-block wall with a wide open gap; the yard is open to the street
    blocks = ph_mat("concrete_block_wall", 0.8, (0.45, 0.45, 0.43), name="Blocks")
    wall("YardWallW", (-7.2, 4.3), (-3.2, 4.3), 0.95, 0.2, blocks)
    wall("YardWallE", (4.2, 4.3), (7.2, 4.3), 0.95, 0.2, blocks)
    wall("YardWallBack", (-7.2, 16.0), (7.2, 16.0), 1.8, 0.2, blocks)
    # yard clutter: scrap pile (instanced kit), tyres, a barrel, a plastic chair, crate slats
    kit_ = scrap_kit(rng)
    hf = lambda x, y: max(0.0, 1.2 * (1 - math.hypot((x - 3.8) / 2.6, (y - 13.9) / 1.8)))
    L_, R_, S_, I_ = scrap_points(kit_, hf, 3.8, 13.9, 2.4, 140 if v != "scrapload" else 220, rng, embed=0.1, scl=(0.4, 0.8), exclude=("CarShell", "Fridge", "WashingMachine"))
    gn_instances("YardScrap", [p for p, w in kit_], L_, R_, S_, I_)
    for k, (aid, loc, rz) in enumerate((("old_tyre", (5.6, 14.6, 0), 0.4), ("Barrel_01", (-6.2, 15.0, 0), 0.0),
                                       ("plastic_monobloc_chair_01", (6.0, 7.0, 0), 2.6), ("metal_jerrycan", (-5.6, 6.2, 0), 0.7))):
        ph_model(aid, loc=loc, rot_z=rz)
    slat_m = noisy("Slat", (0.38, 0.27, 0.16), 0.85, dirt=0.6, scale=6)
    for k in range(9):
        box("Slat", (rng.uniform(-3.5, 3.5), rng.uniform(6.5, 8.0), 0.012), (rng.uniform(0.9, 1.2), 0.15, 0.022), slat_m, rot=(0, 0, rng.uniform(0, 3.1)))
    cyl("LinePost", (6.6, 15.2, 1.1), 0.04, 2.2, pole_m, verts=8)
    wire((6.6, 15.2, 2.15), (7.3, 12.6, 2.2), 0.05, wire_m)
    c["laundry"] = laundry((6.65, 15.0, 2.12), 4)
    for k, e in enumerate(c["laundry"]):
        e.location = Vector((6.65, 15.1, 2.14)).lerp(Vector((7.25, 12.7, 2.17)), (k + 0.5) / 4); e.rotation_euler = (0, 0, math.radians(-75))
    # containers (yard by default; variants move them to the truck bed or the lot)
    cont1, k1 = container("Cont1"); cont1.location = C1; cont1.rotation_euler = (0, 0, -math.pi / 2)
    cont2, k2 = container("Cont2"); cont2.location = C2; cont2.rotation_euler = (0, 0, -0.2)
    c.update(cont1=cont1, cont2=cont2, k1=k1, k2=k2)
    for tr in (k1["trefoil"], k2["trefoil"]):
        tr.hide_render = True                  # the mark is only noticed later (Ch2)
    shell = curved_panel("Shell", 0.41, math.radians(-150), math.radians(-30), 0.8, k1["grey"], z0=0.0)
    hinge = bpy.data.objects.new("ShellHinge", None); bpy.context.collection.objects.link(hinge)
    hinge.parent = cont1; hinge.location = (0, 0, 0.15); shell.parent = hinge; shell.location = (0, 0, 0)
    c["hinge"] = hinge
    shell2 = curved_panel("Shell2", 0.41, math.radians(-150), math.radians(-30), 0.8, k2["grey"], z0=0.0)
    hinge2 = bpy.data.objects.new("ShellHinge2", None); bpy.context.collection.objects.link(hinge2)
    hinge2.parent = cont2; hinge2.location = (0, 0, 0.15); shell2.parent = hinge2; c["hinge2"] = hinge2
    lead_core = cyl("LeadCore", (0, 0, 0.55), 0.33, 0.72, k2["lead"], verts=32); lead_core.parent = cont2; lead_core.location = (0, 0, 0.55); lead_core.hide_render = True
    c["lead_core"] = lead_core
    cr1 = crate("Crate1"); c["crate"] = cr1; cr1.location = (0, -150, 0)
    plug = cyl("Plug", (0, 0, 0), 0.16, 0.45, k1["grey"], verts=24, rot=(0, math.radians(90), 0)); c["plug"] = plug; plug.location = (0, -150, 0)
    chain_m = pbr("ChainM", (0.18, 0.18, 0.18), 0.5, 0.8)
    c["chain"] = cyl("Chain", (0, 0, 0), 0.012, 1.0, chain_m, verts=6); c["chain"].location = (0, -150, 0)
    # the truck (placeholder until the shared vehicle kit lands)
    tk, wheels, bed_z, (bx0, bx1) = truck("Truck", (0.12, 0.2, 0.3))
    c.update(truck=tk, wheels=wheels, bed_z=bed_z)
    tc1, _ = container("TruckCont1", trefoil=False); tc1.parent = tk; tc1.location = (-0.9, 0.35, bed_z)
    tc2, _ = container("TruckCont2", trefoil=False); tc2.parent = tk; tc2.location = (0.4, -0.35, bed_z); tc2.rotation_euler = (0, 0, 0.4)
    c.update(tc1=tc1, tc2=tc2)
    load = []
    for k in range(18):
        p, w = kit_[[i for i, (pp, ww) in enumerate(kit_) if any(w_ in pp.name for w_ in ("Plate", "Pipe", "Bonnet", "IBeam", "Bar", "Angle"))][k % 12]]
        o = instance(p, (rng.uniform(-1.8, 1.8), rng.uniform(-0.8, 0.8), bed_z + 0.1 + rng.uniform(0, 0.4)), rot=(rng.normal(0, 0.3), rng.normal(0, 0.3), rng.uniform(0, 6.28)), scale=(0.6,) * 3)
        o.parent = tk; o.hide_render = v != "scrapload"; load.append(o)
    c["load"] = load
    rope_m = pbr("Rope", (0.45, 0.4, 0.3), 0.9)
    cu = bpy.data.curves.new("Rope", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.012
    sp = cu.splines.new('POLY'); pts = [(-0.9, 1.05, bed_z + 0.42), (-0.9, 0.75, bed_z + 1.08), (-0.9, -0.05, bed_z + 1.1), (-0.9, -1.05, bed_z + 0.45), (-0.9, -1.3, bed_z + 0.2)]
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    c["rope"] = bpy.data.objects.new("Rope", cu); bpy.context.collection.objects.link(c["rope"]); cu.materials.append(rope_m)
    c["rope"].parent = tk; c["rope_spline"] = sp
    # wipers for the rain shot (pivot empties on the cab front)
    c["wipers"] = []
    for sy in (-0.35, 0.35):
        e = bpy.data.objects.new("WiperP", None); bpy.context.collection.objects.link(e); e.parent = tk; e.location = (bx1 + 0.25 + 0.9 + 0.92, sy, 1.55)
        wb = box("WiperBlade", (0, 0, 0), (0.015, 0.02, 0.55), pbr("WiperM", (0.01, 0.01, 0.01), 0.6)); wb.parent = e; wb.location = (0, 0, 0.27)
        c["wipers"].append(e)
    # excavator (rented for the peel)
    ex = excavator("Excavator", (0.7, 0.5, 0.08), tool="bucket")
    ex["base"].location = (-6.6, 9.4, 0); ex["base"].rotation_euler = (0, 0, 0)
    pose_arm(ex, 0.0, math.radians(20), math.radians(80), math.radians(40))
    c["ex"] = ex
    # the pit (burial): a shallow hole in frozen mud, spoil around it, the lead block going in, clods falling
    pit_c = Vector((-3.6, 14.4, 0)); c["pit"] = pit_c
    dirt = ph_mat("brown_mud_02", 1.0, (0.15, 0.11, 0.08), name="PitDirt")
    hole = bpy.data.materials.new("PitHole"); hole.use_nodes = True
    hp = hole.node_tree.nodes["Principled BSDF"]; hp.inputs['Base Color'].default_value = (0.03, 0.025, 0.02, 1); hp.inputs['Roughness'].default_value = 1.0
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=1.0, fill_type='NGON', location=pit_c + Vector((0, 0, 0.004)))
    ho = bpy.context.active_object; ho.scale = (0.75, 0.5, 1); ho.data.materials.append(hole)
    for k in range(18):
        a = k / 18 * 2 * math.pi
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=pit_c + Vector((0.85 * math.cos(a) + rng.uniform(-0.05, 0.05), 0.6 * math.sin(a), -0.02)))
        lump = bpy.context.active_object; lump.scale = (rng.uniform(0.15, 0.3), rng.uniform(0.12, 0.25), rng.uniform(0.05, 0.1)); lump.data.materials.append(dirt)
    c["leadblock"] = box("LeadBlock", pit_c + Vector((0, 0, 0.0)), (0.5, 0.35, 0.16), k1["lead"], bevel=0.02)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=1.0, location=pit_c)
    c["fill"] = bpy.context.active_object; c["fill"].name = "Fill"; c["fill"].scale = (0.7, 0.45, 0.14); c["fill"].data.materials.append(dirt); bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0, location=pit_c + Vector((1.25, 0.25, 0.0)))
    c["mound"] = bpy.context.active_object; c["mound"].scale = (0.6, 0.5, 0.32); c["mound"].data.materials.append(dirt); bpy.ops.object.shade_smooth()
    c["clods"] = []
    for k in range(10):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.035 + 0.02 * rng.random(), location=(0, -150, 0))
        cl = bpy.context.active_object; cl.data.materials.append(dirt); c["clods"].append(cl)
    spade_root, spade_ms = ph_model("rusted_spade_01"); c["spade"] = spade_root
    spade2, _ = ph_model("rusted_spade_01"); c["spade2"] = spade2
    crow, _ = ph_model("crowbar_01"); c["crowbar"] = crow
    # sparks + torch flame light
    c["sparks"] = sparks("Spark", 80)
    c["torch_light"] = flicker_light("TorchLight", (0, 0, -20), energy=140)
    c["flame"] = box("Flame", (0, 0, -30), (0.015, 0.015, 0.06), emissive("Flame", (0.55, 0.7, 1.0), 40))
    c["torch_tool"] = cyl("TorchTool", (0, 0, -30), 0.012, 0.45, pbr("Brass", (0.5, 0.35, 0.12), 0.35, 1.0), verts=8)
    c["sack"] = box("Sack", (0, -150, 0), (0.5, 0.3, 0.7), fabric("SackCloth", (0.45, 0.38, 0.25), 0.95, 0.3, 300), bevel=0.12)
    # people: brothers, relatives, workers, neighbours (unnamed figures; no likeness)
    P = {}
    P["bro1"] = person("Bro1", 1.0, 38, "wool_brown", "short02", moustache=True)
    P["bro2"] = person("Bro2", 1.0, 33, "parka_green", "short04", hat="knit", hat_col=(0.14, 0.15, 0.2))
    P["worker"] = person("Worker", 1.0, 45, "charcoal", "short03", hat="flat", hat_col=(0.24, 0.2, 0.15), moustache=True, weight=0.6)
    P["rel1"] = person("Rel1", 1.0, 62, "wool_grey", "short02", hv=0.7, hat="flat", hat_col=(0.18, 0.18, 0.17), moustache=True)
    P["rel2"] = person("Rel2", 0.0, 50, "woman_coat", "bob02", hv=0.1)
    if v in ("yard", "lot", "yard_morning", "late", "dusk"):
        P["rel3"] = person("Rel3", 1.0, 28, "navy", "short03")
        P["kid1"] = person("Kid1", 1.0, 10, "camel", "short02", height=0.3)
        P["kid2"] = person("Kid2", 0.0, 9, "navy", "bob01", height=0.3)
    c["people"] = P
    for h in P.values():
        place(h, (0, -60, 0), 0)
    # kitchen sitter (the man who reached inside)
    if v == "night":
        precip(c, "snow", (2.0, 5.0, 8.0), x0=0.0, width=30, fade_in=12)
    if v == "rain":
        precip(c, "rain", (-16.0, -12.0, -8.0, -4.0, 0.0), x0=0.0, width=40, fade_in=20)
    c["variant"] = v
    return c


# ============================================================================ helpers per shot
def hide_people(c, keep=()):
    for k, h in c["people"].items():
        if k not in keep:
            h.arm.location = (0, -60, 0)


def walk_to(h, a, b, sec, speed=1.1, stride=1.25):
    a = Vector(a); b = Vector(b); d = (b - a); L_ = d.length
    s = min(L_, max(0.0, speed * sec))
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0)
    moving = 0 < s < L_
    ph_ = (s / stride) % 1.0 if moving else 0.0
    reset_pose(h)
    pose_walk(h, ph_, stride=24 if moving else 0, arm_swing=0)
    arms_relaxed(h, ph_, 14 if moving else 0)
    p = a + d.normalized() * s
    place(h, (p.x, p.y, 0), face_angle(a, b))
    return p


def stand_at(h, loc, look, **kw):
    stand_pose(h, **kw); place(h, loc, face_angle(loc, look))


def ex_rest(c):
    pose_arm(c["ex"], math.radians(-35), math.radians(42), math.radians(115), math.radians(100))


def set_truck(c, x, y, rot_z, roll=0.0):
    c["truck"].location = (x, y, 0); c["truck"].rotation_euler = (0, 0, rot_z)
    for w in c["wheels"]:
        w.rotation_euler = (0, roll / 0.45, 0)


def stage(c, cont="yard", truck_at=None, ex=False, shells=(0, 0), people=()):
    """Common scene state: where the containers are, the truck, excavator, shells open, who is visible."""
    ex_rest(c)
    on_truck = cont == "truck"
    for k in ("tc1", "tc2"):
        c[k].hide_render = not on_truck
    if cont == "yard":
        c["cont1"].location = C1; c["cont2"].location = C2
    elif cont == "lot":
        c["cont1"].location = LOT + Vector((-1.2, 0.5, 0)); c["cont2"].location = LOT + Vector((1.3, -0.4, 0))
    else:
        c["cont1"].location = (0, -80, 0); c["cont2"].location = (2, -80, 0)
    c["hinge"].rotation_euler = (math.radians(shells[0]), 0, 0); c["hinge2"].rotation_euler = (math.radians(shells[1]), 0, 0)
    c["lead_core"].hide_render = shells[1] < 30
    if truck_at:
        set_truck(c, *truck_at)
    else:
        set_truck(c, -40, 40, 0)
    bpy.context.view_layer.update()
    if not ex:
        c["ex"]["base"].location = (-40, 50, 0)
    hide_people(c, people)
    pose_sparks(c["sparks"], (0, 0, -50), 0, on=False)
    c["flame"].location = (0, 0, -30); c["torch_tool"].location = (0, 0, -30); c["torch_light"].location = (0, 0, -20)
    precip_fall(c, 0)


def laundry_sway(c, sec, amp=9):
    for k, e in enumerate(c["laundry"]):
        e.rotation_euler = (math.radians(amp * math.sin(sec * 1.3 + k * 0.9) + 4), 0, math.radians(-75))


def lean_forearm(c, h, sec, stance, rail_pt, look_at):
    """Worker leaning a forearm on the tailboard, head bowed (wider shot; no open hand)."""
    stand_pose(h); place(h, stance, face_angle(stance, look_at))
    sd = forward(h).cross(Vector((0, 0, 1))).normalized()
    h.rot("spine03", sd, -16); h.rot("spine05", sd, -8); h.rot("neck01", sd, -14); h.rot("head", sd, -12)
    br = 0.012 * math.sin(sec * 1.8)
    elbow = Vector(rail_pt) + Vector((0, 0, 0.05 + br))
    reach(h, "R", elbow + forward(h) * 0.22 + Vector((0, 0, 0.02)), Vector((0, 0, -1)), forward(h))
    fingers_curl(h, 75, side=("R",), thumb=40)


def torch_dir(c, sec, h, target, stance):
    torch_man(c, h, sec, target, stance)


def torch_man(c, h, sec, target, stance):
    """A man cutting: torch at `target`, leaning in; bracing hand on the drum."""
    reset_pose(h); stand_pose(h)
    place(h, stance, face_angle(stance, target))
    h.rot("spine03", forward(h).cross(Vector((0, 0, 1))), -18)     # lean in
    fwd = forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    wob = Vector((0.01 * math.sin(sec * 7), 0, 0.008 * math.sin(sec * 5)))
    tip = Vector(target) - fwd * 0.08 + wob
    grip = tip - fwd * 0.38 + Vector((0, 0, 0.12))
    reach(h, "R", grip + side * 0.04, Vector((side.x, side.y, -0.8)), (tip - grip))
    reach(h, "L", grip + (tip - grip) * 0.5 - side * 0.06, Vector((-side.x, -side.y, -0.8)), (tip - grip))
    fingers_curl(h, 60, thumb=30)
    tt = c["torch_tool"]; tt.location = grip.lerp(tip, 0.5)
    tt.rotation_mode = 'QUATERNION'; tt.rotation_quaternion = (tip - grip).to_track_quat('Z', 'Y')
    c["flame"].location = tip; c["flame"].rotation_mode = 'QUATERNION'; c["flame"].rotation_quaternion = (tip - grip).to_track_quat('Z', 'Y')
    c["torch_light"].location = Vector(target) + Vector((0, 0, 0.05)) - fwd * 0.1
    pose_sparks(c["sparks"], target, sec, direction=Vector((side.x, side.y, 0.3)) * 0.4 + Vector((0, 0, -0.6)), spread=0.9)
    attach_cap(h)




# ============================================================================ shots
def C(p0, p1, tgt, lens, tgt1=None):
    def f(c, t):
        e = ease(t)
        tg = Vector(tgt) if tgt1 is None else Vector(tgt).lerp(Vector(tgt1), e)
        return (Vector(p0).lerp(Vector(p1), e), tg, lens)
    return f


def S(name, t):
    return t * dur(name)


# ---- intro
def i1a(c, t):
    sec = S("intro_1a", t); stage(c, "truck", people=("bro2", "rel1"))
    T = dur("intro_1a"); v0 = 7.0
    x = -31 + v0 * sec - 0.25 * v0 * sec * sec / T
    set_truck(c, x, -1.2, 0.0, roll=-(x + 31))
    stand_at(c["people"]["bro2"], (-8.0, -4.2, 0), (x, -1.2), hands_pockets=True)
    walk_to(c["people"]["rel1"], (-20, 4.6, 0), (-6, 4.8, 0), sec, speed=0.9)
    c["focus"] = Vector((x + 2.5, -1.2, 1.4))


def i1b(c, t):
    sec = S("intro_1b", t); stage(c, "truck", truck_at=(1.0, 5.2, 0.0), people=("bro1", "bro2"))
    h = c["people"]["bro1"]; stand_pose(h); place(h, (0.15, 3.45, 0), face_angle((0.15, 3.45), (0.1, 6)))
    pull = math.sin(min(1.0, sec / 2.4) * math.pi / 2)
    M = c["truck"].matrix_world; top = M @ Vector((-0.9, -1.05, c["bed_z"] + 0.45))
    hand = top + Vector((0.0, -0.42, -0.05 - 0.35 * pull))
    c["rope_spline"].points[4].co = (*(M.inverted() @ (hand + Vector((0, 0, -0.25)))), 1)
    reach(h, "R", hand + Vector((0.05, 0, 0)), Vector((0.6, -0.3, -0.6)), Vector((0, 0.4, -1)))
    reach(h, "L", hand + Vector((-0.08, 0, 0.18)), Vector((-0.6, -0.3, -0.6)), Vector((0, 0.4, -1)))
    fingers_curl(h, 70, thumb=40); h.rot("spine03", (1, 0, 0), -8 * pull)
    stand_at(c["people"]["bro2"], (3.6, 3.0, 0), (1.0, 5.2), crossed=True)
    c["focus"] = h.bone_head("spine05")


def i2a(c, t):          # dusk, close and low: torch on the shell, warm glow against blue
    sec = S("intro_2a", t); stage(c, "yard", truck_at=(3.5, 13.5, math.pi), people=("worker",))
    target = c["cont2"].matrix_world @ Vector((-0.39, -0.12, 0.62))
    torch_man(c, c["people"]["worker"], sec, target, (C2.x - 1.05, C2.y - 0.45, 0))
    c["focus"] = target


def i2b(c, t):          # dusk, low close on the bucket hooking the shell, men stepping clear
    sec = S("intro_2b", t); stage(c, "yard", truck_at=(3.5, 13.5, math.pi), ex=True, people=("worker", "bro1"))
    ex = c["ex"]; ex["base"].location = (-6.6, 9.4, 0)
    k = ease(min(1.0, sec / dur("intro_2b")))
    c["hinge"].rotation_euler = (math.radians(8 + 62 * k), 0, 0); bpy.context.view_layer.update()
    edge = c["hinge"].matrix_world @ Vector((0, -0.41, 0.8))
    arm_ik(ex, edge + Vector((-0.35, 0, 0.55)))
    b_ = ex["boom"].rotation_euler.y; s_ = ex["stick"].rotation_euler.y; ex["tool"].rotation_euler = (0, -(b_ + s_) + math.radians(95), 0)
    p0 = C1 + Vector((0.9, -0.6, 0)); p1 = C1 + Vector((1.6, -1.8, 0))
    q = p0.lerp(p1, ease(min(1.0, sec / 1.4)))
    stand_at(c["people"]["worker"], q, C1, crossed=True)
    stand_at(c["people"]["bro1"], C1 + Vector((-0.2, -2.6, 0)), C1, hands_pockets=True)
    c["focus"] = edge


def i3a(c, t):
    sec = S("intro_3a", t); stage(c, "yard", truck_at=(1.5, 12.8, math.pi), shells=(70, 0), people=("worker",))
    M = c["truck"].matrix_world
    rail = M @ Vector((-0.6, 1.07, 1.36)); out = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    st = rail + out * 0.5; st.z = 0
    lean_forearm(c, c["people"]["worker"], sec, st, rail, rail)
    c["focus"] = c["people"]["worker"].bone_head("spine05")


def i3b(c, t):
    sec = S("intro_3b", t); stage(c, "yard", shells=(70, 0), people=("rel1", "rel2", "worker"))
    a1 = Vector((-5.4, 3.6, 0)); a2 = Vector((-4.6, 3.3, 0))
    stand_at(c["people"]["rel1"], a1, C1, hands_pockets=True)
    turn = ease(min(1.0, max(0.0, (sec - 0.9) / 1.6))); h2 = c["people"]["rel2"]
    stand_pose(h2, head_down=14 * turn, crossed=True); place(h2, a2, face_angle(a2, C1) + math.radians(150) * turn)
    stand_at(c["people"]["worker"], C1 + Vector((0.9, -0.6, 0)), C1)
    if "glass" not in c:
        c["glass"] = tulip_glass((-4.0, 4.3, 0.95)); c["steam"] = steam("Steam", (-4.0, 4.3, 1.05))
    pose_steam(c["steam"], (-4.0, 4.3, 1.06), sec)
    c["focus"] = Vector((-4.0, 4.3, 1.0))


def i4a(c, t):
    sec = S("intro_4a", t); stage(c, "yard", shells=(70, 0), people=("bro1",))
    pit = c["pit"]; h = c["people"]["bro1"]; stance = pit + Vector((1.0, -0.55, 0))
    stand_pose(h); place(h, stance, face_angle(stance, pit) + math.radians(35))
    cyc = (sec / 1.6) % 1.0; k = 0.5 - 0.5 * math.cos(2 * math.pi * cyc)
    fwd = forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    h.rot("spine03", side, -(14 + 18 * (1 - k)))
    blade = (pit + Vector((1.2, 0.3, 0.1))).lerp(pit + Vector((0.25, 0.05, 0.4)), k)
    handle = blade + (Vector(stance) + Vector((0, 0, 1.0)) - blade).normalized() * 0.95
    reach(h, "R", handle, Vector((side.x, side.y, -0.6)), blade - handle)
    reach(h, "L", handle.lerp(blade, 0.45), Vector((-side.x, -side.y, -0.6)), blade - handle)
    fingers_curl(h, 70, thumb=40)
    sp = c["spade"]
    if sp is not None:
        sp.location = blade + (handle - blade).normalized() * 0.5; sp.rotation_mode = 'QUATERNION'; sp.rotation_quaternion = (blade - handle).to_track_quat('Z', 'Y')
    fill = ease(min(1.0, sec / dur("intro_4a")))
    c["leadblock"].location = pit + Vector((0, 0, -0.02 - 0.06 * fill))
    c["fill"].location = pit + Vector((0, 0, -0.14 + 0.13 * fill))
    c["mound"].scale = (0.6, 0.5, 0.32 * (1 - 0.4 * fill))
    for j, cl in enumerate(c["clods"]):        # earth falling off the blade after each tip
        age = (cyc - 0.55 - j * 0.015)
        if 0 < age < 0.35:
            cl.location = blade + Vector((0.03 * (j % 3 - 1), 0.03 * (j % 2), -4.9 * (age * 1.6) ** 2 * 0.6))
            if cl.location.z < 0.02:
                cl.location.z = 0.02
        else:
            cl.location = (0, -150, 0)
    c["focus"] = pit + Vector((0.4, 0, 0.4))


def i4b(c, t):
    sec = S("intro_4b", t); stage(c, "yard", shells=(70, 70), people=("rel1",))
    c["fill"].location = c["pit"] + Vector((0, 0, 0.0)); c["mound"].scale = (0.6, 0.5, 0.18); c["leadblock"].location = c["pit"] + Vector((0, 0, -0.2))
    laundry_sway(c, sec)
    walk_to(c["people"]["rel1"], (12, -1.8, 0), (-14, -1.8, 0), sec, speed=1.0)
    c["focus"] = Vector((3.8, 13.6, 0.8))


# ---- chapter 1
def c1_1a(c, t):
    sec = S("ch1_1a", t); stage(c, "truck", people=("rel1",))
    k = ease(min(1.0, sec / dur("ch1_1a")))
    ang = math.radians(90 * k); r = 6.0
    set_truck(c, -14 + r * math.sin(ang) - 0.0, -9.5 + 8.3 * k if k < 1 else -1.2, ang, roll=sec * 4)
    c["truck"].location = Vector((-10 + 9 * k, -12 + 10.8 * min(1, k * 1.4), 0)); c["truck"].rotation_euler = (0, 0, math.radians(90) * (1 - min(1, k * 1.3)))
    walk_to(c["people"]["rel1"], (-24, 4.6, 0), (-12, 4.8, 0), sec, speed=0.8)
    c["focus"] = c["truck"].location


def c1_1b(c, t):
    sec = S("ch1_1b", t); stage(c, "none", truck_at=(-5.5, -1.4, 0.0), people=("bro1", "bro2"))
    walk_to(c["people"]["bro1"], (10.0, 5.2, 0), (3.6, 3.6, 0), sec, speed=1.1)
    walk_to(c["people"]["bro2"], (11.0, 5.8, 0), (4.6, 3.8, 0), sec - 0.4, speed=1.1)
    c["focus"] = c["people"]["bro1"].arm.location + Vector((0, 0, 1.3))


def c1_4a(c, t):
    sec = S("ch1_4a", t); stage(c, "lot", people=("bro1", "bro2", "worker", "rel1", "rel3"))
    L0 = LOT
    for k, (nm, off) in enumerate((("bro1", (-2.4, 0.6)), ("bro2", (0.2, 1.5)), ("worker", (2.6, -0.2)), ("rel1", (-0.8, -1.8)), ("rel3", (1.6, -1.9)))):
        p = L0 + Vector((*off, 0)); stand_at(c["people"][nm], p, L0, crossed=(k == 3), hands_pockets=(k == 4))
    c["crate"].location = c["cont2"].location; c["crate"].rotation_euler = (0, 0, -0.2)
    c["focus"] = L0 + Vector((0, 0, 1))


def c1_4b(c, t):
    sec = S("ch1_4b", t); stage(c, "lot", people=("bro1", "bro2"))
    cr = c["crate"]; cr.location = c["cont2"].location; cr.rotation_euler = (0, 0, -0.2)
    h = c["people"]["bro1"]; st = c["cont2"].location + Vector((-1.25, -0.5, 0))
    stand_pose(h); place(h, st, face_angle(st, c["cont2"].location))
    k = 0.5 - 0.5 * math.cos(sec * 2.0)
    f = forward(h); sd = f.cross(Vector((0, 0, 1)))
    tip = c["cont2"].location + Vector((-0.58, -0.3, 1.0))
    grip = tip - f * 0.6 + Vector((0, 0, -0.15 - 0.25 * k))
    h.rot("spine03", sd, -14)
    reach(h, "R", grip, Vector((sd.x, sd.y, -0.7)), tip - grip); reach(h, "L", grip.lerp(tip, 0.3), Vector((-sd.x, -sd.y, -0.7)), tip - grip)
    fingers_curl(h, 70, thumb=40)
    cb = c["crowbar"]
    if cb is not None:
        cb.location = grip.lerp(tip, 0.5); cb.rotation_mode = 'QUATERNION'; cb.rotation_quaternion = (tip - grip).to_track_quat('Z', 'Y')
    stand_at(c["people"]["bro2"], c["cont2"].location + Vector((0.6, 1.4, 0)), c["cont2"].location, hands_pockets=True)
    c["focus"] = h.bone_head("spine03")


def c1_5a(c, t):
    sec = S("ch1_5a", t); stage(c, "lot", people=("bro1", "worker"))
    k = ease(min(1.0, sec / dur("ch1_5a")))
    c0 = c["cont1"].location
    plug = c["plug"]; p = c0 + Vector((0.0, -0.4 - 0.9 * k, 0.55 - 0.45 * max(0, k - 0.7) / 0.3)); plug.location = p; plug.rotation_euler = (0, 0, math.pi / 2)
    for j, (nm, side) in enumerate((("bro1", -0.35), ("worker", 0.35))):
        h = c["people"][nm]; st = p + Vector((side, -1.6, 0)); st.z = 0
        stand_pose(h); place(h, st, face_angle(st, p))
        sd = forward(h).cross(Vector((0, 0, 1)))
        h.rot("spine03", sd, 18)                       # leaning back, hauling
        grip = h.bone_head("spine02") + forward(h) * 0.42 + Vector((0, 0, -0.15))
        reach(h, "R", grip, Vector((sd.x, sd.y, -0.7)), forward(h)); reach(h, "L", grip + forward(h) * 0.12, Vector((-sd.x, -sd.y, -0.7)), forward(h))
        fingers_curl(h, 75, thumb=40)
    ch = c["chain"]; a = p + Vector((0, -0.22, 0)); b = c["people"]["bro1"].bone_head("spine02") + Vector((0.35, 0.3, -0.15))
    ch.location = (a + b) / 2; ch.scale = (1, 1, (b - a).length); ch.rotation_mode = 'QUATERNION'; ch.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
    c["focus"] = p


def c1_5b(c, t):
    sec = S("ch1_5b", t); stage(c, "lot", people=("worker", "bro1", "bro2", "rel1"))
    c0 = c["cont1"].location; c["plug"].location = c0 + Vector((0.3, -1.4, 0.16)); c["plug"].rotation_euler = (0, 0, 0.3)
    h = c["people"]["worker"]; st = c0 + Vector((0.0, -0.75, 0))
    stand_pose(h); place(h, st, face_angle(st, c0))
    sd = forward(h).cross(Vector((0, 0, 1))); k = ease(min(1.0, sec / 1.6))
    h.rot("spine02", sd, -25 * k); h.rot("spine04", sd, -20 * k); h.rot("neck01", sd, -10 * k)
    arms_relaxed(h)
    for nm, off in (("bro1", (-1.6, -1.8)), ("bro2", (1.5, -1.5)), ("rel1", (0.4, -2.6))):
        stand_at(c["people"][nm], c0 + Vector((*off, 0)), c0, crossed=(nm == "rel1"))
    c["focus"] = h.bone_head("spine03")


def c1_6a(c, t):
    sec = S("ch1_6a", t); stage(c, "lot", truck_at=(0.0, -5.6, 0.0), people=("bro1", "bro2"))
    precip_fall(c, sec)
    c["cont1"].location = (-1.2, -80, 0)
    for nm, off, ph_ in (("bro1", (-1.0, -6.8), 0.0), ("bro2", (1.0, -6.9), 1.4)):
        h = c["people"][nm]; st = Vector((*off, 0)); stand_pose(h); place(h, st, face_angle(st, (off[0], -5.6)))
        k = 0.5 - 0.5 * math.cos(sec * 2.4 + ph_)
        f = forward(h); sd = f.cross(Vector((0, 0, 1)))
        h.rot("spine03", sd, -(25 * (1 - k)))
        hand = st + f * 0.45 + Vector((0, 0, 0.35 + 0.85 * k))
        reach(h, "R", hand + sd * 0.12, Vector((sd.x, sd.y, -0.7)), f); reach(h, "L", hand - sd * 0.12, Vector((-sd.x, -sd.y, -0.7)), f)
        if nm == "bro1":
            c["plug"].location = hand + f * 0.1; c["plug"].rotation_euler = (0, 0, 0)
    c["focus"] = Vector((0, -6.8, 1.2))


def c1_6b(c, t):
    sec = S("ch1_6b", t); stage(c, "truck", people=())
    precip_fall(c, sec)
    k = ease(min(1.0, sec / dur("ch1_6b")))
    c["truck"].location = Vector((-0.5, -1.0, 0)).lerp(Vector((0.0, 5.5, 0)), k); c["truck"].rotation_euler = (0, 0, math.radians(-90))
    for w in c["wheels"]:
        w.rotation_euler = (0, -6.5 * k / 0.45, 0)
    for j, e in enumerate(c["wipers"]):
        e.rotation_euler = (math.radians(70) * (0.5 - 0.5 * math.cos(sec * 4.5)), 0, 0)
    c["focus"] = c["truck"].location + Vector((0, 0, 1.6))


def c1_7a(c, t):
    sec = S("ch1_7a", t); stage(c, "yard", shells=(70, 0), people=("kid1", "kid2", "rel2"))
    walk_to(c["people"]["kid1"], (-5.5, 2.6, 0), (8, 2.6, 0), sec, speed=1.0, stride=0.8)
    walk_to(c["people"]["kid2"], (-6.3, 2.2, 0), (7, 2.2, 0), sec, speed=1.0, stride=0.8)
    walk_to(c["people"]["rel2"], (-8.0, 2.0, 0), (5, 2.0, 0), sec, speed=0.9)
    laundry_sway(c, sec)
    c["focus"] = c["people"]["kid1"].arm.location + Vector((0, 0, 0.8))


def c1_7b(c, t):
    sec = S("ch1_7b", t); stage(c, "yard", shells=(70, 0), people=())
    laundry_sway(c, sec, 12)
    c["focus"] = Vector((7.0, 13.5, 2.5))


def c1_8a(c, t):          # cold clear morning, WIDE: the second container cut with sparks
    sec = S("ch1_8a", t); stage(c, "yard", truck_at=(3.5, 13.5, math.pi), shells=(70, 0), people=("worker", "bro2", "rel1", "rel3"))
    target = c["cont2"].matrix_world @ Vector((-0.39, -0.12, 0.62))
    torch_man(c, c["people"]["worker"], sec, target, (C2.x - 1.05, C2.y - 0.45, 0))
    stand_at(c["people"]["bro2"], C2 + Vector((1.8, -1.0, 0)), C2, crossed=True)
    stand_at(c["people"]["rel1"], Vector((-4.8, 3.6, 0)), C2, hands_pockets=True)
    stand_at(c["people"]["rel3"], Vector((-3.9, 3.3, 0)), C2)
    c["focus"] = target


def c1_8b(c, t):          # wide morning, from the street side: bucket peels the second shell like a lid
    sec = S("ch1_8b", t); stage(c, "yard", truck_at=(3.5, 13.5, math.pi), ex=True, shells=(70, 0), people=("bro2", "worker"))
    ex = c["ex"]; ex["base"].location = (-3.4, 12.6, 0); ex["base"].rotation_euler = (0, 0, math.radians(-30))
    k = ease(min(1.0, sec / dur("ch1_8b")))
    c["hinge2"].rotation_euler = (math.radians(8 + 70 * k), 0, 0); c["lead_core"].hide_render = False; bpy.context.view_layer.update()
    edge = c["hinge2"].matrix_world @ Vector((0, -0.41, 0.8))
    arm_ik(ex, edge + Vector((-0.3, 0.3, 0.55)))
    b_ = ex["boom"].rotation_euler.y; s_ = ex["stick"].rotation_euler.y; ex["tool"].rotation_euler = (0, -(b_ + s_) + math.radians(95), 0)
    stand_at(c["people"]["bro2"], C2 + Vector((2.2, -1.6, 0)), C2, crossed=True)
    stand_at(c["people"]["worker"], C2 + Vector((-1.6, -2.4, 0)), C2, hands_pockets=True)
    c["focus"] = edge


def c1_9a(c, t):
    sec = S("ch1_9a", t); stage(c, "yard", shells=(70, 78), people=("rel1", "rel2", "rel3", "kid1"))
    for k, (nm, p) in enumerate((("rel1", (-5.6, 3.7)), ("rel2", (-4.8, 3.5)), ("rel3", (-3.6, 3.9)), ("kid1", (-2.9, 3.6)))):
        stand_at(c["people"][nm], Vector((*p, 0)), C2, hands_pockets=(k != 1), crossed=(k == 1))
        c["people"][nm].rot("head", (0, 0, 1), 4 * math.sin(sec * 0.7 + k))
    c["focus"] = Vector((-4.5, 3.7, 1.5))


def c1_9b(c, t):
    stage(c, "yard", shells=(70, 78), people=())
    c["focus"] = C2 + Vector((0, 0, 0.6))


def c1_10a(c, t):
    sec = S("ch1_10a", t); stage(c, "yard", truck_at=(3.5, 13.5, math.pi), shells=(70, 78), people=("worker",))
    h = c["people"]["worker"]
    c["crate"].location = C2 + Vector((-1.6, -1.2, 0)); c["crate"].scale = (0.5, 0.5, 0.4)
    k = ease(min(1.0, sec / 2.2))
    st = C2 + Vector((-1.6, -1.2, 0))
    if k < 0.5:
        stand_pose(h, head_down=10 * k); place(h, st + Vector((0.0, -0.35, 0)), face_angle(st, C2))
    else:
        reset_pose(h); h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); pose_sit(h, lean=20 + 10 * k)
        place(h, st, face_angle(st, C2) + math.pi * 0.1)
        h.rot("neck01", forward(h).cross(Vector((0, 0, 1))), -12); h.rot("head", forward(h).cross(Vector((0, 0, 1))), -10)
    c["focus"] = h.bone_head("spine05")


def c1_10b(c, t):
    sec = S("ch1_10b", t); stage(c, "yard", shells=(70, 78), people=("rel2",))
    h = c["people"]["rel2"]
    door = Vector((-12.5 + 2.6 - 4.5, 10.0 - 4.25 - 0.4, 0))
    if sec < 1.6:
        stand_pose(h, head_down=16); place(h, Vector((-8.4, 4.9, 0)), face_angle((-8.4, 4.9), (-8.4, 6)) + 0.4)
        sd = forward(h).cross(Vector((0, 0, 1))); h.rot("spine03", sd, -12)
        wallp = Vector((-7.6, 4.4, 0.95))
        reach(h, "L", wallp + Vector((0, 0, 0.02)), Vector((-1, 0, -0.5)), Vector((0, 0, -1)))
    else:
        walk_to(h, (-8.4, 4.9, 0), door, sec - 1.6, speed=0.6)
    c["focus"] = h.bone_head("spine05")


def c1_12a(c, t):         # night kitchen: a man alone at the table under a bare bulb, staring down (hands below the table)
    sec = S("ch1_12a", t); stage(c, "yard", shells=(70, 78), people=("worker",))
    h = c["people"]["worker"]; k0 = c["fam"]["table"]
    reset_pose(h); h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); pose_sit(h, lean=24, hands="knees")
    place(h, k0 + Vector((0.8, 0.1, 0.0)), face_angle(k0 + Vector((0.8, 0.1, 0)), k0))
    sd = forward(h).cross(Vector((0, 0, 1)))
    h.rot("neck01", sd, -10); h.rot("head", sd, -14 - 2 * math.sin(sec * 0.5))
    c["focus"] = h.bone_head("head")


def c1_12b(c, t):
    sec = S("ch1_12b", t); stage(c, "yard", shells=(70, 78), people=())
    precip_fall(c, sec); laundry_sway(c, sec, 4)
    c["focus"] = KITCHEN_WIN


def c1_13a(c, t):
    sec = S("ch1_13a", t); stage(c, "none", truck_at=(1.5, 11.0, math.pi), people=("bro1", "bro2"))
    for o in c["load"]:
        o.hide_render = False
    h = c["people"]["bro1"]; st = Vector((2.4, 13.0, 0)); stand_pose(h); place(h, st, face_angle(st, (3.8, 13.9)))
    cyc = (sec / 1.5) % 1.0; k = 0.5 - 0.5 * math.cos(2 * math.pi * cyc)
    f = forward(h); sd = f.cross(Vector((0, 0, 1)))
    h.rot("spine03", sd, -(15 + 20 * (1 - k)))
    blade = (st + f * 0.9 + Vector((0, 0, 0.15))).lerp(Vector((1.8, 12.0, 1.3)), k)
    handle = blade + (st + Vector((0, 0, 1.05)) - blade).normalized() * 0.95
    reach(h, "R", handle, Vector((sd.x, sd.y, -0.6)), blade - handle); reach(h, "L", handle.lerp(blade, 0.45), Vector((-sd.x, -sd.y, -0.6)), blade - handle)
    fingers_curl(h, 70, thumb=40)
    sp = c["spade"]
    if sp is not None:
        sp.location = blade + (handle - blade).normalized() * 0.5; sp.rotation_mode = 'QUATERNION'; sp.rotation_quaternion = (blade - handle).to_track_quat('Z', 'Y')
    h2 = c["people"]["bro2"]; st2 = Vector((0.6, 12.6, 0)); stand_pose(h2); place(h2, st2, face_angle(st2, (0.6, 11.0)))
    k2 = ease(min(1.0, (sec % 2.6) / 1.3)) if (sec % 2.6) < 1.3 else 1 - ease(((sec % 2.6) - 1.3) / 1.3)
    f2 = forward(h2); s2 = f2.cross(Vector((0, 0, 1)))
    sack = st2 + f2 * 0.35 + Vector((0, 0, 0.6 + 0.9 * k2))
    reach(h2, "R", sack + s2 * 0.15, Vector((s2.x, s2.y, -0.6)), f2); reach(h2, "L", sack - s2 * 0.15, Vector((-s2.x, -s2.y, -0.6)), f2)
    c["sack"].location = sack + f2 * 0.15
    c["focus"] = st + Vector((0, 0, 1.2))


def c1_13b(c, t):
    sec = S("ch1_13b", t); stage(c, "none", people=())
    for o in c["load"]:
        o.hide_render = False
    k = ease(min(1.0, sec / dur("ch1_13b")))
    p = Vector((0.0, 9.0, 0)).lerp(Vector((0.0, 1.0, 0)), min(1, k * 1.6))
    ang = math.radians(-90) * (1 - max(0, (k - 0.5) * 2))
    if k > 0.6:
        p = Vector((0, 1.0, 0)) + Vector((-14 * (k - 0.6) / 0.4, 0, 0))
    set_truck(c, p.x, p.y, ang + math.radians(180), roll=-sec * 3)
    c["focus"] = p + Vector((0, 0, 1.4))


def c2_5b(c, t):          # push in on a scuffed shell as the three-blade mark comes into the light
    sec = S("ch2_5b", t); stage(c, "yard", shells=(70, 78), people=())
    k1 = c["k1"]; tr = k1["trefoil"]; tr.hide_render = False
    c["cont1"].rotation_euler = (0, 0, math.radians(-160))
    c["focus"] = tr.matrix_world.translation if tr else C1


def c4_5a(c, t):          # specialists in coats walk the family yard with detectors
    sec = S("ch4_5a", t); stage(c, "none", people=("rel3", "worker"))
    from sc_scrapyard import detector, hold_detector
    if "det" not in c:
        c["det"] = detector("YDet")
    h = c["people"]["rel3"]; walk_to(h, (-4.5, 6.0, 0), (2.5, 12.5, 0), sec, speed=0.5, stride=0.9)
    hold_detector(c, h, sec, sweep=sec * 1.3, level=0.06)
    walk_to(c["people"]["worker"], (-5.5, 7.0, 0), (0.5, 13.5, 0), sec - 0.5, speed=0.5)
    c["focus"] = h.bone_head("spine02")


def c4_5b(c, t):          # a surveyor kneels by the old pit while neighbours watch from the street
    sec = S("ch4_5b", t); stage(c, "none", people=("rel3", "rel1", "rel2", "kid1"))
    from sc_scrapyard import detector, hold_detector
    if "det" not in c:
        c["det"] = detector("YDet")
    pit = c["pit"]; c["fill"].location = pit + Vector((0, 0, 0.0)); c["mound"].scale = (0.6, 0.5, 0.05); c["leadblock"].location = pit + Vector((0, 0, -0.3))
    h = c["people"]["rel3"]; st = pit + Vector((0.2, -0.9, 0))
    stand_pose(h); place(h, st, face_angle(st, pit))
    sd = forward(h).cross(Vector((0, 0, 1)))
    for side, sg in (("L", 1), ("R", -1)):                      # kneel: thighs forward, shins back on the ground
        h.aim(f"upperleg01.{side}", forward(h) * 0.9 + Vector((0, 0, -0.45))); h.aim(f"upperleg02.{side}", forward(h) * 0.9 + Vector((0, 0, -0.45)))
        h.aim(f"lowerleg01.{side}", -forward(h) + Vector((0, 0, -0.15))); h.aim(f"lowerleg02.{side}", -forward(h) + Vector((0, 0, -0.15)))
    place(h, st, face_angle(st, pit))
    h.rot("spine03", sd, -18)
    hold_detector(c, h, sec, sweep=sec * 1.1, level=0.05)
    for k, (nm, p) in enumerate((("rel1", (-5.6, 3.7)), ("rel2", (-4.8, 3.5)), ("kid1", (-4.0, 3.6)))):
        stand_at(c["people"][nm], Vector((*p, 0)), pit, hands_pockets=(k != 1), crossed=(k == 1))
    c["focus"] = h.bone_head("head")


SHOTS = {
    "ch2_5b": ("yard", c2_5b, C((C1.x + 1.6, C1.y + 0.2, 0.8), (C1.x + 0.85, C1.y + 0.1, 0.72), (C1.x, C1.y, 0.66), 50), 2.0),
    "ch4_5a": ("yard", c4_5a, C((5.5, 4.5, 1.6), (5.0, 5.0, 1.6), (-0.5, 10.0, 1.1), 30), 4.0),
    "ch4_5b": ("yard", c4_5b, C((-1.0, 11.0, 1.2), (-1.3, 11.3, 1.2), (-3.6, 14.2, 0.7), 32), 4.0),
    "intro_1a": ("drive", i1a, C((14.0, -2.6, 0.9), (13.0, -2.4, 1.1), (-14, 0.6, 2.0), 40), 4.0),
    "intro_1b": ("drive", i1b, C((-3.6, 1.5, 0.95), (-2.0, 1.55, 1.0), (0.9, 5.0, 1.45), 32), 2.8),
    "intro_2a": ("yard_dusk", i2a, C((C2.x + 1.3, C2.y + 1.9, 0.55), (C2.x + 1.0, C2.y + 1.6, 0.6), (C2.x - 0.8, C2.y - 0.4, 0.95), 35), 2.0),
    "intro_2b": ("yard_dusk", i2b, C((-4.6, 5.4, 0.55), (-4.2, 5.7, 0.6), (-2.4, 9.0, 1.1), 28), 2.8),
    "intro_3a": ("yard", i3a, C((-3.6, 8.0, 1.5), (-3.2, 8.4, 1.55), (-0.8, 11.6, 1.2), 32), 4.0),
    "intro_3b": ("yard", i3b, C((-2.45, 3.75, 1.12), (-2.65, 3.8, 1.12), (-5.3, 3.75, 1.2), 40), 2.0),
    "intro_4a": ("late", i4a, C((-6.5, 11.8, 1.05), (-6.2, 12.1, 1.05), (-2.9, 14.6, 0.55), 32), 3.5),
    "intro_4b": ("dusk", i4b, C((-5.5, 1.0, 1.6), (-4.0, 4.0, 1.55), (6.0, 11.5, 1.4), 28), 5.6),
    "ch1_1a": ("drive", c1_1a, C((-18, -16, 12), (-16, -14, 5.5), (-4, -4, 1.2), 28), None),
    "ch1_1b": ("drive", c1_1b, C((-1.5, 1.0, 1.5), (-1.2, 1.4, 1.5), (7.0, 4.6, 1.3), 35), 4.0),
    "ch1_4a": ("lot", c1_4a, C((6.0, -18.0, 4.5), (5.0, -17.0, 4.0), (0.0, -10.0, 0.8), 28), None),
    "ch1_4b": ("lot", c1_4b, C((LOT.x + 3.2, LOT.y - 3.4, 1.3), (LOT.x + 2.9, LOT.y - 3.0, 1.3), (LOT.x + 0.4, LOT.y - 0.8, 0.9), 35), 2.8),
    "ch1_5a": ("lot", c1_5a, C((LOT.x + 2.8, LOT.y - 2.5, 1.1), (LOT.x + 2.5, LOT.y - 2.9, 1.1), (LOT.x - 1.2, LOT.y - 1.6, 0.8), 32), 4.0),
    "ch1_5b": ("lot", c1_5b, C((LOT.x - 1.2, LOT.y - 4.5, 1.6), (LOT.x - 1.2, LOT.y - 3.9, 1.6), (LOT.x - 1.2, LOT.y + 0.5, 0.9), 32), 2.8),
    "ch1_6a": ("rain", c1_6a, C((4.0, -10.5, 1.5), (3.6, -10.1, 1.5), (0.0, -6.0, 1.2), 30), 4.0),
    "ch1_6b": ("rain", c1_6b, C((3.0, 8.5, 1.4), (2.6, 8.2, 1.4), (0.0, 2.0, 1.5), 32), 4.0),
    "ch1_7a": ("yard", c1_7a, C((-6.0, -3.0, 1.2), (2.0, -3.0, 1.2), (-4.0, 6.0, 1.0), 32, (2.0, 8.0, 1.0)), 4.0),
    "ch1_7b": ("yard", c1_7b, C((1.0, 7.0, 1.3), (1.0, 7.0, 7.0), (8.0, 14.0, 2.5), 26, (6.0, 13.0, 4.0)), None),
    "ch1_8a": ("yard_morning", c1_8a, C((6.0, 3.0, 2.4), (5.2, 3.4, 2.5), (0.6, 9.5, 0.8), 26), None),
    "ch1_8b": ("yard_morning", c1_8b, C((5.6, 6.0, 1.6), (5.0, 6.4, 1.7), (0.0, 11.0, 1.5), 28), None),
    "ch1_9a": ("yard_morning", c1_9a, C((-1.0, 6.5, 1.5), (-1.4, 6.2, 1.5), (-4.6, 3.6, 1.4), 35), 2.8),
    "ch1_9b": ("yard_morning", c1_9b, C((C2.x + 0.8, C2.y - 2.0, 1.2), (C2.x + 0.4, C2.y - 1.2, 1.0), (C2.x, C2.y, 0.6), 40), 2.0),
    "ch1_10a": ("late", c1_10a, C((C2.x + 1.2, C2.y - 4.4, 1.3), (C2.x + 0.9, C2.y - 4.0, 1.25), (C2.x - 1.6, C2.y - 1.4, 0.9), 35), 2.8),
    "ch1_10b": ("late", c1_10b, C((-4.0, 1.5, 1.5), (-4.4, 1.9, 1.5), (-8.2, 5.0, 1.2), 35), 2.8),
    "ch1_12a": ("night", c1_12a, C((FAM.x + 1.5, FAM.y - 2.6, 1.55), (FAM.x + 1.3, FAM.y - 2.3, 1.5), (KITCHEN_WIN.x + 2.4, KITCHEN_WIN.y + 0.1, 0.95), 28), 2.4),
    "ch1_12b": ("night", c1_12b, C((2.0, 9.0, 1.6), (2.6, 9.6, 1.65), (KITCHEN_WIN.x, KITCHEN_WIN.y, 1.5), 32), 4.0),
    "ch1_13a": ("scrapload", c1_13a, C((5.5, 9.5, 1.5), (5.1, 9.8, 1.5), (2.0, 12.4, 1.1), 30), 4.0),
    "ch1_13b": ("scrapload", c1_13b, C((-8.0, -3.0, 1.2), (-7.5, -2.6, 1.3), (0.0, 4.0, 1.5), 30), 4.0),
}
VARIANT_FOR = {k: v[0] for k, v in SHOTS.items()}
DUR = {k: dur(k) for k in SHOTS}


def _focus(c, t):
    return c.get("focus", Vector((0, 10, 1)))


from durs import title_for
MOVES = {k: {**dict(kind="anim", far=300.0, anim=v[1], cam=v[2], dof=v[3], focus=_focus), **({'title': title_for(k), 'dof': None} if title_for(k) else {})} for k, v in SHOTS.items()}
