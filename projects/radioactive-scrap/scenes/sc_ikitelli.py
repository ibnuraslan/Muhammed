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
from human import reset_pose, pose_walk, reach, fingers_curl, aim_bone

EXPOSURE = 0.0
BOUNCES = 6
DUR = {"truck_drive": 2.5 + 3.6, "truck_rope": 3.2, "torch": 3.0, "peel": 3.0, "steady": 3.6, "relatives": 3.6,
       "bury": 3.6, "dusk": 4.4}       # estimates until the voiceover arrives (truck_drive carries the 2.5 s lead-in)
VARIANT_FOR = {"dusk": "dusk"}

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


def build(variant=None):
    c = {}
    dusk = variant == "dusk"
    rng = np.random.default_rng(12)
    if dusk:
        overcast(strength=0.1, sun_energy=0.0, sun_elev=4, sun_az=230, tint=(0.55, 0.68, 1.0))
        bpy.context.scene.view_settings.exposure = 0.6
    else:
        overcast(strength=0.12, sun_energy=0.8, sun_elev=18, sun_az=200)
    # ground: muddy yard, rutted street, verge
    mud = ph_mat("muddy_tracks", 0.25, (0.25, 0.21, 0.17), name="Mud")
    road = ph_mat("road_damaged", 0.2, (0.18, 0.18, 0.18), name="Road")
    box("Ground", (0, 0, -0.05), (240, 200, 0.1), mud)
    box("Street", (0, 0, -0.035), (240, 6.5, 0.08), road)
    # houses: plaster in faded ochres, greys and pinks; clay roofs; some unfinished upper floors with rebar
    plasters = [ph_mat("plastered_wall_04", 0.4, (0.6, 0.55, 0.47), name="PlasterA", tint=(0.95, 0.88, 0.75)),
                ph_mat("plastered_wall_04", 0.4, (0.55, 0.55, 0.52), name="PlasterB", tint=(0.8, 0.8, 0.78)),
                ph_mat("plastered_wall_04", 0.4, (0.62, 0.5, 0.45), name="PlasterC", tint=(0.95, 0.8, 0.72))]
    brick = ph_mat("red_brick", 0.6, (0.4, 0.2, 0.15), name="Brick")
    roof = ph_mat("clay_roof_tiles_02", 0.5, (0.45, 0.2, 0.12), name="RoofTiles")
    lit = 2.0 if dusk else 0.0
    # the family house (east of the yard), the neighbour (west), and the street rows
    fam = house("FamilyHouse", (11.5, 10.5, 0), 8.5, 8.0, 1, plasters[0], roof, lit=lit * 1.5)
    nb = house("Neighbour", (-12.5, 10.0, 0), 9.0, 8.5, 2, plasters[1], roof, lit=lit)
    for k, x in enumerate((-36, -24, 24, 35, 47, -48)):
        house(f"North{k}", (x + rng.uniform(-1, 1), 10.5 + rng.uniform(-1, 2), 0), rng.uniform(7, 10), 8, int(rng.integers(1, 3)),
              plasters[k % 3], roof, lit=lit * (k % 2))
    for k, x in enumerate((-40, -28, -16, -4, 8, 20, 32, 44)):
        f_ = int(rng.integers(1, 3))
        house(f"South{k}", (x + rng.uniform(-1, 1), -10.5 - rng.uniform(0, 2), 0), rng.uniform(7, 10.5), 8, f_,
              plasters[(k + 1) % 3], roof, rot_z=math.pi, lit=lit * ((k + 1) % 2))
    # an unfinished brick storey with rebar on one south house (very 1990s Istanbul)
    box("Unfinished", (-4, -10.5, 2.9 + 1.4), (7, 7, 2.8), brick)
    rebar = pbr("Rebar", (0.15, 0.08, 0.05), 0.7, 0.6)
    for k in range(10):
        cyl("Rebar", (-7.2 + k * 0.7, -7.2, 6.6), 0.012, 1.0, rebar, verts=6)
    # distant hillside of more houses and one minaret (generic, CG)
    far = pbr("FarHouses", (0.42, 0.4, 0.38), 0.9)
    for k in range(80):
        x = rng.uniform(-140, 140); y = rng.uniform(55, 120)
        z = (y - 55) * 0.25
        box("FarHouse", (x, y, z + 2), (rng.uniform(6, 11), 7, rng.uniform(3, 8)), far)
    box("Hill", (0, 100, 0), (320, 100, 18), pbr("HillMud", (0.3, 0.29, 0.26), 0.95), rot=(math.radians(-14), 0, 0))
    cyl("Minaret", (-62, 92, 24), 1.1, 34, far, verts=16)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=1.3, depth=5, location=(-62, 92, 43.5)); bpy.context.active_object.data.materials.append(far)
    if not dusk:
        haze((0, 60, 20), (400, 120, 60), density=0.004, color=(0.85, 0.88, 0.92), anis=0.2)
    else:
        haze((0, 60, 20), (400, 120, 60), density=0.006, color=(0.6, 0.65, 0.8), anis=0.2)
    # electricity poles and sagging wires along the street
    pole_m = pbr("PoleWood", (0.22, 0.18, 0.14), 0.85)
    wire_m = pbr("WireM", (0.02, 0.02, 0.02), 0.6)
    poles = [(-30, 4.0), (-12, 4.0), (6, 4.0), (24, 4.0), (42, 4.0)]
    for p in poles:
        electricity_pole(p, pole_m)
    for a, b in zip(poles[:-1], poles[1:]):
        for dy in (-0.6, 0.6):
            wire((a[0], a[1] + dy, 8.7), (b[0], b[1] + dy, 8.7), 0.7, wire_m)
    wire((6, 4.0, 8.4), (8.5, 6.6, 2.7), 0.25, wire_m)              # service drop to the family house
    # yard frontage: breeze-block wall with a wide open gap; the yard is open to the street
    blocks = ph_mat("concrete_block_wall", 0.8, (0.45, 0.45, 0.43), name="Blocks")
    wall("YardWallW", (-7.2, 4.3), (-3.2, 4.3), 0.95, 0.2, blocks)
    wall("YardWallE", (4.2, 4.3), (7.2, 4.3), 0.95, 0.2, blocks)
    wall("YardWallBack", (-7.2, 16.0), (7.2, 16.0), 1.8, 0.2, blocks)
    # yard clutter: scrap pile, tyres, barrels, a plastic chair, crate slats
    rust = rust_mat("YardRust")
    pile = []
    for k in range(110):
        ang = rng.uniform(0, math.pi); rad = rng.uniform(0, 2.4)
        loc = Vector((-4.2 + rad * math.cos(ang), 13.9 + 0.8 * rad * math.sin(ang), rng.uniform(0.05, 1.3) * (2.4 - rad) / 2.4 + 0.05))
        kind = rng.integers(3)
        if kind == 0:
            o = box("ScrapPlate", loc, (rng.uniform(0.4, 1.2), rng.uniform(0.3, 0.8), 0.02), rust, rot=tuple(rng.uniform(-0.6, 0.6, 3)))
        elif kind == 1:
            o = cyl("ScrapPipe", loc, rng.uniform(0.03, 0.08), rng.uniform(0.6, 1.8), rust, verts=12, rot=(rng.uniform(1.2, 1.9), 0, rng.uniform(0, 3.1)))
        else:
            o = box("ScrapBar", loc, (rng.uniform(0.6, 1.5), 0.06, 0.06), rust, rot=tuple(rng.uniform(-0.4, 0.4, 3)))
        pile.append(o)
    for k, (aid, loc, rz) in enumerate((("old_tyre", (5.6, 14.6, 0), 0.4), ("old_tyre", (5.9, 14.2, 0.2), 1.0), ("Barrel_01", (-6.2, 15.0, 0), 0.0),
                                       ("plastic_monobloc_chair_01", (6.0, 7.0, 0), 2.6), ("metal_jerrycan", (-5.6, 6.2, 0), 0.7))):
        ph_model(aid, loc=loc, rot_z=rz)
    slat_m = noisy("Slat", (0.38, 0.27, 0.16), 0.85, dirt=0.6, scale=6)
    for k in range(9):
        box("Slat", (rng.uniform(-3.5, 3.5), rng.uniform(6.5, 8.0), 0.012), (rng.uniform(0.9, 1.2), 0.15, 0.022), slat_m, rot=(0, 0, rng.uniform(0, 3.1)))
    # laundry line from the family house to a post
    cyl("LinePost", (6.6, 15.2, 1.1), 0.04, 2.2, pole_m, verts=8)
    wire((6.6, 15.2, 2.15), (7.9, 13.0, 2.2), 0.05, wire_m)
    c["laundry"] = laundry((6.65, 15.0, 2.12), 4)
    for k, e in enumerate(c["laundry"]):
        e.location = Vector((6.65, 15.1, 2.14)).lerp(Vector((7.85, 13.1, 2.17)), (k + 0.5) / 4); e.rotation_euler = (0, 0, math.radians(-60))
    # the two containers in the yard (one opened: shell panel hinged, lead core visible)
    cont1, k1 = container("Cont1"); cont1.location = C1; cont1.rotation_euler = (0, 0, -math.pi / 2)
    cont2, k2 = container("Cont2"); cont2.location = C2; cont2.rotation_euler = (0, 0, -0.2)
    c.update(cont1=cont1, cont2=cont2, tre1=k1["trefoil"], tre2=k2["trefoil"])
    for tr in (k1["trefoil"], k2["trefoil"]):
        tr.hide_render = True                  # the mark is only noticed later (Ch2); not shown in the yard shots
    shell = curved_panel("Shell", 0.41, math.radians(-150), math.radians(-30), 0.8, k1["grey"], z0=0.0)
    hinge = bpy.data.objects.new("ShellHinge", None); bpy.context.collection.objects.link(hinge)
    hinge.parent = cont1; hinge.location = (0, 0, 0.15); shell.parent = hinge; shell.location = (0, 0, 0)
    c["hinge"] = hinge
    # the truck (variants place it on the street or in the yard)
    tk, wheels, bed_z, (bx0, bx1) = truck("Truck", (0.18, 0.3, 0.38))
    c.update(truck=tk, wheels=wheels, bed_z=bed_z)
    tc1, _ = container("TruckCont1", trefoil=False); tc1.parent = tk; tc1.location = (-0.9, 0.35, bed_z)
    tc2, _ = container("TruckCont2", trefoil=False); tc2.parent = tk; tc2.location = (0.4, -0.35, bed_z); tc2.rotation_euler = (0, 0, 0.4)
    c.update(tc1=tc1, tc2=tc2)
    rope_m = pbr("Rope", (0.45, 0.4, 0.3), 0.9)
    cu = bpy.data.curves.new("Rope", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.012
    sp = cu.splines.new('POLY'); pts = [(-0.9, 1.05, bed_z + 0.42), (-0.9, 0.75, bed_z + 1.08), (-0.9, -0.05, bed_z + 1.1), (-0.9, -1.05, bed_z + 0.45), (-0.9, -1.3, bed_z + 0.2)]
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    c["rope"] = bpy.data.objects.new("Rope", cu); bpy.context.collection.objects.link(c["rope"]); cu.materials.append(rope_m)
    c["rope"].parent = tk; c["rope_spline"] = sp
    # excavator (rented for the peel) parked at the yard's back
    ex = excavator("Excavator", (0.7, 0.5, 0.08), tool="bucket")
    ex["base"].location = (-6.6, 9.4, 0); ex["base"].rotation_euler = (0, 0, 0)
    pose_arm(ex, 0.0, math.radians(20), math.radians(80), math.radians(40))
    c["ex"] = ex
    # the pit (for the burial) by the back wall, with the lead block and a fill surface that rises
    pit_c = Vector((3.4, 14.2, 0))
    dirt = pbr("PitDirt", (0.17, 0.13, 0.1), 0.95)
    for dx, dy, sx, sy in ((0, -0.55, 1.7, 0.35), (0, 0.55, 1.7, 0.35), (-0.85, 0, 0.35, 1.4), (0.85, 0, 0.35, 1.4)):
        box("Berm", pit_c + Vector((dx, dy, 0.0)), (sx, sy, 0.12), dirt, bevel=0.05)
    box("PitHole", pit_c + Vector((0, 0, 0.002)), (1.4, 0.8, 0.004), pbr("PitDark", (0.04, 0.03, 0.025), 0.95))
    c["leadblock"] = box("LeadBlock", pit_c + Vector((0, 0, 0.06)), (0.5, 0.35, 0.12), k1["lead"], bevel=0.02)
    c["fill"] = box("Fill", pit_c + Vector((0, 0, -0.1)), (1.36, 0.76, 0.2), pbr("FillDirt", (0.2, 0.15, 0.1), 0.95), bevel=0.04)
    c["mound"] = box("Mound", pit_c + Vector((1.2, 0.2, 0.15)), (0.8, 0.7, 0.3), pbr("MoundDirt", (0.22, 0.17, 0.12), 0.95), bevel=0.12)
    c["pit"] = pit_c
    spade_root, spade_ms = ph_model("rusted_spade_01")
    c["spade"] = spade_root
    if spade_ms:
        lo, hi = ph.bounds(spade_ms); print("[ikitelli] spade bounds", lo, hi, flush=True)
    # sparks + torch flame light
    c["sparks"] = sparks("Spark", 70)
    c["torch_light"] = flicker_light("TorchLight", (0, 0, -20), energy=90)
    c["flame"] = box("Flame", (0, 0, -30), (0.015, 0.015, 0.06), emissive("Flame", (0.55, 0.7, 1.0), 40))
    c["torch_tool"] = cyl("TorchTool", (0, 0, -30), 0.012, 0.45, pbr("Brass", (0.5, 0.35, 0.12), 0.35, 1.0), verts=8)
    # people: brothers, relatives, workers (unnamed figures; no likeness)
    P = {}
    P["bro1"] = person("Bro1", 1.0, 38, "coat", "short02", cval=0.55, hue=0.47, sat=0.8)
    P["bro2"] = person("Bro2", 1.0, 33, "coat", "short04", cval=0.45, hue=0.52, sat=0.6, cap=True)
    P["worker"] = person("Worker", 1.0, 45, "coat", "short03", cval=0.35, hue=0.5, sat=0.5, weight=0.6)
    P["rel1"] = person("Rel1", 1.0, 60, "coat", "short02", cval=0.4, hue=0.46, sat=0.7, hv=0.7, cap=True)
    P["rel2"] = person("Rel2", 0.0, 50, "coat", "bob02", cval=0.6, hue=0.55, sat=0.8, hv=0.1)
    c["people"] = P
    for h in P.values():
        place(h, (0, -60, 0), 0)              # parked out of sight until a move uses them
    if dusk:
        for k, x in enumerate((-12, 6, 24)):
            l = bpy.data.lights.new("StreetLamp", 'POINT'); l.energy = 400; l.color = (1.0, 0.65, 0.35); l.shadow_soft_size = 0.2
            o = bpy.data.objects.new("StreetLamp", l); bpy.context.collection.objects.link(o); o.location = (x + 0.6, 3.6, 6.5)
            box("LampHead", (x + 0.6, 3.6, 6.62), (0.4, 0.2, 0.12), emissive("LampGlow", (1.0, 0.7, 0.4), 30))
        P["walker"] = P["rel1"]
    return c


# ============================================================================ helpers per shot
def hide_people(c, keep=()):
    for k, h in c["people"].items():
        if k not in keep:
            h.arm.location = (0, -60, 0)


def walk_to(h, a, b, sec, speed=1.1, stride=1.25, bob=True):
    """Walk from a toward b (stops at b). Returns the position."""
    a = Vector(a); b = Vector(b); d = (b - a); L_ = d.length
    s = min(L_, speed * sec)
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0)
    ph_ = (s / stride) % 1.0 if s < L_ else 0.0
    up = pose_walk(h, ph_, stride=24 if s < L_ else 0, arm_swing=12 if s < L_ else 0)
    p = a + d.normalized() * s
    place(h, (p.x, p.y, 0), face_angle(a, b))
    attach_cap(h)
    return p


