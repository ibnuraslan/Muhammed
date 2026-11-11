# blender -b x.blend --python view.py -- out.jpg frame "cx,cy,cz" "tx,ty,tz" lens [w h]
import bpy, sys
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:]
sc=bpy.context.scene
sc.frame_set(int(a[1]))
c=Vector(map(float,a[2].split(","))); t=Vector(map(float,a[3].split(",")))
cam=bpy.data.objects.get("VIEWCAM") or bpy.data.objects.new("VIEWCAM",bpy.data.cameras.new("VIEWCAM"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
cam.location=c; cam.rotation_euler=(t-c).to_track_quat('-Z','Y').to_euler(); cam.data.lens=float(a[4]); cam.data.clip_start=0.005
sc.camera=cam
W=int(a[5]) if len(a)>5 else 360; H=int(a[6]) if len(a)>6 else 640
sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100
sc.cycles.samples=8; sc.render.use_motion_blur=False; sc.cycles.texture_limit_render='1024'
sc.render.image_settings.file_format='JPEG'; sc.render.filepath=a[0]
bpy.ops.render.render(write_still=True)
