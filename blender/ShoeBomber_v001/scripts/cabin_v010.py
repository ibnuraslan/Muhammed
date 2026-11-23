# ================================================================== v010 CABIN CHOREOGRAPHY (director's v009 review, Nov 23)
# Exec'd from 03_animate.py (shares its namespace). The bomber sits in the AISLE seat 3C so that every grab, the tackle
# and the pin happen in the aisle (x -0.23..0.22) with no body crossing a seat. Shot plan (source frames):
#   S1 1-95 / S2 97-197  he lights a fuse poking out of the tongue of the sneaker lying on his lap (left hand grips it)
#   S3 199-372           the attendant walks down the aisle (camera retreats ahead of her, >= 1.6 m)
#   S4 373-467           she stops at row 3: palm out ("stop!"), then takes the shoe off his lap
#   S5 468-581           she sets it on empty seat 4D; he lunges into the aisle, PaxB grabs him from behind, PaxA his
#                        left arm; they take him face-down in the aisle
#   S6 582-768           pin + sedation (steward brings the syringe, the attendant injects his upper arm)
#   S7 769-866           restraint: PaxA straps his wrists behind his back, PaxB holds his legs
#   S8 868-1068          PaxB pulls the left shoe off his foot and holds it up to look at it
BX, BY = SX["C"], ROW(3)
PAX_A_X = SX["B"]
SHOE_LAP = V((BX + 0.0, BY + 0.24, 0.685))          # sneaker on his lap: sole-bottom centre (04 parks it here, toe +Y)
FUSE_TIP = SHOE_LAP + V((0.03, -0.03, 0.235))        # fuse out of the tongue, bending toward the aisle (= 04's fuse curve)
SEAT4D = V((0.44, 0.98, 0.47))                       # where the attendant sets the shoe down (empty seat 4D cushion)
PIN_ROOT = V((0.0, BY + 0.75, 0.31))
WRISTS = V((-0.02, BY + 0.50, 0.37))                 # his wrists, strapped behind his back (S7 on)

# ---------------------------------------------------------------- BOMBER
def bomber_seat(f, lean=6, head=(30, 0), twist=0):
    bom.key_root(f, V((BX + 0.02, BY - 0.10, 0.56)), yaw=FWD, flex=4, side=0)
    bom.key_spine(f, flex=lean, twist=twist, side=0, head=head)
    bom.key_foot("L", f, V((BX - 0.11, BY + 0.37)), FWD, 0, 0)
    bom.key_foot("R", f, V((BX + 0.11, BY + 0.36)), FWD, 0, 0)
# head: (pitch down, yaw); he watches the fuse, glances up the aisle at 70 and 300, freezes when caught (395)
for f, lean, hd, tw in ((1, 10, (34, 4), 0), (40, 12, (36, 6), 2), (62, 6, (6, -12), 0), (80, 6, (4, -14), 0), (100, 12, (34, 4), 2),
                        (150, 11, (36, 2), 0), (200, 12, (34, 4), 2), (260, 12, (36, 2), 0), (290, 6, (6, -10), 0), (310, 6, (4, -14), 0),
                        (330, 12, (34, 2), 0), (372, 12, (34, 4), 2), (392, 2, (-6, -30), -6), (430, 0, (-8, -34), -8), (462, 4, (8, -20), -4)):
    bomber_seat(f, lean, hd, tw)
# left hand grips the collar of the shoe on his lap (palm against the outer side, fingers over the top)
GRIP_L = SHOE_LAP + V((-0.075, -0.05, 0.10))
for f in (1, 100, 200, 300, 372, 440, 462):
    hand(bom, "L", f, GRIP_L, (0.55, 0.15, -0.6), (1, 0, 0), pole=(BX - 0.45, BY - 0.15, 0.70), grip=0.75, pose="wrap_grip")
# right hand: strikes the match on the sole edge (14-26), lights (28), brings the flame to the fuse tip and holds it
strike = [(1, V((0.16, -0.08, -0.12))), (12, V((0.13, 0.02, -0.16))), (20, V((0.13, 0.14, -0.15))), (26, V((0.15, 0.10, -0.08))),
          (36, V((0.09, -0.04, -0.07))), (60, V((0.08, -0.05, -0.08))), (90, V((0.09, -0.04, -0.07))), (130, V((0.08, -0.05, -0.08))),
          (170, V((0.09, -0.04, -0.07))), (220, V((0.08, -0.05, -0.08))), (280, V((0.09, -0.04, -0.07))), (340, V((0.08, -0.05, -0.08))),
          (380, V((0.09, -0.04, -0.07))), (400, V((0.14, -0.06, 0.02))), (440, V((0.15, -0.06, 0.03)))]
