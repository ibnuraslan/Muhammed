"""B16 TitanImplosion: build every set, the sub, the man, the anatomy, the FX and one film camera (hard cuts).
blender -b --factory-startup --python 02_build.py -- <chars.blend> <asset_dir> <polyhaven_dir> <shots.json> <out.blend>

Phase 1: shots.json holds provisional shot lengths (clip = 1.3 x nominal). Phase 2: shots.json holds the VO frames
and this script is re-run, so every action is anchored to its shot start at 1x speed (nothing is time-stretched)."""
import bpy, bmesh, sys, os, json, math, random
from mathutils import Vector, Matrix, Euler, noise
a = sys.argv[sys.argv.index("--") + 1:]
CHARS, ASSETS, PH, SHOTS_JSON, OUT = a[:5]
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.normpath(os.path.join(HERE, "..", "..", "pipeline"))
BRAND = os.path.normpath(os.path.join(HERE, "..", "..", "assets", "brand"))
R = math.radians
random.seed(16)
sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.fps = 60
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.render.use_motion_blur = False
sc.world = bpy.data.worlds.new("World"); sc.world.use_nodes = True
bg = sc.world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.3, 0.33, 0.38, 1); bg.inputs[1].default_value = 0.15

# ------------------------------------------------------------------ shots
SH = json.load(open(SHOTS_JSON))
f = 1; SHOT = {}
for s in SH["shots"]:
    if "frame" in s: f = s["frame"]
    n = s["end"] - f + 1 if "end" in s else (s.get("frames") or round(s["sec"] * 60 * SH.get("headroom", 1.0)))
    SHOT[s["id"]] = (f, f + n - 1); f += n
sc.frame_start, sc.frame_end = 1, SH.get("frame_end", f - 1 + SH.get("tail", 0))
print("SHOTS", SHOT, "end", sc.frame_end)

