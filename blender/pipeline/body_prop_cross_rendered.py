"""body_prop_cross.py, but meshes hidden from render at a frame (e.g. firefighters parked out of sight before they arrive)
are skipped at that frame. The original builds its mesh list once, so hidden characters' coats were counted all film long.
Same arguments: blender -b film.blend --python body_prop_cross_rendered.py -- out.json STEP Prop1,Prop2,..."""
import bpy, sys, os
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "body_prop_cross.py")).read()
a = "    for c, lab in WEAR:\n"
assert src.count(a) == 1
src = src.replace(a, a + "        if c.hide_render or any(p.hide_render for p in [c.parent] if p is not None):\n            continue      # hidden at this frame (not rendered)\n")
exec(src)
