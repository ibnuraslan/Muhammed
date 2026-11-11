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
from human import reset_pose, pose_walk, reach, fingers_curl

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
    paint = painted_steel(name + "Paint", col, 0.35, 0.25)
    glass_m = pbr(name + "Glass", (0.03, 0.035, 0.04), 0.08, 0.0, **{'Coat Weight': 1.0})
    black = pbr(name + "Black", (0.02, 0.02, 0.02), 0.6)
    parts = [box("Body", (0, 0, 1.25), (4.8, 1.9, 1.8), paint, bevel=0.12),
             box("Nose", (2.65, 0, 0.85), (0.6, 1.88, 0.9), paint, bevel=0.15),
             box("Screen", (2.36, 0, 1.75), (0.02, 1.7, 0.6), glass_m, rot=(0, math.radians(-25), 0)),
             box("WinL", (1.6, 0.955, 1.65), (1.0, 0.02, 0.55), glass_m), box("WinR", (1.6, -0.955, 1.65), (1.0, 0.02, 0.55), glass_m),
             box("Bumper", (2.97, 0, 0.45), (0.1, 1.92, 0.2), black), box("SlideDoor", (0.2, -0.957, 1.2), (1.3, 0.01, 1.5), paint)]
    body = join(parts, name)
    tyre = pbr(name + "Tyre", (0.025, 0.025, 0.025), 0.85)
    wheels = []
    for wx in (-1.5, 1.9):
        for sy in (-1, 1):
            w = cyl("VanWheel", (0, 0, 0), 0.33, 0.22, tyre, verts=24, rot=(math.radians(90), 0, 0)); w.parent = body; w.location = (wx, sy * 0.85, 0.33)
            wheels.append(w)
    return body, wheels


