"""Part 2 (VO lines 17-34): "By February 2003..." -> "...a hundred million dollars."  38 shots.
Same house rules and shot API as p1.py. Crew at night: Leonardo (dark wool coat), D'Onorio (brown leather), Finotto
(olive bomber), all in black leather gloves."""
import math, os
import bpy
from mathutils import Vector, Matrix
import sets as ST, sets2 as S2, modern as MD, acts as AC, props as PR

HAIR = float(os.environ.get("HAIR", "0.6"))
V = Vector
DW, WALL = ST.DW, ST.WALL


def dirq(d):
    """Rotation that points a prop's local -Y along world direction d."""
    return (-V(d)).normalized().to_track_quat('Y', 'Z').to_euler()


def torch_pose(st, side, aim, reach=0.42):
    """Torch held forward at chest height toward `aim` (world). Returns a function that places the lit torch
    after finish()."""
    h = st.m.h
    sh = st.M @ h.bone_head(f"upperarm01.{side}")
    d = (V(aim) - sh).normalized()
    w = sh + d * reach + V((0, 0, -0.12))
    st.hand(side, w, elbow=(0.6, 0.3, -0.9), grip=1.0)
    def place(name, energy=60):
        t = PR.torch(name, energy=energy); bpy.context.view_layer.update()
        t.location = st.palm(side); t.rotation_euler = dirq(V(aim) - st.palm(side))
        return t
    return place


def bag_pose(st, side):
    """Holdall carried by its straps at arm's length; returns a placer for after finish()."""
    st.arm_down(side, out=0.34, fwd=0.02, bend=6)
    import poses as P
    P.grip(st.m.h, side, 0.9)
    def place(name, full=0.8):
        b = PR.holdall(name, full=full); bpy.context.view_layer.update()
        p = st.palm(side); sg = 1 if side == "L" else -1
        out = (st.M.to_3x3() @ V((sg, 0, 0))).normalized()
        b.location = p + out * 0.17 - V((0, 0, 0.19 + 0.14 * full + 0.04))
        b.rotation_euler = (0, 0, math.atan2(out.y, out.x) + math.pi / 2)
        return b
    return place


def crew(names=("Leonardo", "DOnorio", "Finotto")):
    return {n: MD.CAST[n](night=True) for n in names}


# ============================================================================ L17 the weekend
def T01():
    S2.exterior("dawn")
    for i, (x, y, hd) in enumerate(((-6.0, -3.2, -100), (-4.8, -3.6, -95))):
        t = MD.Trader(i); st = AC.Stand(t, (x, y), hd); st.walk(0.2 + 0.4 * i); st.finish(density=HAIR)
    return dict(a=((-5.1, 0.6, 1.6), (-5.6, -12.0, 1.1)), b=((-5.15, 0.2, 1.6), (-5.6, -12.0, 1.1)), lens=32)


def T02():
    A = ST.vault_complex("day", door_angle=30)
    leaf = A["vault_door"]; bpy.context.view_layer.update()
    M = leaf.matrix_world
    nout = (M.to_3x3() @ V((0, -1, 0))).normalized()
    p = M @ V((-DW + 0.12, -0.37, 1.1))
    g = MD.Guard(); st = AC.Stand(g, (p + nout * 0.5).to_tuple()[:2], math.degrees(math.atan2(-nout.y, -nout.x)), lean=8)
    for sd, dz in (("L", 0.12), ("R", -0.1)):
        st.hand(sd, p + nout * 0.11 + V((0, 0, dz)), elbow=(0.6, 0.3, -0.8), curl=6)
    st.finish(look=p, density=HAIR)
    return dict(a=((-0.75, -3.4, 1.65), (0.3, -1.2, 1.2)), b=((-0.65, -3.05, 1.62), (0.3, -1.2, 1.2)), lens=28,
                hand_ok=("vault",))


def T03():
    S2.exterior("dawn")
    return dict(a=((12.0, -12.0, 1.4), (-2.0, 0.0, 3.0)), b=((10.5, -11.5, 1.4), (-2.0, 0.0, 3.0)), lens=24, cine=dict(exposure=0.0))


# ============================================================================ L18 hours inside, no alarm
def T04():
    S2.security_room("building", night=True)
    return dict(a=((-1.2, -1.6, 1.5), (0.2, 1.6, 1.1)), b=((-0.9, -1.2, 1.45), (0.2, 1.6, 1.1)), lens=26, cine=dict(exposure=1.6))


# ============================================================================ L19 the night of the 15th, the garage
def T05():
    A = S2.garage("night")
    rt = A["ramp_top"]; GY0 = A["GY0"]
    c = crew()
    for i, (n, x, y) in enumerate((("Leonardo", 0.05, GY0 - 2.4), ("DOnorio", 0.95, GY0 - 4.0), ("Finotto", -0.9, GY0 - 5.4))):
        z = max(0.0, (GY0 - y)) * 0.3                 # three men spread across the ramp, each readable, arms at their sides
        st = AC.Stand(c[n], (x, y, z), 90); st.walk(0.15 + 0.3 * i, stride=18)
        st.arm_down("L", out=0.14, fwd=0.03); st.arm_down("R", out=0.14, fwd=0.03)
        st.finish(density=HAIR, floor_z=0.0, floor_fn=lambda yy: max(0.0, (GY0 - yy) * 0.3))
    return dict(a=((0.4, GY0 - 9.0, 4.1), (0.0, GY0 + 2.0, 0.8)), b=((0.35, GY0 - 8.5, 3.9), (0.0, GY0 + 2.0, 0.8)), lens=28,
                cine=dict(exposure=0.4), hand_ok=("ramp",))


