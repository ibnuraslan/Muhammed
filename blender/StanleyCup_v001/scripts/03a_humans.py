# Part of 03_animate.py: the couple, seated at the table. Slow-motion acting until the bullet drops (f1285), real time after.
import math
from mathutils import Vector, Matrix
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
W_RIG = bpy.data.objects["Woman_rig"]; F_RIG = bpy.data.objects["Fiance_rig"]
RW = make_human_ctrl(W_RIG); RF = make_human_ctrl(F_RIG)
HW = Human(RW); HF = Human(RF)
TOP = sc["table_top"]; SEAT = sc["seat_top"]
def fwd(yaw): return Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((0, -1, 0))
def side(yaw): return Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((1, 0, 0))      # character's left (+X of the rig)
def to_w(base, yaw, lx, ly, lz):
    """character-local offset: lx = to her left, ly = forward, lz = up"""
    return base + side(yaw) * lx + fwd(yaw) * ly + Vector((0, 0, lz))

class Sitter:
    def __init__(self, H, R, seat, yaw, hip_h, knee_fwd):
        self.H, self.R, self.seat, self.yaw = H, R, seat, yaw
        self.hip = Vector((seat.x, seat.y, SEAT + hip_h)) + fwd(yaw) * 0.02
        self.kf = knee_fwd
    def body(self, f, lean=0.0, twist=0.0, sidebend=0.0, head=(0.0, 0.0), dz=0.0, back=0.0):
        p = self.hip + fwd(self.yaw) * (-back) + Vector((0, 0, dz))
        self.H.key_root(f, p, yaw=self.yaw, flex=lean * 0.5, side=sidebend * 0.3)
        self.H.key_spine(f, flex=lean * 0.6, twist=twist, side=sidebend, head=head)
    def feet(self, f, spread=0.0, l_fwd=0.0, r_fwd=0.0, lift_r=0.0):
        for s, sg, fw, lf in (("L", 1, l_fwd, 0.0), ("R", -1, r_fwd, lift_r)):
            ax = self.H.ankle[s].x * 0.85 + sg * spread
            xy = to_w(Vector((self.seat.x, self.seat.y, 0)), self.yaw, ax, self.kf + fw, 0)
            self.H.key_foot(s, f, Vector((xy.x, xy.y)), self.yaw + sg * 6, lf, 0)
    def hand(self, s, f, W, d, n, elbow_out=0.35, elbow_down=0.25):
        sg = 1 if s == "L" else -1
        sh = to_w(self.hip, self.yaw, sg * 0.2, 0.0, 0.45)
        pole = (sh + W) / 2 + side(self.yaw) * sg * elbow_out - fwd(self.yaw) * 0.35 + Vector((0, 0, -elbow_down))
        self.H.key_hand(s, f, W, d, n, pole)
    def face(self, f, lids=0.0, brows=0.0, jaw=0.0, smile=0.0, look=(0.0, 0.0)):
        """lids: +1 wide open, -1 closed; brows: +1 raised; jaw: open (deg); smile 0..1; look: (yaw, pitch) of the eyes in deg"""
        R = self.R
        R.key_rot("orbicularis03.L", f, [("X", -14 * lids)]) if lids >= 0 else R.key_rot("orbicularis03.L", f, [("X", -30 * lids)])
        R.key_rot("orbicularis03.R", f, [("X", -14 * lids)]) if lids >= 0 else R.key_rot("orbicularis03.R", f, [("X", -30 * lids)])
        R.key_rot("orbicularis04.L", f, [("X", 6 * lids)] if lids >= 0 else [("X", 10 * lids)])
        R.key_rot("orbicularis04.R", f, [("X", 6 * lids)] if lids >= 0 else [("X", 10 * lids)])
        for s in "LR":
            R.key_rot("oculi01." + s, f, [("X", -10 * brows)]); R.key_rot("oculi02." + s, f, [("X", -10 * brows)])
            R.key_rot("eye." + s, f, [("X", look[1]), ("Z", look[0])])
            R.key_rot("risorius03." + s, f, [("Z", (12 if s == "L" else -12) * smile)])
        R.key_rot("jaw", f, [("X", jaw)])

ws = Sitter(HW, RW, WOMAN_SEAT, -90.0, 0.085, 0.44)
fs = Sitter(HF, RF, FIANCE_SEAT, 180.0, 0.095, 0.5)
