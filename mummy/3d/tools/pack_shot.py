"""Farm packaging, step 1 (one Blender per shot): copy a built shot into the delivery folder so the folder renders
anywhere and stays small:
  - every image (external or packed) goes once into <PKG>/tex/, capped at 2K (1K for small/instanced detail maps),
  - every big static mesh (terrain, photogrammetry scans) is written ONCE into <PKG>/lib/<hash>.blend and linked
    from the shots that use it (identical meshes in different shots share one file),
  - scan stones instanced many times are decimated to what the camera can resolve,
  - unused data purged, saved compressed.

    blender -b shots/P1/S01.blend --python tools/pack_shot.py -- <PKG dir>
    -> <PKG>/shots/S01.blend, <PKG>/tex/*, <PKG>/lib/*.blend
"""
import os, sys, shutil, hashlib
import numpy as np
import bpy

PKG = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
SHOTS, TEX, LIB = os.path.join(PKG, "shots"), os.path.join(PKG, "tex"), os.path.join(PKG, "lib")
for d in (SHOTS, TEX, LIB):
    os.makedirs(d, exist_ok=True)
sid = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
sc = bpy.data.scenes[0]
sc.name = sid
missing = []
BIG = 40000                 # vertices: meshes above this are shared through lib/
INSTANCED_DECIMATE = (300000, 4, 0.2)     # > 300k verts used by >= 4 objects (scan stones): keep 20 % of the faces


def cap(src, dst, limit):
    """Copy an image, scaled down so its long side is at most `limit` (Blender's own image scaler)."""
    ext = os.path.splitext(dst)[1].lower()
    try:
        im = bpy.data.images.load(src, check_existing=False)
        w, h = im.size[:]
    except Exception:
        shutil.copy2(src, dst); return
    if max(w, h) > limit and ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
        f = limit / max(w, h)
        im.scale(max(1, int(w * f)), max(1, int(h * f)))
        im.filepath_raw = dst
        im.file_format = {".png": 'PNG', ".jpg": 'JPEG', ".jpeg": 'JPEG'}.get(ext, 'TIFF')
        im.save()
    else:
        shutil.copy2(src, dst)
    bpy.data.images.remove(im)


# 1. images -> tex/ (shared by every shot and lib file: both sit one folder below PKG, so "//../tex/x" works in both)
for im in bpy.data.images:
    if im.source not in ('FILE', 'SEQUENCE', 'MOVIE') or not (im.filepath or im.packed_file):
        continue
    if im.packed_file:
        data = im.packed_file.data
        h = hashlib.sha1(data).hexdigest()[:12]
        ext = os.path.splitext(im.filepath or "")[1] or (".png" if data[:4] == b"\x89PNG" else ".jpg")
        name = f"packed_{h}{ext}"
        dst = os.path.join(TEX, name)
        if not os.path.exists(dst):
            tmp = dst + ".tmp" + ext
            open(tmp, "wb").write(data)
            cap(tmp, dst, 2048); os.remove(tmp)
        im.unpack(method='REMOVE')
        im.filepath = "//../tex/" + name
        im.source = 'FILE'
        continue
    src = bpy.path.abspath(im.filepath, library=im.library)
    if not os.path.exists(src):
        missing.append(src); continue
    stem, ext = os.path.splitext(os.path.basename(src))
    name = f"{os.path.basename(os.path.dirname(src))}__{stem}{ext}"
    dst = os.path.join(TEX, name)
    if not os.path.exists(dst):
        cap(src, dst, 2048)
    im.filepath = "//../tex/" + name

# 2. decimate heavily instanced scan stones
users = {}
for o in bpy.data.objects:
    if o.type == 'MESH':
        users.setdefault(o.data, []).append(o)
for m, obs in users.items():
    nv, nu, ratio = INSTANCED_DECIMATE
    if len(m.vertices) > nv and len(obs) >= nu and not m.shape_keys:
        tmp = bpy.data.objects.new("_dec", m); sc.collection.objects.link(tmp)
        dm = tmp.modifiers.new("d", "DECIMATE"); dm.ratio = ratio; dm.use_collapse_triangulate = False
        bpy.context.view_layer.update()
        new = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        new.name = m.name + "_dec"
        for mat in m.materials:
            pass
        m.user_remap(new)
        bpy.data.objects.remove(tmp)
        print("DECIMATED", m.name, len(m.vertices), "->", len(new.vertices), flush=True)

# 3. big static meshes -> lib/<hash>.blend, linked back
deformed = set()
for o in bpy.data.objects:
    if o.type == 'MESH' and (o.vertex_groups or any(md.type in ('ARMATURE', 'MESH_DEFORM', 'SURFACE_DEFORM', 'LATTICE', 'HOOK') for md in o.modifiers)):
        deformed.add(o.data)
shared = 0
for m in list(bpy.data.meshes):
    if m.library or m.users == 0 or len(m.vertices) < BIG or m.shape_keys or m in deformed:
        continue
    co = np.empty(len(m.vertices) * 3, np.float32); m.vertices.foreach_get("co", co)
    lp = np.empty(len(m.loops), np.int32); m.loops.foreach_get("vertex_index", lp)
    hs = hashlib.sha1(co.tobytes()); hs.update(lp.tobytes())
    hs.update(",".join(mt.name if mt else "-" for mt in m.materials).encode())
    h = hs.hexdigest()[:16]
    path = os.path.join(LIB, f"mesh_{h}.blend")
    if not os.path.exists(path):
        bpy.data.libraries.write(path, {m}, path_remap='NONE', fake_user=True, compress=True)
    with bpy.data.libraries.load(path, link=True, relative=False) as (src, dst):
        dst.meshes = [m.name]
    lm = dst.meshes[0]
    lm.library.filepath = "//../lib/" + os.path.basename(path)
    m.user_remap(lm)
    bpy.data.meshes.remove(m)
    shared += 1

for lib in bpy.data.libraries:
    if not os.path.basename(lib.filepath).startswith("mesh_"):
        missing.append("LIBRARY " + lib.filepath)
for f in bpy.data.fonts:
    if f.filepath and f.filepath != "<builtin>" and not f.packed_file:
        f.pack()
for snd in bpy.data.sounds:
    if not snd.packed_file:
        snd.pack()
for _ in range(3):
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
out = os.path.join(SHOTS, sid + ".blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=False, copy=True)
print("PACKED", sid, out, "shared meshes:", shared, "missing:", missing, flush=True)
