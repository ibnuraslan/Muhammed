"""Reuse finished MPFB characters (eye fix already applied) from BelugaRescue_v008 and CaveRescue_v010.
blender -b --factory-startup -P 02_people.py -- work/people.blend"""
import bpy, sys
OUT = sys.argv[-1]
SRC = {"../BelugaRescue_v008/BelugaRescue_v008_60fps.blend": ["Keeper","SpecA","SpecB","SpecC","SpecD","SpecE","SpecF","SpecG"],
       "../CaveRescue_v010/CaveRescue_v010_60fps.blend": ["Crowd1","Crowd2","Crowd3","Crowd4"]}
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
for path, rigs in SRC.items():
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        names = list(src.objects)
    want = [n for n in names if any(n == r or n.startswith(r + ".") or n.startswith(r + "_") for r in rigs)]
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = want
    for o in dst.objects:
        if o is None: continue
        bpy.context.scene.collection.objects.link(o)
for o in bpy.data.objects:
    if o.animation_data: o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys and o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
    if o.type == 'ARMATURE':
        extra = [b.name for b in o.data.bones if b.name.startswith(("IK", "Pole", "CTRL", "ctrl"))]
        cons = sorted({(c.type) for pb in o.pose.bones for c in pb.constraints})
        print("RIG", o.name, len(o.data.bones), "extra", extra[:12], "cons", cons, "kids", [c.name for c in o.children][:14])
        for pb in o.pose.bones:
            pb.location = (0,0,0); pb.rotation_quaternion = (1,0,0,0); pb.rotation_euler = (0,0,0); pb.scale = (1,1,1)
    if o.type == 'MESH' and o.parent is None: print("LOOSE", o.name)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