def T06():
    A = S2.district()
    for a, b in A["district_streets"]:
        S2.soft_strip(a, b, 0.0115, 0.06, alpha=0.55)
    S2.ripple_bands(A["garage_entrance"] + V((0, 0, 0.002)), (0, 0, 1), (0.02,), width=0.03, color=(1.0, 0.85, 0.55), strength=3.0, alpha=0.6)
    return dict(a=((-0.55, -0.75, 0.65), (0.0, 0.05, 0.0)), b=((-0.35, -0.6, 0.48), (0.0, 0.1, 0.0)), lens=35,
                fstop=6.0, focus=(0, 0.05, 0.02))


def T07():
    A = S2.garage("night")
    c = crew(); places = []
    for i, (n, x, y) in enumerate((("Leonardo", 1.2, 1.2), ("DOnorio", 2.3, 2.6), ("Finotto", 1.4, 3.6))):
        st = AC.Stand(c[n], (x, y), 80); st.walk(0.3 + 0.27 * i)
        pl = bag_pose(st, "L") if n == "Finotto" else None
        st.finish(density=HAIR)
        if pl:
            pl("holdall_" + n, full=0.2)
    return dict(a=((0.2, -3.0, 1.55), (2.8, 6.5, 1.1)), b=((0.4, -2.3, 1.55), (2.9, 6.5, 1.1)), lens=30, hand_ok=("holdall",),
                cine=dict(exposure=1.4))


# ============================================================================ L20 down toward the vault
def T08():
    A = ST.vault_complex("night", gate_angle=0)
    c = crew(); y_end = -WALL - ST.CY
    for i, (n, x, y) in enumerate((("Finotto", 0.3, y_end + 2.6), ("Leonardo", -0.35, y_end + 1.6), ("DOnorio", 0.25, y_end + 0.6))):
        z = 0.0
        st = AC.Stand(c[n], (x, y, z), 90); st.walk(0.2 + 0.3 * i)
        pl = torch_pose(st, "R", (0, -2.0, 0.6))
        st.finish(density=HAIR, floor_z=z)
        pl(f"torch_{n}", 135)
    return dict(a=((-0.25, y_end - 1.5, 2.5), (0.1, -2.0, 0.9)), b=((-0.2, y_end - 1.1, 2.35), (0.1, -2.0, 0.9)), lens=26,
                hand_ok=("torch", "stair"), cine=dict(exposure=0.6))


# ============================================================================ L21 cameras record, recordings upstairs
def T09():
    A = ST.vault_complex("night", gate_angle=0)
    c = crew(("DOnorio", "Finotto"))
    for i, (n, x, y) in enumerate((("DOnorio", 0.25, -3.3), ("Finotto", -0.3, -4.1))):
        st = AC.Stand(c[n], (x, y), 92); st.walk(0.3 + 0.4 * i); pl = torch_pose(st, "R", (0, -1.0, 0.8))
        st.finish(density=HAIR); pl(f"torch_{n}", 135)
    cc = A["cctv"]
    ST.box("cctv_led", cc + V((0.06, -0.2, -0.04)), (0.01, 0.01, 0.01), ST.emit("rec_led", (1.0, 0.05, 0.02), 40))
    return dict(a=((0.35, -6.4, 1.85), (-0.55, -2.3, 2.1)), b=((0.3, -6.0, 1.85), (-0.55, -2.3, 2.15)), lens=26,
                hand_ok=("torch",), cine=dict(exposure=1.7))


def T10():
    A = S2.security_room("building", night=True)
    v = A["vcr"]
    return dict(a=((0.9, -0.25, 1.3), tuple(v + V((0, 0, 0.15)))), b=((1.35, -0.55, 1.2), tuple(v + V((0, 0, 0.25)))), lens=35,
                fstop=3.2, focus=v, cine=dict(exposure=1.7))


# ============================================================================ L22 first, the steel door
def T11():
    A = ST.vault_complex("night", gate_angle=95)
    c = crew()
    pos = (("Leonardo", -0.4, -1.55, 92), ("DOnorio", 0.35, -1.7, 100), ("Finotto", -0.1, -2.45, 90))
    for n, x, y, hd in pos:
        st = AC.Stand(c[n], (x, y), hd); pl = torch_pose(st, "R", (0.0, -WALL - 0.3, 1.3))
        st.head_to((0, -WALL, 1.4), share=0.6)
        st.finish(density=HAIR); pl(f"torch_{n}", 210)
    return dict(a=((0.15, -4.1, 1.7), (0.0, -0.6, 1.1)), b=((0.1, -3.6, 1.68), (0.0, -0.6, 1.1)), lens=30, hand_ok=("torch",),
                cine=dict(exposure=1.5))


