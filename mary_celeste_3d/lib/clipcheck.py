"""Automated clipping check: BVH triangle overlap between every character's meshes (body, clothes) and every
other mesh in the shot (props, the boat, oars, furniture, other people).

Characters are tagged by deveau.Deveau.finish (and lib5.people.Person.finish): o["person"] = name, o["hands"] = wrist points. A person's own body and clothes overlap
by design (shells) and are skipped; everything else is reported. Contacts are counted in intersecting triangle
pairs; a hand closed on an oar loom gives a few dozen, a body through a prop gives hundreds.

    report = check(shot, limit=60)      # prints CLIP lines, writes out/clip/<shot>.json, returns the list
"""
import os, json
import bpy
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out", "clip")
SKIP_PREFIX = ("Ocean", "far_sea", "band", "island", "cabin_air", "rock", "puddles", "deck_water", "SeaHaze")


CENTERS = {}
FLOATING = []          # (person, mm) hands that could not reach the bar they are meant to hold (set by boatcrew)
HAND_R = 0.10          # a contact whose triangles all lie this close to a wrist/knuckle is the hand, not the body


def _in_hands(o, pairs, first=True, r=None):
    import numpy as np
    h = o.get("hands")
    if not h:
        return False
    H = np.array(list(h), np.float32).reshape(-1, 3)
    idx = np.array([p[0] if first else p[1] for p in pairs])
    c = CENTERS[o.name][idx]
    d = np.min(np.linalg.norm(c[:, None, :] - H[None, :, :], axis=2), axis=1)
    return bool((d < (r or HAND_R)).all())


def _trees(objs, dg):
    """World-space BVH trees of the evaluated (posed, subdivided at viewport level) meshes."""
    import numpy as np
    t = {}
    for o in objs:
        try:
            oe = o.evaluated_get(dg); me = oe.to_mesh()
            n = len(me.vertices)
            if n == 0:
                oe.to_mesh_clear(); continue
            co = np.empty(n * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
            M = np.array(oe.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
            me.calc_loop_triangles()
            tri = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", tri)
            oe.to_mesh_clear()
            T = tri.reshape(-1, 3)
            t[o.name] = BVHTree.FromPolygons(w.tolist(), T.tolist(), all_triangles=True)
            CENTERS[o.name] = w[T].mean(1)
        except Exception as e:
            print("clipcheck: skip", o.name, e)
    return t


def check(shot, limit=60, hand_ok=("oar", "tiller", "doll", "Sophia", "letter", "thwart", "sternseat", "board", "Chair", "chair", "floor")):
    """limit: triangle pairs allowed for a deliberate contact (a hand on an oar, Sarah's hands on Sophia).
    Objects whose name contains one of hand_ok get that allowance; anything else must be 0 (above a 4-pair
    tolerance for coplanar touching)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and not o.name.startswith(SKIP_PREFIX)]
    people = {}
    for o in meshes:
        if "person" in o:
            people.setdefault(o["person"], []).append(o)
    others = [o for o in meshes if "person" not in o]
    trees = _trees(meshes, dg)
    found = []
    names = sorted(people)
    for i, pn in enumerate(names):
        mine = [o for o in people[pn] if o.name in trees]
        targets = others + [o for q in names[i + 1:] for o in people[q]]
        for a in mine:
            for b in targets:
                if b.name not in trees:
                    continue
                pairs = trees[a.name].overlap(trees[b.name])
                n = len(pairs)
                if n == 0:
                    continue
                # only the hand itself can grip (body mesh within HAND_R of a wrist/knuckle); clothing only at the cuff
                ra = HAND_R if a.name.endswith("_body") else 0.07
                rb = HAND_R if b.name.endswith("_body") else 0.07
                grip = _in_hands(a, pairs, r=ra) or ("person" in b and _in_hands(b, pairs, first=False, r=rb))
                allowed = limit if any(k in b.name or k in b.get("person", "") for k in hand_ok) else 4
                import numpy as np
                c = CENTERS[a.name][np.array([q[0] for q in pairs])]
                at = [round(float(v), 3) for v in c.mean(0)]; span = [round(float(v), 3) for v in (c.max(0) - c.min(0))]
                found.append(dict(person=pn, part=a.name, other=b.name, pairs=n, grip=grip, ok=grip or n <= allowed, at=at, span=span))
    bad = [f for f in found if not f["ok"]] + [dict(person=n, part=n + " hand", other="(nothing: floating)", pairs=0, ok=False, gap_m=g) for n, g in FLOATING]
    for n, g in FLOATING:
        print(f"CLIP {n} hand floating {g * 1000:.0f} mm off its bar")
    for f in found:
        print(("CLIP " if not f["ok"] else "touch ") + f"{f['part']} x {f['other']}: {f['pairs']}  at {f['at']} span {f['span']}")
    print(f"CLIPCHECK {shot}: {len(bad)} clipping, {len(found) - len(bad)} contacts within allowance, {len(names)} people")
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(shot=shot, bad=bad, contacts=[f for f in found if f["ok"]]), open(os.path.join(OUT, shot + ".json"), "w"), indent=1)
    return bad


def report_floating(person, gap_m, limit=0.015):
    """Hook for pose helpers that aim a hand at a bar/handle: call with the palm-to-target residual after the IK.
    Gaps over `limit` become CLIP entries in the next check() ("hand floating N mm off its bar")."""
    if gap_m > limit:
        FLOATING.append((person, float(gap_m)))
