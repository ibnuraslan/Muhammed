"""Ten people in the yawl: Briggs at the tiller, Sarah with Sophia in her lap on the stern sheets, six men at
the oars (double-banked on three thwarts), Richardson on the after thwart facing forward, watching the ship.

    people = man_the_boat(b, look=world_point, who="all"|"rowers"|..., density=0.5)

b is yawl.build(...) AFTER its root has its final matrix_world (it reads world points from it).
"""
import math
from mathutils import Vector, Matrix
import yawl, people as PP
from sitpose import Seat


def man_the_boat(b, look, density=0.5, who=None, stroke=0.0, hair=True):
    """stroke: 0 = catch (arms long, leaning toward the stern), 1 = finish (leaning back, hands at the chest)."""
    Mb = b["root"].matrix_world.copy()
    W = lambda p: Mb @ Vector(p)
    floor = yawl.FLOOR_Z + 0.011 + 0.135          # ankle height above the bottom boards (boot sole + heel under it)
    out = []
    who = who or ["Briggs", "Sarah", "Sophia", "Richardson", "rowers"]
    # ---- rowers: thwarts 0..2, both sides; facing aft (heading 180 in boat frame)
    if "rowers" in who:
        k = 1
        for i in range(3):
            x = yawl.THWARTS[i]
            for sg in (1, -1):
                p = PP.sailor(k % len(PP.CREW)); k += 1
                yy = sg * min(0.36, yawl.half_breadth_at(x, yawl.SEAT_Z + 0.4) - 0.39)
                st = Seat(p, W((x, yy, yawl.SEAT_Z)), 180.0, frame=Mb)
                st.legs({"L": W((x - 0.48, yy * 0.55 - 0.08, floor)), "R": W((x - 0.48, yy * 0.55 + 0.08, floor))}, knees_out=0.06)
                st.lean(fwd=9 - 14 * stroke)
                hnd = b["oar_handles"].get((i, sg))
                if hnd is not None:
                    hw = Mb @ hnd
                    loom = (Mb.to_3x3() @ b["oar_dirs"][(i, sg)]).normalized()     # handle -> rowlock
                    # both hands closed on the loom, a hand's width apart along it (outboard hand nearer the rowlock)
                    upw = Mb.to_3x3() @ Vector((0, 0, 1))
                    err1 = st.grip_bar("L" if sg < 0 else "R", hw + loom * 0.07, loom, over=upw)
                    err2 = st.grip_bar("R" if sg < 0 else "L", hw - loom * 0.05, loom, over=upw)
                    p.grip_err = max(err1, err2)
                st.head(look if i == 0 and sg > 0 else W((x - 3.0, sg * 0.2, 1.1)))
                p.dv_seat = st
                out.append((p, st))
    if "Richardson" in who:
        # the mate on the after thwart, facing aft toward the captain; feet tucked in under the stern sheets
        p = PP.sailor(0)
        x = yawl.THWARTS[3]
        st = Seat(p, W((x, 0.2, yawl.SEAT_Z)), 180.0, frame=Mb)
        st.legs({"L": W((x - 0.3, 0.16, floor)), "R": W((x - 0.3, 0.31, floor))}, knees_out=0.05)
        st.lean(fwd=6)
        st.hand_on_thigh("L"); st.hand_on_thigh("R")
        st.head(look)
        out.append((p, st))
    if "Briggs" in who:
        p = PP.briggs()
        st = Seat(p, W((-2.63, 0.3, yawl.SEAT_Z)), 0.0, frame=Mb)
        st.legs({"L": W((-2.27, 0.24, floor)), "R": W((-2.27, 0.08, floor))})
        st.lean(fwd=4)
        tip = b["tiller"]
        tdir = (Mb.to_3x3() @ Vector((1, 0, 0.1))).normalized()
        p.grip_err = st.grip_bar("R", Mb @ tip, tdir, radius=0.018, over=Mb.to_3x3() @ Vector((0, 0, 1)), elbow=(0.6, 0.3, -0.8))
        st.hand_on_thigh("L")
        st.head(look)
        p.brow_knit(0.6)
        out.append((p, st))
    sarah = None
    if "Sarah" in who:
        # on the port side bench, turned in toward the middle
        hbs = yawl.half_breadth_at(-1.95, yawl.SEAT_Z)
        p = PP.sarah()
        sy = -(hbs - 0.16)
        st = Seat(p, W((-1.95, sy, yawl.SEAT_Z)), 72.0, frame=Mb)
        st.legs({"L": W((-1.88, sy + 0.27, floor)), "R": W((-2.05, sy + 0.25, floor))}, knees_out=0.02)
        st.lean(fwd=8)
        sarah = (p, st)
        out.append((p, st))
    if "Sophia" in who and sarah:
        # Sophia on the aft bench at her mother's left, on the other side of the tiller from her father
        sp, sst = sarah
        p = PP.sophia()
        qx, qy = -2.69, -0.34
        st = Seat(p, W((qx, qy, yawl.SEAT_Z)), 10.0, frame=Mb)
        st.legs({"L": W((qx + 0.38, qy + 0.06, yawl.SEAT_Z + 0.02)), "R": W((qx + 0.38, qy - 0.04, yawl.SEAT_Z + 0.02))}, knees_out=0.05)
        st.lean(fwd=-2)
        st.hand_on_thigh("L"); st.hand_on_thigh("R")
        st.head(look, tilt=4)
        out.append((p, st))
        knee = st.M @ (p.h.bone_tail("upperleg02.L") + Vector((0, 0, 0.055)))
        sst.hand("L", knee, elbow=(0.7, 0.3, -0.6), grip=0)
        sst.hand_on_thigh("R")
        sst.head(look, share=0.6)
        sp.brow_knit(0.5)
    for p, st in out:
        if hasattr(p, "grip_err"):
            print(f"GRIP {p.name}: palm {p.grip_err * 1000:.0f} mm from the bar")
        st.place_finish(look, density=density, hair=hair)
        trim_under_seat(p, st.seat_world)
    return [p for p, _ in out]


