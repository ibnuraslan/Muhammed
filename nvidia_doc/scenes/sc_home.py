"""SET 1 / HOME (dramatization). Blue-hour dawn. A living room with floor-to-ceiling windows onto wooded hills and a
road in the valley below. The man in the black leather jacket sits on a low sofa, phone in both hands.

Everything is animated per frame:
  - breathing (spine/shoulders), small head motion
  - thumbs: a simple IK that aims the thumb bones at key positions on the screen keyboard (taps), then at Send
  - the email itself is the phone's screen texture (rendered per frame), so the thumb occludes it correctly
  - shot 4: arm brings the phone down to the coffee table (face down), he leans back, hand to his face
  - outside: trees sway, a car's headlights travel along the valley road, the sky brightens slowly

Moves (seconds at 12 fps):  wide 3.0 | shoulder 2.4 | thumb 1.2 | side 2.2
"""
import os, sys, math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion
from kit import *
from common import grid_mesh
from human import reset_pose, fingers_curl, rotate_bone, aim_bone, _world_verts, SIDE, reach, ik2
from people import man

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "iceman_video", "scenes"))
from terrain import fbm

EXPOSURE = 0.9
WIN_Y = 3.2                       # window wall (behind the sofa); the man faces -Y, into the room
DUR = {"wide": 3.0, "shoulder": 2.4, "thumb": 1.2, "side": 2.2}
UI_DIR = os.path.join(HERE, "..", "out", "ui_frames")
LINE = "I was unfaithful to my wife."