for f, o in strike:
    hand(bom, "R", f, FUSE_TIP + o, (-0.45, 0.35, 0.75), (0, -1, 0), pole=(BX + 0.55, BY - 0.30, 0.75), grip=0.8, pose="pinch")
# 466: she takes the shoe; his hands follow it a little, then he lunges up into the aisle after it
hand(bom, "L", 470, SHOE_LAP + V((0.02, 0.12, 0.16)), (0.4, 0.6, -0.3), (0, 0, -1), pole=(BX - 0.45, BY - 0.1, 0.8), grip=0.5)
hand(bom, "R", 470, SHOE_LAP + V((0.18, 0.12, 0.20)), (0.3, 0.8, 0.1), (0, 0, -1), pole=(BX + 0.55, BY - 0.2, 0.8), grip=0.5)
bomber_seat(476, 18, (-4, -22), -10)
# 484-500: up out of the seat into the aisle (feet travel in the row-3 legroom, y 0.37-0.45, then into the aisle)
bom.key_root(486, V((BX + 0.12, BY + 0.05, 0.72)), yaw=FWD - 25, flex=30, side=0); bom.key_spine(486, flex=20, twist=-10, head=(-5, -15))
bom.key_foot("L", 486, V((BX - 0.02, BY + 0.40)), FWD - 20, 0, 0); bom.key_foot("R", 486, V((BX + 0.24, BY + 0.40)), FWD - 30, 0, 0)
bom.key_root(496, V((-0.06, BY + 0.18, 0.94)), yaw=FWD - 15, flex=18, side=0); bom.key_spine(496, flex=12, twist=-6, head=(-6, -8))
bom.key_foot("L", 496, V((-0.14, BY + 0.40)), FWD - 10, 0, 0); bom.key_foot("R", 496, V((0.06, BY + 0.30)), FWD - 15, 0, 0)
for f, hr_, hl_ in ((486, (0.02, BY + 0.55, 1.00), (BX + 0.18, BY + 0.50, 0.95)), (496, (0.10, BY + 0.70, 1.15), (-0.10, BY + 0.62, 1.10))):
    hand(bom, "R", f, hr_, (0.2, 1, 0.1), (0, 0, -1), grip=0.5)
    hand(bom, "L", f, hl_, (0, 1, 0.1), (0, 0, -1), grip=0.5)
# 505-540: grabbed from behind (PaxB) and by the left arm (PaxA); struggles upright in the aisle
for f, tw, sd in ((508, 12, 4), (520, -14, -6), (532, 10, 5), (542, -8, -3)):
    bom.key_root(f, V((-0.03 + 0.02 * math.sin(f), BY + 0.20, 0.93)), yaw=FWD - 8 + tw * 0.5, flex=14, side=sd)
    bom.key_spine(f, flex=10, twist=tw, head=(-4, tw * 0.8))
    bom.key_foot("L", f, V((-0.13, BY + 0.34)), FWD - 8, 0, 0); bom.key_foot("R", f, V((0.07, BY + 0.24)), FWD - 8, 0, 0)
for f, rr in ((508, (0.12, BY + 0.62, 1.12)), (520, (0.15, BY + 0.55, 1.20)), (532, (0.10, BY + 0.58, 1.05)), (542, (0.12, BY + 0.55, 1.10))):
    hand(bom, "R", f, rr, (0.2, 1, 0.2), (0, 0, -1), grip=0.6)
for f in (508, 542):
    hand(bom, "L", f, V((-0.18, BY + 0.28, 0.95)), (-0.4, 0.2, -0.8), (0, 0, -1), pole=(-0.6, BY + 0.0, 1.0), grip=0.4)