def trim_under_seat(p, seat_w, r=0.42, boxes=None):
    """Coat tails and skirts that the person sits on are pressed onto the seat: shell vertices that would go below
    the seat surface, over the seat itself, are lifted to lie on it (the shells cannot fold, so they are flattened)."""
    import bpy
    from mathutils import Vector
    z0 = seat_w.z + 0.006
    seats = [o for o in bpy.data.objects if o.type == 'MESH' and any(k in o.name for k in ("thwart", "sternseat", "sideseat", "Chair", "settee"))]
    given = boxes; boxes = list(given or [])
    for o in ([] if given else seats):
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = Vector([min(v[i] for v in bb) for i in range(3)]); hi = Vector([max(v[i] for v in bb) for i in range(3)])
        if lo.z - 0.06 < seat_w.z < hi.z + 0.06:
            boxes.append((lo, hi))
    for o in p.objects:
        if o.type != 'MESH' or o is p.h.body or "src_verts" not in o:
            continue
        M = o.matrix_world; Mi = M.inverted(); ch = False
        for v in o.data.vertices:
            w = M @ v.co
            if w.z < z0 + 0.04 and (w.xy - seat_w.xy).length < r:
                for lo, hi in boxes:
                    top = hi.z + 0.006
                    if w.z >= top or w.z < lo.z - 0.25:
                        continue
                    if lo.x - 0.035 < w.x < hi.x + 0.035 and lo.y - 0.035 < w.y < hi.y + 0.035:
                        w.z = top; v.co = Mi @ w; ch = True            # lying on the seat (and rolling over its edge)
                        break
                    m = 0.06
                    if lo.x - m < w.x < hi.x + m and lo.y - m < w.y < hi.y + m and w.z > lo.z - 0.02:
                        # hanging just past the edge: keep the cloth 12 mm clear of the seat's side
                        dx = min(w.x - (lo.x - 0.012), (hi.x + 0.012) - w.x); dy = min(w.y - (lo.y - 0.012), (hi.y + 0.012) - w.y)
                        if 0 < dx and 0 < dy:
                            if dx < dy:
                                w.x = lo.x - 0.012 if w.x < (lo.x + hi.x) / 2 else hi.x + 0.012
                            else:
                                w.y = lo.y - 0.012 if w.y < (lo.y + hi.y) / 2 else hi.y + 0.012
                            v.co = Mi @ w; ch = True
                        break
        if ch:
            o.data.update()
