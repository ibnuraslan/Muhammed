"""v012 (client: shirtless behind frosted glass reads as naked): the shower ending is re-staged at a bathroom SINK. The man keeps
his T-shirt and jeans (import_clothes.py), the glass stall, shower fittings, water streaks and steam are removed, and a vanity
(cabinet, stone counter, basin, tap) stands in front of him at waist height, so the shot reads chest-up at a sink. His animation
(the nostril press, the sneeze, the brick into his palm) is unchanged. blender -b in.blend --python restage_sink.py -- out.blend"""
import bpy, sys, bmesh, math
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
HIDE = ("BA_GlassFront", "BA_GlassFrontTop", "BA_GlassPanel", "BA_GlassPanelTop", "BA_GlassRail", "BA_GlassRailF", "BA_ShowerArm", "BA_ShowerHead",
        "BA_ShowerPipe", "BA_ShowerTray", "BA_Niche", "BA_Bottle0", "BA_Bottle1", "BA_Bottle2", "BA_Duck", "FX_Steam")
n = 0
for o in bpy.data.objects:
    if o.name in HIDE or o.name.startswith("FX_Water"):
        for x in [o] + list(o.children_recursive):
            if x.animation_data: x.animation_data_clear()
            x.hide_render = True; x.hide_viewport = True; n += 1
sc.frame_set(1700); M = bpy.data.objects["Man"]; pel = (M.matrix_world @ M.pose.bones["pelvis.L"].head + M.matrix_world @ M.pose.bones["pelvis.R"].head) / 2
R = (M.matrix_world @ M.pose.bones["head"].matrix @ M.data.bones["head"].matrix_local.inverted()).to_3x3().normalized()
fw = R @ Vector((0, -1, 0)); fw.z = 0; fw.normalize(); yaw = math.atan2(fw.y, fw.x)   # he faces fw; the vanity stands in front of him
C = pel + fw * 0.33; C.z = 0; top = 0.88; DEP = 0.26
def place(o, along, side, z):      # along = toward him (-) / toward the camera (+) from the cabinet centre, side = across
    sd = Vector((-fw.y, fw.x, 0)); p = C + fw * along + sd * side; o.location = (p.x, p.y, z); o.rotation_euler = (0, 0, yaw)
def mat(name, col, rough, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1); p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal; return m
def box(name, size, loc, m, bevel=0.01):
    bm_ = bmesh.new(); bmesh.ops.create_cube(bm_, size=1.0); me = bpy.data.meshes.new(name); bm_.to_mesh(me); bm_.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.scale = size; o.location = loc; me.materials.append(m)
    if bevel: b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3
    return o
W = 0.95
cab = box("BA_VanityCabinet", (DEP, W, top - 0.02), (0, 0, 0), mat("M_Vanity", (0.93, 0.92, 0.89), 0.45)); place(cab, 0, 0, (top - 0.02) / 2)
ctr = box("BA_VanityTop", (DEP + 0.05, W + 0.06, 0.04), (0, 0, 0), mat("M_Counter", (0.36, 0.34, 0.33), 0.3)); place(ctr, 0.01, 0, top)
for i, dx in enumerate((-0.235, 0.235)):
    d = box("BA_VanityDoor%d" % i, (0.01, W / 2 - 0.03, top - 0.12), (0, 0, 0), mat("M_VanityDoor", (0.88, 0.87, 0.84), 0.4), 0.004); place(d, DEP / 2 + 0.002, dx, (top - 0.02) / 2)
    k = box("BA_VanityKnob%d" % i, (0.02, 0.012, 0.06), (0, 0, 0), mat("M_Chrome", (0.9, 0.9, 0.92), 0.12, 1.0), 0.003); place(k, DEP / 2 + 0.012, dx * 0.25, top - 0.18)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16)
bsn = bpy.context.active_object; bsn.name = "BA_Basin"; bsn.scale = (0.15, 0.22, 0.07); place(bsn, 0, 0, top + 0.025)
bsn.data.materials.append(mat("M_Basin", (0.97, 0.97, 0.97), 0.15))
inner = bsn.copy(); inner.data = bsn.data.copy(); sc.collection.objects.link(inner); inner.name = "BA_BasinBowl"
inner.scale = (0.125, 0.19, 0.06); place(inner, 0, 0, top + 0.03); inner.data.materials[0] = mat("M_BasinIn", (0.86, 0.88, 0.9), 0.1)
bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.16); tap = bpy.context.active_object; tap.name = "BA_Tap"; place(tap, -DEP / 2 + 0.03, 0, top + 0.1)
tap.data.materials.append(mat("M_Chrome2", (0.92, 0.92, 0.94), 0.1, 1.0))
bpy.ops.mesh.primitive_cylinder_add(radius=0.01, depth=0.11); sp = bpy.context.active_object; sp.name = "BA_TapSpout"
place(sp, -DEP / 2 + 0.08, 0, top + 0.17); sp.rotation_euler = (0, math.radians(90), yaw); sp.data.materials.append(tap.data.materials[0])
new = [o for o in bpy.data.objects if o.name.startswith(("BA_Vanity", "BA_Basin", "BA_Tap"))]
# only in the bathroom (from the cut into it on)
for o in new:
    for f, h in ((1, True), (1586, False)):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f); o.hide_viewport = h; o.keyframe_insert("hide_viewport", frame=f)
print("SINK hidden", n, "added", len(new), "centre", [round(x, 2) for x in C], "facing", [round(x, 2) for x in fw])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
