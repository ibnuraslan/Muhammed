"""Part 1 (VO lines 1-16): "Monday morning..." -> "...more than two years."  37 shots.

Each shot function builds its set and cast and returns the camera move:
    dict(a=(loc, target), b=(loc, target), lens=, fstop=, focus=, cine=, extra=[...])
Durations are first estimates from the VO (~145 wpm); they are re-timed to the recorded VO later.
House rules: no face close-ups (backs, OTS, profiles in half shadow, silhouettes); every hand belongs to a person in
frame; nothing moves by itself (the camera carries the motion); clipcheck 0.
"""
import math, os
import bpy
from mathutils import Vector, Matrix
import sets as ST, sets2 as S2, modern as MD, acts as AC, props as PR
import look

HAIR = float(os.environ.get("HAIR", "0.6"))
V = Vector


def _cast(cls, night=False, **kw):
    return cls(night=night, **kw) if "night" in cls.__init__.__code__.co_varnames else cls(**kw)


def stool(loc, h=0.62, name="stool"):
    """Round workshop stool: wooden seat (r 0.17) on a steel centre column and a ring foot (legs stay clear of the thighs)."""
    import ship as SH
    wood = ST.flat(name + "_seat", (0.12, 0.07, 0.04), 0.6); st = ST.flat(name + "_leg", (0.05, 0.05, 0.05), 0.4, 0.7)
    SH.cyl(name + "_seat", (loc[0], loc[1], h - 0.035), (loc[0], loc[1], h), 0.17, mat=wood, verts=32)
    SH.cyl(name + "_column", (loc[0], loc[1], 0.02), (loc[0], loc[1], h - 0.035), 0.025, mat=st, verts=12)
    SH.cyl(name + "_foot", (loc[0], loc[1], 0.0), (loc[0], loc[1], 0.02), 0.2, mat=st, verts=32)


# ============================================================================ L1  Monday morning
def S01():
    A = S2.exterior("dawn")
    import city
    city.district("dawn", skip=[(-65, 65, -40, 25)])
    city.dress_street(A, "dawn", haze=0.0)
    ST.haze_box("aerial_haze", (0, 0, 30), (700, 700, 60), density=0.0006, aniso=0.5, color=(0.85, 0.88, 1.0))
    # blue hour over the diamond district: the drone pushes in and down toward the Diamond Center
    return dict(a=((-150.0, -230.0, 120.0), (0.0, 5.0, 8.0)), b=((-62.0, -105.0, 48.0), (0.0, 4.0, 10.0)), lens=30)


def S02():
    A = ST.vault_complex("wreck")
    m = MD.Porter(); st = AC.Stand(m, (0.15, -6.7), 90); st.walk(0.3)
    st.finish(look=(0, 0, 1.4), density=HAIR)
    return dict(a=((-0.3, -9.1, 2.35), (0.1, -3.0, 1.15)), b=((-0.25, -8.6, 2.15), (0.1, -2.6, 1.15)), lens=26)


# ============================================================================ L2  lights on, door open
def S03():
    A = ST.vault_complex("wreck")
    m = MD.Porter(); st = AC.Stand(m, (0.2, -2.95), 90); st.hands_front(); st.head_to((0, 1.5, 1.2))
    st.finish(look=(0, 1.5, 1.0), density=HAIR)
    return dict(a=((0.78, -4.15, 1.74), (-0.15, 0.8, 1.15)), b=((0.72, -3.85, 1.72), (-0.15, 1.0, 1.1)), lens=30,
                fstop=4.0, focus=(0, -0.3, 1.0))


def S04():
    ST.vault_complex("wreck")
    return dict(a=((2.25, 0.45, 1.7), (-1.3, 3.9, 0.7)), b=((0.9, 0.5, 1.62), (-1.7, 3.6, 0.65)), lens=20)


def S05():
    ST.vault_complex("wreck", seed=7)
    return dict(a=((-0.6, 1.0, 0.22), (-1.9, 2.6, 0.02)), b=((-0.35, 1.25, 0.2), (-1.7, 2.9, 0.02)), lens=28,
                fstop=4.0, focus=(-1.5, 2.3, 0.02))


# ============================================================================ L3  the alarm says secure
def S06():
    A = ST.vault_complex("wreck")
    m = MD.Investigator(); st = AC.Stand(m, (-0.25, -1.2), -95)
    st.phone_dial("R", prop=PR.mobile("mobile")); st.arm_down("L")
    st.finish(look=(-0.3, -4, 1.5), density=HAIR)
    return dict(a=((0.4, 0.95, 1.52), (-0.25, -1.4, 1.45)), b=((0.3, 0.65, 1.52), (-0.25, -1.4, 1.45)), lens=32,
                hand_ok=("mobile",))


