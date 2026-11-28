"""Romand film: reusable diorama sets. Each builder makes one slab floating in the black void, fades its edges into
black, and returns a dict of anchors (positions, objects) for figures, props and cameras.
Codes follow SHOTLIST.md: FOR CAR PAR HPM HPI CLV UNI WHO CAF LIB HOT CRT PRI ABB CHU FTB HOS EXP."""
import math, random
import bpy
from mathutils import Vector
import rk, rprops as PR
from rk import box, cyl, M


def _slab(name, size, m, z=0.0, fade=None, center=(0, 0)):
    s = box(name, (center[0], center[1], z - 0.1), (size[0], size[1], 0.2), m)
    if fade:
        rk.fade_to_void([m], center, fade[0], fade[1])
    return s


# ------------------------------------------------------------------------------------------------- FOR: forest road
def forest(seed=3, car_kw=None, size=(18, 14), density=70, car_at=(0.0, 0.0), car_rz=0.0, snow=False):
    P = M(); rng = random.Random(seed)
    _slab("forest_floor", size, P["soil"], fade=(5.0, 8.0))
    road = box("road", (0, 0, 0.005), (size[0], 3.6, 0.02), P["asphalt"])
    rk.fade_to_void([P["asphalt"]], (0, 0), 5.0, 8.5)
    box("verge_l", (0, 2.1, 0.01), (size[0], 0.6, 0.02), P["soil"]); box("verge_r", (0, -2.1, 0.01), (size[0], 0.6, 0.02), P["soil"])
    trees = []
    for i in range(density):
        x = rng.uniform(-size[0] / 2 + 0.5, size[0] / 2 - 0.5)
        side = 1 if rng.random() < 0.72 else -1          # the near (camera, -y) side stays sparse and low
        y = side * rng.uniform(2.8, size[1] / 2 - 0.3)
        if side < 0 and abs(x - car_at[0]) < 4.5:
            continue
        hk = 1.0 if side > 0 else 0.7
        if rng.random() < 0.55:
            trees.append(PR.pine(f"pine{i}", (x, y, 0), rng.uniform(4.5, 6.5) * hk, seed=i))
        else:
            trees.append(PR.bare_tree(f"tree{i}", (x, y, 0), rng.uniform(4.0, 6.0) * hk, seed=i))
    car = PR.car405("car", (car_at[0], car_at[1] - 0.8, 0), car_rz, **(car_kw or {}))
    return dict(car=car, trees=trees, center=Vector((0, 0, 0)))


# ------------------------------------------------------------------------------------------------- FTB: phantom country house
def country_house(seed=5):
    P = M(); rng = random.Random(seed)
    _slab("ftb_ground", (20, 16), P["soil"], fade=(5.0, 9.0))
    PR.gable_house("ftb_house", (0, 3.0, 0), 0.0, w=14, d=8, h=6.0, roof=3.0, lit=list(range(10)), door_lit=True)
    for i in range(26):
        x = rng.uniform(-10, 10); y = rng.uniform(-8, -1.5)
        PR.bare_tree(f"ftb_tree{i}", (x, y, 0), rng.uniform(5, 8), seed=100 + i)
    return dict(house=Vector((0, 3.0, 0)))


