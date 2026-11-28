"""Romand farm package for one part, per FARM_DELIVERY_RULES.md with the hub's settings for this film
(native 1920x1080, Cycles 16 spp adaptive, OIDN, no volumes; the 2K upscale and the overlays happen after the farm).
Adapted from antwerp_heist/3d/tools/package.py + zip_part.py.

    blender -b --python pack_farm.py -- 1 lib        # lib/trees.blend textures -> textures/, relative
    blender -b --python pack_farm.py -- 1 shots      # built shots (FARM build) -> pkg/shots, textures shared + relative
    blender -b --python pack_farm.py -- 1 master     # pkg/MASTER.blend: scene MASTER, Scene strips from //shots/
    python3 pack_farm.py 1 lists                     # CapCut shot list (.txt + .csv) + CREDITS.txt
    python3 pack_farm.py 1 zip                       # normal independent zips < 300 MB
    python3 pack_farm.py 1 test [pct]                # fresh unzip into one folder, check links/images, render 3 frames
Env: PKG=<package dir> (holds MASTER.blend, shots/, lib/, textures/), BUILT=<dir with the farm-built shots/*.blend>,
     DELIV=<zip output dir>.
Layout of PKG (= what the user uploads after "Extract all"): MASTER.blend shots/ lib/ textures/ frames/ (render output)"""
import os, sys, json, hashlib, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
try:
    import bpy
    argv = sys.argv[sys.argv.index("--") + 1:]
except ImportError:
    bpy = None; argv = sys.argv[1:]
PART, STEP = int(argv[0]), argv[1]
PKG = os.environ["PKG"]; BUILT = os.environ.get("BUILT", ""); DELIV = os.environ.get("DELIV", os.path.join(PKG, "..", "delivery"))
ROWS = json.load(open(os.path.join(ROOT, "shots", "shots.json")))[str(PART)]["rows"]
FPS = 24
MAXTEX = 2048
# timeline: every shot in VO order, frame counts as built (max(12, round(dur * 24)))
TL = []; f = 1
for r in ROWS:
    n = max(12, round(r["dur"] * FPS)); TL.append(dict(id=r["id"], start=f, frames=n, kind=r["kind"], vo=r["vo"], act=r["act"])); f += n
NFR = f - 1
if bpy:
    bpy.context.preferences.filepaths.save_version = 0


def _textures(tag):
    """Copy every external image into PKG/textures (capped at 2K) and point it there relatively; unpack packed ones."""
    os.makedirs(os.path.join(PKG, "textures"), exist_ok=True)
    for img in list(bpy.data.images):
        if img.library is not None or img.source not in ('FILE', 'SEQUENCE'):
            continue
        if img.packed_file:
            try:
                w, h = img.size
                if max(w, h) > MAXTEX:
                    s = MAXTEX / max(w, h); img.scale(max(1, int(w * s)), max(1, int(h * s))); img.pack()
            except Exception as e:
                print("packed", img.name, e)
            continue
        ap = bpy.path.abspath(img.filepath)
        if not os.path.exists(ap):
            print("MISSING", tag, img.name, ap); continue
        stem, ext = os.path.splitext(os.path.basename(ap))
        key = hashlib.md5(os.path.abspath(ap).encode()).hexdigest()[:8]
        try:
            w, h = img.size
        except Exception:
            w, h = 0, 0
        big = max(w, h) > MAXTEX
        name = f"{stem}_{key}{'_2k' if big else ''}{ext.lower()}"
        dst = os.path.join(PKG, "textures", name)
        if not os.path.exists(dst):
            if big:
                s = MAXTEX / max(w, h); img.scale(max(1, int(w * s)), max(1, int(h * s)))
                img.filepath_raw = dst; img.file_format = 'JPEG' if ext.lower() in ('.jpg', '.jpeg') else 'PNG'; img.save()
            else:
                shutil.copy2(ap, dst)
        img.filepath = "//../textures/" + name


def lib_step():
    src = os.path.join(PKG, "lib", "trees.blend")
    bpy.ops.wm.open_mainfile(filepath=src)
    _textures("lib")
    bpy.ops.wm.save_as_mainfile(filepath=src, compress=True, relative_remap=False)
    print("LIB", src, os.path.getsize(src) >> 20, "MB")


