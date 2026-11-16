"""family photo texture for S26: mother + girl standing together on a soft blue backdrop (rendered from our own characters).
blender -b /tmp/claude-0/kh/work/chars.blend --python 05_photo.py -- /tmp/claude-0/kh/work/family_photo.png"""
import bpy, sys, math
from mathutils import Vector
sc = bpy.context.scene; out = sys.argv[sys.argv.index("--") + 1]
for o in bpy.data.objects:
    if o.type == 'ARMATURE' and o.name not in ("Kid", "Mom"):
        for c in o.children: c.hide_render = True
K = bpy.data.objects["Kid"]; M = bpy.data.objects["Mom"]
K.location = (0.2, -0.25, 0.42); M.location = (-0.17, 0.05, 0)   # heads-and-shoulders portrait (the girl stands on a step out of frame)
for r, ang in ((K, 0), (M, 0)):
    for s in "LR":   # arms down a little from the A-pose
        pb = r.pose.bones["upperarm01." + s]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, math.radians(-50 if s == "L" else 50))
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 1.2, 2), rotation=(math.radians(90), 0, 0))
bd = bpy.context.object; m = bpy.data.materials.new("bd"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.45, 0.65, 0.9, 1); bd.data.materials.append(m)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -2.3, 1.5); cam.rotation_euler = (Vector((0, 0, 1.47)) - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 50
l = bpy.data.objects.new("s", bpy.data.lights.new("s", "AREA")); l.data.energy = 300; l.data.size = 3; sc.collection.objects.link(l); l.location = (1, -3, 3)
l.rotation_euler = (Vector((0, 0, 1)) - l.location).to_track_quat('-Z', 'Y').to_euler()
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.7, 0.75, 0.8, 1)
sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.render.resolution_x = 600; sc.render.resolution_y = 450
sc.view_settings.view_transform = 'AgX'; sc.render.filepath = out; bpy.ops.render.render(write_still=True)
