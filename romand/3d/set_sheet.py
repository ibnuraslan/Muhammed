"""Render one wide establishing frame per reusable set (review sheet).
    SET=FOR OUT=... blender -b --python set_sheet.py"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rk, rsets as ST, rprops as PR
from mathutils import Vector
E = os.environ.get
code = E("SET", "FOR")
sc = rk.setup(res=(960, 540), spp=int(E("SPP", "8")))
CAM = {  # target, azimuth, elevation, distance, lens
    "FOR": ((0, 0.5, 0.5), -115, 48, 19, 35), "FTB": ((0, 1, 2), -110, 30, 22, 35), "PAR": ((0, 2, 2), -115, 30, 19, 35),
    "HPM": ((0, 0, 1.5), -120, 38, 19, 35), "HPI": ((-0.6, 0.8, 0.7), -60, 42, 6.0, 30), "CLV": ((0, 1, 1.5), -115, 35, 18, 35),
    "WHO": ((0, 2, 4), -110, 30, 30, 35), "UNI": ((0, 1, 3), -110, 38, 26, 35), "CAF": ((0, 0.4, 0.8), -120, 40, 8.5, 32),
    "LIB": ((0, 0.8, 0.9), -115, 42, 10, 32), "HOT": ((-1, 0, 4), -120, 32, 26, 35), "CRT": ((0, 1, 1), -125, 42, 15, 32),
    "PRI": ((0, 2, 3), -110, 28, 22, 35), "ABB": ((2, 0, 5), -135, 30, 40, 35), "EXP": ((0, 0, 0), -90, 89, 7, 35),
}
kw = {}
if code == "FOR":
    kw = dict(car_kw=dict(boot=0.0, lights=True))
if code == "HPM":
    kw = dict(lit=(1,), door_lit=False)
A = ST.SET_BUILDERS[code](**kw)
figs = []
if code == "FOR":
    pass
elif code == "CAF":
    rk.person("caf_a", (0.4 - 0.55, -0.9, 0), -90, "sit_table", "man", seed=1)
    rk.person("caf_b", (0.4 + 0.55, -0.9, 0), 90, "sit_table", "man", seed=2)
elif code == "LIB":
    rk.person("lib_r", (-0.8, 1.35, 0), 180, "sit_table", "man", seed=3)
elif code == "UNI":
    for i in range(5):
        rk.person(f"uni_s{i}", (-3 + i * 1.6, -2 + (i % 2) * 1.2, 0), [20, -160, 40, 200, 10][i], "walk", "man" if i % 2 else "woman", seed=i)
elif code == "CRT":
    rk.person("crt_acc", (-4.6, 0.75, 0), 180, "stand_bow", "man", seed=4)
elif code == "WHO":
    rk.person("who_w", (-2, -5, 0.12), -90, "walk_carry", "man", seed=5)
t, az, el, d, lens = CAM[code]
rk.look(center=t, extent=max(6.0, d * 0.6), fill=float(E("FILL", "120")) * (d / 12) ** 2, moon=float(E("MOON", "150")) * (d / 12) ** 2,
        fig_target=None)
if code == "EXP":
    rk.pawn("p0", (-1, 0, 0)); rk.pawn("p1", (1, 0, 0), hot=True)
rk.orbit_cam(t, az, el, d, lens=lens)
rk.grade(expo=-2.6)
out = E("OUT", f"/tmp/set_{code}.png")
rk.render_to_luma(out) if code != "EXP" else rk.render(out)
