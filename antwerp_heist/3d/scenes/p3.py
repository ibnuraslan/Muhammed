"""Part 3 (VO lines 35-55): "Detectives Agim De Bruycker and Patrick Peys..." -> "...left beside the road."  46 shots.
Same rules: no face close-ups (backs, OTS, profiles in half shadow, silhouettes), hands only with their person in frame,
camera carries the motion, clipcheck 0."""
import math, os
import bpy
from mathutils import Vector, Matrix
import sets as ST, sets2 as S2, sets3 as S3, modern as MD, acts as AC, props as PR

HAIR = float(os.environ.get("HAIR", "0.6"))
V = Vector
HERE = os.path.dirname(os.path.abspath(__file__))
EXTRA = os.path.join(HERE, "..", "out", "p3", "extra")


def img(rel):
    p = os.path.join(HERE, "..", "out", rel)
    return p if os.path.exists(p) else None


def desk_hands(se, dy, z=0.875, spread=0.2, fwd=0.22):
    se.hand("R", (spread, dy + fwd, z), elbow=(0.9, 0.2, -0.5), curl=24)
    se.hand("L", (-spread, dy + fwd, z), elbow=(0.9, 0.2, -0.5), curl=24)


# ============================================================================ L1 a room full of evidence
def U01():
    ST.vault_complex("wreck", contacts="bypassed", taped=True)
    ST.clear_floor([(-0.3, 1.6), (0.6, 2.2)], 0.6)
    for cls, (x, y, hd) in ((MD.DeBruycker, (-0.3, 1.5, 115)), (MD.Peys, (0.65, 2.1, 60))):
        m = cls(); st = AC.Stand(m, (x, y), hd); st.hands_front(); st.head_to((x * 3, 4.4, 1.3), share=0.5); st.finish(density=HAIR)
    return dict(a=((0.25, -1.3, 1.62), (0.0, 3.2, 1.2)), b=((0.25, -0.8, 1.6), (0.0, 3.2, 1.2)), lens=24)


def U02():
    A = S2.security_room("building")
    for o in list(bpy.data.objects):
        if o.name.startswith(("vhs",)):
            bpy.data.objects.remove(o)                 # the tapes are gone
    v = A["vcr"]
    return dict(a=((v.x - 1.3, v.y - 1.12, 1.6), (v.x, v.y, 1.2)), b=((v.x - 1.22, v.y - 1.08, 1.58), (v.x, v.y, 1.2)), lens=26)


# ============================================================================ L2 a call about rubbish
def U03():
    A = S2.office("leasing")
    m = MD.Peys(); se = AC.Seated(m, A["seat_behind"], -90, lean=10)
    se.hand("L", (-0.7, A["desk_y"] + 0.12, 0.88), elbow=(0.9, 0.2, -0.5), curl=30)     # hand on the ringing desk phone
    se.hand("R", (0.2, A["desk_y"] + 0.27, 0.87), elbow=(0.9, 0.2, -0.5), curl=24)
    se.head_to((-0.7, A["desk_y"] + 0.1, 0.8), share=0.6); se.finish(density=HAIR)
    return dict(a=((0.45, 2.0, 1.55), (-0.5, 0.6, 0.9)), b=((0.4, 1.98, 1.5), (-0.5, 0.6, 0.9)), lens=28,
                hand_ok=("desk_phone", "desk", "Desk", "chair"))


def U04():
    S3.woodland()
    return dict(a=((-9.0, -12.5, 2.6), (0.5, 3.0, 1.6)), b=((-7.5, -12.0, 2.5), (0.5, 3.0, 1.6)), lens=26)


# ============================================================================ L3 Van Camp
def U05():
    A = S3.woodland()
    m = MD.VanCamp(); st = AC.Stand(m, (-1.6, 0.6), 70); st.walk(0.3); st.finish(density=HAIR)
    return dict(a=((-2.9, -2.3, 1.5), (0.3, 3.0, 0.7)), b=((-2.6, -1.9, 1.48), (0.3, 3.0, 0.7)), lens=30)


def _vancamp_kneel(A):
    m = MD.VanCamp(); bo = A["bag_open"]
    kn = AC.Kneel(m, (bo.x - 0.05, bo.y - 0.75), 90, lean=30)
    kn.hand("L", (bo.x - 0.12, bo.y - 0.25, 0.22), elbow=(0.8, 0.2, -0.6), curl=40)
    kn.hand("R", (bo.x + 0.12, bo.y - 0.28, 0.2), elbow=(0.8, 0.2, -0.6), curl=30)
    kn.head_to(bo, share=0.8); kn.finish(density=HAIR)
    return kn


def U06():
    A = S3.woodland()
    _vancamp_kneel(A)
    return dict(a=((-0.95, 0.2, 1.45), (0.0, 2.2, 0.35)), b=((-0.85, 0.35, 1.4), (0.0, 2.2, 0.35)), lens=30,
                hand_ok=("trashbag", "w_paper"))


# ============================================================================ L4 materials of the diamond trade
def U07():
    A = S3.woodland()
    kn = _vancamp_kneel(A)
    bo = A["bag_open"]
    for i in range(5):
        d = PR.document(f"dpaper{i}", 0.1, 0.068, seed=i, kind="briefke", folds=0, color=(0.88, 0.88, 0.84))
        d.location = (bo.x - 0.1 + i * 0.05, bo.y - 0.42 + (i % 2) * 0.05, 0.012 + 0.001 * i); d.rotation_euler = (0, 0, 0.4 * i)
    env = PR.document("envelope", 0.23, 0.16, seed=7, lines=0, folds=0, color=(0.62, 0.48, 0.3)); env.location = (bo.x + 0.15, bo.y - 0.5, 0.012)
    return dict(a=((0.45, bo.y - 1.25, 1.05), (bo.x + 0.02, bo.y - 0.45, 0.05)), b=((0.38, bo.y - 1.15, 1.0), (bo.x + 0.02, bo.y - 0.45, 0.05)),
                lens=35, fstop=3.2, focus=(bo.x, bo.y - 0.45, 0.05), hand_ok=("trashbag", "w_paper", "dpaper", "envelope"))


