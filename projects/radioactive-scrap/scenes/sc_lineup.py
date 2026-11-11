from mathutils import Vector
from kit import *
from rs_kit import *
from rs_env import sky
OUT = ["wool_brown", "wool_grey", "parka_green", "navy", "camel", "overall_white", "overall_orange", "doctor", "police", "woman_coat"]
def build(variant=None):
    sky("afternoon")
    box("Ground", (0, 0, -0.05), (60, 60, 0.1), noisy("G", (0.3, 0.27, 0.24)))
    for k, o in enumerate(OUT):
        g = 0.0 if o == "woman_coat" else 1.0
        h = person(f"P{k}", g, 35 + (k * 7) % 30, o, "bob02" if g < 0.5 else ["short02", "short03", "short04"][k % 3],
                   hat=["knit", None, "flat", None][k % 4], hat_col=[(0.3, 0.06, 0.05), None, (0.25, 0.2, 0.15), None][k % 4] or (0.2, 0.2, 0.2),
                   moustache=(k % 2 == 0), dosimeter=o.startswith("overall"))
        stand_pose(h, crossed=(k == 3), hands_pockets=(k == 1)); place(h, (-6.75 + k * 1.5, 0, 0), 0.0)
    return {}
MOVES = {"look": dict(kind="plate", cam=lambda c, t: ((0, -9, 1.3), (0, 0, 1.1), 40))}
