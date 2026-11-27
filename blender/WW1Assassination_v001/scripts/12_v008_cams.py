# v008 (batch-2 standard): hard-cut shot cameras on the v007 VO timing (frames 1-1826).
# Exec'd by 12_v008.py after the scene fixes. Each shot: camera + aim, keyed every 3 frames, bound to a marker.
import bpy, math
from mathutils import Vector, Matrix
sc = bpy.context.scene; O = bpy.data.objects

def W(x, y, z):
    v = Vector((x, y, z)); return lambda: v.copy()
def C(x, y, z, car="Car1_Sway"):
    v = Vector((x, y, z)); return lambda: O[car].matrix_world @ v
def BN(rig, bone, off=(0, 0, 0), tail=0.0):
    o = Vector(off)
    def g():
        a = O[rig]; pb = a.pose.bones[bone]
        return a.matrix_world @ pb.head.lerp(pb.tail, tail) + o
    return g
def OB(name, off=(0, 0, 0)):
    o = Vector(off); return lambda: O[name].matrix_world.translation + o

def ease(u): return u * u * (3 - 2 * u)

# (name, f0, f1, cam_start, cam_end, aim_start, aim_end, lens_start, lens_end)
SHOTS = [
 ("S01_corner_approach",   1,   75, W(1.6, -1.2, 1.75), W(1.3, -0.7, 1.7), C(0, 0.3, 1.3), C(0, 0.3, 1.3), 30, 30),
 ("S02_turn_in",          76,  151, W(-0.5, 16.2, 1.9), W(-0.4, 15.4, 1.85), C(0, 0.6, 1.35), C(0, 0.6, 1.35), 34, 36),
 ("S03_princip_waits",   152,  250, W(1.95, 9.55, 1.62), W(2.0, 9.7, 1.6), BN("Gunman", "head", (0, 0, -0.18)), BN("Gunman", "head", (0, 0, -0.18)), 32, 38),
 ("S04_couple",          251,  341, C(-1.45, -1.35, 1.38), C(-1.35, -1.2, 1.36), C(0.0, 0.92, 1.5), C(0.0, 0.92, 1.5), 36, 40),
 ("S05_quay_conspirators", 342, 472, W(89.2, 4.0, 1.75), W(90.3, 5.15, 1.6), W(91.05, 6.8, 1.45), W(91.05, 6.8, 1.45), 30, 34),
 ("S06_nerveA_coat",     473,  560, W(91.35, 5.2, 1.6), W(91.3, 5.4, 1.58), BN("NerveA", "head", (0, 0, -0.2)), BN("NerveA", "head", (0, 0, -0.2)), 42, 46),
 ("S07_nerve_turns_away", 561,  612, W(89.4, 4.5, 1.75), W(89.6, 4.7, 1.75), W(91.4, 7.4, 1.4), W(91.9, 8.2, 1.35), 30, 30),
 ("S08_bomber_throws",   613,  664, W(83.5, 4.75, 1.65), W(83.4, 4.95, 1.65), BN("Bomber", "spine01", (0, 0, 0.2)), BN("Bomber", "spine01", (0, 0, 0.25)), 36, 38),
 ("S08b_roof_bounce",    665,  700, C(-1.3, 2.9, 2.1), C(-1.3, 2.9, 2.1), C(0.0, 1.35, 1.25), C(0.0, 1.8, 0.7), 30, 30),
 ("S09_bomb_bounces",    701,  776, W(81.8, -0.6, 0.95), W(81.6, -0.8, 1.0), W(83.6, 1.4, 0.25), W(84.6, 1.5, 0.6), 30, 30),
 ("S10_blast",           777,  850, W(79.6, -2.4, 1.7), W(79.3, -2.7, 1.75), W(84.0, 1.5, 0.9), W(84.0, 1.5, 1.4), 28, 26),
 ("S11_aftermath",       851,  910, W(78.6, -3.6, 2.6), W(78.2, -4.0, 2.9), W(84.3, 2.2, 1.2), W(84.3, 2.2, 1.4), 24, 24),
 ("S12_driver",          911,  990, C(1.35, -1.15, 1.62), C(1.3, -1.05, 1.62), C(0.2, 0.1, 1.62), C(0.2, 0.1, 1.62), 34, 36),
 ("S13_wrong_turn",      991, 1056, W(-1.4, 14.2, 3.3), W(-1.2, 13.8, 3.1), C(0, 0.2, 1.0), C(0, 0.2, 1.0), 28, 28),
 ("S14_assassin_waiting", 1057, 1140, W(-0.9, 14.8, 1.75), W(-0.8, 14.6, 1.72), C(-0.3, 0.5, 1.3), C(-0.3, 0.5, 1.3), 34, 36),
 ("S15_eyes",           1141, 1236, W(2.0, 9.65, 1.62), W(2.2, 9.95, 1.6), BN("Gunman", "head", (0, 0, -0.04)), BN("Gunman", "head", (0, 0, -0.04)), 45, 55),
 ("S16_two_shots",      1237, 1300, W(3.6, 8.2, 1.8), W(3.55, 8.3, 1.8), W(2.2, 10.8, 1.45), W(2.2, 10.8, 1.45), 24, 24),
 ("S17_couple_hit",     1301, 1432, C(1.55, -0.65, 1.78), C(1.5, -0.45, 1.85), C(0.0, 0.92, 1.3), C(0.0, 0.92, 1.25), 32, 32),
 ("S18_map_two",        1433, 1530, W(5, -80, 160), W(6, -66, 140), W(2, 26, 0), W(4, 28, 0), 30, 30),
 ("S19_map_allies",     1531, 1680, W(-15, -95, 230), W(0, -105, 268), W(8, 62, 0), W(10, 70, 0), 26, 26),
 ("S20_corner_end",     1681, 1826, W(-0.6, 14.0, 1.8), W(-2.6, 17.8, 6.2), W(1.3, 10.8, 1.2), W(1.3, 10.8, 1.0), 28, 28),
]

STEP = 3
# speed: skip mesh evaluation while baking (armatures still evaluate)
hidden = []
for o in O:
    if o.type == 'MESH' and not o.hide_viewport:
        o.hide_viewport = True; hidden.append(o)
sc.timeline_markers.clear()
for name, f0, f1, cs, ce, as_, ae, l0, l1 in SHOTS:
    cd = bpy.data.cameras.new("CAM_" + name); cd.clip_start = 0.05; cd.clip_end = 4000; cd.sensor_fit = 'AUTO'
    cd.dof.use_dof = False
    cam = bpy.data.objects.new("CAM_" + name, cd); sc.collection.objects.link(cam)
    aim = bpy.data.objects.new("AIM_" + name, None); sc.collection.objects.link(aim)
    tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
    frames = list(range(f0, f1 + 1, STEP))
    if frames[-1] != f1: frames.append(f1)
    for f in frames:
        sc.frame_set(f)
        u = ease((f - f0) / max(1, f1 - f0))
        cam.location = cs().lerp(ce(), u); aim.location = as_().lerp(ae(), u); cd.lens = l0 + (l1 - l0) * u
        cam.keyframe_insert("location", frame=f); aim.keyframe_insert("location", frame=f); cd.keyframe_insert("lens", frame=f)
    m = sc.timeline_markers.new(name, frame=f0); m.camera = cam
    print("SHOT", name, f0, f1)
for o in hidden: o.hide_viewport = False
sc.camera = O["CAM_" + SHOTS[0][0]]
# the old one-take camera is not used any more
for n in ("CAM_Film", "CAM_Film_Aim", "WhiteoutCard"):
    o = O.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)
print("CAMS_DONE", len(SHOTS))