# 548-582: forced down: knees (556), hands (568), flat on the carpet (582), head toward +Y
bom.key_root(556, V((0.0, BY + 0.36, 0.58)), yaw=FWD, flex=28, side=0); bom.key_spine(556, flex=20, twist=0, head=(-10, 0))
bom.key_foot("L", 556, V((-0.10, BY - 0.12)), FWD, 0.03, -70); bom.key_foot("R", 556, V((0.10, BY - 0.12)), FWD, 0.03, -70)
bom.key_root(568, V((0.0, BY + 0.58, 0.42)), yaw=FWD, flex=62, side=0); bom.key_spine(568, flex=10, twist=0, head=(-20, 10))
bom.key_foot("L", 568, V((-0.10, BY - 0.22)), FWD, 0.03, -75); bom.key_foot("R", 568, V((0.10, BY - 0.22)), FWD, 0.03, -75)
hand(bom, "R", 568, V((0.12, BY + 1.18, 0.10)), (0, 1, -0.3), (0, 0, -1), grip=0.3)
hand(bom, "L", 568, V((-0.14, BY + 1.10, 0.10)), (0, 1, -0.3), (0, 0, -1), grip=0.3)
for f, z, fl in ((582, 0.31, 91), (590, 0.335, 90), (598, 0.31, 91), (654, 0.31, 91), (700, 0.305, 91), (768, 0.305, 91)):
    bom.key_root(f, V((PIN_ROOT.x, PIN_ROOT.y, z)), yaw=FWD, flex=fl, side=0)
    bom.key_spine(f, flex=-2, twist=-5, head=(-6, 34) if f < 700 else (-6, 38))   # face turned sideways (toward +X), not into the carpet
    bom.key_foot("L", f, V((-0.10, BY - 0.25)), FWD, 0.03, -75); bom.key_foot("R", f, V((0.10, BY - 0.27)), FWD, 0.03, -75)
for f in range(600, 721, 12):   # struggles while pinned, then limp once sedated (~720)
    w = 1.0 if f < 690 else max(0.0, (720 - f) / 30)
    bom.key_root(f, V((0.02 * w * math.sin(f), PIN_ROOT.y, 0.31 + 0.015 * w * abs(math.sin(f * 0.7)))), yaw=FWD + 3 * w * math.sin(f * 0.5), flex=91, side=4 * w * math.sin(f * 0.9))
    bom.key_spine(f, flex=-2 + 3 * w * math.sin(f * 0.3), twist=-5 + 6 * w * math.sin(f * 0.6), head=(-6, 34 + 4 * (1 - w)))
for f in range(780, 1069, 30):  # after sedation: still, tiny breathing
    bom.key_root(f, V((0.0, PIN_ROOT.y, 0.305 + 0.004 * math.sin(f * 0.1))), yaw=FWD, flex=91, side=0)
    bom.key_spine(f, flex=-2, twist=-5, head=(-6, 38))
    bom.key_foot("L", f, V((-0.10, BY - 0.25)), FWD, 0.03, -75); bom.key_foot("R", f, V((0.10, BY - 0.27)), FWD, 0.03, -75)
# arms when pinned: right arm forward on the carpet (held by the attendant, injected), left arm twisted behind his back
for f in (582, 654, 720, 768, 1068):
    hand(bom, "R", f, V((0.14, BY + 1.62, 0.30 if f < 720 else 0.28)), (0.05, 0.8, 0.3), (0, 0, -1), pole=(0.55, BY + 1.0, 0.5), grip=0.6 if f < 720 else 0.15)
hand(bom, "L", 582, V((-0.16, BY + 0.58, 0.38)), (0.6, -0.4, 0), (0, 0, 1), pole=(-0.6, BY + 0.9, 0.6), grip=0.3)
for f in (654, 720):
    hand(bom, "L", f, WRISTS + V((-0.05, 0.02, 0.0)), (1, -0.2, 0), (0, 0, 1), pole=(-0.6, BY + 0.9, 0.6), grip=0.3)
# S7: right wrist brought behind his back too, crossed over the left; strapped (04 animates the strap)
hand(bom, "R", 772, V((0.25, BY + 1.0, 0.40)), (-0.3, -0.6, 0), (0, 0, 1), pole=(0.6, BY + 1.0, 0.7), grip=0.2)
for f in (786, 1068):
    hand(bom, "R", f, WRISTS + V((0.05, -0.02, 0.01)), (-1, 0.2, 0), (0, 0, 1), pole=(0.6, BY + 0.9, 0.6), grip=0.2)
    hand(bom, "L", f, WRISTS + V((-0.05, 0.02, 0.0)), (1, -0.2, 0), (0, 0, 1), pole=(-0.6, BY + 0.9, 0.6), grip=0.2)
print("BOMBER_DONE")

