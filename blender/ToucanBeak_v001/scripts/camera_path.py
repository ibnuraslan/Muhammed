"""Dump the camera path and draw a top + side plot coloured by beat.  blender -b film.blend -P camera_path.py -- out.png"""
import bpy, sys, json, os
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene; cam = sc.camera; pts = []
for f in range(sc.frame_start, sc.frame_end + 1, 2):
    sc.frame_set(f); pts.append((f,) + tuple(cam.matrix_world.translation))
beats = json.load(open(os.path.join(os.path.dirname(bpy.data.filepath), '..', 'beats.json')))
json.dump({'pts': pts, 'beats': beats}, open(out + '.json', 'w'))
print('DUMPED')
