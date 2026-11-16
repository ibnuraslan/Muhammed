"""Append generic MPFB (CC0) characters from earlier studio packages, strip animation and bone constraints,
keep worn items (Child Of to their own rig). blender -b --factory-startup --python 01_chars.py -- work/chars.blend"""
import bpy, sys
BL = "/home/user/Muhammed/blender/"
SRC = [("BellyFat_v010/BellyFat_v010_60fps.blend", "Woman", "Mom"),
       ("ToddlerWell_v008/ToddlerWell_v008_60fps.blend", "Toddler", "Kid"),
       ("ElectricianPolice_v010/ElectricianPolice_v010_60fps.blend", "OfficerA", "CopA"),
       ("ElectricianPolice_v010/ElectricianPolice_v010_60fps.blend", "OfficerB", "CopB"),
       ("ToddlerWell_v008/ToddlerWell_v008_60fps.blend", "ResA", "ResA"),
       ("ToddlerWell_v008/ToddlerWell_v008_60fps.blend", "ResB", "ResB"),
       ("ElectricianPolice_v010/ElectricianPolice_v010_60fps.blend", "Vendor", "Clerk")]
out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
for path, rig, new in SRC:
    with bpy.data.libraries.load(BL + path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n == rig or n.startswith(rig + ".") or n.startswith(rig + "_")]
    objs = [k for k in dst.objects if k is not None]
    r = next(k for k in objs if k.name.split(".")[0] == rig and k.type == 'ARMATURE')
    keep = []
    for k in objs:
        if k is r or k.parent is r or any(c.type == 'CHILD_OF' and c.target is r for c in k.constraints) or (k.parent and k.parent.parent is r):
            bpy.context.scene.collection.objects.link(k); keep.append(k)
        else:
            bpy.data.objects.remove(k)
    for k in keep:
        if k is r: continue
        tail = k.name[len(r.name):] if k.name.startswith(r.name) else "." + k.name
        k.name = new + tail
    r.name = new; r.data.name = new
    print("APPENDED", new, [k.name for k in keep])
for o in list(bpy.data.objects):
    if not o.users_scene: bpy.data.objects.remove(o)
for o in bpy.data.objects:
    o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
    for c in list(o.constraints):
        if c.type != 'CHILD_OF': o.constraints.remove(c)
    if o.type == 'ARMATURE':
        for pb in o.pose.bones:
            for c in list(pb.constraints): pb.constraints.remove(c)
            pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
        o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0)
    o.hide_render = False if not o.name.endswith(("jacketsrc",)) else True
    o.hide_viewport = o.hide_render
# Child Of constraints: recompute inverse at rest so worn items sit where they were authored at rest
bpy.context.view_layer.update()
for i, n in enumerate(["Mom", "Kid", "CopA", "CopB", "ResA", "ResB", "Clerk"]):
    bpy.data.objects[n].location.x = i * 0.9
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, o.parent.name if o.parent else None, o.hide_render, [c.type + ":" + str(getattr(c, 'subtarget', '')) for c in o.constraints], [m.name for m in getattr(o.data, 'materials', [])][:3] if o.type == 'MESH' else '')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
