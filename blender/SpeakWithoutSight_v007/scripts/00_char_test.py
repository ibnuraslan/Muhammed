"""quick look at the two characters (rest pose) - scratch only"""
import bpy, sys, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
G, GB = human("Girl", 0.0, 0.17, {"asian": 0.1, "caucasian": 0.8, "african": 0.1}, "braid01/braid01.mhclo",
              "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
              height=0.5, weight=0.5, muscle=0.4, clothes=["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes02/shoes02.mhclo"])
T, TB = human("Teacher", 0.0, 0.42, {"asian": 0.1, "caucasian": 0.3, "african": 0.6}, "ponytail01/ponytail01.mhclo",
              "young_african_female/young_african_female.mhmat", "eyebrow010/eyebrow010.mhclo",
              height=0.5, weight=0.5, muscle=0.45, clothes=["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"])
T.location.x = 0.7
eye_fix(G); eye_fix(T); eye_group_fix()
for o in (G, T):
    print(o.name, [c.name for c in o.children], o.dimensions)
    print("head z", (o.matrix_world @ o.data.bones["head"].head_local).z)
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); bpy.context.scene.collection.objects.link(cam)
cam.location = (0.35, -3.6, 1.0); cam.rotation_euler = (math.radians(90), 0, 0); bpy.context.scene.camera = cam
cam.data.lens = 40
L = bpy.data.objects.new("L", bpy.data.lights.new("L", 'SUN')); bpy.context.scene.collection.objects.link(L)
L.rotation_euler = (math.radians(50), 0, math.radians(-30)); L.data.energy = 4
w = bpy.context.scene.world or bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.35, 0.4, 1)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.render.resolution_x = 540; sc.render.resolution_y = 540
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT.replace(".png", ".blend"))
