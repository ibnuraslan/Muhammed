"""HeadsetBullet v009 stage C: pack everything into the delivered .blend (factory-startup safe).
blender -b b.blend --python 03_package.py -- <pkg_dir>"""
import bpy, sys, os
pkg = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
name = "HeadsetBullet_v009"
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
sc.frame_start, sc.frame_end = 1, 1203
# de-duplicate images appended twice (same file), then shrink background textures (alpha kept: Image.pack of the buffer)
import re
first = {}
for im in list(bpy.data.images):
    key = re.sub(r"\.\d{3}$", "", im.name)
    if key in first and im.size[:] == first[key].size[:]:
        im.user_remap(first[key]); bpy.data.images.remove(im)
    else:
        first.setdefault(key, im)
KEEP2K = ("young_caucasian_male_diffuse", "short02", "boy_tee_diffuse", "eyebrow", "eyelash", "logo_poster")
import tempfile
TMP = tempfile.mkdtemp()
for im in bpy.data.images:
    if im.size[0] == 0 or im.type != 'IMAGE': continue
    big = max(im.size)
    if any(k in im.name for k in KEEP2K): tgt = min(big, 2048)
    elif im.name.startswith(("potted_plant", "shrub", "island_tree", "decorative_book", "book_")): tgt = 512
    else: tgt = min(big, 1024)
    if big > tgt: im.scale(int(im.size[0] * tgt / big), int(im.size[1] * tgt / big))
    # write an 8-bit PNG (alpha kept, LESSONS 3) and pack that file, not the raw float buffer
    fn = os.path.join(TMP, "".join(c if c.isalnum() or c in "._-" else "_" for c in im.name))
    if not fn.lower().endswith(".png"): fn += ".png"
    im.filepath_raw = fn; im.file_format = 'PNG'; im.save()
    im.unpack(method='REMOVE') if im.packed_file else None
    im.filepath = fn; im.reload(); im.pack()
# very dense meshes (the Poly Haven tree and book set): decimated in place (they are far background)
dg = bpy.context.evaluated_depsgraph_get()
for o in list(bpy.data.objects):
    if o.type != 'MESH' or len(o.data.vertices) < 150000: continue
    n0 = len(o.data.vertices); md = o.modifiers.new("dec", 'DECIMATE'); md.ratio = max(0.08, 120000 / n0)
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.remove(md); old = o.data; o.data = me
    print("DECIMATED", o.name, n0, "->", len(me.vertices))
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.ops.file.pack_all()
for snd in bpy.data.sounds:
    if not snd.packed_file: snd.pack()
out = os.path.join(pkg, name + "_60fps.blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("PACKED", out, os.path.getsize(out) // 1e6, "MB")
