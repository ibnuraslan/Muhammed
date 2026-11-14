"""Typewriters thumbnail B: one cream golf-ball typewriter on the night desk, its lower case X-ray clear, the hidden
bar inside glowing Seldom lime. Dark office, haze, one hard beam. Built from the film's own set
(claude/typewriters: projects/typewriters/scenes/sc_twoffice.py, typewriter.py)."""
import math
import bpy
from mathutils import Vector
from common import area_light, point_at

CREAM = (0.62, 0.58, 0.50)
LIMEC = (0.88, 0.97, 0.0)


def _spot(name, loc, tgt, energy, color, deg=30, blend=0.5, soft=0.05):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color
    l.spot_size = math.radians(deg); l.spot_blend = blend; l.shadow_soft_size = soft
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt)
    return o


def _w(c, p):
    import typewriter as T
    return T.world(c["tw"], p)


def _emit(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N):
        if n.type != 'OUTPUT_MATERIAL':
            N.remove(n)
    e = N.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    L.new(e.outputs[0], next(n for n in N if n.type == 'OUTPUT_MATERIAL').inputs['Surface'])
    return m


def swap_machine(c):
    """Replace the film's desk machine with a cream, bugged one in the same spot."""
    import typewriter as T, sc_twoffice as S
    old = c["tw"]["root"]
    loc, rz = old.location.copy(), old.rotation_euler.z
    for o in [old] + list(old.children_recursive):
        o.hide_render = True; o.hide_viewport = True
    tw = T.make("TWX", loc=tuple(loc), rot_z=rz, color=CREAM, bugged=True, text=S.TEXT_P, dpi=400, seed=0)
    c["tw"] = tw
    for o in tw["root"].children_recursive:          # no sheet: it would cover the title
        if any(k in o.name for k in ("Paper", "Page", "Bail")) or o is tw.get("paper"):
            o.hide_render = True
    return tw


def setup(c, xray=True):
    from kit import haze
    import typewriter as T
    tw = swap_machine(c)
    if not xray:
        return _rest(c, tw, xray)
    # X-ray: the lower case and side towers go mostly clear, so the bar inside shows; keys and platen stay solid
    lower = [o for o in tw["shell"] if o.name.startswith(("TWX_Lower", "TWX_Side"))]
    T.xray_shell(tw, expr="0.93", objs=lower, tint=LIMEC)
    glow = _emit("BugGlow", LIMEC, 10.0); hot = _emit("BugHot", (0.95, 1.0, 0.55), 20.0)
    for o in tw["bug_parts"]:
        o.data = o.data.copy(); o.data.materials.clear(); o.data.materials.append(hot if "Chip" in o.name else glow)
    for o in (tw["bar"], tw["bar_lid"]):
        o.data = o.data.copy(); o.data.materials.clear(); o.data.materials.append(_emit("BarGlow", LIMEC, 5.0))
    _rest(c, tw, xray)


