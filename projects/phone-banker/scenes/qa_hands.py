"""QA: twisted hands. For each shot, measure how far each visible arm is rolled about its own length, from the
upper arm to the wrist, relative to the rest pose (swing-twist decomposition per bone). A palm rolled ~180 deg
(thumb on the wrong side) shows up as a large total twist. Also reports where each wrist lands on screen, for crops.
  python qa_hands.py <set> <move>:<t>[,<t>...] ... > report lines "QA <set> <move> <t> <person> <side> <twist> <x> <y> <vis>"
"""
import os, sys, math, importlib, json
os.environ.setdefault("HOUSE_LOOK", "plain")
HERE = os.path.dirname(os.path.abspath(__file__))
import bpy
from mathutils import Vector, Quaternion
import kit
from common import reset, camera
from bpy_extras.object_utils import world_to_camera_view

CHAIN = ["upperarm01", "upperarm02", "lowerarm01", "lowerarm02", "wrist"]


def twist_deg(arm, side):
    tot = 0.0
    parts = []
    for k, bn in enumerate(CHAIN):
        b = arm.data.bones.get(f"{bn}.{side}")
        if b is None or b.parent is None:
            return None, []
        p = b.parent
        rest_rel = (p.matrix_local.inverted() @ b.matrix_local).to_3x3()
        pb = arm.pose.bones[b.name]; pp = arm.pose.bones[p.name]
        pose_rel = (pp.matrix.inverted() @ pb.matrix).to_3x3()
        q = (rest_rel.inverted() @ pose_rel).to_quaternion()
        tw = math.degrees(2 * math.atan2(q.y, q.w))
        tw = (tw + 180) % 360 - 180
        parts.append(round(tw)); tot += tw
    return tot, parts


def visible(arm):
    kids = [o for o in bpy.data.objects if o.parent == arm and o.type == 'MESH']
    return bool(kids) and not all(o.hide_render for o in kids) and not arm.hide_render


def main():
    set_name = sys.argv[1]
    mod = importlib.import_module("sc_" + set_name)
    jobs = []
    for a in sys.argv[2:]:
        mv, ts = a.split(":")
        for t in ts.split(","):
            jobs.append((mv, float(t)))
    by_var = {}
    for mv, t in jobs:
        by_var.setdefault(getattr(mod, "VARIANT_FOR", {}).get(mv), []).append((mv, t))
    if len(by_var) > 1:                      # one process per variant: rebuilding a set in the same process trips stale refs
        import subprocess
        for variant, js in by_var.items():
            args = {}
            for mv, t in js:
                args.setdefault(mv, []).append(str(t))
            subprocess.run([sys.executable, os.path.abspath(__file__), set_name] + [f"{m}:{','.join(ts)}" for m, ts in args.items()])
        return
    for variant, js in by_var.items():
        s = reset(res=kit.RES, samples=1, exposure=0.0)
        ctx = mod.build(variant)
        for mv, t in js:
            spec = mod.MOVES[mv]
            cam = camera((0, 0, 0), (0, 1, 0), lens=35)
            ctx["cam"] = cam
            kit.apply_cam(cam, ctx, spec, t)
            bpy.context.view_layer.update()
            for arm in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
                if not visible(arm):
                    continue
                for side in ("L", "R"):
                    tw, parts = twist_deg(arm, side)
                    if tw is None:
                        continue
                    fa = (arm.pose.bones[f"lowerarm02.{side}"].matrix.to_3x3() @ Vector((0, 1, 0))).normalized()
                    hy = (arm.pose.bones[f"wrist.{side}"].matrix.to_3x3() @ Vector((0, 1, 0))).normalized()
                    bend = round(math.degrees(fa.angle(hy)))
                    w = arm.matrix_world @ arm.pose.bones[f"wrist.{side}"].head
                    v = world_to_camera_view(s, cam, w)
                    vis = 0.0 <= v.x <= 1.0 and 0.0 <= v.y <= 1.0 and v.z > 0
                    print("QA", set_name, mv, t, arm.name, side, round(tw), round(v.x, 3), round(v.y, 3), int(vis),
                          json.dumps(parts), round((cam.location - w).length, 2), bend, flush=True)


main()