# ============================================================================ L5 the lab: documents, receipts, gems, a sandwich
def _techs(A, n=2):
    b = A["bench"]
    for i, x in enumerate((-0.7, 0.7)[:n]):
        m = MD.LabTech(name=f"LabTech{i}"); st = AC.Stand(m, (x, b.y - 0.78), 90, lean=12)
        st.hand("L", (x - 0.15, b.y - 0.25, 0.975), elbow=(0.8, 0.2, -0.6), curl=26)
        st.hand("R", (x + 0.15, b.y - 0.2, 0.975), elbow=(0.8, 0.2, -0.6), curl=26)
        st.head_to(b + V((x, 0, 0)), share=0.8); st.finish(density=HAIR)


def _bench_items(A):
    b = A["bench"]; xs = A["markers_x"]
    PR.document("doc1", seed=1, kind="form").location = (xs[0], b.y + 0.05, b.z + 0.001)
    PR.document("doc_torn", torn=True, seed=2).location = (xs[1], b.y + 0.02, b.z + 0.001)
    PR.receipt("rcpt", seed=3).location = (xs[2], b.y + 0.05, b.z + 0.001)
    for k in range(4):
        PR.document(f"dpap{k}", 0.1, 0.068, seed=10 + k, kind="briefke", folds=0).location = (xs[3] - 0.08 + k * 0.05, b.y + 0.05 + (k % 2) * 0.06, b.z + 0.001)
    S3.sandwich("sandwich", loc=(xs[4], b.y + 0.05, b.z + 0.001), rz=0.3)
    PR.sf_put(S3.EVIDENCE_BAG, (xs[5], b.y + 0.05, b.z + 0.001), width=0.25, rz=1.57) if True else None
    PR.document("doc_torn2", torn=True, seed=5).location = (xs[6], b.y + 0.02, b.z + 0.001)


def U08():
    A = S3.lab(); _bench_items(A); _techs(A)
    return dict(a=((0.2, -2.8, 2.0), (0.0, -0.6, 0.95)), b=((0.3, -2.7, 1.95), (0.0, -0.6, 0.95)), lens=24,
                hand_ok=("bench", "evidence_paper"))


def U09():
    A = S3.lab(); _bench_items(A); b = A["bench"]; x = A["markers_x"][1]
    return dict(a=((x - 0.35, b.y - 0.45, b.z + 0.32), (x + 0.2, b.y + 0.02, b.z)), b=((x - 0.3, b.y - 0.4, b.z + 0.28), (x + 0.3, b.y + 0.02, b.z)),
                lens=40, fstop=3.2, focus=(x + 0.2, b.y, b.z), cine=dict(exposure=-0.7))


def U10():
    A = S3.lab(); b = A["bench"]
    o = V((0, b.y, b.z))
    ST.box("gem_pad", o + V((0.0, 0.0, 0.002)), (0.16, 0.12, 0.004), ST.velvet("gem_pad_velvet", (0.005, 0.006, 0.022)))   # the lab's dark gem pad
    dp = PR.document("dpaper_open", 0.15, 0.1025, seed=3, kind="briefke", folds=0); dp.location = o + V((-0.075, 0.055, 0.0045)); dp.rotation_euler = (0, 0, 0.3)
    dz = PR.brilliants("trace", n=9, spread=0.016, seed=14); dz.location = o + V((0.0, 0.0, 0.0042))     # the U31 / P2 brilliants
    lp = PR.loupe(); lp.location = o + V((0.045, -0.006, 0.0045 + 0.0145)); lp.rotation_euler = (math.radians(20), 0, math.radians(144))   # on its side, lens to camera
    ST.light_spot("dust_key", tuple(o + V((-0.4, -0.5, 0.6))), tuple(o), 25, angle=35, color=(1.0, 0.9, 0.75), radius=0.01)
    ST.light_area("dust_soft", tuple(o + V((0.1, 0.2, 0.5))), tuple(o), 0.6, 6, (1.0, 0.97, 0.92))
    for k, (x, y, z) in enumerate(((0.3, -0.3, 0.5), (-0.2, 0.35, 0.45), (0.05, -0.45, 0.35), (0.4, 0.2, 0.3))):   # P2 hero sparkle rig
        ST.light_point(f"lab_spark{k}", tuple(o + V((x, y, z))), 12, (1.0, 0.97, 0.92), radius=0.004)
    return dict(a=(tuple(o + V((-0.075, -0.15, 0.1))), tuple(o + V((0.01, 0, 0.005)))), b=(tuple(o + V((-0.06, -0.125, 0.085))), tuple(o + V((0.01, 0, 0.005)))),
                lens=55, fstop=8.0, focus=tuple(o + V((0, 0, 0.006))), cine=dict(exposure=-1.0))


