"""blender -b work/humans.blend --python scripts/00_build.py -- <out.blend> [anim]"""
import sys, os, bpy
D = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("FC_ASSETS", os.path.join(D, "..", "assets"))
argv = sys.argv[sys.argv.index("--") + 1:]
exec(open(os.path.join(D, "02_build_scene.py")).read())
if "anim" in argv:
    exec(open(os.path.join(D, "03_animate.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=argv[0], compress=False)
print("SAVED", argv[0])
