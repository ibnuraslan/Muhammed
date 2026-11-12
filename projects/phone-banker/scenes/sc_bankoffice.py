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

ROOM_X, ROOM_Y0, ROOM_Y1, ROOM_H = 3.2, -3.0, 3.0, 3.1
DESK = Vector((0.0, 1.15, 0.0))          # desk centre; the banker's side is +Y (his back to the cabinet)
TOP_Z = 0.79                              # desk top
PHONE = Vector((-0.55, 1.36, TOP_Z))      # at the banker's right hand (he sits at +Y facing -Y)
PHONE_ROT = math.radians(180 + 24)
FILE_X, FILE_Y = ROOM_X - 0.27, -0.3           # steel filing unit on the right wall, between the door and the cabinet
DOOR_Y = -1.6
CHAIR_AT_DESK = Vector((0.0, 2.02, 0.0))
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
    mp = N.new("ShaderNodeMapping"); mp.inputs['Location'].default_value = (0.0, -0.0234, -0.0174); mp.inputs['Scale'].default_value = (1.2, 0.9, 1.2)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    wob = N.new("ShaderNodeTexNoise"); wob.inputs['Scale'].default_value = 60; wob.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], wob.inputs['Vector'])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(mp.outputs[0], ln.inputs[0])
    jit = N.new("ShaderNodeMath"); jit.operation = 'MULTIPLY_ADD'; jit.inputs[1].default_value = 0.014
    L.new(wob.outputs['Fac'], jit.inputs[0]); L.new(ln.outputs['Value'], jit.inputs[2])
    mask = N.new("ShaderNodeMapRange"); mask.inputs['From Min'].default_value = 0.05; mask.inputs['From Max'].default_value = 0.02
    L.new(jit.outputs[0], mask.inputs['Value'])
    # fine mottling inside the patch (a dried film, not a blot)
    mot = N.new("ShaderNodeTexNoise"); mot.inputs['Scale'].default_value = 420; mot.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], mot.inputs['Vector'])
    mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; L.new(mask.outputs[0], mm.inputs[0]); L.new(mot.outputs['Fac'], mm.inputs[1])
    mk = N.new("ShaderNodeMath"); mk.operation = 'MULTIPLY'; mk.inputs[1].default_value = 2.2; mk.use_clamp = True
    L.new(mm.outputs[0], mk.inputs[0])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'
    col.inputs[6].default_value = (0.80, 0.78, 0.72, 1); col.inputs[7].default_value = (0.42, 0.34, 0.2, 1)
    L.new(mk.outputs[0], col.inputs['Factor']); L.new(col.outputs[2], p.inputs['Base Color'])
    rg = N.new("ShaderNodeMix"); rg.data_type = 'FLOAT'; rg.inputs[2].default_value = 0.3; rg.inputs[3].default_value = 0.07
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
    beige = plastic("PhoneBeige", (0.7, 0.64, 0.5), 0.28, coat=0.35)
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
    lcd = pbr("PhoneLCD", (0.3, 0.34, 0.27), 0.15, 0.0, **{'Emission Color': (0.35, 0.45, 0.3, 1), 'Emission Strength': 0.06, 'Coat Weight': 1.0})
    parts.append(box("DisplayBezel", (0.048, 0.045, topz(0.045) + 0.001), (0.078, 0.034, 0.002), dark, rot=(slope, 0, 0)))
    parts.append(box("Display", (0.048, 0.045, topz(0.045) + 0.0022), (0.066, 0.022, 0.001), lcd, rot=(slope, 0, 0)))
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


def cord_mesh(cu_obj, handset, end, reach_len=0.32):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(cu_obj.evaluated_get(dg), depsgraph=dg)
    me.transform(cu_obj.matrix_world)
    o = bpy.data.objects.new("Cord", me); bpy.context.collection.objects.link(o)
    for m in cu_obj.data.materials:
        me.materials.append(m)
    bpy.data.objects.remove(cu_obj, do_unlink=True)
    vg = o.vertex_groups.new(name="hook")
    for v in me.vertices:
        d = (v.co - Vector(end)).length
        w = max(0.0, 1.0 - d / reach_len); w = w * w * (3 - 2 * w)
        if w > 0:
            vg.add([v.index], w, 'REPLACE')
    hk = o.modifiers.new("hook", 'HOOK'); hk.object = handset; hk.vertex_group = "hook"
    bpy.context.view_layer.update()
    hk.matrix_inverse = handset.matrix_world.inverted()
    for p_ in me.polygons:
        p_.use_smooth = True
    return o


# ============================================================================ people
from pbpeople import person, stand, seat, walk_at, nod, look, hold_flat, hand_to, hide, protective_gear, turn_torso
from pbpeople import fwd as _fwd


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
    slat_m = pbr("BlindSlat", (0.78, 0.76, 0.7), 0.45, 0.2)
    for k in range(34):                                                # venetian blind on the window behind the desk
        box("BlindSlat", (-ROOM_X + 0.1, win_y[1], 0.95 + k * 0.05), (0.05, 1.42, 0.004), slat_m, rot=(0, math.radians(-35), 0))
    box("BlindRail", (-ROOM_X + 0.1, win_y[1], 2.66), (0.06, 1.46, 0.04), slat_m)
    for y in win_y[:1]:
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
    box("Opposite", (-ROOM_X - 30, 0, 5), (1.0, 80, 22), fac)
    c["opp_mat"] = fac
    build_anteroom(c, floor, paper, panel)
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
        sn = sun(42, 160, 3.0, (1.0, 0.9, 0.76), 0.8)                     # low sun from the window side: shafts and slat light
        c["sun"] = sn

    # ceiling fixture (off in the search variant: they don't touch the switches)
    box("CeilRose", (0, 0.4, ROOM_H - 0.02), (0.3, 0.3, 0.04), pbr("Rose", (0.7, 0.68, 0.62), 0.6))
    # ---------------------------------------------------------------- furniture (scanned)
    r, desk = ph.model("metal_office_desk", loc=tuple(DESK), rot_z=math.pi)
    walnut = ph.texture("dark_wood", scale=1.6, name="Walnut")
    pw = walnut.node_tree.nodes["Principled BSDF"]; pw.inputs['Coat Weight'].default_value = 0.5; pw.inputs['Coat Roughness'].default_value = 0.15
    for o in desk:
        for i in range(len(o.material_slots)):
            o.material_slots[i].material = walnut
    c["desk_drawers"] = {o.name: o for o in desk if "drawer" in o.name}
    for o in desk:
        if "drawer" in o.name:
            o["y0"] = o.location.y
    blot = pbr("Blotter", (0.03, 0.1, 0.06), 0.6, 0.0, **{'Sheen Weight': 0.3})
    box("Blotter", (-0.02, 1.2, TOP_Z + 0.003), (1.2, 0.62, 0.006), blot, bevel=0.002)
    for sx in (-1, 1):
        box("BlotterCorner", (-0.02 + sx * 0.59, 1.2, TOP_Z + 0.005), (0.03, 0.64, 0.008), pbr("BlotLeather", (0.25, 0.18, 0.08), 0.3, 0.8))
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
    r, _ = ph.model("potted_plant_02", loc=(-ROOM_X + 0.5, -2.45, 0), rot_z=0.6)
    r, bs = ph.model("wooden_bookshelf_worn", loc=(-ROOM_X + 0.75, ROOM_Y1 - 0.32, 0), rot_z=0.0)
    retint(bs, (0.55, 0.35, 0.2))
    vol_ms = [pbr(f"Book{k}", col, 0.6) for k, col in enumerate(((0.3, 0.08, 0.06), (0.08, 0.15, 0.1), (0.12, 0.1, 0.2), (0.4, 0.3, 0.15), (0.2, 0.18, 0.15)))]
    for sh in range(5):
        x = -ROOM_X + 0.2
        while x < -ROOM_X + 1.3:
            w = rng.uniform(0.025, 0.05); hgt = rng.uniform(0.2, 0.3)
            box("Book", (x + w / 2, ROOM_Y1 - 0.34, 0.12 + sh * 0.39 + hgt / 2), (w, 0.2, hgt), vol_ms[int(rng.integers(0, 5))])
            x += w + 0.003
    gl = glass("Crystal", (0.97, 0.96, 0.92), 0.0)
    dec = cyl("Decanter", (1.45, ROOM_Y1 - 0.45, 0.98), 0.07, 0.2, gl, verts=24); cyl("DecNeck", (1.45, ROOM_Y1 - 0.45, 1.13), 0.022, 0.1, gl, verts=16)
    cyl("DecStopper", (1.45, ROOM_Y1 - 0.45, 1.2), 0.03, 0.04, gl, verts=16)
    cyl("Cognac", (1.45, ROOM_Y1 - 0.45, 0.94), 0.066, 0.1, pbr("Cognac", (0.5, 0.22, 0.05), 0.05, 0.0, **{'Transmission Weight': 1.0}), verts=24)
    for dx in (-0.16, -0.25):
        cyl("Tumbler", (1.45 + dx, ROOM_Y1 - 0.42, 0.93), 0.03, 0.07, gl, verts=16)
    box("Tray", (1.38, ROOM_Y1 - 0.44, 0.882), (0.42, 0.24, 0.008), pbr("TrayBrass", (0.55, 0.42, 0.2), 0.3, 1.0))
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
    dl = bpy.data.lights.new("DeskLampOn", 'SPOT'); dl.energy = 22; dl.spot_size = math.radians(75); dl.spot_blend = 0.5; dl.color = (1.0, 0.78, 0.5)
    dlo = bpy.data.objects.new("DeskLampOn", dl); bpy.context.collection.objects.link(dlo); dlo.location = (0.62, 1.38, 1.3); point_at(dlo, (0.25, 1.2, TOP_Z))

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
    c["cord"] = cord_mesh(coiled_cord("Cord", pts, mat=cord_m), hs, pts[0])
    c.update(phone=root, handset=hs, phone_base=base)
    # ---------------------------------------------------------------- per-variant set dressing
    if variant in ("day", "brother", "visit", "alone", "leave"):
        c["chair"].location = CHAIR_AT_DESK; c["chair"].rotation_euler = (0, 0, math.pi)
    if variant in ("sealed", "ante", "ledger"):
        c["door"].rotation_euler = (0, 0, 0)                       # door shut (ante shots see it from the other side)
    if variant in ("ante", "ledger"):
        c["door"].rotation_euler = (0, 0, 0)
    if variant == "sealed":
        c["door"].rotation_euler = (0, 0, math.radians(-75))     # open: they come and go
    if variant == "dust":
        dust_sheets(c)
    for s_ in c["seal"]:
        s_.hide_render = variant != "ante"
    if variant in ("brother",):
        c["door"].rotation_euler = (0, 0, 0)
    build_people(c, variant)
    animate(c, 0.0, None)
    return c


