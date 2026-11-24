"""v014 base: open the v013 package for its MODELS only (room, monkey meshes, surgeon MPFB body), freeze every
animated value at frame 1, delete all old animation, the extra people, the gowns and the old stitches.
blender -b v013.blend --python 01_base.py -- base.blend"""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
sc.frame_set(1)
def fcs(ad):
    if not ad or not ad.action: return []
    a = ad.action
    try: return list(a.fcurves)
    except Exception: return [fc for l in a.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
# freeze material node values at frame 1 (fades visible, x-ray off, void off)
for m in bpy.data.materials:
    nt = m.node_tree
    if nt and nt.animation_data:
        vals = []
        for fc in fcs(nt.animation_data):
            vals.append((fc.data_path, fc.array_index, fc.evaluate(1)))
        nt.animation_data_clear()
        for dp, ix, v in vals:
            try:
                prop = nt.path_resolve(dp)
                if hasattr(prop, "__len__"): prop[ix] = v
                else:
                    base, attr = dp.rsplit(".", 1); setattr(nt.path_resolve(base), attr, v)
            except Exception as e: print("FREEZE FAIL", m.name, dp, e)
for k in ("XRay", "VoidOn"):
    for m in bpy.data.materials:
        if m.node_tree and k in m.node_tree.nodes: m.node_tree.nodes[k].outputs[0].default_value = 0.0
for m in bpy.data.materials:
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.name.startswith("Fade_"): n.outputs[0].default_value = 1.0
# objects: freeze transforms/visibility at frame 1 then clear
DROP_PREFIX = ("Nurse", "Anaes.", "Anaes_Cap", "Anaes_Gloves", "Anaes_Gown", "Anaes_GownTop", "Anaes_Mask", "Surgeon_Gown",
               "Stitch_", "Thread", "Dust_", "Chair", "Forceps", "Needle")
DROP_EXACT = {"Anaes", "Dust_Root", "Surgeon_GownTop", "Surgeon_Gown"}
for o in list(bpy.data.objects):
    if o.name in DROP_EXACT or (o.name.startswith(DROP_PREFIX) and o.name != "NeedleHolder"):
        if o.name in ("NeedleHolderRing1", "NeedleHolderRing-1"): continue
        bpy.data.objects.remove(o, do_unlink=True)
sc.frame_set(1)
for o in bpy.data.objects:
    if o.animation_data:
        mw = o.matrix_world.copy(); hv, hr = o.hide_viewport, o.hide_render
        o.animation_data_clear()
        if o.type != 'ARMATURE':
            o.matrix_world = mw
        o.hide_viewport, o.hide_render = hv, hr
    if o.type == 'MESH' and o.data.shape_keys and o.data.shape_keys.animation_data:
        o.data.shape_keys.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks[1:]: kb.value = 0.0
    for md in getattr(o, "modifiers", []):
        if md.type == 'MASK' and md.name == "DrapeHide": md.show_render = md.show_viewport = True
sc.animation_data_clear()
sc.view_settings.exposure = 0.0
# reset surgeon pose
r = bpy.data.objects["Surgeon"]
for pb in r.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
for a in list(bpy.data.actions):
    if a.users == 0: bpy.data.actions.remove(a)
bpy.ops.outliner.orphans_purge(do_recursive=True)
print("OBJECTS", len(bpy.data.objects))
print("KEEP", sorted(o.name for o in bpy.data.objects if not o.name.startswith(("Bottle", "Box_", "Jar_", "ClockTick", "RadFin", "CeilPanel"))))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