# ============================================================================ materials
def haze_mix(m, color=(0.42, 0.52, 0.68), start=80.0, end=4200.0, strength=0.7):
    """Aerial perspective: blend the surface toward the dawn haze with camera distance (cheap, no volumes)."""
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]; out = N["Material Output"]
    cd = N.new("ShaderNodeCameraData")
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = start; mr.inputs['From Max'].default_value = end
    mr.inputs['To Max'].default_value = strength
    L.new(cd.outputs['View Distance'], mr.inputs['Value'])
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = 1.0
    mx = N.new("ShaderNodeMixShader"); L.new(mr.outputs[0], mx.inputs[0])
    L.new(p.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    return m


def window_glass():
    """Real reflections for the camera, but transparent to shadow rays so the sky lights the room cleanly."""
    m = bpy.data.materials.new("WinGlass"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); lp = N.new("ShaderNodeLightPath")
    tr = N.new("ShaderNodeBsdfTransparent"); gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs['Roughness'].default_value = 0.02
    fr = N.new("ShaderNodeFresnel"); fr.inputs['IOR'].default_value = 1.5
    refl = N.new("ShaderNodeMixShader"); L.new(fr.outputs[0], refl.inputs[0]); L.new(tr.outputs[0], refl.inputs[1]); L.new(gl.outputs[0], refl.inputs[2])
    mx = N.new("ShaderNodeMixShader"); L.new(lp.outputs['Is Shadow Ray'], mx.inputs[0])
    L.new(refl.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    return m


def plaster(name, col):
    m = pbr(name, col, 0.85)
    N = m.node_tree.nodes; L = m.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 18; n.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.04; L.new(n.outputs['Fac'], b.inputs['Height'])
    L.new(b.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    return m


def screen_material():
    m = bpy.data.materials.new("PhoneScreen"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); tex = N.new("ShaderNodeTexImage"); tex.name = "UI"; tex.interpolation = 'Cubic'
    os.makedirs(UI_DIR, exist_ok=True)
    tex.image = bpy.data.images.new("UIImg", 540, 1170); tex.image.colorspace_settings.name = 'sRGB'
    L.new(tc.outputs['UV'], tex.inputs['Vector'])
    L.new(tex.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = 0.55
    p.inputs['Base Color'].default_value = (0.004, 0.004, 0.005, 1); p.inputs['Roughness'].default_value = 0.08
    p.inputs['Coat Weight'].default_value = 1.0; p.inputs['Coat Roughness'].default_value = 0.03
    return m


def set_ui(c, t_sec, typed, sent):
    """Render the mail UI for this frame (Skia) and load it as the screen texture."""
    sys.path.insert(0, os.path.join(HERE, "..", "edit"))
    from intro_cut import phone_ui
    from PIL import Image
    img = phone_ui(t_sec, typed, sent)
    path = os.path.join(UI_DIR, f"ui_{int(typed * 1000):04d}_{int(sent * 1000):04d}_{int(t_sec * 2) % 2}.png")
    if not os.path.exists(path):
        Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(path)
    tex = c["screen_mat"].node_tree.nodes["UI"]
    old = tex.image; tex.image = bpy.data.images.load(path, check_existing=True); tex.image.colorspace_settings.name = 'sRGB'
    if old is not None and old.users == 0:
        bpy.data.images.remove(old)


# ============================================================================ furniture
def sofa(x, y, seat_z, mat, leg_mat):
    """Low modern sofa facing -Y. Returns the parts. seat_z = top of the seat cushions."""
    W_, D_ = 2.3, 0.98
    parts = []
    base_top = seat_z - 0.16
    parts.append(box("SofaBase", (x, y, (0.12 + base_top) / 2), (W_, D_, base_top - 0.12), mat, bevel=0.03))
    for k in (-1, 1):
        parts.append(box("SofaArm", (x + k * (W_ / 2 - 0.1), y, (0.12 + seat_z + 0.18) / 2), (0.2, D_, seat_z + 0.06), mat, bevel=0.05))
    parts.append(box("SofaBack", (x, y + D_ / 2 - 0.11, (base_top + seat_z + 0.5) / 2), (W_ - 0.36, 0.22, seat_z + 0.5 - base_top), mat, bevel=0.06))
    for k in (-1, 1):       # two seat cushions and two back cushions, softened
        c1 = box("SeatCushion", (x + k * 0.49, y - 0.06, base_top + 0.08), (0.96, D_ - 0.3, 0.17), mat, bevel=0.06)
        c2 = box("BackCushion", (x + k * 0.49, y + D_ / 2 - 0.3, seat_z + 0.24), (0.94, 0.2, 0.46), mat, bevel=0.08, rot=(math.radians(-9), 0, 0))
        for o in (c1, c2):
            s = o.modifiers.new("s", 'SUBSURF'); s.levels = 2; s.render_levels = 2
        parts += [c1, c2]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl("SofaLeg", (x + sx * (W_ / 2 - 0.12), y + sy * (D_ / 2 - 0.1), 0.06), 0.02, 0.12, leg_mat, verts=12))
    return parts


def floor_lamp(loc):
    brass = pbr("LampBrass", (0.55, 0.42, 0.25), 0.28, 1.0)
    x, y = loc
    cyl("LampFoot", (x, y, 0.01), 0.16, 0.02, brass, verts=48)
    cyl("LampPole", (x, y, 0.78), 0.012, 1.55, brass, verts=16)
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.24, radius2=0.17, depth=0.3, location=(x, y, 1.62), end_fill_type='NOTHING')
    sh = bpy.context.active_object; sh.modifiers.new("s", 'SOLIDIFY').thickness = 0.004
    shade = pbr("LampShade", (0.85, 0.78, 0.66), 0.9, 0.0, **{'Transmission Weight': 0.0, 'Subsurface Weight': 0.6})
    p = shade.node_tree.nodes["Principled BSDF"]; p.inputs['Emission Color'].default_value = (1.0, 0.68, 0.38, 1); p.inputs['Emission Strength'].default_value = 1.4
    sh.data.materials.append(shade)
    l = bpy.data.lights.new("LampBulb", 'POINT'); l.energy = 55; l.shadow_soft_size = 0.08; l.color = (1.0, 0.66, 0.38)
    o = bpy.data.objects.new("LampBulb", l); bpy.context.collection.objects.link(o); o.location = (x, y, 1.6)


def bookshelf(x0, y0, mat):
    rng = np.random.default_rng(3)
    for k in range(6):
        box("Shelf", (x0, y0, 0.3 + k * 0.38), (0.32, 2.2, 0.025), mat)
    for s in (-1, 1):
        box("ShelfSide", (x0, y0 + s * 1.1, 1.25), (0.32, 0.025, 2.5), mat)
    cols = [(0.35, 0.33, 0.3), (0.12, 0.14, 0.18), (0.5, 0.45, 0.38), (0.22, 0.12, 0.1), (0.6, 0.6, 0.58), (0.16, 0.2, 0.17)]
    bm = [pbr(f"Book{i}", c_, 0.7) for i, c_ in enumerate(cols)]
    for k in range(5):
        y = y0 - 1.05
        while y < y0 + 1.0:
            w = rng.uniform(0.025, 0.05); h = rng.uniform(0.2, 0.3)
            if rng.random() < 0.12:
                y += 0.15; continue
            box("Book", (x0 - 0.02, y + w / 2, 0.3 + k * 0.38 + 0.0125 + h / 2), (rng.uniform(0.17, 0.23), w * 0.95, h), bm[rng.integers(len(bm))])
            y += w


def plant(loc, seed=5):
    rng = np.random.default_rng(seed)
    x, y = loc
    cyl("Pot", (x, y, 0.22), 0.2, 0.44, pbr("Pot", (0.55, 0.52, 0.48), 0.75), verts=48)
    cyl("Soil", (x, y, 0.43), 0.18, 0.01, pbr("Soil", (0.03, 0.02, 0.015), 0.95), verts=32)
    leaf_m = pbr("Leaf", (0.05, 0.12, 0.04), 0.45, 0.0, **{'Subsurface Weight': 0.2, 'Coat Weight': 0.3})
    for k in range(14):        # fiddle-leaf style: stems with broad tilted leaves
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.02, 0.12); hgt = rng.uniform(0.7, 1.55)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.14, location=(x + r * math.cos(a), y + r * math.sin(a), hgt))
        lf = bpy.context.active_object; lf.scale = (1.0, 0.55, 0.05); lf.rotation_euler = (rng.uniform(-0.7, 0.7), rng.uniform(-0.5, 0.5), a)
        lf.data.materials.append(leaf_m)
        cyl("Stem", (x + r * math.cos(a) * 0.5, y + r * math.sin(a) * 0.5, (0.44 + hgt) / 2), 0.006, hgt - 0.44, leaf_m, verts=6)


