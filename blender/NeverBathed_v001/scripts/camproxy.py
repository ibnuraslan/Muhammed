"""Run a pipeline check on a hard-cut film (one camera per shot, bound by timeline markers).
qa_check / clip_scan / limb_check read sc.camera ONCE at start; this wrapper gives them a proxy camera that copies the
marker-bound shot camera (matrix, lens, sensor) on every frame change, then execs the check with the same argv.
CHECK=/path/to/check.py blender -b film.blend --python camproxy.py -- <the check's own args>"""
import bpy, os
sc = bpy.context.scene
mk = sorted([(m.frame, m.camera) for m in sc.timeline_markers if m.camera], key=lambda t: t[0])
def shot_cam(f):
    c = mk[0][1]
    for fr, cam in mk:
        if fr <= f: c = cam
    return c
cd = bpy.data.cameras.new("QA_PROXY"); proxy = bpy.data.objects.new("QA_PROXY", cd); sc.collection.objects.link(proxy)
def follow(scene, *a):
    c = shot_cam(scene.frame_current)
    proxy.matrix_world = c.matrix_world.copy(); cd.lens = c.data.lens; cd.sensor_width = c.data.sensor_width
    cd.sensor_fit = c.data.sensor_fit; cd.clip_start = c.data.clip_start; cd.clip_end = c.data.clip_end
bpy.app.handlers.frame_change_post.append(follow)
for m in sc.timeline_markers: m.camera = None          # the checks see one (proxy) camera; CAMJUMP then reports the cuts as teleports
sc.camera = proxy; sc.frame_set(sc.frame_start)
exec(compile(open(os.environ["CHECK"]).read(), os.environ["CHECK"], "exec"), {"__name__": "__main__"})
