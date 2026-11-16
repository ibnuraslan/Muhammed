"""Append candidate MPFB characters (rig + children) from earlier packages and render a face + full-body look.
blender -b --factory-startup --python look_chars.py -- out_dir pkg:Rig ..."""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; O = a[0]; os.makedirs(O, exist_ok=True)
B = "/home/user/Muhammed/blender/"
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.render.resolution_x = 400; sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.7, 0.75, 0.8)
for spec in a[1:]:
    pkg, rig = spec.split(":")
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    import glob
    path = glob.glob(B + pkg + "/*_60fps.blend")[0]
    with bpy.data.libraries.load(path, link=False) as (s, d):
        d.objects = [n for n in s.objects if n == rig or n.startswith(rig + ".")]
    R = None
    print("TRY", spec)
    for o in d.objects:
        if o is None: continue
        sc.collection.objects.link(o)
        if o.name.split(".")[0] == rig and o.type == 'ARMATURE': R = o
    for o in bpy.data.objects:
        o.animation_data_clear(); o.hide_render = False; o.hide_viewport = False
    if R is None: print("NORIG", spec); continue
    for pb in R.pose.bones:
        for c in list(pb.constraints): pb.constraints.remove(c)
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0)
    for c in list(R.constraints): R.constraints.remove(c)
    R.location = (0, 0, 0); R.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    hd = R.matrix_world @ R.data.bones["head"].head_local; ht = R.matrix_world @ R.data.bones["head"].tail_local
    print("CHAR", spec, "height", round(ht.z, 2), "scale", tuple(round(x, 2) for x in R.scale), [c.name for c in R.children])
    cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
    L = bpy.data.objects.new("L", bpy.data.lights.new("L", 'SUN')); L.data.energy = 3; L.rotation_euler = (0.9, 0, 0.3); sc.collection.objects.link(L)
    fc = (hd + ht) / 2; h = (ht - hd).length
    cam.data.lens = 50
    for tag, tgt, dist in (("face", fc, h * 7), ("body", Vector((fc.x, fc.y, ht.z * 0.5)), ht.z * 2.3)):
        cam.location = tgt + Vector((0, -dist, 0)); cam.rotation_euler = (1.5708, 0, 0)
        sc.render.filepath = f"{O}/{pkg}_{rig}_{tag}.png"; bpy.ops.render.render(write_still=True)