# ============================================================================ outside: hills, trees, road, car
def landscape(c):
    n = 220
    # rows = y (away from the house), cols = x. The house sits on a hillside; the valley floor is ~70 m below.
    sx, sy = 5200.0, 3600.0; y0 = WIN_Y + 30 + sy / 2
    H = fbm((n, n), seed=11, octaves=7, base_freq=2.4)
    yy = np.linspace(-sy / 2, sy / 2, n)[:, None] + y0 - WIN_Y          # distance from the window
    valley = -70.0 + 0.0 * yy
    rise = np.clip((yy - 700) / 1600, 0, 1) ** 1.3 * 260                 # far hills climbing to ~190 m
    near = np.clip((220 - yy) / 220, 0, 1) ** 1.5 * 62                    # our own slope just below the house
    Z = valley + rise + near + H * (25 + 110 * np.clip((yy - 500) / 2000, 0, 1))
    Z = np.broadcast_to(Z, (n, n)).copy()
    g = grid_mesh("Hills", Z, sx, sy, 1.0, origin=(0, y0, 0))
    gm = pbr("Ground", (0.05, 0.07, 0.045), 0.95)
    N = gm.node_tree.nodes; L = gm.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.02; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (0.035, 0.05, 0.03, 1); ramp.color_ramp.elements[1].color = (0.09, 0.09, 0.06, 1)
    L.new(nz.outputs['Fac'], ramp.inputs['Fac']); L.new(ramp.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    g.data.materials.append(haze_mix(gm)); bpy.ops.object.select_all(action='DESELECT')
    c["Z"], c["grid"] = Z, (sx, sy, y0, n)
    return g


def ground_z(c, x, y):
    sx, sy, y0, n = c["grid"]
    i = (y - (y0 - sy / 2)) / sy * (n - 1); j = (x + sx / 2) / sx * (n - 1)
    i = min(max(i, 0), n - 1.001); j = min(max(j, 0), n - 1.001)
    i0, j0 = int(i), int(j); fi, fj = i - i0, j - j0
    Z = c["Z"]
    return (Z[i0, j0] * (1 - fi) * (1 - fj) + Z[i0, j0 + 1] * (1 - fi) * fj + Z[i0 + 1, j0] * fi * (1 - fj) + Z[i0 + 1, j0 + 1] * fi * fj)


def trees(c):
    rng = np.random.default_rng(21)
    bark = pbr("Bark", (0.04, 0.03, 0.022), 0.9)
    fol = [haze_mix(pbr(f"Foliage{k}", col, 0.8, 0.0, **{'Subsurface Weight': 0.1}), strength=0.8)
           for k, col in enumerate(((0.012, 0.022, 0.014), (0.02, 0.032, 0.018), (0.012, 0.02, 0.016)))]
    # templates: a layered conifer (stacked, noise-displaced tiers on a trunk) and a rounded broadleaf crown
    tx = bpy.data.textures.new("TreeN", 'CLOUDS'); tx.noise_scale = 0.05; tx.noise_depth = 2
    tiers = []
    for k in range(12):
        r = (1.0 - k * 0.075) * (0.85 + 0.15 * (k % 2)); z = 0.12 + k * 0.072
        bpy.ops.mesh.primitive_cone_add(vertices=36, radius1=r * 0.2, radius2=0.0, depth=0.2, location=(0, 0, z))
        o = bpy.context.active_object
        sub = o.modifiers.new("sub", 'SUBSURF'); sub.levels = 1; sub.render_levels = 1; sub.subdivision_type = 'SIMPLE'
        d = o.modifiers.new("d", 'DISPLACE'); d.texture = tx; d.strength = 0.035
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
        tiers.append(o)
    tiers.append(cyl("Trunk", (0, 0, 0.2), 0.025, 0.4, bark, verts=8))
    for o in tiers[:-1]:
        o.data.materials.append(fol[0])
    con = join(tiers, "Conifer"); con.location = (0, 0, -500)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(0, 0, 0))
    leaf = bpy.context.active_object; leaf.data.materials.append(fol[1])
    d = leaf.modifiers.new("d", 'DISPLACE'); d.texture = tx; d.strength = 0.3
    bpy.ops.object.modifier_apply(modifier=d.name); leaf.location = (0, 0, -500)
    near_trees = []
    for k in range(2600):
        x = rng.uniform(-2400, 2400); y = WIN_Y + rng.uniform(90, 3300)
        dist = y - WIN_Y
        if abs(x) > 300 + dist * 1.2:            # outside the window's view: skip
            continue
        if 520 < dist < 640 and rng.random() < 0.85:     # keep the valley floor (road) mostly clear
            continue
        z = ground_z(c, x, y); s = rng.uniform(14, 24)
        if rng.random() < 0.65:
            instance(con, (x, y + 500 * 0, z), scale=(s, s, s * 1.15))
        else:
            instance(leaf, (x, y, z + s * 0.3), scale=(s * 0.45, s * 0.45, s * 0.38))
    # a few conifers on our own slope below the deck; their tops sway in the wind
    for k in range(9):
        x = rng.uniform(-45, 45); y = WIN_Y + rng.uniform(30, 75); z = ground_z(c, x, y); s = rng.uniform(18, 26)
        o = instance(con, (x, y, z), scale=(s, s, s * 1.2))
        near_trees.append((o, rng.uniform(0, 6.28), Vector(o.location)))
    c["near_trees"] = near_trees


