# Story clock and story-world paths (exec'd by 04_anim.py and 05_camera_fx.py).
# Film frame f (1..2130) -> film seconds t = (f-1)/60 -> story seconds SIG(t).
# Beats 1-2 show the climax (story 19-25.9), beat 3 rewinds to the morning (0.5), 4-6 play it (slow motion on the throw),
# beat 7 fast-forwards back to the corner, 8-9 are the shots.
import math
from mathutils import Vector
FPS = 60
def t_of(f): return (f - 1) / FPS
def f_of(t): return 1 + round(t * FPS)

def _pchip(xs, ys):
    n = len(xs); h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    dl = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if dl[i - 1] * dl[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i])
    m[0] = dl[0]; m[-1] = dl[-1]
    def f(x):
        if x <= xs[0]: return ys[0] + m[0] * (x - xs[0])
        if x >= xs[-1]: return ys[-1] + m[-1] * (x - xs[-1])
        lo, hi = 0, n - 2
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if xs[mid] <= x: lo = mid
            else: hi = mid - 1
        i = lo; t = (x - xs[i]) / h[i]
        return ((1 + 2 * t) * (1 - t) ** 2 * ys[i] + t * (1 - t) ** 2 * h[i] * m[i]
                + t * t * (3 - 2 * t) * ys[i + 1] + t * t * (t - 1) * h[i] * m[i + 1])
    return f

SIG_KEYS = [(0.0, 19.0), (6.9, 25.9), (7.5, 24.6), (9.5, 1.7), (10.1, 0.5), (12.4, 2.8), (12.8, 3.15),
            (15.0, 4.25), (15.5, 4.7), (18.5, 7.7), (19.1, 8.6), (20.0, 19.6), (22.4, 23.0), (24.8, 25.75), (26.0, 26.95), (35.6, 36.5)]
SIG = _pchip([k[0] for k in SIG_KEYS], [k[1] for k in SIG_KEYS])
def sig_f(f): return SIG(t_of(f))

# ---------------------------------------------------------------- car path (ground xy), heading 0 = facing -Y
Y_LANE = 1.5; X_START = 95.0; TURN_C = Vector((5.8, 6.5)); TURN_R = 5.0; X_SIDE = TURN_C.x - TURN_R
L_STRAIGHT = X_START - TURN_C.x; L_ARC = math.pi / 2 * TURN_R
def car_xy(d):
    """position and heading (radians) at distance d along the parade route"""
    if d <= L_STRAIGHT:
        return Vector((X_START - d, Y_LANE)), -math.pi / 2
    if d <= L_STRAIGHT + L_ARC:
        a = (d - L_STRAIGHT) / TURN_R          # 0..pi/2
        p = TURN_C + Vector((-math.sin(a), -math.cos(a))) * TURN_R
        return p, -math.pi / 2 - a
    return Vector((X_SIDE, TURN_C.y + (d - L_STRAIGHT - L_ARC))), -math.pi
L_TO_SIDE = L_STRAIGHT + L_ARC
D1_KEYS = [(-3.0, -12.0), (0.0, 0.0), (5.0, 20.0), (5.6, 23.0), (7.0, 33.5), (9.0, 52.0), (17.5, 82.0), (19.0, 86.5), (20.3, 89.8),
           (21.3, 93.6), (22.0, 97.0), (22.8, 101.0), (23.4, 102.6), (24.0, 102.45), (24.8, 101.9), (25.6, 101.55), (26.2, 101.5), (40.0, 101.5)]
D1 = _pchip([k[0] for k in D1_KEYS], [k[1] for k in D1_KEYS])
CAR2_GAP = 9.0; BLAST_SIG = 5.0
def d2(s):
    return D1(min(s, BLAST_SIG)) - CAR2_GAP
def car1(s): return car_xy(D1(s))
def car2(s): return car_xy(d2(s))

# ---------------------------------------------------------------- bomb: thrown, bounces off car1's folded roof, rolls under car2
BOMBER = Vector((82.4, 6.7))
REL_S, HIT_S, LAND_S, ROLL_S = 3.2, 3.72, 4.1, 4.85
ROOF_LOCAL = Vector((0.0, 1.18, 1.52))
def roof_world(s):
    p, h = car1(s); c, sn = math.cos(h), math.sin(h)
    return Vector((p.x + c * ROOF_LOCAL.x - sn * ROOF_LOCAL.y, p.y + sn * ROOF_LOCAL.x + c * ROOF_LOCAL.y, ROOF_LOCAL.z))
REL_P = Vector((82.25, 6.35, 1.95)); HIT_P = roof_world(HIT_S)
LAND_P = Vector((HIT_P.x + 1.8, 1.05, 0.055))
def _blast_xy():
    p, h = car2(BLAST_SIG); return Vector((p.x - 0.4, p.y - 0.1, 0.055))
BLAST_P = _blast_xy()
def ballistic(p0, p1, T, s):
    g = 9.81; v = (p1 - p0) / T + Vector((0, 0, 0.5 * g * T))
    return p0 + v * s - Vector((0, 0, 0.5 * g * s * s))
def bomb_pos(s):
    if s <= REL_S: return None
    if s <= HIT_S: return ballistic(REL_P, HIT_P, HIT_S - REL_S, s - REL_S)
    if s <= LAND_S: return ballistic(HIT_P, LAND_P, LAND_S - HIT_S, s - HIT_S)
    if s <= ROLL_S:
        u = (s - LAND_S) / (ROLL_S - LAND_S); u = 1 - (1 - u) ** 2
        return LAND_P.lerp(BLAST_P, u)
    return BLAST_P.copy()

# ---------------------------------------------------------------- corner
GUNMAN0 = Vector((3.5, 11.7)); GUNMAN1 = Vector((2.78, 10.7))
STEP_S = (23.0, 24.0); DRAW_S = (24.3, 25.1); AIM_S = (25.0, 25.8); SHOT_S = (26.0, 26.6)
