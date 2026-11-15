"""Portrait photo for the framed picture (S23-S24): our generic girl (not any real person) holding a teddy bear,
school-photo style. blender -b work/dressed.blend --python 05_portrait.py -- assets/portrait.png"""
import bpy, sys, math
from mathutils import Vector, Matrix
P_ = "/home/user/Muhammed/blender/pipeline/"; HERE = "/home/user/Muhammed/blender/AshaDegree_v001/"
exec(open(P_ + "anim_lib.py").read()); exec(open(P_ + "hand_poses.py").read()); exec(open(HERE + "scripts/asha_lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; R_ = math.radians
for o in bpy.data.objects:
    if o.type == 'ARMATURE' and o.name != "Girl":
        for c in o.children: c.hide_render = True
        o.hide_render = True
G = bpy.data.objects["Girl"]; H = setup_char(G); s_ = G.scale.x
p = Vector((0, 0, H.root_head.z))
H.key_root(1, p, yaw=0); H.key_spine(1, flex=-2, head=(-4, 8))
for s in "LR": H.key_foot(s, 1, H.foot_xy(s, Vector((0, 0, 0)), 0), 0)
# teddy hugged against the chest
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=HERE + "assets/teddy.glb")
new = [o for o in bpy.data.objects if o not in before]; ms = [o for o in new if o.type == 'MESH']
bpy.context.view_layer.update(); mws = {o.name: o.matrix_world.copy() for o in ms}
for o in ms: o.parent = None
for o in ms: o.matrix_world = mws[o.name]
for o in new:
    if o not in ms: bpy.data.objects.remove(o)
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]; bpy.ops.object.join(); T = bpy.context.object
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
pts = [v.co for v in T.data.vertices]; mn = Vector([min(q[i] for q in pts) for i in range(3)]); mx = Vector([max(q[i] for q in pts) for i in range(3)])
T.data.transform(Matrix.Scale(0.30 / (mx - mn).z, 4) @ Matrix.Translation(-(mn + mx) / 2)); bpy.context.view_layer.update()
sc.frame_set(1); bpy.context.view_layer.update()
chest = G.matrix_world @ G.pose.bones["spine04"].head
T.location = chest + Vector((0, -0.16, 0.06)); T.rotation_euler = (0, 0, R_(0))
# hands on the bear's sides
for s in "LR":
    sx = 1 if s == "L" else -1
    Wp = (T.location + Vector((0.11 * sx, 0.02, -0.02))) / s_
    H.key_hand(s, 1, Wp + Vector((0.03 * sx, 0.03, 0)) / s_, Vector((-sx * 0.6, -0.4, 0.3)), Vector((-sx, 0.2, 0)), pole=p + Vector((0.5 * sx, 0.3, -0.2)))
    apply_pose(G, s, "cup_hold", 1)
cam = bpy.data.objects.new("PC", bpy.data.cameras.new("PC")); sc.collection.objects.link(cam); sc.camera = cam
head = G.matrix_world @ G.pose.bones["head"].head
cam.location = head + Vector((0.15, -1.3, -0.1)); cam.data.lens = 60
cam.rotation_euler = ((head + Vector((0, 0, -0.18))) - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 1.2, 1.0), rotation=(R_(90), 0, 0)); bd = bpy.context.object
m = bpy.data.materials.new("Backdrop"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.55, 0.8, 1); bd.data.materials.append(m)
for nm, loc, e in (("K", (1.2, -1.6, 1.8), 220), ("F", (-1.3, -1.4, 1.4), 90)):
    l = bpy.data.lights.new(nm, 'AREA'); l.energy = e; l.size = 1.5; lo = bpy.data.objects.new(nm, l); sc.collection.objects.link(lo); lo.location = loc
    lo.rotation_euler = (Vector((0, 0, 1.1)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
sc.world = bpy.data.worlds.new("PW"); sc.world.color = (0.4, 0.42, 0.45)
sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 600, 760
sc.view_settings.view_transform = 'AgX'
sc.frame_set(2); sc.frame_set(1); bpy.context.view_layer.update(); sc.render.filepath = out; bpy.ops.render.render(write_still=True); print("PORTRAIT", out)
