"""HERO SET: the second scrapyard on the edge of Istanbul, January 1999. Mountains of rusted scrap behind a
corrugated-iron fence, a grab crane, the smaller heap where the capsule lies, and (by variant) the response:
specialists with handheld detectors, a police cordon at the gate, the boom-detector truck, the concrete-block wall,
the crane with the lead-lined drum, responders with a long pole and a shovel.

Moves (preview set; the plan reuses this set for ~40 shots):
  wide          (Ch1 15A)  high wide over the scrap mountains; the grab swings far off
  heap_push     (Ch1 15B)  slow push deep into one heap toward a dark gap
  gate_van      (Ch2 7A)   a white van pulls up at the gate; a specialist steps out
  cordon        (Ch2 8B)   a policeman strings tape across the gate; the police light turns
  sweep         (Ch3 1B)   a specialist sweeps a detector over the heap, needle climbing
  grab_lift     (Ch3 4A)   the grab carries the cylinder overhead toward the lead-brick box
  boom_truck    (Ch3 10A)  a truck reverses in, its long detector boom over the heap
  capsule_drop  (Ch3 17B)  a tiny steel capsule drops off the shovel into the hanging drum
"""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Euler, Quaternion
from kit import *
from rs_kit import *
from rs_env import sky, periphery, pylons, puddles, smoke
from human import reset_pose, pose_walk, reach, fingers_curl
from durs import dur

EXPOSURE = 0.0
BOUNCES = 6
DUR = {"wide": 2.5 + 3.5, "heap_push": 4.0, "gate_van": 4.0, "cordon": 4.0, "sweep": 4.0, "grab_lift": 4.0,
       "boom_truck": 4.5, "capsule_drop": 4.0}     # estimates until the voiceover arrives
VARIANT_FOR = {"wide": "quiet", "heap_push": "quiet", "gate_van": "arrival", "cordon": "arrival", "sweep": "search",
               "grab_lift": "search", "boom_truck": "recovery", "capsule_drop": "recovery"}

HC = Vector((6.0, 4.0, 0))          # the smaller heap that hides the capsule
GATE = Vector((0.0, -30.0, 0))
HEAPS = [((-20, 15), 12, 9.0), ((18, 24), 14, 11.0), ((-6, 36), 11, 8.0), ((31, -6), 9, 6.0), ((-32, -12), 8, 5.5), ((36, 32), 9, 7.5),
         ((-36, 33), 9, 7.0)]


# ============================================================================ scrap
def mound(name, cx, cy, R, H, mat, seed):
    """Heap surface: a lumpy cone-ish mound (grid displaced by a height function). Returns the height function."""
    rng = np.random.default_rng(seed)
    ph_ = rng.uniform(0, 6.28, 6)
    def hfun(x, y):
        dx, dy = x - cx, y - cy; r = math.hypot(dx, dy) / R
        if r >= 1:
            return 0.0
        a = math.atan2(dy, dx)
        lump = 1 + 0.12 * math.sin(3 * a + ph_[0]) + 0.08 * math.sin(5 * a + ph_[1]) + 0.06 * math.sin(7 * a + ph_[2])
        return H * lump * (1 - r) ** 1.15 * (1 - 0.15 * r)
    n = 34
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=2 * R, location=(cx, cy, 0))
    o = bpy.context.active_object; o.name = name
    for v in o.data.vertices:
        x, y = v.co.x + cx, v.co.y + cy
        v.co.z = hfun(x, y) - 0.15 + rng.normal(0, 0.06)
    o.data.materials.append(mat)
    return hfun


def scrap_protos(mats):
    """Prototype scrap pieces (linked duplicates are scattered over the heaps)."""
    P = []
    out = lambda o: (setattr(o, "location", (0, 0, -80)), P.append(o))
    for k, m in enumerate(mats):
        out(box("Plate", (0, 0, 0), (1.4, 0.9, 0.02), m))
        out(box("Sheet", (0, 0, 0), (2.0, 1.1, 0.015), m, rot=(0.15, 0, 0)))
        ib = join([box("W", (0, 0, 0), (2.6, 0.02, 0.3), m), box("F1", (0, 0, 0.15), (2.6, 0.16, 0.02), m), box("F2", (0, 0, -0.15), (2.6, 0.16, 0.02), m)], "IBeam")
        out(ib)
        out(cyl("Pipe", (0, 0, 0), 0.09, 2.2, m, verts=12, rot=(0, math.radians(90), 0)))
        out(box("Bar", (0, 0, 0), (1.8, 0.06, 0.06), m))
        out(box("Panel", (0, 0, 0), (1.2, 0.04, 0.8), m, bevel=0.03))
    tyre_m = pbr("ScrapTyre", (0.03, 0.03, 0.03), 0.85)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.11, major_segments=24, minor_segments=8)
    t = bpy.context.active_object; t.name = "Tyre"; t.data.materials.append(tyre_m); out(t)
    rim = join([cyl("Rim", (0, 0, 0), 0.25, 0.2, mats[0], verts=20), cyl("Disc", (0, 0, 0), 0.22, 0.02, mats[1], verts=20)], "Rim"); out(rim)
    drum = join([cyl("Drum", (0, 0, 0), 0.29, 0.88, mats[2 % len(mats)], verts=20)], "Drum"); out(drum)
    shell = box("CarShell", (0, 0, 0), (3.6, 1.6, 1.0), mats[3 % len(mats)], bevel=0.25); out(shell)
    return P


def scatter(protos, hfun, cx, cy, R, n, rng, embed=0.12, scl=(1.1, 2.0), small=False):
    objs = []
    weights = np.array([1.0 if p.name.startswith(("Plate", "Sheet", "IBeam", "Pipe", "Bar", "Panel")) else 0.35 for p in protos])
    if small:
        weights = weights * np.array([0.0 if p.name.startswith(("CarShell", "Drum")) else 1.0 for p in protos])
    weights /= weights.sum()
    for k in range(n):
        r = R * math.sqrt(rng.uniform(0, 0.96)); a = rng.uniform(0, 2 * math.pi)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        z = hfun(x, y) - embed * rng.uniform(0, 1)
        p = protos[rng.choice(len(protos), p=weights)]
        if p.name.startswith("CarShell") and r > 0.6 * R:
            continue
        objs.append(instance(p, (x, y, z), rot=(rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9), rng.uniform(0, 6.28)),
                             scale=(rng.uniform(*scl),) * 3))
    return objs


# ============================================================================ vehicles / props
def van(name="Van", col=(0.78, 0.78, 0.76)):
    """1990s white panel van (generic): sloped bonnet, raked windscreen, sliding door. Front toward +X."""
    paint = painted_steel(name + "Paint", col, 0.35, 0.3)
    glass_m = pbr(name + "Glass", (0.02, 0.025, 0.03), 0.06, 0.0, **{'Coat Weight': 1.0})
    black = pbr(name + "Black", (0.015, 0.015, 0.015), 0.6)
    lamp = pbr(name + "Lamp", (0.85, 0.85, 0.8), 0.08, 0.0, **{'Coat Weight': 1.0})
    parts = [box("Body", (-0.3, 0, 1.3), (4.0, 1.9, 1.9), paint, bevel=0.2),
             box("Bonnet", (2.15, 0, 0.92), (0.95, 1.86, 0.75), paint, bevel=0.18),
             box("BonnetTop", (2.0, 0, 1.3), (0.9, 1.84, 0.2), paint, bevel=0.08, rot=(0, math.radians(14), 0)),
             box("Screen", (1.72, 0, 1.75), (0.03, 1.7, 0.7), glass_m, rot=(0, math.radians(-32), 0)),
             box("WinL", (1.2, 0.952, 1.7), (0.85, 0.02, 0.55), glass_m), box("WinR", (1.2, -0.952, 1.7), (0.85, 0.02, 0.55), glass_m),
             box("Bumper", (2.66, 0, 0.5), (0.1, 1.95, 0.2), black, bevel=0.03), box("RearBumper", (-2.33, 0, 0.5), (0.1, 1.95, 0.2), black),
             box("Grille", (2.63, 0, 0.88), (0.02, 0.9, 0.22), black),
             box("SlideSeam", (0.75, -0.953, 1.2), (0.012, 0.004, 1.55), black), box("SlideSeam", (-0.55, -0.953, 1.2), (0.012, 0.004, 1.55), black),
             box("Rail", (0.1, -0.953, 1.95), (1.6, 0.01, 0.025), black),
             box("RearWin", (-2.31, 0, 1.75), (0.02, 1.3, 0.45), glass_m)]
    for sy in (-1, 1):
        parts.append(box("Headlamp", (2.635, sy * 0.68, 0.9), (0.02, 0.32, 0.16), lamp))
        parts.append(box("Mirror", (1.55, sy * 1.1, 1.75), (0.05, 0.14, 0.26), black, bevel=0.01))
        parts.append(box("Arch", (1.75, sy * 0.95, 0.42), (0.85, 0.02, 0.18), black))
        parts.append(box("Arch", (-1.45, sy * 0.95, 0.42), (0.85, 0.02, 0.18), black))
    body = join(parts, name)
    tyre = pbr(name + "Tyre", (0.022, 0.022, 0.022), 0.85); hub = painted_steel(name + "Hub", (0.4, 0.4, 0.4), 0.5, 0.4)
    wheels = []
    for wx in (-1.45, 1.75):
        for sy in (-1, 1):
            w = wheel("VanWheel", 0.33, 0.21, tyre, hub, sy); w.parent = body; w.location = (wx, sy * 0.84, 0.33)
            wheels.append(w)
    return body, wheels


def police_car(name="Police"):
    from sc_street import car
    from sc_police import flash_material
    pc = car(name, (0.78, 0.78, 0.8))
    stripe = box("PStripe", (0, 0, 0.62), (4.3, 1.87, 0.12), pbr("PoliceBlue", (0.02, 0.06, 0.25), 0.3, 0.2)); stripe.parent = pc
    # one rotating blue beacon on the roof (1990s Turkish police car), no light bar, no glitter
    base = cyl("BeaconBase", (0, 0, 1.36), 0.11, 0.05, pbr("BeaconBase", (0.05, 0.05, 0.05), 0.5), verts=20); base.parent = pc
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=0.1, location=(0, 0, 1.43))
    dome = bpy.context.active_object; dome.name = "BeaconDome"; dome.scale = (1, 1, 1.25)
    dome.data.materials.append(pbr("BeaconGlass", (0.1, 0.25, 0.9), 0.1, 0.0, **{'Transmission Weight': 0.6, 'Emission Color': (0.15, 0.35, 1.0, 1), 'Emission Strength': 2.5}))
    dome.parent = pc
    rot = bpy.data.objects.new("BeaconSpin", None); bpy.context.collection.objects.link(rot); rot.parent = pc; rot.location = (0, 0, 1.43)
    d = rot.driver_add("rotation_euler", 2).driver; d.type = 'SCRIPTED'; d.expression = "frame * 0.42"
    l = bpy.data.lights.new("Beacon", 'SPOT'); l.color = (0.2, 0.4, 1.0); l.energy = 900; l.spot_size = math.radians(40); l.spot_blend = 0.6; l.shadow_soft_size = 0.02
    lo = bpy.data.objects.new("Beacon", l); bpy.context.collection.objects.link(lo); lo.parent = rot; lo.location = (0, 0, 0)
    lo.rotation_euler = (math.radians(85), 0, 0)
    return pc


