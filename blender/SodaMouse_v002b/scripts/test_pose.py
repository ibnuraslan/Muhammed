import bpy, os, math
from mathutils import Vector, Matrix
exec(open(os.path.dirname(__file__) + "/common.py").read())
exec(open(PIPE + "/anim_lib.py").read()); exec(open(PIPE + "/hand_poses.py").read()); exec(open(os.path.dirname(__file__) + "/lib.py").read())
man = Man("SodaMan"); f = 1
man.stand(f, (0, 0.42)); man.spine(f, flex=-4, pitch=-22)
man.hang("L", f)
sc.frame_set(f)
can = bpy.data.objects["SodaCan"]
lip = head_point(man, mouth_rest(man))
can.matrix_world = can_frame((0, 0.75, 0.66), lip)
sc.frame_set(f)
a = can.matrix_world.to_3x3() @ Vector((0, 0, 1)); org = can.matrix_world.translation
C = org + a * 0.055 + Vector((-0.033, 0, 0))
res = grip_object(man.o, "R", f, can, C, (1, 0, 0))
print("GRIP", res)
sc.frame_set(f)
print("WRIST", man.wrist_world("R").translation, "C", C, "LIP", lip)
cams = bpy.data.collections.get("CAMS") or bpy.data.collections.new("CAMS")
if cams.name not in sc.collection.children: sc.collection.children.link(cams)
sc.render.engine = 'CYCLES'; sc.cycles.samples = 12; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
sc.render.resolution_x = 540; sc.render.resolution_y = 960
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 1.2
for i, (eye, tgt, lens) in enumerate([((0.9, -0.6, 1.5), (0, 0.3, 1.42), 50), ((0.0, -1.6, 1.3), (0, 0.3, 1.2), 35), ((-0.8, -0.4, 1.45), (0, 0.3, 1.42), 60)]):
    c = cam("T%d" % i, lens); look(c, f, eye, tgt); sc.camera = c
    sc.render.filepath = SCR + "/tp_%d.png" % i; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/test_pose.blend")
