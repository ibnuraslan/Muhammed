"""Live test: the v3 vault look-test scene animated (120 frames, 24 fps). The three clothed thieves walk out of the
vault carrying their bags: a planted-foot walk cycle (ported from antwerp_heist lib/human.pose_walk_planted to this
rig), with the stance foot pinned exactly every frame (root motion solved from the planted foot: no sliding). Bags
ride on the carrying hand. Slow camera push. Frames go to OUTDIR as PNGs.
    FRAMES=120 blender -b --python style_anim.py"""
import os, sys, math, runpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["NORENDER"] = "1"
os.environ.setdefault("ACCENT", "red")
for k, v in dict(EXPO="-2.6", RIM_E="1200", FILL_E="120", VAULT_E="350", ACC_E="300", FKEY_E="300", TGZ="2.0").items():
    os.environ.setdefault(k, v)
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "style_yellow.py"), run_name="scene")
import bpy
from mathutils import Vector, Matrix
import crew
E = os.environ.get
sc = bpy.context.scene
N = int(E("FRAMES", "120")); FPS = 24
sc.frame_start, sc.frame_end = 1, N; sc.render.fps = FPS
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
UPPER = [b for b in crew.SNEAK if b[0].startswith(("spine", "neck", "head"))]


def arm_of(pv):
    return [o for o in pv.children_recursive if o.type == 'ARMATURE'][0]


def pose_frame(arm, Rh, phase, stride, swing):
    """Reset, then the sneaking upper body + a planted walk (character axes: Rh @ X lateral)."""
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    Xc = Rh @ X; Yc = Rh @ Y
    for (b, ax, d) in UPPER:
        crew._rot(arm, b, Rh @ ax, d)
    for sd, ul, ll, ft, ua, la in (("L", "upperleg_l_074", "lowerleg_l_075", "foot_l_076", "upperarm_l_024", "lowerarm_l_025"),
                                   ("R", "upperleg_r_081", "lowerleg_r_082", "foot_r_083", "upperarm_r_049", "lowerarm_r_050")):
        u = (phase + (0.0 if sd == "L" else 0.5)) % 1.0
        if u < 0.5:
            hip = stride * (1.0 - 4.0 * u); knee = 14.0 + 4.0 * math.sin(math.pi * u * 2.0); foot = hip - knee
        else:
            s = (u - 0.5) / 0.5
            hip = -stride + 2.0 * stride * (0.5 - 0.5 * math.cos(math.pi * s))
            knee = 14.0 + 46.0 * math.sin(math.pi * min(1.0, s * 1.15)) ** 1.2
            foot = hip - knee * 0.55 + 12.0 * math.sin(math.pi * s)
        crew._rot(arm, ul, Xc, -hip - 8)          # thigh forward = -X (as in crew.SNEAK); slight crouch
        crew._rot(arm, ll, Xc, knee + 8)
        crew._rot(arm, ft, Xc, -(foot) * 0.6 - 4)
        if sd == "L":                              # free arm swings, out a little
            a = swing * math.sin(2 * math.pi * (u + 0.5) - math.pi / 2)
            crew._rot(arm, ua, Yc, 40); crew._rot(arm, ua, Xc, -a - 12); crew._rot(arm, la, Xc, -25)
        else:                                      # carrying arm hangs straight with the bag
            crew._rot(arm, ua, Yc, -38); crew._rot(arm, ua, Xc, -4); crew._rot(arm, la, Xc, -4)


def ankle(arm, side):
    return arm.matrix_world @ arm.pose.bones["foot_l_076" if side == "L" else "foot_r_083"].head


thieves = []
for i in range(3):
    pv = bpy.data.objects[f"thief{i}"]; arm = arm_of(pv)
    # out of the vault, toward the camera: start in the doorway / just inside, heading out
    hd = math.radians([-20, -27, -12][i]); pv.rotation_euler.z = hd; Rh = Matrix.Rotation(hd, 3, 'Z')
    fwd = Rh @ Vector((0, -1, 0))
    pv.location = Vector([(0.05, 1.05, 0.0), (-0.45, 1.9, 0.0), (0.45, 2.6, 0.0)][i])
    thieves.append(dict(pv=pv, arm=arm, Rh=Rh, fwd=fwd, ph0=[0.0, 0.33, 0.66][i], period=[34, 32, 36][i],
                        stride=[11.0, 12.0, 10.5][i], plant=None, side=None))
# bags: re-hang from the carrying (right) hand, parented to the hand bone so they travel with the walk
bags = [bpy.data.objects[f"bag{i}"] for i in range(3)]
for t, b in zip(thieves, bags):
    pose_frame(t["arm"], t["Rh"], t["ph0"], t["stride"], 14)
    bpy.context.view_layer.update()
    h = t["arm"].matrix_world @ t["arm"].pose.bones["hand_r_051"].head
    side = t["Rh"] @ Vector((-0.2, 0, 0))
    b.location = Vector((h.x, h.y, h.z - 0.55)) + side; b.rotation_euler = (0, 0, t["pv"].rotation_euler.z + math.pi / 2)
    bpy.context.view_layer.update(); mw = b.matrix_world.copy()
    b.parent = t["arm"]; b.parent_type = 'BONE'; b.parent_bone = "hand_r_051"; bpy.context.view_layer.update(); b.matrix_world = mw
# the accent spot follows the red bag
acc = bpy.data.objects.get("accent")
if acc:
    tc = acc.constraints.new('TRACK_TO'); tc.target = bags[0]; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
    cc = acc.constraints.new('COPY_LOCATION'); cc.target = bags[0]; cc.use_offset = True

for f in range(1, N + 1):
    sc.frame_set(f)
    for t in thieves:
        phase = t["ph0"] + (f - 1) / t["period"]
        pose_frame(t["arm"], t["Rh"], phase, t["stride"], 14)
        bpy.context.view_layer.update()
        uL = phase % 1.0
        side = "L" if uL < 0.5 else "R"
        if side != t["side"]:                    # a new stance foot: plant it where it is now
            t["side"] = side; t["plant"] = ankle(t["arm"], side)
        else:                                    # keep the stance foot pinned: move the root by its drift
            d = t["plant"] - ankle(t["arm"], side)
            t["pv"].location += Vector((d.x, d.y, d.z))
            bpy.context.view_layer.update()
        t["pv"].keyframe_insert("location", frame=f)
        for pb in t["arm"].pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=f)
            pb.keyframe_insert("location", frame=f)
# slow camera push (6% closer over the shot)
cam = sc.camera; tgt = Vector((0.0, -0.6, float(E("TGZ", "2.0"))))
p0 = cam.location.copy(); p1 = tgt + (p0 - tgt) * float(E("PUSH", "0.92"))
for f, p in ((1, p0), (N, p1)):
    cam.location = p; cam.keyframe_insert("location", frame=f)
for fc in (cam.animation_data.action.fcurves if hasattr(cam.animation_data.action, "fcurves") else []):
    for kp in fc.keyframe_points:
        kp.interpolation = 'SINE'
out = E("ANIM_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "anim", "f_####.png"))
os.makedirs(os.path.dirname(out), exist_ok=True); sc.render.filepath = out
if E("ONLY"):                                    # render single frames: ONLY=60
    for fr in E("ONLY").split(","):
        sc.frame_set(int(fr)); sc.render.filepath = out.replace("####", f"{int(fr):04d}")
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print("ANIM DONE")
