import bpy, math
from mathutils import Vector
sc=bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples=8; sc.render.use_motion_blur=False; sc.render.image_settings.file_format='JPEG'
cd=bpy.data.cameras.new("cu"); cam=bpy.data.objects.new("cu",cd); sc.collection.objects.link(cam); sc.camera=cam; cd.lens=28; cd.clip_start=0.01; cd.dof.use_dof=False
SHOTS=[(60,"Woman","R"),(170,"Shover","L"),(330,"Woman","L"),(445,"Woman","R"),(628,"Woman","L"),(805,"Woman","L"),(1000,"Woman","L"),(1135,"Woman","L"),(1216,"Woman","L"),(1336,"Woman","L"),(1356,"Woman","R"),(1700,"Woman","L"),(1990,"Woman","L"),(2250,"Woman","L")]
dirs=[]
for el in (20, 40, 0, 60):
    for az in range(0, 360, 30):
        a=math.radians(az); e=math.radians(el); dirs.append(Vector((math.cos(a)*math.cos(e), math.sin(a)*math.cos(e), math.sin(e))))
for i,(f,n,s) in enumerate(SHOTS):
    sc.frame_set(f); R=bpy.data.objects[n]; P=R.pose.bones
    W=(R.matrix_world@P["wrist."+s].head).lerp(R.matrix_world@P["finger3-1."+s].head,0.7)
    inside = -0.75<W.x<0.75 and -0.6<W.y<0.6
    dg=bpy.context.evaluated_depsgraph_get(); best=None
    for dist in (0.40, 0.32, 0.25):
        for d in dirs:
            c=W+d*dist
            if inside and not (-0.68<c.x<0.68 and -0.54<c.y<0.54 and c.z<2.38): continue
            v=W-c; hit,loc,nr,idx,ob,M=sc.ray_cast(dg,c,v.normalized(),distance=v.length+0.05)
            if hit and ob.name.startswith(n) and (loc-W).length<0.08:
                best=c; break
        if best: break
    if best is None: best=W+Vector((0.3,-0.3,0.15)); print("NOVIEW",f)
    cam.location=best; cam.rotation_euler=(W-best).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'/tmp/claude-0/s/hcu_{i:02d}.jpg'; bpy.ops.render.render(write_still=True)
