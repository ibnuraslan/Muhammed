"""DogBuriedAlive: sets, per-shot animation at 1x, one camera per shot with hard-cut markers, look.
blender -b lib.blend --python 02_build.py -- <out.blend> [brand_dir]
Shot lengths come from shots.py (Phase 2: VO frames). Every shot is keyed from its own start frame."""
import bpy, sys, math, os, random, bmesh
from mathutils import Vector, Matrix, Euler, Quaternion
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
HERE = "/home/user/Muhammed/blender/DogBuriedAlive_v002/scripts"
BRAND = "/home/user/Muhammed/blender/assets/brand/"
P = "/home/user/Muhammed/blender/pipeline/"
exec(open(P + "anim_lib.py").read()); exec(open(P + "hand_poses.py").read())
exec(open(HERE + "/shots.py").read())
R_ = math.radians
random.seed(7)
sc = bpy.context.scene
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
SH = {sid: (st, f0, f1) for sid, st, f0, f1 in layout()}
FEND = max(f1 for _, f1 in [(v[1], v[2]) for v in SH.values()])
sc.frame_start = 1; sc.frame_end = FEND

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def move_to(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)

# ------------------------------------------------------------------ materials / shapes
MATS = {}
def mat(name, rgb, rough=0.5, metal=0.0, emit=None, ew=0.0, alpha=1.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1); p.inputs["Emission Strength"].default_value = ew
    if alpha < 1: p.inputs["Alpha"].default_value = alpha
    MATS[name] = m; return m

def rbox(name, size, loc, m, c, bevel=0.02, rot=(0, 0, 0), seg=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = seg; b.limit_method = 'NONE'
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m); move_to(o, c); return o

def cyl(name, r, depth, loc, m, c, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; bpy.ops.object.shade_smooth()
    o.data.materials.append(m); move_to(o, c); return o

def plane(name, size, loc, m, c, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m); move_to(o, c); return o

def dup(src, name, loc, rot=(0, 0, 0), scale=1.0, c=None, linked=True):
    o = src.copy()
    if not linked: o.data = src.data.copy()
    o.name = name; o.rotation_mode = 'XYZ'; o.location = loc; o.rotation_euler = rot
    o.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    (c or src.users_collection[0]).objects.link(o); bpy.context.view_layer.update(); return o

def area(name, loc, target, energy, size, c, color=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = energy; L.size = size; L.color = color
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o

def point(name, loc, energy, c, color=(1, 1, 1), r=0.05):
    L = bpy.data.lights.new(name, 'POINT'); L.energy = energy; L.color = color; L.shadow_soft_size = r
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc; return o

def logo_decal(name, loc, rot, width, dark, c, parent=None):
    img = bpy.data.images.load(BRAND + ("DaKrasFilms_logo_dark.png" if dark else "DaKrasFilms_logo_white.png"), check_existing=True)
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True; nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]; tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
    nt.links.new(tx.outputs["Color"], pr.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], pr.inputs["Alpha"])
    pr.inputs["Roughness"].default_value = 0.5
    m.blend_method = 'BLEND' if hasattr(m, "blend_method") else None
    o = plane(name, (width, width * 414 / 967), loc, m, c, rot)
    if parent:
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw
    return o

# ------------------------------------------------------------------ world: sky gradient seen by camera, soft light
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputWorld"); lp = nt.nodes.new("ShaderNodeLightPath")
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.05; mr.inputs["From Max"].default_value = 0.5
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (0.72, 0.90, 1.0, 1); ramp.color_ramp.elements[1].color = (0.10, 0.52, 0.95, 1)
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
bg_cam = nt.nodes.new("ShaderNodeBackground"); nt.links.new(ramp.outputs["Color"], bg_cam.inputs["Color"]); bg_cam.inputs["Strength"].default_value = 1.0
bg_lit = nt.nodes.new("ShaderNodeBackground"); bg_lit.inputs["Color"].default_value = (0.85, 0.92, 1.0, 1); bg_lit.inputs["Strength"].default_value = 1.6
SUN = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(SUN)
SUN.data.energy = 4.0; SUN.data.angle = R_(8); SUN.rotation_euler = (R_(40), R_(10), R_(35))
mix = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
nt.links.new(bg_lit.outputs[0], mix.inputs[1]); nt.links.new(bg_cam.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], o_.inputs[0])

def keyobj(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale if not isinstance(scale, (int, float)) else (scale,) * 3; o.keyframe_insert("scale", frame=f)

def emit_key(m, f, v):
    p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Emission Strength"].default_value = v
    p.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)

def light_key(o, f, e):
    o.data.energy = e; o.data.keyframe_insert("energy", frame=f)

def lerp(a, b, t): return a + (b - a) * t
def ease(t): return t * t * (3 - 2 * t)

# cameras
CAMC = coll("CAMERAS")
CAMS = {}
def camera(sid, lens=35, fstop=8.0):
    cd = bpy.data.cameras.new("CAM_" + sid); cd.lens = lens; cd.clip_start = 0.02
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    o = bpy.data.objects.new("CAM_" + sid, cd); CAMC.objects.link(o); CAMS[sid] = o
    return o
