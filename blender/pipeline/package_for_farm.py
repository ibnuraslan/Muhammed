"""Pack everything, check farm settings, save compressed.
blender -b film.blend --python package_for_farm.py -- <out_dir>/<Name>_v00N_60fps.blend
Then verify:  blender -b --factory-startup <that file> --python-expr "import bpy;print([i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file])" """
import sys, os
import bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
bpy.ops.file.pack_all()
for s in bpy.data.sounds:
    if not s.packed_file: s.pack()
r, cy = sc.render, sc.cycles
problems = []
if (r.resolution_x, r.resolution_y, r.resolution_percentage) != (1080, 1920, 100): problems.append("resolution")
if r.fps != 60 or r.fps_base != 1.0: problems.append("fps")
if r.engine != "CYCLES": problems.append("engine")
if [o for o in bpy.data.objects if o.type == "CAMERA"].__len__() != 1 or any(m.camera for m in sc.timeline_markers): problems.append("must be ONE camera, no camera markers")
if bpy.data.libraries: problems.append("linked libraries")
if [i.name for i in bpy.data.images if i.source == "FILE" and not i.packed_file]: problems.append("unpacked images")
base = os.path.splitext(os.path.basename(out))[0].replace("_60fps", "")
r.filepath = "//render/%s_" % base
print("FARM", dict(res=(r.resolution_x, r.resolution_y), fps=r.fps, frames=(sc.frame_start, sc.frame_end), samples=cy.samples,
                   thr=cy.adaptive_threshold, denoise=cy.use_denoising, mblur=(r.use_motion_blur, r.motion_blur_shutter),
                   view=(sc.view_settings.view_transform, sc.view_settings.look), fmt=r.image_settings.file_format, out=r.filepath))
print("PROBLEMS", problems or "none")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("SAVED", out, os.path.getsize(out) // 2**20, "MB")
