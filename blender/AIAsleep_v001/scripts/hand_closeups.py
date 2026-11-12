import bpy, sys, os
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:]; outd=a[0]; frames=[int(x) for x in a[1:]]
sc=bpy.context.scene; O=bpy.data.objects; rig=O["Driver"]
c=sc.camera; c.constraints[0].mute=True; c.animation_data_clear(); c.data.animation_data_clear(); c.data.lens=28; c.data.dof.use_dof=False
sc.render.resolution_x,sc.render.resolution_y=270,480; sc.cycles.samples=8; sc.render.image_settings.file_format="JPEG"; sc.render.use_compositing=False
os.makedirs(outd,exist_ok=True); i=0
for f in frames:
    sc.frame_set(f)
    for s in "LR":
        h=rig.matrix_world@rig.pose.bones["finger3-1."+s].head
        sx=1 if s=="L" else -1
        for off in (Vector((0.04*sx,0.24,0.20)), Vector((0.24*sx,-0.06,0.12))):
            c.location=h+off; c.rotation_euler=(h-c.location).to_track_quat('-Z','Y').to_euler()
            sc.render.filepath=os.path.join(outd,"s%04d.jpg"%i); bpy.ops.render.render(write_still=True); i+=1
