"""HERO SET / THE BANKER'S OFFICE, Moscow 1995 (dramatization). Wood panelling, net curtains on the left windows,
a steel desk with a green blotter, a small CRT, a dark wood cabinet, a steel filing cabinet and, at the centre, the
beige push-button phone with its white handset. A faint stain sits on the handset near the earpiece.

Variants
  empty   : overcast daylight, nobody there, the chair pushed back (Intro 1A/1B)
  search  : overcast daylight, two investigators in coats search the drawers and files (Intro 3A/3B)
  (later) day / sealed / anteroom / dust for Chapters 1-3
"""
import os, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from kit import *
from pbkit import joinm
from human import Human, add_asset, reset_pose, fingers_curl, pose_walk, _world_verts, reach
import ph

EXPOSURE = 1.4
BOUNCES = 8
# seconds per shot (estimates at 125 wpm until the voiceover arrives; 1A includes the 2.5 s lead-in)
DUR = {"handset": 7.8, "empty": 9.0, "search": 6.5, "find": 5.0}
VARIANT_FOR = {"handset": "empty", "empty": "empty", "search": "search", "find": "search"}

ROOM_X, ROOM_Y0, ROOM_Y1, ROOM_H = 3.2, -3.0, 3.0, 3.1
DESK = Vector((0.0, 1.15, 0.0))          # desk centre; the banker's side is +Y (his back to the cabinet)
TOP_Z = 0.79                              # desk top
PHONE = Vector((-0.55, 0.92, TOP_Z))      # front-left corner of the desk as seen from the visitor's chair
PHONE_ROT = math.radians(180 + 24)
FILE_X, FILE_Y = ROOM_X - 0.27, -0.3           # steel filing unit on the right wall, between the door and the cabinet        # keypad turned toward the banker's chair, angled to his right hand
rng = np.random.default_rng(1995)


# ============================================================================ materials
def plastic(name, col, rough=0.38, coat=0.0):
    return pbr(name, col, rough, 0.0, **{'Coat Weight': coat, 'Coat Roughness': 0.2, 'Specular IOR Level': 0.5})


def handset_material():
    """White phone plastic, yellowed a touch with age, with a faint stain near the earpiece: slightly darker,
    warmer and glossier in an irregular patch (object space, so it stays put when the handset moves)."""
    m = bpy.data.materials.new("HandsetPlastic"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    # distance from the stain centre (on the ear cup, upper face), squashed into an ellipse
    mp = N.new("ShaderNodeMapping"); mp.inputs['Location'].default_value = (0.0, -0.0616, -0.0165); mp.inputs['Scale'].default_value = (1.3, 0.8, 1.6)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    wob = N.new("ShaderNodeTexNoise"); wob.inputs['Scale'].default_value = 60; wob.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], wob.inputs['Vector'])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(mp.outputs[0], ln.inputs[0])
    jit = N.new("ShaderNodeMath"); jit.operation = 'MULTIPLY_ADD'; jit.inputs[1].default_value = 0.014
    L.new(wob.outputs['Fac'], jit.inputs[0]); L.new(ln.outputs['Value'], jit.inputs[2])
    mask = N.new("ShaderNodeMapRange"); mask.inputs['From Min'].default_value = 0.034; mask.inputs['From Max'].default_value = 0.014
    L.new(jit.outputs[0], mask.inputs['Value'])
    # fine mottling inside the patch (a dried film, not a blot)
    mot = N.new("ShaderNodeTexNoise"); mot.inputs['Scale'].default_value = 420; mot.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], mot.inputs['Vector'])
    mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; L.new(mask.outputs[0], mm.inputs[0]); L.new(mot.outputs['Fac'], mm.inputs[1])
    mk = N.new("ShaderNodeMath"); mk.operation = 'MULTIPLY'; mk.inputs[1].default_value = 1.6; mk.use_clamp = True
    L.new(mm.outputs[0], mk.inputs[0])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'
    col.inputs[6].default_value = (0.80, 0.78, 0.72, 1); col.inputs[7].default_value = (0.56, 0.48, 0.33, 1)
    L.new(mk.outputs[0], col.inputs['Factor']); L.new(col.outputs[2], p.inputs['Base Color'])
    rg = N.new("ShaderNodeMix"); rg.data_type = 'FLOAT'; rg.inputs[2].default_value = 0.36; rg.inputs[3].default_value = 0.12
    L.new(mask.outputs[0], rg.inputs['Factor']); L.new(rg.outputs[0], p.inputs['Roughness'])
    p.inputs['Coat Weight'].default_value = 0.15; p.inputs['Subsurface Weight'].default_value = 0.05
    return m