def detector(name="Detector"):
    """Handheld survey meter: grey box with a round dial and a needle (pivot empty), a handle, and a probe on a cable."""
    body = box(name, (0, 0, 0), (0.22, 0.1, 0.12), painted_steel(name + "Body", (0.55, 0.52, 0.42), 0.5, 0.3), bevel=0.01)
    face = cyl(name + "Dial", (0, -0.051, 0.0), 0.04, 0.004, pbr(name + "DialM", (0.85, 0.83, 0.75), 0.4), verts=24, rot=(math.radians(90), 0, 0)); face.parent = body
    nd = bpy.data.objects.new(name + "NeedleP", None); bpy.context.collection.objects.link(nd); nd.parent = body; nd.location = (0, -0.055, -0.025)
    ne = box(name + "Needle", (0, 0, 0.025), (0.003, 0.002, 0.05), pbr(name + "NeedleM", (0.6, 0.05, 0.03), 0.4)); ne.parent = nd; ne.location = (0, 0, 0.025)
    hd = box(name + "Handle", (0, 0, 0.09), (0.16, 0.03, 0.03), pbr(name + "HandleM", (0.05, 0.05, 0.05), 0.6)); hd.parent = body; hd.location = (0, 0, 0.09)
    probe = cyl(name + "Probe", (0, 0, 0), 0.025, 0.3, pbr(name + "ProbeM", (0.12, 0.12, 0.12), 0.4, 0.6), verts=12)
    return dict(body=body, needle=nd, probe=probe)


def lead_drum(name="LeadDrum"):
    m = painted_steel(name + "M", (0.3, 0.31, 0.3), 0.5, 0.5)
    inside = pbr(name + "Lead", (0.12, 0.12, 0.13), 0.5, 0.6)
    d = join([cyl("D", (0, 0, 0.45), 0.36, 0.9, m, verts=32), cyl("Rim", (0, 0, 0.9), 0.38, 0.04, m, verts=32),
              cyl("Bail", (0, 0, 1.55), 0.025, 0.04, m, verts=8)], name)
    ins = cyl(name + "In", (0, 0, 0.91), 0.3, 0.012, inside, verts=32); ins.parent = d
    lid = cyl(name + "Lid", (0, 0, 0.94), 0.39, 0.05, m, verts=32)
    # bail (chains from the rim up to the hook)
    chain_m = pbr("Chain", (0.2, 0.2, 0.2), 0.5, 0.8)
    for a in (0, 2.09, 4.19):
        p = Vector((0.36 * math.cos(a), 0.36 * math.sin(a), 0.9)); top = Vector((0, 0, 1.6))
        ch = cyl("DrumChain", (p + top) / 2, 0.005, (top - p).length, chain_m, verts=6)
        ch.rotation_mode = 'QUATERNION'; ch.rotation_quaternion = (top - p).to_track_quat('Z', 'Y'); ch.parent = d
        ch.location = (p + top) / 2
    return d, lid


def mobile_crane(name="Crane", col=(0.8, 0.55, 0.1)):
    """Truck crane: carrier + slewing cab + telescopic boom (pivot) + hook line. hook() gives the hook point."""
    tk, wheels, bz, _ = truck(name + "Carrier", (0.75, 0.5, 0.08), bed_len=5.2)
    paint = painted_steel(name + "Paint", col, 0.45, 0.5)
    piv = bpy.data.objects.new(name + "BoomP", None); bpy.context.collection.objects.link(piv); piv.parent = tk; piv.location = (-1.5, 0, 1.9)
    box(name + "Turret", (0, 0, 0), (1.6, 1.4, 0.9), paint).parent = tk
    bpy.data.objects[name + "Turret"].location = (-1.5, 0, 1.45)
    boom = box(name + "Boom", (0, 0, 0), (13.0, 0.55, 0.6), paint, bevel=0.03); boom.parent = piv; boom.location = (6.0, 0, 0)
    tip = bpy.data.objects.new(name + "Tip", None); bpy.context.collection.objects.link(tip); tip.parent = piv; tip.location = (12.4, 0, -0.2)
    line = cyl(name + "Line", (0, 0, 0), 0.015, 1.0, pbr("Cable", (0.03, 0.03, 0.03), 0.5), verts=6)
    steel = painted_steel(name + "BlockSteel", (0.18, 0.18, 0.19), 0.45, 0.6)
    blk = join([box("Sheave", (0, 0, 0.15), (0.32, 0.14, 0.36), steel, bevel=0.04),
                cyl("Pin", (0, 0, 0.22), 0.05, 0.18, steel, verts=12, rot=(math.radians(90), 0, 0))], name + "HookBlock")
    bpy.ops.mesh.primitive_torus_add(major_radius=0.09, minor_radius=0.022, major_segments=20, minor_segments=8, location=(0, 0, -0.12), rotation=(math.radians(90), 0, 0))
    hk = bpy.context.active_object; hk.data.materials.append(steel); hk.parent = blk; hk.location = (0, 0, -0.12)
    hook = blk
    return dict(body=tk, wheels=wheels, piv=piv, tip=tip, line=line, hook=hook)


def crane_hang(cr, slew, luff, drop):
    """slew (rad, about the carrier's Z), luff (rad up), drop: hook depth below the tip. Returns hook world pos."""
    cr["piv"].rotation_euler = Euler((0, -luff, slew), 'ZYX')
    bpy.context.view_layer.update()
    tp = cr["tip"].matrix_world.translation
    hk = tp - Vector((0, 0, drop))
    ln = cr["line"]; ln.location = (tp + hk) / 2; ln.scale = (1, 1, max(0.05, drop)); ln.rotation_euler = (0, 0, 0)
    cr["hook"].location = hk + Vector((0, 0, -0.2))
    return hk


def boom_truck(name="BoomTruck"):
    tk, wheels, bz, _ = truck(name, (0.5, 0.52, 0.5), bed_len=4.6)
    steel = painted_steel(name + "Steel", (0.75, 0.75, 0.72), 0.4, 0.4)
    post = box(name + "Post", (0, 0, 0), (0.4, 0.4, 1.4), steel); post.parent = tk; post.location = (-1.6, 0, 1.6)
    piv = bpy.data.objects.new(name + "BoomP", None); bpy.context.collection.objects.link(piv); piv.parent = tk; piv.location = (-1.6, 0, 2.3)
    tel = box(name + "Tele", (0, 0, 0), (9.0, 0.22, 0.22), steel); tel.parent = piv; tel.location = (-4.5, 0, 0)
    head_p = bpy.data.objects.new(name + "HeadP", None); bpy.context.collection.objects.link(head_p); head_p.parent = piv; head_p.location = (-9.0, 0, 0)
    det = join([cyl("DetHead", (0, 0, -0.5), 0.09, 0.35, pbr("DetYellow", (0.75, 0.6, 0.08), 0.4), verts=16),
                cyl("DetCable", (0, 0, -0.18), 0.01, 0.36, pbr("Cable2", (0.02, 0.02, 0.02), 0.5), verts=6)], name + "Det")
    det.parent = head_p; det.location = (0, 0, 0)
    return dict(body=tk, wheels=wheels, piv=piv, tele=tel, head=head_p)


def block_wall(loc, rot_z, mat, w=4.0, h=1.8):
    rng = np.random.default_rng(5)
    proto = box("BlockP", (0, 0, -90), (0.6, 0.4, 0.4), mat, bevel=0.01)
    e = bpy.data.objects.new("BlockWall", None); bpy.context.collection.objects.link(e)
    for row in range(int(h / 0.4)):
        off = 0.3 * (row % 2)
        for k in range(int(w / 0.6)):
            o = instance(proto, (-w / 2 + off + k * 0.6 + rng.uniform(-0.01, 0.01), 0, 0.2 + row * 0.4), rot=(0, 0, rng.uniform(-0.03, 0.03)))
            o.parent = e
    e.location = loc; e.rotation_euler = (0, 0, rot_z)
    return e


