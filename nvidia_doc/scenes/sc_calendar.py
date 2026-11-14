"""CH4 7D redo (199 f): a wall calendar, November 2026, morning light through a window (soft bar shadows across the
wall). Days 8, 9, 10 and 11 get crossed out in red one by one (each stroke draws itself), then a red circle closes
around the 12th. In the foreground, out of focus on a desk, a phone lights up. Slow push. Nobody in frame."""
import os, math
import bpy
from mathutils import Vector, Matrix
from PIL import Image, ImageDraw, ImageFont
from kit import *
from common import area_light, world_flat

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "assets", "generated")
EXPOSURE = 0.0
FRAMES = {"calendar": 199}
CW, CH_ = 0.42, 0.56                       # calendar sheet size (m)
WALL_Y = 1.0
CAL_C = Vector((0.0, WALL_Y - 0.012, 1.45))
FIRST_WD = 6                               # 1 Nov 2026 is a Sunday (columns Mon..Sun)


def calendar_image(path, W=1200, H=1600):
    im = Image.new("RGB", (W, H), (246, 244, 238)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 640], fill=(70, 92, 110))                      # a plain photo band (generic landscape tones)
    d.polygon([(0, 640), (0, 430), (260, 300), (520, 420), (800, 260), (1200, 470), (1200, 640)], fill=(52, 70, 84))
    d.polygon([(0, 640), (0, 560), (400, 470), (820, 560), (1200, 500), (1200, 640)], fill=(38, 52, 62))
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 76)
    fn = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
    fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    d.text((W / 2, 715), "NOVEMBER 2026", fill=(40, 40, 44), font=fb, anchor="mm")
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    gx0, gy0, cw, ch = 60, 800, (W - 120) / 7, 125
    for k, dn in enumerate(days):
        d.text((gx0 + cw * (k + 0.5), gy0), dn, fill=(170, 60, 50) if k == 6 else (90, 90, 95), font=fs, anchor="mm")
    cells = {}
    for day in range(1, 31):
        idx = FIRST_WD + day - 1; col, row = idx % 7, idx // 7
        cx, cy = gx0 + cw * (col + 0.5), gy0 + 75 + ch * (row + 0.5)
        d.rectangle([gx0 + cw * col + 4, cy - ch / 2 + 4, gx0 + cw * (col + 1) - 4, cy + ch / 2 - 4], outline=(220, 218, 212), width=2)
        d.text((cx, cy), str(day), fill=(170, 60, 50) if col == 6 else (45, 45, 50), font=fn, anchor="mm")
        cells[day] = (cx / W, cy / H)
    im.save(path)
    return path, cells


def uv_to_world(u, v):
    return CAL_C + Vector(((u - 0.5) * CW, -0.003, (0.5 - v) * CH_))


