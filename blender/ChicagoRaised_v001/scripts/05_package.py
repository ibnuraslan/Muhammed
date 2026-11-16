"""Phase-2 package: VO strip, frame range, farm settings, unused data removed, textures capped at 1k and packed.
blender -b work/look.blend -P 05_package.py -- <vo.mp3> <out.blend> <frame_end>
Then run pipeline/package_for_farm.py on <out.blend> for the farm checks."""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; VO, OUT, FEND = a[0], a[1], int(a[2])
sc = bpy.context.scene
sc.frame_start = 1; sc.frame_end = FEND
# VO as the only sound strip, from frame 1
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
for st in list(getattr(se, "strips", getattr(se, "sequences", []))):
    (se.strips if hasattr(se, "strips") else se.sequences).remove(st)
coll = se.strips if hasattr(se, "strips") else se.sequences
snd = coll.new_sound("VO", VO, 1, 1)
# unused rig (W4 was dropped from the crank crew) and the hidden model library (copies keep their mesh data)
def drop(o):
    for c in list(o.children_recursive): bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.objects.remove(o, do_unlink=True)
if "W4" in bpy.data.objects: drop(bpy.data.objects["W4"])
reed = bpy.data.collections.get("ReedSet")
keep = set(reed.objects) if reed else set()
lib = bpy.data.collections.get("LIB")
if lib:
    for o in list(lib.objects):
        if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
for _ in range(3): bpy.ops.outliner.orphans_purge(do_recursive=True)
# identical donor textures appended several times (".001", ".002"): keep one, remap the users
by = {}
for im in list(bpy.data.images):
    key = (bpy.path.abspath(im.filepath) if im.filepath else None, tuple(im.size), im.source)
    if key[0] is None or im.source != 'FILE': continue
    if key in by: im.user_remap(by[key]); bpy.data.images.remove(im)
    else: by[key] = im
print("IMAGES after dedupe", len(bpy.data.images))
# textures: cap the long side at 1024 px (512 for tiling set textures); keeps alpha: Image.scale + pack, never save_render
SET_TEX = ("_2k", "_1k", "Armchair_01", "Shelf_01", "nor_gl")
n = 0
for im in bpy.data.images:
    if im.source != 'FILE' or im.size[0] == 0: continue
    w, h = im.size
    cap = 512 if (any(t in im.name for t in SET_TEX) and not im.name.endswith(".hdr")) else 1024
    if max(w, h) > cap:
        k = cap / max(w, h); im.scale(max(1, int(w * k)), max(1, int(h * k))); n += 1
    im.pack()
print("IMAGES scaled", n, "of", len(bpy.data.images))
# farm settings (PRODUCTION_RULES: Cycles 48 spp, adaptive 0.05, OIDN; 1080x1920 @ 60)
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = 60; r.fps_base = 1.0; r.use_motion_blur = False
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.device = 'CPU'
r.image_settings.file_format = 'PNG'
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("PKG_SAVED", OUT, os.path.getsize(OUT) // 2 ** 20, "MB", "frames", sc.frame_start, sc.frame_end)
