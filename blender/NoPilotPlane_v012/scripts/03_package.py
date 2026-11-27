"""NoPilotPlane v012 stage C: pack everything into the delivered .blend (factory-startup safe).
blender -b b.blend --python 03_package.py -- <pkg_dir>"""
import bpy, sys, os, re
pkg = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
name = "NoPilotPlane_v012"
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
sc.frame_start, sc.frame_end = 1, 3481
# render budget (<= 120 s/frame on a 4-core CPU, measured): adaptive 14 samples + OIDN, short light paths, no caustics
c = sc.cycles
c.samples, c.use_adaptive_sampling, c.adaptive_threshold = 14, True, 0.1
c.use_denoising, c.denoiser = True, 'OPENIMAGEDENOISE'
c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.transparent_max_bounces = 3, 1, 1, 4, 8
c.caustics_reflective = c.caustics_refractive = False
sc.render.use_persistent_data = True
# de-duplicate images loaded once per character (same file), then shrink: the hero's skin/tee/hair 2048, the rest 1024
first = {}
for im in list(bpy.data.images):
    key = re.sub(r"\.\d{3}$", "", im.name)
    if key in first and im.size[:] == first[key].size[:] and im.filepath == first[key].filepath:
        im.user_remap(first[key]); bpy.data.images.remove(im)
    else:
        first.setdefault(key, im)
def imgs_of(prefixes):
    out = set()
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(prefixes):
            for m in o.data.materials:
                if m and m.use_nodes:
                    for n in m.node_tree.nodes:
                        if n.type == 'TEX_IMAGE' and n.image: out.add(n.image.name)
    return out
hero_imgs = imgs_of(("HERO.",)) - {i.name for i in bpy.data.images if "teeth" in i.name or "_ao" in i.name}
crew_imgs = imgs_of(("CAPT.", "FO."))
for im in bpy.data.images:
    if im.size[0] == 0: continue
    big = max(im.size)
    keep = im.name in hero_imgs or "logo" in im.name or "eyebrow" in im.name or "eyelash" in im.name
    tgt = min(big, 2048) if keep else min(big, 1024) if (im.name in crew_imgs or not any(im.name in imgs_of((p,)) for p in ("PAX",))) else min(big, 512)
    if "teeth" in im.name or "tongue" in im.name or "_ao" in im.name: tgt = min(big, 512)
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
