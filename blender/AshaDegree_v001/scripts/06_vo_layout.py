"""Phase 2: lay the film out to the client's VO (B06_AshaDegree_VO.mp3, 33.3 s).
Every set's action (animated at 1x in 04_shots.py on its own source timeline) is SHIFTED by one constant offset
per set (film = source - offset). Nothing is time-stretched. Cuts sit on the VO word frames: 1 + round(s * 60).
Each shot gets its own camera keyed over its source window; markers bind the cameras (hard cuts).
blender -b work/film.blend --python 06_vo_layout.py -- work/film_vo.blend VO.mp3 beats.json"""
import bpy, sys, json, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
OUT, VO, BEATS = a[0], a[1], a[2]
sc = bpy.context.scene
R_ = math.radians
F = lambda s: 1 + round(s * 60)

# ------------------------------------------------------------------ VO shot table (film frames from word times)
# (shot, set, first word time s, words)
VOS = [("S01", "room", 0.00, "In 2000,"), ("S02", "room", 1.28, "a nine-year-old girl"), ("S03", "room", 2.24, "packed a book bag and"),
       ("S04", "room", 3.52, "quietly left her house in the rain."), ("S05", "road", 5.86, "It was extremely early in the morning"),
       ("S06", "road", 7.60, "when a driver spotted her"), ("S07", "road", 8.92, "walking beside the highway."),
       ("S08", "road", 10.66, "He turned around to check on her,"), ("S09", "road", 12.18, "but as he approached,"),
       ("S10", "road", 13.74, "she suddenly ran into the woods."), ("S11", "woods", 15.88, "By daylight,"),
       ("S12", "woods", 16.74, "she had vanished."), ("S13", "shed", 18.10, "A few belongings were later found"),
       ("S14", "shed", 19.48, "inside a nearby shed,"), ("S15", "search", 20.88, "but there was no"),
       ("S16", "search", 21.80, "sign of her."), ("S17", "site", 22.90, "A year later,"),
       ("S18", "site", 23.72, "her book bag was discovered buried"), ("S19", "site", 25.32, "at a construction site"),
       ("S20", "site", 26.46, "inside a plastic bag,"), ("S21", "site", 28.08, "but it revealed nothing."),
       ("S22", "ghost", 30.18, "Nobody knows why she left that night,"), ("S23", "wall", 32.10, "or where she went.")]
END = F(32.96 + 0.5)          # last word ends 32.96 s
shots = []
for i, (sid, setn, t, words) in enumerate(VOS):
    f0 = F(t); f1 = (F(VOS[i + 1][2]) - 1) if i + 1 < len(VOS) else END
    shots.append((sid, setn, f0, f1, words))
# source = film + OFFSET[set]   (one constant shift per set; the S02/S03 cut lands on the bag-swap frame 210/211)
OFFSET = {"room": 211 - F(2.24), "road": 960 - F(13.74), "woods": 1081 - F(15.88), "shed": 1261 - F(18.10),
          "search": 1501 - F(20.88), "site": 1842 - F(22.90), "ghost": 2281 - F(30.18), "wall": 2461 - F(32.10)}
print("OFFSETS", OFFSET)

# ------------------------------------------------------------------ helpers shared with 04 (same formulas)
XR, XW, XS, XT, XP = 100.0, 200.0, 300.0, 400.0, 500.0
SX = XR + 5.0; v = 1.0 / 60.0
def road_y(f): return -34.0 + max(0, min(f, 905) - 400) * v + (max(0, f - 905) * v * 0.15 if f < 925 else 20 * v * 0.15)
y_stop = road_y(925)
wy = lambda f: -8.0 + (f - 1060) * 3.0 / 60.0
gy = lambda f: 62.0 + max(0, f - 2250) * v
CL = Vector((XW + 12.0, 10.0)); a_pos = Vector((XS + 1.35, 0.25))

# ------------------------------------------------------------------ remove the provisional cameras / markers
for o in list(bpy.data.objects):
    if o.name.startswith(("CAM_", "TGT_")): bpy.data.objects.remove(o)
sc.timeline_markers.clear()

def src(sid):
    s = next(x for x in shots if x[0] == sid); off = OFFSET[s[1]]
    return s[2] + off, s[3] + off
