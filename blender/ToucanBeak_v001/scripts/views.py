import bpy,sys
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]; views=eval(a[1])
sc=bpy.context.scene
cam=bpy.data.objects.get('CamTest') or bpy.data.objects.new('CamTest',bpy.data.cameras.new('CamTest'))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera=cam; cam.data.sensor_width=36
sc.render.resolution_x=270; sc.render.resolution_y=480; sc.cycles.samples=8; sc.render.use_motion_blur=False
sc.cycles.texture_limit_render='1024'
f0=sc.frame_current
for i,v in enumerate(views):
    loc,tg,lens=v[:3]; 
    if len(v)>3: sc.frame_set(v[3])
    cam.location=loc; cam.rotation_euler=(Vector(tg)-Vector(loc)).to_track_quat('-Z','Y').to_euler(); cam.data.lens=lens
    sc.render.filepath=f"{out}{i:02d}.jpg"; sc.render.image_settings.file_format='JPEG'; bpy.ops.render.render(write_still=True)
