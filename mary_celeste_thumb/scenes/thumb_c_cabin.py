"""Concept (c): the captain's cabin table, abandoned. The log slate, a lit lantern and Sophia's china doll on the
table; the storm sea glimpsed through a porthole behind. Warm lantern key against the cold daylight in the port.
No people, no text (the slate carries only wiped chalk smears)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
T.C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, sea, ph, sf

E = os.environ.get
OUT = E("OUT", os.path.join(T.OUTDIR, "c_cabin.png"))
sc = T.res_setup(int(E("SPP", "384")), noise=0.015)

RX, RY, RZ = 1.6, 1.3, 2.05               # cabin half-width x, half-depth y (back wall at +RY), height
TOP = 0.76                                # table top
walls = ship.wood("dark_wooden_planks", 1.4, wet=0.2, tint=(0.75, 0.6, 0.48), name="walls")
floorm = ship.wood("wood_floor_deck", 1.0, wet=0.3, name="floor")
tablem = ship.wood(E("TABLE_TEX", "dark_wooden_planks"), float(E("TABLE_S", "2.5")), wet=0.1, tint=(0.75, 0.6, 0.45), name="table")
brass = bpy.data.materials.new("brass"); bp = brass.node_tree.nodes["Principled BSDF"]
bp.inputs['Base Color'].default_value = (0.5, 0.33, 0.13, 1); bp.inputs['Metallic'].default_value = 1; bp.inputs['Roughness'].default_value = 0.32

# --- room: floor, ceiling with beams, side walls; back wall (the ship's side) with a porthole cut in it
ship.box("floor", (0, 0, -0.02), (2 * RX, 2 * RY, 0.04), floorm)
ship.box("ceil", (0, 0, RZ + 0.03), (2 * RX, 2 * RY, 0.06), walls)
for k in range(-3, 4):
    ship.box(f"beam{k}", (k * 0.5, 0, RZ - 0.07), (0.12, 2 * RY, 0.14), walls, bevel=0.01)
ship.box("wall_l", (-RX, 0, RZ / 2), (0.06, 2 * RY, RZ), walls); ship.box("wall_r", (RX, 0, RZ / 2), (0.06, 2 * RY, RZ), walls)
ship.box("wall_f", (0, -RY - 1.4, RZ / 2), (2 * RX, 0.06, RZ), walls)
PX, PZ, PR = float(E("PX", "-0.35")), float(E("PZ", "1.32")), 0.2
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, RY + 0.1, RZ / 2)); bw = bpy.context.active_object; bw.name = "wall_b"
bw.scale = (2 * RX, 0.2, RZ); bw.data.materials.append(walls)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=PR, depth=1.0, location=(PX, RY + 0.1, PZ), rotation=(math.pi / 2, 0, 0))
cutter = bpy.context.active_object
bm = bw.modifiers.new("port", "BOOLEAN"); bm.object = cutter; bm.operation = 'DIFFERENCE'
bpy.context.view_layer.objects.active = bw; bpy.ops.object.modifier_apply(modifier="port"); bpy.data.objects.remove(cutter)
# brass rim, hinged glass, and the dogs
bpy.ops.mesh.primitive_torus_add(major_radius=PR + 0.035, minor_radius=0.035, major_segments=64, location=(PX, RY - 0.01, PZ), rotation=(math.pi / 2, 0, 0))
bpy.context.active_object.data.materials.append(brass); bpy.ops.object.shade_smooth()
glass = bpy.data.materials.new("port_glass"); gp = glass.node_tree.nodes["Principled BSDF"]
gp.inputs['Transmission Weight'].default_value = 1.0; gp.inputs['Roughness'].default_value = 0.04; gp.inputs['IOR'].default_value = 1.45
gN = glass.node_tree.nodes; gL = glass.node_tree.links
lp = gN.new("ShaderNodeLightPath"); tr = gN.new("ShaderNodeBsdfTransparent"); mx = gN.new("ShaderNodeMixShader")
gL.new(lp.outputs['Is Shadow Ray'], mx.inputs[0]); gL.new(gp.outputs[0], mx.inputs[1]); gL.new(tr.outputs[0], mx.inputs[2])
gL.new(mx.outputs[0], gN["Material Output"].inputs['Surface'])
ship.cyl("port_glass", (PX, RY + 0.05, PZ), (PX, RY + 0.06, PZ), PR, mat=glass, verts=64)
for k in range(3):
    a = math.radians(30 + k * 120); p = Vector((PX + math.cos(a) * (PR + 0.09), RY - 0.03, PZ + math.sin(a) * (PR + 0.09)))
    ship.cyl(f"dog{k}", p, p + Vector((0, -0.07, 0)), 0.018, mat=brass, verts=12)

# --- the table with its fiddle rail
ship.box("table", (0, 0.15, TOP - 0.025), (1.5, 1.0, 0.05), tablem, bevel=0.008)
for sgx in (-1, 1):
    ship.box(f"fiddle_x{sgx}", (sgx * 0.73, 0.15, TOP + 0.02), (0.025, 1.0, 0.04), tablem, bevel=0.005)
for sgy in (-1, 1):
    ship.box(f"fiddle_y{sgy}", (0, 0.15 + sgy * 0.485, TOP + 0.02), (1.5, 0.025, 0.04), tablem, bevel=0.005)
for sx_ in (-0.65, 0.65):
    for sy_ in (-0.25, 0.55):
        ship.box("leg", (sx_, sy_, (TOP - 0.05) / 2), (0.07, 0.07, TOP - 0.05), tablem)

# --- the log slate: a wooden frame and dark slate with wiped chalk smears (no writing)
SL = Vector((float(E("SLX", "0.3")), float(E("SLY", "-0.22")), TOP)); slr = math.radians(-14)
framem = ship.paint("slate_wood", (0.38, 0.26, 0.15), rough=0.6, grime=0.4)
frame = ship.box("slate_frame", SL + Vector((0, 0, 0.009)), (0.36, 0.27, 0.018), framem, rot=(0, 0, slr), bevel=0.003)
slm = bpy.data.materials.new("slate"); sN = slm.node_tree.nodes; sL_ = slm.node_tree.links; sp_ = sN["Principled BSDF"]
tc = sN.new("ShaderNodeTexCoord"); nz = sN.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 6
mp = sN.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1, 5, 1); sL_.new(tc.outputs['Object'], mp.inputs['Vector'])
sL_.new(mp.outputs[0], nz.inputs['Vector'])
cr = sN.new("ShaderNodeMapRange"); cr.inputs['From Min'].default_value = 0.5; cr.inputs['From Max'].default_value = 0.75
cr.inputs['To Min'].default_value = 0.04; cr.inputs['To Max'].default_value = 0.45; sL_.new(nz.outputs['Fac'], cr.inputs['Value'])
cm = sN.new("ShaderNodeMix"); cm.data_type = 'RGBA'; cm.inputs[6].default_value = (0.022, 0.024, 0.026, 1); cm.inputs[7].default_value = (0.6, 0.6, 0.58, 1)
sL_.new(cr.outputs[0], cm.inputs['Factor']); sL_.new(cm.outputs[2], sp_.inputs['Base Color']); sp_.inputs['Roughness'].default_value = 0.75
ship.box("slate", SL + Vector((0, 0, 0.0185)), (0.31, 0.22, 0.002), slm, rot=(0, 0, slr))
# a stub of chalk beside it
ship.cyl("chalk", SL + Vector((0.2, -0.13, 0.006)), SL + Vector((0.245, -0.11, 0.006)), 0.006, mat=None, verts=10)

# --- the lantern, lit
lan, lms = ph.model("wooden_lantern_01")
LX = Vector((float(E("LX", "0.36")), float(E("LY", "0.32")), TOP)); lan.location = LX; lan.rotation_euler = (0, 0, 0.5)
bpy.context.view_layer.update()
lo, hi = ph.bounds(lms); lan.location.z += TOP - lo.z; bpy.context.view_layer.update(); lo, hi = ph.bounds(lms)
flame_c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + 0.2))
fl = bpy.data.lights.new("lantern", 'POINT'); fl.energy = float(E("LANTERN", "80")); fl.color = (1.0, 0.56, 0.24); fl.shadow_soft_size = 0.02
flo = bpy.data.objects.new("lantern_light", fl); sc.collection.objects.link(flo); flo.location = flame_c
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=flame_c + Vector((0, 0, 0.01)))
fm = bpy.context.active_object; fm.name = "flame"; fm.scale = (0.7, 0.7, 1.9)
em = bpy.data.materials.new("flame"); N = em.node_tree.nodes; N.remove(N["Principled BSDF"]); e = N.new("ShaderNodeEmission")
e.inputs['Color'].default_value = (1.0, 0.62, 0.25, 1); e.inputs['Strength'].default_value = 60
em.node_tree.links.new(e.outputs[0], N["Material Output"].inputs['Surface']); fm.data.materials.append(em); fm.visible_shadow = False
lglass = bpy.data.materials.new("lantern_glass"); lg = lglass.node_tree.nodes["Principled BSDF"]
lg.inputs['Transmission Weight'].default_value = 1.0; lg.inputs['Roughness'].default_value = 0.06
lg.inputs['Base Color'].default_value = (1.0, 0.93, 0.8, 1); lg.inputs['IOR'].default_value = 1.2
_N = lglass.node_tree.nodes; _L = lglass.node_tree.links
_lp = _N.new("ShaderNodeLightPath"); _tr = _N.new("ShaderNodeBsdfTransparent"); _tr.inputs['Color'].default_value = (1.0, 0.92, 0.78, 1)
_mx = _N.new("ShaderNodeMixShader"); _L.new(_lp.outputs['Is Shadow Ray'], _mx.inputs[0])
_L.new(lg.outputs[0], _mx.inputs[1]); _L.new(_tr.outputs[0], _mx.inputs[2]); _L.new(_mx.outputs[0], _N["Material Output"].inputs['Surface'])
for o in lms:
    for sl in o.material_slots:
        if sl.material and "glass" in sl.material.name.lower():
            sl.material = lglass

# --- Sophia's china doll, fallen on its side on the table (CC-BY "China Doll - toy" by CMBC)
DOLL = "7c6f3f614592486e9124b0d84e1fde08"
droot, dms = sf.model(DOLL, height=float(E("DOLL_H", "0.34")))
DX = Vector((float(E("DX", "0.02")), float(E("DY", "-0.06")), TOP))
droot.rotation_euler = (math.radians(float(E("DOLL_RX", "90"))), math.radians(float(E("DOLL_RY", "0"))), math.radians(float(E("DOLL_RZ", "-40"))))
droot.location = DX; bpy.context.view_layer.update()
lo, hi = ph.bounds(dms); droot.location.z += TOP + 0.001 - lo.z; bpy.context.view_layer.update()
lo, hi = ph.bounds(dms); dcen = (lo + hi) / 2; print("DOLL bounds", lo, hi)

# --- outside: storm sea and sky behind the port
water = sea.water_material(deep=(0.0008, 0.01, 0.016), crest=(0.005, 0.06, 0.065), fog_color=(0.3, 0.33, 0.37))
sea.ocean(size=120, res=int(E("OCEAN_RES", "10")), scale=2.6, chop=1.8, wind=15.0, repeat=2, foam=0.3, mat=water,
          direction=60.0, loc=(0, 120, -1.2), seed=3)
fs = sea.far_sea(110, mat=water, center=(0, 120), z=-1.25)
# she is rolling: tilt the sea about the eye so the horizon rides up, slanted, across the port
oc = bpy.data.objects["Ocean"]; piv = bpy.data.objects.new("roll", None); sc.collection.objects.link(piv)
piv.location = (0, -0.95, 1.05)
for o in (oc, fs):
    o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()
piv.rotation_euler = (math.radians(float(E("PITCH", "7.5"))), math.radians(float(E("ROLLDEG", "12"))), 0)
rot, el = T.sky_with_sun_at(E("SKY", "kloofendal_overcast_puresky"), 90, strength=float(E("SKY_K", "0.3")))
# cold daylight through the port into the cabin
pl = bpy.data.lights.new("port_light", 'AREA'); pl.shape = 'DISK'; pl.size = 2 * PR; pl.energy = float(E("PORTL", "25"))
pl.color = (0.62, 0.74, 0.92)
plo = bpy.data.objects.new("port_light", pl); sc.collection.objects.link(plo); plo.location = (PX, RY + 0.16, PZ)
plo.rotation_euler = (Vector((PX + 0.2, 0.0, TOP)) - plo.location).to_track_quat('-Z', 'Y').to_euler()
plo.visible_camera = False; plo.visible_glossy = False; plo.visible_transmission = False
w = sc.world
# cabin air
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.05, RZ / 2)); air = bpy.context.active_object; air.name = "cabin_air"
air.scale = (2 * RX - 0.05, 2 * RY - 0.12, RZ - 0.05)
am = bpy.data.materials.new("air"); N = am.node_tree.nodes; N.remove(N["Principled BSDF"])
vs = N.new("ShaderNodeVolumeScatter"); vs.inputs['Density'].default_value = float(E("FOG", "0.03")); vs.inputs['Anisotropy'].default_value = 0.4
am.node_tree.links.new(vs.outputs[0], N["Material Output"].inputs['Volume']); air.data.materials.append(am); air.visible_shadow = False

if E("CLIP"):
    import clipcheck
    clipcheck.check("c_cabin", limit=40); sys.exit(0)

cam_loc = Vector((float(E("CX", "0.12")), float(E("CY", "-0.95")), float(E("CZ", "1.05"))))
tgt = Vector((float(E("TX", "-0.08")), float(E("TY", "0.5")), float(E("TZ", "0.85"))))
T.C.camera(cam_loc, tgt, lens=float(E("LENS", "32")), fstop=float(E("FSTOP", "2.8")), focus=(dcen - cam_loc).length)
T.C.finish(OUT, cine={"sat": 1.1, "exposure": float(E("EXPO", "0.4")), "contrast": 1.1}, bloom=0.5)
print("RENDERED", OUT)