def _rest(c, tw, xray):
    from kit import haze
    import typewriter as T
    bl = bpy.data.lights.new("BugLight", 'AREA'); bl.energy = 10; bl.size = 0.3; bl.shape = 'RECTANGLE'; bl.size_y = 0.03
    bl.color = LIMEC; bo = bpy.data.objects.new("BugLight", bl); bpy.context.collection.objects.link(bo)
    bo.location = _w(c, (0, T.BAR_Y, T.BAR_Z + 0.03)) if xray else _w(c, (0, -0.1, 0.004))
    if not xray:                                     # solid machine: the glow leaks out from under it onto the desk
        bl.energy = 25; bl.size = 0.42; bl.size_y = 0.3; bo.rotation_euler = (0, 0, 0); bo.rotation_euler = c["tw"]["root"].rotation_euler
    p0 = _w(c, (0, 0, 0))
    for o in bpy.data.objects:                       # chairs and clutter between the camera and the machine
        n = o.name.lower()
        if o.type == 'MESH' and ("chair" in n or "stationery" in n or "notepad" in n or "pen" in n.split("_")[0]):
            if (o.matrix_world.translation - p0).length < 3.5:
                o.hide_render = True
    bpy.context.scene.view_settings.exposure = -1.2
    # night room down, one hard beam, haze
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and not o.name.startswith("BugLight"):
            o.data.energy *= 0.15
    w = bpy.context.scene.world
    if w and w.node_tree:
        for n in w.node_tree.nodes:
            if n.type == 'BACKGROUND':
                n.inputs['Strength'].default_value *= 0.05
    p = _w(c, (0, 0, 0.1))
    haze(p + Vector((0, 0, 0.6)), (5.0, 5.0, 2.4), density=0.02, color=(0.95, 0.9, 0.85), anis=0.55)
    _spot("TopBeam", p + Vector((0.2, 0.3, 1.9)), p, 700, (1.0, 0.93, 0.84), 16, 0.35, 0.03)
    k = area_light(_w(c, (-0.7, -0.8, 0.4)), (0, 0, 0), 0.6, 10, (0.85, 0.9, 1.0)); point_at(k, p)
    rim = area_light(_w(c, (0.6, 0.7, 0.35)), (0, 0, 0), 0.4, 25, (1.0, 0.8, 0.6)); point_at(rim, p)


def cam(c):
    return (_w(c, (0.38, -0.98, 0.36)), _w(c, (0.0, -0.02, 0.07)), 40)


def machine(c):
    r = c["tw"]["root"]
    return [o for o in r.children_recursive if o.type in ('MESH', 'CURVE', 'FONT') and not o.hide_render]


CONCEPTS = {
    "tw_solid": dict(scene="twoffice", variant="night", cam=cam, shift=(0.0, 0.15), focus=lambda c: _w(c, (0, -0.06, 0.08)),
                     fstop=2.8, setup=lambda c: setup(c, xray=False), exposure=-1.2, mask=machine),
    "tw_b": dict(scene="twoffice", variant="night", cam=cam, shift=(0.0, 0.15), focus=lambda c: _w(c, (0, -0.06, 0.08)),
                 fstop=2.8, setup=setup, exposure=-1.2, mask=machine),
}


# ---------------------------------------------------------------- layout D: the two sides, the typewriter between them
import os
HERE = os.path.dirname(os.path.abspath(__file__))


def flag_images():
    """A Soviet flag (red, gold star + hammer and sickle) and a US flag (13 stripes, 50 stars), drawn flat."""
    from PIL import Image, ImageDraw
    out = os.path.join(HERE, "plates"); os.makedirs(out, exist_ok=True)
    W_, H_ = 1500, 750
    def star(d, cx, cy, r, fill, outline=False):
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.382
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=None if outline else fill, outline=fill, width=max(2, int(r * 0.12)) if outline else 1)
    su = Image.new("RGB", (W_, H_), (204, 0, 0)); d = ImageDraw.Draw(su); g = (255, 216, 0)
    star(d, 250, 95, 45, g, outline=True)
    # sickle: a thick crescent; hammer: a handle and a head across it
    d.pieslice([140, 150, 360, 370], 200, 470, fill=g); d.pieslice([170, 165, 345, 340], 190, 480, fill=(204, 0, 0))
    d.polygon([(150, 330), (175, 355), (205, 325), (180, 300)], fill=g)
    d.line([(190, 345), (325, 210)], fill=g, width=22)
    d.polygon([(285, 170), (345, 230), (370, 205), (310, 145)], fill=g)
    us = Image.new("RGB", (W_, H_), (255, 255, 255)); d = ImageDraw.Draw(us)
    sh = H_ / 13
    for k in range(13):
        if k % 2 == 0:
            d.rectangle([0, k * sh, W_, (k + 1) * sh], fill=(178, 34, 52))
    cw, chh = W_ * 0.4, sh * 7
    d.rectangle([0, 0, cw, chh], fill=(60, 59, 110))
    for r in range(9):
        n = 6 if r % 2 == 0 else 5
        for k in range(n):
            x = cw / 12 * (2 * k + 1 + (r % 2)); y = chh / 10 * (r + 1)
            star(d, x, y, chh / 22, (255, 255, 255))
    a, b = os.path.join(out, "flag_su.png"), os.path.join(out, "flag_us.png")
    su.save(a); us.save(b)
    return a, b


