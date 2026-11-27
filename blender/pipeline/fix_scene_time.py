"""Make Scene-Time-driven effects follow a VO retime.

blender -b synced.blend --python blender/pipeline/fix_scene_time.py -- anchors.json [--audit]

A VO retime warps keyframes and markers, but Geometry Nodes that read the *Scene Time* node
(spray windows like "Seconds > 21.3", rain, ripples) keep running on the raw clock, so their
events fire at the wrong moment after the warp. This replaces every Scene Time node with Value
nodes keyed to the ORIGINAL timeline (old frame for the new frame, linear between anchors,
linear extrapolation), so every effect fires on the same picture it was built for.

anchors.json: {"anchors": [[old_frame, new_frame, ...], ...], "fps": 60}
--audit: only list other raw-clock time sources (frame drivers, particle and Build/Wave
modifier frame settings) that a retime does not move. They must be fixed by hand.
"""
import bpy, sys, json

a = sys.argv[sys.argv.index("--") + 1:]
AN = json.load(open(a[0]))
FPS = AN.get("fps", 60)
PAIRS = sorted({(int(x[1]), float(x[0])) for x in AN["anchors"]})   # (new, old)
AUDIT = "--audit" in a


def channelbag_fcurves(action):
    if hasattr(action, "layers") and action.layers:
        for L in action.layers:
            for s in L.strips:
                for cb in s.channelbags:
                    yield from cb.fcurves
    else:
        yield from getattr(action, "fcurves", [])


def audit():
    issues = []
    for col in (bpy.data.objects, bpy.data.materials, bpy.data.node_groups, bpy.data.scenes, bpy.data.worlds):
        for idb in col:
            ad = getattr(idb, "animation_data", None)
            if ad:
                for d in ad.drivers:
                    if "frame" in d.driver.expression:
                        issues.append("DRIVER %s %s %s" % (idb.name, d.data_path, d.driver.expression))
    for o in bpy.data.objects:
        for p in getattr(o, "particle_systems", []):
            issues.append("PARTICLES %s %s start %s end %s" % (o.name, p.name, p.settings.frame_start, p.settings.frame_end))
        for m in o.modifiers:
            if m.type == "BUILD":
                issues.append("BUILD %s start %s len %s" % (o.name, m.frame_start, m.frame_duration))
            if m.type == "WAVE":
                issues.append("WAVE %s time_offset %s" % (o.name, m.time_offset))
    for i in issues:
        print("TIMESRC", i)
    return issues


if AUDIT:
    audit()
    raise SystemExit

done = 0
for g in bpy.data.node_groups:
    sts = [n for n in g.nodes if n.bl_idname == "GeometryNodeInputSceneTime"]
    for st in sts:
        outs = {}
        for name, scale in (("Seconds", 1.0 / FPS), ("Frame", 1.0)):
            links = [l for l in g.links if l.from_node == st and l.from_socket.name == name]
            if not links:
                continue
            v = g.nodes.new("ShaderNodeValue")
            v.name = v.label = "SrcTime_%s_%s" % (name, st.name)
            v.location = (st.location.x, st.location.y - (60 if name == "Frame" else 0))
            sock = v.outputs[0]
            for new, old in PAIRS:
                sock.default_value = old * scale
                sock.keyframe_insert("default_value", frame=new)
            for l in links:
                g.links.new(sock, l.to_socket)
            outs[name] = v
        g.nodes.remove(st)
        done += 1
    if sts and g.animation_data and g.animation_data.action:
        for fc in channelbag_fcurves(g.animation_data.action):
            if "SrcTime_" in fc.data_path:
                fc.extrapolation = "LINEAR"
                for k in fc.keyframe_points:
                    k.interpolation = "LINEAR"
print("SCENE_TIME_FIXED nodes", done)
left = audit()
bpy.ops.wm.save_mainfile(compress=True)
print("SAVED", bpy.data.filepath, "other_raw_clock_sources", len(left))
