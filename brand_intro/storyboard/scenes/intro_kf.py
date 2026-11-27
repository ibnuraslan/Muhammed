"""Seldom brand intro: storyboard key frames (stills, not animation). Monochrome world, Seldom yellow is the only
colour, faceless black silhouettes. One vignette per SHOT (1..6):
  1 chalk outline   2 door ajar   3 dropped glove   4 phone off the hook   5 car in rain   6 evidence bag + logo
    SHOT=1 SPP=48 blender -b --python intro_kf.py        (PREVIEW=0.5 for half size)
Reuses the Antwerp 3D lib (render setup, grade, Sketchfab fetch) and the thumbnails' rigged crew (Eric, CC-BY)."""
import os, sys, math, random
import bpy
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/user/Muhammed/thumbnails_am/scenes")
import tcommon as T
C = T.use("antwerp")
import crew, sf
E = os.environ.get
SHOT = int(E("SHOT", "1")); TEX = os.path.join(HERE, "..", "tex"); OUT = os.path.join(HERE, "..", "out")
sc = C.render_setup(samples=int(E("SPP", "48")), noise=0.03, res=(1280, 720))
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
pv = float(E("PREVIEW", "0")); sc.render.resolution_percentage = int(100 * pv) if pv else 100
sc.cycles.samples = int(E("SPP", "48")); sc.view_settings.view_transform = 'AgX'
sc.cycles.sample_clamp_indirect = 3.0; sc.cycles.max_bounces = 6
col = sc.collection; rng = random.Random(SHOT)
YLIN = (0.76, 1.0, 0.0)          # Seldom yellow #E3FF00 in linear RGB (as a light / base colour)