def shots_step():
    os.makedirs(os.path.join(PKG, "shots"), exist_ok=True)
    only = argv[2:] or [t["id"] for t in TL]
    for sid in only:
        src = os.path.join(BUILT, "shots", sid + ".blend")
        if not os.path.exists(src):
            print("NO3D", sid); continue
        bpy.ops.wm.open_mainfile(filepath=src)
        for lib in bpy.data.libraries:                   # the shared tree library, relative to shots/
            lib.filepath = "//../lib/" + os.path.basename(lib.filepath)
        _textures(sid)
        sc = bpy.context.scene; sc.name = sid
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
        sc.cycles.samples = 16; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
        sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.max_bounces = 4
        sc.render.use_motion_blur = False
        # one colour pipeline for MASTER: the shot's view exposure moves into its compositor (same linear multiply)
        ev = sc.view_settings.exposure
        if abs(ev) > 1e-6:
            nt = getattr(sc, "compositing_node_group", None) or getattr(sc, "node_tree", None)
            outn = next((n for n in nt.nodes if n.bl_idname in ("NodeGroupOutput", "CompositorNodeComposite")), None) if nt else None
            if outn is None or not outn.inputs[0].links:
                raise RuntimeError(f"{sid}: view exposure {ev} but no compositor to carry it")
            lk = outn.inputs[0].links[0]; s_ = lk.from_socket; nt.links.remove(lk)
            ex = nt.nodes.new("CompositorNodeExposure"); ex.inputs[1].default_value = ev
            nt.links.new(s_, ex.inputs[0]); nt.links.new(ex.outputs[0], outn.inputs[0])
            sc.view_settings.exposure = 0.0
            print("EXPOSURE", sid, round(ev, 3), "-> compositor")
        out = os.path.join(PKG, "shots", sid + ".blend")
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=False)
        print("PKG", sid, os.path.getsize(out) >> 10, "KB")


