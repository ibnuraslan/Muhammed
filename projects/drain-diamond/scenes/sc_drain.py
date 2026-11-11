"""THE DRAIN (hero set): the yard of a millstone pavillon in Les Pavillons-sous-Bois, March 2011, grey drizzle.
A rainwater drain pit by the downpipe; at its bottom, a patch of concrete a little lighter than the rest.
  walk      (intro 1A): crane down over the wet yard as three officers walk from the gate to the drain
  patch     (intro 1B): low push along the ground to the pale patch, drizzle rings spreading in a puddle
  drill     (intro 2A): an officer kneels and drills the patch, grey dust puffing into the rain
  container (intro 2B): the open container on the concrete, the camera easing in as the big diamond catches light
  yard      (ch3): an officer walks slowly round the yard looking down
  gate      (ch3): the fifth visit, officers come back in through the gate under umbrellas
  torch     (ch3): an officer crouches and runs a torch beam across the drain
  circle    (ch3): slow circle over the open container in the rain
  bag       (ch3): an evidence bag lowered over the container
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import dd
from dd import person, officer, place, face_to, walk_to, arms_relaxed, pose_kneel, pose_crouch, zero, rain, rain_fall
from human import reach, fingers_curl
from sc_street import car, umbrella

EXPOSURE = 0.7
BOUNCES = 8
DRAIN = Vector((3.2, 3.4, 0.0))       # centre of the pit opening (ground level)
PIT_IN, PIT_RIM, PIT_D = 0.5, 0.7, 0.26
GATE = Vector((1.7, -5.0, 0.0))
LEAD = 2.5
DUR = {"walk": LEAD + 8.0, "patch": 9.0, "drill": 9.0, "container": 9.0,
       "yard": 9.0, "gate": 9.0, "torch": 9.0, "circle": 9.0, "bag": 9.0}
VARIANT_FOR = {"walk": "walk", "patch": "patch", "drill": "drill", "container": "open", "yard": "yard",
               "gate": "gate", "torch": "torch", "circle": "open_rain", "bag": "bag"}
CONT_SIZE = (0.24, 0.17, 0.09)
CONT_AT = Vector((2.45, 2.95, 0.0))


def grate(loc, rot_z=0.0):
    iron = pbr("CastIron", (0.04, 0.04, 0.04), 0.55, 0.6)
    parts = [box("GFrame", (0, 0, 0.012), (0.5, 0.5, 0.025), iron)]
    for k in range(9):
        parts.append(box("GBar", (-0.2 + k * 0.05, 0, 0.03), (0.018, 0.48, 0.03), iron))
    g = join(parts, "Grate"); g.location = loc; g.rotation_euler = (0, 0, rot_z)
    return g


def drill_tool():
    """A rotary hammer drill: dark body, side grip, long bit pointing down -Z. Origin at the bit tip."""
    body = pbr("DrillBody", (0.05, 0.12, 0.09), 0.45)
    blk = pbr("DrillGrip", (0.02, 0.02, 0.02), 0.7)
    steel = pbr("DrillBit", (0.5, 0.5, 0.52), 0.25, 1.0)
    parts = [cyl("Bit", (0, 0, 0.16), 0.006, 0.32, steel, verts=10),
             cyl("Chuck", (0, 0, 0.35), 0.022, 0.07, blk, verts=16),
             box("Body", (0, 0, 0.47), (0.08, 0.09, 0.2), body, bevel=0.015),
             box("Motor", (0, 0.05, 0.6), (0.08, 0.2, 0.08), body, bevel=0.02),
             box("Handle", (0, 0.14, 0.53), (0.04, 0.04, 0.16), blk, bevel=0.01),
             cyl("SideGrip", (0.11, 0, 0.42), 0.017, 0.14, blk, verts=12, rot=(0, math.radians(90), 0))]
    return join(parts, "Drill")


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


def build_yard(c, variant):
    rng = np.random.default_rng(11)
    w = world_flat((0.42, 0.46, 0.52), 1.0)
    N = w.node_tree.nodes; L = w.node_tree.links        # the sky the camera sees: soft grey, not blown out
    lp = N.new("ShaderNodeLightPath"); bg2 = N.new("ShaderNodeBackground"); bg2.inputs['Color'].default_value = (0.2, 0.22, 0.25, 1)
    mx = N.new("ShaderNodeMixShader"); out = N["World Output"]; bg = N["Background"]
    L.new(lp.outputs['Is Camera Ray'], mx.inputs[0]); L.new(bg.outputs[0], mx.inputs[1]); L.new(bg2.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    sun(40, 210, energy=0.5, color=(0.85, 0.9, 1.0), angle_deg=12)
    yard = dd.wet(dd.tex_mat("concrete_floor_worn_001", 0.5, tint=(0.8, 0.8, 0.8), name="Yard"), 0.6, 0.45)
    x0, x1, y0, y1 = -7.0, 8.0, -5.0, 5.0
    a, b = DRAIN.x - PIT_IN / 2, DRAIN.x + PIT_IN / 2
    cy0, cy1 = DRAIN.y - PIT_IN / 2, DRAIN.y + PIT_IN / 2
    t = 0.1
    box("YardW", ((x0 + a) / 2, (y0 + y1) / 2, -t / 2), (a - x0, y1 - y0, t), yard)
    box("YardE", ((b + x1) / 2, (y0 + y1) / 2, -t / 2), (x1 - b, y1 - y0, t), yard)
    box("YardS", (DRAIN.x, (y0 + cy0) / 2, -t / 2), (PIT_IN, cy0 - y0, t), yard)
    box("YardN", (DRAIN.x, (cy1 + y1) / 2, -t / 2), (PIT_IN, y1 - cy1, t), yard)
    # the pit: concrete walls, a rim, the old bottom and the lighter patch
    pitc = dd.wet(dd.tex_mat("concrete_floor_02", 1.2, tint=(0.5, 0.5, 0.5), name="PitWall", sat=0.3), 0.8, ripples=False)
    for dx, dy, sx, sy in ((-1, 0, 0.05, PIT_IN), (1, 0, 0.05, PIT_IN), (0, -1, PIT_IN, 0.05), (0, 1, PIT_IN, 0.05)):
        box("PitWall", (DRAIN.x + dx * (PIT_IN / 2 + 0.025), DRAIN.y + dy * (PIT_IN / 2 + 0.025), -PIT_D / 2), (sx, sy, PIT_D), pitc)
    rim = dd.wet(dd.tex_mat("concrete_floor_02", 1.0, tint=(0.62, 0.62, 0.6), name="Rim", sat=0.3), 0.7, ripples=False)
    for dx, dy, sx, sy in ((-1, 0, 0.1, PIT_RIM), (1, 0, 0.1, PIT_RIM), (0, -1, PIT_IN, 0.1), (0, 1, PIT_IN, 0.1)):
        box("Rim", (DRAIN.x + dx * (PIT_IN / 2 + 0.05), DRAIN.y + dy * (PIT_IN / 2 + 0.05), 0.012), (sx, sy, 0.025), rim)
    old = dd.wet(dd.tex_mat("concrete_floor_02", 1.4, tint=(0.2, 0.2, 0.2), name="PitBottom", sat=0.3), 0.9, 0.9, ripple_scale=14)
    box("PitBottom", (DRAIN.x, DRAIN.y, -PIT_D - 0.02), (PIT_IN, PIT_IN, 0.04), old)
    opened = variant in ("open", "open_rain", "bag")
    patch_m = dd.wet(dd.tex_mat("concrete_floor_02", 2.2, tint=(1.0, 1.0, 0.98), name="Patch", sat=0.15), 0.5, ripples=False)
    if not opened:
        box("Patch", (DRAIN.x + 0.02, DRAIN.y - 0.03, -PIT_D + 0.004), (0.3, 0.26, 0.012), patch_m, bevel=0.004)
    else:
        box("Hole", (DRAIN.x + 0.02, DRAIN.y - 0.03, -PIT_D + 0.002), (0.27, 0.2, 0.01), pbr("HoleDark", (0.015, 0.013, 0.012), 0.9))
        for k in range(7):        # broken pieces of the patch heaped at the side
            box("Chunk", (DRAIN.x - 0.15 + rng.uniform(-0.04, 0.04), DRAIN.y + 0.14 + rng.uniform(-0.04, 0.04), -PIT_D + 0.02),
                (rng.uniform(0.03, 0.07), rng.uniform(0.03, 0.06), 0.02), patch_m, rot=(0.2 * rng.uniform(-1, 1), 0.2, rng.uniform(0, 3)))
    c["grate"] = grate((DRAIN.x + 0.75, DRAIN.y - 0.15, 0.0), 0.25)
    # house, downpipe into a small channel to the pit
    house, hi = dd.pavillon((0, 5.0, 0), w=9.0, d=8.0, floors=2, name="House")
    c["house"] = house
    box("Channel", (DRAIN.x + 0.4, (DRAIN.y + 4.9) / 2 + 0.15, -0.005), (0.14, 4.9 - DRAIN.y - 0.2, 0.02), pbr("ChannelC", (0.25, 0.25, 0.24), 0.4))
    cyl("Shoe", (4.0, 4.83, 0.15), 0.05, 0.3, pbr("Zinc2", (0.42, 0.44, 0.45), 0.35, 0.9), verts=12)
    # front wall with railing and gate
    wallm = dd.tex_mat("plastered_wall_03", 0.6, tint=(0.82, 0.8, 0.75), name="FrontWall")
    rail = pbr("Railing", (0.06, 0.07, 0.07), 0.45, 0.7)
    for xa, xb in ((x0, GATE.x - 0.6), (GATE.x + 0.6, x1)):
        box("Muret", ((xa + xb) / 2, -5.0, 0.4), (xb - xa, 0.25, 0.8), wallm)
        n = int((xb - xa) / 0.14)
        for k in range(n):
            cyl("Bar", (xa + 0.07 + k * 0.14, -5.0, 1.15), 0.009, 0.7, rail, verts=6)
        box("RailTop", ((xa + xb) / 2, -5.0, 1.5), (xb - xa, 0.04, 0.04), rail)
    for sx in (-0.65, 0.65):
        box("GatePier", (GATE.x + sx, -5.0, 0.8), (0.3, 0.3, 1.6), wallm)
    c["gate_leaf"] = gl = join([box("GateFrame", (0.55, 0, 0.75), (1.1, 0.04, 1.2), rail)] +
                               [cyl("GateBar", (0.06 + k * 0.12, 0, 0.75), 0.008, 1.15, rail, verts=6) for k in range(9)], "Gate")
    gl.location = (GATE.x - 0.55, -5.0, 0.05); gl.rotation_euler = (0, 0, math.radians(-70))
    # side boundaries: hedges / shrubs, neighbour houses, the street behind the wall
    for k, x in enumerate((-6.6, 7.6)):
        box("SideWall", (x, 0, 0.9), (0.2, 10, 1.8), wallm)
    for x, y, rz in ((-5.9, -3.2, math.pi / 2), (-5.9, 1.8, math.pi / 2), (7.0, -2.8, -math.pi / 2)):
        try:
            ph.model("shrub_02", loc=(x, y, 0), rot_z=rz, scale=1.05)       # four bushes in a row: a garden hedge
        except Exception as e:
            print("[drain] shrubs skipped", e)
    dd.model_h("potted_plant_02", (-1.4, 4.4, 0), 0.8)
    dd.pavillon((-12.5, 6.5, 0), w=8.0, d=8.0, floors=2, name="NeighW", stone=False)
    dd.pavillon((13.0, 7.0, 0), w=8.0, d=8.0, floors=2, name="NeighE", stone=True)
    dd.pavillon((0.0, 24.0, 0), w=10.0, d=8.0, floors=2, name="Behind", stone=False)
    road = dd.wet(dd.tex_mat("asphalt_02", 0.4, tint=(0.6, 0.6, 0.62), name="Road"), 0.8, 0.3)
    box("Road", (0, -10.5, -0.06), (60, 9, 0.1), road)
    box("Pave", (0, -5.8, 0.0), (60, 1.4, 0.1), pbr("Kerbstone", (0.4, 0.4, 0.39), 0.6))
    for k, x in enumerate((-6.0, 5.5)):
        cr = car(f"Parked{k}", ((0.12, 0.13, 0.15), (0.35, 0.36, 0.38))[k]); cr.location = (x, -7.6, 0)
    box("Ground", (0, 10, -0.65), (80, 40, 0.1), pbr("Lawn", (0.08, 0.1, 0.06), 0.9))
    c["rain_ys"] = (-3.5, -0.5, 2.0, 6.0)
    rain(c, 0, c["rain_ys"], width=30, height=8, strength=0.45, density=0.955)


def build(variant=None):
    c = {"variant": variant}
    build_yard(c, variant or "walk")
    rng = np.random.default_rng(5)
    v = variant or "walk"
    if v == "walk":
        c["walkers"] = []
        starts = [Vector((1.5, -2.4, 0)), Vector((0.6, -3.3, 0)), Vector((2.3, -4.0, 0))]
        ends = [DRAIN + Vector((-0.5, -0.75, 0)), DRAIN + Vector((0.7, -0.8, 0)), DRAIN + Vector((-1.2, -0.3, 0))]
        for k in range(3):
            h = officer(f"Off{k}", 35 + 7 * k, seed=k)
            c["walkers"].append((h, starts[k], ends[k], 0.4 * k))
    if v == "drill":
        h = officer("Driller", 38, seed=1)
        c["driller"] = h
        w = officer("Watcher", 50, seed=2); place(w, DRAIN + Vector((-0.75, 0.75, 0)), face_to(DRAIN + Vector((-0.75, 0.75, 0)), DRAIN))
        arms_relaxed(w); c["watcher"] = w
        c["drill"] = drill_tool()
        c["dust"] = dust_volume(DRAIN + Vector((0, 0, -0.2)))
    if v in ("open", "open_rain", "bag"):
        box_ = dd.container("Container", CONT_AT, CONT_SIZE, rot_z=0.35)
        c["box"] = box_
        hero, items = dd.fill_container(box_, CONT_SIZE, rng)
        c["hero"] = hero
        # the lid set aside, a soft key catching the stone
        lid = box("Lid", CONT_AT + Vector((-0.28, -0.1, 0.006)), (0.25, 0.18, 0.012), box_.data.materials[0], bevel=0.01, rot=(0, 0, -0.2))
        k = bpy.data.lights.new("Glint", 'AREA'); k.size = 0.5; k.energy = 10; k.color = (1.0, 0.97, 0.92)
        ko = bpy.data.objects.new("Glint", k); bpy.context.collection.objects.link(ko); ko.location = CONT_AT + Vector((-0.6, -0.4, 0.9))
        ko.visible_camera = False
        point_at(ko, CONT_AT); c["glint"] = ko
        if v != "bag":
            o = officer("Stand", 45, seed=0); place(o, CONT_AT + Vector((0.9, 0.7, 0)), face_to(CONT_AT + Vector((0.9, 0.7, 0)), CONT_AT))
            arms_relaxed(o); c["stander"] = o
        if v == "bag":
            # a yellow evidence marker tent beside the box, and a photographer's flash popping (frame driver)
            mk = pbr("Marker", (0.85, 0.62, 0.05), 0.4)
            for sg in (-1, 1):
                box("MarkerSide", CONT_AT + Vector((0.2, -0.16 + sg * 0.025, 0.045)), (0.09, 0.005, 0.1), mk, rot=(sg * 0.45, 0, 0.3))
            fl = bpy.data.lights.new("Flash", 'AREA'); fl.size = 0.15; fl.color = (0.95, 0.97, 1.0)
            dr = fl.driver_add("energy").driver; dr.type = 'SCRIPTED'
            dr.expression = "120 * (max(0, 1 - abs(frame - 30) / 2.5) + max(0, 1 - abs(frame - 78) / 2.5))"
            fo = bpy.data.objects.new("Flash", fl); bpy.context.collection.objects.link(fo)
            fo.location = CONT_AT + Vector((0.45, -0.7, 1.5)); point_at(fo, CONT_AT); fo.visible_camera = False
            ph_ = officer("Photographer", 33, seed=1, gender=0.0); c["photog"] = ph_
            place(ph_, CONT_AT + Vector((0.5, -0.8, 0)), face_to(CONT_AT + Vector((0.5, -0.8, 0)), CONT_AT))
    if v == "yard":
        h = officer("Searcher", 44, seed=0); c["searcher"] = h
    if v == "gate":
        c["walkers"] = []
        for k in range(3):
            h = officer(f"Ret{k}", 36 + 6 * k, seed=k + 1)
            u = join(umbrella(0.55), f"Umb{k}") if k != 1 else None
            c["walkers"].append((h, GATE + Vector((0.2 * k, -2.5 - 1.3 * k, 0)), Vector((0.6 + 0.9 * k, 1.0 - 0.6 * k, 0)), 0.5 * k, u))
    if v == "torch":
        h = officer("Torch", 41, seed=2); c["torcher"] = h
        tl = bpy.data.lights.new("TorchBeam", 'SPOT'); tl.energy = 80; tl.spot_size = math.radians(16); tl.spot_blend = 0.5
        tl.color = (1.0, 0.94, 0.82); tl.shadow_soft_size = 0.02
        to = bpy.data.objects.new("TorchBeam", tl); bpy.context.collection.objects.link(to); c["torch"] = to
        c["torch_body"] = cyl("TorchBody", (0, 0, 0), 0.018, 0.2, pbr("TorchBlk", (0.02, 0.02, 0.02), 0.4), verts=12)
    return c


# ============================================================================ animation
def anim_walk(c, t):
    sec = t * DUR["walk"]
    rain_fall(c, sec)
    for h, a, b, delay in c["walkers"]:
        walk_to(h, a, b, max(0.0, sec - delay), speed=1.1)


def anim_drill(c, t):
    sec = t * DUR["drill"]
    rain_fall(c, sec)
    h = c["driller"]
    pose_kneel(h, lean=34)
    pos = DRAIN + Vector((0.66, 0.02, 0))
    h.arm.rotation_euler = (0, 0, face_to(pos, DRAIN)); h.arm.location = pos; dd.ground(h)
    jit = 0.004 * math.sin(sec * 55)
    tip = DRAIN + Vector((0.02, -0.03, -PIT_D + 0.01 + jit))
    d = c["drill"]; d.location = tip; d.rotation_euler = (0, math.radians(8), -math.pi / 2)      # handle toward him (+X)
    grip_top = tip + Vector((0.14 + 0.05, 0, 0.56))
    reach(h, "R", grip_top + Vector((0.0, 0.0, 0.02)), Vector((0.3, -0.8, -0.3)))
    reach(h, "L", tip + Vector((0.07, 0.11, 0.43)), Vector((0.3, 0.8, -0.3)))
    fingers_curl(h, 50, thumb=25)
    h.rot("head", (1, 0, 0), 6)


def anim_open(c, t, dur):
    sec = t * dur
    rain_fall(c, sec)
    g = c["glint"]
    g.location = CONT_AT + Vector((-0.7 + 0.3 * t, -0.4 - 0.1 * t, 0.9)); point_at(g, CONT_AT)


def anim_bag(c, t):
    anim_open(c, t, DUR["bag"])
    h = c["photog"]; M = h.arm.matrix_world.to_3x3()
    eye = h.bone_head("head") + M @ Vector((0, -0.12, 0.05))
    reach(h, "R", eye + M @ Vector((-0.07, -0.18, -0.06)), M @ Vector((-1, 0.2, -0.5)))
    reach(h, "L", eye + M @ Vector((0.08, -0.18, -0.08)), M @ Vector((1, 0.2, -0.5)))
    h.rot("spine03", (1, 0, 0), 0)


def anim_yard(c, t):
    sec = t * DUR["yard"]
    rain_fall(c, sec)
    h = c["searcher"]
    walk_to(h, Vector((-2.8, 0.8, 0)), Vector((1.8, 2.4, 0)), sec, speed=0.75, cadence=1.4)
    h.rot("neck01", (1, 0, 0), 14); h.rot("head", (1, 0, 0), 14)


def anim_gate(c, t):
    sec = t * DUR["gate"]
    rain_fall(c, sec)
    for h, a, b, delay, u in c["walkers"]:
        walk_to(h, a, b, max(0.0, sec - delay), speed=1.05)
        if u is not None:
            hd = h.bone_head("head")
            u.location = hd + Vector((0.12, 0.05, 0.5)); u.rotation_euler = (0.1, -0.12, 0)
            M = h.arm.matrix_world.to_3x3()
            reach(h, "R", hd + Vector((0.1, 0.04, -0.15)) + M @ Vector((0, -0.2, 0)), M @ Vector((-1, 0.2, -0.6)))


def anim_torch(c, t):
    sec = t * DUR["torch"]
    rain_fall(c, sec)
    h = c["torcher"]
    pos = DRAIN + Vector((0.6, -0.55, 0))
    pose_crouch(h, lean=30)
    h.arm.rotation_euler = (0, 0, face_to(pos, DRAIN)); h.arm.location = pos; dd.ground(h)
    sweep = -0.13 + 0.26 * ease(t)
    hand = DRAIN + Vector((0.32, -0.32, 0.45))
    reach(h, "R", hand, Vector((0.5, -0.6, -0.4)))
    tgt = DRAIN + Vector((0.02 + 0.6 * sweep, -0.03, -PIT_D))
    tb = c["torch_body"]; tb.location = hand + Vector((-0.03, 0.03, -0.04)); point_at(tb, tgt); tb.rotation_euler.x += 0
    to = c["torch"]; to.location = hand + Vector((-0.06, 0.06, -0.08)); point_at(to, tgt)
    fingers_curl(h, 55, side=("R",), thumb=25)


# ============================================================================ cameras
def cam_walk(c, t):
    e = ease(t)
    loc = Vector((-1.6, -6.2, 6.0)).lerp(Vector((-1.0, -4.6, 2.3)), e)
    tgt = Vector((2.5, 1.2, 0.2)).lerp(Vector((2.8, 2.4, 0.6)), e)
    return loc, tgt, 30


def cam_patch(c, t):
    e = ease(t)
    loc = Vector((DRAIN.x - 0.3, DRAIN.y - 1.5, 1.05)).lerp(Vector((DRAIN.x - 0.1, DRAIN.y - 0.85, 0.95)), e)
    return loc, DRAIN + Vector((0.02, 0.0, -PIT_D + 0.05)), 32


def cam_drill(c, t):
    e = ease(t)
    loc = Vector((DRAIN.x - 1.3, DRAIN.y - 3.3, 1.0)).lerp(Vector((DRAIN.x - 1.0, DRAIN.y - 3.0, 0.95)), e)
    return loc, DRAIN + Vector((0.1, 0.1, 0.62)), 26


def cam_container(c, t):
    e = ease(t)
    loc = CONT_AT + Vector((-0.05, -0.3, 0.42)).lerp(Vector((-0.03, -0.2, 0.3)), e)
    return loc, c["hero"].location + Vector((0, 0, 0.004)), 50


def cam_circle(c, t):
    a = math.radians(-120 + 50 * ease(t))
    loc = CONT_AT + Vector((0.5 * math.cos(a), 0.5 * math.sin(a), 0.42))
    return loc, CONT_AT + Vector((0, 0, 0.04)), 42


def cam_bag(c, t):
    e = ease(t)
    loc = CONT_AT + Vector((-2.6, 0.9, 1.5)).lerp(Vector((-2.3, 0.7, 1.4)), e)
    return loc, CONT_AT + Vector((0.3, -0.4, 0.7)), 28


def cam_yard(c, t):
    e = ease(t)
    loc = Vector((-4.5, -3.6, 1.6)).lerp(Vector((-3.6, -3.4, 1.55)), e)
    return loc, Vector((0.0, 2.2, 1.2)).lerp(Vector((1.2, 2.6, 1.0)), e), 32


def cam_gate(c, t):
    e = ease(t)
    loc = Vector((3.6, 2.6, 1.55)).lerp(Vector((3.3, 2.3, 1.5)), e)
    return loc, Vector((1.4, -3.5, 1.3)), 32


def cam_torch(c, t):
    e = ease(t)
    loc = Vector((DRAIN.x - 2.2, DRAIN.y + 0.4, 4.2)).lerp(Vector((DRAIN.x - 1.9, DRAIN.y + 0.3, 3.8)), e)
    return loc, DRAIN + Vector((0.35, -0.3, 0.3)), 28


MOVES = {
    "overview": dict(kind="anim", cam=lambda c, t: (Vector((-5, -9, 7)), Vector((2, 2, 1)), 24)),
    "walk": dict(kind="anim", dof=5.6, cam=cam_walk, anim=anim_walk, focus=lambda c, t: Vector((2.4, 1.5, 1.0))),
    "patch": dict(kind="anim", dof=2.8, cam=cam_patch, anim=lambda c, t: rain_fall(c, t * DUR["patch"]),
                  focus=lambda c, t: DRAIN + Vector((0.02, 0, -PIT_D))),
    "drill": dict(kind="anim", dof=4.0, cam=cam_drill, anim=anim_drill, focus=lambda c, t: DRAIN + Vector((0, -0.4, 0.3))),
    "container": dict(kind="anim", dof=4.0, cam=cam_container, anim=lambda c, t: anim_open(c, t, DUR["container"]),
                      focus=lambda c, t: c["hero"].location),
    "circle": dict(kind="anim", dof=4.0, cam=cam_circle, anim=lambda c, t: anim_open(c, t, DUR["circle"]),
                   focus=lambda c, t: c["hero"].location),
    "bag": dict(kind="anim", dof=4.0, cam=cam_bag, anim=anim_bag, focus=lambda c, t: CONT_AT),
    "yard": dict(kind="anim", dof=4.0, cam=cam_yard, anim=anim_yard, focus=lambda c, t: c["searcher"].arm.location + Vector((0, 0, 1.4))),
    "gate": dict(kind="anim", dof=4.0, cam=cam_gate, anim=anim_gate, focus=lambda c, t: c["walkers"][0][0].arm.location + Vector((0, 0, 1.5))),
    "torch": dict(kind="anim", dof=4.0, cam=cam_torch, anim=anim_torch, focus=lambda c, t: DRAIN + Vector((0.1, -0.1, -0.2))),
}
