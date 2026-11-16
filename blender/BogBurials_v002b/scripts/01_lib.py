"""BogBurials: asset library (characters, wolf, props, plants). Everything sits at the origin; 02_build.py places it.
blender -b <wolf_rig.blend> --python 01_lib.py -- <glb_dir> <polyhaven_dir> <out_lib.blend>
wolf_rig.blend comes from pipeline/rig_quadruped.py on the wolf GLB (height 0.80 m).
Humans are re-dressed copies of characters from our approved films (the MakeHuman asset server is down for new ones)."""
import bpy, sys, math, os, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
GLB, PH, OUT = a
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

# ------------------------------------------------------------------ wolf (grey coat, clean)
wolf = bpy.data.objects["Wolf_rig"]; wbody = bpy.data.objects["Wolf_body"]
CW = coll("CHAR_Wolf"); move_to(wolf, CW); move_to(wbody, CW)
for m in wbody.data.materials:
    P = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if P:
        P.inputs['Roughness'].default_value = 0.7
        if 'Specular IOR Level' in P.inputs: P.inputs['Specular IOR Level'].default_value = 0.3

# ------------------------------------------------------------------ humans
def append_char(f, rn, new, drop=(), extra=()):
    with bpy.data.libraries.load(f) as (src, dst):
        dst.objects = [n for n in src.objects if n == rn or n.startswith(rn + ".") or n.startswith(rn + "_") or n in extra]
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
        for con in list(o.constraints):
            if con.type == 'CHILD_OF': con.influence = 1.0
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.name = new
    for o in rig.children:
        if o.name in extra: o.name = new + "_" + o.name; continue
        o.name = new + "." + o.name.split(".", 1)[1] if "." in o.name else new + "_" + o.name.split("_", 1)[-1]
        o.hide_render = o.hide_viewport = False
    print("LIB char", new, [o.name for o in rig.children])
    return rig

def tint(rig, key, rgb, rough=0.6, bright=0.25):
    for ch in rig.children:
        if ch.type != 'MESH' or key not in ch.name: continue
        for m in ch.data.materials:
            nt = m.node_tree
            P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and 'diffuse' in n.name.lower()), None)
            hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
            bc = nt.nodes.new('ShaderNodeBrightContrast'); bc.inputs['Bright'].default_value = bright; bc.inputs['Contrast'].default_value = -0.3
            if tex:
                nt.links.new(tex.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], bc.inputs['Color'])
                nt.links.new(bc.outputs['Color'], mx.inputs['A'])
            else:
                mx.inputs['A'].default_value = (1, 1, 1, 1)
            nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
            P.inputs['Roughness'].default_value = rough
            for l in list(P.inputs['Roughness'].links): nt.links.remove(l)

burA = append_char(B + "EscapeArtist_v010/EscapeArtist_v010_60fps.blend", "Father", "BurA")
tint(burA, "casualsuit", (0.45, 0.27, 0.13))     # hide-brown tunic and leggings
tint(burA, "shoes", (0.22, 0.13, 0.07))          # leather moccasins
burB = append_char(B + "BelugaRescue_v008/BelugaRescue_v008_60fps.blend", "SpecD", "BurB")
tint(burB, "casualsuit", (0.62, 0.46, 0.22))     # ochre tunic
tint(burB, "shoes", (0.22, 0.13, 0.07))
dead = append_char(B + "BellyFat_v010/BellyFat_v010_60fps.blend", "ShopperC", "Dead")
tint(dead, "elegantsuit", (0.86, 0.80, 0.66), 0.8, 0.3)   # cream woven burial garment
tint(dead, "shoes", (0.30, 0.19, 0.10))
worker = append_char(B + "ElectricianPolice_v010/ElectricianPolice_v010_60fps.blend", "Man", "Worker")
tint(worker, "casualsuit", (0.20, 0.24, 0.32), 0.7, 0.15)  # navy work shirt and work trousers; the hi-vis vest keeps its own colour
tint(worker, "shoes", (0.22, 0.14, 0.08))                  # brown work boots
arch = append_char(B + "FrozenTearsGun_v010/FrozenTearsGun_v010_60fps.blend", "Inventor", "Arch", drop=("Funnel",))
tint(arch, "casualsuit", (0.55, 0.50, 0.32))     # khaki field shirt and trousers
tint(arch, "shoes", (0.25, 0.17, 0.10))
HUMANS = (burA, burB, dead, worker, arch)

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
for rig in HUMANS:
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
    print("LIB rig", rig.name, "IK bones", [b.name for b in rig.data.bones if b.name.startswith(("IK_", "Pole_"))])

# ------------------------------------------------------------------ GLB props
def imp(name, path, target_size=None, keep_mats=True):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH' and len(o.data.polygons) > 0]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
        for md in list(o.modifiers):
            if md.type == 'ARMATURE': o.modifiers.remove(md)
    for o in new:
        if o not in meshes: bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name; ob.rotation_mode = 'XYZ'
    if ob.animation_data: ob.animation_data_clear()
    pts = [v.co for v in ob.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    s = 1.0
    if target_size:
        ax, val = target_size; s = val / (mx - mn)["xyz".index(ax)]
    cen = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    ob.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-cen)); ob.data.update()
    move_to(ob, coll("PROPS"))
    pts = [v.co for v in ob.data.vertices]
    print("LIB prop", name, tuple(round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)), len(ob.data.polygons))
    return ob

skel = imp("Skeleton", GLB + "/skel.glb", ("z", 1.60))
brain = imp("Brain", GLB + "/brain.glb", ("y", 0.16))
excav = imp("Excavator", GLB + "/excav.glb", ("x", 9.0))
truck = imp("Pickup", GLB + "/truck.glb", ("y", 4.9))
brush = imp("Brush", GLB + "/brush.glb", ("x", 0.17))
hardhat = imp("HardHat", GLB + "/hardhat.glb", ("x", 0.29))

def plain(ob, rgb, rough=0.5, metal=0.0, keep_dark=True):
    """replace texture colours with one clean colour (removes brand text / grime); dark parts (tyres, glass) keep theirs"""
    m = bpy.data.materials.new(ob.name + "_plain"); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    ob.data.materials.clear(); ob.data.materials.append(m)
    return m
plain(excav, (0.95, 0.66, 0.08), 0.45)      # CAT text and numbers removed: plain yellow
# truck: keep its textured materials but recolour the paint white for the logo door; words on the plates removed
for m in truck.data.materials:
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE':
            print("LIB truck tex", m.name, n.image.name if n.image else None, n.image.size[:] if n.image else None)
plain(brush, (0.55, 0.38, 0.20), 0.6)
plain(hardhat, (1.0, 0.62, 0.05), 0.4)

# ------------------------------------------------------------------ Poly Haven plants
PL = coll("PLANTS")
for pid in ("grass_medium_01", "grass_medium_02", "dry_branches_medium_01", "dead_tree_trunk", "island_tree_02",
            "tree_stump_01", "shrub_02"):
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