# ============================================================================ ante-room (the secretary's room, through the door)
AX0, AX1, AY0, AY1 = ROOM_X + 0.1, ROOM_X + 4.0, -3.6, 0.6


def build_anteroom(c, floor_m, paper_m, panel_m):
    box("AnteFloor", ((AX0 + AX1) / 2, (AY0 + AY1) / 2, -0.01), (AX1 - AX0, AY1 - AY0, 0.02), floor_m)
    box("AnteCeil", ((AX0 + AX1) / 2, (AY0 + AY1) / 2, ROOM_H + 0.02), (AX1 - AX0, AY1 - AY0, 0.04), pbr("AnteCeil", (0.62, 0.6, 0.56), 0.9))
    for y in (AY0 - 0.05, AY1 + 0.05):
        box("AnteWallY", ((AX0 + AX1) / 2, y, ROOM_H / 2), (AX1 - AX0, 0.1, ROOM_H), paper_m)
        box("AnteDado", ((AX0 + AX1) / 2, y + (0.055 if y < 0 else -0.055), 0.55), (AX1 - AX0, 0.02, 1.1), panel_m)
    # far wall with a window (net curtain), the light source of the room
    wy = -1.4
    for (y0, y1) in ((AY0, wy - 0.7), (wy + 0.7, AY1)):
        box("AnteWallX", (AX1 + 0.05, (y0 + y1) / 2, ROOM_H / 2), (0.1, y1 - y0, ROOM_H), paper_m)
    box("AnteUnder", (AX1 + 0.05, wy, 0.42), (0.1, 1.4, 0.85), paper_m); box("AnteOver", (AX1 + 0.05, wy, 2.85), (0.1, 1.4, 0.5), paper_m)
    box("AnteGlass", (AX1 + 0.08, wy, 1.73), (0.01, 1.4, 1.75), glass("WinGlass2", (0.92, 0.95, 0.96), 0.02))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=40, size=1, location=(AX1 - 0.1, wy, 1.6), rotation=(math.radians(90), 0, math.radians(90)))
    o = bpy.context.active_object; o.name = "AnteNet"; o.scale = (1.5, 2.95, 1); o.data.materials.append(net_curtain("Net2"))
    for v in o.data.vertices:
        v.co.z += 0.018 * math.sin(v.co.x * 2 * math.pi * 14)
    wv = o.modifiers.new("stir", 'WAVE'); wv.use_normal = True; wv.use_x = False; wv.use_y = False; wv.height = 0.02; wv.width = 0.9; wv.speed = 0.012
    l = area_light((AX1 + 0.4, wy, 1.75), (0, math.radians(90), 0), 1.4, 220, (0.9, 0.94, 1.0))
    l.visible_camera = False; l.visible_glossy = False; l.visible_transmission = False
    fill = area_light(((AX0 + AX1) / 2, -1.5, ROOM_H - 0.1), (0, 0, 0), 2.0, 60, (1.0, 0.88, 0.75)); fill.visible_camera = False
    box("AnteOppo", (AX1 + 20, 0, 12), (1.0, 60, 30), c["opp_mat"])
    # secretary's desk (scanned), chair, typewriter, a folded cloth, papers
    r, _ = ph.model("WoodenTable_03", loc=(AX0 + 1.9, -0.35, 0), rot_z=math.radians(90))
    r, _ = ph.model("dining_chair_02", loc=(AX0 + 2.45, -0.35, 0), rot_z=math.radians(90))
    tz = 0.83
    tw = typewriter()
    tw.location = (AX0 + 1.9, 0.12, tz); tw.rotation_euler = (0, 0, math.radians(-90))           # keys toward her chair (+X)
    cloth = folded_cloth()
    cloth.location = (AX0 + 1.85, -0.72, tz + 0.001); cloth.rotation_euler = (0, 0, 0.3)
    c["cloth"] = cloth
    import paper_tex
    pages = paper_tex.make_all()["pages"]
    from pbkit import image_plane
    image_plane("AntePage", pages[2], (AX0 + 1.75, -0.95, tz + 0.002), (0.21, 0.28), (0, 0, math.radians(95)), rough=0.75)
    # visitor ledger (opened on the desk in the ledger variant)
    c["ledger"] = ledger(pages)
    c["ledger"]["root"].location = (AX0 + 1.85, -0.38, tz + 0.001); c["ledger"]["root"].rotation_euler = (0, 0, math.radians(-90))
    ph.model("standing_picture_frame_01", loc=(AX0 + 1.7, 0.42, tz), rot_z=math.radians(-110))
    r, _ = ph.model("potted_plant_02", loc=(AX1 - 0.4, AY1 - 0.4, 0), rot_z=1.0)
    r, cl = ph.model("wall_clock", loc=(AX0 + 2.0, AY1 + 0.0, 2.1), rot_z=math.pi)
    # coat stand corner and a row of chairs for visitors along the near wall
    for k in range(3):
        ph.model("dining_chair_02", loc=(AX0 + 0.7 + k * 0.55, AY0 + 0.35, 0), rot_z=0.0)
    # Soviet-style paper seal across the office door, on the ante-room side (sealed variants)
    seal_m = pbr("SealPaper", (0.86, 0.84, 0.76), 0.85)
    seal = box("DoorSeal", (ROOM_X + 0.06, DOOR_Y - 0.48, 1.25), (0.004, 0.32, 0.07), seal_m, rot=(math.radians(8), 0, 0))
    stamp = cyl("SealStamp", (ROOM_X + 0.063, DOOR_Y - 0.5, 1.25), 0.022, 0.002, pbr("StampInk", (0.25, 0.15, 0.45), 0.7), verts=24, rot=(0, math.radians(90), 0))
    c["seal"] = [seal, stamp]


