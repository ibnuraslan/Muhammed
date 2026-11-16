"""Lay the provisional build onto the VO word frames WITHOUT stretching anything.
Every set-run (consecutive VO shots from one provisional action) gets ONE constant time shift, so all character
animation plays at 1x. Cameras of a run take the same shift (tracking stays locked to the walkers) and extrapolate
linearly where a VO shot is longer than its provisional camera keys. Set switches (sun, world, lamps, window glow)
are keyed at shot starts and map shot-start -> VO shot-start. Visibility is re-keyed from the recorded ranges.
blender -b work/film.blend --python 05_retime.py -- work/film_vo.blend"""
import bpy, sys, json
HERE = "/home/user/Muhammed/blender/NatashaRyan_v001/"
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
PROV = {s["shot"]: (s["f0"], s["f1"], s["set"]) for s in json.load(open(HERE + "shots_provisional.json"))}
VO = json.load(open(HERE + "beats.json"))
NEW = {b["shot"]: (b["frame"], b["frame_end"]) for b in VO}
RUNS = [(["S01", "S02"], 0), (["S03", "S04"], -142), (["S06"], -260), (["S07", "S08"], -352), (["S09"], -312),
        (["S10"], -347), (["S11", "S12", "S13"], -353), (["S15", "S16", "S17", "S18", "S19"], -560), (["S20"], -560),
        (["S21"], -550), (["S22"], -605), (["S23"], -648)]
SHOT_RUN = {sid: i for i, (ss, _) in enumerate(RUNS) for sid in ss}
SPAN = [(min(PROV[s][0] for s in ss), max(PROV[s][1] for s in ss)) for ss, _ in RUNS]
NWIN = [(min(NEW[s][0] for s in ss), max(NEW[s][1] for s in ss)) for ss, _ in RUNS]
FEND = max(b["frame_end"] for b in VO)
# coverage report: the action time each VO window needs must lie inside the provisional action
for i, (ss, sh) in enumerate(RUNS):
    print("RUN", ss, "shift", sh, "VO", NWIN[i], "-> action", (NWIN[i][0] - sh, NWIN[i][1] - sh), "prov span", SPAN[i])
VISR = json.load(open(HERE + "work/visr.json"))
def runs_overlapping(ranges):
    rs = set()
    for a, b in ranges:
        for i, (s0, s1) in enumerate(SPAN):
            if a <= s1 and b >= s0: rs.add(i)
    return rs
OBJRUNS = {}
for name, rg in VISR.items():
    r = bpy.data.objects.get(name)
    if r is None or name.startswith("__"): continue
    rr = runs_overlapping(rg)
    OBJRUNS[name] = rr
    for c in r.children_recursive: OBJRUNS[c.name] = rr
    for o in bpy.data.objects:
        if any(cn.type == 'CHILD_OF' and cn.target == r for cn in o.constraints): OBJRUNS[o.name] = rr
for o in bpy.data.objects:
    if o.name.startswith(("CAM_", "TGT_")):
        sid = o.name[4:]
        OBJRUNS[o.name] = {SHOT_RUN[sid]} if sid in SHOT_RUN else set()
    if o.name.startswith(("Police_",)): OBJRUNS[o.name] = {SHOT_RUN["S20"]}

def fcurves_of(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    act = ad.action; res = []
    try: res = list(act.fcurves)
    except Exception: res = []
    if not res:
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []): res += list(cb.fcurves)
    return res

def map_global(f):
    for sid, (f0, f1, _) in PROV.items():
        if abs(f - f0) < 0.5: return NEW[sid][0] if sid in NEW else None
        if abs(f - f1) < 0.5 and sid in NEW: return NEW[sid][1]
    if f <= 1.5: return 1
    for sid, (f0, f1, _) in PROV.items():
        if f0 <= f <= f1: return (NEW[sid][0] + (f - f0)) if sid in NEW else None
    return None

def map_run(f, runs):
    if not runs: runs = set(range(len(RUNS)))
    best = min(runs, key=lambda i: 0 if SPAN[i][0] <= f <= SPAN[i][1] else min(abs(f - SPAN[i][0]), abs(f - SPAN[i][1])))
    return best, f + RUNS[best][1]

def remap_curve(fc, mode, runs, extrap=None):
    pts = [(kp.co.x, kp.co.y, kp.interpolation, kp.handle_left_type, kp.handle_right_type) for kp in fc.keyframe_points]
    new = []
    for x, y, it, hl, hr in pts:
        if mode == "global":
            nx = map_global(x)
            if nx is None: continue
            new.append((nx, y, it))
        else:
            ri, nx = map_run(x, runs)
            # a key mapped by one run must not land inside another run's VO window of this object
            if any(j != ri and NWIN[j][0] - 1 <= nx <= NWIN[j][1] + 1 for j in runs): continue
            new.append((nx, y, it))
    new.sort(key=lambda t: t[0])
    ded = []
    for t in new:
        if ded and abs(ded[-1][0] - t[0]) < 0.5: ded[-1] = t
        else: ded.append(t)
    while len(fc.keyframe_points): fc.keyframe_points.remove(fc.keyframe_points[0], fast=True)
    for x, y, it in ded:
        kp = fc.keyframe_points.insert(x, y, options={'FAST'}); kp.interpolation = it
    fc.update()
    if extrap: fc.extrapolation = extrap