def dinner_table(n=10, seed=6):
    P = M()
    _slab("dt_floor", (9, 6), P["wet"], fade=(2.8, 4.6))
    box("dt_wall", (0, 2.4, 1.6), (9, 0.3, 3.2), P["grey"]); rk.fade_to_void([P["grey"]], (0, 0), 3.0, 5.0)
    L = 4.6
    PR.table("dt_table", (0, 0, 0), w=L, d=1.1, h=0.76, cloth=True)
    k = 0
    for i in range(n // 2):
        x = -L / 2 + 0.4 + i * (L - 0.8) / (n // 2 - 1)
        for s in (-1, 1):
            PR.chair(f"dt_chair{k}", (x, s * 0.82, 0), 0.0 if s > 0 else math.pi); k += 1
            PR.place_setting(f"dt_ps{k}", (x, s * 0.33, 0.77))
    for i in range(5):
        PR.candle(f"dt_candle{i}", (-L / 2 + 0.5 + i * (L - 1.0) / 4, 0, 0.77))
    for x in (-2.8, 0, 2.8):
        PR.window(f"dt_win{x}", (x, 2.24, 1.6), 1.2, 1.6, "y", lit=False, sign=-1)
    return dict(table=Vector((0, 0, 0.77)))


# ------------------------------------------------------------------------------------------------- PAR: Paris street at night
def paris_street(seed=7, lit_frac=0.18):
    P = M()
    _slab("par_street", (16, 12), P["asphalt"], fade=(4.5, 7.5))
    box("par_pavement", (0, 2.2, 0.06), (16, 2.6, 0.12), P["grey"]); rk.fade_to_void([P["grey"]], (0, 0), 4.5, 7.5)
    PR.slab_block("par_block", (0, 6.0, 0.12), 14, 6.4, 18, 6, 9, lit_frac, seed=seed)
    box("par_door", (1.2, 2.78, 1.3), (1.4, 0.08, 2.4), P["win"])
    for x in (-5, 5):
        cyl("par_lamp_post", (x, 1.2, 0), (x, 1.2, 4.2), 0.05, P["steel"], 8)
        box("par_lamp", (x, 1.0, 4.2), (0.3, 0.5, 0.15), P["lamp"])
        rk.spot("par_lamp_l", (x, 1.0, 4.1), (x, 0.6, 0), 600, (1.0, 0.62, 0.25), 70, 0.6, 0.2)
    return dict(door=Vector((1.2, 2.6, 0.12)), kerb=Vector((0, 0.8, 0)))


# ------------------------------------------------------------------------------------------------- HPM: the house in Prevessin-Moens
def house_pm(night=True, snow=True, lit=(), door_lit=False, seed=8, swing=False):
    P = M(); rng = random.Random(seed)
    _slab("hpm_lawn", (18, 14), P["snow"] if snow else P["foliage"], fade=(5.0, 8.0))
    box("hpm_drive", (4.2, -3.5, 0.01), (3.0, 7.0, 0.02), P["asphalt"])
    PR.gable_house("hpm_house", (0, 1.5, 0), 0.0, w=10, d=7.5, h=5.4, roof=2.6, lit=lit, door_lit=door_lit, snow=snow)
    box("hpm_porch_lamp", (0.5, -2.3, 2.5), (0.12, 0.12, 0.2), P["lamp"] if lit or door_lit else P["dark"])
    if lit or door_lit:
        rk.point("hpm_porch_l", (0.5, -2.6, 2.4), 40, (1.0, 0.6, 0.2))
    for i in range(16):
        a = rng.uniform(0, 6.28); r = rng.uniform(7.0, 8.5)
        PR.pine(f"hpm_pine{i}", (math.cos(a) * r, math.sin(a) * r * 0.75 + 1.5, 0), rng.uniform(5, 8), seed=200 + i)
    for i in range(9):
        PR.bush(f"hpm_hedge{i}", (-7 + i * 1.3, -6.0, 0), 0.6, seed=i)
    PR.letterbox("hpm_letterbox", (2.6, -6.2, 0))
    if swing:
        P2 = M()
        for s in (-1, 1):
            cyl("swing_leg", (-5 + s * 0.8, -3.0, 0), (-5 + s * 0.6, -3.0, 2.2), 0.04, P2["steel"], 8)
        cyl("swing_top", (-5.7, -3.0, 2.2), (-4.3, -3.0, 2.2), 0.04, P2["steel"], 8)
        for s in (-1, 1):
            cyl("swing_rope", (-5 + s * 0.22, -3.0, 2.2), (-5 + s * 0.22, -3.0, 0.5), 0.008, P2["grey"], 6)
        box("swing_seat", (-5, -3.0, 0.48), (0.5, 0.2, 0.04), P2["wood"])
    return dict(door=Vector((0, -2.3, 0)), drive=Vector((4.2, -3.5, 0)), letterbox=Vector((2.6, -6.2, 1.12)))


# ------------------------------------------------------------------------------------------------- HPI: house interior pieces
def hallway(seed=9):
    """Cutaway hallway: floor, back wall with the front door, side wall with a coat rack, children's boots."""
    P = M()
    _slab("hpi_floor", (6, 5), P["wood"], fade=(2.2, 3.6))
    box("hpi_wall_b", (0, 2.0, 1.4), (6, 0.2, 2.8), P["light"]); box("hpi_wall_l", (-2.4, 0, 1.4), (0.2, 4.0, 2.8), P["light"])
    rk.fade_to_void([P["light"]], (0, 0.5), 2.4, 4.0)
    box("hpi_door", (0.4, 1.88, 1.05), (0.95, 0.06, 2.1), P["wood"])
    cyl("hpi_knob", (0.0, 1.84, 1.0), (0.0, 1.8, 1.0), 0.03, P["chrome"], 10)
    PR.boots("hpi_boots_a", (-1.4, 1.5, 0.0), 0.15, 0.55); PR.boots("hpi_boots_b", (-1.05, 1.55, 0.0), -0.1, 0.5)
    box("hpi_rack", (-2.25, 0.8, 1.55), (0.06, 1.4, 0.06), P["wood"])
    for i, y in enumerate((0.35, 0.75, 1.15)):
        PR.cone(f"hpi_coat{i}", (-2.2, y, 1.1), 0.18 if i else 0.12, 0.08, 0.8 if i else 0.55, P["coat"], 16)
    # snow-melt puddles round the boots
    box("hpi_mat", (-1.2, 1.4, 0.006), (1.1, 0.6, 0.012), P["cloth"])
    return dict(boots=Vector((-1.25, 1.52, 0.05)), door=Vector((0.4, 1.85, 1.0)))


# ------------------------------------------------------------------------------------------------- CLV: the parents' house
def parents_house(night=True, lit=(), seed=10):
    P = M(); rng = random.Random(seed)
    _slab("clv_ground", (18, 14), P["foliage"], fade=(5.0, 8.0))
    water = box("clv_lake", (0, 8.5, -0.02), (22, 6, 0.05), P["wet"])
    PR.gable_house("clv_house", (0, 1.0, 0), 0.0, w=8.0, d=7.0, h=5.0, roof=3.0, lit=lit, chimney=True)
    for i in range(10):
        PR.bare_tree(f"clv_tree{i}", (rng.uniform(-8, 8), rng.uniform(-6, -2.5) if i % 2 else rng.uniform(4, 6), 0), rng.uniform(5, 7), seed=300 + i)
    # neighbours: village roofs falling into the dark
    for i, x in enumerate((-9.5, 9.5)):
        PR.gable_house(f"clv_n{i}", (x, 2.0, 0), 0.0, w=6, d=6, h=4.5, roof=2.4, lit=(), chimney=False)
    return dict(door=Vector((0, -2.5, 0)), window=Vector((-2.67, -2.5, 1.35)))


def garden_table(seed=11):
    P = M()
    _slab("gt_lawn", (12, 10), P["foliage"], fade=(3.2, 5.5))
    PR.table("gt_table", (0, 0, 0), w=3.2, d=1.0, h=0.75, cloth=True)
    for i in range(4):
        PR.place_setting(f"gt_ps{i}", (-1.1 + i * 0.73, -0.25, 0.76)); PR.place_setting(f"gt_psb{i}", (-1.1 + i * 0.73, 0.25, 0.76), math.pi)
    for i in range(6):
        PR.bare_tree(f"gt_tree{i}", (-5 + i * 2, 4.2, 0), 6.0, seed=400 + i)
    return dict(table=Vector((0, 0, 0.75)))


# ------------------------------------------------------------------------------------------------- WHO: headquarters, Geneva
def who_ext(seed=12):
    P = M()
    _slab("who_plaza", (26, 16), P["wet"], fade=(7.0, 11.0))
    PR.slab_block("who_slab", (0, 5.0, 0), 22, 4.0, 14.0, 8, 22, 0.08, seed=seed, mat_key="light", pilotis=3.0)
    box("who_lowblock", (8, 1.2, 1.3), (6, 3, 2.6), P["grey"])
    PR.flagpoles("who_flags", (-4, -2.5, 0), n=8, gap=1.1)
    box("who_pavement", (0, -5.0, 0.06), (26, 3.0, 0.12), P["grey"]); rk.fade_to_void([P["grey"], P["light"]], (0, 2), 8.0, 13.0)
    return dict(entrance=Vector((0, 2.6, 0)), pavement=Vector((0, -5.0, 0.12)))


# ------------------------------------------------------------------------------------------------- UNI: Lyon medical faculty
def faculty(seed=13):
    P = M(); rng = random.Random(seed)
    _slab("uni_court", (22, 18), P["wet"], fade=(6.5, 10.5))
    PR.slab_block("uni_main", (0, 6.0, 0), 18, 4, 9, 3, 12, 0.15, seed=seed, mat_key="light")
    PR.slab_block("uni_wing_l", (-8.5, -0.5, 0), 4, 10, 9, 3, 6, 0.1, seed=seed + 1, mat_key="light", rz=math.radians(-90))
    PR.slab_block("uni_wing_r", (8.5, -0.5, 0), 4, 10, 9, 3, 6, 0.1, seed=seed + 2, mat_key="light", rz=math.radians(90))
    rk.fade_to_void([P["light"]], (0, 1), 9.0, 14.0)
    for i in range(6):
        PR.bare_tree(f"uni_tree{i}", (-5 + i * 2, -1.0 + (i % 2), 0), 6, seed=500 + i)
    box("uni_steps", (0, 3.4, 0.2), (4, 1.2, 0.4), P["grey"])
    return dict(steps=Vector((0, 2.6, 0)), court=Vector((0, -2, 0)))


def diploma_wall():
    P = M()
    box("dw_wall", (0, 0.1, 1.5), (4.0, 0.2, 3.0), P["light"]); rk.fade_to_void([P["light"]], (0, 0), 1.0, 2.2)
    f = PR.frame("dw_frame", (0, -0.01, 1.55), 0.52, 0.4, empty=True)
    cyl("dw_nail", (0, 0, 1.8), (0, -0.03, 1.8), 0.004, P["chrome"], 6)
    return dict(frame=Vector((0, -0.04, 1.55)))


# ------------------------------------------------------------------------------------------------- EXP: explainer slab
def explainer(size=(8, 5)):
    """Dark blue-grey ground and world (never pitch black); cool neutral light; key objects get P['hot']."""
    P = M()
    rk.world_color((0.012, 0.016, 0.022), 1.0)
    box("exp_slab", (0, 0, -0.1), (size[0], size[1], 0.2), P["slab"], bevel=0.05)
    rk.area("exp_key", (0, -1.5, 7), (0, 0, 0), 6, 380, (0.85, 0.9, 1.0))
    rk.area("exp_fill", (-6, -4, 4), (0, 0, 0), 4, 120, (0.6, 0.7, 0.85))
    return dict(center=Vector((0, 0, 0)))


# ------------------------------------------------------------------------------------------------- other reusable sets
def cafe(seed=14):
    P = M()
    _slab("caf_floor", (8, 6), P["wet"], fade=(2.6, 4.2))
    box("caf_bar", (0, 2.0, 0.55), (4.5, 0.6, 1.1), P["wood"], bevel=0.02); box("caf_wall", (0, 2.6, 1.6), (8, 0.2, 3.2), P["grey"])
    rk.fade_to_void([P["grey"]], (0, 0), 3.0, 4.8)
    for i, (x, y) in enumerate(((-1.6, -0.4), (0.4, -0.9), (2.2, -0.2))):
        cyl(f"caf_t{i}", (x, y, 0), (x, y, 0.72), 0.04, P["steel"], 8); cyl(f"caf_tt{i}", (x, y, 0.72), (x, y, 0.75), 0.36, P["light"], 24)
        for s in (-1, 1):
            PR.chair(f"caf_c{i}{s}", (x + s * 0.55, y, 0), math.radians(90 * s))
    for x in (-2.5, -1.2, 0.1, 1.4, 2.7):
        cyl("caf_bottle", (x * 0.6, 2.45, 1.4), (x * 0.6, 2.45, 1.7), 0.035, P["glass"], 10)
    rk.point("caf_pend", (0.4, -0.9, 2.2), 60, (1.0, 0.6, 0.2))
    return dict(table=Vector((0.4, -0.9, 0.75)))


def library(seed=15):
    P = M()
    _slab("lib_floor", (10, 8), P["wood"], fade=(3.0, 5.0))
    for i, x in enumerate((-3.6, -1.8, 1.8, 3.6)):
        PR.shelf(f"lib_shelf{i}", (x, 2.6, 0), 1.6, 2.6, seed=i)
    for y in (0.6, -1.4):
        PR.table(f"lib_table{y}", (0, y, 0), w=2.4, d=1.0)
        for x in (-0.8, 0.8):
            PR.chair(f"lib_ch{x}{y}", (x, y + 0.75, 0), 0.0)
        PR.cone(f"lib_lamp{y}", (0, y, 1.05), 0.12, 0.05, 0.14, P["lamp"], 16)
        rk.point(f"lib_l{y}", (0, y, 1.0), 25, (1.0, 0.65, 0.25))
    box("lib_clock", (0, 2.85, 2.9), (0.4, 0.05, 0.4), P["light"])
    return dict(seat=Vector((-0.8, 1.35, 0)))


def airport_hotel(seed=16):
    P = M()
    _slab("hot_ground", (26, 16), P["asphalt"], fade=(7, 11))
    box("hot_runway", (0, 6.5, 0.01), (30, 3.5, 0.02), P["grey"])
    for i in range(14):
        box("hot_rlight", (-13 + i * 2, 4.6, 0.04), (0.12, 0.12, 0.06), P["lamp"])
    PR.slab_block("hot_block", (-2, -2.0, 0), 12, 3.6, 10.5, 6, 12, 0.08, seed=seed)
    # a jet climbing out above the roof
    jet = []
    jet.append(cyl("jet_fus", (-3, 0, 0), (3, 0, 0), 0.32, P["light"], 16))
    jet.append(box("jet_wing", (0.2, 0, 0), (1.0, 5.2, 0.06), P["light"]))
    jet.append(box("jet_tail", (-2.7, 0, 0.6), (0.7, 0.06, 1.0), P["light"]))
    j = rk.group("jet", jet, (2, 1, 16), math.radians(10)); j.rotation_euler.y = math.radians(-12)
    return dict(window=Vector((-2, -3.8, 5.0)), jet=j)


def courtroom(seed=17):
    P = M()
    _slab("crt_floor", (14, 11), P["wood"], fade=(4.5, 7.0))
    box("crt_bench", (0, 4.0, 0.7), (6.5, 1.0, 1.4), P["wood"], bevel=0.02); box("crt_dais", (0, 4.2, 0.2), (7.5, 2.0, 0.4), P["wood"])
    box("crt_wall", (0, 5.2, 2.4), (14, 0.3, 4.8), P["light"]); rk.fade_to_void([P["light"]], (0, 0), 5, 8)
    box("crt_dock", (-4.6, 0.5, 0.55), (2.2, 1.4, 1.1), P["wood"], bevel=0.02)
    cyl("crt_mic", (-4.6, -0.1, 1.1), (-4.6, -0.25, 1.4), 0.01, P["steel"], 6)
    for r in range(4):
        box(f"crt_pew{r}", (1.5, -1.2 - r * 1.2, 0.25), (8, 0.5, 0.5), P["wood"])
        box(f"crt_pewb{r}", (1.5, -1.45 - r * 1.2, 0.6), (8, 0.08, 0.8), P["wood"])
    for i in range(5):
        PR.chair(f"crt_judge{i}", (-2 + i, 4.5, 0.4), math.pi)
    return dict(dock=Vector((-4.6, 0.6, 0.0)), bench=Vector((0, 4.0, 1.4)))


def prison(seed=18):
    P = M()
    _slab("pri_ground", (20, 14), P["wet"], fade=(6, 9.5))
    box("pri_wall", (0, 3.0, 3.0), (20, 0.8, 6.0), P["grey"]); rk.fade_to_void([P["grey"]], (0, 1), 7, 11)
    box("pri_gate", (0, 2.55, 2.0), (3.2, 0.12, 4.0), P["steel"])
    for x in (-8, 8):
        box("pri_tower", (x, 3.0, 4.5), (1.8, 1.8, 9.0), P["grey"])
        box("pri_tower_win", (x, 2.05, 8.2), (1.2, 0.05, 0.6), P["win"])
    for i in range(30):
        cyl("pri_wire", (-10 + i * 0.68, 3.0, 6.0), (-10 + i * 0.68 + 0.34, 3.0, 6.35), 0.01, P["steel"], 4)
    return dict(gate=Vector((0, 2.3, 0)))


def abbey(seed=19):
    P = M(); rng = random.Random(seed)
    _slab("abb_ground", (24, 18), P["foliage"], fade=(7, 11))
    box("abb_nave", (0, 3.0, 4.0), (5.0, 14.0, 8.0), P["light"], bevel=0.05)
    for s in (-1, 1):
        r = box("abb_roof", (s * 1.3, 3.0, 9.0), (3.4, 14.4, 0.2), P["grey"]); r.rotation_euler.y = math.radians(-s * 40)
    box("abb_tower", (0, -3.6, 7.0), (3.2, 3.2, 14.0), P["light"], bevel=0.05)
    PR.cone("abb_spire", (0, -3.6, 15.5), 2.3, 0.05, 3.0, P["grey"], 4, rot=(0, 0, math.radians(45)))
    for i in range(6):   # cloister arcade
        x = 4.2 + i * 1.0
        box(f"abb_arch{i}", (x, 1.0, 1.4), (0.25, 0.25, 2.8), P["light"])
    box("abb_cloister_roof", (6.7, 1.0, 2.9), (6.2, 1.8, 0.2), P["grey"])
    rk.fade_to_void([P["light"], P["grey"]], (0, 2), 9, 14)
    for i in range(8):
        PR.bare_tree(f"abb_tree{i}", (rng.uniform(-11, 11), rng.uniform(-8, -5), 0), 6, seed=600 + i)
    return dict(cloister=Vector((6.5, 0.0, 0)), door=Vector((0, -5.2, 0)))


SET_BUILDERS = dict(FOR=forest, FTB=country_house, PAR=paris_street, HPM=house_pm, HPI=hallway, CLV=parents_house,
                    WHO=who_ext, UNI=faculty, CAF=cafe, LIB=library, HOT=airport_hotel, CRT=courtroom, PRI=prison, ABB=abbey,
                    EXP=explainer)