def typewriter():
    from pbkit import joinm
    body_m = pbr("TypeBody", (0.16, 0.2, 0.18), 0.45, 0.2, **{'Coat Weight': 0.4})
    key_m = pbr("TypeKey", (0.05, 0.05, 0.05), 0.4); keytop = pbr("TypeKeyTop", (0.8, 0.78, 0.72), 0.4)
    chrome = pbr("TypeChrome", (0.7, 0.7, 0.7), 0.25, 1.0)
    parts = [box("TwBase", (0, 0, 0.045), (0.42, 0.34, 0.09), body_m, bevel=0.02),
             box("TwTop", (0, 0.06, 0.1), (0.4, 0.2, 0.06), body_m, bevel=0.02),
             cyl("TwPlaten", (0, 0.12, 0.15), 0.025, 0.46, pbr("Platen", (0.03, 0.03, 0.03), 0.6), verts=24, rot=(0, math.radians(90), 0)),
             box("TwCarriage", (0, 0.15, 0.15), (0.48, 0.05, 0.04), chrome, bevel=0.005),
             cyl("TwKnob", (-0.25, 0.12, 0.15), 0.022, 0.03, key_m, verts=16, rot=(0, math.radians(90), 0)),
             box("TwLever", (-0.27, 0.08, 0.18), (0.012, 0.09, 0.012), chrome)]
    for r in range(4):
        for k in range(11 - (r % 2)):
            x = -0.16 + k * 0.031 + (r % 2) * 0.015; y = -0.12 + r * 0.035; z = 0.07 + r * 0.012
            parts.append(cyl("TwKey", (x, y, z), 0.011, 0.012, keytop, verts=12))
    parts.append(box("TwSpace", (0, -0.155, 0.07), (0.18, 0.016, 0.01), keytop, bevel=0.003))
    o = joinm(parts, "Typewriter")
    import paper_tex
    from pbkit import image_plane
    pg = image_plane("TwPaper", paper_tex.make_all()["pages"][0], (0, 0.13, 0.25), (0.21, 0.2), (math.radians(80), 0, 0), rough=0.75)
    pg.parent = o
    return o


def folded_cloth():
    m = fabric("DustCloth", (0.36, 0.42, 0.46), 0.95, 0.5, 600)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=24, size=1, location=(0, 0, 0.012))
    o = bpy.context.active_object; o.name = "Cloth"; o.scale = (0.24, 0.18, 1); o.data.materials.append(m)
    r = np.random.default_rng(4)
    for v in o.data.vertices:
        v.co.z += 0.006 * math.sin(v.co.x * 23) * math.cos(v.co.y * 17) + r.uniform(0, 0.002)
    s = o.modifiers.new("t", 'SOLIDIFY'); s.thickness = 0.02
    sub = o.modifiers.new("s", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    return o


def ledger(pages):
    """An open visitor ledger: hard cover, a left page block, and a page that can turn (rotates about the spine)."""
    cover_m = pbr("LedgerCover", (0.12, 0.05, 0.04), 0.6)
    root = bpy.data.objects.new("Ledger", None); bpy.context.collection.objects.link(root)
    cov = box("LedgerCover", (0, 0, 0.003), (0.46, 0.32, 0.006), cover_m); cov.parent = root
    from pbkit import image_plane
    import paper_tex
    tab = paper_tex.make_all()
    lp = image_plane("LedgerLeft", pages[3] if len(pages) > 3 else pages[0], (-0.115, 0, 0.012), (0.22, 0.3), (0, 0, 0), rough=0.8); lp.parent = root
    rp = image_plane("LedgerRight", pages[0], (0.115, 0, 0.012), (0.22, 0.3), (0, 0, 0), rough=0.8); rp.parent = root
    piv = bpy.data.objects.new("LedgerPivot", None); bpy.context.collection.objects.link(piv); piv.parent = root; piv.location = (0, 0, 0.014)
    turn = image_plane("LedgerTurn", pages[1], (0.112, 0, 0.0), (0.22, 0.3), (0, 0, 0), rough=0.8)
    turn.parent = piv
    return {"root": root, "pivot": piv}


def dust_sheets(c):
    """Years later: white dust sheets over the chairs, the cabinet's lower half and the CRT. The phone is left out."""
    sheet_m = fabric("DustSheet", (0.78, 0.77, 0.72), 0.95, 0.5, 400)
    targets = [o for o in bpy.data.objects if o.type == 'MESH' and o.parent and o.parent.name.split(".")[0] in
               ("dining_chair_02", "GreenChair_01", "television_02", "drawer_cabinet")]
    groups = {}
    for o in targets:
        groups.setdefault(o.parent.name, []).append(o)
    for nm, ms in groups.items():
        lo, hi = ph.bounds(ms)
        ctr = (lo + hi) / 2; sz = hi - lo
        bpy.ops.mesh.primitive_cube_add(size=1, location=(ctr.x, ctr.y, (lo.z + hi.z) / 2 + 0.02))
        o = bpy.context.active_object; o.name = "DustSheet"; o.scale = (sz.x + 0.1, sz.y + 0.1, sz.z + 0.04)
        bpy.ops.object.transform_apply(scale=True)
        sub = o.modifiers.new("sub", 'SUBSURF'); sub.levels = 3; sub.render_levels = 3; sub.subdivision_type = 'SIMPLE'
        for v in o.data.vertices:                                     # the skirt flares a little at the floor
            if v.co.z < lo.z + 0.05:
                v.co.x = ctr.x + (v.co.x - ctr.x) * 1.12; v.co.y = ctr.y + (v.co.y - ctr.y) * 1.12; v.co.z = 0.005
        sw = o.modifiers.new("wrap", 'SHRINKWRAP'); sw.target = max(ms, key=lambda m_: len(m_.data.vertices)); sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.offset = 0.025
        sm = o.modifiers.new("smooth", 'CORRECTIVE_SMOOTH'); sm.iterations = 8; sm.factor = 0.7
        tx = bpy.data.textures.new("Folds", 'WOOD'); tx.wood_type = 'BANDNOISE'; tx.noise_scale = 0.18; tx.turbulence = 6
        dp = o.modifiers.new("folds", 'DISPLACE'); dp.texture = tx; dp.strength = 0.03; dp.texture_coords = 'GLOBAL'
        tx2 = bpy.data.textures.new("Wrinkle", 'CLOUDS'); tx2.noise_scale = 0.1
        dp2 = o.modifiers.new("wrinkle", 'DISPLACE'); dp2.texture = tx2; dp2.strength = 0.02; dp2.texture_coords = 'GLOBAL'
        # skirt hangs to the floor: drop the bottom ring
        o.data.materials.append(sheet_m)
        for p_ in o.data.polygons:
            p_.use_smooth = True
        for m_ in ms:
            m_.hide_render = True                                     # under the sheet
        # keep the sheet's shape: wrap to the hull of all parts (single part covers chairs and CRT well enough)
    for o in bpy.data.objects:                                       # the room has been tidied: no papers, no pen
        if o.name.startswith(("Page", "Pen", "binder_notebook")) or (o.parent and o.parent.name.startswith("binder_notebook")):
            o.hide_render = True


# ============================================================================ people per variant
def officer_shirt(name, years, hv=0.3):
    from pbpeople import militia
    return militia(name, years, hv)


def build_people(c, variant):
    P = {}
    if variant == "search":
        P["A"] = person("InvA", 1.0, 46, "male_casualsuit05", "short02", hv=0.3, col=(0.42, 0.3, 0.17))       # camel
        P["B"] = person("InvB", 1.0, 38, "male_casualsuit05", "short04", hv=0.2, col=(0.3, 0.3, 0.31))        # grey
    if variant in ("day", "brother", "visit", "leave"):
        P["banker"] = person("Banker", 1.0, 52, "male_elegantsuit01", "short04", cval=0.1, hv=0.45, sat=0.2)
    if variant == "brother":
        P["brother"] = person("Brother", 1.0, 47, "male_casualsuit03", "short02", cval=0.25, hv=0.25, sat=0.3)
    if variant in ("visit", "alone", "leave"):
        P["visitor"] = person("Visitor", 1.0, 42, "male_elegantsuit01", "short01", cval=0.2, hv=0.15, hue=0.62, sat=0.5)
        bc = briefcase(); c["briefcase"] = bc
    if variant == "sealed":
        for k, (yrs, hair) in enumerate(((40, "short02"), (34, "short04"))):
            from pbpeople import tyvek
            h = tyvek(f"Suit{k}", 1.0, yrs)
            P[f"suit{k}"] = h
        bag_m = pbr("EvidenceBag", (0.95, 0.96, 0.97), 0.08, 0.0, **{'Transmission Weight': 0.9, 'Alpha': 0.55})
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=16, y_subdivisions=20, size=1)
        bag = bpy.context.active_object; bag.name = "EvidenceBag"; bag.scale = (0.26, 0.34, 1); bag.data.materials.append(bag_m)
        for v in bag.data.vertices:
            v.co.z += 0.01 * math.sin(v.co.x * 9) * math.cos(v.co.y * 7)
        so = bag.modifiers.new("t", 'SOLIDIFY'); so.thickness = 0.03
        strip = box("BagStrip", (0, 0.16, 0.0), (0.26, 0.03, 0.032), pbr("BagRed", (0.6, 0.06, 0.05), 0.5)); strip.parent = bag
        c["bag"] = bag
        tr, tm = ph.model("vintage_flashlight"); retint(tm, (0.15, 0.15, 0.15)); c["torch"] = tr
        tl = bpy.data.lights.new("Torch", 'SPOT'); tl.energy = 6; tl.spot_size = math.radians(25); tl.spot_blend = 0.5; tl.color = (1.0, 0.92, 0.8)
        to = bpy.data.objects.new("Torch", tl); bpy.context.collection.objects.link(to); c["torch_light"] = to
    if variant == "ante":
        P["officer"] = officer_shirt("OfficerUnwell", 36)
        r, _ = ph.model("wooden_bucket_02", loc=(ROOM_X + 0.45, DOOR_Y - 0.95, 0), rot_z=0.4)
        r, _ = ph.model("plastic_broom", loc=(ROOM_X + 0.2, DOOR_Y - 1.2, 0), rot_z=0.0)
        r.rotation_euler = (0, math.radians(-12), 0)
    if variant == "ledger":
        P["inv"] = person("InvLedger", 1.0, 44, "male_casualsuit05", "short02", cval=0.14, hv=0.3, sat=0.2)
    c["people"] = P


