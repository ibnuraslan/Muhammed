"""Romand Part 1 storyboard: one key frame per shot (fast preview: 960x540, low spp, OIDN).
    SHOT=P1-01 OUT=dir blender -b --python sb_p1.py      (SHOT=all renders every 3D shot in turn)
2D shots (title, disclaimer, link board, timeline) are made in post (sb_post.py) from the kit."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import rk, rsets as ST, rprops as PR
E = os.environ.get
OUT = E("OUT", "/tmp/sb_p1")
SPP = int(E("SPP", "10"))


def fig_in_seat(name, seat, heading, kind="man", pose="drive", seed=0):
    return rk.person(name, (0, 0, 0), heading, pose, kind, seed=seed, hip_at=Vector(seat) + Vector((0, 0, 0.08)))


def forest_scene(car_kw=None, driver=True, passenger=True, pass_pose="car_sit", seed=3):
    A = ST.forest(seed=seed, car_kw=car_kw or {})
    car = A["car"]
    figs = {}
    if driver:
        figs["romand"] = fig_in_seat("romand", car["seats"]["driver"], 90, "man", "car_drive", 1)
    if passenger:
        figs["chantal"] = fig_in_seat("chantal", car["seats"]["passenger"], 90, "woman", pass_pose, 2)
    return A, car, figs


# ---------------------------------------------------------------------------------------------------------- shots
def s01():
    A, car, f = forest_scene(dict(lights=True))
    rk.look(center=(0, 0, 0), extent=12, fill=260, moon=300, key=300, rim=300, fig_target=car["root"].location + Vector((0, 0, 1)))
    rk.orbit_cam((0.4, -0.6, 0.6), -125, 36, 11.5, lens=35)


def s02():
    A, car, f = forest_scene(dict(lights=True), seed=3)
    rk.look(center=(0, 0, 0), extent=16, fill=420, moon=420)
    rk.orbit_cam((0, 0, 0), -100, 74, 24, lens=32)


def s03():
    A, car, f = forest_scene(dict(lights=True, dome=12.0))
    rk.look(center=(0, -0.8, 0), extent=8, fill=120, moon=140, key=200, rim=260, key_from=(-1.5, -2.5, 3.0), rim_from=(-2.0, 1.0, 1.5))
    rk.orbit_cam(car["root"].location + Vector((0.0, 0, 1.05)), 200, 18, 4.6, lens=40)


def s04():
    A, car, f = forest_scene(dict(lights=True, boot=0.1), driver=True, passenger=True)
    mw = car["root"].matrix_world
    rk.look(center=mw @ Vector((-2, 0, 0)), extent=5, fill=40, moon=40)
    rk.camera(mw @ Vector((-4.6, -2.6, 2.3)), mw @ Vector((-1.75, 0, 0.9)), lens=50, fstop=2.2)


def s05():
    A = ST.country_house()
    rk.look(center=(0, 2, 0), extent=14, fill=160, moon=200)
    rk.camera((-6.0, -14.0, 2.2), (0.5, 3.0, 3.2), lens=45, fstop=4.0, focus=17.5)


def s06():
    A = ST.dinner_table()
    rk.look(center=(0, 0, 0), extent=6, fill=50, moon=60)
    rk.camera((-3.4, -0.55, 1.25), (1.6, 0.2, 0.85), lens=32, fstop=2.8, focus=3.0)


def s07():
    A, car, f = forest_scene(dict(lights=True, boot=1.0, door_l=1.0), driver=False, passenger=True)
    mw = car["root"].matrix_world
    stand = mw @ Vector((-2.75, 0.0, 0))
    rk.person("romand", (stand.x, stand.y, 0), 90, "boot", "man", seed=4)   # faces +X, into the boot
    rk.look(center=mw @ Vector((-1.5, 0, 0)), extent=7, fill=120, moon=140, key=320, rim=320,
            fig_target=mw @ Vector((-2.4, 0, 1.0)), key_from=(-2.0, -3.0, 3.0))
    rk.orbit_cam(mw @ Vector((-1.3, 0, 0.9)), -150, 24, 6.8, lens=35)


def s08(lifted=False):
    """Macro into the open boot from above (no figure in frame): the red coil under the boot lamp."""
    A, car, f = forest_scene(dict(lights=True, boot=1.0, beams=False), driver=False, passenger=False)
    mw = car["root"].matrix_world
    bf = car["boot_floor"]
    coil = PR.cord_coil("cord", bf + Vector((0.05, 0.12, 0.0)), 0.12)
    rk.look(center=bf, extent=3, fill=20, moon=20)
    rk.accent(coil, energy=60, size_deg=22, offset=(-0.3, -0.4, 1.2))
    d = 0.55 if lifted else 0.85
    rk.camera(bf + mw.to_3x3() @ Vector((-0.55, -0.35, 0.0)) + Vector((0, 0, d)), bf + Vector((0.03, 0.1, 0.02)), lens=50, fstop=2.0)

def s09():
    s08(lifted=True)


def s10():
    A, car, f = forest_scene(dict(lights=True, door_l=1.0, door_r=1.0, dome=25.0), driver=False, passenger=False)
    mw = car["root"].matrix_world
    rk.person("romand", tuple(mw @ Vector((0.2, 1.45, 0))), 0, "stand", "man", seed=5)
    rk.person("chantal", tuple(mw @ Vector((-0.4, -1.5, 0))), 180, "stand_bow", "woman", seed=6)
    rk.look(center=(0, 0, 0), extent=18, fill=520, moon=500, key=400, rim=400)
    rk.orbit_cam((0, -0.8, 0), -95, 72, 30, lens=35)


def s11():
    A, car, f = forest_scene(dict(lights=True), driver=False, passenger=False)
    mw = car["root"].matrix_world
    can = PR.canister("canister", mw @ Vector((3.3, -0.35, 0)), rz=0.7)
    PR.beam("mist", mw @ Vector((2.3, -0.55, 0.62)), car["fwd"] + Vector((0, -0.1, -0.05)), 6.0, 1.2, (1.0, 0.9, 0.7), 0.05)
    rk.look(center=mw @ Vector((3, 0, 0)), extent=4, fill=30, moon=40)
    rk.accent(can, energy=50, size_deg=18, offset=(0.6, -0.8, 1.6))
    rk.camera(mw @ Vector((2.5, -1.35, 0.42)), mw @ Vector((3.6, -0.2, 0.05)), lens=40, fstop=2.2)


def s12():
    A, car, f = forest_scene(dict(lights=True, dome=20.0), driver=False, passenger=False)
    mw = car["root"].matrix_world
    rk.person("romand", tuple(mw @ Vector((0.3, 1.6, 0))), -20, "stand", "man", seed=5)
    rk.person("chantal", tuple(mw @ Vector((-1.2, -1.7, 0))), 150, "stand_bow", "woman", seed=6)
    for i, (x, y) in enumerate(((-9.0, -6.8), (-3.6, -7.6))):
        PR.bare_tree(f"fg{i}", (x, y, 0), 6.0, seed=50 + i)
    rk.look(center=(0, 0, 0), extent=10, fill=200, moon=200, key=200, rim=300)
    rk.camera((-7.5, -10.5, 2.2), (0, -0.8, 0.8), lens=45, fstop=5.6, focus=13.0)


def s13():
    A, car, f = forest_scene(dict(lights=True, door_r=1.0), driver=False, passenger=False)
    mw = car["root"].matrix_world
    p = mw @ Vector((4.3, -0.2, 0))
    rk.person("chantal", (p.x, p.y, 0), 90, "stand_hug", "woman", seed=7)    # faces away from the car, into the dark
    rk.look(center=p, extent=6, fill=40, moon=60, key=140, rim=420, fig_target=p + Vector((0, 0, 1.0)), rim_from=(-2.0, 0.3, 0.6),
            key_from=(-2.0, -2.0, 2.0))
    rk.orbit_cam(p + Vector((0, 0, 1.0)), 160, 6, 3.6, lens=45, fstop=2.8)


def explainer_pair(notes=False):
    A = ST.explainer()
    PR.table("exp_table", (0, 0, 0), w=1.6, d=0.9, h=0.75)
    rk.person("a", (0, 0, 0), 90, "sit_table", "woman", seed=8, hip_at=Vector((-1.15, 0, 0.56)))
    rk.person("b", (0, 0, 0), -90, "sit_table", "man", seed=9, hip_at=Vector((1.15, 0, 0.56)))
    for x in (-1.15, 1.15):
        PR.chair(f"exp_ch{x}", (x, 0, 0), math.radians(-90 if x < 0 else 90))
    if notes:
        PR.notes_stack("notes", (0.25, 0.0, 0.76), n=7, rz=0.2, hot=True)
    rk.look(center=(0, 0, 0), extent=5, fill=0.0, moon=0.0, key=160, rim=120, key_from=(-1, -2, 4))
    rk.camera((0.0, -0.9, 6.2), (0, 0, 0.4), lens=40)


def s14():
    explainer_pair(False)


def s15():
    explainer_pair(True)


def s16():
    A, car, f = forest_scene(dict(lights=True, dome=14.0), driver=False, passenger=False)
    mw = car["root"].matrix_world
    PR.doctor_bag("bag", mw @ Vector((-0.9, 0.3, 0.69)), rz=0.3)
    rk.look(center=mw @ Vector((-0.9, 0, 0.7)), extent=3, fill=8, moon=10)
    rk.camera(mw @ Vector((-0.55, -1.05, 1.45)), mw @ Vector((-0.9, 0.25, 0.85)), lens=40, fstop=2.0)


def s17():
    A, car, f = forest_scene(dict(lights=True), seed=3)
    rk.look(center=(0, 0, 0), extent=14, fill=300, moon=300)
    rk.orbit_cam((2.5, -0.8, 0), -150, 62, 17, lens=35)


def s18():
    A = ST.paris_street()
    PR.car405("car", (0.6, 0.0, 0), math.pi, lights=True, beams=False)
    rk.look(center=(0, 2, 0), extent=12, fill=200, moon=200)
    rk.orbit_cam((0.5, 2.5, 3.0), -100, 26, 19, lens=35)


def s19():
    A = ST.paris_street()
    car = PR.car405("car", (0.6, 0.0, 0), math.pi, lights=True, beams=False, dome=6.0)
    fig_in_seat("romand", car["seats"]["driver"], -90, "man", "car_drive", 1)
    rk.person("chantal", (1.0, 1.9, 0.12), 180, "walk", "woman", seed=2)     # walking to the door (faces +Y)
    rk.look(center=(0.8, 1.2, 0), extent=7, fill=120, moon=120, key=300, rim=300, fig_target=(1.0, 1.6, 1.0))
    rk.orbit_cam((0.8, 1.4, 1.0), -70, 22, 7.5, lens=35)


def s20():
    A = ST.house_pm(lit=(), door_lit=False)
    rk.look(center=(0, 0, 0), extent=14, fill=220, moon=260)
    rk.orbit_cam((0, -1.5, 2.0), -100, 22, 15, lens=35)


def s21():
    A = ST.hallway()
    rk.look(center=(-1, 1, 0), extent=4, fill=60, moon=60)
    rk.point("hall_lamp", (-0.6, 0.6, 2.6), 60, (1.0, 0.7, 0.35))
    b = A["boots"]
    rk.camera(b + Vector((0.9, -0.95, 0.45)), b + Vector((0, 0, 0.08)), lens=45, fstop=2.0)


def s22():
    A = ST.parents_house(lit=())
    rk.look(center=(0, 0, 0), extent=14, fill=200, moon=240)
    rk.orbit_cam((0, -1.0, 2.0), -95, 18, 14, lens=35)


def s23():
    """Both houses side by side in the void, lights off."""
    P = rk.M()
    for i, x in enumerate((-8.0, 8.0)):
        m = rk.mat(f"lawn{i}", (0.75, 0.74, 0.7), 0.5)
        rk.box(f"slab{i}", (x, 0, -0.1), (11, 9, 0.2), m)
        rk.fade_to_void([m], (x, 0), 3.5, 5.6)
        PR.gable_house(f"house{i}", (x, 0.5, 0), 0.0, w=8 if i else 9, d=6.5, h=5.0, roof=2.6, snow=True)
        for k in range(6):
            a = k / 6 * 6.28 + i
            PR.pine(f"p{i}{k}", (x + math.cos(a) * 4.4, math.sin(a) * 3.4, 0), 4.5, seed=k + 10 * i)
    rk.look(center=(0, 0, 0), extent=22, fill=420, moon=300)
    rk.orbit_cam((0, 0.5, 1.0), -90, 55, 46, lens=35)


def s26():
    A = ST.garden_table()
    # far side (y>0) faces -Y (heading 0) toward the table, near side faces +Y (heading 180); Romand at the head
    seats = [((-1.95, 0.0), 90, "man", "romand"), ((-1.1, 0.78), 0, "woman", "florence"), ((-0.2, 0.78), 0, "girl", "caroline"),
             ((0.7, 0.78), 0, "child", "antoine"), ((-0.6, -0.78), 180, "old_man", "aime"), ((0.4, -0.78), 180, "old_woman", "annemarie")]
    for i, ((x, y), hd, kind, nm) in enumerate(seats):
        PR.chair(f"ch_{nm}", (x, y, 0), math.radians(hd))
        back = {0: (0, 0.06), 180: (0, -0.06), 90: (-0.06, 0)}[hd]
        rk.person(nm, (0, 0, 0), hd, "sit_table", kind, seed=20 + i, hip_at=Vector((x + back[0], y + back[1], 0.55)))
    rk.look(center=(0, 0, 0), extent=8, fill=120, moon=160, key=320, rim=320)
    rk.orbit_cam((0, 0, 0.7), -125, 38, 7.2, lens=35)

def s28():
    A = ST.who_ext()
    rk.person("romand", (-3.0, -5.0, 0.12), -90, "walk_carry", "man", seed=5)
    PR.doctor_bag("case", (-3.0, -5.0, 0.12), stetho=False) if False else None
    rk.look(center=(-2, -3, 0), extent=16, fill=300, moon=300, key=300, rim=300, fig_target=(-3.0, -5.0, 1.0))
    rk.orbit_cam((-2.0, -1.0, 3.5), -105, 28, 22, lens=35)


def s29():
    A = ST.diploma_wall()
    rk.look(center=(0, -1, 1.5), extent=3, fill=10, moon=14)
    rk.spot("frame_spot", (0.4, -1.6, 2.6), A["frame"], 40, (1.0, 0.7, 0.3), 25)
    rk.camera((0.55, -1.25, 1.62), A["frame"] + Vector((-0.05, 0, 0)), lens=50, fstop=2.8)


def s30():
    A = ST.explainer()
    PR.model_house("model_house", (0, 0, 0), s=1.3)
    for i in range(7):
        a = i / 7 * 6.28 + 0.3; p = Vector((math.cos(a) * 2.9, math.sin(a) * 1.8, 0))
        PR.pawn(f"pawn{i}", p, s=0.9)
        for k in range(2, 8):    # coin trail into the house
            q = p.lerp(Vector((0, 0, 0)), k / 9.0)
            rk.cyl(f"coin{i}_{k}", q + Vector((0, 0, 0.01)), q + Vector((0, 0, 0.03)), 0.07, rk.M()["hot"], 16)
    rk.camera((0.0, -4.2, 6.4), (0, 0, 0.3), lens=35)


def s31():
    A = ST.house_pm(lit=(), door_lit=True)
    rk.look(center=(0, 0, 0), extent=14, fill=160, moon=200)
    rk.orbit_cam((0, -2.0, 1.8), -92, 12, 12, lens=40)


def s33():
    A = ST.faculty()
    for i in range(6):
        rk.person(f"st{i}", (-3.5 + i * 1.4, -2.5 + (i % 3) * 1.0, 0), [10, 170, 30, 200, -20, 160][i], "walk", "man" if i % 2 else "woman", seed=30 + i)
    rk.look(center=(0, 0, 0), extent=16, fill=260, moon=260, key=300, rim=300)
    rk.orbit_cam((0, 0.5, 2.5), -100, 40, 24, lens=35)


SHOTS3D = {"P1-01": s01, "P1-02": s02, "P1-03": s03, "P1-04": s04, "P1-05": s05, "P1-06": s06, "P1-07": s07, "P1-08": s08,
           "P1-09": s09, "P1-10": s10, "P1-11": s11, "P1-12": s12, "P1-13": s13, "P1-14": s14, "P1-15": s15, "P1-16": s16,
           "P1-17": s17, "P1-18": s18, "P1-19": s19, "P1-20": s20, "P1-21": s21, "P1-22": s22, "P1-23": s23, "P1-26": s26,
           "P1-28": s28, "P1-29": s29, "P1-30": s30, "P1-31": s31, "P1-33": s33}
EXPLAINERS = {"P1-14", "P1-15", "P1-30"}
MAXEV = {"P1-21": 1.5, "P1-29": 1.5}


def run(sid):
    rk.setup(res=(960, 540), spp=SPP)
    SHOTS3D[sid]()
    if sid in EXPLAINERS:
        rk.grade(expo=-1.2, vig=0.5)
        return rk.render(os.path.join(OUT, sid + ".png"))
    rk.grade(expo=-2.6)
    return rk.render_to_luma(os.path.join(OUT, sid + ".png"), max_ev=MAXEV.get(sid, 5.0))


if __name__ == "__main__":
    sid = E("SHOT", "P1-01")
    for s in (SHOTS3D if sid == "all" else sid.split(",")):
        run(s)