def S07():
    A = S2.security_room("alarm")
    m = MD.Operator(); se = AC.Seated(m, (0.2, 0.15, 0.47), 90)
    for sd, x in (("L", -0.05), ("R", 0.45)):
        se.hand(sd, (x + 0.0, 0.88, 0.835), elbow=(0.7, 0.3, -0.7), curl=20)
    se.head_to((0.0, 2.0, 1.5), share=0.7)
    se.finish(look=(0, 2.0, 1.4), density=HAIR)
    return dict(a=((-1.0, -1.5, 1.6), (0.15, 2.0, 1.45)), b=((-0.75, -1.15, 1.55), (0.15, 2.0, 1.45)), lens=28,
                hand_ok=("console", "chair", "Chair"))


# ============================================================================ L4  gone
def S08():
    ST.vault_complex("wreck")
    return dict(a=((-0.25, 2.5, 0.6), (0.1, -1.8, 1.05)), b=((-0.3, 3.3, 0.55), (0.1, -1.8, 1.05)), lens=24)


# ============================================================================ L5  two years earlier
def S09():
    S2.exterior("day")
    m = MD.Leonardo(); st = AC.Stand(m, (-1.1, -2.4), 88); st.walk(0.6)
    st.finish(look=(0, 3, 1.6), density=HAIR)
    return dict(a=((-6.5, -14.5, 1.5), (0.5, 0.0, 6.5)), b=((-5.8, -13.4, 1.5), (0.4, 0.0, 6.2)), lens=22)


def S10():
    A = S2.office("leasing")
    mg = MD.Manager(); se = AC.Seated(mg, A["seat_behind"], -90)
    se.hand("L", (0.14, A["desk_y"] + 0.02, 0.815), elbow=(0.9, 0.2, -0.5), curl=22)      # forearms on the desk, hands on the form
    se.hand("R", (-0.14, A["desk_y"] + 0.05, 0.815), elbow=(0.9, 0.2, -0.5), curl=26)
    se.head_to((0.0, A["desk_y"] + 0.3, 0.75), share=1.0)                                 # head bowed over the tenant form as they talk
    se.finish(density=HAIR)
    le = MD.Leonardo(); sv = AC.Seated(le, A["seat_visitor"], 90, lean=4)
    sv.head_to((0, 1.55, 1.25), share=0.6)
    sv.finish(look=(0, 1.55, 1.25), density=HAIR)
    return dict(a=((-0.5, -1.3, 2.15), (0.05, 1.3, 0.85)), b=((-0.42, -1.12, 2.1), (0.05, 1.3, 0.85)), lens=30,
                fstop=3.5, focus=(0, 1.5, 1.1), hand_ok=("chair", "Chair", "desk", "Desk"))


# ============================================================================ L6  who he is
def S11():
    A = S2.office("leonardo")
    m = MD.Leonardo(); st = AC.Stand(m, (1.2, 1.7), 92); st.head_to((1.0, 6.0, 1.2), share=0.5)
    st.finish(look=(1.0, 8, 1.0), density=HAIR)
    return dict(a=((-0.55, 1.15, 1.65), (1.25, 1.75, 1.58)), b=((-0.3, 1.3, 1.64), (1.25, 1.75, 1.58)), lens=40,
                fstop=2.8, focus=(1.2, 1.7, 1.6))


def S12():
    A = S2.turin_flat("day")
    b = A["bench"]; seat = A["bench_seat"]
    stool((seat.x, seat.y, 0), h=0.6)
    m = MD.Leonardo(); se = AC.Seated(m, (seat.x, seat.y, 0.6), 90, lean=18)
    se.hand("L", (b.x - 0.16, b.y - 0.26, 0.99), elbow=(0.8, 0.1, -0.6), curl=26)
    se.hand("R", (b.x + 0.02, b.y - 0.3, 1.02), elbow=(0.8, 0.1, -0.8), grip=0.6)
    se.head_to((b.x + 0.05, b.y - 0.05, 1.0), share=0.8)
    se.finish(look=(b.x + 0.05, b.y - 0.05, 0.95), density=HAIR)
    return dict(a=((2.45, 0.45, 1.5), (1.5, 2.15, 1.0)), b=((2.3, 0.7, 1.45), (1.5, 2.15, 1.0)), lens=35,
                fstop=2.8, focus=(1.6, 1.9, 1.0), hand_ok=("bench", "stool", "chain", "torus", "Torus"))