def briefcase():
    from pbkit import joinm
    lm = pbr("BriefLeather", (0.08, 0.045, 0.025), 0.45, 0.0, **{'Coat Weight': 0.3})
    br = pbr("BriefBrass", (0.6, 0.45, 0.2), 0.3, 1.0)
    return joinm([box("Case", (0, 0, 0), (0.44, 0.11, 0.32), lm, bevel=0.02),
                  box("Handle", (0, 0, 0.185), (0.12, 0.025, 0.03), lm, bevel=0.01),
                  box("Lock", (-0.12, -0.057, 0.13), (0.03, 0.006, 0.02), br), box("Lock", (0.12, -0.057, 0.13), (0.03, 0.006, 0.02), br)], "Briefcase")


# ============================================================================ animation
def tick_clock(c, sec, start=(15, 8, 20)):
    h0, m0, s0 = start
    s = s0 + int(sec)
    for k, o in c["clock_hands"].items():
        if k == "second":
            a = s / 60 * 2 * math.pi
        elif k == "minute":
            a = (m0 + s / 60) / 60 * 2 * math.pi
        else:
            a = (h0 % 12 + (m0 + s / 60) / 60) / 12 * 2 * math.pi
        o.rotation_mode = 'XYZ'; o.rotation_euler = (0, -a, 0)


def handset_home(c):
    if "hs_home" not in c:
        c["hs_home"] = c["handset"].matrix_world.copy()
    return c["hs_home"]


def place_handset(c, mw):
    c["handset"].matrix_world = mw; bpy.context.view_layer.update()


def handset_at_ear(c, h, k=1.0):
    """Handset from the cradle (k = 0) to the person's right ear (k = 1)."""
    home = handset_home(c)
    head = h.bone_head("head"); tl = h.bone_tail("head")
    up = (tl - head).normalized(); f = fwd_of(h); s = Vector((0, 0, 1)).cross(f).normalized()       # s = his left (up x forward)
    ear = head + up * 0.08 + s * 0.085 + f * 0.02
    # handset long axis runs ear (top) to mouth (bottom-front): earpiece end (+Y local) at the ear
    axis = (up * 0.9 + f * 0.6).normalized() * -1                     # from ear down to mouth
    y_ax = -axis; z_ax = s.normalized(); x_ax = y_ax.cross(z_ax).normalized(); z_ax = x_ax.cross(y_ax)
    M = Matrix((x_ax, y_ax, z_ax)).transposed().to_4x4()
    M.translation = ear - y_ax * 0.085 + s * 0.015
    if k >= 1:
        return M
    if k <= 0:
        return home
    lift = home.copy(); lift.translation = home.translation + Vector((0, 0, 0.15))
    q0, q1 = home.to_quaternion(), M.to_quaternion()
    t0, t1 = home.translation, M.translation
    e = ease(k)
    q = q0.slerp(q1, e); t = t0.lerp(t1, e) + Vector((0, 0, 0.12 * math.sin(math.pi * e)))
    R = q.to_matrix().to_4x4(); R.translation = t
    return R


def fwd_of(h):
    return _fwd(h)


def animate(c, sec, move):
    if "clock_hands" in c:
        tick_clock(c, sec)
    fn = ANIM.get(move)
    if fn:
        fn(c, sec)
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- intro
def win_y_blind():
    return 1.4


def a_search(c, sec, turn=0.0, drawer=None, fileo=None):
    a, b = c["people"]["A"], c["people"]["B"]
    stand(a, (-0.72, 2.1, 0), 0.0)
    dr = c["desk_drawers"].get("metal_office_desk_drawer_01") or list(c["desk_drawers"].values())[0]
    dr.location.y = dr["y0"] - 0.3 * (ease(min(1.0, max(0.0, (sec - 0.6) / 1.8))) if drawer is None else drawer)
    nod(a, "spine04", 4 + 2 * turn); nod(a, "neck01", 8 * (1 - turn) + 4 * turn); nod(a, "head", 16 * (1 - turn) + 10 * turn)
    lower = ease(min(1.0, turn * 1.6))
    if "folder" not in c:
        c["folder"] = box("Folder", (0, 0, 0), (0.31, 0.235, 0.004), pbr("Manila", (0.6, 0.48, 0.28), 0.8), bevel=0.001)
        import paper_tex
        from pbkit import image_plane
        pg = image_plane("FolderPage", paper_tex.make_all()["pages"][1], (0.0, 0.0, 0.0025), (0.29, 0.215), (0, 0, math.radians(90)), rough=0.75)
        pg.parent = c["folder"]
    hold_flat(a, c["folder"], dist=0.3 - 0.05 * lower, drop=0.12 + 0.22 * lower, tilt_deg=38 - 28 * lower, spread=0.13, wobble=0.006 * math.sin(sec * 0.8))
    look(a, PHONE, turn)
    stand(b, (FILE_X - 0.9, FILE_Y, 0), math.radians(90))
    fdr = c["file_drawers"][0]
    fdr.location.y = fdr["y0"] - 0.34 * ((0.8 + 0.2 * ease(min(1.0, sec / 2.0))) if fileo is None else fileo)
    bpy.context.view_layer.update()
    lo, hi = ph.bounds([fdr]); top = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))
    nod(b, "spine04", 8); nod(b, "neck01", 8); nod(b, "head", 18)
    hand_to(b, "R", top + Vector((-0.05, -0.08 + 0.05 * math.sin(sec * 1.3), 0.1)), hand_dir=Vector((1, 0, -0.8)), curl=30)
    hand_to(b, "L", top + Vector((-0.08, 0.14, 0.08)), hand_dir=Vector((1, 0, -0.8)), curl=30)


