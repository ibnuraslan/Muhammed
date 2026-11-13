"""Slim one baked shot file for delivery (the look does not change):
 1. identical meshes (same geometry hash) are shared: scanned trees and props were imported once per copy, each with
    its own 1-2 M vertex mesh; every object keeps its own materials (slots switched to OBJECT before sharing);
 2. packed images move to the shared texture folder (below).
  python edit/slim_shot.py <shot.blend> [max_px=2048]
Every packed image is written once to out/blend/textures/<sha1>_<name>.<ext> (deduplicated by content across all
shots), downscaled to max_px on its long side if larger; the shot then refers to it by a relative path. Fonts stay
packed. The shot is saved compressed. Prints [tex] lines."""
import os, sys, hashlib, re
import bpy
f = os.path.abspath(sys.argv[1]); MAXPX = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
TEX = os.path.join(os.path.dirname(os.path.dirname(f)), "textures"); os.makedirs(TEX, exist_ok=True)
EXT = {'PNG': '.png', 'JPEG': '.jpg', 'OPEN_EXR': '.exr', 'HDR': '.hdr', 'TIFF': '.tif', 'TARGA': '.tga', 'BMP': '.bmp', 'WEBP': '.webp'}
bpy.ops.wm.open_mainfile(filepath=f)
import numpy as np
canon = {}; shared = 0
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.data and o.data.users >= 1]:
    me = o.data
    if me.shape_keys or len(me.vertices) < 2000:
        continue
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)
    key = (len(me.vertices), len(me.polygons), hashlib.sha1(co.tobytes() + lv.tobytes()).hexdigest())
    c = canon.setdefault(key, me)
    if c is me:
        continue
    mats = [s.material for s in o.material_slots]
    for s_, m_ in zip(o.material_slots, mats):                   # keep this object's own materials
        s_.link = 'OBJECT'; s_.material = m_
    o.data = c; shared += 1
    if len(c.materials) < len(mats):
        pass
for me in [m for m in bpy.data.meshes if m.users == 0]:
    bpy.data.meshes.remove(me)
print(f"[mesh] {shared} objects now share a mesh", flush=True)
new = reused = scaled = 0
for im in list(bpy.data.images):
    if not im.packed_file or im.source != 'FILE':
        continue
    data = bytes(im.packed_file.data)
    h = hashlib.sha1(data).hexdigest()[:16]
    ext = EXT.get(im.file_format) or os.path.splitext(im.filepath)[1].lower() or ".png"
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", os.path.splitext(os.path.basename(im.name))[0])[:60]
    target = os.path.join(TEX, f"{h}_{base}{ext}")
    if not os.path.exists(target):
        tmp = target + f".{os.getpid()}.part"
        open(tmp, "wb").write(data)
        w, hgt = im.size[:]
        if max(w, hgt) > MAXPX:                                  # downscale on its own copy, keep format and colour data
            k = MAXPX / max(w, hgt)
            im2 = bpy.data.images.load(tmp, check_existing=False)
            im2.colorspace_settings.name = im.colorspace_settings.name
            im2.scale(max(1, int(w * k)), max(1, int(hgt * k)))
            tmp2 = target + f".{os.getpid()}{ext}"                    # unique per process; two workers may meet here
            im2.filepath_raw = tmp2; im2.file_format = im.file_format
            im2.save(); bpy.data.images.remove(im2); os.remove(tmp); os.replace(tmp2, target); scaled += 1
        else:
            os.replace(tmp, target)
        new += 1
    else:
        reused += 1
    cs = im.colorspace_settings.name; am = im.alpha_mode
    im.unpack(method='REMOVE')
    im.filepath = bpy.path.relpath(target)                       # //../textures/...
    im.colorspace_settings.name = cs; im.alpha_mode = am
    im.reload()
    if not im.has_data and im.size[0] == 0:
        print("[tex] WARNING could not load", target, flush=True)
bpy.ops.wm.save_mainfile(filepath=f, compress=True)
if os.path.exists(f + "1"):
    os.remove(f + "1")
print(f"[tex] {os.path.basename(f)}: {new} new ({scaled} downscaled), {reused} shared, {os.path.getsize(f) / 2**20:.1f} MB", flush=True)