# ============================================================================ L23 the key, the combination
def _cupboard(A):
    kc = A["key_cabinet"]
    for o in list(bpy.data.objects):
        if o.name.startswith("key_cabinet"):
            bpy.data.objects.remove(o)
    cab = ST.steel_paint("cab_open", (0.25, 0.3, 0.26)); x0 = kc.x - 0.08
    ST.box("cab_back", (x0 - 0.06, kc.y, kc.z), (0.02, 0.5, 0.6), cab)
    for sg in (1, -1):
        ST.box("cab_side", (x0, kc.y + sg * 0.25, kc.z), (0.14, 0.02, 0.6), cab)
    for sz in (1, -1):
        ST.box("cab_tb", (x0, kc.y, kc.z + sz * 0.3), (0.14, 0.5, 0.02), cab)
    ST.box("cab_door", (x0 - 0.03, kc.y - 0.53, kc.z), (0.02, 0.5, 0.6), cab)          # swung right back against the wall
    hook = V((x0 - 0.03, kc.y - 0.05, kc.z + 0.18)); ST.box("cab_hook", hook, (0.04, 0.008, 0.008), ST.brushed())
    return kc, hook


def T12():
    A = ST.vault_complex("night", gate_angle=95)
    kc, hook = _cupboard(A)
    k1 = PR.vault_key_part("keyA", 0.24, bit=True); k1.location = hook + V((0.01, -0.01, -0.02))
    m = MD.DOnorio(night=True); st = AC.Stand(m, (kc.x + 0.62, kc.y - 0.12), 180)
    st.hand("R", hook + V((0.06, -0.02, -0.04)), elbow=(0.6, 0.3, -0.8), grip=0.5)
    pl = torch_pose(st, "L", hook)
    st.head_to(hook, share=0.7)
    st.finish(look=hook, density=HAIR); pl("torch_D", 160)
    return dict(a=((kc.x + 1.55, kc.y + 0.5, 1.75), tuple(hook + V((0.2, 0, -0.1)))), b=((kc.x + 1.4, kc.y + 0.4, 1.72), tuple(hook + V((0.2, 0, -0.1)))),
                lens=30, hand_ok=("torch", "key", "cab"), cine=dict(exposure=1.7))


def T13():
    A = ST.vault_complex("night", gate_angle=95)
    m = MD.DOnorio(night=True); st = AC.Stand(m, (0.3, -3.2), 90)
    sh = st.M @ m.h.bone_head("upperarm01.R")
    hp = V((0.3, -2.8, 1.15))
    st.hand("R", hp + V((0.06, 0, 0)), elbow=(0.7, 0.3, -0.8), grip=0.7)
    st.hand("L", hp + V((-0.06, 0, -0.02)), elbow=(0.7, 0.3, -0.8), grip=0.7)
    st.head_to(hp, share=0.8)
    st.finish(look=hp, density=HAIR)
    k1 = PR.vault_key_part("keyA", 0.24, bit=True); k2 = PR.vault_key_part("keyB", 0.16, bit=False)
    bpy.context.view_layer.update()
    pr, pll = st.palm("R"), st.palm("L")
    k1.location = pr + V((0, 0.0, 0.03)); k1.rotation_euler = (0, math.radians(90), 0)
    k2.location = pll + V((0, 0.0, 0.03)); k2.rotation_euler = (0, math.radians(-90), 0)
    AC.fit_clear(k1, [o for o in m.objects if o.type == 'MESH'], V((0, 0, 1)))
    AC.fit_clear(k2, [o for o in m.objects if o.type == 'MESH'], V((0, 0, 1)))
    ST.light_spot("key_torch", (1.0, -3.7, 1.9), hp, 50, angle=35, color=(1.0, 0.9, 0.75))
    return dict(a=((1.0, -4.15, 1.8), tuple(hp)), b=((0.95, -4.0, 1.75), tuple(hp)), lens=30, fstop=4.0, focus=hp,
                hand_ok=("key",), cine=dict(exposure=1.6))


def T14():
    A = ST.vault_complex("night", gate_angle=95)
    d = A["dial"]
    m = MD.Finotto(night=True); st = AC.Stand(m, (d.x - 0.1, d.y - 0.58), 95)
    st.hand("R", d + V((0.02, -0.14, -0.04)), elbow=(0.7, 0.3, -0.8), grip=0.35)
    pl = torch_pose(st, "L", d)
    st.head_to(d, share=0.8); st.finish(look=d, density=HAIR); pl("torch_F", 160)
    return dict(a=((d.x + 0.55, d.y - 1.0, 1.75), tuple(d)), b=((d.x + 0.45, d.y - 0.85, 1.7), tuple(d)), lens=40, fstop=2.8, focus=d,
                hand_ok=("torch", "vault_dial", "vault"), cine=dict(exposure=1.7))


def T15():
    A = ST.vault_complex("night", gate_angle=95)
    d = A["dial"]
    # a pinhole camera concealed in the ceiling fitting above the door, aimed at the dial
    cam = V((-0.45, -WALL - 1.15, ST.CZ - 0.06))
    blk = ST.flat("pinhole_body", (0.02, 0.02, 0.022), 0.4)
    ST.box("pinhole_cam", cam, (0.05, 0.04, 0.035), blk, bevel=0.004)
    import ship as SH
    SH.cyl("pinhole_lens", cam + V((-0.02, 0.012, -0.012)), cam + V((-0.026, 0.02, -0.02)), 0.006, mat=ST.flat("lens", (0.0, 0.0, 0.0), 0.05), verts=16)
    S2.ripple_bands(cam + V((-0.03, 0.02, -0.025)), (d - cam), (0.06,), width=0.07, strength=2.5, alpha=0.5)
    ST.light_point("pinhole_fill", cam + V((0.25, -0.35, -0.3)), 6, (1.0, 0.8, 0.55), radius=0.1)
    ST.light_spot("door_torch", (0.8, -3.0, 1.8), d, 120, angle=30, color=(1.0, 0.85, 0.65))
    return dict(a=((0.4, -1.3, 2.0), tuple(cam)), b=((0.35, -1.35, 1.98), tuple(cam.lerp(d, 0.2))),
                lens=35, fstop=2.8, focus=cam, cine=dict(exposure=0.3))


