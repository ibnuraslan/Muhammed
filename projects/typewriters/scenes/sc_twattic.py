"""EMBASSY ATTIC, the staging area (dramatization). Low pitched roof, timber rafters, bare bulbs, dust in the light
from two small dormers. Rows of old equipment waiting to go: copiers, terminals, teletypes, cipher boxes; burlap crates.

Intro 5A  track    slow lateral track along the rows of machines under the bulbs; a worker wheels a hand truck behind
Intro 5B  staple   a worker staples burlap over the last crate
Ch1 10A   cable    a technician runs an alarm cable along the rafters (later)
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import machines as MC

EXPOSURE = -0.3
DUR = {"track": 5.0, "staple": 4.5, "cable": 5.0}
LX, LY, EAVE, RIDGE = 9.0, 3.4, 1.3, 3.4        # half length (x), half width (y), eave and ridge heights


def build(variant=None):
    c = {}
    rng = np.random.default_rng(9)
    world_sky(sun_elev_deg=30, sun_rot_deg=120, strength=0.35, tint=(0.85, 0.9, 1.0))
    floor = ph.texture("old_planks_02", scale=0.5, name="AtticBoards")
    box("Floor", (0, 0, -0.05), (2 * LX, 2 * LY, 0.1), floor)
    plaster = pbr("AtticPlaster", (0.45, 0.43, 0.4), 0.9)
    timber = ph.texture("brown_planks_05", scale=1.0, name="Timber", tint=(0.8, 0.75, 0.7))
    # pitched roof: two slopes of boards, rafters every 0.6 m, a ridge beam, gable walls
    slope = math.atan2(RIDGE - EAVE, LY)
    Ls = math.hypot(RIDGE - EAVE, LY)
    for sy in (-1, 1):
        box("RoofBoards", (0, sy * LY / 2, (RIDGE + EAVE) / 2 + 0.06), (2 * LX, Ls, 0.04), timber, rot=(-sy * slope, 0, 0))
        box("KneeWall", (0, sy * LY, EAVE / 2 + 0.2), (2 * LX, 0.1, EAVE + 0.4), plaster)
    for k in range(31):
        x = -LX + 0.3 + k * 0.6
        for sy in (-1, 1):
            box("Rafter", (x, sy * LY / 2, (RIDGE + EAVE) / 2 - 0.02), (0.07, Ls, 0.14), timber, rot=(-sy * slope, 0, 0))
        if k % 4 == 1:
            box("CollarTie", (x, 0, RIDGE - 0.55), (0.06, 2 * LY * 0.55 / (RIDGE - EAVE) * 1.0, 0.12), timber)
    box("Ridge", (0, 0, RIDGE - 0.04), (2 * LX, 0.12, 0.2), timber)
    for sx in (-1, 1):
        box("Gable", (sx * LX, 0, RIDGE / 2), (0.1, 2 * LY, RIDGE), plaster)
    # two dormers on the -Y slope with cool daylight and dusty air
    for x in (-4.0, 3.0):
        box("DormerGlass", (x, -LY * 0.62, 1.95), (1.0, 0.02, 0.8), glass("DormerG", (0.85, 0.9, 0.95)))
        l = area_light((x, -LY * 0.7, 2.0), (math.radians(90), 0, 0), 1.0, 160, (0.85, 0.92, 1.0)); point_at(l, (x + 0.8, 0.8, 0.0))
        l.data.shape = 'RECTANGLE'; l.data.size = 1.0; l.data.size_y = 0.8; l.visible_camera = False
        l.data.spread = math.radians(40)
    haze((0, 0, 1.5), (2 * LX, 2 * LY, 3.0), density=0.012, color=(0.75, 0.8, 0.88), anis=0.55)
    # bare bulbs on pull-chain sockets along the ridge
    bulb = pbr("Bulb", (1, 0.9, 0.7), 0.1, 0.0, **{'Emission Color': (1.0, 0.75, 0.45, 1), 'Emission Strength': 25.0})
    for x in (-6.0, -2.0, 2.0, 6.0):
        ph.model("pull_chain_light_socket", loc=(x, 0, RIDGE - 0.2))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.035, location=(x, 0, RIDGE - 0.4))
        bpy.context.active_object.data.materials.append(bulb)
        pl = bpy.data.lights.new("BulbL", 'POINT'); pl.energy = 45; pl.color = (1.0, 0.72, 0.45); pl.shadow_soft_size = 0.04
        po = bpy.data.objects.new("BulbL", pl); bpy.context.collection.objects.link(po); po.location = (x, 0, RIDGE - 0.47)
    # ---------------------------------------------------------------- the equipment, in rows (front row y = -1.0, back row y = 1.1)
    MC.copier("CopierA", (-5.8, -1.0, 0), 0.0); MC.copier("CopierB", (-4.5, -1.0, 0), 0.05); MC.copier("CopierC", (2.8, 1.2, 0), math.pi)
    ph.model("metal_office_desk", loc=(-2.75, -1.0, 0), rot_z=math.pi, scale=0.8)
    for k, x in enumerate((-3.35, -2.75, -2.15)):
        MC.terminal(f"Term{k}", (x, -0.95, 0.632), rng.uniform(-0.1, 0.1))
    c["tty"] = []
    for k, x in enumerate((-1.2, -0.25)):
        r, p = MC.teletype(f"TTY{k}", (x, -1.0, 0), 0.0); c["tty"].append(p)
    for k in range(3):
        MC.cipher(f"Cipher{k}", (0.85 + k * 0.62, -1.0, 0), 0.0, height=0.5)
        MC.cipher(f"CipherT{k}", (0.85 + k * 0.62, -1.0, 0.5), 0.0, height=0.4)
    MC.lamp_blink()
    for k, x in enumerate((-5.5, -4.5, -3.4, -2.3, -1.0, 0.2)):          # back row: crated already
        for j in range(1 + (k % 2)):
            o = MC.burlap_crate(f"Crate{k}{j}"); o.location = (x + rng.uniform(-0.1, 0.1), 1.25, 0.43 + j * 0.86)
            o.rotation_euler = (0, 0, rng.uniform(-0.06, 0.06))
    for x in (4.6, 5.6):
        ph.model("wooden_crate_01", loc=(x, -1.4, 0), rot_z=rng.uniform(-0.2, 0.2))
    ph.model("cardboard_box_01", loc=(6.4, -0.6, 0), rot_z=0.4)
    # the last crate, half-wrapped: a box with a burlap skin that covers it as the worker staples
    c["last"] = Vector((4.3, 0.95, 0.0))
    wood = ph.texture("wood_table_001" if False else "brown_planks_03", scale=1.5, name="CrateWood")
    box("LastCrateWood", (c["last"].x, c["last"].y, 0.43), (0.95, 0.75, 0.85), wood, bevel=0.01)
    hes = bpy.data.materials.get("Burlap") or ph.texture("hessian_230", scale=2.0, name="Burlap", tint=(0.78, 0.66, 0.5))
    wrap = box("Wrap", (0, 0, 0), (0.97, 0.77, 0.87), hes, bevel=0.03)
    wrap.location = (c["last"].x, c["last"].y, 0.43)
    c["wrap"] = wrap
    st, sms = ph.model("vintage_stapler")
    c["stapler"] = st
    staples = []
    sm = pbr("Staple", (0.7, 0.7, 0.72), 0.25, 1.0)
    for k in range(9):
        s = box("Staple", (0, 0, 0), (0.012, 0.002, 0.002), sm); s.hide_render = True; staples.append(s)
    c["staples"] = staples
    # people: the stapler, and a worker wheeling a hand truck behind the rows
    w = twp.person("Stapler", 1.0, 38, "male_worksuit01", "short04", hv=0.25, cval=0.3, hue=0.58, sat=0.12)
    c["worker"] = w
    w2 = twp.person("Mover", 1.0, 29, "male_worksuit01", "short02", hv=0.2, cval=0.25, hue=0.58, sat=0.12)
    c["mover"] = w2
    ht, _ = ph.model("hand_truck")
    c["truck"] = ht
    animate(c, 0.0, "track")
    return c


# ============================================================================ animation
def animate(c, sec, shot):
    from human import reach, fingers_curl
    for p in c["tty"]:
        pass
    # stapler worker: stands at the crate's front face (-Y side), stapling along the top edge left to right
    L = c["last"]; w = c["worker"]
    twp.stand(w, (L.x - 0.1, L.y - 0.68, 0.0), math.pi)          # faces +Y, the crate
    k = sec / DUR["staple"]
    n = int(sec / 0.45)
    xs = L.x - 0.4 + min(n, 8) * 0.1
    ph_ = (sec % 0.45) / 0.45
    lift = 0.04 * max(0.0, math.sin(math.pi * ph_)) if ph_ < 0.6 else 0.0
    sp = Vector((xs, L.y - 0.3, 0.875 + lift))
    st = c["stapler"]; st.location = sp; st.rotation_euler = (0, 0, math.pi / 2)
    for i, s in enumerate(c["staples"]):
        s.location = (L.x - 0.4 + i * 0.1, L.y - 0.33, 0.876); s.hide_render = i >= min(n, 9)
    reach(w, "R", sp + Vector((0.0, -0.02, 0.09)), Vector((-0.8, -0.3, -0.6)), Vector((0, 1, -0.6)))
    reach(w, "L", Vector((xs - 0.25, L.y - 0.42, 0.75)), Vector((0.8, -0.3, -0.6)), Vector((0, 1, 0)))
    fingers_curl(w, 45, thumb=20)
    w.rot("head", (1, 0, 0), -8)
    # the mover wheels a hand truck down the aisle behind the rows (x from +5 to -6)
    mv = c["mover"]; x = 5.5 - 0.9 * sec
    twp.hide(twp.person_objs(mv) + [c["truck"]] + list(c["truck"].children_recursive), shot != "track")
    twp.walk(mv, (5.5, 0.15), (-7.0, 0.15), sec, speed=0.9)
    ht = c["truck"]; fwd = twp.forward(mv)
    ht.location = mv.arm.location + fwd * 0.75; ht.rotation_euler = (math.radians(-25), 0, math.atan2(fwd.x, -fwd.y) + math.pi)
    for sd, sg in (("L", 1), ("R", -1)):
        side = fwd.cross(Vector((0, 0, 1)))
        reach(mv, sd, ht.location + Vector((0, 0, 1.0)) - fwd * 0.3 + side * 0.18 * sg * -1, Vector((0, 0, -1)), fwd)
    for p in c["tty"]:
        MC.run_teletype(p, sec) if False else None
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_track(c, t):
    e = ease(t)
    a = Vector((-5.8, -2.6, 1.6)); b = Vector((-2.0, -2.6, 1.65))
    return (a.lerp(b, e), a.lerp(b, e) + Vector((1.6, 3.0, -0.65)), 28)


def cam_staple(c, t):
    e = ease(t); L = c["last"]
    a = L + Vector((2.0, -2.0, 1.5)); b = L + Vector((1.8, -1.75, 1.45))
    return (a.lerp(b, e), L + Vector((-0.25, -0.5, 0.95)), 30)


MOVES = {
    "track": dict(kind="anim", dof=3.5, cam=cam_track, focus=lambda c, t: Vector((-3.0 + 3.5 * ease(t), -1.0, 0.9)), anim=anim("track")),
    "staple": dict(kind="anim", dof=2.4, cam=cam_staple, focus=lambda c, t: c["stapler"].location, anim=anim("staple")),
}
