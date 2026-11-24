"""People in the Cladh Hallan film (all procedural MakeHuman + fitted fieldwear; never shown face-on).

2001 excavation team (same costume in every shot):
  Director   tall, grey-haired, dark waxed field coat, dark trousers                 (the site director, seen from behind)
  DiggerA    fair hair tied back look (short), bottle-green hip-length waterproof smock, loose khaki work trousers    (kneels with a trowel)
  DiggerB    dark hair, red hip-length waterproof smock, loose navy trousers                         (kneels / carries buckets)
  DiggerC    sandy hair, navy knit sweater, grey trousers                             (at the sieve)
Lab:
  Osteologist  brown hair, white lab coat over a blue shirt                           (from behind / profile in shadow)
"""
import math
import bpy
from mathutils import Vector, Matrix
import modern as MD
import acts as AC
import dig as G


class Director(MD.ModernMan):
    TROUSER_EASE = 1.3; TROUSER_EXTRA = 0.03
    GENDER = 1.0; MUSCLE = 0.5; WEIGHT = 0.5; HEIGHT = 0.72
    HAIR = (0.78, 0.04); HAIR_LEN = (0.01, 0.02); HAIRLINE = 0.012
    SHIRT = (0.35, 0.38, 0.42); JACKET = "coat"; JACKET_COL = (0.05, 0.055, 0.035)
    TROUSERS = (0.04, 0.04, 0.045); SHOES = (0.03, 0.02, 0.012)

    def __init__(self, name="Director", **kw):
        super().__init__(name, years=45, **kw)


class DiggerA(MD.ModernMan):
    TROUSER_EASE = 1.3; TROUSER_EXTRA = 0.03
    GENDER = 0.0; MUSCLE = 0.45; WEIGHT = 0.45; HEIGHT = 0.42
    HAIR = (0.75, 0.45); HAIR_LEN = (0.03, 0.06)
    SHIRT = (0.5, 0.5, 0.48); JACKET = "cagoule"; JACKET_COL = (0.03, 0.08, 0.05)
    TROUSERS = (0.2, 0.17, 0.1); SHOES = (0.05, 0.035, 0.02)

    def __init__(self, name="DiggerA", **kw):
        super().__init__(name, years=26, **kw)


class DiggerB(MD.ModernMan):
    TROUSER_EASE = 1.3; TROUSER_EXTRA = 0.03
    GENDER = 1.0; MUSCLE = 0.55; WEIGHT = 0.5; HEIGHT = 0.55
    HAIR = (0.08, 0.04); HAIR_LEN = (0.015, 0.03)
    SHIRT = (0.2, 0.2, 0.22); JACKET = "cagoule"; JACKET_COL = (0.32, 0.03, 0.025)
    TROUSERS = (0.025, 0.03, 0.06); SHOES = (0.03, 0.02, 0.012)

    def __init__(self, name="DiggerB", **kw):
        super().__init__(name, years=30, **kw)


class DiggerC(MD.ModernMan):
    TROUSER_EASE = 1.3; TROUSER_EXTRA = 0.03
    GENDER = 1.0; MUSCLE = 0.5; WEIGHT = 0.55; HEIGHT = 0.5
    HAIR = (0.55, 0.3); HAIR_LEN = (0.01, 0.025); FACIAL = "stubble"
    SHIRT = (0.3, 0.3, 0.3); JACKET = None; SWEATER = (0.02, 0.03, 0.07)
    TROUSERS = (0.12, 0.12, 0.12); SHOES = (0.03, 0.02, 0.012)

    def __init__(self, name="DiggerC", **kw):
        super().__init__(name, years=35, **kw)


class Osteologist(MD.ModernMan):
    TROUSER_EASE = 1.3; TROUSER_EXTRA = 0.03
    GENDER = 0.0; MUSCLE = 0.45; WEIGHT = 0.45; HEIGHT = 0.45
    HAIR = (0.22, 0.12); HAIR_LEN = (0.035, 0.07)
    SHIRT = (0.4, 0.5, 0.65); JACKET = "labcoat"; JACKET_COL = (0.8, 0.8, 0.78)
    TROUSERS = (0.05, 0.05, 0.06); SHOES = (0.03, 0.02, 0.012)

    def __init__(self, name="Osteologist", **kw):
        super().__init__(name, years=38, **kw)