def ex_rest(c):
    """Excavator parked with its arm folded (every shot but the peel)."""
    pose_arm(c["ex"], math.radians(-35), math.radians(42), math.radians(115), math.radians(100))


def set_truck(c, x, y, rot_z, roll=0.0):
    c["truck"].location = (x, y, 0); c["truck"].rotation_euler = (0, 0, rot_z)
    for w in c["wheels"]:
        w.rotation_euler = (0, roll / 0.45, 0)


def containers_in_bed(c, on=True):
    ex_rest(c)
    for k in ("tc1", "tc2"):
        c[k].hide_render = not on
    c["cont1"].location = C1 if not on else Vector((0, -80, 0))
    c["cont2"].location = C2 if not on else Vector((0, -80, 0))


# ============================================================================ animations
def anim_drive(c, t):
    sec = t * DUR["truck_drive"]
    containers_in_bed(c, True); hide_people(c, ("bro2",))
    v0 = 7.0; T = DUR["truck_drive"]
    x = -31 + v0 * sec - 0.25 * v0 * sec * sec / T      # rolls in and eases off
    set_truck(c, x, -1.2, 0.0, roll=-(x + 31))
    # a man on the verge watches it pass (life in the street)
    h = c["people"]["bro2"]
    stand_pose(h, head_down=0); place(h, (-8.0, -4.2, 0), face_angle((-8, -4.2), (x, -1.2))); attach_cap(h)
    c["focus"] = Vector((x + 2.5, -1.2, 1.4))


