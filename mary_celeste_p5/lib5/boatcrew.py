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
    floor = yawl.FLOOR_Z + 0.011 + 0.085          # ankle height above the bottom boards
    out = []
    who = who or ["Briggs", "Sarah", "Sophia", "Richardson", "rowers"]
    # ---- rowers: thwarts 0..2, both sides; facing aft (heading 180 in boat frame)
    if "rowers" in who:
        k = 1
        for i in range(3):
            x = yawl.THWARTS[i]
            for sg in (1, -1):
                p = PP.sailor(k % len(PP.CREW)); k += 1
                st = Seat(p, W((x, sg * 0.43, yawl.SEAT_Z)), 180.0, frame=Mb)
                st.legs({"L": W((x - 0.5, sg * 0.43 - 0.1, floor)), "R": W((x - 0.5, sg * 0.43 + 0.1, floor))}, knees_out=0.12)
                st.lean(fwd=24 - 34 * stroke)
                hnd = b["oar_handles"].get((i, sg))
                if hnd is not None:
                    hw = Mb @ hnd
                    # both hands on the loom, a hand's width apart
                    side_dir = (Mb.to_3x3() @ Vector((0, sg, 0))).normalized()
                    st.hand("L" if sg < 0 else "R", hw + side_dir * 0.06, elbow=(0.7, 0.4, -0.6))
                    st.hand("R" if sg < 0 else "L", hw - side_dir * 0.08, elbow=(0.7, 0.4, -0.6))
                st.head(look if i == 0 and sg > 0 else W((x - 3.0, sg * 0.2, 1.1)))
                p.dv_seat = st
                out.append((p, st))
    if "Richardson" in who:
        p = PP.sailor(0)
        x = yawl.THWARTS[3]
        st = Seat(p, W((x, 0.25, yawl.SEAT_Z)), 0.0, frame=Mb)
        st.legs({"L": W((x + 0.45, 0.35, floor)), "R": W((x + 0.45, 0.15, floor))})
        st.lean(fwd=6, twist=-6)
        st.hand_on_thigh("L"); st.hand_on_thigh("R")
        st.head(look)
        out.append((p, st))
    if "Briggs" in who:
        p = PP.briggs()
        st = Seat(p, W((-2.55, 0.26, yawl.SEAT_Z)), 0.0, frame=Mb)
        st.legs({"L": W((-2.1, 0.36, floor)), "R": W((-2.1, 0.16, floor))})
        st.lean(fwd=4)
        tip = b["tiller"]
        st.hand("R", Mb @ tip, elbow=(0.6, 0.3, -0.8))
        st.hand_on_thigh("L")
        st.head(look)
        p.brow_knit(0.6)
        out.append((p, st))
    sarah = None
    if "Sarah" in who:
        p = PP.sarah()
        st = Seat(p, W((-2.2, -0.3, yawl.SEAT_Z)), 10.0, frame=Mb)
        st.legs({"L": W((-1.78, -0.2, floor)), "R": W((-1.8, -0.4, floor))}, knees_out=0.02)
        st.lean(fwd=10)
        sarah = (p, st)
        out.append((p, st))
    if "Sophia" in who and sarah:
        sp, sst = sarah
        h = sp.h
        # her lap: midpoint of Sarah's thighs, a little toward the knees, in world space
        lapL = sst.M @ h.bone_head("upperleg02.L"); lapR = sst.M @ h.bone_head("upperleg02.R")
        lap = (lapL + lapR) / 2 + Vector((0, 0, 0.075))
        p = PP.sophia()
        st = Seat(p, lap, 15.0 + 70.0, frame=Mb)          # sideways across her mother's lap, facing the side
        fwd = (Mb.to_3x3() @ Vector((math.cos(math.radians(85)), math.sin(math.radians(85)), 0)))
        st.legs({"L": lap + fwd * 0.22 + Vector((0, 0, -0.12)), "R": lap + fwd * 0.22 + Vector((0.05, 0, -0.14))})
        st.lean(fwd=-4)
        st.hand_on_thigh("L"); st.hand_on_thigh("R")
        st.head(look, tilt=4)
        out.append((p, st))
        # Sarah holds her: one hand round her back to her far side, the other over her knees
        back = st.M @ (p.h.bone_head("spine03") + Vector((0.09, 0.07, 0.0)))
        knees = st.M @ (p.h.bone_tail("upperleg02.L") + Vector((0, 0, 0.06)))
        sst.hand("R", back, elbow=(0.8, 0.2, -0.5), grip=0)
        sst.hand("L", knees, elbow=(0.7, 0.3, -0.6), grip=0)
        sst.head(look, share=0.6)
        sp.brow_knit(0.5)
    for p, st in out:
        st.place_finish(look, density=density, hair=hair)
    return [p for p, _ in out]