def cam_key(o, f, loc, tgt, lens=None, focus=None):
    # compatible Euler (no +pi/-pi wrap between keys, which spun the camera the long way round)
    o.location = loc; o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler('XYZ', o.rotation_euler)
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    if lens: o.data.lens = lens; o.data.keyframe_insert("lens", frame=f)
    o.data.dof.focus_distance = focus if focus else (Vector(tgt) - Vector(loc)).length
    o.data.dof.keyframe_insert("focus_distance", frame=f)

def lerp(a, b, t): return a + (b - a) * t
def ease(t): return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ library objects
DAD = bpy.data.objects["Dad"]; MOM = bpy.data.objects["Mom"]; SON = bpy.data.objects["Son"]
DOG = bpy.data.objects["Dog"]; DOGB = bpy.data.objects["Dog_body"]
PLANTS = {o.name: o for o in bpy.data.collections["PLANTS"].objects}
LIBC = bpy.data.collections["PLANTS"]
for o in PLANTS.values(): o.location = (0, 0, -50)
exec(open(HERE + "/02_sets.py").read())
exec(open(HERE + "/03_shots.py").read())
lay = layout()
CLUMP_SHOTS = {"G01", "G02", "U13", "Y14"}
for sid, st, f0, f1 in lay:
    if sid not in CLUMP_SHOTS:
        for cl in CLUMPS: clump_park(cl, f0)
    FUN[sid](f0, f1)
    pres = PRESENT[sid]
    for key in ("dad", "mom", "son", "dog"):
        if key not in pres: park(key, f0); park(key, f1)
    if sid not in ("U13",): keyobj(TUNNEL, f0, loc=Vector((0, 0.18, -60)))
    if sid not in ("Y14",): keyobj(HOLE, f0, loc=YMOUND + Vector((0, 0, -60)))
    if sid in ("Y06", "Y07", "Y08"):
        keyobj(SUVB, f0, loc=SUVB.location.copy() if sid == "Y08" else DRV + Vector((0, 2.5, 0)), rot=(0, 0, R_(180)) if sid != "Y08" else None)
    if sid in ("Y06", "Y07"):
        keyobj(SUVB, f0, loc=DRV + Vector((0, 2.5, 0)), rot=(0, 0, R_(180)))
    if sid in ("Y14",): keyobj(SUVB, f0, loc=YX + Vector((40, -9, 0)))
    mound_on = sid not in ("Y06",)
    keyobj(MOUND_Y, f0, scale=(0.75, 0.55, 0.20) if mound_on else (0.75, 0.55, 0.001))
    print("BUILD shot", sid, st, f0, f1, sorted(pres))

BOUND = set()
for sid, st, f0, f1 in lay: BOUND |= {f0, f1}
ENDS = {f1 for _, _, _, f1 in lay}
def all_fcurves(action):
    try:
        return list(action.fcurves)
    except Exception:
        out = []
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags: out += list(cb.fcurves)
        return out
def _fix(ad):
    if not ad or not ad.action: return
    for fc in all_fcurves(ad.action):
        for kp in fc.keyframe_points:
            fr = int(round(kp.co.x))
            if fr in BOUND: kp.handle_left_type = 'VECTOR'; kp.handle_right_type = 'VECTOR'
            if fr in ENDS or fr + 1 in BOUND and fr not in BOUND: kp.interpolation = 'CONSTANT'
        fc.update()
for idb in list(bpy.data.objects) + list(bpy.data.materials) + list(bpy.data.lights) + list(bpy.data.cameras):
    _fix(getattr(idb, "animation_data", None))
# parking keys one frame before a shot (clumps, cutters) must not drift: constant everywhere for those
for o in CLUMPS + [TUNNEL, HOLE, FILL, MOUND_G, MOUND_Y, POCKET] + LIDS:
    if o.animation_data and o.animation_data.action:
        for fc in all_fcurves(o.animation_data.action):
            for kp in fc.keyframe_points:
                if o in (TUNNEL, HOLE, MOUND_Y, POCKET) or o in LIDS: kp.interpolation = 'CONSTANT'

for sid, st, f0, f1 in lay:
    mk = sc.timeline_markers.new("S" + sid, frame=f0); mk.camera = CAMS[sid]
sc.camera = CAMS[lay[0][0]]
sc.frame_end = lay[-1][3]
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.render.use_motion_blur = False
for o in bpy.data.collections["PROPS"].objects:
    if o.parent is None or o.parent.name in ("SUV", "Pickup"): o.hide_render = o.hide_viewport = True
for o in (SUV, PICKUP, HOUSE, bpy.data.objects["shovel_GEO"]) + tuple(bpy.data.objects["shovel_GEO"].children): o.hide_render = o.hide_viewport = True
for o in LIBC.objects: o.hide_render = o.hide_viewport = True
SHOVEL.hide_render = SHOVEL.hide_viewport = True; SHOVY.hide_render = SHOVY.hide_viewport = True   # the only shovel asset read as a bucket: dropped
sc.view_settings.exposure = 0.2
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT, "frames", sc.frame_start, sc.frame_end)
