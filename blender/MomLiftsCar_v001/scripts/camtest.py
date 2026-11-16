"""blender -b file --python camtest.py -- outprefix json_list_of_[name,[x,y,z],[tx,ty,tz],lens]"""
import bpy, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; pre = a[0]; shots = json.loads(a[1])
sc = bpy.context.scene
for m_ in list(sc.timeline_markers): sc.timeline_markers.remove(m_)
cam = bpy.data.objects.new("TestCam", bpy.data.cameras.new("TestCam")); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 540, 960; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.image_settings.file_format = 'JPEG'
if len(a) > 2: sc.frame_set(int(a[2]))
for nm, p, t, lens in shots:
    cam.location = p; d = Vector(t) - Vector(p); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
    cam.data.clip_start = 0.02
    sc.render.filepath = f"{pre}_{nm}.jpg"; bpy.ops.render.render(write_still=True)
