"""One camera per shot (hard cuts via timeline markers), keyed start->end on the master timeline; level horizon (Track-free
explicit rotations from look-at with world up), no DOF (everything sharp), small camera-side catchlight on close-ups.
blender -b anim.blend --python 06_cams.py -- cams.blend"""
import bpy, sys, math
from mathutils import Vector as V
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
HX = 60.0
c = bpy.data.collections.new("Cameras"); sc.collection.children.link(c)
def bite_at(f, n="Singer"):
    """frame centre for the bite: in front of the mouth and a little low, so the bat and both hands are in frame"""
    sc.frame_set(f); r = bpy.data.objects[n]; M = r.matrix_world @ r.pose.bones["head"].matrix
    R0 = r.data.bones["head"].matrix_local.to_3x3().inverted(); fwd = (M.to_3x3() @ (R0 @ V((0, -1, 0)))).normalized()
    return M.translation + fwd * 0.10 + V((0, 0, -0.06))
def head_at(f, n="Singer"):
    sc.frame_set(f); r = bpy.data.objects[n]; return r.matrix_world @ r.pose.bones["head"].head + V((0, 0, 0.05))
# (name, f0, f1, cam0, cam1, tgt0, tgt1, lens, closeup)
SH = [
 ("S01_crowd_bat",    1,   80, (-0.10, -5.9, 0.30), (-0.08, -5.6, 0.35), (0.0, -0.5, 1.75), (0.0, -0.5, 1.65), 24, False),
 ("S02_bat_lands",   80,  150, (-0.45, 2.4, 2.7), (-0.35, 2.2, 2.6), (0.35, -1.6, 0.3), (0.35, -1.6, 0.25), 24, False),
 ("S03_notices",    150,  300, (1.05, -2.75, 1.15), (0.95, -2.45, 1.20), (0.05, -0.2, 1.25), (0.05, -0.2, 1.20), 30, False),
 ("S04_steps",      300,  410, (0.45, -5.40, 0.85), (0.45, -5.30, 0.85), (0.35, -0.25, 1.05), (0.50, -0.25, 0.95), 42, False),
 ("S05_grabs",      410,  470, (0.85, -2.30, 0.50), (0.80, -2.15, 0.50), (0.48, -0.40, 0.55), (0.48, -0.40, 0.55), 28, False),
 ("S06_rises",      470,  620, (1.55, -2.25, 1.35), (1.35, -1.85, 1.45), (0.55, -0.35, 1.15), (0.55, -0.35, 1.35), 38, False),
 ("S07_to_mouth",   620,  700, (1.30, -1.20, 1.62), (1.18, -1.05, 1.62), "HEAD", "HEAD", 55, True),
 ("S08_bite",       700,  860, (1.44, -0.60, 1.63), (1.40, -0.58, 1.63), "BITE", "BITE", 45, True),
 ("S09_bite_side",  860,  996, (1.28, -0.52, 1.62), (1.24, -0.50, 1.62), "BITE", "BITE", 55, True),
 ("S10_shock",      996, 1100, (0.32, -1.50, 1.62), (0.36, -1.30, 1.62), "HEAD", "HEAD", 60, True),
 ("S11_stares",    1100, 1280, (1.35, -1.65, 1.50), (1.25, -1.50, 1.48), (0.55, -0.40, 1.35), (0.55, -0.40, 1.35), 35, False),
 ("S12_drops",     1280, 1380, (0.45, -5.40, 0.85), (0.45, -5.30, 0.85), (0.65, -0.25, 1.05), (0.65, -0.25, 1.00), 42, False),
 ("S13_bends",     1380, 1600, (1.7, -2.5, 0.60), (1.55, -2.2, 0.62), (0.55, -0.2, 0.95), (0.55, -0.2, 0.92), 28, False),
 ("S14_hospital",  1600, 1800, (HX + 0.95, -0.15, 1.72), (HX + 0.86, -0.02, 1.70), (HX - 0.32, 1.02, 1.38), (HX - 0.30, 1.04, 1.40), 30, False),
 ("S15_mask_cu",   1800, 2100, (HX + 0.42, 0.25, 1.60), (HX + 0.30, 0.55, 1.55), "HEAD", "HEAD", 50, True),
]
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for name, f0, f1, c0, c1, t0, t1, lens, cu in SH:
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.05; cd.clip_end = 6000; cd.dof.use_dof = False
    cam = bpy.data.objects.new(name, cd); c.objects.link(cam); cam.rotation_mode = 'XYZ'
    keys = [(f0, V(c0), t0), (f1, V(c1), t1)]
    for f, p, t in keys:
        tgt = head_at(f) if t == "HEAD" else (bite_at(f) if t == "BITE" else V(t))
        cam.location = p; cam.rotation_euler = (tgt - p).to_track_quat('-Z', 'Y').to_euler()
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    if cu:   # mid key keeps the head framed while it moves
        fm = (f0 + f1) // 2; tgt = bite_at(fm) if t0 == "BITE" else head_at(fm); p = V(c0).lerp(V(c1), 0.5)
        cam.location = p; cam.rotation_euler = (tgt - p).to_track_quat('-Z', 'Y').to_euler()
        cam.keyframe_insert("location", frame=fm); cam.keyframe_insert("rotation_euler", frame=fm)
        L = bpy.data.objects.new(name + "_catch", bpy.data.lights.new(name + "_catch", 'POINT')); L.data.energy = 4.0; L.data.shadow_soft_size = 0.03
        L.parent = cam; L.location = (0.12, 0.10, 0.0); c.objects.link(L)
        L.data.use_shadow = False
    mk = sc.timeline_markers.new(name, frame=f0); mk.camera = cam
    print("CAM", name, f0, f1)
sc.camera = bpy.data.objects[SH[0][0]]
sc.frame_start, sc.frame_end = 1, 2100
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
