# Part 2 of 03_animate.py: the one continuous camera + rock blackout card for the scale moves.
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.lens = 24; cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.02; cam_d.clip_end = 400
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_d.dof.focus_object = aim
X0, D0 = V((CX, 0, 0)), V((DX, 0, 0))
def C(x, y, z): return V((CX + x, y, z))
def D(x, y, z): return V((DX + x, y, z))
SEGS = [
 [(1, V((7, -26, 12)), V((0, -8, 1.5)), 22), (70, V((3.5, -17, 4.5)), V((0, -7, 1.2)), 24), (130, V((-3.4, -11, 0.5)), V((-0.5, -4, 1.0)), 22),
  (190, V((0.6, -9.0, 1.55)), V((0, -2, 1.3)), 26), (250, V((0.4, -6.5, 1.5)), V((0.3, 1, 1.2)), 26), (300, V((0.3, -3.5, 1.6)), V((0.5, 4, 1.0)), 24),
  (335, V((0.6, -0.5, 1.5)), V((0, -8, 2.3)), 22), (370, V((1.1, 1.8, 1.3)), V((-0.3, -3, 1.0)), 22), (405, V((-0.9, 2.4, 0.8)), V((0.3, 6, 0.6)), 22),
  (450, V((-0.9, 1.4, 0.55)), V((0.6, 6, 0.5)), 22), (500, V((-0.8, 2.6, 0.6)), V((0.8, 7, 0.6)), 22), (540, V((-0.3, 4.4, 0.9)), V((2.2, 6.5, 0.5)), 24),
  (575, V((-1.8, 5.2, 1.0)), V((2.2, 7.0, 0.5)), 24), (582, V((-2.6, 5.3, 1.0)), V((2.2, 7.0, 0.5)), 24)],
 [(583, D(0.5, 2.0, 0.7), D(8, 2.4, 0.6), 24), (600, D(-1.2, 2.5, 0.9), D(5, 3, 0.8), 24), (640, D(-6, 6, 2.5), D(0, 7, 1.0), 24),
  (680, D(-22, 12, 6), D(0, 15, 3.5), 24), (727, D(-46, 19, 10), D(0, 19, 4.5), 24), (780, D(-20, 9, 3.5), D(0, 8, 0.4), 26),
  (840, D(-15, 17, 3.0), D(0, 16, 0.2), 28), (900, D(-14, 27, 3.2), D(0, 27.5, 0.0), 28), (960, D(-9, 34, 2.6), D(0, 36.5, 1.8), 28),
  (995, D(-2.0, 37.3, 2.1), D(1, 37.6, 2.0), 26), (1008, D(0.8, 37.6, 2.05), D(3, 37.6, 2.0), 26)],
 [(1009, C(-6.9, 3.2, 1.9), C(0, 1.8, 0.4), 24), (1035, C(-4.4, 3.0, 1.6), C(0.3, 2.0, 0.5), 26), (1060, C(-3.0, 0.2, 0.6), C(0.3, 1.6, 0.3), 26),
  (1090, C(-1.2, -0.9, -0.15), C(0.4, -2.0, -0.15), 28), (1130, C(0.55, -2.85, 0.35), C(0.4, 1.8, 0.3), 30), (1175, C(0.9, -2.6, 0.6), C(0.6, 2.2, 0.5), 30),
  (1205, C(0.4, -1.4, 0.2), C(0.2, -3.0, -0.9), 26), (1235, C(0.2, -2.5, -1.1), C(0, -6, -2.4), 24), (1280, C(0.4, -5.5, -2.0), C(0, -9, -2.8), 24),
  (1330, C(-0.3, -8.5, -2.6), C(-0.5, -10.5, -3.0), 28), (1390, C(0.5, -15.8, -3.4), C(0, -13, -3.1), 24), (1450, C(0.6, -18.5, -3.5), C(0, -16, -3.2), 24),
  (1490, C(0.5, -19.5, -3.6), C(0, -22, -4.0), 26), (1560, C(0.4, -20.2, -3.6), C(-0.2, -26, -4.3), 28), (1640, C(0.3, -20.8, -3.7), C(-0.6, -30, -4.6), 30),
  (1700, C(0.2, -21.4, -3.8), C(-0.8, -33, -4.8), 32), (1745, C(0.2, -16, -3.2), C(0, -8, -2.5), 24), (1790, C(0.1, -6, -2.2), C(0.2, -1.5, -0.6), 24),
  (1840, C(0.1, -2.3, -0.8), C(0.3, -0.4, 0.8), 24), (1880, C(0.1, -2.0, -0.12), C(0.3, -0.5, 0.8), 26), (1930, C(0.2, -1.9, 0.3), C(0.3, -0.9, 0.5), 30),
  (1990, C(0.3, -1.5, 0.5), C(0.3, -0.9, 0.48), 40), (2030, C(-1.5, -1.3, 1.8), C(0.6, 1.15, 0.5), 26), (2080, C(-1.6, 3.7, 1.9), C(0.6, 1.15, 0.5), 26),
  (2130, C(2.4, 3.6, 1.7), C(0.7, 1.15, 0.5), 26), (2180, C(1.5, -0.3, 0.95), C(0.93, 1.08, 0.57), 30), (2230, C(1.25, 0.1, 0.72), C(0.93, 1.08, 0.57), 38),
  (2290, C(1.1, 0.05, 0.85), C(0.78, 1.0, 0.72), 35), (2340, C(1.2, 0.0, 0.85), C(0.76, 1.0, 0.73), 38), (2375, C(1.05, 0.15, 0.8), C(0.76, 1.0, 0.73), 42),
  (2406, C(1.5, -0.5, 1.2), C(0.6, 0.9, 0.55), 28), (2440, C(1.3, -1.3, 0.1), C(0.3, -2.6, -0.6), 26), (2480, C(-1.2, -4.2, -1.9), C(0.1, -5.5, -2.4), 24),
  (2520, C(-1.0, -7.5, -2.5), C(0.1, -8.4, -2.8), 24), (2550, C(-1.6, -9.8, -2.6), C(0.1, -10.0, -3.0), 24), (2565, C(-3.4, -10.3, -2.6), C(0.1, -10.4, -3.0), 24)],
 [(2566, D(0.4, 22, 0.8), D(8, 22, 0.8), 24), (2588, D(-1.4, 23, 1.0), D(3, 23.5, 0.8), 24), (2620, D(-6, 26, 2.5), D(0, 28, 0.9), 26),
  (2660, D(-12, 18, 4.5), D(0, 15, 0.9), 26), (2700, D(-5, 4, 1.8), D(0, 2, 0.9), 26), (2716, D(-1.2, 0.8, 1.0), D(2, 0.4, 0.9), 26),
  (2726, D(1.0, 0.5, 0.95), D(4, 0.5, 0.9), 26)],
 [(2727, V((1.2, 9.0, 1.3)), V((0.3, 0, 1.4)), 26), (2760, V((0.6, 6.0, 1.5)), V((0, -3, 1.3)), 26), (2800, V((0.4, 1.0, 1.6)), V((0, -6, 1.2)), 24),
  (2840, V((-1.6, -4.0, 0.9)), V((0.2, -4.5, 0.9)), 26), (2880, V((-2.5, -9, 2.0)), V((0, -8, 1.0)), 24), (2929, V((1.0, -15, 5.5)), V((0, -9, 1.0)), 24),
  (3000, V((4, -25, 14)), V((1, -8, 4)), 24), (3090, V((6, -34, 24)), V((2, -6, 16)), 24)]]
