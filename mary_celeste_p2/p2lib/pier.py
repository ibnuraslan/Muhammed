"""New York, East River, early November 1872: Pier 50 with the Mary Celeste lying alongside, loading barrels.

Frame: river surface z = 0; the pier runs along +x from the bulkhead (x = X_SHORE) out into the river; its deck is
at z = DECK. The Mary Celeste lies along the pier's port-side edge (+y), bow out toward the river (+x), starboard side
to the pier. Behind the bulkhead: South Street (cobbles) and a row of brick counting-houses and warehouses.
"""
import math, random
import numpy as np
import bpy
from mathutils import Vector, Matrix, noise
import ship, sea, ph
import stage as S

DECK = 1.75
PIER_W = 14.0            # y in [-PIER_W/2, PIER_W/2]
X_SHORE = -46.0
X_HEAD = 34.0
SHIP_Y = PIER_W / 2 + ship.B / 2 + 0.55
SHIP_X = 2.0


def harbour_rig(mc):
    """Turn the as-found sail plan into a ship in port: every square sail furled on its yard, headsails stowed."""
    keep = []
    for o in list(mc["coll"].objects):
        n = o.name
        if any(k in n for k in ("_sail_", "_shred", "_jib", "_fstay")):
            bpy.data.objects.remove(o)
    Y = mc["spars"]["yards"]
    can = mc["mats"]["canvas"]
    for nm in ("course", "ltop", "utop"):
        if nm in Y:
            a, b, _ = Y[nm]
            f = ship.furled(f"MC_{nm}_furl", a, b, 0.22 if nm == "course" else 0.18, can, mc["coll"], seed=hash(nm) % 9)
            f.parent = mc["root"]
    return mc


def water(mat=None, size=260, calm=True):
    m = mat or sea.water_material("harbour", deep=(0.008, 0.011, 0.008), crest=(0.02, 0.03, 0.022), fog_color=(0.5, 0.48, 0.42))
    o = sea.ocean(size=size, res=20, scale=0.18 if calm else 0.5, chop=0.7, wind=4.5 if calm else 9, foam=0.0, mat=m,
                  direction=30, loc=(0, 0, 0), repeat=2)
    sea.far_sea(size, mat=m)
    return o


def _facade(x, y0, width, storeys, mats, rng, sign=None, depth=12.0):
    """A brick front of 1860s South Street: granite ground floor with doors, brick above, stone lintels, cornice."""
    st = 3.3
    h = storeys * st + 1.0
    brick = mats["brick"][rng.integers(len(mats["brick"]))]
    ship.box("bldg", (x - depth / 2, y0 + width / 2, h / 2), (depth, width - 0.08, h), brick)
    ship.box("granite", (x + 0.12, y0 + width / 2, 1.9), (0.3, width - 0.1, 3.8), mats["granite"])
    nwin = max(2, int(width / 2.2))
    for k in range(nwin):
        yy = y0 + width * (k + 0.5) / nwin
        # ground floor: double doors (dark wood) / shop window
        ship.box("door", (x + 0.28, yy, 1.45), (0.06, 1.3, 2.6), mats["door"])
        ship.box("door_head", (x + 0.3, yy, 2.85), (0.1, 1.5, 0.16), mats["granite"])
        for f in range(1, storeys):
            z = f * st + 1.6
            ship.box("win", (x + 0.04, yy, z), (0.08, 0.95, 1.7), mats["glass"])
            for sg in (-1, 1):
                ship.box("sash", (x + 0.09, yy + sg * 0.25, z), (0.02, 0.03, 1.7), mats["sash"])
            ship.box("sash", (x + 0.09, yy, z), (0.02, 0.95, 0.03), mats["sash"])
            ship.box("lintel", (x + 0.1, yy, z + 0.95), (0.12, 1.15, 0.2), mats["granite"])
            ship.box("sill", (x + 0.12, yy, z - 0.9), (0.18, 1.1, 0.08), mats["granite"])
    ship.box("cornice", (x + 0.15, y0 + width / 2, h - 0.3), (0.5, width, 0.35), mats["cornice"])
    for c in range(rng.integers(1, 3)):
        cy = y0 + width * rng.uniform(0.2, 0.8)
        ship.box("chimney", (x - depth * rng.uniform(0.2, 0.8), cy, h + 0.8), (0.7, 1.0, 1.6), brick)
    if sign:
        board = ship.box("signboard", (x + 0.25, y0 + width / 2, 3.95), (0.06, width * 0.86, 0.6), mats["signboard"])
        cu = bpy.data.curves.new("sign", 'FONT'); cu.body = sign; cu.size = 0.36; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
        try:
            cu.font = bpy.data.fonts.load(S.FONT_SERIF) if hasattr(S, "FONT_SERIF") else cu.font
        except Exception:
            pass
        cu.extrude = 0.01
        o = bpy.data.objects.new("sign", cu); bpy.context.collection.objects.link(o)
        o.location = (x + 0.29, y0 + width / 2, 3.95); o.rotation_euler = (math.pi / 2, 0, math.pi / 2)
        o.data.materials.append(mats["gilt"])
    return h


