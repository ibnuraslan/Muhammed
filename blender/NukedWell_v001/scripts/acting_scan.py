"""Acting scan: for every crew member, every 2 frames:
  TELEPORT   root moves > 0.6 m in 2 frames while in the camera view
  FOOT_SLIDE a foot that is on the ground (< 3 cm up) moves > 1.5 cm in 2 frames while the other foot also is planted (both feet down and one slides)
  FROZEN     on screen and large in frame (> 6 % of frame height) with almost no bone motion for > 1.5 s
blender -b anim.blend --python acting_scan.py -- <report.txt>"""
import sys, bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects; cam = sc.camera
CREW = ["SolA", "SolB", "SolC", "SolD", "EngA", "EngB"]
SHAFT = Vector((-14.0, -2.7))
def gz(x, y): r = (Vector((x, y)) - SHAFT).length; return 0.4 if 0.72 < r < 1.68 else 0.0
def jz(): return O["JoltRoot"].matrix_world.translation.z
prev = {}; still = {n: [] for n in CREW}; out = {"TELEPORT": [], "FOOT_SLIDE": [], "FROZEN": []}
for f in range(1, sc.frame_end + 1, 2):
    sc.frame_set(f); j = jz()
    for nm in CREW:
        r = O[nm]; P = r.pose.bones
        root = r.matrix_world @ P["root"].head; head = r.matrix_world @ P["head"].head
        feet = {s: r.matrix_world @ P["foot." + s].head for s in "LR"}
        hands = {s: r.matrix_world @ P["wrist." + s].head for s in "LR"}
        c = world_to_camera_view(sc, cam, root); ch = world_to_camera_view(sc, cam, head)
        vis = 0 <= c.x <= 1 and -0.1 <= c.y <= 1.1 and c.z > 0.3
        size = abs(ch.y - world_to_camera_view(sc, cam, (feet["L"] + feet["R"]) / 2).y) if vis else 0
        if nm in prev:
            pr, pf, ph = prev[nm]
            if vis and (root - pr).length > 0.6: out["TELEPORT"].append((f, nm, (root - pr).length))
            down = {s: feet[s].z - gz(feet[s].x, feet[s].y) - j < 0.13 for s in "LR"}   # ankle height ~0.1 when planted
            for s in "LR":
                mv = (feet[s] - pf[s]).to_2d().length
                if vis and size > 0.04 and down["L"] and down["R"] and mv > 0.015 and (pf[s].z - feet[s].z) ** 2 < 1e-4 and (root - pr).length < 0.6:
                    out["FOOT_SLIDE"].append((f, nm + "." + s, mv))
            motion = sum((hands[s] - ph[s]).length for s in "LR") + (root - pr).length
            if vis and size > 0.06 and motion < 0.004: still[nm].append(f)
        prev[nm] = (root, feet, hands)
for nm, fs in still.items():
    run = []
    for f in fs:
        if run and f - run[-1] > 2:
            if len(run) * 2 > 90: out["FROZEN"].append((run[0], nm, (run[-1] - run[0]) / 60))
            run = []
        run.append(f)
    if run and len(run) * 2 > 90: out["FROZEN"].append((run[0], nm, (run[-1] - run[0]) / 60))
lines = []
for k, v in out.items():
    lines.append("%s %d" % (k, len(v)))
    for f, nm, x in v[:400]: lines.append("   f%d %.2fs %s %.2f" % (f, (f - 1) / 60, nm, x))
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