def police_car(name="Police"):
    from sc_street import car
    from sc_police import flash_material
    pc = car(name, (0.78, 0.78, 0.8))
    stripe = box("PStripe", (0, 0, 0.62), (4.3, 1.87, 0.12), pbr("PoliceBlue", (0.02, 0.06, 0.25), 0.3, 0.2)); stripe.parent = pc
    for k, (col, ph_) in enumerate((((0.15, 0.3, 1.0), 0), ((0.15, 0.3, 1.0), 6))):
        lb = box("LightBar", (0.0, -0.35 + 0.7 * k, 1.42), (0.25, 0.6, 0.1), flash_material(f"PFlash{k}", col, ph_)); lb.parent = pc
        l = bpy.data.lights.new(f"PFlashL{k}", 'POINT'); l.color = col; l.shadow_soft_size = 0.05
        dl = l.driver_add("energy").driver; dl.type = 'SCRIPTED'; dl.expression = f"250 * (1 if ((frame + {ph_}) % 12) < 6 else 0.02)"
        lo = bpy.data.objects.new(f"PFlashL{k}", l); bpy.context.collection.objects.link(lo); lo.parent = pc; lo.location = (0.0, -0.35 + 0.7 * k, 1.7)
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
    hook = box(name + "Hook", (0, 0, 0), (0.25, 0.2, 0.4), paint, bevel=0.03)
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
    overcast(strength=0.12, sun_energy=0.7, sun_elev=16, sun_az=210)
    ground = ph_mat("muddy_tracks", 0.12, (0.25, 0.21, 0.17), name="YardMud")
    box("Ground", (0, 0, -0.05), (400, 400, 0.1), ground)
    box("Road", (0, -40, -0.03), (400, 9, 0.07), ph_mat("road_damaged", 0.15, (0.18, 0.18, 0.18), name="Road"))
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
    # scrap mountains: rusty mound + thousands of scattered pieces
    mats = [rust_mat("RustA", (0.24, 0.1, 0.04)), rust_mat("RustB", (0.18, 0.09, 0.05), 6.0),
            painted_steel("FadedBlue", (0.07, 0.1, 0.13), 0.6, 0.8), painted_steel("FadedGreen", (0.08, 0.1, 0.07), 0.6, 0.8),
            painted_steel("Galv", (0.2, 0.2, 0.19), 0.5, 0.7), rust_mat("RustC", (0.3, 0.14, 0.06), 3.0)]
    for m in mats[:2] + mats[5:]:
        pass
    protos = scrap_protos(mats)
    heap_m = rust_mat("HeapBase", (0.16, 0.08, 0.04), 2.5)
    c["heaps"] = []
    for k, ((cx, cy), R, H) in enumerate(HEAPS):
        hf = mound(f"Heap{k}", cx, cy, R, H, heap_m, 10 + k)
        scatter(protos, hf, cx, cy, R, int(R * R * 1.6), rng)
        c["heaps"].append(hf)
    # the capsule heap: smaller, a little apart, where the action happens
    hfc = mound("CapsuleHeap", HC.x, HC.y, 4.2, 1.7, heap_m, 99)
    c["heap_pieces"] = scatter(protos, hfc, HC.x, HC.y, 4.2, 110, rng, embed=0.15, scl=(0.5, 1.0), small=True)
    c["hfc"] = hfc
    # loose pieces on the open ground (wheel ruts, offcuts)
    for k in range(160):
        x, y = rng.uniform(-44, 44), rng.uniform(-28, 44)
        if math.hypot(x - HC.x, y - HC.y) < 5 or abs(x) < 6 and y < -18:
            continue
        p = protos[rng.integers(len(protos))]
        if p.name.startswith("CarShell"):
            continue
        instance(p, (x, y, 0.03), rot=(0, 0, rng.uniform(0, 6.28)), scale=(0.8,) * 3)
    # background: industrial sheds, chimneys, a hillside of houses, pylons
    shed = ph_mat("rusty_corrugated_iron", 0.25, (0.3, 0.3, 0.3), name="ShedIron", tint=(0.35, 0.36, 0.38))
    for k, (x, y, w, d, h) in enumerate(((-80, 90, 40, 20, 8), (-15, 110, 50, 25, 10), (65, 95, 35, 20, 7), (110, 30, 25, 40, 7), (-110, 20, 25, 40, 7))):
        box("Shed", (x, y, h / 2), (w, d, h), shed)
        box("ShedRoof", (x, y, h + 0.6), (w + 1, d + 1, 1.2), shed, rot=(math.radians(4), 0, 0))
    chim = pbr("Chimney", (0.35, 0.33, 0.31), 0.85)
    for x, y, hgt in ((-30, 110, 40), (40, 120, 32)):
        cyl("Stack", (x, y, hgt / 2), 1.4, hgt, chim, verts=16)
    far = noisy("FarCity", (0.2, 0.19, 0.18), 0.9, dirt=0.7, scale=0.05)
    for k in range(120):
        x = rng.uniform(-260, 260); y = rng.uniform(140, 260); z = (y - 140) * 0.2
        box("Far", (x, y, z + 3), (rng.uniform(8, 16), 10, rng.uniform(4, 12)), far)
    box("Hill", (0, 220, 0), (700, 160, 30), noisy("Hill", (0.14, 0.13, 0.12), 0.95, dirt=0.7, scale=0.02), rot=(math.radians(-12), 0, 0))
    haze((0, 120, 30), (700, 220, 80), density=0.0013, color=(0.85, 0.88, 0.92), anis=0.2)
    # the grab crane (material handler) beside the capsule heap
    gc = excavator("Grab", (0.72, 0.48, 0.07), tool="grab")
    gc["base"].location = HC + Vector((-6.5, -3.0, 0)); gc["base"].rotation_euler = (0, 0, 0)
    pose_arm(gc, 0, math.radians(35), math.radians(70), 0); hang_tool_level(gc); set_grab(gc, 0.6)
    c["grab"] = gc
    # the cylinder (part of a container) on the heap; the lead-brick box near the crane
    grey = painted_steel("CylGrey", (0.32, 0.33, 0.33), 0.55, 0.5)
    c["cyl"] = join([cyl("CylBody", (0, 0, 0), 0.22, 0.75, grey, verts=28), cyl("CylBore", (0, 0, 0.376), 0.08, 0.004, pbr("Bore", (0.01, 0.01, 0.01), 0.9), verts=20)], "Cylinder")
    c["cyl_rest"] = HC + Vector((-1.2, -1.0, hfc(HC.x - 1.2, HC.y - 1.0) + 0.1))
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
    # specialists / police / responders
    P = {}
    P["spec1"] = person("Spec1", 1.0, 42, "suit", "short03", cval=0.6, hue=0.5, sat=0.3)
    P["spec2"] = person("Spec2", 1.0, 36, "coat", "short02", cval=0.4, hue=0.5, sat=0.4, cap=True)
    P["cop"] = person("Cop", 1.0, 30, "suit", "short04", cval=0.35, hue=0.62, sat=1.2)
    P["r1"] = person("Resp1", 1.0, 34, "work", "short02", cval=1.2, hue=0.5, sat=0.0)
    P["r2"] = person("Resp2", 1.0, 40, "work", "short04", cval=1.2, hue=0.5, sat=0.0, cap=True)
    P["op"] = person("Operator", 1.0, 45, "coat", "short03", cval=0.5, hue=0.48, sat=0.5)
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
    if v in ("search", "recovery"):
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
    grab_idle_swing(c, t * DUR["wide"])


