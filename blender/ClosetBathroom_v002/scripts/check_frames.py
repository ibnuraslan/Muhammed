"""render first / middle / last frame of every shot (or given frames) at 270x480, Cycles 8 spp.
blender -b film.blend --python check_frames.py -- OUT_DIR [shots.json] [w] [frames,...]"""
import bpy, sys, json, os
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; os.makedirs(out, exist_ok=True)
shots = json.load(open(a[1] if len(a) > 1 and a[1] != "-" else "/home/user/Muhammed/blender/ClosetBathroom_v002/shots_provisional.json"))
W = int(a[2]) if len(a) > 2 else 270
sc = bpy.context.scene; r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = W, round(W * 16 / 9), 100
sc.cycles.samples = 8; sc.cycles.use_denoising = True; r.image_settings.file_format = 'JPEG'
frames = []
if len(a) > 3: frames = [int(x) for x in a[3].split(",")]
else:
    for s in shots: frames += [s["f0"], (s["f0"] + s["f1"]) // 2, s["f1"]]
for f in frames:
    sc.frame_set(f); r.filepath = os.path.join(out, "f%04d.jpg" % f); bpy.ops.render.render(write_still=True)
print("CHECK_DONE", len(frames))
