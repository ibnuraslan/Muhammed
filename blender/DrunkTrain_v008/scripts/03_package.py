"""DrunkTrain v008 stage C: pack everything into the delivered .blend (factory-startup safe).
blender -b b.blend --python 03_package.py -- <pkg_dir>"""
import bpy, sys, os, re
pkg = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
name = "DrunkTrain_v008"
vo = os.path.join(pkg, name + "_VO.mp3")
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
for s_ in list(strips):
    if s_.type == 'SOUND': s_.sound.filepath = vo
for o in bpy.data.objects:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
sc.render.filepath = "//render/" + name + "_####.png"; sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 1735
first = {}
for im in list(bpy.data.images):
    key = re.sub(r"\.\d{3}$", "", im.name)
    if key in first and im.size[:] == first[key].size[:]:
        im.user_remap(first[key]); bpy.data.images.remove(im)
    else:
        first.setdefault(key, im)
KEEP2K = ("young_caucasian_male", "man_tee_diffuse", "short02", "eyebrow", "eyelash")
for im in bpy.data.images:
    if im.size[0] == 0 or im.type != 'IMAGE': continue
    big = max(im.size)
    if any(k in im.name for k in KEEP2K): tgt = min(big, 2048)
    elif im.name.startswith(("shrub", "tree_small", "Image")): tgt = 512
    else: tgt = min(big, 1024)
    if big > tgt:
        im.scale(int(im.size[0] * tgt / big), int(im.size[1] * tgt / big)); im.pack()
        print("SHRUNK", im.name, tgt)
# background tree: render only its LOD1 meshes (the LOD0 copy doubled the tree and weighed 1.75 M vertices)
for o in list(bpy.data.objects):
    if o.name.startswith("tree_small_02") and o.name.endswith("_LOD0"):
        bpy.data.objects.remove(o, do_unlink=True)
# 16-bit / float data maps (height, normal, alpha, mask) -> 8-bit buffers, so the packed file stays small
for im in list(bpy.data.images):
    if im.type != 'IMAGE' or im.size[0] == 0 or not im.is_float: continue
    w, h = im.size; px = [0.0] * (w * h * 4); im.pixels.foreach_get(px)
    nw = bpy.data.images.new(im.name + "_8bit", w, h, alpha=True, float_buffer=False)
    nw.colorspace_settings.name = im.colorspace_settings.name; nw.alpha_mode = im.alpha_mode
    nw.pixels.foreach_set(px); nw.pack(); im.user_remap(nw); bpy.data.images.remove(im)
    print("TO8BIT", nw.name)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.ops.file.pack_all()
for snd in bpy.data.sounds:
    if not snd.packed_file: snd.pack()
out = os.path.join(pkg, name + "_60fps.blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("PACKED", out, os.path.getsize(out) // 1e6, "MB")