def cam_drive(c, t):
    e = ease(t)
    return (Vector((14.0, -2.6, 0.9)).lerp(Vector((13.0, -2.4, 1.1)), e), Vector((-14, 0.6, 2.0)), 40)


def anim_rope(c, t):
    sec = t * DUR["truck_rope"]
    containers_in_bed(c, True); hide_people(c, ("bro1",))
    set_truck(c, 1.0, 5.2, 0.0)
    h = c["people"]["bro1"]
    reset_pose(h); stand_pose(h)
    place(h, (0.15, 3.45, 0), face_angle((0.15, 3.45), (0.1, 6)))
    pull = math.sin(min(1.0, sec / 2.4) * math.pi / 2)      # hauls the rope down and tight
    M = c["truck"].matrix_world
    top = M @ Vector((-0.9, -1.05, c["bed_z"] + 0.45))
    hand = top + Vector((0.0, -0.42, -0.05 - 0.35 * pull))
    c["rope_spline"].points[4].co = (*(M.inverted() @ (hand + Vector((0, 0, -0.25)))), 1)
    reach(h, "R", hand + Vector((0.05, 0, 0)), Vector((0.6, -0.3, -0.6)), Vector((0, 0.4, -1)))
    reach(h, "L", hand + Vector((-0.08, 0, 0.18)), Vector((-0.6, -0.3, -0.6)), Vector((0, 0.4, -1)))
    fingers_curl(h, 70, thumb=40)
    h.rot("spine03", (1, 0, 0), -8 * pull)
    c["rope"].hide_render = False
    c["focus"] = h.bone_head("spine05")


