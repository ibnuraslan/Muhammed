"""Chat B storyboard v2: evidence as the subject. Object-on-black and fact-in-the-set shots (no hands, no faces).
  tape     3-2A  the tape strip on a lightbox; powder drifts down and the fingerprint surfaces by itself
  cards    3-2B  pull back from the print card over a field of 20,000 fingerprint cards; "≈ 20,000" on the floor
  compare  3-3A  comparison viewer: the tape print fixed, card prints slide past on the right, faster; none locks
  soil     3-7B  soil section on black: the hole cuts itself out, a folding rule and a rod measure it, a box settles in
  boxmarks 4-1A  the box on black, slow orbit, numbered evidence tents rise at the sampling spots (title)
  string / nolink  4-2A/B  screw bag and glass bag far apart; a red thread draws between them, then sags and drops
  timeline 4-4   31 year blocks 1981..2011 along the floor; a marker slides to 2007; the last blocks turn red
  reels    4-9B  three call tapes; behind each a row of aluminium bars rises as the jingle's envelope; one peak sinks
  lineup / chosen  4-10A/B  eleven recorders in a line-up before a height-line wall; spots click on; all but one go dark
  chain / clicks   4-14 long take + 4-16C  the court's equipment chain on one long table, a pulse running down the cable
  exhibits 5-1B  exhibit table: the struck statement, the binoculars, the letters, a soldering iron, the Grundig land in turn
  days56   5-2C  fifty-six hearing-day folders in a row
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import ease, point_at, area_light
import b_common as B
import b_fx as F
import b_props as P

EXPOSURE = 0.0
DUR = {"tape": 5.0, "cards": 7.0, "compare": 5.0, "soil": 6.0, "boxmarks": 7.0, "string": 5.0, "nolink": 5.0,
       "timeline": 7.0, "reels": 6.0, "lineup": 6.0, "chosen": 5.0, "chain": 45.0, "clicks": 7.0, "exhibits": 8.0, "days56": 6.0}
VARIANT_FOR = {**{m: m for m in DUR}, "nolink": "string", "chosen": "lineup", "clicks": "chain"}
TZ = 0.9                                   # working surface height


def lightbox(name, loc, w, d, glow=0.45):
    x, y, z = loc
    frame = pbr(name + "Frame", (0.08, 0.08, 0.085), 0.4, 0.5)
    box(name + "Case", (x, y, z - 0.04), (w + 0.06, d + 0.06, 0.08), frame, bevel=0.006)
    return box(name + "Panel", (x, y, z + 0.001), (w, d, 0.002), emissive(name + "Lit", (1.0, 0.96, 0.88), glow))


def bench(loc=(0, 0, 0), size=(1.6, 0.9), top=TZ - 0.08):
    box("Bench", (loc[0], loc[1], top / 2), (size[0], size[1], top), pbr("BenchDark", (0.035, 0.035, 0.038), 0.45), bevel=0.01)


def build(variant=None):
    variant = variant or "tape"
    c = {"variant": variant}
    rng = np.random.default_rng(3)
    if variant in BUILDERS:
        BUILDERS[variant](c, rng)
        return c
    if variant == "tape":
        F.void_stage(c, top=(0.5, -0.4, 2.4), target=(0, 0, TZ), energy=20, size=0.5, radius=2.0)
        bench()
        lightbox("LB", (0, 0, TZ), 0.5, 0.36)
        m = F.print_mat("TapeM", 0, base=(0.82, 0.66, 0.38), ink_col=(0.06, 0.05, 0.04), aspect=4.0, zoom=1.15)
        p = m.node_tree.nodes["Principled BSDF"]; p.inputs['Emission Color'].default_value = (1.0, 0.8, 0.5, 1)
        p.inputs['Emission Strength'].default_value = 0.08; p.inputs['Roughness'].default_value = 0.25
        tape = F.card_plane("TapeStrip", (0, 0, TZ + 0.004), 0.24, 0.06, m)
        c["reveal"] = m.node_tree.nodes["Reveal"].inputs[1]
        # fold-over tab and a second, plain strip (as lifted from the box)
        box("TapeTab", (0.125, 0, TZ + 0.005), (0.012, 0.06, 0.002), pbr("Tab", (0.86, 0.84, 0.78), 0.8))
        # powder motes: fine grey grains above the strip (positions advanced in anim)
        import bmesh
        from mathutils import Matrix
        c["motes0"] = [(rng.uniform(-0.13, 0.13), rng.uniform(-0.05, 0.05), rng.uniform(0.0, 0.25), rng.uniform(0.006, 0.02)) for _ in range(260)]
        bm = bmesh.new()
        for (x, y, z, _) in c["motes0"]:
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0008, matrix=Matrix.Translation((x, y, z)))
        me = bpy.data.meshes.new("Motes"); bm.to_mesh(me); bm.free()
        mo = bpy.data.objects.new("Motes", me); bpy.context.collection.objects.link(mo)
        mo.data.materials.append(pbr("Powder", (0.5, 0.5, 0.52), 0.8)); mo.location = (0, 0, TZ + 0.01)
        c["motes"] = mo
        B.key_spot((0.6, -0.5, 1.6), (0, 0, TZ), 35, 22, (1.0, 0.86, 0.68), soft=0.05, name="Lamp")
    elif variant == "cards":
        F.void_stage(c, top=(0, 0, 9.0), target=(0, 0, 0), energy=0.0, size=1.0, radius=9.0, warm=False)
        B.key_spot((0, -1.0, 11.0), (0, 0.5, 0), 6000, 62, (0.95, 0.95, 1.0), soft=0.3, blend=1.0, name="FieldSpot")
        cols, rows = 140, 146                                      # ≈ 20,000 cards around the aisle
        pw, ph_ = 0.12, 0.17
        cw, ch = 0.09, 0.13
        verts, faces, uvs, mats = [], [], [], []
        for j in range(rows):
            for i in range(cols):
                x = (i - cols / 2) * pw + rng.uniform(-0.006, 0.006); y = (j - rows / 2) * ph_ + rng.uniform(-0.006, 0.006)
                if abs(x) < 0.5 and 0.6 < y < 5.5:
                    continue                                       # an aisle through the field, the count painted on its floor
                a = rng.uniform(-0.05, 0.05); ca, sa = math.cos(a), math.sin(a)
                k = len(verts)
                for (u, v) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    dx, dy = u * cw / 2, v * ch / 2
                    verts.append((x + dx * ca - dy * sa, y + dx * sa + dy * ca, 0.002))
                faces.append((k, k + 1, k + 2, k + 3)); uvs.append(((0, 0), (1, 0), (1, 1), (0, 1)))
                mats.append(int(rng.integers(0, 4)))
        me = bpy.data.meshes.new("Cards"); me.from_pydata(verts, [], faces); me.update()
        uvl = me.uv_layers.new(name="UVMap")
        for fi, f in enumerate(me.polygons):
            for li, lo in enumerate(f.loop_indices):
                uvl.data[lo].uv = uvs[fi][li]
            f.material_index = mats[fi]
        cards = bpy.data.objects.new("Cards", me); bpy.context.collection.objects.link(cards)
        for s in range(4):
            cards.data.materials.append(F.print_mat(f"Card{s}", s + 1))
        # the tape print's card in the middle, raised a little, with a thin red frame
        mid = F.card_plane("TapeCard", (0, 0, 0.004), 0.09, 0.13, F.print_mat("TapeCardM", 0, base=(0.95, 0.92, 0.82)))
        for (dx, dy, sx, sy) in ((0, 0.067, 0.1, 0.004), (0, -0.067, 0.1, 0.004), (0.047, 0, 0.004, 0.138), (-0.047, 0, 0.004, 0.138)):
            box("RedFrame", (dx, dy, 0.005), (sx, sy, 0.001), F.ink("RedF", F.BRICK, 0.6))
        c["fact"] = F.fact_text("Count", "≈ 20,000", (0, 3.0, 0.004), 0.32, color=(0.82, 0.8, 0.74), rot=(0, 0, math.radians(90)))   # floor paint along the aisle
        B.key_spot((0, -0.4, 1.4), (0, 0, 0), 30, 30, (1.0, 0.9, 0.75), soft=0.2, name="CardKey")
    elif variant == "compare":
        F.void_stage(c, top=(0.3, -0.5, 2.4), target=(0, 0, TZ), energy=15, size=0.6, radius=2.0)
        bench()
        lightbox("LB", (0, 0, TZ), 0.62, 0.3)
        box("Divider", (0, 0, TZ + 0.003), (0.004, 0.3, 0.002), pbr("Div", (0.05, 0.05, 0.05), 0.5))
        F.card_plane("Left", (-0.15, 0, TZ + 0.004), 0.18, 0.24, F.print_mat("LeftM", 0, base=(0.95, 0.92, 0.82)))
        for (dx, dy, sx, sy) in ((0, 0.124, 0.192, 0.006), (0, -0.124, 0.192, 0.006), (0.094, 0, 0.006, 0.254), (-0.094, 0, 0.006, 0.254)):
            box("RedFrame", (-0.15 + dx, dy, TZ + 0.005), (sx, sy, 0.001), F.ink("RedF", F.BRICK, 0.6))
        c["right"] = [F.card_plane(f"Right{k}", (5, 0, -5), 0.18, 0.24, F.print_mat(f"RightM{k}", k + 1, base=(0.95, 0.92, 0.82))) for k in range(7)]
        # a tray edge at the right where the cards come from and go to
        box("Mask", (0.33, 0, TZ + 0.01), (0.04, 0.34, 0.02), pbr("MaskM", (0.08, 0.08, 0.085), 0.4))
        B.key_spot((0.3, -0.6, 1.6), (0, 0, TZ), 15, 25, (1.0, 0.88, 0.7), soft=0.1, name="Lamp")
    return c


def anim(c, t, move):
    sec = t * DUR[move]; v = c["variant"]
    if v in BUILDERS:
        return anim_v2(c, t, move)
    if v == "tape":
        c["reveal"].default_value = ease(min(1.0, max(0.0, (sec - 0.6) / 3.2)))
        mo = c["motes"]; sp = mo.data.vertices
        # whole cloud drifts down slowly and settles: simple per-frame offset of the object, plus a slight sway
        mo.location = (0.004 * math.sin(sec * 0.9), 0.003 * math.cos(sec * 0.7), TZ + 0.01 + max(0.0, 0.18 - 0.05 * sec))
    elif v == "cards":
        pass
    else:
        k = 0; acc = 0.0; rate = 1.2 + 4.0 * t * t           # cards per second, accelerating
        pos = sec * (1.2 + 2.0 * t * t)
        k = int(pos); f = pos - k
        for i, o in enumerate(c["right"]):
            o.location = (5, 0, -5)
        cur = c["right"][k % len(c["right"])]; nxt = c["right"][(k + 1) % len(c["right"])]
        slide = ease(min(1.0, f / 0.35))
        cur.location = (0.15 - 0.4 * slide if f > 0.65 else 0.15, 0, TZ + 0.004)
        if f > 0.65:
            u = ease((f - 0.65) / 0.35)
            cur.location = (0.15 - 0.0 * u + 0.4 * u, 0, TZ + 0.004)   # leaves to the right
            nxt.location = (0.55 - 0.4 * u, 0, TZ + 0.0045)              # next arrives
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens, tgt2=None):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt).lerp(Vector(tgt2 or tgt), ease(t)), lens)


def _orbit(center, r, h, a0, a1, lens):
    def f(c, t):
        a = math.radians(a0 + (a1 - a0) * ease(t))
        return (Vector((center[0] + r * math.sin(a), center[1] - r * math.cos(a), h)), Vector(center), lens)
    return f


def cam_chain(c, t):
    """45 s: a slow lateral dolly down the table at station height, a step ahead of the pulse."""
    st = c["st"]; e = t
    x = -4.1 + 8.0 * (0.04 + 0.92 * e)
    xt = x + 0.55
    return (Vector((x - 0.4, -2.05 + 0.15 * math.sin(e * math.pi), TZ + 0.85)), Vector((xt, 0.1, TZ + 0.1)), 30)


MOVES = {
    "tape": dict(kind="anim", dof=4.0, cam=cam((0.28, -0.42, TZ + 0.42), (0.14, -0.22, TZ + 0.24), (0, 0, TZ), 50),
                 anim=lambda c, t: anim(c, t, "tape"), focus=lambda c, t: Vector((0, 0, TZ))),
    "cards": dict(kind="anim", dof=None, cam=lambda c, t: (Vector((0.0, -0.25 - 3.4 * ease(t), 0.5 + 6.5 * ease(t) ** 1.2)),
                                                         Vector((0, 1.2 * ease(t), 0)), 32),
                  anim=lambda c, t: anim(c, t, "cards")),
    "soil": dict(kind="anim", dof=None, cam=cam((0.35, -3.1, 1.25), (0.2, -2.7, 1.15), (0.05, 0, 0.62), 35), anim=lambda c, t: anim(c, t, "soil")),
    "boxmarks": dict(kind="anim", dof=None, title=("CHAPTER 4", "The Clicks", 8, 96), cam=_orbit((0, 0, 0.6), 3.6, 1.75, -60, -20, 32),
                     anim=lambda c, t: anim(c, t, "boxmarks")),
    "string": dict(kind="anim", dof=4.0, cam=cam((-0.1, -1.6, TZ + 0.7), (0.0, -1.35, TZ + 0.6), (0, 0.05, TZ + 0.03), 35),
                   anim=lambda c, t: anim(c, t, "string"), focus=lambda c, t: Vector((0, 0.05, TZ))),
    "nolink": dict(kind="anim", dof=4.0, cam=cam((0.0, -1.35, TZ + 0.6), (0.2, -1.5, TZ + 0.65), (0.1, 0.05, TZ + 0.03), 35),
                   anim=lambda c, t: anim(c, t, "nolink"), focus=lambda c, t: Vector((0, 0.05, TZ))),
    "timeline": dict(kind="anim", dof=2.8, cam=lambda c, t: (Vector((0.85, -0.6 + 6.2 * ease(t), 0.42)), Vector((0.0, 0.6 + 6.2 * ease(t), 0.03)), 32),
                     anim=lambda c, t: anim(c, t, "timeline"), focus=lambda c, t: c["marker"].location),
    "reels": dict(kind="anim", dof=None, cam=cam((0.9, -1.45, 0.75), (0.7, -1.2, 0.68), (-0.15, 0.55, 0.15), 30), anim=lambda c, t: anim(c, t, "reels")),
    "lineup": dict(kind="anim", dof=None, cam=lambda c, t: (Vector((-2.6 + 5.2 * ease(t), -2.6, 1.2)), Vector((-2.6 + 5.2 * ease(t), 0.5, 0.9)), 30),
                   anim=lambda c, t: anim(c, t, "lineup")),
    "chosen": dict(kind="anim", dof=2.8, cam=cam((0.0, -3.6, 1.3), (0.0, -1.4, 0.95), (0.0, 0.3, 0.75), 32),
                   anim=lambda c, t: anim(c, t, "chosen"), focus=lambda c, t: Vector((0.0, 0.2, 0.6))),
    "chain": dict(kind="anim", dof=None, cam=cam_chain, anim=lambda c, t: anim(c, t, "chain"),
                  focus=lambda c, t: Vector((-4.1 + 8.0 * (0.04 + 0.92 * t) + 0.55, 0.1, TZ + 0.1))),
    "clicks": dict(kind="anim", dof=None, cam=cam((0.0, -3.4, TZ + 3.2), (0.0, -3.0, TZ + 2.9), (0.0, 0.0, TZ), 30), anim=lambda c, t: anim(c, t, "clicks")),
    "exhibits": dict(kind="anim", dof=4.0, cam=cam((0.0, -1.3, TZ + 0.85), (0.0, -1.05, TZ + 0.72), (0.0, 0.0, TZ), 35),
                     anim=lambda c, t: anim(c, t, "exhibits"), focus=lambda c, t: Vector((0, 0, TZ))),
    "days56": dict(kind="anim", dof=2.8, cam=lambda c, t: (Vector((0.55, -0.6 + 6.0 * ease(t), TZ + 0.45)), Vector((0.0, 0.6 + 6.0 * ease(t), TZ + 0.15)), 32),
                   anim=lambda c, t: anim(c, t, "days56")),
    "compare": dict(kind="anim", dof=5.6, cam=cam((0.05, -0.55, TZ + 0.55), (0.03, -0.4, TZ + 0.42), (0, 0, TZ), 40),
                    anim=lambda c, t: anim(c, t, "compare"), focus=lambda c, t: Vector((0, 0, TZ))),
}


# =========================================================================================== v2 builders (Ch3-5)
def _drop(o, u, h=0.25):
    """Land an object from just above its home position (u 0..1)."""
    if "home" not in o:
        o["home"] = tuple(o.location)
    hm = Vector(o["home"]); e = ease(max(0.0, min(1.0, u)))
    o.hide_render = u <= 0.0
    for ch in o.children_recursive:
        ch.hide_render = u <= 0.0
    o.location = hm + Vector((0, 0, h * (1 - e)))


def b_soil(c, rng):
    F.void_stage(c, top=(0.6, -1.2, 2.6), target=(0, 0, 0.5), energy=420, size=1.2, radius=3.0)
    layers = [("Litter", 0.06, B.tex_mat("Litter", "forest_ground_04", scale=1.2, tint=(0.6, 0.55, 0.45))),
              ("Humus", 0.22, B.tex_mat("Humus", "forest_ground_04", scale=2.5, tint=(0.32, 0.24, 0.18))),
              ("Loam", 0.36, B.tex_mat("Loam", "farm_soil", scale=1.5, tint=(0.75, 0.6, 0.45))),
              ("Clay", 0.42, B.tex_mat("ClayT", "farm_soil", scale=2.2, tint=(0.95, 0.66, 0.42)))]
    z = 1.06
    slabs = []
    for nm, th, m in layers:
        z -= th
        slabs.append(box("Soil" + nm, (0, 0, z + th / 2), (1.5, 0.3, th), m))
    # the hole: a boolean cutter that sinks into the section (a real cut, animated), sides darkened by AO
    cut = box("HoleCut", (0.05, 0, 1.06), (0.62, 0.5, 0.01), None)
    cut.hide_render = True; cut.display_type = 'WIRE'
    for sl in slabs:
        bo = sl.modifiers.new("hole", 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
    c["cut"] = cut
    # a pale wooden box outline that settles into the hole (simple frame of slats)
    pale = pbr("BoxPale", (0.62, 0.5, 0.33), 0.75)
    w, d, h = 0.5, 0.26, 0.44
    edges = [((0, -d / 2, h / 2), (w, 0.012, h)), ((0, d / 2, h / 2), (w, 0.012, h)), ((-w / 2, 0, h / 2), (0.012, d, h)),
             ((w / 2, 0, h / 2), (0.012, d, h)), ((0, 0, h), (w, d, 0.012))]
    bx = join([box("BoxSlat", e[0], e[1], pale) for e in edges], "BuriedBox")
    bx.location = (0.05, 0.04, 1.2); c["bx"] = bx
    # real measuring tools: a yellow folding rule across the top of the hole, a red-white rod standing in it
    rule = box("Rule", (0.05, -0.17, 1.065), (0.7, 0.018, 0.004), pbr("RuleY", (0.8, 0.62, 0.08), 0.5))
    for k in range(14):
        box("RuleTick", (-0.3 + k * 0.05 + 0.05, -0.17, 1.068), (0.002, 0.012, 0.001), pbr("Tick", (0.05, 0.05, 0.05), 0.5))
    c["rule"] = rule
    rod = join([cyl(f"Rod{k}", (0.33, -0.1, 0.06 + k * 0.1 + 0.05), 0.008, 0.1, pbr("RodR" if k % 2 else "RodW", (0.7, 0.08, 0.05) if k % 2 else (0.9, 0.9, 0.88), 0.5), verts=10) for k in range(10)], "Rod")
    c["rod"] = rod
    B.key_spot((-0.9, -1.6, 1.8), (0, 0, 0.8), 260, 30, (1.0, 0.85, 0.65), soft=0.2, name="SideKey")
    B.key_spot((0.05, -1.4, 1.35), (0.05, 0, 0.75), 120, 18, (1.0, 0.9, 0.75), soft=0.3, name="IntoHole")


def b_boxmarks(c, rng):
    import sc_box as X
    F.void_stage(c, top=(0.3, -0.4, 3.4), target=(0, 0, 0.8), energy=1400, size=1.6, radius=3.6)
    X.build_box(c)
    W, D, H, Z0 = X.W, X.D, X.H, X.Z0
    spots = [((W / 2 + 0.25, -0.15), -1.57), ((W / 2 + 0.28, 0.2), -1.57), ((-W / 2 - 0.25, 0.0), 1.57),
             ((0.15, -D / 2 - 0.4), 0.0), ((-0.2, -D / 2 - 0.35), 0.0), ((0.0, D / 2 + 0.32), 3.14)]
    c["tents"] = [F.marker_tent(f"T{k}", (x, y, 0.0), k + 1, rz, 0.14) for k, ((x, y), rz) in enumerate(spots)]
    B.key_spot((2.2, -1.6, 1.6), (0, 0, 0.8), 500, 35, (0.85, 0.9, 1.0), soft=0.4, name="Rim")


def b_string(c, rng):
    F.void_stage(c, top=(0, -0.3, 2.6), target=(0, 0, TZ), energy=220, size=1.2, radius=2.6)
    bench(size=(2.2, 0.9), top=TZ)
    import sc_b_dna as DN
    screw = cyl("Screw", (0, 0, 0.03), 0.004, 0.05, pbr("ScrewZn", (0.55, 0.55, 0.5), 0.3, 1.0), verts=12, rot=(0, math.radians(90), 0.3))
    gl = cyl("Tumbler", (0, 0, 0.045), 0.035, 0.09, glass("Tumb", (0.9, 0.92, 0.92), 0.02), verts=32)
    c["bag_a"] = DN.bag("BagScrew", (-0.6, 0.0, TZ), screw)
    c["bag_b"] = DN.bag("BagGlass", (0.6, 0.0, TZ), gl)
    c["pa"] = F.push_pin("PinA", (-0.6, 0.1, TZ + 0.025)); c["pb"] = F.push_pin("PinB", (0.6, 0.1, TZ + 0.025))
    c["pb"].parent = c["bag_b"]; c["pb"].location = (0, 0.1, 0.025)
    c["a"], c["b"] = Vector((-0.6, 0.1, TZ + 0.05)), Vector((0.6, 0.1, TZ + 0.05))
    c["thread"] = F.string("Thread", c["a"], c["b"], sag=0.03, n=40)
    for k, x in enumerate((-0.6, 0.6)):
        B.key_spot((x, -0.25, TZ + 1.0), (x, 0, TZ), 160, 28, (1.0, 0.88, 0.72), soft=0.15, name=f"Pool{k}")


def b_timeline(c, rng):
    F.void_stage(c, top=(0, 3.0, 4.0), target=(0, 3.0, 0), energy=0.0, size=1.0, radius=6.0)
    box("ConcFloor", (0, 3.0, -0.004), (3.0, 10, 0.008), B.tex_mat("ConcF", "concrete_floor_02", scale=0.5, tint=(0.5, 0.5, 0.5)))
    c["blocks"] = []
    for k in range(31):
        yr = 1981 + k; y = k * 0.24
        m = pbr(f"Blk{yr}", (0.42, 0.33, 0.22), 0.7)
        b = box(f"Year{yr}", (0, y, 0.035), (0.34, 0.2, 0.07), m, bevel=0.004)
        F.stencil(f"YrT{yr}", str(yr), (0, y, 0.0712), 0.085, (0, 0, math.radians(90)), color=(0.96, 0.94, 0.88))
        c["blocks"].append((b, m, yr))
    # the brass marker on a little stand that slides along the row
    mk = join([cyl("MkRod", (0, 0, 0.15), 0.004, 0.3, pbr("Brass", (0.6, 0.45, 0.2), 0.3, 1.0), verts=8),
               box("MkFlag", (0.06, 0, 0.27), (0.12, 0.003, 0.07), pbr("MkFlagR", (0.6, 0.06, 0.04), 0.5)),
               cyl("MkFoot", (0, 0, 0.005), 0.04, 0.01, pbr("Brass2", (0.6, 0.45, 0.2), 0.3, 1.0), verts=20)], "Marker")
    mk.location = (0.26, 0, 0); c["marker"] = mk
    for k in range(4):
        B.key_spot((0.6, 1.0 + k * 1.8, 2.4), (0, 1.0 + k * 1.8, 0), 380, 40, (1.0, 0.92, 0.8), soft=0.3, name=f"Strip{k}")


def b_reels(c, rng):
    F.void_stage(c, top=(0, -0.6, 2.8), target=(0, 0.3, 0.4), energy=300, size=1.6, radius=3.0)
    alu = pbr("BarAlu", (0.7, 0.71, 0.72), 0.25, 1.0)
    env = lambda u: (0.25 + 0.75 * abs(math.sin(u * math.pi * 3.5)) ** 0.7) * (1 - 0.3 * u) * (0.85 + 0.15 * math.sin(u * 40))
    c["rows"] = []
    for r in range(3):
        y = r * 0.55
        reel = join([cyl(f"Reel{r}", (0, 0, 0), 0.09, 0.012, pbr("ReelM", (0.1, 0.1, 0.11), 0.3, 0.6), verts=40),
                     cyl(f"Hub{r}", (0, 0, 0.008), 0.025, 0.006, pbr("HubM", (0.75, 0.75, 0.74), 0.3, 0.9), verts=24),
                     cyl(f"Tape{r}", (0, 0, 0.002), 0.065, 0.013, pbr("TapeBrown", (0.12, 0.07, 0.04), 0.4), verts=40)], f"ReelR{r}")
        reel.location = (-0.75, y, 0.09); reel.rotation_euler = (math.radians(90), 0, 0)
        cyl(f"Stand{r}", (-0.75, y, 0.004), 0.05, 0.008, pbr("StandM", (0.05, 0.05, 0.05), 0.4), verts=24)
        bars = []
        for i in range(48):
            u = i / 47; hgt = 0.03 + 0.32 * env(u + 0.07 * r)
            b = box(f"Bar{r}_{i}", (-0.6 + i * 0.03, y, hgt / 2), (0.016, 0.016, hgt), alu)
            bars.append((b, hgt))
        c["rows"].append((reel, bars))
    pk = 30; b, hgt = c["rows"][1][1][pk]                                # the highest note that drops in volume
    c["peak"] = (b, hgt)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.003, location=(b.location.x, 0.55, hgt * 0.55 + 0.02), rotation=(math.radians(90), 0, 0))
    ring = bpy.context.active_object; ring.data.materials.append(pbr("RingRed", (0.7, 0.07, 0.04), 0.4)); c["ring"] = ring
    for k, y in enumerate((0, 0.55, 1.1)):
        B.key_spot((0.2, y - 0.9, 1.6), (0, y, 0.15), 280, 30, (1.0, 0.9, 0.75), soft=0.2, name=f"RowKey{k}")


def b_lineup(c, rng):
    F.void_stage(c, top=(0, -2.0, 3.0), target=(0, 0, 0.6), energy=0.0, size=1.0, radius=6.0)
    wall = B.plaster("LineupWall", (0.32, 0.32, 0.31), dirt=0.05)
    box("Wall", (0, 0.75, 1.3), (7.5, 0.1, 2.6), wall)
    paint = pbr("WallPaint", (0.86, 0.85, 0.8), 0.7)
    for k in range(11):
        z = 0.5 + k * 0.15
        box(f"HLine{k}", (0, 0.695, z), (7.2, 0.004, 0.006 if k % 2 else 0.012), paint)
    box("Plinth", (0, 0.2, 0.25), (7.0, 0.7, 0.5), pbr("PlinthM", (0.06, 0.06, 0.065), 0.5))
    c["recs"] = []
    for k in range(11):
        x = -3.0 + k * 0.6
        r = P.reel_recorder(f"LR{k}", (x, 0.2, 0.5), rot_z=0.0, spin=0.0, scale=0.85, lid_wood=(k != 5))
        F.stencil(f"Num{k}", str(k + 1), (x, 0.694, 1.32), 0.14, (math.radians(90), 0, 0), color=(0.88, 0.87, 0.82))
        sp = B.key_spot((x, -0.4, 2.6), (x, 0.3, 0.8), 0.0, 26, (1.0, 0.92, 0.8), soft=0.08, name=f"Spot{k}")
        c["recs"].append((r, sp))
        if k == 5 and r.get("keys"):
            c["pause_key"] = r["keys"][min(3, len(r["keys"]) - 1)]; c["pause_z0"] = c["pause_key"].location.z
    B.fill((0, -4, 1.5), (0, 0, 0.6), 60, 3.0, (0.55, 0.6, 0.75))


def _booth_mini(name, loc, scale=0.32):
    """A small yellow phone-booth model on the table (court reconstruction prop): frame, glass, a lit roof sign box."""
    y = pbr(name + "Y", (0.85, 0.62, 0.05), 0.4)
    g = glass(name + "G", (0.85, 0.9, 0.9), 0.02)
    s_ = scale; parts = []
    for (dx, dy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        parts.append(box(name + "Post", (dx * 0.5 * s_, dy * 0.5 * s_, 1.1 * s_), (0.06 * s_, 0.06 * s_, 2.2 * s_), y))
    parts += [box(name + "Roof", (0, 0, 2.25 * s_), (1.08 * s_, 1.08 * s_, 0.1 * s_), y),
              box(name + "Base", (0, 0, 0.03 * s_), (1.1 * s_, 1.1 * s_, 0.06 * s_), pbr(name + "B", (0.2, 0.2, 0.2), 0.6))]
    for (dx, dy, sx, sy) in ((0, -0.5, 1.0, 0.02), (0, 0.5, 1.0, 0.02), (-0.5, 0, 0.02, 1.0), (0.5, 0, 0.02, 1.0)):
        parts.append(box(name + "Glass", (dx * s_, dy * s_, 1.15 * s_), (sx * s_, sy * s_, 1.9 * s_), g))
    parts.append(box(name + "Phone", (0, 0.44 * s_, 1.3 * s_), (0.25 * s_, 0.08 * s_, 0.35 * s_), pbr(name + "Ph", (0.1, 0.1, 0.1), 0.4)))
    o = join(parts, name); o.location = loc
    lamp = emissive(name + "Lamp", (1.0, 0.95, 0.85), 2.0)
    l = box(name + "LampBox", (loc[0], loc[1], loc[2] + 2.16 * s_), (0.5 * s_, 0.5 * s_, 0.03 * s_), lamp)
    return o, lamp


def b_chain(c, rng):
    import rj
    F.void_stage(c, top=(0, -0.6, 3.0), target=(0, 0, TZ), energy=0.0, size=1.0, radius=7.0)
    box("LongTable", (0, 0, TZ - 0.025), (8.4, 1.0, 0.05), pbr("TableBlack", (0.03, 0.03, 0.032), 0.35, **{'Coat Weight': 0.3}), bevel=0.004)
    for x in (-4.0, 4.0):
        for y in (-0.42, 0.42):
            box("TLeg", (x, y, (TZ - 0.05) / 2), (0.06, 0.06, TZ - 0.05), pbr("LegM", (0.05, 0.05, 0.05), 0.4))
    st = {}
    r, dial = rj.kitchen_radio("ChainRadio"); r.location = (-3.6, 0.1, TZ); st["radio"] = Vector((-3.6, 0.1, TZ))
    g = P.reel_recorder("ChainGrundig", (-2.1, 0.05, TZ), rot_z=0.0, spin=0.6, lid_wood=True); st["grundig"] = Vector((-2.1, 0.05, TZ)); c["grundig"] = g
    try:
        import ph
        cp, _ = ph.model("cassette_player", loc=(-0.6, 0.05, TZ), rot_z=0.0, scale=1.0)
    except Exception as e:
        print("[chain] cassette", e)
    st["cassette"] = Vector((-0.6, 0.05, TZ))
    booth, blamp = _booth_mini("ChainBooth", (0.9, 0.18, TZ), 0.24); st["booth"] = Vector((0.9, 0.1, TZ)); c["blamp"] = blamp
    wood_m = pbr("PoleWood", (0.25, 0.18, 0.1), 0.9)
    for k, x in enumerate((1.75, 2.45)):
        cyl(f"MiniPole{k}", (x, 0.25, TZ + 0.25), 0.012, 0.5, wood_m, verts=10)
        box(f"MiniArm{k}", (x, 0.25, TZ + 0.46), (0.03, 0.18, 0.015), wood_m)
    st["line"] = Vector((2.1, 0.25, TZ))
    deck = rj.reel_deck("ChainPolice", 0.85); deck["root"].location = (3.4, 0.05, TZ); c["deck"] = deck
    ph_r, hs, dl = rj.rotary_phone("ChainPhone"); ph_r.location = (3.95, 0.25, TZ)
    st["police"] = Vector((3.4, 0.05, TZ))
    c["st"] = st
    # the signal cable: a real red cable running station to station along the table, a light bead travelling in it
    pts = [Vector((-3.6, -0.15, TZ + 0.01)), Vector((-2.9, -0.2, TZ + 0.01)), Vector((-2.1, -0.22, TZ + 0.01)), Vector((-1.35, -0.2, TZ + 0.01)),
           Vector((-0.6, -0.18, TZ + 0.01)), Vector((0.15, -0.2, TZ + 0.01)), Vector((0.9, -0.15, TZ + 0.01)), Vector((1.4, 0.0, TZ + 0.02)),
           Vector((1.75, 0.25, TZ + 0.44)), Vector((2.1, 0.25, TZ + 0.40)), Vector((2.45, 0.25, TZ + 0.44)), Vector((2.8, 0.0, TZ + 0.02)),
           Vector((3.4, -0.18, TZ + 0.01))]
    c["cable_pts"] = pts
    c["cable"] = F.curve("SignalCable", pts, pbr("CableRed", (0.45, 0.05, 0.035), 0.45), bevel=0.004, smooth=True)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.012, location=pts[0])
    bead = bpy.context.active_object; bm = emissive("BeadE", (1.0, 0.62, 0.3), 30.0); bead.data.materials.append(bm)
    c["bead"], c["bead_m"] = bead, bm
    bl = bpy.data.lights.new("BeadL", 'POINT'); bl.energy = 0.0; bl.color = (1.0, 0.6, 0.3); bl.shadow_soft_size = 0.01
    blo = bpy.data.objects.new("BeadL", bl); bpy.context.collection.objects.link(blo); blo.parent = bead; c["bead_l"] = bl
    c["flashes"] = []
    for k, key in enumerate(("grundig", "cassette", "booth")):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.05, location=st[key] + Vector((0, -0.2, 0.05)))
        f = bpy.context.active_object; fm = emissive(f"Flash{k}", (1.0, 0.12, 0.06), 0.0); f.data.materials.append(fm)
        c["flashes"].append((f, fm))
    for k, x in enumerate((-3.6, -2.1, -0.6, 0.9, 2.1, 3.4)):
        B.key_spot((x, -0.5, TZ + 1.4), (x, 0.05, TZ), 170, 34, (1.0, 0.9, 0.76), soft=0.2, name=f"StaKey{k}")


def b_exhibits(c, rng):
    import ph
    F.void_stage(c, top=(0, -0.2, 2.6), target=(0, 0, TZ), energy=55, size=1.0, radius=2.4)
    box("ExTable", (0, 0, TZ - 0.025), (1.6, 0.8, 0.05), B.tex_mat("ExOak", "oak_veneer_01", scale=0.6, tint=(0.5, 0.38, 0.26)), bevel=0.005)
    box("ExTableBody", (0, 0, (TZ - 0.05) / 2), (1.5, 0.7, TZ - 0.05), pbr("ExBody", (0.08, 0.05, 0.035), 0.6))
    items = []
    # 1 the statement, typed, struck through in red (the same page as 3-9A)
    pg = F.card_plane("Statement", (-0.55, -0.05, TZ + 0.001), 0.21, 0.297, B.paper_mat("StPaper", (0.9, 0.88, 0.8)), rot_z=0.12)
    for k in range(9):
        ln = box(f"Strike{k}", (-0.55, -0.15 + k * 0.025, TZ + 0.0025), (0.16, 0.002, 0.0005), pbr("RedInk", (0.6, 0.05, 0.04), 0.5), rot=(0, 0, 0.12))
        ln.parent = pg; ln.matrix_parent_inverse = pg.matrix_world.inverted()
    items.append(pg)
    r, ms = ph.model("binoculars", loc=(-0.2, 0.12, TZ), rot_z=0.4); items.append(r)
    lt = []
    for k in range(5):
        lt.append(box(f"Letter{k}", (0.12 + rng.uniform(-0.01, 0.01), -0.12, TZ + 0.003 + k * 0.004), (0.22, 0.11, 0.003),
                      B.paper_mat(f"Env{k}", (0.92, 0.9, 0.84) if k % 2 else (0.88, 0.84, 0.7)), rot=(0, 0, rng.uniform(-0.25, 0.25))))
    letters = join(lt, "Letters"); items.append(letters)
    iron = join([cyl("IronTip", (0.36, 0.2, TZ + 0.012), 0.003, 0.08, pbr("Tip", (0.5, 0.5, 0.52), 0.3, 1.0), verts=8, rot=(0, math.radians(90), 0)),
                 cyl("IronBody", (0.46, 0.2, TZ + 0.014), 0.008, 0.12, pbr("IronMetal", (0.6, 0.6, 0.62), 0.3, 1.0), verts=12, rot=(0, math.radians(90), 0)),
                 cyl("IronGrip", (0.6, 0.2, TZ + 0.016), 0.012, 0.13, pbr("Grip", (0.08, 0.06, 0.05), 0.6), verts=12, rot=(0, math.radians(90), 0))], "Iron")
    items.append(iron)
    g = P.reel_recorder("ExGrundig", (0.55, -0.12, TZ), rot_z=-0.3, spin=0.0, scale=0.8); items.append(g["root"])
    c["items"] = items


def b_days56(c, rng):
    F.void_stage(c, top=(0, 3.5, 3.0), target=(0, 3.5, TZ), energy=0.0, size=1.0, radius=6.0)
    box("Row", (0, 3.4, TZ - 0.025), (0.7, 7.4, 0.05), B.tex_mat("RowOak", "oak_veneer_01", scale=0.6, tint=(0.45, 0.34, 0.24)))
    cols = [(0.62, 0.5, 0.3), (0.55, 0.45, 0.28), (0.6, 0.48, 0.3)]
    for k in range(56):
        y = k * 0.125
        f = box(f"Day{k}", (0, y, TZ + 0.13), (0.32, 0.035, 0.26), pbr(f"DayM{k % 3}", cols[k % 3], 0.8), bevel=0.003, rot=(math.radians(-6), 0, 0))
        tab = box(f"Tab{k}", (0.1, y, TZ + 0.275), (0.07, 0.03, 0.04), pbr("TabW", (0.9, 0.88, 0.82), 0.7))
        F.stencil(f"DayN{k}", str(k + 1), (0.1, y - 0.016, TZ + 0.274), 0.025, (math.radians(90), 0, 0), color=(0.08, 0.07, 0.06))
    for k in range(5):
        B.key_spot((0.6, k * 1.6, TZ + 1.4), (0, k * 1.6, TZ), 220, 40, (1.0, 0.9, 0.76), soft=0.3, name=f"RowKey{k}")


BUILDERS = {"soil": b_soil, "boxmarks": b_boxmarks, "string": b_string, "timeline": b_timeline, "reels": b_reels,
            "lineup": b_lineup, "chain": b_chain, "exhibits": b_exhibits, "days56": b_days56}


def anim_v2(c, t, move):
    sec = t * DUR[move]; v = c["variant"]
    if v == "soil":
        u = ease(min(1.0, max(0.0, (sec - 0.6) / 2.2)))
        cut = c["cut"]; depth = 0.62 * u
        cut.location.z = 1.07 - depth / 2; cut.scale.z = max(0.01, depth / 0.01) * 0.01 / 0.01 if False else 1.0
        cut.dimensions = (0.62, 0.5, max(0.005, depth + 0.02))
        bz = 1.2 - 0.66 * ease(min(1.0, max(0.0, (sec - 3.0) / 1.6)))
        c["bx"].location.z = bz; c["bx"].hide_render = sec < 2.9
        F.show(c["rule"], (sec - 1.6) / 0.4); F.show(c["rod"], (sec - 2.2) / 0.4)
    elif v == "boxmarks":
        for k, o in enumerate(c["tents"]):
            F.show(o, (sec - 1.2 - 0.6 * k) / 0.35)
    elif v == "string":
        a, b = c["a"], c["b"]
        if move == "string":
            F.string_sag(c["thread"], a, b, 0.03)
            F.draw(c["thread"], ease(min(1.0, max(0.0, (sec - 0.8) / 2.6))))
            c["pb"].hide_render = sec < 0.4
        else:
            F.draw(c["thread"], 1.0)
            sag = 0.03 + 0.5 * ease(min(1.0, max(0.0, (sec - 0.8) / 1.4)))
            sp = c["thread"].data.splines[0]; n = len(sp.points)
            slide = ease(min(1.0, max(0.0, (sec - 2.6) / 2.0)))
            c["bag_b"].location = (0.6 + 0.9 * slide, 0.0, TZ)
            bb = Vector((0.6 + 0.9 * slide, 0.1, TZ + 0.05))
            for i in range(n):
                u = i / (n - 1); p = a.lerp(bb, u) - Vector((0, 0, sag * math.sin(math.pi * u)))
                p.z = max(p.z, TZ + 0.002)                                 # the slack thread lies on the bench
                sp.points[i].co = (p.x, p.y, p.z, 1)
    elif v == "timeline":
        u = ease(min(1.0, max(0.0, (sec - 0.8) / 3.6)))
        c["marker"].location = (0.26, 26 * 0.24 * u, 0)
        red = ease(min(1.0, max(0.0, (sec - 4.6) / 1.0)))
        for b, m, yr in c["blocks"]:
            if yr >= 2008:
                col = Vector((0.42, 0.33, 0.22)).lerp(Vector((0.55, 0.07, 0.05)), red)
                m.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (*col, 1)
    elif v == "reels":
        for r, (reel, bars) in enumerate(c["rows"]):
            reel.rotation_euler.y = -sec * 2.5
            for i, (b, hgt) in enumerate(bars):
                u = (sec - 0.4 - r * 0.5 - i * 0.03) / 0.25
                e = ease(max(0.0, min(1.0, u)))
                h = hgt * e
                if r == 1 and b is c["peak"][0]:
                    h *= 1 - 0.45 * ease(min(1.0, max(0.0, (sec - 3.4) / 0.6)))
                b.scale.z = max(0.001, e if not (r == 1 and b is c["peak"][0]) else h / hgt)
                b.location.z = hgt * b.scale.z / 2
                b.hide_render = e <= 0
        F.show(c["ring"], (sec - 4.1) / 0.4)
    elif v == "lineup":
        for k, (r, sp) in enumerate(c["recs"]):
            if move == "lineup":
                on = sec > 0.6 + k * 0.42
                sp.data.energy = 420.0 if on else 0.0
            else:
                off = sec > 1.2 + 0.08 * abs(k - 5) and k != 5
                sp.data.energy = 0.0 if off else 420.0
                if k == 5 and c.get("pause_key") is not None:
                    c["pause_key"].location.z = c["pause_z0"] - (0.006 if sec > 3.6 else 0.0)   # the pause key drops
    elif v == "chain":
        B.label(c, "Court reconstruction")
        pts = c["cable_pts"]
        if move == "chain":
            u = min(1.0, max(0.0, (sec - 2.0) / 38.0))
        else:
            u = min(1.0, max(0.0, sec / 6.5))
        i = u * (len(pts) - 1); k = min(len(pts) - 2, int(i)); f = i - k
        c["bead"].location = pts[k].lerp(pts[k + 1], f) + Vector((0, 0, 0.004))
        loss = 1.0 - 0.6 * u                                            # the signal weakens station by station
        c["bead_m"].node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = 30.0 * loss
        c["bead_l"].energy = 0.6 * loss
        c["blamp"].node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = 2.0 * (0.75 + 0.25 * (math.sin(sec * 61) > 0.6))   # the booth tube buzzes
        if move == "clicks":
            for j, (fo, fm) in enumerate(c["flashes"]):
                tj = 1.2 + 1.6 * j; w = max(0.0, 1 - abs(sec - tj) / 0.35)
                fm.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = 40.0 * w
                fo.hide_render = w <= 0
        else:
            for fo, fm in c["flashes"]:
                fo.hide_render = True
    elif v == "exhibits":
        for k, o in enumerate(c["items"]):
            _drop(o, (sec - 0.6 - 1.35 * k) / 0.5, 0.18)
    bpy.context.view_layer.update()