def U11():
    A = S3.lab(); b = A["bench"]
    S3.sandwich("sandwich", loc=(0, b.y, b.z + 0.001), rz=0.4)
    PR.sf_put(S3.EVIDENCE_BAG, (0.22, b.y + 0.05, b.z + 0.001), width=0.25, rz=1.4)
    PR.document("label", 0.1, 0.06, seed=9, lines=5, color=(0.9, 0.9, 0.85)).location = (-0.18, b.y - 0.08, b.z + 0.001)
    return dict(a=((-0.25, b.y - 0.4, b.z + 0.3), (0.02, b.y, b.z + 0.03)), b=((-0.2, b.y - 0.34, b.z + 0.25), (0.02, b.y, b.z + 0.03)),
                lens=45, fstop=3.2, focus=(0, b.y, b.z + 0.03))


# ============================================================================ L6 robbery rubbish + ordinary lives
def U12():
    A = S3.lab(); _bench_items(A); b = A["bench"]
    return dict(a=((0.0, b.y - 0.05, 2.65), (0.0, b.y, b.z)), b=((0.25, b.y - 0.05, 2.55), (0.25, b.y, b.z)), lens=24)


# ============================================================================ L7 the torn document, the names
def _lightbox_scene(A, seed=2):
    b2 = A["bench2"]
    lb = PR.lightbox(); lb.location = (0.6, b2.y - 0.1, b2.z)
    for k in range(4):
        d = PR.document(f"scrap{k}", 0.1, 0.12, torn=True, seed=seed + k, lines=7)
        d.location = (0.45 + (k % 2) * 0.11, b2.y - 0.15 + (k // 2) * 0.09, b2.z + 0.053); d.rotation_euler = (0, 0, 0.15 * (k - 1.5))
    return V((0.6, b2.y - 0.1, b2.z + 0.06))


def U13():
    A = S3.lab(); c = _lightbox_scene(A)
    m = MD.LabTech(); st = AC.Stand(m, (c.x, c.y - 0.72), 90, lean=16)
    st.hand("L", c + V((-0.14, -0.1, 0.04)), elbow=(0.8, 0.2, -0.6), curl=20)
    st.hand("R", c + V((0.12, -0.05, 0.04)), elbow=(0.8, 0.2, -0.6), curl=30)
    st.head_to(c, share=0.8); st.finish(density=HAIR)
    return dict(a=((c.x + 0.95, c.y - 1.85, 1.8), tuple(c + V((0, -0.2, 0.2)))), b=((c.x + 0.85, c.y - 1.75, 1.78), tuple(c + V((0, -0.2, 0.2)))), lens=28, fstop=4.0, focus=c,
                hand_ok=("lightbox", "scrap"))


def U14():
    A = S3.lab(); c = _lightbox_scene(A, seed=12)
    return dict(a=((c.x - 0.25, c.y - 0.3, c.z + 0.3), tuple(c)), b=((c.x - 0.2, c.y - 0.25, c.z + 0.26), tuple(c + V((0.05, 0, 0)))), lens=45,
                fstop=4.0, focus=c, cine=dict(exposure=-0.7))


def U15():
    S2.exterior("day")
    for cls, (x, y) in ((MD.DeBruycker, (-0.7, -2.6)), (MD.Peys, (0.2, -2.9))):
        m = cls(); st = AC.Stand(m, (x, y), 90); st.walk(0.3 if x < 0 else 0.7); st.finish(density=HAIR)
    return dict(a=((-2.4, -9.5, 1.6), (0.0, 1.0, 2.4)), b=((-2.1, -8.8, 1.6), (0.0, 1.0, 2.4)), lens=30)


# ============================================================================ L8 one of its tenants
def U16():
    A = S2.office("leasing")
    for o in list(bpy.data.objects):                 # De Bruycker stands where the visitor chair was
        if o.name.startswith("visitor_chair"):
            bpy.data.objects.remove(o)
    mg = MD.Manager(); se = AC.Seated(mg, A["seat_behind"], -90, lean=12)
    se.hand("R", (0.1, A["desk_y"] - 0.2, 0.86), elbow=(0.9, 0.2, -0.5), curl=20); se.hand("L", (-0.25, A["desk_y"] + 0.22, 0.875), elbow=(0.9, 0.2, -0.5), curl=24)
    se.head_to((0.1, A["desk_y"] - 0.25, 0.79), share=1.0)        # head bowed over the file: no face to camera
    se.finish(density=HAIR)
    PR.document("lease_file", 0.21, 0.297, seed=21, kind="form").location = (0.1, A["desk_y"] - 0.25, 0.793)
    d = MD.DeBruycker(); st = AC.Stand(d, (0.15, A["desk_y"] - 1.05), 90, lean=8); st.hand("R", (0.12, A["desk_y"] - 0.38, 0.84), elbow=(0.8, 0.2, -0.6), curl=20)
    st.head_to((0.1, A["desk_y"] - 0.25, 0.8), share=0.7); st.finish(density=HAIR)
    return dict(a=((-0.6, A["desk_y"] - 2.1, 1.85), (0.1, A["desk_y"] + 0.4, 0.95)), b=((-0.5, A["desk_y"] - 1.95, 1.83), (0.1, A["desk_y"] + 0.4, 0.95)),
                lens=28, hand_ok=("desk", "Desk", "chair", "lease_file"))


# ============================================================================ L9 Turin
def U17():
    A = S2.office("leasing")
    fx = PR.fax(); fx.location = (-0.55, A["desk_y"] + 0.05, 0.79); fx.rotation_euler = (0, 0, math.radians(180))
    return dict(a=((-0.1, A["desk_y"] - 0.75, 1.15), (-0.55, A["desk_y"], 0.92)), b=((-0.15, A["desk_y"] - 0.6, 1.1), (-0.55, A["desk_y"], 0.92)), lens=40,
                fstop=3.2, focus=(-0.55, A["desk_y"], 0.92))


def U18():
    A = S2.office("leonardo", hour="day")
    for o in list(bpy.data.objects):
        if o.name.startswith(("blueprint", "visitor_chair")):
            bpy.data.objects.remove(o)
    m = MD.TurinOfficer(); se = AC.Seated(m, A["seat_behind"], -90, lean=12); desk_hands(se, A["desk_y"]); se.head_to((0, A["desk_y"], 0.8), share=0.7); se.finish(density=HAIR)
    PR.document("file_turin", 0.24, 0.32, seed=31).location = (0, A["desk_y"] + 0.05, 0.793)
    return dict(a=((-0.35, 2.02, 1.6), (0.1, 0.3, 0.85)), b=((-0.3, 2.0, 1.56), (0.1, 0.3, 0.85)), lens=26, hand_ok=("desk", "Desk", "chair", "file"))


# ============================================================================ L10 the receipt, the footage, Finotto
def U19():
    A = S3.lab(); b = A["bench"]
    r = PR.receipt("rcpt_hero", 0.22, seed=5); r.location = (0, b.y, b.z + 0.001); r.rotation_euler = (0, 0, 0.25)
    return dict(a=((-0.18, b.y - 0.3, b.z + 0.25), (0, b.y, b.z)), b=((-0.14, b.y - 0.25, b.z + 0.2), (0.02, b.y + 0.04, b.z)), lens=45,
                fstop=3.2, focus=(0, b.y, b.z), cine=dict(exposure=-0.7))


def U20():
    A = S3.supermarket(); c = A["checkout"]
    m = MD.Finotto(); st = AC.Stand(m, (c.x + 0.1, c.y + 0.62), -90); st.hand("R", c + V((0.15, 0.25, 0.04)), elbow=(0.8, 0.2, -0.6), curl=26)
    st.finish(density=HAIR)
    # 1) the shop's ceiling camera records the checkout (rendered now, shown on the monitor below and in U21)
    sc = bpy.context.scene; os.makedirs(EXTRA, exist_ok=True); path = os.path.join(EXTRA, "super_cctv.png")
    cd = bpy.data.cameras.new("cctv_cam"); cd.lens = 20; co = bpy.data.objects.new("cctv_cam", cd); sc.collection.objects.link(co)
    co.location = (c.x + 1.7, c.y - 1.35, 2.75)
    co.rotation_euler = (V((c.x, c.y + 0.45, 0.9)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    keep = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage, sc.cycles.samples, sc.render.filepath)
    sc.camera = co; sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
    sc.cycles.samples = 48; sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage, sc.cycles.samples, sc.render.filepath = keep
    bpy.data.objects.remove(co)
    for o in list(bpy.data.objects):                 # move the shop far away; the police watch the recording
        if o.parent is None:
            o.location.x += 100.0
    # 2) the recording on a CCTV monitor in the building's security room
    ST.box("view_floor", (0, 0, -0.05), (6, 6, 0.1), ST.flat("view_floor", (0.08, 0.07, 0.06), 0.8))
    ST.box("view_wall", (0, 1.2, 1.5), (6, 0.2, 3.0), ST.flat("view_wall", (0.22, 0.2, 0.18), 0.85))
    ST.box("view_desk", (0, 0.6, 0.73), (1.6, 0.8, 0.04), ST.flat("view_desk", (0.12, 0.09, 0.07), 0.5))
    plast = ST.flat("crt_plastic", (0.16, 0.155, 0.15), 0.45)
    ST.box("crt_body", (0, 0.78, 1.0), (0.44, 0.36, 0.42), plast, bevel=0.02)           # a 14-inch CCTV monitor
    ST.box("crt_back", (0, 0.98, 0.99), (0.3, 0.2, 0.3), plast, bevel=0.03)
    scr = S2.plane("crt_view", (0, 0.565, 1.02), (0.36, 0.27), S2.cctv_mat("cctv_play", path, 1.15), rot=(math.radians(90), 0, 0))
    ST.box("vcr_deck", (0, 0.72, 0.79), (0.43, 0.32, 0.08), ST.flat("vcr_deck", (0.06, 0.06, 0.065), 0.4))
    ST.box("vcr_led", (0.15, 0.555, 0.8), (0.006, 0.002, 0.004), ST.emit("vcr_led", (0.1, 1.0, 0.2), 20))
    ST.light_area("view_room", (0.6, -0.8, 2.4), (0, 0.6, 0.8), 1.2, 25, (1.0, 0.82, 0.6))
    ST.world((0.02, 0.02, 0.02), 0.2)
    p = V((0, 0.565, 1.02))
    return dict(a=((0.32, -0.38, 1.12), tuple(p)), b=((0.25, -0.3, 1.1), tuple(p)), lens=40, fstop=4.0, focus=tuple(p))


def U21():
    p = os.path.join(EXTRA, "super_cctv.png")
    A = S2.security_room("building", screen_images=[None, p if os.path.exists(p) else None])
    m = MD.Peys(); se = AC.Seated(m, (0.2, 0.15, 0.47), 90)
    for sd, x in (("L", -0.05), ("R", 0.45)):
        se.hand(sd, (x, 0.88, 0.835), elbow=(0.7, 0.3, -0.7), curl=20)
    se.head_to((0.0, 1.9, 1.62), share=0.7); se.finish(density=HAIR)
    return dict(a=((-0.55, -1.0, 1.6), (0.0, 1.95, 1.55)), b=((-0.4, -0.75, 1.58), (0.0, 1.95, 1.58)), lens=32, hand_ok=("console", "chair", "Chair"))


# ============================================================================ L11 the sandwich goes for testing
def U22():
    A = S3.lab(); b = A["bench"]
    S3.sandwich("sandwich", loc=(0.1, b.y + 0.05, b.z + 0.001), rz=0.4)
    m = MD.LabTech(); st = AC.Stand(m, (0.0, b.y - 0.78), 90, lean=16)
    sw = PR.swab()
    st.hand("R", (0.08, b.y - 0.12, b.z + 0.09), elbow=(0.8, 0.2, -0.6), grip=0.7)
    st.hand("L", (-0.18, b.y - 0.2, 0.95), elbow=(0.8, 0.2, -0.6), curl=26)
    st.head_to((0.1, b.y, b.z), share=0.8); st.finish(density=HAIR)
    bpy.context.view_layer.update(); p = st.palm("R"); sw.location = p; sw.rotation_euler = (0, math.radians(30), math.radians(70))
    return dict(a=((0.95, b.y - 1.9, 1.75), (0.05, b.y - 0.25, 1.1)), b=((0.85, b.y - 1.8, 1.72), (0.05, b.y - 0.25, 1.1)), lens=28, fstop=4.0,
                focus=(0.1, b.y, b.z), hand_ok=("swab", "bench", "evidence_paper"))


def U23():
    A = S3.lab(); t = A["tubes"]
    return dict(a=((t.x - 0.3, t.y - 0.35, t.z + 0.12), tuple(t)), b=((t.x - 0.22, t.y - 0.3, t.z + 0.09), tuple(t)), lens=55, fstop=2.8, focus=t)


# ============================================================================ L12-14 Leonardo returns
def U24():
    S2.exterior("day")
    m = MD.Leonardo(); st = AC.Stand(m, (0.6, -2.0), 92); st.walk(0.5); st.finish(density=HAIR)
    return dict(a=((2.8, -9.5, 1.5), (0.2, 2.0, 2.0)), b=((2.4, -8.8, 1.5), (0.2, 2.0, 2.0)), lens=32)


def U25():
    A = S2.security_room("building"); r = A["badge_reader"]
    m = MD.Leonardo(); st = AC.Stand(m, (r.x - 0.6, r.y - 0.05), 2)
    st.hand("R", (r.x - 0.1, r.y, r.z - 0.02), elbow=(0.7, 0.3, -0.8), grip=0.55); st.head_to(r, share=0.6); st.finish(look=r, density=HAIR)
    bd = PR.badge(); bpy.context.view_layer.update(); bd.location = r + V((-0.04, 0, 0)); bd.rotation_euler = (0, 0, math.radians(90))
    return dict(a=((r.x - 1.75, r.y + 0.75, 1.6), (r.x - 0.15, r.y, 1.25)), b=((r.x - 1.65, r.y + 0.68, 1.58), (r.x - 0.15, r.y, 1.25)), lens=30,
                hand_ok=("badge",))


def U26():
    A = S2.security_room("building")
    g = MD.Guard(); st = AC.Stand(g, (-0.8, 0.42), 200); st.hands_front(); st.head_to((-3.4, -0.9, 1.6), share=0.6); st.finish(density=HAIR)
    le = MD.Leonardo(); s2 = AC.Stand(le, (-3.6, -1.0), 0); s2.finish(density=HAIR)
    return dict(a=((0.1, 1.45, 1.75), (-3.0, -0.8, 1.2)), b=((0.05, 1.38, 1.74), (-3.0, -0.8, 1.2)), lens=26)


def U27():
    A = S2.office("leasing")
    mg = MD.Manager(); se = AC.Seated(mg, A["seat_behind"], -90, lean=10)
    se.hand("L", (-0.66, A["desk_y"] + 0.07, 0.88), elbow=(0.9, 0.2, -0.5), curl=30)   # dialling the desk phone
    se.hand("R", (0.2, A["desk_y"] + 0.27, 0.87), elbow=(0.9, 0.2, -0.5), curl=24)
    se.head_to((-0.7, A["desk_y"] + 0.1, 0.8), share=0.6); se.finish(density=HAIR)
    return dict(a=((0.5, 2.0, 1.5), (-0.55, 0.6, 0.9)), b=((0.45, 1.98, 1.47), (-0.55, 0.6, 0.9)), lens=30, hand_ok=("desk_phone", "desk", "Desk", "chair"))


def U28():
    A = S2.office("leasing")
    mg = MD.Manager(); se = AC.Seated(mg, A["seat_behind"], -90); desk_hands(se, A["desk_y"], fwd=-0.25); se.head_to((0.0, A["desk_y"] + 0.15, 0.79), share=1.0); se.finish(density=HAIR)   # eyes on the file while he talks
    le = MD.Leonardo(); sv = AC.Seated(le, A["seat_visitor"], 90, lean=4); sv.head_to((0, 1.55, 1.25), share=0.6); sv.finish(density=HAIR)
    dy = A["desk_y"]
    return dict(a=((0.55, dy - 2.0, 1.45), (-0.05, dy + 0.9, 1.15)), b=((0.48, dy - 1.9, 1.45), (-0.05, dy + 0.9, 1.15)), lens=30,
                fstop=4.0, focus=(0, dy + 0.6, 1.1), hand_ok=("chair", "Chair", "desk", "Desk"))


def U29():
    A = S2.security_room("building")
    for i, (x, y) in enumerate(((-4.1, -0.6), (-4.6, -1.3))):
        m = MD.Police(name=f"Police{i}"); st = AC.Stand(m, (x, y), 0); st.walk(0.3 + 0.4 * i); st.finish(density=HAIR)
    # from behind and to the side as they come in: backs and shoulders, faces turned away into the lobby
    return dict(a=((-5.9, -2.3, 1.65), (-2.8, -0.4, 1.25)), b=((-5.75, -2.2, 1.64), (-2.6, -0.35, 1.25)), lens=28)


# ============================================================================ L15 the apartment, the links
def U30():
    A = S2.turin_flat("day")
    rg = PR.rug(color=(0.2, 0.075, 0.055)); rg.location = (0.0, -1.2, 0.0)
    for o in list(bpy.data.objects):
        if o.name.startswith("t_chair_S"):
            bpy.data.objects.remove(o)
    for cls, (x, y, hd) in ((MD.DeBruycker, (-0.5, -1.3, 20)), (MD.TurinOfficer, (0.6, -1.0, 200))):
        m = cls(); kn = AC.Kneel(m, (x, y), hd, lean=40)
        kn.hand("L", (x + 0.35 * math.cos(math.radians(hd)) - 0.1, y + 0.35 * math.sin(math.radians(hd)), 0.06), elbow=(0.8, 0.2, -0.6), curl=30)
        kn.hand("R", (x + 0.35 * math.cos(math.radians(hd)) + 0.1, y + 0.35 * math.sin(math.radians(hd)), 0.06), elbow=(0.8, 0.2, -0.6), curl=30)
        kn.finish(density=HAIR, floor_z=0.01)
    t = PR.torch("t_torch", energy=120); t.location = (0.0, -1.6, 0.03); t.rotation_euler = (0, 0, math.radians(-90))
    return dict(a=((-1.85, -2.2, 2.2), (0.1, -1.05, 0.45)), b=((-1.75, -2.1, 2.15), (0.1, -1.05, 0.45)), lens=20, hand_ok=("rug",))


def U31():
    ST.world((0.5, 0.5, 0.5), 0.12)
    rg = PR.rug("rug_close", 1.0, 1.0, color=(0.2, 0.075, 0.055))
    dz = PR.brilliants("carpet_gems", n=9, spread=0.018, seed=14); dz.location = (0, 0, 0.0125)     # resting on the pile
    ST.light_spot("rug_key", (-0.4, -0.5, 0.6), (0, 0, 0), 25, angle=35, color=(1.0, 0.9, 0.75), radius=0.01)
    ST.light_area("rug_soft", (0.1, 0.2, 0.5), (0, 0, 0), 0.6, 6, (1.0, 0.97, 0.92))           # a broad source for the facets to mirror
    for k, (x, y, z) in enumerate(((0.3, -0.3, 0.5), (-0.2, 0.35, 0.45), (0.05, -0.45, 0.35), (0.4, 0.2, 0.3))):   # P2 hero sparkle rig
        ST.light_point(f"rug_spark{k}", (x, y, z), 12, (1.0, 0.97, 0.92), radius=0.004)
    return dict(a=((-0.07, -0.12, 0.085), (0, 0, 0.012)), b=((-0.055, -0.1, 0.07), (0, 0, 0.012)), lens=60, fstop=9.0, focus=(0, 0, 0.013),
                cine=dict(exposure=-1.0))


def U32():
    prints = [img("p2/board/T31.png"), img("p3/board/U12.png"), img("p3/board/U31.png"), img("p1/board/S33.png"), img("p3/board/U07.png")]
    prints = [p for p in prints if p] or [img("p1/board/S04.png")]
    A = S3.evidence_wall(prints)
    pins = A["pins"]
    for a_, b_ in zip(pins, pins[1:]):
        o = S2.soft_strip((a_.x, a_.z), (b_.x, b_.z), 0, 0.03, alpha=0.6)
        o.rotation_euler = (math.radians(90), 0, o.rotation_euler.z); o.location = ((a_.x + b_.x) / 2, 1.448, (a_.z + b_.z) / 2)
    return dict(a=((-0.6, -0.9, 1.65), tuple(A["board"])), b=((-0.4, -0.7, 1.62), tuple(A["board"])), lens=32)


# ============================================================================ L16 2005: the sentences
def U33():
    A = S3.courtroom()
    for i, p in enumerate(A["judges"]):
        m = MD.Judge(name=f"Judge{i}"); se = AC.Seated(m, V((p.x, p.y + 0.25, 0.97)), -90, lean=6, floor=0.5); se.finish(density=HAIR, floor_z=0.5)
        se._rest_on_seat(margin=0.016, r=0.55, depth=0.35)          # robe over the chair seat
    le = MD.Leonardo(); st = AC.Stand(le, (A["dock"].x, A["dock"].y), 90); st.hands_front(); st.finish(density=HAIR)
    return dict(a=((0.5, -1.6, 1.75), (0.0, 5.0, 1.6)), b=((0.45, -1.2, 1.72), (0.0, 5.0, 1.6)), lens=28, hand_ok=("chair",))


def U34():
    A = S3.courtroom()
    who = (MD.DOnorio, MD.Finotto, MD.Speedy)
    for i, cls in enumerate(who):
        p = V((-4.4 + i * 0.85, -1.5, 0.47)); m = cls(); se = AC.Seated(m, p, 90, lean=6); se.finish(density=HAIR)
    return dict(a=((-2.4, -3.6, 1.55), (-3.6, 0.0, 1.0)), b=((-2.5, -3.35, 1.52), (-3.6, 0.0, 1.0)), lens=32, hand_ok=("c_pew",))


# ============================================================================ L17 his other story
def U35():
    A = S3.interview()
    seat, yaw = A["seats"]["L"]
    m = MD.Leonardo(); se = AC.Seated(m, seat, yaw, lean=10)
    se.hand("L", (-0.42, 0.12, 0.835), elbow=(0.9, 0.2, -0.5), curl=24); se.hand("R", (-0.38, -0.12, 0.835), elbow=(0.9, 0.2, -0.5), curl=24)
    se.head_to((0.8, 0.0, 1.2), share=0.5); se.finish(density=HAIR)
    # from behind his shoulder, toward the interviewer's empty side of the table: the back of his head against the lamp
    return dict(a=((-1.75, -0.75, 1.45), (0.5, 0.15, 1.05)), b=((-1.7, -0.65, 1.44), (0.5, 0.15, 1.05)), lens=32,
                hand_ok=("iv_table", "iv_chair"), cine=dict(exposure=0.0))


def U36():
    A = S2.office("leonardo", hour="day")
    for o in list(bpy.data.objects):
        if o.name.startswith(("blueprint",)):
            bpy.data.objects.remove(o)
    m = MD.Trader(2); st = AC.Stand(m, (0.9, 1.55), 90); st.hands_front(); st.finish(density=HAIR)
    return dict(a=((-0.6, -1.2, 1.55), (0.9, 2.0, 1.4)), b=((-0.45, -1.0, 1.55), (0.9, 2.0, 1.4)), lens=30)


def U37():
    A = S3.replica()
    for i, (cls, x, y, hd) in enumerate(((MD.Leonardo, -0.6, 0.8, 80), (MD.DOnorio, 0.4, 1.2, 95), (MD.Finotto, -0.1, 0.1, 90))):
        m = cls(night=True); st = AC.Stand(m, (x, y), hd); st.head_to(A["door"], share=0.5); st.finish(density=HAIR)
    return dict(a=((1.8, -3.0, 1.9), (0.0, 2.0, 1.1)), b=((1.6, -2.6, 1.85), (0.0, 2.0, 1.1)), lens=26)


def U38():
    ST.world((0.01, 0.01, 0.01), 0.15)
    ST.box("small_table", (0, 0, -0.01), (0.6, 0.4, 0.02), ST.velvet("small_velvet", (0.06, 0.03, 0.02)))
    PR.sf_put(PR.GOLD_BAR, (-0.06, 0.02, 0.0), width=0.116, rz=0.3)
    PR.sf_put(PR.USD_LOOSE, (0.1, -0.02, 0.0), width=0.15, rz=-0.4)
    dz = PR.brilliants("few", n=6, spread=0.02, seed=3); dz.location = (0.0, -0.08, 0.0)
    ST.light_spot("small_key", (-0.4, -0.5, 0.7), (0, 0, 0), 60, angle=30, color=(1.0, 0.88, 0.7), radius=0.03)
    ST.light_area("small_soft", (0.15, 0.25, 0.5), (0, 0, 0), 0.6, 8, (1.0, 0.95, 0.88))       # a broad source for the facets to mirror
    dz.location.z = 0.001
    return dict(a=((-0.2, -0.32, 0.22), (0.02, 0, 0.0)), b=((-0.15, -0.27, 0.18), (0.02, 0, 0.0)), lens=50, fstop=5.6, focus=(0.02, 0, 0))


# ============================================================================ L18 the scene contradicts him
def U39():
    A = S2.office("leasing", hour="night")
    for cls, (x, hd) in ((MD.DeBruycker, (-0.25, -90)),):
        m = cls(); se = AC.Seated(m, A["seat_behind"], hd, lean=12); desk_hands(se, A["desk_y"]); se.head_to((0, A["desk_y"], 0.8), share=0.7); se.finish(density=HAIR)
        se._rest_on_seat(margin=0.016, r=0.55, depth=0.35)          # coat skirt over the chair seat, not through it
    PR.document("report", 0.21, 0.3, seed=41).location = (0.0, A["desk_y"] + 0.05, 0.793)
    return dict(a=((-0.5, 2.0, 1.55), (0.1, 0.5, 0.85)), b=((-0.45, 1.98, 1.52), (0.1, 0.5, 0.85)), lens=26, hand_ok=("desk", "Desk", "chair", "report"))


def U40():
    ST.vault_complex("wreck", contacts="bypassed", taped=True)
    # inside the vault looking back at the open door: the ceiling lights burning over the forced boxes
    return dict(a=((0.9, 4.0, 1.05), (-0.05, 0.2, 1.75)), b=((0.8, 3.85, 1.0), (-0.05, 0.2, 1.8)), lens=20)


def U41():
    A = ST.vault_complex("heist", forced=80, debris=0.8, contacts="bypassed", taped=True)
    for i in range(5):
        cb = PR.sf_put(PR.USD_STACKS, (0.0 + 0.2 * i, 1.4 - 0.05 * i, 0.0), width=0.16, rz=0.3 * i)
    return dict(a=((-0.4, 0.6, 0.45), (0.4, 1.4, 0.05)), b=((-0.3, 0.75, 0.4), (0.45, 1.4, 0.05)), lens=32, fstop=3.2, focus=(0.4, 1.4, 0.05))


# ============================================================================ L19 convicted; the loot missing
def U42():
    ST.vault_complex("wreck", contacts="bypassed", taped=True)
    return dict(a=((0.0, 0.6, 1.3), (0.0, 4.4, 1.2)), b=((0.0, 2.2, 1.25), (0.0, 4.4, 1.2)), lens=28)


# ============================================================================ L20 what explains it all
def U43():
    A = ST.vault_complex("wreck", contacts="bypassed", taped=True); ld = A["light_detector"]
    # a raking light skimming the ceiling picks out the tape's matte silver and its edges
    ST.light_area("tape_rake", (ld.x + 0.45, ld.y + 0.05, ld.z + 0.01), tuple(ld), 0.08, 6, (1.0, 0.94, 0.85))
    # really close under the detector: it fills ~40% of the frame, the tape strip across its sensor face
    return dict(a=((ld.x + 0.1, ld.y - 0.3, ld.z - 0.24), tuple(ld)), b=((ld.x + 0.09, ld.y - 0.28, ld.z - 0.23), tuple(ld)), lens=50,
                fstop=5.6, focus=ld)


def U44():
    A = ST.vault_complex("wreck", contacts="bypassed", taped=True); mc = A["mag_contact"]
    # from the corridor: the open vault door and, above its head, the plate holding the two contacts together
    return dict(a=((-0.65, -1.95, 1.55), (-0.1, -0.55, 2.0)), b=((-0.6, -1.85, 1.57), (-0.1, -0.55, 2.02)), lens=26, fstop=4.0, focus=mc)


def U45():
    A = S2.office("leasing"); k = A["keys"]
    return dict(a=((k.x - 0.35, k.y - 0.4, 1.12), tuple(k)), b=((k.x - 0.28, k.y - 0.33, 1.06), tuple(k)), lens=50, fstop=3.2, focus=k)


# ============================================================================ L21 the rubbish by the road
def U46():
    A = S3.woodland(); d = A["dump"]
    return dict(a=((d.x - 0.6, d.y - 1.6, 0.6), (d.x, d.y, 0.25)), b=((d.x - 2.5, d.y - 11.0, 3.4), (d.x, d.y, 0.8)), lens=28)


VO = open(os.path.join(HERE, "..", "..", "vo", "ANTWERP_P3_VO.txt")).read().splitlines()
PLAN = [
    ("U01", 1, 4.5, "The detectives in the wrecked vault (from behind)"), ("U02", 1, 3.5, "Upstairs the recorder slots are empty"),
    ("U03", 2, 3.0, "Peys at his desk, the phone ringing"), ("U04", 2, 4.0, "EXT: woodland beside the motorway"),
    ("U05", 3, 4.0, "Van Camp along the tree line (from behind)"), ("U06", 3, 4.5, "Van Camp kneels at the bin bags"),
    ("U07", 4, 4.0, "Diamond papers and an envelope from the bag (OTS)"),
    ("U08", 5, 4.5, "The lab: the rubbish laid out, two technicians"), ("U09", 5, 3.0, "Documents and receipts"),
    ("U10", 5, 3.0, "Traces of gems, a loupe"), ("U11", 5, 3.5, "A half-eaten salami sandwich"),
    ("U12", 6, 5.0, "Top-down: robbery rubbish beside household rubbish"),
    ("U13", 7, 4.0, "Torn scraps pieced together on a lightbox"), ("U14", 7, 3.5, "Another scrap"),
    ("U15", 7, 3.5, "EXT: the detectives walk back to the Diamond Center"),
    ("U16", 8, 3.0, "The building manager opens the tenant's file"),
    ("U17", 9, 3.0, "A fax to Turin"), ("U18", 9, 4.5, "Turin: an officer with Leonardo's file"),
    ("U19", 10, 3.0, "The supermarket receipt"), ("U20", 10, 3.5, "The shop's camera: a man at the checkout"),
    ("U21", 10, 3.5, "Peys watches the footage: Finotto"),
    ("U22", 11, 3.5, "A technician swabs the sandwich"), ("U23", 11, 3.0, "Sample tubes for DNA"),
    ("U24", 12, 3.5, "EXT: five days later Leonardo walks up"), ("U25", 13, 3.0, "His badge still works"),
    ("U26", 13, 3.5, "Staff watch him cross the lobby"), ("U27", 14, 3.0, "The manager dials the police"),
    ("U28", 14, 3.5, "...and keeps him talking"), ("U29", 14, 3.0, "Police come through the lobby doors"),
    ("U30", 15, 4.0, "Turin: investigators search the apartment on their knees"), ("U31", 15, 3.0, "Gems in the carpet pile"),
    ("U32", 15, 4.5, "The evidence links up: vault, rubbish, apartment"),
    ("U33", 16, 4.5, "2005: the court; Leonardo in the dock (from behind)"), ("U34", 16, 3.5, "Three accomplices"),
    ("U35", 17, 4.5, "Years later Leonardo tells another story (profile, half shadow)"),
    ("U36", 17, 3.0, "A faceless diamond dealer"), ("U37", 17, 4.5, "His claimed replica vault, the crew rehearsing"),
    ("U38", 17, 3.0, "A smaller haul"), ("U39", 18, 4.0, "Investigators check his account"),
    ("U40", 18, 3.0, "The lights were on"), ("U41", 18, 3.0, "The contents already sorted"),
    ("U42", 19, 5.0, "The empty vault: most of the loot was never found"),
    ("U43", 20, 3.0, "The tape over the light detector"), ("U44", 20, 3.0, "The displaced contacts"),
    ("U45", 20, 3.0, "The office lease: keys and badge"),
    ("U46", 21, 7.0, "The rubbish beside the road; pull back to the motorway"),
]
SHOTS = {sid: dict(fn=globals()[sid], dur=d, vo=VO[ln - 1], line=ln, desc=desc) for sid, ln, d, desc in PLAN}
