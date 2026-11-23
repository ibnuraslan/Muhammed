"""Osteology lab (University, early 2000s): a dark room, one long bench by a tall window with grey Atlantic daylight,
an anglepoise lamp as the practical key, black velvet on the bench under the bones, a stereo microscope,
a stool, shelves of archive boxes falling into darkness.

    A = room(window_light=1.0, lamp=True)     -> dict(bench_top=z, bench=(x0, x1, y0, y1), lamp=obj, ...)
    velvet(x0, x1, y0, y1, z)                 black cloth with soft folds
Coordinates: the bench runs along x at y = 0..0.8 (window side +y), top at z = 0.92. Origin at the bench centre.
"""
import math
import bpy, bmesh
from mathutils import Vector
import ph, sf

TOP = 0.92


def _box(name, c, s, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.active_object; o.name = name; o.scale = s
    o.data.materials.append(m)
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = min(0.006, min(s) * 0.2); bv.segments = 2
    return o


def _mat(name, col, rough=0.6, metal=0.0, sheen=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal; p.inputs['Sheen Weight'].default_value = sheen
    return m


def velvet(x0, x1, y0, y1, z, name="velvet"):
    bpy.ops.mesh.primitive_plane_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, z + 0.002))
    o = bpy.context.active_object; o.name = name; o.scale = (x1 - x0, y1 - y0, 1)
    sub = o.modifiers.new("sub", "SUBSURF"); sub.subdivision_type = 'SIMPLE'; sub.levels = 5; sub.render_levels = 5
    d = o.modifiers.new("folds", "DISPLACE"); t = bpy.data.textures.new("velvetfold", "CLOUDS"); t.noise_scale = 0.12
    d.texture = t; d.strength = 0.006; d.mid_level = 0.0
    m = _mat("velvet", (0.004, 0.004, 0.005), rough=0.95, sheen=0.35)
    m.node_tree.nodes["Principled BSDF"].inputs['Sheen Roughness'].default_value = 0.4
    m.node_tree.nodes["Principled BSDF"].inputs['Sheen Tint'].default_value = (0.25, 0.25, 0.28, 1)
    o.data.materials.append(m)
    return o