def S13():
    A = S2.office("leasing")
    dy = A["desk_y"]; k = A["keys"]
    mg = MD.Manager(); se = AC.Seated(mg, A["seat_behind"], -90, lean=14)
    se.hand("L", (k.x + 0.03, k.y + 0.06, 0.86), elbow=(0.7, 0.3, -0.7), curl=16)      # his left slides the keys across
    se.hand("R", (-0.3, dy + 0.0, 0.86), elbow=(0.7, 0.3, -0.7), curl=24)
    se.head_to(k, share=0.8)
    se.finish(look=k, density=HAIR)
    le = MD.Leonardo(); sv = AC.Seated(le, A["seat_visitor"], 90, lean=12)
    sv.hand("R", (0.25, dy - 0.42, 0.835), elbow=(0.7, 0.3, -0.7), curl=24)
    sv.head_to(k, share=0.8)
    sv.finish(look=k, density=HAIR)
    return dict(a=((-1.75, 0.35, 2.35), (0.0, 0.55, 0.85)), b=((-1.6, 0.4, 2.25), (0.0, 0.5, 0.85)), lens=24,
                hand_ok=("chair", "Chair", "desk", "Desk", "key", "torus", "Torus", "card"))


# ============================================================================ L7  tenant, access, a box
def S14():
    A = S2.office("leonardo")
    RY = A["RY"]
    # beyond the glass: the low roofline of the district far off (no near facade), so a low sun rakes into the room
    for o in list(bpy.data.objects):
        if o.name.startswith("far_"):
            bpy.data.objects.remove(o)
    import city                                       # the district's roofs below and beyond (14 m down, across the street)
    city.district("day", R=3, skip=[(-25, 25, -60, 20)])
    for o in list(bpy.data.objects):
        if o.name in ("district", "city_ground"):
            o.location.y += RY + 120; o.location.z -= 26.0
    sun = A["sun"]; sun.data.energy = 4.5; sun.data.angle = math.radians(0.6)
    sun.rotation_euler = V((0.4, -1.0, -0.3)).normalized().to_track_quat('-Z', 'Y').to_euler()   # low afternoon sun in through the blinds
    ST.haze_box("office_haze", (0, 0, 1.4), (5.0, 4.2, 2.75), density=0.03, aniso=0.6, color=(1.0, 0.9, 0.78))
    m = MD.Leonardo(); st = AC.Stand(m, (-1.05, 1.7), 90); st.head_to((-1.6, 8.0, 1.2), share=0.6)
    st.finish(density=HAIR)
    # slow push in from behind as the sun cuts through the slats
    return dict(a=((0.25, -1.1, 1.5), (-1.05, 2.4, 1.45)), b=((-0.35, 0.15, 1.55), (-1.1, 2.4, 1.5)), lens=30, fstop=4.0, focus=(-1.05, 1.7, 1.5))


def S15():
    A = S2.security_room("building")
    r = A["badge_reader"]
    m = MD.Leonardo(); st = AC.Stand(m, (r.x - 0.6, r.y - 0.05), 2)
    st.hand("R", (r.x - 0.1, r.y, r.z - 0.02), elbow=(0.7, 0.3, -0.8), grip=0.55)
    st.head_to(r, share=0.6)
    st.finish(look=r, density=HAIR)
    bd = PR.badge(); bpy.context.view_layer.update()
    bd.location = r + V((-0.04, 0, 0)); bd.rotation_euler = (0, 0, math.radians(90))
    return dict(a=((r.x - 0.95, r.y - 1.35, 1.35), (r.x - 0.2, r.y, 1.2)), b=((r.x - 0.85, r.y - 1.1, 1.33), (r.x - 0.2, r.y, 1.2)),
                lens=35, fstop=3.2, focus=r, hand_ok=("badge",))


