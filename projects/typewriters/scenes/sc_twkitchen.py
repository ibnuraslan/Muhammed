"""A KITCHEN, used twice (dramatization; unnamed figures):
  variant "home"  a Maryland kitchen at night, July 1984: warm pendant light, dark window. A man sits silent; his wife pours coffee.
  variant "safe"  a safe-house kitchen, cool daylight through blinds: a defector talks to two officers, a tape recorder turning.

Ch2 6A  silent    he sits at the table, saying nothing; she pours coffee at the counter
Ch2 6B  wide      wide: the two of them in the warm kitchen, the night window behind
Ch4 4A  talk      an unnamed man talks at the table to two officers (safe variant)
Ch4 4B  reels     the tape recorder's reels turn between them (safe variant)
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp

EXPOSURE = 0.0
DUR = {"silent": 5.0, "wide": 4.5, "talk": 5.0, "reels": 4.5, "family": 5.0, "post": 5.0}
VARIANT_FOR = {"silent": "home", "wide": "home", "talk": "safe", "reels": "safe", "family": "moscow", "post": "post"}
TABLE = Vector((0.0, 0.2, 0.0))


def reel_deck(name):
    """Portable reel-to-reel recorder: grey case, two reels (spinning), a tape path, VU meters."""
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    case = pbr("DeckCase", (0.35, 0.36, 0.34), 0.45, 0.3); dark = pbr("DeckDark", (0.03, 0.03, 0.035), 0.4)
    for o in (box("Case", (0, 0, 0.06), (0.42, 0.34, 0.12), case, bevel=0.01), box("Plate", (0, 0, 0.121), (0.4, 0.32, 0.004), dark),
              box("Meter", (0.1, -0.13, 0.125), (0.07, 0.03, 0.006), pbr("VU", (0.85, 0.75, 0.45), 0.3, 0.0, **{'Emission Color': (1, 0.8, 0.4, 1), 'Emission Strength': 0.6}))):
        o.parent = r
    reels = []
    for x in (-0.1, 0.1):
        hub = bpy.data.objects.new("Reel", None); bpy.context.collection.objects.link(hub); hub.parent = r; hub.location = (x, 0.03, 0.135)
        for o in (cyl("Flange", (0, 0, 0), 0.085, 0.004, pbr("ReelPlastic", (0.6, 0.62, 0.65), 0.2, 0.0, **{'Transmission Weight': 0.4}), verts=32),
                  cyl("TapePack", (0, 0, 0.004), 0.06 if x < 0 else 0.045, 0.006, pbr("Tape", (0.12, 0.07, 0.04), 0.4), verts=32)):
            o.parent = hub
        for k in range(3):
            b = box("Spoke", (0.03 * math.cos(k * 2.09), 0.03 * math.sin(k * 2.09), 0.008), (0.05, 0.008, 0.004), dark, rot=(0, 0, k * 2.09)); b.parent = hub
        reels.append(hub)
    return r, reels


def build(variant="home"):
    c = {"variant": variant}
    home = variant in ("home", "moscow", "post")
    moscow = variant == "moscow"
    if home:
        world_flat((0.004, 0.006, 0.012), 1.0)
    else:
        w = world_sky(sun_elev_deg=30, sun_rot_deg=200, strength=0.5, tint=(0.85, 0.9, 1.0)); w.node_tree.nodes["Sky Texture"].sun_disc = False
    # room x -2.5..2.5, y -2.5..2.5, h 2.5
    box("Floor", (0, 0, -0.01), (5, 5, 0.02), ph.texture("old_linoleum_flooring_01" if home else "floor_tiles_08", scale=0.6, name="KitFloor",
                                                       tint=(0.8, 0.72, 0.6) if home else (0.7, 0.72, 0.7)))
    wall = ph.texture("painted_plaster_wall", scale=0.5, name="KitWall", tint=(0.85, 0.78, 0.62) if home else (0.75, 0.78, 0.76))
    for (x, y, sx, sy) in ((0, -2.55, 5, 0.1), (-2.55, 0, 0.1, 5), (2.55, 0, 0.1, 5)):
        box("KWall", (x, y, 1.25), (sx, sy, 2.5), wall)
    box("Ceiling", (0, 0, 2.52), (5, 5, 0.04), wall)
    # back wall (+Y) with a window over the sink
    for x, w_ in ((-1.75, 1.5), (1.75, 1.5)):
        box("KWallB", (x, 2.55, 1.25), (w_, 0.1, 2.5), wall)
    box("KWallBlow", (0, 2.55, 0.5), (2.0, 0.1, 1.0), wall); box("KWallBhigh", (0, 2.55, 2.25), (2.0, 0.1, 0.5), wall)
    box("KGlass", (0, 2.57, 1.5), (2.0, 0.01, 1.0), glass("KGlassM", (0.9, 0.93, 0.95)))
    box("KSash", (0, 2.55, 1.5), (0.04, 0.06, 1.0), pbr("KSashM", (0.85, 0.83, 0.78), 0.5))
    twp.venetian(0, 2.48, 1.02, 1.95, 2.0, "x", pbr("KBlind", (0.8, 0.78, 0.72), 0.5), tilt=-65 if not home else -20)
    # counters with cabinet fronts (scanned wood textures), sink, kettle, coffee pot
    wood = ph.texture("kitchen_wood", scale=1.0, name="KitWood", tint=(0.9, 0.85, 0.78))
    top = ph.texture("marble_01", scale=0.8, name="KitTop", tint=(0.8, 0.8, 0.78))
    box("Counter", (0, 2.2, 0.45), (4.9, 0.6, 0.9), wood); box("CounterTop", (0, 2.2, 0.92), (5.0, 0.65, 0.04), top)
    box("CounterL", (-2.2, 0.8, 0.45), (0.6, 2.2, 0.9), wood); box("CounterLTop", (-2.2, 0.8, 0.92), (0.65, 2.2, 0.04), top)
    box("Upper", (-1.6, 2.35, 1.95), (1.6, 0.35, 0.7), wood); box("UpperR", (1.6, 2.35, 1.95), (1.6, 0.35, 0.7), wood)
    box("Sink", (0, 2.2, 0.9), (0.7, 0.45, 0.06), pbr("SinkSteel", (0.6, 0.6, 0.62), 0.25, 1.0))
    ph.model("vintage_electric_kettle", loc=(1.3, 2.15, 0.94), rot_z=math.pi)
    ph.model("jug_01", loc=(-1.4, 2.1, 0.94), rot_z=0.3)
    ph.model("wooden_cutting_board", loc=(-2.2, 1.2, 0.94), rot_z=1.6)
    if variant == "home":
        ph.model("vintage_microwave", loc=(-2.2, 1.2, 0.94), rot_z=-math.pi / 2)
    elif variant == "safe":
        ph.model("Television_01", loc=(-2.2, 0.3, 0.94), rot_z=math.pi / 2, scale=0.7)
    ph.model("vintage_telephone_wall_clock", loc=(2.49, 0.9, 1.4), rot_z=math.pi / 2)
    ph.model("potted_plant_04", loc=(0.8, 2.25, 0.94), scale=0.5)
    # the table and chairs
    ph.model("WoodenTable_02" if False else "dining_table", loc=TABLE, rot_z=0.0, scale=0.55)
    for k, (dx, dy, rz) in enumerate(((0, -0.62, 0.0), (0, 0.62, math.pi), (-0.85, 0, -math.pi / 2), (0.85, 0, math.pi / 2))):
        ph.model("dining_chair_02", loc=(TABLE.x + dx, TABLE.y + dy, 0), rot_z=rz)
    for k in range(2):
        ph.model("tea_set_01", loc=(TABLE.x - 0.15 + 0.3 * k, TABLE.y + 0.05, 0.48), rot_z=k, scale=0.45) if k == 0 else None
    mug_m = pbr("Mug", (0.75, 0.72, 0.65), 0.25)
    c["mugs"] = [cyl("Mug", (TABLE.x + 0.15, TABLE.y - 0.25, 0.53), 0.04, 0.09, mug_m, verts=24), cyl("Mug2", (TABLE.x - 0.25, TABLE.y + 0.2, 0.53), 0.04, 0.09, mug_m, verts=24)]
    pot = join([cyl("PotBody", (0, 0, 0.09), 0.065, 0.18, pbr("PotGlass", (0.15, 0.08, 0.04), 0.1, 0.0, **{'Transmission Weight': 0.3}), verts=24),
                cyl("PotTop", (0, 0, 0.2), 0.05, 0.04, pbr("PotBlack", (0.02, 0.02, 0.02), 0.4), verts=24),
                box("PotHandle", (0.08, 0, 0.12), (0.02, 0.02, 0.12), pbr("PotBlack2", (0.02, 0.02, 0.02), 0.4))], "CoffeePot")
    c["pot"] = pot
    # light
    if home:
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.22, radius2=0.06, depth=0.18, location=(TABLE.x, TABLE.y, 1.8))
        shade = bpy.context.active_object; shade.data.materials.append(pbr("Shade", (0.55, 0.45, 0.3), 0.6, 0.0, **{'Emission Color': (1, 0.7, 0.4, 1), 'Emission Strength': 0.6}))
        cyl("Cord", (TABLE.x, TABLE.y, 2.2), 0.004, 0.6, pbr("CordM", (0.05, 0.05, 0.05), 0.5), verts=6)
        pl = bpy.data.lights.new("Pendant", 'SPOT'); pl.energy = 120; pl.spot_size = math.radians(120); pl.spot_blend = 0.8; pl.color = (1.0, 0.72, 0.42)
        po = bpy.data.objects.new("Pendant", pl); bpy.context.collection.objects.link(po); po.location = (TABLE.x, TABLE.y, 1.72)
        amb = area_light((0, 0, 2.4), (0, 0, 0), 3.0, 10, (1.0, 0.75, 0.5)); amb.visible_camera = False
        nightw = area_light((0, 3.4, 1.5), (math.radians(90), 0, 0), 2.0, 6, (0.3, 0.4, 0.8)); point_at(nightw, (0, 0, 0.8)); nightw.visible_camera = False
        bl = bpy.data.lights.new("Street", 'POINT'); bl.energy = 600; bl.color = (1.0, 0.6, 0.3)
        bo = bpy.data.objects.new("Street", bl); bpy.context.collection.objects.link(bo); bo.location = (3, 9, 4)
    else:
        sn = bpy.data.lights.new("Sun", 'SUN'); sn.energy = 2.5; sn.color = (1.0, 0.95, 0.88); sn.angle = math.radians(2)
        so = bpy.data.objects.new("Sun", sn); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(-50), math.radians(10), 0)
        pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 2.0; pt.size_y = 1.0; pt.cycles.is_portal = True
        po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (0, 2.6, 1.5); po.rotation_euler = (math.radians(-90), 0, 0)
        fill = area_light((0, -2.0, 2.3), (0, 0, 0), 2.0, 90, (0.9, 0.93, 1.0)); point_at(fill, TABLE + Vector((0, 0, 0.8))); fill.visible_camera = False
        tl = area_light((TABLE.x + 0.4, TABLE.y - 0.6, 1.3), (0, 0, 0), 0.5, 12, (1.0, 0.92, 0.8)); point_at(tl, TABLE + Vector((0.15, 0, 0.5))); tl.visible_camera = False
        deck, reels = reel_deck("Deck"); deck.location = TABLE + Vector((0.15, -0.05, 0.475)); deck.rotation_euler = (0, 0, 0.2)
        c["reels"] = reels
        ph.model("office_notepads", loc=TABLE + Vector((-0.3, -0.2, 0.48)), scale=0.35)
        box("Outside", (0, 14, 4), (30, 1, 10), ph.texture("brick_wall_02", scale=0.3, name="KitOut"))
    # people
    P = {}
    if variant == "post":                         # a Soviet listening post in a flat: blinds shut, receivers on the table
        for k in range(3):
            ph.model("vintage_radio_transceiver", loc=(TABLE.x - 0.3 + 0.0 * k, TABLE.y + 0.25, 0.48 + k * 0.0) if k == 0 else (TABLE.x + 0.35, TABLE.y + 0.3, 0.48 + (k - 1) * 0.43), rot_z=math.pi)
        deck, reels = reel_deck("PostDeck"); deck.location = TABLE + Vector((0.0, -0.15, 0.475)); c["reels"] = reels
        dial = pbr("DialGlow", (0.5, 0.35, 0.1), 0.3, 0.0, **{'Emission Color': (1.0, 0.7, 0.3, 1), 'Emission Strength': 1.5})
        for k in range(3):
            box("Dial", (TABLE.x - 0.3 + 0.12 * k, TABLE.y + 0.1, 0.62), (0.06, 0.005, 0.03), dial)
        c["switch"] = box("Switch", (TABLE.x + 0.2, TABLE.y - 0.3, 0.52), (0.02, 0.04, 0.015), pbr("SwitchM", (0.6, 0.6, 0.62), 0.3, 1.0))
        P["op"] = twp.person("Operator", 1.0, 38, "male_casualsuit05", "short01", hv=0.3, cval=0.5, hue=0.3, sat=0.2)
        c["P"] = P
        animate(c, 0.0, "post")
        return c
    if moscow:                                    # a Moscow flat: the family watches the television on the counter
        tv, _ = ph.model("Television_01", loc=(-2.2, 0.3, 0.94), rot_z=math.pi / 2, scale=0.75)
        scr = pbr("TVScreen", (0.02, 0.02, 0.02), 0.2, 0.0, **{'Emission Color': (0.55, 0.65, 0.8, 1), 'Emission Strength': 2.0})
        d = scr.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].driver_add("default_value").driver
        d.type = 'SCRIPTED'; d.expression = "2.0 + 0.4 * sin(frame * 0.7) - (1.6 if 60 < frame < 66 else 0)"      # the picture ripples once
        box("TVFace", (-1.98, 0.3, 1.13), (0.01, 0.34, 0.26), scr)
        tvl = area_light((-1.8, 0.3, 1.15), (0, math.radians(90), 0), 0.35, 8, (0.6, 0.7, 0.9)); tvl.visible_camera = False
        d2 = tvl.data.driver_add("energy").driver; d2.type = 'SCRIPTED'; d2.expression = "8 + 2 * sin(frame * 0.7) - (6 if 60 < frame < 66 else 0)"
        P["dad"] = twp.person("Dad", 1.0, 45, "male_casualsuit05", "short04", hv=0.4, cval=0.5, hue=0.1, sat=0.2)
        P["mum"] = twp.person("Mum", 0.0, 42, "female_elegantsuit01", "bob02", hv=0.35, cval=0.6, hue=0.0, sat=0.3)
        P["kid"] = twp.person("Kid", 1.0, 13, "male_casualsuit02", "short01", hv=0.3, cval=0.55, hue=0.6, sat=0.3, height=0.2)
        c["P"] = P
        animate(c, 0.0, "family")
        return c
    if home:
        P["man"] = twp.person("Husband", 1.0, 40, "male_casualsuit02", "short02", hv=0.3, cval=0.55, hue=0.55, sat=0.2)
        P["wife"] = twp.person("Wife", 0.0, 38, "female_elegantsuit01", "long01", hv=0.3, cval=0.6, hue=0.08, sat=0.3)
    else:
        P["defector"] = twp.person("Defector", 1.0, 50, "male_casualsuit04", "short04", hv=0.55, cval=0.45, hue=0.1, sat=0.2)
        P["offA"] = twp.person("OfficerA", 1.0, 42, "male_elegantsuit01", "short03", hv=0.25, cval=0.45, hue=0.6, sat=0.15)
        P["offB"] = twp.person("OfficerB", 0.0, 36, "female_elegantsuit01", "bob01", hv=0.3, cval=0.55, hue=0.55, sat=0.25)
    c["P"] = P
    animate(c, 0.0, "silent" if home else "talk")
    return c


def animate(c, sec, shot):
    from human import reach, fingers_curl
    P = c["P"]
    if c["variant"] == "post":
        op = P["op"]
        twp.seat(op, (TABLE.x, TABLE.y - 0.66, 0), math.pi, lean=14)
        flick = ease(min(1.0, max(0.0, (sec - 2.0) / 0.5)))
        sw = c["switch"]; sw.rotation_euler = (0, math.radians(30) * (1 if flick > 0.5 else -1), 0)
        reach(op, "R", sw.location + Vector((0.04, -0.06, 0.05 - 0.02 * flick)), Vector((0.6, -0.3, -0.7)), Vector((0, 1, -0.3)))
        reach(op, "L", TABLE + Vector((-0.2, -0.25, 0.52)), Vector((-0.6, -0.3, -0.7)), Vector((0, 1, -0.2)))
        fingers_curl(op, 40, thumb=20); op.rot("head", (1, 0, 0), 12)
        spin = 3.0 * (1 - flick) + 0.0
        ang = 3.0 * min(sec, 2.0) + 3.0 * max(0.0, sec - 2.0) * (1 - 0.5 * min(1.0, (sec - 2.0) / 1.5)) if sec > 2.0 else 3.0 * sec
        for k, r in enumerate(c["reels"]):
            r.rotation_euler = (0, 0, -ang * (0.8 if k else 1.0))
        bpy.context.view_layer.update()
        return
    if c["variant"] == "moscow":
        for nm, (x, y), lean in (("dad", (TABLE.x + 0.35, TABLE.y - 0.66), 8), ("mum", (TABLE.x - 0.35, TABLE.y - 0.62), 10), ("kid", (TABLE.x + 0.62, TABLE.y + 0.0), 14)):
            h = P[nm]; d = Vector((-1.98, 0.3, 0)) - Vector((x, y, 0))
            twp.seat(h, (x, y, 0), math.atan2(d.x, -d.y), lean=lean)
            h.rot("head", (0, 0, 1), 2 * math.sin(sec * 0.5 + x))
        bpy.context.view_layer.update()
        return
    if c["variant"] == "home":
        m, w = P["man"], P["wife"]
        twp.seat(m, (TABLE.x, TABLE.y - 0.66, 0), math.pi, lean=22)            # faces +Y over the table, head low
        reach(m, "L", TABLE + Vector((-0.08, -0.22, 0.52)), Vector((-0.6, -0.4, -0.6)), Vector((0.3, 1, -0.2)))
        reach(m, "R", TABLE + Vector((0.12, -0.25, 0.52)), Vector((0.6, -0.4, -0.6)), Vector((-0.2, 1, -0.2)))
        fingers_curl(m, 40, thumb=20)
        m.rot("head", (1, 0, 0), 18 + 2 * math.sin(sec * 0.5))
        twp.stand(w, (1.3, 1.55, 0), math.radians(160))                         # at the counter, turning to the table with the pot
        pour = ease(min(1.0, max(0.0, (sec - 1.2) / 1.2)))
        pot = c["pot"]
        tgt = c["mugs"][1].location + Vector((0.1, 0.05, 0.2))
        hold = w.bone_head("upperarm01.R") + Vector((-0.1, -0.3, -0.35))
        pot.location = hold.lerp(tgt, pour) if shot == "silent" else hold
        pot.rotation_euler = (0, math.radians(-45) * pour * (shot == "silent"), math.radians(200))
        reach(w, "R", pot.location + Vector((0.09, 0, 0.1)), Vector((0.5, 0.3, -0.7)), Vector((0, -1, 0)))
        fingers_curl(w, 50, thumb=25)
        w.rot("head", (1, 0, 0), 10)
    else:
        d, a, b = P["defector"], P["offA"], P["offB"]
        twp.seat(d, (TABLE.x, TABLE.y + 0.66, 0), 0.0, lean=12)
        twp.seat(a, (TABLE.x - 0.9, TABLE.y, 0), -math.pi / 2, lean=10)
        twp.seat(b, (TABLE.x + 0.9, TABLE.y, 0), math.pi / 2, lean=14)
        g = math.sin(sec * 2.1)
        reach(d, "R", TABLE + Vector((0.2 + 0.05 * g, 0.3, 0.62 + 0.05 * abs(g))), Vector((0.6, 0.3, -0.7)), Vector((0, -1, 0.2)))
        reach(d, "L", TABLE + Vector((-0.2, 0.32, 0.52)), Vector((-0.6, 0.3, -0.7)), Vector((0, -1, -0.2)))
        d.rot("head", (0, 0, 1), 12 * math.sin(sec * 0.7))
        reach(b, "R", TABLE + Vector((0.45, -0.15, 0.52)), Vector((0.3, -0.6, -0.7)), Vector((-1, 0, -0.3)))
        for h in (a, b):
            h.rot("head", (1, 0, 0), 6)
        for k, r in enumerate(c["reels"]):
            r.rotation_euler = (0, 0, -sec * (2.4 if k else 3.2))
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_silent(c, t):
    e = ease(t)
    return (TABLE + Vector((0.85, 1.35, 1.35)).lerp(Vector((0.7, 1.15, 1.3)), e), TABLE + Vector((0.0, -0.6, 0.95)), 35)


def cam_wide(c, t):
    e = ease(t)
    return (Vector((-1.9, -2.2, 1.7)).lerp(Vector((-1.7, -2.0, 1.65)), e), Vector((0.4, 1.2, 1.0)), 26)


def cam_talk(c, t):
    e = ease(t)
    return (TABLE + Vector((-1.75, -1.6, 1.45)).lerp(Vector((-1.5, -1.35, 1.42)), e), TABLE + Vector((0.1, 0.35, 0.95)), 30)


def cam_reels(c, t):
    e = ease(t); r = c["reels"][0].matrix_world.translation
    return (r + Vector((0.55, -0.7, 0.35)).lerp(Vector((0.42, -0.55, 0.28)), e), r + Vector((0.1, 0.0, 0.0)), 40)


MOVES = {
    "post": dict(kind="anim", dof=2.6, cam=lambda c, t: (TABLE + Vector((1.3, -1.5, 1.35)).lerp(Vector((1.1, -1.25, 1.3)), ease(t)), TABLE + Vector((0.0, -0.2, 0.75)), 32),
                 focus=lambda c, t: TABLE + Vector((0.2, -0.3, 0.6)), anim=anim("post")),
    "family": dict(kind="anim", dof=None, cam=lambda c, t: (Vector((1.6, -1.9, 1.5)).lerp(Vector((1.35, -1.65, 1.45)), ease(t)), Vector((-1.2, 0.3, 0.95)), 28),
                   anim=lambda c, t: (animate(c, t * DUR["family"], "family"), bpy.context.scene.frame_set(int(t * DUR["family"] * 24) + 1))),
    "silent": dict(kind="anim", dof=2.4, cam=cam_silent, focus=lambda c, t: c["P"]["man"].bone_head("head"), anim=anim("silent")),
    "wide": dict(kind="anim", dof=None, cam=cam_wide, anim=anim("wide")),
    "talk": dict(kind="anim", dof=2.8, cam=cam_talk, focus=lambda c, t: c["P"]["defector"].bone_head("head"), anim=anim("talk")),
    "reels": dict(kind="anim", dof=1.6, cam=cam_reels, focus=lambda c, t: c["reels"][0].matrix_world.translation, anim=anim("reels")),
}
