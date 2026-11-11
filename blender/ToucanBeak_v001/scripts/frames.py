import bpy,sys,os
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]; frames=[int(x) for x in a[1].split(',')]
sc=bpy.context.scene; os.makedirs(out,exist_ok=True)
sc.render.resolution_x=270; sc.render.resolution_y=480; sc.cycles.samples=8; sc.render.use_motion_blur=False; sc.cycles.texture_limit_render='1024'
sc.render.image_settings.file_format='JPEG'
for i,f in enumerate(frames):
    sc.frame_set(f); sc.render.filepath=f"{out}/f{i:02d}_{f:04d}.jpg"; bpy.ops.render.render(write_still=True)
