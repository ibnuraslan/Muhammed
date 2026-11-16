"""Run pipeline/body_prop_cross.py once per shot: only that shot's frames, its visible rigs, the props it touches.
blender -b film.blend --python bpc_shots.py -- outdir step SID"""
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]; od, step, sid = a[0], a[1], a[2]
SH = {s["id"]: s for s in json.load(open("/home/user/Muhammed/blender/FakeDrainRescue_v001/shots.json"))}; s = SH[sid]
sc = bpy.context.scene; sc.frame_start, sc.frame_end = s["f0"], s["f1"]; sc.frame_set(s["f0"] + 1)
sc.camera = bpy.data.objects["CAM_" + sid]
rigs = [o.name for o in bpy.data.objects if o.type == 'ARMATURE' and not o.hide_render]
allp = open("/home/user/Muhammed/blender/FakeDrainRescue_v001/work/bpc_props.txt").read().split(",")
props = [p for p in allp if p in bpy.data.objects and not bpy.data.objects[p].hide_render]
props += [o.name for o in bpy.data.objects if o.name.startswith(("C_bag", "Clog_", "Drift_")) and not o.hide_render and o.name not in props]
print("BPCSHOT", sid, rigs, len(props))
if not rigs: json.dump({"visible_frames": [], "frames": {}, "note": "no characters"}, open(f"{od}/{sid}.json", "w")); raise SystemExit
for o in bpy.data.objects:   # the checker reads hide_render once, at load: freeze per-shot visibility
    pass
sys.argv = ["x", "--", f"{od}/{sid}.json", step, ",".join(props), ",".join(rigs)]
exec(open("/home/user/Muhammed/blender/pipeline/body_prop_cross.py").read())
