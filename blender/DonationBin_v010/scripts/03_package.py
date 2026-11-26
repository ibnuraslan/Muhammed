"""DonationBin v010 stage C: VO strip, frame range, purge, then the farm package (pipeline/package_for_farm.py).
blender -b anim.blend --python 03_package.py -- <vo.mp3> <out_dir>/DonationBin_v010_60fps.blend"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]
VO, OUTB = a[0], a[1]
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 2388
# the client's voiceover from frame 1
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = se.strips if hasattr(se, "strips") else se.sequences
for s_ in list(strips): strips.remove(s_)
snd = strips.new_sound("VO", VO, 1, 1)
snd.sound.pack()
# helper objects never render; the temporary off-set copies are removed
for o in list(bpy.data.objects):
    if o.name in ("SparkInst",):
        o.hide_render = True
for m in bpy.data.objects:
    for md in getattr(m, "modifiers", []):
        if md.type == 'SUBSURF': md.show_viewport = True
# texture budget (package < 95 MB): nothing above 2048 px; the background people and helmet maps at 1024 px.
# Re-saved with Image.save() into a temp file (keeps alpha: no black hair cards), then re-packed.
import tempfile
TMP = tempfile.mkdtemp()
SMALL = ("young_lightskinned_male", "middleage_darkskinned_male", "short01", "short02", "braid01", "Scene_-_Root", "teeth", "tongue", "Polo", "shoes03")
for img in list(bpy.data.images):
    if img.source != 'FILE' or img.size[0] == 0: continue
    lim = 1024 if any(k in img.name for k in SMALL) else 2048
    if max(img.size) <= lim: continue
    w, h = img.size; k = lim / max(w, h)
    jpg = img.name.lower().endswith((".jpg", ".jpeg"))
    img.scale(int(w * k), int(h * k))
    path = os.path.join(TMP, os.path.splitext(img.name)[0] + (".jpg" if jpg else ".png"))
    img.filepath_raw = path; img.file_format = 'JPEG' if jpg else 'PNG'; img.save()
    if img.packed_file: img.unpack(method='REMOVE')
    img.filepath = path; img.reload(); img.pack()
    print("SHRUNK", img.name, (w, h), "->", tuple(img.size))
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
sys.argv = [sys.argv[0], "--", OUTB]
exec(open("/home/user/Muhammed/blender/pipeline/package_for_farm.py").read())