CAMSET = {}
def cam(sid, keys, tkeys, lens):
    """keys in SOURCE frames, given as fractions u of the shot's source window (0 = first frame, 1 = last)"""
    s0, s1 = src(sid)
    c = bpy.data.cameras.new("CAM_" + sid); c.lens = lens; c.clip_start = 0.05; c.clip_end = 600; c.dof.use_dof = False; c.sensor_width = 36
    o = bpy.data.objects.new("CAM_" + sid, c); sc.collection.objects.link(o)
    t = bpy.data.objects.new("TGT_" + sid, None); sc.collection.objects.link(t)
    for u, p in keys:
        o.location = p(s0 + u * (s1 - s0)) if callable(p) else p; o.keyframe_insert("location", frame=s0 + u * (s1 - s0) - 4 + 8 * u)
    for u, p in tkeys:
        t.location = p(s0 + u * (s1 - s0)) if callable(p) else p; t.keyframe_insert("location", frame=s0 + u * (s1 - s0) - 4 + 8 * u)
    tr = o.constraints.new('TRACK_TO'); tr.target = t; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    CAMSET[o.name] = CAMSET[t.name] = next(x[1] for x in shots if x[0] == sid)
    return o

# ---- ROOM
cam("S01", [(0, (0.78, -1.62, 0.55)), (1, (0.66, -1.38, 0.52))], [(0, (0.0, 0.05, 0.5)), (1, (0.0, 0.1, 0.55))], 32)
cam("S02", [(0, (0.9, -0.8, 0.76)), (1, (0.78, -0.64, 0.74))], [(0, (0.0, 0.2, 0.72)), (1, (0.0, 0.22, 0.74))], 45)
cam("S03", [(0, (0.25, -2.3, 0.95)), (1, (0.45, -1.8, 1.0))], [(0, (0.05, 0.4, 0.75)), (1, (0.45, 1.0, 0.8))], 30)
cam("S04", [(0, (2.45, 0.55, 1.05)), (1, (2.25, 1.15, 1.1))], [(0, (0.6, 1.2, 0.8)), (0.6, (1.1, 2.4, 0.85)), (1, (1.17, 3.4, 0.85))], 28)
# ---- ROAD (her walk: x = SX, y = road_y)
cam("S05", [(0, lambda f: (SX - 0.9, road_y(f) - 3.4, 0.85)), (1, lambda f: (SX - 0.8, road_y(f) - 2.8, 0.9))],
    [(0, lambda f: (SX, road_y(f), 1.15)), (1, lambda f: (SX, road_y(f), 1.15))], 32)
cam("S06", [(0, lambda f: (SX - 1.6, road_y(f) + 3.0, 1.0)), (1, lambda f: (SX - 1.5, road_y(f) + 2.5, 1.0))],
    [(0, lambda f: (SX, road_y(f), 1.05)), (1, lambda f: (SX, road_y(f), 1.05))], 35)
cam("S07", [(0, lambda f: (XR - 0.4, road_y(f) - 3.2, 1.25)), (0.5, lambda f: (XR - 0.4, road_y(f) - 3.1, 1.25)), (1, lambda f: (XR - 0.4, road_y(f) - 3.0, 1.25))],
    [(0, lambda f: (SX - 0.2, road_y(f) + 0.6, 0.95)), (0.5, lambda f: (SX - 0.2, road_y(f) + 0.6, 0.95)), (1, lambda f: (SX - 0.2, road_y(f) + 0.6, 0.95))], 30)
cam("S08", [(0, lambda f: (XR - 4.0, road_y(f) - 12.0, 4.2)), (1, lambda f: (XR - 3.6, road_y(f) - 10.5, 4.0))],
    [(0, lambda f: (XR + 3.5, road_y(f) + 6.0, 0.6)), (1, lambda f: (XR + 3.5, road_y(f) + 6.0, 0.6))], 26)
cam("S09", [(0, lambda f: (SX + 0.6, road_y(f) - 2.6, 0.95)), (1, lambda f: (SX + 0.9, road_y(f) - 2.2, 0.95))],
    [(0, lambda f: (SX - 0.4, road_y(f) + 3.0, 1.0)), (1, lambda f: (SX - 0.6, road_y(f) + 3.0, 1.0))], 30)
cam("S10", [(0, (XR + 2.4, y_stop - 1.5, 1.05)), (1, (XR + 3.0, y_stop - 0.4, 1.15))],
    [(0, (SX + 0.3, y_stop + 0.3, 0.9)), (0.5, (SX + 3.0, y_stop + 1.6, 0.8)), (1, (SX + 6.0, y_stop + 3.2, 0.8))], 28)
