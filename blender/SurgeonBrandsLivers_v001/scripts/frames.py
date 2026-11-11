# blender -b film.blend --python frames.py -- outdir f1 f2 ...  (film camera, 270x480, 8 spp)
import bpy, sys, os
a=sys.argv[sys.argv.index("--")+1:]; out=a[0]; os.makedirs(out,exist_ok=True)
sc=bpy.context.scene; sc.render.resolution_x,sc.render.resolution_y=270,480; sc.render.resolution_percentage=100
sc.cycles.samples=8; sc.render.use_motion_blur=False; sc.cycles.texture_limit_render='1024'; sc.render.image_settings.file_format='JPEG'
for f in a[1:]:
    sc.frame_set(int(f)); sc.render.filepath=os.path.join(out,"f%04d.jpg"%int(f)); bpy.ops.render.render(write_still=True)