def tape_between(name, a, b, z, mat, sag=0.08):
    a = Vector((a[0], a[1], z)); b = Vector((b[0], b[1], z)); L_ = (b - a).length
    bpy.ops.mesh.primitive_plane_add(size=1, location=(a + b) / 2)
    o = bpy.context.active_object; o.name = name; o.scale = (L_, 0.05, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.rotation_euler = (math.radians(90), 0, math.atan2(b.y - a.y, b.x - a.x))
    o.data.materials.append(mat)
    return o


def tape_material():
    m = bpy.data.materials.new("Tape"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (4, 4, 4)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    w = N.new("ShaderNodeTexWave"); w.wave_type = 'BANDS'; w.bands_direction = 'DIAGONAL'; w.inputs['Scale'].default_value = 1.0; w.inputs['Distortion'].default_value = 0
    L.new(mp.outputs[0], w.inputs['Vector'])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5; L.new(w.outputs['Fac'], gt.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(gt.outputs[0], mx.inputs['Factor'])
    mx.inputs[6].default_value = (0.6, 0.04, 0.03, 1); mx.inputs[7].default_value = (0.85, 0.85, 0.82, 1)
    L.new(mx.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.4
    return m


# ============================================================================ build
def build(variant=None):
    c = {}
    v = variant or "quiet"
    rng = np.random.default_rng(77)
    day = {"quiet": "overcast", "arrival": "afternoon", "search": "afternoon", "dusk": "dusk", "recovery": "morning"}.get(v, "overcast")
    sky(day)
    ground = ph_mat("muddy_tracks", 0.12, (0.25, 0.21, 0.17), name="YardMud")
    box("Ground", (0, 0, -0.05), (400, 400, 0.1), ground)
    box("Road", (0, -40, -0.03), (400, 9, 0.07), ph_mat("road_damaged", 0.15, (0.18, 0.18, 0.18), name="Road"))
    puddles(rng, ((-44, -28), (44, 44)), 40, avoid=[(x, y, R + 1) for (x, y), R, H in HEAPS] + [(HC.x, HC.y, 6)], size=(0.6, 2.6))
    puddles(rng, ((-30, -39), (30, -36)), 8, size=(0.8, 2.0))
    # perimeter fence: rusty corrugated iron on posts, a wide gate opening at the south
    fence = ph_mat("rusty_corrugated_iron", 0.5, (0.35, 0.2, 0.12), name="Fence")
    post_m = pbr("FencePost", (0.08, 0.08, 0.08), 0.6, 0.5)
    for (a, b) in (((-48, -30), (-5, -30)), ((5, -30), (48, -30)), ((48, -30), (48, 48)), ((-48, -30), (-48, 48)), ((-48, 48), (48, 48))):
        wall("Fence", a, b, 3.0, 0.06, fence)
    for x in np.arange(-48, 49, 4):
        if abs(x) > 5:
            box("FPost", (x, -30.1, 1.6), (0.1, 0.1, 3.2), post_m)
    for sx in (-1, 1):
        box("GatePost", (sx * 5.2, -30, 1.8), (0.35, 0.35, 3.6), post_m)
        g = box("GateLeaf", (sx * 5.2 + sx * 0.0, -30, 1.5), (4.6, 0.05, 2.8), fence)
        g.location = (sx * 7.4, -31.8, 1.5); g.rotation_euler = (0, 0, sx * math.radians(-75))
    # scrap mountains: textured mound showing through thousands of varied instanced pieces
    kit_ = scrap_kit(rng)
    heap_m = ph_mat("rust_coarse_01", 0.35, (0.2, 0.1, 0.05), name="HeapBase")
    c["heaps"] = []
    PL, PR, PS, PI = [], [], [], []
    def acc(d):
        for A, B in zip((PL, PR, PS, PI), d):
            A.extend(B)
    for k, ((cx, cy), R, H) in enumerate(HEAPS):
        hf = mound(f"Heap{k}", cx, cy, R, H, heap_m, 10 + k)
        acc(scrap_points(kit_, hf, cx, cy, R, int(R * R * 6.0), rng))
        c["heaps"].append(hf)
    # the capsule heap: smaller, a little apart, where the action happens
    hfc = mound("CapsuleHeap", HC.x, HC.y, 4.2, 1.7, heap_m, 99)
    acc(scrap_points(kit_, hfc, HC.x, HC.y, 4.2, 300, rng, embed=0.2, scl=(0.55, 1.0), exclude=("CarShell", "Fridge")))
    c["hfc"] = hfc
    # loose offcuts on the open ground
    small = [i for i, (p, w) in enumerate(kit_) if not p.name.startswith(("CarShell", "Fridge", "WashingMachine"))]
    for k in range(320):
        x, y = rng.uniform(-44, 44), rng.uniform(-28, 44)
        if math.hypot(x - HC.x, y - HC.y) < 13 or abs(x) < 7 and y < -16 or math.hypot(x - HC.x - 14, y - HC.y + 16) < 4:
            continue
        PL.append((x, y, 0.02)); PR.append((rng.normal(0, 0.1), rng.normal(0, 0.1), rng.uniform(0, 6.28)))
        PS.append(rng.uniform(0.6, 1.0)); PI.append(small[rng.integers(len(small))])
    gn_instances("Scrap", [p for p, w in kit_], PL, PR, PS, PI)
    # neighbouring industrial sheds (corrugated, with roofs) just beyond the fence
    shed = ph_mat("rusty_corrugated_iron", 0.25, (0.3, 0.3, 0.3), name="ShedIron", tint=(0.55, 0.55, 0.58))
    for k, (x, y, w, d, h) in enumerate(((-75, 70, 40, 20, 8), (-10, 78, 44, 22, 9), (62, 72, 35, 20, 7), (85, 10, 22, 36, 7))):
        box("Shed", (x, y, h / 2), (w, d, h), shed)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.0, depth=1.0, location=(x, y, h + 1.2), rotation=(0, 0, math.radians(45)))
        r_ = bpy.context.active_object; r_.scale = (w * 0.72, d * 0.72, 2.4); r_.data.materials.append(shed)
    # the Istanbul periphery: hills of apartment blocks in haze, minarets, chimneys with smoke, a power line
    periphery(rng, center=(0, 10), r_min=230, r_max=700, arc=(-10, 190), n_blocks=520, hill_h=55, minarets=3, smokes=2)
    pylons(rng, (-260, 110, 8), (260, 150, 10), n=6)
    haze((0, 330, 50), (1800, 760, 140), density=0.0011 if day != "morning" else 0.0007,
         color=(0.85, 0.88, 0.93) if day != "dusk" else (0.5, 0.55, 0.7), anis=0.3)
    haze((0, 8, 6), (110, 90, 14), density=0.0008, color=(0.88, 0.9, 0.94), anis=0.3)
    if v in ("search", "dusk"):                        # floodlight masts (real lamp housings + spot lights)
        for k, (x, y) in enumerate(((HC.x - 14, HC.y - 13), (HC.x + 14, HC.y - 12))):
            cyl("MastPole", (x, y, 4.5), 0.09, 9.0, post_m, verts=10)
            for j in (-1, 1):
                hsg = box("LampHousing", (x + j * 0.35, y, 9.0), (0.5, 0.25, 0.4), pbr("Housing", (0.15, 0.15, 0.15), 0.5, 0.5), bevel=0.03)
                lens = cyl("LampLens", (x + j * 0.35, y + 0.13, 9.0), 0.17, 0.02, pbr("Lens", (0.9, 0.9, 0.85), 0.1, 0.0, **{'Emission Color': (1.0, 0.92, 0.75, 1), 'Emission Strength': 6.0}),
                           verts=20, rot=(math.radians(90), 0, 0))
                l = bpy.data.lights.new("Flood", 'SPOT'); l.energy = 0; l.color = (1.0, 0.9, 0.75); l.spot_size = math.radians(70); l.spot_blend = 0.5
                dl = l.driver_add("energy").driver; dl.type = 'SCRIPTED'
                dl.expression = "15000 * min(1, max(0, (frame - 40) / 6))" if v == "dusk" else "0"
                lo = bpy.data.objects.new("Flood", l); bpy.context.collection.objects.link(lo); lo.location = (x + j * 0.35, y + 0.2, 9.0)
                d_ = Vector((HC.x, HC.y, 0)) - Vector((x, y, 9)); lo.rotation_euler = d_.to_track_quat('-Z', 'Y').to_euler()
    # the grab crane (material handler) beside the capsule heap
    gc = excavator("Grab", (0.72, 0.48, 0.07), tool="grab")
    gc["base"].location = HC + Vector((-6.5, -3.0, 0)); gc["base"].rotation_euler = (0, 0, 0)
    pose_arm(gc, 0, math.radians(35), math.radians(70), 0); hang_tool_level(gc); set_grab(gc, 0.6)
    c["grab"] = gc
    # the cylinder (part of a container) on the heap; the lead-brick box near the crane
    grey = painted_steel("CylGrey", (0.32, 0.33, 0.33), 0.55, 0.5)
    c["cyl"] = join([cyl("CylBody", (0, 0, 0), 0.22, 0.75, grey, verts=28), cyl("CylBore", (0, 0, 0.376), 0.08, 0.004, pbr("Bore", (0.01, 0.01, 0.01), 0.9), verts=20)], "Cylinder")
    c["cyl_rest"] = HC + Vector((-2.4, -2.9, hfc(HC.x - 2.4, HC.y - 2.9) + 0.12))
    c["cyl"].location = c["cyl_rest"]; c["cyl"].rotation_euler = (math.radians(80), 0, math.radians(30))
    lead = pbr("LeadBrick", (0.22, 0.225, 0.24), 0.45, 0.6)
    bx = HC + Vector((-3.5, -6.8, 0)); c["box_pos"] = bx
    bp = box("LeadBrickP", (0, 0, -90), (0.2, 0.1, 0.05), lead, bevel=0.004)
    for side in range(4):
        for row in range(10):
            for k in range(5):
                ang = side * math.pi / 2
                off = Vector((math.cos(ang), math.sin(ang), 0)) * 0.55
                tang = Vector((-math.sin(ang), math.cos(ang), 0))
                p = bx + off + tang * (-0.45 + k * 0.22 + 0.05 * (row % 2)) + Vector((0, 0, 0.03 + row * 0.052))
                instance(bp, p, rot=(0, 0, ang + math.pi / 2))
    # search props: a pipe for the practice lift, a tangle of scrap to tear off, two lead bricks in hand
    rm = rust_mat("PropRust", (0.25, 0.11, 0.05), 4.0)
    c["pipe"] = cyl("PracticePipe", (0, 0, 0), 0.12, 1.6, rm, verts=16, rot=(0, math.radians(90), 0))
    c["pipe_rest"] = HC + Vector((-3.2, -2.6, 0.12)); c["pipe"].location = c["pipe_rest"]
    tg = [box("TPlate", (0, 0, 0), (1.2, 0.8, 0.02), rm, rot=(0.4, 0.2, 0.3)), cyl("TPipe", (0, 0, 0), 0.06, 1.8, rm, verts=10, rot=(1.2, 0.3, 0.5)),
          box("TBar", (0, 0, 0), (1.5, 0.06, 0.06), rm, rot=(0.2, 0.6, 1.2)), box("TPanel", (0, 0.2, -0.2), (0.9, 0.04, 0.7), painted_steel("TPaint", (0.15, 0.2, 0.3), 0.6, 0.7), rot=(0.7, 0.1, 0.4))]
    c["tangle"] = join(tg, "Tangle"); c["tangle"].location = (0, -150, 0)
    for nm in ("r1", "r2"):
        c["brick_" + nm] = box("CarriedBrick" + nm, (0, -150, 0), (0.2, 0.1, 0.05), pbr("LeadBrickC", (0.22, 0.225, 0.24), 0.45, 0.6), bevel=0.004)
    # specialists / police / responders
    P = {}
    P["spec1"] = person("Spec1", 1.0, 46, "overall_white", "short03", hv=0.35, moustache=True, dosimeter=True)
    P["spec2"] = person("Spec2", 1.0, 36, "overall_orange", "short02", hat="knit", hat_col=(0.08, 0.08, 0.09), dosimeter=True)
    P["cop"] = person("Cop", 1.0, 30, "police", "short04", hat="flat", hat_col=(0.08, 0.1, 0.16), moustache=True)
    P["r1"] = person("Resp1", 1.0, 34, "overall_orange", "short02", dosimeter=True, hat="knit", hat_col=(0.12, 0.13, 0.16))
    P["r2"] = person("Resp2", 1.0, 41, "overall_white", "short04", dosimeter=True, moustache=True)
    P["op"] = person("Operator", 1.0, 50, "parka_green", "short03", hat="flat", hat_col=(0.2, 0.17, 0.13), moustache=True)
    c["people"] = P
    for h in P.values():
        place(h, (0, -150, 0), 0)
    c["det"] = detector("Det1")
    c["det"]["body"].location = (0, -150, 0)
    # police car and van outside the gate; cordon tape (arrival variant)
    c["police"] = police_car(); c["police"].location = (-8.5, -35.2, 0); c["police"].rotation_euler = (0, 0, math.radians(180))
    c["van"], c["van_wheels"] = van()
    c["van"].location = (0, -150, 0)
    tm = tape_material()
    c["tape"] = tape_between("Tape", (-5.0, -30.3), (5.0, -30.3), 1.0, tm)
    c["tape"].scale = (0.001, 1, 1)
    if v not in ("arrival",):
        c["police"].location = (0, -150, 0); c["tape"].hide_render = True
    # recovery: boom truck, concrete-block wall + operator, crane with the lead drum, the capsule
    if v == "recovery":
        gc["base"].location = HC + Vector((-12.0, 7.0, 0))
        bt = boom_truck(); bt["body"].location = HC + Vector((8.0, 2.0, 0)); bt["body"].rotation_euler = (0, 0, 0)
        c["bt"] = bt
        blocks = ph_mat("concrete_block_wall", 0.8, (0.45, 0.45, 0.43), name="CBlock")
        block_wall(HC + Vector((5.5, -9.0, 0)), math.radians(20), pbr("CBlockM", (0.5, 0.5, 0.48), 0.85))
        cr = mobile_crane(); cr["body"].location = HC + Vector((-7.5, -10.0, 0)); cr["body"].rotation_euler = (0, 0, math.radians(30))
        c["crane"] = cr
        dr, lid = lead_drum(); c["drum"] = dr; c["lid"] = lid
        steel = brushed_metal("Capsule", (0.7, 0.7, 0.72), (0.15, 0.3), 0.3)
        c["capsule"] = join([cyl("Cap", (0, 0, 0), 0.012, 0.03, steel, verts=16), cyl("CapEnd", (0, 0, 0.016), 0.009, 0.004, steel, verts=16)], "Capsule")
        c["capsule"].location = (0, -150, 0)
        ctl = box("ControlBox", (0, 0, 0), (0.4, 0.3, 0.25), painted_steel("Ctl", (0.4, 0.42, 0.4), 0.5, 0.4), bevel=0.02)
        ctl.location = HC + Vector((5.0, -10.2, 1.0))
        pole_m = pbr("Pole", (0.55, 0.5, 0.35), 0.7)
        c["pole"] = cyl("LongPole", (0, 0, 0), 0.02, 3.2, pole_m, verts=8)
        sp_root, _ = ph_model("rusted_spade_01"); c["spade"] = sp_root
    if v == "arrival":                                  # scrapyard workers who get evacuated
        for k, (o, hat) in enumerate((("wool_grey", "flat"), ("parka_green", None), ("camel", "knit"))):
            P[f"w{k}"] = person(f"Worker{k}", 1.0, 30 + 9 * k, o, ["short03", "short02", "short04"][k], hat=hat,
                                hat_col=(0.22, 0.18, 0.14) if hat == "flat" else (0.1, 0.1, 0.12), moustache=(k != 1))
            place(P[f"w{k}"], (0, -150, 0), 0)
    if v == "recovery":                                 # the next pair waiting, the dosimetry tent, the concrete mixer
        P["r3"] = person("Resp3", 1.0, 29, "overall_white", "short03", dosimeter=True)
        P["r4"] = person("Resp4", 1.0, 44, "overall_orange", "short02", dosimeter=True, moustache=True)
        for k in ("r3", "r4"):
            place(P[k], (0, -150, 0), 0)
        tent_c = HC + Vector((14.0, -16.0, 0)); c["tent"] = tent_c
        canvas = noisy("Canvas", (0.42, 0.45, 0.36), 0.9, dirt=0.4, scale=4)
        for dx in (-1.5, 1.5):
            for dy in (-1.5, 1.5):
                cyl("TentPole", (tent_c.x + dx, tent_c.y + dy, 1.1), 0.025, 2.2, post_m, verts=8)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.3, depth=0.9, location=(tent_c.x, tent_c.y, 2.6), rotation=(0, 0, math.radians(45)))
        bpy.context.active_object.data.materials.append(canvas)
        box("TentBack", (tent_c.x, tent_c.y + 1.5, 1.1), (3.0, 0.02, 2.2), canvas)
        tab = box("Table", (tent_c.x, tent_c.y + 0.6, 0.74), (1.6, 0.8, 0.04), noisy("TableTop", (0.45, 0.35, 0.22), 0.7))
        for dx in (-0.7, 0.7):
            for dy in (-0.3, 0.3):
                cyl("TableLeg", (tent_c.x + dx, tent_c.y + 0.6 + dy, 0.36), 0.02, 0.72, post_m, verts=6)
        for k in range(8):
            box("Badge", (tent_c.x - 0.5 + k * 0.12, tent_c.y + 0.45, 0.765), (0.035, 0.045, 0.008), pbr("BadgeM", (0.85, 0.82, 0.7), 0.4))
        box("Logbook", (tent_c.x + 0.4, tent_c.y + 0.6, 0.765), (0.3, 0.22, 0.015), pbr("Logbook", (0.15, 0.2, 0.35), 0.6))
        P["tentman"] = person("TentMan", 1.0, 52, "suit_grey", "short03", moustache=True, hv=0.5)
        stool = cyl("Stool", (tent_c.x, tent_c.y + 1.15, 0.22), 0.18, 0.44, post_m, verts=12)
        mx_tk, mx_wh, _, _ = truck("Mixer", (0.55, 0.55, 0.52), bed_len=4.6)
        mx_tk.location = (-14.0, -36.5, 0)
        tilt = bpy.data.objects.new("MixerTilt", None); bpy.context.collection.objects.link(tilt); tilt.parent = mx_tk
        tilt.location = (-0.3, 0, 2.0); tilt.rotation_euler = (0, math.radians(-78), 0)
        drum = cyl("MixerDrum", (0, 0, 0), 0.95, 3.4, painted_steel("MixDrum", (0.75, 0.7, 0.55), 0.5, 0.6), verts=24)
        drum.parent = tilt; drum.location = (0, 0, 0)
        for k in range(6):
            fin = box("MixerFin", (0, 0, 0), (0.06, 0.12, 2.0), painted_steel("MixFin", (0.6, 0.55, 0.42), 0.5, 0.6)); fin.parent = drum
            a = k / 6 * 2 * math.pi; fin.location = (1.0 * math.cos(a), 1.0 * math.sin(a), 0); fin.rotation_euler = (0, 0, a)
        dd = drum.driver_add("rotation_euler", 2).driver; dd.type = 'SCRIPTED'; dd.expression = "frame * 0.08"
        c["mixer"] = mx_tk
    if v == "investigation":                            # the two opened shells, roped off
        for k, off in enumerate((Vector((-1.0, 0, 0)), Vector((1.0, 0.2, 0)))):
            o_, kk = container(f"Shell{k}"); o_.location = HC + Vector((-2.0, -8.0, 0)) + off; o_.rotation_euler = (0, 0, 0.4 * k)
            kk["trefoil"].hide_render = False
        tm3 = tape_material()
        q = [HC + Vector((dx, dy, 0)) for dx, dy in ((-4.5, -10.5), (0.5, -10.5), (0.5, -5.5), (-4.5, -5.5))]
        for a, b in zip(q, q[1:] + q[:1]):
            tape_between("ShellTape", a, b, 0.9, tm3); cyl("Stake", (a.x, a.y, 0.45), 0.02, 0.9, post_m, verts=6)
        P["inv"] = person("Investigator", 1.0, 48, "camel", "short03", hat="flat", hat_col=(0.3, 0.26, 0.2), moustache=True)
        P["inv2"] = person("Investigator2", 1.0, 39, "navy", "short02", dosimeter=True)
        for k in ("inv", "inv2"):
            place(P[k], (0, -150, 0), 0)
    if v in ("search", "recovery", "dusk"):
        # cordon line around the work area on stakes
        tm2 = tape_material()
        pts = [HC + Vector((dx, dy, 0)) for dx, dy in ((-14, -14), (14, -14), (14, 12), (-14, 12))]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            tape_between("Cordon", a, b, 0.95, tm2)
            cyl("Stake", (a.x, a.y, 0.5), 0.02, 1.0, post_m, verts=6)
    return c


# ============================================================================ animation helpers
def hold_detector(c, h, sec, sweep=0.0, level=0.5):
    """Detector in the right hand at waist height, probe in the left swept low over the scrap."""
    fwd = forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    sh = h.bone_head("upperarm01.R")
    hand = sh + fwd * 0.32 - side * 0.1 + Vector((0, 0, -0.45))
    reach(h, "R", hand, Vector((side.x, side.y, -0.7)), fwd)
    d = c["det"]["body"]; d.location = hand + fwd * 0.05 + Vector((0, 0, 0.02))
    d.rotation_euler = (0, 0, math.atan2(fwd.y, fwd.x) - math.pi / 2)
    c["det"]["needle"].rotation_euler = (0, math.radians(-50 + 100 * level + 3 * math.sin(sec * 9)), 0)
    shl = h.bone_head("upperarm01.L")
    probe = shl + fwd * (0.55) + side * (0.15 + 0.25 * math.sin(sweep)) + Vector((0, 0, -0.75))
    reach(h, "L", probe, Vector((-side.x, -side.y, -0.7)), fwd + Vector((0, 0, -0.6)))
    pr = c["det"]["probe"]; pr.location = probe + fwd * 0.12 + Vector((0, 0, -0.05))
    pr.rotation_mode = 'QUATERNION'; pr.rotation_quaternion = (fwd + Vector((0, 0, -0.7))).to_track_quat('Z', 'Y')
    fingers_curl(h, 60, thumb=30)


def walk(h, a, b, sec, speed=1.0, stride=1.25):
    a = Vector(a); b = Vector(b); d = b - a; L_ = d.length; s = min(L_, speed * sec)
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0)
    moving = s < L_
    pose_walk(h, (s / stride) % 1.0 if moving else 0.0, stride=24 if moving else 0, arm_swing=12 if moving else 0)
    arms_relaxed(h, (s / stride) % 1.0, 14 if moving else 0)
    p = a + d.normalized() * s
    place(h, (p.x, p.y, 0), face_angle(a, b)); attach_cap(h)
    return p


def stand(h, loc, look, **kw):
    reset_pose(h); stand_pose(h, **kw); place(h, loc, face_angle(loc, look)); attach_cap(h)


def grab_idle_swing(c, sec):
    gc = c["grab"]
    pose_arm(gc, math.radians(-20 + 40 * math.sin(sec * 0.35)), math.radians(32), math.radians(65), 0)
    hang_tool_level(gc); set_grab(gc, 0.5)


# ============================================================================ moves
def anim_wide(c, t):
    grab_idle_swing(c, t * dur("ch1_15a"))


def cam_wide(c, t):
    e = ease(t)
    return (Vector((-26, -32, 6.5)).lerp(Vector((-24, -30, 8.0)), e), Vector((4, 16, 4.5)), 26)


def _heap_pt(i, r, z, surface=False, ang=-1.1):
    (cx, cy), R, H = HEAPS[i]
    p = Vector((cx + r * math.cos(ang), cy + r * math.sin(ang), z))
    if surface:
        p.z = z + H * max(0.0, 1 - r / R) ** 1.15 * (1 - 0.15 * r / R)
    return p


def anim_heap(c, t):
    grab_idle_swing(c, t * dur("ch1_15b"))


def cam_heap(c, t):
    e = ease(t)
    return (_heap_pt(0, 22.0, 2.2).lerp(_heap_pt(0, 16.5, 2.4), e), _heap_pt(0, 8.0, 0.4, surface=True), 35)


def anim_van(c, t):
    sec = t * dur("ch2_7a")
    grab_idle_swing(c, sec)
    stop = 2.4
    x = -18 + 14 * min(sec, stop) - 14 * min(sec, stop) ** 2 / (2 * stop)
    vn = c["van"]; vn.location = (x, -35.5, 0); vn.rotation_euler = (0, 0, 0)
    for w in c["van_wheels"]:
        w.rotation_euler = (0, (x + 18) / 0.33, 0)
    h = c["people"]["spec1"]
    if sec > stop + 0.2:
        walk(h, (x + 0.4, -34.4, 0), (x + 0.6, -31.5, 0), sec - stop - 0.2, speed=1.0)
    else:
        place(h, (0, -150, 0), 0)
    stand(c["people"]["cop"], (0, -150, 0), (0, 0))
    c["focus"] = Vector((x, -35.5, 1.2))


def cam_van(c, t):
    e = ease(t)
    return (Vector((10.0, -39.5, 1.5)).lerp(Vector((9.0, -39.2, 1.55)), e), Vector((-3.0, -33.5, 1.6)), 30)


def anim_cordon(c, t):
    sec = t * dur("ch2_8b")
    grab_idle_swing(c, sec)
    c["van"].location = (-15.5, -35.5, 0)
    k = ease(min(1.0, sec / 3.4))
    h = c["people"]["cop"]
    x = -5.0 + 9.5 * k
    walk(h, (-5.0, -31.0, 0), (4.6, -31.0, 0), sec * 0.85, speed=1.2)
    hp = h.arm.location
    fwd = forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    hand = h.bone_head("upperarm01.R") + side * 0.0 + fwd * 0.25 + Vector((0, 0, -0.35)) - side * 0.25
    reach(h, "R", hand, Vector((0.3, 0, -0.8)), -side)
    tape_len = max(0.001, (hand.x + 5.0) / 10.0)
    c["tape"].scale = (tape_len, 1, 1); c["tape"].location = (-5.0 + 5.0 * tape_len, -30.3, 1.0)
    walk(c["people"]["spec1"], (-2.5, -24.0, 0), (-1.5, -33.0, 0), sec, speed=0.9)
    c["focus"] = Vector((hp.x, -31.0, 1.2))


def cam_cordon(c, t):
    e = ease(t)
    return (Vector((9.0, -37.5, 1.45)).lerp(Vector((8.2, -37.9, 1.45)), e), Vector((-1.5, -31.0, 1.3)), 28)


def anim_sweep(c, t):
    sec = t * dur("ch3_1b")
    grab_idle_swing(c, sec * 0.3)
    h = c["people"]["spec2"]
    a = HC + Vector((3.5, -4.8, 0)); b = HC + Vector((1.8, -3.0, 0))
    p = walk(h, a, b, sec, speed=0.45, stride=0.9)
    h.rot("spine03", forward(h).cross(Vector((0, 0, 1))), -12)
    level = 0.25 + 0.6 * ease(min(1.0, sec / dur("ch3_1b")))
    hold_detector(c, h, sec, sweep=sec * 1.6, level=level)
    stand(c["people"]["spec1"], HC + Vector((5.5, -7.0, 0)), HC)
    c["focus"] = c["det"]["body"].location


def cam_sweep(c, t):
    e = ease(t)
    return (HC + Vector((-0.6, -7.2, 1.35)).lerp(Vector((-0.2, -6.8, 1.35)), e), HC + Vector((2.4, -3.7, 1.0)), 38)


def anim_grab(c, t):
    sec = t * dur("ch3_4a")
    gc = c["grab"]
    k = ease(min(1.0, sec / dur("ch3_4a")))
    rest = c["cyl_rest"]; bx = c["box_pos"] + Vector((0, 0, 1.6))
    path = rest.lerp(bx, k) + Vector((0, 0, 1.6 * math.sin(math.pi * k) + 0.9))
    arm_ik(gc, path + Vector((0, 0, 1.15)))
    hang_tool_level(gc); set_grab(gc, 0.05)
    c["cyl"].location = path; c["cyl"].rotation_euler = (math.radians(80 * (1 - k) + 90 * k * 0), 0, math.radians(30))
    stand(c["people"]["spec1"], HC + Vector((-4.0, -9.0, 0)), path)
    stand(c["people"]["spec2"], HC + Vector((-2.6, -9.6, 0)), path, hands_pockets=True)
    c["focus"] = path


def cam_grab(c, t):
    e = ease(t)
    return (HC + Vector((4.5, -16.0, 1.4)).lerp(Vector((3.8, -15.4, 1.6)), e), HC + Vector((-3.2, -3.5, 3.6)), 26)


def anim_boom(c, t):
    sec = t * dur("ch3_10a")
    grab_idle_swing(c, 0)
    bt = c["bt"]; k = ease(min(1.0, sec / 3.2))
    bt["body"].location = HC + Vector((16.0 - 8.0 * k, 3.0, 0)); bt["body"].rotation_euler = (0, 0, 0)
    for w in bt["wheels"]:
        w.rotation_euler = (0, -(8.0 * k) / 0.45, 0)
    bt["piv"].rotation_euler = (0, math.radians(-3), math.radians(8))
    bt["tele"].scale = (0.55 + 0.45 * ease(min(1.0, max(0.0, (sec - 1.0) / 3.0))), 1, 1)
    bt["tele"].location = (-4.5 * bt["tele"].scale.x, 0, 0); bt["head"].location = (-9.0 * bt["tele"].scale.x, 0, 0)
    bt["head"].rotation_euler = (0, math.radians(3), 0)
    crane_hang(c["crane"], math.radians(35), math.radians(28), 4.0)
    c["drum"].location = c["crane"]["hook"].location + Vector((0, 0, -1.6)); c["lid"].location = (0, -150, 0)
    stand(c["people"]["op"], HC + Vector((5.2, -10.6, 0)), HC)
    c["focus"] = bt["body"].location + Vector((0, 0, 1.5))


def cam_boom(c, t):
    e = ease(t)
    return (HC + Vector((15.5, -9.5, 2.0)).lerp(Vector((14.8, -9.0, 2.2)), e), HC + Vector((7.0, 2.5, 2.0)), 28)


def anim_drop(c, t):
    sec = t * dur("ch3_17b")
    grab_idle_swing(c, 0)
    bt = c["bt"]; bt["body"].location = HC + Vector((8.0, 3.0, 0)); bt["piv"].rotation_euler = (0, math.radians(-3), math.radians(8))
    cr = c["crane"]
    drum_top = HC + Vector((-1.0, -5.0, 0.0))
    hk = crane_hang(cr, 0, 0, 0)
    # place the crane hook straight above the drum spot: aim slew/luff once, then the drum hangs 0.25 m off the ground
    cr["piv"].rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
    base = cr["piv"].matrix_world.translation
    d = drum_top - base; slew = math.atan2(d.y, d.x) - cr["body"].rotation_euler.z
    horiz = math.hypot(d.x, d.y); luff = math.acos(min(1.0, horiz / 12.4))
    hk = crane_hang(cr, slew, luff, 1.0)
    hk = crane_hang(cr, slew, luff, hk.z - 1.85)
    drum = c["drum"]; drum.location = hk + Vector((0, 0, -1.65)); c["lid"].location = (0, -150, 0)
    mouth = drum.location + Vector((0, 0, 0.92))
    # responder with the shovel tips it over the drum; the capsule slides off and drops in
    h2 = c["people"]["r2"]; stance = mouth + Vector((0.2, -1.25, 0)); stance.z = 0
    reset_pose(h2); stand_pose(h2); place(h2, stance, face_angle(stance, mouth)); attach_cap(h2)
    fwd = forward(h2); side = fwd.cross(Vector((0, 0, 1))).normalized()
    tip_k = ease(min(1.0, max(0.0, (sec - 0.6) / 1.2)))
    blade = mouth + Vector((0, 0, 0.18)) - fwd * 0.18
    handle = blade - fwd * 0.92 + Vector((0, 0, 0.05 + 0.18 * tip_k))
    h2.rot("spine03", side, -14)
    reach(h2, "R", handle, Vector((side.x, side.y, -0.7)), blade - handle)
    reach(h2, "L", handle.lerp(blade, 0.45), Vector((-side.x, -side.y, -0.7)), blade - handle)
    fingers_curl(h2, 70, thumb=40)
    sp = c["spade"]
    if sp is not None:
        sp.location = blade + (handle - blade).normalized() * 0.5; sp.rotation_mode = 'QUATERNION'
        sp.rotation_quaternion = (blade - handle).to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), tip_k * 1.2)
    cap = c["capsule"]
    fall = max(0.0, sec - 1.9)
    if fall <= 0:
        cap.location = blade + Vector((0, 0, 0.03))
    else:
        cap.location = blade + Vector((0, 0.0, 0.03 - 4.9 * fall * fall))
        if cap.location.z < mouth.z - 0.5:
            cap.location = (0, -150, 0)
    cap.rotation_euler = (sec * 3.0, sec * 1.3, 0)
    # partner with the long pole stands back
    h1 = c["people"]["r1"]; st1 = HC + Vector((3.6, -2.4, 0))
    reset_pose(h1); stand_pose(h1); place(h1, st1, face_angle(st1, HC)); attach_cap(h1)
    pl = c["pole"]; f1 = forward(h1); s1 = f1.cross(Vector((0, 0, 1)))
    grip = h1.bone_head("upperarm01.R") + f1 * 0.35 + Vector((0, 0, -0.35))
    end = grip + f1 * 2.4 + Vector((0, 0, -1.0))
    reach(h1, "R", grip, Vector((s1.x, s1.y, -0.7)), end - grip); reach(h1, "L", grip.lerp(end, 0.25), Vector((-s1.x, -s1.y, -0.7)), end - grip)
    pl.location = grip.lerp(end, 0.4); pl.rotation_mode = 'QUATERNION'; pl.rotation_quaternion = (end - grip).to_track_quat('Z', 'Y')
    c["focus"] = mouth