def room(window_light=1.0, lamp=True, lamp_at=(0.35, 0.55), lamp_target=(0.0, 0.35), lamp_energy=60.0, shelves=True):
    out = {}
    wall = ph.texture("painted_plaster_wall", scale=1.2, name="labwall", tint=(0.55, 0.58, 0.6))
    floor = ph.texture("concrete_floor_worn_001", scale=1.0, name="labfloor", tint=(0.45, 0.45, 0.45))
    wood = ph.texture("wood_table_worn", scale=1.5, name="benchwood", tint=(0.7, 0.62, 0.55))
    steel = _mat("labsteel", (0.4, 0.4, 0.42), rough=0.35, metal=1.0)
    # room shell: 9 x 6 m, 3.2 m high; window wall at y = 1.2
    W, D, Hh = 9.0, 6.0, 3.2
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 1.2 - D / 2, 0)); f = bpy.context.active_object; f.scale = (W, D, 1)
    f.data.materials.append(floor); f.name = "floor"
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 1.2 - D / 2, Hh)); c = bpy.context.active_object; c.scale = (W, D, 1)
    c.rotation_euler.x = math.pi; c.data.materials.append(_mat("ceiling", (0.5, 0.5, 0.5), 0.9)); c.name = "ceiling"
    for nm, loc, rot, sc in (("wall_back", (0, 1.2 - D, Hh / 2), (math.pi / 2, 0, 0), (W, Hh, 1)),
                             ("wall_l", (-W / 2, 1.2 - D / 2, Hh / 2), (math.pi / 2, 0, math.pi / 2), (D, Hh, 1)),
                             ("wall_r", (W / 2, 1.2 - D / 2, Hh / 2), (math.pi / 2, 0, -math.pi / 2), (D, Hh, 1))):
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc); o = bpy.context.active_object; o.rotation_euler = rot; o.scale = sc
        o.data.materials.append(wall); o.name = nm
    # window wall with two tall windows (holes): built from slabs, glazing bars, and a sky emitter outside
    y = 1.2; t = 0.25
    for nm, cx, sx, cz, sz in (("ww_low", 0, W, 0.45, 0.9), ("ww_high", 0, W, 2.95, 0.5),
                               ("ww_l", -3.2, 2.6, 1.8, 1.8), ("ww_m", 0, 1.0, 1.8, 1.8), ("ww_r", 3.2, 2.6, 1.8, 1.8)):
        _box(nm, (cx, y + t / 2, cz), (sx, t, sz), wall)
    frame = _mat("frame", (0.75, 0.75, 0.72), 0.5)
    for cx in (-1.25, 1.25):
        for k in range(4):
            _box("mullion", (cx - 0.95 + k * 0.633, y + 0.04, 1.8), (0.04, 0.05, 1.8), frame)
        for k in range(3):
            _box("transom", (cx, y + 0.04, 0.9 + k * 0.9), (1.9, 0.05, 0.04), frame)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y + 2.0, 1.8)); sk = bpy.context.active_object
    sk.scale = (9, 4, 1); sk.rotation_euler.x = math.pi / 2; sk.name = "window_sky"
    em = _mat("skyem", (0, 0, 0)); N = em.node_tree.nodes; Lk = em.node_tree.links
    e = N.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (0.62, 0.7, 0.82, 1); e.inputs['Strength'].default_value = 6.0 * window_light
    Lk.new(e.outputs[0], N["Material Output"].inputs['Surface']); sk.data.materials.append(em)
    sk.visible_shadow = False
    # soft daylight through the windows (area lights just inside the glass, invisible to camera)
    for cx in (-1.25, 1.25):
        d = bpy.data.lights.new("window", 'AREA'); d.shape = 'RECTANGLE'; d.size = 1.9; d.size_y = 1.8
        d.energy = 260 * window_light; d.color = (0.78, 0.85, 1.0)
        lo = bpy.data.objects.new("window", d); bpy.context.scene.collection.objects.link(lo)
        lo.location = (cx, y - 0.05, 1.8); lo.rotation_euler = (math.radians(90 + 25), 0, math.pi)
        lo.visible_camera = False; lo.visible_glossy = False
    # the bench: thick worn timber top on steel frame, along the window
    out["bench"] = (-2.2, 2.2, -0.05, 0.8)
    _box("bench_top", (0, 0.375, TOP - 0.025), (4.4, 0.85, 0.05), wood)
    for x in (-2.1, 2.1):
        for yy in (0.0, 0.75):
            _box("bench_leg", (x, yy, (TOP - 0.05) / 2), (0.04, 0.04, TOP - 0.05), steel)
    _box("bench_rail", (0, 0.75, 0.12), (4.2, 0.03, 0.03), steel)
    out["bench_top"] = TOP
    # anglepoise-style practical lamp (Poly Haven) clamped at the back of the bench, warm bulb
    if lamp:
        try:
            root, ms = ph.model("desk_lamp_arm_01", loc=(lamp_at[0], 0.72, TOP), rot_z=math.radians(200))
            out["lamp_obj"] = root
        except Exception as ex:
            print("lamp model:", ex)
        d = bpy.data.lights.new("lampkey", 'SPOT'); d.energy = lamp_energy; d.color = (1.0, 0.86, 0.68)
        d.spot_size = math.radians(70); d.spot_blend = 0.6; d.shadow_soft_size = 0.04
        lo = bpy.data.objects.new("lampkey", d); bpy.context.scene.collection.objects.link(lo)
        lo.location = (lamp_at[0], lamp_at[1], TOP + 0.48)
        lo.rotation_euler = (Vector((lamp_target[0], lamp_target[1], TOP)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
        out["lamp"] = lo
    # stereo microscope and a lab stool
    try:
        r, ms = sf.model("8a34cfebf2c84eb2b9a6e3c07a54d87c", loc=(1.45, 0.45, TOP), rot_z=math.radians(180), height=0.42)
        out["microscope"] = r
    except Exception as ex:
        print("microscope:", ex)
    try:
        r, ms = sf.model("a734ca63ca1c489a9a3749fa50345930", loc=(1.4, -0.45, 0), rot_z=0.3, height=0.62)
        out["stool"] = r
    except Exception as ex:
        print("stool:", ex)
    # archive shelving on the back wall, boxes fading into the dark
    if shelves:
        box = _mat("archivebox", (0.42, 0.36, 0.27), 0.85)
        lid = _mat("archivelid", (0.36, 0.3, 0.22), 0.85)
        import random
        rng = random.Random(2)
        for sx in (-3.0, -1.0, 1.0, 3.0):
            for k in range(5):
                z = 0.15 + k * 0.48
                _box("shelf", (sx, 1.2 - D + 0.35, z), (1.9, 0.5, 0.025), steel)
                xx = sx - 0.85
                while xx < sx + 0.75:
                    w = rng.choice((0.32, 0.32, 0.4))
                    _box("archive", (xx + w / 2, 1.2 - D + 0.36, z + 0.17), (w - 0.02, 0.42, 0.32), box if rng.random() < 0.7 else lid)
                    xx += w
            for x in (sx - 0.95, sx + 0.95):
                _box("upright", (x, 1.2 - D + 0.35, 1.2), (0.03, 0.5, 2.4), steel)
    w = bpy.data.worlds.new("labworld"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs['Color'].default_value = (0.02, 0.022, 0.025, 1)
    w.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.3
    return out


def tray(x, y, w=0.42, d=0.32, z=TOP):
    """Shallow acid-free card tray (bones are laid out in these)."""
    m = _mat("traycard", (0.62, 0.58, 0.5), 0.9)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new("tray"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("tray", me); bpy.context.scene.collection.objects.link(o)
    o.scale = (w, d, 0.05); o.location = (x, y, z + 0.025)
    sol = o.modifiers.new("hollow", "SOLIDIFY"); sol.thickness = -0.004
    # open the top: delete the top face
    bm = bmesh.new(); bm.from_mesh(me)
    top = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=top, context='FACES'); bm.to_mesh(me); bm.free()
    me.materials.append(m)
    return o
