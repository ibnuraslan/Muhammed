import bpy, json, sys
sc=bpy.context.scene; out=[]
for f in range(1,1711,2):
    sc.frame_set(f); c=bpy.data.objects["CAM_Film"].matrix_world.translation; a=bpy.data.objects["CAM_Film_Aim"].matrix_world.translation
    out.append([f, list(c), list(a), bpy.data.cameras["CAM_Film"].lens])
json.dump(out, open(sys.argv[-1],"w"))
