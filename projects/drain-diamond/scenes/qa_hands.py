"""Hand QA: for every set/move, at t = 0.05 / 0.5 / 0.95, measure the twist (roll about the bone axis) of each
forearm and wrist relative to its parent on every MakeHuman rig. A hand rolled ~180 deg (thumb on the wrong side)
shows up as a large twist. Prints one line per suspicious arm:  QA set move t rig side bone twist_deg
  PYTHONPATH=projects/drain-diamond/scenes:nvidia_doc/scenes python projects/drain-diamond/scenes/qa_hands.py set [moves...]
"""
import sys, math, importlib
import bpy
from mathutils import Vector
import kit
from common import reset, camera

LIMIT = float(__import__("os").environ.get("QA_TWIST", 75))
CHAIN = ["upperarm01", "upperarm02", "lowerarm01", "lowerarm02", "wrist"]


def twist(parent, child):
    q = parent.matrix.to_quaternion().inverted() @ child.matrix.to_quaternion()
    d = math.degrees(2 * math.atan2(q.y, q.w))
    return (d + 180.0) % 360.0 - 180.0             # wrap: 350 deg is really -10


def rigs():
    return [o for o in bpy.data.objects if o.type == 'ARMATURE' and "wrist.L" in o.pose.bones]


set_name = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else sys.argv[1]
mod = importlib.import_module("sc_" + set_name)
moves = sys.argv[2:3] or list(mod.MOVES)[:1]          # one move per process (module caches hold materials)
for mv in moves:
    if mv not in mod.MOVES:
        continue
    s = reset(res=kit.RES, samples=1)
    ctx = mod.build(getattr(mod, "VARIANT_FOR", {}).get(mv, None))
    spec = mod.MOVES[mv]
    cam = camera((0, 0, 0), (0, 1, 0), lens=35); ctx["cam"] = cam
    worst = 0.0
    for t in (0.05, 0.5, 0.95):
        kit.apply_cam(cam, ctx, spec, t); bpy.context.view_layer.update()
        for r in rigs():
            if r.location.z < -5:        # parked out of shot
                continue
            for sd in ("L", "R"):
                pb = r.pose.bones
                for a, b in zip(CHAIN, CHAIN[1:]):
                    tw = twist(pb[f"{a}.{sd}"], pb[f"{b}.{sd}"])
                    worst = max(worst, abs(tw))
                    if abs(tw) > LIMIT:
                        print(f"QA {set_name} {mv} t={t} {r.name} {sd} {a}->{b} twist={tw:.0f}", flush=True)
    print(f"QADONE {set_name} {mv} worst={worst:.0f}", flush=True)
