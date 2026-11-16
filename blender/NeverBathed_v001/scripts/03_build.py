# ================================================================== build
def cut_after(f1):
    """trim: drop every key this shot placed after its last frame (+1 for the hide keys), so nothing spills into the next shot"""
    ids = list(bpy.data.objects) + list(bpy.data.lights) + list(bpy.data.cameras) + [sc.world.node_tree]
    for idb in ids:
        for fc in all_fcurves(idb):
            for kp in [k for k in fc.keyframe_points if k.co.x > f1 + 1.01][::-1]:
                fc.keyframe_points.remove(kp, fast=True)
            fc.update()
shots = json.load(open(SHOTS))
sc.frame_start = 1; sc.frame_end = max(s_["f0"] + s_["len"] - 1 for s_ in shots)
used = {}
for s_ in shots:
    if s_["id"] not in SHOT_FUNCS or (ONLY and s_["id"] not in ONLY): continue
    print("SHOT", s_["id"], s_["f0"], s_["len"])
    used[s_["id"]] = SHOT_FUNCS[s_["id"]](s_["f0"], s_["len"])
    hold_ends(s_["f0"], s_["f0"] + s_["len"] - 1)
    cut_after(s_["f0"] + s_["len"] - 1)
for s_ in shots:
    if s_["id"] not in used: continue
    for n in CH: place_rig(n, s_["f0"], s_["f0"] + s_["len"] - 1, n in used[s_["id"]])
for o in bpy.data.objects:      # object-level parking keys must not interpolate between shots
    ad = o.animation_data
    if ad and ad.action:
        for layer in getattr(ad.action, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        if fc.data_path in ("location", "hide_render", "hide_viewport") and o.type == 'ARMATURE':
                            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
                        if fc.data_path in ("hide_render", "hide_viewport"):
                            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# light states are per shot: constant between shot starts (no fades into dusk)
for idb in (OB["Sun"], OB["Sun"].data, sc.world.node_tree):
    for fc in all_fcurves(idb):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
VO = os.environ.get("NB_VO")
if VO:
    if not sc.sequence_editor: sc.sequence_editor_create()
    seq = sc.sequence_editor
    coll = seq.strips if hasattr(seq, "strips") else seq.sequences
    snd = coll.new_sound("VO", VO, channel=1, frame_start=1)
    sc.render.ffmpeg.audio_codec = 'AAC' if hasattr(sc.render, "ffmpeg") else None
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SHOTS_OK", list(used))