def a_find(c, sec):
    a_search(c, DUR["search"] + sec, turn=ease(min(1.0, max(0.0, (sec - 0.3) / 2.0))), drawer=1.0, fileo=1.0)
    if "beam" not in c:                                         # a shaft of daylight between the slats, sliding onto the phone
        l = bpy.data.lights.new("SunPatch", 'SPOT'); l.energy = 60; l.spot_size = math.radians(9); l.spot_blend = 0.3; l.color = (1.0, 0.9, 0.75)
        o = bpy.data.objects.new("SunPatch", l); bpy.context.collection.objects.link(o); c["beam"] = o
    k = ease(min(1.0, sec / DUR["find"]))
    tgt = (PHONE + Vector((0.45, -0.25, 0.0))).lerp(PHONE + Vector((0.0, 0.0, 0.08)), k)
    c["beam"].location = Vector((-ROOM_X + 0.2, win_y_blind(), 2.2)); point_at(c["beam"], tuple(tgt))


# ---------------------------------------------------------------- chapter 1
def seat_banker(c, slump=0.0, lean=14):
    b = c["people"]["banker"]
    seat(b, (0.0, 2.05, 0), 0.0, lean=lean + 10 * slump)
    return b


def point_hand(h, sd, index=8, others=78, thumb=35):
    """A relaxed pointing hand: index nearly straight, the other fingers folded into the palm, thumb tucked along them.
    Bends about each finger bone's own axis (like curl_local), so a hand turned sideways stays a hand, not a claw."""
    for f in range(2, 6):
        deg = index if f == 2 else others
        for k in (1, 2, 3):
            pb = h.arm.pose.bones.get(f"finger{f}-{k}.{sd}")
            if pb is None:
                continue
            ax = (h.arm.matrix_world.to_3x3() @ pb.matrix.to_3x3()) @ Vector((1, 0, 0))
            h.rot(pb.name, ax, deg * (0.8 if k == 1 else 1.0)); bpy.context.view_layer.update()
    for k in (2, 3):
        pb = h.arm.pose.bones.get(f"finger1-{k}.{sd}")
        if pb is not None:
            ax = (h.arm.matrix_world.to_3x3() @ pb.matrix.to_3x3()) @ Vector((1, 0, 0))
            h.rot(pb.name, ax, thumb); bpy.context.view_layer.update()


def a_dial(c, sec):
    """Ch1 2A: on the phone already, handset in his left hand at his ear, cord hanging to the base; head a little
    bowed toward the phone, his right index finger presses the keys one after another. Shoulders relaxed."""
    b = seat_banker(c)
    nod(b, "neck01", 8); nod(b, "head", 14)
    place_handset(c, handset_at_ear(c, b, 1.0))
    hs = c["handset"].matrix_world
    hand_to(b, "L", hs @ Vector((0.0, -0.01, -0.02)), curl=55)
    # keys: a slow sequence across the keypad, the fingertip dips onto each key and lifts a little between them
    seq = [(1, 0), (0, 1), (2, 2), (1, 1), (0, 3), (2, 1), (1, 2)]
    i = int(sec / 0.42) % len(seq); ph_ = (sec / 0.42) % 1.0
    col, row = seq[i]
    key = c["phone"].matrix_world @ Vector((0.022 + 0.026 * col, -0.024 * row, 0.06))       # top of that key
    dip = 0.018 * (1 - math.sin(math.pi * min(1.0, ph_ / 0.6))) if ph_ < 0.6 else 0.018
    d = Vector((0.12, -0.62, -0.78)).normalized()                         # the hand points away from him and down
    wrist = key - d * 0.165 + Vector((0, 0, dip))                         # wrist one hand-length behind the fingertip
    s = Vector((0, 0, 1)).cross(fwd_of(b)).normalized() * -1             # his right
    hand_to(b, "R", wrist, pole=s * 0.5 + Vector((0, 0, -0.9)), hand_dir=d, curl=0)
    point_hand(b, "R")
    look(b, key, 0.45)


def a_note(c, sec):
    """Ch1 2B: on the phone, he writes a note on the pad."""
    b = seat_banker(c)
    nod(b, "spine04", 6); nod(b, "neck01", 8); nod(b, "head", 16)
    place_handset(c, handset_at_ear(c, b, 1.0))
    hs = c["handset"].matrix_world
    hand_to(b, "L", hs @ Vector((0.0, -0.01, -0.02)), curl=55)
    pen = c.get("pen_obj") or [o for o in bpy.data.objects if o.name.startswith("Pen")][0]; c["pen_obj"] = pen
    tip = Vector((0.08 + 0.05 * ((sec * 0.35) % 1.0), 1.32 - 0.02 * int(sec * 0.35), TOP_Z + 0.012)) + Vector((0, 0, 0.004 * abs(math.sin(sec * 12))))
    pen.location = tip + Vector((0, 0.04, 0.05)); pen.rotation_euler = (math.radians(50), 0, math.radians(10))
    hand_to(b, "R", tip + Vector((0.02, 0.07, 0.06)), hand_dir=Vector((0, -0.6, -0.8)), curl=45)


def a_brother_in(c, sec):
    """Ch1 3A: the door opens; his brother stops on the threshold. He sits slumped, a hand to his temple."""
    b = seat_banker(c, slump=1.0)
    nod(b, "neck01", 12); nod(b, "head", 18)
    hand_to(b, "L", b.bone_head("head") + side_of(b) * 0.06 + fwd_of(b) * 0.05 + Vector((0, 0, 0.02)), curl=30)
    hand_to(b, "R", Vector((-0.25, 1.62, TOP_Z + 0.05)), hand_dir=Vector((0, -0.7, -0.6)), curl=20)
    op = ease(min(1.0, max(0.0, (sec - 0.3) / 1.6)))
    c["door"].rotation_euler = (0, 0, math.radians(-80 * op))
    br = c["people"]["brother"]
    if sec < 1.2:
        walk_at(br, sec * 0.9, (ROOM_X + 0.9 - 0.8 * ease(sec / 1.2), DOOR_Y, 0), math.radians(-90 + 180), stride=18)
    else:
        stand(br, (ROOM_X + 0.1, DOOR_Y, 0), math.radians(90 + 180))     # faces -X, into the room
        look(br, b.bone_head("head"), 1.0)


def side_of(h):
    return Vector((0, 0, 1)).cross(fwd_of(h)).normalized()           # his own left


def a_brother_help(c, sec):
    """Ch1 3B: his brother walks him toward the door, an arm round his back."""
    b, br = c["people"]["banker"], c["people"]["brother"]
    c["door"].rotation_euler = (0, 0, math.radians(-80))
    c["chair"].location = CHAIR_AT_DESK + Vector((0.3, 0.25, 0)); c["chair"].rotation_euler = (0, 0, math.pi + 0.5)
    path0, path1 = Vector((0.9, 0.9, 0)), Vector((2.4, -1.2, 0))
    d = (path1 - path0); face = math.atan2(d.x, -d.y)
    k = min(1.0, sec / 6.0)
    p = path0.lerp(path1, k)
    walk_at(b, sec * 0.55, p, face, stride=10, swing=4)
    nod(b, "spine04", 16); nod(b, "spine03", 8); nod(b, "neck01", 10); nod(b, "head", 18)
    s = Vector((math.cos(face), math.sin(face), 0))                   # walker's right (perpendicular)
    walk_at(br, sec * 0.55 + 0.5, p + s * 0.5, face, stride=10, swing=4)
    look(br, b.bone_head("head"), 0.6)
    hand_to(br, "L", b.bone_head("spine04") + s * 0.12 - fwd_of(b) * 0.12, curl=30)
    hand_to(b, "R", br.bone_head("upperarm01.L") + Vector((0, 0, -0.05)), curl=30)


