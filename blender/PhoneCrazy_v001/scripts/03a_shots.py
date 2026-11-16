# exec'd by 03_anim.py: staging per shot (crew placement + acting, phone screen, water, excavator, camera keys)
GROUND = OB["Ground"]
def gz(x, y):
    ok, loc, *_ = GROUND.ray_cast(Vector((x, y, 20.0)), Vector((0, 0, -1)))
    return loc.z if ok else 0.0
_put = put
def put(n, s, pos, yaw):
    PLACE[n].append((f0(s), Vector((pos[0], pos[1], gz(*pos) + 0.005)), yaw))
CASE_P = OB["Case"].location.copy(); PH_W = OB["Phone"].location.copy()
SPOT = {"Foreman": (-4.0, 1.32), "Digger": (-4.82, 1.12), "Mate": (-3.18, 1.16)}
EXC_LOOK = EXC_POS + Vector((-2.5, 0, 1.5))
import math as _m
PIT_SPOT = {"Foreman": 225, "Digger": 207, "Mate": 243}

def crew(s, mode, fa=None, fb=None, **kw):
    fa = fa or f0(s); fb = fb or (f1(s))
    for n in NAMES:
        if mode == "watch_exc":
            p = SPOT[n]; put(n, s, p, yaw_to(p, EXC_LOOK))
            hands = ("point", "R") if n == "Mate" else "hang"
            tgt = to_local(n, s, EXC_LOOK + Vector((-3.0, 0, -0.5))) if n == "Mate" else None
            idle(n, s, fa, fb, head=(2, {"Foreman": 4, "Digger": -6, "Mate": 0}[n]), hands=hands, tgt=tgt, head_end=(4, {"Foreman": -6, "Digger": 4, "Mate": 6}[n]))
        elif mode == "case":
            p = SPOT[n]; yaw = yaw_to(p, PH_W) if n != "Foreman" else 0.0; put(n, s, p, yaw)
            o = kw.get(n, {})
            idle(n, s, fa, fb, flex=o.get("flex", 6), spine=o.get("spine", 10), head=o.get("head", (16, 0)), head_end=o.get("head_end"),
                 spine_end=o.get("spine_end"), hands=o.get("hands", "hang"), tgt=to_local(n, s, PH_W) if o.get("hands", "hang") != "hang" else None,
                 brow=o.get("brow", 0.0), jaw=o.get("jaw", 0.0))
        elif mode == "pit":
            a = R_(PIT_SPOT[n]); p = (PIT.x + 4.5 * _m.cos(a), PIT.y + 4.5 * _m.sin(a)); put(n, s, p, yaw_to(p, PIT))
            idle(n, s, fa, fb, flex=5, spine=8, head=(10, 0), head_end=(20, 0), brow=0.002)