def build(mood="morning", ship_state="port", people=True, barrels=True, sling=True, tug=False, haze=True):
    A = {}
    rng = np.random.default_rng(7)
    random.seed(7)
    planks = ship.wood("weathered_planks", 0.6, tint=(0.9, 0.8, 0.68), name="pierdeck")
    timber = ship.wood("brown_planks_05", 0.8, tint=(0.6, 0.45, 0.32), name="timber")
    iron = ship.iron("bollard_iron")
    mats = dict(
        brick=[ph.texture(a, scale=0.35, name=a, tint=t) for a, t in
               (("brick_wall_02", (1.0, 0.82, 0.7)), ("brick_wall_04", (0.9, 0.7, 0.58)), ("brick_wall_09", (1.0, 0.85, 0.75)))],
        granite=ship.paint("granite", (0.42, 0.4, 0.37), rough=0.7, grime=0.5, scale=4),
        door=ship.paint("door", (0.08, 0.05, 0.03), rough=0.4, grime=0.3),
        glass=ship.paint("winglass", (0.02, 0.025, 0.03), rough=0.08, grime=0.2),
        sash=ship.paint("sash", (0.55, 0.52, 0.45), rough=0.4, grime=0.4),
        cornice=ship.paint("cornice", (0.3, 0.22, 0.16), rough=0.5, grime=0.4),
        signboard=ship.paint("signboard", (0.03, 0.06, 0.04), rough=0.35, grime=0.2),
        gilt=S.emissive("gilt", (0.75, 0.55, 0.2), 0.0),
    )
    p = mats["gilt"].node_tree.nodes["Principled BSDF"]; p.inputs['Metallic'].default_value = 1.0; p.inputs['Roughness'].default_value = 0.3
    # ---- the pier: plank deck, stringpieces, piles, bollards
    L = X_HEAD - X_SHORE
    ship.box("pier_deck", ((X_HEAD + X_SHORE) / 2, 0, DECK - 0.1), (L, PIER_W, 0.2), planks)
    for sg in (1, -1):
        ship.box("stringpiece", ((X_HEAD + X_SHORE) / 2, sg * (PIER_W / 2 - 0.2), DECK + 0.08), (L, 0.4, 0.36), timber, bevel=0.03)
        x = X_SHORE + 1.0
        while x < X_HEAD:
            ship.cyl("pile", (x, sg * (PIER_W / 2 - 0.15), -3.0), (x, sg * (PIER_W / 2 - 0.15), DECK - 0.15), 0.17, 0.16, mat=timber, verts=12)
            x += 2.4
        for bx in np.arange(X_SHORE + 8, X_HEAD, 9.0):
            b0 = Vector((bx, sg * (PIER_W / 2 - 0.25), DECK + 0.26))
            ship.cyl("bollard", b0, b0 + Vector((0, 0, 0.45)), 0.16, 0.13, mat=iron, verts=16)
            ship.cyl("bollard_cap", b0 + Vector((0, 0, 0.45)), b0 + Vector((0, 0, 0.53)), 0.2, 0.2, mat=iron, verts=16)
    ship.box("pierhead", (X_HEAD + 0.2, 0, DECK - 0.4), (0.4, PIER_W, 1.2), timber)
    # pier shed roof line along the starboard edge (open sides), adds depth behind
    for x in np.arange(X_SHORE + 4, X_SHORE + 30, 4.0):
        for sy in (-PIER_W / 2 + 0.8, -PIER_W / 2 + 5.0):
            ship.cyl("shedpost", (x, sy, DECK), (x, sy, DECK + 4.2), 0.12, mat=timber, verts=8)
    ship.box("shedroof", (X_SHORE + 17, -PIER_W / 2 + 2.9, DECK + 4.3), (28, 5.0, 0.15), timber)
    # ---- South Street: cobbles and the row of buildings (facing +x)
    cob = ph.texture("cobblestone_floor_01", scale=0.25, name="cobbles", tint=(0.85, 0.8, 0.72))
    ship.box("street", (X_SHORE - 9, 0, DECK - 0.1), (18, 160, 0.2), cob)
    signs = ["SHIP CHANDLERY", "COMMISSION MERCHANTS", None, "J. H. WINCHESTER & CO.", None, "SAIL LOFT", None, "NAVAL STORES", None, None]
    y = -68.0; i = 0
    while y < 70:
        w = float(rng.uniform(7, 10))
        _facade(X_SHORE - 18, y, w, int(rng.integers(4, 6)), mats, rng, sign=signs[i % len(signs)])
        y += w; i += 1
    for o in [o for o in bpy.data.objects if o.name.startswith(("bldg", "granite", "door", "win", "sash", "lintel", "sill", "cornice", "chimney", "signboard", "sign"))]:
        o.location.z += DECK
    # ---- the Mary Celeste alongside
    mc = ship.build("MC", sails=("full" if ship_state == "sail" else "found"), wet=0.0, detail=True, hatches_off=(ship_state == "port"))
    if ship_state == "port":
        harbour_rig(mc)
    mc["root"].location = (SHIP_X, SHIP_Y, 0.0)
    bpy.context.view_layer.update()
    A["ship"] = mc; A["ship_M"] = mc["root"].matrix_world.copy()
    # mooring lines from the bow and quarter to bollards, and a gangplank to the rail
    rope = mc["mats"]["rope"]
    for sx, bx in ((ship.L / 2 - 4, SHIP_X + ship.L / 2 + 2), (-ship.L / 2 + 3, SHIP_X - ship.L / 2 - 3)):
        a = A["ship_M"] @ Vector((sx, -ship.B / 2 + 0.3, ship.zdeck(sx) + 0.9))
        b = Vector((bx, PIER_W / 2 - 0.25, DECK + 0.5))
        ship.rope("mooring", [a, a.lerp(b, 0.5) - Vector((0, 0, 0.6)), b], 0.03, rope)
    gx = SHIP_X - 2.5
    g0 = Vector((gx, PIER_W / 2 - 1.6, DECK + 0.02)); g1 = A["ship_M"] @ Vector((gx - SHIP_X, -ship.B / 2 + 0.1, ship.zdeck(gx - SHIP_X) + ship.RAIL_H + 0.08))
    gp = ship.box("gangplank", tuple((g0 + g1) / 2), ((g1 - g0).length, 0.6, 0.06), timber)
    d = g1 - g0
    gp.rotation_euler = (0, -math.atan2(d.z, math.hypot(d.x, d.y)), math.atan2(d.y, d.x))
    gp.rotation_euler = (0, 0, 0)
    gp.rotation_mode = 'QUATERNION'; gp.rotation_quaternion = d.to_track_quat('X', 'Z')
    A["gangplank"] = (g0, g1)
    # ---- barrels: rows and tiers on the pier, and one swinging aboard in a sling
    if barrels:
        r, ms = S.place_model("wine_barrel_01", (0, 0, DECK), size=0.86)
        proto = r; proto["off"] = tuple(r.location - Vector((0, 0, DECK)))
        A["barrel_proto"] = (r, ms)
        lo, hi = ph.bounds(ms); bd = max(hi.x - lo.x, hi.y - lo.y)
        n = 0
        for row in range(5):
            for col in range(14):
                for tier in range(2 if row < 3 else 1):
                    x = SHIP_X - 36 + col * (bd + 0.04) + (tier * bd / 2)
                    yy = PIER_W / 2 - 3.2 - row * (bd + 0.05)
                    c = _inst(proto, Vector((x, yy, DECK + tier * (hi.z - lo.z) * 0.98)) - Vector((0, 0, 0)),
                              rz=rng.uniform(0, 6.28), lying=False)
                    n += 1
        proto.location = Vector((SHIP_X - 30, PIER_W / 2 - 2.0, DECK)) + Vector(proto["off"])
        A["barrel_size"] = (bd, hi.z - lo.z)
        if sling:
            yx = mc["spars"]["yards"]["course"]
            ya = A["ship_M"] @ yx[1] if yx[1].y < 0 else A["ship_M"] @ yx[0]
            sl = Vector((ya.x, PIER_W / 2 - 0.2, DECK + 1.45))
            sb = _inst(proto, sl - Vector((0, 0, 0.43)), rz=0.3, lying=True)
            A["sling_barrel"] = sl
            for dy in (-0.25, 0.25):
                ship.rope("sling", [sl + Vector((-0.3, dy, -0.42)), sl + Vector((0, 0, 0.55))], 0.012, rope)
                ship.rope("sling", [sl + Vector((0.3, dy, -0.42)), sl + Vector((0, 0, 0.55))], 0.012, rope)
            ship.rope("whip", [sl + Vector((0, 0, 0.55)), ya + Vector((0, 0, -0.1))], 0.016, rope)
            ship.rope("fall", [ya + Vector((0, 0, -0.1)), A["ship_M"] @ Vector((yx[0].x - SHIP_X + 1.5 if False else 2.0, 0.6, ship.zdeck(2.0) + 0.8))], 0.014, rope)
    # crates and a coil or two
    for k in range(6):
        try:
            if k == 0:
                cr, cms = S.place_model("wooden_crate_01", (SHIP_X - 20, -1.5, DECK), size=0.7)
                cproto = cr; cr["off"] = tuple(cr.location - Vector((SHIP_X - 20, -1.5, DECK)))
            else:
                _inst(cproto, Vector((SHIP_X - 20 + k * 1.1, -1.5 + (k % 2) * 1.1, DECK)), rz=k * 0.4)
        except Exception:
            break
    # ---- sky and light: a clear, hazy November morning, sun low in the south-east, warm
    import look
    sea_m = sea.water_material("harbour", deep=(0.01, 0.014, 0.01), crest=(0.03, 0.04, 0.03), fog_color=(0.55, 0.5, 0.42))
    water(sea_m)
    w, bg, mp = ph.world_hdri("kloppenheim_06_puresky", strength=0.8, rot_z=math.radians(200), res="4k")
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = 4.2; sun.data.angle = math.radians(1.2); sun.data.color = (1.0, 0.8, 0.6)
    az, el = math.radians(-35), math.radians(16)
    sun.rotation_euler = (Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * -1).to_track_quat('-Z', 'Y').to_euler()
    A["sun_dir"] = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    if haze and not S.NOVOL:
        sea.haze((0, 0, 30), (420, 420, 60), density=0.0016, color=(0.85, 0.75, 0.62), aniso=0.6)
    return A


def _inst(proto, loc, rz=0.0, lying=False):
    """Linked duplicate of a model hierarchy (cheap instancing)."""
    new = proto.copy(); bpy.context.collection.objects.link(new)
    for ch in proto.children:
        c = ch.copy(); c.data = ch.data; bpy.context.collection.objects.link(c); c.parent = new
    new.location = Vector(loc) + Vector(proto.get("off", (0, 0, 0)))
    new.rotation_euler = ((math.pi / 2 if lying else 0), 0, rz)
    return new
