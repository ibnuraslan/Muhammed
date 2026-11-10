# Part 3 of 03_animate.py: one continuous camera shot (exec'd in the same namespace).
cam_d = bpy.data.cameras.new("CAM_Main")
cam_d.lens = 50
cam_d.sensor_fit = 'AUTO'
cam_d.sensor_width = 36
cam_d.clip_start = 0.05
cam_d.dof.use_dof = True
cam_d.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new("CAM_Main", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
aim = bpy.data.objects.new("CAM_Aim", None)
aim.empty_display_type = 'SPHERE'; aim.empty_display_size = 0.08
sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO')
tt.target = aim
tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_d.dof.focus_object = aim

CAM_AZ = R_(-64)                          # from the character's forward toward its right
def cam_pos(dist, h, cx=-0.05, cy=0.22):
    return Vector((cx + dist * math.sin(CAM_AZ), cy - dist * math.cos(CAM_AZ), h))
# aim: follows the walk, settles between body and bottle, lifts for the drink
AIM = [(1, (0.0, 0.78, 0.92)), (60, (-0.02, 0.50, 0.90)), (120, (-0.06, 0.10, 0.86)),
       (240, (-0.09, -0.10, 0.74)), (300, (-0.09, -0.06, 0.80)), (400, (-0.06, 0.12, 0.98)),
       (470, (-0.06, 0.14, 1.02)), (540, (-0.04, 0.12, 0.95)), (600, (-0.04, 0.12, 0.95))]
POS = [(1, (3.85, 1.25)), (120, (3.75, 1.2)), (240, (3.65, 1.12)), (430, (3.45, 1.24)),
       (600, (3.5, 1.22))]
fa = {i: pchip([(f, v[i]) for f, v in AIM]) for i in range(3)}
fp = {i: pchip([(f, v[i]) for f, v in POS]) for i in range(2)}
for f in sorted(set([k for k, _ in AIM] + [k for k, _ in POS])):
    aim.location = (fa[0](f), fa[1](f), fa[2](f))
    aim.keyframe_insert("location", frame=f)
    cam.location = cam_pos(fp[0](f), fp[1](f))
    cam.keyframe_insert("location", frame=f)
print("CAMERA_DONE")