def road_and_car(c):
    pts = []
    for k in range(80):
        x = -2400 + k * 60.0; y = WIN_Y + 580 + 35 * math.sin(x / 400.0)
        pts.append(Vector((x, y, ground_z(c, x, y) + 0.3)))
    cu = bpy.data.curves.new("Road", 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p_, q in zip(sp.points, pts):
        p_.co = (*q, 1)
    cu.extrude = 4.0
    ro = bpy.data.objects.new("Road", cu); bpy.context.collection.objects.link(ro)
    ro.data.materials.append(haze_mix(pbr("Asphalt", (0.03, 0.03, 0.032), 0.6), strength=0.75))
    c["road"] = pts
    head = emissive("Headlight", (1.0, 0.9, 0.75), 900); tail = emissive("Taillight", (1.0, 0.05, 0.02), 300)
    cars = []
    for k, (u0, speed, d) in enumerate(((0.38, 0.018, 1), (0.66, -0.014, -1))):
        parts = []
        for s in (-0.8, 0.8):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.35, location=(0, 0, -900))
            hl = bpy.context.active_object; hl.data.materials.append(head if d > 0 else tail); parts.append((hl, s, 2.2 * d))
            bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.3, location=(0, 0, -900))
            tl = bpy.context.active_object; tl.data.materials.append(tail if d > 0 else head); parts.append((tl, s, -2.2 * d))
        cars.append((u0, speed, parts))
    c["cars"] = cars


def road_point(c, u):
    pts = c["road"]; f = min(max(u, 0), 0.9999) * (len(pts) - 1); i = int(f)
    return pts[i].lerp(pts[i + 1], f - i), (pts[i + 1] - pts[i]).normalized()


# ============================================================================ the man and his phone
HOLD = dict(lean=24, head=16)


def pose_man(c, sec, phase):
    """Pose the man for this moment. phase: dict with typing/send/down/back weights."""
    h = c["h"]; reset_pose(h)
    breathe = math.sin(2 * math.pi * sec / 3.6)
    back = phase.get("back", 0.0)                 # 0 = leaning forward over the phone, 1 = sitting back
    lean = HOLD["lean"] * (1 - back) - 15 * back + (0.8 + 1.4 * back) * breathe
    for sd, sg in SIDE.items():
        for b, d in ((f"upperleg01.{sd}", (0.16 * sg, -1, -0.08)), (f"upperleg02.{sd}", (0.16 * sg, -1, -0.08)),
                     (f"lowerleg01.{sd}", (0.06 * sg, -0.32, -1)), (f"lowerleg02.{sd}", (0.06 * sg, -0.32, -1)),
                     (f"foot.{sd}", (0.1 * sg, -1, -0.3))):
            h.aim(b, d)
    for b, a in (("spine05", 4), ("spine04", 5), ("spine03", 5), ("spine02", 4), ("spine01", 3)):
        h.rot(b, (1, 0, 0), lean * a / 21)
    for sd in ("L", "R"):
        h.rot(f"clavicle.{sd}", (1, 0, 0), -1.2 * breathe)
    if c.get("base_loc") is not None:             # sitting back = sliding the hips back into the cushions
        h.arm.location = c["base_loc"] + Vector((0, 0.24 * back, 0.01 * back)); bpy.context.view_layer.update()
    down = phase.get("down", 0.0)                 # 0 = phone held in front of the chest, 1 = arm out to the table
    hand_face = phase.get("face", 0.0)
    if down > 0 or hand_face > 0 or phase.get("left_rest", 0) > 0:
        head_pose(h, sec, back); arms_ik(c, phase); return
    for sd, sg in SIDE.items():
        hold_up = (0.1 * sg, -0.5, -0.86); hold_lo = (-0.55 * sg, -0.75, 0.25); hold_wr = (-0.3 * sg, -0.6, 0.6)
        if sd == "R":
            reach_up = (-0.05, -0.75, -0.65); reach_lo = (0.05, -0.8, -0.6); reach_wr = (0.0, -0.4, -0.9)
            face_up = (0.15 * sg, -0.45, -0.3); face_lo = (-0.45 * sg, -0.25, 0.88); face_wr = (-0.3 * sg, 0.2, 0.9)
            mix = lambda a, b, k: tuple(x * (1 - k) + y * k for x, y in zip(a, b))
            up = mix(mix(hold_up, reach_up, down), face_up, hand_face); lo = mix(mix(hold_lo, reach_lo, down), face_lo, hand_face)
            wr = mix(mix(hold_wr, reach_wr, down), face_wr, hand_face)
        else:
            rest_up = (0.15, -0.35, -0.92); rest_lo = (-0.2, -0.95, -0.1); rest_wr = (-0.2, -0.95, -0.2)
            k = phase.get("left_rest", 0.0)
            mix = lambda a, b, k: tuple(x * (1 - k) + y * k for x, y in zip(a, b))
            up, lo, wr = mix(hold_up, rest_up, k), mix(hold_lo, rest_lo, k), mix(hold_wr, rest_wr, k)
        h.aim(f"upperarm01.{sd}", up); h.aim(f"upperarm02.{sd}", up)
        h.aim(f"lowerarm01.{sd}", lo); h.aim(f"lowerarm02.{sd}", lo); h.aim(f"wrist.{sd}", wr)
    fingers_curl(h, 38, thumb=8)
    head_pose(h, sec, back)


