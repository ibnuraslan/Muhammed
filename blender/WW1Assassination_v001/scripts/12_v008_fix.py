# v008 scene fixes, exec'd by 12_v008.py (helpers fcurves/drop_curves/hide_always come from there).
import bpy, math
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- 2. props that read as floating or pierce bodies: dropped (simplest staging)
hide_always(O["Parasol"])                       # items 1, 3: a parasol on a stick through thigh, door and body
for o in O:
    if o.name.startswith("Plume_"): hide_always(o)   # item 24: grey oval smoke blobs scattered over the map
print("PROPS parasol + map blobs removed")

# ---------------------------------------------------------------- 3. continuity: the following car is the same green motorcade car (item 16)
def principled(m):
    if m and m.use_nodes:
        return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
src = {s.material.name.replace("Car1_", ""): s.material for s in O["Car1_Body"].material_slots if s.material}
for s in O["Car2_Body"].material_slots:
    m = s.material
    if not m: continue
    key = m.name.replace("Car2_", "")
    base = key.rsplit(".", 1)[0]
    cand = src.get(key) or next((v for k, v in src.items() if k.rsplit(".", 1)[0] == base), None)
    if cand: s.material = cand
print("CAR2 repainted to the motorcade green")

# ---------------------------------------------------------------- 4. muzzle flash light: no bleached face (item 20)
ml = O["MuzzleLight"].data
for f in fcurves(ml):
    if f.data_path == "energy":
        for k in f.keyframe_points:
            k.co[1] *= 0.12; k.handle_left[1] *= 0.12; k.handle_right[1] *= 0.12
ml.shadow_soft_size = 0.15
print("MUZZLE light tamed")

# ---------------------------------------------------------------- 5. crowd waves/cheers: hand at head height with the elbow bent out (items 2, 10, 11)
def loc_curves(arm, bone):
    c = {}
    for f in fcurves(arm):
        if f.data_path == f'pose.bones["{bone}"].location': c[f.array_index] = f
    return c
nfix = 0
for arm in [o for o in O if o.type == 'ARMATURE' and o.name.startswith("Crowd")]:
    BNs = arm.data.bones
    rc = loc_curves(arm, "root")
    Rr = BNs["root"].matrix_local.to_3x3(); hr = BNs["root"].head_local
    for side in "LR":
        hb = BNs["IK_hand." + side]; Rh = hb.matrix_local.to_3x3(); hh = hb.head_local
        hc = loc_curves(arm, "IK_hand." + side)
        if len(hc) < 3 or len(rc) < 3: continue
        def remap(f):
            L = Vector((hc[0].evaluate(f), hc[1].evaluate(f), hc[2].evaluate(f)))
            P = hh + Rh @ L
            RP = hr + Rr @ Vector((rc[0].evaluate(f), rc[1].evaluate(f), rc[2].evaluate(f)))
            rel = P - RP
            if rel.z < 0.3: return None
            frac = max(0.0, min(1.0, (rel.z + 0.08) / 1.05))
            h = Vector((rel.x, rel.y, 0.0)); r = h.length
            hd = h.normalized() if r > 1e-4 else Vector((1, 0, 0))
            newrel = hd * (r + 0.2 * frac)
            newrel.z = -0.08 + frac * 0.8
            return Rh.inverted() @ (RP + newrel - hh)
        new = {}
        for ax in range(3):
            for kp in hc[ax].keyframe_points:
                f = kp.co[0]
                if f not in new: new[f] = remap(f)
        for ax in range(3):
            for kp in hc[ax].keyframe_points:
                Ln = new[kp.co[0]]
                if Ln is None: continue
                d = Ln[ax] - kp.co[1]; kp.co[1] = Ln[ax]; kp.handle_left[1] += d; kp.handle_right[1] += d
        nfix += sum(1 for v in new.values() if v is not None)
        for c in hc.values(): c.update()
print("CROWD arms re-posed at", nfix, "keys")

# ---------------------------------------------------------------- 6. city back on for the closing shot at the corner (item 25)
END0 = 1681
for o in O:
    for f in fcurves(o):
        if f.data_path in ("hide_render", "hide_viewport"):
            a, b = f.evaluate(1), f.evaluate(1600)
            if a != b:
                kp = f.keyframe_points
                kp.insert(END0 - 1, b, options={'FAST'}); kp.insert(END0, a, options={'FAST'})
                for k in kp: k.interpolation = 'CONSTANT'
                f.update()
for idb in list(bpy.data.lights) + [sc.world]:
    for f in fcurves(idb):
        a, b = f.evaluate(1000), f.evaluate(1600)
        if abs(a - b) > 1e-6:
            f.keyframe_points.insert(END0 - 1, b, options={'FAST'}); f.keyframe_points.insert(END0, a, options={'FAST'}); f.update()
print("ENDING city visible from", END0)
