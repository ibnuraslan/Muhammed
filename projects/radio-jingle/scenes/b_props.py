"""Props reused across chat B's sets: an unbadged 1970s reel-to-reel recorder (reels spin by frame driver),
a 2000s LCD monitor, headphones fitted to a MakeHuman head, generated waveform screens."""
import math, os
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, join, emissive, brushed_metal, wood
import b_common as B


def _bool_diff(o, cutters):
    for c_ in cutters:
        m = o.modifiers.new("cut", 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = c_; m.solver = 'EXACT'
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(c_, do_unlink=True)


_REEL = {}


def reel_mesh(r=0.075, pack=0.6):
    """One reel (two flanges with three windows, hub, a pack of brown tape). Returns a joined template object."""
    key = (round(r, 3), round(pack, 2))
    if key in _REEL and _REEL[key].name in bpy.data.objects:
        return _REEL[key]
    flange_m = pbr("ReelFlange", (0.55, 0.57, 0.6), 0.3, 0.9)
    tape_m = pbr("TapePack", (0.12, 0.07, 0.04), 0.45)
    hub_m = pbr("ReelHub", (0.08, 0.08, 0.08), 0.4)
    parts = []
    for z in (0.002, 0.016):
        f = cyl("Flange", (0, 0, z), r, 0.0018, flange_m, verts=64)
        cuts = []
        for k in range(3):
            a = k * 2 * math.pi / 3
            cuts.append(cyl("Win", (r * 0.55 * math.cos(a), r * 0.55 * math.sin(a), z), r * 0.25, 0.01, None, verts=32))
        _bool_diff(f, cuts)
        parts.append(f)
    parts.append(cyl("Pack", (0, 0, 0.009), r * (0.3 + 0.62 * pack), 0.0125, tape_m, verts=64))
    parts.append(cyl("Hub", (0, 0, 0.012), r * 0.22, 0.026, hub_m, verts=24))
    for k in range(3):                                   # three hub spokes, so rotation reads
        a = k * 2 * math.pi / 3
        parts.append(box("Spoke", (r * 0.14 * math.cos(a), r * 0.14 * math.sin(a), 0.026), (r * 0.12, 0.004, 0.004), flange_m, rot=(0, 0, a)))
    o = join(parts, "ReelT")
    o.location = (0, 0, -100); o.hide_render = True
    _REEL[key] = o
    return o


def reel_recorder(name, loc, rot_z=0.0, spin=1.0, start_frame=0, scale=1.0, lid_wood=True, spin_expr=None):
    """Flat deck, reels on top. Returns dict(root, reels, keys, needle). Reel rotation is a frame driver:
    spin = revolutions per second (0 = stopped); spin_expr overrides the rotation driver expression."""
    alu = brushed_metal(name + "Plate", (0.6, 0.61, 0.62), (0.2, 0.3), 0.5)
    dark = pbr(name + "Body", (0.03, 0.03, 0.032), 0.45)
    side = wood(name + "Side", (0.06, 0.035, 0.02), (0.14, 0.08, 0.045), scale=(0.3, 6, 6), rough=0.4) if lid_wood else dark
    key_m = pbr(name + "Key", (0.72, 0.72, 0.7), 0.35)
    W, D, H = 0.44, 0.34, 0.15
    parts = [box("Body", (0, 0, H / 2 - 0.004), (W, D, H - 0.008), dark, bevel=0.006),
             box("Top", (0, 0, H - 0.002), (W - 0.01, D - 0.01, 0.004), alu),
             box("SideL", (-W / 2 - 0.008, 0, H / 2), (0.016, D + 0.004, H), side, bevel=0.003),
             box("SideR", (W / 2 + 0.008, 0, H / 2), (0.016, D + 0.004, H), side, bevel=0.003),
             box("HeadCover", (0, -0.08, H + 0.018), (0.12, 0.05, 0.036), dark, bevel=0.008),
             box("Front", (0, -D / 2 - 0.001, 0.05), (W - 0.03, 0.004, 0.07), dark)]
    for x in (-0.135, 0.135):                            # tape guides beside the head
        parts.append(cyl("Guide", (x * 0.55, -0.085, H + 0.012), 0.007, 0.024, alu, verts=16))
    root = join(parts, name)
    # the tape running from reel to reel past the head
    tape = box(name + "Tape", (0, -0.075, H + 0.012), (0.27, 0.0015, 0.0065), pbr("Tape", (0.1, 0.06, 0.035), 0.4))
    tape.parent = root
    # piano keys along the front edge of the top plate
    keys = []
    for k in range(6):
        kk = box(name + f"PKey{k}", (-0.14 + k * 0.045, -D / 2 + 0.03, H + 0.006), (0.036, 0.05, 0.012), key_m, bevel=0.002)
        kk.parent = root; keys.append(kk)
    # VU meter window
    vu = box(name + "VU", (0.15, -D / 2 + 0.035, H + 0.002), (0.07, 0.035, 0.004), pbr("VUFace", (0.9, 0.82, 0.55), 0.4,
             **{'Emission Color': (1.0, 0.75, 0.4, 1), 'Emission Strength': 0.6}))
    vu.parent = root
    needle = box(name + "Needle", (0, 0.012, 0), (0.0012, 0.026, 0.001), pbr("NeedleBlk", (0.02, 0.02, 0.02), 0.5))
    needle.parent = vu; needle.location = (0, -0.012, 0.0028)
    # reels
    tpl = reel_mesh()
    reels = []
    for k, x in enumerate((-0.11, 0.11)):
        rl = bpy.data.objects.new(name + f"Reel{k}", tpl.data); bpy.context.collection.objects.link(rl)
        rl.parent = root; rl.location = (x, 0.045, H + 0.006)
        expr = spin_expr if spin_expr else (f"-max(0, frame - {start_frame}) / 24 * {spin} * 6.2832" if spin else "0")
        d = rl.driver_add("rotation_euler", 2).driver; d.type = 'SCRIPTED'; d.expression = expr + (f" + {k * 1.1}")
        reels.append(rl)
    # needle twitches (frame driver)
    d = needle.driver_add("rotation_euler", 2).driver; d.type = 'SCRIPTED'
    d.expression = (f"(0.35 + 0.35 * sin(frame * 0.9) * sin(frame * 0.37 + 1)) * (1 if frame > {start_frame} else 0) - 0.5" if spin else "-0.5")
    root.location = loc; root.rotation_euler = (0, 0, rot_z); root.scale = (scale,) * 3
    return dict(root=root, reels=reels, keys=keys, needle=needle, top=H)


def lcd_monitor(name, loc, rot_z, screen_mat, w=0.48, h=0.3):
    """A 2000s flat panel on a foot stand; returns (root, screen)."""
    bez = pbr("LCDBezel", (0.025, 0.025, 0.028), 0.4)
    parts = [box("LCDBody", (0, 0.015, h / 2 + 0.12), (w + 0.03, 0.03, h + 0.03), bez, bevel=0.004),
             box("LCDNeck", (0, 0.05, 0.07), (0.05, 0.02, 0.14), bez),
             box("LCDFoot", (0, 0.04, 0.006), (0.22, 0.16, 0.012), bez, bevel=0.004)]
    root = join(parts, name)
    scr = B.sheet(name + "Scr", (0, -0.0005, h / 2 + 0.12), (w, h), screen_mat, rot=(math.radians(90), 0, 0))
    scr.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    return root, scr


def headphones(h, name="Phones"):
    """Closed headphones fitted to a MakeHuman head: band over the crown, cups over the ears. Parented to the head bone."""
    head = h.bone_head("head"); tail = h.bone_tail("head")
    M = h.arm.matrix_world.to_3x3()
    side = (M @ Vector((1, 0, 0))).normalized(); up = (tail - head).normalized()
    c = head + up * 0.085
    m = pbr(name + "Mat", (0.03, 0.03, 0.035), 0.4)
    cups = []
    for sg in (-1, 1):
        cp = cyl(name + "Cup", c + side * (0.085 * sg) - up * 0.0, 0.042, 0.03, m, verts=32)
        cp.rotation_euler = (0, math.radians(90), 0)
        cp.rotation_mode = 'QUATERNION'; cp.rotation_quaternion = side.to_track_quat('Z', 'Y')
        cups.append(cp)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.095, minor_radius=0.008, location=c + up * 0.0)
    band = bpy.context.active_object; band.name = name + "Band"; band.data.materials.append(m)
    band.rotation_mode = 'QUATERNION'; band.rotation_quaternion = (h.arm.matrix_world.to_quaternion() @ Vector((0, 1, 0))).to_track_quat('Z', 'X')
    # keep only the top half of the band
    import bmesh
    bpy.context.view_layer.update()
    mw = band.matrix_world
    bm = bmesh.new(); bm.from_mesh(band.data)
    kill = [v for v in bm.verts if (mw @ v.co - c).dot(up) < -0.005]
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(band.data); bm.free()
    objs = cups + [band]
    for o in objs:
        mw = o.matrix_world.copy()
        o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = "head"
        bpy.context.view_layer.update()
        o.matrix_world = mw
    return objs


