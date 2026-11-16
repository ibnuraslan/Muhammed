"""Hero bat: the CC-BY 'Bat | Kelelawar' scan joined, decimated, scaled to a 0.40 m wingspan (big fruit-bat size, like a
rubber Halloween bat), head up +Z, face -Y, wings along X, with a 7-bone armature (root, head, wing1/2 L/R, legs) weighted by position.
blender -b scene.blend --python 03_bat.py -- out.blend   (adds objects 'Bat' + 'BatRig' to the open file)"""
import bpy, sys, math
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath="/home/user/Muhammed/blender/BatBite_v001/assets/bat.glb")
new = [o for o in bpy.data.objects if o not in before]
empt = [o.name for o in new if o.type != 'MESH']
meshes = [o for o in new if o.type == 'MESH']
for o in meshes:
    M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
bat = bpy.context.view_layer.objects.active; bat.name = "Bat"; bat.data.name = "Bat"
for n in empt:
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
# rotate +90 about Z (face -X -> -Y, wings Y -> X), scale, centre on the body
S = 0.48 / 11705.0
me = bat.data
R = Matrix.Rotation(math.radians(90), 4, 'Z')
for v in me.vertices: v.co = (R @ v.co) * S
body = [v.co for v in me.vertices if abs(v.co.x) < 0.03]
c = Vector((sum(p.x for p in body) / len(body), sum(p.y for p in body) / len(body), sum(p.z for p in body) / len(body)))
for v in me.vertices: v.co -= c
lo = Vector([min(v.co[i] for v in me.vertices) for i in range(3)]); hi = Vector([max(v.co[i] for v in me.vertices) for i in range(3)])
print("BAT bbox", tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi), "faces", len(me.polygons))
dec = bat.modifiers.new("Dec", 'DECIMATE'); dec.ratio = 0.35
bpy.context.view_layer.objects.active = bat; bpy.ops.object.modifier_apply(modifier="Dec")
for p in me.polygons: p.use_smooth = True
print("BAT faces after", len(me.polygons))
# armature
arm = bpy.data.armatures.new("BatRig"); rig = bpy.data.objects.new("BatRig", arm); bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
zt = hi.z; zb = lo.z
def bone(n, h, t, par=None):
    b = arm.edit_bones.new(n); b.head = h; b.tail = t; b.roll = 0
    if par: b.parent = arm.edit_bones[par]
    return b
bone("root", Vector((0, 0, zb * 0.3)), Vector((0, 0, zt * 0.45)))
bone("head", Vector((0, 0, zt * 0.45)), Vector((0, 0, zt)), "root")
bone("legs", Vector((0, 0, zb * 0.3)), Vector((0, 0, zb)), "root")
for s, sx in (("L", 1), ("R", -1)):
    bone("wing1." + s, Vector((0.025 * sx, 0, 0.01)), Vector((0.10 * sx, 0, 0.02)), "root")
    bone("wing2." + s, Vector((0.10 * sx, 0, 0.02)), Vector((0.20 * sx, 0, 0.0)), "wing1." + s)
bpy.ops.object.mode_set(mode='OBJECT')
def sm(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
G = {n: bat.vertex_groups.new(name=n) for n in ("root", "head", "legs", "wing1.L", "wing2.L", "wing1.R", "wing2.R")}
for v in me.vertices:
    p = v.co; ax = abs(p.x); s = "L" if p.x > 0 else "R"
    w1 = sm(0.028, 0.055, ax); w2 = sm(0.09, 0.12, ax)
    core = 1 - w1
    hd = sm(zt * 0.30, zt * 0.55, p.z) * core; lg = sm(zb * 0.2, zb * 0.6, p.z) * core
    rt = core - hd - lg
    for n, w in (("root", rt), ("head", hd), ("legs", lg), ("wing1." + s, w1 * (1 - w2)), ("wing2." + s, w1 * w2)):
        if w > 1e-4: G[n].add([v.index], w, 'REPLACE')
bat.parent = rig
am = bat.modifiers.new("Armature", 'ARMATURE'); am.object = rig
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
# clean animated look: lift the fur colour a touch, roughness >= 0.45
for m in me.materials:
    if m and m.use_nodes:
        P = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if P:
            for l in list(P.inputs['Roughness'].links): m.node_tree.links.remove(l)
            P.inputs['Roughness'].default_value = 0.55
rig.location = (0, 0, -50)  # parked
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