# ---------------------------------------------------------------- ATTENDANT
def swing(h, path, f0, f1, facing_y=-1, step=8, amp=0.13, period=36):
    """v010: natural walk arms -- elbows bent ~45 deg, hands close to the hips, opposite-arm swing fore/aft"""
    for f in range(f0, f1 + 1, step):
        p = path(f); ph = math.sin((f - f0) / period * 2 * math.pi)
        for s_, sg in (("L", 1), ("R", -1)):
            side = sg * (1 if facing_y < 0 else -1) * 0.155
            sw = sg * ph * amp
            hand(h, s_, f, V((p.x + side, p.y + facing_y * (0.10 + sw), 0.93 + 0.25 * abs(sw))),
                 (0, facing_y * 0.75, -0.65), (-side, 0, 0),
                 pole=(p.x + side * 2.2, p.y - facing_y * 0.6, 0.95), grip=0.35)
apath = catmull([(170, V((0.0, 7.9, 0))), (230, V((0.0, 5.6, 0))), (300, V((0.0, 3.0, 0))), (318, V((0.0, 2.85, 0)))])
att.walk(apath, lambda f: 0.0, 170, 318, stride=0.62, lift=0.06, lean=8)
TROLLEY = bpy.data.objects["Trolley"]
TROLLEY.location = V((0, 8.55, 0.52)); TROLLEY.keyframe_insert("location", frame=1)
swing(att, apath, 170, 318)
# stops, smells smoke: chin up, looks around, then turns toward row 3
stand(att, 330, apath(318), 0, spine=(-6, 0, 0), head=(-14, 0))
stand(att, 350, apath(318), 0, spine=(-4, 0, 0), head=(-8, -20))
stand(att, 372, V((0.0, 2.8, 0)), -15, spine=(4, -12, 0), head=(6, -20))
for f in (330, 350, 372):
    hand(att, "L", f, V((0.17, 2.85, 0.93)), (0, -0.4, -0.9), (-1, 0, 0), pole=(0.45, 3.4, 0.95), grip=0.3)
    hand(att, "R", f, V((-0.17, 2.82, 0.93)), (0, -0.4, -0.9), (1, 0, 0), pole=(-0.45, 3.4, 0.95), grip=0.3)
# S4: walks to row 3 and stops in the aisle 0.6 m ahead of him; palm out at him ("stop!"), then takes the shoe
apath2 = catmull([(376, V((0.0, 2.8, 0))), (400, V((0.04, 1.65, 0))), (420, V((0.06, 0.86, 0)))])
att.walk(apath2, lambda f: -45.0 * smooth((f - 404) / 16.0), 376, 420, stride=0.6, lift=0.06, lean=10)
swing(att, apath2, 376, 412, step=8)
AT = V((0.06, 0.86, 0))
stand(att, 428, AT, -45, spine=(6, -6, 0), head=(10, -10), stance=0.12)
stand(att, 452, AT, -45, spine=(10, -8, 0), head=(12, -12), stance=0.12)
hand(att, "L", 428, V((0.22, 0.88, 0.92)), (0, -0.4, -0.9), (-1, 0, 0), pole=(0.5, 1.3, 0.95), grip=0.3)
for f in (436, 450):   # right arm straight out toward him, palm facing him: STOP
    hand(att, "R", f, V((-0.22, 0.42, 1.22)), (-0.15, -0.2, 1), (-0.6, -0.8, 0), pole=(0.2, 0.9, 0.85), grip=0.0, pose="relaxed")
