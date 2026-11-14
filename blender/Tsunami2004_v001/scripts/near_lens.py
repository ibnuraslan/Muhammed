"""Frames where any visible person (rig bone heads) is within LIMIT m of the camera AND inside the frame.
blender -b film.blend --python near_lens.py -- out.txt [limit=1.5] [step=2]"""
import bpy, sys
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; LIM = float(a[1]) if len(a) > 1 else 1.5; STEP = int(a[2]) if len(a) > 2 else 2
sc = bpy.context.scene; cam = sc.camera
rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE' and any(c.type == 'MESH' for c in o.children)]
hits = []
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f); cp = cam.matrix_world.translation
    for r in rigs:
        mesh = next(c for c in r.children if c.type == 'MESH')
        if mesh.hide_render or r.hide_render: continue
        mw = r.matrix_world
        best = None
        for pb in r.pose.bones:
            if pb.name.startswith(("Pole", "IK", "CTRL", "ctrl")) or not pb.bone.use_deform: continue
            w = mw @ pb.head; d = (w - cp).length
            if d < LIM:
                v = world_to_camera_view(sc, cam, w)
                if -0.15 < v.x < 1.15 and -0.15 < v.y < 1.15 and v.z > 0:
                    if best is None or d < best[0]: best = (d, pb.name)
        if best: hits.append((f, r.name, round(best[0], 2), best[1]))
open(out, "w").write("\n".join("%d %s %.2f %s" % h for h in hits) + "\n")
print("NEAR_LENS", len(hits), sorted(set(h[1] for h in hits)), [h[0] for h in hits][:40])
