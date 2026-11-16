"""Run a pipeline checker once per shot with that shot's camera.
The pipeline checkers read `cam = sc.camera` once at load; this film switches cameras with timeline markers, so a single run
judges every frame through CAM_S01. This wrapper sets the shot's camera and frame range, runs the checker, and merges the output.
blender -b film.blend --python per_shot_check.py -- <checker.py> <out.json> <step> [extra args...]"""
import bpy, sys, json, os
a = sys.argv[sys.argv.index("--") + 1:]
CHK, OUT, STEP, EXTRA = a[0], a[1], a[2], a[3:]
sc = bpy.context.scene
shots = json.loads(sc["SHOTS_JSON"])
merged = {"per_shot": {}}
src = open(CHK).read()
for name, f0, f1 in shots:
    sc.frame_start, sc.frame_end = f0, f1
    sc.camera = bpy.data.objects["CAM_" + name]
    out = OUT + "." + name + ".json"
    sys.argv = [sys.argv[0], "--", out, STEP] + EXTRA
    g = {"__name__": "__main__", "__file__": CHK}
    try:
        exec(compile(src, CHK, "exec"), g)
        merged["per_shot"][name] = json.load(open(out))
    except Exception as e:
        merged["per_shot"][name] = {"error": repr(e)}
    print("PER_SHOT", name, f0, f1, "done", flush=True)
sc.frame_start, sc.frame_end = shots[0][1], shots[-1][2]
json.dump(merged, open(OUT, "w"))
print("PER_SHOT_DONE", OUT)