def cam_rope(c, t):
    e = ease(t)
    return (Vector((-3.6, 1.5, 0.95)).lerp(Vector((-2.0, 1.55, 1.0)), e), Vector((0.9, 5.0, 1.45)), 32)


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


def anim_torch(c, t):
    sec = t * DUR["torch"]
    containers_in_bed(c, False); hide_people(c, ("worker", "bro2"))
    set_truck(c, 3.5, 13.5, math.radians(180))
    cont = c["cont2"]
    target = cont.matrix_world @ Vector((-0.39, -0.12, 0.62))
    torch_man(c, c["people"]["worker"], sec, target, (C2.x - 1.05, C2.y - 0.45, 0))
    h = c["people"]["bro2"]; stand_pose(h, hands_pockets=True); place(h, (C2.x + 1.5, C2.y + 0.6, 0), face_angle((C2.x + 1.5, C2.y + 0.6), C2)); attach_cap(h)
    c["focus"] = target


def cam_torch(c, t):
    e = ease(t)
    tgt = C2 + Vector((-0.6, -0.35, 1.1))
    return (C2 + Vector((0.35, -4.4, 1.3)).lerp(Vector((0.15, -3.9, 1.3)), e), tgt, 38)


def anim_peel(c, t):
    sec = t * DUR["peel"]
    containers_in_bed(c, False); hide_people(c, ("worker", "bro1"))
    set_truck(c, 3.5, 13.5, math.radians(180))
    ex = c["ex"]; k = ease(min(1.0, sec / DUR["peel"]))
    # shell swings out about its hinge while the bucket, hooked over its top edge, pulls it
    c["hinge"].rotation_euler = (math.radians(8 + 62 * k), 0, 0)
    bpy.context.view_layer.update()
    edge = c["hinge"].matrix_world @ Vector((0, -0.41, 0.8))
    arm_ik(ex, edge + Vector((-0.35, 0, 0.55)))
    b_ = ex["boom"].rotation_euler.y; s_ = ex["stick"].rotation_euler.y
    ex["tool"].rotation_euler = (0, -(b_ + s_) + math.radians(95), 0)
    pose_sparks(c["sparks"], (0, 0, -50), 0, on=False)
    c["flame"].location = (0, 0, -30); c["torch_tool"].location = (0, 0, -30); c["torch_light"].location = (0, 0, -20)
    walk_to(c["people"]["worker"], (C1.x + 0.9, C1.y - 0.6, 0), (C1.x + 2.0, C1.y - 2.6, 0), sec * 0.8, speed=0.9)
    walk_to(c["people"]["bro1"], (C1.x + 0.1, C1.y - 1.0, 0), (C1.x - 0.3, C1.y - 3.0, 0), max(0, sec - 0.4) * 0.8, speed=0.8)
    c["focus"] = C1 + Vector((0, 0, 0.8))