def net_curtain(name):
    """Sheer net: translucent white with a fine woven pattern of tiny holes."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    ck = N.new("ShaderNodeTexChecker"); ck.inputs['Scale'].default_value = 900; L.new(tc.outputs['UV'], ck.inputs['Vector'])
    tl = N.new("ShaderNodeBsdfTranslucent"); tl.inputs['Color'].default_value = (0.95, 0.95, 0.92, 1)
    df = N.new("ShaderNodeBsdfDiffuse"); df.inputs['Color'].default_value = (0.8, 0.8, 0.77, 1)
    tr = N.new("ShaderNodeBsdfTransparent")
    m1 = N.new("ShaderNodeMixShader"); m1.inputs[0].default_value = 0.5; L.new(tl.outputs[0], m1.inputs[1]); L.new(df.outputs[0], m1.inputs[2])
    fac = N.new("ShaderNodeMath"); fac.operation = 'MULTIPLY_ADD'; fac.inputs[1].default_value = 0.12; fac.inputs[2].default_value = 0.74
    L.new(ck.outputs['Fac'], fac.inputs[0])
    m2 = N.new("ShaderNodeMixShader"); L.new(fac.outputs[0], m2.inputs[0]); L.new(tr.outputs[0], m2.inputs[1]); L.new(m1.outputs[0], m2.inputs[2])
    L.new(m2.outputs[0], out.inputs['Surface'])
    return m


def wallpaper(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (14, 14, 14); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.inputs['Scale'].default_value = 1.0; wv.inputs['Distortion'].default_value = 0.0
    L.new(mp.outputs[0], wv.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.5, 0.47, 0.4, 1); cr.color_ramp.elements[1].color = (0.56, 0.53, 0.46, 1)
    L.new(wv.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85
    return m


def retint(root_meshes, mul, rough_add=0.0):
    """Multiply every material on a scanned asset by a colour (copies the materials)."""
    done = {}
    for o in root_meshes:
        for i, ms in enumerate(o.material_slots):
            mt = ms.material
            if mt is None or "glass" in mt.name.lower():
                continue
            if mt.name not in done:
                c = mt.copy(); N = c.node_tree.nodes; L = c.node_tree.links; p = N.get("Principled BSDF")
                if p:
                    src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].is_linked else None
                    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
                    if src:
                        L.new(src, mx.inputs[6])
                    else:
                        mx.inputs[6].default_value = p.inputs['Base Color'].default_value
                    mx.inputs[7].default_value = (*mul, 1); L.new(mx.outputs[2], p.inputs['Base Color'])
                done[mt.name] = c
            o.material_slots[i].material = done[mt.name]


# ============================================================================ the telephone
def _wedge(name, w, d, h_back, h_front, mat, bevel=0.006, segs=3):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object; o.name = name
    for v in o.data.vertices:
        v.co.x *= w; v.co.y *= d
        v.co.z = (0.0 if v.co.z < 0 else (h_back if v.co.y > 0 else h_front))
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("b", 'BEVEL'); b.width = bevel; b.segments = segs
    for p_ in o.data.polygons:
        p_.use_smooth = True
    return o


HS_L = 0.215                                   # handset length


def _hs_profile(s):
    """Handset shape along its length s in [0,1] (0 = mouthpiece, 1 = earpiece): width, top z, bottom z."""
    cup = math.exp(-((s - 0.1) / 0.1) ** 2) + math.exp(-((s - 0.9) / 0.1) ** 2)
    r = max(0.0, 1 - abs(2 * s - 1) ** 10) ** 0.18          # rounded ends
    w = (0.036 + 0.018 * cup) * r
    top = 0.006 + 0.009 * (1 - (2 * s - 1) ** 2)              # gently bowed
    bot = top - (0.021 + 0.019 * cup)
    mid = (top + bot) / 2; h = (top - bot) * r
    return w, mid + h / 2, mid - h / 2


def handset_mesh(name, mat, n_len=64, n_ring=28, ex=3.2):
    verts, faces = [], []
    for i in range(n_len + 1):
        s = i / n_len; y = -HS_L / 2 + s * HS_L
        w, top, bot = _hs_profile(s); mid = (top + bot) / 2; hh = (top - bot) / 2
        for k in range(n_ring):
            a = 2 * math.pi * k / n_ring; ca, sa = math.cos(a), math.sin(a)
            x = w / 2 * math.copysign(abs(ca) ** (2 / ex), ca); z = mid + hh * math.copysign(abs(sa) ** (2 / ex), sa)
            verts.append((x, y, z))
    for i in range(n_len):
        for k in range(n_ring):
            a = i * n_ring + k; b = i * n_ring + (k + 1) % n_ring
            faces.append((a, b, b + n_ring, a + n_ring))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    me.materials.append(mat)
    for p_ in me.polygons:
        p_.use_smooth = True
    sub = o.modifiers.new("s", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    return o


def telephone():
    """A 1990s office push-button phone: soft beige wedge base with the white handset lying lengthwise on the
    left and a 4 x 3 keypad on the right. Keypad toward -Y, base on z = 0. The handset's earpiece is at the back (+Y).
    Returns (root, handset, base)."""
    beige = plastic("PhoneBeige", (0.56, 0.51, 0.42), 0.45)
    dark = plastic("PhoneDark", (0.09, 0.085, 0.08), 0.45)
    keycap = plastic("KeyCap", (0.74, 0.71, 0.64), 0.35)
    ink = pbr("KeyInk", (0.05, 0.05, 0.05), 0.5)
    rubber = pbr("PhoneRubber", (0.03, 0.03, 0.03), 0.8)
    root = bpy.data.objects.new("Telephone", None); bpy.context.collection.objects.link(root)
    W, D, HB, HF = 0.205, 0.225, 0.072, 0.03
    slope = math.atan2(HB - HF, D)
    topz = lambda y: HF + (y + D / 2) / D * (HB - HF)
    base = _wedge("PhoneBase", W, D, HB, HF, beige, bevel=0.016, segs=5)
    parts = [base]
    # a shallow cradle channel on the left: two raised saddles the handset cups sit in
    for y in (-0.072, 0.072):
        sd = box("Saddle", (-0.046, y, topz(y) + 0.004), (0.06, 0.045, 0.016), beige, bevel=0.007, rot=(slope, 0, 0))
        sd.modifiers["bevel"].segments = 4
        parts.append(sd)
    parts.append(box("HookSwitch", (-0.046, 0.032, topz(0.032) + 0.006), (0.018, 0.012, 0.012), dark, bevel=0.002, rot=(slope, 0, 0)))
    # keypad: 4 x 3 keys with their digits, two function keys, a small display strip
    labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
    for r in range(4):
        for k in range(3):
            x = 0.022 + k * 0.026; y = 0.0 - r * 0.024
            z = topz(y) + 0.0035
            parts.append(box("Key", (x, y, z), (0.02, 0.017, 0.006), keycap, bevel=0.0025, rot=(slope, 0, 0)))
            parts.append(text_obj("KeyNum", labels[r * 3 + k], (x, y - 0.002, z + 0.0032), 0.008, ink, rot=(slope, 0, 0), extrude=0.0))
    for r in range(3):
        y = 0.0 - r * 0.024
        parts.append(box("FnKey", (0.06 + 0.035, y, topz(y) + 0.003), (0.008, 0.016, 0.005), dark, bevel=0.002, rot=(slope, 0, 0)))
    parts.append(box("Display", (0.048, 0.045, topz(0.045) + 0.0012), (0.07, 0.028, 0.002), dark, rot=(slope, 0, 0)))
    parts.append(box("Speaker", (0.048, 0.082, topz(0.082) + 0.0008), (0.07, 0.02, 0.0015), dark, rot=(slope, 0, 0)))
    for sx in (-0.08, 0.08):
        for sy in (-0.09, 0.09):
            parts.append(cyl("Foot", (sx, sy, 0.002), 0.008, 0.004, rubber, verts=12))
    body = joinm(parts, "PhoneBody"); body.parent = root
    # handset (loft), resting in the saddles, tilted with the slope
    hm = handset_material()
    hs = handset_mesh("Handset", hm)
    plug_y = -HS_L / 2 + 0.76 * HS_L; _, ptop, _ = _hs_profile(0.76)
    plug = cyl("RubberPlug", (0.0, plug_y, ptop + 0.0004), 0.0042, 0.0016, pbr("Plug", (0.06, 0.06, 0.06), 0.7), verts=20)
    plug.parent = hs
    grille = cyl("Grille", (0.0, -HS_L / 2 + 0.1 * HS_L, _hs_profile(0.1)[2] - 0.0003), 0.016, 0.001, dark, verts=24); grille.parent = hs
    hs.parent = root
    _, _, cupbot = _hs_profile(0.1)
    hs.location = (-0.046, 0.0, topz(0.0) + 0.006 - cupbot)
    hs.rotation_euler = (slope, 0, 0)
    return root, hs, body


def coiled_cord(name, pts, radius=0.0055, pitch=0.0042, wire=0.0016, mat=None):
    """A coiled cord along a smooth path through `pts` (world points)."""
    P = [Vector(p) for p in pts]
    # Catmull-Rom resample
    path = []
    for i in range(len(P) - 1):
        p0 = P[max(i - 1, 0)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[min(i + 2, len(P) - 1)]
        for k in range(40):
            t = k / 40
            path.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    path.append(P[-1])
    L = [0.0]
    for a, b in zip(path, path[1:]):
        L.append(L[-1] + (b - a).length)
    total = L[-1]; n = int(total / pitch * 14)
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = wire; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(n - 1)
    j = 0; up = Vector((0, 0, 1))
    for i in range(n):
        s = total * i / (n - 1)
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        f = (s - L[j]) / max(L[j + 1] - L[j], 1e-9)
        c = path[j].lerp(path[j + 1], f); tng = (path[j + 1] - path[j]).normalized()
        a = tng.cross(up)
        if a.length < 1e-4:
            a = tng.cross(Vector((1, 0, 0)))
        a.normalize(); b = tng.cross(a)
        ang = 2 * math.pi * s / pitch
        q = c + (a * math.cos(ang) + b * math.sin(ang)) * radius
        sp.points[i].co = (q.x, q.y, q.z, 1)
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o)
    if mat:
        cu.materials.append(mat)
    return o


# ============================================================================ people
def person(name, gender, years, cloth, hair, cval=0.25, hv=0.3, hue=0.5, sat=1.0, skin=None):
    h = Human(name, gender=gender, years=years, muscle=0.5, weight=0.5, height=0.5, eyelashes="eyelashes01",
              skin=skin or ("middleage_lightskinned_female_diffuse.png" if gender < 0.5 else "middleage_lightskinned_male_diffuse.png"))
    add_asset(h, "clothes", cloth, val=cval, hue=hue, sat=sat, rough=0.7)
    add_asset(h, "clothes", "shoes02", val=0.15, rough=0.4)
    add_asset(h, "hair", hair, val=hv, rough=0.45)
    return h


def stand(h, loc, face_z):
    """Standing, legs straight, arms relaxed. face_z: rotation about Z (0 = facing -Y; theta faces (sin, -cos)).
    Posed in the rest orientation first (bone rotations use world axes), then turned and placed."""
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); bpy.context.view_layer.update()
    pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    for sd in ("L", "R"):
        for b in (f"upperleg01.{sd}", f"lowerleg01.{sd}", f"foot.{sd}"):
            h.arm.pose.bones[b].matrix_basis = Matrix.Identity(4)
    h.rot("spine05", (1, 0, 0), 6)                           # undo the walk's lean back
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = loc; bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()


def _fwd(h):
    return (h.arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def nod(h, bone, deg):
    """Bend a spine/neck/head bone forward (down) by deg, whichever way the person faces."""
    f = _fwd(h); h.rot(bone, Vector((0, 0, 1)).cross(f).normalized(), deg)


# ============================================================================ build
def build(variant="empty"):
    variant = variant or "empty"
    c = {"variant": variant}
    night = False                                  # every office variant so far is daytime
    if night:
        world_flat((0.025, 0.04, 0.075), 1.0)                     # blue hour outside
    else:
        world_sky(sun_elev_deg=24, sun_rot_deg=200, strength=0.35, tint=(0.82, 0.88, 1.0))   # overcast-ish summer day
    # ---------------------------------------------------------------- room shell
    floor = ph.texture("herringbone_parquet", scale=0.7)
    box("Floor", (0, 0, -0.01), (2 * ROOM_X, ROOM_Y1 - ROOM_Y0, 0.02), floor)
    rug = fabric("Rug", (0.11, 0.035, 0.028), 0.95, 0.4, 500)
    box("Rug", (0, 0.2, 0.002), (3.6, 2.6, 0.006), rug)
    panel = wood("Panel", (0.07, 0.035, 0.018), (0.2, 0.11, 0.055), scale=(0.25, 5, 5), rough=0.4, coat=0.35)
    paper = wallpaper("Wallpaper")
    ceil = pbr("Ceiling", (0.62, 0.6, 0.56), 0.9)
    box("Ceiling", (0, 0, ROOM_H + 0.02), (2 * ROOM_X, ROOM_Y1 - ROOM_Y0, 0.04), ceil)
    # back wall (+Y): panelling to 1.1 m, wallpaper above, a picture rail
    for (nm, x0, x1) in (("Back", -ROOM_X, ROOM_X),):
        box("WallBackLow", (0, ROOM_Y1 + 0.05, 0.55), (2 * ROOM_X, 0.1, 1.1), panel)
        box("WallBackHigh", (0, ROOM_Y1 + 0.05, 2.1), (2 * ROOM_X, 0.1, 2.0), paper)
        box("Rail", (0, ROOM_Y1 - 0.01, 1.11), (2 * ROOM_X, 0.03, 0.05), panel)
    for k in range(7):                                             # panel stiles
        box("Stile", (-ROOM_X + 0.45 + k * 0.92, ROOM_Y1 - 0.005, 0.55), (0.05, 0.02, 1.05), panel)
    # front wall (-Y), behind the camera mostly
    box("WallFront", (0, ROOM_Y0 - 0.05, ROOM_H / 2), (2 * ROOM_X, 0.1, ROOM_H), paper)
    box("WallFrontLow", (0, ROOM_Y0 + 0.005, 0.55), (2 * ROOM_X, 0.02, 1.1), panel)
    # right wall (+X): panelled, with the door to the ante-room at y = -1.6
    door_y = -1.6
    for (y0, y1) in ((ROOM_Y0, door_y - 0.5), (door_y + 0.5, ROOM_Y1)):
        box("WallR", (ROOM_X + 0.05, (y0 + y1) / 2, ROOM_H / 2), (0.1, y1 - y0, ROOM_H), paper)
        box("WallRLow", (ROOM_X - 0.005, (y0 + y1) / 2, 0.55), (0.02, y1 - y0, 1.1), panel)
    box("WallROver", (ROOM_X + 0.05, door_y, 2.6), (0.1, 1.0, 1.0), paper)
    frame_m = wood("DoorFrame", (0.06, 0.03, 0.015), (0.16, 0.09, 0.045), scale=(0.25, 5, 5), rough=0.4, coat=0.4)
    for dy in (-0.53, 0.53):
        box("DoorJamb", (ROOM_X, door_y + dy, 1.05), (0.16, 0.07, 2.1), frame_m)
    box("DoorHead", (ROOM_X, door_y, 2.13), (0.16, 1.13, 0.07), frame_m)
    # the door leaf: hinged on the far jamb, ajar
    leaf = join([box("Leaf", (0, 0.5, 1.03), (0.05, 0.96, 2.04), frame_m, bevel=0.004),
                 box("LeafPanelU", (-0.028, 0.5, 1.5), (0.01, 0.7, 0.75), panel),
                 box("LeafPanelL", (-0.028, 0.5, 0.5), (0.01, 0.7, 0.7), panel),
                 cyl("Knob", (-0.06, 0.88, 1.0), 0.025, 0.05, pbr("Brass", (0.55, 0.42, 0.2), 0.3, 1.0), verts=16, rot=(0, math.radians(90), 0))], "DoorLeaf")
    leaf.location = (ROOM_X + 0.02, door_y - 0.5, 0.0)
    c["door"] = leaf
    leaf.rotation_euler = (0, 0, math.radians(-25 if not night else -70))
    # ante-room glimpsed through the door: a lit corridor wall
    box("AnteWall", (ROOM_X + 2.0, door_y, 1.5), (0.1, 3.0, 3.0), pbr("AnteWall", (0.5, 0.48, 0.42), 0.85))
    box("AnteFloor", (ROOM_X + 1.0, door_y, -0.01), (2.0, 3.0, 0.02), floor)
    ante = area_light((ROOM_X + 1.0, door_y, 2.9), (0, 0, 0), 1.2, 60 if night else 25, (1.0, 0.82, 0.6)); ante.visible_camera = False
    # left wall (-X): two tall windows with net curtains and heavy side drapes
    win_y = (-0.8, 1.4)
    piers = [(ROOM_Y0, win_y[0] - 0.7), (win_y[0] + 0.7, win_y[1] - 0.7), (win_y[1] + 0.7, ROOM_Y1)]
    for (y0, y1) in piers:
        box("WallL", (-ROOM_X - 0.05, (y0 + y1) / 2, ROOM_H / 2), (0.1, y1 - y0, ROOM_H), paper)
    for y in win_y:
        box("Sill", (-ROOM_X + 0.05, y, 0.85), (0.3, 1.5, 0.05), pbr("SillPaint", (0.7, 0.68, 0.62), 0.5))
        box("WallUnder", (-ROOM_X - 0.05, y, 0.42), (0.1, 1.4, 0.85), paper)
        box("WallOver", (-ROOM_X - 0.05, y, 2.85), (0.1, 1.4, 0.5), paper)
        wf = pbr("WinFrame", (0.72, 0.7, 0.64), 0.5)
        box("WinMullion", (-ROOM_X - 0.03, y, 1.73), (0.06, 0.05, 1.75), wf)
        box("WinTransom", (-ROOM_X - 0.03, y, 2.25), (0.06, 1.4, 0.05), wf)
        box("WinGlass", (-ROOM_X - 0.06, y, 1.73), (0.01, 1.4, 1.75), glass("WinGlass", (0.92, 0.95, 0.96), 0.02))
    # net curtains: one long sheer per window, stirring (wave modifier, time-driven so it bakes)
    nm = net_curtain("Net")
    c["nets"] = []
    for y in win_y:
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=50, size=1, location=(-ROOM_X + 0.14, y, 1.6), rotation=(math.radians(90), 0, math.radians(90)))
        o = bpy.context.active_object; o.name = "NetCurtain"; o.scale = (1.5, 2.95, 1); o.data.materials.append(nm)
        # gathered folds: sine displacement along the width
        for v in o.data.vertices:
            v.co.z += 0.018 * math.sin(v.co.x * 2 * math.pi * 14)
        wv = o.modifiers.new("stir", 'WAVE'); wv.use_normal = True; wv.use_x = False; wv.use_y = False
        wv.height = 0.025; wv.width = 0.9; wv.narrowness = 1.0; wv.speed = 0.012; wv.time_offset = rng.uniform(0, 60)
        wv.start_position_x = 0.0; wv.start_position_y = 1.6
        c["nets"].append(o)
        drape = fabric("Drape", (0.18, 0.12, 0.06), 0.85, 0.6, 300)
        for dy in (-0.82, 0.82):
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=8, size=1, location=(-ROOM_X + 0.2, y + dy, 1.55), rotation=(math.radians(90), 0, math.radians(90)))
            d = bpy.context.active_object; d.name = "Drape"; d.scale = (0.35, 3.0, 1); d.data.materials.append(drape)
            for v in d.data.vertices:
                v.co.z += 0.05 * math.sin(v.co.x * 2 * math.pi * 3)
            s_ = d.modifiers.new("solid", 'SOLIDIFY'); s_.thickness = 0.01
        box("CurtainRod", (-ROOM_X + 0.2, y, 2.62), (0.03, 2.1, 0.03), pbr("RodBrass", (0.5, 0.4, 0.2), 0.35, 1.0))
    # the street outside: a facade across the road (CG, house style)
    from pbkit import masonry_facade
    fac = masonry_facade("OppFacade", plaster=(0.55, 0.47, 0.36), floor=3.3, bay=2.6, win_w=1.3, win_h=1.7,
                         lit_frac=0.35 if night else 0.0, lit_strength=1.5)
    box("Opposite", (-ROOM_X - 24, 0, 13), (1.0, 80, 30), fac)
    box("Street", (-ROOM_X - 12, 0, -4.0), (24, 80, 0.2), pbr("StreetAsphalt", (0.08, 0.08, 0.085), 0.8))
    # daylight / dusk through the windows
    if night:
        for y in win_y:
            l = area_light((-ROOM_X - 0.3, y, 1.75), (0, math.radians(-90), 0), 1.4, 70, (0.45, 0.58, 0.95))
            l.visible_camera = False; l.visible_glossy = False; l.visible_transmission = False
    else:
        for y in win_y:
            l = area_light((-ROOM_X - 0.3, y, 1.75), (0, math.radians(-90), 0), 1.4, 420, (0.9, 0.94, 1.0))
            l.visible_camera = False; l.visible_glossy = False; l.visible_transmission = False
            pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 1.4; pt.size_y = 1.75; pt.cycles.is_portal = True
            po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (-ROOM_X - 0.08, y, 1.73); po.rotation_euler = (0, math.radians(-90), 0)
        fill = area_light((1.5, -2.5, 2.8), (0, 0, 0), 2.5, 90, (1.0, 0.9, 0.8)); point_at(fill, (0, 1, 0.8)); fill.visible_camera = False
    # ceiling fixture (off in the search variant: they don't touch the switches)
    box("CeilRose", (0, 0.4, ROOM_H - 0.02), (0.3, 0.3, 0.04), pbr("Rose", (0.7, 0.68, 0.62), 0.6))
    # ---------------------------------------------------------------- furniture (scanned)
    r, desk = ph.model("metal_office_desk", loc=tuple(DESK), rot_z=math.pi)
    retint(desk, (0.95, 0.9, 0.8))
    c["desk_drawers"] = {o.name: o for o in desk if "drawer" in o.name}
    for o in desk:
        if "drawer" in o.name:
            o["y0"] = o.location.y
    blot = pbr("Blotter", (0.03, 0.1, 0.06), 0.6, 0.0, **{'Sheen Weight': 0.3})
    box("Blotter", (-0.02, 1.25, TOP_Z + 0.003), (0.62, 0.46, 0.006), blot, bevel=0.002)
    for sx in (-1, 1):
        box("BlotterCorner", (-0.02 + sx * 0.3, 1.25, TOP_Z + 0.005), (0.05, 0.48, 0.008), pbr("BlotLeather", (0.08, 0.04, 0.02), 0.45))
    r, chair = ph.model("GreenChair_01", loc=(1.15, 1.95, 0), rot_z=math.pi + math.radians(55))     # pushed back from the desk, turned
    c["chair"] = r
    r, cab = ph.model("vintage_cabinet_01", loc=(1.75, ROOM_Y1 - 0.3, 0), rot_z=0.0)
    for o in cab:
        pass
    r, fc = ph.model("drawer_cabinet", loc=(ROOM_X - 0.27, FILE_Y, 0), rot_z=math.radians(-90))       # faces -X, into the room
    retint(fc, (0.75, 0.75, 0.72))
    c["file_drawers"] = sorted([o for o in fc if "_drawer_" in o.name], key=lambda o: o.name)
    for o in c["file_drawers"]:
        o["y0"] = o.location.y
    r, _ = ph.model("potted_plant_02", loc=(-ROOM_X + 0.45, 2.55, 0), rot_z=0.6)
    r, clk = ph.model("wall_clock", loc=(-0.9, ROOM_Y1 - 0.0, 2.15), rot_z=0.0)
    c["clock_hands"] = {k: o for o in clk for k in ("second", "minute", "hours") if k in o.name}
    r, _ = ph.model("hanging_picture_frame_01", loc=(0.3, ROOM_Y1 - 0.0, 1.95), rot_z=0.0)
    from pbkit import painting, image_plane
    GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")
    image_plane("Painting", painting(os.path.join(GEN, "painting_birches.png")), (0.3, ROOM_Y1 - 0.014, 1.95), (0.46, 0.71), (math.radians(90), 0, 0), rough=0.5)
    # visitor chairs facing the desk
    for k, x in enumerate((-0.75, 0.75)):
        ph.model("dining_chair_02", loc=(x, 0.05, 0), rot_z=math.pi + (0.35 if x < 0 else -0.35))
    # ---------------------------------------------------------------- on the desk
    r, crt = ph.model("television_02", loc=(0.6, 1.45, TOP_Z), rot_z=math.pi - math.radians(32))     # small CRT monitor, toward his chair
    kb_m = plastic("KeyboardBeige", (0.62, 0.58, 0.5), 0.45)
    box("Keyboard", (0.5, 1.2, TOP_Z + 0.015), (0.4, 0.14, 0.03), kb_m, bevel=0.006, rot=(0, 0, math.radians(-32)))
    r, lamp = ph.model("desk_lamp_arm_01", loc=(0.88, 1.62, TOP_Z), rot_z=math.radians(215))
    retint(lamp, (0.15, 0.25, 0.18))
    import paper_tex
    pages = paper_tex.make_all()["pages"]
    from pbkit import image_plane
    for k in range(4):                                             # typed pages and a pen on the blotter
        image_plane("Page", pages[k % len(pages)], (-0.12 + k * 0.09, 1.22 + 0.03 * (k % 2), TOP_Z + 0.007 + k * 0.0006), (0.21, 0.28),
                    (0, 0, math.radians(180 + rng.uniform(-12, 12))), rough=0.75)
    cyl("Pen", (0.22, 1.05, TOP_Z + 0.012), 0.005, 0.14, pbr("PenBlack", (0.01, 0.01, 0.012), 0.2, 0.0, **{'Coat Weight': 1.0}), verts=16, rot=(0, math.radians(90), math.radians(30)))
    for k in range(3):
        ph.model("binder_notebook", loc=(0.72, 0.86 + k * 0.012, TOP_Z + 0.002 + k * 0.03), rot_z=math.radians(80 + rng.uniform(-6, 6)))
    # brass nameplate on the front edge, facing the visitor (title only, no name)
    plate_m = pbr("PlateBrass", (0.6, 0.45, 0.22), 0.28, 1.0)
    np_ = box("Nameplate", (0.1, 0.78, TOP_Z + 0.03), (0.26, 0.012, 0.055), pbr("PlateWood", (0.05, 0.025, 0.012), 0.4), bevel=0.003, rot=(math.radians(-12), 0, 0))
    text_obj("PlateText", "ПРЕДСЕДАТЕЛЬ ПРАВЛЕНИЯ", (0.1, 0.771, TOP_Z + 0.03), 0.014, plate_m, rot=(math.radians(78), 0, 0), extrude=0.0006)
    c["nameplate"] = np_
    # ---------------------------------------------------------------- the telephone
    root, hs, base = telephone()
    root.location = PHONE; root.rotation_euler = (0, 0, PHONE_ROT)
    bpy.context.view_layer.update()
    cord_m = plastic("CordWhite", (0.78, 0.76, 0.7), 0.35)
    M = root.matrix_world
    pts = [hs.matrix_world @ Vector((0.0, -HS_L / 2 + 0.004, -0.012)), M @ Vector((-0.06, -0.15, 0.012)), M @ Vector((-0.13, -0.17, 0.0045)),
           M @ Vector((-0.17, -0.09, 0.0045)), M @ Vector((-0.15, -0.03, 0.0045)), M @ Vector((-0.103, -0.05, 0.016))]
    c["cord"] = coiled_cord("Cord", pts, mat=cord_m)
    c.update(phone=root, handset=hs, phone_base=base)
    # ---------------------------------------------------------------- people (search variant)
    c["people"] = {}
    if variant == "search":
        a = person("InvA", 1.0, 46, "male_casualsuit05", "short02", cval=0.14, hv=0.3, sat=0.2)    # dark coat-jacket
        stand(a, (-0.72, 2.1, 0), 0.0)                        # behind the desk, faces -Y: the drawers on its +Y side
        b = person("InvB", 1.0, 38, "male_casualsuit03", "short04", cval=0.22, hv=0.2, sat=0.4)
        stand(b, (FILE_X - 0.9, FILE_Y, 0), math.radians(90))   # faces +X: the filing cabinet
        c["people"] = {"A": a, "B": b}
        manila = pbr("Manila", (0.6, 0.48, 0.28), 0.8)
        fo = box("Folder", (0, 0, 0), (0.31, 0.235, 0.004), manila, bevel=0.001)
        pg = image_plane("FolderPage", pages[1], (0.0, 0.0, 0.0025), (0.29, 0.215), (0, 0, math.radians(90)), rough=0.75); pg.parent = fo
        c["folder"] = fo
    animate(c, 0.0, None)
    return c


# ============================================================================ animation
def tick_clock(c, sec, start=(10, 8, 20)):
    h0, m0, s0 = start
    s = s0 + int(sec)                                         # the second hand steps once a second
    hands = c["clock_hands"]
    for k, o in hands.items():
        if k == "second":
            a = s / 60 * 2 * math.pi
        elif k == "minute":
            a = (m0 + s / 60) / 60 * 2 * math.pi
        else:
            a = (h0 % 12 + (m0 + s / 60) / 60) / 12 * 2 * math.pi
        o.rotation_mode = 'XYZ'; o.rotation_euler = (0, -a, 0)


def place_torch(c, k, hand_pos, aim_at):
    tr, lo = c["torches"][k]
    d = (Vector(aim_at) - Vector(hand_pos)).normalized()
    tr.rotation_mode = 'QUATERNION'; tr.rotation_quaternion = (-d).to_track_quat('Y', 'Z')     # lens end (-Y local) forward
    tr.location = Vector(hand_pos)
    lo.location = Vector(hand_pos) + d * 0.17
    lo.rotation_mode = 'QUATERNION'; lo.rotation_quaternion = (-d).to_track_quat('Z', 'Y')     # spot shines along -Z


def pose_holding_torch(h, side, target, pole):
    """Wrist at a point a little in front of the chest; the torch sits in the hand."""
    reach(h, side, target, pole, None)
    fingers_curl(h, 60, side=(side,), thumb=30)


def look(h, target, amount=1.0):
    """Turn neck and head toward a world point (yaw only, split between neck and head)."""
    f = _fwd(h); d = Vector(target) - h.bone_head("head"); d.z = 0
    if d.length < 1e-4:
        return
    ang = math.degrees(math.atan2(f.x * d.y - f.y * d.x, f.x * d.x + f.y * d.y)) * amount
    ang = max(-70, min(70, ang))
    h.rot("neck01", (0, 0, 1), ang * 0.4); h.rot("head", (0, 0, 1), ang * 0.6)


def animate(c, sec, phase):
    if "clock_hands" in c:
        tick_clock(c, sec + (phase or {}).get("clock", 0.0))
    if c["variant"] != "search" or not c["people"]:
        bpy.context.view_layer.update(); return
    ph_ = phase or {}
    a, b = c["people"]["A"], c["people"]["B"]
    # --- A, behind the desk: 3A he has lifted a folder from the open drawer and reads it; 3B he lowers it and looks at the phone.
    stand(a, (-0.72, 2.1, 0), 0.0)
    dr = c["desk_drawers"].get("metal_office_desk_drawer_01") or list(c["desk_drawers"].values())[0]
    dr.location.y = dr["y0"] - 0.3 * ph_.get("drawer", 0.0)       # the drawer's local -Y is world +Y (desk turned 180)
    turn = ph_.get("turn", 0.0)
    nod(a, "spine04", 4 + 2 * turn); nod(a, "neck01", 8 * (1 - turn) + 4 * turn); nod(a, "head", 16 * (1 - turn) + 10 * turn)
    bpy.context.view_layer.update()
    fwd = _fwd(a); side = fwd.cross(Vector((0, 0, 1))).normalized()
    chest = a.bone_head("spine03")
    lower = ease(min(1.0, turn * 1.6))
    hold = chest + fwd * (0.33 - 0.06 * lower) + Vector((0, 0, -0.06 - 0.25 * lower + 0.008 * math.sin(sec * 0.8)))
    fo = c["folder"]; fo.location = hold
    tilt = math.radians(55 - 45 * lower)                         # page tipped toward his eyes, flatter as he lowers it
    fo.rotation_mode = 'XYZ'; fo.rotation_euler = (tilt, 0, math.atan2(fwd.y, fwd.x) + math.pi / 2)
    bpy.context.view_layer.update()
    for sd, sg in (("L", -1), ("R", 1)):
        reach(a, sd, hold - side * (0.15 * sg) + Vector((0, 0, -0.02)), Vector((-sg * side.x, -sg * side.y, -0.8)), fwd + Vector((0, 0, 0.2)))
    fingers_curl(a, 30, thumb=15)
    look(a, PHONE, turn)
    # --- B, at the steel filing unit: a drawer already out, he walks his fingers through the folders
    stand(b, (FILE_X - 0.9, FILE_Y, 0), math.radians(90))
    fdr = c["file_drawers"][0]
    fp = ph_.get("file", 0.0)
    fdr.location.y = fdr["y0"] - 0.34 * fp
    bpy.context.view_layer.update()
    lo, hi = ph.bounds([fdr]); top = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))
    walk = 0.05 * math.sin(sec * 1.3)
    nod(b, "spine04", 8); nod(b, "neck01", 8); nod(b, "head", 18)
    bpy.context.view_layer.update()
    reach(b, "R", top + Vector((-0.05, -0.08 + walk, 0.1)), Vector((-0.4, -0.6, -0.6)), Vector((1, 0, -0.8)))
    reach(b, "L", top + Vector((-0.08, 0.14, 0.08)), Vector((-0.4, 0.6, -0.6)), Vector((1, 0, -0.8)))
    fingers_curl(b, 30, thumb=15)
    bpy.context.view_layer.update()


def anim_handset(c, t):
    animate(c, t * DUR["handset"], None)


def anim_empty(c, t):
    animate(c, DUR["handset"] + t * DUR["empty"], None)


def anim_search(c, t):
    sec = t * DUR["search"]
    animate(c, sec, {"drawer": ease(min(1.0, max(0.0, (sec - 0.6) / 1.8))), "file": 0.8 + 0.2 * ease(min(1.0, sec / 2.0))})


def anim_find(c, t):
    sec = t * DUR["find"]
    animate(c, DUR["search"] + sec, {"drawer": 1.0, "file": 1.0, "turn": ease(min(1.0, max(0.0, (sec - 0.3) / 2.0)))})


# ============================================================================ cameras
def cam_handset(c, t):
    """Hold on the handset (the 2.5 s lead-in is the first ~32 %), then a slow push."""
    hold = 2.5 / DUR["handset"]
    e = ease(max(0.0, (t - hold) / (1 - hold)))
    tgt = c["handset"].matrix_world @ Vector((0.0, 0.04, 0.0))
    start = tgt + Vector((-0.62, -0.78, 0.42)); end = tgt + Vector((-0.42, -0.52, 0.27))
    return (start.lerp(end, e), tgt, 50)


def cam_empty(c, t):
    e = ease(t)
    return (Vector((2.55, -2.55, 1.62)).lerp(Vector((1.85, -2.6, 1.6)), e), Vector((-0.3, 1.3, 0.95)).lerp(Vector((-0.6, 1.3, 0.95)), e), 24)


def cam_search(c, t):
    e = ease(t)
    return (Vector((-2.3, -2.2, 1.62)).lerp(Vector((-2.0, -1.85, 1.6)), e), Vector((0.9, 1.3, 1.1)).lerp(Vector((0.8, 1.35, 1.1)), e), 24)


def cam_find(c, t):
    e = ease(t)
    tgt0 = Vector((-0.6, 1.6, 1.15)); tgt1 = PHONE + Vector((0.0, 0.03, 0.06))
    return (Vector((-1.7, -1.1, 1.45)).lerp(PHONE + Vector((-0.55, -0.75, 0.38)), e), tgt0.lerp(tgt1, ease(min(1.0, t * 1.25))), 32 + 18 * e)


MOVES = {
    "handset": dict(kind="anim", dof=2.0, far=10.0, cam=cam_handset, anim=anim_handset,
                    focus=lambda c, t: c["handset"].matrix_world @ Vector((0.0, 0.06, 0))),
    "empty": dict(kind="anim", dof=5.6, far=12.0, cam=cam_empty, anim=anim_empty, focus=lambda c, t: DESK + Vector((0, 0, 0.9))),
    "search": dict(kind="anim", dof=4.0, far=12.0, cam=cam_search, anim=anim_search, focus=lambda c, t: Vector((-0.7, 1.9, 1.3))),
    "find": dict(kind="anim", dof=2.8, far=10.0, cam=cam_find, anim=anim_find,
                 focus=lambda c, t: Vector((-0.65, 1.9, 1.5)).lerp(PHONE + Vector((0, 0.03, 0.06)), ease(min(1.0, t * 1.25)))),
}