def head_pose(h, sec, back):
    h.rot("neck01", (1, 0, 0), 4 * (1 - back)); h.rot("head", (1, 0, 0), HOLD["head"] * (1 - back) - 22 * back + 1.2 * math.sin(sec * 1.3))
    h.rot("head", (0, 0, 1), 2.5 * math.sin(sec * 0.7))
    bpy.context.view_layer.update()


def arms_ik(c, phase):
    """Shot 4 arms: right hand carries the phone to the table then goes to his face; left hand settles on the thigh."""
    h = c["h"]
    eye = (h.eyes[0].matrix_world.to_translation() + h.eyes[1].matrix_world.to_translation()) / 2
    down, face, rest = phase.get("down", 0.0), phase.get("face", 0.0), phase.get("left_rest", 0.0)
    sh = h.bone_head("upperarm01.R")
    hold = sh + Vector((0.12, -0.38, -0.22))
    table = c["table_spot"] + Vector((0.0, 0.05, 0.07))
    seat = h.bone_head("upperleg01.R") + Vector((-0.3, 0.12, -0.02))          # on the cushion beside his hip
    T = hold.lerp(table, down).lerp(seat, face)
    hand = Vector((0, -0.3, -1)).lerp(Vector((-0.2, -0.6, -0.75)), face)
    reach(h, "R", T, Vector((-0.8, 0.4, -0.3)), hand)
    thigh = (h.bone_head("upperleg02.L") + h.bone_tail("upperleg02.L")) / 2 + Vector((0.0, -0.02, 0.1))
    holdL = h.bone_head("upperarm01.L") + Vector((-0.12, -0.38, -0.22))
    reach(h, "L", holdL.lerp(thigh, rest), Vector((0.7, 0.2, -1.0)), Vector((-0.1, -1, -0.35)))
    fingers_curl(h, 30, thumb=10)
    bpy.context.view_layer.update()


def place_phone(c, phase):
    """Phone between the hands while held; on the coffee table (face down) once put down."""
    h = c["h"]; ph = c["phone"]
    tl, tr = h.bone_head("finger1-2.L"), h.bone_head("finger1-2.R")
    eye = (h.eyes[0].matrix_world.to_translation() + h.eyes[1].matrix_world.to_translation()) / 2
    mid = (tl + tr) / 2
    xa = (tr - tl).normalized()                            # screen +x = his right (viewer right)
    n = (eye - mid).normalized(); n = (n - xa * n.dot(xa)).normalized()
    ya = n.cross(xa).normalized()
    if ya.dot(Vector((0, 0, 1))) < 0:                      # screen "up" points away from him / upward
        xa = -xa; ya = n.cross(xa).normalized()
    grip = phase.get("grip", 0.0)                          # 0 = typing grip, 1 = shifted up to reach Send
    held_c = mid - n * 0.016 + ya * (0.045 - 0.042 * grip)
    q_held = Matrix((xa, ya, n)).transposed().to_quaternion()
    down = phase.get("down", 0.0); placed = phase.get("placed", 0.0)
    hr = h.bone_tail("wrist.R")
    if down > 0:                          # in the right hand on the way down, then flipped onto the table
        held_c = held_c.lerp(hr + Vector((0, -0.06, 0.02)), min(1, down * 1.5))
    table_c = c["table_spot"]; q_table = Quaternion((0, 1, 0), math.pi) @ Quaternion((0, 0, 1), math.radians(12))   # face down
    loc = held_c.lerp(table_c, placed); q = q_held.slerp(q_table, placed)
    ph.location = loc; ph.rotation_mode = 'QUATERNION'; ph.rotation_quaternion = q
    bpy.context.view_layer.update()