def build(variant=None):
    c = {}
    os.makedirs(GEN, exist_ok=True)
    world_flat((0.02, 0.022, 0.026), 1.0)
    wall = pbr("Wall", (0.55, 0.53, 0.5), 0.9)
    box("Wall", (0, WALL_Y + 0.05, 1.5), (6, 0.1, 3.0), wall)
    box("Floor", (0, -1, -0.01), (6, 6, 0.02), wood("Floor", (0.12, 0.08, 0.05), (0.22, 0.15, 0.09), scale=(0.4, 8, 8), rough=0.4))
    path, cells = calendar_image(os.path.join(GEN, "calendar_nov2026.png"))
    m = bpy.data.materials.new("Calendar"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; t_ = N.new("ShaderNodeTexImage"); t_.image = bpy.data.images.load(path)
    L.new(t_.outputs['Color'], N["Principled BSDF"].inputs['Base Color']); N["Principled BSDF"].inputs['Roughness'].default_value = 0.75
    bpy.ops.mesh.primitive_plane_add(size=1, location=CAL_C, rotation=(math.radians(90), 0, 0))
    cal = bpy.context.active_object; cal.name = "CalendarSheet"; cal.scale = (CW, CH_, 1); cal.data.materials.append(m)
    box("Backing", CAL_C + Vector((0, 0.004, 0)), (CW + 0.01, 0.004, CH_ + 0.01), pbr("Backing", (0.3, 0.3, 0.3), 0.7))
    cyl("Nail", CAL_C + Vector((0, -0.005, CH_ / 2 + 0.02)), 0.004, 0.02, pbr("Nail", (0.5, 0.5, 0.5), 0.3, 1.0), verts=8, rot=(math.radians(90), 0, 0))
    # red marker strokes: two per crossed day (they draw themselves); a ring for the 12th
    ink = pbr("RedInk", (0.62, 0.03, 0.03), 0.5)
    cw, chh = CW * (1080 / 7) / 1200, CH_ * 125 / 1600
    strokes = []
    for day in (8, 9, 10, 11):
        p = uv_to_world(*cells[day])
        for k, ang in enumerate((math.radians(35), math.radians(-35))):
            s = box(f"X{day}_{k}", (0, 0, 0), (1.0, 0.0015, 0.0085), ink)
            s.data.transform(Matrix.Translation((0.5, 0, 0)))                          # grows from its start point
            L_ = math.hypot(cw, chh) * 0.85
            start = p + Vector((-math.cos(ang) * L_ / 2, 0, -math.sin(ang) * L_ / 2 if k == 0 else math.sin(-ang) * L_ / 2))
            s.location = p + Vector((-L_ / 2 * math.cos(ang), 0, -L_ / 2 * math.sin(ang)))
            s.rotation_euler = (0, -ang, 0); s.scale = (0.0001, 1, 1)
            strokes.append((s, L_))
    c["strokes"] = strokes
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.09, major_segments=64, minor_segments=8,
                                     location=uv_to_world(*cells[12]), rotation=(math.radians(90), 0, 0))
    ring = bpy.context.active_object; ring.name = "Circle12"; ring.data.materials.append(ink)
    ring.scale = (0.0001, 0.0001, 0.0001); c["ring"] = ring; c["ring_r"] = (cw * 0.5, chh * 0.55)
    # the window: warm low sun through a 4-pane frame off-screen left (soft bar shadows over the wall)
    sun_ = bpy.data.lights.new("Morning", 'SUN'); sun_.energy = 4.0; sun_.color = (1.0, 0.8, 0.58); sun_.angle = math.radians(7.0)
    so = bpy.data.objects.new("Morning", sun_); bpy.context.collection.objects.link(so)
    so.location = (-3.0, -3.2, 2.4); point_at(so, (0.2, WALL_Y, 1.3)); c["sun"] = so
    fr = pbr("Frame", (0.1, 0.1, 0.1), 0.6)
    for x in (-3.0, -2.2, -1.4):
        box("WinBar", (x, -1.6, 1.6), (0.08, 0.08, 3.0), fr).visible_camera = False
    for z in (0.3, 1.5, 2.7):
        box("WinBarH", (-2.2, -1.6, z), (1.7, 0.08, 0.08), fr).visible_camera = False
    box("WinWallL", (-4.2, -1.6, 1.5), (2.4, 0.1, 3.0), fr).visible_camera = False
    area_light((0.8, -2.0, 2.2), (0, 0, 0), 2.0, 30, (0.7, 0.8, 1.0)).visible_camera = False
    # foreground desk with a phone that lights up (frame driver), out of focus
    box("Desk", (0.15, -0.55, 1.22), (1.2, 0.6, 0.04), wood("Desk", (0.06, 0.04, 0.025), (0.14, 0.09, 0.05), scale=(6, 0.35, 0.35), rough=0.3))
    box("Phone", (0.32, -0.27, 1.205), (0.075, 0.155, 0.008), pbr("PhoneBody", (0.02, 0.02, 0.022), 0.3), bevel=0.004, rot=(0, 0, 0.25))
    pm = bpy.data.materials.new("PhoneScreen"); pm.use_nodes = True
    n_ = pm.node_tree.nodes; l_ = pm.node_tree.links; n_.clear(); o_ = n_.new("ShaderNodeOutputMaterial"); em = n_.new("ShaderNodeEmission")
    em.inputs['Color'].default_value = (0.75, 0.85, 1.0, 1); v = n_.new("ShaderNodeValue")
    dd = v.outputs[0].driver_add("default_value").driver; dd.type = 'SCRIPTED'; dd.expression = "4.0 * min(1, max(0, (frame - 150) / 6))"
    l_.new(v.outputs[0], em.inputs['Strength']); l_.new(em.outputs[0], o_.inputs['Surface'])
    box("PhoneScreen", (0.32, -0.27, 1.2095), (0.068, 0.145, 0.001), pm, rot=(0, 0, 0.25))
    nm = bpy.data.materials.new("Notif"); nm.use_nodes = True                  # a stack of notification cards (blurred, unreadable)
    nn = nm.node_tree.nodes; nl = nm.node_tree.links; nn.clear(); no = nn.new("ShaderNodeOutputMaterial"); ne = nn.new("ShaderNodeEmission")
    ne.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1); nv = nn.new("ShaderNodeValue")
    nd = nv.outputs[0].driver_add("default_value").driver; nd.type = 'SCRIPTED'; nd.expression = "7.0 * min(1, max(0, (frame - 156) / 6))"
    nl.new(nv.outputs[0], ne.inputs['Strength']); nl.new(ne.outputs[0], no.inputs['Surface'])
    import mathutils
    for k in range(4):
        off = mathutils.Matrix.Rotation(0.25, 3, 'Z') @ mathutils.Vector((0, 0.045 - k * 0.026, 0))
        box("Notif", (0.32 + off.x, -0.27 + off.y, 1.2102), (0.06, 0.02, 0.0005), nm, rot=(0, 0, 0.25))
    rig = bpy.data.objects.new("PhoneRig", None); bpy.context.collection.objects.link(rig)   # tilt the phone
    rig.location = (0.32, -0.27, 1.205); bpy.context.view_layer.update()                   # toward the lens so
    for o in [o for o in bpy.data.objects if o.name.startswith(("Phone", "Notif")) and o is not rig]:   # the glow reads
        mw = o.matrix_world.copy(); o.parent = rig; o.matrix_world = mw
    rig.location = (0.24, -0.33, 1.25); rig.rotation_euler = (0, 0, 0)      # flat on the desk's far edge
    cyl("Mug", (-0.2, -0.45, 1.29), 0.04, 0.1, pbr("Mug", (0.6, 0.6, 0.6), 0.3), verts=24)
    c["cal"] = CAL_C
    return c