def T16():
    ST.vault_complex("night", gate_angle=95)
    return dict(a=((-0.4, -6.4, 1.55), (0.0, -0.6, 1.2)), b=((-0.35, -5.8, 1.55), (0.0, -0.6, 1.2)), lens=32, cine=dict(exposure=2.0))


# ============================================================================ L24-25 the magnetic contacts
def T17():
    A = ST.vault_complex("night", gate_angle=95)
    mc = A["mag_contact"]
    S2.ripple_bands(mc + V((0, -0.02, -0.025)), (0, -1, 0), (0.06,), width=0.08, strength=2.5, alpha=0.5)
    ST.light_spot("contact_torch", (mc.x + 0.6, mc.y - 1.2, mc.z - 0.6), mc, 90, angle=25, color=(1.0, 0.85, 0.65))
    return dict(a=(tuple(mc + V((0.35, -0.7, 0.28))), tuple(mc + V((0, 0, -0.02)))), b=(tuple(mc + V((0.3, -0.6, 0.24))), tuple(mc + V((0, 0, -0.02)))),
                lens=35, fstop=5.6, focus=mc, cine=dict(exposure=1.8))


def T18():
    A = ST.vault_complex("night", gate_angle=95, contacts="bypassed")
    mc = A["mag_contact"]
    m = MD.DOnorio(night=True); st = AC.Stand(m, (mc.x, mc.y - 0.78), 90, lean=-3)
    st.hand("R", mc + V((0.08, -0.11, -0.05)), elbow=(0.8, 0.2, -0.8), curl=20)
    st.hand("L", mc + V((-0.09, -0.11, -0.06)), elbow=(0.8, 0.2, -0.8), curl=20)
    st.head_to(mc, share=0.8); st.finish(look=mc, density=HAIR)
    ST.light_spot("contact_torch", (mc.x + 0.9, mc.y - 1.3, 1.4), mc, 120, angle=30, color=(1.0, 0.85, 0.65))
    return dict(a=((mc.x + 0.85, mc.y - 1.9, 1.75), tuple(mc)), b=((mc.x + 0.75, mc.y - 1.75, 1.75), tuple(mc)), lens=30,
                fstop=3.2, focus=mc, hand_ok=("bypass", "magcontact", "doorwall", "vframe"), cine=dict(exposure=1.7))


def T19():
    A = ST.vault_complex("night", gate_angle=95, contacts="bypassed", door_angle=38)
    leaf = A["vault_door"]; bpy.context.view_layer.update(); M = leaf.matrix_world
    hub = M @ V((-DW / 2 - 0.03, -0.36 - 0.05, 1.0)); nout = (M.to_3x3() @ V((0, -1, 0))).normalized()
    spoke = M @ V((-DW / 2 - 0.03 - 0.17, -0.36 - 0.05, 1.0 + 0.1))
    m = MD.Finotto(night=True); st = AC.Stand(m, (spoke + nout * 0.55).to_tuple()[:2], math.degrees(math.atan2(-nout.y, -nout.x)) - 15, lean=-4)
    gap = st.grip("R", spoke, (M.to_3x3() @ V((math.cos(math.radians(210)), 0, math.sin(math.radians(210))))).normalized(), radius=0.012)
    st.arm_down("L"); st.finish(look=hub, density=HAIR)
    ST.light_point("corr_torchlight", (-0.5, -2.6, 1.5), 25, (1.0, 0.85, 0.65), radius=0.2)
    return dict(a=((-0.75, -3.3, 1.6), (0.2, -1.2, 1.2)), b=((-0.6, -2.95, 1.58), (0.2, -1.1, 1.2)), lens=28,
                hand_ok=("vault_spoke", "vault"), cine=dict(exposure=1.7))


# ============================================================================ L26-27 sensors blinded, lights on
def T20():
    A = ST.vault_complex("night", gate_angle=95, contacts="bypassed", door_angle=92, taped=True)
    ld = A["light_detector"]
    stepm = ST.steel_paint("step_box", (0.35, 0.3, 0.2), 0.5)
    ST.box("step_box", (ld.x, ld.y - 0.38, 0.2), (0.6, 0.45, 0.4), stepm, bevel=0.01)      # a sturdy step box
    m = MD.Finotto(night=True); st = AC.Stand(m, (ld.x, ld.y - 0.38, 0.4), 90)
    st.hand("R", ld + V((0.06, -0.04, -0.19)), elbow=(0.7, 0.3, -0.9), curl=10)
    st.hand("L", ld + V((-0.07, -0.06, -0.2)), elbow=(0.7, 0.3, -0.9), curl=10)
    st.head_to(ld, share=0.6); st.finish(look=ld, density=HAIR, floor_z=0.4)
    tr = PR.tape_roll(); tr.location = (ld.x + 0.24, ld.y - 0.5, 0.432)
    t = PR.torch("torch_floor", energy=80); t.location = (0.8, 1.0, 0.03); t.rotation_euler = dirq(ld - V((0.8, 1.0, 0.03)))
    return dict(a=((1.6, 0.4, 0.9), tuple(ld + V((0, 0, -0.5)))), b=((1.45, 0.55, 0.95), tuple(ld + V((0, 0, -0.45)))), lens=26,
                hand_ok=("light_detector", "tape", "step_box"), cine=dict(exposure=1.7))


