"""CH4/CH5 (chat B): a German regional courtroom, Augsburg style (generic: no crest, no names). Light oak panelling,
a raised judges' bench for five, tall windows on the right with a low winter sun raking across, haze.
The defendant is an unnamed figure, seen only from behind or at medium distance.
Variants: trial (2009, ch4), verdict (2010, ch5), civil (2013-18, small hearing), empty (lights going out).
  dock     (A, trial):   from behind the defendant at the defence table while his lawyer stands to speak
  witness  (B, trial):   an elderly market seller in the witness chair shrugs and shakes his head
  bench    (A, verdict): slow push to the bench as the presiding judge turns pages
  exhibit  (B, verdict): a clerk carries bagged binoculars to the exhibit table under the window light
  rise     (A, verdict): wide from the public seats: everyone rises as the judges stand to read
  back     (B, verdict): from behind the defendant standing; heads in the gallery turn
  civil    (A, civil):   a single judge reads the ruling; the claimant seen from behind
  lights   (A, empty):   the emptied room, a clerk stacks files and the lights start going off
  pullback (B, empty):   slow pull back as the last light goes out over the empty bench
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import world_flat, ease
from human import reach, fingers_curl
import ph
import b_common as B
import b_props as P

EXPOSURE = 0.6
DUR = {"dock": 5.0, "witness": 5.0, "bench": 5.5, "exhibit": 5.0, "rise": 5.5, "back": 5.0, "civil": 5.5, "lights": 5.5, "pullback": 5.5}
VARIANT_FOR = {"dock": "trial", "witness": "trial", "bench": "verdict", "exhibit": "verdict", "rise": "verdict", "back": "verdict",
               "civil": "civil", "lights": "empty", "pullback": "empty"}
DAIS_Z = 0.45
BENCH_TOP = DAIS_Z + 0.78
JUDGE_X = (-2.4, -1.2, 0.0, 1.2, 2.4)


def chair(loc, face_z, mat, high=False):
    parts = [box("CSeat", (0, 0, 0.46), (0.5, 0.48, 0.07), mat, bevel=0.02),
             box("CBack", (0, 0.23, 0.8 if not high else 0.95), (0.48, 0.06, 0.6 if not high else 0.95), mat, bevel=0.025),
             cyl("CStem", (0, 0, 0.23), 0.025, 0.42, pbr("ChairSteel", (0.2, 0.2, 0.21), 0.35, 0.9), verts=12),
             box("CFoot", (0, 0, 0.02), (0.55, 0.06, 0.03), pbr("ChairSteel2", (0.2, 0.2, 0.21), 0.35, 0.9)),
             box("CFoot2", (0, 0, 0.02), (0.06, 0.55, 0.03), pbr("ChairSteel3", (0.2, 0.2, 0.21), 0.35, 0.9))]
    o = join(parts, "Chair"); o.location = loc; o.rotation_euler = (0, 0, face_z)
    return o


def table(loc, size, top_m, leg_m, rot_z=0.0, modesty=True):
    w, d, h = size
    parts = [box("TTop", (0, 0, h - 0.02), (w, d, 0.04), top_m, bevel=0.005)]
    for sx in (-1, 1):
        parts.append(box("TSide", (sx * (w / 2 - 0.03), 0, (h - 0.04) / 2), (0.04, d - 0.04, h - 0.04), leg_m))
    if modesty:
        parts.append(box("TModesty", (0, -d / 2 + 0.03, h * 0.55), (w - 0.06, 0.02, h * 0.6), leg_m))
    o = join(parts, "Table"); o.location = loc; o.rotation_euler = (0, 0, rot_z)
    return o


def files_on(loc, n, rng, mats, rot=0.0):
    out = []
    for k in range(n):
        out.append(box("File", (loc[0] + rng.uniform(-0.03, 0.03), loc[1] + rng.uniform(-0.03, 0.03), loc[2] + 0.012 + k * 0.024),
                       (0.24, 0.32, 0.022), mats[k % len(mats)], bevel=0.002, rot=(0, 0, rot + rng.uniform(-0.08, 0.08))))
    return out


def robe(name, gender, years, hair, hv=0.3, val=0.07):
    """Black court robe (judges, prosecutor, counsel)."""
    h = B.person(name, gender, years, "male_elegantsuit01" if gender > 0.5 else "female_elegantsuit01", hair, hair_val=hv)
    B.flat_clothes(h, (0.012, 0.012, 0.014), rough=0.6)
    return h


def civilian(name, gender, years, hair, hv=0.3):
    """Lay judges (Schoeffen) sit in plain civilian clothes."""
    if gender > 0.5:
        h = B.person(name, gender, years, "male_casualsuit05", hair, hair_val=hv)
        B.flat_clothes(h, (0.13, 0.1, 0.07))
    else:
        h = B.person(name, gender, years, "female_elegantsuit01", hair, hue=0.55, sat=0.6, val=0.9, hair_val=hv)
    return h


def build(variant=None):
    variant = variant or "trial"
    c = {"variant": variant}
    rng = np.random.default_rng(10)
    world_flat((0.012, 0.014, 0.018), 1.0)
    oak = B.tex_mat("CourtOak", "oak_veneer_01", scale=0.8, tint=(1.0, 0.86, 0.68))
    oak_dark = B.tex_mat("CourtOakDark", "oak_veneer_01", scale=0.8, tint=(0.42, 0.32, 0.24))
    plaster = B.plaster("CourtPlaster", (0.62, 0.6, 0.56), dirt=0.08)
    floor = B.tex_mat("CourtFloor", "laminate_floor_02", scale=0.4, tint=(0.55, 0.5, 0.45))
    box("Floor", (0, 1, -0.01), (12.4, 15, 0.02), floor)
    # walls: oak panelling to 2.4 m, plaster above
    box("WallBack", (0, 7.55, 2.2), (12.4, 0.1, 4.4), oak)
    box("WallL_pan", (-6.15, 1, 1.2), (0.1, 15, 2.4), oak); box("WallL_up", (-6.18, 1, 3.4), (0.06, 15, 2.0), plaster)
    box("WallFront", (0, -6.5, 2.2), (12.4, 0.1, 4.4), plaster)
    box("Ceiling", (0, 1, 4.42), (12.4, 15, 0.06), B.plaster("CourtCeil", (0.6, 0.6, 0.58)))
    for k in range(12):                                   # vertical panel joints on the back wall
        box("Joint", (-5.5 + k * 1.0, 7.49, 2.2), (0.012, 0.01, 4.4), oak_dark)
    # right wall: three tall windows; a low winter sun rakes across the room
    box("WallR_lo", (6.15, 1, 0.45), (0.1, 15, 0.9), plaster); box("WallR_hi", (6.15, 1, 4.0), (0.1, 15, 0.8), plaster)
    for y in (-6.0, -2.2, 1.6, 5.4):
        box("WallR_pier", (6.15, y + (0.75 if y > 5 else 0), 2.3), (0.1, 1.4 if y < 5 else 2.9, 3.0), plaster)
    fr = pbr("WinFrame", (0.25, 0.25, 0.26), 0.4, 0.6)
    for y0 in (-4.1, -0.3, 3.5):
        for k in range(4):
            box("Mull", (6.12, y0 - 1.2 + k * 0.8, 2.35), (0.06, 0.05, 3.1), fr)
        box("Trans", (6.12, y0, 2.9), (0.06, 2.4, 0.05), fr)
    sky = box("Outside", (9.0, 1, 2.2), (0.05, 18, 7), emissive("CourtSky", (0.85, 0.8, 0.72), 0.22)); sky.visible_shadow = False
    sun_e = {"empty": 6.0}.get(variant, 24.0)
    B.key_sun(14, 30, sun_e, color=(1.0, 0.72, 0.48), angle=0.7)               # from +X (window side), low
    B.fill((-4.5, -4.0, 3.5), (0, 3, 1.2), 30, 4.0, (0.45, 0.58, 0.78))
    B.room_haze((0, 1, 2.2), (12.0, 14.5, 4.3), density=0.008, color=(0.95, 0.93, 0.9))
    # ceiling lights: a row of round pendants (energy driven for the "empty" variant)
    lamp_m = pbr("LampShade", (0.85, 0.84, 0.8), 0.4, **{'Emission Color': (1.0, 0.85, 0.65, 1), 'Emission Strength': 2.5})
    c["lamps"] = []
    for k, (x, y) in enumerate([(x, y) for y in (5.0, 2.0, -1.5, -4.5) for x in (-3.0, 0.0, 3.0)]):
        sh = cyl("Pendant", (x, y, 3.85), 0.28, 0.05, lamp_m, verts=48)
        cyl("PendCord", (x, y, 4.15), 0.006, 0.55, pbr("Cord", (0.05, 0.05, 0.05), 0.5), verts=8)
        l = area_light((x, y, 3.8), (0, 0, 0), 0.5, 28, (1.0, 0.86, 0.68)); l.visible_camera = False
        c["lamps"].append((sh, l, k))
    if variant == "empty":                            # the lights switch off front to back, the bench row last
        order = sorted(range(len(c["lamps"])), key=lambda k: -c["lamps"][k][1].location.y)[::-1]
        for rank, k in enumerate(order):
            sh, l, _ = c["lamps"][k]
            off = 20 + rank * 9 if rank < len(order) - 3 else 95 + (rank - (len(order) - 3)) * 6
            d = l.data.driver_add("energy").driver; d.type = 'SCRIPTED'; d.expression = f"28 * (1 if frame < {off} else 0)"
            m = lamp_m.copy(); sh.data = sh.data.copy(); sh.data.materials.clear(); sh.data.materials.append(m)
            d = m.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].driver_add("default_value").driver
            d.type = 'SCRIPTED'; d.expression = f"2.5 * (1 if frame < {off} else 0)"
    # ------------------------------------------------------------------ the bench
    box("Dais", (0, 6.55, DAIS_Z / 2), (8.4, 2.0, DAIS_Z), oak_dark)
    box("BenchFront", (0, 5.72, (BENCH_TOP - 0.03) / 2), (7.6, 0.08, BENCH_TOP - 0.03), oak, bevel=0.01)
    box("BenchTop", (0, 5.98, BENCH_TOP), (7.8, 0.62, 0.05), oak, bevel=0.005)
    box("BenchSides", (0, 6.0, DAIS_Z + 0.37), (7.6, 0.5, 0.02), oak_dark)
    leather = pbr("Leather", (0.05, 0.035, 0.03), 0.45, **{'Coat Weight': 0.3})
    paper = B.paper_mat("CasePaper", (0.86, 0.85, 0.8)); manila = pbr("Manila", (0.62, 0.5, 0.3), 0.8); red = pbr("RedFile", (0.4, 0.08, 0.06), 0.7)
    for x in JUDGE_X:
        if variant == "civil" and x != 0:                  # a small civil court: a single judge, one chair
            continue
        chair((x, 6.75, DAIS_Z), 0.0, leather, high=True)
        files_on((x + 0.25, 5.95, BENCH_TOP + 0.025), 3 if x != 0 else 5, rng, [manila, red, paper])
    c["page"] = B.sheet("TurnPage", (0, 0, -20), (0.21, 0.297), paper)
    c["open_file"] = box("OpenFile", (-0.15, 5.98, BENCH_TOP + 0.035), (0.44, 0.31, 0.02), manila, bevel=0.002)
    # ------------------------------------------------------------------ the floor of the court
    table_m = oak
    table((-3.9, 2.4, 0), (0.8, 3.0, 0.76), table_m, oak_dark, rot_z=0, modesty=False)   # defence (left), long along y
    box("DefModesty", (-3.52, 2.4, 0.42), (0.02, 2.9, 0.5), oak_dark)
    table((3.9, 2.4, 0), (0.8, 3.0, 0.76), table_m, oak_dark, modesty=False)            # prosecution (right)
    box("ProModesty", (3.52, 2.4, 0.42), (0.02, 2.9, 0.5), oak_dark)
    table((0, 2.9, 0), (1.1, 0.6, 0.76), table_m, oak_dark)                              # witness table (faces the bench)
    c["exhibit_table"] = table((2.0, 4.6, 0), (1.2, 0.6, 0.8), table_m, oak_dark)       # exhibits under the window
    box("Barrier", (0, -0.6, 0.5), (11.0, 0.08, 1.0), oak_dark)
    for k in range(5):
        for x in (-3.0, 3.0):
            box("Pew", (x, -1.6 - k * 1.05, 0.23), (5.0, 0.42, 0.46), oak, bevel=0.01)
            box("PewBack", (x, -1.6 - k * 1.05 - 0.2, 0.68), (5.0, 0.05, 0.5), oak, bevel=0.01)
    for y in (1.5, 2.4, 3.3):
        files_on((-3.85, y, 0.76), 2, rng, [manila, paper], rot=1.57)
        files_on((3.85, y, 0.76), 2, rng, [red, paper], rot=1.57)
    # the bagged binoculars (evidence bag: clear, with a white label strip)
    bag_m = pbr("EvBag", (0.9, 0.92, 0.95), 0.15, **{'Transmission Weight': 0.85, 'IOR': 1.4})
    r, ms = ph.model("binoculars", loc=(0, 0, 0))
    bag = box("EvBagBox", (0, 0.08, 0.035), (0.24, 0.36, 0.08), bag_m, bevel=0.02)
    lab = box("EvLabel", (0, -0.06, 0.077), (0.18, 0.06, 0.002), pbr("EvLabelW", (0.92, 0.92, 0.9), 0.7))
    ev = bpy.data.objects.new("Exhibit", None); bpy.context.collection.objects.link(ev)
    for o in (r, bag, lab):
        o.parent = ev
    c["exhibit"] = ev
    ev.location = (2.0, 4.6, 0.8) if variant != "verdict" else (0, 0, -30)
    # ------------------------------------------------------------------ people
    c["people"] = {}
    P_ = c["people"]
    def judge(nm, x, g, yrs, hair):
        h = (civilian if nm.startswith("Lay") else robe)(nm, g, yrs, hair, hv=0.3 if yrs < 55 else 1.4)
        B.seat(h, (x, 6.62, 0), 0.0, lean=4); B.ground(h, DAIS_Z + 0.1)
        h.arm.location.z = h.arm.location.z           # seated on the dais
        P_[nm] = h; return h
    if variant in ("trial", "verdict"):
        judge("Presiding", 0.0, 1.0, 58, "short02")
        judge("JudgeL", -1.2, 0.0, 44, "bob01")
        judge("JudgeR", 1.2, 1.0, 50, "short04")
        judge("LayL", -2.4, 0.0, 61, "bob02")
        judge("LayR", 2.4, 1.0, 39, "short03")
        dfn = B.mazurek("Defendant", 2009)
        B.seat(dfn, (-4.45, 2.0, 0), math.pi / 2, lean=6)              # faces +X, across the court
        chair((-4.53, 2.0, 0), math.pi / 2, leather)
        P_["defendant"] = dfn
        law = robe("Lawyer", 1.0, 52, "short04", hv=0.35)
        P_["lawyer"] = law
        if variant == "trial":
            B.stand(law, (-4.3, 2.9, 0), math.pi / 2)                  # standing to address the court
        else:
            B.seat(law, (-4.45, 2.9, 0), math.pi / 2, lean=6)
        chair((-4.53, 2.95, 0), math.pi / 2, leather)
        pro = robe("Prosecutor", 0.0, 47, "ponytail01", hv=0.3)
        B.seat(pro, (4.45, 2.6, 0), -math.pi / 2, lean=8); chair((4.53, 2.6, 0), -math.pi / 2, leather)
        P_["prosecutor"] = pro
        # the public: reporters and family in the first rows
        gal = [(-4.2, -1.75, 1.0, 34, "male_casualsuit01", "short01"), (-2.9, -1.75, 0.0, 41, "female_elegantsuit01", "long01"),
               (-1.7, -1.75, 1.0, 29, "male_casualsuit03", "short03"), (1.6, -1.75, 0.0, 52, "female_elegantsuit01", "bob01"),
               (2.9, -1.75, 1.0, 45, "male_casualsuit05", "short04"), (4.1, -1.75, 1.0, 60, "male_elegantsuit01", "short02"),
               (-3.5, -2.8, 0.0, 38, "female_elegantsuit01", "ponytail01"), (-1.2, -2.8, 1.0, 50, "male_casualsuit01", "short02"),
               (2.2, -2.8, 1.0, 33, "male_casualsuit03", "short01"), (3.8, -2.8, 0.0, 27, "female_elegantsuit01", "bob02")]
        for k, (x, y, g, yrs, cl, hr) in enumerate(gal):
            h = B.person(f"Pub{k}", g, yrs, cl, hr, hue=0.5 + 0.05 * (k % 3), sat=0.5, val=0.3 + 0.08 * (k % 3), hair_val=0.2 + 0.1 * (k % 4))
            B.seat(h, (x, y + 0.08, 0), math.pi, lean=4)
            P_[f"pub{k}"] = h
    if variant == "trial":
        wit = B.person("Witness", 1.0, 72, "male_casualsuit05", "short02", hue=0.08, sat=0.4, val=0.35, hair_val=3.0, hair_sat=0.0)
        B.seat(wit, (0, 2.32, 0), math.pi, lean=6); chair((0, 2.24, 0), math.pi, leather)
        P_["witness"] = wit
    if variant == "verdict":
        clerk = B.person("Clerk", 0.0, 35, "female_elegantsuit01", "ponytail01", hue=0.55, sat=0.3, val=0.25, hair_val=0.3)
        B.stand(clerk, (3.2, 3.4, 0), math.pi); P_["clerk"] = clerk
        c["carry"] = ev
    if variant == "civil":
        j = robe("CivilJudge", 0.0, 55, "ponytail01", hv=1.4)
        B.key_spot((-1.6, 3.4, 3.4), (0.0, 6.55, DAIS_Z + 1.15), 260, 30, (1.0, 0.9, 0.78), soft=0.4, name="JudgeFace")
        B.seat(j, (0.0, 6.62, 0), 0.0, lean=4); B.ground(j, DAIS_Z + 0.1); P_["Presiding"] = j
        cl = B.michael("Claimant", 51)
        B.seat(cl, (-0.35, 2.32, 0), math.pi, lean=8); chair((-0.35, 2.24, 0), math.pi, leather); P_["claimant"] = cl
        law = robe("CivLawyer", 1.0, 50, "short02", hv=0.4)
        B.seat(law, (0.45, 2.32, 0), math.pi, lean=8); chair((0.45, 2.24, 0), math.pi, leather); P_["civlaw"] = law
    if variant == "empty":
        clerk = B.person("Clerk", 1.0, 30, "male_casualsuit01", "short03", hue=0.6, sat=0.3, val=0.45, hair_val=0.25)
        B.stand(clerk, (-3.9, 3.35, 0), -math.pi / 2); P_["clerk"] = clerk   # faces -X ... at the defence table end
    c["rest"] = {k: B.capture(h) for k, h in P_.items()}
    if variant == "verdict":                            # standing versions for the "rise" shot
        c["standp"] = {}
        for k, h in P_.items():
            if k == "clerk":
                continue
            P0 = c["rest"][k]
            fz = P0["rot"].z; loc = P0["loc"]
            fwd = Vector((math.sin(fz), -math.cos(fz), 0))
            B.stand(h, (loc.x + fwd.x * 0.15, loc.y + fwd.y * 0.15, 0), fz, z=DAIS_Z + 0.0 if k in ("Presiding", "JudgeL", "JudgeR", "LayL", "LayR") else 0.0)
            c["standp"][k] = B.capture(h)
            B.apply_pose(h, P0)
    B.finish_interior(lift=-0.2)
    return c


# ============================================================================ animation
def turn_page(c, h, sec, at=1.2):
    """The presiding judge turns a page of the open file (hands at medium distance)."""
    f = c["open_file"]; base = f.location + Vector((0, 0, 0.012))
    u = ease(min(1.0, max(0.0, (sec - at) / 1.1)))
    # the judge faces -Y, so her right hand is on -X: the page flips from her right (-X) over to her left (+X)
    pg = c["page"]
    pg.rotation_mode = 'XYZ'; pg.rotation_euler = (0, math.pi * u, 0)
    pg.location = base + Vector((-0.11 * math.cos(math.pi * u), 0, 0.11 * math.sin(math.pi * u) + 0.001))
    tip = base + Vector((-0.2 * math.cos(math.pi * u), -0.08, 0.04 + 0.12 * math.sin(math.pi * u)))
    back = ease(min(1.0, max(0.0, (sec - at - 1.1) / 0.6)))   # after the turn the right hand returns to rest
    tip = tip.lerp(base + Vector((-0.26, -0.14, 0.02)), back)
    reach(h, "R", tip, Vector((-0.6, -0.4, -0.6)), Vector((0, -1, -0.6)))
    reach(h, "L", base + Vector((0.34, -0.12, 0.02)), Vector((0.6, -0.4, -0.6)), Vector((0, -1, -0.6)))
    B.curl(h, 25, thumb=10)
    B.nod(h, 14)


def desk_hands(h, desk_y, sec, ph_=0.0, top=0.76, spread=0.18):
    fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    sh = h.bone_head("spine01")
    base = Vector((sh.x, sh.y, top + 0.04)) + fwd * 0.42
    for sd, sg in (("L", -1), ("R", 1)):
        reach(h, sd, base + side * (spread * sg) + Vector((0, 0, 0.005 * math.sin(sec + ph_))), Vector((sg * side.x, sg * side.y, -0.8)), fwd + Vector((0, 0, -0.3)))
    B.curl(h, 30, thumb=10)


def idle(c, sec):
    P_ = c["people"]
    for k, (nm, h) in enumerate(P_.items()):
        if nm.startswith("pub"):
            h.rot("head", (0, 0, 1), 4 * math.sin(sec * 0.4 + k))
            B.arms_down(h) if False else None
        elif nm in ("JudgeL", "JudgeR", "LayL", "LayR", "prosecutor"):
            desk_hands(h, 0, sec, k, top=BENCH_TOP if nm != "prosecutor" else 0.76)
            B.nod(h, 10 + 2 * math.sin(sec * 0.5 + k))


def anim(c, t, move):
    sec = t * DUR[move]
    P_ = c["people"]; v = c["variant"]
    for k, h in P_.items():
        B.apply_pose(h, c["rest"][k])
    idle(c, sec)
    if "Presiding" in P_:
        if move == "civil":                                 # the civil judge reads with her hands resting on the bench
            desk_hands(P_["Presiding"], 0, sec, 0.0, top=BENCH_TOP, spread=0.2); B.nod(P_["Presiding"], 14)
        else:
            turn_page(c, P_["Presiding"], sec, at=1.0 if move == "bench" else 99)
    if v == "trial":
        law = P_["lawyer"]
        fwd = B.fwd_of(law)
        reach(law, "R", law.bone_head("spine01") + fwd * 0.38 + Vector((0, 0, 0.12 + 0.05 * math.sin(sec * 1.3))), Vector((0.2, -0.8, -0.6)), fwd)
        B.curl(law, 20, side=("R",)); law.rot("head", (0, 0, 1), 8 * math.sin(sec * 0.5))
        dfn = P_["defendant"]; desk_hands(dfn, 0, sec, 0.3); B.nod(dfn, 6)
        w = P_["witness"]
        if move == "witness":
            desk_hands(w, 0, sec, 0.0, spread=0.16)
            sh = math.sin(math.pi * min(1.0, max(0.0, (sec - 1.4) / 1.2)))
            B.shrug(w, sh)
            w.rot("head", (0, 0, 1), 14 * math.sin(max(0.0, sec - 2.6) * 3.2) * (1 if 2.6 < sec < 4.4 else 0))
        else:
            desk_hands(w, 0, sec, 0.0, spread=0.16)
    if v == "verdict":
        cl = P_["clerk"]
        if move == "exhibit":
            u = ease(min(1.0, sec / (DUR["exhibit"] * 0.8)))
            p0 = Vector((3.4, 3.0)); p1 = Vector((2.35, 4.2))
            B.walk_to(cl, (p0.x, p0.y, 0), (p1.x, p1.y, 0), u, 3.0 * u + 0.001, stride=18, swing=0)
            fwd = B.fwd_of(cl)
            hold = cl.bone_head("spine02") + fwd * 0.34 + Vector((0, 0, -0.1 - 0.05 * u))
            side = fwd.cross(Vector((0, 0, 1))).normalized()
            for sd, sg in (("L", -1), ("R", 1)):
                reach(cl, sd, hold + side * 0.12 * sg, Vector((sg * side.x, sg * side.y, -0.7)), fwd)
            B.curl(cl, 35, thumb=20)
            ev = c["exhibit"]; ev.location = hold + Vector((0, 0, 0.0)) if u < 0.98 else Vector((2.0, 4.6, 0.8))
            ev.rotation_euler = (0, 0, math.atan2(fwd.y, fwd.x) - math.pi / 2)
            if u >= 0.98:
                ev.location = Vector((2.0, 4.6, 0.8)); ev.rotation_euler = (0, 0, 0)
        else:
            c["exhibit"].location = (2.0, 4.6, 0.8); c["exhibit"].rotation_euler = (0, 0, 0)
            B.hide_person(cl) if move in ("rise", "back") else None
        if move in ("rise", "back"):
            u = ease(min(1.0, max(0.0, (sec - (0.6 if move == "rise" else 0.0)) / 1.6))) if move == "rise" else 1.0
            for k, h in P_.items():
                if k in c["standp"]:
                    B.blend_pose(h, c["rest"][k], c["standp"][k], u)
            if move == "back":
                for k, h in P_.items():
                    if k.startswith("pub"):
                        h.rot("head", (0, 0, 1), (18 if int(k[3:]) % 2 else -14) * ease(min(1.0, max(0.0, (sec - 1.0 - 0.15 * int(k[3:])) / 0.8))))
    if v == "civil":
        jd = P_["Presiding"]                                # reads the ruling, then looks up to the room
        B.nod(jd, -16 * ease(min(1.0, max(0.0, (sec - 2.4) / 0.9))))
        for k in ("claimant", "civlaw"):
            desk_hands(P_[k], 0, sec, 0.5 if k == "civlaw" else 0.0, spread=0.15)
        B.nod(P_["claimant"], 6)
    if v == "empty":
        cl = P_["clerk"]
        fwd = B.fwd_of(cl); side = fwd.cross(Vector((0, 0, 1))).normalized()
        base = Vector((-3.95, 3.35, 0.8 + 0.06 * abs(math.sin(sec * 1.2))))
        for sd, sg in (("L", -1), ("R", 1)):
            reach(cl, sd, base + side * 0.12 * sg, Vector((sg * side.x, sg * side.y, -0.7)), fwd + Vector((0, 0, -0.4)))
        B.curl(cl, 30); B.nod(cl, 18)
        if move == "pullback":
            B.hide_person(cl)
    bpy.context.view_layer.update()


# ============================================================================ cameras
def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


MOVES = {
    "dock": dict(kind="anim", dof=2.8, cam=cam((-5.6, 0.9, 1.45), (-5.45, 1.3, 1.42), (-3.6, 3.2, 1.05), 32),
                 anim=lambda c, t: anim(c, t, "dock"), focus=lambda c, t: c["people"]["lawyer"].bone_head("head")),
    "witness": dict(kind="anim", dof=2.8, cam=cam((1.4, 4.4, 1.55), (1.2, 4.2, 1.5), (0.0, 2.3, 1.15), 45),
                    anim=lambda c, t: anim(c, t, "witness"), focus=lambda c, t: c["people"]["witness"].bone_head("head")),
    "bench": dict(kind="anim", dof=None, title=("CHAPTER 5", "After the Verdict", 8, 96), cam=cam((0.6, -0.4, 1.55), (0.4, 2.0, 1.75), (0.0, 6.4, 1.75), 32),
                  anim=lambda c, t: anim(c, t, "bench"), focus=lambda c, t: c["people"]["Presiding"].bone_head("head")),
    "exhibit": dict(kind="anim", dof=3.2, cam=cam((-0.2, 2.2, 1.6), (0.1, 2.5, 1.55), (2.3, 4.2, 1.05), 35),
                    anim=lambda c, t: anim(c, t, "exhibit"), focus=lambda c, t: c["exhibit"].matrix_world.translation),
    "rise": dict(kind="anim", dof=5.6, cam=cam((0.0, -5.8, 1.9), (0.0, -5.2, 1.85), (0.0, 4.0, 1.6), 28),
                 anim=lambda c, t: anim(c, t, "rise"), focus=lambda c, t: Vector((0, 4.0, 1.4))),
    "back": dict(kind="anim", dof=2.8, cam=cam((-5.6, 0.6, 1.75), (-5.5, 1.0, 1.72), (-1.5, 3.0, 1.5), 35),
                 anim=lambda c, t: anim(c, t, "back"), focus=lambda c, t: c["people"]["defendant"].bone_head("head")),
    "civil": dict(kind="anim", dof=3.2, cam=cam((-0.35, 0.5, 1.66), (-0.35, 1.2, 1.66), (0.0, 6.4, 1.55), 40),
                  anim=lambda c, t: anim(c, t, "civil"), focus=lambda c, t: c["people"]["Presiding"].bone_head("head")),
    "lights": dict(kind="anim", dof=4.0, cam=cam((4.6, -3.0, 2.3), (4.3, -2.6, 2.25), (-1.5, 4.0, 1.0), 28),
                   anim=lambda c, t: anim(c, t, "lights"), focus=lambda c, t: Vector((-3.9, 3.35, 1.0))),
    "pullback": dict(kind="anim", dof=5.6, cam=cam((0.0, 0.5, 1.8), (0.0, -4.5, 2.1), (0.0, 6.0, 1.5), 30),
                     anim=lambda c, t: anim(c, t, "pullback"), focus=lambda c, t: Vector((0, 6.0, 1.3))),
}
