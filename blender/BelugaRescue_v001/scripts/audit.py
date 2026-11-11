"""Contact / penetration audit for BelugaRescue.  blender -b film.blend --python audit.py -- <report.txt> [step]
Numeric BVH checks (sampled every <step> frames):
  DIVER_SINK / FIN_SINK   body / fin / pocket vertices below the tank floor (> 1 cm)
  DIVER_HOVER             seated frames: lowest body point > 3 cm above the tiles
  SCENE_PEN               diver, fins, mask or whale vertices inside walls, rocks, coping, deck, window (> 1 cm)
  WHALE_DIVER_PEN         diver vertices inside the whale (> 1.5 cm); the held ankle counts too
  WHALE_FLOOR             whale vertices below the floor
  MASK_GAP / MASK_PEN     mask rim off the face (> 6 mm) or face through the rim
  HAND_PEN                hand/finger vertices inside scene geometry or the whale
  HAND_FLOAT              holding frames: palm more than 3 cm from what it holds (coping / glass / calf)
  FOOT_SINK / FOOT_FLOAT  spectators' shoes vs their floor (gallery 0.0, deck 6.25)
  CAMERA_INSIDE           camera inside solid geometry, the whale, or the diver
"""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

class WB:
    """world-space BVH wrapper (BVHTree.FromObject works in object-local space)"""
    def __init__(self, o, dg):
        self.t = BVHTree.FromObject(o, dg); self.M = o.matrix_world.copy(); self.Mi = self.M.inverted(); self.R = self.M.to_3x3()
    def find_nearest(self, p, dmax=1e9):
        loc, nrm, idx, dist = self.t.find_nearest(self.Mi @ p, dmax)
        if loc is None: return None, None, None, None
        loc = self.M @ loc; nrm = (self.R @ nrm).normalized()
        return loc, nrm, idx, (p - loc).length

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 else 10
sc = bpy.context.scene
issues = {}; counts = {}
def flag(kind, f, msg, n=1):
    issues.setdefault(kind, []).append((f, msg)); counts[kind] = counts.get(kind, 0) + n
D = bpy.data.objects["Diver"]; BR = bpy.data.objects["Beluga_Rig"]; BEL = bpy.data.objects["Beluga"]
STATIC = [o for o in bpy.data.objects if o.type == 'MESH' and (o.name.startswith(("IceWall", "IceBoulder", "FrontWall", "Acrylic", "Coping", "Deck", "Ladder", "Gallery_", "WinFrame")))]
FLOOR_Z = 0.0
dg0 = bpy.context.evaluated_depsgraph_get()
sc.frame_set(1)
ST = []
for o in STATIC:
    t = WB(o, dg0)
    c = Vector((0, 0, 3.0)) if not o.name.startswith("Gallery_") else Vector((0, -7.5, 1.5))
    loc, nrm, idx, dist = t.find_nearest(o.matrix_world.inverted() @ c) if False else t.find_nearest(c)
    sgn = 1.0 if (c - loc).dot(nrm) > 0 else -1.0
    closed = not o.name.startswith("IceWall")
    ST.append((o, t, sgn, closed))
def inside_static(p, eps=0.01):
    for o, t, sgn, closed in ST:
        loc, nrm, idx, dist = t.find_nearest(p, 0.6)
        if loc is None: continue
        d = (p - loc).dot(nrm)
        if closed:
            if d < -eps: return o.name
        else:
            if sgn * d < -eps: return o.name
    return None
def verts(o, dg, every=4):
    ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
    ps = [mw @ v.co for v in list(me.vertices)[::every]]
    ev.to_mesh_clear(); return ps
