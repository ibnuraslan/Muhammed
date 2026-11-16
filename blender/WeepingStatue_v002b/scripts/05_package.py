"""Add the VO, shrink/pack textures, farm settings, save the package.
blender -b anim.blend --python 05_package.py -- <repo_root> <VO.mp3> <out.blend>"""
import sys, os, bpy, tempfile
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, VO, OUT = a
sc = bpy.context.scene
se = sc.sequence_editor_create()
coll = se.strips if hasattr(se, "strips") else se.sequences
for st in list(coll): coll.remove(st)
snd = coll.new_sound("VO", VO, 1, 1)
print("VO strip", snd.frame_final_start, snd.frame_final_end)
sc.render.ffmpeg.audio_codec = 'AAC' if hasattr(sc.render, "ffmpeg") else None
# remap textures to the asset folder (the build stored cwd-relative paths)
ASSETS = os.path.join(ROOT, "blender", "WeepingStatue_v001", "work", "assets")
INDEX = {}
for d_, _, fs_ in os.walk(ASSETS):
    for f_ in fs_: INDEX.setdefault(f_, os.path.join(d_, f_))
for im in bpy.data.images:
    if im.source != 'FILE' or im.packed_file: continue
    if not os.path.exists(bpy.path.abspath(im.filepath)):
        hit = INDEX.get(os.path.basename(im.filepath))
        if hit: im.filepath = hit; im.reload()
        else: print("MISSING", im.name, im.filepath)
# hair/brow/lash cards from the PopeShot package lost their alpha (JPEG): use the intact twin from Tsunami2004 (".001")
for m in bpy.data.materials:
    if not m.use_nodes: continue
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.image and not nd.image.name.endswith(".001"):
            tw = bpy.data.images.get(nd.image.name + ".001")
            if tw:
                try: amin = min(tw.pixels[3::4][:200000])
                except Exception: amin = 1.0
                if amin < 0.5: print("ALPHA_TWIN", m.name, nd.image.name, "->", tw.name); nd.image = tw
TMP = tempfile.mkdtemp(); nj = 0
for im in list(bpy.data.images):
    if im.source != 'FILE': continue
    try: w, h = im.size
    except Exception: continue
    if w == 0: continue
    if max(w, h) > 1024: im.scale(max(1, int(w * 1024 / max(w, h))), max(1, int(h * 1024 / max(w, h))))
    alpha = im.name.lower().find("alpha") >= 0 or "logo" in im.name.lower() or any(k in im.name.lower() for k in ("hair", "brow", "lash", "long01", "short", "leaves", "branches"))
    ext = ".png" if alpha else ".jpg"
    path = os.path.join(TMP, "%03d%s" % (nj, ext))
    try:
        im.filepath_raw = path; im.file_format = 'PNG' if alpha else 'JPEG'
        im.save()                                   # Image.save keeps alpha (save_render drops it: black hair cards)
        if im.packed_file: im.unpack(method='REMOVE')
        im.filepath = path; im.reload(); im.pack(); nj += 1
    except Exception as e:
        print("IMG skip", im.name, e)
print("IMAGES", nj)
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
sc.cycles.samples = 48; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.frame_start, sc.frame_end = 1, 1724
for m in list(sc.timeline_markers):
    m.camera = None
sys.argv = [sys.argv[0], "--", OUT]
exec(open(os.path.join(ROOT, "blender", "pipeline", "package_for_farm.py")).read())
