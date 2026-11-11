"""THE DRAIN (hero set): the yard of a pavillon in Les Pavillons-sous-Bois, March 2011, grey drizzle.
A zinc downpipe feeds a square cast-iron rainwater grate set in the concrete; BESIDE it, a patch of concrete a little
lighter than the rest. Garden: grass edges, gravel, a hedge, a low wall with railings and a gate.
  walk      (intro 1A): crane down over the wet yard as three officers walk from the gate toward the drain
  patch     (intro 1B): low, close push along the wet concrete to the pale patch beside the grate, rain rings in a puddle
  drill     (intro 2A): an officer kneels and drills the patch, grey dust puffing into the rain (medium)
  container (intro 2B): the grimy tub, lid half off, the rings bundled inside; the camera eases in as the diamond catches light
  yard      (ch3 5A): an officer walks slowly round the yard looking down
  gate      (ch3 6A): the fifth visit: officers come back in through the gate under black umbrellas
  torch     (ch3 6B): high angle; only a torch beam pool sliding across the concrete onto the patch
  circle    (ch3 7A): slow circle over the open tub in the rain
  bag       (ch3 7B): medium-wide: a photographer's flash pops and lights the open tub, a yellow evidence marker beside it
"""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector
from kit import *
import ph
import dd
from dd import person, officer, place, face_to, walk_to, arms_relaxed, pose_kneel, pose_crouch, zero, rain, rain_fall
from human import reach, fingers_curl, pose_walk
from sc_street import car

EXPOSURE = -0.6
BOUNCES = 8
HOUSE_Y = 5.0
DRAIN = Vector((4.0, 4.62, 0.0))        # centre of the cast-iron grate
PATCH = Vector((3.3, 4.45, 0.0))        # the lighter concrete patch beside it
PATCH_SIZE = (0.5, 0.4)
GATE = Vector((1.7, -5.0, 0.0))
LEAD = 2.5
DUR = {"walk": LEAD + 8.0, "patch": 9.0, "drill": 9.0, "container": 9.0,
       "yard": 9.0, "gate": 9.0, "torch": 9.0, "circle": 9.0, "bag": 9.0}
VARIANT_FOR = {"walk": "walk", "patch": "patch", "drill": "drill", "container": "open", "yard": "yard",
               "gate": "gate", "torch": "torch", "circle": "open", "bag": "bag"}
CONT_SIZE = (0.17, 0.12, 0.075)
CONT_AT = Vector((2.75, 4.05, 0.0))


def grate(loc, size=0.4):
    """Square cast-iron grid cover in a steel frame, sitting flush; a dark sump shows between the bars."""
    iron = muddy_iron = dd.muddy(pbr("CastIron", (0.05, 0.05, 0.05), 0.5, 0.7), 0.35, (0.1, 0.09, 0.07))
    B = dd.Builder("Grate")
    B.box((0, 0, -0.06), (size - 0.02, size - 0.02, 0.1), pbr("Sump", (0.008, 0.008, 0.008), 0.9))
    for dx, dy, sx, sy in ((-1, 0, 0.03, size), (1, 0, 0.03, size), (0, -1, size, 0.03), (0, 1, size, 0.03)):
        B.box((dx * (size / 2 - 0.015), dy * (size / 2 - 0.015), -0.012), (sx, sy, 0.026), iron)
    n = 9
    for k in range(n):
        B.box((-size / 2 + 0.03 + k * (size - 0.06) / (n - 1), 0, -0.012), (0.012, size - 0.04, 0.025), iron)
    for k in range(3):
        B.box((0, -size / 2 + 0.1 + k * (size - 0.2) / 2, -0.016), (size - 0.04, 0.01, 0.018), iron)
    return B.done(loc)


def drill_tool():
    """Poly Haven cordless drill, standing upright with its bit down; origin near the bit tip."""
    root = dd.model_h("Drill_01", (0, 0, 0), 0.26)
    if root is None:
        return cyl("Drill", (0, 0, 0.15), 0.03, 0.3, pbr("DrillM", (0.1, 0.1, 0.1), 0.5))
    holder = bpy.data.objects.new("DrillRig", None); bpy.context.collection.objects.link(holder)
    root.parent = holder; root.rotation_euler = (0, math.radians(90), 0); root.location = (0.0, 0.0, 0.1)
    return holder