def T21():
    A = ST.vault_complex("night", gate_angle=95, door_angle=92, taped=True)
    p = A["pirs"][1]
    ST.light_spot("pir_torch", (p.x - 1.2, p.y - 1.4, 1.3), p, 90, angle=25, color=(1.0, 0.85, 0.65))
    return dict(a=(tuple(p + V((-0.7, -0.8, -0.5))), tuple(p)), b=(tuple(p + V((-0.55, -0.65, -0.42))), tuple(p)), lens=45,
                fstop=2.8, focus=p, cine=dict(exposure=1.8))


def T22():
    A = ST.vault_complex("heist", forced=6, debris=0.0, contacts="bypassed", taped=True)
    c = crew()
    for n, x, y, hd in (("Leonardo", -0.4, 0.9, 110), ("DOnorio", 0.6, 1.6, 30), ("Finotto", -1.2, 2.3, 170)):
        st = AC.Stand(c[n], (x, y), hd); st.head_to((x * 2, 3.5, 1.4), share=0.5); st.finish(density=HAIR)
    return dict(a=((0.25, -1.6, 1.55), (0.0, 3.0, 1.2)), b=((0.25, -1.1, 1.5), (0.0, 3.0, 1.2)), lens=24)


# ============================================================================ L28 each box, its own lock; the tool
def T23():
    A = ST.vault_complex("heist", forced=24, debris=0.15, contacts="bypassed", taped=True, extra_open=[])
    cells = A["cells"]
    # D'Onorio at a closed box on the right wall (col 5, row 2): tool head at its lock
    tgt = None
    for (kind, sg, c, r, org, yaw, w, h) in cells:
        if kind == "side" and sg == 1 and c == 5 and r == 2:
            R = Matrix.Rotation(yaw, 4, 'Z'); tgt = Matrix.Translation(org) @ R @ V((w * 0.72, -0.03, h * 0.12)); break
    ST.clear_floor([(VXp(), tgt.y)], 0.8)
    m = MD.DOnorio(night=True); st = AC.Stand(m, (tgt.x - 0.6, tgt.y + 0.05), 0, lean=6)
    st.hand("R", tgt + V((-0.33, 0.0, -0.02)), elbow=(0.7, 0.3, -0.8), grip=0.9)
    st.hand("L", tgt + V((-0.17, -0.02, 0.02)), elbow=(0.7, 0.3, -0.8), grip=0.9)
    st.head_to(tgt, share=0.8); st.finish(look=tgt, density=HAIR)
    tl = PR.forcing_tool(); tl.location = st.palm("R"); tl.rotation_euler = (0, 0, 0)
    d = tgt - st.palm("R"); tl.rotation_euler = (0, -math.atan2(d.z, math.hypot(d.x, d.y)), math.atan2(d.y, d.x))
    AC.fit_clear(tl, [o for o in m.objects if o.type == 'MESH'], V((0, 0, 1)))
    return dict(a=((tgt.x - 1.9, tgt.y - 1.0, 1.65), tuple(tgt + V((-0.3, 0, -0.1)))), b=((tgt.x - 1.75, tgt.y - 0.85, 1.62), tuple(tgt + V((-0.3, 0, -0.1)))),
                lens=32, hand_ok=("tool", "boxdoor"))


def VXp():
    return ST.VX - 0.5


def T24():
    out = T23()
    tool = bpy.data.objects.get("tool")
    if tool:
        bpy.context.view_layer.update()
        hd = tool.matrix_world @ V((0.33, 0, 0))
        out = dict(out, a=(tuple(hd + V((-1.0, -0.55, 0.5))), tuple(hd)), b=(tuple(hd + V((-0.92, -0.5, 0.46))), tuple(hd)), lens=35,
                   fstop=3.2, focus=hd)
    return out


# ============================================================================ L29 diamonds, gold, cash, jewellery
def _tabletop(color=(0.18, 0.02, 0.04), sparkle=False):
    if sparkle:                     # stones refract their surroundings: a soft light studio, not a black void
        w = ST.world((0.75, 0.74, 0.72), 0.9)
    else:
        ST.world((0.01, 0.01, 0.01), 0.15)
    ST.box("velvet_tray", (0, 0, -0.01), (0.6, 0.4, 0.02), ST.velvet("tray_velvet", color))
    ST.box("steel_floor", (0, 0, -0.03), (3, 3, 0.02), ST.flat("dark", (0.04, 0.035, 0.03), 0.5))
    ST.light_spot("hero_key", (-0.4, -0.5, 0.7), (0, 0, 0), 70, angle=30, color=(1.0, 0.9, 0.74), radius=0.02 if sparkle else 0.05)
    ST.light_area("hero_rim", (0.5, 0.5, 0.4), (0, 0, 0), 0.4, 15, (0.8, 0.85, 1.0))
    if sparkle:                     # small hard points: each facet throws a flash and a little fire
        for k, (x, y, z) in enumerate(((0.3, -0.3, 0.5), (-0.2, 0.35, 0.45), (0.05, -0.45, 0.35), (0.4, 0.2, 0.3))):
            ST.light_point(f"spark{k}", (x, y, z), 12, (1.0, 0.97, 0.92), radius=0.004)


