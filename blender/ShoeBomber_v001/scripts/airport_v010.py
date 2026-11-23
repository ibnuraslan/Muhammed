# ================================================================== v010 AIRPORT (director 13-15). Exec'd from 03_animate.py.
# Every sneaker is carried by its collar in a real grip (hand over the collar, fingers round it), lifted over the tray rim
# and set flat on the tray floor; 04 parents each shoe to the hand, then to the tray (which rides the belt from 1506).
#   A1 1393-1459  the traveller sets his pair in Tray_1
#   A2 1461-1532  the payoff: two passengers set theirs in Tray_2 / Tray_3, then step back
#   A3 1534-1640  trays roll into the X-ray; the traveller (socks) watches, then walks after them
#   A4 1642-1727  he walks toward the lens, stops, looks down at his socks, shrugs, looks up
from mathutils import Matrix as _Mx
for o in bpy.data.objects:      # v006e: conveyor models turned to run along the lane
    if o.name.startswith("Conveyor_") and o.parent is None:
        loc = o.matrix_world.translation.copy()
        o.matrix_world = _Mx.Translation(loc) @ _Mx.Rotation(math.radians(90), 4, 'Z') @ _Mx.Translation(-loc) @ o.matrix_world
bpy.context.view_layer.update()
TRAY_FLOOR = 0.762
GRIP_OFS = V((0.0, 0.09, -0.24))          # shoe origin (sole centre, toe +Y) relative to the wrist holding its collar
SHOE_SPOTS = {"Tray_1": (AX + V((-0.96, 0.0, TRAY_FLOOR)), AX + V((-0.74, 0.0, TRAY_FLOOR))),
              "Tray_2": (AX + V((-0.21, 0.0, TRAY_FLOOR)), AX + V((0.01, 0.0, TRAY_FLOOR))),
              "Tray_3": (AX + V((0.54, 0.0, TRAY_FLOOR)), AX + V((0.76, 0.0, TRAY_FLOOR)))}
CARRIERS = ((trav, AX + V((-1.2, -0.75, 0)), "Tray_1", 1408, 1430, 1440),      # (human, stand spot, tray, lift, down, release)
            (HS["AirPaxA"], AX + V((-0.10, -0.80, 0)), "Tray_2", 1462, 1478, 1486),
            (HS["AirPaxB"], AX + V((0.65, -0.82, 0)), "Tray_3", 1474, 1492, 1500))
PLACE = {}
def carry_hand(h, s, f, W):
    sg = 1 if s == "L" else -1          # left hand palm faces +X (the shoe's outer side), right hand palm faces -X
    hand(h, s, f, W, (0, 0.15, -1), (sg, 0, 0), pole=(W.x - sg * 0.45, W.y - 0.45, W.z + 0.1), grip=0.75, pose="wrap_grip")
for h, P0, tray, f_lift, f_down, f_rel in CARRIERS:
    spotL, spotR = SHOE_SPOTS[tray]
    PLACE[h.name] = (tray, f_rel)
    for f in (1, 1381):
        stand(h, f, P0 + V((0, -0.02, 0)), FWD, spine=(4, 0, 0), head=(14, 0))
    # body: stands, leans in over the belt to set the shoes down, straightens
    for f, sp, hd, cr in ((1393, 4, (14, 0), 0.0), (f_lift - 6, 6, (18, 0), 0.0), (f_lift + 6, 14, (26, 0), 0.02), (f_down, 26, (32, 0), 0.06),
                          (f_rel, 26, (32, 0), 0.06), (f_rel + 14, 8, (14, 0), 0.0)):
        stand(h, f, P0, FWD, spine=(sp, 0, 0), head=hd, crouch=cr, stance=0.06)
    # hands: carried at the sides (shoes hanging by their collars) -> lifted over the rim -> lowered flat -> let go -> up
    for s, spot, sg in (("L", spotL, -1), ("R", spotR, 1)):
        side = V((P0.x + sg * 0.20, P0.y + 0.10, 0.88))
        above = spot - GRIP_OFS + V((0, 0, 0.14))
        place = spot - GRIP_OFS
        for f, W in ((1, side), (1393, side), (f_lift - 6, side), (f_lift + 6, (side + above) / 2 + V((0, 0, 0.10))), (f_down - 6, above), (f_down, place), (f_rel, place)):
            carry_hand(h, s, f, W)
        hand(h, s, f_rel + 6, place + V((0, -0.02, 0.10)), (0, 0.3, -1), (-sg, 0, 0), grip=0.25)
        hand(h, s, f_rel + 18, V((P0.x + sg * 0.17, P0.y + 0.10, 0.92)), (0, -0.4, -0.9), (-sg, 0, 0), pole=(P0.x + sg * 0.5, P0.y - 0.5, 0.95), grip=0.3)