def S16():
    A = ST.vault_complex("day", extra_open=[(-1, 6, 2)])
    tf = A["tray_front"]
    m = MD.Leonardo(); st = AC.Stand(m, (-2.38, tf.y - 0.05), 180)
    st.hand("R", tf + V((0.03, 0.06, 0.03)), elbow=(0.7, 0.3, -0.8), grip=0.7)
    st.hand("L", tf + V((0.03, -0.14, 0.03)), elbow=(0.7, 0.3, -0.8), grip=0.7)
    st.head_to(tf, share=0.7)
    st.finish(look=tf, density=HAIR)
    # light: the fluorescent over his row as a hard top-key on the brushed doors, a little dust in the air
    ST.light_area("tray_key", (-2.2, tf.y - 0.1, 2.35), (-2.7, tf.y, 1.0), 0.5, 120, (1.0, 0.88, 0.7))
    ST.haze_box("vault_haze", (0, 2.3, 1.25), (6.0, 4.6, 2.45), density=0.004, aniso=0.6, color=(1.0, 0.94, 0.86))
    # low along the wall of boxes, sliding past: the steel doors recede, Leonardo draws his tray out (back three-quarter)
    return dict(a=((-0.55, tf.y + 1.75, 0.95), (-2.75, tf.y - 0.35, 1.3)), b=((-0.8, tf.y + 1.25, 1.0), (-2.75, tf.y - 0.2, 1.28)), lens=28,
                fstop=3.2, focus=tf, hand_ok=("tray", "cavity", "boxdoor"))


def S17():
    A = ST.vault_complex("day")
    m = MD.Leonardo(); st = AC.Stand(m, (0.05, 1.1), 90); st.head_to((-1.5, 4.0, 1.4), share=0.5)
    st.finish(look=(-1.5, 4, 1.4), density=HAIR)
    return dict(a=((0.35, -1.1, 1.25), (0.0, 4.4, 1.3)), b=((0.3, -0.45, 1.3), (0.0, 4.4, 1.32)), lens=28)


# ============================================================================ L9  how the vault works
def S18():
    A = S2.maquette()
    S2.ripple_bands(A["vault"] + V((0, -0.035, 0)), (0, -1, 0), (0.075,), width=0.07, strength=3.5, alpha=0.5)
    # a slow descent: from above the roofline down the cut face to the warm vault two floors under the street
    return dict(a=((-0.36, -0.62, 0.14), (0.03, 0.0, 0.05)), b=((-0.16, -0.44, 0.035), (0.035, 0.0, 0.02)), lens=40,
                fstop=6.3, focus=A["vault"])


def S19():
    ST.vault_complex("day")
    return dict(a=((-0.5, -6.1, 1.55), (0.1, 0.0, 1.1)), b=((-0.45, -5.2, 1.5), (0.1, 0.0, 1.1)), lens=30)


def S20():
    A = ST.vault_complex("day")
    cc = A["cctv"]
    m = MD.Leonardo(); st = AC.Stand(m, (0.1, -2.6), 95); st.head_to(cc, share=0.75)
    st.finish(look=cc, density=HAIR)
    return dict(a=((0.62, -4.05, 1.62), (-0.35, -2.2, 1.95)), b=((0.56, -3.75, 1.62), (-0.35, -2.2, 1.95)), lens=30,
                extra=[dict(name="cctv_S20", loc=tuple(cc + V((0.05, -0.12, -0.08))), tgt=(0.1, -3.2, 1.0), lens=18)])


def S21():
    img = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "p1", "extra", "cctv_S20.png")
    A = S2.security_room("building")
    if os.path.exists(img):                      # the grille camera's picture, grey and grainy, on the middle monitor
        scr = A["screens"][1]; scr.data.materials.clear(); scr.data.materials.append(S2.cctv_mat("cctv_grille", img, 1.3))
    m = MD.Guard(); se = AC.Seated(m, (0.2, 0.15, 0.47), 90)
    b = A["gate_button"]
    se.hand("L", (b.x + 0.02, b.y - 0.03, b.z + 0.025), elbow=(0.7, 0.3, -0.7), curl=30)     # the release button is on his left
    se.hand("R", (0.45, 0.88, 0.835), elbow=(0.7, 0.3, -0.7), curl=20)
    se.head_to((0.0, 1.9, 1.62), share=0.7)
    se.finish(look=(0.0, 1.9, 1.62), density=HAIR)
    return dict(a=((-0.65, -1.2, 1.62), (0.0, 1.95, 1.45)), b=((-0.45, -0.9, 1.58), (0.0, 1.95, 1.5)), lens=32,
                hand_ok=("console", "chair", "Chair"))


