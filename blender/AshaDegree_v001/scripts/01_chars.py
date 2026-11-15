"""Append generic MPFB (CC0) characters from earlier studio packages (the MakeHuman asset server is unreachable here),
strip their animation, recolour clothes. blender -b --factory-startup --python 01_chars.py -- work/chars.blend"""
import bpy, sys
BL = "/home/user/Muhammed/blender/"
SRC = [("NoPilotPlane_v010/NoPilotPlane_v010_60fps.blend", "PE", "Girl"),
       ("ElectricianPolice_v010/ElectricianPolice_v010_60fps.blend", "Man", "SearchA"),
       ("ElectricianPolice_v010/ElectricianPolice_v010_60fps.blend", "Vendor", "SearchB"),
       ("EscapeArtist_v010/EscapeArtist_v010_60fps.blend", "Father", "SearchC"),
       ("DrunkTrain_v007/DrunkTrain_v007_60fps.blend", "Worker", "Worker")]
out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
for path, rig, new in SRC:
    with bpy.data.libraries.load(BL + path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(rig + ".")]
    kids = [k for k in dst.objects if k is not None]
    r = next(k.parent for k in kids if k.parent and k.parent.type == 'ARMATURE')
    for k in kids:
        if k.parent is r: bpy.context.scene.collection.objects.link(k)
        else: bpy.data.objects.remove(k)
    kids = [k for k in r.children]
    bpy.context.scene.collection.objects.link(r)
    old = rig; r.name = new; r.data.name = new
    for k in kids: k.name = new + "." + k.name.split(".")[1]
    print("APPENDED", new, [k.name for k in kids])
for o in list(bpy.data.objects):
    if o.users_scene == () : bpy.data.objects.remove(o)
for o in bpy.data.objects:
    o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
    for c in list(o.constraints): o.constraints.remove(c)
    if o.type == 'ARMATURE':
        for pb in o.pose.bones:
            for c in list(pb.constraints): pb.constraints.remove(c)
            pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
        o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0)
for o in bpy.data.objects:
    o.hide_render = False; o.hide_viewport = False
for i, n in enumerate(["Girl", "SearchA", "SearchB", "SearchC", "Worker"]):
    bpy.data.objects[n].location.x = i * 1.0
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, o.parent.name if o.parent else None, [m.type + ":" + (getattr(m, 'object', None).name if getattr(m, 'object', None) else '') for m in o.modifiers][:4], [m.name for m in getattr(o.data, 'materials', [])][:3])
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
