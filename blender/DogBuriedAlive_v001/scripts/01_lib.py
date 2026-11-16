"""DogBuriedAlive: asset library. Everything sits at the origin; 02_build.py places it.
blender -b --factory-startup --python 01_lib.py -- <glb_dir> <polyhaven_dir> <out_lib.blend>
Dog: the Labrador rig from SpeakWithoutSight_v006 (Sketchfab CC-BY Yury Misiyuk, rigged with pipeline/rig_quadruped.py),
the same model ConnectB01 used. Family: Tsunami2004_v012 TouristM (Dad), LocalW (Mom), KidA (Son), re-dressed."""
import bpy, sys, math, os
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
GLB, PH, OUT = a
B = "/home/user/Muhammed/blender/"
R_ = math.radians
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    return c
def move_to(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)

# ------------------------------------------------------------------ dog
with bpy.data.libraries.load(B + "SpeakWithoutSight_v006/SpeakWithoutSight_v006_60fps.blend") as (src, dst):
    dst.objects = ["Dog_rig", "Dog_body"]
dog, dbody = dst.objects
CD = coll("CHAR_Dog"); CD.objects.link(dog); CD.objects.link(dbody)
for o in (dog, dbody):
    if o.animation_data: o.animation_data_clear()
for pb in dog.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0)
dog.location = (0, 0, 0); dog.rotation_euler = (0, 0, 0); dog.scale = (1.25, 1.25, 1.25)   # 0.55 m -> ~0.69 m (lab head height)
dog.name = "Dog"; dbody.name = "Dog_body"
for m in dbody.data.materials:
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    lk = P.inputs['Base Color'].links
    if lk:   # cream-yellow labrador coat (reference), uniform
        src_ = lk[0].from_socket
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
        mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (1.0, 0.80, 0.55, 1)
        nt.links.new(src_, mx.inputs['A']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    P.inputs['Roughness'].default_value = 0.6
    if 'Specular IOR Level' in P.inputs: P.inputs['Specular IOR Level'].default_value = 0.3
print("LIB dog", [b.name for b in dog.data.bones][:5], len(dbody.data.vertices))

# ------------------------------------------------------------------ humans (re-dressed copies of approved characters)
def append_char(f, rn, new, drop=()):
    with bpy.data.libraries.load(f) as (src, dst):
        dst.objects = [n for n in src.objects if n == rn or n.startswith(rn + ".")]
    c = coll("CHAR_" + new); rig = None
    for o in dst.objects:
        if o is None: continue
        if any(d in o.name for d in drop): bpy.data.objects.remove(o, do_unlink=True); continue
        c.objects.link(o)
        if o.type == 'ARMATURE' and o.name == rn: rig = o
    for o in list(c.objects):
        if o.type != 'ARMATURE' and o.parent is not rig: bpy.data.objects.remove(o, do_unlink=True)
    if rig.animation_data: rig.animation_data_clear()
    for o in rig.children:
        if o.animation_data: o.animation_data_clear()
        if o.data and getattr(o.data, "shape_keys", None) and o.data.shape_keys.animation_data:
            o.data.shape_keys.animation_data_clear()
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.name = new
    for o in rig.children:
        o.name = new + "." + o.name.split(".", 1)[1]
        o.hide_render = o.hide_viewport = False
    print("LIB char", new, [o.name for o in rig.children])
    return rig

def tint(rig, key, rgb, rough=0.6, keep_tex=0.25):
    for ch in rig.children:
        if ch.type != 'MESH' or key not in ch.name: continue
        for m in ch.data.materials:
            m = m.copy(); ch.data.materials[0] = m if len(ch.data.materials) == 1 else m
            nt = m.node_tree
            P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and 'diffuse' in n.name.lower()), None)
            hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
            bc = nt.nodes.new('ShaderNodeBrightContrast'); bc.inputs['Bright'].default_value = keep_tex; bc.inputs['Contrast'].default_value = -0.3
            if tex:
                nt.links.new(tex.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], bc.inputs['Color'])
                nt.links.new(bc.outputs['Color'], mx.inputs['A'])
            else:
                mx.inputs['A'].default_value = (1, 1, 1, 1)
            nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
            P.inputs['Roughness'].default_value = rough
            for l in list(P.inputs['Roughness'].links): nt.links.remove(l)

TS = B + "Tsunami2004_v012/Tsunami2004_v012_60fps.blend"
dad = append_char(TS, "TouristM", "Dad")
mom = append_char(TS, "LocalW", "Mom")
son = append_char(TS, "KidA", "Son")
# outfit colours: all clearly non-skin
tint(dad, "casualsuit", (0.20, 0.30, 0.48))     # navy shirt + trousers
tint(dad, "shoes", (0.14, 0.10, 0.08))
tint(mom, "casualsuit", (0.85, 0.62, 0.12))     # mustard yellow top (reference)
tint(mom, "shoes", (0.9, 0.9, 0.9))
tint(son, "casualsuit", (0.62, 0.10, 0.10))     # red tee
tint(son, "shoes", (0.15, 0.15, 0.18))