def T25():
    _tabletop((0.01, 0.015, 0.06), sparkle=True)
    ST.box("diamond_paper", (0.01, 0.0, 0.0004), (0.16, 0.11, 0.0008), ST.paper_mat("briefke", (0.85, 0.84, 0.8)), rot=(0, 0, 0.15))
    PR.brilliants("dia", n=60, spread=0.035)
    return dict(a=((-0.1, -0.2, 0.13), (0, 0, 0.0)), b=((-0.07, -0.16, 0.1), (0, 0, 0.0)), lens=60, fstop=5.6, focus=(0, 0, 0))


def T26():
    _tabletop((0.06, 0.01, 0.01))
    PR.sf_put(PR.GOLD_BARS, (0.02, 0.0, 0.0), width=0.15, rz=0.3)
    PR.sf_put(PR.GOLD_BAR, (-0.12, -0.04, 0.0), width=0.116, rz=-0.2)
    PR.sf_put(PR.GOLD_BAR, (0.15, -0.07, 0.0), width=0.116, rz=0.6)
    return dict(a=((-0.25, -0.33, 0.2), (0, 0, 0.02)), b=((-0.2, -0.29, 0.17), (0, 0, 0.02)), lens=50, fstop=5.6, focus=(0, 0, 0.02))


def T27():
    _tabletop((0.03, 0.03, 0.035))
    PR.sf_put(PR.USD_STACKS, (0.02, 0.02, 0.0), width=0.2, rz=0.25)
    PR.sf_put(PR.USD_STACKS, (-0.17, -0.06, 0.0), width=0.18, rz=-0.5)
    PR.sf_put(PR.USD_LOOSE, (0.17, -0.08, 0.0), width=0.18, rz=0.9)
    return dict(a=((0.28, -0.4, 0.26), (0, 0, 0.03)), b=((0.22, -0.35, 0.22), (0, 0, 0.03)), lens=40, fstop=5.6, focus=(0, 0, 0.03))

def T28():
    _tabletop((0.09, 0.0, 0.02), sparkle=True)
    for k, (x, y, rz, uid) in enumerate(((-0.06, -0.03, 0.2, PR.RING_DIAMOND), (0.03, 0.03, 1.1, PR.RING_CARAT), (0.08, -0.05, 2.0, PR.RING_DIAMOND),
                                          (-0.02, 0.06, 0.7, PR.RING_CARAT), (0.12, 0.04, 2.6, PR.RING_DIAMOND))):
        if uid == PR.RING_CARAT:
            o = PR.sf_put(uid, (x, y, 0.0), height=0.022, rz=rz); o.rotation_euler.x = math.radians(90)
            bpy.context.view_layer.update()
        else:
            PR.sf_put(uid, (x, y, 0.0), width=0.024, rz=rz)
    PR.brilliants("dia_j", n=18, spread=0.04, seed=5)
    return dict(a=((-0.2, -0.24, 0.15), (0.02, 0, 0.0)), b=((-0.16, -0.2, 0.12), (0.02, 0, 0.0)), lens=60, fstop=5.6, focus=(0.02, 0, 0.0))


# ============================================================================ L30 sorting; bags have a limit
def T29():
    A = ST.vault_complex("heist", forced=80, debris=0.6, contacts="bypassed", taped=True)
    ST.clear_floor([(0.0, 2.2), (-0.4, 2.2), (0.9, 2.6), (1.3, 3.1), (-0.6, 1.2), (0.35, 1.75), (-0.8, 2.7)], 0.75)
    c = crew()
    k1 = AC.Kneel(c["Leonardo"], (0.0, 2.2), 0, lean=38)
    k1.hand("L", (0.35, 2.05, 0.06), elbow=(0.7, 0.3, -0.8), curl=30); k1.hand("R", (0.35, 2.35, 0.06), elbow=(0.7, 0.3, -0.8), curl=30)
    k1.finish(density=HAIR)
    k2 = AC.Kneel(c["DOnorio"], (0.95, 2.75), 225, lean=34)
    k2.hand("L", (0.6, 2.5, 0.06), elbow=(0.7, 0.3, -0.8), curl=30); k2.hand("R", (0.75, 2.35, 0.06), elbow=(0.7, 0.3, -0.8), curl=30)
    k2.finish(density=HAIR)
    st = AC.Stand(c["Finotto"], (-0.6, 1.2), 30); pl = bag_pose(st, "R"); st.finish(density=HAIR); pl("bag_F", 0.9)
    for i, (x, y) in enumerate(((0.35, 1.7), (-0.85, 2.75))):
        b = PR.holdall(f"bag{i}", full=0.5 + 0.3 * i); b.location = (x, y, 0)
    for i in range(5):
        cb = PR.cash_bundle(f"sorted{i}"); cb.location = (0.42 + 0.06 * i, 2.15 + 0.03 * (i % 2), 0.001)
    return dict(a=((-1.1, 0.0, 2.15), (0.45, 2.45, 0.25)), b=((-0.95, 0.15, 2.1), (0.45, 2.45, 0.25)), lens=26,
                hand_ok=("holdall", "bag", "sorted", "cash", "floor"))