# passengers step back from the belt after letting go (clear of the traveller's walk)
for h, P0, tray, f_lift, f_down, f_rel in CARRIERS[1:]:
    bk = catmull([(f_rel + 20, P0), (f_rel + 44, P0 + V((0.10, -0.62, 0)))])
    h.walk(bk, lambda f: FWD, f_rel + 20, f_rel + 44, stride=0.4, lift=0.04, lean=-2)
    for f, hd in ((f_rel + 50, (10, 20)), (1600, (8, 40)), (1660, (6, 60)), (END, (6, 70))):
        stand(h, f, P0 + V((0.10, -0.62, 0)), FWD, spine=(4, 0, 0), head=hd)
        for s, sg in (("L", -1), ("R", 1)):
            hand(h, s, f, P0 + V((0.10 + sg * 0.17, -0.52, 0.92)), (0, -0.4, -0.9), (-sg, 0, 0), pole=(P0.x + 0.1 + sg * 0.5, P0.y - 1.1, 0.95), grip=0.3)
# traveller in socks: watches the trays roll (1534-1600), walks after them along the belt (1600-1695), stops, looks down at
# his socks (1705), small shrug and looks up (1718)
TP = CARRIERS[0][1]
for f, hd in ((1470, (14, 0)), (1534, (10, 25)), (1570, (8, 40)), (1596, (6, 50))):
    stand(trav, f, TP, FWD, spine=(4, 0, 0), head=hd)
    for s, sg in (("L", -1), ("R", 1)):
        hand(trav, s, f, TP + V((sg * 0.17, 0.10, 0.92)), (0, 0.4, -0.9), (-sg, 0, 0), pole=(TP.x + sg * 0.5, TP.y - 0.5, 0.95), grip=0.3)
TEND = AX + V((0.55, -0.70, 0))
tw = catmull([(1600, TP), (1615, TP + V((0.25, 0.02, 0))), (1695, TEND)])
trav.walk(tw, lambda f: FWD - 90 * smooth((f - 1600) / 14.0), 1600, 1695, stride=0.62, lift=0.04, lean=6)   # yaw 90: facing +X
for f in range(1604, 1691, 6):      # arm swing walking along +X (his left = +Y)
    p_ = tw(f); ph = math.sin((f - 1604) / 40.0 * 2 * math.pi)
    for s, sg in (("L", 1), ("R", -1)):
        sw = sg * ph * 0.12
        hand(trav, s, f, V((p_.x + 0.10 + sw, p_.y + sg * 0.16, 0.93 + 0.25 * abs(sw))), (0.75, 0, -0.65), (0, -sg, 0),
             pole=(p_.x - 0.6, p_.y + sg * 0.35, 0.95), grip=0.3)
for f, sp, hd, sd in ((1702, 6, (8, 0), 0), (1708, 24, (34, 0), 0), (1716, 4, (0, -5), 0), (1722, 2, (-6, 0), 2), (END, 2, (-4, 4), 0)):
    stand(trav, f, TEND, 90, spine=(sp, 0, sd), head=hd)
for f in (1702, 1714):      # hands on his hips (facing +X: his left is +Y)
    for s, sg in (("L", 1), ("R", -1)):
        hand(trav, s, f, TEND + V((0.02, sg * 0.19, 0.98)), (0.4, -sg * 0.5, -0.6), (0, -sg, 0), pole=(TEND.x - 0.1, TEND.y + sg * 0.6, 1.15), grip=0.3)
for f in (1720, END):      # palms-up shrug in front of him
    for s, sg in (("L", 1), ("R", -1)):
        hand(trav, s, f, TEND + V((0.20, sg * 0.40, 1.02)), (0.4, sg * 0.9, 0.1), (0, 0, 1), pole=(TEND.x - 0.2, TEND.y + sg * 0.5, 0.9), grip=0.2)
# trays ride the belt into the tunnel together from 1506
TRAY = bpy.data.objects["Tray_1"]
for o in bpy.data.objects:
    if o.name.startswith("Tray_"):
        x0 = o.location.x
        for f in (1, 1506): o.location.x = x0; o.keyframe_insert("location", frame=f)
        o.location.x = x0 + 2.75; o.keyframe_insert("location", frame=1690)