def dust_volume(loc, r=0.28):
    """Concrete dust puffing up out of the pit: a volume whose density churns with frame-driven noise."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=24, ring_count=12)
    o = bpy.context.active_object; o.name = "Dust"; o.scale = (1.0, 1.0, 1.4)
    m = bpy.data.materials.new("Dust"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs['Color'].default_value = (0.62, 0.6, 0.56, 1)
    tc = N.new("ShaderNodeTexCoord")
    t = dd.frame_value(N, "frame / 24.0")
    rise = N.new("ShaderNodeCombineXYZ"); tz = N.new("ShaderNodeMath"); tz.operation = 'MULTIPLY'; tz.inputs[1].default_value = -0.25
    L.new(t.outputs[0], tz.inputs[0]); L.new(tz.outputs[0], rise.inputs['Z'])
    add = N.new("ShaderNodeVectorMath"); add.operation = 'ADD'; L.new(tc.outputs['Object'], add.inputs[0]); L.new(rise.outputs[0], add.inputs[1])
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 7.0; nz.inputs['Detail'].default_value = 4
    L.new(add.outputs[0], nz.inputs['Vector']); L.new(t.outputs[0], nz.inputs['W'])
    # spherical falloff
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(tc.outputs['Object'], ln.inputs[0])
    fo = N.new("ShaderNodeMapRange"); fo.inputs['From Min'].default_value = r * 0.3; fo.inputs['From Max'].default_value = r
    fo.inputs['To Min'].default_value = 1.0; fo.inputs['To Max'].default_value = 0.0; L.new(ln.outputs['Value'], fo.inputs['Value'])
    dn = N.new("ShaderNodeMapRange"); dn.inputs['From Min'].default_value = 0.45; dn.inputs['From Max'].default_value = 0.75
    dn.inputs['To Max'].default_value = 9.0; L.new(nz.outputs['Fac'], dn.inputs['Value'])
    # pulses with the hammer action
    pulse = dd.frame_value(N, "0.55 + 0.45 * abs(sin(frame * 0.9))", "Pulse")
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(dn.outputs[0], m1.inputs[0]); L.new(fo.outputs[0], m1.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(pulse.outputs[0], m2.inputs[1])
    L.new(m2.outputs[0], vol.inputs['Density']); L.new(vol.outputs[0], out.inputs['Volume'])
    o.data.materials.append(m); o.visible_shadow = False
    return o




def umbrella(name, radius=0.47):
    """A black umbrella: a deep domed canopy in 8 gores (each sagging between its ribs), visible ribs ending in tips,
    a shaft, and a hooked J handle. Modelled with the canopy tip at the origin; the shaft runs down -Z."""
    fabric_m = pbr(name + "Canopy", (0.006, 0.006, 0.007), 0.55, 0.0, **{'Coat Weight': 0.15, 'Coat Roughness': 0.2})
    metal = pbr(name + "Metal", (0.35, 0.35, 0.37), 0.3, 0.9)
    grip = pbr(name + "Grip", (0.07, 0.04, 0.02), 0.35)
    bm = bmesh.new()
    nr, na = 10, 64
    rows = []
    for i in range(nr + 1):
        u = i / nr                                     # 0 at the tip, 1 at the rim
        row = []
        for j in range(na):
            a = 2 * math.pi * j / na
            sag = 0.5 - 0.5 * math.cos(8 * a)         # 0 on a rib, 1 mid-gore
            r = radius * math.sin(u * math.pi / 2) * (1 - 0.1 * sag * u ** 3)
            z = -0.52 * radius * (1 - math.cos(u * math.pi / 2)) + 0.05 * sag * u ** 4
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rows.append(row)
    for i in range(nr):
        for j in range(na):
            j2 = (j + 1) % na
            bm.faces.new((rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    can = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(can)
    can.data.materials.append(fabric_m)
    for p_ in me.polygons:
        p_.use_smooth = True
    can.modifiers.new("sol", 'SOLIDIFY').thickness = 0.003
    B = dd.Builder(name + "Frame")
    for k in range(8):                                   # ribs along the canopy underside, tips at the rim
        a = k * math.pi / 4
        for i in range(nr):
            u0, u1 = i / nr, (i + 1) / nr
            p0 = Vector((radius * math.sin(u0 * math.pi / 2) * math.cos(a), radius * math.sin(u0 * math.pi / 2) * math.sin(a), -0.52 * radius * (1 - math.cos(u0 * math.pi / 2)) - 0.004))
            p1 = Vector((radius * math.sin(u1 * math.pi / 2) * math.cos(a), radius * math.sin(u1 * math.pi / 2) * math.sin(a), -0.52 * radius * (1 - math.cos(u1 * math.pi / 2)) - 0.004))
            d = p1 - p0; mid = (p0 + p1) / 2
            B.cyl(mid, 0.003, d.length, metal, verts=6, rot=d.to_track_quat('Z', 'Y').to_euler())
        tip = Vector((radius * 1.01 * math.cos(a), radius * 1.01 * math.sin(a), -0.52 * radius - 0.01))
        B.cyl(tip, 0.005, 0.025, metal, verts=6)
    B.cyl((0, 0, 0.03), 0.004, 0.06, metal, verts=6)
    B.cyl((0, 0, -0.42), 0.006, 0.84, metal, verts=8)
    B.cyl((0, 0, -0.88), 0.013, 0.1, grip, verts=10)
    for k in range(9):                                   # the hooked J handle
        a0 = math.pi * k / 8; a1 = math.pi * (k + 1) / 8
        p0 = Vector((0.04 - 0.04 * math.cos(a0), 0, -0.93 - 0.04 * math.sin(a0)))
        p1 = Vector((0.04 - 0.04 * math.cos(a1), 0, -0.93 - 0.04 * math.sin(a1)))
        d = p1 - p0
        if d.length > 1e-4:
            B.cyl((p0 + p1) / 2, 0.012, d.length + 0.004, grip, verts=8, rot=d.to_track_quat('Z', 'Y').to_euler())
    fr = B.done(); fr.parent = can
    return can


def wet_concrete(name, tint=(0.62, 0.62, 0.6), scale=0.5, puddles=0.42):
    m = dd.tex_mat("concrete_floor_worn_001", scale, tint=tint, name=name, sat=0.35)
    return dd.wet(m, 0.75, puddles, ripple_scale=7.0)


def build_yard(c, variant):
    rng = np.random.default_rng(11)
    w = world_sky(sun_elev_deg=20, sun_rot_deg=230, strength=0.22, tint=(0.8, 0.85, 0.95), air=3.0, aerosol=10.0)
    sky = [n for n in w.node_tree.nodes if n.type == 'TEX_SKY'][0]; sky.sun_disc = False
    sun(35, 230, energy=0.35, color=(0.9, 0.94, 1.0), angle_deg=40)
    # yard slab: concrete with expansion joints; the patch is a separate, paler, drier rectangle
    yard = wet_concrete("Yard")
    B = dd.Builder("YardSlab")
    B.box((0.5, 1.0, -0.05), (11.0, 8.0, 0.1), yard)
    for k in range(5):
        B.box((-4.5 + k * 2.5, 1.0, 0.0005), (0.012, 8.0, 0.002), pbr("Joint", (0.1, 0.1, 0.1), 0.8))
    B.done()
    patch_m = dd.tex_mat("concrete_floor_worn_001", 0.9, tint=(0.86, 0.85, 0.82), name="Patch", sat=0.3)
    patch_m = dd.wet(patch_m, 0.25, 0.9, ripples=False)
    opened = variant in ("open", "bag")
    if not opened:
        c["patch"] = box("Patch", PATCH + Vector((0, 0, 0.002)), (PATCH_SIZE[0], PATCH_SIZE[1], 0.006), patch_m, bevel=0.003)
    else:
        box("Hole", PATCH + Vector((0, 0, 0.001)), (PATCH_SIZE[0] - 0.08, PATCH_SIZE[1] - 0.08, 0.004), pbr("HoleDark", (0.02, 0.016, 0.012), 0.9))
        for k in range(10):                          # broken lumps of the patch at its edges
            a = rng.uniform(0, 6.28)
            p = PATCH + Vector((0.27 * math.cos(a), 0.22 * math.sin(a), 0.012))
            box("Chunk", p, (rng.uniform(0.04, 0.09), rng.uniform(0.03, 0.07), rng.uniform(0.02, 0.035)), patch_m,
                rot=(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0, 3)))
        for k in range(30):                          # grit
            a = rng.uniform(0, 6.28); r_ = rng.uniform(0.25, 0.5)
            box("Grit", PATCH + Vector((r_ * math.cos(a), r_ * math.sin(a), 0.004)), (0.012, 0.01, 0.008), patch_m, rot=(0, 0, rng.uniform(0, 3)))
    c["grate"] = grate(DRAIN + Vector((0, 0, 0.004)))
    # house and the downpipe elbow into the grate
    house, hi = dd.pavillon((0, HOUSE_Y, 0), w=9.0, d=8.0, floors=2, name="House")
    zinc = pbr("Zinc2", (0.42, 0.44, 0.45), 0.35, 0.9)
    cyl("PipeDown", (4.0, HOUSE_Y - 0.12, 0.42), 0.045, 0.6, zinc, verts=12)
    cyl("PipeShoe", (4.0, HOUSE_Y - 0.2, 0.1), 0.047, 0.22, zinc, verts=12, rot=(math.radians(-35), 0, 0))
    dd.model_h("metal_trash_can", (5.6, 4.5, 0), 0.95, rot_z=0.3)
    dd.model_h("plastic_crate_02", (-3.8, 4.4, 0), 0.32, rot_z=0.2)
    # garden: lawn strips, a gravel path from the gate to the door, the hedge, plants, a garden table
    lawn = dd.tex_mat("leafy_grass", 0.5, tint=(0.7, 0.78, 0.62), name="Lawn", sat=0.7)
    gravel = dd.wet(dd.tex_mat("gravel_floor", 0.8, tint=(0.75, 0.73, 0.7), name="Gravel", sat=0.5), 0.4, ripples=False)
    G = dd.Builder("Garden")
    G.box((-5.5, 0.0, -0.03), (3.0, 10.0, 0.06), lawn).box((7.2, 0.0, -0.03), (1.4, 10.0, 0.06), lawn)
    G.box((0.5, -4.2, -0.03), (11.0, 1.6, 0.06), lawn)
    G.box((1.7, -4.2, 0.0), (1.2, 1.6, 0.02), gravel)
    G.box((-0.3, -1.4, 0.0), (1.2, 4.4, 0.02), gravel)
    G.box((0.5, -3.0, 0.0), (11.0, 0.12, 0.05), pbr("Edging", (0.45, 0.44, 0.42), 0.7))
    G.done()
    for x, y, rz in ((-6.0, -3.6, math.pi / 2), (-6.0, 1.6, math.pi / 2), (7.6, -3.0, -math.pi / 2), (7.6, 2.4, -math.pi / 2)):
        try:
            ph.model("shrub_02", loc=(x, y, 0), rot_z=rz, scale=1.15)
        except Exception as e:
            print("[drain] shrubs skipped", e)
    dd.model_h("tree_small_02", (-5.2, 3.6, 0), 4.6, rot_z=0.6)
    dd.model_h("outdoor_table_chair_set_01", (-2.6, 3.4, 0), 0.9, rot_z=0.3)
    dd.model_h("planter_box_01", (-1.4, 4.5, 0), 0.55)
    dd.model_h("potted_plant_02", (1.0, 4.5, 0), 0.75)
    dd.model_h("watering_can_metal_01", (5.6, 4.4, 0), 0.3, rot_z=1.2)
    dd.model_h("garden_hose_wall_mounted_01", (-3.6, HOUSE_Y - 0.12, 0.6), 0.45)
    # front wall with railings and the gate
    wallm = dd.tex_mat("plastered_wall_03", 0.6, tint=(0.88, 0.85, 0.78), name="FrontWall", sat=0.6)
    cap = pbr("WallCap", (0.55, 0.54, 0.52), 0.7)
    rail = pbr("Railing", (0.06, 0.08, 0.07), 0.45, 0.7)
    W = dd.Builder("FrontWall")
    for xa, xb in ((-7.0, GATE.x - 0.6), (GATE.x + 0.6, 8.0)):
        W.box(((xa + xb) / 2, -5.0, 0.4), (xb - xa, 0.25, 0.8), wallm).box(((xa + xb) / 2, -5.0, 0.83), (xb - xa, 0.32, 0.06), cap)
        n = int((xb - xa) / 0.13)
        for k in range(n):
            W.box((xa + 0.07 + k * 0.13, -5.0, 1.2), (0.014, 0.014, 0.7), rail)
            W.box((xa + 0.07 + k * 0.13, -5.0, 1.57), (0.03, 0.03, 0.05), rail)
        W.box(((xa + xb) / 2, -5.0, 1.52), (xb - xa, 0.04, 0.03), rail).box(((xa + xb) / 2, -5.0, 0.95), (xb - xa, 0.04, 0.03), rail)
    for sx in (-0.65, 0.65):
        W.box((GATE.x + sx, -5.0, 0.85), (0.32, 0.32, 1.7), wallm).box((GATE.x + sx, -5.0, 1.73), (0.38, 0.38, 0.08), cap)
    for x in (-6.9, 7.9):
        W.box((x, 0.0, 0.9), (0.2, 10.0, 1.8), wallm)
    W.done()
    gl = dd.Builder("Gate")
    gl.box((0.55, 0, 0.12), (1.1, 0.04, 0.05), rail).box((0.55, 0, 1.3), (1.1, 0.04, 0.05), rail)
    for k in range(10):
        gl.box((0.05 + k * 0.111, 0, 0.72), (0.016, 0.016, 1.2), rail)
    c["gate_leaf"] = gl.done((GATE.x - 0.55, -5.0, 0.05), math.radians(-75))
    # neighbours, the street, parked cars
    dd.pavillon((-12.5, 6.5, 0), w=8.0, d=8.0, floors=2, name="NeighW", stone=False, shutters=(0.0, 1.0, 0.5))
    dd.pavillon((13.0, 7.0, 0), w=8.0, d=8.0, floors=2, name="NeighE", stone=True, shutters=(0.8, 0.0, 0.3))
    dd.pavillon((0.0, 24.0, 0), w=10.0, d=8.0, floors=2, name="Behind", stone=False)
    for k, x in enumerate((-14.0, -3.0, 8.0, 19.0)):          # the houses across the street
        dd.pavillon((x, -16.0, 0), w=8.5, d=8.0, floors=2, rot_z=math.pi, name=f"Opp{k}", stone=(k % 2 == 0), shutters=(0.6, 1.0, 0.2))
        box(f"OppWall{k}", (x, -15.2, 0.5), (8.0, 0.25, 1.0), wallm)
    dd.model_h("jacaranda_tree", (-8.5, -14.5, 0), 7.5, rot_z=1.0)
    dd.model_h("island_tree_02", (9.5, 14.0, 0), 8.0, rot_z=2.0)
    dd.model_h("island_tree_01", (-10.0, 16.0, 0), 7.0)
    road = dd.wet(dd.tex_mat("asphalt_02", 0.4, tint=(0.6, 0.6, 0.62), name="Road", sat=0.4), 0.8, 0.3)
    box("Road", (0, -10.5, -0.06), (60, 9, 0.1), road)
    box("Pave", (0, -5.8, 0.0), (60, 1.4, 0.1), wet_concrete("Pavement", (0.55, 0.55, 0.54), 0.6))
    for k, (x, col) in enumerate(((-6.0, (0.12, 0.13, 0.15)), (5.5, (0.35, 0.36, 0.38)), (11.0, (0.42, 0.1, 0.07)))):
        cr = dd.sedan(f"Parked{k}", col, lights=False); cr.location = (x, -7.6, 0)
    box("Ground", (0, 10, -0.65), (80, 40, 0.1), pbr("Earth", (0.06, 0.07, 0.05), 0.9))
    c["rain_ys"] = (-3.5, -1.0, 1.5, 3.6)
    rain(c, 0, c["rain_ys"], width=30, height=8, strength=4.0, density=0.975)


def build(variant=None):
    c = {"variant": variant}
    v = variant or "walk"
    build_yard(c, v)
    rng = np.random.default_rng(5)
    if v == "walk":
        c["walkers"] = []
        starts = [Vector((1.5, -2.6, 0)), Vector((0.7, -3.5, 0)), Vector((2.3, -4.2, 0))]
        ends = [PATCH + Vector((-0.6, -0.8, 0)), DRAIN + Vector((0.5, -0.9, 0)), PATCH + Vector((-1.3, -0.4, 0))]
        for k in range(3):
            h = officer(f"Off{k}", 35 + 7 * k, seed=k)
            c["walkers"].append((h, starts[k], ends[k], 0.5 * k))
    if v == "drill":
        h = officer("Driller", 38, seed=1); c["driller"] = h
        w = officer("Watcher", 50, seed=3); wp = PATCH + Vector((-0.95, 0.15, 0)); place(w, wp, face_to(wp, PATCH)); arms_relaxed(w)
        c["drill"] = drill_tool()
        c["dust"] = dust_volume(PATCH + Vector((0, 0, 0.1)), 0.32)
    if v in ("open", "bag"):
        box_ = dd.container("Container", CONT_AT, CONT_SIZE, rot_z=0.35, lid_open=1.0)
        c["box"] = box_
        hero, items = dd.fill_container(box_, CONT_SIZE, rng)
        c["hero"] = hero
        k = bpy.data.lights.new("Glint", 'AREA'); k.size = 0.4; k.energy = 14; k.color = (1.0, 0.97, 0.93)
        ko = bpy.data.objects.new("Glint", k); bpy.context.collection.objects.link(ko); ko.visible_camera = False
        c["glint"] = ko
        for j in range(3):                           # tiny hard sparkle sources
            pl = bpy.data.lights.new("Spark", 'POINT'); pl.energy = 6; pl.shadow_soft_size = 0.001
            po = bpy.data.objects.new("Spark", pl); bpy.context.collection.objects.link(po); po.location = CONT_AT + Vector((-0.3 + 0.25 * j, -0.35, 0.5))
        if v == "open":
            o = officer("Stand", 45, seed=0); sp = CONT_AT + Vector((-0.9, 0.35, 0)); place(o, sp, face_to(sp, CONT_AT)); arms_relaxed(o)
        if v == "bag":
            mk = pbr("Marker", (0.85, 0.62, 0.05), 0.4)
            for sg in (-1, 1):
                box("MarkerSide", CONT_AT + Vector((0.22, -0.18 + sg * 0.025, 0.045)), (0.09, 0.005, 0.1), mk, rot=(sg * 0.45, 0, 0.3))
            fl = bpy.data.lights.new("Flash", 'AREA'); fl.size = 0.12; fl.color = (0.95, 0.97, 1.0)
            dr = fl.driver_add("energy").driver; dr.type = 'SCRIPTED'
            dr.expression = "260 * (max(0, 1 - abs(frame - 60) / 2.5) + max(0, 1 - abs(frame - 150) / 2.5))"
            fo = bpy.data.objects.new("Flash", fl); bpy.context.collection.objects.link(fo); fo.visible_camera = False
            c["flash"] = fo
            ph_ = officer("Photographer", 33, seed=1, gender=0.0); c["photog"] = ph_
            cam_b = dd.model_h("Camera_01", (0, 0, 0), 0.12); c["camera_prop"] = cam_b
    if v == "yard":
        c["searcher"] = officer("Searcher", 44, seed=4)
    if v == "gate":
        c["walkers"] = []
        for k in range(3):
            h = officer(f"Ret{k}", 36 + 6 * k, seed=k + 2)
            u = umbrella(f"Umb{k}") if k != 1 else None
            c["walkers"].append((h, GATE + Vector((0.15 * k, -2.0 - 1.3 * k, 0)), Vector((0.4 + 1.0 * k, 1.2 - 0.6 * k, 0)), 0.6 * k, u))
    if v == "torch":
        tl = bpy.data.lights.new("TorchBeam", 'SPOT'); tl.energy = 320; tl.spot_size = math.radians(18); tl.spot_blend = 0.3
        tl.color = (1.0, 0.95, 0.85); tl.shadow_soft_size = 0.01
        to = bpy.data.objects.new("TorchBeam", tl); bpy.context.collection.objects.link(to); c["torch"] = to
        h = officer("Torch", 41, seed=2); c["torcher"] = h
    return c


# ============================================================================ animation
def anim_walk(c, t):
    sec = t * DUR["walk"]
    rain_fall(c, sec)
    for h, a, b, delay in c["walkers"]:
        walk_to(h, a, b, max(0.0, sec - delay), speed=0.95)


def anim_drill(c, t):
    sec = t * DUR["drill"]
    rain_fall(c, sec)
    h = c["driller"]
    pose_kneel(h, lean=36)
    pos = PATCH + Vector((0.5, -0.1, 0))
    h.arm.rotation_euler = (0, 0, face_to(pos, PATCH)); h.arm.location = pos; dd.ground(h)
    jit = 0.003 * math.sin(sec * 55)
    tip = PATCH + Vector((0.04, 0.02, 0.006 + jit))
    d = c["drill"]; d.location = tip; d.rotation_euler = (0, 0, math.radians(180))
    top = tip + Vector((0, 0, 0.3))
    reach(h, "R", top + Vector((0.0, -0.06, 0.0)), Vector((-0.6, -0.5, -0.4)))
    reach(h, "L", top + Vector((0.06, -0.02, -0.08)), Vector((0.6, -0.5, -0.4)))
    fingers_curl(h, 55, thumb=25)
    mid = (h.bone_tail("wrist.L") + h.bone_tail("wrist.R")) / 2           # the drill sits in his hands, bit down to the patch
    d.location = Vector((mid.x, mid.y, max(PATCH.z + 0.01, mid.z - 0.24 + jit)))


def anim_open(c, t, dur):
    sec = t * dur
    rain_fall(c, sec)
    g = c["glint"]
    g.location = CONT_AT + Vector((-0.6 + 0.35 * t, -0.45 - 0.1 * t, 0.75)); point_at(g, CONT_AT)


def anim_bag(c, t):
    anim_open(c, t, DUR["bag"])
    h = c["photog"]
    sp = CONT_AT + Vector((0.55, -0.9, 0))
    zero(h); pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    for b_, a_ in (("spine03", 8), ("spine04", 6), ("neck01", 8), ("head", 18)):
        h.rot(b_, (1, 0, 0), a_)                                          # leaning a little to look down at the tub
    place(h, sp, face_to(sp, CONT_AT))
    M = h.arm.matrix_world.to_3x3(); fwd = M @ Vector((0, -1, 0)); side = M @ Vector((1, 0, 0))
    import numpy as _np
    from human import _world_verts
    top = float(_np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])[:, 2].max())
    eye = Vector((h.bone_head("head").x, h.bone_head("head").y, top - 0.12)) + fwd * 0.1
    camp = eye + fwd * 0.07 - Vector((0, 0, 0.02))
    reach(h, "R", camp - side * 0.075 - Vector((0, 0, 0.03)), -side + Vector((0, 0, -1.2)))
    reach(h, "L", camp + side * 0.06 - Vector((0, 0, 0.045)) + fwd * 0.03, side + Vector((0, 0, -1.2)))
    if c.get("camera_prop") is not None:
        cp = c["camera_prop"]; cp.location = camp - Vector((0, 0, 0.045)); cp.rotation_euler = (0, 0, h.arm.rotation_euler.z + math.pi / 2)
    c["flash"].location = camp + Vector((0, 0, 0.12)); point_at(c["flash"], CONT_AT)


def anim_yard(c, t):
    sec = t * DUR["yard"]
    rain_fall(c, sec)
    h = c["searcher"]
    walk_to(h, Vector((-2.4, 1.0, 0)), Vector((2.2, 3.0, 0)), sec, speed=0.55, cadence=1.3)
    h.rot("neck01", (1, 0, 0), 14); h.rot("head", (1, 0, 0), 16)


def anim_gate(c, t):
    sec = t * DUR["gate"]
    rain_fall(c, sec)
    for h, a, b, delay, u in c["walkers"]:
        walk_to(h, a, b, max(0.0, sec - delay), speed=0.95)
        if u is not None:
            M = h.arm.matrix_world.to_3x3()
            hd = h.bone_head("head")
            grip = hd + M @ Vector((-0.16, -0.22, -0.3))            # the hand at shoulder height, in front of the right shoulder
            tipp = grip + Vector((0.02, 0.02, 0.9))                   # the shaft shows between hand and canopy; rim just above the head
            u.location = tipp
            d = (tipp - grip).normalized(); u.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
            reach(h, "R", grip + Vector((0, 0, -0.02)), M @ Vector((-1, 0.4, -0.8)))
            fingers_curl(h, 60, side=("R",), thumb=30)


def anim_torch(c, t):
    sec = t * DUR["torch"]
    rain_fall(c, sec)
    # the officer stands just below frame; only the beam pool slides across the wet concrete onto the patch
    h = c["torcher"]; sp = PATCH + Vector((-1.35, -0.45, 0)); place(h, sp, face_to(sp, PATCH)); arms_relaxed(h)
    hand = sp + Vector((0.3, 0.12, 1.05))
    u = ease(t)
    tgt = (PATCH + Vector((-1.0, -0.55, 0))).lerp(PATCH + Vector((0.02, 0.0, 0)), u)
    to = c["torch"]; to.location = hand; point_at(to, tgt)


# ============================================================================ cameras
def cam_walk(c, t):
    e = ease(t)
    loc = Vector((-2.2, -6.6, 6.2)).lerp(Vector((-1.2, -4.8, 2.4)), e)
    tgt = Vector((2.0, 1.5, 0.3)).lerp(Vector((2.8, 3.2, 0.8)), e)
    return loc, tgt, 30


def cam_patch(c, t):
    e = ease(t)
    loc = PATCH + Vector((-1.4, -1.9, 0.28)).lerp(Vector((-0.55, -0.85, 0.22)), e)
    return loc, PATCH + Vector((0.15, 0.05, 0.0)), 35


def cam_drill(c, t):
    e = ease(t)
    loc = PATCH + Vector((-1.3, -4.2, 1.5)).lerp(Vector((-1.1, -3.8, 1.42)), e)
    return loc, PATCH + Vector((-0.1, 0.0, 0.8)), 30


def cam_container(c, t):
    e = ease(t)
    loc = CONT_AT + Vector((-0.1, -0.26, 0.3)).lerp(Vector((-0.06, -0.15, 0.2)), e)
    return loc, c["hero"].location + Vector((0, 0, 0.008)), 60


def cam_circle(c, t):
    a = math.radians(-125 + 50 * ease(t))
    loc = CONT_AT + Vector((0.42 * math.cos(a), 0.42 * math.sin(a), 0.38))
    return loc, CONT_AT + Vector((0, 0, 0.04)), 45


def cam_bag(c, t):
    e = ease(t)
    loc = CONT_AT + Vector((-2.6, -2.4, 1.35)).lerp(Vector((-2.35, -2.15, 1.3)), e)
    return loc, CONT_AT + Vector((0.3, -0.45, 0.75)), 30


def cam_yard(c, t):
    e = ease(t)
    loc = Vector((-4.8, -3.6, 1.65)).lerp(Vector((-3.9, -3.3, 1.6)), e)
    return loc, Vector((0.0, 2.4, 1.1)).lerp(Vector((1.2, 2.8, 1.0)), e), 32


def cam_gate(c, t):
    e = ease(t)
    loc = Vector((3.4, 2.4, 1.6)).lerp(Vector((3.1, 2.1, 1.55)), e)
    return loc, Vector((1.4, -3.5, 1.45)), 30


def cam_torch(c, t):
    e = ease(t)
    loc = PATCH + Vector((0.35, -1.05, 2.7)).lerp(Vector((0.3, -0.95, 2.6)), e)
    return loc, PATCH + Vector((-0.35, -0.2, 0.0)), 34


MOVES = {
    "walk": dict(kind="anim", dof=5.6, cam=cam_walk, anim=anim_walk, focus=lambda c, t: Vector((2.2, 1.5, 1.0))),
    "patch": dict(kind="anim", dof=2.2, cam=cam_patch, anim=lambda c, t: rain_fall(c, t * DUR["patch"]),
                  focus=lambda c, t: PATCH),
    "drill": dict(kind="anim", dof=4.0, cam=cam_drill, anim=anim_drill, focus=lambda c, t: PATCH + Vector((0, -0.4, 0.4))),
    "container": dict(kind="anim", dof=4.0, cam=cam_container, anim=lambda c, t: anim_open(c, t, DUR["container"]),
                      focus=lambda c, t: c["hero"].location),
    "circle": dict(kind="anim", dof=4.0, cam=cam_circle, anim=lambda c, t: anim_open(c, t, DUR["circle"]),
                   focus=lambda c, t: c["hero"].location),
    "bag": dict(kind="anim", dof=5.6, cam=cam_bag, anim=anim_bag, focus=lambda c, t: CONT_AT + Vector((0.3, -0.4, 0.5))),
    "yard": dict(kind="anim", dof=4.0, cam=cam_yard, anim=anim_yard, focus=lambda c, t: c["searcher"].arm.location + Vector((0, 0, 1.4))),
    "gate": dict(kind="anim", dof=4.0, cam=cam_gate, anim=anim_gate, focus=lambda c, t: c["walkers"][0][0].arm.location + Vector((0, 0, 1.5))),
    "torch": dict(kind="anim", dof=None, cam=cam_torch, anim=anim_torch),
}