def S22():
    A = ST.vault_complex("day", gate_angle=38)
    g = A["gate_handle"]
    gb0 = A["gate_bar"]
    m = MD.Leonardo(); st = AC.Stand(m, (gb0.x - 0.12, gb0.y - 0.36), 75)
    gb = A["gate_bar"]
    gap = st.grip("R", gb, (0, 0, 1), radius=0.011)
    st.head_to((0, 0, 1.2), share=0.5)
    st.finish(look=(0, 0, 1.2), density=HAIR)
    return dict(a=((1.0, -3.3, 1.4), (-0.1, -2.2, 1.1)), b=((0.92, -3.05, 1.4), (-0.1, -2.2, 1.1)), lens=30,
                hand_ok=("grille",))


# ============================================================================ L10 each visit, another look
def S23():
    A = ST.vault_complex("day", extra_open=[(-1, 6, 2)])
    tf = A["tray_front"]; pir = A["pirs"][0]
    m = MD.Leonardo(); st = AC.Stand(m, (-2.38, tf.y - 0.05), 180)
    st.hand("R", tf + V((0.03, 0.06, 0.03)), elbow=(0.7, 0.3, -0.8), grip=0.7)
    st.head_to(pir, share=0.85)
    st.finish(look=pir, density=HAIR)
    return dict(a=((-1.35, 0.95, 1.3), (-2.45, 3.3, 1.95)), b=((-1.5, 1.2, 1.3), (-2.45, 3.3, 1.95)), lens=30,
                hand_ok=("tray", "cavity", "boxdoor"))


def S24():
    A = ST.vault_complex("day", extra_open=[(-1, 6, 2)])
    pir = A["pirs"][0]; ld = A["light_detector"]
    return dict(a=((-2.3, 2.1, 1.64), tuple(pir)), b=((-2.25, 2.05, 1.64), tuple(ld)), lens=28)


# ============================================================================ L11 at night
def S25():
    ST.vault_complex("night")
    return dict(a=((0.0, -5.6, 1.5), (0.0, -0.6, 1.0)), b=((0.0, -4.7, 1.45), (0.0, -0.6, 1.0)), lens=28,
                cine=dict(exposure=1.3))


def S26():
    A = ST.vault_complex("night")
    d = A["dial"]; k = A["keylock"]
    ST.light_spot("dial_spot", (d.x + 0.7, d.y - 1.0, d.z + 0.6), d, 260, angle=28, color=(1.0, 0.74, 0.5))
    ST.light_point("dial_rim", (d.x - 0.5, d.y - 0.6, d.z + 0.4), 15, (0.6, 0.7, 1.0), radius=0.1)
    return dict(a=(tuple(d + V((0.24, -0.34, 0.08))), tuple(d)), b=(tuple(d + V((0.16, -0.26, 0.02))), tuple(d)), lens=50,
                fstop=2.8, focus=d, cine=dict(exposure=1.0))


def S27():
    A = ST.vault_complex("night")
    for p in A["pirs"]:
        S2.ripple_bands(p + V((0, -0.06, -0.06)), (0, -1, -0.6), (0.42,), width=0.55, strength=2.2, alpha=0.42)
    S2.ripple_bands(A["light_detector"] + V((0, 0, -0.01)), (0, 0, -1), (0.32,), width=0.42, strength=2.2, alpha=0.45)
    ST.light_point("vault_dim", (0, 2.0, 2.2), 18, (1.0, 0.6, 0.35), radius=0.3)
    return dict(a=((1.9, 0.55, 1.3), (-0.7, 3.8, 1.55)), b=((1.55, 0.8, 1.25), (-0.7, 3.8, 1.6)), lens=24, cine=dict(exposure=0.4))


def S28():
    A = ST.vault_complex("night")
    sp = A["seismic"][0]
    S2.ripple_bands(sp + V((0.01, 0, 0)), (1, 0, 0), (0.24,), width=0.3, strength=2.2, alpha=0.45)
    ST.light_point("wall_dim", (-2.2, 1.0, 2.2), 6, (1.0, 0.6, 0.35), radius=0.2)
    return dict(a=((-2.15, 1.05, 2.0), (-3.0, 0.25, 2.25)), b=((-2.3, 0.85, 2.05), (-3.0, 0.25, 2.28)), lens=35,
                cine=dict(exposure=0.4))


