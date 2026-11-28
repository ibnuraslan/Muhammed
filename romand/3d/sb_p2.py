"""Romand Part 2 storyboard ("The student"): one key frame per shot.
    SHOT=P2-01 OUT=dir blender -b --python sb_p2.py     (run_sb.sh sb_p2.py renders every 3D shot)"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import rk, rsets as ST, rprops as PR
E = os.environ.get
OUT = E("OUT", "/tmp/sb_p2")
SPP = int(E("SPP", "10"))
HOT = lambda: rk.M()["hot"]


def seated(name, chair_xy, heading, kind="man", pose="sit_table", seed=0, back=0.06):
    a = math.radians(heading); bx, by = -math.sin(a) * back, math.cos(a) * back   # facing (sin a, -cos a); hip sits behind
    return rk.person(name, (0, 0, 0), heading, pose, kind, seed=seed, hip_at=Vector((chair_xy[0] + bx, chair_xy[1] + by, 0.53)))


def students_in_hall(A, n=16, romand_at=7, seed=1):
    rng = random.Random(seed); out = {}
    for i, s in enumerate(A["seats"][:n * 2:2]):
        nm = "romand" if i == romand_at else f"stu{i}"
        out[nm] = seated(nm, (s.x, s.y), 0, rng.choice(["man", "man", "woman"]) if nm != "romand" else "man", seed=40 + i)
    return out


# ---------------------------------------------------------------------------------------------------------- shots
def s01():
    A = ST.exam_hall(); F = students_in_hall(A)
    r = F["romand"]["pivot"].location
    rk.look(center=(0, 0, 0), extent=10, fill=160, moon=160, key=300, rim=300, fig_target=r + Vector((0, 0, 1)))
    rk.orbit_cam((r.x, r.y - 0.3, 0.9), -105, 48, 7.5, lens=35)


def s02():
    A = ST.results_corridor()
    rng = random.Random(3)
    for i in range(6):
        rk.person(f"crowd{i}", (-1.2 + i * 0.5 + rng.uniform(-0.1, 0.1), 1.2 + rng.uniform(-0.25, 0.2), 0), 180 + rng.uniform(-20, 20),
                  "stand", rng.choice(["man", "woman"]), seed=60 + i)
    rk.person("romand", (2.4, 0.2, 0), 90, "walk", "man", seed=1)          # turning away, walking out (+X)
    rk.look(center=(0, 1, 0), extent=6, fill=60, moon=60, key=260, rim=300, fig_target=(1.0, 0.8, 1.0))
    rk.orbit_cam((0.6, 1.0, 1.3), -110, 18, 7.2, lens=35, fstop=4.0)


def exp_paths(stage):
    A = ST.explainer()
    P = rk.M()
    rk.person("romand", (0, -1.6, 0), 180, "stand", "man", seed=1)
    paths = [((0, -1.3), (-2.6, 1.8)), ((0, -1.3), (0, 2.2)), ((0, -1.3), (2.6, 1.8))]
    for i, (a, b) in enumerate(paths):
        lit = stage >= 1
        rk.cyl(f"path{i}", (a[0], a[1], 0.01), (b[0], b[1], 0.01), 0.12, P["pawn"] if lit else P["grey"], 16)
    if stage >= 2:      # the fourth path, drawn in Seldom yellow just ahead of his feet
        rk.cyl("path4", (0, -1.3, 0.012), (1.2, -0.4, 0.012), 0.13, HOT(), 16)
    rk.look(center=(0, 0, 0), extent=5, fill=0, moon=0, key=200, rim=160, key_from=(-1, -2, 4))
    rk.camera((0.0, -4.2, 6.5), (0, 0.0, 0.2), lens=35)


def s03(): exp_paths(0)
def s04(): exp_paths(1)
def s05(): exp_paths(2)


def s06():
    A = ST.registration_office()
    rk.person("clerk", (0.1, 1.15, 0), 0, "stand", "woman", seed=5,
              extra=[("upperarm_r_049", rk.X, -45), ("lowerarm_r_050", rk.X, -40)])
    rk.person("romand", (-0.4, -0.55, 0), 180, "stand", "man", seed=1)
    rk.look(center=(0, 0.4, 0), extent=5, fill=40, moon=40, key=240, rim=260, fig_target=(0, 0.4, 1.2))
    rk.orbit_cam((0.1, 0.35, 1.15), -120, 30, 3.4, lens=40, fstop=2.8)


def lecture(two=False):
    A = ST.lecture_hall(); rng = random.Random(4)
    back = A["seats"][-9:]
    for i, s in enumerate(A["seats"]):
        if rng.random() < 0.45 or (two and i in (len(A["seats"]) - 5, len(A["seats"]) - 4)) or (not two and i == len(A["seats"]) - 5):
            nm = "romand" if i == len(A["seats"]) - 5 else ("friend" if two and i == len(A["seats"]) - 4 else f"lst{i}")
            rk.person(nm, (0, 0, 0), 0, "sit_table", rng.choice(["man", "woman"]) if nm.startswith("lst") else "man", seed=80 + i,
                      hip_at=Vector((s.x, s.y + 0.02, s.z + 0.52)))
    return A


def s07():
    A = lecture()
    rk.look(center=(0, 0, 1), extent=11, fill=200, moon=200, key=300, rim=300)
    rk.orbit_cam((0, 0.5, 1.2), -60, 30, 12, lens=32)


def s08():
    A = ST.student_room()
    d = A["desk"]
    rk.look(center=(0, 1, 0), extent=4, fill=16, moon=16)
    rk.camera(d + Vector((0.85, -0.75, 0.55)), d + Vector((-0.05, 0.1, 0.05)), lens=40, fstop=2.2)


def exp_lanes(own=False):
    A = ST.explainer(size=(9, 5.5))
    P = rk.M()
    for k in range(4):
        y = -1.8 + k * 1.2
        rk.box(f"lane{k}", (0, y, 0.005), (8, 0.7, 0.01), P["grey"])
        for g in range(4):
            x = -2.4 + g * 1.8
            hollow = own and k == 0
            m = P["pawn"] if not hollow else HOT()
            for side in (-1, 1):
                rk.cyl(f"gate{k}{g}{side}", (x, y + side * 0.3, 0), (x, y + side * 0.3, 0.45), 0.03, m, 8)
            rk.box(f"gatebar{k}{g}", (x, y, 0.45), (0.04, 0.64, 0.04), m)
        PR.pawn(f"walker{k}", ((-3.3 if k == 0 else -0.6 + k * 0.9), y, 0), s=0.9, hot=(k == 0))
    rk.camera((0.0, -6.0, 6.0), (0, -0.2, 0), lens=35)


def s09(): exp_lanes(False)
def s10(): exp_lanes(True)


def s11():
    A = ST.student_room()
    seated("romand", (0.2, 1.0), 180, "man", seed=1)
    rk.person("friend", (2.2, 0.0, 0), 90, "walk", "man", seed=3)
    rk.look(center=(0.6, 0.8, 0), extent=5, fill=40, moon=40, key=260, rim=260, fig_target=(1.2, 0.6, 1.0))
    rk.orbit_cam((0.9, 0.7, 1.0), -70, 28, 5.2, lens=35)


def s12():
    A = ST.student_room()
    d = A["desk"]
    rk.look(center=(0, 1, 0), extent=4, fill=16, moon=16)
    rk.camera(d + Vector((-0.2, -0.45, 0.32)), d + Vector((-0.3, 0.15, 0.08)), lens=50, fstop=1.8)


def s13():
    A = ST.cafe(); t = A["table"]
    seated("romand", (t.x - 0.55, t.y), 90, "man", seed=1); seated("friend", (t.x + 0.55, t.y), -90, "man", seed=3)
    rk.look(center=t, extent=5, fill=60, moon=60, key=280, rim=280, fig_target=t + Vector((0, 0, 0.4)))
    rk.orbit_cam(t + Vector((0, 0, 0.3)), -130, 22, 4.2, lens=40, fstop=2.8)


def s14():
    A = lecture(two=True)
    r = bpy.data.objects["romand"].location
    rk.look(center=(0, 2, 1), extent=8, fill=120, moon=120, key=300, rim=300, fig_target=r + Vector((0.5, 0, 1.2)))
    rk.orbit_cam(r + Vector((0.55, 0, 1.15)), -100, 12, 4.2, lens=40, fstop=2.8)


def s15():
    A = ST.explainer(); P = rk.M()
    rng = random.Random(5)
    for i in range(9):      # puzzle tiles forming a standing figure's outline; the last one in yellow
        x = -0.6 + (i % 3) * 0.6; y = -0.9 + (i // 3) * 0.6
        rk.box(f"tile{i}", (x, y, 0.03), (0.56, 0.56, 0.06), HOT() if i == 4 else P["pawn"], bevel=0.02)
    rk.camera((0.0, -2.6, 5.0), (0, -0.3, 0), lens=40)


def s16():
    A = ST.library()
    P = rk.M()
    bk = rk.group("book", [rk.box("book_l", (-0.16, 0, 0.015), (0.3, 0.42, 0.03), P["paper"], rot=(0, math.radians(6), 0)),
                           rk.box("book_r", (0.16, 0, 0.015), (0.3, 0.42, 0.03), P["paper"], rot=(0, math.radians(-6), 0)),
                           rk.box("book_page", (0.08, 0, 0.12), (0.01, 0.4, 0.2), P["paper"], rot=(0, math.radians(-30), 0))],
                  (0.0, 0.6, 0.76))
    rk.look(center=(0, 0.6, 0.7), extent=3, fill=10, moon=12)
    rk.camera((0.45, 0.15, 1.2), (0.0, 0.6, 0.78), lens=45, fstop=2.0)


def s17():
    A = ST.diploma_wall()
    rk.look(center=(0, -1, 1.5), extent=3, fill=10, moon=14)
    rk.spot("frame_spot", (0.4, -1.6, 2.6), A["frame"], 40, (1.0, 0.7, 0.3), 25)
    rk.camera((-0.45, -1.05, 1.5), A["frame"] + Vector((0.05, 0, 0)), lens=50, fstop=2.8)


def s18():
    A = ST.church(); rng = random.Random(7)
    rk.person("romand", (-0.35, 2.3, 0.9), 0, "stand", "man", seed=1)
    rk.person("florence", (0.35, 2.3, 0.9), 0, "stand", "woman", seed=2)
    for i in range(10):
        x = rng.uniform(-3.5, 3.5); y = rng.uniform(-2.5, 0.6)
        rk.person(f"guest{i}", (x, y, 0), rng.uniform(150, 210), "stand", rng.choice(["man", "woman", "old_man", "old_woman"]), seed=90 + i)
    for i in range(60):     # rice in the air
        rk.sphere(f"rice{i}", (rng.uniform(-1.5, 1.5), rng.uniform(0.6, 2.4), rng.uniform(1.2, 3.0)), 0.012, rk.M()["paper"], seg=6)
    rk.look(center=(0, 1, 0), extent=10, fill=220, moon=220, key=320, rim=320, fig_target=(0, 2.3, 1.9))
    rk.orbit_cam((0, 1.4, 1.6), -95, 22, 13, lens=35)


def s20():
    A = ST.pharmacy()
    rk.person("florence", (0.4, 1.2, 0), 0, "stand", "woman", seed=2)
    rk.look(center=(0, 1, 0), extent=5, fill=60, moon=60, key=260, rim=300, fig_target=(0.4, 1.2, 1.0))
    rk.orbit_cam((0.2, 1.4, 1.2), -100, 14, 5.5, lens=35, fstop=4.0)


def dinner_party():
    A = ST.round_dinner(6); rng = random.Random(8); figs = {}
    kinds = ["man", "woman", "man", "woman", "man", "woman"]
    for i, (p, hd) in enumerate(A["seats"]):
        nm = "romand" if i == 0 else f"guest{i}"
        a = math.radians(hd); behind = Vector((-math.sin(a), math.cos(a), 0)) * 0.06
        figs[nm] = rk.person(nm, (0, 0, 0), hd, "sit_table", kinds[i], seed=100 + i, hip_at=Vector((p.x, p.y, 0.53)) + behind)
    return A, figs


def s21():
    A, F = dinner_party()
    rk.look(center=(0, 0, 0), extent=6, fill=80, moon=80, key=300, rim=300)
    rk.orbit_cam((0, 0, 0.8), -120, 30, 4.6, lens=32)


def s22():
    A, F = dinner_party()
    r = bpy.data.objects["romand"].location
    rk.look(center=(0, 0, 0), extent=6, fill=60, moon=60, key=300, rim=300, fig_target=r + Vector((0, 0, 1.0)))
    rk.orbit_cam(r + Vector((0, 0, 1.0)), 180, 14, 2.6, lens=45, fstop=2.2)


def s23():
    A = ST.who_ext()
    rk.look(center=(0, 2, 0), extent=16, fill=300, moon=300)
    rk.orbit_cam((0, 3, 5), -105, 22, 30, lens=32)


def s25():
    A = ST.waiting_room()
    rk.look(center=(0, 1, 0), extent=5, fill=40, moon=40)
    rk.orbit_cam((0.4, 1.6, 1.0), -115, 22, 5.2, lens=32)


def s26():
    A = ST.who_lobby(); rng = random.Random(9)
    for i in range(7):
        rk.person(f"staff{i}", (rng.uniform(-5, 5), rng.uniform(-3, 3), 0), rng.uniform(0, 360), "walk_carry" if i % 2 else "walk",
                  rng.choice(["man", "woman"]), seed=120 + i)
    rk.look(center=(0, 0, 0), extent=12, fill=240, moon=240, key=300, rim=300)
    rk.orbit_cam((0, 1, 1.5), -95, 30, 15, lens=32)


def s29():
    A = ST.house_pm(night=False, snow=False, lit=(), door_lit=True)
    car = PR.car405("car", A["drive"] + Vector((0, 0.5, 0)), math.pi / 2, lights=False)
    rk.person("romand", (2.4, -3.3, 0), 90, "walk_carry", "man", seed=1)
    case = rk.box("briefcase", (0, 0, 0), (0.42, 0.11, 0.32), rk.M()["cloth"], bevel=0.02)
    fr = rk.person("florence", (0.0, -2.7, 0), 0, "stand", "woman", seed=2)
    rom = {"pivot": bpy.data.objects["romand"], "arm": [o for o in bpy.data.objects["romand"].children_recursive if o.type == 'ARMATURE'][0]}
    h = rk.bone_world(rom, "hand_r_051"); case.location = h + Vector((0, 0, -0.2)); case.rotation_euler.z = math.pi / 2
    rk.attach(case, rom, "hand_r_051")
    rk.look(center=(1.5, -2.5, 0), extent=12, fill=260, moon=260, key=300, rim=300, fig_target=(2.0, -3.0, 1.0))
    rk.orbit_cam((1.8, -2.4, 1.2), -120, 30, 11, lens=35)


def s30():
    A = ST.empty_office(False)
    rk.look(center=(0, 1, 0), extent=5, fill=30, moon=30)
    rk.orbit_cam((0, 1.2, 0.9), -110, 18, 5.0, lens=32)


def s31():
    A = ST.empty_office(True)
    rk.look(center=(0, 1, 0), extent=5, fill=30, moon=30)
    rk.orbit_cam((0, 1.0, 0.9), -60, 22, 5.6, lens=32)


def s32():
    A = ST.house_pm(night=False, snow=False)
    lb = A["letterbox"]
    rk.look(center=lb, extent=4, fill=60, moon=60)
    rk.camera(lb + Vector((0.55, -0.6, 0.25)), lb + Vector((0, 0, 0.02)), lens=50, fstop=2.0)


SHOTS3D = {"P2-01": s01, "P2-02": s02, "P2-03": s03, "P2-04": s04, "P2-05": s05, "P2-06": s06, "P2-07": s07, "P2-08": s08,
           "P2-09": s09, "P2-10": s10, "P2-11": s11, "P2-12": s12, "P2-13": s13, "P2-14": s14, "P2-15": s15, "P2-16": s16,
           "P2-17": s17, "P2-18": s18, "P2-20": s20, "P2-21": s21, "P2-22": s22, "P2-23": s23, "P2-25": s25, "P2-26": s26,
           "P2-29": s29, "P2-30": s30, "P2-31": s31, "P2-32": s32}
EXPLAINERS = {"P2-03", "P2-04", "P2-05", "P2-09", "P2-10", "P2-15"}
MAXEV = {}


def run(sid):
    rk.setup(res=(960, 540), spp=SPP)
    SHOTS3D[sid]()
    if sid in EXPLAINERS:
        rk.grade(expo=-1.2, vig=0.5)
        return rk.render(os.path.join(OUT, sid + ".png"))
    rk.grade(expo=-2.6)
    return rk.render_to_luma(os.path.join(OUT, sid + ".png"), max_ev=MAXEV.get(sid, 5.0))


if __name__ == "__main__":
    sid = E("SHOT", "P2-01")
    for s in (SHOTS3D if sid == "all" else sid.split(",")):
        run(s)