def a_sealed(c, sec):
    """Ch1 9A: two investigators in protective gear at the desk; one bends with a torch to the handset."""
    s0, s1 = c["people"]["suit0"], c["people"]["suit1"]
    stand(s0, (-0.75, 0.55, 0), math.radians(180 + 25))               # visitor side, facing the phone across the desk
    nod(s0, "spine04", 22); nod(s0, "spine03", 10); nod(s0, "head", 12)
    hp = c["handset"].matrix_world.translation
    sweep = Vector((0.05 * math.sin(sec * 0.7), 0, 0))
    tpos = s0.bone_head("spine03") + fwd_of(s0) * 0.4 + Vector((0, 0, 0.0))
    hand_to(s0, "R", tpos, curl=60)
    torch_at(c, s0.bone_tail("wrist.R"), hp + sweep)
    hand_to(s0, "L", Vector((-0.3, 0.75, TOP_Z + 0.05)), hand_dir=Vector((0, 0.6, -0.8)), curl=15)
    stand(s1, (0.35, 0.35, 0), math.radians(180 - 20))
    nod(s1, "head", 14)
    c["bag"].location = s1.bone_head("spine03") + fwd_of(s1) * 0.3 + Vector((0, 0, -0.2))
    c["bag"].rotation_euler = (math.radians(70), 0, math.radians(-20))
    hand_to(s1, "L", c["bag"].location + Vector((-0.1, 0, 0.12)), curl=40)
    hand_to(s1, "R", c["bag"].location + Vector((0.1, 0, 0.12)), curl=40)
    look(s1, hp, 1.0)


def torch_at(c, hand, aim):
    d = (Vector(aim) - Vector(hand)).normalized()
    tr = c["torch"]; tr.rotation_mode = 'QUATERNION'; tr.rotation_quaternion = (-d).to_track_quat('Y', 'Z'); tr.location = hand
    lo = c["torch_light"]; lo.location = Vector(hand) + d * 0.16
    lo.rotation_mode = 'QUATERNION'; lo.rotation_quaternion = (-d).to_track_quat('Z', 'Y')


def a_bag(c, sec):
    """Ch1 9B: he lifts the handset and lowers it into the open evidence bag his colleague holds."""
    s0, s1 = c["people"]["suit0"], c["people"]["suit1"]
    stand(s0, (-0.55, 0.45, 0), math.radians(180 + 10))
    stand(s1, (-0.05, 0.42, 0), math.radians(180 - 25))
    nod(s0, "spine04", 14); nod(s0, "head", 14); nod(s1, "spine04", 10); nod(s1, "head", 16)
    c["torch"].hide_render = True; c["torch_light"].data.energy = 0
    bagc = Vector((-0.3, 0.62, 1.05))
    c["bag"].location = bagc; c["bag"].rotation_euler = (math.radians(80), 0, math.radians(15))
    hand_to(s1, "L", bagc + Vector((-0.12, 0.0, 0.16)), curl=50); hand_to(s1, "R", bagc + Vector((0.12, 0.0, 0.16)), curl=50)
    home = handset_home(c)
    k = ease(min(1.0, max(0.0, (sec - 0.5) / 2.6)))
    up = home.copy(); up.translation = home.translation + Vector((0, 0, 0.25))
    inbag = Matrix.Translation(bagc + Vector((0, -0.01, 0.02))) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Rotation(math.radians(90), 4, 'Z')
    if k < 0.4:
        M = matlerp(home, up, k / 0.4)
    else:
        M = matlerp(up, inbag, (k - 0.4) / 0.6)
    place_handset(c, M)
    hand_to(s0, "R", c["handset"].matrix_world @ Vector((0, 0.0, 0.03)), curl=50)
    hand_to(s0, "L", s0.bone_head("spine03") + fwd_of(s0) * 0.25 + Vector((0, 0, -0.25)), curl=20)


def matlerp(A, B, t):
    t = max(0.0, min(1.0, t)); e = ease(t)
    q = A.to_quaternion().slerp(B.to_quaternion(), e)
    M = q.to_matrix().to_4x4(); M.translation = A.translation.lerp(B.translation, e)
    return M


def a_ante_desk(c, sec):
    c["door"].rotation_euler = (0, 0, math.radians(-30))
    for o in bpy.data.objects:
        if o.name.split(".")[0] in ("wooden_bucket_02", "plastic_broom") or (o.parent and o.parent.name.split(".")[0] in ("wooden_bucket_02", "plastic_broom")):
            o.hide_render = True
    for s_ in c["seal"]:
        s_.hide_render = True
    hide(c["people"]["officer"], True)


def a_ante(c, sec):
    """Ch1 10B: the sealed door, a cleaner's bucket and mop left beside it; an officer leans on the wall, unwell."""
    o = c["people"]["officer"]
    stand(o, (ROOM_X + 0.55, -0.35, 0), math.radians(-90 + 20))       # faces -X, turned slightly toward camera
    nod(o, "spine04", 14); nod(o, "spine03", 6); nod(o, "neck01", 12); nod(o, "head", 18 + 2 * math.sin(sec * 0.6))
    hand_to(o, "R", Vector((ROOM_X + 0.12, -0.55, 1.45)), hand_dir=Vector((-1, 0, 0.2)), curl=10)       # palm on the wall
    hand_to(o, "L", o.bone_head("spine02") + fwd_of(o) * 0.08 + Vector((0, 0, 0.02)), curl=40)            # hand to his stomach
    for s_ in c["seal"]:
        s_.hide_render = False
    c["door"].rotation_euler = (0, 0, 0)


def a_ledger(c, sec):
    """Ch1 12A: an investigator at the secretary's desk turns the pages of the visitor ledger."""
    inv = c["people"]["inv"]
    seat(inv, (AX0 + 2.45, -0.35, 0), math.radians(-90), lean=16)            # faces -X, the desk
    nod(inv, "neck01", 10); nod(inv, "head", 18)
    L = c["ledger"]; root = L["root"]
    period = 2.4; ph_ = (sec % period) / period
    ang = math.radians(180) * ease(min(1.0, max(0.0, (ph_ - 0.35) / 0.4)))
    L["pivot"].rotation_euler = (0, -ang, 0)
    edge = L["pivot"].matrix_world @ (Matrix.Rotation(-ang, 4, 'Y') @ Vector((0.2, 0.08, 0.0)))
    edge = root.matrix_world @ Vector((0.21 * math.cos(ang), 0.08, 0.012 + 0.21 * math.sin(ang)))
    hand_to(inv, "R", edge + Vector((0.03, 0, 0.04)), hand_dir=Vector((-1, 0, -0.5)), curl=30)
    hand_to(inv, "L", root.matrix_world @ Vector((-0.15, -0.05, 0.05)), hand_dir=Vector((-1, 0, -0.6)), curl=20)