def mat(name, v, rough=0.6, metal=0.0, coat=0.0, c=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*(c or (v, v, v)), 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal; p.inputs['Coat Weight'].default_value = coat
    return m


def noisy(m, scale=6.0, lo=0.7, hi=1.15, rough=None, bump=0.0):
    """Break up a flat material: base colour modulated by noise, optional roughness variation and bump."""
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]; base = p.inputs['Base Color'].default_value[:]
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = lo; mr.inputs['To Max'].default_value = hi
    L.new(nz.outputs['Fac'], mr.inputs['Value'])
    mu = N.new("ShaderNodeMix"); mu.data_type = 'RGBA'; mu.blend_type = 'MULTIPLY'; mu.inputs['Factor'].default_value = 1
    mu.inputs[6].default_value = base; L.new(mr.outputs[0], mu.inputs[7]); L.new(mu.outputs[2], p.inputs['Base Color'])
    if rough:
        r2 = N.new("ShaderNodeMapRange"); r2.inputs['From Min'].default_value = 0.42; r2.inputs['From Max'].default_value = 0.62
        r2.inputs['To Min'].default_value = rough[0]; r2.inputs['To Max'].default_value = rough[1]
        n2 = N.new("ShaderNodeTexNoise"); n2.inputs['Scale'].default_value = scale * 0.35; n2.inputs['Detail'].default_value = 5
        L.new(n2.outputs['Fac'], r2.inputs['Value']); L.new(r2.outputs[0], p.inputs['Roughness'])
    if bump:
        bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.02
        n3 = N.new("ShaderNodeTexNoise"); n3.inputs['Scale'].default_value = scale * 12; n3.inputs['Detail'].default_value = 10
        L.new(n3.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def yellow(name="yel", rough=0.4, emit=0.0):
    m = mat(name, 0, rough, c=YLIN)
    if emit:
        p = m.node_tree.nodes["Principled BSDF"]; p.inputs['Emission Color'].default_value = (*YLIN, 1); p.inputs['Emission Strength'].default_value = emit
    return m


def emis(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes
    for n in list(N):
        if n.bl_idname != "ShaderNodeOutputMaterial":
            N.remove(n)
    e = N.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    m.node_tree.links.new(e.outputs[0], N["Material Output"].inputs[0]); return m


BLACK = mat("silhouette", 0.006, 0.55)


def box(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.active_object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); return o


def plane(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.active_object; o.name = name
    o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); return o


def light(kind, name, loc, target, energy, color=(1, 1, 1), size=0.1, spot=None, blend=0.3, volume=True):
    l = bpy.data.lights.new(name, kind); l.energy = energy; l.color = color
    if kind == 'AREA':
        l.size = size
    else:
        l.shadow_soft_size = size
    if kind == 'SPOT':
        l.spot_size = math.radians(spot or 45); l.spot_blend = blend
    if not volume:
        l.volume_factor = 0.0
    o = bpy.data.objects.new(name, l); col.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o


def camera(loc, target, lens=35, fstop=None, focus=None, roll=0.0):
    cd = bpy.data.cameras.new("cam"); cd.lens = lens; cd.sensor_width = 36
    o = bpy.data.objects.new("cam", cd); col.objects.link(o); o.location = loc
    q = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); o.rotation_euler = q.to_euler()
    if roll:
        o.rotation_euler.rotate_axis('Z', math.radians(roll))
    if fstop:
        cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = focus if focus else (Vector(target) - Vector(loc)).length
    sc.camera = o; return o


def world(v=0.002, fog=0.0, aniso=0.3):
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (v, v, v, 1)
    w.cycles_visibility.scatter = False
    if fog:
        bpy.ops.mesh.primitive_cube_add(size=60, location=(0, 0, 10)); vb = bpy.context.active_object; vb.name = "fogbox"
        m = bpy.data.materials.new("fog"); m.use_nodes = True; N = m.node_tree.nodes
        N.remove(N["Principled BSDF"]); v_ = N.new("ShaderNodeVolumePrincipled"); v_.inputs['Density'].default_value = fog
        v_.inputs['Anisotropy'].default_value = aniso
        m.node_tree.links.new(v_.outputs[0], N["Material Output"].inputs['Volume']); vb.data.materials.append(m)
        vb.visible_shadow = False


def figure(loc, heading, pose, mat_=None, name="fig"):
    piv, arm, ms, hand = crew.thief(Vector(loc), heading, pose=pose, mat=mat_ or BLACK, name=name)
    for o in bpy.data.objects:
        if o.name.startswith(name + "_beanie"):
            o.data.materials.clear(); o.data.materials.append(mat_ or BLACK)
    return piv, arm


STAND = [("upperarm_r_049", Y, -58) if False else ("upperarm_r_049", Vector((0, 1, 0)), -62), ("upperarm_l_024", Vector((0, 1, 0)), 62),
         ("lowerarm_r_050", Vector((0, 1, 0)), -6), ("lowerarm_l_025", Vector((0, 1, 0)), 6),
         ("neck_06", Vector((1, 0, 0)), -4), ("head_07", Vector((1, 0, 0)), 6)]
X_, Y_ = Vector((1, 0, 0)), Vector((0, 1, 0))
WALK = [("spine_01_03", X_, 4), ("upperleg_l_074", X_, -24), ("lowerleg_l_075", X_, 12), ("foot_l_076", X_, -8),
        ("upperleg_r_081", X_, 18), ("lowerleg_r_082", X_, 34), ("foot_r_083", X_, 14),
        ("upperarm_r_049", Y_, -64), ("upperarm_r_049", X_, -16), ("upperarm_l_024", Y_, 64), ("upperarm_l_024", X_, 14),
        ("lowerarm_r_050", X_, -10), ("lowerarm_l_025", X_, -10)]


def sf_import(uid, height=None, length=None, drop=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=sf.fetch(uid))
    new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.type == 'MESH' and any(k in o.name for k in (drop or []))]:
        new.remove(o); bpy.data.objects.remove(o)
    root = bpy.data.objects.new("sf_" + uid[:6], None); col.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    ms = [o for o in new if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    s = 1.0
    if height:
        s = height / (mx.z - mn.z)
    if length:
        s = length / max(mx.x - mn.x, mx.y - mn.y)
    root.scale = (s, s, s); root.location = -Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)) * s
    bpy.context.view_layer.update()
    piv = bpy.data.objects.new("piv_" + uid[:6], None); col.objects.link(piv); root.parent = piv
    return piv, ms


