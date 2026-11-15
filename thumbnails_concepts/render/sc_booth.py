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

# the handset, lying on the shelf, mouthpiece end towards +x
HS = Vector((-0.07, YB - 0.16, SH_Z))
h_root = bpy.data.objects.new("Handset", None); bpy.context.collection.objects.link(h_root)
grip = box("Grip", (0, 0, 0.018), (0.15, 0.04, 0.026), bakelite, bevel=0.012); grip.parent = h_root
for sx, nm in ((-0.085, "Ear"), (0.085, "Mouth")):
    c = cyl(nm, (sx, 0, 0.027), 0.029, 0.05, bakelite, verts=40, rot=(0, math.radians(90 if sx > 0 else -90), 0))
    c.parent = h_root
    bv = c.modifiers.new("b", 'BEVEL'); bv.width = 0.006; bv.segments = 3
mp_grille = cyl("MouthHoles", (0.111, 0, 0.027), 0.021, 0.002, pbr("Holes", (0.05, 0.05, 0.05), 0.4, 0.6), verts=40, rot=(0, math.radians(90), 0))
mp_grille.parent = h_root
h_root.location = HS; h_root.rotation_euler = (0, 0, math.radians(8))
# curly cord from the phone to the handset's ear end
cv = bpy.data.curves.new("Cord", 'CURVE'); cv.dimensions = '3D'; cv.bevel_depth = 0.0017; cv.bevel_resolution = 3
sp_ = cv.splines.new('POLY')
a = Vector((-0.11, YB - 0.1, PZ - 0.17)); b = HS + Vector((-0.11, 0.0, 0.02))
N = 240; sp_.points.add(N - 1)
for i in range(N):
    t = i / (N - 1)
    base = a.lerp(b, t) + Vector((0, -0.05 * math.sin(math.pi * t), -0.16 * math.sin(math.pi * t)))
    ang = t * 70 * 2 * math.pi
    sp_.points[i].co = (base.x + 0.0055 * math.cos(ang), base.y + 0.0055 * math.sin(ang), base.z + 0.0055 * math.sin(ang + 1.3), 1)
co = bpy.data.objects.new("Cord", cv); bpy.context.collection.objects.link(co); cv.materials.append(bakelite)

# the cassette player, standing on the shelf, its face (speaker) against the mouthpiece
root, ms = ph.model("portable_cassette_player")
for m_ in list(ms):
    if m_.name.endswith("casette"):
        m_.hide_render = True; ms.remove(m_)
lo, hi = ph.bounds(ms)
root.location = (HS.x + 0.2, HS.y + 0.01, SH_Z - lo.z)
root.rotation_euler = (0, 0, math.radians(68))
bpy.context.view_layer.update()
lo, hi = ph.bounds(ms)
mouth_x = (h_root.matrix_world @ Vector((0.112, 0, 0))).x
root.location.x += mouth_x - lo.x + 0.001          # touching, not intersecting
root.location.z += SH_Z - lo.z

# light: a cold tube in the booth roof, sodium street light outside, a soft kick on the hero
tube = cyl("Tube", (0, 0.05, BH - 0.04), 0.012, 0.6, emissive("TubeE", (0.82, 0.92, 1.0), 4.0), rot=(0, math.radians(90), 0))
t_ = area_light((0, 0.05, BH - 0.06), (0, 0, 0), 0.6, 5, (0.8, 0.9, 1.0)); t_.data.shape = 'RECTANGLE'; t_.data.size_y = 0.05
sod = area_light((1.6, -1.2, 3.2), (0, 0, 0), 1.5, 260, (1.0, 0.55, 0.18)); point_at(sod, (0, 0.2, 1.0))
key = area_light((0.25, -0.35, 1.35), (0, 0, 0), 0.25, 4.5, (1.0, 0.78, 0.5)); point_at(key, (HS.x + 0.12, HS.y, SH_Z + 0.05))
# out of focus street lamps behind the side glass
for k, (x, y, z) in enumerate(((3.5, 2.5, 3.0), (-4.0, 4.0, 2.6), (6.0, 7.0, 3.2))):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x, y, z)); l_ = bpy.context.active_object
    l_.data.materials.append(emissive(f"Lamp{k}", (1.0, 0.6, 0.25), 25))

CL = (0.40, -0.44, 1.40)
tgt = (HS.x + 0.1, HS.y + 0.04, SH_Z + 0.13)
cam = camera(CL, tgt, lens=40)
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (Vector(CL) - Vector(tgt)).length; cam.data.dof.aperture_fstop = 2.8
out = arg("--out", os.path.join(HERE, "plates", "radio.png"))
s.render.filepath = out; s.render.image_settings.color_depth = '8'
bpy.ops.render.render(write_still=True)
print("[plate]", out)