def thumb_to(c, side, target, press):
    """Aim the thumb's distal bones at a point just above (press=0) or on (press=1) the screen."""
    h = c["h"]; n = c["screen"].matrix_world.to_3x3() @ Vector((0, 0, 1))
    tgt = target + n * (0.012 * (1 - press) + 0.0015)
    ik2(h, f"finger1-2.{side}", f"finger1-3.{side}", tgt, n)


def screen_point(c, u, v):
    """Point on the screen: u in [-1,1] across, v in [-1,1] up the screen."""
    return c["screen"].matrix_world @ Vector((u * 0.033, v * 0.072, 0.0))


# keyboard targets (u, v) for the two thumbs, and the Send button
KEYS_L = [(-0.6, -0.45), (-0.25, -0.62), (-0.45, -0.3), (-0.75, -0.6), (-0.15, -0.4)]
KEYS_R = [(0.35, -0.5), (0.65, -0.35), (0.2, -0.62), (0.55, -0.62), (0.8, -0.45)]
SEND = (0.74, 0.79)


def animate(c, sec, phase):
    if "send_reach" in phase:
        phase.setdefault("grip", ease(min(1.0, phase["send_reach"] * 1.5)))
    pose_man(c, sec, phase); place_phone(c, phase)
    typed = phase.get("typed", 1.0); sent = phase.get("sent", 0.0)
    if phase.get("down", 0) < 0.05:
        if phase.get("typing", False):          # alternate thumbs, ~6 taps a second
            k = int(sec * 6); f = (sec * 6) % 1.0; press = max(0.0, math.sin(math.pi * min(f / 0.6, 1)))
            side = "L" if k % 2 == 0 else "R"; keys = KEYS_L if side == "L" else KEYS_R
            u, v = keys[k % len(keys)]
            thumb_to(c, side, screen_point(c, u, v), press)
            o = "R" if side == "L" else "L"; ou, ov = (KEYS_R if o == "R" else KEYS_L)[(k + 2) % 5]
            thumb_to(c, o, screen_point(c, ou, ov), 0.0)
        elif "send_reach" in phase:             # right thumb travels up to Send and presses
            r = phase["send_reach"]; pr = phase.get("send_press", 0.0)
            u = -0.05 + (SEND[0] + 0.05) * r; v = -0.4 + (SEND[1] + 0.4) * r
            thumb_to(c, "R", screen_point(c, u, v), pr); thumb_to(c, "L", screen_point(c, -0.5, -0.45), 0.0)
        else:
            thumb_to(c, "R", screen_point(c, 0.4, -0.5), 0.0); thumb_to(c, "L", screen_point(c, -0.5, -0.45), 0.0)
    set_ui(c, sec, typed, sent)
    # outside life
    for o, ph_, base in c["near_trees"]:
        o.rotation_euler = (0.015 * math.sin(sec * 1.7 + ph_), 0.012 * math.sin(sec * 1.3 + ph_ * 2), 0)
    for u0, speed, parts in c["cars"]:
        p, d = road_point(c, u0 + speed * sec)
        side = Vector((-d.y, d.x, 0))
        for o, s, fwd in parts:
            o.location = p + side * s + d * fwd + Vector((0, 0, 0.6))
    # the dawn brightens through the shot sequence
    c["sky_bg"].inputs['Strength'].default_value = c["sky0"] * (1 + 0.04 * phase.get("clock", sec))


