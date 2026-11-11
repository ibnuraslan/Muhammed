import bpy, sys, math
from mathutils import Vector
out = sys.argv[sys.argv.index("--")+1]
sc = bpy.context.scene
h = bpy.data.objects["MK_Head"]; bA = bpy.data.objects["MK_BodyA"]; bB = bpy.data.objects["MK_BodyB"]
bB.location.x = 0.45; h.location.z = 0.09
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.7,0.8,0.9,1)
L = bpy.data.objects.new("l", bpy.data.lights.new("l", "SUN")); sc.collection.objects.link(L); L.rotation_euler = (0.7, 0.2, -0.4); L.data.energy = 3
sc.render.engine = "CYCLES"; sc.cycles.samples = 16; sc.render.resolution_x = 500; sc.render.resolution_y = 500
sc.render.image_settings.file_format = "JPEG"
def shot(nm, loc, tgt, lens):
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = lens
    sc.render.filepath = f"{out}_{nm}.jpg"; bpy.ops.render.render(write_still=True)
shot("wide", (0.35, -1.6, 0.6), (0.15, -0.25, 0.3), 35)
shot("under", (-0.3, -0.9, 0.25), (-0.08, -0.4, 0.42), 50)
h.location.z = 0
shot("eyes", (-0.16, -0.62, 0.46), (-0.085, -0.466, 0.444), 90)
# lids closed test
nt = bpy.data.materials["M_MonkeyHead"].node_tree; nt.nodes["GazeX"].outputs[0].default_value = 0.004
shot("gaze", (-0.16, -0.62, 0.46), (-0.085, -0.466, 0.444), 90)
nt.nodes["GazeX"].outputs[0].default_value = 0.0
for s in "LR":
    bpy.data.objects["LidUp_"+s].rotation_euler.x = math.radians(-2); bpy.data.objects["LidLo_"+s].rotation_euler.x = math.radians(2)
shot("closed", (-0.16, -0.62, 0.46), (-0.085, -0.466, 0.444), 90)