def waveform_image(path, segments=3, seed=1, W=1600, H=900, accent=(0.95, 0.68, 0.3), bg=(0.03, 0.035, 0.045), spectro=False):
    """A forensic audio screen: stacked waveform tracks, highlighted comparison segments, no readable text."""
    import skia
    if os.path.exists(path):
        return path
    rng = np.random.default_rng(seed)
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.Color4f(*bg, 1))
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(skia.Color4f(0.09, 0.1, 0.12, 1)); cv.drawRect(skia.Rect.MakeXYWH(0, 0, W, 46), p)       # toolbar
    for k in range(10):
        p.setColor4f(skia.Color4f(0.22, 0.24, 0.28, 1)); cv.drawRect(skia.Rect.MakeXYWH(16 + k * 44, 12, 28, 22), p)
    n = segments
    th = (H - 90) / n
    for k in range(n):
        y0 = 60 + k * th; mid = y0 + th / 2
        p.setColor4f(skia.Color4f(0.06, 0.07, 0.085, 1)); cv.drawRect(skia.Rect.MakeXYWH(10, y0, W - 20, th - 12), p)
        # highlighted comparison window
        hx = W * (0.38 + 0.04 * k)
        p.setColor4f(skia.Color4f(accent[0], accent[1], accent[2], 0.18)); cv.drawRect(skia.Rect.MakeXYWH(hx, y0, W * 0.16, th - 12), p)
        p.setColor4f(skia.Color4f(*accent, 0.9)); cv.drawRect(skia.Rect.MakeXYWH(hx, y0, 3, th - 12), p); cv.drawRect(skia.Rect.MakeXYWH(hx + W * 0.16, y0, 3, th - 12), p)
        # waveform: a melody envelope (notes) with noise, and a few click spikes
        xs = np.arange(20, W - 20, 2)
        env = np.zeros_like(xs, dtype=float)
        for nn in range(7):
            c0 = 0.12 + nn * 0.11 + rng.uniform(-0.01, 0.01)
            env += np.exp(-((xs / W - c0) / 0.03) ** 2) * (0.9 if nn != 4 else 0.45)
        env = 0.08 + env
        amp = env * (th * 0.42) * (0.6 + 0.4 * rng.random(len(xs)))
        col = (0.45, 0.85, 0.65) if not spectro else (0.6, 0.75, 1.0)
        p.setColor4f(skia.Color4f(*col, 0.95)); p.setStrokeWidth(2)
        for x, a in zip(xs, amp):
            cv.drawLine(float(x), float(mid - a), float(x), float(mid + a), p)
        for cx in (W * (0.4 + 0.04 * k), W * (0.47 + 0.04 * k)):
            p.setColor4f(skia.Color4f(1, 1, 1, 1)); p.setStrokeWidth(3); cv.drawLine(cx, mid - th * 0.45, cx, mid + th * 0.45, p)
    s.makeImageSnapshot().save(path, skia.kPNG)
    return path