# ---------------------------------------------------------------- S1 "As soon as (they started digging)": wide site, excavator digging, crew watching
crew("S1", "watch_exc")
camshot("S1", [(0, (-9.5, -8.5, 6.2), (0.5, 5.5, 0.6), 22), (1, (-8.4, -7.0, 5.4), (0.8, 6.0, 0.6), 23)])
# ---------------------------------------------------------------- S2 "digging": bucket bites into the pit wall (low, close)
crew("S2", "watch_exc")
ev(sec("S2", 0.6)); BK = OB["shovel_GEO"].matrix_world.translation.copy() if False else None
camshot("S2", [(0, (0.0, 4.3, 1.1), (2.8, 8.3, 0.1), 30), (1, (0.4, 4.8, 0.8), (2.8, 8.3, -0.1), 32)])
# ---------------------------------------------------------------- S3 "one of their phones unlocked itself": phone on the case lid wakes and unlocks
crew("S3", "case", Foreman={"head": (20, 0), "head_end": (30, 0)})
tiles("S3", [(0, 0), (0.35, 1), (1.0, 2), (1.25, 3), (1.5, 4), (1.75, 5), (2.0, 6), (2.3, 7), (2.7, 8)])
camshot("S3", [(0, PH_W + Vector((0.01, -0.03, 0.40)), PH_W + Vector((0, 0.01, 0)), 38), (1, PH_W + Vector((0.01, -0.06, 0.30)), PH_W + Vector((0, 0.01, 0)), 40)])
# ---------------------------------------------------------------- S4 "without anyone": home screen, nobody near it
crew("S4", "case", Foreman={"head": (14, 0), "head_end": (18, -6), "brow": 0.002}, Digger={"head": (12, 6)}, Mate={"head": (14, -4), "head_end": (8, 10)})
tiles("S4", [(0, 8)])
camshot("S4", [(0, (-3.85, -0.3, 0.95), (-3.62, 1.2, 1.08), 18), (1, (-3.82, -0.2, 0.93), (-3.62, 1.2, 1.1), 18.5)])
# ---------------------------------------------------------------- S5 "touching it ... watch": crew around the case, low front; logo on the case front
crew("S5", "case", Foreman={"hands": ("open", "R"), "head": (2, 0), "spine": 8, "brow": 0.002}, Mate={"hands": ("point", "R"), "head": (4, 0)}, Digger={"head": (0, 0), "head_end": (6, -10)})
tiles("S5", [(0, 8), (1.3, 9)])
camshot("S5", [(0, (-3.75, -2.25, 0.72), (-4.0, 1.0, 1.05), 27), (1, (-3.85, -1.8, 0.7), (-4.0, 1.0, 1.08), 28)])
# ---------------------------------------------------------------- S6 "as it opened apps"
crew("S6", "case")
tiles("S6", [(0, 8), (0.3, 9), (0.8, 10)])
camshot("S6", [(0, PH_W + Vector((0.0, -0.05, 0.25)), PH_W, 42), (1, PH_W + Vector((0.0, -0.04, 0.21)), PH_W, 42)])
# ---------------------------------------------------------------- S7 "snapped screenshots"
crew("S7", "case", Mate={"hands": ("point", "R"), "head": (12, 0)}, Foreman={"head": (14, 0), "brow": 0.003}, Digger={"head": (10, 0), "head_end": (14, 12)})
tiles("S7", [(0, 10), (0.35, 11), (0.45, 13), (1.0, 9), (1.3, 11), (1.4, 12), (2.1, 10)])
camshot("S7", [(0, (-4.15, -0.28, 0.97), (-3.6, 1.2, 1.08), 18), (1, (-4.1, -0.18, 0.95), (-3.6, 1.2, 1.1), 18.5)])
# ---------------------------------------------------------------- S8 "and even tried to call 911 over and over": keypad lights 9-1-1, call
crew("S8", "case")
tiles("S8", [(0, 14), (0.4, 15), (0.65, 14), (0.85, 16), (1.1, 14), (1.3, 16), (1.6, 17), (1.9, 18), (2.15, 19), (2.4, 18), (2.65, 19), (2.9, 18), (3.15, 19), (3.4, 18)])
BUZZ.append((sec("S8", 1.9), fx("S8")))
camshot("S8", [(0, PH_W + Vector((-0.05, -0.08, 0.28)), PH_W, 42), (1, PH_W + Vector((-0.02, -0.05, 0.22)), PH_W, 44)])
# ---------------------------------------------------------------- S9 "again": high over the crew, the phone calling again on the lid
crew("S9", "case", Foreman={"head": (6, 0)}, Mate={"head": (4, 0), "head_end": (0, 20)}, Digger={"head": (4, 0)})
tiles("S9", [(0, 18), (0.25, 19), (0.5, 18), (0.75, 14), (1.0, 16), (1.2, 14), (1.4, 16), (1.6, 17), (1.9, 18), (2.15, 19), (2.4, 18)])
BUZZ.append((f0("S9"), sec("S9", 0.7))); BUZZ.append((sec("S9", 1.9), fx("S9")))
camshot("S9", [(0, (-5.25, -1.35, 1.25), (-4.3, 0.9, 1.1), 28), (1, (-5.1, -1.15, 1.2), (-4.3, 0.9, 1.12), 29)])
# ---------------------------------------------------------------- S10-S13 the pit: full of water, swirls, drains away
for s in ("S10", "S11", "S12", "S13", "S14", "S15", "S16"): crew(s, "watch_exc")
key_water(1, -PD, 0, 0); key_water(f0("S10") - 1, -PD, 0, 0)
LV = [(f0("S10"), -0.12, 0.0), (f0("S11"), -0.2, 0.15), (f0("S12"), -0.55, 0.8), (f0("S13"), -1.25, 1.0), (sec("S13", 1.5), -1.97, 0.4), (f0("S14"), -PD, 0)]
for f in range(f0("S10"), f0("S14") + 1, 2):
    for a, b in zip(LV, LV[1:]):
        if a[0] <= f <= b[0]:
            u = (f - a[0]) / max(1, b[0] - a[0]); z = a[1] + (b[1] - a[1]) * u; v = a[2] + (b[2] - a[2]) * u; break
    sw = (f - f0("S10")) * (0.4 + 3.0 * v)
    key_water(f, z, sw, v)