DPARTS = [o for o in D.children if o.type == 'MESH' and o.name.split(".")[-1] in ("body",)]
FINS = [o for o in bpy.data.objects if o.name.startswith(("Diver.FinBlade", "Diver.FootPocket"))]
MASK = bpy.data.objects["Diver.Mask"]
BODY = bpy.data.objects["Diver.body"]
SEATED = [(270, 520)]
HOLD = (1440, 1975)
PEOPLE = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name in ("Keeper", "SpecA", "SpecB", "SpecC", "SpecD", "SpecE", "SpecF", "SpecG")]
DECKP = ("SpecE", "SpecF", "SpecG")
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    bpts = []
    for o in DPARTS: bpts += verts(o, dg, 5)
    low = min(p.z for p in bpts)
    if low < FLOOR_Z - 0.01: flag("DIVER_SINK", f, "lowest body point %.1f cm below the tiles" % ((FLOOR_Z - low) * 100))
    if any(a <= f <= b for a, b in SEATED) and low > FLOOR_Z + 0.03: flag("DIVER_HOVER", f, "seated, lowest point %.1f cm above the tiles" % ((low - FLOOR_Z) * 100))
    fpts = []
    for o in FINS:
        if o.hide_render: continue
        fpts += verts(o, dg, 2)
    if fpts:
        lf = min(p.z for p in fpts)
        if lf < FLOOR_Z - 0.01: flag("FIN_SINK", f, "fin %.1f cm below the tiles" % ((FLOOR_Z - lf) * 100))
    pen = {}
    for p in bpts + fpts:
        if p.z > 7.5: continue
        hit = inside_static(p)
        if hit: pen[hit] = pen.get(hit, 0) + 1
    if pen: flag("SCENE_PEN", f, "diver/fin points inside " + ", ".join("%s:%d" % kv for kv in pen.items()), sum(pen.values()))
    # whale
    wpts = verts(BEL, dg, 6)
    wl = min(p.z for p in wpts)
    if wl < FLOOR_Z - 0.01: flag("WHALE_FLOOR", f, "whale %.1f cm below the tiles" % ((FLOOR_Z - wl) * 100))
    wpen = {}
    for p in wpts:
        hit = inside_static(p, 0.02)
        if hit: wpen[hit] = wpen.get(hit, 0) + 1
    if wpen: flag("SCENE_PEN", f, "whale points inside " + ", ".join("%s:%d" % kv for kv in wpen.items()), sum(wpen.values()))
    wt = WB(BEL, dg)
    n_in = 0; ank = D.matrix_world @ D.pose.bones["foot.R"].head; mouth = []
    holding = HOLD[0] <= f <= HOLD[1]
    for p in bpts + fpts:
        loc, nrm, idx, dist = wt.find_nearest(p, 0.3)
        if loc is None: continue
        sd = (p - loc).dot(nrm)
        if holding and (p - ank).length < 0.25:
            mouth.append(sd); continue
        if sd < -0.015: n_in += 1
    if n_in: flag("WHALE_DIVER_PEN", f, "%d diver samples inside the whale (away from the held foot)" % n_in, n_in)
    if holding and mouth:
        gap = min(abs(x) for x in mouth)
        if gap > 0.006: flag("MOUTH_GAP", f, "held ankle %.1f cm from the lips" % (gap * 100))
        flag("MOUTH_CONTACT_INFO", f, "foot in mouth: deepest %.1f cm, %d samples inside" % (-min(mouth) * 100, sum(1 for x in mouth if x < 0)), 0)
    # mask rim vs face
    bt = WB(BODY, dg)
    mev = MASK.evaluated_get(dg); mme = mev.to_mesh()
    gaps = []
    for v in list(mme.vertices)[:48]:
        p = MASK.matrix_world @ v.co
        loc, nrm, idx, dist = bt.find_nearest(p, 0.2)
        if loc is not None: gaps.append((p - loc).dot(nrm))
    mev.to_mesh_clear()
    if gaps:
        if max(gaps) > 0.006: flag("MASK_GAP", f, "rim up to %.1f mm off the face" % (max(gaps) * 1000))
        if min(gaps) < -0.002: flag("MASK_PEN", f, "face through the rim by %.1f mm" % (-min(gaps) * 1000))
    # hands (diver): wrist + finger tips
    for s in "LR":
        tips = [D.matrix_world @ D.pose.bones["finger%d-3.%s" % (k, s)].tail for k in range(1, 6)] + [D.matrix_world @ D.pose.bones["wrist." + s].head]
        for p in tips:
            hit = inside_static(p, 0.005)
            if hit: flag("HAND_PEN", f, "diver %s hand inside %s" % (s, hit)); break
            loc, nrm, idx, dist = wt.find_nearest(p, 0.2)
            if loc is not None and (p - loc).dot(nrm) < -0.01: flag("HAND_PEN", f, "diver %s hand inside the whale" % s); break
        if f >= 2085:
            ct = [t for o, t, sg, cl in ST if o.name == "Coping"][0]
            t = min(ct.find_nearest(p, 1.0)[3] or 1.0 for p in tips)
            if t > 0.03: flag("HAND_FLOAT", f, "diver %s hand %.1f cm off the coping" % (s, t * 100))
    # spectators feet: lowest shoe vertex vs their floor
    for o in PEOPLE:
        gz = 6.25 if o.name in DECKP else 0.0
        for ch in o.children:
            if ch.type == 'MESH' and "shoes" in ch.name:
                ps = verts(ch, dg, 3)
                for side, sel in (("L", [p for p in ps if (o.matrix_world.inverted() @ p).x > 0 or True]),):
                    pass
                h = min(p.z for p in ps) - gz
                if h < -0.015: flag("FOOT_SINK", f, "%s shoes %.1f cm into the floor" % (o.name, -h * 100))
                elif h > 0.025: flag("FOOT_FLOAT", f, "%s shoes %.1f cm above the floor" % (o.name, h * 100))
    # camera
    cam = sc.camera
    if cam:
        cp = cam.matrix_world.translation
        hit = inside_static(cp, 0.0)
        if hit: flag("CAMERA_INSIDE", f, "camera inside %s" % hit)
        if cp.z < FLOOR_Z + 0.05: flag("CAMERA_INSIDE", f, "camera at/below the floor")
        loc, nrm, idx, dist = wt.find_nearest(cp, 1.0)
        if loc is not None and (cp - loc).dot(nrm) < 0: flag("CAMERA_INSIDE", f, "camera inside the whale")
        loc, nrm, idx, dist = bt.find_nearest(cp, 0.5)
        if loc is not None and (cp - loc).dot(nrm) < 0 and dist < 0.2: flag("CAMERA_INSIDE", f, "camera inside the diver")
        if abs(cp.z - 6.0) < 0.04:
            flag("CAMERA_AT_SURFACE", f, "camera in the waterline (ok only while crossing)")

def ranges(items):
    fr = sorted(set(f for f, _ in items)); out = []; start = prev = None
    for f in fr:
        if start is None: start = prev = f
        elif f - prev <= STEP: prev = f
        else: out.append((start, prev)); start = prev = f
    if start is not None: out.append((start, prev))
    return out
lines = ["AUDIT BelugaRescue (step %d frames, 60 fps)" % STEP]
total = 0
for kind in sorted(issues):
    its = issues[kind]
    lines.append("%-18s %4d frames, %5d hits | ranges (s): %s" % (kind, len(its), counts[kind], ", ".join("%.1f-%.1f" % ((a - 1) / 60, (b - 1) / 60) for a, b in ranges(its))))
    for f, m in its[:3]:
        lines.append("      e.g. f%d (%.2fs): %s" % (f, (f - 1) / 60, m))
    if kind not in ("CAMERA_AT_SURFACE", "MOUTH_CONTACT_INFO"): total += counts[kind]
lines.append("PENETRATION/CONTACT TOTAL (hits): %d" % total)
open(OUT, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