def cam_drop(c, t):
    e = ease(t)
    m = c["drum"].location + Vector((0, 0, 0.95))
    return (m + Vector((4.4, -1.4, 0.35)).lerp(Vector((4.0, -1.3, 0.35)), e), m + Vector((0.0, -0.7, -0.35)), 28)


def _focus(c, t):
    return c.get("focus", HC + Vector((0, 0, 1)))


# ============================================================================ every scrapyard shot in the plan
from durs import dur


def C(p0, p1, tgt, lens, rel=True):
    """Camera move p0 -> p1 looking at tgt (relative to the capsule heap HC unless rel=False)."""
    o = HC if rel else Vector((0, 0, 0))
    return lambda c, t: (o + Vector(p0).lerp(Vector(p1), ease(t)), o + Vector(tgt), lens)


def sec_of(name, t):
    sec = t * dur(name)
    bpy.context.scene.frame_current = int(round(sec * 24)) + 1
    return sec


def carry(c, obj, a, b, k, lift=1.6, hang=1.15):
    """Grab carries `obj` from a to b on an arc (k 0..1), tines closed."""
    gc = c["grab"]; path = Vector(a).lerp(Vector(b), k) + Vector((0, 0, lift * math.sin(math.pi * k) + 0.9))
    arm_ik(gc, path + Vector((0, 0, hang))); hang_tool_level(gc); set_grab(gc, 0.05)
    obj.location = path
    return path