hand(att, "R", 428, V((-0.05, 0.68, 1.10)), (-0.3, -0.5, 0.6), (-0.5, -0.6, 0), pole=(0.2, 0.9, 0.85), grip=0.1)
hand(att, "L", 450, V((0.22, 0.88, 0.94)), (0, -0.4, -0.9), (-1, 0, 0), pole=(0.5, 1.3, 0.95), grip=0.3)
# 456-466: bends and takes the shoe off his lap with both hands; 466-490: turns and sets it on seat 4D
stand(att, 462, V((0.04, 0.74, 0)), -60, flex=6, spine=(30, -10, 0), head=(20, -5), crouch=0.08, stance=0.12)
hand(att, "R", 464, SHOE_LAP + V((0.10, 0.10, 0.12)), (-0.6, 0.0, -0.7), (-1, 0, 0), pole=(0.3, 0.9, 1.0), grip=0.75, pose="wrap_grip")
hand(att, "L", 464, SHOE_LAP + V((0.05, 0.24, 0.10)), (-0.6, -0.3, -0.6), (0, -1, 0), pole=(0.5, 1.2, 1.0), grip=0.6)
stand(att, 476, V((0.06, 0.82, 0)), 30, flex=4, spine=(14, 10, 0), head=(5, 15), stance=0.12)
hand(att, "R", 476, V((0.20, 0.72, 1.00)), (0.5, 0.5, 0), (-0.3, 0, -1), pole=(-0.1, 0.9, 1.1), grip=0.75, pose="wrap_grip")
hand(att, "L", 476, V((0.28, 0.86, 1.00)), (0.3, -0.3, 0), (0, -1, 0), pole=(0.6, 1.2, 1.0), grip=0.6)
stand(att, 488, V((0.10, 0.86, 0)), 80, flex=6, spine=(36, 0, 0), head=(25, 0), crouch=0.1, stance=0.12)
hand(att, "R", 488, SEAT4D + V((-0.02, -0.10, 0.12)), (0.6, 0.2, -0.7), (0, 0, -1), pole=(0.0, 0.7, 1.0), grip=0.75, pose="wrap_grip")
hand(att, "L", 488, SEAT4D + V((-0.04, 0.12, 0.12)), (0.6, -0.2, -0.7), (0, 0, -1), pole=(0.3, 1.4, 1.0), grip=0.5)
# 496-540: turns back to him and pushes him off with both hands on his chest, braced
stand(att, 500, V((0.06, 0.95, 0)), -10, flex=4, spine=(14, 0, 0), head=(8, 0), crouch=0.05, stance=0.2)
stand(att, 540, V((0.06, 1.02, 0)), -5, flex=4, spine=(16, 4, 0), head=(10, 0), crouch=0.08, stance=0.22)
for f, dy in ((506, 0.0), (520, 0.03), (538, 0.0)):
    hand(att, "R", f, V((-0.08, 0.66 + dy, 1.12)), (0, -1, 0.2), (0, -1, 0), pole=(-0.4, 1.2, 0.9), grip=0.2)
    hand(att, "L", f, V((0.12, 0.66 + dy, 1.12)), (0, -1, 0.2), (0, -1, 0), pole=(0.5, 1.2, 0.9), grip=0.2)
# 548-600: steps back as he goes down, then kneels at his head (y 2.0) facing -Y, holding his outstretched right arm
apath3 = catmull([(546, V((0.06, 1.05, 0))), (568, V((0.02, 1.60, 0))), (582, V((-0.02, 2.05, 0)))])
att.walk(apath3, lambda f: 0.0, 546, 582, stride=0.4, lift=0.05, lean=-4)
swing(att, apath3, 548, 578, facing_y=-1, step=8, amp=0.06, period=24)
stand(att, 594, V((-0.02, 2.08, 0)), 0, spine=(28, 0, 0), head=(18, 0), crouch=0.35)
AK = V((-0.02, BY + 2.08, 0.47))
for f, fl, hd in ((610, 55, (12, 8)), (654, 50, (10, 8)), (768, 46, (8, 10)), (900, 30, (-4, 12)), (1068, 28, (-4, 15))):
    att.key_root(f, AK, yaw=0, flex=14)
    att.key_spine(f, flex=fl, twist=0, head=hd)
    att.key_foot("L", f, V((AK.x - 0.12, AK.y + 0.40)), 0, 0.02, -65); att.key_foot("R", f, V((AK.x + 0.12, AK.y + 0.42)), 0, 0.02, -65)
for f in (610, 654, 1068):
    hand(att, "L", f, V((0.12, BY + 1.72, 0.40)), (0, -1, -0.4), (0, 0, -1), pole=(-0.3, BY + 2.4, 0.8), grip=0.55)   # his right wrist
# her right hand: on his forearm, takes the syringe from the steward (650), injects his upper arm (668-715), sets it down
hand(att, "R", 610, V((0.16, BY + 1.50, 0.42)), (0, -1, -0.4), (0, 0, -1), pole=(0.5, BY + 2.4, 0.8), grip=0.5)
hand(att, "R", 640, V((0.18, BY + 1.70, 0.62)), (0.2, 0.4, 0.8), (0, 1, 0), pole=(0.5, BY + 2.4, 0.8), grip=0.5)
hand(att, "R", 650, V((0.16, BY + 1.96, 0.88)), (0.1, 0.5, 0.8), (0, 1, 0), pole=(0.5, BY + 2.4, 0.8), grip=0.6)
print("ATTENDANT_DONE")

# ---------------------------------------------------------------- PAX A (asleep beside him in 3B; grabs his arm, kneels on 3C, straps his wrists)
for f in range(1, 470, 20):
    sit(pa, f, PAX_A_X, BY, flex=4, spine=(-2, 0, 6), head=(18 + 6 * math.sin(f * 0.05), 25 + 8 * math.sin(f * 0.03)))