# ---------------------------------------------------------------- chapter 2
def a_visitor_in(c, sec):
    """Ch2 1A: the board member walks in with a briefcase; the banker looks up from his desk."""
    b = seat_banker(c)
    vis = c["people"]["visitor"]
    c["door"].rotation_euler = (0, 0, math.radians(-80))
    p0, p1 = Vector((ROOM_X + 0.4, DOOR_Y, 0)), Vector((0.9, 0.0, 0))
    k = min(1.0, sec / 4.5)
    d = p1 - p0; face = math.atan2(d.x, -d.y)
    if k < 1.0:
        walk_at(vis, sec * 0.95, p0.lerp(p1, ease(k) * 0.3 + k * 0.7), face, stride=22, swing=10)
    else:                                                                       # arrived: he stops (no walking on the spot)
        stand(vis, p1, face); look(vis, b.bone_head("head"), 0.6)
    c["briefcase"].location = vis.bone_tail("wrist.R") + Vector((0, 0, -0.22)); c["briefcase"].rotation_euler = (0, 0, face)
    nod(b, "head", 8); look(b, vis.bone_head("head"), 0.7)
    hand_to(b, "L", Vector((0.15, 1.5, TOP_Z + 0.05)), hand_dir=Vector((0, -0.7, -0.6)), curl=20)
    hand_to(b, "R", Vector((-0.15, 1.5, TOP_Z + 0.05)), hand_dir=Vector((0, -0.7, -0.6)), curl=20)


def a_across(c, sec):
    """Ch2 1B: the two men across the desk, papers between them; the banker taps a page."""
    b = seat_banker(c)
    vis = c["people"]["visitor"]
    seat(vis, (-0.75, 0.05, 0), math.pi + 0.35, lean=16)
    c["briefcase"].location = (-0.35, -0.15, 0.16); c["briefcase"].rotation_euler = (0, 0, 0.3)
    nod(b, "neck01", 6); nod(b, "head", 12)
    tap = 0.01 * max(0.0, math.sin(sec * 3.0))
    hand_to(b, "R", Vector((-0.05, 1.12, TOP_Z + 0.04 + tap)), hand_dir=Vector((0, -0.8, -0.6)), curl=40)
    hand_to(b, "L", Vector((0.25, 1.45, TOP_Z + 0.05)), hand_dir=Vector((0, -0.7, -0.6)), curl=20)
    look(vis, Vector((-0.05, 1.12, TOP_Z)), 0.6); nod(vis, "head", 14)
    hand_to(vis, "R", Vector((-0.5, 0.78, TOP_Z + 0.05)), hand_dir=Vector((0, 0.7, -0.6)), curl=25)


def a_alone(c, sec, read=0.0):
    """Ch2 2A/2B: the visitor alone by the desk; the banker's chair empty. In 2B he picks up the papers and reads."""
    vis = c["people"]["visitor"]
    c["briefcase"].location = (-0.95, 0.25, 0.16); c["briefcase"].rotation_euler = (0, 0, 0.6)
    stand(vis, (-0.95, 0.62, 0), math.radians(180 + 30))
    if read <= 0:
        nod(vis, "head", 10); look(vis, Vector((ROOM_X, DOOR_Y, 1.5)), 0.35 + 0.15 * math.sin(sec * 0.5))
        hand_to(vis, "R", Vector((-0.75, 0.8, TOP_Z + 0.04)), hand_dir=Vector((0.3, 0.7, -0.6)), curl=15)
    else:
        if "papers" not in c:
            import paper_tex
            from pbkit import image_plane
            c["papers"] = image_plane("SharePapers", paper_tex.make_all()["pages"][4 % len(paper_tex.make_all()["pages"])], (0, 0, 0), (0.21, 0.28), (0, 0, 0), rough=0.75)
        k = ease(min(1.0, sec / 1.5))
        nod(vis, "neck01", 8); nod(vis, "head", 16)
        hold_flat(vis, c["papers"], dist=0.3, drop=0.05 + 0.3 * (1 - k), tilt_deg=60, spread=0.1, wobble=0.006 * math.sin(sec))


def a_leave(c, sec):
    """Ch2 8A: the banker gets up and walks out; the visitor stays by the desk."""
    b, vis = c["people"]["banker"], c["people"]["visitor"]
    c["chair"].location = CHAIR_AT_DESK + Vector((0.35, 0.2, 0)); c["chair"].rotation_euler = (0, 0, math.pi + 0.6)
    p0, p1 = Vector((0.75, 1.75, 0)), Vector((ROOM_X + 0.3, DOOR_Y, 0))
    k = min(1.0, sec / 5.0)
    d = p1 - p0; face = math.atan2(d.x, -d.y)
    walk_at(b, sec * 0.9, p0.lerp(p1, k), face, stride=22, swing=12)
    c["door"].rotation_euler = (0, 0, math.radians(-80))
    stand(vis, (-0.95, 0.62, 0), math.radians(180 + 30))
    look(vis, b.bone_head("head"), 0.8)
    c["briefcase"].location = (-0.95, 0.25, 0.16); c["briefcase"].rotation_euler = (0, 0, 0.6)


def a_glance(c, sec):
    """Ch2 8B: alone, he glances back at the open door."""
    vis = c["people"]["visitor"]
    c["briefcase"].location = (-0.95, 0.25, 0.16); c["briefcase"].rotation_euler = (0, 0, 0.6)
    stand(vis, (-0.95, 0.75, 0), math.radians(180 + 40))
    g = ease(min(1.0, max(0.0, (sec - 0.6) / 1.0))) * (1 - ease(min(1.0, max(0.0, (sec - 2.8) / 1.0))))
    look(vis, Vector((ROOM_X, DOOR_Y, 1.5)), g)
    nod(vis, "head", 6 + 8 * (1 - g))


ANIM = {"search": a_search, "find": a_find, "dial": a_dial, "note": a_note, "brother_in": a_brother_in, "brother_help": a_brother_help,
        "sealed": a_sealed, "bag": a_bag, "ante_desk": lambda c, s: a_ante_desk(c, s), "ante_trolley": a_ante, "ledger": a_ledger,
        "visitor_in": a_visitor_in, "across": a_across, "alone": a_alone, "reads": lambda c, s: a_alone(c, s, 1.0),
        "steps_out": a_leave, "glance": a_glance}


# ============================================================================ cameras and moves
def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


def cam_handset(c, t):
    """Hold on the handset (the 2.5 s lead-in is the first ~32 %), then a slow push."""
    hold = 2.5 / DUR["handset"]
    e = ease(max(0.0, (t - hold) / (1 - hold)))
    tgt = handset_home(c).translation + Vector((0, 0, 0.0))
    start = tgt + Vector((-0.6, -0.8, 0.42)); end = tgt + Vector((-0.4, -0.53, 0.27))
    return (start.lerp(end, e), tgt, 50)


def cam_match(c, t):
    tgt = handset_home(c).translation
    return (tgt + Vector((-0.5, -0.66, 0.35)).lerp(Vector((-0.36, -0.48, 0.25)), ease(t)), tgt, 50)


def cam_bag(c, t):
    e = ease(t); tgt = Vector((-0.3, 0.55, 1.3))
    return (Vector((-1.6, 2.6, 1.7)).lerp(Vector((-1.45, 2.4, 1.66)), e), tgt, 30)


def cam_find(c, t):
    e = ease(t)
    tgt = PHONE + Vector((0.0, 0.0, 0.05))
    return (Vector((-1.55, 2.7, 2.05)).lerp(Vector((-1.25, 2.3, 1.7)), e), tgt, 38 + 10 * e)


def cam_glance(c, t):
    """From behind the desk: his glance to the door, then the focus slides to the phone in the foreground."""
    e = ease(t)
    start = Vector((0.2, 2.6, 1.5)); end = Vector((0.0, 2.4, 1.42))
    tgt = Vector((-0.85, 0.85, 1.3)).lerp(Vector((-0.75, 1.0, 1.22)), ease(max(0.0, (t - 0.4) / 0.6)))
    return (start.lerp(end, e), tgt, 25 + 3 * e)


DUR = {"handset": 7.8, "empty": 9.0, "search": 6.5, "find": 5.0,
       "dial": 5.5, "note": 5.5, "brother_in": 6.0, "brother_help": 6.0, "sealed": 5.5, "door_push": 6.0, "bag": 5.0,
       "ante_desk": 6.5, "ante_trolley": 6.5, "ledger": 5.0,
       "visitor_in": 5.0, "across": 5.0, "alone": 5.5, "reads": 5.5, "steps_out": 5.0, "glance": 6.0,
       "match": 5.0, "dust": 6.0}