def T30():
    A = ST.vault_complex("heist", forced=80, debris=0.8, contacts="bypassed", taped=True)
    b = PR.holdall("bag_full", full=1.0); b.location = (0.3, 1.6, 0)
    for i in range(4):
        cb = PR.cash_bundle(f"left{i}"); cb.location = (0.0 + 0.09 * i, 1.35 - 0.03 * i, 0.001); cb.rotation_euler = (0, 0, 0.3 * i)
    au = ST.gold()
    for i in range(6):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.01, minor_radius=0.0018, location=(-0.1 + 0.05 * i, 1.48, 0.002))
        bpy.context.active_object.data.materials.append(au)
    g = PR.gold_bar("bar_left"); g.location = (0.15, 1.25, 0.0)
    return dict(a=((-0.4, 0.7, 0.35), (0.2, 1.5, 0.05)), b=((-0.3, 0.85, 0.3), (0.2, 1.5, 0.05)), lens=35, fstop=3.2, focus=(0.15, 1.35, 0.02))


# ============================================================================ L31 109 boxes
def T31():
    ST.vault_complex("wreck", contacts="bypassed", taped=True)
    return dict(a=((-2.2, 0.5, 2.1), (1.3, 3.9, 0.6)), b=((-1.6, 0.4, 2.0), (1.6, 3.6, 0.6)), lens=20)


# ============================================================================ L32 the tapes; out; until Monday
def T32():
    A = S2.security_room("building", night=True)
    v = A["vcr"]
    m = MD.Finotto(night=True); st = AC.Stand(m, (v.x - 0.4, v.y + 0.24), 4)
    st.hand("R", v + V((-0.095, 0.0, 0.05)), elbow=(0.5, 0.4, -0.9), grip=0.5)   # relaxed bent arm, hand resting on the recorder
    pl = bag_pose(st, "L")
    st.head_to(v + V((0.3, 0.35, 0.0)), share=0.4); st.finish(density=HAIR); pl("bag_tapes", 0.6)   # face kept turned away from camera
    for o in bpy.data.objects:                       # the monitor glow is a broad bounce: no hard arm shadows on the sweater
        if o.type == 'LIGHT' and o.name.startswith("screen_glow"):
            o.data.use_shadow = False
    ST.light_area("vcr_soft", (v.x - 1.0, v.y + 0.6, 2.1), v, 1.2, 45, (1.0, 0.84, 0.62))
    # medium shot from behind and to his left: whole head in frame, face turned away to the recorder
    return dict(a=((v.x - 1.3, v.y - 1.15, 1.58), (v.x - 0.15, v.y + 0.1, 1.25)), b=((v.x - 1.24, v.y - 1.12, 1.56), (v.x - 0.15, v.y + 0.1, 1.25)), lens=22,
                hand_ok=("vcr", "bag"), cine=dict(exposure=0.2))


def T33():
    A = S2.garage("night")
    GY0 = A["GY0"]; c = crew()
    for i, (n, x, y) in enumerate((("Finotto", 0.4, GY0 - 4.5), ("DOnorio", -0.5, GY0 - 3.1), ("Leonardo", 0.1, GY0 - 1.6))):
        z = max(0.0, (GY0 - y)) * 0.3
        st = AC.Stand(c[n], (x, y, z), -90); st.walk(0.2 + 0.3 * i)
        pl = bag_pose(st, "R"); st.finish(density=HAIR, floor_z=0.0, floor_fn=lambda yy: max(0.0, (GY0 - yy) * 0.3)); pl(f"bag_{n}", 0.9)
    return dict(a=((0.2, GY0 + 4.0, 1.4), (0.0, GY0 - 8.0, 2.6)), b=((0.15, GY0 + 3.2, 1.4), (0.0, GY0 - 8.0, 2.6)), lens=30,
                hand_ok=("bag", "ramp"), cine=dict(exposure=0.4))


def T34():
    S2.exterior("dawn")
    return dict(a=((-3.0, -8.5, 1.1), (-0.5, 1.0, 1.6)), b=((-2.6, -7.8, 1.1), (-0.5, 1.0, 1.6)), lens=28)


# ============================================================================ L33 Monday: the traders
def T35():
    A = ST.vault_complex("wreck", contacts="bypassed", taped=True)
    spots = ((-2.2, 1.6, 180), (-2.25, 3.2, 175), (1.5, 4.0, 60), (2.3, 2.0, 0))
    ST.clear_floor([(x, y) for x, y, _ in spots], 0.6)
    for k, (x, y, hd) in enumerate(spots):
        t = MD.Trader(k); st = AC.Stand(t, (x, y), hd)
        st.head_to((x + 1.5 * math.cos(math.radians(hd)), y + 1.5 * math.sin(math.radians(hd)), 1.0), share=0.6)
        st.finish(density=HAIR)
    return dict(a=((0.4, -1.4, 1.65), (0.0, 3.0, 1.1)), b=((0.35, -0.9, 1.62), (0.0, 3.0, 1.1)), lens=24)