def greyscale(ms, mult=1.0, rough=None):
    """Keep the model's texture detail but drain its colour (RGB to BW on the base colour)."""
    done = set()
    for o in ms:
        for m in o.data.materials:
            if m is None or m.name in done or not m.use_nodes:
                continue
            done.add(m.name); N = m.node_tree.nodes; L = m.node_tree.links
            p = next((n for n in N if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
            if p is None:
                continue
            bc = p.inputs['Base Color']
            bw = N.new("ShaderNodeRGBToBW"); mu = N.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = mult
            if bc.links:
                L.new(bc.links[0].from_socket, bw.inputs[0])
            else:
                c = bc.default_value; bw.inputs[0].default_value = c
            L.new(bw.outputs[0], mu.inputs[0]); L.new(mu.outputs[0], bc)
            if rough is not None:
                for lk in list(p.inputs['Roughness'].links):
                    L.remove(lk)
                p.inputs['Roughness'].default_value = rough


def finish(name, sat=1.0, con=1.12, expo=0.0, vig=0.3, bloom=0.2):
    T.C = C; T.grade(sc, sat=sat, con=con, expo=expo, vig=vig, bloom=bloom)
    os.makedirs(OUT, exist_ok=True)
    sc.render.filepath = os.path.join(OUT, name + ".png"); bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath)


# =====================================================================================================================
GROT = float(E("GROT", "150"))
if SHOT == 1:      # CHALK OUTLINE: top-down on wet night asphalt; a numbered yellow marker; a faceless figure's shadow
    world(0.0015)
    asph = noisy(mat("asphalt", 0.035, 0.55, coat=0.5), scale=40, lo=0.45, hi=1.25, rough=(0.12, 0.7), bump=0.35)
    fl = plane("ground", (0, 0, 0), (14, 14), asph)
    cm = bpy.data.materials.new("chalk"); cm.use_nodes = True; N = cm.node_tree.nodes; Lk = cm.node_tree.links
    p = N["Principled BSDF"]; p.inputs['Base Color'].default_value = (0.85, 0.85, 0.83, 1); p.inputs['Roughness'].default_value = 0.95
    im = N.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(os.path.join(TEX, "chalk_outline.png")); im.image.colorspace_settings.name = 'Non-Color'
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    Lk.new(im.outputs['Color'], mx.inputs[0]); Lk.new(tr.outputs[0], mx.inputs[1]); Lk.new(p.outputs[0], mx.inputs[2])
    Lk.new(mx.outputs[0], N["Material Output"].inputs[0]); cm.blend_method = 'HASHED' if hasattr(cm, "blend_method") else None
    plane("chalk", (0, 0, 0.002), (4, 4), cm, rot=(0, 0, math.radians(-12)))
    # evidence marker: a folded yellow card tent with a black "1" on its camera-facing side
    ym = yellow("marker", 0.45)
    mk = bpy.data.objects.new("marker", None); col.objects.link(mk)
    for side in (1, -1):
        f = plane("mk_face", (0, 0, 0), (0.17, 0.14), ym); f.data.transform(Matrix.Translation((0, -0.07, 0)))
        f.parent = mk; f.rotation_euler = (math.radians(-62) * side, 0, 0 if side == 1 else math.pi); f.location = (0, 0, 0.124)
        if side == 1:
            bpy.ops.object.text_add(location=(0, 0, 0)); tx = bpy.context.active_object; tx.data.body = "1"; tx.data.size = 0.075
            tx.data.align_x = 'CENTER'; tx.data.align_y = 'CENTER'; tx.data.materials.append(BLACK)
            tx.parent = f; tx.location = (0, -0.072, 0.0012); tx.rotation_euler = (0, 0, math.pi)
    mk.location = (0.62, -0.42, 0); mk.rotation_euler.z = math.radians(-20)
    # a dropped shell casing / leaves of paper: keep it bare. The figure stands out of frame, a low light behind him
    figure((-0.35, -3.0, 0), 0 + 8, STAND, name="watcher")
    light('SPOT', "key", (-0.55, -5.2, 3.0), (0.0, 0.2, 0.0), 2600, (1, 1, 1), size=0.04, spot=60, blend=0.25, volume=False)
    light('AREA', "fill", (2.5, 3.0, 3.0), (0, 0, 0), 14, (0.9, 0.92, 1.0), size=4)
    camera((0.25, 0.1, 4.4), (0.15, -0.1, 0), lens=33, roll=-8)
    finish("k1_chalk", vig=0.35)

elif SHOT == 2:    # DOOR AJAR: a dark corridor; the door at the end stands open a hand's width; yellow light knifes out
    world(0.001, fog=0.007)
    wall = noisy(mat("plaster", 0.22, 0.85), scale=3, lo=0.8, hi=1.1, bump=0.08)
    floorm = noisy(mat("boards", 0.12, 0.35, coat=0.3), scale=10, lo=0.6, hi=1.2, rough=(0.2, 0.5))
    plane("floor", (0, 0, 0), (2.2, 12), floorm)
    box("wall_l", (-1.15, 0, 1.4), (0.1, 12, 2.8), wall); box("wall_r", (1.15, 0, 1.4), (0.1, 12, 2.8), wall)
    box("ceil", (0, 0, 2.85), (2.4, 12, 0.1), wall)
    # end wall with a door opening (two pieces + lintel)
    DW, DH, YD = 0.9, 2.1, 4.0
    box("end_l", (-0.725, YD, 1.4), (0.75, 0.12, 2.8), wall); box("end_r", (0.725, YD, 1.4), (0.75, 0.12, 2.8), wall)
    box("lintel", (0, YD, (DH + 2.8) / 2), (DW - 0.4 + 0.42, 0.12, 2.8 - DH), wall)
    doorm = noisy(mat("door", 0.15, 0.4), scale=8, lo=0.85, hi=1.1)
    d = box("door", (DW / 2, YD, DH / 2), (DW - 0.02, 0.045, DH - 0.01), doorm)
    d.data.transform(Matrix.Translation((-DW / 2, 0, 0)))  # hinge on the left post
    d.location = (-DW / 2 + 0.01, YD - 0.04, DH / 2); d.rotation_euler.z = math.radians(-22)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(0, 0, 0)); kn = bpy.context.active_object; kn.data.materials.append(mat("brass", 0.5, 0.25, 1.0))
    kn.parent = d; kn.location = (DW - 0.12, -0.05, 0)
    # the room beyond: yellow light, a faceless figure standing just inside, half in the gap
    plane("room_floor", (0, YD + 2.5, 0), (4, 5), floorm); box("room_back", (0, YD + 5, 1.4), (4, 0.1, 2.8), wall)
    light('AREA', "room", (0.3, YD + 3.6, 2.0), (0.1, YD, 1.0), 420, YLIN, size=1.2)
    light('SPOT', "beam", (0.5, YD + 3.6, 1.6), (-0.1, YD - 3.0, 0), 2600, YLIN, size=0.04, spot=30, blend=0.3)
    figure((0.15, YD + 0.95, 0), 180 + 10, STAND, name="doorman")
    light('AREA', "hall", (0, -2, 2.7), (0, 1.0, 0), 2.5, (1, 1, 1), size=1.0)
    camera((0.35, -1.8, 0.55), (0.05, YD, 1.0), lens=32, fstop=4.0, focus=5.6)
    finish("k2_door", vig=0.4)