def pair_pole_shovel(c, sec, at, drum_pos=None, scoop=True):
    """r1 pushes scrap with the long pole at `at`; r2 shovels toward the drum."""
    at = Vector(at)
    h1 = c["people"]["r1"]; st1 = at + Vector((-2.3, -1.4, 0)); st1.z = 0
    stand_pose(h1); place(h1, st1, face_angle(st1, at))
    f1 = forward(h1); s1 = f1.cross(Vector((0, 0, 1)))
    push = 0.25 * math.sin(sec * 1.4)
    grip = h1.bone_head("upperarm01.R") + f1 * (0.3 + push) + Vector((0, 0, -0.35))
    end = at + Vector((0, 0, 0.2)) + f1 * push
    reach(h1, "R", grip, Vector((s1.x, s1.y, -0.7)), end - grip); reach(h1, "L", grip.lerp(end, 0.2), Vector((-s1.x, -s1.y, -0.7)), end - grip)
    pl = c["pole"]; pl.location = grip.lerp(end, 0.5); pl.scale = (1, 1, (end - grip).length / 3.2)
    pl.rotation_mode = 'QUATERNION'; pl.rotation_quaternion = (end - grip).to_track_quat('Z', 'Y')
    h2 = c["people"]["r2"]; st2 = at + Vector((0.4, -1.5, 0)); st2.z = 0
    stand_pose(h2); place(h2, st2, face_angle(st2, at))
    f2 = forward(h2); s2 = f2.cross(Vector((0, 0, 1)))
    k = 0.5 - 0.5 * math.cos(sec * 2.2) if scoop else 0.0
    blade = (at + Vector((0, 0, 0.1))).lerp(st2 + f2 * 0.7 + Vector((0, 0, 0.45)), k)
    handle = blade - f2 * 0.85 + Vector((0, 0, 0.35))
    h2.rot("spine03", s2, -(10 + 15 * (1 - k)))
    reach(h2, "R", handle, Vector((s2.x, s2.y, -0.7)), blade - handle); reach(h2, "L", handle.lerp(blade, 0.45), Vector((-s2.x, -s2.y, -0.7)), blade - handle)
    fingers_curl(h1, 70, thumb=40); fingers_curl(h2, 70, thumb=40)
    sp = c["spade"]
    if sp is not None:
        sp.location = blade + (handle - blade).normalized() * 0.5; sp.rotation_mode = 'QUATERNION'; sp.rotation_quaternion = (blade - handle).to_track_quat('Z', 'Y')