# ============================================================================ L12 police behind you
def S29():
    A = ST.vault_complex("night")
    cops = []
    for i, (x, y, hd) in enumerate(((0.35, -6.75, 92), (-0.45, -7.25, 86))):
        m = MD.Police(name=f"Police{i}"); st = AC.Stand(m, (x, y), hd)
        st.hand("R", (x - 0.05 * (1 if i else -1), y + 0.42, 1.25), elbow=(0.6, 0.3, -0.8), grip=1.0)
        st.head_to((0, -2.2, 1.3), share=0.6)
        st.finish(look=(0, -2, 1.3), density=HAIR)
        t = PR.torch(f"torch{i}", energy=60); bpy.context.view_layer.update()
        t.location = st.palm("R"); t.rotation_euler = (0, 0, math.radians(hd - 90 + 180))
        cops.append(m)
    ST.light_area("stair_back", (0, -9.2, 2.6), (0, -6.0, 1.2), 1.5, 120, (1.0, 0.7, 0.45))
    return dict(a=((0.3, -2.55, 1.5), (0.0, -7.3, 1.3)), b=((0.3, -2.95, 1.5), (0.0, -7.3, 1.3)), lens=35,
                cine=dict(exposure=0.3), hand_ok=("torch",))


# ============================================================================ L13 he studies the people
def S30():
    A = S2.security_room("building")
    g = MD.Guard(); se = AC.Seated(g, (0.2, 0.15, 0.47), 90)
    se.hand("L", (-0.05, 0.88, 0.835), elbow=(0.7, 0.3, -0.7), curl=20); se.hand("R", (0.45, 0.88, 0.835), elbow=(0.7, 0.3, -0.7), curl=20)
    se.head_to((0.0, 1.9, 1.5), share=0.6); se.finish(look=(0, 1.9, 1.5), density=HAIR)
    m = MD.Leonardo(); st = AC.Stand(m, (-2.95, -0.85), 15); st.head_to((0.2, 0.4, 1.3), share=0.6)
    st.finish(look=(0.2, 0.4, 1.3), density=HAIR)
    return dict(a=((-4.0, -1.35, 1.66), (0.0, 0.9, 1.2)), b=((-3.75, -1.2, 1.64), (0.0, 0.9, 1.2)), lens=30,
                hand_ok=("console", "chair", "Chair"))


# ============================================================================ L14 key, recordings, blueprints
def S31():
    A = ST.vault_complex("day")
    kc = A["key_cabinet"]
    for o in list(bpy.data.objects):
        if o.name.startswith("key_cabinet"):
            bpy.data.objects.remove(o)
    cab = ST.steel_paint("cab_open", (0.25, 0.3, 0.26))
    x0 = kc.x - 0.08
    ST.box("cab_back", (x0 - 0.06, kc.y, kc.z), (0.02, 0.5, 0.6), cab)
    for sg in (1, -1):
        ST.box("cab_side", (x0, kc.y + sg * 0.25, kc.z), (0.14, 0.02, 0.6), cab)
    for sz in (1, -1):
        ST.box("cab_tb", (x0, kc.y, kc.z + sz * 0.3), (0.14, 0.5, 0.02), cab)
    ST.box("cab_door", (x0 + 0.17, kc.y - 0.25 - 0.0, kc.z), (0.02, 0.5, 0.6), cab, rot=(0, 0, math.radians(70)))
    hook = (x0 - 0.03, kc.y - 0.05, kc.z + 0.18)
    ST.box("cab_hook", hook, (0.04, 0.008, 0.008), ST.brushed())
    k1 = PR.vault_key_part("keyA", 0.24, bit=True); k1.location = (hook[0] + 0.01, hook[1] - 0.01, hook[2] - 0.02)
    k2 = PR.vault_key_part("keyB", 0.16, bit=False); k2.location = (hook[0] + 0.012, hook[1] + 0.012, hook[2] - 0.02)
    k2.rotation_euler = (0, 0, 0.5)
    ST.light_spot("cup_bulb", (kc.x + 1.2, kc.y - 0.3, 2.3), kc, 30, angle=60, color=(1.0, 0.75, 0.45))
    return dict(a=((kc.x + 0.95, kc.y - 0.45, 1.6), tuple(V(hook) + V((0, 0, -0.12)))),
                b=((kc.x + 0.65, kc.y - 0.25, 1.55), tuple(V(hook) + V((0, 0, -0.12)))), lens=40, fstop=2.8,
                focus=V(hook) + V((0, 0, -0.12)))


def S32():
    A = S2.security_room("building")
    v = A["vcr"]
    return dict(a=((0.7, -0.15, 1.35), tuple(v + V((0, 0, 0.1)))), b=((1.25, -0.5, 1.25), tuple(v + V((0, -0.1, 0.25)))), lens=35,
                fstop=3.2, focus=v)


