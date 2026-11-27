"""DwarfGiant v009 stage B2: the framed photo on the wall is a real still of THIS film's opening (frame 20: the short
young man beside the officer), rendered with its own camera, toned sepia, and put into M_Photo.
blender -b b.blend --python 02b_photo.py -- <pkg_dir> <out.blend>"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
import numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
PKG, OUT = a[0], a[1]
sc = bpy.context.scene; O = bpy.data.objects
cd = bpy.data.cameras.new("CAM_PhotoTmp"); cam = bpy.data.objects.new("CAM_PhotoTmp", cd); sc.collection.objects.link(cam)
cd.lens = 50; cd.sensor_fit = 'AUTO'; cd.sensor_width = 36
p = Vector((0.45, -2.85, 1.00)); t = Vector((0.45, 0.0, 0.97))
z = (p - t).normalized(); x = Vector((0, 0, 1)).cross(z).normalized(); y = z.cross(x)
cam.matrix_world = Matrix((x, y, z)).transposed().to_4x4(); cam.location = p
old_cam = sc.camera; sc.camera = cam
r = sc.render; old = (r.resolution_x, r.resolution_y, r.filepath, r.image_settings.file_format, sc.cycles.samples, sc.frame_current)
r.resolution_x, r.resolution_y, r.resolution_percentage = 360, 480, 100
r.image_settings.file_format = 'PNG'; sc.cycles.samples = 48
tmp = os.path.join(PKG, "assets/tex/_photo_raw.png"); r.filepath = tmp
sc.frame_set(20); bpy.ops.render.render(write_still=True)
src = bpy.data.images.load(tmp); W, H = src.size
im = np.array(src.pixels[:], np.float32).reshape(H, W, 4)[..., :3]          # linear, bottom row first
lum = 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
sep = np.stack([lum * 1.10 + 0.02, lum * 0.82 + 0.012, lum * 0.50 + 0.004], -1)
yy, xx = np.mgrid[0:H, 0:W]
vig = 1.0 - 0.45 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
sep = np.clip(sep * vig[..., None], 0, 1)
sep[:10, :] = sep[-10:, :] = sep[:, :10] = sep[:, -10:] = np.array([0.80, 0.72, 0.55])    # cream photo border (linear)
dst = os.path.join(PKG, "assets/tex/photo_young.png")
out = bpy.data.images.new("photo_young", W, H); out.colorspace_settings.name = 'Linear Rec.709'
px = np.concatenate([sep, np.ones((H, W, 1), np.float32)], -1).ravel()
out.pixels[:] = px.tolist(); out.filepath_raw = dst; out.file_format = 'PNG'; out.save()
bpy.data.images.remove(src); os.remove(tmp)
bpy.data.images.remove(out)
m = bpy.data.materials["M_Photo"]; nt = m.node_tree
tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(dst); tx.extension = 'CLIP'
nt.links.new(tx.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
sc.camera = old_cam; bpy.data.objects.remove(cam, do_unlink=True)
r.resolution_x, r.resolution_y, r.filepath, r.image_settings.file_format, sc.cycles.samples, _ = old
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("PHOTO_DONE", dst)
