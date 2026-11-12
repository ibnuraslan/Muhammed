"""Shrink for a <95 MB normal-git package: textures to 1K (2K kept for the HDRI and hero robe/marble), decimate heavy
background meshes, apply farm settings, purge orphans. Then run pipeline/package_for_farm.py on the result.
blender -b PopeShot_anim.blend --python 04_prepare_package.py -- <out_prepared.blend>"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
KEEP2K = ("kloppenheim", "marble_01")
import os, re
TMP = os.path.join(os.path.dirname(os.path.abspath(out)), "_jpg"); os.makedirs(TMP, exist_ok=True)
def jp(im):
    """write the (scaled) pixels as a JPEG file, then pack that file"""
    fn = os.path.join(TMP, re.sub(r"[^A-Za-z0-9_]", "_", im.name) + ".jpg")
    im.filepath_raw = fn; im.file_format = 'JPEG'
    sc.render.image_settings.quality = 82
    im.save()
    im.source = 'FILE'; im.filepath = fn; im.reload(); im.pack()
n = 0
for im in list(bpy.data.images):
    if im.source not in ('FILE',) or not im.has_data and not im.filepath: continue
    try:
        w, h = im.size
    except Exception:
        continue
    hero = any(k in im.name.lower() for k in ("kloppenheim", "marble", "old_caucasian_male", "elegantsuit", "rough_linen"))
    lim = 2048 if "kloppenheim" in im.name else 1024 if hero else 384
    if im.name.endswith(".hdr"):
        continue
    s = min(1.0, lim / max(w, h)); nw, nh = max(1, int(w * s)), max(1, int(h * s)); im.scale(nw, nh); n += 1   # always re-encode
    if im.is_float:      # EXR maps -> 8-bit JPEG (normals/roughness are fine at 8 bit)
        b = bpy.data.images.new(im.name + "_8b", nw, nh, alpha=False, float_buffer=False)
        b.colorspace_settings.name = im.colorspace_settings.name
        px = list(im.pixels); b.pixels = [min(1.0, max(0.0, v)) for v in px]
        im.user_remap(b); im = b
    jp(im)
print("RESIZED", n)
# bake MPFB shape keys into the meshes (smaller file, same look)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.data.shape_keys:
        import numpy as np
        kbs = o.data.shape_keys.key_blocks; n_ = len(o.data.vertices)
        base = np.empty(n_ * 3, dtype=np.float32); kbs[0].data.foreach_get("co", base); mix = base.copy()
        for kb in kbs[1:]:
            if kb.mute or kb.value == 0: continue
            c = np.empty(n_ * 3, dtype=np.float32); kb.data.foreach_get("co", c); mix += kb.value * (c - base)
        o.shape_key_clear(); o.data.vertices.foreach_set("co", mix); o.data.update()
# heavy meshes that are only seen at mid distance
for nm, ratio in (("aorta", 0.35), ("orlamp", 0.4), ("optable", 0.3), ("candles", 0.5), ("guts", 0.6), ("monitor", 0.6)):
    o = bpy.data.objects.get(nm)
    if o and not any(m.type == 'DECIMATE' for m in o.modifiers):
        d = o.modifiers.new("dec", 'DECIMATE'); d.ratio = ratio
sc.render.image_settings.quality = 85
dg = bpy.context.evaluated_depsgraph_get()
for o in [o for o in bpy.data.objects if o.type == 'MESH' and any(m.type == 'DECIMATE' for m in o.modifiers)]:
    ev_ = o.evaluated_get(dg); nm_ = bpy.data.meshes.new_from_object(ev_)
    old = o.data; o.modifiers.clear(); o.data = nm_
    for other in [x for x in bpy.data.objects if x.data == old]: other.data = nm_
for o in [o for o in bpy.data.objects if o.name in ("spine",)]:
    bpy.data.objects.remove(o, do_unlink=True)
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0
r.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.cycles.texture_limit_render = 'OFF'
r.use_motion_blur = False   # animated look: no motion blur
r.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("PREPARED", out)
