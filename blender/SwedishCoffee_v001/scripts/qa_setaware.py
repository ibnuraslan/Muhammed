"""Run pipeline/qa_check.py unchanged, but first sync viewport visibility to render visibility on every frame change.
This film swaps sets with hide_render keys; qa_check ray-casts the viewport scene, so without this it 'sees' every hidden set.
blender -b film.blend --python qa_setaware.py -- out.json [step] [beats.json]"""
import bpy
def sync(scene, *a):
    for o in scene.objects:
        h = o.hide_render
        if o.hide_viewport != h: o.hide_viewport = h
bpy.app.handlers.frame_change_post.append(sync)
sync(bpy.context.scene)
exec(compile(open("/home/user/Muhammed/blender/pipeline/qa_check.py").read(), "qa_check.py", "exec"))
