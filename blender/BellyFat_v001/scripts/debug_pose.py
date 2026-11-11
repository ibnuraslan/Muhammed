"""debug: render the woman from a fixed side camera at given frames, store visible. -- out_dir frames"""
import sys, os, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; FR = [int(x) for x in a[1].split(",")]
sc = bpy.context.scene
cd = bpy.data.cameras.new("DBG"); c = bpy.data.objects.new("DBG", cd); sc.collection.objects.link(c); sc.camera = c
pos = Vector([float(x) for x in a[2].split(",")]) if len(a) > 2 else Vector((2.6, -1.2, 1.2))
tg = Vector([float(x) for x in a[3].split(",")]) if len(a) > 3 else Vector((0.0, 0.45, 1.0))
c.location = pos; d = tg - pos; c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); cd.lens = 30
sc.render.resolution_x, sc.render.resolution_y = 360, 640; sc.cycles.samples = 8
os.makedirs(OUT, exist_ok=True)
for act in bpy.data.actions:
    for lay in act.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == "hide_render": fc.mute = True
MS = set(o.name for o in bpy.data.collections["MACRO"].all_objects)
for o in sc.objects:
    o.hide_render = o.name in MS
for f in FR:
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUT, "p%04d.jpg" % f); bpy.ops.render.render(write_still=True)
