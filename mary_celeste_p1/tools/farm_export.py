"""Farm export (RenderStreet): save the built, animated shot as a small self-contained .blend instead of rendering.

Called from run_anim.py when EXPORT=<package dir>. Layout of the package:
    <pkg>/shots/<id>.blend         one compressed .blend per shot (scene, animation, compositor grade, output settings)
    <pkg>/textures/*               every image the shots use, downscaled (2K max, 1K for small props) and shared by all
                                   shots via relative paths (//../textures/...)
Render settings: 2560x1440, 24 fps, Cycles, adaptive sampling + OIDN, motion blur on, PNG 16-bit RGB to //../frames/<id>/.
"""
import os, re, hashlib
import bpy

BIG = 2048          # max texture size (big surfaces: decks, walls, hull, sky is kept separately)
SMALL = 1024        # props: lantern, bucket, compass card, doll, chests, pots, stove details
SMALL_HINTS = ("lantern", "bucket", "saber", "stool", "pot", "spoon", "compass", "slate", "logpage", "doll", "chest", "lamp",
               "boot", "sextant", "cracks", "calico", "barrel", "stove")


def _safe(name):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)[:80]


def export(pkg, sid, samples=None):
    sc = bpy.context.scene
    tex = os.path.join(pkg, "textures"); shots = os.path.join(pkg, "shots"); os.makedirs(tex, exist_ok=True); os.makedirs(shots, exist_ok=True)
    blend = os.path.join(shots, f"{sid}.blend")
    # render settings for the farm
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 2560, 1440, 100
    sc.render.fps = 24
    sc.cycles.samples = samples or int(os.environ.get("FARM_SPP", "128"))
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    sc.cycles.device = 'CPU'
    sc.render.use_motion_blur = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '16'
    sc.render.filepath = f"//../frames/{sid}/{sid}_"
    sc.render.use_overwrite = False; sc.render.use_placeholder = True
    sc.render.use_persistent_data = True
    # images: downscale and write once into the shared textures folder, then point the image at it (relative)
    for img in list(bpy.data.images):
        if img.type != 'IMAGE' or img.source not in ('FILE', 'GENERATED') or img.users == 0:
            continue
        if img.size[0] == 0:
            try:
                img.reload()
            except Exception:
                continue
        w, h = img.size
        if w == 0:
            continue
        hdr = img.filepath.lower().endswith((".hdr", ".exr")) or img.is_float
        lim = 4096 if hdr else (SMALL if any(k in (img.name + img.filepath).lower() for k in SMALL_HINTS) else BIG)
        if max(w, h) > lim:
            k = lim / max(w, h); img.scale(max(1, int(w * k)), max(1, int(h * k)))
        has_alpha = img.channels == 4 and any(k in img.name.lower() for k in ("alpha", "opacity", "cracks", "eyebrow", "brows", "lash"))
        ext = ".exr" if hdr else (".png" if has_alpha else ".jpg")
        key = hashlib.md5((img.filepath + img.name + str(img.size[:])).encode()).hexdigest()[:8]
        fn = _safe(os.path.splitext(img.name)[0]) + "_" + key + ext
        dst = os.path.join(tex, fn)
        src = bpy.path.abspath(img.filepath)
        if hdr and src.lower().endswith(".hdr") and os.path.exists(src):
            # the sky HDRI: keep the original Radiance file (4K, ~25 MB) rather than an uncompressed float EXR
            import shutil
            dst = os.path.join(tex, _safe(os.path.basename(src)))
            if not os.path.exists(dst):
                shutil.copy(src, dst)
            img.filepath = bpy.path.relpath(dst, start=shots)
            continue
        if not os.path.exists(dst):
            img.filepath_raw = dst
            img.file_format = 'OPEN_EXR' if hdr else ('PNG' if ext == ".png" else 'JPEG')
            sc.render.image_settings.quality = 92
            img.save(filepath=dst, quality=92)
        else:
            img.filepath_raw = dst
        if img.packed_file:
            try:
                img.packed_file  # packed glTF images: drop the packed copy, use the shared file
                img.unpack(method='REMOVE')
            except Exception:
                pass
        img.filepath = bpy.path.relpath(dst, start=shots)
    # fonts are vector data inside text objects once converted: keep text objects as curves (fonts packed, small)
    for f in bpy.data.fonts:
        if f.filepath and f.filepath != "<builtin>" and not f.packed_file:
            try:
                f.pack()
            except Exception:
                pass
    try:
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    except Exception:
        pass
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True, relative_remap=True, copy=False)
    print("EXPORTED", blend, round(os.path.getsize(blend) / 1e6, 1), "MB", flush=True)
    return blend