for s in "LR":
    for f in (1, 440):
        rest_arm(pa, s, f, V((PAX_A_X, BY, 0.56)), grip=0.25)
sit(pa, 476, PAX_A_X, BY, flex=4, spine=(6, 25, 0), head=(0, 40))      # wakes, looks at the commotion
# 490-545: half up in his row, grabs the bomber's left arm and pulls it back
stand(pa, 500, V((PAX_A_X + 0.10, BY + 0.30, 0)), FWD + 50, flex=8, spine=(20, 15, 0), head=(5, 10), crouch=0.30)
for f in (508, 524, 542):
    ev(f); el = wpos(bom, "lowerarm01.L", f)
    hand(pa, "R", f, el + V((-0.02, 0.0, 0.04)), (1, 0.2, -0.2), (0, 0, -1), pole=(PAX_A_X + 0.2, BY - 0.2, 1.0), grip=0.75, pose="wrap_grip")
    hand(pa, "L", f, el + V((-0.10, -0.08, 0.02)), (1, 0.0, -0.2), (0, 0, -1), pole=(PAX_A_X, BY - 0.3, 0.9), grip=0.75, pose="wrap_grip")
stand(pa, 542, V((PAX_A_X + 0.20, BY + 0.32, 0)), FWD + 60, flex=10, spine=(26, 10, 0), head=(10, 0), crouch=0.32)
# 560-1068: kneels on seat 3C (cushion z ~0.47) facing the aisle (+X), pinning/strapping his wrists behind his back
KA = V((BX + 0.02, BY + 0.10, 0.78))
for f, fl, hd in ((578, 52, (20, 0)), (654, 48, (22, 0)), (700, 45, (-8, 0)), (768, 50, (24, 0)), (866, 50, (24, 0)), (868, 8, (5, 10)), (900, 6, (5, 10)), (1068, 6, (5, 15))):
    pa.key_root(f, KA, yaw=90, flex=8)
    pa.key_spine(f, flex=fl, twist=10, head=hd)
    pa.key_foot("L", f, V((KA.x - 0.30, KA.y + 0.08)), 90, 0.45, -70); pa.key_foot("R", f, V((KA.x - 0.30, KA.y - 0.14)), 90, 0.45, -70)
for f in (580, 654, 768):
    hand(pa, "R", f, WRISTS + V((0.02, -0.04, 0.05)), (0.3, 0.3, -0.9), (0, 0, -1), pole=(BX, BY - 0.3, 1.0), grip=0.7, pose="wrap_grip")
    hand(pa, "L", f, V((-0.14, BY + 0.72, 0.40)), (0.4, 0.6, -0.7), (0, 0, -1), pole=(BX - 0.1, BY + 0.6, 1.0), grip=0.4)
# S7 (770-860): wraps the strap round his wrists: right hand holds the end, left hand loops it round twice, then pulls it tight
for f, o in ((776, V((0.0, -0.10, 0.10))), (790, V((-0.10, 0.05, -0.02))), (802, V((0.08, 0.06, 0.08))), (814, V((-0.10, -0.05, -0.02))),
             (826, V((0.08, -0.04, 0.09))), (840, V((-0.06, 0.10, 0.10))), (852, V((-0.12, 0.16, 0.18))), (866, V((-0.10, 0.12, 0.16)))):
    hand(pa, "L", f, WRISTS + o, (0.2, 0.3, -0.9), (0, 0, -1), pole=(BX - 0.1, BY + 0.6, 1.0), grip=0.7, pose="pinch")
for f, o in ((776, V((0.03, -0.12, 0.06))), (852, V((0.04, -0.18, 0.12))), (866, V((0.04, -0.16, 0.10)))):
    hand(pa, "R", f, WRISTS + o, (0.3, 0.3, -0.9), (0, 0, -1), pole=(BX, BY - 0.3, 1.0), grip=0.75, pose="wrap_grip")
for f in (868, 1068):   # done: kneels up on the seat (head clear of the aisle cameras), hands on his thighs
    hand(pa, "R", f, V((BX + 0.12, BY + 0.20, 0.74)), (0.6, 0.3, -0.7), (0, 0, -1), grip=0.3)
    hand(pa, "L", f, V((BX + 0.10, BY + 0.00, 0.74)), (0.6, -0.1, -0.7), (0, 0, -1), grip=0.3)

# ---------------------------------------------------------------- PAX B (2C behind; grabs him from behind, holds his legs, checks the shoes)
for f in range(1, 480, 20):
    sit(pb, f, SX["C"], ROW(2), spine=(8, 0, 0), head=(20 + 3 * math.sin(f * 0.04), -5))
