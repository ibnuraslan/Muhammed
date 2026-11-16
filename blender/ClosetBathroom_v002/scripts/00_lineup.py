"""lineup of candidate characters. blender -b --factory-startup --python 00_lineup.py -- out.blend out.png"""
import bpy, sys, math
BL = "/home/user/Muhammed/blender/"
SRC = [("EscapeArtist_v010", "Father"), ("BelugaRescue_v008", "SpecB"), ("BelugaRescue_v008", "SpecF"),
       ("BelugaRescue_v008", "SpecG"), ("EarInArm_v011", "Surgeon"), ("DonationBin_v009", "Shover"),
       ("BellyFat_v007", "ShopperA"), ("FanCancer_v011", "Doctor")]
a = sys.argv[sys.argv.index("--") + 1:]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
def append(folder, rig, new):
    path = BL + folder + "/" + folder + "_60fps.blend"
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(rig + ".") or n == rig]
    objs = [k for k in dst.objects if k is not None]
    r = next(k for k in objs if k.type == 'ARMATURE' and k.name.split(".")[0] == rig)
    kids = [k for k in objs if k.parent is r and k.type == 'MESH']
    for k in objs:
        if k is not r and k not in kids: bpy.data.objects.remove(k)
    for k in [r] + kids: bpy.context.scene.collection.objects.link(k)
    r.name = new; r.data.name = new
    for k in kids: k.name = new + "." + k.name.split(".", 1)[1]
    r.animation_data_clear()
    for c in list(r.constraints): r.constraints.remove(c)
    for pb in r.pose.bones:
        for c in list(pb.constraints): pb.constraints.remove(c)
        pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    r.parent = None; r.location = (0, 0, 0); r.rotation_euler = (0, 0, 0)
    for k in kids:
        k.animation_data_clear(); k.hide_render = k.hide_viewport = False
        if k.data.shape_keys: k.data.shape_keys.animation_data_clear()
        for c in list(k.constraints): k.constraints.remove(c)
    return r
if __name__ == "__main__":
    for i, (f, n) in enumerate(SRC):
        r = append(f, n, n); r.location.x = (i - 3.5) * 0.75
        print("CHAR", n, r.scale[:], [k.name for k in r.children])
    sc = bpy.context.scene
    cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (0, -7.5, 1.0); cam.rotation_euler = (math.radians(90), 0, 0); cam.data.lens = 35
    sun = bpy.data.objects.new("S", bpy.data.lights.new("S", 'SUN')); sun.data.energy = 4; sun.rotation_euler = (0.7, 0.2, 0.3); sc.collection.objects.link(sun)
    sc.world = bpy.data.worlds.new("W"); sc.world.use_nodes = True; sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.7, 0.8, 0.9, 1)
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    sc.render.resolution_x = 1600; sc.render.resolution_y = 700; sc.render.filepath = a[1]
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=a[0], compress=True)