def S33():
    A = S2.office("leonardo", hour="night")
    for o in list(bpy.data.objects):
        if o.name.startswith("visitor_chair"):
            bpy.data.objects.remove(o)
    dy = A["desk_y"]
    m = MD.Leonardo(); ln = AC.Lean(m, (-0.2, -0.12), 90, {"L": (-0.48, dy - 0.3, 0.79), "R": (0.08, dy - 0.3, 0.79)}, lean=30)
    ln.finish(look=A["blueprint"], density=HAIR)
    return dict(a=((-1.05, -1.45, 1.8), (-0.15, 0.7, 0.9)), b=((-0.85, -1.15, 1.72), (-0.15, 0.72, 0.88)), lens=30,
                hand_ok=("desk", "Desk", "blueprint", "paper"))


# ============================================================================ L15 the crew
def S34():
    A = S2.turin_flat("evening")
    t = A["table_top"]
    pnl = PR.alarm_panel(); pnl.location = (t.x - 0.42, t.y, t.z + 0.001); pnl.rotation_euler = (0, 0, math.radians(90))
    m = MD.DOnorio(); seat, yaw = A["seats"]["W"]
    se = AC.Seated(m, seat, yaw, lean=16)
    se.hand("L", (t.x - 0.72, t.y + 0.2, t.z + 0.11), elbow=(0.9, 0.1, -0.5), curl=26)
    se.hand("R", (t.x - 0.72, t.y - 0.2, t.z + 0.11), elbow=(0.9, 0.1, -0.5), curl=26)
    se.head_to((t.x - 0.52, t.y, t.z), share=0.8)
    se.finish(look=(t.x - 0.52, t.y, t.z), density=HAIR)
    return dict(a=((-0.75, -1.65, 1.42), (-0.85, 0.25, 1.0)), b=((-0.62, -1.42, 1.4), (-0.85, 0.25, 1.0)), lens=35,
                fstop=2.8, focus=(-1.0, 0.2, 1.1), hand_ok=("t_table", "alarm_panel", "chair"))


def S35():
    A = S2.turin_flat("evening")
    x = A["windows"][0]
    m = MD.Finotto(); st = AC.Stand(m, (x, 2.0), 90); st.head_to((x, 8, 1.0), share=0.5)
    st.finish(look=(x, 8, 1.0), density=HAIR)
    return dict(a=((x + 0.55, 0.15, 1.7), (x, 3.0, 1.55)), b=((x + 0.45, 0.45, 1.7), (x, 3.0, 1.55)), lens=30)


def S36():
    A = S2.turin_flat("evening")
    t = A["table_top"]
    ST.box("plan_on_table", (t.x, t.y, t.z + 0.001), (0.9, 0.6, 0.0012), S2.blueprint_mat("bp_turin"), rot=(0, 0, 0.05))
    who = {"W": MD.DOnorio, "E": MD.Leonardo, "S": MD.Finotto}
    for k, cls in who.items():
        seat, yaw = A["seats"][k]
        m = cls(); se = AC.Seated(m, seat, yaw, lean=14)
        f = V((math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0)); sdv = V((-f.y, f.x, 0))
        base = seat + f * 0.55
        base = seat + f * 0.52
        se.hand("L", (base + sdv * 0.16).to_tuple()[:2] + (t.z + 0.11,), elbow=(0.9, 0.1, -0.5), curl=24)
        se.hand("R", (base - sdv * 0.16).to_tuple()[:2] + (t.z + 0.11,), elbow=(0.9, 0.1, -0.5), curl=24)
        se.head_to(t, share=0.8)
        se.finish(look=t, density=HAIR)
    return dict(a=((0.95, -1.5, 2.75), (0.0, 0.2, 0.8)), b=((0.72, -1.2, 2.62), (0.0, 0.2, 0.8)), lens=26,
                hand_ok=("t_table", "plan", "chair"))


# ============================================================================ L16 two years
def S37():
    A = S2.office("leonardo")
    m = MD.Leonardo(); se = AC.Seated(m, A["seat_behind"], -90, lean=10)
    dy = A["desk_y"]
    se.hand("L", (0.2, dy + 0.2, 0.88), elbow=(0.9, 0.2, -0.5), curl=24)
    se.hand("R", (-0.2, dy + 0.2, 0.88), elbow=(0.9, 0.2, -0.5), curl=24)
    se.head_to((0, 0.6, 0.8), share=0.7)
    se.finish(look=(0, -2, 1.0), density=HAIR)
    ST.light_point("desk_glow", (-0.4, A["desk_y"] - 0.2, 1.25), 40, (1.0, 0.8, 0.55), radius=0.15)
    return dict(a=((-0.32, 2.05, 1.58), (0.1, 0.2, 0.85)), b=((-0.28, 2.02, 1.54), (0.1, 0.2, 0.85)), lens=26,
                hand_ok=("desk", "Desk", "chair", "Chair", "paper", "blueprint"))


