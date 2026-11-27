"""Tsunami2004 v013 stage C (from BellyFat v018 03_package.py): pack everything into the delivered .blend (factory-startup safe).
blender -b b.blend --python 03_package.py -- <pkg_dir>"""
import bpy, sys, os
pkg = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
name = "Tsunami2004_v013"
vo = os.path.join(pkg, name + "_VO.mp3")
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
for s_ in list(strips):
    if s_.type == 'SOUND':
        s_.sound.filepath = vo
for o in bpy.data.objects:                         # render-level subdivision kept; viewport off for speed
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
sc.render.filepath = "//render/" + name + "_####.png"; sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 2066
# render cost (director: <=120 s per 1080x1920 frame): adaptive sampling, fewer max samples, subdivision level 1
sc.cycles.samples = 28; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.06
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 1
# de-duplicate images appended twice (same file), then shrink background textures (alpha kept: Image.pack of the buffer)
import re
first = {}
for im in list(bpy.data.images):
    key = re.sub(r"\.\d{3}$", "", im.name)
    if key in first and im.size[:] == first[key].size[:]:
        im.user_remap(first[key]); bpy.data.images.remove(im)
    else:
        first.setdefault(key, im)
KEEP2K = ("young_asian", "boy_tee_diffuse", "mom_tee_diffuse", "girl_tee_diffuse", "DaKrasFilms", "eyebrow", "eyelash", "short02", "short04", "long01", "braid01")
for im in bpy.data.images:
    if im.size[0] == 0: continue
    big = max(im.size)
    if any(k in im.name for k in KEEP2K): tgt = min(big, 2048)
    elif not any(k in im.name.lower() for k in ("casualsuit", "skin", "eye", "teeth")): tgt = 512
    else: tgt = min(big, 1024)
    if big > tgt:
        im.scale(int(im.size[0] * tgt / big), int(im.size[1] * tgt / big)); im.pack()
        print("SHRUNK", im.name, tgt)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.ops.file.pack_all()
for snd in bpy.data.sounds:
    if not snd.packed_file: snd.pack()
out = os.path.join(pkg, name + "_60fps.blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("PACKED", out, os.path.getsize(out) // 1e6, "MB")