# eye fix on every EnhancedEye group (LegoInNose eye_fix.py a44130b)
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    if any(n.name.startswith("CorneaTransparentMix") for n in g.nodes): continue
    P = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None)
    OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
    if not P or not OUTN: continue
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    srcs = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN]
    if not ol: continue
    out_sock = ol[0].to_socket; g.links.remove(ol[0])
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if srcs: g.links.new(srcs, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    print("LIB eyefix", g.name)

# open the elbow IK limit (MPFB rest elbow ~46 deg)
for rig in (dad, mom, son):
    for s in "LR":
        for bn in ("lowerarm01." + s, "lowerarm02." + s):
            pb = rig.pose.bones.get(bn)
            if not pb: continue
            for ax in "xyz":
                if getattr(pb, "use_ik_limit_" + ax): setattr(pb, "ik_min_" + ax, min(getattr(pb, "ik_min_" + ax), R_(-60)))
            for c in pb.constraints:
                if c.type == 'LIMIT_ROTATION': c.min_x = min(c.min_x, R_(-60)); c.min_z = min(c.min_z, R_(-60))

# ------------------------------------------------------------------ GLB props
def imp(name, path, target_size, wheel_key=None):
    """import a GLB, bake transforms, scale so the given axis has the given size, origin at the base centre.
    wheel_key(obj, centre) -> wheel label or None: those parts stay separate (they spin) and are parented to the body."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH' and len(o.data.polygons)]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o not in meshes: bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pts = [v.co for o in meshes for v in o.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    ax, val = target_size; s = val / (mx - mn)["xyz".index(ax)]
    cen = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    T = Matrix.Scale(s, 4) @ Matrix.Translation(-cen)
    wheels = {}
    for o in meshes:
        o.data.transform(T); o.data.update()
        if wheel_key:
            vs = [v.co for v in o.data.vertices]
            c = sum(vs, Vector()) / len(vs)
            k = wheel_key(o, c)
            if k: wheels[k] = (o, c)
    body = [o for o in meshes if all(o is not w[0] for w in wheels.values())]
    bpy.ops.object.select_all(action='DESELECT')
    for o in body: o.select_set(True)
    bpy.context.view_layer.objects.active = body[0]
    if len(body) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name
    if ob.animation_data: ob.animation_data_clear()
    move_to(ob, coll("PROPS"))
    for k, (o, c) in wheels.items():
        o.data.transform(Matrix.Translation(-c)); o.location = c; o.name = name + "_Wheel_" + k
        o.parent = ob; move_to(o, coll("PROPS"))
    pts = [v.co for v in ob.data.vertices]
    print("LIB prop", name, tuple(round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)), [m.name for m in ob.data.materials][:12], sorted(wheels))
    return ob

imp("House", GLB + "/house2.glb", ("z", 8.5))
imp("SUV", GLB + "/suv.glb", ("z", 1.66), lambda o, c: o.name.split("_")[1] if o.name.startswith("Wheel_") else None)
imp("Pickup", GLB + "/pickup2.glb", ("z", 1.90),
    lambda o, c: (("F" if c.y < 0 else "R") + ("L" if c.x > 0 else "R")) if o.data.materials[0].name == "ban_pck" else None)

# shovel from ToddlerWell (no hands on it: it stands in the dirt pile)
with bpy.data.libraries.load(B + "ToddlerWell_v008/ToddlerWell_v008_60fps.blend") as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("shovel_GEO")]
for o in dst.objects:
    if o: coll("PROPS").objects.link(o)
print("LIB shovel", [o.name for o in dst.objects if o])

# ------------------------------------------------------------------ Poly Haven plants / rocks
PL = coll("PLANTS")
for pid in ("grass_medium_01", "shrub_02", "fern_02", "rock_09"):
    f = f"{PH}/{pid}/{pid}_1k.blend"
    if not os.path.exists(f): print("LIB missing", pid); continue
    with bpy.data.libraries.load(f) as (src, dst):
        dst.objects = list(src.objects)
    for o in dst.objects:
        if o and o.type == 'MESH':
            PL.objects.link(o); o.name = "PH_" + o.name
            print("LIB plant", o.name, len(o.data.polygons), tuple(round(v, 2) for v in o.dimensions))
bpy.ops.file.make_paths_absolute()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("LIB_OK", OUT)
