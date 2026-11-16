"""Render the funeral portrait (man + croc together, plain painting, no text) from the film itself.
blender -b work/film.blend -P portrait.py -- assets/portrait.png"""
import bpy, sys, json, os
from mathutils import Vector
out = sys.argv[-1]; sc = bpy.context.scene
shots = {s["name"].split("_")[0]: s for s in json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shots.json")))}
bpy.data.objects["PortraitFrame"].hide_render = True
s = shots["S13"]; f = s["f1"] - 10; sc.frame_set(f)
cam = bpy.data.objects.new("PCam", bpy.data.cameras.new("PCam")); sc.collection.objects.link(cam); sc.camera = cam
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
man = bpy.data.objects["Keeper"]; head = man.matrix_world @ man.pose.bones["head"].head
croc = bpy.data.objects["Croc"]; ch = croc.matrix_world @ croc.pose.bones["head"].head
tgt = (head + ch) / 2 + Vector((0, 0, 0.1))
import math
yaw = math.radians(225); fw = Vector((math.sin(yaw), -math.cos(yaw), 0))   # the man's facing (S13): camera in front, the house behind him
cam.location = tgt + fw * 2.6 + Vector((0, 0, 0.45)); cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 40
sc.render.resolution_x, sc.render.resolution_y = 600, 760; sc.cycles.samples = 24; sc.render.engine = 'CYCLES'
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = out; bpy.ops.render.render(write_still=True)

