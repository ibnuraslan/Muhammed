"""Camera search with qa_check's own criteria. args: -- frame:rig:bone[:dz] ...  -> prints best camera (pos, aim, lens)"""
import bpy, sys, math, itertools
from mathutils import Vector
src = open("/home/user/Muhammed/blender/pipeline/qa_check.py").read()
pre = src[:src.index("res = {")]
pre = pre.replace("a = sys.argv[sys.argv.index(\"--\") + 1:]", "a = ['/dev/null']")
exec(pre)
_wc = bpy.data.objects.get("WipeCard")
if _wc: _wc.hide_viewport = True; _wc.hide_render = True; _wc.hide_set(True)
HAIR = ("hair", "short0", "long0", "bob0", "ponytail", "braid", "afro")
def metrics(dg):
    cpos = cam.matrix_world.translation
    hits = ray_grid(dg)
    names = [h[0] for h in hits if h[0]]
    charf = sum(1 for h in hits if h[0] in CHAR_MESH and not any(k in h[0].lower() for k in HAIR)) / len(hits)
    hair = sum(1 for h in hits if h[0] and any(k in h[0].lower() for k in HAIR)) / len(hits)
    close = sum(1 for h in hits if h[1] < 0.12) / len(hits)
    top = max(set(names), key=names.count) if names else None
    near_top = sum(1 for h in hits if h[0] == top and h[1] < 0.6) / len(hits) if top else 0
    fill = (top not in CHAR_MESH and near_top > 0.7) or close > 0.7 or hair > 0.25
    live = [r for r in RIGS if not hidden(r)]
    def unocc(r, p):
        if not visible(p): return False
        d = p - cpos; nm, dist = cast(dg, cpos, d.normalized(), d.length + 0.05)
        return nm is None or nm in CHAR_MESH
    seen = [r for r in live if any(unocc(r, wpos(r, b)) for b in ("head", "wrist.L", "wrist.R", "spine03"))]
    facing = -2
    if seen:
        r = min(seen, key=lambda r: (wpos(r, "head") - cpos).length); hb = r.pose.bones["head"]
        rot = (hb.matrix.to_3x3() @ hb.bone.matrix_local.to_3x3().inverted())
        fwd = (r.matrix_world.to_3x3() @ rot @ Vector((0, -1, 0))).normalized()
        facing = fwd.dot((cpos - wpos(r, "head")).normalized())
    # inside
    cm_ = cam.matrix_world; fr_ = [cm_ @ v for v in cam.data.view_frame(scene=sc)]; back = 0
    for u in (0.2, 0.5, 0.8):
        for v in (0.2, 0.5, 0.8):
            p_ = fr_[2].lerp(fr_[1], u).lerp(fr_[3].lerp(fr_[0], u), v); d_ = (p_ - cpos).normalized()
            ok, loc, n, idx, ob, _ = sc.ray_cast(dg, cpos, d_, distance=50)
            if ok and n.dot(d_) > 0.05: back += 1
    return charf, facing, fill, back / 9 > 0.5, bool(seen)
cam.animation_data_clear() if False else None
for spec in sys.argv[sys.argv.index("--") + 1:]:
    p = spec.split(":"); FR = [int(x) for x in p[0].split(",")]; rig = bpy.data.objects[p[1]]; bone = p[2]; dz = float(p[3]) if len(p) > 3 else 0.0
    ad = cam.animation_data; act = ad.action if ad else None
    if ad: ad.action = None
    for c in cam.constraints: c.mute = True
    lens0 = cam.data.lens
    sc.frame_set(FR[0])
    head0 = rig.matrix_world @ rig.pose.bones[bone].head + Vector((0, 0, dz))
    hb = rig.pose.bones["head"]; rot = (hb.matrix.to_3x3() @ hb.bone.matrix_local.to_3x3().inverted())
    fwd = (rig.matrix_world.to_3x3() @ rot @ Vector((0, -1, 0))).normalized()
    fh = Vector((fwd.x, fwd.y, 0)).normalized() if Vector((fwd.x, fwd.y, 0)).length > 0.1 else Vector((0, -1, 0))
    cands = []
    for az, el, dist, lens in itertools.product(range(-80, 81, 20), (-10, 5, 20, 35), (0.9, 1.3, 1.8, 2.4), (22, 28)):
        d = fh.copy(); d.rotate(__import__("mathutils").Euler((0, 0, math.radians(az))))
        d = (d * math.cos(math.radians(el)) + Vector((0, 0, math.sin(math.radians(el))))).normalized()
        c = head0 + d * dist
        if 0.15 < c.z < 2.15: cands.append((c, lens))
    score = {i: [] for i in range(len(cands))}
    for f in FR:
        sc.frame_set(f)
        head = rig.matrix_world @ rig.pose.bones[bone].head + Vector((0, 0, dz))
        for i, (c, lens) in enumerate(cands):
            if score[i] is None: continue
            cam.location = c; cam.rotation_euler = (head - c).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
            dg = bpy.context.evaluated_depsgraph_get(); dg.update()
            charf, facing, fill, ins, seen = metrics(dg)
            near = [sc.ray_cast(dg, c, dd, distance=0.08)[0] for dd in (Vector((1,0,0)),Vector((-1,0,0)),Vector((0,1,0)),Vector((0,-1,0)),Vector((0,0,1)),Vector((0,0,-1)))]
            if ins or fill or not seen or facing < 0.1 or charf < 0.18 or (c - head).length < 0.6 or any(near): score[i] = None; continue
            score[i].append(charf + 0.6 * facing)
    ok = [(min(v) - 0.05 * (cands[i][0] - head0).length, i) for i, v in score.items() if v]
    ok.sort(reverse=True)
    for sv, i in ok[:3]:
        print("BEST", spec, round(sv, 2), tuple(round(x, 3) for x in cands[i][0]), cands[i][1])
    if not ok: print("BEST", spec, None)
    if ad: ad.action = act
    for c in cam.constraints: c.mute = False
    cam.data.lens = lens0