def cam_peel(c, t):
    e = ease(t)
    return (Vector((-1.6, 1.2, 3.1)).lerp(Vector((-2.4, 1.8, 2.9)), e), Vector((-3.3, 9.2, 1.0)), 27)


def anim_steady(c, t):
    sec = t * DUR["steady"]
    containers_in_bed(c, False); hide_people(c, ("worker",))
    set_truck(c, 1.5, 12.8, math.radians(180))
    c["hinge"].rotation_euler = (math.radians(70), 0, 0)
    pose_sparks(c["sparks"], (0, 0, -50), 0, on=False)
    h = c["people"]["worker"]
    a = Vector((-1.0, 10.6, 0)); b = Vector((0.0, 11.25, 0))
    stop = 1.4
    if sec < stop:
        walk_to(h, a, b, sec, speed=(b - a).length / stop)
        lean = 0
    else:
        reset_pose(h); stand_pose(h)
        place(h, b, face_angle(a, b) + math.radians(25))
        lean = ease(min(1.0, (sec - stop) / 1.2))
        side = forward(h).cross(Vector((0, 0, 1))).normalized()
        h.rot("spine03", side, -14 * lean); h.rot("spine05", side, -8 * lean)
        h.rot("neck01", side, -14 * lean); h.rot("head", side, -10 * lean)
        breath = 0.01 * math.sin(sec * 2.0)
        hand = c["truck"].matrix_world @ Vector((-1.4, -1.06, 1.38)) + Vector((0, 0, breath))
        reach(h, "R", hand.lerp(h.bone_head("upperarm01.R") + Vector((0, 0, -0.5)), 1 - lean), Vector((0.3, -0.5, -0.7)), Vector((0, 0, -1)))
        fingers_curl(h, 25)
    attach_cap(h)
    c["focus"] = h.bone_head("spine05")