for seg in SEGS:
    fc = catmull([(f, c) for f, c, a, l in seg]); fa = catmull([(f, a) for f, c, a, l in seg]); fl = catmull([(f, float(l)) for f, c, a, l in seg])
    f0, f1 = seg[0][0], seg[-1][0]
    for f in list(range(f0, f1 + 1, 3)) + [f1]:
        cam.location = fc(f); cam.keyframe_insert("location", frame=f)
        aim.location = fa(f); aim.keyframe_insert("location", frame=f)
        cam_d.lens = fl(f); cam_d.keyframe_insert("lens", frame=f)
JUMPS = {582, 1008, 2565, 2726}
stepped(cam, JUMPS); stepped(aim, JUMPS)
for layer in cam_d.animation_data.action.layers:
    for strip in layer.strips:
        for cb in strip.channelbags:
            for fcv in cb.fcurves:
                for kp in fcv.keyframe_points:
                    if int(round(kp.co.x)) in JUMPS: kp.interpolation = 'CONSTANT'
# rock blackout card in front of the lens: dark rock texture fading to black while the camera is inside the rock
bpy.ops.mesh.primitive_plane_add(size=1)
card = bpy.context.active_object; card.name = "CAM_RockWipe"; card.parent = cam; card.location = (0, 0, -0.03); card.scale = (0.2, 0.2, 1)
card.visible_shadow = False
mw = bpy.data.materials.new("M_RockWipe"); mw.use_nodes = True
wn_, wl_ = mw.node_tree.nodes, mw.node_tree.links; wn_.clear()
wo_ = wn_.new('ShaderNodeOutputMaterial'); we = wn_.new('ShaderNodeEmission'); we.inputs['Color'].default_value = (0, 0, 0, 1); we.inputs['Strength'].default_value = 0
wtr = wn_.new('ShaderNodeBsdfTransparent'); wmx = wn_.new('ShaderNodeMixShader'); wv = wn_.new('ShaderNodeValue'); wv.name = "Wipe"
wl_.new(wv.outputs[0], wmx.inputs['Fac']); wl_.new(wtr.outputs[0], wmx.inputs[1]); wl_.new(we.outputs[0], wmx.inputs[2]); wl_.new(wmx.outputs[0], wo_.inputs['Surface'])
card.data.materials.append(mw)
WIPES = [(566, 576, 590, 600), (998, 1005, 1022, 1034), (2540, 2550, 2586, 2596), (2708, 2718, 2730, 2742)]
wv.outputs[0].default_value = 0.0; wv.outputs[0].keyframe_insert("default_value", frame=1)
for a, b, c, d in WIPES:
    for f, v in ((a, 0.0), (b, 1.0), (c, 1.0), (d, 0.0)):
        wv.outputs[0].default_value = v; wv.outputs[0].keyframe_insert("default_value", frame=f)
# soft fill that travels with the camera (a "bounce" from the torches), keyed per set
fl_o = bpy.data.objects.new("CAM_Fill", bpy.data.lights.new("CAM_Fill", 'AREA')); sc.collection.objects.link(fl_o)
fl_o.data.size = 1.5; fl_o.data.color = (0.9, 0.92, 1.0); fl_o.parent = cam; fl_o.location = (0.3, 0.5, 0.2)
fl_o.visible_glossy = False; fl_o.visible_volume_scatter = False
for f, e in ((1, 0), (280, 0), (330, 40), (582, 40), (583, 0), (1008, 0), (1009, 30), (1200, 30), (1215, 25), (1820, 25), (1850, 30),
             (2420, 30), (2440, 25), (2565, 25), (2566, 0), (2726, 0), (2727, 20), (2810, 0), (3090, 0)):
    fl_o.data.energy = e; fl_o.data.keyframe_insert("energy", frame=f)
print("CAMERA_OK")