# ============================================================================ build
def build(variant=None):
    c = {}
    w = world_sky(sun_elev_deg=1.2, sun_rot_deg=0, strength=0.35, tint=(0.55, 0.66, 0.95), air=1.6, aerosol=2.5)
    bg = [n for n in w.node_tree.nodes if n.type == 'BACKGROUND'][0]; c["sky_bg"] = bg; c["sky0"] = bg.inputs['Strength'].default_value
    # ---------------------------------------------------------------- room
    oak = wood("Oak", (0.12, 0.08, 0.05), (0.26, 0.18, 0.11), scale=(0.35, 9, 9), rough=0.32, coat=0.25)
    box("Floor", (0, -0.4, -0.01), (7.4, 7.4, 0.02), oak)
    wall = plaster("Plaster", (0.52, 0.5, 0.47))
    box("WallL", (-3.7, -0.4, 1.5), (0.12, 7.4, 3.0), wall)
    box("WallR", (3.7, -0.4, 1.5), (0.12, 7.4, 3.0), wall)
    box("WallBack", (0, -4.1, 1.5), (7.4, 0.12, 3.0), wall)
    box("Ceiling", (0, -0.4, 3.02), (7.4, 7.4, 0.04), plaster("Ceil", (0.6, 0.59, 0.57)))
    frame_m = pbr("BlackSteel", (0.015, 0.015, 0.016), 0.35, 0.8)
    box("WinGlass", (0, WIN_Y, 1.5), (7.3, 0.012, 2.98), window_glass())
    for k in range(5):
        box("Mullion", (-3.65 + k * 1.825, WIN_Y, 1.5), (0.05, 0.06, 3.0), frame_m)
    box("Transom", (0, WIN_Y, 2.98), (7.4, 0.07, 0.06), frame_m); box("Sill", (0, WIN_Y, 0.02), (7.4, 0.09, 0.04), frame_m)
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 7.3; pt.size_y = 2.98; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (0, WIN_Y + 0.05, 1.5); po.rotation_euler = (math.radians(-90), 0, 0)
    # deck outside with a glass balustrade
    box("Deck", (0, WIN_Y + 2.2, -0.08), (7.4, 4.3, 0.12), wood("Deck", (0.06, 0.045, 0.035), (0.12, 0.09, 0.07), scale=(0.5, 3, 3), rough=0.6, coat=0.0))
    box("Balustrade", (0, WIN_Y + 4.3, 0.5), (7.4, 0.02, 1.0), glass("Bal", (0.9, 0.93, 0.95)))
    box("Rail", (0, WIN_Y + 4.3, 1.0), (7.4, 0.06, 0.04), frame_m)
    rug = fabric("Rug", (0.32, 0.31, 0.29), 0.95, 0.4, 700)
    box("Rug", (0, 0.6, 0.005), (3.4, 2.6, 0.012), rug)
    # ---------------------------------------------------------------- the man first (the sofa is fitted to him)
    h = man("Man"); c["h"] = h
    h.arm.location = (0.0, 1.45, 0.0); bpy.context.view_layer.update()
    pose_man(c, 0.0, {"typing": True})
    wv = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= wv[:, 2].min(); bpy.context.view_layer.update()
    c["base_loc"] = Vector(h.arm.location)
    hips_z = (h.bone_head("upperleg02.L").z + h.bone_head("upperleg02.R").z) / 2
    hips_y = h.bone_head("upperleg01.L").y
    seat_z = hips_z - 0.085
    fab = fabric("SofaFab", (0.38, 0.36, 0.33), 0.92, 0.55, 520)
    sofa(0.0, hips_y + 0.33, seat_z, fab, pbr("Walnut", (0.08, 0.05, 0.03), 0.4))
    # cushions and a throw
    for x, col in ((-0.95, (0.15, 0.2, 0.26)), (0.92, (0.5, 0.42, 0.32))):
        cu = box("Throw", (x, hips_y + 0.12, seat_z + 0.2), (0.42, 0.16, 0.42), fabric("Cush", col, 0.9, 0.5, 400), bevel=0.06,
                 rot=(math.radians(-12), 0, math.radians(8 * x)))
        s = cu.modifiers.new("s", 'SUBSURF'); s.levels = 2; s.render_levels = 2
    # coffee table, book, mug
    walnut = wood("TableWalnut", (0.05, 0.03, 0.018), (0.13, 0.08, 0.045), scale=(0.3, 10, 10), rough=0.3, coat=0.5)
    box("CoffeeTop", (0.0, 0.4, 0.4), (1.3, 0.7, 0.05), walnut, bevel=0.008)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("CoffeeLeg", (sx * 0.58, 0.4 + sy * 0.28, 0.19), (0.04, 0.04, 0.38), walnut)
    box("Book", (-0.35, 0.33, 0.44), (0.24, 0.32, 0.035), pbr("BookCover", (0.55, 0.5, 0.42), 0.7), rot=(0, 0, 0.2))
    cyl("Mug", (0.42, 0.52, 0.47), 0.045, 0.1, pbr("MugCeramic", (0.85, 0.84, 0.8), 0.25, 0.0, **{'Coat Weight': 0.6}), verts=32)
    c["table_spot"] = Vector((0.12, 0.3, 0.429))
    floor_lamp((1.55, 1.75))
    bookshelf(-3.45, -1.0, wood("ShelfOak", (0.12, 0.08, 0.05), (0.22, 0.15, 0.09), rough=0.4, coat=0.2))
    plant((-1.7, 1.95))
    # abstract framed print on the right wall
    box("Frame", (3.62, -1.2, 1.6), (0.03, 1.1, 0.8), frame_m)
    box("Print", (3.6, -1.2, 1.6), (0.01, 1.0, 0.7), pbr("Print", (0.62, 0.6, 0.56), 0.9))
    # ---------------------------------------------------------------- the phone
    phone = box("Phone", (0, 0, 0), (0.072, 0.152, 0.008), pbr("PhoneBody", (0.02, 0.02, 0.022), 0.25, 0.8), bevel=0.006)
    sm = screen_material(); c["screen_mat"] = sm
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.0041)); scr = bpy.context.active_object; scr.name = "Screen"
    scr.scale = (0.066, 0.144, 1); bpy.ops.object.transform_apply(scale=True); scr.data.materials.append(sm)
    scr.parent = phone
    sl = bpy.data.lights.new("ScreenLight", 'AREA'); sl.energy = 0.5; sl.size = 0.07; sl.color = (0.8, 0.88, 1.0)
    so = bpy.data.objects.new("ScreenLight", sl); bpy.context.collection.objects.link(so); so.parent = phone; so.location = (0, 0, 0.012)
    so.visible_camera = False; so.visible_glossy = False
    c.update(phone=phone, screen=scr, screen_light=sl)
    # ---------------------------------------------------------------- outside
    landscape(c); trees(c); road_and_car(c)
    # soft cool fill from the window side for the jacket's rim, very low
    f = area_light((0.0, WIN_Y - 0.4, 2.2), (0, 0, 0), 3.0, 18, (0.6, 0.72, 1.0)); point_at(f, (0, 1.4, 1.0)); f.visible_camera = False; f.visible_glossy = False
    animate(c, 0.0, {"typing": True, "typed": 0.3})
    return c


