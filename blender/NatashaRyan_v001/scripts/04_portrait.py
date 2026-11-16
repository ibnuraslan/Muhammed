"""render the school-photo portrait used on the memorial (our own render of the generic girl, S02 camera)
blender -b work/film.blend --python 04_portrait.py -- portrait.png"""
import bpy, sys
sc = bpy.context.scene; out = sys.argv[sys.argv.index("--") + 1]
sc.frame_set(215); sc.camera = bpy.data.objects["CAM_S02"]
sc.render.resolution_x, sc.render.resolution_y = 450, 600; sc.cycles.samples = 32
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = out; bpy.ops.render.render(write_still=True)
