"""WeepingStatue cast. The MakeHuman asset server is unreachable from the cloud, so the cast reuses MPFB characters
already built in our own delivered films (PopeShot_v012, Tsunami2004_v012): appended, animation/IK/constraints stripped,
pose cleared, renamed and re-tinted. make_human_ctrl() re-rigs them in the animate step.
blender -b --factory-startup --python 01_chars.py -- <repo_blender_dir> <out.blend>"""
import sys, os, bpy
A = sys.argv[sys.argv.index("--") + 1:]
BL, OUT = A[0], A[1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
SRC = {"PopeShot_v012": {"AideA": "Investigator", "AideB": "CrowdM1", "Crowd0": "CrowdM2", "Crowd2": "CrowdM3", "Crowd4": "CrowdM4",
                         "Crowd6": "CrowdM5", "Crowd1": "CrowdW1", "Crowd3": "CrowdW2", "Crowd5": "CrowdW3", "Crowd7": "CrowdW4"},
       "Tsunami2004_v012": {"LocalW": "Woman", "OldM": "Caretaker", "LocalM": "CrowdM6", "Fisher": "CrowdM7"}}
for film, cast in SRC.items():
    path = os.path.join(BL, film, film + "_60fps.blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in cast or n.split(".", 1)[0] in cast and "." in n]
    for o in dst.objects:
        if o is None: continue
        bpy.context.scene.collection.objects.link(o)
    for old, new in cast.items():
        rig = bpy.data.objects[old]
        kids = [c for c in bpy.data.objects if c.parent == rig]
        rig.name = new; rig.data.name = new
        for c in kids:
            c.name = new + "." + c.name.split(".", 1)[1] if "." in c.name else new + "." + c.name
            c.animation_data_clear()
            if c.type == 'MESH' and c.data.shape_keys: c.data.shape_keys.animation_data_clear()
            for m in c.modifiers:
                if m.type == 'ARMATURE': m.object = rig
            c.hide_render = c.hide_viewport = False
            c.constraints.clear() if c.constraints else None
        # anything else parented under the rig that is not a body part (props, helmets) goes
        for c in kids:
            if c.type != 'MESH' or c.find_armature() != rig:
                if not any(k in c.name for k in ("body", "eyebrow", "eyelash", "high-poly", "low-poly", "teeth", "tongue")):
                    print("DROP", c.name); bpy.data.objects.remove(c, do_unlink=True)
        rig.animation_data_clear(); rig.data.animation_data_clear() if rig.data.animation_data else None
        rig.constraints.clear(); rig.parent = None
        rig.hide_render = rig.hide_viewport = False
        bpy.context.view_layer.objects.active = rig
        for o in bpy.context.selected_objects: o.select_set(False)
        rig.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        for b in list(rig.data.edit_bones):
            if b.name.startswith(("IK_", "Pole_")): rig.data.edit_bones.remove(b)
        bpy.ops.object.mode_set(mode='POSE')
        for pb in rig.pose.bones:
            for c in list(pb.constraints): pb.constraints.remove(c)
            pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
        bpy.ops.object.mode_set(mode='OBJECT')
        rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
# keep only rigs + their meshes; remove orphans pulled in (props, cameras)
keep = set()
for o in bpy.data.objects:
    if o.type == 'ARMATURE': keep.add(o.name); keep.update(c.name for c in o.children_recursive)
for o in list(bpy.data.objects):
    if o.name not in keep: bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.outliner.orphans_purge(do_recursive=True)
x = 0.0
for o in sorted(bpy.data.objects, key=lambda o: o.name):
    if o.type == 'ARMATURE':
        o.location.x = x; x += 0.8
        print("CHAR", o.name, sorted(c.name.split(".", 1)[1] for c in o.children), tuple(round(d, 2) for d in o.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
