"""B09 Phase 2: lay the Phase-1 clips onto the client VO (no time-stretch: each group is only SHIFTED).
blender -b work/anim_t.blend --python 04_layout.py -- out.blend vo.mp3 beats_out.json
Word frames = 1 + round(seconds * 60) from vo/B09_VO.words.json."""
import bpy, sys, json, statistics
a = sys.argv[sys.argv.index("--") + 1:]; OUT, VO, BOUT = a[0], a[1], a[2]
sc = bpy.context.scene
# group: (Phase-1 clip window, clip frame shown at the group's first VO frame, VO start, VO end (exclusive), cuts [(vo_frame, camera)])
GROUPS = {
    "B1":   ((1, 420),     66,   1,    302, [(1, "Cam1a"), (65, "Cam1b"), (225, "Cam1c")]),
    "B2a":  ((421, 640),   457,  302,  445, [(302, "Cam2a")]),
    "B2bc": ((641, 1200),  755,  445,  727, [(445, "Cam2b"), (590, "Cam2c")]),
    "B3":   ((1201, 1700), 1277, 727,  1044, [(727, "Cam3a"), (811, "Cam3b"), (950, "Cam3c")]),
    "B4":   ((1701, 2280), 1811, 1044, 1482, [(1044, "Cam4a"), (1135, "Cam4b"), (1281, "Cam4c"), (1391, "Cam4d")]),
    "B5":   ((2281, 2560), 2353, 1482, 1643, [(1482, "Cam5a"), (1570, "Cam5b")]),
    "B6":   ((2561, 2860), 2600, 1643, 1809, [(1643, "Cam6a"), (1733, "Cam6b")]),
}
END = 1808
BEATS = [("B1", 1, "A woman accidentally spilled"), ("B2", 302, "At the time, the coffee"), ("B3", 727, "The burns were so severe"),
         ("B4", 1044, "And she wasn't the only one"), ("B5", 1482, "The case created massive backlash"),
         ("B6", 1643, "pushed the company to lower the serving temperature")]

def fcurves(ad):
    act = ad.action if ad else None
    if not act: return []
    out = list(getattr(act, "fcurves", []) or [])
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                if getattr(ad, "action_slot", None) is None or cb.slot == ad.action_slot: out += list(cb.fcurves)
    return out

def owners():
    """every animated ID with its animation_data"""
    ids = []
    for coll in (bpy.data.objects, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.shape_keys, bpy.data.node_groups, bpy.data.worlds):
        for idb in coll:
            if idb.animation_data and idb.animation_data.action: ids.append(idb)
            nt = getattr(idb, "node_tree", None)
            if nt and nt.animation_data and nt.animation_data.action: ids.append(nt)
    return ids

def group_of(idb, fcs):
    name = idb.name if not hasattr(idb, "id_data") else idb.id_data.name
    xs = [k.co.x for fc in fcs if not fc.data_path.startswith("hide") for k in fc.keyframe_points]
    if not xs: xs = [k.co.x for fc in fcs for k in fc.keyframe_points]
    if not xs: return None
    m = statistics.median(xs)
    for g, (win, *_r) in GROUPS.items():
        if g.startswith("B2"): continue
        if win[0] <= m <= win[1]: return g
    if 421 <= m <= 1201:
        nm = name
        if nm.startswith(("Pour", "Cam2a")) or "PourSteam" in nm: return "B2a"
        return "B2bc"
    return None

# actions are shared per ID here (one action per object); collect fcurves per action once
done_actions = set(); assigned = {}
rig_group = {}
for idb in owners():
    if isinstance(idb, bpy.types.Object) and idb.type == 'ARMATURE':
        rig_group[idb.name] = group_of(idb, fcurves(idb.animation_data))
def follow_rig(idb):
    """props held by a character (Child Of a rig bone) move with that character's group"""
    if not isinstance(idb, bpy.types.Object): return None
    for c in idb.constraints:
        if c.type == 'CHILD_OF' and c.target and c.target.name in rig_group: return rig_group[c.target.name]
    return None
for idb in owners():
    ad = idb.animation_data; fcs = fcurves(ad)
    g = follow_rig(idb) or group_of(idb, fcs)
    if g is None: continue
    assigned.setdefault(g, []).append(idb)
    if ad.action.name in done_actions:
        continue
    done_actions.add(ad.action.name)
    win, c0, v0, v1, cuts = GROUPS[g]; d = v0 - c0
    for fc in fcs:
        for k in fc.keyframe_points:
            k.co.x += d; k.handle_left.x += d; k.handle_right.x += d
        fc.update()
# visibility: every object of a group with hide keys stays hidden outside its VO range
for g, ids in assigned.items():
    win, c0, v0, v1, cuts = GROUPS[g]
    for idb in ids:
        if not isinstance(idb, bpy.types.Object): continue
        for fc in fcurves(idb.animation_data):
            if fc.data_path not in ("hide_render", "hide_viewport"): continue
            val0 = fc.evaluate(v0)            # state the group starts with (after the shift)
            for k in list(fc.keyframe_points)[::-1]:
                if k.co.x <= v0 or k.co.x > v1: fc.keyframe_points.remove(k)
            fc.keyframe_points.insert(v0, val0).interpolation = 'CONSTANT'
            # value at v0 (after the shift) must be whatever it was; make it hidden before v0 and after v1
            for f, val in ((v0 - 1, 1.0), (v1, 1.0)):
                if f >= 1: fc.keyframe_points.insert(f, val).interpolation = 'CONSTANT'
            if v0 > 1:
                fc.keyframe_points.insert(1, 1.0).interpolation = 'CONSTANT'
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
            fc.update()
print("LAYOUT groups", {g: len(v) for g, v in assigned.items()})
# the served cup from 2b/2c sits under the behind-the-counter lens in B4: hide it once its own shots are over
for o in [bpy.data.objects["CounterCup"]] + list(bpy.data.objects["CounterCup"].children_recursive) + [bpy.data.objects["CounterSteam"]] + [b for b in bpy.data.objects if b.name.startswith("Bubble")]:
    for f, v in ((1, False), (727, True)):
        o.hide_render = v; o.hide_viewport = v; o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
# hard-cut markers on the VO frames
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for g, (win, c0, v0, v1, cuts) in GROUPS.items():
    for f, cam in cuts:
        m = sc.timeline_markers.new(cam, frame=f); m.camera = bpy.data.objects[cam]
sc.frame_start, sc.frame_end = 1, END
sc.camera = bpy.data.objects["Cam1a"]
# VO
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
coll = se.strips if hasattr(se, "strips") else se.sequences
snd = coll.new_sound("VO", VO, channel=1, frame_start=1)
sc.render.ffmpeg.audio_codec = 'AAC'
json.dump([{"beat": b, "frame": f, "first_words": w} for b, f, w in BEATS], open(BOUT, "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("LAYOUT_OK", OUT, "frames 1-%d" % END, "cuts", sorted((m.frame, m.name) for m in sc.timeline_markers))
