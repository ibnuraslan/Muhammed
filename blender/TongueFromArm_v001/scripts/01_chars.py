"""Append generic MPFB (CC0) characters from earlier studio packages, strip animation/constraints, rename.
blender -b --factory-startup --python 01_chars.py -- work/chars.blend"""
import bpy, sys
BL = "/home/user/Muhammed/blender/"
SRC = [("Tsunami2004_v012/Tsunami2004_v012_60fps.blend", "TouristW", "Patient"),
       ("FanCancer_v011/FanCancer_v011_60fps.blend", "Doctor", "Doctor"),
       ("Tsunami2004_v012/Tsunami2004_v012_60fps.blend", "KidB", "Girl"),
       ("EarInArm_v011/EarInArm_v011_60fps.blend", "Surgeon", "Surgeon"),
       ("EarInArm_v011/EarInArm_v011_60fps.blend", "Nurse", "Nurse")]
out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
KEEP = ("body", "eyebrow", "eyelashes", "high-poly", "suit", "shoes", "short", "teeth", "tongue", "ponytail", "bob", "long", "_Cap", "_FaceMask", "_Mask", "Glove")
for path, rig, new in SRC:
    with bpy.data.libraries.load(BL + path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n == rig or n.startswith(rig + ".") or n.startswith(rig + "_")]
    objs = [k for k in dst.objects if k is not None]
    r = next(k for k in objs if k.name == rig or (k.type == 'ARMATURE' and k.name.startswith(rig)))
    bpy.context.scene.collection.objects.link(r)
    for k in objs:
        if k is r: continue
        if k.parent is r and any(t in k.name for t in KEEP) and k.type == 'MESH':
            bpy.context.scene.collection.objects.link(k)
    r.name = new; r.data.name = new
    for k in r.children:
        k.name = new + "." + k.name.split(".", 1)[1] if "." in k.name else new + "_" + k.name.split("_", 1)[1]
    print("APPENDED", new, [k.name for k in r.children])
for o in list(bpy.data.objects):
    if not o.users_scene: bpy.data.objects.remove(o)
for o in bpy.data.objects:
    o.hide_render = False; o.hide_viewport = False; o.hide_set(False)
for o in bpy.data.objects:
    o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
    for m in getattr(o, "modifiers", []):
        if m.type == 'ARMATURE' and m.object is None: print("WARN no arm obj", o.name)
    if o.type == 'ARMATURE':
        for pb in o.pose.bones:
            for c in list(pb.constraints): pb.constraints.remove(c)
            pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
        o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0)
        # drop non-default bones added by earlier films (IK controls / poles), anim_lib adds its own
        bpy.context.view_layer.objects.active = o; bpy.ops.object.mode_set(mode='EDIT')
        for eb in list(o.data.edit_bones):
            if eb.name.startswith(("IK_", "Pole_", "MCH", "CTRL")): o.data.edit_bones.remove(eb)
        bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.data.objects:
    o.hide_render = False; o.hide_viewport = False
    if o.type == 'MESH':
        for c in list(o.constraints):
            if c.type == 'CHILD_OF' and c.target and c.target.type == 'ARMATURE': continue
            o.constraints.remove(c)
for i, n in enumerate(["Patient", "Doctor", "Girl", "Surgeon", "Nurse"]):
    bpy.data.objects[n].location.x = i * 0.8
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, o.parent.name if o.parent else None, [c.type + ":" + str(getattr(c, 'subtarget', '')) for c in o.constraints], [m.type for m in getattr(o, "modifiers", [])][:5], [m.name for m in getattr(o.data, 'materials', [])][:3])
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
