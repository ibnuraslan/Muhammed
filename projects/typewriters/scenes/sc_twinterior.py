"""EMBASSY INTERIOR, Moscow 1984 (dramatization): a long office corridor with open doors (a typewriter on every desk),
the lift lobby with its floor-indicator lamp, the Marine post on the sixth floor, and the stairwell.

Ch1 4A  count     a man with a clipboard walks the corridor, glancing into each office, counting
Ch1 4B  doors     looking down the corridor of open doors, a typewriter in each room; a clerk crosses far off
Ch1 8B  chat      two staff in the corridor chat by the upgrade notice
Ch1 9A  lift      the lift's indicator lamp dies; two workers carrying a box turn for the stairs
Ch1 10B marine    the Marine at the sixth-floor post watches the alarm panel light up
Ch1 11A landing   two men tilt a teletype round a tight stair landing
Ch1 11B stairs    looking down the stairwell as crates pass floor by floor
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import *
import ph
import twp
import typewriter as T
import machines as MC

EXPOSURE = 0.0
DUR = {"count": 5.0, "doors": 4.5, "chat": 4.5, "lift": 4.5, "marine": 4.5, "landing": 5.0, "stairs": 5.0}
CW, CH = 2.2, 2.8                 # corridor width, ceiling
ROOMS = [-9.0, -5.0, -1.0, 3.0, 7.0]
STAIR_X = -16.0                   # stair core centre (x), floors 3.4 apart


def build(variant=None):
    c = {}
    rng = np.random.default_rng(31)
    world_sky(sun_elev_deg=35, sun_rot_deg=80, strength=0.45, tint=(0.88, 0.92, 1.0)).node_tree.nodes["Sky Texture"].sun_disc = False
    lino = ph.texture("old_linoleum_flooring_01", scale=0.5, name="Lino", tint=(0.55, 0.6, 0.62))
    plaster = ph.texture("painted_plaster_wall", scale=0.5, name="CorrPlaster", tint=(0.8, 0.8, 0.74))
    lower = ph.texture("painted_plaster_wall", scale=0.5, name="CorrDado", tint=(0.42, 0.48, 0.46))
    ceil = ph.texture("ceiling_interior", scale=0.5, name="CorrCeil")
    frame_m = pbr("DoorFrame", (0.3, 0.27, 0.22), 0.5)
    door_m = ph.texture("dark_wood", scale=1.0, name="DoorWood", tint=(0.9, 0.85, 0.8))
    box("Floor", (-2, 0, -0.01), (30, 12, 0.02), lino)
    box("Ceiling", (-2, 0, CH + 0.02), (30, 12, 0.04), ceil)
    # corridor walls with door openings into offices on both sides
    for sy in (-1, 1):
        y = sy * CW / 2
        xs = [-13.0] + sum(([r - 0.55, r + 0.55] for r in ROOMS), []) + [11.0]
        for a, b in zip(xs[0::2], xs[1::2]):
            box("CorrWall", ((a + b) / 2, y + sy * 0.06, 1.0 + 0.4), (b - a, 0.12, CH), plaster)
            box("Dado", ((a + b) / 2, y - sy * 0.005, 0.5), (b - a, 0.01, 1.0), lower)
        for r in ROOMS:
            box("Lintel", (r, y + sy * 0.06, CH - 0.35), (1.1, 0.12, 0.7), plaster)
            for dx in (-0.55, 0.55):
                box("Jamb", (r + dx, y, 1.05), (0.06, 0.16, 2.1), frame_m)
            box("Head", (r, y, 2.12), (1.16, 0.16, 0.06), frame_m)
            leaf = box("DoorLeaf", (0, 0, 0), (0.95, 0.04, 2.05), door_m, bevel=0.005)
            leaf.location = (r - 0.48 + 0.48 * math.cos(math.radians(80)), y + sy * (0.08 + 0.48 * math.sin(math.radians(80))), 1.03)
            leaf.rotation_euler = (0, 0, sy * math.radians(80))
            # the office behind: desk + typewriter by a window with blinds
            ry = sy * (CW / 2 + 1.9)
            yb = sy * (CW / 2 + 3.6)
            box("RoomBackL", (r - 1.35, yb, 1.4), (1.3, 0.1, CH), plaster); box("RoomBackR", (r + 1.65, yb, 1.4), (0.7, 0.1, CH), plaster)
            box("RoomBackLow", (r + 0.3, yb, 0.575), (1.6, 0.1, 1.15), plaster); box("RoomBackHigh", (r + 0.3, yb, 2.6), (1.6, 0.1, 0.5), plaster)
            box("RoomGlass", (r + 0.3, yb, 1.75), (1.6, 0.01, 1.2), glass("WinG", (0.9, 0.93, 0.95)))
            for dx in (-2.0, 2.0):
                box("RoomSide", (r + dx, ry, 1.4), (0.1, 3.6, CH), plaster)
            ph.model("metal_office_desk", loc=(r + 0.3, sy * (CW / 2 + 2.3), 0), rot_z=0 if sy > 0 else math.pi, scale=0.75)
            T.make(f"TWr{int(r)}{sy}", loc=(r + 0.3, sy * (CW / 2 + 2.2), 0.6), rot_z=(math.pi if sy > 0 else 0.0) + rng.uniform(-0.15, 0.15),
                   color=[(0.11, 0.15, 0.2), (0.32, 0.28, 0.22), (0.22, 0.24, 0.2)][int(r) % 3], mechanism=False, glyphs=False, legends=False,
                   text="Memorandum\n" if rng.random() < 0.5 else " ", seed=int(r))
            twp.model_fit("painted_wooden_chair_01", (r + 0.3, sy * (CW / 2 + 1.55), 0), rot_z=(math.pi if sy > 0 else 0) + 0.2, height=0.92)
            ph.model("drawer_cabinet" if r % 2 else "potted_plant_01", loc=(r - 1.5, sy * (CW / 2 + 3.2), 0), rot_z=0 if sy > 0 else math.pi, scale=0.7 if r % 2 else 1.0)
            wl = area_light((r + 0.3, sy * (CW / 2 + 3.5), 1.7), (0, 0, 0), 1.6, 70, (0.9, 0.94, 1.0)); point_at(wl, (r, 0, 0.6))
            wl.data.shape = 'RECTANGLE'; wl.data.size = 1.6; wl.data.size_y = 1.2; wl.visible_camera = False
            twp.venetian(r + 0.3, sy * (CW / 2 + 3.52), 1.2, 2.3, 1.5, "x", pbr("BlindI", (0.72, 0.71, 0.66), 0.5), tilt=-60)
    box("CorrEnd", (11.0, 0, 1.4), (0.1, CW, CH), plaster)
    box("Skirting", (-1, CW / 2 - 0.01, 0.05), (24, 0.02, 0.1), frame_m); box("Skirting", (-1, -CW / 2 + 0.01, 0.05), (24, 0.02, 0.1), frame_m)
    for x in np.arange(-11, 11, 3.0):
        ph.model("mounted_fluorescent_lights", loc=(x, 0, CH), rot_z=0.0)
        l = area_light((x, 0, CH - 0.08), (0, 0, 0), 0.8, 30, (0.9, 0.96, 1.0)); l.visible_camera = False
    # notice board in the corridor between rooms, a wall phone, a radiator
    box("CorrCork", (1.0, CW / 2 - 0.02, 1.5), (1.1, 0.03, 0.8), pbr("Cork", (0.4, 0.29, 0.18), 0.9))
    import sc_twoffice
    nm = bpy.data.materials.new("NoticeC"); nm.use_nodes = True
    t = nm.node_tree.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(sc_twoffice.notice_image(os.path.join(T.GEN, "notice.png")))
    nm.node_tree.links.new(t.outputs[0], nm.node_tree.nodes["Principled BSDF"].inputs['Base Color'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(1.1, CW / 2 - 0.04, 1.55), rotation=(math.radians(90), 0, math.pi))
    o = bpy.context.active_object; o.scale = (0.21, 0.28, 1); o.data.materials.append(nm)
    ph.model("vintage_telephone_wall_clock", loc=(-3.0, CW / 2 - 0.01, 1.35), rot_z=math.pi)
    # ---------------------------------------------------------------- lift lobby (x < -11): lift doors, indicator lamp
    box("LobbyWall", (-13.0, 0, 1.4), (0.1, CW + 2, CH), plaster)
    steel = brushed_metal("LiftSteel", (0.55, 0.56, 0.57), (0.25, 0.4), 0.5)
    box("LiftDoors", (-12.94, 0.0, 1.05), (0.03, 1.1, 2.1), steel)
    box("LiftSeam", (-12.92, 0.0, 1.05), (0.01, 0.01, 2.1), pbr("Seam", (0.02, 0.02, 0.02), 0.5))
    box("LiftFrame", (-12.95, 0.0, 1.1), (0.05, 1.3, 2.25), frame_m)
    lamp_m = pbr("LiftLamp", (0.5, 0.35, 0.15), 0.3, 0.0, **{'Emission Color': (1.0, 0.6, 0.25, 1), 'Emission Strength': 0.0})
    for k in range(8):
        o = cyl(f"FloorLamp{k}", (-12.92, -0.42 + k * 0.12, 2.4), 0.03, 0.02, lamp_m if k == 5 else pbr("LampOff", (0.25, 0.22, 0.18), 0.3), verts=16, rot=(0, math.radians(90), 0))
    d = lamp_m.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].driver_add("default_value").driver
    d.type = 'SCRIPTED'; d.expression = "8 * (1 if frame < 40 else 0) + 3 * (1 if 43 < frame < 46 else 0)"
    c["lift_lamp"] = lamp_m
    # ---------------------------------------------------------------- the Marine post (by the lift lobby): desk, alarm panel
    ph.model("metal_office_desk", loc=(-10.0, -0.55, 0), rot_z=math.pi / 2, scale=0.7)          # in front of the Marine, who faces down the corridor
    panel = box("AlarmPanel", (-11.55, -0.6, 1.25), (0.08, 0.6, 0.4), pbr("PanelGrey", (0.35, 0.37, 0.35), 0.4, 0.3), bevel=0.01)
    pl = pbr("AlarmLamp", (0.3, 0.04, 0.03), 0.3, 0.0, **{'Emission Color': (1.0, 0.12, 0.05, 1), 'Emission Strength': 0.0})
    pg = pbr("AlarmGreen", (0.05, 0.2, 0.06), 0.3, 0.0, **{'Emission Color': (0.3, 1.0, 0.35, 1), 'Emission Strength': 2.0})
    for k in range(6):
        cyl("AlarmLED", (-11.5, -0.82 + k * 0.09, 1.32), 0.016, 0.02, pl if k == 3 else pg, verts=12, rot=(0, math.radians(90), 0))
    d = pl.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].driver_add("default_value").driver
    d.type = 'SCRIPTED'; d.expression = "10 * (1 if frame > 36 and (frame // 6) % 2 == 0 else 0)"
    # wire bundle running up the wall to the ceiling (from the attic)
    cyl("AlarmWire", (-11.56, -0.35, 2.05), 0.012, 1.5, pbr("WireGrey", (0.2, 0.2, 0.2), 0.5), verts=8)
    ph.model("vintage_telephone_wall_clock", loc=(-12.93, -0.9, 1.4), rot_z=-math.pi / 2)
    marine = twp.person("MarineP", 1.0, 23, "male_elegantsuit01", "short01", hv=0.2, cval=0.55, hue=0.12, sat=0.35)
    for o in marine.parts:
        if "elegantsuit" in o.name:
            twp.two_tone(o, 0.74, (0.40, 0.34, 0.21), (0.03, 0.04, 0.09))         # khaki shirt over blue trousers (seated)
    c["cap"] = twp.marine_cap((-9.85, -0.1, 0.555), 2.0)
    c["marine"] = marine
    twp.model_fit("SchoolChair_01", (-10.75, -0.55, 0), rot_z=math.pi / 2, height=0.92)
    c["insignia"] = [box(f"Insignia{k}", (0, 0, -5), (0.018, 0.006, 0.014), pbr("InsigniaGold", (0.75, 0.55, 0.2), 0.3, 1.0)) for k in range(2)]
    # ---------------------------------------------------------------- stairwell (x around STAIR_X), three storeys, open well
    conc = ph.texture("concrete_floor_02", scale=0.5, name="StairConc", tint=(0.75, 0.75, 0.72))
    rail = pbr("StairRail", (0.1, 0.1, 0.1), 0.4, 0.7)
    wood_rail = ph.texture("dark_wood", scale=1.0, name="Handrail")
    X0, W_, D = STAIR_X, 3.0, 6.0
    for sy in (-1, 1):
        box("StairWall", (X0, sy * (W_ / 2 + 0.05), 4.0), (D, 0.1, 13), plaster)
    box("StairWallE", (X0 - D / 2 - 0.05, 0, 4.0), (0.1, W_, 13), plaster)
    c["landings"] = []
    for f in range(-2, 2):
        z = f * 3.4
        box("Landing", (X0 + D / 2 - 0.7, 0, z - 0.1), (1.4, W_, 0.2), conc)         # floor landing (lobby side)
        box("MidLanding", (X0 - D / 2 + 0.7, 0, z + 1.6), (1.4, W_, 0.2), conc)
        for sy, (z0, z1, xa, xb) in ((-1, (z, z + 1.7, X0 + D / 2 - 1.4, X0 - D / 2 + 1.4)), (1, (z + 1.7, z + 3.4, X0 - D / 2 + 1.4, X0 + D / 2 - 1.4))):
            n = 11
            for k in range(n):
                fx = xa + (xb - xa) * (k + 0.5) / n
                fz = z0 + (z1 - z0) * (k + 1) / n
                box("Step", (fx, sy * 0.9, fz - 0.09), (abs(xb - xa) / n + 0.01, 1.1, 0.18), conc)
            # rail along the well side
            mid = Vector(((xa + xb) / 2, 0.0, (z0 + z1) / 2 + 0.95))
            L_ = math.hypot(xb - xa, z1 - z0); ang = math.atan2(z1 - z0, xb - xa)
            cyl("Handrail", (mid.x, sy * 0.32, mid.z), 0.03, L_, wood_rail, verts=10, rot=(0, math.pi / 2 - ang, 0))
            for k in range(8):
                fx = xa + (xb - xa) * (k + 0.5) / 8; fz = z0 + (z1 - z0) * (k + 0.5) / 8
                cyl("Baluster", (fx, sy * 0.32, fz + 0.45), 0.01, 0.95, rail, verts=6)
        if f == 0:
            pass
    box("StairOpening", (X0 + D / 2 + 0.6, 0, 1.4), (1.2, W_, 0.01), plaster).hide_render = True
    for f in range(-2, 2):
        l = area_light((X0, 0, f * 3.4 + 3.1), (0, 0, 0), 0.5, 25, (1.0, 0.85, 0.65)); l.visible_camera = False
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.12, location=(X0 - D / 2 + 0.1, 0, f * 3.4 + 2.4))
        o = bpy.context.active_object; o.scale = (0.5, 1, 1); o.data.materials.append(pbr("Globe", (0.9, 0.88, 0.8), 0.2, 0.0, **{'Emission Color': (1, 0.85, 0.65, 1), 'Emission Strength': 3.0}))
    # props carried in this set
    r, p = MC.teletype("CarryTTY", (0, 0, 0), 0.0, stand=False); c["tty"] = r
    c["box"] = MC.burlap_crate("CarryBox", size=(0.6, 0.45, 0.45), tag=False)
    c["crates"] = [MC.burlap_crate(f"StairCrate{k}", size=(0.7, 0.5, 0.55), tag=False) for k in range(2)]
    cb, _ = ph.model("clipboard"); c["clipboard"] = cb
    # people
    P = {}
    P["counter"] = twp.person("Counter", 1.0, 44, "male_casualsuit01", "short02", hv=0.35, cval=0.5, hue=0.1, sat=0.2)
    P["clerk"] = twp.person("Clerk2", 0.0, 29, "female_elegantsuit01", "long01", hv=0.3, cval=0.55, hue=0.55, sat=0.25)
    P["staffA"] = twp.person("StaffA", 0.0, 48, "female_elegantsuit01", "bob01", hv=0.5, cval=0.55, hue=0.08, sat=0.25)
    P["staffB"] = twp.person("StaffB", 1.0, 36, "male_casualsuit03", "short03", hv=0.25, cval=0.5, hue=0.58, sat=0.2)
    P["workA"] = twp.person("WorkA", 1.0, 31, "male_worksuit01", "short01", hv=0.25, cval=0.5, hue=0.58, sat=0.15)
    P["workB"] = twp.person("WorkB", 1.0, 45, "male_worksuit01", "short04", hv=0.4, cval=0.42, hue=0.58, sat=0.15)
    c["P"] = P
    animate(c, 0.0, "count")
    return c


# ============================================================================ animation
def carry(c, a, b, obj, mid_off=Vector((0, 0, 0))):
    """Two people carrying obj between them (obj already placed): hands on its sides."""
    from human import reach, fingers_curl
    for h in (a, b):
        d = (obj.location - h.arm.location); d.z = 0; d.normalize()
        side = d.cross(Vector((0, 0, 1)))
        for sd, sg in (("L", 1), ("R", -1)):
            reach(h, sd, obj.location - d * 0.28 + side * 0.2 * sg * -1 + mid_off, Vector((-sg * side.x, -sg * side.y, -0.8)), d)
        fingers_curl(h, 45, thumb=20)


def animate(c, sec, shot):
    from human import reach, fingers_curl
    P = c["P"]
    used = {"count": ["counter", "clerk"], "doors": ["clerk"], "chat": ["staffA", "staffB", "clerk"], "lift": ["workA", "workB"],
            "marine": [], "landing": ["workA", "workB"], "stairs": ["workA", "workB"]}[shot]
    for k, h in P.items():
        twp.hide(twp.person_objs(h), k not in used)
    twp.hide(twp.person_objs(c["marine"]), shot != "marine")
    hideables = [c["tty"]] + list(c["tty"].children) + [c["box"], c["clipboard"]] + list(c["clipboard"].children_recursive) + c["crates"]
    twp.hide(hideables, True)
    if shot == "count":
        h = P["counter"]
        twp.walk(h, (8.5, 0.15), (-11.0, 0.15), sec, speed=0.75)
        k = math.sin(sec * 1.4)
        h.rot("head", (0, 0, 1), 35 * k)                                   # glancing into the rooms either side
        cb = c["clipboard"]; twp.hide([cb] + list(cb.children_recursive), False)
        fwd = twp.forward(h); chest = h.bone_head("spine03")
        cb.location = twp.chest_point(h, 0.24, 0.3); cb.rotation_euler = (math.radians(-50), 0, math.atan2(fwd.x, -fwd.y))
        for sd, sg in (("L", 1), ("R", -1)):
            side = fwd.cross(Vector((0, 0, 1)))
            reach(h, sd, cb.location - side * 0.1 * sg + Vector((0, 0, -0.03)), Vector((-sg * side.x, -sg * side.y, -0.8)), fwd)
        twp.walk(P["clerk"], (-7.0, -2.6), (-7.0, 2.6), max(0.0, sec - 1.0), speed=1.0)
    elif shot == "doors":
        twp.walk(P["clerk"], (-9.0, -2.4), (-9.0, 2.6), sec, speed=0.9)
    elif shot == "chat":
        a, b = P["staffA"], P["staffB"]
        twp.stand(a, (0.75, 0.15, 0), math.pi); twp.stand(b, (1.75, -0.1, 0), math.radians(-130))      # A in profile at the notice, B turned to her and to us
        cb = c["clipboard"]; twp.hide([cb] + list(cb.children_recursive), False)          # she holds a folder at her chest
        fa = twp.forward(a); cb.location = twp.chest_point(a, 0.22, 0.28); cb.rotation_euler = (math.radians(-60), 0, math.atan2(fa.x, -fa.y))
        sa = fa.cross(Vector((0, 0, 1)))
        for sd, sg in (("L", 1), ("R", -1)):
            reach(a, sd, cb.location - sa * 0.08 * sg + Vector((0, 0, -0.04)), Vector((-sg * sa.x, -sg * sa.y, -0.8)), fa)
        a.rot("head", (0, 0, 1), -20 + 12 * math.sin(sec * 0.7)); b.rot("head", (0, 0, 1), 10)
        nb = Vector((1.1, CW / 2 - 0.05, 1.5))                                  # B points, small, at the notice: forearm only, elbow at the side
        sh = b.bone_head("upperarm01.R"); fb = twp.forward(b); rb = fb.cross(Vector((0, 0, 1))).normalized()
        hand = sh + Vector((0, 0, -0.3)) + rb * 0.08 + ((nb - sh) * Vector((1, 1, 0))).normalized() * 0.32
        reach(b, "R", hand, rb * 0.5 + Vector((0, 0, -1)) - fb * 0.3, nb - hand)
        twp.walk(P["clerk"], (6.0, -0.3), (-6.0, -0.3), sec, speed=1.1)
    elif shot == "lift":
        a, b = P["workA"], P["workB"]
        bx = c["box"]; twp.hide([bx], False)
        turn = ease(min(1.0, max(0.0, (sec - 2.1) / 1.2)))
        base = Vector((-11.4, 0.1, 0.0))
        heading = Vector((-1, 0, 0)).lerp(Vector((0, 1, 0)), turn).normalized()       # toward the lift, then off to the stairs (+Y door)
        mid = base + Vector((0, 0.9 * ease(max(0.0, (sec - 3.0) / 1.5)), 0))
        bx.location = mid + Vector((0, 0, 0.8)); bx.rotation_euler = (0, 0, math.atan2(heading.y, heading.x))
        twp.stand(a, (mid - heading * 0.62).to_tuple(), math.atan2(heading.x, -heading.y))
        twp.stand(b, (mid + heading * 0.62).to_tuple(), math.atan2(-heading.x, heading.y))
        carry(c, a, b, bx)
        a.rot("head", (0, 0, 1), 20 * turn)
    elif shot == "marine":
        m = c["marine"]
        twp.seat(m, (-10.7, -0.55, 0), math.pi / 2, lean=2)                   # faces +X down the corridor, desk in front, sitting up straight
        alarm = ease(min(1.0, max(0.0, (sec - 1.5) / 0.6)))
        m.rot("spine03", (0, 0, 1), 18 * alarm); m.rot("neck01", (0, 0, 1), 20 * alarm); m.rot("head", (0, 0, 1), 30 * alarm)   # turns to the panel behind him
        fw = twp.forward(m); sd_ = fw.cross(Vector((0, 0, 1))).normalized(); nk = m.bone_head("neck01")
        for k, sg in enumerate((-1, 1)):                                        # collar insignia
            o = c["insignia"][k]; o.location = nk + fw * 0.07 + sd_ * sg * 0.055 + Vector((0, 0, -0.035))
            o.rotation_euler = (0, 0, math.atan2(fw.x, -fw.y) + sg * 0.5)
    elif shot in ("landing", "stairs"):
        a, b = P["workA"], P["workB"]
        tty = c["tty"]; twp.hide([tty] + list(tty.children), False)
        X0, D = STAIR_X, 6.0
        LZ = 1.7 if shot == "landing" else 5.1                # 11B: the top mid-landing, seen from straight above
        k = ease(min(1.0, sec / DUR[shot]))
        ang = math.radians(90) * k                            # turning the teletype round the mid landing
        piv = Vector((X0 - D / 2 + 0.75, 0.0, LZ))
        tty.location = piv + Vector((0, -0.35 + 0.7 * k, 0.55)); tty.rotation_euler = (math.radians(-12 * math.sin(math.pi * k)), 0, ang)
        fa = tty.location + Vector((0.7, -0.4 + 0.3 * k, 0)); fb = tty.location + Vector((-0.2, 0.7, 0))
        twp.stand(a, (fa.x, fa.y, LZ), math.atan2(tty.location.x - fa.x, -(tty.location.y - fa.y)))
        twp.stand(b, (fb.x, fb.y, LZ), math.atan2(tty.location.x - fb.x, -(tty.location.y - fb.y)))
        carry(c, a, b, tty, Vector((0, 0, 0.2)))
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_count(c, t):
    h = c["P"]["counter"]; base = Vector(h.arm.location) + Vector((0, 0, 1.6))
    return (base + Vector((-2.4, -0.45, 0.0)), base + Vector((0, 0.1, -0.2)), 35)            # leads him backward down the corridor


def cam_doors(c, t):
    e = ease(t)
    return (Vector((9.6, -0.6, 1.6)).lerp(Vector((8.6, -0.5, 1.58)), e), Vector((-6, 0.2, 1.2)), 30)


def cam_chat(c, t):
    e = ease(t)
    return (Vector((-1.6, -0.75, 1.55)).lerp(Vector((-1.3, -0.7, 1.55)), e), Vector((1.1, 0.4, 1.4)), 35)


def cam_lift(c, t):
    e = ease(t)
    return (Vector((-8.4, -0.85, 1.6)).lerp(Vector((-8.9, -0.8, 1.6)), e), Vector((-12.5, 0.2, 1.4)), 30)


def cam_marine(c, t):
    e = ease(t)
    return (Vector((-7.9, 0.85, 1.3)).lerp(Vector((-8.15, 0.72, 1.28)), e), Vector((-10.4, -0.45, 0.88)), 28)


def cam_landing(c, t):
    e = ease(t); X0, D = STAIR_X, 6.0
    return (Vector((X0 + D / 2 - 0.7, 0.95, 4.9)).lerp(Vector((X0 + D / 2 - 0.9, 0.9, 4.85)), e), Vector((X0 - D / 2 + 0.9, 0.0, 2.3)), 26)


def cam_stairs(c, t):
    e = ease(t); X0 = STAIR_X
    D = 6.0
    return (Vector((X0 - D / 2 + 1.7, 0.05, 9.4)).lerp(Vector((X0 - D / 2 + 1.6, 0.05, 9.0)), e), Vector((X0 - D / 2 + 0.85, 0.0, 5.4)), 30, (1, 0, 0))


MOVES = {
    "count": dict(kind="anim", dof=3.0, cam=cam_count, focus=lambda c, t: c["P"]["counter"].bone_head("head"), anim=anim("count")),
    "doors": dict(kind="anim", dof=None, cam=cam_doors, anim=anim("doors")),
    "chat": dict(kind="anim", dof=3.0, cam=cam_chat, focus=lambda c, t: Vector((1.1, 0.2, 1.5)), anim=anim("chat")),
    "lift": dict(kind="anim", dof=3.5, cam=cam_lift, focus=lambda c, t: Vector((-11.5, 0.2, 1.2)), anim=anim("lift")),
    "marine": dict(kind="anim", dof=5.0, cam=cam_marine, focus=lambda c, t: Vector((-10.4, -0.45, 0.9)), anim=anim("marine")),
    "landing": dict(kind="anim", dof=None, cam=cam_landing, anim=anim("landing")),
    "stairs": dict(kind="anim", dof=None, cam=cam_stairs, anim=anim("stairs")),
}


# ---------------------------------------------------------------- the cinematic look (house style, Nov 2026)
import look
_build_raw = build


def build(variant=None):
    c = _build_raw(variant) if variant is not None else _build_raw()
    look.night_interior(lift=0.15)          # windowless corridor and lobby under fluorescents
    return c
