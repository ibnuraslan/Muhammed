"""B08 BatBite characters. MakeHuman's asset server (files.makehumancommunity.org) is down (502), so the MPFB humans
are appended from our own earlier packages (CC0 MakeHuman/MPFB assets), stripped of animation/control bones and rebuilt.
blender -b --factory-startup --python 01_chars.py -- out.blend"""
import bpy, sys
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]
B = "/home/user/Muhammed/blender/"
SRC = [(B + "ShoeBomber_v008/ShoeBomber_v008_60fps.blend", {"Bomber": "Singer", "Sleeper2": "HairDonor", "Officer": "Doctor"}),
       (B + "PopeShot_v012/PopeShot_v012_60fps.blend", {"Crowd0": "Fan1", "Crowd2": "Fan2", "Crowd4": "Fan3", "Crowd6": "Fan4"})]
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
CTRL = ("IK_", "Pole_")
for path, names in SRC:
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        want = set(names)
        dst.objects = [n for n in src.objects if n in want or ("." in n and n.split(".")[0] in want)]
    for o in dst.objects:
        if o is None: continue
        base = o.name.split(".")[0]
        if base not in names: continue
        bpy.context.scene.collection.objects.link(o)
        new = names[base]
        o.name = new if o.type == 'ARMATURE' else new + "." + o.name.split(".", 1)[1]
for o in bpy.data.objects:
    o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
    if o.type == 'ARMATURE':
        bpy.context.view_layer.objects.active = o
        for pb in o.pose.bones:
            for c in list(pb.constraints): pb.constraints.remove(c)
            pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in list(o.data.edit_bones):
            if eb.name.startswith(CTRL): o.data.edit_bones.remove(eb)
        bpy.ops.object.mode_set(mode='OBJECT')
        o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
        for c in list(o.constraints): o.constraints.remove(c)
    elif o.parent is None:
        pass
    for c in list(getattr(o, "constraints", [])):
        if o.type != 'ARMATURE': o.constraints.remove(c)
    o.hide_render = False; o.hide_viewport = False; o.hide_set(False)
# space them out
for i, n in enumerate(["Singer", "HairDonor", "Doctor", "Fan1", "Fan2", "Fan3", "Fan4"]):
    bpy.data.objects[n].location.x = i * 1.2
print("EYEFIX present:", any(n.name == "CorneaTransparentMix" for g in bpy.data.node_groups if g.name.startswith("EnhancedEye") for n in g.nodes),
      [g.name for g in bpy.data.node_groups if "Eye" in g.name])
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        print("CHAR", o.name, len(o.data.bones), [c.name for c in o.children], [b.name for b in o.data.bones if "jaw" in b.name or "eye" in b.name.lower() or "lid" in b.name][:12])
for o in bpy.data.objects:
    if o.type == 'MESH': print("MESH", o.name, [m.type for m in o.modifiers], len(o.data.vertices), o.data.shape_keys and len(o.data.shape_keys.key_blocks))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