elif SHOT == 3:    # DROPPED GLOVE: floor level; a black leather glove in the pool of yellow light; the figure walks away
    world(0.001, fog=0.012)
    floorm = noisy(mat("boards", 0.12, 0.32, coat=0.4), scale=10, lo=0.6, hi=1.2, rough=(0.15, 0.45), bump=0.05)
    plane("floor", (0, 0, 0), (8, 14), floorm)
    gp, gm = sf_import("20cd135432134121ac6e9c73164460c2", length=0.25)
    greyscale(gm, 0.22, rough=0.38)
    gp.location = (0.02, 0.0, 0.0); gp.rotation_euler = (0, 0, math.radians(GROT))
    bpy.context.view_layer.update()
    # lay it flat: the asset stands upright along Y; check its smallest extent and rest it on the floor
    figure((-0.35, 2.6, 0), 0 + 4, WALK, name="walker")
    light('SPOT', "pool", (0.15, -0.2, 2.6), (0.0, 0.05, 0), 700, YLIN, size=0.1, spot=16, blend=0.6)
    light('SPOT', "back", (-0.1, 5.0, 0.9), (-0.35, 2.6, 0.5), 900, (1, 1, 1), size=0.1, spot=18, blend=0.4)
    light('AREA', "fill", (0.6, -1.2, 0.6), (0, 0, 0), 2.5, (1, 1, 1), size=1)
    camera((0.06, -0.62, 0.11), (0.0, 0.3, 0.06), lens=40, fstop=1.8, focus=0.62)
    finish("k3_glove", vig=0.4)

