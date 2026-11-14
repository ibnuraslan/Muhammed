"""VOID: evidence on black. A black void, one hard top light, a glossy floor that fades to nothing.
Short inserts (3.5 s) that turn the script's numbers into objects:
  ring     (intro 3A)  "The stone came from Harry Winston": the 31-carat ring turning slowly, a jeweller's tag "31 ct"
  grid360  (ch1 2B)    "three hundred and sixty pieces": 18 x 20 velvet slots, every piece taken in a sweeping wave
  suitcase (ch2 4B)    "seventy-one million euros": the closed suitcase alone, its luggage tag typed "71 000 000 €"
  dna      (ch4 3B)    "traces of their DNA in the boutique": swab tubes in a rack, a sealed evidence bag slides in
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import dd

EXPOSURE = 0.0
DUR = {"ring": 3.5, "grid360": 4.5, "suitcase": 3.5, "dna": 3.5, "cctv": 4.0}
VARIANT_FOR = {k: k for k in DUR}
MONO = "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"


def void(top=(0, 0, 1.4), energy=90.0, size=0.5, floor_gloss=0.28):
    """Black world, a glossy black floor, ONE hard-ish top light, a faint rim from behind."""
    world_flat((0.0, 0.0, 0.0), 0.0)
    fm = pbr("VoidFloor", (0.003, 0.003, 0.0032), 0.55 + 0.0 * floor_gloss)
    box("VoidFloor", (0, 0, -0.01), (12, 12, 0.02), fm)
    k = bpy.data.lights.new("VoidTop", 'AREA'); k.size = size; k.energy = energy; k.color = (1.0, 0.97, 0.92)
    ko = bpy.data.objects.new("VoidTop", k); bpy.context.collection.objects.link(ko); ko.location = top
    r = bpy.data.lights.new("VoidRim", 'AREA'); r.size = 1.2; r.energy = energy * 0.25; r.color = (0.9, 0.93, 1.0)
    ro = bpy.data.objects.new("VoidRim", r); bpy.context.collection.objects.link(ro)
    ro.location = (top[0], top[1] + 1.2, top[2] * 0.6); point_at(ro, (top[0], top[1], 0.05)); ro.visible_camera = False
    ro.visible_glossy = False; ko.visible_glossy = False          # no big soft highlight smeared across the floor
    return ko


def paper_tag(name, loc, text, size=(0.06, 0.035), rot_z=0.0, text_size=0.011, rot=None):
    """A buff card tag with a reinforced hole and typed text (FreeMono, like a typewriter)."""
    card = pbr(name + "Card", (0.52, 0.45, 0.32), 0.85)
    t = box(name, loc, (size[0], size[1], 0.0008), card, rot=rot or (0, 0, rot_z))
    ring_ = cyl(name + "Eye", Vector(loc) + Vector((-size[0] / 2 + 0.008, 0, 0.0006)), 0.004, 0.0004,
                pbr(name + "EyeM", (0.6, 0.55, 0.45), 0.6), verts=16)
    ring_.parent = t; ring_.location = (-size[0] / 2 + 0.008, 0, 0.0006); ring_.rotation_euler = (0, 0, 0)
    ink = pbr(name + "Ink", (0.004, 0.004, 0.006), 0.8)
    tx = text_obj(name + "Text", text, (0, 0, 0), text_size, ink, rot=(0, 0, 0), extrude=0.0, font_path=MONO)
    tx.parent = t; tx.location = (0.004, -text_size * 0.35, 0.0006)
    return t


def build_ring(c):
    void(top=(0.05, -0.05, 0.9), energy=55, size=0.35)
    vel = dd.black_velvet()
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.035, radius2=0.011, depth=0.09, location=(0, 0, 0.045))
    bpy.context.active_object.data.materials.append(vel)
    r = dd.ring("HeroRing", (0, 0, 0.09 + 0.0105 - 0.003), stone_r=0.0105, band="plat", band_r=0.0105)
    c["ring"] = r
    paper_tag("RingTag", (0.018, -0.034, 0.052), "31 ct", size=(0.04, 0.024), text_size=0.0085,
              rot=(math.radians(72), 0, math.radians(-12)))                    # the jeweller's tag leaning on the cone
    box("TagString", (0.006, -0.02, 0.075), (0.0012, 0.0012, 0.04), pbr("TagStr", (0.75, 0.7, 0.6), 0.8), rot=(math.radians(25), 0, 0))
    for k, p in enumerate(((0.25, -0.2, 0.35), (-0.3, -0.1, 0.25))):       # tiny hard points: the facets flash
        l = bpy.data.lights.new("Glint", 'POINT'); l.energy = 3 + 2 * k; l.shadow_soft_size = 0.002
        o = bpy.data.objects.new("Glint", l); bpy.context.collection.objects.link(o); o.location = p


def build_grid360(c):
    void(top=(0, 0, 2.2), energy=700, size=1.2, floor_gloss=0.5)
    vel = dd.black_velvet()
    box("Board", (0, 0, 0.01), (1.25, 1.15, 0.02), vel)
    M = dd.jewel_mats()
    # one band mesh + one stone mesh, linked into 360 pieces (cheap); each piece vanishes at its own frame (driver)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.012, minor_radius=0.0018, major_segments=24, minor_segments=8)
    band = bpy.context.active_object; band.data.materials.append(M["gold"]); band_me = band.data
    bpy.data.objects.remove(band)
    st = dd.diamond_mesh("GridStone", 0.0045); st.data.materials.append(M["diamond"]); stone_me = st.data
    bpy.data.objects.remove(st)
    slot = pbr("Slot", (0.004, 0.004, 0.005), 0.9)
    S = dd.Builder("Slots")
    rng = np.random.default_rng(360)
    nx, ny = 20, 18; pitch = 0.058
    fps = 24
    for i in range(nx):
        for j in range(ny):
            x = (i - (nx - 1) / 2) * pitch; y = (j - (ny - 1) / 2) * pitch
            S.cyl((x, y, 0.0205), 0.018, 0.002, slot, verts=20)
            # the sweep: from one corner to the other with a little scatter, between 0.6 s and 3.6 s
            u = (i + j) / (nx + ny - 2)
            f_out = int(fps * (0.6 + 3.0 * u + float(rng.uniform(-0.12, 0.12))))
            for nm, me, dz in (("Band", band_me, 0.023), ("Stone", stone_me, 0.026)):
                o = bpy.data.objects.new(f"{nm}{i}_{j}", me); bpy.context.collection.objects.link(o)
                o.location = (x, y, dz)
                if nm == "Band":
                    o.rotation_euler = (0, 0, float(rng.uniform(0, math.pi)))
                for prop in ("hide_render", "hide_viewport"):
                    d = o.driver_add(prop).driver; d.type = 'SCRIPTED'; d.expression = f"frame > {f_out}"
    S.done()
    paper_tag("Inventory", (0.3, -0.62, 0.0208), "INVENTAIRE\n360 PIECES", size=(0.2, 0.08), text_size=0.022)


def build_suitcase(c):
    void(top=(0.1, -0.2, 1.8), energy=420, size=0.6)
    shell = pbr("CaseShell", (0.05, 0.045, 0.04), 0.35, 0.0, **{"Coat Weight": 0.5})
    trim = pbr("CaseTrim", (0.55, 0.55, 0.57), 0.25, 1.0)
    B = dd.Builder("Suitcase")
    B.box((0, 0, 0.24), (0.7, 0.24, 0.48), shell)
    B.box((0, 0, 0.24), (0.705, 0.012, 0.485), trim)                      # the closing seam
    for sx in (-0.2, 0.2):
        B.box((sx, -0.125, 0.4), (0.05, 0.012, 0.03), trim)               # latches
    B.box((0, 0, 0.505), (0.16, 0.03, 0.02), shell).box((-0.075, 0, 0.49), (0.015, 0.025, 0.03), shell).box((0.075, 0, 0.49), (0.015, 0.025, 0.03), shell)
    for sx in (-0.3, 0.3):
        B.cyl((sx, 0.08, 0.012), 0.02, 0.024, pbr("Wheel", (0.02, 0.02, 0.02), 0.6), verts=16, rot=(0, math.radians(90), 0))
    B.done()
    # the luggage tag hangs from the handle on a strap, slowly swinging
    piv = bpy.data.objects.new("TagPivot", None); bpy.context.collection.objects.link(piv); piv.location = (0.05, -0.135, 0.5)
    strap = box("TagStrap", (0, 0, -0.06), (0.008, 0.002, 0.12), pbr("Strap", (0.12, 0.09, 0.06), 0.6)); strap.parent = piv
    tag = paper_tag("CaseTag", (0, 0, 0), "71 000 000 €", size=(0.11, 0.055), text_size=0.0105)
    tag.parent = piv; tag.location = (0.0, -0.006, -0.15); tag.rotation_euler = (math.radians(90), 0, math.radians(8))
    c["tag_pivot"] = piv


def build_dna(c):
    void(top=(0, 0, 1.3), energy=80, size=0.4)
    clear = glass("TubeGlass", (0.95, 0.97, 0.98), 0.05)
    cap = pbr("TubeCap", (0.85, 0.85, 0.82), 0.4)
    cotton = pbr("Cotton", (0.92, 0.9, 0.86), 0.95)
    rack = pbr("Rack", (0.08, 0.08, 0.09), 0.5)
    B = dd.Builder("SwabRack")
    B.box((0, 0, 0.03), (0.24, 0.06, 0.006), rack).box((0, 0, 0.004), (0.24, 0.06, 0.006), rack)
    for k in range(4):
        x = -0.08 + k * 0.053
        B.cyl((x, 0, 0.07), 0.009, 0.13, clear, verts=20).cyl((x, 0, 0.14), 0.0095, 0.02, cap, verts=20)
        B.cyl((x, 0, 0.07), 0.0015, 0.1, cap, verts=8).cyl((x, 0, 0.026), 0.004, 0.014, cotton, verts=12)
    B.done((0.02, 0.06, 0))
    # the sealed evidence bag (translucent, red tamper tape) with a typed label; it slides in from the left
    bag = dd.Builder("EvidenceBag")
    film = glass("BagFilm", (0.96, 0.96, 0.95), 0.25)
    bag.box((0, 0, 0.004), (0.2, 0.26, 0.006), film).box((0, 0.118, 0.008), (0.2, 0.02, 0.002), pbr("Tamper", (0.55, 0.04, 0.03), 0.5))
    bag.box((0.02, -0.02, 0.003), (0.03, 0.05, 0.004), pbr("Fibre", (0.25, 0.2, 0.16), 0.9))   # a fibre swatch inside
    b = bag.done((0, -0.14, 0)); c["bag"] = b
    lab = paper_tag("BagLabel", (0, 0, 0), "SCELLE N 14\nPRELEVEMENT ADN", size=(0.12, 0.05), text_size=0.0085)
    lab.parent = b; lab.location = (0.0, -0.075, 0.0085)


def build_cctv(c):
    """Desk insert (ch3 1B): three CCTV stills of the service corridor (a faceless guard by the door, timestamps
    07:52 / 07:53 / 07:54) slid one by one onto a dark desk under a warm lamp pool."""
    import os
    world_flat((0.0, 0.0, 0.0), 0.0)
    desk = dd.tex_mat("walnut_veneer", 1.2, tint=(0.5, 0.42, 0.34), name="CCTVDesk", sat=0.8, coat=0.3)
    box("CCTVDesk", (0, 0, -0.02), (2.0, 1.2, 0.04), desk)
    pl = bpy.data.lights.new("PrintLamp", 'SPOT'); pl.energy = 45; pl.spot_size = math.radians(70); pl.spot_blend = 0.9
    pl.color = (1.0, 0.82, 0.58); pl.shadow_soft_size = 0.06
    plo = bpy.data.objects.new("PrintLamp", pl); bpy.context.collection.objects.link(plo); plo.location = (0.35, 0.3, 0.75)
    point_at(plo, (0.0, 0.0, 0.0))
    here = os.path.dirname(os.path.abspath(__file__))
    c["prints"] = []
    for k, (home, rz) in enumerate((((-0.12, 0.03), 0.07), ((0.11, 0.06), -0.05), ((0.0, -0.08), 0.1))):
        m = bpy.data.materials.new(f"CCTV{k}"); m.use_nodes = True
        N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; b.inputs['Roughness'].default_value = 0.35
        im = N.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(os.path.join(here, "..", "assets", f"cctv_{k + 1}.jpg"))
        L.new(im.outputs['Color'], b.inputs['Base Color'])
        bpy.ops.mesh.primitive_plane_add(size=1, location=(home[0], home[1], 0.0006 * (k + 1)))
        pr = bpy.context.active_object; pr.name = f"CCTVPrint{k}"; pr.scale = (0.2, 0.15, 1); pr.data.materials.append(m)
        c["prints"].append((pr, Vector((home[0], home[1], 0.0006 * (k + 1))), rz))
    pen = cyl("Pen", (0.27, -0.12, 0.006), 0.005, 0.14, pbr("PenM", (0.02, 0.02, 0.025), 0.3, 0.4), verts=12, rot=(0, math.radians(90), 0.4))


def build(variant=None):
    c = {}
    {"ring": build_ring, "grid360": build_grid360, "suitcase": build_suitcase, "dna": build_dna,
     "cctv": build_cctv}[variant or "ring"](c)
    return c


def _frame(t, mv):
    bpy.context.scene.frame_set(1 + int(round(t * (DUR[mv] * 24 - 1))))     # frame drivers (pieces vanishing) follow t


def anim_grid(c, t):
    _frame(t, "grid360")


def anim_ring(c, t):
    c["ring"].rotation_euler = (0, 0, math.radians(-25 + 50 * t))


def anim_suitcase(c, t):
    sec = t * DUR["suitcase"]
    c["tag_pivot"].rotation_euler = (math.radians(6 * math.sin(sec * 2.1) * math.exp(-sec * 0.3)), 0, math.radians(8))


def anim_dna(c, t):
    u = ease(min(1.0, t / 0.55))
    c["bag"].location = Vector((-0.45, -0.16, 0)).lerp(Vector((0.0, -0.14, 0)), u)
    c["bag"].rotation_euler = (0, 0, math.radians(-14 * (1 - u) + 4))


def anim_cctv(c, t):
    sec = t * DUR["cctv"]
    for k, (pr, home, rz) in enumerate(c["prints"]):               # each print slides in from the left, a beat apart
        u = ease(min(1.0, max(0.0, (sec - 0.2 - 0.85 * k) / 0.75)))
        pr.location = home + Vector((-0.6 * (1 - u), -0.1 * (1 - u), 0))
        pr.rotation_euler = (0, 0, rz - 0.45 * (1 - u))


MOVES = {
    "cctv": dict(kind="anim", dof=5.6, anim=anim_cctv,
                 cam=lambda c, t: (Vector((0.02, -0.18, 0.62)).lerp(Vector((0.0, -0.12, 0.52)), ease(t)), Vector((0.0, 0.0, 0.0)), 35),
                 focus=lambda c, t: Vector((0, 0, 0))),
    "ring": dict(kind="anim", dof=2.8, anim=anim_ring,
                 cam=lambda c, t: (Vector((0.01, -0.36, 0.12)).lerp(Vector((0.005, -0.29, 0.11)), ease(t)), Vector((0.006, -0.02, 0.076)), 48),
                 focus=lambda c, t: Vector((0, 0, 0.1))),
    "grid360": dict(kind="anim", dof=None, anim=anim_grid,
                    cam=lambda c, t: (Vector((0.05, -0.75, 1.55)).lerp(Vector((0.0, -0.6, 1.3)), ease(t)), Vector((0, -0.12, 0)), 32, (0, 1, 0))),
    "suitcase": dict(kind="anim", dof=4.0, anim=anim_suitcase,
                     cam=lambda c, t: (Vector((1.0, -1.8, 0.6)).lerp(Vector((0.75, -1.45, 0.52)), ease(t)), Vector((0.05, -0.1, 0.32)), 60),
                     focus=lambda c, t: Vector((0.05, -0.1, 0.3))),
    "dna": dict(kind="anim", dof=2.8, anim=anim_dna,
                cam=lambda c, t: (Vector((-0.1, -0.56, 0.44)).lerp(Vector((0.04, -0.52, 0.4)), ease(t)), Vector((0.0, -0.1, 0.02)), 40),
                focus=lambda c, t: Vector((0.0, -0.08, 0.03))),
}
