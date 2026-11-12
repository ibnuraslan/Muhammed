"""blender -b work/humans.blend --python scripts/00_build.py -- <out.blend> [anim]"""
import sys, os, bpy
D = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("FC_ASSETS", os.path.join(D, "..", "assets"))
argv = sys.argv[sys.argv.index("--") + 1:]; SAVE_PATH = argv[0]; DO_ANIM = "anim" in argv
exec(open(os.path.join(D, "02_build_scene.py")).read())
if DO_ANIM:
    exec(open(os.path.join(D, "03_animate.py")).read())
    _argv = sys.argv; sys.argv = ["blender", "--"]
    exec(open(os.path.join(D, "..", "..", "pipeline", "anim_look.py")).read())
    sys.argv = _argv
    exec(open(os.path.join(D, "03c_look.py")).read())
    exec(open(os.path.join(D, "03d_hands.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH, compress=False)
print("SAVED", SAVE_PATH)