camshot("S10", [(0, (-6.5, -1.8, 3.9), (0.4, 7.4, -0.4), 26), (1, (-5.6, -0.6, 3.4), (0.3, 7.4, -0.4), 27)])
camshot("S11", [(0, (-2.6, 1.6, 3.0), (0.0, 7.2, -0.6), 26), (1, (-2.1, 2.4, 2.6), (0.0, 7.2, -0.7), 27)])
camshot("S12", [(0, (0.4, 4.4, 5.4), (0.0, 7.0, -1.2), 24), (1, (0.3, 4.9, 4.7), (0.0, 7.0, -1.3), 25)])
camshot("S13", [(0, (-3.2, 1.6, 2.2), (0.0, 7.0, -1.3), 24), (1, (-2.2, 2.2, 5.8), (0.0, 7.0, -1.4), 24)])
# ---------------------------------------------------------------- S14 "without a trace": the empty pit and the dark drain hole
camshot("S14", [(0, (-2.6, 2.3, 2.6), (0.0, 7.0, -2.6), 26), (1, (-1.6, 3.6, 1.7), (0.0, 7.0, -2.8), 28)])
# ---------------------------------------------------------------- S15 "trying to see what was going on": bucket digging in the pit
camshot("S15", [(0, (-5.6, 7.0, 3.7), (2.8, 8.2, 0.3), 34), (1, (-5.1, 7.1, 3.5), (2.8, 8.2, 0.2), 36)])
# ---------------------------------------------------------------- S16 "underneath the ground": cross-section block
XO = Vector((300.0, 0.0, 0.0)); FRONT = -6.0
EXCC = bpy.data.collections["EXCAVATOR"]; EXCC.instance_offset = EXC_POS
XI = OB["XS_excavator"]; XI.location = XO + Vector((EXC_POS.x - PIT.x, FRONT + 2.2 + (EXC_POS.y - PIT.y), 0))
SFLOW = bpy.data.materials["Stream"].node_tree.nodes["Flow"]
SFLOW.inputs["Location"].default_value = (0, 0, 0); SFLOW.inputs["Location"].keyframe_insert("default_value", frame=f0("S16"))
SFLOW.inputs["Location"].default_value = (0, 0, 3.0); SFLOW.inputs["Location"].keyframe_insert("default_value", frame=fx("S16") + 10)
for fc in fcurves_of(bpy.data.materials["Stream"].node_tree.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
camshot("S16", [(0, XO + Vector((-3.0, FRONT - 19.0, -2.6)), XO + Vector((1.0, FRONT, -3.3)), 30), (1, XO + Vector((-1.8, FRONT - 16.5, -2.8)), XO + Vector((1.0, FRONT, -3.6)), 30)])
# ---------------------------------------------------------------- S17 "until the phone": Foreman stares at the phone, then looks up at the Digger
crew("S17", "case", Foreman={"head": (18, 0), "head_end": (-2, -22), "brow": 0.003, "jaw": 1.5, "spine": 10, "spine_end": 4}, Digger={"head": (8, 10)})
tiles("S17", [(0, 20), (0.15, 8), (0.3, 21), (0.45, 20), (0.6, 22)]); JIT.append((f0("S17"), fx("S17")))
camshot("S17", [(0, (-3.9, -0.45, 1.05), (-4.0, 1.32, 1.52), 46), (1, (-3.92, -0.2, 1.08), (-4.0, 1.32, 1.55), 48)])
# ---------------------------------------------------------------- S18-S19 "was going crazy": glitching screen, phone buzzing
for s in ("S18", "S20", "S21"): crew(s, "case", Foreman={"head": (14, 0), "brow": 0.002})
crew("S19", "case", Foreman={"hands": ("open", "R"), "head": (10, 0), "brow": 0.003, "jaw": 1.5}, Digger={"head": (6, 0), "spine": 4, "head_end": (0, -12)}, Mate={"head": (10, 0), "head_end": (4, 14)})
tiles("S18", [(t * 0.12, [20, 21, 8, 22, 20, 9, 21, 22][i % 8]) for i, t in enumerate(range(0, 22))]); JIT.append((f0("S18"), fx("S18"))); BUZZ.append((f0("S18"), fx("S18")))
camshot("S18", [(0, PH_W + Vector((0.03, -0.07, 0.26)), PH_W, 42), (1, PH_W + Vector((0.02, -0.05, 0.22)), PH_W, 44)])
tiles("S19", [(t * 0.1, [22, 20, 14, 21, 22, 18, 20][i % 7]) for i, t in enumerate(range(0, 26))]); JIT.append((f0("S19"), fx("S19"))); BUZZ.append((f0("S19"), fx("S19")))
camshot("S19", [(0, (-3.85, -0.28, 0.97), (-4.4, 1.2, 1.08), 18), (1, (-3.9, -0.18, 0.95), (-4.4, 1.2, 1.1), 18.5)])
# ---------------------------------------------------------------- S20 "it was like something was inside": dark ripple screen, crew behind
tiles("S20", [(0, 23), (0.9, 22), (1.0, 23), (1.8, 21), (1.9, 23)])
camshot("S20", [(0, PH_W + Vector((0.0, -0.04, 0.26)), PH_W, 42), (1, PH_W + Vector((0.0, -0.015, 0.17)), PH_W, 46)])
# ---------------------------------------------------------------- S21 "trying to send": keypad flashes again
tiles("S21", [(0, 14), (0.25, 15), (0.45, 16), (0.65, 16), (0.85, 17), (1.1, 18), (1.35, 19), (1.6, 18)]); BUZZ.append((sec("S21", 1.1), fx("S21")))
camshot("S21", [(0, PH_W + Vector((-0.02, -0.06, 0.25)), PH_W, 42), (1, PH_W + Vector((-0.01, -0.04, 0.21)), PH_W, 44)])
# ---------------------------------------------------------------- S22 "a message": the crew at the pit edge looks down into the hole
crew("S22", "pit")
tiles("S22", [(0, 18)])
camshot("S22", [(0, (-0.6, 12.4, 5.6), (-2.1, 5.0, -0.3), 32), (1, (-0.8, 11.8, 5.2), (-2.1, 5.0, -0.4), 33)])
for s in ("S1", "S2", "S10", "S11", "S12", "S13", "S14", "S15", "S16"): pass
bake_excavator([(1, F["END"], 4.4, 0.0)])

# small camera-only catchlight for the eyes (parented to the camera)
cl = bpy.data.objects.new("Catchlight", bpy.data.lights.new("Catchlight", 'POINT')); sc.collection.objects.link(cl)
cl.data.energy = 6.0; cl.data.shadow_soft_size = 0.08; cl.parent = cam; cl.location = (0.0, 0.12, 0.0); cl.visible_camera = False

PHONE_SHOTS = ("S3", "S6", "S8", "S10", "S11", "S12", "S13", "S14", "S15", "S16", "S18", "S20", "S21")
for s_ in ORDER:
    cl.data.energy = 0.0 if s_ in PHONE_SHOTS else 6.0; cl.data.keyframe_insert("energy", frame=f0(s_))
for fc in fcurves_of(cl.data.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
