"""Close crops of hands for QA sheets: render only a small border region around a wrist at full resolution.
  python handcrops.py <outdir> <set> <move>:<t>:<rig>:<side> [...]
Writes <outdir>/<set>_<move>_<t>_<rig>_<side>.exr (+ .json with the exposure), one build per variant.
"""
import os, sys, json, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
import bpy
from mathutils import Vector
import kit
from common import reset, camera
from bpy_extras.object_utils import world_to_camera_view


def main():
    out, set_name = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    mod = importlib.import_module("sc_" + set_name)
    jobs = [a.split(":") for a in sys.argv[3:]]
    by_var = {}
    for mv, t, rig, side in jobs:
        by_var.setdefault(getattr(mod, "VARIANT_FOR", {}).get(mv), []).append((mv, float(t), rig, side))
    if len(by_var) > 1:
        import subprocess
        for v, js in by_var.items():
            subprocess.run([sys.executable, os.path.abspath(__file__), out, set_name] + [f"{m}:{t}:{r}:{s}" for m, t, r, s in js])
        return
    for variant, js in by_var.items():
        s = reset(res=kit.RES, samples=int(os.environ.get("CROP_SAMPLES", 24)), exposure=getattr(mod, "EXPOSURE", 0.0))
        s.cycles.max_bounces = getattr(mod, "BOUNCES", 8)
        ctx = mod.build(variant)
        for mv, t, rig, side in js:
            spec = mod.MOVES[mv]
            cam = camera((0, 0, 0), (0, 1, 0), lens=35, dof_dist=spec.get("dof", None) and 3.0, fstop=spec.get("dof", 2.8) or 2.8)
            if spec.get("dof"):
                cam.data.dof.use_dof = True
            ctx["cam"] = cam
            kit.apply_cam(cam, ctx, spec, t)
            bpy.context.view_layer.update()
            arm = bpy.data.objects[rig]
            w = arm.matrix_world @ arm.pose.bones[f"wrist.{side}"].tail
            v = world_to_camera_view(s, cam, w)
            dist = (cam.location - w).length
            half = min(0.25, max(0.05, 0.22 / max(dist, 0.3) * 35 / cam.data.lens))     # ~22 cm around the hand
            s.render.use_border = True; s.render.use_crop_to_border = True
            s.render.border_min_x = max(0.0, v.x - half * 0.55); s.render.border_max_x = min(1.0, v.x + half * 0.55)
            s.render.border_min_y = max(0.0, v.y - half * 1.3); s.render.border_max_y = min(1.0, v.y + half * 1.3)
            s.render.resolution_percentage = 100
            s.render.image_settings.file_format = 'OPEN_EXR'; s.render.image_settings.color_depth = '32'
            s.render.use_compositing = False
            base = os.path.join(out, f"{set_name}_{mv}_{t}_{rig}_{side}")
            s.render.filepath = base + ".exr"
            bpy.ops.render.render(write_still=True)
            json.dump(dict(exposure=s.view_settings.exposure), open(base + ".json", "w"))
            print("[crop]", base, flush=True)


main()
