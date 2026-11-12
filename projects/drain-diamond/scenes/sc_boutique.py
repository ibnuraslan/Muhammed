"""THE BOUTIQUE (hero set): a nameless luxury jeweller on a Paris avenue. A limestone Haussmann building, dark awnings,
a doorman; NO name, logo or sign anywhere. Interiors: the lit salon with display cases, the safe room.
Variants: dawn (avenue, October 2007), lane (side street with the service door), salon (ground-floor salon), safe.
  facade   (intro 3A): dawn crane up the facade while the doorman sweeps the step
  painters (intro 3B): four men in white overalls carry paint tins down the side lane toward the service door, wide
  grille   (ch1 1A, title): dawn track along the avenue as a staff member raises the front grille
  floor    (ch1 2A): wide from the doorway, staff sitting on the salon floor, a painter standing over them
  safe     (ch1 2B): the manager at the alarm panel, its LED turning green, the vault door swinging open
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import dd
from dd import person, place, face_to, walk_to, arms_relaxed, pose_floor_sit, zero, ground
from human import reach, fingers_curl, pose_walk
from sc_street import car

EXPOSURE = 0.0
BOUNCES = 8
LEAD = 2.5
DUR = {"facade": 9.0, "painters": 9.0, "grille": 9.0, "floor": 9.0, "safe": 9.0, "corridor": 9.0, "chair": 9.0,
       "night_door": 9.0, "night_wait": 9.0}
VARIANT_FOR = {"facade": "dawn", "painters": "lane", "grille": "dawn", "floor": "salon", "safe": "safe",
               "corridor": "corridor", "chair": "corridor_empty", "night_door": "lane_night", "night_wait": "salon_night"}
WARM = (1.0, 0.74, 0.46)                # ~2700 K practicals


# ============================================================================ materials
_M = {}


def mats():
    if not _M:
        _M["stone"] = ashlar("Limestone", course=0.52, block=1.15)
        _M["stone_gf"] = ashlar("LimestoneGF", course=0.42, block=1.0, mortar=0.022, groove=True)
        _M["stone_plain"] = ashlar("LimestoneP", course=10.0, block=10.0, mortar=0.0)
        _M["slate"] = dd.tex_mat("roof_slates_02", 0.5, tint=(0.55, 0.6, 0.66), name="Slate", sat=0.5)
        _M["glass"] = pbr("WinGlass", (0.02, 0.025, 0.03), 0.03, 0.2, **{'Coat Weight': 1.0})
        _M["shopglass"] = glass("ShopGlass", (0.95, 0.97, 0.97), 0.0)
        _M["frame"] = pbr("WinFrame", (0.78, 0.76, 0.72), 0.5)
        _M["iron"] = pbr("Iron", (0.025, 0.027, 0.03), 0.45, 0.7)
        _M["bronze"] = pbr("Bronze", (0.5, 0.36, 0.16), 0.28, 1.0)
        _M["lacquer"] = pbr("BlackLacquer", (0.012, 0.012, 0.014), 0.12, 0.0, **{'Coat Weight': 1.0, 'Coat Roughness': 0.03})
        _M["awning"] = fabric("Awning", (0.018, 0.02, 0.026), 0.85, 0.4, 600)
        _M["lit"] = emissive("ShopGlow", WARM, 2.5)
        _M["curtain_lit"] = emissive("RoomGlow", (1.0, 0.76, 0.48), 4.0)
    return _M


def ashlar(name, course=0.5, block=1.1, mortar=0.006, groove=False):
    """Paris limestone ashlar: a pale stone texture laid in courses with fine joints (Brick Texture on the facade's
    x/z), each block a slightly different cream; the ground floor gets deeper rusticated grooves."""
    m = dd.tex_mat("beige_wall_001", 0.6, tint=(1.0, 0.97, 0.9), name=name, sat=0.6)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    src = p.inputs['Base Color'].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    # horizontal coordinate: x on y-facing faces, y on x-facing faces
    geo = N.new("ShaderNodeNewGeometry"); nrm = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], nrm.inputs[0])
    ax = N.new("ShaderNodeMath"); ax.operation = 'ABSOLUTE'; L.new(nrm.outputs['X'], ax.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5; L.new(ax.outputs[0], gt.inputs[0])
    hm = N.new("ShaderNodeMix"); hm.data_type = 'FLOAT'; L.new(gt.outputs[0], hm.inputs['Factor']); L.new(sep.outputs['X'], hm.inputs[2]); L.new(sep.outputs['Y'], hm.inputs[3])
    uv = N.new("ShaderNodeCombineXYZ"); L.new(hm.outputs[0], uv.inputs['X']); L.new(sep.outputs['Z'], uv.inputs['Y'])
    br = N.new("ShaderNodeTexBrick"); br.offset = 0.5; br.squash = 1.0
    br.inputs['Scale'].default_value = 1.0; br.inputs['Brick Width'].default_value = block; br.inputs['Row Height'].default_value = course
    br.inputs['Mortar Size'].default_value = mortar; br.inputs['Mortar Smooth'].default_value = 0.3; br.inputs['Bias'].default_value = 0.0
    br.inputs['Color1'].default_value = (1.0, 0.985, 0.95, 1); br.inputs['Color2'].default_value = (0.93, 0.9, 0.84, 1)
    br.inputs['Mortar'].default_value = (0.62, 0.58, 0.52, 1)
    L.new(uv.outputs[0], br.inputs['Vector'])
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    L.new(src, mul.inputs[6]); L.new(br.outputs['Color'], mul.inputs[7]); L.new(mul.outputs[2], p.inputs['Base Color'])
    if mortar > 0:
        inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(br.outputs['Fac'], inv.inputs[1])
        bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.9 if groove else 0.35
        bp.inputs['Distance'].default_value = 0.02 if groove else 0.004
        L.new(inv.outputs[0], bp.inputs['Height'])
        if p.inputs['Normal'].is_linked:
            L.new(p.inputs['Normal'].links[0].from_socket, bp.inputs['Normal'])
        L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


# ============================================================================ the Haussmann block
def haussmann(x0, x1, seed=0, boutique=False, depth=14.0, gf=5.0, floors=5, fh=3.25, lit_frac=0.12, rot_z=0.0, origin=(0, 0, 0), shops=True):
    """A limestone apartment block with its front face on y=0 (street at -y). Returns the joined object + info."""
    M = mats(); rng = np.random.default_rng(seed)
    w = x1 - x0; cx = (x0 + x1) / 2
    H = gf + floors * fh
    B = dd.Builder("Block%d" % seed)
    B.box((cx, depth / 2, (gf + H) / 2), (w, depth, H - gf), M["stone"])
    B.box((cx, depth / 2 + 0.6, gf / 2), (w, depth - 1.2, gf), pbr("ShopInterior", (0.05, 0.045, 0.04), 0.7))
    nb = max(3, int(round(w / 2.7)))
    bay = w / nb
    lit = []
    for f in range(floors):
        z0 = gf + f * fh
        B.box((cx, -0.06, z0 + 0.05), (w, 0.14, 0.22), M["stone_plain"])
        for b in range(nb):
            x = x0 + bay * (b + 0.5)
            wh = 2.2 if f < 3 else 1.9
            zc = z0 + 0.45 + wh / 2
            B.box((x, 0.04, zc), (1.25, 0.06, wh), M["glass"])
            B.box((x, -0.03, zc + wh / 2 + 0.12), (1.6, 0.1, 0.24), M["stone_plain"])
            for sx in (-1, 1):
                B.box((x + sx * 0.7, -0.02, zc), (0.16, 0.08, wh + 0.1), M["stone_plain"])
            B.box((x, 0.0, zc), (0.05, 0.04, wh), M["frame"])
            B.box((x, 0.0, zc + wh * 0.25), (1.25, 0.04, 0.04), M["frame"])
            if rng.random() < lit_frac:
                B.box((x, 0.12, zc), (1.2, 0.02, wh * 0.95), M["curtain_lit"])
            if f not in (1, 4):           # individual balconettes (continuous balconies on the 2nd and 5th floors)
                B.box((x, -0.18, z0 + 0.95), (1.3, 0.02, 0.05), M["iron"])
                for k in range(9):
                    B.box((x - 0.6 + k * 0.15, -0.18, z0 + 0.7), (0.012, 0.012, 0.5), M["iron"])
        if f in (1, 4):                   # continuous balcony
            B.box((cx, -0.45, z0 + 0.05), (w - 0.2, 0.9, 0.16), M["stone_plain"])
            B.box((cx, -0.86, z0 + 1.08), (w - 0.2, 0.03, 0.05), M["iron"])
            n = int((w - 0.3) / 0.13)
            for k in range(n):
                B.box((x0 + 0.2 + k * 0.13, -0.86, z0 + 0.6), (0.014, 0.014, 0.95), M["iron"])
            for k in range(nb * 3):
                B.box((x0 + bay * (k / 3 + 0.17), -0.4, z0 - 0.15), (0.12, 0.7, 0.28), M["stone_plain"])
    # cornice + mansard roof with dormers
    B.box((cx, -0.25, H + 0.1), (w + 0.1, 0.6, 0.35), M["stone_plain"])
    pitch = math.radians(68); mh = 3.0; run = mh / math.tan(pitch)
    B.box((cx, run / 2 + 0.2, H + 0.25 + mh / 2), (w, mh / math.sin(pitch), 0.12), M["slate"], rot=(pitch - math.pi / 2, 0, 0))
    B.box((cx, depth / 2, H + 0.25 + mh), (w, depth - 2 * run, 0.1), M["slate"])
    for b in range(nb):
        x = x0 + bay * (b + 0.5)
        B.box((x, run / 2 - 0.05, H + 1.5), (1.0, 0.8, 1.6), M["stone_plain"])
        B.box((x, run / 2 - 0.46, H + 1.45), (0.65, 0.02, 1.1), M["glass"])
        B.box((x, run / 2 - 0.05, H + 2.35), (1.15, 0.95, 0.12), M["slate"])
    for k in range(int(w // 6) + 1):
        B.box((x0 + 2 + k * 6, depth / 2 + 1, H + 0.25 + mh + 0.8), (0.8, 2.2, 1.6), M["stone_plain"])
    # ground floor
    info = dict(H=H, gf=gf, x0=x0, x1=x1)
    if boutique:
        opens = shop_front(B, x0, x1, gf, info)
    elif shops:
        gfn = max(2, int(round(w / 4.5))); opens = []
        for b in range(gfn):
            x = x0 + w / gfn * (b + 0.5); ww = w / gfn - 1.0
            B.box((x, 0.06, 1.95), (ww, 0.05, 3.7), M["glass"])
            B.box((x, 0.05, 0.12), (ww, 0.2, 0.24), M["iron"])
            B.box((x, 0.0, 3.85), (ww, 0.12, 0.12), M["iron"])
            opens.append((x, ww))
    else:                                   # a plain rusticated ground floor with a few small barred windows
        opens = []
        for b in range(max(2, int(w / 6.0))):
            x = x0 + 3.0 + b * 6.0
            B.box((x, -0.01, 2.6), (0.9, 0.04, 1.2), M["glass"])
            for k in range(5):
                B.box((x - 0.36 + k * 0.18, -0.06, 2.6), (0.02, 0.02, 1.2), M["iron"])
    # stone piers between the ground-floor openings, the openings themselves recessed 1.2 m
    edges = [x0] + [e for x, ww in sorted(opens) for e in (x - ww / 2, x + ww / 2)] + [x1]
    for a_, b_ in zip(edges[0::2], edges[1::2]):
        if b_ - a_ > 0.01:
            B.box(((a_ + b_) / 2, 0.6, gf / 2), (b_ - a_, 1.2, gf), M["stone_gf"])
    for x, ww in opens:
        B.box((x, 0.6, 4.4), (ww, 1.2, gf - 4.0 if gf > 4.4 else 0.2), M["stone_gf"])
    B.box((cx, -0.08, gf - 0.1), (w + 0.04, 0.2, 0.3), M["stone_plain"])
    o = B.done(origin, rot_z)
    return o, info


def shop_front(B, x0, x1, gf, info):
    """Three tall display windows with bronze frames and dark awnings, a central door. No name, no logo."""
    M = mats(); cx = (x0 + x1) / 2
    xs = [cx - 6.0, cx, cx + 6.0]
    doors = []
    for i, x in enumerate(xs):
        isdoor = (i == 1)
        ww = 2.4 if isdoor else 3.6
        for sx in (-1, 1):
            B.box((x + sx * (ww / 2 + 0.09), -0.02, 2.0), (0.18, 0.16, 4.0), M["lacquer"])
            B.box((x + sx * (ww / 2 + 0.005), -0.1, 2.0), (0.025, 0.02, 4.0), M["bronze"])
        B.box((x, -0.02, 4.02), (ww + 0.36, 0.16, 0.2), M["lacquer"])
        B.box((x, -0.11, 3.94), (ww + 0.1, 0.02, 0.025), M["bronze"])
        B.box((x, -0.02, 0.1), (ww + 0.36, 0.16, 0.2), M["lacquer"])
        if isdoor:
            B.box((x, 0.03, 1.6), (ww - 0.2, 0.04, 3.2), M["shopglass"])
            B.box((x, 0.0, 1.6), (0.08, 0.08, 3.2), M["lacquer"])
            for sx in (-1, 1):
                B.box((x + sx * 0.12, -0.04, 1.2), (0.03, 0.03, 0.9), M["bronze"])       # brass pull handles
            B.box((x, -0.45, 0.06), (ww + 0.8, 0.9, 0.12), M["stone_plain"])
            doors.append(Vector((x, 0, 0)))
        else:
            B.box((x, 0.03, 2.0), (ww - 0.15, 0.04, 3.8), M["shopglass"])
            # the lit display behind the glass: a cream velvet backdrop and three plinths with jewels on stands
            B.box((x, 1.0, 2.0), (ww - 0.2, 0.05, 3.6), fabric("ShowBackM", (0.55, 0.47, 0.38), 0.9, 0.6, 400))
            B.box((x, 0.55, 0.3), (ww - 0.2, 0.9, 0.6), fabric("ShowFloorM", (0.45, 0.38, 0.3), 0.9, 0.6, 400))
            for k in range(3):
                B.box((x - 1.0 + k * 1.0, 0.55, 0.6 + 0.35 + 0.15 * (k % 2)), (0.36, 0.36, 0.7 + 0.3 * (k % 2)), fabric("PlinthM", (0.08, 0.09, 0.16), 0.9, 0.7, 300))
        # awning: a dark slanted fabric canopy over each opening
        B.box((x, -0.75, 4.3), (ww + 0.6, 1.6, 0.04), M["awning"], rot=(math.radians(-24), 0, 0))
        B.box((x, -1.48, 3.98), (ww + 0.6, 0.02, 0.28), M["awning"])
    # a blank bronze plaque by the door (no text) and two carriage lamps
    B.box((cx + 1.6, -0.03, 1.7), (0.4, 0.03, 0.55), M["bronze"])
    info["door"] = doors[0]; info["shows"] = [Vector((x, 0, 0)) for x in (xs[0], xs[2])]
    return [(x, (2.4 if i == 1 else 3.6) + 0.3) for i, x in enumerate(xs)]


def show_lights(info):
    stand = pbr("ShowStand", (0.9, 0.88, 0.84), 0.45)
    for p in info["shows"]:
        for k in range(3):                                   # a jewel on a small stand on each plinth
            top = p + Vector((-1.0 + k * 1.0, 0.55, 0.6 + 0.7 + 0.3 * (k % 2)))
            cyl("ShowStandO", top + Vector((0, 0, 0.06)), 0.035, 0.12, stand, verts=16)
            dd.ring(f"ShowRing{k}", top + Vector((0, 0, 0.14)), stone_r=0.008, band="plat" if k % 2 else "gold",
                    stone=("diamond", "sapphire", "diamond")[k])
        spill = bpy.data.lights.new("ShowSpill", 'AREA'); spill.size = 3.0; spill.energy = 80; spill.color = WARM
        so = bpy.data.objects.new("ShowSpill", spill); bpy.context.collection.objects.link(so)
        so.location = p + Vector((0, -0.4, 2.6)); so.rotation_euler = (math.radians(35), 0, 0); so.visible_camera = False
        for k in range(3):
            l = bpy.data.lights.new("ShowL", 'SPOT'); l.energy = 60; l.color = WARM; l.spot_size = math.radians(50); l.shadow_soft_size = 0.2
            o = bpy.data.objects.new("ShowL", l); bpy.context.collection.objects.link(o)
            o.location = p + Vector((-1.0 + k * 1.0, 0.3, 3.6)); point_at(o, p + Vector((-1.0 + k * 1.0, 0.5, 1.4)))
        a = bpy.data.lights.new("ShowFill", 'AREA'); a.energy = 120; a.size = 3.0; a.color = WARM
        ao = bpy.data.objects.new("ShowFill", a); bpy.context.collection.objects.link(ao); ao.location = p + Vector((0, 0.6, 3.8))
        ao.visible_camera = False


def street(c, y_kerb=-6.0, length=140, opposite=True):
    road = dd.wet(dd.tex_mat("asphalt_02", 0.35, tint=(0.5, 0.5, 0.52), name="Road", sat=0.4), 0.35, 0.25, ripples=False)
    box("Road", (0, y_kerb - 8, -0.06), (length, 16, 0.1), road)
    pave = dd.tex_mat("concrete_floor_02", 0.5, tint=(0.62, 0.61, 0.59), name="Pavement", sat=0.3)
    box("Pavement", (0, y_kerb / 2, 0.0), (length, -y_kerb, 0.12), pave)
    box("Kerb", (0, y_kerb, 0.0), (length, 0.25, 0.13), pbr("Granite", (0.32, 0.32, 0.33), 0.5))
    if opposite:
        for k, (a, b) in enumerate(((-60, -30), (-30, -8), (-8, 14), (14, 40), (40, 66))):
            haussmann(a, b, seed=20 + k, rot_z=math.pi, origin=(0, y_kerb - 16 - 6, 0), lit_frac=0.1)
            # rotated by pi about the origin: x flips, so the row still spans the street
        box("PaveOpp", (0, y_kerb - 19, 0.0), (length, 6, 0.12), pave)
    # lamp posts and a few parked cars along the kerb
    for k in range(-5, 6):
        x = k * 11.0 + 3.0
        dd.model_h("street_lamp_02", (x, y_kerb + 0.6, 0.06), 4.6) if k % 2 == 0 else None
    rng = np.random.default_rng(77)
    for k in range(-4, 5):                       # plane trees along the kerb (none in front of the boutique door)
        x = k * 11.0 + 5.5 + float(rng.uniform(-0.6, 0.6))
        if abs(x) > 10.0:
            dd.model_h("jacaranda_tree", (x, y_kerb + 0.9, 0.06), float(rng.uniform(10.0, 12.0)), rot_z=float(rng.uniform(0, 6)))
        if opposite:
            dd.model_h("jacaranda_tree", (x + 4.0, y_kerb - 16.8, 0.06), float(rng.uniform(10.0, 12.0)), rot_z=float(rng.uniform(0, 6)))
    cars = []
    for k, (x, col) in enumerate(((-14, (0.05, 0.05, 0.06)), (-8.5, (0.4, 0.41, 0.43)), (9, (0.12, 0.14, 0.18)), (15, (0.6, 0.6, 0.6)))):
        cr = dd.sedan(f"Parked{k}", col, lights=False); cr.location = (x, y_kerb - 1.2, 0); cars.append(cr)
    c["cars"] = cars


def doorman(c, loc):
    h = dd.guard("Doorman", 52, "short04")
    broom = dd.model_h("wooden_broom", (0, 0, 0), 1.35) or cyl("Broom", (0, 0, 0.65), 0.012, 1.3, pbr("BroomW", (0.3, 0.2, 0.1), 0.6))
    c["doorman"] = h; c["broom"] = broom; c["doorman_at"] = Vector(loc)


def anim_doorman(c, sec):
    h = c["doorman"]; base = c["doorman_at"]
    zero(h); from human import pose_walk
    pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    h.rot("spine03", (1, 0, 0), 12); h.rot("head", (1, 0, 0), 16)
    face = math.radians(-60)
    h.arm.rotation_euler = (0, 0, face); h.arm.location = base; ground(h, 0.12)
    M = h.arm.matrix_world.to_3x3()
    sw = 0.28 * math.sin(sec * 2.2)
    foot = base + M @ Vector((sw, -0.75, 0)) + Vector((0, 0, 0.12))
    top = base + M @ Vector((0.05 + 0.1 * sw, -0.22, 1.1))
    b = c["broom"]; b.location = foot
    d = (top - foot).normalized(); b.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    reach(h, "L", top, M @ Vector((1, 0, -0.5)))
    reach(h, "R", foot.lerp(top, 0.55), M @ Vector((-1, -0.3, -0.5)))
    fingers_curl(h, 60, thumb=30)


def paint_stains(m, seed=0):
    """Splashes and smears of paint on the white overalls (noise-masked flecks, a few colours)."""
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    src = p.inputs['Base Color'].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord"); cur = src
    for k, (col, sc, th) in enumerate((((0.55, 0.62, 0.7), 9.0, 0.7), ((0.85, 0.8, 0.62), 14.0, 0.72), ((0.35, 0.36, 0.38), 30.0, 0.76))):
        nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs['W'].default_value = seed * 3.1 + k * 7.7
        nz.inputs['Scale'].default_value = sc; nz.inputs['Detail'].default_value = 8; nz.inputs['Roughness'].default_value = 0.7
        L.new(tc.outputs['Object'], nz.inputs['Vector'])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = th; mr.inputs['From Max'].default_value = th + 0.03
        L.new(nz.outputs['Fac'], mr.inputs['Value'])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[7].default_value = (*col, 1)
        L.new(mr.outputs[0], mx.inputs['Factor']); L.new(cur, mx.inputs[6]); cur = mx.outputs[2]
    L.new(cur, p.inputs['Base Color'])


def painter(name, years, seed):
    h = person(name, 1.0, years, "male_worksuit01", ("short02", "short01", "short03", "short04")[seed % 4], cval=1.75, sat=0.0,
               hv=0.2 + 0.15 * (seed % 2), height=0.45 + 0.05 * (seed % 3), weight=0.5)
    m = bpy.data.materials.get(f"{name}_male_worksuit01")
    if m:
        paint_stains(m, seed)
    return h


def paint_tin(name):
    tin = pbr("TinWhite", (0.85, 0.85, 0.83), 0.35, 0.3)
    parts = [cyl(name, (0, 0, 0.13), 0.13, 0.26, tin, verts=24),
             cyl(name + "Rim", (0, 0, 0.265), 0.132, 0.012, pbr("TinRim", (0.6, 0.6, 0.62), 0.3, 1.0), verts=24)]
    return join(parts, name)


# ============================================================================ variants
def build_dawn(c):
    w = world_sky(sun_elev_deg=6, sun_rot_deg=300, strength=1.6, tint=(0.95, 0.94, 0.95))
    [n for n in w.node_tree.nodes if n.type == 'TEX_SKY'][0].sun_disc = False
    # warm dawn sun grazing along the facade from the east (low, raking across the limestone)
    sn = sun(12, 0, energy=6.0, color=(1.0, 0.64, 0.38), angle_deg=1.5)
    sn.rotation_euler = (math.radians(78), 0, math.radians(-78))   # travels +X and slightly into the facade (+Y)
    blk, info = haussmann(-11, 11, seed=1, boutique=True, lit_frac=0.18)
    haussmann(-34, -11, seed=2, lit_frac=0.28); haussmann(11, 33, seed=3, lit_frac=0.25)
    haussmann(33, 55, seed=4, lit_frac=0.25); haussmann(-56, -34, seed=5, lit_frac=0.25)
    show_lights(info); c["info"] = info
    street(c)
    doorman(c, info["door"] + Vector((1.1, -0.9, 0)))
    # the front grille over the door: an iron lattice that rolls up
    gr = [box("GrilleBar", (0, 0, 1.6), (2.5, 0.03, 0.03), mats()["iron"])]
    for k in range(18):
        gr.append(box("GrilleV", (-1.2 + k * 0.14, 0, 1.6), (0.015, 0.02, 3.2), mats()["iron"]))
    for k in range(12):
        gr.append(box("GrilleH", (0, 0, 0.1 + k * 0.28), (2.5, 0.02, 0.02), mats()["iron"]))
    c["grille"] = join(gr, "Grille"); c["grille"].location = info["door"] + Vector((0, -0.1, 0))
    st = dd.staff("Staff", 0.0, 34, "bob01", seed=0)
    c["staff"] = st
    haze = dd.frame_value  # (unused placeholder to keep imports explicit)


def build_lane(c, night=False):
    if night:
        world_flat((0.012, 0.016, 0.028), 1.0)
        for y in (-14.0,):                      # one far street lamp at the mouth of the lane, the rest dark
            sl = bpy.data.lights.new("StreetL", 'SPOT'); sl.energy = 400; sl.spot_size = math.radians(120); sl.color = (1.0, 0.7, 0.42)
            so = bpy.data.objects.new("StreetL", sl); bpy.context.collection.objects.link(so); so.location = (-3.5, y, 6.0)
    else:
        w = world_sky(sun_elev_deg=6, sun_rot_deg=300, strength=2.2, tint=(0.9, 0.93, 1.0))
        [n for n in w.node_tree.nodes if n.type == 'TEX_SKY'][0].sun_disc = False
    # a narrow rue running along +Y: the boutique block's side on the right (x>0), another block on the left
    haussmann(-30, 30, seed=7, rot_z=math.radians(-90), origin=(4.0, 0, 0), lit_frac=0.06, gf=5.0, shops=False)
    haussmann(-30, 30, seed=8, rot_z=math.radians(90), origin=(-4.0, 0, 0), lit_frac=0.06, gf=5.0, shops=False)
    road = dd.wet(dd.tex_mat("cobblestone_floor_04", 0.6, tint=(0.55, 0.55, 0.56), name="Cobbles", sat=0.4), 0.4, 0.4, ripples=False)
    box("Lane", (0, 0, -0.05), (8, 70, 0.1), road)
    haussmann(-12, 12, seed=9, rot_z=0.0, origin=(0, 30.0, 0), lit_frac=0.1)      # closes the end of the lane
    for sx in (-1, 1):                         # granite kerbs; wall lamps along both walls
        box("LaneKerb", (sx * 3.6, 0, 0.04), (0.3, 70, 0.1), pbr("LaneKerbM", (0.3, 0.3, 0.31), 0.55))
        for y in (-8.0, 2.0, 12.0, 22.0):
            dd.model_h("industrial_wall_lamp", (sx * 3.92, y + (0 if sx > 0 else 4.0), 3.0), 0.32, rot_z=(-math.pi / 2 if sx > 0 else math.pi / 2))
            wl = bpy.data.lights.new("WallLamp", 'POINT'); wl.energy = 40 if not night else 0; wl.color = WARM; wl.shadow_soft_size = 0.08
            wo = bpy.data.objects.new("WallLamp", wl); bpy.context.collection.objects.link(wo); wo.location = (sx * 3.6, y + (0 if sx > 0 else 4.0), 2.95)
    for k in range(4):                         # a few drainpipes, a bin, a crate on the cobbles
        cyl("LanePipe", (3.9, -12 + k * 9.3, 4.0), 0.05, 8.0, pbr("PipeL", (0.35, 0.37, 0.38), 0.4, 0.8), verts=12)
    dd.model_h("metal_trash_can", (-3.3, 5.5, 0.0), 0.75)
    dd.model_h("plastic_crate_01", (-3.2, 6.4, 0.0), 0.3, rot_z=0.4)
    # the service door on the right wall: plain dark steel, a small caged lamp above
    D = dd.Builder("ServiceDoor"); D.box((-0.0, 0.55, 1.15), (0.06, 1.1, 2.3), pbr("SteelDoor", (0.08, 0.085, 0.09), 0.45, 0.6))
    c["sdoor"] = D.done((3.94, 8.45, 0.0))
    if night:     # behind the door: a lit back corridor
        box("DoorInside", (4.6, 9.0, 1.15), (0.02, 1.08, 2.28), emissive("Inside", (1.0, 0.85, 0.65), 0.35))
        for sy in (-1, 1):                      # the passage behind the door
            box("Passage", (4.3, 9.0 + sy * 0.56, 1.15), (0.6, 0.04, 2.3), pbr("PassageWall", (0.3, 0.29, 0.27), 0.8))
    box("ServiceFrame", (3.98, 9.0, 1.2), (0.05, 1.3, 2.45), pbr("DoorFrameM", (0.3, 0.3, 0.3), 0.5, 0.5))
    lamp = bpy.data.lights.new("DoorLamp", 'POINT'); lamp.energy = 160 if night else 25; lamp.color = WARM; lamp.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("DoorLamp", lamp); bpy.context.collection.objects.link(lo); lo.location = (3.7, 9.0, 2.8)
    box("DoorLampBox", (3.85, 9.0, 2.8), (0.15, 0.15, 0.2), emissive("DoorLampGlow", WARM, 6))
    c["door_at"] = Vector((3.4, 9.0, 0))
    c["painters"] = []
    if night:
        mf = bpy.data.lights.new("NightFill", 'AREA'); mf.size = 6.0; mf.energy = 120; mf.color = (0.55, 0.65, 0.95)     # a cold sky fill down the lane
        mfo = bpy.data.objects.new("NightFill", mf); bpy.context.collection.objects.link(mfo); mfo.location = (0.0, 4.0, 9.0)
        box("Bulb", (3.8, 9.0, 2.72), (0.05, 0.05, 0.07), emissive("BulbE", (1.0, 0.8, 0.5), 40))      # a single bare bulb
        g = dd.guard("Guard", 41, "short02"); c["guard"] = g
        for k in range(4):                      # four men in overalls, each carrying a tin, hurrying to the door
            h = painter(f"Shape{k}", 30 + 6 * k, k)
            tin = paint_tin(f"STin{k}")
            c["painters"].append((h, tin, Vector((-0.4 + 0.6 * (k % 2), -1.0 - 1.5 * k, 0)), 0.3 * k))
        return
    for k in range(4):
        h = painter(f"Painter{k}", 30 + 6 * k, k)
        tin = paint_tin(f"Tin{k}")
        c["painters"].append((h, tin, Vector((0.3 + 0.55 * (k % 2) - 0.2 * (k // 2), -3.5 - 1.3 * k, 0)), 0.25 * k))


def salon_room(c, w=14.0, d=10.0, hgt=4.6, carpet=False, night=False):
    M = mats()
    floor = dd.tex_mat("marble_01", 0.35, tint=(0.92, 0.9, 0.86), name="Marble", sat=0.6)
    floor.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.6
    box("Floor", (0, d / 2, -0.05), (w, d, 0.1), floor)
    rug = dd.tex_mat("quatrefoil_jacquard_fabric", 1.2, tint=(1.15, 1.02, 0.84), name="Rug", sat=0.0)
    box("Rug", (0, d / 2 + 0.3, 0.004), (8.0, 6.0, 0.008), rug)
    box("RugBorder", (0, d / 2 + 0.3, 0.003), (8.3, 6.3, 0.006), fabric("RugBorder", (0.12, 0.13, 0.2), 0.95, 0.5, 400))
    panel = pbr("Boiserie", (0.72, 0.68, 0.6), 0.55)
    mould = pbr("Moulding", (0.8, 0.77, 0.7), 0.5)
    box("WallBack", (0, d + 0.1, hgt / 2), (w, 0.2, hgt), panel)
    box("WallL", (-w / 2 - 0.1, d / 2, hgt / 2), (0.2, d, hgt), panel)
    box("WallR", (w / 2 + 0.1, d / 2, hgt / 2), (0.2, d, hgt), panel)
    box("Ceiling", (0, d / 2, hgt + 0.1), (w, d, 0.2), pbr("Ceil", (0.85, 0.83, 0.8), 0.8))
    # moulded panels on the side and back walls
    for (ax, pos, rng_) in (("x", d - 0.01, np.arange(-w / 2 + 1.2, w / 2 - 1.0, 2.2)),):
        for x in rng_:
            for z0, hz in ((0.45, 0.6), (1.4, 2.3)):
                for (dx, dz, sx, sz) in ((0, 0, 1.8, 0.04), (0, hz, 1.8, 0.04), (-0.9, hz / 2, 0.04, hz), (0.9, hz / 2, 0.04, hz)):
                    box("Mould", (x + dx + 0.9, pos, z0 + dz), (sx, 0.03, sz), mould)
    for sx in (-1, 1):
        for y in np.arange(1.2, d - 1.0, 2.2):
            for z0, hz in ((0.45, 0.6), (1.4, 2.3)):
                for (dy, dz, sy, sz) in ((0, 0, 1.8, 0.04), (0, hz, 1.8, 0.04), (-0.9, hz / 2, 0.04, hz), (0.9, hz / 2, 0.04, hz)):
                    box("Mould", (sx * (w / 2 - 0.01), y + dy + 0.9, z0 + dz), (0.03, sy, sz), mould)
    box("Cornice", (0, d - 0.05, hgt - 0.12), (w, 0.15, 0.24), mould)
    # front wall with the tall windows onto the avenue (daylight from outside)
    for x in (-5.0, 0.0, 5.0):
        box("FrontGlass", (x, -0.02, 2.0), (3.4, 0.03, 3.8), glass("FrontGlass", (0.92, 0.95, 0.96), 0.03))
    for x in (-7.0, -2.5, 2.5, 7.0):
        box("FrontPier", (x, 0.0, hgt / 2), (1.4 if abs(x) < 7 else 0.6, 0.3, hgt), panel)
    box("FrontHead", (0, 0.0, 4.3), (w, 0.3, 0.6), panel)
    if not night:
        for x in (-3.5, 3.5):
            f_ = bpy.data.lights.new("CeilFill", 'AREA'); f_.size = 4.0; f_.energy = 60; f_.color = (1.0, 0.8, 0.6)
            fo = bpy.data.objects.new("CeilFill", f_); bpy.context.collection.objects.link(fo); fo.location = (x, d / 2, hgt - 0.05); fo.visible_camera = False
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = w; pt.size_y = 4.0; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (0, -0.1, 2.0); po.rotation_euler = (math.radians(-90), 0, 0)
    # chandeliers + warm ceiling wash
    # dressing: gilt mirrors on the back wall, a console with a vase, sofa and armchairs, wall sconces
    for x in (-4.4, 4.4):
        dd.model_h("ornate_mirror_01", (x, d - 0.08, 1.0), 1.7)
    dd.model_h("ClassicConsole_01", (0.0, d - 0.35, 0), 0.85, rot_z=math.pi)
    dd.model_h("ceramic_vase_01", (0.0, d - 0.35, 0.86), 0.45)
    dd.model_h("Sofa_01", (2.6, d - 1.1, 0), 0.95, rot_z=math.pi)
    for x in (-6.2, 6.2):
        for y in (3.0, 7.0):
            box("Sconce", (x + (0.1 if x < 0 else -0.1), y, 2.6), (0.06, 0.18, 0.28), emissive("SconceE", WARM, 0 if night else 6))
    for x in (-3.5, 3.5):
        dd.model_h("Chandelier_03", (x, d / 2, hgt - 1.1), 1.0)
        for j in range(6):                              # the chandelier's own bulbs: a warm glow around it
            a_ = j * math.pi / 3
            pl = bpy.data.lights.new("ChandBulb", 'POINT'); pl.energy = 0 if night else 35; pl.color = (1.0, 0.72, 0.45); pl.shadow_soft_size = 0.05
            po = bpy.data.objects.new("ChandBulb", pl); bpy.context.collection.objects.link(po); po.location = (x + 0.35 * math.cos(a_), d / 2 + 0.35 * math.sin(a_), hgt - 0.85)
        l = bpy.data.lights.new("Chand", 'POINT'); l.energy = 0 if night else 200; l.color = WARM; l.shadow_soft_size = 0.4
        o = bpy.data.objects.new("Chand", l); bpy.context.collection.objects.link(o); o.location = (x, d / 2, hgt - 0.6)
    return panel


def vitrine(name, loc, size=(1.4, 0.6), rot_z=0.0, rng=None, lit=True):
    """A display case: dark wood base, glass top, a warm light strip inside and jewels on small stands."""
    rng = rng or np.random.default_rng(3)
    M = mats(); W, D = size
    wood_ = dd.tex_mat("walnut_veneer", 1.5, tint=(0.6, 0.5, 0.42), name=name + "Wood", sat=0.8, coat=0.6)
    parts = [box(name + "Base", (0, 0, 0.45), (W, D, 0.9), wood_, bevel=0.01),
             box(name + "Bed", (0, 0, 0.91), (W - 0.06, D - 0.06, 0.02), fabric(name + "Velvet", (0.05, 0.06, 0.08), 0.9, 0.7, 300))]
    case = join(parts, name)
    gl = box(name + "Glass", (0, 0, 1.13), (W, D, 0.42), glass(name + "G", (0.95, 0.97, 0.98), 0.0))
    gl.parent = case
    if lit:
        st = box(name + "Strip", (0, D / 2 - 0.04, 1.32), (W - 0.1, 0.02, 0.01), emissive(name + "StripE", WARM, 25)); st.parent = case
        l = bpy.data.lights.new(name + "L", 'AREA'); l.size = W * 0.8; l.energy = 30; l.color = WARM
        lo = bpy.data.objects.new(name + "L", l); bpy.context.collection.objects.link(lo); lo.parent = case; lo.location = (0, 0, 1.3)
    if lit:
        glow = box(name + "BaseGlow", (0, -D / 2 - 0.004, 0.86), (W - 0.1, 0.01, 0.05), emissive(name + "BaseGlowE", WARM, 8)); glow.parent = case
        fl = bpy.data.lights.new(name + "Floor", 'AREA'); fl.size = W; fl.energy = 18; fl.color = WARM
        flo = bpy.data.objects.new(name + "Floor", fl); bpy.context.collection.objects.link(flo); flo.parent = case
        flo.location = (0, -D / 2 - 0.15, 0.1); flo.rotation_euler = (math.radians(180), 0, 0); flo.visible_camera = False
    jew = []
    tray_m = dd.tex_mat("velour_velvet", 2.0, tint=(0.25, 0.32, 0.7), name=name + "Tray", sat=0.4)
    for k in range(2):
        t_ = box(name + "TrayV", (-W / 4 + k * W / 2, 0.0, 0.93), (W / 2 - 0.08, D - 0.16, 0.025), tray_m, bevel=0.006); t_.parent = case
    for k in range(int(W / 0.25)):
        x = -W / 2 + 0.15 + k * 0.25
        stand_m = pbr(name + "Stand", (0.82, 0.8, 0.76), 0.5)
        s = cyl(name + "Stand", (x, 0.0, 0.965), 0.025, 0.05, stand_m, verts=16); s.parent = case
        r = dd.ring(f"{name}R{k}", (x, 0.0, 1.0), stone_r=rng.uniform(0.003, 0.006), band="plat" if k % 2 else "gold",
                    stone=("diamond", "ruby", "diamond", "sapphire", "emerald")[k % 5])
        r.parent = case; jew.append(r)
    case.location = loc; case.rotation_euler = (0, 0, rot_z)
    return case, jew


def build_salon(c, night=False):
    if night:
        world_sky(sun_elev_deg=-2, sun_rot_deg=95, strength=0.25, tint=(0.5, 0.55, 0.7))
    else:
        world_sky(sun_elev_deg=4, sun_rot_deg=95, strength=0.5, tint=(0.85, 0.9, 1.0))
        sun(4, 95, energy=1.0, color=(1.0, 0.75, 0.55), angle_deg=1.5)
    salon_room(c, night=night)
    rng = np.random.default_rng(9)
    c["cases"] = []
    for k, (x, y) in enumerate(((-3.0, 3.2), (0.4, 3.6), (3.5, 3.2), (-2.4, 6.6), (3.5, 6.4))):
        cs, _ = vitrine(f"Vit{k}", (x, y, 0), rng=rng); c["cases"].append(cs)
    for x in (-5.8, 5.8):
        dd.model_h("ArmChair_01", (x, 8.5, 0), 0.95, rot_z=math.pi if x < 0 else math.pi)
    if night:
        # the stair opening at the back: the first staff light coming on downstairs (frame driver ramps it up)
        box("StairWell", (5.0, 9.95, 1.3), (1.4, 0.05, 2.6), pbr("StairDark", (0.02, 0.02, 0.02), 0.8))
        sl = bpy.data.lights.new("Downstairs", 'AREA'); sl.size = 1.2; sl.color = (1.0, 0.85, 0.65)
        dr = sl.driver_add("energy").driver; dr.type = 'SCRIPTED'; dr.expression = "0 if frame < 96 else min(260, (frame - 96) * 26)"
        so = bpy.data.objects.new("Downstairs", sl); bpy.context.collection.objects.link(so); so.location = (5.0, 9.6, 0.4); so.rotation_euler = (math.radians(-60), 0, 0)
        # near-dark: three men on the floor with their backs to the cases, one standing at the blinds; sodium streetlight
        # falls through the slats in bars across them; a wall clock; then the morning light comes up (frame driver)
        c["seated"] = []
        for k, (x, y) in enumerate(((-3.35, 2.6), (-2.6, 2.6), (0.15, 3.0))):
            h = person(f"Waiter{k}", 1.0, 30 + 6 * k, ("male_casualsuit05", "male_casualsuit01")[k % 2], ("short02", "short04", "short01")[k], cval=0.85)
            pose_floor_sit(h, hunch=12, hands_back=False); place(h, (x, y, 0), 0.0)
            hp = (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) / 2
            h.arm.location.z += 0.11 - hp.z; bpy.context.view_layer.update()
            c["seated"].append(h)
        wm = person("WindowMan", 1.0, 44, "male_casualsuit01", "short03", cval=0.7); c["window_man"] = wm
        zero(wm); pose_walk(wm, 0.0, stride=0.0, arm_swing=0.0); place(wm, (-4.7, 0.55, 0), math.radians(-10)); arms_relaxed(wm)
        BL = dd.Builder("Blinds")
        slat = pbr("BlindSlat", (0.7, 0.68, 0.64), 0.5)
        for x in (-5.0, 0.0, 5.0):
            for j in range(40):
                BL.box((x, 0.1, 0.25 + j * 0.092), (3.4, 0.05, 0.012), slat, rot=(math.radians(35), 0, 0))
        BL.done()
        st = bpy.data.lights.new("StreetSodium", 'SPOT'); st.energy = 9000; st.spot_size = math.radians(40); st.color = (1.0, 0.6, 0.28); st.shadow_soft_size = 0.04
        sto = bpy.data.objects.new("StreetSodium", st); bpy.context.collection.objects.link(sto); sto.location = (2.0, -7.0, 5.5); point_at(sto, (-3.0, 2.4, 0.5))
        dd.model_h("wall_clock", (-6.88, 2.2, 3.0), 0.42, rot_z=-math.pi / 2)
        dawn = bpy.data.lights.new("DawnWin", 'AREA'); dawn.shape = 'RECTANGLE'; dawn.size = 13; dawn.size_y = 3.6; dawn.color = (0.75, 0.82, 1.0)
        dr = dawn.driver_add("energy").driver; dr.type = 'SCRIPTED'; dr.expression = "0 if frame < 130 else min(900, (frame - 130) * 14)"
        do = bpy.data.objects.new("DawnWin", dawn); bpy.context.collection.objects.link(do); do.location = (0, 0.4, 2.1); do.rotation_euler = (math.radians(90), 0, 0)
        for k, (x, y) in enumerate(((-3.0, 3.2), (0.4, 3.6), (3.5, 3.2), (-2.4, 6.6), (3.5, 6.4))):
            vitrine(f"Vit{k}", (x, y, 0), rng=np.random.default_rng(9), lit=False)
        haussmann(-30, 30, seed=30, rot_z=math.pi, origin=(0, -14, 0), lit_frac=0.05)
        return
    # outside the windows: the avenue at dawn (a facade across the street)
    haussmann(-30, 30, seed=30, rot_z=math.pi, origin=(0, -14, 0), lit_frac=0.12)
    box("StreetOut", (0, -7, -0.06), (80, 14, 0.1), pbr("AsphaltOut", (0.08, 0.08, 0.085), 0.6))
    # staff sitting on the floor against the left wall; one painter standing over them
    c["seated"] = []
    spots = [(-6.0, 4.4), (-5.95, 5.3), (-6.05, 6.2), (-5.9, 7.1)]
    who = [("Staff0", 0.0, 32, "female_elegantsuit01", "bob02"), ("Staff1", 1.0, 45, "male_elegantsuit01", "short02"),
           ("Staff2", 0.0, 51, "female_elegantsuit01", "ponytail01"), ("Staff3", 1.0, 29, "male_elegantsuit01", "short04")]
    for (x, y), (nm, g, yr, cl, hr) in zip(spots, who):
        h = dd.staff(nm, g, yr, hr, seed=len(c["seated"]))
        pose_floor_sit(h, hunch=16)
        place(h, (x, y, 0), face_to((x, y), (0.0, y)))
        c["seated"].append(h)
    p = painter("PainterG", 38, 1); c["guard_painter"] = p
    c["pistol"] = dd.model_h("service_pistol", (0, 0, 0), 0.13)


def build_safe(c):
    world_flat((0.02, 0.02, 0.025), 1.0)
    steel = brushed_metal("SafeSteel", (0.5, 0.51, 0.52))
    wall = pbr("SafeWall", (0.22, 0.24, 0.23), 0.6)
    box("Floor", (0, 2, -0.05), (6, 6, 0.1), dd.tex_mat("concrete_floor_painted", 0.6, tint=(0.6, 0.6, 0.6), name="SafeFloor", sat=0.4))
    box("Back", (0, 4.6, 1.5), (6, 0.2, 3.0), wall); box("L", (-3.0, 2, 1.5), (0.2, 6, 3.0), wall); box("R", (3.0, 2, 1.5), (0.2, 6, 3.0), wall)
    box("Ceil", (0, 2, 3.0), (6, 6, 0.1), wall)
    # safe deposit wall on the left
    br = brushed_metal("Deposit", (0.6, 0.6, 0.6))
    for i in range(10):
        for j in range(7):
            box("Box", (-2.88, 1.0 + i * 0.32, 0.4 + j * 0.3), (0.05, 0.3, 0.28), br, bevel=0.004)
            cyl("Lock", (-2.85, 1.0 + i * 0.32, 0.45 + j * 0.3), 0.012, 0.02, mats()["bronze"], verts=10, rot=(0, math.radians(90), 0))
    # the vault door in the back wall: a thick round door hinged on its left edge
    box("VaultFrame", (0.8, 4.48, 1.15), (2.2, 0.1, 2.2), steel)
    box("VaultDark", (0.8, 4.52, 1.15), (1.6, 0.05, 1.6), pbr("VaultIn", (0.05, 0.05, 0.05), 0.6))
    B = dd.Builder("VaultDoor"); R = (math.radians(90), 0, 0)
    B.cyl((0.85, 0, 0), 0.82, 0.3, steel, verts=64, rot=R)
    for k in range(6):
        a = k * math.pi / 3
        B.cyl((0.85 + 0.18 * math.cos(a), -0.2, 0.18 * math.sin(a)), 0.02, 0.36, mats()["bronze"], verts=8, rot=(0, math.pi / 2 - a, 0))
    B.cyl((0.85, -0.2, 0), 0.07, 0.08, mats()["bronze"], verts=24, rot=R)
    B.cyl((0.85, -0.18, 0), 0.62, 0.04, steel, verts=64, rot=R)                     # raised inner ring
    for k in range(48):                                                            # the hand wheel rim
        a = 2 * math.pi * k / 48
        B.cyl((0.85 + 0.36 * math.cos(a), -0.38, 0.36 * math.sin(a)), 0.018, 0.05, mats()["bronze"], verts=8, rot=(0, -a, 0))
    for k in range(16):                                                            # locking bolts round the edge
        a = 2 * math.pi * k / 16
        B.cyl((0.85 + 0.84 * math.cos(a), 0.0, 0.84 * math.sin(a)), 0.035, 0.22, steel, verts=12, rot=(0, math.pi / 2 - a, 0))
    for k in range(3):                                                             # hinge knuckles on the left edge
        B.box((0.05, -0.05, -0.45 + k * 0.45), (0.16, 0.2, 0.22), steel)
    door = B.done((0.8 - 0.85, 4.25, 1.15)); c["vault"] = door
    bpy.ops.object.select_all(action='DESELECT'); door.select_set(True); bpy.context.view_layer.objects.active = door
    bpy.ops.object.shade_smooth()
    for i in range(5):                       # more deposit boxes on the right wall, nearer the door
        for j in range(7):
            box("BoxR", (2.88, 0.2 + i * 0.32, 0.4 + j * 0.3), (0.05, 0.3, 0.28), br, bevel=0.004)
    box("SafeCabinet", (-1.6, 4.3, 0.55), (1.0, 0.5, 1.1), steel, bevel=0.01)
    # alarm keypad with a status LED (red, then green: frame driver)
    box("Keypad", (2.88, 2.6, 1.45), (0.04, 0.22, 0.3), pbr("KeypadM", (0.85, 0.85, 0.82), 0.4))
    for i in range(3):
        for j in range(4):
            box("Key", (2.855, 2.53 + i * 0.07, 1.36 + j * 0.055), (0.01, 0.05, 0.04), pbr("KeyM", (0.3, 0.3, 0.32), 0.4))
    led = bpy.data.materials.new("LED"); led.use_nodes = True
    N = led.node_tree.nodes; L = led.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs['Strength'].default_value = 30
    g = dd.frame_value(N, "1 if frame > 46 else 0", "Green")
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (1, 0.05, 0.02, 1); mx.inputs[7].default_value = (0.1, 1, 0.2, 1)
    L.new(g.outputs[0], mx.inputs['Factor']); L.new(mx.outputs[2], em.inputs['Color']); L.new(em.outputs[0], out.inputs['Surface'])
    box("LED", (2.85, 2.6, 1.58), (0.01, 0.03, 0.02), led)
    for x in (-1.2, 1.2):
        box("Tube", (x, 2.0, 2.94), (0.12, 2.4, 0.04), emissive("Tube", (0.9, 0.95, 1.0), 6))
        a = bpy.data.lights.new("TubeL", 'AREA'); a.shape = 'RECTANGLE'; a.size = 0.2; a.size_y = 2.4; a.energy = 60; a.color = (0.9, 0.95, 1.0)
        o = bpy.data.objects.new("TubeL", a); bpy.context.collection.objects.link(o); o.location = (x, 2.0, 2.9)
    mg = dd.staff("Manager", 0.0, 46, "bob01", seed=1); c["manager"] = mg
    pt = painter("PainterS", 34, 2); c["safe_painter"] = pt


def build_corridor(c, empty=False):
    """The service corridor behind the shop: painted walls, lino floor, one fluorescent tube; a door at the far end."""
    world_flat((0.0, 0.0, 0.0), 1.0)
    wall = dd.tex_mat("painted_plaster_wall", 0.7, tint=(0.68, 0.68, 0.62), name="CorrWall", sat=0.4)
    floor = dd.tex_mat("concrete_floor_painted", 0.8, tint=(0.4, 0.42, 0.42), name="CorrFloor", sat=0.4)
    B = dd.Builder("Corridor")
    B.box((0, 5, -0.05), (1.8, 12, 0.1), floor).box((0, 5, 2.65), (1.8, 12, 0.1), wall)
    B.box((-0.95, 5, 1.3), (0.1, 12, 2.7), wall).box((0.95, 5, 1.3), (0.1, 12, 2.7), wall)
    B.box((0, -0.9, 1.3), (1.8, 0.1, 2.7), wall)
    B.box((-0.5, 10.05, 1.3), (0.8, 0.1, 2.7), wall).box((0.55, 10.05, 1.3), (0.7, 0.1, 2.7), wall)
    B.box((0, 10.05, 2.4), (1.8, 0.1, 0.5), wall)
    for y in (2.0, 5.5):                                  # pipes and a cable tray along the ceiling
        pass
    B.cyl((0.75, 5, 2.45), 0.04, 12, pbr("Pipe", (0.5, 0.5, 0.48), 0.4, 0.6), verts=12, rot=(math.radians(90), 0, 0))
    B.box((-0.94, 3.0, 1.1), (0.04, 0.5, 0.4), pbr("Fusebox", (0.55, 0.55, 0.52), 0.5))
    B.done()
    # the far door (hinged at x=-0.1+...): opens toward us, warm shop light behind it
    door = dd.Builder("CorrDoor"); door.box((0.425, 0, 1.05), (0.85, 0.05, 2.1), pbr("CorrDoorM", (0.3, 0.32, 0.33), 0.45, 0.5))
    door.box((0.75, -0.05, 1.0), (0.12, 0.03, 0.03), pbr("Handle", (0.6, 0.6, 0.6), 0.3, 1.0))
    c["cdoor"] = door.done((-0.1 - 0.3, 10.0, 0.0))
    box("ShopBeyond", (0, 12.5, 1.3), (4, 0.1, 2.7), emissive("Beyond", WARM, 1.5))
    a = bpy.data.lights.new("Spill", 'AREA'); a.size = 1.2; a.energy = 220; a.color = WARM
    ao = bpy.data.objects.new("Spill", a); bpy.context.collection.objects.link(ao); ao.location = (0, 11.0, 1.3); ao.rotation_euler = (math.radians(-90), 0, 0)
    # fluorescent tube: a slow, gentle, irregular buzz (frame driver: two slow sines + a rare soft dip)
    expr = "0.85 + 0.08 * sin(frame * 0.21) + 0.05 * sin(frame * 0.53 + 1.3) - 0.25 * max(0, sin(frame * 0.071) - 0.93) * 10"
    tube_m = bpy.data.materials.new("Tube"); tube_m.use_nodes = True
    N = tube_m.node_tree.nodes; L = tube_m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (0.85, 0.95, 1.0, 1)
    fv = dd.frame_value(N, "8 * (" + expr + ")", "Buzz"); L.new(fv.outputs[0], em.inputs['Strength']); L.new(em.outputs[0], out.inputs['Surface'])
    box("Tube", (0, 8.3, 2.57), (0.08, 1.2, 0.04), tube_m)
    tl = bpy.data.lights.new("TubeL", 'AREA'); tl.shape = 'RECTANGLE'; tl.size = 0.1; tl.size_y = 1.2; tl.color = (0.85, 0.95, 1.0)
    d = tl.driver_add("energy").driver; d.type = 'SCRIPTED'; d.expression = "45 * (" + expr + ")"
    to = bpy.data.objects.new("TubeL", tl); bpy.context.collection.objects.link(to); to.location = (0, 8.3, 2.5)
    if empty:
        # the guard's post by the door: a small metal desk with a CCTV monitor, an office chair, a lanyard on the seat
        from sc_invest import office_chair
        dd.model_h("metal_office_desk", (-0.58, 8.3, 0), 0.76, rot_z=math.radians(-90))
        ch = office_chair((0.15, 8.25, 0), math.radians(110), fabric("ChairFab", (0.05, 0.05, 0.06), 0.9, 0.3, 400),
                          pbr("ChairMetal", (0.25, 0.25, 0.27), 0.35, 0.9))
        tv = dd.model_h("Television_01", (-0.62, 8.15, 0.76), 0.32, rot_z=math.radians(-90))
        scr = bpy.data.materials.new("CCTV"); scr.use_nodes = True
        N = scr.node_tree.nodes; L = scr.node_tree.links; N.clear()
        out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tc = N.new("ShaderNodeTexCoord")
        nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 60
        fv = dd.frame_value(N, "frame * 0.37", "Static"); L.new(fv.outputs[0], nz.inputs['W']); L.new(tc.outputs['Object'], nz.inputs['Vector'])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 0.25; mr.inputs['To Max'].default_value = 0.6
        L.new(nz.outputs['Fac'], mr.inputs['Value'])
        cr = N.new("ShaderNodeCombineColor"); L.new(mr.outputs[0], cr.inputs[0]); L.new(mr.outputs[0], cr.inputs[1]); L.new(mr.outputs[0], cr.inputs[2])
        L.new(cr.outputs[0], em.inputs['Color']); em.inputs['Strength'].default_value = 2.0; L.new(em.outputs[0], out.inputs['Surface'])
        box("CCTVScreen", (-0.44, 8.12, 0.92), (0.005, 0.2, 0.15), scr)
        lan = pbr("Lanyard", (0.08, 0.14, 0.42), 0.7)
        box("Lanyard", (0.15, 8.25, 0.52), (0.3, 0.015, 0.004), lan, rot=(0, 0, 0.4))
        box("Badge", (0.25, 8.32, 0.525), (0.07, 0.1, 0.004), pbr("Badge", (0.92, 0.92, 0.9), 0.4), rot=(0, 0, 0.4))
        # a coat hook rail on the right wall with a dark jacket hanging
        box("HookRail", (0.89, 7.4, 1.7), (0.03, 0.6, 0.05), pbr("HookWood", (0.3, 0.2, 0.12), 0.5))
        for k in range(3):
            box("Hook", (0.86, 7.2 + k * 0.2, 1.68), (0.05, 0.015, 0.015), pbr("HookM", (0.6, 0.6, 0.6), 0.3, 1.0))
        box("Jacket", (0.83, 7.4, 1.3), (0.1, 0.45, 0.75), fabric("JacketF", (0.04, 0.05, 0.08), 0.9, 0.4, 300), bevel=0.04)
    else:
        c["waiting"] = []
        for k, (x, y, f) in enumerate(((-0.55, 7.2, 0.4), (0.5, 6.5, -0.3), (-0.5, 5.6, 0.2), (0.45, 4.6, -0.5))):
            h = painter(f"Wait{k}", 30 + 6 * k, k)
            place(h, (x, y, 0), math.pi + f)       # facing the far door (+Y)
            arms_relaxed(h)
            c["waiting"].append(h)


def build(variant=None):
    c = {"variant": variant}
    v = variant or "dawn"
    {"dawn": build_dawn, "lane": build_lane, "salon": build_salon, "safe": build_safe,
     "corridor": build_corridor, "corridor_empty": lambda c: build_corridor(c, True),
     "lane_night": lambda c: build_lane(c, True), "salon_night": lambda c: build_salon(c, True)}[v](c)
    import look                                   # house cinematic lighting (look.py), at the end of the build
    if v == "dawn":
        look.day_light("mist", azim=70, elev=10, haze_box=((0, -8, 6), (70, 30, 14)), haze_density=0.004)
    elif v == "lane":
        look.day_light("mist", azim=150, haze_box=((0, 4, 6), (10, 60, 14)), haze_density=0.005)
    elif v == "salon":
        look.interior_day(window=((0, -1.2, 2.6), (-0.5, 5.0, 0.4)), mood="low_sun", key_size=3.0)
    else:                                         # safe, corridors, the night lane and the dark salon
        look.night_interior()
    return c


# ============================================================================ animation + cameras
def anim_facade(c, t):
    anim_doorman(c, t * DUR["facade"])
    c["staff"].arm.location = (0, 0, -50)
    c["grille"].location.z = 3.2


def cam_facade(c, t):
    e = ease(t)
    d = c["info"]["door"]
    loc = Vector((d.x - 5.0, -5.6, 1.6)).lerp(Vector((d.x - 4.0, -5.2, 4.2)), e)
    tgt = Vector((d.x + 1.0, 0, 3.2)).lerp(Vector((d.x + 1.0, 0, 9.5)), e)
    return loc, tgt, 18


def anim_grille(c, t):
    sec = t * DUR["grille"]
    anim_doorman(c, sec + 3.0)
    d = c["info"]["door"]
    u = ease(min(1.0, max(0.0, (sec - 0.8) / 3.4)))
    c["grille"].location = d + Vector((0, -0.1, 3.0 * u))
    st = c["staff"]; zero(st); from human import pose_walk
    pose_walk(st, 0.0, stride=0.0, arm_swing=0.0)
    place(st, d + Vector((-0.6, -0.65, 0.12)), face_to(d + Vector((-0.6, -0.65, 0)), d + Vector((-0.6, 0, 0))), z=0.12)
    M = st.arm.matrix_world.to_3x3()
    hz = 1.15 + 0.5 * u
    reach(st, "R", d + Vector((-0.45, -0.25, hz)), M @ Vector((-1, 0.3, -0.5)))
    arms_relaxed_one(st, "L")


def arms_relaxed_one(h, sd):
    M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
    sg = 1 if sd == "L" else -1
    up = (Vector((0, 0, -1)) + left * (0.12 * sg)).normalized(); lo = (up + fwd * 0.25).normalized()
    h.aim(f"upperarm01.{sd}", up); h.aim(f"upperarm02.{sd}", up); h.aim(f"lowerarm01.{sd}", lo); h.aim(f"lowerarm02.{sd}", lo)


def cam_grille(c, t):
    e = ease(t)
    d = c["info"]["door"]
    loc = Vector((d.x - 4.0, -4.4, 1.7)).lerp(Vector((d.x - 2.6, -4.0, 1.68)), e)
    return loc, d + Vector((0.4, 0, 2.2)), 24


def anim_painters(c, t):
    sec = t * DUR["painters"]
    for h, tin, start, delay in c["painters"]:
        end = c["door_at"] + Vector((-0.6 - 0.25 * (start.x), -0.5 + 0.1 * start.y, 0))
        walk_to(h, start, start + Vector((0.4, 12.0, 0)), max(0.0, sec - delay) + 0.5, speed=1.15)
        tip = h.bone_tail("wrist.R") if "wrist.R" in h.arm.pose.bones else h.bone_tail("lowerarm02.R")
        tin.location = tip - Vector((0, 0, 0.3))


def cam_painters(c, t):
    e = ease(t)
    loc = Vector((-1.5, -9.5, 2.4)).lerp(Vector((-1.2, -7.8, 2.2)), e)
    return loc, Vector((1.2, 9.0, 1.4)), 30


def anim_floor(c, t):
    sec = t * DUR["floor"]
    p = c["guard_painter"]
    x = -4.4 + 0.5 * math.sin(sec * 0.6)
    walk_to(p, Vector((-4.1, 3.9, 0)), Vector((-4.3, 7.6, 0)), sec, speed=0.55, cadence=1.2)
    pp = c["pistol"]
    if pp is not None:
        tip = p.bone_tail("wrist.R") if "wrist.R" in p.arm.pose.bones else p.bone_tail("lowerarm02.R")
        pp.location = tip + Vector((0, 0, -0.1)); pp.rotation_euler = (math.radians(90), 0, p.arm.rotation_euler.z)
    for k, h in enumerate(c["seated"]):
        h.rot("head", (0, 0, 1), 0)


def cam_floor(c, t):
    e = ease(t)
    loc = Vector((2.2, 9.3, 2.5)).lerp(Vector((1.4, 9.2, 2.4)), e)
    return loc, Vector((-4.6, 4.8, 1.0)), 22


def anim_safe(c, t):
    sec = t * DUR["safe"]
    mg = c["manager"]; zero(mg); from human import pose_walk
    pose_walk(mg, 0.0, stride=0.0, arm_swing=0.0)
    place(mg, (2.35, 2.55, 0), math.radians(-90))
    M = mg.arm.matrix_world.to_3x3()
    press = 0.015 * max(0.0, math.sin(sec * 7.0)) if sec < 1.9 else 0.0
    reach(mg, "L", Vector((2.8 - press, 2.62, 1.42)), M @ Vector((0.6, 0.2, -0.8)))
    arms_relaxed_one(mg, "R")
    mg.rot("head", (0, 1, 0), -6)
    p = c["safe_painter"]; place(p, (0.9, 3.2, 0), face_to((0.9, 3.2), (2.3, 2.6))); arms_relaxed(p)
    u = ease(min(1.0, max(0.0, (sec - 2.2) / 2.6)))
    c["vault"].rotation_euler = (0, 0, math.radians(-95 * u))


def cam_safe(c, t):
    e = ease(t)
    loc = Vector((-1.8, 0.3, 1.75)).lerp(Vector((-1.5, 0.6, 1.7)), e)
    return loc, Vector((1.3, 3.4, 1.15)), 20


def anim_corridor(c, t):
    sec = t * DUR["corridor"]
    u = ease(min(1.0, max(0.0, (sec - 1.5) / 3.0)))
    c["cdoor"].rotation_euler = (0, 0, math.radians(-100 * u))
    for k, h in enumerate(c.get("waiting", [])):
        h.rot("head", (0, 0, 1), 0)


def cam_corridor(c, t):
    e = ease(t)
    return Vector((0.1, 0.0, 1.65)).lerp(Vector((0.05, 1.4, 1.6)), e), Vector((0.0, 10.0, 1.2)), 28


def cam_chair(c, t):
    e = ease(t)
    return Vector((0.35, 4.6, 1.65)).lerp(Vector((0.3, 5.3, 1.6)), e), Vector((-0.1, 8.5, 0.75)), 28


def anim_night_door(c, t):
    sec = t * DUR["night_door"]
    c["sdoor"].rotation_euler = (0, 0, math.radians(-55 - 5 * math.sin(sec * 0.7)))      # held half open
    g = c["guard"]; zero(g); pose_walk(g, 0.0, stride=0.0, arm_swing=0.0)
    place(g, (3.95, 9.45, 0.0), math.radians(-15)); arms_relaxed(g)
    edge = c["sdoor"].matrix_world @ Vector((0, 1.05, 1.05))
    reach(g, "L", edge, Vector((1, 0.3, -1)))                      # a hand on the door
    g.rot("head", (0, 0, 1), 25 + 10 * math.sin(sec * 0.9))        # glancing up the lane
    for h, tin, start, delay in c["painters"]:
        walk_to(h, start, c["door_at"] + Vector((0.2, -0.3 + 0.2 * start.x, 0)), max(0.0, sec - delay), speed=1.35, cadence=2.1)
        tip = h.bone_tail("wrist.R") if "wrist.R" in h.arm.pose.bones else h.bone_tail("lowerarm02.R")
        tin.location = tip - Vector((0, 0, 0.3))


def anim_night_wait(c, t):
    sec = t * DUR["night_wait"]
    for k, h in enumerate(c["seated"]):
        h.rot("head", (0, 0, 1), 4 * math.sin(sec * 0.3 + k))
    c["window_man"].rot("head", (0, 0, 1), 8 * math.sin(sec * 0.25))


MOVES = {
    "night_door": dict(kind="anim", dof=5.6, anim=anim_night_door,
                       cam=lambda c, t: (Vector((-1.9, 0.6, 1.6)).lerp(Vector((-1.6, 1.6, 1.55)), ease(t)), Vector((3.3, 9.0, 1.3)), 30),
                       focus=lambda c, t: Vector((3.6, 9.2, 1.3))),
    "night_wait": dict(kind="anim", dof=4.0, anim=anim_night_wait,
                       cam=lambda c, t: (Vector((1.0, 1.7, 1.55)).lerp(Vector((0.6, 1.8, 1.5)), ease(t)), Vector((-4.2, 1.7, 0.9)), 24),
                       focus=lambda c, t: Vector((-3.0, 2.3, 0.6))),
    "corridor": dict(kind="anim", dof=4.0, cam=cam_corridor, anim=anim_corridor, focus=lambda c, t: Vector((0, 6.0, 1.4))),
    "chair": dict(kind="anim", dof=2.8, cam=cam_chair, anim=lambda c, t: None, focus=lambda c, t: Vector((0.55, 8.6, 0.6))),
    "facade": dict(kind="anim", dof=8.0, cam=cam_facade, anim=anim_facade, focus=lambda c, t: c["info"]["door"]),
    "grille": dict(kind="anim", dof=5.6, cam=cam_grille, anim=anim_grille, focus=lambda c, t: c["info"]["door"] + Vector((0, -0.6, 1.5)),
                   title=("Chapter One", "The Service Door", 24, 4.0 * 24)),
    "painters": dict(kind="anim", dof=8.0, cam=cam_painters, anim=anim_painters, focus=lambda c, t: Vector((0.5, 2.0, 1.2))),
    "floor": dict(kind="anim", dof=5.6, cam=cam_floor, anim=anim_floor, focus=lambda c, t: Vector((-5.2, 5.6, 0.8))),
    "safe": dict(kind="anim", dof=5.6, cam=cam_safe, anim=anim_safe, focus=lambda c, t: Vector((2.3, 2.6, 1.4))),
}
for _k in ("grille",):
    MOVES[_k]["dof"] = None        # DOF off on the title shot