def cam_steady(c, t):
    e = ease(t)
    return (Vector((3.0, 9.3, 1.45)).lerp(Vector((2.7, 9.6, 1.48)), e), Vector((0.1, 11.3, 1.2)), 40)


def anim_relatives(c, t):
    sec = t * DUR["relatives"]
    containers_in_bed(c, False); hide_people(c, ("rel1", "rel2", "worker"))
    set_truck(c, 3.5, 13.5, math.radians(180))
    c["hinge"].rotation_euler = (math.radians(70), 0, 0)
    a1 = Vector((-5.4, 3.6, 0)); a2 = Vector((-4.6, 3.3, 0))
    h1 = c["people"]["rel1"]; stand_pose(h1, hands_pockets=True); place(h1, a1, face_angle(a1, C1)); attach_cap(h1)
    h2 = c["people"]["rel2"]
    turn = ease(min(1.0, max(0.0, (sec - 0.9) / 1.6)))
    stand_pose(h2, head_down=14 * turn)
    place(h2, a2, face_angle(a2, C1) + math.radians(150) * turn)
    side = forward(h2).cross(Vector((0, 0, 1))).normalized()
    h2.rot("spine03", side, -10 * turn)
    hw = c["people"]["worker"]; stand_pose(hw); place(hw, (C1.x + 0.9, C1.y - 0.6, 0), face_angle((C1.x + 0.9, C1.y - 0.6), C1))
    if "glass" not in c:
        c["glass"] = tulip_glass((-4.0, 4.3, 0.95)); c["steam"] = steam("Steam", (-4.0, 4.3, 1.05))
    pose_steam(c["steam"], (-4.0, 4.3, 1.06), sec)
    c["focus"] = Vector((-4.0, 4.3, 1.0))


def cam_relatives(c, t):
    e = ease(t)
    return (Vector((-2.45, 3.75, 1.12)).lerp(Vector((-2.65, 3.8, 1.12)), e), Vector((-5.3, 3.75, 1.2)), 40)


