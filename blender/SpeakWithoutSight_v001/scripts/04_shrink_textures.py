"""Re-encode opaque textures as JPEG (q92) so the packed farm file stays under ~150 MB; alpha textures (hair, leaves, lashes, brows) stay PNG.
blender -b anim.blend --python 04_shrink_textures.py -- <tmp_dir> <out.blend>"""
import sys, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
TMP, OUT = a[0], a[1]; os.makedirs(TMP, exist_ok=True)
KEEP = ("hair", "ponytail", "braid", "long01", "short0", "bob0", "leaves", "eyelash", "eyebrow", "lashes", "brow", "flame", "glass")
HERO = ("young_lightskinned_female_diffuse",)      # the girl's and teacher's faces carry the macros: keep these 2K
# bake the MPFB phenotype shape keys into the meshes (they are static) - big saving
for ob in bpy.data.objects:
    if ob.type == 'MESH' and ob.data.shape_keys:
        bpy.context.view_layer.objects.active = ob
        for o_ in bpy.context.selected_objects: o_.select_set(False)
        ob.select_set(True)
        try:
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
        except Exception as e:
            print("SK_FAIL", ob.name, e)
# decimate huge background meshes (the outside tree's 1.2M-vertex base) - seen only through the window
for me in list(bpy.data.meshes):
    if len(me.vertices) < 300000: continue
    tmp = bpy.data.objects.new("_dec", me); bpy.context.scene.collection.objects.link(tmp)
    dm = tmp.modifiers.new("D", 'DECIMATE'); dm.ratio = 0.06
    dg = bpy.context.evaluated_depsgraph_get(); new = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    print("DECIMATE", me.name, len(me.vertices), "->", len(new.vertices))
    me.user_remap(new); bpy.data.objects.remove(tmp); new.name = me.name + "_dec"
n = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or not im.filepath: continue
    p = bpy.path.abspath(im.filepath); low = (im.name + p).lower()
    if p.lower().endswith((".hdr", ".exr")) and "nor_gl" not in low and "rough" not in low: continue
    if any(k in low for k in KEEP):
        if max(im.size) > 1024:            # alpha textures: keep PNG, but 1K
            try:
                im.reload(); im.scale(1024, 1024); im.filepath_raw = os.path.join(TMP, "%03d_%s.png" % (n, bpy.path.clean_name(im.name))); im.file_format = 'PNG'; im.save(); im.filepath = im.filepath_raw; im.reload(); n += 1
            except Exception as e: print("SKIP", im.name, e)
        continue
    if p.lower().endswith((".jpg", ".jpeg")) and im.size[0] <= 1024: continue
    try:
        im.reload(); _ = im.pixels[0]
    except Exception as e:
        print("SKIP", im.name, e); continue
    cs = im.colorspace_settings.name
    if max(im.size) > 1024 and not any(h in im.name for h in HERO):
        im.scale(1024, max(1, round(1024 * im.size[1] / im.size[0])))
    out = os.path.join(TMP, "%03d_%s.jpg" % (n, bpy.path.clean_name(os.path.splitext(im.name)[0])))
    im.filepath_raw = out; im.file_format = 'JPEG'
    sc = bpy.context.scene; sc.render.image_settings.quality = 92
    try:
        im.save(quality=92) if 'quality' in im.save.__doc__ else im.save()
    except TypeError:
        im.save()
    im.filepath = out; im.reload(); im.colorspace_settings.name = cs; im.alpha_mode = 'NONE'; n += 1
print("SHRUNK", n)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