def cam_wide(c, t):
    e = ease(t)
    return (Vector((-31, -43, 12.5)).lerp(Vector((-28, -41, 14.0)), e), Vector((2, 14, 3.0)), 30)


def _heap_pt(i, r, z, surface=False, ang=-1.1):
    (cx, cy), R, H = HEAPS[i]
    p = Vector((cx + r * math.cos(ang), cy + r * math.sin(ang), z))
    if surface:
        p.z = z + H * max(0.0, 1 - r / R) ** 1.15 * (1 - 0.15 * r / R)
    return p


def anim_heap(c, t):
    grab_idle_swing(c, t * DUR["heap_push"])


def cam_heap(c, t):
    e = ease(t)
    return (_heap_pt(0, 22.0, 2.2).lerp(_heap_pt(0, 16.5, 2.4), e), _heap_pt(0, 8.0, 0.4, surface=True), 35)


def anim_van(c, t):
    sec = t * DUR["gate_van"]
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
    sec = t * DUR["cordon"]
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
    sec = t * DUR["sweep"]
    grab_idle_swing(c, sec * 0.3)
    h = c["people"]["spec2"]
    a = HC + Vector((3.5, -4.8, 0)); b = HC + Vector((1.8, -3.0, 0))
    p = walk(h, a, b, sec, speed=0.45, stride=0.9)
    h.rot("spine03", forward(h).cross(Vector((0, 0, 1))), -12)
    level = 0.25 + 0.6 * ease(min(1.0, sec / DUR["sweep"]))
    hold_detector(c, h, sec, sweep=sec * 1.6, level=level)
    stand(c["people"]["spec1"], HC + Vector((5.5, -7.0, 0)), HC)
    c["focus"] = c["det"]["body"].location


def cam_sweep(c, t):
    e = ease(t)
    return (HC + Vector((-0.6, -7.2, 1.35)).lerp(Vector((-0.2, -6.8, 1.35)), e), HC + Vector((2.4, -3.7, 1.0)), 38)


def anim_grab(c, t):
    sec = t * DUR["grab_lift"]
    gc = c["grab"]
    k = ease(min(1.0, sec / DUR["grab_lift"]))
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
    sec = t * DUR["boom_truck"]
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
    sec = t * DUR["capsule_drop"]
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
    handle = blade - fwd * 0.9 + Vector((0, 0, 0.45 + 0.2 * tip_k))
    h2.rot("spine03", side, -14)
    reach(h2, "R", handle, Vector((side.x, side.y, -0.7)), blade - handle)
    reach(h2, "L", handle.lerp(blade, 0.45), Vector((-side.x, -side.y, -0.7)), blade - handle)
    fingers_curl(h2, 70, thumb=40)
    sp = c["spade"]
    if sp is not None:
        sp.location = blade + (handle - blade).normalized() * 0.5; sp.rotation_mode = 'QUATERNION'
        sp.rotation_quaternion = (handle - blade).to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), tip_k * 1.2)
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
    h1 = c["people"]["r1"]; st1 = HC + Vector((2.6, -7.2, 0))
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
    return (m + Vector((-1.9, 0.6, 0.3)).lerp(Vector((-1.65, 0.5, 0.27)), e), m + Vector((0.25, -0.35, 0.1)), 38)


def _focus(c, t):
    return c.get("focus", HC + Vector((0, 0, 1)))


MOVES = {
    "wide": dict(kind="anim", far=500.0, anim=anim_wide, cam=cam_wide),
    "heap_push": dict(kind="anim", dof=4.0, far=200.0, anim=anim_heap, cam=cam_heap, focus=lambda c, t: _heap_pt(0, 8.0, 0.4, surface=True)),
    "gate_van": dict(kind="anim", dof=4.0, far=200.0, anim=anim_van, cam=cam_van, focus=_focus),
    "cordon": dict(kind="anim", dof=4.0, far=200.0, anim=anim_cordon, cam=cam_cordon, focus=_focus),
    "sweep": dict(kind="anim", dof=2.8, far=200.0, anim=anim_sweep, cam=cam_sweep, focus=_focus),
    "grab_lift": dict(kind="anim", dof=5.6, far=200.0, anim=anim_grab, cam=cam_grab, focus=_focus),
    "boom_truck": dict(kind="anim", dof=5.6, far=200.0, anim=anim_boom, cam=cam_boom, focus=_focus),
    "capsule_drop": dict(kind="anim", dof=2.0, far=100.0, anim=anim_drop, cam=cam_drop, focus=_focus),
}
