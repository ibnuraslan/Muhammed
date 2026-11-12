"""Close-up pass of every hand action (270x480). blender -b film.blend --python hand_closeups.py -- <out_prefix>"""
import sys, bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'JPEG'
cd = bpy.data.cameras.new("HandCheck"); cd.lens = 35; cd.clip_start = 0.01; cam = bpy.data.objects.new("HandCheck", cd); sc.collection.objects.link(cam); sc.camera = cam
for o in O:
    if o.name == "WipeCard": o.hide_render = True
SHOTS = [(60, "Bomber", "wrist.R", (0.35, 0.25, 0.25)), (60, "Bomber", "wrist.L", (0.35, 0.3, 0.2)), (492, "Attendant", "wrist.R", (0.3, -0.3, 0.3)),
         (600, "PaxA", "wrist.L", (0.3, 0.3, 0.4)), (600, "PaxB", "wrist.R", (0.35, 0.2, 0.35)), (640, "Attendant", "wrist.R", (0.35, 0.2, 0.3)),
         (712, "Steward", "wrist.R", (0.1, -0.4, 0.3)), (880, "Attendant", "wrist.L", (-0.35, 0.3, 0.3)), (960, "Attendant", "wrist.R", (0.3, 0.45, 0.1)),
         (1478, "Traveller", "wrist.R", (0.4, -0.3, 0.2)), (1515, "Traveller", "wrist.R", (0.3, -0.4, 0.3)), (1500, "Officer", "wrist.L", (0.0, -0.45, 0.3)),
         (300, "Attendant", "wrist.L", (0.3, -0.35, 0.3)), (900, "Sleeper1", "wrist.L", (0.3, 0.4, 0.3)),
         # v006 contacts
         (30, "Bomber", "wrist.R", (-0.3, 0.1, 0.25)), (150, "Bomber", "wrist.L", (-0.35, 0.15, 0.2)), (450, "Attendant", "wrist.L", (0.3, -0.3, 0.3)),
         (480, "PaxA", "wrist.R", (0.3, 0.3, 0.3)), (500, "Attendant", "wrist.R", (0.3, -0.3, 0.3)), (600, "PaxC", "wrist.R", (-0.3, 0.3, 0.3)),
         (600, "PaxD", "wrist.R", (0.3, 0.35, 0.3)), (690, "Steward", "wrist.R", (0.35, 0.1, 0.3)), (690, "Steward", "wrist.L", (0.35, 0.2, 0.3)),
         (720, "Attendant", "wrist.R", (0.3, 0.3, 0.3)), (876, "Attendant", "wrist.R", (0.3, 0.3, 0.3)), (900, "PaxA", "wrist.L", (0.3, 0.3, 0.3))]
# v006: each close-up camera searches for a clear sightline to the hand (no seat/body between, not inside anything) and carries a light
ld = bpy.data.lights.new("HandCheckLight", 'POINT'); ld.energy = 25; ld.shadow_soft_size = 0.3
lo = bpy.data.objects.new("HandCheckLight", ld); sc.collection.objects.link(lo)
import itertools
DIRS = [Vector(v).normalized() for v in itertools.product((-1, 0, 1), repeat=3) if any(v)]
for i, (f, rig, bone, off) in enumerate(SHOTS):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); r = O[rig]
    p = (r.matrix_world @ r.pose.bones[bone].matrix).translation
    hand_c = (p + r.matrix_world @ r.pose.bones[bone.replace("wrist", "finger3-1")].tail) / 2
    def score(dd_):
        d, dist = dd_
        c = hand_c + d * dist
        ok, loc, n, idx, ob, _ = sc.ray_cast(dg, c, (hand_c - c).normalized(), distance=dist + 0.1)
        if not ok or (loc - hand_c).length > 0.08: return -1      # first thing on the sightline must be the hand itself
        for dd in DIRS[::3]:
            ok2, l2, n2, _, ob2, _ = sc.ray_cast(dg, c, dd, distance=0.08)
            if ok2: return -1
        return d.dot(Vector(off).normalized()) + 0.5 * d.z - 0.3 * dist
    best = max([(d, dist) for d in DIRS for dist in (0.42, 0.6)], key=score)
    cam.location = hand_c + best[0] * best[1]; cam.rotation_euler = (hand_c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    lo.location = cam.location + Vector((0, 0, 0.15))
    sc.render.filepath = "%s_%02d_f%d_%s_%s.jpg" % (OUT, i, f, rig, bone); bpy.ops.render.render(write_still=True)