def flag(name, img, loc, rot_z, size=(1.5, 1.0)):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=90, y_subdivisions=60, size=1, location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale = (size[0], size[1], 1); o.rotation_euler = (math.pi / 2, 0, rot_z)
    tx = bpy.data.textures.new(name + "Folds", 'WOOD'); tx.wood_type = 'BANDNOISE'; tx.noise_scale = 0.35; tx.turbulence = 4
    tx.noise_basis_2 = 'SIN'
    m_ = o.modifiers.new("folds", 'DISPLACE'); m_.texture = tx; m_.strength = 0.035; m_.texture_coords = 'LOCAL'
    o.modifiers.new("sub", 'SUBSURF').levels = 1
    bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new(name + "Mat"); m.use_nodes = True
    N = m.node_tree.nodes; pb = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(img); t.extension = 'EXTEND'
    m.node_tree.links.new(t.outputs[0], pb.inputs['Base Color'])
    pb.inputs['Roughness'].default_value = 0.75; pb.inputs['Sheen Weight'].default_value = 0.5
    o.data.materials.append(m)
    return o


def leader(name, loc, rot, turn, desk_z):
    from mathutils import Matrix
    from human import Human, add_asset, reach, fingers_curl, _world_verts
    import numpy as np
    h = Human(name, gender=1.0, years=68, muscle=0.45, weight=0.6, height=0.45,
              skin="old_lightskinned_male_diffuse.png", eyebrows="eyebrow002", eyelashes="eyelashes01")
    add_asset(h, "clothes", "male_elegantsuit01", sat=0.1, val=0.1, rough=0.55, sheen=0.3)
    add_asset(h, "clothes", "shoes02", val=0.15, rough=0.3)
    add_asset(h, "hair", "short02", sat=0.0, val=0.8, rough=0.8)
    for o in h.parts:
        for m in (o.data.materials if o.data else []):
            if m and "short02" in m.name:
                m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    h.rot("neck01", (0, 0, 1), turn * 0.4); h.rot("head", (0, 0, 1), turn * 0.6)
    h.arm.location = loc; h.arm.rotation_euler = (0, 0, rot)
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z += 0.0 - w[:, 2].min(); bpy.context.view_layer.update()
    R = Matrix.Rotation(rot, 3, 'Z'); f = R @ Vector((0, -1, 0)); ax = tuple(Vector((0, 0, 1)).cross(f))
    for b, d in (("spine03", 7), ("spine02", 8), ("spine01", 6)):     # leaning in over the desk
        h.rot(b, ax, d)
    h.rot("neck01", ax, 6); h.rot("head", ax, 12)
    bpy.context.view_layer.update()
    base = Vector(loc); base.z = desk_z
    for sd, sg in (("L", 1), ("R", -1)):                    # both palms flat on the desk
        tgt = base + R @ Vector((0.21 * sg, -0.33, 0.035))
        reach(h, sd, tgt, tuple(R @ Vector((0.8 * sg, 0.3, -0.2))), hand_dir=tuple(R @ Vector((0.15 * sg, -1.0, -0.25))))
    fingers_curl(h, 8, thumb=10)
    return h