def anim_bury(c, t):
    sec = t * DUR["bury"]
    containers_in_bed(c, False); hide_people(c, ("bro1",))
    set_truck(c, -40.0, 40.0, 0.0)
    c["hinge"].rotation_euler = (math.radians(70), 0, 0)
    pit = c["pit"]; h = c["people"]["bro1"]
    stance = pit + Vector((1.0, -0.55, 0))
    reset_pose(h); stand_pose(h)
    place(h, stance, face_angle(stance, pit) + math.radians(35))
    cyc = (sec / 1.6) % 1.0                                   # scoop from the mound, swing, tip over the pit
    k = 0.5 - 0.5 * math.cos(2 * math.pi * cyc)
    fwd = forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    h.rot("spine03", side, -(12 + 16 * (1 - k)))
    blade = (pit + Vector((1.2, 0.3, 0.1))).lerp(pit + Vector((0.2, 0.05, 0.35)), k)
    handle = blade + (Vector(stance) + Vector((0, 0, 1.05)) - blade).normalized() * 0.95
    reach(h, "R", handle, Vector((side.x, side.y, -0.6)), blade - handle)
    reach(h, "L", handle.lerp(blade, 0.45), Vector((-side.x, -side.y, -0.6)), blade - handle)
    fingers_curl(h, 70, thumb=40)
    sp = c["spade"]
    if sp is not None:
        sp.location = blade + (handle - blade).normalized() * 0.5; sp.rotation_mode = 'QUATERNION'
        sp.rotation_quaternion = (handle - blade).to_track_quat('Z', 'Y')
    fill = ease(min(1.0, sec / DUR["bury"])) * 0.6 + 0.3
    c["fill"].location = pit + Vector((0, 0, -0.1 + 0.2 * fill))
    c["mound"].scale = (1, 1, 1 - 0.4 * fill)
    attach_cap(h)
    c["focus"] = pit + Vector((0.4, 0, 0.5))


def cam_bury(c, t):
    e = ease(t)
    p = c["pit"]
    return (p + Vector((-2.9, -2.6, 1.05)).lerp(Vector((-2.6, -2.3, 1.05)), e), p + Vector((0.7, 0.2, 0.75)), 32)


def anim_dusk(c, t):
    sec = t * DUR["dusk"]
    containers_in_bed(c, False); hide_people(c, ("rel1",))
    set_truck(c, -40.0, 40.0, 0.0)
    c["ex"]["base"].location = (-40, 50, 0)
    c["hinge"].rotation_euler = (math.radians(70), 0, 0)
    c["fill"].location = c["pit"] + Vector((0, 0, 0.09)); c["mound"].scale = (1, 1, 0.5)
    for k, e in enumerate(c["laundry"]):
        e.rotation_euler = (math.radians(9 * math.sin(sec * 1.3 + k * 0.9) + 4), 0, math.radians(-60))
    walk_to(c["people"]["rel1"], (12, -1.8, 0), (-14, -1.8, 0), sec, speed=1.0)
    c["focus"] = Vector((-4.6, 13.6, 0.6))


def cam_dusk(c, t):
    e = ease(t)
    return (Vector((1.8, -0.8, 1.65)).lerp(Vector((0.6, 3.2, 1.55)), e), Vector((-2.2, 12.8, 0.9)), 28)


def _focus(c, t):
    return c.get("focus", Vector((0, 10, 1)))


MOVES = {
    "truck_drive": dict(kind="anim", dof=4.0, far=200.0, anim=anim_drive, cam=cam_drive, focus=_focus),
    "truck_rope": dict(kind="anim", dof=2.8, far=100.0, anim=anim_rope, cam=cam_rope, focus=_focus),
    "torch": dict(kind="anim", dof=2.8, far=100.0, anim=anim_torch, cam=cam_torch, focus=_focus),
    "peel": dict(kind="anim", dof=5.6, far=100.0, anim=anim_peel, cam=cam_peel, focus=_focus),
    "steady": dict(kind="anim", dof=2.8, far=100.0, anim=anim_steady, cam=cam_steady, focus=_focus),
    "relatives": dict(kind="anim", dof=2.0, far=100.0, anim=anim_relatives, cam=cam_relatives, focus=_focus),
    "bury": dict(kind="anim", dof=3.5, far=100.0, anim=anim_bury, cam=cam_bury, focus=_focus),
    "dusk": dict(kind="anim", dof=5.6, far=200.0, anim=anim_dusk, cam=cam_dusk, focus=_focus),
}
