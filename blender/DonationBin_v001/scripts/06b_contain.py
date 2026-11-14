"""Containment pass (client: no body part through the bin's walls, flap, sill bar or panel).
blender -b anim_fix.blend --python 06b_contain.py -- out.blend
Per frame it measures how far the woman's evaluated mesh (body, clothes, shoes, hair) pokes through the bin geometry
for the phase she is in, and shifts her WHOLE body (root + IK hands + IK feet + poles) just clear of it, smoothed over
time. Rigid shifts only: the acting stays the same, she is simply a few cm further from the surface.
  outside, reaching in (1-159):   nothing in front of the wall face except inside the chute opening; nothing in the sill bar
  the dive (160-240):             nothing below the top of the sill bar where it crosses the front wall
  inside (241-2087):              inside the liner walls; behind the closed flap's inner face
  climbing out (2088-2150):       under the top of the cut opening while passing through the wall plane"""
import sys
import bpy, numpy as np
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
W = bpy.data.objects["Woman"]
MESH = [c for c in W.children_recursive if c.type == 'MESH' and not c.hide_render]
FY = sc["bin_front_y"]                       # outer front face (-0.60)
XI, YI = 0.738 - 0.012, 0.588 - 0.012        # liner inner faces with 1.2 cm skin
BAR_Z, BAR_Y = 1.135, FY - 0.068             # top of the sill bar, its front
CH_X, CH_Z0, CH_Z1 = 0.42, 1.12, 1.615       # chute opening
CUT_TOP = 0.97
BONES = ["root", "IK_hand.L", "IK_hand.R", "IK_foot.L", "IK_foot.R", "Pole_elbow.L", "Pole_elbow.R", "Pole_knee.L", "Pole_knee.R"]
BONES = [b for b in BONES if b in W.pose.bones]
BONES = [b for b in BONES if not (W.pose.bones[b].parent and W.pose.bones[b].parent.name in BONES)]
print("CONTAIN bones", BONES)

def verts():
    dg = bpy.context.evaluated_depsgraph_get(); out = []
    for o in MESH:
        e = o.evaluated_get(dg); me = e.to_mesh(); n = len(me.vertices)
        if n:
            a = np.empty(n * 3, dtype=np.float32); me.vertices.foreach_get("co", a); a = a.reshape(-1, 3)[::3]
            M = np.array(e.matrix_world); a = a @ M[:3, :3].T + M[:3, 3]; out.append(a)
        e.to_mesh_clear()
    return np.concatenate(out) if out else np.zeros((0, 3))

def need(f, v):
    """world shift (dx, dy, dz) and whether the feet move too"""
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    if f < 160:                                                       # outside: only the chute opening is open
        inopen = (np.abs(x) < CH_X - 0.01) & (z > CH_Z0 + 0.01) & (z < CH_Z1 - 0.01)
        limit = np.where((z < BAR_Z) & (z > 1.0) & (np.abs(x) < 0.47), BAR_Y, FY - 0.006)
        bad = (~inopen) & (y > limit) & (y < FY + 0.10) & (np.abs(x) < 0.80)
        dy = float(np.min(limit[bad] - y[bad])) if bad.any() else 0.0
        return Vector((0, dy, 0)), True
    if f <= 240:                                                      # the dive: over the sill bar
        bad = (y > BAR_Y - 0.01) & (y < FY + 0.04) & (z < BAR_Z + 0.012) & (np.abs(x) < 0.47) & (z > 0.9)
        up_ = float(np.max(BAR_Z + 0.012 - z[bad])) if bad.any() else 0.0
        hi = (y > FY - 0.03) & (y < -0.15) & (z > 1.575) & (np.abs(x) < 0.47)      # under the opening top / the open flap
        dn_ = float(np.min(1.575 - z[hi])) if hi.any() else 0.0
        dz = (up_ + dn_) / 2 if (up_ > 0 and dn_ < 0) else (up_ or dn_)
        return Vector((0, 0, dz)), True
    if 2088 <= f <= 2150:                                             # crawling out: under the cut opening's top
        bad = (y > FY - 0.04) & (y < FY + 0.05) & (z > CUT_TOP) & (np.abs(x) < 0.75)
        dz = float(np.min(CUT_TOP - z[bad])) if bad.any() else 0.0
        return Vector((0, 0, dz)), False
    if f > 2150: return Vector(), False
    up = z > 0.25                                                     # inside the bin
    flap = (np.abs(x) < 0.45) & (z > 1.10) & (z < 1.66)
    ylo = np.where(flap, -0.565, -YI)
    d = Vector()
    hx, lx = x[up].max(initial=-9), x[up].min(initial=9)
    if hx > XI and lx >= -XI: d.x = XI - hx
    elif lx < -XI and hx <= XI: d.x = -XI - lx
    hy = y[up].max(initial=-9); low = (ylo - y)[up]; ly = low.max(initial=-9)
    if hy > YI and ly <= 0: d.y = YI - hy
    elif ly > 0 and hy <= YI: d.y = ly
    return d, False

RANGE = list(range(1, 2151, 2))
S = {}; FEET = {}
def measure(frames):
    for f in frames:
        sc.frame_set(f); d, ft = need(f, verts()); S[f] = d; FEET[f] = ft
measure(RANGE)
def dense():
    """per-frame shift: envelope (max |need| over +-5 frames, same sign), then a 7-frame average"""
    D = {}
    for f in range(1, 2151):
        ks = [k for k in range(f - 5, f + 6) if k in S]
        d = Vector()
        for i in range(3):
            vals = [S[k][i] for k in ks]
            pos, neg = max(vals + [0.0]), min(vals + [0.0])
            d[i] = pos if pos > -neg else neg
        D[f] = d
    E = {}
    for f in range(1, 2151):
        ks = [D[k] for k in range(f - 3, f + 4) if k in D]
        E[f] = sum(ks, Vector()) / len(ks)
        for i in range(3):          # never weaker than the need at this frame
            n_ = D[f][i]
            if abs(n_) > abs(E[f][i]): E[f][i] = n_
    return E
for it in range(3):
    E = dense()
    fr = [f for f in range(1, 2151) if E[f].length > 0.0005]
    print("CONTAIN iter", it, "frames", len(fr), "max", round(max((E[f].length for f in fr), default=0) * 100, 1), "cm")
    if not fr: break
    keyf = sorted({g for f in fr for g in range(f - 2, f + 3) if 1 <= g <= 2150})
    orig = {}
    for g in keyf:
        sc.frame_set(g); orig[g] = {b: W.pose.bones[b].matrix.copy() for b in BONES}
    for g in keyf:
        sc.frame_set(g)
        d = E.get(g, Vector()) * 1.15
        feet = FEET.get(g - (g % 2 == 0), True) if g < 2088 or g > 2150 else False
        for b in BONES:
            if not feet and (b.startswith("IK_foot") or b.startswith("Pole_knee")): continue
            pb = W.pose.bones[b]; M = orig[g][b].copy(); M.translation += W.matrix_world.inverted().to_3x3() @ d
            pb.matrix = M; pb.keyframe_insert("location", frame=g, group=b)
            bpy.context.view_layer.update()
    S.clear(); FEET.clear(); measure(sorted({f for f in RANGE if any(abs(f - g) <= 2 for g in fr)}))
    for f in RANGE:
        if f not in S: S[f] = Vector(); FEET[f] = True
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("CONTAIN_DONE")
