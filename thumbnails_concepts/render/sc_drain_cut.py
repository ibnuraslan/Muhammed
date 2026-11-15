"""Drain thumbnail plate: cutaway of the courtyard ground. On top: wet concrete, the cast-iron grate, one slightly lighter
patch. Cut open below: the soil, and the sealed plastic tub of rings right under the patch.
  python sc_drain_cut.py [--pct 25] [--samples 64] [--out plates/drain.png]"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "lib"))
import numpy as np
import bpy
from mathutils import Vector
from common import reset, camera, point_at, area_light
from kit import pbr, box, cyl
import ph, dd

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
s = reset(res=(1920, 1080), samples=arg("--samples", 160), exposure=0.0)
s.render.resolution_percentage = arg("--pct", 100)
s.cycles.max_bounces = 10; s.cycles.transmission_bounces = 10; s.cycles.glossy_bounces = 6

w = bpy.data.worlds.new("W"); s.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs['Color'].default_value = (0.006, 0.009, 0.016, 1)
w.node_tree.nodes["Background"].inputs['Strength'].default_value = 1.0

CUT_KEEP = []          # objects cut by the section plane y = 0


def section(o):
    """Remove everything in front of the plane y = 0 (the cutaway)."""
    m = o.modifiers.new("cut", 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = CUTTER; m.solver = 'EXACT'
    return o


bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2.5, 0)); CUTTER = bpy.context.active_object
CUTTER.scale = (10, 5, 10); CUTTER.name = "Cutter"; CUTTER.hide_render = True; CUTTER.display_type = 'WIRE'

# ---------------------------------------------------------------- materials
conc = ph.texture("concrete_floor_02", scale=1.6, tint=(0.42, 0.43, 0.45), name="Concrete")
pc = conc.node_tree.nodes["Principled BSDF"]; pc.inputs['Coat Weight'].default_value = 0.75; pc.inputs['Coat Roughness'].default_value = 0.08
patch = ph.texture("concrete_floor_02", scale=3.1, tint=(1.3, 1.28, 1.22), name="Patch")
pp = patch.node_tree.nodes["Principled BSDF"]; pp.inputs['Coat Weight'].default_value = 0.5; pp.inputs['Coat Roughness'].default_value = 0.1
soil = ph.texture("brown_mud_rocks_01", scale=2.2, tint=(1.0, 0.92, 0.82), name="Soil")
grav = ph.texture("gravel_floor", scale=3.0, tint=(0.5, 0.5, 0.5), name="Gravel")
wall = ph.texture("plastered_stone_wall", scale=1.2, tint=(0.5, 0.48, 0.45), name="Wall")
iron = pbr("Iron", (0.025, 0.024, 0.023), 0.45, 0.8); iron.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.6

# ---------------------------------------------------------------- ground: slab, patch, soil, gravel bed
SL = 0.075                              # slab thickness
PX, PY, PW, PD = -0.08, 0.16, 0.25, 0.30       # patch centre / size (it reaches the cut face, so its section shows too)
TUB = (0.17, 0.12, 0.075)
TZ = -SL - TUB[2] / 2 - 0.004
# slab = four blocks around the patch hole
for nm, (x0, x1, y0, y1) in {"SlabL": (-3, PX - PW / 2, -0.3, 4), "SlabR": (PX + PW / 2, 3, -0.3, 4),
                             "SlabB": (PX - PW / 2, PX + PW / 2, PY + PD / 2, 4)}.items():
    section(box(nm, ((x0 + x1) / 2, (y0 + y1) / 2, -SL / 2), (x1 - x0, y1 - y0, SL), conc))
section(box("Patch", (PX, PY - 0.15, -SL / 2 - 0.0005), (PW, PD + 0.3, SL + 0.001), patch))   # extends past the cut
# soil under the slab: one block with the pit dug for the tub (tight round it)
soilb = section(box("Soil", (0, 1.5, -SL - 0.5), (6, 3.6, 1.0), soil))
pit = box("Pit", (PX, 0.03, TZ), (TUB[0] + 0.012, TUB[1] + 0.012, TUB[2] + 0.012), soil); pit.hide_render = True; pit.display_type = 'WIRE'
pm = soilb.modifiers.new("pit", 'BOOLEAN'); pm.operation = 'DIFFERENCE'; pm.object = pit; pm.solver = 'EXACT'
soilb.modifiers.move(soilb.modifiers.find("pit"), 0)

# the drain: cast-iron grate flush in the slab to the right, dark shaft under it
GX = 0.27
for nm, (x0, x1, y0, y1) in {"SlabGl": (PX + PW / 2, GX - 0.15, -0.3, 4)}.items():
    pass
gr_root = []
for k in range(9):
    section(box(f"GBar{k}", (GX - 0.12 + k * 0.03, 0.2, -0.012), (0.012, 0.3, 0.024), iron, bevel=0.002))
section(box("GFrameF", (GX, 0.05, -0.012), (0.28, 0.012, 0.024), iron)); section(box("GFrameB", (GX, 0.35, -0.012), (0.28, 0.012, 0.024), iron))

# house wall behind (dark, for the words)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 2.6, 1.2), rotation=(math.pi / 2, 0, 0)); wb = bpy.context.active_object
wb.scale = (8, 3, 1); wb.data.materials.append(wall)
section(box("Step", (-0.9, 2.45, 0.08), (1.0, 0.3, 0.16), conc))

# ---------------------------------------------------------------- the tub, sealed, cut in half by the section
rng = np.random.default_rng(4)
tub = dd.container("Tub", (PX, 0.03, TZ - TUB[2] / 2), size=TUB, rot_z=0.0, dirt=0.75, lid_open=0.0)
lid = bpy.data.objects["TubLid"]; lid.parent = None
lid.location = (PX, 0.03, TZ + TUB[2] / 2 + 0.003); lid.rotation_euler = (0, 0, 0)
for o in list(bpy.data.objects):
    if o.name.startswith("Tub") and o.type == 'MESH' and o.name not in ("TubMud",):
        pass
# drop the rain droplets (they belong to the rainy shot, not the buried tub)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.data.materials and o.data.materials[0].name == "TubDrop":
        bpy.data.objects.remove(o)
section(tub); section(lid); section(bpy.data.objects["TubMud"])
hero, items = dd.fill_container(tub, TUB, rng, n_rings=14, n_ear=6, hero_scale=1.5)
hero.location = Vector((PX + 0.0, 0.035, TZ - TUB[2] / 2 + 0.024)); hero.rotation_euler = (1.05, 0.0, 0.12)
for it in items:                         # keep only the pieces behind the cut
    if it.location.y < 0.012:
        it.location.y = 0.012 + (it.location.y % 0.03)

# ---------------------------------------------------------------- light
# the "exhibit" spot on the tub section, warm and hard
bpy.ops.object.light_add(type='SPOT', location=(PX - 0.12, -0.5, 0.05)); sp = bpy.context.active_object
sp.data.energy = 7; sp.data.spot_size = math.radians(18); sp.data.spot_blend = 1.0; sp.data.shadow_soft_size = 0.01
sp.data.color = (1.0, 0.86, 0.66); point_at(sp, (PX, 0.06, TZ))
# a second tiny hard key just for the stone sparkle
bpy.ops.object.light_add(type='SPOT', location=(PX + 0.2, -0.45, 0.05)); sp2 = bpy.context.active_object
sp2.data.energy = 6; sp2.data.spot_size = math.radians(6); sp2.data.shadow_soft_size = 0.002; point_at(sp2, hero.location)
# cool night light on the courtyard surface (raking, shows the lighter patch)
nl = area_light((-1.2, 1.8, 1.6), (0, 0, 0), 1.2, 110, (0.55, 0.68, 1.0)); point_at(nl, (PX, 0.3, 0))
# faint cool fill on the section face so the soil reads
fl = area_light((0.1, -0.9, -0.2), (0, 0, 0), 1.6, 3.5, (0.5, 0.6, 0.85)); point_at(fl, (0, 0, -0.25))

# sparkle cards: small bright panels round the camera that only the stones see (a diamond in a black world reads black)
from kit import emissive
em = emissive("Card", (1.0, 0.95, 0.88), 40.0)
for k, (x, z) in enumerate(((-0.12, 0.02), (0.14, 0.05), (0.02, -0.1), (-0.05, 0.12), (0.2, -0.05))):
    bpy.ops.mesh.primitive_plane_add(size=0.03, location=(PX + x, -0.25, TZ + z)); cd = bpy.context.active_object
    cd.data.materials.append(em); point_at(cd, hero.location); cd.rotation_euler.rotate_axis('X', math.pi / 2)
    cd.visible_camera = False; cd.visible_diffuse = False; cd.visible_glossy = False
# ---------------------------------------------------------------- camera
CL = (0.0, -0.52, 0.07)
cam = camera(CL, (PX + 0.06, 0.2, -0.105), lens=40)
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (Vector(CL) - Vector((PX, 0.05, TZ))).length
cam.data.dof.aperture_fstop = 5.6
out = arg("--out", os.path.join(HERE, "plates", "drain.png"))
os.makedirs(os.path.dirname(out), exist_ok=True)
s.render.filepath = out; s.render.image_settings.color_depth = '8'
bpy.ops.render.render(write_still=True)
print("[plate]", out)