def master_step():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.name = "MASTER"
    ref = None; have = []
    for t in TL:
        path = os.path.join(PKG, "shots", t["id"] + ".blend")
        if not os.path.exists(path):
            continue
        with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
            dst.scenes = [t["id"]]
        have.append(t["id"]); ref = ref or bpy.data.scenes[t["id"]]
    sc.render.engine = 'CYCLES'
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = NFR
    vs, rs = sc.view_settings, ref.view_settings
    sc.display_settings.display_device = ref.display_settings.display_device
    vs.view_transform = rs.view_transform; vs.look = rs.look; vs.exposure = rs.exposure; vs.gamma = rs.gamma
    vs.use_curve_mapping = rs.use_curve_mapping
    sc.sequencer_colorspace_settings.name = ref.sequencer_colorspace_settings.name
    for sid in have:                                         # rule 7: every shot agrees with what MASTER applies
        s2 = bpy.data.scenes[sid]
        assert (s2.view_settings.view_transform, s2.view_settings.look, s2.view_settings.exposure, s2.view_settings.gamma) == \
            (vs.view_transform, vs.look, vs.exposure, vs.gamma), sid
    sc.render.use_compositing = False; sc.render.use_sequencer = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'
    sc.render.filepath = "//frames/"
    sc.cycles.samples = 16; sc.cycles.use_adaptive_sampling = True; sc.cycles.use_denoising = True
    se = sc.sequence_editor_create(); strips = se.strips if hasattr(se, "strips") else se.sequences
    for t in TL:
        if t["id"] in have:
            st = strips.new_scene(name=t["id"], scene=bpy.data.scenes[t["id"]], channel=1, frame_start=t["start"])
            st.scene_input = 'CAMERA'; st.frame_final_duration = t["frames"]
        else:                                                # card-only shot: black under the overlay
            st = strips.new_effect(name=t["id"], type='COLOR', channel=1, frame_start=t["start"], length=t["frames"]) \
                if hasattr(strips, "new_effect") else None
            if st is not None:
                st.color = (0, 0, 0)
    cam = bpy.data.objects.new("MASTER_cam", bpy.data.cameras.new("MASTER_cam")); sc.collection.objects.link(cam); sc.camera = cam
    out = os.path.join(PKG, "MASTER.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out, relative_remap=True)
    print("MASTER", out, NFR, "frames", len(have), "scene strips", len(TL) - len(have), "card strips")


def lists_step():
    import csv
    tc = lambda f: "%02d:%02d:%02d" % (int((f - 1) / FPS // 60), int((f - 1) / FPS % 60), int((f - 1) % FPS))
    rows = [[k + 1, t["id"], t["start"], t["start"] + t["frames"] - 1, tc(t["start"]), tc(t["start"] + t["frames"]),
             f"{t['frames'] / FPS:.2f}", t["act"], t["vo"]] for k, t in enumerate(TL)]
    hdr = ["#", "shot", "first_frame", "last_frame", "in", "out", "seconds", "picture", "narration"]
    with open(os.path.join(PKG, f"P{PART}_capcut_shotlist.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(hdr); w.writerows(rows)
    with open(os.path.join(PKG, f"P{PART}_capcut_shotlist.txt"), "w", encoding="utf-8") as f:
        f.write(f"Romand film, Part {PART}: {NFR} frames @ 24 fps = {NFR / FPS:.2f} s (timed to the estimated VO; retime to the recording).\n")
        f.write("Render: MASTER.blend, scene MASTER, frames 1-%d -> frames/. Overlays come separately (alpha PNG sequence).\n\n" % NFR)
        for r in rows:
            f.write(f"{r[0]:>2}. {r[1]}  frames {r[2]}-{r[3]}  ({r[4]} -> {r[5]}, {r[6]} s)\n    {r[7]}\n    VO: {r[8]}\n")
    with open(os.path.join(PKG, "CREDITS.txt"), "w") as f:
        f.write("3D models from Sketchfab (Creative Commons Attribution 4.0):\n"
                '"Eric Rigged 001" by renderpeople\n"1994 Peugeot 405 GLX (facelift version)" by Mehrdad995GTa\n'
                '"leafless tree_2" by sambath21052009\n"ZBrush leafless tree" by hirnlaich\n\n'
                "Models and textures from Poly Haven (CC0): fir_tree_01, fir_sapling_medium, rubber_boots.\n"
                "Map outlines: Natural Earth (public domain).\n")
    print("LISTS", PART, len(rows), NFR)


def zip_step():
    import zipfile
    LIMIT = 280 * 1024 * 1024
    os.makedirs(DELIV, exist_ok=True)
    for f in os.listdir(DELIV):
        if f.startswith(f"Romand_P{PART}_"):
            os.remove(os.path.join(DELIV, f))
    fs = []
    for dp, dn, fn in os.walk(PKG):
        if os.path.relpath(dp, PKG).startswith("frames"):
            continue
        for f_ in fn:
            if not f_.endswith((".blend1", ".blend2")):
                p = os.path.join(dp, f_); fs.append((os.path.relpath(p, PKG), os.path.getsize(p)))
    first = [x for x in fs if x[0] == "MASTER.blend" or x[0].endswith((".txt", ".csv"))]
    rest = sorted([x for x in fs if x not in first], key=lambda x: -x[1])
    for rel, sz in fs:
        if sz > LIMIT:
            raise SystemExit(f"{rel} is {sz >> 20} MB: larger than one zip may hold")
    bins = [list(first)]; sizes = [sum(s for _, s in first)]
    for rel, sz in rest:
        for k in range(len(bins)):
            if sizes[k] + sz < LIMIT:
                bins[k].append((rel, sz)); sizes[k] += sz; break
        else:
            bins.append([(rel, sz)]); sizes.append(sz)
    n = len(bins)
    for k, b in enumerate(bins):
        name = os.path.join(DELIV, f"Romand_P{PART}_{k + 1}_of_{n}.zip")
        with zipfile.ZipFile(name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for rel, _ in sorted(b):
                z.write(os.path.join(PKG, rel), rel.replace(os.sep, "/"))
        print("ZIP", os.path.basename(name), os.path.getsize(name) >> 20, "MB", len(b), "files")
        assert os.path.getsize(name) < 300 * 1024 * 1024


def test_step():
    import zipfile, subprocess
    pct = int(argv[2]) if len(argv) > 2 else 100
    tmp = os.path.join(os.environ.get("TESTDIR", "/tmp"), f"romand_unzip_P{PART}")
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    zips = sorted(f for f in os.listdir(DELIV) if f.startswith(f"Romand_P{PART}_") and f.endswith(".zip"))
    for z in zips:
        with zipfile.ZipFile(os.path.join(DELIV, z)) as zz:
            assert zz.testzip() is None, z
            zz.extractall(tmp)
    script = f'''
import bpy, os
sc = bpy.data.scenes["MASTER"]; bad = []
assert sc.camera is not None, "no scene camera"
for lib in bpy.data.libraries:
    if not os.path.exists(bpy.path.abspath(lib.filepath)): bad.append(("lib", lib.filepath))
for im in bpy.data.images:
    if im.source == "FILE" and not im.packed_file:
        p = bpy.path.abspath(im.filepath, library=im.library)
        if not os.path.exists(p): bad.append(("img", im.name, p))
print("LIBS", len(bpy.data.libraries), "MISSING", len(bad), bad[:10])
sc.render.resolution_percentage = {pct}
for f in (1, {NFR} // 2, {NFR}):
    sc.frame_set(f); sc.render.filepath = os.path.join("{tmp}", "test_%04d.png" % f)
    bpy.ops.render.render(write_still=True, scene="MASTER")
    print("TESTFRAME", f, os.path.exists(sc.render.filepath))
'''
    sp = os.path.join(tmp, "_test.py"); open(sp, "w").write(script)
    r = subprocess.run(["blender", "-b", os.path.join(tmp, "MASTER.blend"), "--python", sp], capture_output=True, text=True)
    for l in (r.stdout + r.stderr).splitlines():
        if l.startswith(("LIBS", "TESTFRAME", "Traceback")) or "Error" in l:
            print(l)
    print("unzipped", sum(os.path.getsize(os.path.join(dp, f_)) for dp, _, fn in os.walk(tmp) for f_ in fn) >> 20, "MB from", len(zips), "zips")


{"lib": lib_step, "shots": shots_step, "master": master_step, "lists": lists_step, "zip": zip_step, "test": test_step}[STEP]()