# ---- WOODS run
cam("S11", [(0, lambda f: (XW - 2.4, wy(f) - 1.0, 1.0)), (1, lambda f: (XW - 2.4, wy(f) - 1.4, 1.05))],
    [(0, lambda f: (XW, wy(f), 0.85)), (1, lambda f: (XW, wy(f), 0.85))], 28)
cam("S12", [(0, lambda f: (XW - 0.8, wy(f) - 4.5, 1.5)), (1, lambda f: (XW - 0.7, wy(f) - 6.5, 1.5))],
    [(0, lambda f: (XW, wy(f) + 2.0, 0.9)), (1, lambda f: (XW, wy(f), 0.9))], 30)
# ---- SHED
cam("S13", [(0, (XS + 0.2, -4.6, 1.55)), (1, (XS + 0.5, -4.0, 1.5))], [(0, (XS + 0.2, 1.0, 0.95)), (1, (XS + 0.35, 1.0, 0.95))], 30)
cam("S14", [(0, (XS + 1.95, -1.7, 1.55)), (1, (XS + 1.8, -1.5, 1.55))], [(0, (a_pos.x, a_pos.y, 1.35)), (1, (a_pos.x, a_pos.y, 1.4))], 35)
# ---- SEARCH
cam("S15", [(0, (CL.x - 1.5, CL.y - 9.0, 2.0)), (1, (CL.x - 1.0, CL.y - 8.4, 1.95))], [(0, (CL.x, CL.y - 1.0, 1.0)), (1, (CL.x, CL.y - 0.8, 1.0))], 26)
cam("S16", [(0, (CL.x - 3.6, CL.y + 1.6, 1.55)), (1, (CL.x - 3.5, CL.y + 2.2, 1.55))], [(0, (CL.x - 2.2, CL.y - 2.2, 1.3)), (1, (CL.x - 2.0, CL.y - 1.4, 1.35))], 32)
# ---- SITE
cam("S17", [(0, (XT - 0.25, -0.42, 0.42)), (1, (XT - 0.15, -0.3, 0.38))], [(0, (XT + 0.2, 0.33, 0.08)), (1, (XT + 0.2, 0.33, 0.08))], 40)
cam("S18", [(0, (XT - 0.5, -1.45, 0.42)), (1, (XT - 0.38, -1.28, 0.42))], [(0, (XT + 0.5, 0.35, 0.45)), (1, (XT + 0.45, 0.35, 0.45))], 28)
cam("S19", [(0, (XT - 2.6, -2.6, 1.5)), (1, (XT - 2.2, -2.2, 1.4))], [(0, (XT + 0.4, 0.3, 0.3)), (1, (XT + 0.4, 0.3, 0.3))], 28)
cam("S20", [(0, (XT + 0.05, -0.62, 0.55)), (1, (XT + 0.15, -0.52, 0.5))], [(0, (XT + 0.3, 0.32, 0.2)), (1, (XT + 0.3, 0.32, 0.2))], 35)
cam("S21", [(0, (XT - 0.15, -1.15, 0.38)), (1, (XT - 0.05, -1.0, 0.38))], [(0, (XT + 0.6, 0.38, 0.62)), (1, (XT + 0.6, 0.38, 0.65))], 30)
# ---- GHOST + WALL
cam("S22", [(0, lambda f: (XR + 0.6, gy(f) - 3.2, 0.9)), (1, lambda f: (XR + 0.3, gy(f) - 2.4, 0.95))],
    [(0, lambda f: (XR + 1.6, gy(f), 1.0)), (1, lambda f: (XR + 1.6, gy(f), 1.05))], 32)
cam("S23", [(0, (XP + 0.0, -2.2, 2.45)), (1, (XP + 0.0, -1.65, 2.5))], [(0, (XP, 0, 2.48)), (1, (XP, 0, 2.5))], 40)

# ------------------------------------------------------------------ which set does every animated object belong to?
RIGSET = {"Girl": "room", "GirlRoad": "road", "GirlWoods": "woods", "GirlGhost": "ghost", "SearchA": "shed", "SearchB": "shed",
          "SearchA2": "search", "SearchB2": "search", "SearchC": "search", "Worker": "site"}
