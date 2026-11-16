"""Run a pipeline check shot by shot with that shot's own camera (our films cut between one camera per shot; the
pipeline checks read sc.camera once). Mask modifiers on MPFB bodies are applied first (the warrior's hands are
masked out; clip_scan/body_prop_cross otherwise see vertices that never render). Writes <prefix>_<shot>.json.
blender -b film.blend --python check_per_shot.py -- <pipeline script path> <out prefix> <step> [extra args...]"""
import bpy, bmesh, sys, os, json
a = sys.argv[sys.argv.index("--") + 1:]
SCRIPT, PREFIX, STEP, EXTRA = a[0], a[1], a[2], a[3:]
for body in [o for o in bpy.data.objects if o.type == 'MESH' and any(m.type == 'MASK' for m in o.modifiers)]:
    bm = bmesh.new(); bm.from_mesh(body.data); dl = bm.verts.layers.deform.active
    kill = set()
    for m in body.modifiers:
        if m.type != 'MASK' or not m.vertex_group or m.vertex_group not in body.vertex_groups or dl is None: continue
        gi = body.vertex_groups[m.vertex_group].index
        for v in bm.verts:
            if (gi in v[dl] and v[dl][gi] > m.threshold) == m.invert_vertex_group: kill.add(v)
    bmesh.ops.delete(bm, geom=list(kill), context='VERTS'); bm.to_mesh(body.data); bm.free()
    for m in body.modifiers:
        if m.type == 'MASK': m.show_viewport = False; m.show_render = False
sc = bpy.context.scene
shots = json.loads(sc["SHOTS_JSON"])
code = open(SCRIPT).read()
for name, f0, f1 in shots:
    sc.frame_start, sc.frame_end = f0, f1
    sc.frame_set(f0); sc.camera = bpy.data.objects["CAM_" + name]
    for m in list(sc.timeline_markers): pass
    sys.argv = [sys.argv[0], "--", "%s_%s.json" % (PREFIX, name), STEP] + EXTRA
    g = {"__name__": "__main__"}
    try: exec(code, g)
    except SystemExit: pass
    print("SHOT_DONE", name)