def screen_mat(name, img_path, strength=1.2, cursor=True, cursor_speed=0.08, cursor_start=0.25):
    """Emissive screen from an image with a white playback cursor sweeping (frame driver)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    im = N.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(img_path, check_existing=True)
    L.new(tc.outputs['UV'], im.inputs['Vector'])
    col = im.outputs['Color']
    if cursor:
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
        pos = N.new("ShaderNodeValue"); d = pos.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
        d.expression = f"{cursor_start} + ((frame / 24 * {cursor_speed}) % 0.7)"
        cmp_ = N.new("ShaderNodeMath"); cmp_.operation = 'COMPARE'; cmp_.inputs[2].default_value = 0.0015
        L.new(sep.outputs['X'], cmp_.inputs[0]); L.new(pos.outputs[0], cmp_.inputs[1])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(cmp_.outputs[0], mx.inputs['Factor'])
        L.new(col, mx.inputs[6]); mx.inputs[7].default_value = (1, 1, 1, 1); col = mx.outputs[2]
    em = N.new("ShaderNodeEmission"); em.inputs['Strength'].default_value = strength; L.new(col, em.inputs['Color'])
    gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs['Roughness'].default_value = 0.15; gl.inputs['Color'].default_value = (0.03, 0.03, 0.035, 1)
    ad = N.new("ShaderNodeAddShader"); L.new(em.outputs[0], ad.inputs[0]); L.new(gl.outputs[0], ad.inputs[1])
    L.new(ad.outputs[0], out.inputs['Surface'])
    return m


def mic_stand(name, loc, target, h=0.25):
    """A small table microphone on a short boom, pointed at target."""
    m = pbr(name + "M", (0.05, 0.05, 0.055), 0.35, 0.6)
    base = cyl(name + "Base", (loc[0], loc[1], loc[2] + 0.006), 0.05, 0.012, m, verts=32)
    pole = cyl(name + "Pole", (loc[0], loc[1], loc[2] + h / 2), 0.005, h, m, verts=12)
    head = cyl(name + "Head", (0, 0, 0), 0.014, 0.08, pbr(name + "Grille", (0.2, 0.2, 0.22), 0.5, 0.8), verts=24)
    head.location = (loc[0], loc[1], loc[2] + h)
    d = Vector(target) - head.location
    head.rotation_mode = 'QUATERNION'; head.rotation_quaternion = d.to_track_quat('Z', 'Y')
    head.location += d.normalized() * 0.04
    return [base, pole, head]