def setup_leaders(c):
    setup(c)
    rz = c["tw"]["root"].rotation_euler.z
    fsu, fus = flag_images()
    for o in bpy.data.objects:                              # clear the back of the room behind the two men
        n = o.name.lower()
        if o.type == 'MESH' and ("chair" in n or "plant" in n or "clock" in n or "lamp" in n or "notepad" in n or "stationery" in n):
            o.hide_render = True
        if o.name.startswith(("TW1", "TW2", "TWside")):
            o.hide_render = True
        if "desk" in n and o.type == 'MESH' and (o.matrix_world.translation - _w(c, (0, 0, 0))).length > 1.0:
            o.hide_render = True
    for m in bpy.data.materials:                            # thinner haze: no purple fog over the wall
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.type in ('PRINCIPLED_VOLUME', 'VOLUME_SCATTER') and 'Density' in n.inputs:
                    n.inputs['Density'].default_value *= 0.2
    from kit import pbr
    dark = pbr("DarkWall", (0.035, 0.034, 0.033), 0.85)
    for o in bpy.data.objects:                              # the long lens sits back past the wall behind the camera
        if o.name.startswith(("WallBack", "Window", "Blind", "Venetian")):
            o.hide_render = True
        if o.name.startswith(("WallL", "WallR", "WallFront", "Floor")) and o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(dark)
    for o in bpy.data.objects:                              # loose sheets left on the hidden back desks
        if o.type == 'MESH' and o.name.startswith("Plane") and (o.matrix_world.translation - _w(c, (0, 0, 0))).length > 1.0:
            o.hide_render = True
    for sd, img, col, x in ((-1, fsu, (1.0, 0.12, 0.08), -0.62), (1, fus, (0.25, 0.45, 1.0), 0.62)):
        h = leader("Leader" + ("SU" if sd < 0 else "US"), _w(c, (x, 0.66, 0)) - Vector((0, 0, _w(c, (0, 0, 0)).z)), rz - sd * 0.5, sd * -22, _w(c, (0, 0, 0)).z)
        flag("Flag" + ("SU" if sd < 0 else "US"), img, _w(c, (x + sd * 0.15, 1.6, 0.85)), rz + math.pi - sd * 0.25)
        hd = h.bone_head("head")
        rim = area_light(hd + (_w(c, (sd * 0.9, 1.0, 0.25)) - _w(c, (0, 0, 0))), (0, 0, 0), 0.5, 140, col); point_at(rim, hd)
        rim.visible_camera = False
        wash = _spot("Wash" + str(sd), _w(c, (x, 0.6, 1.6)) , _w(c, (x + sd * 0.25, 1.75, 0.2)), 30, col, 45, 0.8, 0.2)
        fill = area_light(hd + (_w(c, (-sd * 0.2, -1.2, 0.0)) - _w(c, (0, 0, 0))), (0, 0, 0), 0.8, 1.2, (1.0, 0.9, 0.8)); point_at(fill, hd)
        fill.visible_camera = False
        c.setdefault("leaders", []).append(h)


def cam_leaders(c):
    return (_w(c, (0.0, -2.55, 0.66)), _w(c, (0.0, 0.3, 0.42)), 52)


def machine_and_men(c):
    return machine(c) + [o for h in c.get("leaders", []) for o in h.parts if o.type == 'MESH']


CONCEPTS["tw_leaders"] = dict(scene="twoffice", variant="night", cam=cam_leaders, shift=(0.0, 0.0), focus=lambda c: _w(c, (0, -0.06, 0.08)),
                              fstop=4.0, setup=setup_leaders, exposure=-1.2, mask=machine)


# ---------------------------------------------------------------- layout C2: the headline painted on a wall behind the desk
def headline_image(path, W_=3600, H_=880):
    """White headline, SOVIETS and AMERICA in Seldom lime, transparent background (Anton)."""
    from PIL import Image, ImageDraw, ImageFont
    F = os.path.join(HERE, "..", "..", "assets", "fonts", "Anton-Regular.ttf")
    im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F, 420)
    tl = d.textlength("THE SOVIETS SPIED ON AMERICA", font=f)
    f = ImageFont.truetype(F, int(420 * min(1.0, (W_ * 0.96) / tl)))
    WH, LI = (242, 240, 235, 255), (224, 248, 0, 255)
    def line(parts, y):
        sp = d.textlength(" ", font=f)
        ws = [d.textlength(t, font=f) for t, _ in parts]
        x = (W_ - (sum(ws) + sp * (len(parts) - 1))) / 2
        for (t, col), w in zip(parts, ws):
            d.text((x, y), t, font=f, fill=col); x += w + sp
    line([("THE", WH), ("SOVIETS", LI), ("SPIED", WH), ("ON", WH), ("AMERICA", LI)], 40)
    line([("USING A", WH)], 40 + int(f.size * 1.3))
    im.save(path)
    return path