elif SHOT == 4:    # PHONE OFF THE HOOK: rotary phone on a side table; the yellow receiver hangs on its coiled cord
    world(0.001, fog=0.006)
    wallp = noisy(mat("wallpaper", 0.16, 0.8), scale=2.5, lo=0.75, hi=1.1, bump=0.06)
    box("wall", (0, 0.6, 1.5), (6, 0.1, 3), wallp)
    floorm = noisy(mat("floor", 0.08, 0.4), scale=8, lo=0.7, hi=1.2)
    plane("floor", (0, -1, 0), (6, 4), floorm)
    pp, pm = sf_import("812e8f59f9e749fab483eabf4800dec2", height=0.86, drop=["Spring001", "Line_phone"])
    greyscale(pm, 0.35, rough=0.3)
    pp.location = (0, 0.25, 0); pp.rotation_euler.z = 0
    bpy.context.view_layer.update()
    rec = [o for o in pm if o.name.startswith("hand_phone")]
    Ym = yellow("receiver", 0.3)
    if rec:
        r = rec[0]; mw = r.matrix_world.copy(); r.parent = None; r.matrix_world = mw
        r.data.materials.clear(); r.data.materials.append(Ym)
        bpy.context.view_layer.update()
        # hang it: rotate so it hangs vertically below the table edge, swinging a little
        bpy.ops.object.select_all(action='DESELECT'); r.select_set(True); bpy.context.view_layer.objects.active = r
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        r.location = (0.02, -0.06, 0.46); r.rotation_euler = (math.radians(6), math.radians(84), math.radians(-10))
        bpy.context.view_layer.update()
    # coiled cord: a helix from the phone base, over the table edge, down to the receiver
    cu = bpy.data.curves.new("cord", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0035; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); P0 = Vector((-0.03, 0.28, 0.79)); P1 = Vector((0.0, -0.03, 0.71)); P2 = Vector((0.02, -0.06, 0.56))
    pts = []
    n = 420
    for i in range(n):
        u = i / (n - 1)
        base = (P0 + (P1 - P0) * (u / 0.3)) if u < 0.3 else (P1 + (P2 - P1) * ((u - 0.3) / 0.7))
        sag = Vector((0, 0, -0.03 * math.sin(math.pi * min(1, u / 0.3))))
        a = u * 2 * math.pi * 60; rr = 0.0 if u < 0.28 else 0.011
        pts.append(base + sag + Vector((rr * math.cos(a), rr * math.sin(a) * 0.6, rr * math.sin(a) * 0.4)))
    sp.points.add(len(pts) - 1)
    for i, q in enumerate(pts):
        sp.points[i].co = (*q, 1)
    co = bpy.data.objects.new("cord", cu); col.objects.link(co); cu.materials.append(yellow("cordm", 0.35))
    # the figure is out of frame; only its shadow lands on the wall behind the phone
    figure((0.7, -1.6, 0), 180 + 25, STAND, name="caller")
    light('SPOT', "lamp", (1.3, -3.6, 1.9), (0.0, 0.6, 1.2), 1000, (1, 1, 1), size=0.05, spot=42, blend=0.3, volume=False)
    light('SPOT', "glow", (-0.5, -0.6, 1.5), (0.0, -0.05, 0.5), 90, YLIN, size=0.1, spot=22, blend=0.6)
    light('AREA', "fill", (-1.5, -1.5, 1.2), (0, 0.2, 0.6), 6, (1, 1, 1), size=1.5)
    camera((-0.95, -1.35, 0.75), (0.02, 0.15, 0.6), lens=40, fstop=2.8, focus=1.65)
    finish("k4_phone", vig=0.38)