VARIANT_FOR = {"handset": "empty", "empty": "empty", "search": "search", "find": "search", "dial": "day", "note": "day",
               "brother_in": "brother", "brother_help": "brother", "sealed": "sealed", "bag": "sealed",
               "ante_desk": "ante", "ante_trolley": "ante", "ledger": "ledger", "door_push": "empty",
               "visitor_in": "visit", "across": "visit", "alone": "alone", "reads": "alone", "steps_out": "leave", "glance": "alone",
               "match": "empty", "dust": "dust"}


def _anim(move):
    return lambda c, t: animate(c, t * DUR[move], move)


A = ROOM_X
MOVES = {
    # intro
    "handset": dict(kind="anim", dof=2.0, far=10.0, cam=cam_handset, anim=_anim("handset"), focus=lambda c, t: handset_home(c).translation),
    "empty": dict(kind="anim", dof=5.6, far=12.0, anim=_anim("empty"), cam=_push((2.55, -2.55, 1.62), (1.85, -2.6, 1.6), (-0.3, 1.3, 0.95), (-0.6, 1.3, 0.95), 24),
                  focus=lambda c, t: DESK + Vector((0, 0, 0.9))),
    "search": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("search"), cam=_push((-2.3, -2.2, 1.62), (-2.0, -1.85, 1.6), (0.9, 1.3, 1.1), (0.8, 1.35, 1.1), 24),
                   focus=lambda c, t: Vector((-0.7, 1.9, 1.3))),
    "find": dict(kind="anim", dof=2.4, far=10.0, cam=cam_find, anim=_anim("find"), focus=lambda c, t: PHONE + Vector((0, 0, 0.05))),
    # chapter 1
    "dial": dict(kind="anim", dof=3.2, far=12.0, anim=_anim("dial"), cam=_push((-2.0, 0.1, 1.45), (-1.75, 0.35, 1.42), (-0.1, 1.85, 1.1), (-0.05, 1.9, 1.12), 35),
                 focus=lambda c, t: Vector((0.0, 1.95, 1.2))),
    "note": dict(kind="anim", dof=2.8, far=10.0, anim=_anim("note"), cam=_push((-1.0, 2.75, 1.75), (-0.85, 2.62, 1.7), (0.05, 1.3, 0.85), (0.1, 1.3, 0.85), 35),
                 focus=lambda c, t: Vector((0.1, 1.35, 0.85))),
    "brother_in": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("brother_in"), cam=_push((-1.6, 2.55, 1.55), (-1.35, 2.5, 1.5), (2.2, -1.2, 1.3), (2.4, -1.4, 1.3), 30),
                       focus=lambda c, t: Vector((1.5, -0.3, 1.3))),
    "brother_help": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("brother_help"), cam=_push((-0.9, 2.3, 1.6), (-0.5, 1.9, 1.58), (1.6, 0.1, 1.2), (2.6, -1.2, 1.2), 28),
                         focus=lambda c, t: Vector((0.9, 0.9, 1.2)).lerp(Vector((2.2, -0.9, 1.2)), ease(t))),
    "sealed": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("sealed"), cam=_push((-2.4, -1.7, 1.65), (-2.1, -1.4, 1.62), (-0.2, 1.0, 1.0), (-0.3, 1.1, 1.0), 28),
                   focus=lambda c, t: Vector((-0.5, 0.8, 1.2))),
    "bag": dict(kind="anim", dof=2.8, far=10.0, anim=_anim("bag"), cam=cam_bag, focus=lambda c, t: Vector((-0.3, 0.62, 1.05))),
    "ante_desk": dict(kind="anim", dof=3.2, far=12.0, anim=_anim("ante_desk"),
                      cam=_push((A + 3.25, 0.35, 1.35), (A + 3.0, 0.25, 1.32), (A + 1.1, -1.0, 0.85), (A + 1.0, -1.1, 0.88), 26),
                      focus=lambda c, t: Vector((A + 1.95, -0.3, 0.95))),
    "ante_trolley": dict(kind="anim", dof=3.6, far=12.0, anim=_anim("ante_trolley"),
                         cam=_push((A + 3.3, 0.3, 1.55), (A + 3.05, 0.15, 1.52), (A + 0.3, -1.7, 1.05), (A + 0.35, -1.6, 1.05), 28),
                         focus=lambda c, t: Vector((A + 0.6, -0.4, 1.3))),
    "ledger": dict(kind="anim", dof=2.8, far=10.0, anim=_anim("ledger"),
                   cam=_push((A + 0.7, -1.6, 1.5), (A + 0.85, -1.4, 1.45), (A + 2.0, -0.35, 1.0), (A + 2.05, -0.35, 1.0), 35),
                   focus=lambda c, t: Vector((A + 1.9, -0.4, 0.95))),
    "door_push": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("empty"), cam=_push((A + 0.6, DOOR_Y, 1.6), (1.4, -0.4, 1.35), PHONE + Vector((0, 0.3, 0.2)), PHONE + Vector((0, 0.2, 0.05)), 30),
                      focus=lambda c, t: PHONE),
    # chapter 2
    "visitor_in": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("visitor_in"), title=("CHAPTER 2", "THE MAN IN THE OFFICE", 12, 120), cam=_push((-1.4, 2.6, 1.6), (-1.25, 2.45, 1.58), (1.8, -0.8, 1.3), (1.2, -0.3, 1.3), 28),
                       focus=lambda c, t: Vector((2.6, -1.4, 1.3)).lerp(Vector((1.1, -0.1, 1.3)), ease(t))),
    "across": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("across"), cam=_push((-2.5, 1.1, 1.4), (-2.3, 1.0, 1.38), (0.0, 1.0, 1.0), (0.0, 1.05, 1.0), 30),
                   focus=lambda c, t: Vector((-0.2, 1.0, 1.0))),
    "alone": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("alone"), cam=_push((2.2, -2.4, 1.6), (1.9, -2.2, 1.58), (-0.6, 1.0, 1.2), (-0.7, 1.05, 1.2), 30),
                  focus=lambda c, t: Vector((-0.95, 0.62, 1.4))),
    "reads": dict(kind="anim", dof=2.8, far=10.0, anim=_anim("reads"), cam=_push((-2.75, 2.45, 1.6), (-2.6, 2.3, 1.58), (-0.95, 0.62, 1.3), (-0.95, 0.62, 1.28), 32),
                  focus=lambda c, t: Vector((-0.95, 0.62, 1.4))),
    "steps_out": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("steps_out"), cam=_push((-2.4, 2.5, 1.6), (-2.2, 2.3, 1.58), (1.2, -0.4, 1.2), (2.4, -1.3, 1.3), 26),
                      focus=lambda c, t: Vector((1.0, 0.8, 1.3)).lerp(Vector((3.0, -1.5, 1.3)), ease(t))),
    "glance": dict(kind="anim", dof=3.2, far=10.0, anim=_anim("glance"), cam=cam_glance,
                   focus=lambda c, t: Vector((-0.95, 0.75, 1.5)).lerp(PHONE, ease(max(0.0, (t - 0.35) / 0.65)))),
    # chapter 3
    "match": dict(kind="anim", dof=2.0, far=10.0, cam=cam_match, anim=_anim("match"), focus=lambda c, t: handset_home(c).translation),
    "dust": dict(kind="anim", dof=5.6, far=12.0, anim=_anim("dust"), cam=_push((2.5, -2.6, 1.55), (2.1, -2.5, 1.5), (-0.3, 1.3, 0.9), (-0.5, 1.3, 0.85), 26),
                 focus=lambda c, t: PHONE),
}


_build_set = build


def build(variant=None):
    c = _build_set(variant)
    from pbkit import finish_scene
    import pblook
    pblook.apply("sc_bankoffice", variant)                 # the house cinematic light (HOUSE_LOOK=plain for the old)
    finish_scene()
    return c