def drum_on_crane(c, at, height):
    """Crane hook straight above `at`; the drum hangs with its base `height` above the ground."""
    cr = c["crane"]
    cr["piv"].rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
    base = cr["piv"].matrix_world.translation; d = Vector(at) - base
    slew = math.atan2(d.y, d.x) - cr["body"].rotation_euler.z
    luff = math.acos(min(1.0, math.hypot(d.x, d.y) / 12.4))
    hk = crane_hang(cr, slew, luff, 1.0)
    hk = crane_hang(cr, slew, luff, max(0.3, hk.z - (height + 1.65 + 0.2)))
    c["drum"].location = hk + Vector((0, 0, -1.65))
    return c["drum"].location


def boom_parked(c):
    bt = c["bt"]; bt["body"].location = HC + Vector((8.0, 3.0, 0)); bt["piv"].rotation_euler = (0, math.radians(-3), math.radians(8))
    bt["tele"].scale = (1, 1, 1); bt["tele"].location = (-4.5, 0, 0); bt["head"].location = (-9.0, 0, 0)


def recovery_base(c, sec):
    grab_idle_swing(c, 0); boom_parked(c)
    c["lid"].location = (0, -150, 0)
    stand(c["people"]["op"], HC + Vector((5.2, -10.7, 0)), HC)


# ---- Chapter 2 gate
def a_gate_detector(c, t):
    sec = sec_of("ch2_7b", t); grab_idle_swing(c, sec)
    c["van"].location = (-1.0, -35.5, 0)
    h = c["people"]["spec1"]
    walk(h, (-3.5, -27.0, 0), (1.5, -24.0, 0), sec, speed=0.55, stride=0.9)
    hold_detector(c, h, sec, sweep=sec * 1.2, level=0.3 + 0.55 * ease(min(1.0, sec / dur("ch2_7b"))))
    c["focus"] = c["det"]["body"].location


def a_evacuate(c, t):
    sec = sec_of("ch2_8a", t); grab_idle_swing(c, sec)
    c["van"].location = (-1.0, -35.5, 0)
    for k in range(3):
        walk(c["people"][f"w{k}"], (-1.5 + 1.4 * k, -14.0 - 2.5 * k, 0), (-2.5 + 2.0 * k, -38.0, 0), sec + 1.2 * k, speed=1.3)
    stand(c["people"]["spec1"], (3.8, -29.0, 0), (0, -20), crossed=True)
    c["focus"] = c["people"]["w0"].arm.location + Vector((0, 0, 1.3))


# ---- Chapter 3, Jan 8 (grey afternoon)
def a_fanout(c, t):
    sec = sec_of("ch3_1a", t); grab_idle_swing(c, sec * 0.4)
    for nm, a, b in (("spec1", (-1.0, -12.0), (-5.0, -4.0)), ("spec2", (0.0, -12.0), (4.0, -4.5))):
        h = c["people"][nm]; walk(h, HC + Vector((*a, 0)), HC + Vector((*b, 0)), sec, speed=0.8)
        hold_detector(c, h, sec, sweep=sec, level=0.5) if nm == "spec2" else None


def a_point(c, t):
    sec = sec_of("ch3_2a", t); grab_idle_swing(c, sec * 0.3)
    h = c["people"]["spec1"]; stand(h, HC + Vector((-2.2, -5.4, 0)), c["cyl_rest"])
    k = ease(min(1.0, sec / 1.2)); tgt = c["cyl_rest"]
    from human import reach as rch
    sh = h.bone_head("upperarm01.R"); d = (tgt - sh).normalized()
    rest = sh + Vector((0, 0, -0.6)); rch(h, "R", rest.lerp(sh + d * 0.62, k), Vector((0, 0, -1)), d)
    h2 = c["people"]["spec2"]; stand(h2, HC + Vector((-0.9, -5.9, 0)), tgt); hold_detector(c, h2, sec, sweep=0, level=0.8)
    c["focus"] = h.bone_head("head")


def a_cyl_push(c, t):
    grab_idle_swing(c, sec_of("ch3_2b", t) * 0.3)
    c["focus"] = c["cyl_rest"]


def a_bricks(c, t):
    sec = sec_of("ch3_3a", t); grab_idle_swing(c, sec * 0.3)
    bx = c["box_pos"]
    for nm, side in (("r1", -1), ("r2", 1)):
        h = c["people"][nm]; st = bx + Vector((side * 0.95, -0.85, 0)); st.z = 0
        stand_pose(h); place(h, st, face_angle(st, bx))
        f = forward(h); sd = f.cross(Vector((0, 0, 1)))
        k = 0.5 - 0.5 * math.cos(sec * 1.8 + (0 if side < 0 else 1.6))
        hand = (st + Vector((0, 0, 0.75)) + f * 0.25).lerp(bx + Vector((side * 0.3, -0.45, 0.6)), k)
        h.rot("spine03", sd, -(8 + 22 * k))
        reach(h, "R", hand + sd * 0.07, Vector((sd.x, sd.y, -0.7)), f); reach(h, "L", hand - sd * 0.07, Vector((-sd.x, -sd.y, -0.7)), f)
        fingers_curl(h, 50, thumb=30)
        c["brick_" + nm].location = hand + f * 0.04
    c["focus"] = bx + Vector((0, 0, 0.6))


def a_practice(c, t):
    sec = sec_of("ch3_3b", t)
    k = ease(min(1.0, sec / dur("ch3_3b")))
    carry(c, c["pipe"], c["pipe_rest"], c["pipe_rest"] + Vector((-2.5, -2.5, 0)), k)
    stand(c["people"]["spec1"], HC + Vector((-4.0, -9.0, 0)), HC, crossed=True)
    c["focus"] = c["pipe"].location


def a_carry(c, t):
    sec = sec_of("ch3_4a", t); k = ease(min(1.0, sec / dur("ch3_4a"))) * 0.75
    p = carry(c, c["cyl"], c["cyl_rest"], c["box_pos"] + Vector((0, 0, 0.75)), k)
    stand(c["people"]["spec1"], HC + Vector((-4.0, -9.0, 0)), p); stand(c["people"]["spec2"], HC + Vector((-2.6, -9.6, 0)), p, hands_pockets=True)
    c["focus"] = p


def a_lower(c, t):
    sec = sec_of("ch3_4b", t); k = 0.75 + 0.25 * ease(min(1.0, sec / dur("ch3_4b")))
    p = carry(c, c["cyl"], c["cyl_rest"], c["box_pos"] + Vector((0, 0, 0.75)), k, lift=1.6)
    if k > 0.97:
        set_grab(c["grab"], 0.5)
    c["cyl"].rotation_euler = (0, 0, 0)
    stand(c["people"]["spec1"], c["box_pos"] + Vector((-1.8, -1.2, 0)), c["box_pos"])
    c["focus"] = c["box_pos"] + Vector((0, 0, 0.8))


def cyl_in_box(c):
    c["cyl"].location = c["box_pos"] + Vector((0, 0, 0.42)); c["cyl"].rotation_euler = (0, 0, 0)
    pose_arm(c["grab"], math.radians(-30), math.radians(40), math.radians(70), 0); hang_tool_level(c["grab"]); set_grab(c["grab"], 0.6)


def a_needle_high(c, t):
    sec = sec_of("ch3_5a", t); cyl_in_box(c)
    h = c["people"]["spec2"]; stand(h, c["box_pos"] + Vector((2.2, -1.0, 0)), HC + Vector((0, 0, 0)))
    hold_detector(c, h, sec, sweep=sec * 0.8, level=0.88)
    c["focus"] = c["det"]["body"].location


