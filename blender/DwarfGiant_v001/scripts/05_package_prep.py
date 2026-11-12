"""Shrink for a <95 MB normal-git package, set farm settings, then hand off to pipeline/package_for_farm.py.
blender -b film.blend --python 05_package_prep.py -- <out.blend>"""
import bpy, sys, os
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
# bake static MPFB shape keys (phenotype targets) into the mesh: same shape, a fraction of the size
import numpy as np
for ob in bpy.data.objects:
    me = ob.data if ob.type == "MESH" else None
    if not me or not me.shape_keys or me.users > 1: continue
    kb = me.shape_keys.key_blocks; n = len(me.vertices)
    if me.shape_keys.animation_data: continue
    base = np.empty(n * 3); kb[0].data.foreach_get("co", base); mix = base.copy()
    for k in kb[1:]:
        if k.mute or k.value == 0: continue
        c = np.empty(n * 3); k.data.foreach_get("co", c)
        ref = np.empty(n * 3); (k.relative_key or kb[0]).data.foreach_get("co", ref)
        mix += k.value * (c - ref)
    ob.shape_key_clear(); me.vertices.foreach_set("co", mix); me.update()
# thin the heavy tree twig/leaf mesh further
import bmesh, random
random.seed(7)
for me in bpy.data.meshes:
    if len(me.polygons) < 150000: continue
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); seen = set(); kill = []
    for f in bm.faces:
        if f.index in seen: continue
        isl = []; st = [f]; seen.add(f.index)
        while st:
            g = st.pop(); isl.append(g)
            for e in g.edges:
                for hh in e.link_faces:
                    if hh.index not in seen: seen.add(hh.index); st.append(hh)
        if len(isl) < 400 and random.random() > 0.55: kill += isl
    bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(me); bm.free(); print("THIN", me.name, len(me.polygons))
for im in bpy.data.images:          # 1K HDRI for the package (lighting only; never seen directly except through windows)
    if im.filepath.endswith("kloppenheim_06_2k.hdr"):
        im.filepath = im.filepath.replace("_2k.hdr", "_1k.hdr"); im.reload()
import tempfile
TMP = tempfile.mkdtemp(prefix="dg_tex_")
HERO_1K = ("young_lightskinned_male_diffuse",)        # hero face close-ups keep 1K skin, everything else 512
n = 0
for im in list(bpy.data.images):
    if im.source != "FILE" or im.filepath.lower().endswith(".hdr"): continue      # keep HDR lighting in float
    try:
        try: _ = im.pixels[0]          # force-load so size is known
        except Exception: pass
        if im.size[0] == 0: continue
        w, h = im.size
        lim = 1024 if any(k in im.name for k in HERO_1K) else 512
        f = min(1.0, lim / max(w, h))
        if f < 1.0: im.scale(max(1, int(w * f)), max(1, int(h * f)))
        alpha = im.alpha_mode != "NONE" and any(k in im.name.lower() for k in ("alpha", "leaves", "lash", "brow", "hair", "short", "bob"))
        ext = "png" if alpha else "jpg"
        path = f"{TMP}/{n:04d}.{ext}"; n += 1
        im.filepath_raw = path; im.file_format = "PNG" if alpha else "JPEG"
        sc.render.image_settings.quality = 82
        im.save(); im.reload(); im.pack()
    except Exception as e:
        print("IMG ERR", im.name, e)
print("IMAGES", n)
# farm render settings
r, cy = sc.render, sc.cycles
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0
r.engine = "CYCLES"; cy.device = "CPU"; cy.samples = 48; cy.adaptive_threshold = 0.05; cy.use_adaptive_sampling = True
cy.use_denoising = True; cy.denoiser = "OPENIMAGEDENOISE"; cy.texture_limit_render = "OFF"
r.use_motion_blur = False   # animated look: no motion blur
cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 8; cy.transparent_max_bounces = 16
cy.caustics_reflective = False; cy.caustics_refractive = False; r.use_persistent_data = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"; r.image_settings.color_depth = "8"
# hide every helper from render
for o in bpy.data.objects:
    if o.type == "EMPTY": o.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("PREP SAVED", out, os.path.getsize(out) // 2**20, "MB")
