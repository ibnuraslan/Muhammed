"""Render the steward's photograph (beat 1 view of the berg) and pack it into every print material.
blender -b anim.blend --python 04_make_photo.py -- <work_dir> <out.blend>
Step 1 renders <work_dir>/photo_raw.png from the bellows camera's viewpoint (frame 112, the shutter click),
step 2 tones it like a 1912 print (sepia, red streak kept, grain, vignette, paper border) with PIL if available
(Blender's bundled Python has numpy; we do the toning with numpy), then loads it as image 'Photo_Iceberg' and packs it."""
import sys, os, math
import bpy, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; WD, OUT = a[0], a[1]
sc = bpy.context.scene; O = bpy.data.objects
sc.frame_set(112)
bc = O["bcamera"]; p = bc.matrix_world.translation.copy()
pc = bpy.data.objects.new("PhotoCam", bpy.data.cameras.new("PhotoCam")); sc.collection.objects.link(pc)
tgt = Vector((0.0, -5.0, 7.0))
pc.location = p + (tgt - p).normalized() * 0.4
pc.rotation_euler = (tgt - p).to_track_quat('-Z', 'Y').to_euler(); pc.data.lens = 42; pc.data.sensor_width = 36
main = sc.camera; sc.camera = pc
hidden = [o for o in O if o.name.startswith(("Steward", "bcamera", "Rail_", "Deck_", "Porthole", "Deckhand", "deckchair", "lifebuoy", "crate", "Rope"))]
for o in hidden: o.hide_render = True
rx, ry = sc.render.resolution_x, sc.render.resolution_y
sc.render.resolution_x, sc.render.resolution_y = 720, 540
SMP, MB = sc.cycles.samples, sc.render.use_motion_blur
sc.cycles.samples = 24; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'PNG'
raw = os.path.join(WD, "photo_raw.png"); sc.render.filepath = raw
bpy.ops.render.render(write_still=True)
for o in hidden: o.hide_render = False
sc.camera = main; sc.render.resolution_x, sc.render.resolution_y = rx, ry
sc.cycles.samples, sc.render.use_motion_blur = SMP, MB
bpy.data.objects.remove(pc, do_unlink=True)

im = bpy.data.images.load(raw); w, h = im.size
px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, :3]
lum = px @ np.array([0.3, 0.59, 0.11], dtype=np.float32)
lum = np.clip((lum - 0.05) * 1.25, 0, 1) ** 1.1
sep = np.stack([lum * 1.0, lum * 0.86, lum * 0.66], -1)
redness = np.clip((px[:, :, 0] - 0.5 * (px[:, :, 1] + px[:, :, 2])) * 6.0, 0, 1)[..., None]
streak = np.stack([lum * 0.75, lum * 0.18, lum * 0.12], -1)
out = sep * (1 - redness) + streak * redness
rng = np.random.default_rng(35); out += rng.normal(0, 0.03, out.shape[:2])[..., None]
yy, xx = np.mgrid[0:h, 0:w]; r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
out *= np.clip(1.15 - 0.45 * r ** 2, 0, 1)[..., None]
b = 22; paper = np.array([0.86, 0.82, 0.72], dtype=np.float32)
out[:b, :] = paper; out[-b:, :] = paper; out[:, :b] = paper; out[:, -b:] = paper
out = np.clip(out, 0, 1)
img = bpy.data.images["Photo_Iceberg"]; img.scale(w, h)
rgba = np.concatenate([out, np.ones((h, w, 1), np.float32)], -1)
img.pixels.foreach_set(rgba.ravel()); img.filepath_raw = os.path.join(WD, "photo_print.png"); img.file_format = 'PNG'; img.save(); img.pack()
bpy.data.images.remove(im)
print("PHOTO", w, h)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
