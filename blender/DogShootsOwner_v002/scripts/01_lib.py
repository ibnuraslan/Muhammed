"""DogShootsOwner: asset library (characters, dog, props, plants). Everything sits at the origin; 02_build.py places it.
blender -b <dog_rig.blend> --python 01_lib.py -- <glb_dir> <polyhaven_dir> <amb_clean.png> <out_lib.blend>
dog_rig.blend comes from pipeline/rig_quadruped.py on the Labrador GLB (height 0.72 m)."""
import bpy, sys, math, os
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
GLB, PH, AMBTEX, OUT = a
B = "/home/user/Muhammed/blender/"
R_ = math.radians

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c

def move_to(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)

# ------------------------------------------------------------------ dog
dog = bpy.data.objects["Dog_rig"]; dbody = bpy.data.objects["Dog_body"]
CD = coll("CHAR_Dog"); move_to(dog, CD); move_to(dbody, CD)
for m in dbody.data.materials:
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    lk = P.inputs['Base Color'].links
    if lk:
        src = lk[0].from_socket
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
        mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (1.0, 0.68, 0.34, 1)
        nt.links.new(src, mx.inputs['A']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    P.inputs['Roughness'].default_value = 0.6
    if 'Specular IOR Level' in P.inputs: P.inputs['Specular IOR Level'].default_value = 0.3
dbody.data.shade_smooth() if hasattr(dbody.data, "shade_smooth") else None
# eyes: the GLB eyes are part of the body texture; give them a little gloss
print("LIB dog", dog.name, dbody.name, len(dbody.data.vertices))

# ------------------------------------------------------------------ humans (re-dressed copies of approved characters)
def append_char(f, rn, new, drop=()):
    with bpy.data.libraries.load(f) as (src, dst):
        dst.objects = [n for n in src.objects if n == rn or n.startswith(rn + ".") or n.startswith(rn + "_")]
    c = coll("CHAR_" + new)
    rig = None
    for o in dst.objects:
        if o is None: continue
        if any(d in o.name for d in drop):
            bpy.data.objects.remove(o, do_unlink=True); continue
        c.objects.link(o)
        if o.type == 'ARMATURE' and o.name.split(".")[0] == rn: rig = o
    for o in list(c.objects):
        if o.type == 'ARMATURE' and o is not rig:
            for ch in list(o.children): bpy.data.objects.remove(ch, do_unlink=True)
            bpy.data.objects.remove(o, do_unlink=True)
    for o in list(c.objects):
        if o.type != 'ARMATURE' and o.parent is not rig:
            bpy.data.objects.remove(o, do_unlink=True)
    if rig.animation_data: rig.animation_data_clear()
    for o in rig.children:
        if o.animation_data: o.animation_data_clear()
        if o.data and getattr(o.data, "shape_keys", None) and o.data.shape_keys.animation_data:
            o.data.shape_keys.animation_data_clear()
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.name = new
    for o in rig.children:
        o.name = new + "." + o.name.split(".", 1)[1] if "." in o.name else new + "_" + o.name.split("_", 1)[-1]
        o.hide_render = o.hide_viewport = False
    print("LIB char", new, [o.name for o in rig.children])
    return rig

def tint(rig, key, rgb, rough=0.6):
    for ch in rig.children:
        if ch.type != 'MESH' or key not in ch.name: continue
        for m in ch.data.materials:
            nt = m.node_tree
            P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and 'diffuse' in n.name.lower()), None)
            hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
            bc = nt.nodes.new('ShaderNodeBrightContrast'); bc.inputs['Bright'].default_value = 0.25; bc.inputs['Contrast'].default_value = -0.3
            if tex:
                nt.links.new(tex.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], bc.inputs['Color'])
                nt.links.new(bc.outputs['Color'], mx.inputs['A'])
            else:
                mx.inputs['A'].default_value = (1, 1, 1, 1)
            nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
            P.inputs['Roughness'].default_value = rough
            for l in list(P.inputs['Roughness'].links): nt.links.remove(l)

owner = append_char(B + "WaterTubes_v006/WaterTubes_v006_60fps.blend", "Hero", "Owner")
tint(owner, "casualsuit", (0.30, 0.36, 0.20))      # olive-green jumper and trousers (non-skin)
tint(owner, "shoes", (0.16, 0.11, 0.08))
medA = append_char(B + "BelugaRescue_v008/BelugaRescue_v008_60fps.blend", "Keeper", "MedA")
tint(medA, "casualsuit", (0.16, 0.36, 0.70))       # blue scrubs
tint(medA, "shoes", (0.12, 0.12, 0.13))
medB = append_char(B + "MonkeyHeadTransplant_v012/MonkeyHeadTransplant_v012_60fps.blend", "Surgeon", "MedB",
                   drop=("_Gown", "_Mask", "_Cap"))
tint(medB, "casualsuit", (0.20, 0.42, 0.78))
tint(medB, "shoes", (0.12, 0.12, 0.13))

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

