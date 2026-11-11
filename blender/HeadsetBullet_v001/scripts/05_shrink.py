"""Shrink for the <95 MB no-LFS package: 1K textures (2K for the face skin), 1K HDRI, opaque maps re-encoded as JPEG,
alpha maps as 8-bit PNG, orphans purged.  blender -b anim.blend --python 05_shrink.py -- <out.blend> <tmpdir>"""
import sys, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT, TMP = a[0], a[1]
os.makedirs(TMP, exist_ok=True)
HERO = ("young_lightskinned_male_diffuse", "young_caucasian_male")
n = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    hdr = im.name.lower().endswith((".hdr", ".exr")) and "nor" not in im.name.lower() and "rough" not in im.name.lower()
    lim = 2048 if any(h in im.name for h in HERO) else 1024
    w, h = im.size
    if w > lim: im.scale(lim, max(1, round(h * lim / w)))
    base = os.path.splitext(im.name)[0].replace(".", "_")
    if hdr:
        if im.size[0] > 1024: im.scale(1024, 512)
        p = os.path.join(TMP, base + ".hdr"); fmt = 'HDR'
    else:
        alpha = im.channels == 4 and any(k in im.name.lower() for k in ("alpha", "leaves", "branch", "eyelash", "brow", "hair", "short02"))
        p = os.path.join(TMP, base + (".png" if alpha else ".jpg")); fmt = 'PNG' if alpha else 'JPEG'
    sc = bpy.context.scene.render.image_settings
    im.filepath_raw = p; im.file_format = fmt
    s = bpy.context.scene
    s.render.image_settings.file_format = fmt
    if fmt == 'JPEG': s.render.image_settings.quality = 92
    if fmt == 'PNG': s.render.image_settings.color_depth = '8'; s.render.image_settings.compression = 90
    cs = im.colorspace_settings.name
    im.save_render(p, scene=s)
    if im.packed_file: im.unpack(method='REMOVE') if False else None
    im.filepath = p; im.source = 'FILE'; im.reload(); im.colorspace_settings.name = cs
    n += 1
bpy.context.scene.render.image_settings.file_format = 'PNG'; bpy.context.scene.render.image_settings.color_depth = '8'
bpy.context.scene.render.image_settings.compression = 15
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
print("SHRUNK", n)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
