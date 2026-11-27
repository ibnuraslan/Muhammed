"""CaveRescue v012 stage C: package. blender -b film.blend --python 03_package.py -- <out.blend>
Textures: vegetation to 512 px, everything else to max 1024 px (the logo kept), re-saved as JPEG (PNG where alpha is
needed) and packed; orphans purged; compressed save."""
import bpy, sys, os, tempfile
OUT = sys.argv[sys.argv.index("--") + 1]
TMP = tempfile.mkdtemp(prefix="pkgimg_")
VEG = ("tree", "pachira", "fern", "boulder", "short0", "ponytail", "eyebrow", "eyelash", "image_")   # v012: hair cards + ambulance maps at 512 too
sc = bpy.context.scene
sc.render.image_settings.quality = 88
for i, im in enumerate(list(bpy.data.images)):
    if im.source != 'FILE' or "DaKras" in im.name: continue
    n = im.name.lower()
    if n.endswith(".hdr"): continue                       # v012: EXR roughness maps are converted too (were 2k, unshrunk)
    _ = im.pixels[0] if len(im.pixels) else None          # force load (packed images report size 0 until loaded)
    if im.size[0] == 0: print("SKIP", im.name); continue
    lim = 512 if any(k in n for k in VEG) else 1024
    if max(im.size) > lim:
        s = lim / max(im.size); im.scale(max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s)))
    alpha = any(k in n for k in ("leaves", "leaf", "alpha", "opacity", "fern", "lash", "brow", "short", "pony"))
    if any(k in n for k in ("nor_gl", "_nor", "rough", "disp", "normal", "spec", "_ao")): alpha = False   # data maps: no alpha needed
    if n.endswith(".exr"):
        im.colorspace_settings.name = "Non-Color"
    fn = os.path.join(TMP, "%03d.%s" % (i, "png" if alpha else "jpg"))
    im.filepath_raw = fn; im.file_format = 'PNG' if alpha else 'JPEG'
    im.save()
    if im.packed_file: im.unpack(method='REMOVE')
    im.filepath = fn; im.reload(); im.pack()
bpy.ops.file.pack_all()
# v012 farm settings (measured: <= 112 s per 1080x1920 frame on a 4-core CPU, see README)
cy = sc.cycles
cy.samples = 12; cy.adaptive_threshold = 0.08; cy.use_adaptive_sampling = True
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 3; cy.diffuse_bounces = 1; cy.glossy_bounces = 1; cy.transmission_bounces = 3; cy.transparent_max_bounces = 8
for m in bpy.data.materials:            # the underwater fog is a look, not a light: never sample it as an emitter
    if m.node_tree and any(n.type == 'GROUP' and n.node_tree and n.node_tree.name == "UW_Fog" for n in m.node_tree.nodes):
        m.cycles.emission_sampling = 'NONE'
for o in bpy.data.objects:              # clear water bodies / soft FX: camera + transmission rays only
    if o.name.startswith(("Water", "FX_Silt", "FX_Bub")):
        o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False
# no linked data on the farm: make every library datablock local (auto-smooth node group from Blender's essentials)
for coll in (bpy.data.node_groups, bpy.data.materials, bpy.data.objects, bpy.data.meshes):
    for idb in list(coll):
        if idb.library: idb.make_local()
for nm in [l.name for l in bpy.data.libraries]:
    lib = bpy.data.libraries.get(nm)
    if lib is not None: bpy.data.libraries.remove(lib)
for _ in range(3): bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
sc.render.filepath = "//render/CaveRescue_v012_####"; sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("PACKAGE_DONE", OUT)
