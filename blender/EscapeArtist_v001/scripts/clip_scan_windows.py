"""Run the director's pipeline/clip_scan.py once per cast-visibility window (it picks its characters at the
first frame only, so characters that appear later would never be scanned).
blender -b film.blend --python clip_scan_windows.py -- <out_dir> [step]"""
import sys, os, json, bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = a[1] if len(a) > 1 else "6"
os.makedirs(OUT, exist_ok=True)
WIN = [(0, 677), (678, 941), (942, 1379), (1380, 1547), (1548, 1859), (1860, 2483), (2484, 2898), (2899, 3165), (3166, 3228), (3229, 3479), (3480, 3750)]
SRC = open("/home/user/Muhammed/blender/pipeline/clip_scan.py").read()
sc = bpy.context.scene; allbad = []
for w0, w1 in WIN:
    sc.frame_start, sc.frame_end = w0, w1; sc.frame_set(w0)
    out = os.path.join(OUT, "clip_%04d_%04d.json" % (w0, w1))
    sys.argv = ["blender", "--", out, STEP]
    exec(SRC, {"__name__": "__main__"})
    r = json.load(open(out)); allbad += r["bad_ranges"]
    print("WINDOW", w0, w1, "bad", r["bad_ranges"])
sc.frame_start, sc.frame_end = 0, 3750
json.dump({"windows": WIN, "bad_ranges": allbad}, open(os.path.join(OUT, "clip_all.json"), "w"), indent=1)
print("ALL_BAD_RANGES", allbad)
