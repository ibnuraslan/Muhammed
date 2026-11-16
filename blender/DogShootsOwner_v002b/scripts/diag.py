import bpy, sys
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:]; out=a[0]; f=int(a[1]); loc=Vector(eval(a[2])); tgt=Vector(eval(a[3])); hide=a[4].split(",") if len(a)>4 else []
sc=bpy.context.scene
for o in bpy.data.objects:
    if any(o.name.startswith(h) for h in hide if h): o.hide_render=True
cd=bpy.data.cameras.new("dg"); cd.lens=24; c=bpy.data.objects.new("dg",cd); sc.collection.objects.link(c)
c.location=loc; c.rotation_euler=(tgt-loc).to_track_quat('-Z','Y').to_euler()
sc.frame_set(f); sc.camera=c
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
r=sc.render; r.resolution_x=480; r.resolution_y=480; sc.cycles.samples=6; r.filepath=out; bpy.ops.render.render(write_still=True)