def a_bore(c, t):
    cyl_in_box(c); grab_idle_swing(c, 0)
    c["focus"] = c["box_pos"] + Vector((0, 0, 0.8))


def a_follow(c, t):
    sec = sec_of("ch3_6a", t); cyl_in_box(c)
    h = c["people"]["spec2"]
    walk(h, HC + Vector((-12.0, 4.0, 0)), HC + Vector((-3.5, 0.5, 0)), sec, speed=0.7, stride=1.0)
    hold_detector(c, h, sec, sweep=sec * 1.5, level=0.5 + 0.1 * sec)
    c["focus"] = h.arm.location + Vector((0, 0, 1.2))


def a_raise_hand(c, t):
    sec = sec_of("ch3_6b", t); cyl_in_box(c)
    h = c["people"]["spec2"]; stand(h, HC + Vector((-3.5, 0.5, 0)), HC)
    hold_detector(c, h, sec, sweep=0, level=0.9)
    k = ease(min(1.0, max(0.0, (sec - 0.6) / 0.8)))
    sh = h.bone_head("upperarm01.L")
    reach(h, "L", sh + Vector((0, 0, -0.55)).lerp(Vector((0.05, 0, 0.6)), k), Vector((-1, 0, 0)), Vector((0, 0, 1)))
    stand(c["people"]["spec1"], HC + Vector((-7.0, -2.0, 0)), h.arm.location)
    c["focus"] = h.bone_head("head")


def a_tear(c, t):
    sec = sec_of("ch3_7a", t); k = ease(min(1.0, sec / dur("ch3_7a")))
    cyl_in_box(c)
    top = HC + Vector((0, 0, c["hfc"](HC.x, HC.y) - 0.2))
    carry(c, c["tangle"], top, top + Vector((-4.0, 2.5, -1.5)), k * 0.6, lift=2.5)
    c["focus"] = c["tangle"].location


def a_needle_climb(c, t):
    sec = sec_of("ch3_7b", t); k = ease(min(1.0, sec / dur("ch3_7b")))
    cyl_in_box(c)
    top = HC + Vector((0, 0, c["hfc"](HC.x, HC.y) - 0.2))
    carry(c, c["tangle"], top, top + Vector((-4.0, 2.5, -1.5)), 0.3 + 0.5 * k, lift=2.5)
    h = c["people"]["spec1"]; stand(h, HC + Vector((-1.5, -6.0, 0)), HC)
    hold_detector(c, h, sec, sweep=0, level=0.5 + 0.45 * k)
    c["focus"] = c["det"]["body"].location


def a_heap_wide(c, t):
    sec = sec_of("ch3_8a", t); cyl_in_box(c)
    top = HC + Vector((0, 0, c["hfc"](HC.x, HC.y) - 0.2))
    carry(c, c["tangle"], top, top + Vector((-5.0, 3.5, -1.5)), 0.5 + 0.5 * ease(min(1.0, sec / dur("ch3_8a"))), lift=2.5)


def a_step_back(c, t):
    sec = sec_of("ch3_8b", t); cyl_in_box(c); grab_idle_swing(c, sec)
    for nm, a in (("spec1", (-1.0, -4.5)), ("spec2", (0.8, -4.8))):
        h = c["people"][nm]; p0 = HC + Vector((*a, 0)); p1 = p0 + Vector((0, -1.6, 0))
        s = min(1.6, 0.55 * sec); p = p0.lerp(p1, s / 1.6)
        stand_pose(h, crossed=(nm == "spec1")); place(h, p, face_angle(p, HC))
    c["focus"] = c["people"]["spec1"].bone_head("head")


def a_grab_stop(c, t):
    sec = sec_of("ch3_9a", t); cyl_in_box(c)
    k = ease(min(1.0, sec / dur("ch3_9a")))
    pose_arm(c["grab"], math.radians(-20 + 30 * k), math.radians(32 - 12 * k), math.radians(65 + 20 * k), 0)
    hang_tool_level(c["grab"]); set_grab(c["grab"], 0.5)
    c["focus"] = c["grab"]["base"].location + Vector((0, 0, 2))


def a_walk_out(c, t):
    sec = sec_of("ch3_9b", t); cyl_in_box(c); grab_idle_swing(c, 0)
    walk(c["people"]["spec1"], HC + Vector((-1.0, -6.0, 0)), HC + Vector((-1.0, -22.0, 0)), sec, speed=1.0)
    walk(c["people"]["spec2"], HC + Vector((0.6, -5.0, 0)), HC + Vector((0.4, -22.0, 0)), sec - 0.4, speed=1.0)
    c["focus"] = c["people"]["spec1"].arm.location + Vector((0, 0, 1.2))


# ---- Chapter 3, Jan 10 (clear cold morning)
def a_boom_head(c, t):
    sec = sec_of("ch3_10b", t); recovery_base(c, sec)
    bt = c["bt"]; bt["head"].rotation_euler = (0, math.radians(3 + 2 * math.sin(sec * 0.9)), 0)
    drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.0)
    bpy.context.view_layer.update(); c["focus"] = bt["head"].matrix_world.translation + Vector((0, 0, -0.5))


def a_operator(c, t):
    sec = sec_of("ch3_11a", t); recovery_base(c, sec)
    h = c["people"]["op"]; stand(h, HC + Vector((5.2, -10.7, 0)), HC + Vector((5.0, -10.2, 1.0)))
    ctl = HC + Vector((5.0, -10.2, 1.0))
    f = forward(h); sd = f.cross(Vector((0, 0, 1)))
    reach(h, "R", ctl + Vector((0.08, 0, 0.14 + 0.01 * math.sin(sec * 3))), Vector((sd.x, sd.y, -0.7)), f)
    reach(h, "L", ctl + Vector((-0.08, 0, 0.14)), Vector((-sd.x, -sd.y, -0.7)), f)
    h.rot("head", sd, 6 * math.sin(sec * 0.6))
    drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.0)
    c["focus"] = h.bone_head("head")


def a_drum_lower(c, t):
    sec = sec_of("ch3_11b", t); recovery_base(c, sec)
    h_ = 3.0 * (1 - ease(min(1.0, sec / dur("ch3_11b"))))
    p = drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.05 + h_)
    c["focus"] = p + Vector((0, 0, 0.6))


def a_pair_out(c, t):
    sec = sec_of("ch3_12a", t); recovery_base(c, sec)
    drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.05)
    walk(c["people"]["r1"], HC + Vector((4.6, -9.6, 0)), HC + Vector((1.0, -4.5, 0)), sec, speed=1.0)
    walk(c["people"]["r2"], HC + Vector((5.4, -9.9, 0)), HC + Vector((2.2, -4.8, 0)), sec - 0.3, speed=1.0)
    c["pole"].location = (0, -150, 0)
    c["focus"] = c["people"]["r1"].arm.location + Vector((0, 0, 1.2))


def a_pole(c, t):
    sec = sec_of("ch3_12b", t); recovery_base(c, sec)
    drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.05)
    pair_pole_shovel(c, sec, HC + Vector((-0.6, -2.6, 0.4)), scoop=False)
    c["focus"] = c["pole"].location


def a_shovel(c, t):
    sec = sec_of("ch3_13a", t); recovery_base(c, sec)
    drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.05)
    pair_pole_shovel(c, sec, HC + Vector((-0.6, -2.6, 0.4)))
    c["focus"] = c["people"]["r2"].bone_head("spine03")


def a_hoist(c, t):
    sec = sec_of("ch3_13b", t); recovery_base(c, sec)
    p = drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.05 + 2.6 * ease(min(1.0, sec / dur("ch3_13b"))))
    stand(c["people"]["r1"], HC + Vector((1.2, -6.5, 0)), p); stand(c["people"]["r2"], HC + Vector((2.2, -6.0, 0)), p, crossed=True)
    c["focus"] = p + Vector((0, 0, 0.6))


def a_swap(c, t):
    sec = sec_of("ch3_14a", t); recovery_base(c, sec)
    drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.05)
    walk(c["people"]["r1"], HC + Vector((1.0, -4.5, 0)), HC + Vector((4.8, -9.8, 0)), sec, speed=0.75)
    walk(c["people"]["r2"], HC + Vector((2.0, -4.6, 0)), HC + Vector((5.6, -10.0, 0)), sec - 0.3, speed=0.7)
    walk(c["people"]["r3"], HC + Vector((4.4, -9.9, 0)), HC + Vector((0.6, -4.8, 0)), sec - 0.6, speed=1.0)
    walk(c["people"]["r4"], HC + Vector((5.2, -10.3, 0)), HC + Vector((1.8, -5.2, 0)), sec - 0.9, speed=1.0)
    c["pole"].location = (0, -150, 0)
    c["focus"] = c["people"]["r1"].arm.location + Vector((0, 0, 1.2))


def a_tip(c, t):
    sec = sec_of("ch3_14b", t); recovery_base(c, sec)
    p = drum_on_crane(c, HC + Vector((-2.5, -5.5, 0)), 0.6)
    k = ease(min(1.0, sec / (dur("ch3_14b") * 0.8)))
    c["drum"].rotation_euler = (0, math.radians(110 * k), 0)
    c["focus"] = p + Vector((0, 0, 0.6))


def a_mixer(c, t):
    recovery_base(c, 0)
    drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.05)
    c["focus"] = c["mixer"].location + Vector((0, 0, 1.5))


def a_heap_sky(c, t):
    recovery_base(c, 0); drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.05)


def a_tent(c, t, nod=False):
    sec = sec_of("ch3_16b" if nod else "ch3_16a", t); recovery_base(c, sec)
    drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.05)
    h = c["people"]["tentman"]; tc_ = c["tent"]
    from human import pose_sit
    reset_pose(h); h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); pose_sit(h, lean=14)
    place(h, tc_ + Vector((0, 1.15, 0.0)), 0.0)
    f = forward(h); sd = f.cross(Vector((0, 0, 1)))
    b = tc_ + Vector((-0.1 + 0.05 * math.sin(sec * 0.7), 0.45, 0.8))
    reach(h, "R", b + sd * 0.05, Vector((sd.x, sd.y, -0.7)), f); reach(h, "L", tc_ + Vector((0.35, 0.6, 0.8)), Vector((-sd.x, -sd.y, -0.7)), f)
    look = 18 if not nod else 18 * (1 - ease(min(1.0, sec / 1.0))) + (6 * math.sin(max(0, sec - 1.4) * 5) if 1.4 < sec < 2.2 else 0)
    h.rot("neck01", sd, -look * 0.5); h.rot("head", sd, -look * 0.6)
    c["focus"] = h.bone_head("head")


