"""v009j (director): at about 1790-1816 his right hand reaches the yoke with an open flat palm. Once it arrives the fingers
close round the horn (hand_poses 'wrap_grip'). blender -b film.blend --python 13_v009j_yoke_grip.py -- out.blend"""
import sys, os, bpy
out = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())
YOU = bpy.data.objects["YOU"]
for f in range(1796, 1841, 4):
    apply_pose(YOU, "R", "wrap_grip", f)
print("GRIP13 keyed wrap_grip R 1796-1840")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
