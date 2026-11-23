"""Zip a packaged part into NORMAL, INDEPENDENT .zip files, each < 300 MB (no split archives), then test them:
fresh plain unzip of every zip into ONE new folder -> open MASTER.blend -> check every linked/external file resolves
-> render 3 frames (start / middle / end).

    python3 tools/zip_part.py P1 zip          # -> delivery/Antwerp_P1_k_of_n.zip
    python3 tools/zip_part.py P1 test [pct]   # fresh unzip into /tmp, verify + render 3 frames (pct of 2560x1440)
"""
import os, sys, zipfile, json, shutil, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PART, STEP = sys.argv[1], sys.argv[2]
PKG = os.path.join(ROOT, "pkg", PART); OUT = os.path.join(ROOT, "delivery")
LIMIT = 280 * 1024 * 1024          # headroom under 300 MB


def files():
    out = []
    for dp, dn, fn in os.walk(PKG):
        for f in fn:
            if f.endswith((".blend1", ".blend2")):
                continue
            p = os.path.join(dp, f); out.append((os.path.relpath(p, PKG), os.path.getsize(p)))
    return out


def zip_step():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.startswith(f"Antwerp_{PART}_"):
            os.remove(os.path.join(OUT, f))
    fs = files()
    first = [f for f in fs if f[0] == "MASTER.blend" or f[0].endswith((".txt", ".csv"))]
    rest = sorted([f for f in fs if f not in first], key=lambda x: -x[1])
    for rel, sz in fs:
        if sz > LIMIT:
            raise SystemExit(f"{rel} is {sz >> 20} MB: larger than one zip may hold")
    bins = [list(first)]; sizes = [sum(s for _, s in first)]
    for rel, sz in rest:                                  # first fit decreasing
        for k in range(len(bins)):
            if sizes[k] + sz < LIMIT:
                bins[k].append((rel, sz)); sizes[k] += sz; break
        else:
            bins.append([(rel, sz)]); sizes.append(sz)
    n = len(bins)
    for k, b in enumerate(bins):
        name = os.path.join(OUT, f"Antwerp_{PART}_{k + 1}_of_{n}.zip")
        with zipfile.ZipFile(name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for rel, _ in sorted(b):
                z.write(os.path.join(PKG, rel), rel.replace(os.sep, "/"))
        print("ZIP", os.path.basename(name), os.path.getsize(name) >> 20, "MB", len(b), "files")
        assert os.path.getsize(name) < 300 * 1024 * 1024


def test_step():
    pct = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    tmp = f"/tmp/antwerp_unzip_{PART}"
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    zips = sorted(f for f in os.listdir(OUT) if f.startswith(f"Antwerp_{PART}_") and f.endswith(".zip"))
    for z in zips:                                          # plain extraction, all into ONE folder
        with zipfile.ZipFile(os.path.join(OUT, z)) as zz:
            assert zz.testzip() is None, z
            zz.extractall(tmp)
    T = json.load(open(os.path.join(ROOT, "timing", f"{PART}_shots.json"))); N = T["frames"]
    script = f'''
import bpy, os, sys
sc = bpy.data.scenes["MASTER"]
bad = []
for lib in bpy.data.libraries:
    if not os.path.exists(bpy.path.abspath(lib.filepath)): bad.append(("lib", lib.filepath))
assert sc.camera is not None, "no scene camera"
print("LIBS", len(bpy.data.libraries), "MISSING", bad)
for lib in bpy.data.libraries:
    pass
import bpy
for im in bpy.data.images:
    if im.source == "FILE" and not im.packed_file:
        p = bpy.path.abspath(im.filepath, library=im.library)
        if not os.path.exists(p): bad.append(("img", im.name, p))
print("MISSINGALL", len(bad), bad[:10])
sc.render.resolution_percentage = {pct}
for f in (1, {N} // 2, {N}):
    sc.frame_set(f); sc.render.filepath = os.path.join("{tmp}", "test_%04d.png" % f)
    bpy.ops.render.render(write_still=True, scene="MASTER")
    print("TESTFRAME", f, os.path.exists(sc.render.filepath))
'''
    sp = os.path.join(tmp, "_test.py"); open(sp, "w").write(script)
    r = subprocess.run(["blender", "-b", os.path.join(tmp, "MASTER.blend"), "--python", sp], capture_output=True, text=True)
    for l in (r.stdout + r.stderr).splitlines():
        if l.startswith(("LIBS", "MISSING", "TESTFRAME", "Error", "Traceback")) or "Error" in l:
            print(l)
    print("unzipped", sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fn in os.walk(tmp) for f in fn) >> 20, "MB from", len(zips), "zips")


{"zip": zip_step, "test": test_step}[STEP]()
