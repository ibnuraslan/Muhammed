"""Small sets: the grandmother's parlour in Marion, Massachusetts (Arthur at the window), a village schoolroom,
and the Mary Celeste's hold being stowed with barrels in New York."""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix, noise
import ship, ph
import stage as S
import cabin


def wallpaper(name="wallpaper", base=(0.36, 0.2, 0.12), motif=(0.5, 0.36, 0.18)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (7, 7, 7); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    v = N.new("ShaderNodeTexVoronoi"); v.feature = 'SMOOTH_F1'; L.new(mp.outputs[0], v.inputs['Vector'])
    st = N.new("ShaderNodeTexWave"); st.bands_direction = 'Z'; st.inputs['Scale'].default_value = 2.5
    L.new(mp.outputs[0], st.inputs['Vector'])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.1; mr.inputs['From Max'].default_value = 0.18
    L.new(v.outputs['Distance'], mr.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (*motif, 1); mx.inputs[7].default_value = (*base, 1)
    L.new(mr.outputs[0], mx.inputs['Factor'])
    L.new(mx.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.8
    return m


def window(c, w, h, mat_frame, panes=(2, 3), glass=None):
    """A sash window in a wall facing -X at x = c.x: frame, muntins, glass."""
    x, y, z = c
    g = glass or _glass()
    ship.box("win_glass", (x, y, z), (0.006, w, h), g)
    for sg in (-1, 1):
        ship.box("win_jamb", (x - 0.02, y + sg * (w / 2 + 0.04), z), (0.12, 0.08, h + 0.16), mat_frame)
        ship.box("win_head", (x - 0.02, y, z + sg * (h / 2 + 0.05)), (0.12, w + 0.16, 0.1), mat_frame)
    ship.box("win_meet", (x - 0.03, y, z), (0.06, w, 0.04), mat_frame)
    for k in range(1, panes[0]):
        ship.box("muntin", (x - 0.025, y - w / 2 + w * k / panes[0], z), (0.03, 0.018, h), mat_frame)
    for k in range(1, panes[1] * 2):
        if k == panes[1]:
            continue
        ship.box("muntin", (x - 0.025, y, z - h / 2 + h * k / (panes[1] * 2)), (0.03, w, 0.018), mat_frame)
    ship.box("win_sill", (x - 0.1, y, z - h / 2 - 0.1), (0.24, w + 0.2, 0.04), mat_frame)
    return Vector((x - 0.12, y, z - h / 2 - 0.08))


def _glass():
    g = bpy.data.materials.new("glass"); g.use_nodes = True
    p = g.node_tree.nodes["Principled BSDF"]; p.inputs['Transmission Weight'].default_value = 1.0
    p.inputs['Roughness'].default_value = 0.03; p.inputs['IOR'].default_value = 1.5
    return g


def parlour():
    """Grandmother's parlour, Marion: wallpaper, a sash window onto autumn trees, lace curtains, a rocking chair."""
    A = {}
    paint = ship.paint("trim", (0.42, 0.36, 0.28), rough=0.4, grime=0.2)
    floor = ship.wood("wood_floor_deck", 0.8, tint=(0.75, 0.55, 0.38), name="parlourfloor")
    wp = wallpaper()
    ship.box("floor", (0, 0, -0.03), (6, 6, 0.06), floor)
    # walls: x = 1.6 window wall (facing -x into the room), y = 2.0 side wall, with an opening for the window
    W = 1.6
    ship.box("wall_a", (W + 0.05, -1.65, 1.4), (0.1, 2.3, 2.8), wp)
    ship.box("wall_b", (W + 0.05, 1.65, 1.4), (0.1, 2.3, 2.8), wp)
    ship.box("wall_c", (W + 0.05, 0, 0.375), (0.1, 1.0, 0.75), wp)
    ship.box("wall_d", (W + 0.05, 0, 2.45), (0.1, 1.0, 0.7), wp)
    ship.box("wall_side", (0, 2.05, 1.4), (6, 0.1, 2.8), wp)
    ship.box("wainscot", (W - 0.01, 0, 0.45), (0.03, 5.6, 0.9), paint)
    ship.box("ceiling", (0, 0, 2.83), (6, 6, 0.06), ship.paint("ceil", (0.5, 0.46, 0.4), rough=0.6, grime=0.1))
    A["sill"] = window(Vector((W + 0.04, 0, 1.43)), 0.84, 1.3, paint)
    # lace curtains either side
    lace = cabin.cloth_material("lace", (0.7, 0.66, 0.58), sheen=0.6)
    lm = lace.node_tree.nodes["Principled BSDF"]; lm.inputs['Transmission Weight'].default_value = 0.4
    for sg in (-1, 1):
        cabin._curtain(W - 0.06, W - 0.06, 0.0, 2.25, 0.0, lace)
    for o in [o for o in bpy.data.objects if o.name.startswith("curtain")]:
        bpy.data.objects.remove(o)
    for sg in (-1, 1):
        y0 = sg * 0.5
        V = []; F = []
        n, m = 30, 24
        for j in range(m + 1):
            for i in range(n + 1):
                u, v = i / n, j / m
                yy = y0 + sg * 0.32 * u * (0.7 + 0.3 * v)
                xx = W - 0.08 - 0.03 * math.sin(u * 2 * math.pi * 5)
                V.append((xx, yy, 2.3 - 1.75 * v))
        for j in range(m):
            for i in range(n):
                a = j * (n + 1) + i
                F.append([a, a + 1, a + n + 2, a + n + 1])
        ship.mesh_obj("lace", V, F, lace)
    try:
        S.place_model("Rockingchair_01", (0.5, 1.2, 0), size=1.05, rot_z=math.radians(-130))
    except Exception:
        pass
    try:
        S.place_model("side_table_01", (1.2, 1.55, 0), size=0.7)
        S.place_model("vintage_oil_lamp", (1.2, 1.55, 0.7), size=0.4)
    except Exception:
        pass
    # outside: autumn trees in soft daylight
    ph.world_hdri("autumn_park", strength=1.0, rot_z=math.radians(180), res="4k")
    S.area("WinKey", Vector((W + 0.6, 0, 1.5)), Vector((0, 0, 1.0)), 380, size=0.9, size_y=1.3, color=(0.9, 0.93, 1.0))
    S.area("Fill", Vector((-1.5, -1.0, 2.2)), Vector((1, 0, 1)), 20, size=2, color=(1.0, 0.8, 0.6))
    A["bounds"] = (-2.8, W - 0.15, -2.8, 1.95, 0.3, 2.7)
    return A


def schoolroom():
    A = {}
    floor = ship.wood("weathered_planks", 0.7, tint=(0.85, 0.7, 0.55), name="schoolfloor")
    wall = ship.paint("schoolwall", (0.5, 0.42, 0.3), rough=0.6, grime=0.3, scale=3)
    ship.box("floor", (0, 0, -0.03), (8, 8, 0.06), floor)
    ship.box("wall_w", (2.0, 0, 1.6), (0.1, 8, 3.2), wall)
    ship.box("wall_b", (0, 2.6, 1.6), (8, 0.1, 3.2), wall)
    trim = ship.paint("strim", (0.25, 0.17, 0.1), rough=0.4)
    window(Vector((1.96, 0.6, 1.7)), 0.9, 1.4, trim)
    desks = []
    for k, (x, y) in enumerate(((0.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (-1.0, 1.0))):
        try:
            r, ms = S.place_model("SchoolDesk_01", (x, y, 0), size=0.72, rot_z=math.radians(90))
            desks.append((Vector((x, y, 0)), ms))
        except Exception:
            pass
    A["desk"] = desks[0][0] if desks else Vector((0, 0, 0))
    lo, hi = ph.bounds(desks[0][1]) if desks else (Vector((0, 0, 0)), Vector((0, 0, 0.72)))
    A["desk_top"] = hi.z
    A["desk_lo"], A["desk_hi"] = lo, hi
    ph.world_hdri("autumn_field", strength=0.8, rot_z=0, res="4k")
    S.area("WinKey", Vector((2.6, 0.6, 1.8)), Vector((0, 0, 0.8)), 420, size=1.0, size_y=1.4, color=(0.92, 0.95, 1.0))
    S.area("Fill", Vector((-2.5, -1.5, 2.4)), Vector((0, 0, 0.8)), 25, size=2, color=(1.0, 0.82, 0.62))
    return A


def hold():
    """The main hold, New York: curved frames and ceiling planking, barrels stowed lying in tiers, bilge-and-cantline,
    a lantern on a hook, the hatch square bright above."""
    A = {}
    plank = ship.wood("brown_planks_05", 0.9, tint=(0.6, 0.45, 0.32), name="ceiling_planks")
    frame = ship.wood("dark_wooden_planks", 1.2, tint=(0.55, 0.4, 0.3), name="frames")
    # a section of the hold ~8 m long: a U of planking
    n = 26
    V = []; F = []
    for j in range(2):
        x = -4 + 8 * j
        for i in range(n + 1):
            a = math.pi * (0.08 + 0.84 * i / n)
            V.append((x, 3.2 * math.cos(a), 2.6 - 2.6 * math.sin(a) ** 0.7))
    for i in range(n):
        F.append([i, i + 1, n + 2 + i, n + 1 + i])
    o = ship.mesh_obj("hold_ceiling", V, F, plank)
    o.data.materials[0].use_backface_culling = False
    for x in np.arange(-3.8, 4.0, 0.6):
        pts = []
        for i in range(n + 1):
            a = math.pi * (0.08 + 0.84 * i / n)
            pts.append(Vector((x, 3.1 * math.cos(a), 2.6 - 2.5 * math.sin(a) ** 0.7)))
        ship.rope("frame", pts, 0.08, frame)
    hx0, hx1, hy = -0.4, 2.0, 1.1
    ship.box("deckhead", ((-4 + hx0) / 2, 0, 2.75), (hx0 + 4, 7, 0.1), plank)
    ship.box("deckhead", ((hx1 + 4) / 2, 0, 2.75), (4 - hx1, 7, 0.1), plank)
    for sg in (1, -1):
        ship.box("deckhead", ((hx0 + hx1) / 2, sg * (hy + 3.5) / 2, 2.75), (hx1 - hx0, 3.5 - hy, 0.1), plank)
    S.area("HatchSky", Vector((0.8, 0, 3.4)), Vector((0.8, 0, 0)), 260, size=2.4, size_y=2.2, color=(0.75, 0.8, 0.9))
    ship.box("hatch_well", (0.8, 0, 2.75), (2.4, 2.2, 0.12), ship.paint("void", (0.9, 0.85, 0.75), rough=0.9))
    for x in np.arange(-3.6, 4, 0.9):
        if abs(x - 0.8) > 1.3:
            ship.box("deckbeam", (x, 0, 2.62), (0.2, 6.5, 0.22), frame)
    # barrels lying fore-and-aft in tiers (bilge free, cantline up), chocked with dunnage
    r, ms = S.place_model("wine_barrel_01", (0, 0, 0), size=0.86)
    lo, hi = ph.bounds(ms); bd = max(hi.x - lo.x, hi.y - lo.y); bl = hi.z - lo.z
    r.rotation_euler = (0, math.pi / 2, 0); bpy.context.view_layer.update()
    lo, hi = ph.bounds(ms); c = (lo + hi) / 2
    r["off"] = tuple(r.location - c)
    import pier
    A["barrels"] = []
    for tier in range(3):
        nrow = 6 - tier
        for row in range(nrow):
            yy = (row - (nrow - 1) / 2) * (bd + 0.02)
            zz = 0.55 + bd / 2 + tier * bd * 0.86
            for col in range(6):
                xx = -3.2 + col * (bl + 0.05)
                if tier == 2 and col > 2:
                    continue
                b = pier._inst(r, Vector((xx, yy, zz)), rz=0)
                b.rotation_euler = (0, math.pi / 2, 0)
                A["barrels"].append(Vector((xx, yy, zz)))
    r.location = Vector((-8, 0, 0))
    A["bd"] = bd; A["bl"] = bl
    try:
        lr, lms = S.place_model("Lantern_01", (1.2, -1.6, 1.85), size=0.32)
        lo, hi = ph.bounds(lms)
        A["lantern"] = (lo + hi) / 2
        S.point("LanternLight", A["lantern"], 28, color=(1.0, 0.6, 0.28), radius=0.04)
        S.flame("lflame", A["lantern"], h=0.02, strength=60)
    except Exception:
        S.point("LanternLight", Vector((1.2, -1.6, 1.85)), 28, color=(1.0, 0.6, 0.28))
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = 6.0; sun.data.color = (1.0, 0.85, 0.65); sun.data.angle = math.radians(1)
    sun.rotation_euler = (math.radians(18), math.radians(-14), 0)
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.55, 0.65, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.4
    bpy.data.objects["hatch_well"].hide_render = True
    vol = bpy.data.materials.new("dust"); vol.use_nodes = True
    N = vol.node_tree.nodes; N.remove(N["Principled BSDF"])
    pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs['Density'].default_value = 0.09; pv.inputs['Anisotropy'].default_value = 0.6
    vol.node_tree.links.new(pv.outputs[0], N["Material Output"].inputs['Volume'])
    du = ship.box("dust", (0, 0, 1.3), (7.8, 6.2, 2.6), vol); du.visible_shadow = False
    du.hide_render = S.NOVOL
    return A