# ============================================================================ moves
def _chest(c):
    return (c["h"].bone_head("spine03") + c["h"].bone_head("neck01")) / 2


def anim_wide(c, t):
    s = t * DUR["wide"]
    typing = 0.8 < s < 2.0
    animate(c, s, {"typing": typing, "typed": min(1.0, 0.45 + 0.55 * max(0, (s - 0.8) / 1.2)), "clock": s})


def anim_shoulder(c, t):
    s = t * DUR["shoulder"]
    if s < 1.4:
        animate(c, 3.0 + s, {"typing": True, "typed": 0.82 + 0.18 * s / 1.4, "clock": 3 + s})
    else:
        r = ease(min(1.0, (s - 1.4) / 1.0))
        animate(c, 3.0 + s, {"typing": False, "send_reach": r, "typed": 1.0, "clock": 3 + s})


def anim_thumb(c, t):
    s = t * DUR["thumb"]
    pr = max(0.0, math.sin(math.pi * min(s / 0.5, 1.0))) if s < 0.5 else 0.0
    animate(c, 5.4 + s, {"send_reach": 1.0, "send_press": pr, "typed": 1.0, "sent": max(0.0, (s - 0.35) / 0.85), "clock": 5.4 + s})


def anim_side(c, t):
    s = t * DUR["side"]
    down = ease(min(1.0, s / 0.7)); placed = ease(min(1.0, max(0.0, (s - 0.35) / 0.6)))
    back = ease(min(1.0, max(0.0, (s - 0.9) / 1.0))); face = ease(min(1.0, max(0.0, (s - 1.3) / 0.8)))
    animate(c, 6.6 + s, {"down": down * (1 - face), "placed": placed, "back": back, "face": face,
                         "left_rest": min(1.0, down * 1.4), "typed": 1.0, "sent": 1.0, "clock": 6.6 + s})


def cam_wide(c, t):
    e = ease(t)
    loc = Vector((0.75, -3.4, 1.22)).lerp(Vector((0.45, -2.7, 1.18)), e)
    return (loc, Vector((0.1, 1.3, 0.95)), 35)


def cam_shoulder(c, t):
    sh = c["h"].bone_head("upperarm01.R")
    ph = c["phone"].location
    loc = sh + Vector((-0.18, 0.26, 0.34)) + Vector((0.015 * math.sin(t * 7), -0.05 * ease(t), -0.04 * ease(t)))
    return (loc, ph, 50)


def cam_thumb(c, t):
    ph = c["phone"].location; n = c["phone"].matrix_world.to_3x3() @ Vector((0, 0, 1))
    up = c["phone"].matrix_world.to_3x3() @ Vector((0, 1, 0)); side = c["phone"].matrix_world.to_3x3() @ Vector((1, 0, 0))
    tgt = screen_point(c, *SEND)
    loc = tgt + n * (0.2 - 0.02 * t) + up * 0.1 + side * 0.025
    return (loc, tgt - up * 0.02, 60, up)


def cam_side(c, t):
    e = ease(t)
    loc = Vector((2.9, 0.15, 1.05)).lerp(Vector((2.7, 0.55, 1.05)), e)
    return (loc, Vector((0.05, 1.05, 0.75)), 40)


MOVES = {
    "wide": dict(kind="anim", dof=4.0, far=60.0, cam=cam_wide, focus=lambda c, t: _chest(c), anim=anim_wide),
    "shoulder": dict(kind="anim", dof=2.0, far=8.0, cam=cam_shoulder, focus=lambda c, t: c["phone"].location, anim=anim_shoulder),
    "thumb": dict(kind="anim", dof=2.0, far=2.0, cam=cam_thumb, focus=lambda c, t: screen_point(c, *SEND), anim=anim_thumb),
    "side": dict(kind="anim", dof=2.8, far=20.0, cam=cam_side, focus=lambda c, t: _chest(c), anim=anim_side),
}
