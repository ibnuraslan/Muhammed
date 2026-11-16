"""Radio thumbnail plate: inside a public phone booth at night. The handset lies on the shelf; a small portable
cassette player rests against it, its speaker to the mouthpiece (the court's reconstruction of how the jingle was played).
Cold tube light inside, sodium street light outside, rain on the glass. No brand, no sign.
  python sc_booth.py [--pct 25] [--samples 64] [--out plates/radio.png]"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "lib"))
import bpy
from mathutils import Vector
from common import reset, camera, point_at, area_light
from kit import pbr, box, cyl, emissive, glass, rain_glass
import ph

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
s = reset(res=(1920, 1080), samples=arg("--samples", 160), exposure=0.0)
s.render.resolution_percentage = arg("--pct", 100)
s.cycles.max_bounces = 10; s.cycles.transmission_bounces = 10
w = bpy.data.worlds.new("W"); s.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs['Color'].default_value = (0.004, 0.005, 0.008, 1)

BW, BD, BH = 0.95, 0.95, 2.2           # booth inside (x width, y depth); back wall at y = +BD/2
YB = BD / 2
SH_Z = 1.02                            # shelf top

panel = pbr("BoothPanel", (0.05, 0.05, 0.048), 0.5)       # dull painted metal, no colour scheme of any real operator
steel = pbr("Steel", (0.35, 0.35, 0.36), 0.38, 1.0)
phone_grey = pbr("PhoneGrey", (0.09, 0.095, 0.1), 0.4)
bakelite = pbr("Bakelite", (0.008, 0.008, 0.009), 0.38)
bakelite.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.15

# back wall and the frame posts
box("Back", (0, YB + 0.02, BH / 2), (BW, 0.04, BH), panel)
for x in (-BW / 2, BW / 2):
    box("Post", (x, YB, BH / 2), (0.05, 0.05, BH), panel)
    box("PostF", (x, -YB, BH / 2), (0.05, 0.05, BH), panel)
box("Roof", (0, 0, BH + 0.03), (BW + 0.1, BD + 0.1, 0.06), panel)
box("Floor", (0, 0, -0.01), (6, 6, 0.02), ph.texture("asphalt_02", scale=1.5, tint=(0.3, 0.3, 0.32), name="Street"))
# side glass with rain
rg = rain_glass("RainGlass")
for x in (-BW / 2, BW / 2):
    g = box("Glass", (x, 0, 1.25), (0.008, BD - 0.05, 1.7), rg)
box("Kick", (-BW / 2, 0, 0.2), (0.03, BD, 0.4), panel); box("KickR", (BW / 2, 0, 0.2), (0.03, BD, 0.4), panel)

# the shelf
box("Shelf", (0, YB - 0.14, SH_Z - 0.012), (0.62, 0.28, 0.024), steel, bevel=0.004)
box("ShelfLip", (0, YB - 0.28, SH_Z - 0.03), (0.62, 0.012, 0.05), steel)

# the payphone body on the back wall (generic grey box, coin slot, keypad, a small window; no logo)
PZ = 1.42
box("PhoneBody", (0.02, YB - 0.07, PZ), (0.24, 0.12, 0.40), phone_grey, bevel=0.012)
box("CoinSlot", (0.09, YB - 0.131, PZ + 0.13), (0.035, 0.004, 0.006), bakelite)
box("Window", (-0.03, YB - 0.131, PZ + 0.12), (0.1, 0.004, 0.04), pbr("Lcd", (0.03, 0.05, 0.04), 0.1))
for r_ in range(4):
    for c_ in range(3):
        box("Key", (-0.06 + c_ * 0.035, YB - 0.133, PZ + 0.03 - r_ * 0.035), (0.026, 0.006, 0.026), steel, bevel=0.002)
box("ReturnCup", (0.02, YB - 0.14, PZ - 0.16), (0.08, 0.04, 0.04), steel, bevel=0.004)
box("Cradle", (-0.125, YB - 0.09, PZ + 0.04), (0.03, 0.06, 0.2), phone_grey, bevel=0.006)    # empty hook

PLAYER_ROT = float(sys.argv[sys.argv.index('--prot') + 1]) if '--prot' in sys.argv else 0.0
# the handset: a classic curved handset lying on its side along the shelf; the handle bows towards the viewer and
# both cups open towards the back wall. Ear cup left, mouth cup right.
HS = Vector((-0.05, YB - 0.2, SH_Z))
CR = 0.03                                   # cup radius; the handset rests on its cups
ZC = SH_Z + CR
EAR = Vector((HS.x - 0.085, HS.y, ZC)); MOUTH = Vector((HS.x + 0.085, HS.y, ZC))
hc = bpy.data.curves.new("Handle", 'CURVE'); hc.dimensions = '3D'; hc.bevel_depth = 0.0135; hc.bevel_resolution = 6
spl = hc.splines.new('BEZIER'); spl.bezier_points.add(2)
pts = [EAR + Vector((-0.004, -0.012, 0)), Vector((HS.x, HS.y - 0.036, ZC)), MOUTH + Vector((0.004, -0.012, 0))]
for bp, co_ in zip(spl.bezier_points, pts):
    bp.co = co_; bp.handle_left_type = bp.handle_right_type = 'AUTO'
hob = bpy.data.objects.new("Handle", hc); bpy.context.collection.objects.link(hob); hc.materials.append(bakelite)
holes = pbr("Holes", (0.02, 0.02, 0.02), 0.5)
hole_dark = pbr("HoleDark", (0, 0, 0), 0.9)
for nm, c_, tilt in (("EarCup", EAR, 14), ("MouthCup", MOUTH, -14)):
    rot = (math.radians(-90), 0, math.radians(tilt))           # cylinder axis -> +y
    cup = cyl(nm, c_ + Vector((0, 0.004, 0)), CR, 0.03, bakelite, verts=48); cup.rotation_euler = rot
    bv = cup.modifiers.new("b", 'BEVEL'); bv.width = 0.007; bv.segments = 4
    face = cyl(nm + "Face", c_ + Vector((0, 0.0195, 0)), CR * 0.72, 0.003, holes, verts=48); face.rotation_euler = rot
    neck = cyl(nm + "Neck", c_ + Vector((0, -0.016, 0)), 0.017, 0.02, bakelite, verts=32); neck.rotation_euler = rot
# curly cord from the phone down to the mouth end of the handset
cv = bpy.data.curves.new("Cord", 'CURVE'); cv.dimensions = '3D'; cv.bevel_depth = 0.0017; cv.bevel_resolution = 3
sp_ = cv.splines.new('POLY')
a = Vector((-0.11, YB - 0.1, PZ - 0.17)); b = EAR + Vector((-0.02, -0.025, 0.0))
N = 260; sp_.points.add(N - 1)
for i in range(N):
    t = i / (N - 1)
    base = a.lerp(b, t) + Vector((-0.03 * math.sin(math.pi * t), -0.02 * math.sin(math.pi * t), -0.1 * math.sin(math.pi * t)))
    ang = t * 70 * 2 * math.pi
    sp_.points[i].co = (base.x + 0.0055 * math.cos(ang), base.y + 0.0055 * math.sin(ang), base.z + 0.0055 * math.sin(ang + 1.3), 1)
co = bpy.data.objects.new("Cord", cv); bpy.context.collection.objects.link(co); cv.materials.append(bakelite)

# the cassette player standing on the shelf behind the mouth cup, its face pressed flat to the mouthpiece, taped on
root, ms = ph.model("portable_cassette_player")
for m_ in list(ms):
    if m_.name.endswith("casette"):
        m_.hide_render = True; ms.remove(m_)
root.rotation_euler = (0, 0, math.radians(PLAYER_ROT))
bpy.context.view_layer.update()
lo, hi = ph.bounds(ms)
mouth_face_y = MOUTH.y + 0.0215
root.location.y += mouth_face_y - lo.y + 0.0005
root.location.x += MOUTH.x - (lo.x + hi.x) / 2
root.location.z += SH_Z - lo.z
bpy.context.view_layer.update()
lo, hi = ph.bounds(ms)
# grey cloth tape: one band wrapped round the player and the back of the mouth cup
tape = pbr("Tape", (0.36, 0.36, 0.35), 0.45, 0.5)
TW, TT = 0.024, 0.0012
pb_ = hi.y + TT / 2                      # player back face
cb = MOUTH.y - 0.03                      # in front of the cup (round its neck)
xl, xr = lo.x - TT / 2, hi.x + TT / 2
cxl, cxr = MOUTH.x - CR * 0.8, MOUTH.x + CR * 0.8


def strip(p0, p1, z):
    d_ = Vector(p1) - Vector(p0); L_ = d_.length
    o = box("Tape", ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, z), (L_, TT, TW), tape)
    o.rotation_euler = (0, 0, math.atan2(d_.y, d_.x))
    return o


for z in (ZC,):
    strip((xl, pb_), (xr, pb_), z)
    strip((xr, pb_), (xr, lo.y), z); strip((xr, lo.y), (cxr, cb), z)
    strip((xl, pb_), (xl, lo.y), z); strip((xl, lo.y), (cxl, cb), z)
    strip((cxl, cb), (cxr, cb), z)

# light: a cold tube in the booth roof, sodium street light outside, a soft kick on the hero
tube = cyl("Tube", (0, 0.05, BH - 0.04), 0.012, 0.6, emissive("TubeE", (0.82, 0.92, 1.0), 4.0), rot=(0, math.radians(90), 0))
t_ = area_light((0, 0.05, BH - 0.06), (0, 0, 0), 0.6, 5, (0.8, 0.9, 1.0)); t_.data.shape = 'RECTANGLE'; t_.data.size_y = 0.05
sod = area_light((1.6, -1.2, 3.2), (0, 0, 0), 1.5, 260, (1.0, 0.55, 0.18)); point_at(sod, (0, 0.2, 1.0))
key = area_light((0.25, -0.35, 1.35), (0, 0, 0), 0.25, 4.5, (1.0, 0.78, 0.5)); point_at(key, (MOUTH.x + 0.05, MOUTH.y, SH_Z + 0.05))
# out of focus street lamps behind the side glass
for k, (x, y, z) in enumerate(((3.5, 2.5, 3.0), (-4.0, 4.0, 2.6), (6.0, 7.0, 3.2))):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x, y, z)); l_ = bpy.context.active_object
    l_.data.materials.append(emissive(f"Lamp{k}", (1.0, 0.6, 0.25), 25))

CL = (0.25, -0.25, 1.27)
tgt = (HS.x + 0.03, HS.y + 0.02, SH_Z + 0.07)
cam = camera(CL, tgt, lens=40)
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (Vector(CL) - Vector(tgt)).length; cam.data.dof.aperture_fstop = 2.8
out = arg("--out", os.path.join(HERE, "plates", "radio.png"))
s.render.filepath = out; s.render.image_settings.color_depth = '8'
bpy.ops.render.render(write_still=True)
print("[plate]", out)
