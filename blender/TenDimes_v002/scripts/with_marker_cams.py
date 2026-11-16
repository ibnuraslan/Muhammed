"""Run a pipeline check with the camera switched by timeline markers on every frame_set (background frame_set does
not switch cameras, so checks would judge every shot through the first camera).
blender -b f.blend --python with_marker_cams.py -- <check.py> <check args...>"""
import bpy, sys
sc = bpy.context.scene
MS = sorted([m for m in sc.timeline_markers if m.camera], key=lambda m: m.frame)
def setcam(scene, *a):
    f = scene.frame_current; cam = None
    for m in MS:
        if m.frame <= f: cam = m.camera
    if cam is not None and scene.camera != cam: scene.camera = cam
bpy.app.handlers.frame_change_pre.append(setcam)
a = sys.argv[sys.argv.index("--") + 1:]
script = a[0]
sys.argv = [sys.argv[0], "--"] + a[1:]
exec(compile(open(script).read(), script, "exec"), {"__name__": "__main__", "__file__": script})