def wall_text(c, at=(-0.26, 1.25, 0.42), size=(1.5, 0.3667)):
    from kit import pbr
    img = headline_image(os.path.join(HERE, "plates", "headline.png"))
    # a dark plaster wall close behind the desk
    bpy.ops.mesh.primitive_plane_add(size=1, location=_w(c, (0, at[1] + 0.01, 0.6)))
    wl = bpy.context.active_object; wl.name = "NearWall"; wl.scale = (6, 4, 1)
    wl.rotation_euler = (math.pi / 2, 0, c["tw"]["root"].rotation_euler.z)
    src = bpy.data.materials.get("WallPaint")
    if src:
        m = src.copy(); m.name = "NearWallPaint"
        pb = m.node_tree.nodes.get("Principled BSDF")
        mul = m.node_tree.nodes.new("ShaderNodeMixRGB"); mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1.0
        mul.inputs[2].default_value = (0.3, 0.29, 0.27, 1)
        ln = pb.inputs['Base Color'].links
        if ln:
            m.node_tree.links.new(ln[0].from_socket, mul.inputs[1]); m.node_tree.links.new(mul.outputs[0], pb.inputs['Base Color'])
        else:
            pb.inputs['Base Color'].default_value = (0.05, 0.048, 0.045, 1)
    else:
        m = pbr("NearWallPaint", (0.05, 0.048, 0.045), 0.85)
    wl.data.materials.append(m)
    # the painted letters, a hair in front of the wall: paint (lit by the room) + a little glow so they read
    bpy.ops.mesh.primitive_plane_add(size=1, location=_w(c, at))
    p = bpy.context.active_object; p.name = "WallHeadline"; p.scale = (size[0], size[1], 1)
    p.rotation_euler = (math.pi / 2, 0, c["tw"]["root"].rotation_euler.z)
    tm = bpy.data.materials.new("HeadlinePaint"); tm.use_nodes = True; tm.blend_method = 'HASHED' if hasattr(tm, 'blend_method') else None
    N = tm.node_tree.nodes; L = tm.node_tree.links
    pb = N["Principled BSDF"]; out = N["Material Output"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(img); t.extension = 'CLIP'
    L.new(t.outputs['Color'], pb.inputs['Base Color']); pb.inputs['Roughness'].default_value = 0.6
    L.new(t.outputs['Color'], pb.inputs['Emission Color']); pb.inputs['Emission Strength'].default_value = 0.55
    L.new(t.outputs['Alpha'], pb.inputs['Alpha'])
    p.data.materials.append(tm)
    c["headline"] = p
    return p


def setup_wall(c, text=True):
    setup(c)
    wall_text(c)
    if not text:
        c["headline"].hide_render = True
    for o in bpy.data.objects:
        n = o.name.lower()
        if o.type == 'MESH' and ("lamp" in n or "cabinet" in n or "clock" in n or "plant" in n):
            o.hide_render = True
    # a soft wash across the wall so the paint reads in the dark room
    h = c["headline"]
    _spot("WallWash", _w(c, (0.6, 0.2, 1.5)), h.matrix_world.translation, 120, (1.0, 0.92, 0.82), 40, 0.9, 0.3)


def cam_wall(c):
    return (_w(c, (0.30, -1.02, 0.36)), _w(c, (0.0, 0.2, 0.22)), 36)


CONCEPTS["tw_wall"] = dict(scene="twoffice", variant="night", cam=cam_wall, shift=(0.0, 0.0), focus=lambda c: _w(c, (0, -0.06, 0.08)),
                           fstop=4.5, setup=setup_wall, exposure=-1.2, mask=machine)

CONCEPTS["tw_wall_plain"] = dict(CONCEPTS["tw_wall"], setup=lambda c: setup_wall(c, text=False))