elif SHOT == 5:    # CAR IN RAIN: a parked '71 sedan, headlights on (yellow beams through the rain); a figure in the beams
    world(0.0015, fog=0.007, aniso=0.6)
    asph = noisy(mat("asphalt", 0.03, 0.08, coat=1.0), scale=30, lo=0.5, hi=1.4, rough=(0.03, 0.45), bump=0.12)
    plane("road", (0, 0, 0), (40, 40), asph)
    cp, cm_ = sf_import("78f76d386a4341b0b71745bdc50fd5ab", length=5.3, drop=["ground"])
    greyscale(cm_, 0.6)
    for o in cm_:
        for m in o.data.materials:
            if m and m.name.startswith("M_Lights"):
                p = next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
                if p:
                    p.inputs['Emission Color'].default_value = (*YLIN, 1); p.inputs['Emission Strength'].default_value = 8
    cp.rotation_euler.z = math.radians(90 + 0); cp.location = (0, 0, 0)
    bpy.context.view_layer.update()
    ms_pts = [o.matrix_world @ Vector(c) for o in cm_ for c in o.bound_box]
    fy = min(p.y for p in ms_pts); hx = 0.62
    for sx in (-hx, hx):
        light('SPOT', "head", (sx, fy - 0.05, 0.68), (sx * 1.6, fy - 12, 0.0), 2600, YLIN, size=0.06, spot=36, blend=0.35)
    figure((-0.25, fy - 3.6, 0), 180 + 0, STAND, name="stander")
    light('SPOT', "street", (-2.5, fy + 1.5, 6.5), (0.0, fy + 1.8, 0.6), 7000, (0.92, 0.95, 1.0), size=0.3, spot=45, blend=0.3)
    light('AREA', "sky", (4.0, fy - 2.0, 5.0), (0, fy + 2.0, 0.5), 300, (0.85, 0.9, 1.0), size=6, volume=False)
    # rain: thousands of thin streaks (motion-blurred drops) in front of and around the car
    rm = emis("rain", (0.85, 0.88, 0.9), 0.0)
    rm2 = mat("rainm", 0.9, 0.05); p_ = rm2.node_tree.nodes["Principled BSDF"]; p_.inputs['Transmission Weight'].default_value = 0.0
    p_.inputs['Emission Color'].default_value = (1, 1, 1, 1); p_.inputs['Emission Strength'].default_value = 0.03
    bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=0.0025, depth=0.34); drop = bpy.context.active_object; drop.data.materials.append(rm2)
    import bmesh
    me = bpy.data.meshes.new("rain"); bm = bmesh.new()
    rgen = random.Random(5)
    src = bmesh.new(); src.from_mesh(drop.data)
    for i in range(int(E("RAIN", "9000"))):
        x = rgen.uniform(-6, 6); y = rgen.uniform(fy - 7.5, fy + 5); z = rgen.uniform(0, 5.5)
        Mx = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(8), 4, 'X')
        tmp = src.copy(); bmesh.ops.transform(tmp, matrix=Mx, verts=tmp.verts)
        tm = bpy.data.meshes.new("t"); tmp.to_mesh(tm); bm.from_mesh(tm); bpy.data.meshes.remove(tm); tmp.free()
    bm.to_mesh(me); bm.free(); ro = bpy.data.objects.new("rain", me); col.objects.link(ro); me.materials.append(rm2)
    bpy.data.objects.remove(drop)
    ro.visible_shadow = False
    camera((2.6, fy - 9.0, 1.35), (0.0, fy - 0.2, 0.85), lens=45, fstop=4.0, focus=6.4)
    finish("k5_car", vig=0.4, bloom=0.3)