def a_pair_works(c, t):
    sec = sec_of("ch3_17a", t); recovery_base(c, sec)
    drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.25)
    pair_pole_shovel(c, sec, HC + Vector((-0.6, -2.6, 0.4)))
    c["focus"] = c["people"]["r2"].bone_head("spine03")


def a_lid_lift(c, t):
    sec = sec_of("ch3_18a", t); recovery_base(c, sec)
    k1 = ease(min(1.0, sec / 1.4)); k2 = ease(min(1.0, max(0.0, (sec - 1.6) / (dur("ch3_18a") - 1.6))))
    p = drum_on_crane(c, HC + Vector((-1.0, -5.0, 0)), 0.05 + 2.4 * k2)
    c["lid"].location = p + Vector((0, 0, 0.96 + 0.5 * (1 - k1)))
    h = c["people"]["r2"]; stand(h, HC + Vector((0.4, -5.6, 0)), p)
    c["focus"] = p + Vector((0, 0, 0.9))


def a_gather(c, t):
    sec = sec_of("ch3_18b", t); recovery_base(c, sec)
    c["drum"].location = c["bt"]["body"].location + Vector((-1.2, 0, 0.9)); c["lid"].location = c["drum"].location + Vector((0, 0, 0.96))
    crane_hang(c["crane"], 0.2, math.radians(20), 3.0)
    for k, (nm, off) in enumerate((("r1", (3.0, -5.0)), ("r2", (4.0, -4.3)), ("r3", (4.6, -5.6)), ("r4", (3.4, -6.2)), ("op", (5.4, -4.9)))):
        p = HC + Vector((*off, 0))
        stand(c["people"][nm], p, HC + Vector((4.0, -5.0, 0)) if k else HC + Vector((8.0, 3.0, 0)), crossed=(k == 2), hands_pockets=(k == 3))
    c["focus"] = HC + Vector((4.0, -5.0, 1.2))


# ---- Chapter 4: the second container
def a_shells(c, t):
    grab_idle_swing(c, sec_of("ch4_4a", t) * 0.3)
    c["focus"] = HC + Vector((-2.0, -8.0, 0.6))


def a_circle(c, t):
    sec = sec_of("ch4_4b", t); grab_idle_swing(c, sec * 0.3)
    ctr = HC + Vector((-1.0, -7.8, 0)); a = -2.2 + 0.32 * sec
    p = ctr + Vector((2.3 * math.cos(a), 2.3 * math.sin(a), 0)); q = ctr + Vector((2.3 * math.cos(a + 0.2), 2.3 * math.sin(a + 0.2), 0))
    h = c["people"]["inv"]; h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0)
    ph_ = (sec * 0.8 / 1.1) % 1.0
    pose_walk(h, ph_, stride=18, arm_swing=0); arms_relaxed(h, ph_, 0)
    place(h, p, face_angle(p, q) + 0.5)
    arms_crossed(h)
    stand(c["people"]["inv2"], ctr + Vector((-2.8, -2.0, 0)), ctr, hands_pockets=True)
    c["focus"] = h.bone_head("head")


SHOTS = {
    # name: (variant, anim, cam, dof)
    "ch1_15a": ("quiet", anim_wide, cam_wide, None),
    "ch1_15b": ("quiet", anim_heap, cam_heap, 4.0),
    "ch2_7a": ("arrival", anim_van, cam_van, 4.0),
    "ch2_7b": ("arrival", a_gate_detector, C((5.0, -27.5, 1.3), (4.6, -26.8, 1.3), (-0.5, -25.0, 1.0), 40, rel=False), 2.8),
    "ch2_8a": ("arrival", a_evacuate, C((1.5, -44.0, 1.4), (1.2, -43.0, 1.5), (-0.5, -26.0, 1.4), 32, rel=False), 4.0),
    "ch2_8b": ("arrival", anim_cordon, cam_cordon, 4.0),
    "ch3_1a": ("search", a_fanout, C((-3.0, -24.0, 2.0), (-2.0, -22.0, 9.0), (0.0, -2.0, 1.0), 26), None),
    "ch3_1b": ("search", anim_sweep, cam_sweep, 2.8),
    "ch3_2a": ("search", a_point, C((-4.8, -9.2, 1.6), (-4.4, -8.8, 1.6), (-2.0, -3.4, 1.0), 35), 4.0),
    "ch3_2b": ("search", a_cyl_push, C((-3.4, -6.6, 1.0), (-2.9, -5.1, 0.85), (-2.4, -2.9, 0.55), 45), 2.8),
    "ch3_3a": ("search", a_bricks, C((0.2, -10.8, 1.7), (-0.2, -10.4, 1.7), (-3.5, -7.0, 0.7), 32), 4.0),
    "ch3_3b": ("search", a_practice, C((4.5, -14.0, 1.4), (3.8, -13.4, 1.6), (-2.5, -3.5, 2.6), 28), None),
    "ch3_4a": ("search", a_carry, cam_grab, None),
    "ch3_4b": ("search", a_lower, C((-0.2, -10.5, 2.2), (-0.6, -10.0, 2.1), (-3.5, -6.8, 1.0), 35), 5.6),
    "ch3_5a": ("search", a_needle_high, C((0.2, -10.2, 1.5), (0.0, -9.8, 1.45), (-1.3, -7.8, 1.1), 40), 2.8),
    "ch3_5b": ("search", a_bore, C((-2.4, -8.2, 1.9), (-3.0, -7.4, 1.6), (-3.5, -6.8, 0.75), 45), 2.0),
    "ch3_6a": ("search", a_follow, C((-10.0, 10.0, 1.5), (-8.0, 9.0, 1.5), (-6.0, 2.0, 1.1), 32), 4.0),
    "ch3_6b": ("search", a_raise_hand, C((-3.0, -4.2, 1.4), (-3.1, -3.7, 1.4), (-3.5, 0.5, 1.4), 38), 4.0),
    "ch3_7a": ("search", a_tear, C((5.5, -9.0, 1.3), (5.0, -8.6, 1.5), (-1.5, 0.5, 2.5), 28), None),
    "ch3_7b": ("search", a_needle_climb, C((0.4, -8.4, 1.5), (0.1, -8.0, 1.45), (-1.4, -4.0, 1.4), 35), 2.8),
    "ch3_8a": ("search", a_heap_wide, C((8.0, -9.5, 0.9), (7.2, -10.0, 1.0), (-1.0, 0.0, 2.0), 24), None),
    "ch3_8b": ("search", a_step_back, C((1.6, -10.5, 1.5), (1.3, -10.0, 1.5), (0.0, -5.0, 1.3), 32), 4.0),
    "ch3_9a": ("dusk", a_grab_stop, C((-1.0, -14.0, 1.3), (-1.6, -13.5, 1.4), (-6.5, -3.0, 2.8), 30), None),
    "ch3_9b": ("dusk", a_walk_out, C((2.5, -26.0, 1.5), (2.2, -25.0, 1.5), (-0.5, -12.0, 1.3), 30), 5.6),
    "ch3_10a": ("recovery", anim_boom, cam_boom, None),
    "ch3_10b": ("recovery", a_boom_head, C((4.0, -6.5, 1.8), (3.4, -6.0, 2.0), (-0.5, 2.5, 1.8), 35), 4.0),
    "ch3_11a": ("recovery", a_operator, C((7.5, -12.8, 1.6), (7.1, -12.5, 1.6), (5.0, -10.4, 1.3), 35), 2.8),
    "ch3_11b": ("recovery", a_drum_lower, C((3.0, -11.0, 1.2), (2.6, -10.5, 1.4), (-1.0, -5.0, 1.6), 30), 5.6),
    "ch3_12a": ("recovery", a_pair_out, C((7.5, -6.0, 1.4), (7.0, -6.4, 1.4), (3.2, -7.5, 1.2), 30), 4.0),
    "ch3_12b": ("recovery", a_pole, C((-5.6, -6.8, 1.7), (-5.2, -6.4, 1.7), (-1.8, -3.6, 0.8), 30), 4.0),
    "ch3_13a": ("recovery", a_shovel, C((3.6, -5.6, 1.3), (3.2, -5.3, 1.35), (-0.2, -3.6, 0.8), 32), 4.0),
    "ch3_13b": ("recovery", a_hoist, C((2.5, -11.0, 0.9), (2.2, -10.4, 1.1), (-1.0, -5.0, 2.2), 28), 5.6),
    "ch3_14a": ("recovery", a_swap, C((8.0, -2.0, 1.6), (7.4, -2.4, 1.6), (3.0, -7.5, 1.2), 30), 5.6),
    "ch3_14b": ("recovery", a_tip, C((0.5, -10.5, 1.0), (0.1, -10.0, 1.05), (-2.5, -5.5, 1.3), 28), 4.0),
    "ch3_15a": ("recovery", a_mixer, C((-5.0, -41.5, 1.4), (-5.6, -41.0, 1.45), (-14.0, -36.5, 1.8), 32, rel=False), 4.0),
    "ch3_15b": ("recovery", a_heap_sky, C((2.0, -6.5, 0.4), (1.4, -5.6, 0.45), (-0.5, 1.0, 2.2), 24), None),
    "ch3_16a": ("recovery", a_tent, C((15.6, -18.6, 1.4), (15.3, -18.3, 1.4), (14.0, -15.0, 1.0), 35), 2.8),
    "ch3_16b": ("recovery", lambda c, t: a_tent(c, t, nod=True), C((12.6, -18.0, 1.3), (12.8, -17.7, 1.3), (14.0, -15.0, 1.1), 40), 2.8),
    "ch3_17a": ("recovery", a_pair_works, C((2.8, -9.8, 1.8), (2.3, -9.3, 1.8), (-0.8, -3.8, 1.0), 28), 5.6),
    "ch3_17b": ("recovery", anim_drop, cam_drop, 2.8),
    "ch3_18a": ("recovery", a_lid_lift, C((2.8, -8.8, 1.3), (2.4, -8.4, 1.5), (-1.0, -5.0, 1.6), 30), 4.0),
    "ch3_18b": ("recovery", a_gather, C((-6.0, -22.0, 5.0), (-5.0, -20.0, 6.0), (3.0, -3.0, 1.0), 26), None),
    "ch4_4a": ("investigation", a_shells, C((3.0, -13.0, 1.4), (2.0, -12.4, 1.35), (-1.6, -7.8, 0.6), 32), 4.0),
    "ch4_4b": ("investigation", a_circle, C((4.6, -10.5, 1.5), (4.3, -10.0, 1.5), (-1.0, -7.8, 1.0), 30), 4.0),
}
VARIANT_FOR = {k: v[0] for k, v in SHOTS.items()}
DUR = {k: dur(k) for k in SHOTS}
from durs import title_for
MOVES = {k: {**dict(kind="anim", far=500.0, anim=v[1], cam=v[2], dof=v[3], focus=_focus), **({'title': title_for(k), 'dof': None} if title_for(k) else {})} for k, v in SHOTS.items()}
