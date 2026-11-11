# Shared layout constants (exec'd by the build/animate scripts). Units: metres, Z up. Room interior floor z=0.
from mathutils import Vector
V = lambda *a: Vector(a)
FPS = 60; END = 1530
BEATS = [(1, 0.0, "A bullet was fired at the house"), (2, 2.3, "tore straight through the wall"),
         (3, 4.5, "Inside, a woman and her fiance"), (4, 6.5, "froze as the stray bullet"),
         (5, 10.1, "her trusty tumbler, full of ice water"), (6, 16.2, "the bullet slammed into the cup"),
         (7, 21.4, "dropped harmlessly to the floor"), (8, 23.6, "saving her life")]
BF = {b: 1 + round(t * FPS) for b, t, _ in BEATS}          # beat start frames: 1,139,271,391,607,973,1285,1417
WALL_OUT, WALL_IN = -0.17, 0.0      # shot wall (house side wall) occupies x in [WALL_OUT, WALL_IN]
ROOM = dict(x0=0.0, x1=6.6, y0=-3.4, y1=3.2, h=2.7)
GROUND_Z = -0.55                    # exterior lawn level
TABLE_C = V(3.4, 0.0, 0.0)          # dining table centre (long axis along X)
CUP_C = V(4.42, -0.234, 0.0)         # tumbler base centre (z filled at build = table top)
CUP_R_IMPACT = 0.047
SHOT_SLOPE = 0.474                   # dy/dx of the shot line (comes in diagonally from the street)
SHOT_Z0 = 1.30                      # bullet height at x=-14
WOMAN_SEAT = V(5.05, 0.0, 0.0)      # chair position (end of table), she faces -X
FIANCE_SEAT = V(4.22, -1.12, 0.0)   # chair position (long side, at her corner), he faces +Y
F_IMPACT = BF[6]
F_WALL = BF[2]
IMPACT_Z = 0.95
TABLE_SY = 0.62                     # table narrowed in Y
HER_CHEST = V(4.90, -0.01, 1.0)
