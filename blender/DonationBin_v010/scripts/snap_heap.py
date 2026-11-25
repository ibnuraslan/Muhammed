# exec'd by 02_animate.py after the woman's bake: she rests ON the clothes heap. Per frame, the deepest point of her body /
# clothes / shoes below the heap surface lifts her root (window max + smoothing, so she never pops), and is re-keyed.
_wparts = [O[n] for n in ("Woman.body", "Woman.top", "Woman.trousers")] + [c for c in O["Woman"].children if c.type == 'MESH' and ("shoes" in c.name or "ponytail" in c.name)]
_dg_lifts = {}
_F0, _F1 = 205, min(UNTIL, 2388)
for f in range(_F0, _F1 + 1, 2):
    fs(f); dg = bpy.context.evaluated_depsgraph_get(); worst = 0.0
    for o in _wparts:
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
        for v in me.vertices:
            p = mw @ v.co
            if IX0 + 0.02 < p.x < IX1 - 0.02 and IY0 + 0.02 < p.y < IY1 - 0.02 and p.z < 1.0:
                d = heap(p.x, p.y) - p.z
                if d > worst: worst = d
        e.to_mesh_clear()
    _dg_lifts[f] = worst + (0.004 if worst > 0 else 0.0)
_fr = sorted(_dg_lifts)
_mx = {f: max(_dg_lifts[g] for g in _fr if abs(g - f) <= 8) for f in _fr}
_sm = {f: sum(_mx[g] for g in _fr if abs(g - f) <= 6) / len([g for g in _fr if abs(g - f) <= 6]) for f in _fr}
_sm = {f: max(_sm[f], _dg_lifts[f]) for f in _fr}
_kk = [(f, _sm[f]) for f in _fr]
_lift_f = pchip([(_F0 - 20, 0.0)] + _kk + [(_F1 + 20, 0.0)])
W.lift = lambda f: max(0.0, _lift_f(f)) if _F0 - 20 <= f <= _F1 + 20 else 0.0
W.bake(_F0 - 20, min(UNTIL, _F1 + 20))       # re-bake: the whole body (root AND the body-local hands/feet) rides up together
log("heap snap: max lift %.1f mm, frames lifted %d" % (1000 * max(_sm.values()), sum(1 for v in _sm.values() if v > 0)))