NAMESET = {"Car": "road", "BagFloor": "room", "Room_ToyBox": "room", "Room_ToyBoxLogo": "room", "FaceFill_Road": "road"}
def owner_set(o):
    if o.name in CAMSET: return CAMSET[o.name]
    if o.name in RIGSET: return RIGSET[o.name]
    if o.parent and o.parent.name in RIGSET: return RIGSET[o.parent.name]
    for c in o.constraints:
        if c.type == 'CHILD_OF' and c.target and c.target.name in RIGSET: return RIGSET[c.target.name]
    if o.parent:
        r = owner_set(o.parent)
        if r: return r
    for k, sname in NAMESET.items():
        if o.name.startswith(k): return sname
    return None

def fcurves_of(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    act = ad.action; out = []
    try: out = list(act.fcurves)
    except Exception: out = []
    if not out:
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out

shifted = {}; unknown = []
done_actions = set()
for o in bpy.data.objects:
    fcs = fcurves_of(o)
    if not fcs: continue
    st = owner_set(o)
    if st is None:
        unknown.append(o.name); continue
    act = o.animation_data.action
    if act.name in done_actions and act.users > 1:
        unknown.append(o.name + "(shared action)"); continue
    done_actions.add(act.name)
    off = OFFSET[st]
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.co.x -= off; kp.handle_left.x -= off; kp.handle_right.x -= off
        fc.update()
    shifted[st] = shifted.get(st, 0) + 1
print("SHIFTED", shifted); print("UNASSIGNED animated objects", unknown)

# ------------------------------------------------------------------ keep the new camera paths clear of vegetation
pts = []
for sid, setn, f0, f1, words in shots:
    c = bpy.data.objects["CAM_" + sid]
    for f in range(f0, f1 + 1, 4):
        sc.frame_set(f); pts.append(c.matrix_world.translation.copy())
removed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(("Woods_Under", "Woods_Tree", "Woods_LaneTree", "Road_Shrub", "Shed_Under", "Shed_Tree", "Site_Tree", "Road_Tree")):
        rad = 4.5 if o.name.startswith("Woods_Tree") else (2.8 if o.name.startswith("Woods_Under") else 1.8)
        if any((o.location.xy - p.xy).length < rad for p in pts):
            bpy.data.objects.remove(o); removed += 1
print("CLEARED near-lens vegetation (new cameras)", removed)
# ------------------------------------------------------------------ markers, per-shot world/sun, frame range, VO
for sid, setn, f0, f1, words in shots:
    m = sc.timeline_markers.new(sid, frame=f0); m.camera = bpy.data.objects["CAM_" + sid]
sun = bpy.data.lights["Sun"]; bg = sc.world.node_tree.nodes["Background"]
for idb in (sun, sc.world.node_tree):
    if idb.animation_data: idb.animation_data_clear()
LOOK = {"room": (0.0, (0.03, 0.045, 0.09), 0.6), "road": (0.0, (0.045, 0.06, 0.13), 1.0), "woods": (0.0, (0.07, 0.09, 0.18), 1.0),
        "search": (0.0, (0.07, 0.09, 0.18), 1.0), "shed": (4.5, (0.55, 0.72, 0.95), 1.0), "site": (4.5, (0.6, 0.75, 0.95), 1.0),
        "ghost": (0.0, (0.045, 0.06, 0.13), 1.0), "wall": (0.0, (0.05, 0.04, 0.03), 0.3)}
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'
for sid, setn, f0, f1, words in shots:
    se, col, stv = LOOK[setn]
    sun.energy = se; sun.keyframe_insert("energy", frame=f0)
    bg.inputs["Color"].default_value = (*col, 1); bg.inputs["Color"].keyframe_insert("default_value", frame=f0)
    bg.inputs["Strength"].default_value = stv; bg.inputs["Strength"].keyframe_insert("default_value", frame=f0)
for idb in (sun, sc.world.node_tree):
    for fc in fcurves_of(idb):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
seq = sc.sequence_editor
strips = seq.strips if hasattr(seq, "strips") else seq.sequences
snd = strips.new_sound("VO", VO, 1, 1)
sc.render.ffmpeg.audio_codec = 'AAC'
json.dump([{"beat": sid, "set": setn, "frame": f0, "frame_last": f1, "first_words": words} for sid, setn, f0, f1, words in shots] + [{"frame_end": END}],
          open(BEATS, "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("VO_LAYOUT_DONE frames 1-%d, %d shots" % (END, len(shots)))