def T36():
    A = ST.vault_complex("wreck", contacts="bypassed", taped=True)
    ST.clear_floor([(0.3, 2.4), (-1.9, 3.0)], 0.6)
    t = MD.Trader(1); st = AC.Stand(t, (0.3, 2.4), 95); AC.hands_to_face(st); st.finish(density=HAIR)
    t2 = MD.Trader(3); s2 = AC.Stand(t2, (-1.9, 3.0), 175); s2.finish(density=HAIR)
    return dict(a=((0.55, 0.6, 1.7), (0.3, 3.2, 1.45)), b=((0.5, 0.9, 1.68), (0.3, 3.2, 1.45)), lens=35, fstop=3.2, focus=(0.3, 2.4, 1.5))


def T37():
    A = ST.vault_complex("wreck", contacts="bypassed", taped=True)
    ST.clear_floor([(-1.6, 1.5), (-2.2, 1.5), (-1.75, 2.1), (-1.5, 2.45)], 0.75)
    t = MD.Trader(2); sf = AC.SitFloor(t, (-1.6, 1.5), 180, back_lean=-12); sf.finish(density=HAIR)
    t2 = MD.Trader(4); kn = AC.Kneel(t2, (-1.75, 2.1), -100, lean=20)
    bpy.context.view_layer.update()
    knee = sf.M @ t.h.bone_head("lowerleg01.L")
    kn.hand("R", knee + V((0.0, 0.0, 0.11)), elbow=(0.5, 0.2, -1.0), curl=28)
    kn.finish(density=HAIR)
    return dict(a=((0.35, 1.15, 1.3), (-1.8, 1.7, 0.5)), b=((0.2, 1.2, 1.25), (-1.8, 1.7, 0.5)), lens=30,
                hand_ok=("Trader2", "Trader4"))


# ============================================================================ L34 a hundred million
def T38():
    ST.vault_complex("wreck", contacts="bypassed", taped=True)
    return dict(a=((0.2, 3.2, 0.25), (-0.6, 0.0, 0.5)), b=((0.4, 4.0, 1.4), (-0.4, -1.0, 0.9)), lens=22)


VO = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vo", "ANTWERP_P2_VO.txt")).read().splitlines()
PLAN = [
    ("T01", 1, 4.0, "EXT dusk, Friday: traders leave the Diamond Center (from behind)"),
    ("T02", 1, 3.5, "The vault: a guard swings the steel door shut for the weekend"),
    ("T03", 1, 3.0, "EXT: the street empties"),
    ("T04", 2, 4.5, "Night: the security room, monitors on, chair empty"),
    ("T05", 3, 4.0, "15 February, night: three men walk down the garage ramp (silhouettes)"),
    ("T06", 3, 5.5, "Maquette: the gated district streets (soft band) - the garage opens outside them"),
    ("T07", 3, 3.5, "The garage: the crew between covered cars, toward the stairwell"),
    ("T08", 4, 3.5, "Down the stairs to the vault level, torches (from behind)"),
    ("T09", 5, 3.5, "A corridor camera records them passing below"),
    ("T10", 5, 3.0, "Upstairs the recorders run"),
    ("T11", 6, 3.0, "Torchlight on the shut steel door"),
    ("T12", 7, 3.5, "D'Onorio at the key cupboard (from behind)"),
    ("T13", 7, 3.5, "The two halves of the key in gloved hands (OTS)"),
    ("T14", 7, 3.5, "Finotto at the combination dial (OTS)"),
    ("T15", 7, 4.0, "A pinhole camera above the door, aimed at the dial (Leonardo's claim)"),
    ("T16", 7, 3.5, "The empty corridor: how they got the combination is unknown"),
    ("T17", 8, 3.5, "The magnetic contact on the door frame"),
    ("T18", 9, 5.0, "D'Onorio holds the two contacts together and moves them aside"),
    ("T19", 9, 4.0, "Finotto hauls the door open: the alarm still reads 'shut'"),
    ("T20", 10, 3.5, "On a stepladder, tape over the light detector"),
    ("T21", 10, 2.5, "A motion sensor bagged"),
    ("T22", 11, 3.0, "The lights come on"),
    ("T23", 12, 3.5, "D'Onorio forces a box with the tool (from behind)"),
    ("T24", 12, 3.0, "Macro: the tool bites behind the lock"),
    ("T25", 13, 1.5, "Diamonds"),
    ("T26", 13, 1.5, "Gold"),
    ("T27", 13, 1.5, "Cash"),
    ("T28", 13, 1.5, "Jewellery"),
    ("T29", 14, 5.0, "On their knees, sorting; a bag fills"),
    ("T30", 14, 3.5, "A full bag; what does not fit stays on the floor"),
    ("T31", 15, 4.0, "109 boxes forced"),
    ("T32", 16, 3.0, "Upstairs Finotto takes the tapes"),
    ("T33", 16, 3.5, "Up the ramp and out, bags in hand"),
    ("T34", 16, 3.0, "EXT: Sunday, quiet street"),
    ("T35", 17, 4.0, "Monday: traders searching the wreckage for their boxes"),
    ("T36", 17, 3.0, "A trader with his hands over his face (from behind)"),
    ("T37", 17, 3.5, "One has collapsed against the boxes; another kneels beside him"),
    ("T38", 18, 5.0, "Rising pull-back over the wreck: a hundred million dollars"),
]
SHOTS = {sid: dict(fn=globals()[sid], dur=d, vo=VO[ln - 1], line=ln, desc=desc) for sid, ln, d, desc in PLAN}