# ------------------------------------------------------------------ helpers
def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
def link(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o); return o
def mat(name, col, rough=0.4, metal=0.0, emit=None, estr=0.0, coat=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = coat
    if emit is not None:
        p.inputs["Emission Color"].default_value = (*emit, 1); p.inputs["Emission Strength"].default_value = estr
    return m
def emit_mat(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0]); return m
GRAD_LO, GRAD_HI = -0.6, 0.8
def gradient_mat(name, top, bottom, strength=1.0, axis_z=True, power=1.0, center=Vector((0, 0, 0)), r=50.0):
    """camera-facing backdrop sphere: emission gradient by world Z (top colour above, bottom colour below)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = GRAD_LO; mr.inputs[2].default_value = GRAD_HI
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*bottom, 1); ramp.color_ramp.elements[1].color = (*top, 1)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[1].default_value = strength
    lp = nt.nodes.new("ShaderNodeLightPath"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    nm = nt.nodes.new("ShaderNodeVectorMath"); nm.operation = 'NORMALIZE'
    nt.links.new(tc.outputs["Object"], nm.inputs[0]); nt.links.new(nm.outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs[2], mr.inputs[0]); nt.links.new(mr.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], e.inputs[0])
    # camera rays see the gradient; other rays see a dim version (so the backdrop only gently lights the set)
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); nt.links.new(e.outputs[0], mx.inputs[2])
    e2 = nt.nodes.new("ShaderNodeEmission"); e2.inputs[1].default_value = strength * 0.35
    nt.links.new(ramp.outputs[0], e2.inputs[0]); nt.links.new(e2.outputs[0], mx.inputs[1])
    nt.links.new(mx.outputs[0], o.inputs[0]); return m
def backdrop(name, c, loc, r, top, bottom, strength=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=64, ring_count=32)
    o = bpy.context.object; o.name = name; o.data.materials.append(gradient_mat(name + "_M", top, bottom, strength))
    for p in o.data.polygons: p.use_smooth = True
    o.visible_shadow = False
    return link(o, c)
def area(name, c, loc, rot, size, energy, col=(1, 1, 1), shape='DISK', spec=1.0):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = energy; L.size = size; L.color = col; L.shape = shape
    L.specular_factor = spec
    o = bpy.data.objects.new(name, L); o.location = loc; o.rotation_euler = rot; c.objects.link(o); return o
def point(name, c, loc, energy, col=(1, 1, 1), radius=0.1):
    L = bpy.data.lights.new(name, 'POINT'); L.energy = energy; L.color = col; L.shadow_soft_size = radius
    o = bpy.data.objects.new(name, L); o.location = loc; c.objects.link(o); return o
def aim(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()
def append_ph(name, c):
    with bpy.data.libraries.load(os.path.join(PH, name, name + "_1k.blend")) as (fr, to): to.objects = fr.objects
    obs = [o for o in to.objects if o]
    for o in obs: c.objects.link(o)
    return obs
def import_glb(name, c):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: link(o, c)
    return new
def bbox(obs):
    pts = [o.matrix_world @ Vector(cn) for o in obs if o.type == 'MESH' for cn in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
def root_group(name, obs, c):
    """parent the imported top-level objects to one empty at the bbox bottom centre"""
    mn, mx = bbox(obs); e = bpy.data.objects.new(name, None); c.objects.link(e)
    e.location = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    bpy.context.view_layer.update()
    for o in obs:
        if o.parent is None:
            mw = o.matrix_world.copy(); o.parent = e; o.matrix_world = mw
    return e, mx - mn
def place_group(e, size_now, target_len, axis, loc, rotz=0.0):
    s = target_len / size_now[axis]; e.scale = (s, s, s)
    e.location = loc; e.rotation_euler = (0, 0, rotz)
def key_hide(o, f, hidden):
    o.hide_render = hidden; o.hide_viewport = hidden
    o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
def set_interp(o, kind='LINEAR'):
    ad = o.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves if hasattr(ad.action, "fcurves") else []:
            for k in fc.keyframe_points: k.interpolation = kind
def all_fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])): return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out
def interp_all(idb, kind):
    for fc in all_fcurves(idb):
        for k in fc.keyframe_points: k.interpolation = kind
def ease(t): return t * t * (3 - 2 * t)

# ================================================================== SET 1: DEEP SEA (origin)
C_SEA = coll("SET1_DeepSea")
SEA0 = Vector((0, 0, 0))
backdrop("SeaBackdrop", C_SEA, SEA0, 90, (0.10, 0.38, 0.62), (0.02, 0.10, 0.22), 1.0)
# seabed: displaced sand, blue-grey
bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=120, location=(0, 0, -6))
bed = link(bpy.context.object, C_SEA); bed.name = "Seabed"
for v in bed.data.vertices:
    p = v.co * 0.08
    v.co.z += noise.noise(p) * 0.9 + noise.noise(p * 4.0) * 0.15
for p in bed.data.polygons: p.use_smooth = True
mbed = bpy.data.materials.new("Seabed_M"); mbed.use_nodes = True; nt = mbed.node_tree
pb_ = nt.nodes["Principled BSDF"]; pb_.inputs["Roughness"].default_value = 0.9
tx = nt.nodes.new("ShaderNodeTexImage")
sand = os.path.join(PH, "aerial_beach_01", "textures")
sf = [x for x in os.listdir(sand) if "diff" in x.lower()]
if sf:
    tx.image = bpy.data.images.load(os.path.join(sand, sf[0]))
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (12, 12, 12)
    tcd = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tcd.outputs["UV"], mp.inputs[0]); nt.links.new(mp.outputs[0], tx.inputs[0])
    mx_ = nt.nodes.new("ShaderNodeMix"); mx_.data_type = 'RGBA'; mx_.blend_type = 'MULTIPLY'; mx_.inputs[0].default_value = 1.0
    mx_.inputs['B'].default_value = (0.55, 0.68, 0.80, 1)
    nt.links.new(tx.outputs[0], mx_.inputs['A']); nt.links.new(mx_.outputs['Result'], pb_.inputs["Base Color"])
bed.data.materials.append(mbed)
# rocks on the seabed
mrock = mat("Rock_M", (0.22, 0.27, 0.32), 0.8)
for i in range(26):
    ang = random.uniform(0, 6.283); rr = random.uniform(4, 30)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=random.uniform(0.3, 1.4),
                                          location=(math.cos(ang) * rr, math.sin(ang) * rr, -6.2))
    rk = link(bpy.context.object, C_SEA); rk.name = "Rock%02d" % i
    for v in rk.data.vertices: v.co += v.co.normalized() * noise.noise(v.co * 2.5 + Vector((i, 0, 0))) * 0.35 * rk.dimensions.x / 2
    rk.scale = (1, random.uniform(0.7, 1.3), random.uniform(0.4, 0.7)); rk.data.materials.append(mrock)
    rk.location.z = -6 + noise.noise(Vector((rk.location.x, rk.location.y, -6)) * 0.08) * 0.9 - 0.1
# marine snow (static, the camera move gives parallax)
msnow = emit_mat("Snow_M", (0.85, 0.92, 1.0), 2.0)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.025, location=(0, 0, 0))
snow = link(bpy.context.object, C_SEA); snow.name = "MarineSnow"; snow.data.materials.append(msnow)
bm = bmesh.new(); bm.from_mesh(snow.data); base = [v.co.copy() for v in bm.verts]; faces = [[v.index for v in fc.verts] for fc in bm.faces]
bm2 = bmesh.new()
for i in range(1400):
    c = Vector((random.uniform(-30, 30), random.uniform(-30, 30), random.uniform(-6, 18)))
    s = random.uniform(0.5, 1.6)
    vs = [bm2.verts.new(c + b * s) for b in base]
    for fc in faces: bm2.faces.new([vs[j] for j in fc])
bm2.to_mesh(snow.data); bm.free(); bm2.free()
snow.visible_shadow = False
area("SeaKey", C_SEA, (4, -6, 14), (R(35), 0, R(20)), 14, 9000, (0.75, 0.88, 1.0))
area("SeaRim", C_SEA, (-10, 8, 6), (R(-70), 0, R(-130)), 8, 2500, (0.5, 0.75, 1.0))
area("SeaFill", C_SEA, (0, -14, 0), (R(90), 0, 0), 12, 2200, (0.7, 0.85, 1.0))
# the same three lights around the implosion sub (SubB sits at SubA's spot + (-30, 25, -2)), so S11 matches SubA
_OB = Vector((-30, 25, -2))
area("SeaKeyB", C_SEA, _OB + Vector((4, -6, 14)), (R(35), 0, R(20)), 14, 9000, (0.75, 0.88, 1.0))
area("SeaRimB", C_SEA, _OB + Vector((-10, 8, 6)), (R(-70), 0, R(-130)), 8, 2500, (0.5, 0.75, 1.0))
area("SeaFillB", C_SEA, _OB + Vector((0, -14, 0)), (R(90), 0, 0), 12, 2200, (0.7, 0.85, 1.0))

# ------------------------------------------------------------------ the sub (Titan-like, generic, no text)
def build_sub(name, c, loc, rotz=0.0, scale=1.0, crush=False):
    root = bpy.data.objects.new(name, None); c.objects.link(root); root.location = loc; root.rotation_euler = (0, 0, rotz)
    root.scale = (scale,) * 3
    parts = []
    mw = mat(name + "_White", (0.93, 0.94, 0.95), 0.32, coat=0.4)
    mt = mat(name + "_Ti", (0.16, 0.17, 0.19), 0.35, metal=0.8)
    mdome = mat(name + "_Dome", (0.01, 0.03, 0.09), 0.06, coat=1.0, emit=(0.25, 0.4, 0.9), estr=0.05)
    mblk = mat(name + "_Black", (0.04, 0.04, 0.045), 0.45)
    mlamp = emit_mat(name + "_Lamp", (1.0, 0.95, 0.85), 30.0)
    mred = emit_mat(name + "_Strobe", (1.0, 0.15, 0.1), 12.0)
    myel = mat(name + "_Yellow", (0.95, 0.72, 0.1), 0.4)
    def add(o, m, smooth=True, bevel=0.0):
        o.data.materials.append(m)
        if smooth:
            for p in o.data.polygons: p.use_smooth = True
        if bevel:
            b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
        o.parent = root; link(o, c); parts.append(o); return o
    # hull cylinder (axis X), with extra rings so the crush shape key deforms smoothly
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.2, depth=4.6, location=(-0.1, 0, 0), rotation=(0, R(90), 0))
    h = bpy.context.object; h.name = name + "_Hull"
    bm = bmesh.new(); bm.from_mesh(h.data)
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs((e.verts[0].co - e.verts[1].co).normalized().z) > 0.9], cuts=14)
    bm.to_mesh(h.data); bm.free()
    add(h, mw, bevel=0.04)
    for i, x in enumerate((2.18, -2.42)):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.2, minor_radius=0.09, major_segments=64, minor_segments=12,
                                         location=(x, 0, 0), rotation=(0, R(90), 0))
        add(bpy.context.object, mt).name = name + "_Ring%d" % i
    for i, x in enumerate((-1.2, 0.0, 1.2)):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.205, minor_radius=0.018, major_segments=64, minor_segments=8,
                                         location=(x, 0, 0), rotation=(0, R(90), 0))
        add(bpy.context.object, mblk).name = name + "_Seam%d" % i
    # front viewport dome
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.05, segments=48, ring_count=24, location=(2.2, 0, 0))
    d = bpy.context.object; d.name = name + "_Dome"
    bm = bmesh.new(); bm.from_mesh(d.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x < -0.02], context='VERTS'); bm.to_mesh(d.data); bm.free()
    d.scale = (0.62, 1, 1); add(d, mdome)
    # tail fairing + cap
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=1.18, radius2=0.55, depth=1.3, location=(-3.05, 0, 0), rotation=(0, R(-90), 0))
    add(bpy.context.object, mw, bevel=0.03).name = name + "_Tail"
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.56, depth=0.12, location=(-3.72, 0, 0), rotation=(0, R(90), 0))
    add(bpy.context.object, mt, bevel=0.03).name = name + "_TailCap"
    # top fairing spine with strobe mast
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.4, 0, 1.2))
    sp = bpy.context.object; sp.scale = (3.6, 0.7, 0.22); sp.name = name + "_TopFairing"; add(sp, mw, bevel=0.08)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.03, depth=0.5, location=(-1.6, 0, 1.55)); add(bpy.context.object, mblk).name = name + "_Mast"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(-1.6, 0, 1.82)); add(bpy.context.object, mred).name = name + "_Strobe"
    # thrusters: 4 ducts with hub and blades at the stern, 2 side ducts
    props = []
    for k, (y, z) in enumerate(((0.95, 0.55), (-0.95, 0.55), (0.95, -0.55), (-0.95, -0.55))):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.3, minor_radius=0.06, major_segments=40, minor_segments=10,
                                         location=(-3.35, y, z), rotation=(0, R(90), 0))
        add(bpy.context.object, mblk).name = name + "_Duct%d" % k
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-3.0, y * 0.75, z * 0.8))
        st = bpy.context.object; st.scale = (0.25, abs(y) * 0.5, 0.06); st.name = name + "_DuctArm%d" % k; add(st, mt, bevel=0.02)
        pe = bpy.data.objects.new(name + "_Prop%d" % k, None); pe.parent = root; c.objects.link(pe); pe.location = (-3.35, y, z)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(0, 0, 0)); hub = bpy.context.object; hub.scale = (1.4, 1, 1)
        hub.name = name + "_Hub%d" % k; add(hub, mt); hub.parent = pe
        for bl in range(3):
            bpy.ops.mesh.primitive_cube_add(size=1); b = bpy.context.object; b.scale = (0.03, 0.22, 0.07)
            b.location = (0, math.cos(bl * 2.094) * 0.13, math.sin(bl * 2.094) * 0.13)
            b.rotation_euler = (bl * 2.094 + R(90), R(25), 0); b.name = name + "_Blade%d_%d" % (k, bl); add(b, myel, bevel=0.01); b.parent = pe
        props.append(pe)
    # landing skids
    for k, y in enumerate((0.85, -0.85)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.07, depth=5.6, location=(-0.4, y, -1.45), rotation=(0, R(90), 0))
        add(bpy.context.object, mt, bevel=0.02).name = name + "_Skid%d" % k
        for x in (-2.2, -0.4, 1.4):
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.05, depth=0.55, location=(x, y * 0.92, -1.2), rotation=(R(-8 if y > 0 else 8), 0, 0))
            add(bpy.context.object, mt).name = name + "_Strut%d_%d" % (k, x * 10)
        for x in (2.25, -3.05):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(x + (0.05 if x > 0 else -0.05), y, -1.45))
            add(bpy.context.object, mt).name = name + "_SkidEnd%d" % k
    # forward lamps (emissive) + spot lights
    lamps = []
    for k, y in enumerate((0.75, -0.75)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.1, depth=0.12, location=(2.05, y, -0.75), rotation=(0, R(90), 0))
        lp = bpy.context.object; lp.name = name + "_Lamp%d" % k; add(lp, mlamp); lamps.append(lp)
        L = bpy.data.lights.new(name + "_Spot%d" % k, 'SPOT'); L.energy = 900; L.spot_size = R(55); L.spot_blend = 0.6
        L.color = (1.0, 0.95, 0.85); L.shadow_soft_size = 0.1
        so = bpy.data.objects.new(name + "_Spot%d" % k, L); c.objects.link(so); so.parent = root
        so.location = (2.2, y, -0.75); so.rotation_euler = (0, R(-90 - 20), 0); lamps.append(so)
    # hull side detail: grab handles / anodes
    for x in (-1.8, -0.6, 0.6, 1.6):
        for y in (1, -1):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y * 1.22, -0.3)); g = bpy.context.object
            g.scale = (0.3, 0.04, 0.06); g.name = name + "_Anode"; add(g, mt, bevel=0.01)
    if crush:
        for o in parts:
            for m_ in list(o.modifiers):
                if m_.type == 'BEVEL': o.modifiers.remove(m_)
        add_crush(root, parts)
    return root, parts, props, lamps, (mlamp, mred, mdome)

def add_crush(root, parts):
    """shape key 'Crush' on every part: the pressure hull caves in toward the axis with random crumple dents"""
    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    for o in parts:
        if o.type != 'MESH': continue
        if not o.data.shape_keys: o.shape_key_add(name="Basis")
        k = o.shape_key_add(name="Crush", from_mix=False)
        M = inv @ o.matrix_world; Mi = M.inverted()
        for i, v in enumerate(o.data.vertices):
            p = M @ v.co
            r = math.hypot(p.y, p.z); ang = math.atan2(p.z, p.y)
            n1 = noise.noise(Vector((p.x * 1.3, ang * 1.6, 0.5))); n2 = noise.noise(Vector((p.x * 3.1, ang * 3.7, 2.0)))
            if -2.6 < p.x < 2.3:                      # pressure hull section caves in hardest
                f_ = 0.55 + 0.14 * n1 + 0.07 * n2
            else:
                f_ = 0.62 + 0.15 * n1
            nr = r * f_
            nx = p.x * 0.78 + n2 * 0.12
            if p.x > 2.2:                             # the dome is pushed into the hull
                nx = 2.2 * 0.78 - (p.x - 2.2) * 0.6
            q = Vector((nx, math.cos(ang) * nr, math.sin(ang) * nr))
            if r < 1e-4: q = Vector((nx, p.y, p.z))
            k.data[i].co = Mi @ q

subA, subA_parts, subA_props, subA_lamps, subA_mats = build_sub("SubA", C_SEA, Vector((0, 0, 4)), rotz=R(20))
subB, subB_parts, subB_props, subB_lamps, _ = build_sub("SubB", C_SEA, Vector((-30, 25, 2)), rotz=R(-10), crush=True)
# implosion FX for SubB: flash light + glow shell + bubble cloud (all keyed, no scene-time)
flashL = point("ImplodeFlash", C_SEA, subB.location.copy(), 0.0, (0.85, 0.95, 1.0), 1.0)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=subB.location); flashG = link(bpy.context.object, C_SEA)
flashG.name = "ImplodeGlow"; flashG.data.materials.append(emit_mat("Glow_M", (0.8, 0.92, 1.0), 6.0)); flashG.visible_shadow = False
bub = bpy.data.objects.new("BubbleCloud", None); C_SEA.objects.link(bub); bub.location = subB.location.copy()
mbub = mat("Bubble_M", (0.85, 0.93, 1.0), 0.05, emit=(0.7, 0.85, 1.0), estr=0.6, coat=1.0)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8); bubm = bpy.context.object
bm = bmesh.new(); bm.from_mesh(bubm.data); base = [v.co.copy() for v in bm.verts]; faces = [[v.index for v in fc.verts] for fc in bm.faces]
bm2 = bmesh.new()
for i in range(600):
    d = Vector((random.gauss(0, 1), random.gauss(0, 0.6), random.gauss(0, 0.6)))
    d = Vector((d.x * 2.4, d.y, d.z)).normalized() * random.uniform(0.6, 1.0) * Vector((3.4, 1.4, 1.4)).length / 1.4
    d = Vector((d.x * 1.0, d.y * 0.45, d.z * 0.45))
    s = random.uniform(0.015, 0.06)
    vs = [bm2.verts.new(d + b * s) for b in base]
    for fc in faces: bm2.faces.new([vs[j] for j in fc])
bm2.to_mesh(bubm.data); bm.free(); bm2.free()
bubm.name = "Bubbles"; bubm.data.materials.append(mbub)
for p in bubm.data.polygons: p.use_smooth = True
link(bubm, C_SEA); bubm.parent = bub; bubm.location = (0, 0, 0); bub.rotation_euler = subB.rotation_euler.copy()

# ================================================================== SET 2: LIVING ROOM (x = 200)
C_ROOM = coll("SET2_LivingRoom")
RM = Vector((200, 0, 0))
def tex_mat(name, folder, scale=2.0, tint=None, rough_min=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    d = os.path.join(PH, folder, "textures"); fs = os.listdir(d)
    diff = [x for x in fs if "diff" in x.lower()]
    tcd = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    nt.links.new(tcd.outputs["UV"], mp.inputs[0])
    if diff:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(d, diff[0])); nt.links.new(mp.outputs[0], t.inputs[0])
        if tint:
            mx_ = nt.nodes.new("ShaderNodeMix"); mx_.data_type = 'RGBA'; mx_.blend_type = 'MULTIPLY'; mx_.inputs[0].default_value = 1.0
            mx_.inputs['B'].default_value = (*tint, 1); nt.links.new(t.outputs[0], mx_.inputs['A']); nt.links.new(mx_.outputs['Result'], p.inputs["Base Color"])
        else: nt.links.new(t.outputs[0], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = max(rough_min, 0.5)
    return m
def box(name, c, loc, size, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = size; o.name = name
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT')
    o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = 2
    return link(o, c)
mfloor = tex_mat("Floor_M", "laminate_floor_02", 1.0)
mwall = tex_mat("Wall_M", "painted_plaster_wall", 1.0, tint=(0.93, 0.86, 0.74))
mwall2 = tex_mat("WallAccent_M", "painted_plaster_wall", 1.0, tint=(0.55, 0.72, 0.78))
W, D, H = 6.0, 6.0, 2.8          # room x-width, y-depth; sofa against the +Y wall, TV toward -Y
box("Floor", C_ROOM, RM + Vector((0, 0, -0.05)), (W, D, 0.1), mfloor)
box("Ceiling", C_ROOM, RM + Vector((0, 0, H + 0.05)), (W, D, 0.1), mat("Ceil_M", (0.95, 0.95, 0.93), 0.8))
box("WallBack", C_ROOM, RM + Vector((0, D / 2 + 0.05, H / 2)), (W, 0.1, H), mwall2)
box("WallFront", C_ROOM, RM + Vector((0, -D / 2 - 0.05, H / 2)), (W, 0.1, H), mwall)
box("WallRight", C_ROOM, RM + Vector((W / 2 + 0.05, 0, H / 2)), (0.1, D, H), mwall)
# left wall with a window (sky outside)
box("WallLeftA", C_ROOM, RM + Vector((-W / 2 - 0.05, -1.9, H / 2)), (0.1, 2.2, H), mwall)
box("WallLeftB", C_ROOM, RM + Vector((-W / 2 - 0.05, 2.15, H / 2)), (0.1, 1.7, H), mwall)
box("WallLeftLow", C_ROOM, RM + Vector((-W / 2 - 0.05, 0.25, 0.45)), (0.1, 2.1, 0.9), mwall)
box("WallLeftHigh", C_ROOM, RM + Vector((-W / 2 - 0.05, 0.25, 2.55)), (0.1, 2.1, 0.5), mwall)
mframe = mat("WinFrame_M", (0.97, 0.97, 0.97), 0.4)
for nm, l, s in (("WinSill", (0, 0.25, 0.92), (0.2, 2.2, 0.05)), ("WinTop", (0, 0.25, 2.3), (0.14, 2.1, 0.06)),
                 ("WinMid", (0, 0.25, 1.6), (0.12, 0.05, 1.4)), ("WinBar", (0, 0.25, 1.6), (0.12, 2.1, 0.04))):
    box(nm, C_ROOM, RM + Vector((-W / 2 - 0.05, 0, 0)) + Vector(l), s, mframe)
bpy.ops.mesh.primitive_plane_add(size=1, location=RM + Vector((-W / 2 - 2.0, 0.25, 1.7)), rotation=(0, R(90), 0))
skyp = link(bpy.context.object, C_ROOM); skyp.name = "WindowSky"; skyp.scale = (4, 8, 1)
skyp.data.materials.append(emit_mat("WindowSky_M", (0.55, 0.78, 0.98), 2.2))
# skirting
mskirt = mat("Skirt_M", (0.95, 0.95, 0.93), 0.5)
box("SkirtBack", C_ROOM, RM + Vector((0, D / 2 - 0.01, 0.05)), (W, 0.02, 0.1), mskirt)
# sofa (CC-BY) against the back wall
sofa_obs = import_glb("sofa", C_ROOM)
sofaE, sz = root_group("Sofa", sofa_obs, C_ROOM)
place_group(sofaE, sz, 2.1, 1, RM + Vector((0, D / 2 - 0.55, 0)), rotz=R(90))
# the sofa model's long axis is Y, rotated 90 deg so it runs along X and faces -Y; check the facing below
# coffee table, TV on a low cabinet, plant
ct = append_ph("coffee_table_round_01", C_ROOM)
ctE, csz = root_group("CoffeeTable", ct, C_ROOM); place_group(ctE, csz, 1.0, 0, RM + Vector((0.15, 0.95, 0)))
mcab = mat("Cabinet_M", (0.45, 0.30, 0.20), 0.45)
box("TVCabinet", C_ROOM, RM + Vector((0, -D / 2 + 0.35, 0.28)), (1.8, 0.45, 0.56), mcab, bevel=0.01)
tv = append_ph("Television_01", C_ROOM)
tvE, tsz = root_group("TV", tv, C_ROOM); place_group(tvE, tsz, 0.75, 0, RM + Vector((0, -D / 2 + 0.38, 0.56)), rotz=R(0))
pl = append_ph("potted_plant_01", C_ROOM)
plE, psz = root_group("Plant", pl, C_ROOM); place_group(plE, psz, 1.1, 2, RM + Vector((1.55, D / 2 - 0.4, 0)))
pl2 = append_ph("potted_plant_01", C_ROOM)
pl2E, psz2 = root_group("Plant2", pl2, C_ROOM); place_group(pl2E, psz2, 0.9, 2, RM + Vector((-1.4, -D / 2 + 0.4, 0)))
# wall art (blank colour blocks, no text), a floor lamp shade glow
mart = mat("Art_M", (0.95, 0.65, 0.3), 0.6); mart2 = mat("Art2_M", (0.3, 0.55, 0.85), 0.6)
box("ArtFrame", C_ROOM, RM + Vector((-0.1, D / 2 - 0.02, 1.75)), (1.1, 0.04, 0.7), mat("ArtFrameM", (0.15, 0.12, 0.1), 0.5))
box("ArtA", C_ROOM, RM + Vector((-0.35, D / 2 - 0.05, 1.75)), (0.5, 0.02, 0.58), mart)
box("ArtB", C_ROOM, RM + Vector((0.2, D / 2 - 0.05, 1.75)), (0.55, 0.02, 0.58), mart2)
# rug
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.35, depth=0.012, location=RM + Vector((0.1, 0.7, 0.006)))
rug = link(bpy.context.object, C_ROOM); rug.name = "Rug"; rug.data.materials.append(mat("Rug_M", (0.55, 0.25, 0.18), 0.9))
# delivery box with our logo (the film's only logo placement), on the floor right of the TV cabinet
mbox = mat("Cardboard_M", (0.70, 0.52, 0.33), 0.75)

# room lights: window daylight + ceiling soft box + warm lamp
area("RoomWindow", C_ROOM, RM + Vector((-W / 2 + 0.2, 0.25, 1.6)), (0, R(-90), 0), 2.0, 900, (0.85, 0.92, 1.0), 'RECTANGLE')
area("RoomCeil", C_ROOM, RM + Vector((0, 0, H - 0.05)), (0, 0, 0), 3.0, 700, (1.0, 0.97, 0.92))
area("RoomFill", C_ROOM, RM + Vector((0.8, -1.8, 1.6)), (R(80), 0, R(20)), 1.5, 160, (1.0, 0.95, 0.88))
area("TVGlow", C_ROOM, RM + Vector((0, -D / 2 + 0.6, 0.95)), (R(-90), 0, R(180)), 0.6, 25, (0.6, 0.8, 1.0), 'RECTANGLE')

# ------------------------------------------------------------------ the man (from chars.blend)
with bpy.data.libraries.load(CHARS) as (fr, to): to.objects = [n for n in fr.objects if n == "Man" or n.startswith("Man.")]
for o in to.objects: C_ROOM.objects.link(o)
man = bpy.data.objects["Man"]
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
bpy.context.view_layer.objects.active = man
MR = make_human_ctrl(man)
add_hand_limits(man)
for s_ in "LR":   # open the elbow limit (MPFB rest elbow ~46 deg would otherwise force an A-pose); no hyper-extension
    lo = man.pose.bones["lowerarm01." + s_]; lo.use_ik_limit_x = True; lo.ik_min_x = R(-46); lo.ik_max_x = R(145)
    # LESSONS 2.6: forearm twist free, and the arm IK also matches the hand target's orientation, so the wrist limit
    # never has to absorb a pronation (the left wrist was clamped ~240 deg off its target, palm turned up)
    tw = man.pose.bones["lowerarm02." + s_]; tw.lock_ik_y = False
    for c in man.pose.bones["lowerarm02." + s_].constraints:
        if c.type == 'IK': c.use_rotation = True; c.orient_weight = 0.6
    for c in man.pose.bones["wrist." + s_].constraints:
        if c.type == 'LIMIT_ROTATION': c.euler_order = 'YXZ'

HM = Human(MR)
# resting hand on a thigh: fingers nearly straight (the full 'relaxed' curl dug the fingertips into the thigh)
POSES["rest_thigh"] = dict(curl={2: (10, 8, 4), 3: (10, 8, 4), 4: (12, 10, 5), 5: (14, 10, 5)}, spread=2.0, thumb=("beside_index", 0.012))
# eye fix (black-hole eyes) on the MPFB EnhancedEye group
_NO_SAVE = True
g = bpy.data.node_groups.get("EnhancedEye")
if g and not any(n.name == "CorneaTransparentMix" for n in g.nodes):
    P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; out_sock = ol.to_socket; g.links.remove(ol)
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    print("EYEFIX applied")
# clothes (director P1 note): the striped skin-tight shirt becomes a plain, looser shirt; the jeans stay.
# casualsuit03 is one garment: shirt texels are told apart from the blue denim (blue clearly above red).
SHIRT_RGB = (0.16, 0.36, 0.30)      # plain muted green, clearly non-skin
for ch in man.children:
    if "casualsuit" not in ch.name: continue
    m_ = ch.data.materials[0]; nt_ = m_.node_tree
    dtex = next(n for n in nt_.nodes if n.type == 'TEX_IMAGE' and "diffuse" in n.image.name)
    links_out = [l.to_socket for l in nt_.links if l.from_node == dtex and l.from_socket.name == "Color"]
    sep = nt_.nodes.new("ShaderNodeSeparateColor"); nt_.links.new(dtex.outputs["Color"], sep.inputs[0])
    sub_ = nt_.nodes.new("ShaderNodeMath"); sub_.operation = 'SUBTRACT'
    nt_.links.new(sep.outputs[2], sub_.inputs[0]); nt_.links.new(sep.outputs[0], sub_.inputs[1])
    mr_ = nt_.nodes.new("ShaderNodeMapRange"); mr_.inputs[1].default_value = 0.02; mr_.inputs[2].default_value = 0.10
    nt_.links.new(sub_.outputs[0], mr_.inputs[0])                     # 1 = denim, 0 = shirt
    shade = nt_.nodes.new("ShaderNodeMix"); shade.data_type = 'RGBA'; shade.blend_type = 'MULTIPLY'; shade.inputs[0].default_value = 1.0
    shade.inputs['A'].default_value = (*SHIRT_RGB, 1)
    gam = nt_.nodes.new("ShaderNodeMath"); gam.operation = 'MULTIPLY_ADD'
    rgb2bw = nt_.nodes.new("ShaderNodeRGBToBW"); nt_.links.new(dtex.outputs["Color"], rgb2bw.inputs[0])
    gam.inputs[1].default_value = 0.6; gam.inputs[2].default_value = 0.75   # gentle shading from the old texture, stripes flattened
    nt_.links.new(rgb2bw.outputs[0], gam.inputs[0])
    cmb = nt_.nodes.new("ShaderNodeCombineColor"); [nt_.links.new(gam.outputs[0], cmb.inputs[i]) for i in range(3)]
    nt_.links.new(cmb.outputs[0], shade.inputs['B'])
    mixc = nt_.nodes.new("ShaderNodeMix"); mixc.data_type = 'RGBA'
    nt_.links.new(mr_.outputs[0], mixc.inputs[0]); nt_.links.new(shade.outputs['Result'], mixc.inputs['A']); nt_.links.new(dtex.outputs["Color"], mixc.inputs['B'])
    for sock in links_out: nt_.links.new(mixc.outputs['Result'], sock)
    # shirt vertex group from the texture at each vertex's UV, then smooth + push the shirt out a little (looser fit)
    img = dtex.image; W_, H_ = img.size; px = list(img.pixels[:])
    uvl = ch.data.uv_layers.active.data; vshirt = {}
    for poly in ch.data.polygons:
        for li in poly.loop_indices:
            u, v_ = uvl[li].uv; x = min(W_ - 1, max(0, int(u * W_))); y = min(H_ - 1, max(0, int(v_ * H_)))
            k = (y * W_ + x) * 4; r_, g_, b_ = px[k], px[k + 1], px[k + 2]
            vi = ch.data.loops[li].vertex_index
            vshirt[vi] = vshirt.get(vi, False) or (b_ - r_ < 0.04 and (r_ + g_ + b_) > 0.0)
    vg = ch.vertex_groups.new(name="ShirtLoose"); vg.add([i for i, s_ in vshirt.items() if s_], 1.0, 'REPLACE')
    sm = ch.modifiers.new("ShirtSmooth", 'SMOOTH'); sm.factor = 0.7; sm.iterations = 8; sm.vertex_group = "ShirtLoose"
    dp = ch.modifiers.new("ShirtLoose", 'DISPLACE'); dp.strength = 0.012; dp.mid_level = 0.0; dp.vertex_group = "ShirtLoose"
    # keep them right after the Armature modifier (before any subdivision)
    while ch.modifiers.find("ShirtLoose") > 0 and ch.modifiers[ch.modifiers.find("ShirtLoose") - 1].type == 'SUBSURF':
        bpy.ops.object.modifier_move_up({"object": ch}, modifier="ShirtLoose") if False else ch.modifiers.move(ch.modifiers.find("ShirtLoose"), ch.modifiers.find("ShirtLoose") - 1)
    while ch.modifiers.find("ShirtSmooth") > 0 and ch.modifiers[ch.modifiers.find("ShirtSmooth") - 1].type == 'SUBSURF':
        ch.modifiers.move(ch.modifiers.find("ShirtSmooth"), ch.modifiers.find("ShirtSmooth") - 1)
    print("SHIRT verts", sum(vshirt.values()), "of", len(ch.data.vertices), [m.name for m in ch.modifiers])

# ================================================================== SET 3: ANATOMY on the sky-blue gradient (x = 400)
C_AN = coll("SET3_Anatomy")
AN = Vector((400, 0, 0))
GRAD_LO, GRAD_HI = -1.1, 0.25
backdrop("AnatBackdrop", C_AN, AN, 40, (0.078, 0.546, 0.93), (0.807, 0.93, 1.0), 1.5)
area("AnKey", C_AN, AN + Vector((3, -5, 5)), (R(45), 0, R(30)), 4, 900)
area("AnFill", C_AN, AN + Vector((-5, -3, 1)), (R(75), 0, R(-60)), 4, 450, (0.9, 0.95, 1.0))
area("AnRim", C_AN, AN + Vector((0, 5, 3)), (R(-60), 0, R(180)), 4, 500)
# brain (CC-BY), glossy pink, emission keyed for "pain"
br = import_glb("brain", C_AN)
brE, bsz = root_group("Brain", br, C_AN)
mbrain = mat("Brain_M", (0.93, 0.55, 0.60), 0.35, emit=(1.0, 0.75, 0.2), estr=0.0, coat=0.5)
for o in br:
    if o.type == 'MESH':
        o.data.materials.clear(); o.data.materials.append(mbrain)
        for p in o.data.polygons: p.use_smooth = True
        sm = o.modifiers.new("Sub", 'SUBSURF'); sm.levels = 1; sm.render_levels = 1
place_group(brE, bsz, 1.0, 1, AN + Vector((0, 0, 0.6)))
def nerve(name, c, pts, radius=0.035, col=(0.98, 0.85, 0.45), seg_col=(0.98, 0.95, 0.85), segs=True):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu.bevel_depth = radius; cu.bevel_resolution = 6; cu.use_path = True; cu.path_duration = 100
    o = bpy.data.objects.new(name, cu); c.objects.link(o)
    o.data.materials.append(mat(name + "_M", col, 0.35, coat=0.3))
    if segs:   # myelin sheath segments along the axon
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12); m_ = bpy.context.object
        m_.scale = (0.11, radius * 1.9, radius * 1.9); bpy.ops.object.transform_apply(scale=True)
        m_.name = name + "_Myelin"; link(m_, c); m_.data.materials.append(mat(name + "_MyM", seg_col, 0.3, coat=0.5))
        for p in m_.data.polygons: p.use_smooth = True
        ar = m_.modifiers.new("Arr", 'ARRAY'); ar.fit_type = 'FIT_CURVE'; ar.curve = o
        ar.relative_offset_displace = (1.25, 0, 0)
        cm = m_.modifiers.new("Crv", 'CURVE'); cm.object = o; cm.deform_axis = 'POS_X'
        m_.location = Vector(pts[0]); m_.location = (0, 0, 0)
    return o
def pulse(name, c, curve, col=(1.0, 0.85, 0.15), size=0.09, light=60):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=size, segments=24, ring_count=12); p = bpy.context.object; p.name = name
    link(p, c); p.data.materials.append(emit_mat(name + "_M", col, 25.0)); p.visible_shadow = False
    fp = p.constraints.new('FOLLOW_PATH'); fp.target = curve; fp.use_fixed_location = True; fp.use_curve_follow = False
    L = bpy.data.lights.new(name + "_L", 'POINT'); L.energy = light; L.color = col; L.shadow_soft_size = 0.05
    lo = bpy.data.objects.new(name + "_L", L); c.objects.link(lo); lo.parent = p
    return p, fp
# pain nerve: from lower left into the brain stem
bpos = brE.location
NP = [AN + Vector((-2.6, -0.6, -1.6)), AN + Vector((-1.6, -0.3, -1.0)), AN + Vector((-0.6, 0.0, -0.45)), AN + Vector((0.0, 0.05, 0.25))]
painN = nerve("PainNerve", C_AN, NP)
painP, painFP = pulse("PainPulse", C_AN, painN)
# pain sparks: stylised bolts around the brain
mbolt = emit_mat("Bolt_M", (1.0, 0.82, 0.1), 6.0)
bolts = []
for i, (dx, dz, rot) in enumerate(((0.55, 1.15, -25), (0.15, 1.35, 5), (-0.3, 1.25, 30), (0.75, 0.95, -45))):
    bm = bmesh.new()
    zig = [(-0.03, 0.0), (0.05, 0.12), (0.0, 0.12), (0.06, 0.26), (-0.04, 0.12), (0.01, 0.12)]
    pts2 = [Vector((x, 0, z)) for x, z in zig]
    vs = [bm.verts.new(p) for p in pts2]; bm.faces.new(vs)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.02)
    me = bpy.data.meshes.new("Bolt%d" % i); bm.to_mesh(me); bm.free()
    bo = bpy.data.objects.new("PainBolt%d" % i, me); C_AN.objects.link(bo); me.materials.append(mbolt)
    bo.location = AN + Vector((dx, -0.2, dz)); bo.rotation_euler = (0, R(rot), 0); bo.scale = (1.4, 1.4, 1.4)
    bolts.append(bo)
# EYE (CC-BY) with optic nerve, placed left of the brain on the same backdrop
EY = AN + Vector((8, 0, 0))
ey = import_glb("eye2", C_AN)
eyE, esz = root_group("Eye", ey, C_AN); place_group(eyE, esz, 0.9, 0, EY + Vector((0, 0, 0.0)))
eyE.location.z = EY.z - 0.45
# where is the pupil? the model looks along -Y (checked in look renders); turn it to face -Y/-X toward camera side
eyE.rotation_euler = (0, 0, R(0))
ON = [EY + Vector((0, 0.42, 0.0)), EY + Vector((0.3, 1.2, 0.2)), EY + Vector((1.2, 1.9, 0.45)), EY + Vector((2.6, 2.3, 0.6))]
optN = nerve("OpticNerve", C_AN, ON, radius=0.06, col=(0.98, 0.88, 0.62))
optP, optFP = pulse("OpticPulse", C_AN, optN, col=(1.0, 0.95, 0.5), size=0.11)
# a small brain at the end of the optic nerve (same model) so the signal has a destination
br2 = import_glb("brain", C_AN); br2E, b2sz = root_group("Brain2", br2, C_AN)
for o in br2:
    if o.type == 'MESH':
        o.data.materials.clear(); o.data.materials.append(mbrain)
        for p in o.data.polygons: p.use_smooth = True
place_group(br2E, b2sz, 1.2, 1, EY + Vector((3.3, 2.6, 0.0)))
# light ray entering the pupil
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.0, radius2=0.12, depth=1.6, location=(0, 0, 0))
ray = link(bpy.context.object, C_AN); ray.name = "LightRay"
ray.data.materials.append(emit_mat("Ray_M", (1.0, 0.92, 0.55), 4.0)); ray.visible_shadow = False
area("EyKey", C_AN, EY + Vector((2, -5, 4)), (R(45), 0, R(20)), 4, 900)

# ================================================================== SET 3b: COMPARISON (eye vs sub) (x = 460)
CP = AN + Vector((120, 0, 0))
C_CP = coll("SET3b_Compare")
backdrop("CmpBackdrop", C_CP, CP, 40, (0.078, 0.546, 0.93), (0.807, 0.93, 1.0), 1.5)
area("CpKey", C_CP, CP + Vector((3, -6, 5)), (R(45), 0, R(30)), 5, 1100)
area("CpFill", C_CP, CP + Vector((-6, -3, 1)), (R(75), 0, R(-60)), 5, 500, (0.9, 0.95, 1.0))
ey3 = import_glb("eye2", C_CP); ey3E, e3sz = root_group("EyeCmp", ey3, C_CP); place_group(ey3E, e3sz, 0.9, 0, CP + Vector((-0.9, 0, 0.6)))
ON3 = [CP + Vector((-0.9, 0.42, 1.05)), CP + Vector((-0.7, 1.3, 1.3)), CP + Vector((-0.2, 2.2, 1.6)), CP + Vector((0.6, 3.2, 1.9))]
optN3 = nerve("OpticNerveCmp", C_CP, ON3, radius=0.06, col=(0.98, 0.88, 0.62))
optP3, optFP3 = pulse("OpticPulseCmp", C_CP, optN3, col=(1.0, 0.95, 0.5), size=0.11)
subC, subC_parts, subC_props, subC_lamps, _ = build_sub("SubC", C_CP, CP + Vector((1.0, 0.8, 0.55)), rotz=R(-25), scale=0.3, crush=True)
for l in subC_lamps:
    if l.type == 'LIGHT': l.data.energy = 0
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=subC.location); flashC = link(bpy.context.object, C_CP)
flashC.name = "CmpGlow"; flashC.data.materials.append(emit_mat("GlowC_M", (0.8, 0.92, 1.0), 4.0)); flashC.visible_shadow = False
# soft ground shadow catcher disc under the comparison props
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=6, fill_type='NGON', location=CP + Vector((0, 0, 0)))
gnd = link(bpy.context.object, C_CP); gnd.name = "CmpGround"; gnd.data.materials.append(mat("CmpGnd_M", (0.55, 0.78, 0.95), 0.8))
gnd.is_shadow_catcher = False

# ================================================================== SET 4: OCEAN SURFACE AT SUNSET (x = 600)
C_SF = coll("SET4_Surface")
SF = Vector((10000, 0, 0))
GRAD_LO, GRAD_HI = -0.05, 0.4
backdrop("SunsetSky", C_SF, SF, 2500, (0.12, 0.16, 0.45), (1.0, 0.42, 0.12), 1.4)
bpy.ops.mesh.primitive_plane_add(size=4800, location=SF); oc = link(bpy.context.object, C_SF); oc.name = "Ocean"
moc = mat("Ocean_M", (0.03, 0.10, 0.20), 0.18, coat=0.0)
_nt = moc.node_tree; _p = _nt.nodes["Principled BSDF"]; _p.inputs["Specular IOR Level"].default_value = 0.4
_nz = _nt.nodes.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 0.6; _nz.inputs["Detail"].default_value = 6
_mp = _nt.nodes.new("ShaderNodeMapping"); _mp.inputs["Scale"].default_value = (1, 3, 1); _tc = _nt.nodes.new("ShaderNodeTexCoord")
_nt.links.new(_tc.outputs["Object"], _mp.inputs[0]); _nt.links.new(_mp.outputs[0], _nz.inputs[0])
_bp = _nt.nodes.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.35
_nt.links.new(_nz.outputs["Fac"], _bp.inputs["Height"]); _nt.links.new(_bp.outputs["Normal"], _p.inputs["Normal"])
oc.data.materials.append(moc)
bpy.ops.mesh.primitive_uv_sphere_add(radius=12, location=SF + Vector((0, 380, 22))); sun = link(bpy.context.object, C_SF)
sun.location = SF + Vector((150, 2300, 110)); sun.scale = (7, 7, 7); sun.name = "SunDisc"; sun.data.materials.append(emit_mat("Sun_M", (1.0, 0.75, 0.4), 12.0))
area("SunsetKey", C_SF, SF + Vector((0, 60, 18)), (R(-75), 0, R(180)), 30, 90000, (1.0, 0.7, 0.45))
area("SunsetFill", C_SF, SF + Vector((10, -40, 20)), (R(60), 0, R(20)), 30, 30000, (0.6, 0.65, 0.95))
shp = import_glb("ship", C_SF)
for o in list(shp):
    if o.name.startswith("Ocean"):
        shp.remove(o); bpy.data.objects.remove(o, do_unlink=True)
shpE, ssz = root_group("SupportShip", shp, C_SF)
place_group(shpE, ssz, 60.0, 0 if ssz.x > ssz.y else 1, SF + Vector((0, 150, -2.5)), rotz=R(15))

# ================================================================== camera (one film camera, hard cuts)
cam = bpy.data.objects.new("CAM_Film", bpy.data.cameras.new("CAM_Film")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_width = 36; cam.data.dof.use_dof = False; cam.data.clip_start = 0.05; cam.data.clip_end = 6000
tgt = bpy.data.objects.new("CAM_Target", None); sc.collection.objects.link(tgt)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
# camera-only catchlight for eyes (specular only)
cl = bpy.data.lights.new("Catchlight", 'AREA'); cl.size = 0.15; cl.energy = 4
clo = bpy.data.objects.new("Catchlight", cl); sc.collection.objects.link(clo); clo.parent = cam; clo.location = (0.0, 0.12, 0)
clo.visible_diffuse = False; clo.visible_volume_scatter = False; clo.visible_transmission = False
CAMKEYS = []
def shot_cam(sid, keys, lens=35):
    """keys: list of (u in 0..1, cam_loc, target_loc); linear inside the shot, constant at the cut"""
    if sid not in SHOT: return
    f0, f1 = SHOT[sid]
    for u, cl_, tl_ in keys:
        fr = round(f0 + u * (f1 - f0))
        cam.location = cl_; cam.keyframe_insert("location", frame=fr)
        tgt.location = tl_; tgt.keyframe_insert("location", frame=fr)
        cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=fr)
        CAMKEYS.append((fr, u))

# ================================================================== ANIMATION per shot (all anchored to shot start, 1x)
def F(sid, sec): return SHOT[sid][0] + round(sec * 60)
fs, fe = sc.frame_start, sc.frame_end
# --- props spin on every sub all film long (1.5 rev/s); sub drift
for pe in subA_props + subB_props:
    pe.rotation_euler = (0, 0, 0); pe.keyframe_insert("rotation_euler", index=0, frame=fs)
    pe.rotation_euler = (R(540 * (fe - fs) / 60), 0, 0); pe.keyframe_insert("rotation_euler", index=0, frame=fe)
    interp_all(pe, 'LINEAR')
# SubA: descends slowly along its heading through S01-S03 and S16
def sub_path(sid, p0, p1, rz0, rz1, pitch=0.0):
    f0, f1 = SHOT[sid]
    k_ = (f1 - f0) / 155.0; p1 = p0 + (p1 - p0) * k_; rz1 = rz0 + (rz1 - rz0) * k_
    subA.location = p0; subA.rotation_euler = (0, R(pitch), rz0)
    subA.keyframe_insert("location", frame=f0); subA.keyframe_insert("rotation_euler", frame=f0)
    subA.location = p1; subA.rotation_euler = (0, R(pitch), rz1)
    subA.keyframe_insert("location", frame=f1); subA.keyframe_insert("rotation_euler", frame=f1)
sub_path("S01", Vector((0, 0, 7.0)), Vector((0.35, 0.1, 5.3)), R(20), R(26), pitch=8)
sub_path("S02", Vector((0.4, 0.1, 5.0)), Vector((0.7, 0.25, 3.8)), R(26), R(30), pitch=6)
sub_path("S03", Vector((-1.0, -0.6, -2.6)), Vector((1.6, 0.4, -3.1)), R(22), R(22), pitch=2)
sub_path("S16", Vector((0.0, 0.0, -2.2)), Vector((0.8, 0.3, -2.4)), R(22), R(24), pitch=0)
interp_all(subA, 'LINEAR')
# S16: lights out (lamps dim one after another, strobe last)
mlamp, mred, mdome = subA_mats
def key_emit(m, f, v):
    nd = m.node_tree.nodes.get("Emission") or m.node_tree.nodes.get("Principled BSDF")
    sock = nd.inputs[1] if nd.type == 'EMISSION' else nd.inputs["Emission Strength"]
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f)
for mm, on in ((mlamp, 30.0), (mred, 12.0), (mdome, 0.05)):
    key_emit(mm, fs, on); key_emit(mm, F("S16", 0.5), on)
key_emit(mlamp, F("S16", 0.9), 0.0); key_emit(mdome, F("S16", 1.1), 0.0); key_emit(mred, F("S16", 1.4), 0.0)
for l in subA_lamps:
    if l.type == 'LIGHT':
        l.data.energy = 900; l.data.keyframe_insert("energy", frame=F("S16", 0.5))
        l.data.energy = 0; l.data.keyframe_insert("energy", frame=F("S16", 0.9))
        l.data.energy = 900; l.data.keyframe_insert("energy", frame=fs)
for idb in (mlamp.node_tree, mred.node_tree, mdome.node_tree): interp_all(idb, 'LINEAR')
# --- SubB implosion (S11 at 0.45 s, crumple over 10 frames = "under a millisecond" shown in slow motion), cloud S12
fI = F("S11", SH.get("implode_s", 0.55))
for o in subB_parts:
    if o.type == 'MESH' and o.data.shape_keys:
        kb = o.data.shape_keys.key_blocks["Crush"]
        kb.value = 0; kb.keyframe_insert("value", frame=fs); kb.keyframe_insert("value", frame=fI)
        kb.value = 1; kb.keyframe_insert("value", frame=fI + 10)
for l in subB_lamps:
    if l.type == 'LIGHT':
        l.data.energy = 900; l.data.keyframe_insert("energy", frame=fI); l.data.energy = 0; l.data.keyframe_insert("energy", frame=fI + 3)
subB.location = Vector((-30, 25, 2)); subB.keyframe_insert("location", frame=fs)
subB.location = Vector((-29.4, 25.1, 1.9)); subB.keyframe_insert("location", frame=fI)
subB.rotation_euler = (0, 0, R(-10)); subB.keyframe_insert("rotation_euler", frame=fI)
subB.location = Vector((-29.3, 25.1, 1.3)); subB.keyframe_insert("location", frame=SHOT["S12"][1])
subB.rotation_euler = (R(10), R(-12), R(-4)); subB.keyframe_insert("rotation_euler", frame=SHOT["S12"][1])
flashL.data.energy = 0; flashL.data.keyframe_insert("energy", frame=fI + 6)
flashL.data.energy = 60000; flashL.data.keyframe_insert("energy", frame=fI + 9)
flashL.data.energy = 0; flashL.data.keyframe_insert("energy", frame=fI + 20)
flashG.scale = (0.01,) * 3; flashG.keyframe_insert("scale", frame=fs); flashG.keyframe_insert("scale", frame=fI + 6)
flashG.scale = (1.6, 0.9, 0.9); flashG.keyframe_insert("scale", frame=fI + 9)
flashG.scale = (0.01,) * 3; flashG.keyframe_insert("scale", frame=fI + 16)
bub.scale = (0.01,) * 3; bub.keyframe_insert("scale", frame=fs); bub.keyframe_insert("scale", frame=fI + 8)
bub.scale = (1.4,) * 3; bub.keyframe_insert("scale", frame=fI + 30)
bub.scale = (2.2,) * 3; bub.location = subB.location.copy() + Vector((0, 0, 1.2)); bub.keyframe_insert("scale", frame=SHOT["S12"][1]); bub.keyframe_insert("location", frame=SHOT["S12"][1])
bub.location = Vector((-29.4, 25.1, 1.9)); bub.keyframe_insert("location", frame=fI + 8)
bub.scale = (0.001,) * 3; bub.keyframe_insert("scale", frame=SHOT["S12"][1] + 1)
# SubB (the implosion copy) and its FX exist only during S11-S12, so the deep-sea shots never show a second sub
for o in [subB] + list(subB.children_recursive) + [bub, bubm, flashG]:
    key_hide(o, fs, True); key_hide(o, SHOT["S11"][0], False); key_hide(o, SHOT["S12"][1] + 1, True)
    for fc in all_fcurves(o):
        if fc.data_path in ("hide_render", "hide_viewport"):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
# S09 frames the eye close: hide the destination brain there (it sat as a sliver at the frame edge); it shows in S10
for o in [br2E] + list(br2E.children_recursive):
    key_hide(o, fs, False); key_hide(o, SHOT["S09"][0], True); key_hide(o, SHOT["S10"][0], False)
    for fc in all_fcurves(o):
        if fc.data_path in ("hide_render", "hide_viewport"):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
# --- comparison: the optic pulse barely leaves the eye while the mini sub crumples (S13: 0.6 s; S14 holds the crushed state)
fC = F("S13", SH.get("compare_crush_s", 1.37))
for o in subC_parts:
    if o.type == 'MESH' and o.data.shape_keys:
        kb = o.data.shape_keys.key_blocks["Crush"]
        kb.value = 0; kb.keyframe_insert("value", frame=fs); kb.keyframe_insert("value", frame=fC)
        kb.value = 1; kb.keyframe_insert("value", frame=fC + 10)
flashC.scale = (0.01,) * 3; flashC.keyframe_insert("scale", frame=fs); flashC.keyframe_insert("scale", frame=fC + 5)
flashC.scale = (1.4, 1, 1); flashC.keyframe_insert("scale", frame=fC + 8)
flashC.scale = (0.01,) * 3; flashC.keyframe_insert("scale", frame=fC + 15)
# the first ~10 % of the optic nerve path lies inside the eyeball: start the pulse just outside it, so it reads
optFP3.offset_factor = 0.26; optFP3.keyframe_insert("offset_factor", frame=fs); optFP3.keyframe_insert("offset_factor", frame=F("S13", 0.3))
optFP3.offset_factor = 0.32; optFP3.keyframe_insert("offset_factor", frame=SHOT["S14"][1])
optP3.scale = (0.01,) * 3; optP3.keyframe_insert("scale", frame=fs); optP3.keyframe_insert("scale", frame=F("S13", 0.25))
optP3.scale = (1,) * 3; optP3.keyframe_insert("scale", frame=F("S13", 0.35))
# --- pain pulse S07 (travels 0 -> 1 over 1.8 s), brain glows S07 end + S08, bolts pop in S08
f7a, f7b = F("S07", 0.2), F("S07", 2.0)
painFP.offset_factor = 0.0; painFP.keyframe_insert("offset_factor", frame=fs); painFP.keyframe_insert("offset_factor", frame=f7a)
painFP.offset_factor = 1.0; painFP.keyframe_insert("offset_factor", frame=f7b)
painP.scale = (1,) * 3; painP.keyframe_insert("scale", frame=f7b)
painP.scale = (0.01,) * 3; painP.keyframe_insert("scale", frame=f7b + 6)
pbr = mbrain.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
pbr.default_value = 0.0; pbr.keyframe_insert("default_value", frame=fs); pbr.keyframe_insert("default_value", frame=f7b - 4)
pbr.default_value = 0.8; pbr.keyframe_insert("default_value", frame=F("S08", 0.4))
pbr.default_value = 0.35; pbr.keyframe_insert("default_value", frame=F("S08", 1.6))
pbr.default_value = 0.0; pbr.keyframe_insert("default_value", frame=SHOT["S08"][1] + 1)
for i, bo in enumerate(bolts):
    fb = F("S08", 0.15 + 0.12 * i)
    bo.scale = (0.01,) * 3; bo.keyframe_insert("scale", frame=fs); bo.keyframe_insert("scale", frame=fb)
    bo.scale = (1.6,) * 3; bo.keyframe_insert("scale", frame=fb + 6)
    bo.scale = (1.3,) * 3; bo.keyframe_insert("scale", frame=fb + 14)
    bo.scale = (1.45,) * 3; bo.keyframe_insert("scale", frame=fb + 30)
# --- eye: light ray flashes into the pupil S09, optic pulse travels in S10
ray.location = EY + Vector((0, -0.46 - 0.8, 0.0)); ray.rotation_euler = (R(90), 0, 0)
ray.scale = (0.01,) * 3; ray.keyframe_insert("scale", frame=fs); ray.keyframe_insert("scale", frame=F("S09", 0.5))
ray.scale = (1, 1, 1); ray.keyframe_insert("scale", frame=F("S09", 0.7))
ray.keyframe_insert("scale", frame=SHOT["S09"][1])
ray.scale = (0.01,) * 3; ray.keyframe_insert("scale", frame=SHOT["S09"][1] + 1)
optFP.offset_factor = 0.0; optFP.keyframe_insert("offset_factor", frame=fs); optFP.keyframe_insert("offset_factor", frame=F("S09", 0.8))
optFP.offset_factor = 0.12; optFP.keyframe_insert("offset_factor", frame=SHOT["S09"][1])
optFP.offset_factor = 0.15; optFP.keyframe_insert("offset_factor", frame=SHOT["S10"][0])
optFP.offset_factor = 1.0; optFP.keyframe_insert("offset_factor", frame=F("S10", 1.6))
optP.scale = (0.01,) * 3; optP.keyframe_insert("scale", frame=fs); optP.keyframe_insert("scale", frame=F("S09", 0.75))
optP.scale = (1,) * 3; optP.keyframe_insert("scale", frame=F("S09", 0.85))
eyE.rotation_euler = (0, 0, R(-6)); eyE.keyframe_insert("rotation_euler", frame=SHOT["S09"][0])
eyE.rotation_euler = (0, 0, R(4)); eyE.keyframe_insert("rotation_euler", frame=SHOT["S10"][1])
brE.rotation_euler = (0, 0, R(-12)); brE.keyframe_insert("rotation_euler", frame=SHOT["S07"][0])
brE.rotation_euler = (0, 0, R(10)); brE.keyframe_insert("rotation_euler", frame=SHOT["S08"][1])
for o in (eyE, brE): interp_all(o, 'LINEAR')

# --- the man: seated on the sofa, watching TV (faces -Y)
bpy.context.view_layer.update()
# seat height: ray-cast the sofa cushions at the man's seat point
deps = bpy.context.evaluated_depsgraph_get()
seat_xy = RM + Vector((0.15, D / 2 - 0.62, 0))
hit, loc_, nrm_, idx_, ob_, mx_ = sc.ray_cast(deps, seat_xy + Vector((0, 0, 2.0)), Vector((0, 0, -1)))
seat_z = loc_.z if hit else 0.45
print("SEAT", hit, ob_.name if hit else None, round(seat_z, 3))
hip = MR.BN["upperleg01.L"].head_local.z
root_h = MR.BN["root"].head_local.z
seat_root = Vector((seat_xy.x, seat_xy.y - 0.12, seat_z + (root_h - hip) + 0.08))
def seated(f, lean=0.0, head=(0.0, 0.0), twist=0.0, breath=0.0):
    HM.key_root(f, seat_root + Vector((0, -0.04 * lean / 20, 0)), yaw=0, flex=0.0)
    HM.key_spine(f, flex=-14 + lean + breath, twist=twist, side=0, head=head)
    for s_ in "LR":
        sx = 1 if s_ == "L" else -1
        xy = Vector((seat_root.x + sx * 0.16, seat_root.y - 0.42))
        HM.key_foot(s_, f, xy, 0)
from mathutils.bvhtree import BVHTree as _BVH
_BODY = next(c for c in man.children if c.name.endswith(".body"))
_gi = {g.index: g.name for g in _BODY.vertex_groups}; _bones = {b.name for b in man.data.bones}
_lab = {}
for v in _BODY.data.vertices:
    gs = [g for g in v.groups if _gi.get(g.group) in _bones]
    if gs: _lab[v.index] = _gi[max(gs, key=lambda g: g.weight).group]
_THIGH = {i for i, n in _lab.items() if any(k in n for k in ("upperleg", "pelvis", "lowerleg"))}
def finger_depth(f, side):
    """deepest fingertip/hand point (m) inside the thigh skin of the base body mesh (no subsurf / mask)"""
    mods = [m for m in _BODY.modifiers if m.type in ('MASK', 'SUBSURF')]
    for m in mods: m.show_viewport = False
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    ev = _BODY.evaluated_get(dg); me = ev.to_mesh(); mw = _BODY.matrix_world; V = [mw @ v.co for v in me.vertices]
    T = _BVH.FromPolygons(V, [tuple(p.vertices) for p in me.polygons if all(i in _THIGH for i in p.vertices)])
    ev.to_mesh_clear()
    for m in mods: m.show_viewport = True
    worst = 0.0
    for i, n in _lab.items():
        if not n.endswith("." + side) or not any(k in n for k in ("finger", "metacarpal", "wrist")): continue
        loc, nrm, _, d = T.find_nearest(V[i], 0.08)
        if loc is not None and (V[i] - loc).dot(nrm) < 0: worst = max(worst, d)
    return worst
def rest_hands(f, fwd=0.0):
    """palms on the thighs (ray-cast the thigh top), fingers pointing to the knees"""
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    suit = next(c for c in man.children if "casualsuit" in c.name)
    se = suit.evaluated_get(dg); Mi = suit.matrix_world.inverted()
    for s_ in "LR":
        sx = 1 if s_ == "L" else -1
        Mw = man.matrix_world
        knee = Mw @ man.pose.bones["lowerleg01." + s_].head; hipw = Mw @ man.pose.bones["upperleg01." + s_].head
        pnt = hipw.lerp(knee, 0.55 + min(fwd, 0.08))   # stay on the flat of the thigh (near the knee the fingertips sank in)
        h_, l_, n_, i_ = se.ray_cast(Mi @ (pnt + Vector((0, 0, 0.4))), Mi.to_3x3() @ Vector((0, 0, -1)))
        top = suit.matrix_world @ l_ if h_ else pnt + Vector((0, 0, 0.08))
        skin_ = 0.02
        for it_ in range(3):     # a light lift only if a fingertip still sinks into the thigh (base mesh, as clip_scan tests it)
            place_hand(man, s_, f, top, Vector((0, 0, -1)), (knee - hipw).normalized(), skin=skin_)
            apply_pose(man, s_, "rest_thigh", f)
            d_ = finger_depth(f, s_)
            if d_ < 0.012 or skin_ > 0.035: break
            skin_ = min(0.036, skin_ + d_ - 0.008)
        print("HAND", f, s_, round(skin_, 3), round(d_, 3))
from mathutils.bvhtree import BVHTree
def seat_penetration(f):
    """how far (m) the man's body/clothes dip below the sofa's top surface (seat and backrest), at frame f"""
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    so = bpy.data.objects["Object_2"].evaluated_get(dg); me = so.to_mesh(); mw = so.matrix_world
    SV = [mw @ v.co for v in me.vertices]; front = min(v.y for v in SV)
    T = BVHTree.FromPolygons(SV, [tuple(p.vertices) for p in me.polygons]); so.to_mesh_clear()
    down, back = 0.0, 0.0
    for c in man.children:
        if c.type != 'MESH' or not any(k in c.name for k in ("body", "casualsuit")): continue
        e = c.evaluated_get(dg); m2 = e.to_mesh(); M = e.matrix_world
        for v in m2.vertices:
            w = M @ v.co
            if w.z > seat_z + 0.5 or abs(w.x - seat_xy.x) > 0.6 or w.y < front + 0.15: continue
            h = T.ray_cast(Vector((w.x, w.y, w.z + 0.35)), Vector((0, 0, -1)), 0.35)
            if h[0] is not None: down = max(down, h[0].z - w.z)
            h = T.ray_cast(Vector((w.x, w.y - 0.3, w.z)), Vector((0, 1, 0)), 0.3)
            if h[0] is not None and w.z > seat_z + 0.05: back = max(back, w.y - h[0].y)
        e.to_mesh_clear()
    return down, back
_f0 = SHOT["S04"][0]
for it in range(3):
    seated(_f0); bpy.context.view_layer.update()
    dn, bk = seat_penetration(_f0)
    print("SEATFIX", it, round(dn, 3), round(bk, 3))
    if dn < 0.004 and bk < 0.004: break
    seat_root += Vector((0, -(bk + 0.01) if bk > 0.004 else 0, (dn + 0.01) if dn > 0.004 else 0))
seat_root += Vector((0, 0, 0.035))   # margin: body_prop_cross tests the base mesh (no subsurf), which sits ~2 cm lower
# acting (director P1 note: no frozen sitting). (u, lean deg, (head pitch, head turn), hands slide toward knees)
# S05: he leans in with his hands sliding to his knees, head tilting (wondering); S15: an exhale (sinks back), then he
# leans forward and looks down, hands sliding forward, a small slow head shake.
for sid, acts in (("S04", [(0.0, 0, (0, 0), 0.0), (0.7, 2, (-4, 4), 0.0), (1.4, 3, (-4, 8), 0.02)]),
                  ("S05", [(0.0, 3, (-4, 4), 0.02), (0.4, 9, (-2, 0), 0.10), (0.9, 16, (6, -8), 0.22), (1.5, 18, (8, -12), 0.26)]),
                  ("S15", [(0.0, 4, (-2, 0), 0.04), (0.45, -2, (2, 0), 0.0), (1.0, 10, (14, 3), 0.14), (1.5, 13, (18, -4), 0.18), (2.0, 13, (20, 3), 0.18)])):
    if sid not in SHOT: continue
    f0, f1 = SHOT[sid]
    for u, lean, head, fwd in acts:      # u = seconds from the shot start (1x speed; keys past the cut are harmless)
        fr = f0 + round(u * 60)
        seated(fr, lean=lean, head=head, breath=1.5 * math.sin(u * 6.28))
        rest_hands(fr, fwd=fwd)
# --- TV screen: a plane on the TV front showing a frame of the sub (filled in by 03_tvscreen.py)
bpy.context.view_layer.update()
tmn, tmx = bbox(tv)
bpy.ops.mesh.primitive_plane_add(size=1); scr = bpy.context.object; scr.name = "TVScreen"; link(scr, C_ROOM)
scr.rotation_euler = (R(90), 0, R(180))
scr.location = Vector(((tmn.x + tmx.x) / 2, tmx.y + 0.003, tmn.z + (tmx.z - tmn.z) * 0.55))
scr.scale = ((tmx.x - tmn.x) * 0.62, (tmx.z - tmn.z) * 0.55, 1)
mscr = emit_mat("TVScreen_M", (0.3, 0.55, 0.8), 2.0); scr.data.materials.append(mscr)
key_emit(mscr, fs, 2.0)

# ================================================================== CAMERA per shot
seat_head = seat_root + Vector((0, 0, 0.75))
SA = lambda: subA.location
shot_cam("S01", [(0, Vector((14, -9, 13)), Vector((0, 0, 6.6))), (1, Vector((8.5, -11.5, 8.0)), Vector((0.3, 0.1, 5.0)))], 35)
shot_cam("S02", [(0, Vector((7.6, -2.4, 5.4)), Vector((1.4, 0.5, 4.5))), (1, Vector((7.0, 0.6, 4.2)), Vector((1.5, 0.8, 3.5)))], 35)
shot_cam("S03", [(0, Vector((11.5, -8.5, -5.0)), Vector((-0.6, -0.4, -2.9))), (1, Vector((12.0, -7.4, -4.7)), Vector((1.6, 0.4, -3.0)))], 30)
shot_cam("S04", [(0, RM + Vector((1.05, -1.15, 1.45)), seat_head + Vector((0.72, -0.35, -0.5))),
                 (1, RM + Vector((0.98, -0.8, 1.4)), seat_head + Vector((0.7, -0.35, -0.48)))], 22)
shot_cam("S05", [(0, RM + Vector((0.75, 0.2, 1.25)), seat_head + Vector((0, -0.1, -0.15))),
                 (1, RM + Vector((0.6, 0.45, 1.2)), seat_head + Vector((0, -0.12, -0.08)))], 35)
shot_cam("S06", [(0, RM + Vector((0.45, 0.65, 1.32)), seat_head + Vector((0, -0.05, 0.02))),
                 (1, RM + Vector((0.32, 0.95, 1.30)), seat_head + Vector((0, -0.05, 0.04)))], 50)
shot_cam("S07", [(0, AN + Vector((0.9, -4.6, 0.0)), AN + Vector((-0.5, 0, 0.0))), (1, AN + Vector((0.2, -2.7, 0.65)), AN + Vector((-0.1, 0, 0.5)))], 35)
shot_cam("S08", [(0, AN + Vector((-1.1, -1.9, 1.2)), AN + Vector((0.05, 0, 0.95))), (1, AN + Vector((1.0, -2.2, 1.3)), AN + Vector((0.25, 0, 1.0)))], 35)
shot_cam("S09", [(0, EY + Vector((-1.9, -2.8, 0.2)), EY + Vector((-0.1, -0.2, 0))), (1, EY + Vector((-1.0, -2.3, 0.45)), EY + Vector((-0.1, -0.2, 0)))], 50)
_b2 = br2E.location + Vector((0, 0, 0.6))
shot_cam("S10", [(0, EY + Vector((-0.6, -2.7, 0.7)), EY + Vector((0.05, 0.25, 0.05))), (1, _b2 + Vector((-0.7, -2.7, 0.8)), _b2 + Vector((-0.3, 0, 0)))], 28)
SB = Vector((-30, 25, 2))
shot_cam("S11", [(0, SB + Vector((5.0, -9.5, 1.8)), SB), (1, SB + Vector((4.0, -8.0, 1.5)), SB + Vector((0.3, 0, -0.2)))], 32)
shot_cam("S12", [(0, SB + Vector((-7.0, -6.5, 2.5)), SB + Vector((0.4, 0.1, 0.0))), (1, SB + Vector((-6.0, -5.6, 2.0)), SB + Vector((0.5, 0.1, -0.3)))], 32)
shot_cam("S13", [(0, CP + Vector((0.2, -4.6, 1.5)), CP + Vector((0.0, 0.5, 0.75))), (1, CP + Vector((0.0, -4.0, 1.4)), CP + Vector((0.0, 0.5, 0.75)))], 30)
shot_cam("S14", [(0, CP + Vector((1.4, -3.8, 1.5)), CP + Vector((0.0, 0.45, 0.9))), (1, CP + Vector((-0.9, -3.2, 1.7)), CP + Vector((-0.1, 0.5, 0.95)))], 26)
shot_cam("S15", [(0, RM + Vector((-0.75, -0.2, 1.05)), seat_head + Vector((0, -0.1, -0.2))),
                 (1, RM + Vector((-0.6, 0.1, 1.05)), seat_head + Vector((0, -0.1, -0.2)))], 35)
shot_cam("S16", [(0, Vector((11.0, -5.5, -1.2)), Vector((0.6, 0.1, -2.3))), (1, Vector((12.2, -5.0, -1.7)), Vector((1.3, 0.4, -2.4)))], 32)
shot_cam("S17", [(0, SF + Vector((-25, 30, 10.0)), SF + Vector((0, 150, 6))), (1, SF + Vector((-2, 58, 7.5)), SF + Vector((0, 150, 6)))], 35)
interp_all(cam, 'LINEAR'); interp_all(tgt, 'LINEAR'); interp_all(cam.data, 'LINEAR')
# hard cuts: constant from each shot's last key to the next shot's first key
for idb in (cam, tgt, cam.data):
    for fc in all_fcurves(idb):
        for k in fc.keyframe_points:
            fr = int(round(k.co.x))
            if any(fr == SHOT[s][1] for s in SHOT): k.interpolation = 'CONSTANT'
# man keys: smooth (bezier) is fine; FX keys linear
for o in (subB, bub, flashG, flashC, ray, optP, optP3, painP): interp_all(o, 'LINEAR')
# delivery box with our logo (the film's only logo placement), on the floor right of the sofa; built without ops
def make_logo_box():
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * 0.7, v.co.y * 0.5, v.co.z * 0.5 + 0.25))
    me = bpy.data.meshes.new("LogoBox"); bm.to_mesh(me); bm.free()
    bx = bpy.data.objects.new("LogoBox", me); C_ROOM.objects.link(bx)
    me.materials.append(mat("Cardboard_M", (0.70, 0.52, 0.33), 0.75))
    bv = bx.modifiers.new("Bevel", 'BEVEL'); bv.width = 0.008; bv.segments = 2
    bx.location = RM + Vector((1.5, D / 2 - 1.15, 0.0)); bx.rotation_euler = (0, 0, R(-15))
    bm = bmesh.new(); w, h = 0.56, 0.56 * 414 / 967
    vs = [bm.verts.new(Vector((x, -0.2515, z))) for x, z in ((-w / 2, 0.25 - h / 2), (w / 2, 0.25 - h / 2), (w / 2, 0.25 + h / 2), (-w / 2, 0.25 + h / 2))]
    fc = bm.faces.new(vs); uv = bm.loops.layers.uv.new("UVMap")
    for lp, (u, v_) in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = (u, v_)
    me2 = bpy.data.meshes.new("Logo_Box"); bm.to_mesh(me2); bm.free()
    lg = bpy.data.objects.new("Logo_Box", me2); C_ROOM.objects.link(lg); lg.parent = bx
    ml = bpy.data.materials.new("Logo_M"); ml.use_nodes = True; nt = ml.node_tree; p = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(BRAND, "DaKrasFilms_logo_dark.png"))
    nt.links.new(t.outputs["Color"], p.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
    p.inputs["Roughness"].default_value = 0.7; me2.materials.append(ml)
    return bx
cardbox = make_logo_box()
json.dump({"shots": SHOT, "seat_z": seat_z}, open(os.path.join(os.path.dirname(OUT), "layout.json"), "w"), indent=1)
# VO as a sound strip from frame 1, render output
VO = SH.get("vo")
if VO:
    vo_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(SHOTS_JSON)), VO))
    if not sc.sequence_editor: sc.sequence_editor_create()
    try: strips = sc.sequence_editor.strips
    except AttributeError: strips = sc.sequence_editor.sequences
    strips.new_sound("VO", vo_path, 1, 1)
sc.render.filepath = "//render/" + SH.get("name", "Film") + "_####"
sc.render.image_settings.file_format = 'PNG'
sc.frame_set(1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE", OUT, sc.frame_start, sc.frame_end)