VO = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vo", "ANTWERP_P1_VO.txt")).read().splitlines()
PLAN = [  # (shot, VO line 1-based, duration s, description)
    ("S01", 1, 5.5, "Aerial, blue hour: the drone pushes in over the diamond district to the Diamond Center"),
    ("S02", 1, 4.0, "A man walks down the corridor toward the vault (from behind, off the stairs)"),
    ("S03", 2, 4.5, "OTS: the grille and the steel door stand open, lights on"),
    ("S04", 2, 6.0, "The vault: forced boxes on every wall, slow lateral track"),
    ("S05", 2, 4.5, "Floor level: documents, jewellery boxes, trays"),
    ("S06", 3, 4.0, "The investigator on the phone outside the vault door (from behind)"),
    ("S07", 3, 4.0, "The alarm monitoring centre: every lamp green"),
    ("S08", 4, 3.0, "The empty vault, the open door: they are gone"),
    ("S09", 5, 4.0, "EXT 2000: Leonardo walks up to the Diamond Center (from behind)"),
    ("S10", 5, 4.0, "OTS Leonardo: the building manager across the desk"),
    ("S11", 6, 5.5, "Leonardo at the window, profile in half shadow (name card)"),
    ("S12", 6, 4.0, "Turin: Leonardo at his jeweller's bench (OTS)"),
    ("S13", 6, 4.0, "Top-down: keys and an access card slide across the desk; the file stays shut"),
    ("S14", 7, 3.5, "His office: Leonardo at the window, low sun through the blinds (from behind, slow push)"),
    ("S15", 7, 3.5, "The badge reader turns green"),
    ("S16", 7, 4.0, "The vault by day: Leonardo draws out his tray (low dolly along the box wall, from behind)"),
    ("S17", 8, 4.5, "Leonardo in the aisle between the boxes, slow push"),
    ("S18", 9, 6.0, "Architect's cut-away model: two floors underground, the warm vault (descending move)"),
    ("S19", 9, 3.5, "Business hours: the steel door open, the grille shut"),
    ("S20", 9, 3.0, "At the grille, Leonardo looks up into the camera (from behind)"),
    ("S21", 9, 3.5, "Upstairs a guard sees him on the monitor and releases the grille"),
    ("S22", 9, 3.0, "Leonardo pulls the grille open"),
    ("S23", 10, 4.0, "At his box, his eyes go up to the sensors"),
    ("S24", 10, 5.0, "POV: motion sensor, light detector"),
    ("S25", 11, 4.0, "Night: the steel door shut, the corridor dark"),
    ("S26", 11, 4.0, "Macro: the combination dial and the key lock"),
    ("S27", 11, 4.5, "The dark vault: sensor fields as soft orange bands"),
    ("S28", 11, 3.5, "A seismic sensor on the wall"),
    ("S29", 12, 6.0, "Torches at the foot of the stairs: police (silhouettes)"),
    ("S30", 13, 3.5, "Leonardo watches the guard at the monitors (from behind)"),
    ("S31", 14, 6.0, "The two halves of the vault key, hanging together in a cupboard"),
    ("S32", 14, 4.5, "The recorders and tapes upstairs"),
    ("S33", 14, 7.0, "Leonardo bent over the blueprints, lamp light (from behind)"),
    ("S34", 15, 5.0, "Turin: D'Onorio with an alarm panel opened up (profile, half shadow)"),
    ("S35", 15, 4.0, "Finotto at the window (from behind)"),
    ("S36", 15, 6.0, "High angle: the three around a plan"),
    ("S37", 16, 7.0, "His office, months on: Leonardo at the desk (from behind)"),
]
SHOTS = {sid: dict(fn=globals()[sid], dur=d, vo=VO[ln - 1], line=ln, desc=desc) for sid, ln, d, desc in PLAN}

# timed to the narration (tools/vo_align.py + tools/shot_timing.py): the VO decides each shot's length
_TJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "timing", "P1_shots.json")
if os.path.exists(_TJ):
    import json as _json
    for _s, _v in _json.load(open(_TJ))["shots"].items():
        if _s in SHOTS:
            SHOTS[_s]["dur"] = _v["dur"]
