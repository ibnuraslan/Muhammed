"""Pre-package: farm settings + texture sizes so the packed file stays under 95 MB. blender -b in.blend -P 04_shrink.py -- out.blend
Images are scaled in memory and re-packed as PNG (alpha kept, LESSONS §3: never save_render)."""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cy = sc.cycles
cy.samples = 48; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05; cy.use_denoising = True
n = 0; saved = 0
for im in bpy.data.images:
    if im.source != 'FILE' or im.size[0] == 0 or im.name.endswith(".hdr") or im.file_format == 'HDR': continue
    w, h = im.size
    lim = 512 if im.name.startswith("Image_") else 1024
    if max(w, h) <= lim: continue
    k = lim / max(w, h); im.scale(max(1, int(w * k)), max(1, int(h * k)))
    im.pack(); n += 1
print("SHRINK images scaled", n, "samples", cy.samples, "thr", cy.adaptive_threshold)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