def anim(c, t):
    f = 1 + t * (FRAMES["calendar"] - 1)
    so = c["sun"]                                           # the morning light slides across the wall
    so.location = (-3.0 + 0.9 * t, -3.2, 2.4 + 0.35 * t); point_at(so, (0.2, WALL_Y, 1.3))
    for k, (s, L_) in enumerate(c["strokes"]):
        day, stroke = k // 2, k % 2
        t0 = 18 + day * 30 + stroke * 8                     # each day: two strokes, 8 frames apart; days 30 frames apart
        u = min(1.0, max(0.0, (f - t0) / 7.0))
        s.scale = (max(0.0001, L_ * u), 1, 1)
    u = min(1.0, max(0.0, (f - 145) / 16.0))                # the circle around the 12th closes
    rx, rz = c["ring_r"]
    s_ = max(0.0001, u)
    c["ring"].scale = (rx * s_, rz * s_, rx * s_)
    c["ring"].rotation_euler = (math.radians(90), 0, 0)


MOVES = {"calendar": dict(kind="anim", dof=2.0, far=8.0, anim=anim,
                          cam=lambda c, t: (Vector((0.08, -1.15, 1.32)).lerp(Vector((0.04, -0.85, 1.34)), ease(t)), CAL_C + Vector((0.06, 0, -0.12)), 40),
                          focus=lambda c, t: CAL_C)}