GLOBAL_IDS = []
sun = bpy.data.objects.get("Sun")
if sun: GLOBAL_IDS.append(sun.data)
GLOBAL_IDS.append(sc.world.node_tree)
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.name.startswith(("Home_Lamp", "Home_PorchLight", "Home_BfPorchLight")): GLOBAL_IDS.append(o.data)
gm = bpy.data.materials.get("Translucent_Glass_Safety")
if gm: GLOBAL_IDS.append(gm.node_tree)
done = set()
for idb in GLOBAL_IDS:
    for fc in fcurves_of(idb): remap_curve(fc, "global", None)
    done.add(idb.name_full if hasattr(idb, "name_full") else idb.name)
# police bar materials / flash lights follow the S20 run
POL = [bpy.data.materials.get(n) for n in ("BarRed", "BarBlue")]
for m in POL:
    if m:
        for fc in fcurves_of(m.node_tree): remap_curve(fc, "run", {SHOT_RUN["S20"]})
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.name.startswith("Police_Flash"):
        for fc in fcurves_of(o.data): remap_curve(fc, "run", {SHOT_RUN["S20"]})
# objects: drop visibility curves (re-keyed below), shift the rest
nobj = 0
for o in bpy.data.objects:
    fcs = fcurves_of(o)
    if not fcs: continue
    runs = OBJRUNS.get(o.name, set())
    iscam = o.name.startswith(("CAM_", "TGT_"))
    for fc in list(fcs):
        if fc.data_path in ("hide_render", "hide_viewport"):
            o.animation_data.action.fcurves.remove(fc) if hasattr(o.animation_data.action, "fcurves") else None
            continue
        remap_curve(fc, "run", runs, extrap='LINEAR' if iscam else None)
    nobj += 1
# any visibility curves still present (layered actions) -> clear them via keyframe_delete
for o in bpy.data.objects:
    for fc in fcurves_of(o):
        if fc.data_path in ("hide_render", "hide_viewport"):
            while len(fc.keyframe_points): fc.keyframe_points.remove(fc.keyframe_points[0], fast=True)
print("REMAPPED objects", nobj)
# visibility from recorded ranges -> union of the VO windows of the kept shots they cover
def new_ranges(rg):
    out_ = []
    for a, b in rg:
        ws = [NEW[sid] for sid, (f0, f1, _) in PROV.items() if sid in NEW and a <= f1 and b >= f0]
        if ws: out_.append((min(w[0] for w in ws), max(w[1] for w in ws)))
    return out_
def key_vis(names, ranges):
    for n in names:
        o = bpy.data.objects[n]
        o.hide_render = True; o.hide_viewport = True
        o.keyframe_insert("hide_render", frame=0); o.keyframe_insert("hide_viewport", frame=0)
        for f0, f1 in ranges:
            o.hide_render = False; o.hide_viewport = False; o.keyframe_insert("hide_render", frame=f0); o.keyframe_insert("hide_viewport", frame=f0)
            o.hide_render = True; o.hide_viewport = True; o.keyframe_insert("hide_render", frame=f1 + 1); o.keyframe_insert("hide_viewport", frame=f1 + 1)
        for fc in fcurves_of(o):
            if fc.data_path in ("hide_render", "hide_viewport"):
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
HIDDEN = json.load(open(HERE + "work/hidden.json"))
for name, rg in VISR.items():
    if name == "__mem__":
        names = [o.name for o in bpy.data.objects if o.name.startswith("Mem_") and o.type in ('MESH', 'LIGHT')]
    elif name == "__van__":
        names = ["Delivery_Van", "Van_Logo"]
    else:
        r = bpy.data.objects.get(name)
        if r is None: continue
        names = [c.name for c in r.children if c.name not in HIDDEN]
        props = [o for o in bpy.data.objects if any(cn.type == 'CHILD_OF' and cn.target == r for cn in o.constraints)]
        for o in props: names += [o.name] + [c.name for c in o.children if c.name not in HIDDEN]
    key_vis(names, new_ranges(rg))
# markers: only the kept shots, at their VO frames
for m in list(sc.timeline_markers):
    if m.name in NEW: m.frame = NEW[m.name][0]
    else:
        cam = m.camera; sc.timeline_markers.remove(m)
        if cam:
            t = bpy.data.objects.get("TGT_" + cam.name[4:]); cl = bpy.data.objects.get("Catch_" + cam.name[4:])
            for x in (cl, t, cam):
                if x: bpy.data.objects.remove(x)
sc.frame_start = 1; sc.frame_end = FEND
print("RETIME frame_end", FEND, "markers", sorted((m.frame, m.name) for m in sc.timeline_markers))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("RETIME_DONE")
