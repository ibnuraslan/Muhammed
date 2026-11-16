"""B17 PilotSuckedOut: base file. Opens NoPilotPlane_v011 (cockpit set, captain, first officer, sky/ground world), strips
cabin/passengers/animation, appends the plain-white 737 and the flight attendant from ShoeBomber_v008.
blender -b NoPilotPlane_v011/NoPilotPlane_v011_60fps.blend --python 01_base.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1:][0]
B = "/home/user/Muhammed/blender/"
D = bpy.data
def kill(o):
    if o and o.name in D.objects: D.objects.remove(o, do_unlink=True)
for cn in ("PASSENGERS", "SEATS", "MASKS", "BIRDS", "TOWNS"):
    c = D.collections.get(cn)
    if c:
        for o in list(c.all_objects): kill(o)
        D.collections.remove(c)
you = D.objects.get("YOU")
if you:
    for ch in list(you.children_recursive): kill(ch)
    kill(you)
for n in ("CABIN_SHELL", "CABIN_BACKWALL", "CABIN_FIXED", "SEAT_MODEL", "DOOR", "CUP", "SPILL", "DRIP_0", "DRIP_1", "DRIP_2",
          "DRIP_3", "WING_L", "WING_R", "L_alarm", "L_alarm_cabin", "L_cabin_0", "L_cabin_1", "L_cabin_2", "L_cabin_3",
          "L_cabin_4", "L_galley_door_fill", "L_door_fill", "WARN_L", "WARN_R", "CHECKLIST_SHEET", "PEN", "CLIPBOARD",
          "LOOK_1153", "LOOK_2959", "LOOK_546", "LOOK_951", "MUG_L", "MUG_R"):
    kill(D.objects.get(n))
for o in D.objects:
    if o.animation_data: o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys and o.data.shape_keys.animation_data:
        o.data.shape_keys.animation_data_clear()
for m in D.materials:
    if m.node_tree and m.node_tree.animation_data: m.node_tree.animation_data_clear()
if D.worlds and bpy.context.scene.world.node_tree.animation_data: bpy.context.scene.world.node_tree.animation_data_clear()
for l in D.lights:
    if l.animation_data: l.animation_data_clear()
sc = bpy.context.scene
sc.timeline_markers.clear()
for r in ("CAPT", "FO"):
    rig = D.objects[r]
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
# append from ShoeBomber: Airliner + Attendant
SB = B + "ShoeBomber_v008/ShoeBomber_v008_60fps.blend"
with bpy.data.libraries.load(SB) as (src, dst):
    dst.objects = [n for n in src.objects if n == "Airliner" or n == "Attendant" or n.startswith("Attendant.")]
for cn in ("PLANE", "ATTENDANT"):
    if cn not in D.collections: sc.collection.children.link(D.collections.new(cn))
for o in dst.objects:
    if o is None: continue
    (D.collections["PLANE"] if o.name == "Airliner" else D.collections["ATTENDANT"]).objects.link(o)
    if o.animation_data: o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys and o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
att = D.objects["Attendant"]
for pb in att.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
att.location = (0, -1.0, 0.12); att.rotation_euler = (0, 0, 0)
# orphan cleanup
for _ in range(3):
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
print("BASE objects", len(D.objects), "rigs", [o.name for o in D.objects if o.type == 'ARMATURE'])
print("CAPT", tuple(D.objects["CAPT"].location), tuple(D.objects["CAPT"].rotation_euler), "FO", tuple(D.objects["FO"].location))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
