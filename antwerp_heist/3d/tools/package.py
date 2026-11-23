"""Farm package for one part, strictly per FARM_DELIVERY_RULES.md.

    blender -b --python tools/package.py -- P1 shots      # shots/*.blend -> pkg/P1/shots (textures <= 2K, shared, relative)
    blender -b --python tools/package.py -- P1 master     # pkg/P1/MASTER.blend (scene MASTER: Scene strips from //shots/)
    python3 tools/package.py P1 lists                     # CapCut shot list (.txt + .csv) + credits
Layout of pkg/<PART>/ (= what the user uploads after "Extract all"):
    MASTER.blend   shots/<ID>.blend   textures/<file>   frames/ (render output)
"""
import os, sys, json, hashlib, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
try:
    import bpy
    argv = sys.argv[sys.argv.index("--") + 1:]
except ImportError:
    bpy = None; argv = sys.argv[1:]
PART, STEP = argv[0], argv[1]
PKG = os.path.join(ROOT, "pkg", PART)
T = json.load(open(os.path.join(ROOT, "timing", f"{PART}_shots.json")))
ORDER = sorted(T["shots"], key=lambda s: T["shots"][s]["start"])
MAXTEX = 2048


def shots_step():
    os.makedirs(os.path.join(PKG, "shots"), exist_ok=True); os.makedirs(os.path.join(PKG, "textures"), exist_ok=True)
    only = argv[2:] or ORDER
    for sid in only:
        src = os.path.join(ROOT, "shots", PART, sid + ".blend")
        bpy.ops.wm.open_mainfile(filepath=src)
        for img in list(bpy.data.images):
            if img.packed_file:                        # glTF textures arrive packed: cap them at 2K too
                try:
                    w, h = img.size
                    if max(w, h) > MAXTEX:
                        s = MAXTEX / max(w, h); img.scale(max(1, int(w * s)), max(1, int(h * s))); img.pack()
                except Exception as e:
                    print("packed", img.name, e)
                continue
            if img.source not in ('FILE', 'SEQUENCE'):
                continue
            ap = bpy.path.abspath(img.filepath, library=img.library)
            if not os.path.exists(ap):
                print("MISSING", sid, img.name, ap); continue
            try:
                w, h = img.size
            except Exception:
                w, h = 0, 0
            stem, ext = os.path.splitext(os.path.basename(ap))
            key = hashlib.md5(os.path.abspath(ap).encode()).hexdigest()[:8]
            big = max(w, h) > MAXTEX
            name = f"{stem}_{key}{'_2k' if big else ''}{ext.lower() if ext.lower() in ('.jpg', '.jpeg', '.png', '.exr', '.hdr') else '.png'}"
            dst = os.path.join(PKG, "textures", name)
            if not os.path.exists(dst):
                if big:
                    s = MAXTEX / max(w, h)
                    img.scale(max(1, int(w * s)), max(1, int(h * s)))
                    img.filepath_raw = dst
                    img.file_format = 'JPEG' if ext.lower() in ('.jpg', '.jpeg') else ('OPEN_EXR' if ext.lower() == '.exr' else 'PNG')
                    img.save()
                else:
                    shutil.copy2(ap, dst)
            img.filepath = "//../textures/" + name
        out = os.path.join(PKG, "shots", sid + ".blend")
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=False)
        print("PKG", sid, os.path.getsize(out) // 1024, "KB")


def master_step():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.name = "MASTER"
    N = T["frames"]
    # colour management copied from the first shot (all shots share the same pipeline); verified below per shot
    ref = None
    for sid in ORDER:
        path = os.path.join(PKG, "shots", sid + ".blend")
        with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
            dst.scenes = [sid]
        shot_sc = bpy.data.scenes[sid]
        if ref is None:
            ref = shot_sc
    sc.render.engine = 'CYCLES'
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 2560, 1440, 100
    sc.render.fps = 24; sc.render.fps_base = 1.0
    sc.frame_start = 1; sc.frame_end = N
    vs, rs = sc.view_settings, ref.view_settings
    sc.display_settings.display_device = ref.display_settings.display_device
    vs.view_transform = rs.view_transform; vs.look = rs.look; vs.exposure = rs.exposure; vs.gamma = rs.gamma
    vs.use_curve_mapping = rs.use_curve_mapping
    sc.sequencer_colorspace_settings.name = ref.sequencer_colorspace_settings.name
    for sid in ORDER:          # all shots must agree with what MASTER applies
        s2 = bpy.data.scenes[sid]
        assert (s2.view_settings.view_transform, s2.view_settings.look, s2.view_settings.exposure, s2.view_settings.gamma) == \
            (vs.view_transform, vs.look, vs.exposure, vs.gamma), sid
    sc.render.use_compositing = False; sc.render.use_sequencer = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'
    sc.render.filepath = "//frames/"
    sc.cycles.samples = 64; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.01; sc.cycles.use_denoising = True
    sc.render.use_motion_blur = True
    se = sc.sequence_editor_create()
    strips = se.strips if hasattr(se, "strips") else se.sequences
    for sid in ORDER:
        v = T["shots"][sid]; s2 = bpy.data.scenes[sid]
        st = strips.new_scene(name=sid, scene=s2, channel=1, frame_start=v["start"])
        st.scene_input = 'CAMERA'
        st.frame_final_duration = v["frames"]
        assert s2.frame_end - s2.frame_start + 1 >= v["frames"], (sid, s2.frame_end, v["frames"])
    # RenderStreet needs a scene camera even though the sequencer drives the render
    cam = bpy.data.objects.new("MASTER_cam", bpy.data.cameras.new("MASTER_cam")); sc.collection.objects.link(cam); sc.camera = cam
    out = os.path.join(PKG, "MASTER.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out, relative_remap=True)
    print("MASTER", out, N, "frames", len(ORDER), "strips")


def lists_step():
    import csv
    os.makedirs(PKG, exist_ok=True)
    src = open(os.path.join(ROOT, "scenes", PART.lower() + ".py")).read()
    import re
    desc = {s: d for s, _, _, d in re.findall(r'\("([A-Z]\d+)", (\d+), ([0-9.]+), "([^"]*)"\)', src)}
    vo = [l.strip() for l in open(os.path.join(ROOT, "..", "vo", f"ANTWERP_{PART}_VO.txt")) if l.strip()]
    tc = lambda f: "%02d:%02d:%02d" % (int((f - 1) / 24 // 60), int((f - 1) / 24 % 60), int((f - 1) % 24))
    rows = []
    for k, sid in enumerate(ORDER):
        v = T["shots"][sid]; a = v["start"]; b = a + v["frames"] - 1
        rows.append([k + 1, sid, a, b, tc(a), tc(b + 1), f"{v['dur']:.2f}", v["line"], desc.get(sid, ""), vo[v["line"] - 1]])
    hdr = ["#", "shot", "first_frame", "last_frame", "in (mm:ss:ff)", "out (mm:ss:ff)", "seconds", "vo_line", "picture", "narration"]
    with open(os.path.join(PKG, f"{PART}_capcut_shotlist.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(hdr); w.writerows(rows)
    with open(os.path.join(PKG, f"{PART}_capcut_shotlist.txt"), "w") as f:
        f.write(f"They Stole $100 Million. Then Threw Away the Evidence. - Part {PART[1:]}\n")
        f.write(f"{T['frames']} frames @ 24 fps = {T['frames'] / 24:.2f} s (= ANTWERP_{PART}_VO.mp3). Image sequence: frames/0001.png ...\n")
        f.write("No cards or captions are burned in; add them in CapCut.\n\n")
        for r in rows:
            f.write(f"{r[0]:>2}. {r[1]}  frames {r[2]}-{r[3]}  ({r[4]} -> {r[5]}, {r[6]} s)  VO line {r[7]}\n    {r[8]}\n")
    # credits: every Sketchfab model used (CC-BY: attribution required) + Poly Haven (CC0)
    sfd = os.path.join(ROOT, "assets", "sketchfab"); lines = []
    for f in sorted(os.listdir(sfd)) if os.path.isdir(sfd) else []:
        if f.endswith(".json"):
            m = json.load(open(os.path.join(sfd, f)))
            lines.append(f'"{m["name"]}" by {m["author"]} - {m["license"]} - {m["url"]}')
    with open(os.path.join(PKG, "CREDITS.txt"), "w") as f:
        f.write("3D models from Sketchfab (Creative Commons Attribution):\n" + "\n".join(lines) +
                "\n\nTextures and models from Poly Haven (CC0). Human bodies from MakeHuman (CC0 assets).\n")
    print("LISTS", PART, len(rows))


{"shots": shots_step, "master": master_step, "lists": lists_step}[STEP]()