elif SHOT == 6:    # EVIDENCE BAG + LOGO: top-down on a steel table; the glove sealed in a clear bag; the label carries the logo
    world(0.001)
    steel = noisy(mat("steel", 0.12, 0.35, metal=1.0), scale=3, lo=0.7, hi=1.1, rough=(0.25, 0.5), bump=0.03)
    plane("table", (0, 0, 0), (3, 2), steel)
    BW, BH = 0.30, 0.42
    # label (paper) on the bag's upper part
    lm = bpy.data.materials.new("label"); lm.use_nodes = True; N = lm.node_tree.nodes; Lk = lm.node_tree.links
    p = N["Principled BSDF"]; p.inputs['Roughness'].default_value = 0.6
    im = N.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(os.path.join(TEX, "evidence_label.png")); Lk.new(im.outputs['Color'], p.inputs['Base Color'])
    lab = plane("label", (0, BH / 2 - 0.075, 0.0115), (BW - 0.03, (BW - 0.03) * 1100 / 2400), lm)
    # the bag: a thin clear plastic sheet with crinkles
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=220, size=1, location=(0, 0, 0.011))
    bag = bpy.context.active_object; bag.scale = (BW, BH, 1); bpy.ops.object.transform_apply(scale=True)
    tx = bpy.data.textures.new("crinkle", 'VORONOI'); tx.noise_scale = 0.035
    dm = bag.modifiers.new("cr", 'DISPLACE'); dm.texture = tx; dm.strength = 0.0012
    bm_ = bpy.data.materials.new("plastic"); bm_.use_nodes = True; pb = bm_.node_tree.nodes["Principled BSDF"]
    pb.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1); pb.inputs['Roughness'].default_value = 0.08
    pb.inputs['Transmission Weight'].default_value = 1.0; pb.inputs['IOR'].default_value = 1.05; pb.inputs['Alpha'].default_value = 0.5
    bag.data.materials.append(bm_)
    for o in bag.data.polygons:
        o.use_smooth = True
    # yellow tamper seal across the top
    box("seal", (0, BH / 2 - 0.012, 0.0125), (BW, 0.018, 0.0006), yellow("seal", 0.35))
    gp, gm = sf_import("20cd135432134121ac6e9c73164460c2", length=0.24)
    greyscale(gm, 0.22, rough=0.4)
    gp.location = (-0.02, -0.07, 0.0); gp.rotation_euler = (0, 0, math.radians(165))
    light('AREA', "soft", (0.4, -0.3, 1.2), (0, 0, 0), 22, (1, 1, 1), size=0.6)
    light('AREA', "rim", (-0.7, 0.6, 0.35), (0, 0, 0), 6, (1, 1, 1), size=0.3)
    camera((-0.0, 0.06, 0.58), (0.0, 0.085, 0.0), lens=50, fstop=5.6, roll=-3)
    bpy.context.view_layer.update(); print("CAM", sc.camera.matrix_world.translation, sc.camera.rotation_euler)
    finish("k6_evidence_logo", vig=0.35, bloom=0.12)