def kneel_trowel(cls, knees, heading, work, density=0.5, lean=58, trowel_side="R"):
    """Kneeling digger on the (uneven) ground, leaning over `work` (x, y): right hand with a trowel on the surface,
    left hand flat on the ground beside it. Returns the Kneel act; trowel attached to the right palm."""
    m = cls()
    z0 = G.H(*knees)
    st = AC.Kneel(m, knees, heading, lean=lean, sit_back=True)
    wz = G.H(*work) - z0
    f = Vector((math.cos(math.radians(heading)), math.sin(math.radians(heading)), 0))
    s = Vector((f.y, -f.x, 0))           # his right
    w = Vector((work[0], work[1], 0)) - Vector((knees[0], knees[1], 0))
    pR = Vector((knees[0], knees[1], 0)) + w + s * 0.08 + Vector((0, 0, wz + 0.05))
    pL = Vector((knees[0], knees[1], 0)) + w * 0.8 - s * 0.22 + Vector((0, 0, wz + 0.035))
    st.hand("R", pR, elbow=(0.5, 0.3, -0.8), grip=0.85)
    st.hand("L", pL, elbow=(0.6, 0.2, -0.8), curl=12)
    st.head_to((work[0], work[1], z0 + wz), share=0.9)
    st.finish(look=(work[0], work[1], z0 + wz), density=density)
    G.lift(st, z0)
    st.M = Matrix.Translation((0, 0, z0)) @ st.M
    bpy.context.view_layer.update()
    # trowel in the right fist: handle across the palm (little finger -> index), blade out past the index side, flat side down
    attach_trowel(st, "R")
    return st


def stand(cls, feet, heading, look, density=0.5, hands="sides", walk=None):
    m = cls()
    z0 = G.H(*feet)
    st = AC.Stand(m, feet, heading)
    if walk is not None:
        st.walk(walk)
    elif hands == "front":
        st.hands_front()
    st.head_to((look[0], look[1], look[2] - z0), share=0.8)
    st.finish(look=(look[0], look[1], look[2] - z0), density=density)
    G.lift(st, z0)
    return st


def attach_trowel(st, side="R"):
    import numpy as np
    h = st.m.h
    M = st.M
    P = M @ h.bone_tail(f"metacarpal3.{side}").lerp(h.bone_head(f"metacarpal3.{side}"), 0.35)
    a = (M @ h.bone_head(f"finger2-1.{side}") - M @ h.bone_head(f"finger5-1.{side}")).normalized()
    root = G.trowel((0, 0, 0))
    bpy.context.view_layer.update()
    me = [o for o in root.children_recursive if o.type == "MESH"][0]
    Mw = np.array(me.matrix_world)
    co = np.array([v.co for v in me.data.vertices]); W = co @ Mw[:3, :3].T + Mw[:3, 3]
    x = W[:, 0]; lo, hi = x.min(), x.max(); mid = (lo + hi) / 2
    wl = np.ptp(W[x < mid, 1]); wh = np.ptp(W[x > mid, 1])
    blade_pos = wh > wl                        # blade = wider half
    hx = (mid + lo) / 2 if blade_pos else (mid + hi) / 2      # handle centre along x
    hsel = (x < mid) if blade_pos else (x > mid)
    hc = Vector(W[hsel].mean(0)); hc.x = hx
    ax = Vector((1, 0, 0)) if blade_pos else Vector((-1, 0, 0))
    # rotation taking local blade axis -> a, local up (z) -> world up made orthogonal to a
    up = Vector((0, 0, 1)); up = (up - a * up.dot(a)).normalized()
    side_ = a.cross(up)
    R_world = Matrix((a, side_, up)).transposed()
    lz = Vector((0, 0, 1)); ly = lz.cross(ax)
    R_local = Matrix((ax, ly, lz)).transposed()
    R = (R_world @ R_local.inverted()).to_4x4()
    # search a small offset of the handle inside the fist that minimises overlap with the hand/fingers
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    body = [o for o in st.m.objects if o.type == 'MESH' and o.name.endswith("_body")][0]
    bt = BVHTree.FromObject(body, dg)
    d = (M @ h.bone_head(f"finger3-1.{side}") - M @ h.bone_head(f"wrist.{side}")).normalized()
    n = a.cross(d).normalized()
    best = None
    for k1 in (-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03):
        for k2 in (-0.01, 0.0, 0.015, 0.03, 0.045):
            for k3 in (-0.02, 0.0, 0.02):
                root.matrix_world = Matrix.Translation(P + n * k1 + d * k2 + a * k3) @ R @ Matrix.Translation(-hc)
                bpy.context.view_layer.update()
                tt = BVHTree.FromObject(me, bpy.context.evaluated_depsgraph_get())
                c = len(bt.overlap(tt))
                if best is None or c < best[0]:
                    best = (c, k1, k2, k3)
    c, k1, k2, k3 = best
    root.matrix_world = Matrix.Translation(P + n * k1 + d * k2 + a * k3) @ R @ Matrix.Translation(-hc)
    print("TROWEL fit overlap", c, best)
    for o in root.children_recursive:
        o.name = "trowel"
    return root
