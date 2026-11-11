"""CLOSED TOWN, Saratov region (dramatization; a generic closed town, no real institute shown). Variants:
  checkpoint : winter day; the guard lifts the striped barrier for a bus (Ch2 5A)
  institute  : a long institute corridor, one fluorescent tube flickering; a scientist (unnamed) walks away (Ch2 5B)
  kitchen    : years later, night: a man (from behind) on the phone at a dark kitchen window (Ch3 9A)
  blocks     : snow falling over five-storey blocks at night; one window lit (Ch3 9B)"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import *
import ph
from pbkit import joinm, masonry_facade, precip_curtains, soviet_car
from pbpeople import person, stand, walk_at, nod, look, hand_to, hide, fwd, recolor, medic
from sc_bankoffice import retint, plastic, telephone, coiled_cord, handset_at_ear, place_handset
from sc_hospital import two_tone, fluorescents

EXPOSURE = 0.8
BOUNCES = 6
DUR = {"checkpoint": 6.0, "institute": 6.0, "kitchen": 6.5, "blocks": 6.5}
VARIANT_FOR = {k: k for k in DUR}
rng = np.random.default_rng(31)


def snow_ground(name, size, loc=(0, 0, 0)):
    m = pbr(name + "M", (0.82, 0.84, 0.88), 0.55, 0.0, **{'Subsurface Weight': 0.25})
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=80, size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1); o.data.materials.append(m)
    tx = bpy.data.textures.new(name + "Drift", 'CLOUDS'); tx.noise_scale = 3.0
    d = o.modifiers.new("drift", 'DISPLACE'); d.texture = tx; d.strength = 0.25; d.texture_coords = 'GLOBAL'
    return o


def forest(xr, yr, n, seed=2):
    r = np.random.default_rng(seed)
    for k in range(n):
        ph.model("pine_tree_01" if k % 2 else "fir_tree_01", loc=(r.uniform(*xr), r.uniform(*yr), 0), rot_z=r.uniform(0, 6.28), scale=r.uniform(0.6, 0.9))


def bus():
    """A PAZ-style small bus: cream and red, rounded box on four wheels."""
    body = pbr("BusCream", (0.72, 0.68, 0.55), 0.4, 0.1, **{'Coat Weight': 0.5})
    red = pbr("BusRed", (0.5, 0.12, 0.08), 0.4)
    glass_m = pbr("BusGlass", (0.03, 0.035, 0.04), 0.05, 0.0, **{'Coat Weight': 1.0})
    tyre = pbr("BusTyre", (0.02, 0.02, 0.02), 0.85)
    parts = [box("BBody", (0, 0, 1.45), (7.0, 2.4, 2.3), body, bevel=0.3), box("BBand", (0, 0, 0.9), (7.02, 2.42, 0.4), red),
             box("BWin", (0.0, 0, 1.85), (6.0, 2.42, 0.8), glass_m), box("BWind", (3.51, 0, 1.75), (0.03, 2.1, 1.0), glass_m)]
    for k in range(5):
        parts.append(box("BPil", (-2.4 + k * 1.2, 0, 1.85), (0.1, 2.44, 0.82), body))
    for sx in (-2.3, 2.3):
        for sy in (-1, 1):
            parts.append(cyl("BTyre", (sx, sy * 1.0, 0.45), 0.45, 0.28, tyre, verts=24, rot=(math.radians(90), 0, 0)))
    for sy in (-0.7, 0.7):
        parts.append(cyl("BHead", (3.52, sy, 0.75), 0.1, 0.03, emissive("BusHead", (1.0, 0.92, 0.8), 5), verts=16, rot=(0, math.radians(90), 0)))
    return joinm(parts, "Bus")


def build(variant=None):
    variant = variant or "checkpoint"
    c = {"variant": variant}
    if variant == "checkpoint":
        world_flat((0.62, 0.66, 0.72), 0.9)
        snow_ground("Snow", (200, 200))
        road = pbr("SnowRoad", (0.3, 0.3, 0.32), 0.6); box("Road", (0, 0, 0.03), (200, 7, 0.06), road)
        forest((-60, 60), (12, 50), 40); forest((-60, 60), (-50, -14), 30, seed=4)
        # guard booth, barrier, fence, concrete blocks
        booth = joinm([box("Booth", (0, 0, 1.25), (2.2, 2.0, 2.5), pbr("BoothPaint", (0.45, 0.5, 0.42), 0.6), bevel=0.02),
                       box("BoothRoof", (0, 0, 2.6), (2.6, 2.4, 0.2), pbr("BoothRoofM", (0.25, 0.25, 0.25), 0.7))], "Booth")
        booth.location = (2.0, 5.2, 0)
        box("BoothWin", (2.0, 4.19, 1.6), (1.4, 0.02, 0.8), emissive("BoothWinLight", (1.0, 0.85, 0.6), 1.2))
        piv = bpy.data.objects.new("BarrierPivot", None); bpy.context.collection.objects.link(piv); piv.location = (0.8, 3.8, 1.0)
        stripe = bpy.data.materials.new("Stripes"); stripe.use_nodes = True
        N = stripe.node_tree.nodes; L = stripe.node_tree.links; p = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 3
        L.new(tc.outputs['Object'], wv.inputs['Vector']); ck = N.new("ShaderNodeMath"); ck.operation = 'GREATER_THAN'; ck.inputs[1].default_value = 0.5
        L.new(wv.outputs['Fac'], ck.inputs[0]); mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(ck.outputs[0], mx.inputs['Factor'])
        mx.inputs[6].default_value = (0.75, 0.75, 0.73, 1); mx.inputs[7].default_value = (0.55, 0.05, 0.04, 1); L.new(mx.outputs[2], p.inputs['Base Color'])
        arm = cyl("BarrierArm", (0, -3.6, 0), 0.06, 7.0, stripe, verts=16, rot=(math.radians(90), 0, 0)); arm.parent = piv
        box("BarrierPost", (0.8, 3.8, 0.5), (0.3, 0.3, 1.0), pbr("PostGrey", (0.4, 0.4, 0.4), 0.6))
        c["barrier"] = piv
        for k in range(4):
            ph.model("concrete_road_barrier", loc=(-2.5 - k * 1.6, 4.5, 0), rot_z=0.0)
        for k in range(6):
            r, _ = ph.model("modular_chainlink_fence", loc=(-8 - k * 8.1, 6.0, 0), rot_z=0.0)
            r2, _ = ph.model("modular_chainlink_fence", loc=(10 + k * 8.1, 6.0, 0), rot_z=0.0)
        ph.model("security_light", loc=(2.0, 4.2, 2.5), rot_z=0.0)
        c["bus"] = bus()
        c["guard"] = person("Guard", 1.0, 30, "male_casualsuit05", "short02", cval=0.25, hue=0.3, sat=0.6)
        recolor(c["guard"], "casualsuit05", (0.2, 0.24, 0.16))
        c["snowfall"] = precip_curtains("snow", x_range=(-30, 30), ys=(-12, -6, -1, 3, 8))
    elif variant == "institute":
        world_flat((0.2, 0.22, 0.25), 0.5)
        W, L_, H = 2.4, 30.0, 3.0
        walls = two_tone("InstWalls", low=(0.3, 0.38, 0.36), high=(0.7, 0.7, 0.66), dado=1.4)
        box("Floor", (0, 0, -0.01), (W, L_, 0.02), ph.texture("old_linoleum_flooring_01", scale=0.6)); box("Ceil", (0, 0, H), (W, L_, 0.04), pbr("ICeil", (0.65, 0.65, 0.62), 0.9))
        for sx in (-1, 1):
            box("IWall", (sx * (W / 2 + 0.05), 0, H / 2), (0.1, L_, H), walls)
            for k in range(8):
                y = -13 + k * 3.6 + (1.0 if sx > 0 else 0)
                box("IDoor", (sx * (W / 2 - 0.02), y, 1.0), (0.04, 0.9, 2.0), pbr("IDoorM", (0.45, 0.32, 0.2), 0.5))
                box("IPlate", (sx * (W / 2 - 0.045), y + 0.6, 1.55), (0.01, 0.2, 0.12), pbr("IPlateM", (0.6, 0.6, 0.6), 0.3, 0.8))
        box("IEnd", (0, L_ / 2, H / 2), (W, 0.1, H), walls); box("IEnd2", (0, -L_ / 2, H / 2), (W, 0.1, H), walls)
        lights = []
        for k, y in enumerate(range(-12, 15, 4)):
            ph.model("mounted_fluorescent_lights", loc=(0, y, H - 0.02), rot_z=math.radians(90))
            l = area_light((0, y, H - 0.12), (0, 0, 0), 1.0, 22, (0.9, 0.97, 1.0)); l.visible_camera = False
            if k == 3:                                    # this one flickers (frame driver)
                d = l.data.driver_add("energy").driver; d.type = 'SCRIPTED'
                d.expression = "22 * (0.15 if (frame % 37) in (3, 4, 9, 21, 22) else 1)"
        c["sci"] = medic("Scientist", 1.0, 40, "short04")
    elif variant == "kitchen":
        world_flat((0.02, 0.03, 0.06), 1.0)
        walls = pbr("KitchenWall", (0.55, 0.55, 0.5), 0.7)
        box("KFloor", (0, 0, -0.01), (3.5, 3.0, 0.02), ph.texture("old_linoleum_flooring_01", scale=0.6)); box("KCeil", (0, 0, 2.6), (3.5, 3.0, 0.04), pbr("KC", (0.6, 0.6, 0.58), 0.9))
        for (x0, x1) in ((-1.75, -0.6), (0.6, 1.75)):
            box("KWallBack", ((x0 + x1) / 2, 1.5, 1.3), (x1 - x0, 0.1, 2.6), walls)
        box("KUnder", (0, 1.5, 0.45), (1.2, 0.1, 0.9), walls); box("KOver", (0, 1.5, 2.35), (1.2, 0.1, 0.5), walls)
        box("KWinGlass", (0, 1.53, 1.5), (1.2, 0.01, 1.2), glass("KGlass", (0.9, 0.93, 0.95), 0.02))
        box("KWinBar", (0, 1.5, 1.5), (0.04, 0.06, 1.2), pbr("KBar", (0.8, 0.8, 0.76), 0.5))
        box("KSill", (0, 1.4, 0.9), (1.4, 0.25, 0.04), pbr("KSillM", (0.8, 0.8, 0.76), 0.5))
        for sx in (-1, 1):
            box("KWallSide", (sx * 1.8, 0, 1.3), (0.1, 3.0, 2.6), walls)
        # outside: snowy blocks at night with a few lit windows, snow falling past the window
        fac = masonry_facade("KOut", (0.5, 0.5, 0.48), 2.8, 2.2, 1.1, 1.3, 0.12, lit_strength=1.6)
        box("KOutside", (0, 40, 10), (60, 1, 30), fac)
        snow_ground("KSnowGround", (80, 60), (0, 30, -12))
        precip_curtains("snow", x_range=(-6, 6), ys=(2.5, 4.0, 7.0), top=8.0)
        moon = area_light((0, 4, 3), (math.radians(110), 0, 0), 4, 40, (0.45, 0.55, 0.85)); moon.visible_camera = False
        r, tbl = ph.model("WoodenTable_02" if False else "small_wooden_table_01", loc=(0.9, 0.7, 0), rot_z=0.0)
        r, kt = ph.model("vintage_electric_kettle", loc=(0.9, 0.75, 0.75), rot_z=1.0)
        lamp = bpy.data.lights.new("KLamp", 'POINT'); lamp.energy = 15; lamp.color = (1.0, 0.75, 0.45)
        lo = bpy.data.objects.new("KLamp", lamp); bpy.context.collection.objects.link(lo); lo.location = (-1.3, -0.8, 1.2)
        root, hs, base = telephone(); root.location = (0.95, 0.5, 0.75); root.rotation_euler = (0, 0, math.radians(200))
        bpy.context.view_layer.update()
        c.update(phone=root, handset=hs)
        c["man"] = person("Caller", 1.0, 70, "male_casualsuit05", "short04", cval=0.15, hv=0.7, sat=0.2)
    else:  # blocks
        world_flat((0.03, 0.045, 0.08), 1.0)
        snow_ground("BSnow", (200, 200))
        k = 0
        for (x, y, rz) in ((-18, 20, 0.0), (18, 22, 0.0), (0, 48, 0.0), (-40, 40, 0.3), (38, 42, -0.3)):
            lit = 0.0 if k else 0.0
            fac = masonry_facade(f"Block{k}", (0.55, 0.55, 0.52), 2.8, 3.2, 1.3, 1.4, 0.02, lit_strength=1.4)
            o = box(f"Block{k}", (x, y, 7.0), (30, 12, 14), fac); o.rotation_euler = (0, 0, rz)
            box(f"Roof{k}", (x, y, 14.1), (30.2, 12.2, 0.3), pbr("RoofSnow", (0.75, 0.78, 0.82), 0.6)).rotation_euler = (0, 0, rz)
            k += 1
        # the one lit window, warm, on the near block
        box("LitWindow", (-12.6, 13.98, 7.0), (1.2, 0.02, 1.3), emissive("LitWin", (1.0, 0.75, 0.45), 6.0))
        forest((-60, 60), (55, 90), 30); forest((-40, -25), (0, 15), 4, seed=6)
        for x in (-8, 8):
            ph.model("street_lamp_01", loc=(x, 8, 0))
            sl = bpy.data.lights.new("BLamp", 'POINT'); sl.energy = 220; sl.color = (1.0, 0.7, 0.4)
            o = bpy.data.objects.new("BLamp", sl); bpy.context.collection.objects.link(o); o.location = (x, 8, 3.75)
        precip_curtains("snow", x_range=(-30, 30), ys=(-6, -2, 3, 9))
        moon = sun(25, 200, 0.25, (0.55, 0.65, 1.0), 3)
        car = soviet_car("BlockLada", (0.35, 0.36, 0.38), kind="lada"); car.location = (4, 10, 0.12)
        box("CarSnow", (4, 10, 1.48), (1.5, 1.2, 0.1), pbr("CarSnowM", (0.8, 0.82, 0.86), 0.6))
    animate(c, 0.0, variant)
    return c


def animate(c, sec, move):
    v = c["variant"]
    if v == "checkpoint":
        up = ease(min(1.0, max(0.0, (sec - 0.8) / 1.8)))
        c["barrier"].rotation_euler = (math.radians(80 * up), 0, 0)
        x = -30 + 6.0 * max(0.0, sec - 1.2) if sec > 1.2 else -30
        x = -30 + min(28.0, 7.0 * max(0.0, sec - 1.0))
        c["bus"].location = (x, 1.6, 0.05); c["bus"].rotation_euler = (0, 0, 0)
        g = c["guard"]
        stand(g, (1.4, 4.0, 0.1), math.radians(180 + 30))
        hand_to(g, "R", Vector((0.85, 3.6, 1.0 + 0.2 * up)), curl=60)
        look(g, c["bus"].location + Vector((0, 0, 1.5)), 0.7)
    elif v == "institute":
        s = c["sci"]
        walk_at(s, sec * 0.85, (0.2, -6.0 + 1.0 * sec, 0), math.pi, stride=22, swing=12)     # walks away (+Y)
    elif v == "kitchen":
        m = c["man"]
        stand(m, (0.15, 0.85, 0), math.pi)                                                 # faces +Y, the window
        place_handset(c, handset_at_ear(c, m, 1.0))
        hand_to(m, "L", c["handset"].matrix_world @ Vector((0, -0.01, -0.02)), curl=55)
        nod(m, "head", 4 + 3 * math.sin(sec * 0.5))
        hand_to(m, "R", Vector((0.55, 1.35, 0.95)), hand_dir=Vector((0, 0.5, -0.8)), curl=20)          # hand on the sill
    bpy.context.view_layer.update()


def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


def _anim(move):
    return lambda c, t: animate(c, t * DUR[move], move)


MOVES = {
    "checkpoint": dict(kind="anim", dof=8.0, far=120.0, anim=_anim("checkpoint"), cam=_push((-6.0, -9.0, 1.7), (-4.5, -8.0, 1.75), (0.0, 3.5, 1.8), (0.5, 3.5, 1.8), 30),
                       focus=lambda c, t: Vector((0.8, 3.8, 1.2))),
    "institute": dict(kind="anim", dof=4.0, far=40.0, anim=_anim("institute"), cam=_push((-0.4, -10.5, 1.55), (-0.3, -9.6, 1.55), (0.1, 4.0, 1.3), (0.1, 4.0, 1.3), 30),
                      focus=lambda c, t: Vector((0.2, -6.0 + DUR["institute"] * t, 1.3))),
    "kitchen": dict(kind="anim", dof=3.2, far=30.0, anim=_anim("kitchen"), cam=_push((-1.1, -1.0, 1.55), (-0.95, -0.75, 1.55), (0.2, 1.3, 1.45), (0.15, 1.4, 1.45), 30),
                    focus=lambda c, t: Vector((0.15, 0.85, 1.5))),
    "blocks": dict(kind="anim", dof=0.0, far=200.0, anim=_anim("blocks"), cam=_push((-4.0, -12.0, 2.2), (-5.0, -8.0, 2.4), (-12.0, 14.0, 6.5), (-12.6, 14.0, 7.0), 30),
                   focus=lambda c, t: Vector((-12.6, 14.0, 7.0))),
}