for s in "LR":
    for f in (1, 440):
        rest_arm(pb, s, f, V((SX["C"], ROW(2), 0.56)), fwd=0.38, z=0.2, grip=0.6)
sit(pb, 470, SX["C"], ROW(2), spine=(2, -10, 0), head=(-8, -10))      # looks up at the commotion
stand(pb, 488, V((-0.20, ROW(2) + 0.42, 0)), FWD - 60, spine=(20, 0, 0), head=(5, 0), crouch=0.3)
pbo = catmull([(490, V((-0.18, ROW(2) + 0.40, 0))), (504, V((0.0, BY - 0.34, 0)))])
pb.walk(pbo, lambda f: FWD, 490, 504, stride=0.35, lift=0.05, lean=10)
for f in (508, 524, 542):   # bear hug from behind: arms round his chest
    stand(pb, f, V((0.0, BY - 0.30, 0)), FWD, flex=4, spine=(14, 0, 0), head=(5, 0), crouch=0.05, stance=0.2)
    ev(f); ch = wpos(bom, "spine03", f)
    hand(pb, "R", f, ch + V((0.08, 0.10, 0.02)), (-1, 0.3, 0), (0, 1, 0), pole=(0.6, BY - 0.6, 1.0), grip=0.6)
    hand(pb, "L", f, ch + V((-0.12, 0.08, -0.02)), (1, 0.3, 0), (0, 1, 0), pole=(-0.6, BY - 0.6, 1.0), grip=0.6)
# goes down with him: kneels astride his legs at y -0.45, hands pressing on his lower back / thighs
KB = V((0.0, BY - 0.56, 0.55))
for f, fl, hd in ((566, 40, (10, 0)), (582, 45, (12, 0)), (654, 42, (15, 0)), (768, 45, (20, 0)), (856, 45, (18, 0))):
    pb.key_root(f, KB, yaw=FWD, flex=10)
    pb.key_spine(f, flex=fl, twist=0, head=hd)
    pb.key_foot("L", f, V((KB.x - 0.14, KB.y - 0.42)), FWD, 0.02, -65); pb.key_foot("R", f, V((KB.x + 0.14, KB.y - 0.42)), FWD, 0.02, -65)
    hand(pb, "L", f, V((-0.10, BY + 0.10, 0.42)), (0, 1, -0.5), (0, 0, -1), grip=0.3)
    hand(pb, "R", f, V((0.10, BY + 0.10, 0.42)), (0, 1, -0.5), (0, 0, -1), grip=0.3)
# S8 (868-1068): kneels behind his feet; pulls the LEFT sneaker off (874-900), lifts it and holds it up to look at it
KN = V((0.04, BY - 0.86, 0.55))
for f, fl, hd in ((866, 34, (25, 0)), (900, 30, (20, 0)), (930, 8, (10, 0)), (960, 4, (6, -4)), (1000, 2, (2, 6)), (1030, 4, (-4, -10)), (1068, 4, (-2, -12))):
    pb.key_root(f, KN, yaw=FWD, flex=8 if f < 930 else 2)
    pb.key_spine(f, flex=fl, twist=0, head=hd)
    pb.key_foot("L", f, V((KN.x - 0.14, KN.y - 0.40)), FWD, 0.02, -65); pb.key_foot("R", f, V((KN.x + 0.14, KN.y - 0.40)), FWD, 0.02, -65)
