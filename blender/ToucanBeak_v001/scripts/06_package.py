"""Shrink + pack for the farm (normal git file, < 95 MB, no LFS).
blender -b work/look.blend -P 06_package.py -- <out.blend>
- every image capped at 1024 px (MPFB skin maps are 2-4K), re-encoded as JPEG (PNG where alpha is used), duplicates merged
- orphans purged, helpers hidden from render, farm settings (1080x1920, 60 fps, Cycles 48 spp / 0.05 / OIDN, AgX Punchy)
- then pipeline/package_for_farm.py does pack_all + checks + compressed save"""
import bpy, sys, os, tempfile
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
tmp = tempfile.mkdtemp(prefix="pk_")
# images whose alpha drives a material (leaf cut-outs) must stay PNG
alpha_used = set()
for m in bpy.data.materials:
    if m.node_tree:
        for nd in m.node_tree.nodes:
            if nd.type == 'TEX_IMAGE' and nd.image and nd.outputs["Alpha"].is_linked: alpha_used.add(nd.image.name)
# de-duplicate identical source files (pbr() loaded some textures once per material)
by_path = {}
for m in bpy.data.materials:
    if not m.node_tree: continue
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.image and nd.image.filepath and not nd.image.packed_file:
            k = (bpy.path.abspath(nd.image.filepath), nd.image.colorspace_settings.name)
            if k in by_path and by_path[k] != nd.image: nd.image = by_path[k]
            else: by_path[k] = nd.image
KEEP1K = set()
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(("Toucan", "Prosthetic", "VetA", "VetB", "Assist", "BG_Toucan")):
        for m in o.data.materials:
            if m and m.node_tree:
                for nd in m.node_tree.nodes:
                    if nd.type == 'TEX_IMAGE' and nd.image: KEEP1K.add(nd.image.name)
n = 0
for im in list(bpy.data.images):
    if im.users == 0 or im.source != 'FILE' or im.name.startswith("forest_slope"): continue
    try: w, h = im.size
    except Exception: continue
    if w == 0: continue
    cap = 1024 if im.name in KEEP1K else 512
    if max(w, h) > cap:
        k = cap / max(w, h); im.scale(max(1, int(w * k)), max(1, int(h * k)))
    cs = im.colorspace_settings.name
    png = im.name in alpha_used
    p = os.path.join(tmp, "img_%03d.%s" % (n, "png" if png else "jpg")); n += 1
    im.filepath_raw = p; im.file_format = 'PNG' if png else 'JPEG'
    try: im.save()
    except Exception as e: print("SKIP", im.name, e); continue
    if im.packed_file: im.unpack(method='REMOVE') if False else None
    im.filepath = p; im.source = 'FILE'; im.reload(); im.colorspace_settings.name = cs
    if im.packed_file:
        try: im.unpack(method='USE_ORIGINAL')
        except Exception: pass
for o in bpy.data.objects:
    if o.type == 'EMPTY' or o.name in ("Extrude_cutter", "Print_clip", "Laser_line"):
        o.hide_render = True
for c in [o for o in bpy.data.objects if o.type == 'CAMERA' and o != sc.camera]:
    bpy.data.objects.remove(c)

# ---- de-duplicate repeated imports (same mesh / same image imported several times)
import re, hashlib
def base(n): return re.sub(r"\.\d{3}$", "", n)
seen = {}
for o in bpy.data.objects:
    if o.type != 'MESH' or o.modifiers and any(m.type in ('ARMATURE', 'NODES', 'PARTICLE_SYSTEM') for m in o.modifiers): continue
    me = o.data; k = (base(me.name), len(me.vertices), len(me.polygons), tuple(m.name if m else '' for m in me.materials))
    if k in seen and seen[k] != me: o.data = seen[k]
    else: seen[k] = me
imh = {}
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    try: px = im.pixels[:4096:7]
    except Exception: continue
    k = (tuple(im.size), hashlib.md5(str([round(x, 3) for x in px]).encode()).hexdigest(), im.colorspace_settings.name)
    if k in imh: im.user_remap(imh[k])
    else: imh[k] = im
# ---- decimate heavy static background props (cabinets, printer frame, bottles, plants), never the hero bird / people
HERO = ("Toucan", "Prosthetic", "Ghost", "Hollow", "Printing", "Scan_", "Ref_", "New_half", "BG_", "Vet", "Assist", "Beak", "Fig")
done = set()
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name.startswith(HERO) or o.data in done: continue
    if len(o.modifiers): continue            # displaced/subdivided/rigged geometry keeps its stack
    if len(o.data.vertices) > 25000:
        n0 = len(o.data.vertices); r_ = max(0.15, 20000 / n0)
        bm_ = __import__("bmesh").new(); bm_.from_mesh(o.data)
        __import__("bmesh").ops.triangulate(bm_, faces=bm_.faces[:]); bm_.to_mesh(o.data); bm_.free()
        d = o.modifiers.new("dec", 'DECIMATE'); d.ratio = r_
        dg = bpy.context.evaluated_depsgraph_get(); me2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        o.modifiers.remove(d); old = o.data
        for u in [x for x in bpy.data.objects if x.data == old]: u.data = me2
        done.add(me2); print("DECIMATED", o.name, n0, "->", len(me2.vertices))
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = 60; r.fps_base = 1.0; r.engine = 'CYCLES'; sc.frame_start, sc.frame_end = 1, 2250
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.device = 'CPU'; r.image_settings.file_format = 'PNG'
print("RESIZED", n)
sys.argv = [sys.argv[0], "--", out]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline", "package_for_farm.py")).read())