# open the elbow IK limit (MPFB rest elbow ~46 deg; a min-0 limit locks the arm in an A-pose)
for rig in (owner, medA, medB):
    for s in "LR":
        for bn in ("lowerarm01." + s, "lowerarm02." + s):
            pb = rig.pose.bones.get(bn)
            if pb:
                for ax in "xyz":
                    if getattr(pb, "use_ik_limit_" + ax):
                        setattr(pb, "ik_min_" + ax, min(getattr(pb, "ik_min_" + ax), R_(-60)))
                for c in pb.constraints:
                    if c.type == 'LIMIT_ROTATION':
                        c.min_x = min(c.min_x, R_(-60)); c.min_z = min(c.min_z, R_(-60))

# ------------------------------------------------------------------ owner's cap (plain tan baseball cap, Child Of head)
def make_cap(rig):
    hair = next(o for o in rig.children if o.name.endswith(".short02"))
    pts = [hair.matrix_world @ v.co for v in hair.data.vertices]
    top = max(p.z for p in pts)
    up = [p for p in pts if p.z > top - 0.09]
    cx = (max(p.x for p in up) + min(p.x for p in up)) / 2; cy = (max(p.y for p in up) + min(p.y for p in up)) / 2
    rx = (max(p.x for p in up) - min(p.x for p in up)) / 2 + 0.006
    ry = (max(p.y for p in up) - min(p.y for p in up)) / 2 + 0.006
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=(0, 0, 0))
    crown = bpy.context.active_object; crown.name = "Owner_Cap"
    me = crown.data
    for v in me.vertices:
        if v.co.z < -0.05: v.co.z = -0.05
    crown.scale = (rx, ry, 0.10); crown.location = (cx, cy, top - 0.088)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # remove bottom cap faces
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(v.co.z < -0.004 for v in f.verts)], context='FACES')
    bm.to_mesh(me); bm.free()
    sol = crown.modifiers.new("solid", 'SOLIDIFY'); sol.thickness = 0.006
    # brim: flattened half disc in front (-Y)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1, depth=0.008, location=(0, 0, 0))
    brim = bpy.context.active_object; brim.name = "Owner_CapBrim"
    bm = bmesh.new(); bm.from_mesh(brim.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > 0.15], context='VERTS')
    bm.to_mesh(brim.data); bm.free()
    brim.scale = (rx * 0.95, ry * 0.95 + 0.03, 1); brim.location = (cx, cy - ry * 0.45, top - 0.088 - 0.002)
    brim.rotation_euler = (R_(-8), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bw = brim.modifiers.new("bev", 'BEVEL'); bw.width = 0.003; bw.segments = 2
    mat = bpy.data.materials.new("CapTan"); mat.use_nodes = True
    Pn = mat.node_tree.nodes["Principled BSDF"]; Pn.inputs["Base Color"].default_value = (0.55, 0.42, 0.26, 1); Pn.inputs["Roughness"].default_value = 0.7
    for o in (crown, brim):
        o.data.materials.append(mat); bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
        bpy.context.view_layer.objects.active = o; bpy.ops.object.shade_smooth()
        bpy.context.view_layer.update()
        c = o.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "head"
        c.inverse_matrix = (rig.matrix_world @ rig.data.bones["head"].matrix_local).inverted()
        move_to(o, coll("CHAR_Owner"))
    print("LIB cap", round(rx, 3), round(ry, 3), round(top, 3))
# make_cap(owner)  # dropped: read as a helmet in tests

# ------------------------------------------------------------------ GLB props
def imp(name, path, target_size=None, axis=None, keep_parts=False):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1 and not keep_parts: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name
    pts = [v.co for v in ob.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    d = mx - mn
    s = 1.0
    if target_size:
        ax, val = target_size; s = val / d["xyz".index(ax)]
    cen = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    ob.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-cen))
    ob.data.update()
    move_to(ob, coll("PROPS"))
    pts = [v.co for v in ob.data.vertices]
    print("LIB prop", name, tuple(round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)))
    return ob

gun = imp("Shotgun", GLB + "/gun.glb", ("x", 1.0))          # ~1.0 m long pump gun, long axis X
phone = imp("Phone", GLB + "/phone.glb", ("z", 0.150))
seat = imp("CarSeat", GLB + "/seat1.glb", ("z", 1.20))
crate = imp("Crate", GLB + "/crate.glb", ("x", 0.95))
bed = imp("Bed", GLB + "/bed.glb", ("y", 2.15))
amb = imp("Ambulance", GLB + "/amb.glb", ("y", 5.6))
skel = imp("Skeleton", GLB + "/skel.glb", ("z", 1.78))
lungs = imp("Lungs", GLB + "/lungs.glb", ("z", 0.27))
# ambulance texture without its words
for m in amb.data.materials:
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image:
            n.image = bpy.data.images.load(AMBTEX); n.image.pack()

# ------------------------------------------------------------------ Poly Haven plants
PL = coll("PLANTS")
for pid in ("fir_tree_01", "fir_sapling_medium", "fern_02", "grass_medium_01", "shrub_02", "tree_stump_01"):
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