ev(874); hl = wpos(bom, "foot.L", 874)
hand(pb, "L", 868, hl + V((-0.07, -0.10, 0.10)), (0.3, 1, -0.4), (1, 0, 0), grip=0.4)
hand(pb, "R", 868, hl + V((0.07, -0.10, 0.10)), (-0.3, 1, -0.4), (-1, 0, 0), grip=0.4)
hand(pb, "L", 876, hl + V((-0.06, -0.12, 0.08)), (0.3, 1, -0.4), (1, 0, 0), grip=0.75, pose="wrap_grip")      # grips heel + collar
hand(pb, "R", 876, hl + V((0.06, -0.06, 0.12)), (-0.3, 1, -0.6), (-1, 0, 0), grip=0.75, pose="wrap_grip")
hand(pb, "L", 896, hl + V((-0.06, -0.34, 0.12)), (0.3, 1, -0.2), (1, 0, 0), grip=0.75, pose="wrap_grip")      # pulled off backward
hand(pb, "R", 896, hl + V((0.06, -0.28, 0.16)), (-0.3, 1, -0.4), (-1, 0, 0), grip=0.75, pose="wrap_grip")
SH_UP = V((KN.x + 0.10, KN.y + 0.36, 0.98))      # where he holds it up (sole toward +Y, the camera)
for f, o, tw in ((930, V((0, -0.02, -0.06)), 0), (960, V((0, 0, 0)), 0), (1000, V((0.03, 0.02, 0.02)), 1), (1030, V((-0.02, 0.0, 0.0)), -1), (1068, V((0.0, 0.0, 0.01)), 0)):
    hand(pb, "R", f, SH_UP + o + V((0.09, -0.02, -0.08)), (-0.5, 0.2, 0.8), (-1, 0, 0.2 * tw), pole=(0.6, KN.y, 0.8), grip=0.75, pose="wrap_grip")
    hand(pb, "L", f, SH_UP + o + V((-0.07, -0.03, 0.09)), (0.5, 0.1, 0.7), (1, 0, 0.2 * tw), pole=(-0.6, KN.y, 0.8), grip=0.6)

# ---------------------------------------------------------------- STEWARD (forward galley; brings the syringe at 600-650, stays to watch)
for f in range(1, 600, 40):
    stand(stw, f, V((0.05, 8.0, 0)), 0, spine=(5, 0, 0), head=(5, 10 * math.sin(f * 0.02)))
    for s_, sg in (("L", 1), ("R", -1)):
        hand(stw, s_, f, V((0.05 + sg * 0.17, 8.0, 0.92)), (0, -0.4, -0.9), (-sg, 0, 0), pole=(0.05 + sg * 0.5, 8.6, 0.95), grip=0.3)
spath = catmull([(600, V((0.05, 8.0, 0))), (622, V((0.04, 5.2, 0))), (640, V((0.02, 2.75, 0)))])
stw.walk(spath, lambda f: 0.0, 600, 640, stride=0.85, lift=0.09, lean=12, bob=0.03)
swing(stw, spath, 600, 636, step=6, amp=0.15, period=24)
SS = V((0.02, BY + 2.82, 0))
for f, sp, hd in ((648, (34, 0, 0), (25, 0)), (660, (20, 0, 0), (20, 0)), (700, (18, 0, 0), (22, 0)), (768, (16, 0, 0), (18, 0)), (900, (12, 0, 0), (15, 5)), (1068, (12, 0, 0), (15, 8))):
    stand(stw, f, SS, 0, spine=sp, head=hd, crouch=0.10, stance=0.14)
# right hand: holds the syringe (04) and passes it down to the attendant at 650; then both hands on his knees, watching
hand(stw, "R", 640, V((-0.12, BY + 2.62, 1.10)), (0, -0.6, 0.6), (1, 0, 0), pole=(-0.5, BY + 3.1, 1.0), grip=0.6)
hand(stw, "R", 650, V((0.12, BY + 2.18, 0.94)), (0, -0.8, 0.3), (1, 0, 0), pole=(-0.4, BY + 3.0, 1.0), grip=0.6)
hand(stw, "L", 640, V((0.20, BY + 2.66, 0.95)), (0, -0.4, -0.9), (-1, 0, 0), pole=(0.5, BY + 3.2, 0.95), grip=0.3)
for f in (662, 768, 1068):
    hand(stw, "R", f, V((-0.10, BY + 2.52, 0.66)), (0, -0.3, -0.9), (0, -1, 0), pole=(-0.5, BY + 3.0, 1.0), grip=0.4)
    hand(stw, "L", f, V((0.14, BY + 2.52, 0.66)), (0, -0.3, -0.9), (0, -1, 0), pole=(0.5, BY + 3.0, 1.0), grip=0.4)
# attendant injects (her right hand at his upper arm), then sets the syringe down on the carpet
ev(690); UA = wpos(bom, "upperarm02.R", 690) + V((0.0, 0.0, 0.05))
for f, dz in ((664, 0.22), (676, 0.14), (690, 0.07), (712, 0.07), (726, 0.20), (744, 0.10), (768, 0.10)):
    hand(att, "R", f, UA + V((0.04, 0.10, dz + 0.10)), (-0.2, -0.4, -0.85), (0, 1, 0), pole=(0.55, BY + 2.4, 0.9), grip=0.6)
for f in (900, 1068):
    hand(att, "R", f, V((0.16, BY + 1.58, 0.40)), (0, -1, -0.4), (0, 0, -1), pole=(0.5, BY + 2.4, 0.8), grip=0.5)
