"""A merchant brigantine's bilge pump of the 1870s (new shared asset for Part 4).

Common-pump type, as fitted either side of the mainmast: an elm/pine pump-tree (bored log, ~0.3 m square
outside, 0.13 m bore) bound with iron hoops, running from the deck down to the bilge well; a cast spout near
the top; a brake (long wooden lever) on an iron pin in a crutch, linked to the spear (pump rod). At the foot of
the spear, the upper box (piston): a wooden cylinder with a leather flap valve; at the bottom of the tree, the
lower box (foot valve), the same again, fixed.

    pump(name, base, intact=True | False, coll=None) -> dict of objects
    dismantled(): the spear drawn out and laid on deck, the upper box off it, its leather valve lifted,
    a hammer and a marline-spike beside them.
"""
import math, random
import bpy
from mathutils import Vector, Matrix
import ship, ph
import p4

BORE = 0.065; TREE = 0.15         # bore radius, outer half-size of the pump-tree


def materials():
    if "pump_wood" in bpy.data.materials:
        g = bpy.data.materials
        return dict(wood=g["pump_wood"], iron=g["pump_iron"], leather=g["pump_leather"], brake=g["pump_brake"], dark=g["pump_bore"])
    wood = ship.paint("pump_wood", (0.30, 0.20, 0.12), rough=0.6, grime=0.55, scale=8, chips=0.4, under=(0.42, 0.3, 0.18))
    brake = ship.wood("weathered_planks", 0.5, wet=0.2, tint=(0.95, 0.75, 0.55), name="pump_brake")
    iron = ship.paint("pump_iron", (0.05, 0.035, 0.028), rough=0.65, grime=0.7, scale=14, chips=0.6, under=(0.32, 0.12, 0.05))
    iron.node_tree.nodes["Principled BSDF"].inputs['Metallic'].default_value = 0.55
    leather = ship.paint("pump_leather", (0.16, 0.075, 0.035), rough=0.5, grime=0.5, scale=20, wet=0.4)
    dark = p4.mat("pump_bore", (0.01, 0.008, 0.006), rough=0.9)
    return dict(wood=wood, iron=iron, leather=leather, brake=brake, dark=dark)


def _tree(name, base, h, m, coll):
    """Square-ish pump-tree with chamfered corners (an octagon), iron hoops, the bore shown dark at the top."""
    out = []
    out.append(ship.cyl(f"{name}_tree", base + Vector((0, 0, -0.4)), base + Vector((0, 0, h)), TREE * 1.08, mat=m["wood"], verts=8, coll=coll))
    for k, zz in enumerate((0.12, h * 0.45, h - 0.12)):
        out.append(ship.cyl(f"{name}_hoop{k}", base + Vector((0, 0, zz - 0.025)), base + Vector((0, 0, zz + 0.025)), TREE * 1.13, mat=m["iron"], verts=8, coll=coll))
    out.append(ship.cyl(f"{name}_bore", base + Vector((0, 0, h - 0.02)), base + Vector((0, 0, h + 0.004)), BORE, mat=m["dark"], verts=24, coll=coll))
    # spout: a short square trough out of the side, 0.3 m below the top
    sp = base + Vector((TREE + 0.09, 0, h - 0.34))
    out.append(ship.box(f"{name}_spout", sp, (0.2, 0.09, 0.07), m["iron"], bevel=0.008, coll=coll))
    return out


def spear(name, M, m, coll, length=2.6, box_on=True, valve_open=0.0):
    """The pump rod with the upper box on its foot. M places it (rod axis = local +Z, foot at the origin)."""
    out = []
    rod = ship.cyl(f"{name}_spear", (0, 0, 0.16), (0, 0, length), 0.022, mat=m["iron"], verts=12, coll=coll)
    eye = ship.cyl(f"{name}_spear_eye", (-0.03, 0, length), (0.03, 0, length), 0.035, mat=m["iron"], verts=14, coll=coll)
    out += [rod, eye]
    if box_on:
        out += upper_box(f"{name}_box", Matrix(), m, coll, valve_open)
    for o in out:
        o.matrix_world = M @ o.matrix_world
    return out


def upper_box(name, M, m, coll, valve_open=0.0, grit=0.0):
    """Wooden piston (0.12 m tall) with an iron strap and a leather flap valve hinged on its top face.
    valve_open: degrees the flap is lifted. grit > 0 adds coal grit and wood shavings jammed under the flap."""
    out = []
    out.append(ship.cyl(f"{name}_body", (0, 0, 0), (0, 0, 0.12), BORE * 0.97, mat=m["wood"], verts=20, coll=coll))
    out.append(ship.cyl(f"{name}_cup", (0, 0, 0.0), (0, 0, 0.045), BORE * 1.0, mat=m["leather"], verts=20, coll=coll))
    out.append(ship.box(f"{name}_strap", (0, 0, 0.14), (0.02, BORE * 1.6, 0.05), m["iron"], coll=coll))
    flap = ship.cyl(f"{name}_flap", (0, 0, 0.0), (0, 0, 0.008), BORE * 0.8, mat=m["leather"], verts=20, coll=coll)
    flap.matrix_world = Matrix.Translation((-BORE * 0.8, 0, 0.122)) @ Matrix.Rotation(math.radians(-valve_open), 4, 'Y') @ Matrix.Translation((BORE * 0.8, 0, 0))
    out.append(flap)
    if grit:
        rng = random.Random(7)
        cm = p4.mat("coal_grit", (0.012, 0.011, 0.012), rough=0.35)
        sh = p4.mat("shaving", (0.62, 0.42, 0.24), rough=0.7)
        for k in range(int(60 * grit)):
            a = rng.uniform(0, 6.28); r = rng.uniform(0, BORE * 0.8)
            c = Vector((r * math.cos(a), r * math.sin(a), 0.124 + rng.uniform(0, 0.006)))
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rng.uniform(0.002, 0.006), location=c)
            g = bpy.context.active_object; g.name = f"{name}_grit"; g.data.materials.append(cm)
            g.scale = (1, rng.uniform(0.6, 1), rng.uniform(0.5, 0.9)); out.append(g)
            if coll:
                ship._move(g, coll)
        for k in range(int(5 * grit)):                     # curled shavings (thin twisted strips)
            a = rng.uniform(0, 6.28); c = Vector((0.03 * math.cos(a), 0.03 * math.sin(a), 0.128))
            pts = [c + Vector((0.012 * math.cos(t * 5), 0.012 * math.sin(t * 5), 0.002 * t)) for t in [i / 10 for i in range(11)]]
            out.append(ship.rope(f"{name}_shaving", pts, 0.0015, sh, coll=coll))
    for o in out:
        o.matrix_world = M @ o.matrix_world
    return out


SCAN_TOP = "24f8540b2cd8478b83053ff368952474"     # "Top end of pump tube", Viking Ship Museum (CC BY), museum scan
SCAN_FOOT = "7985bc32f0ef4b7698f3cbb47bf2613e"    # "Lower end of a ship's pump (pompvoet)", Batavialand (CC BY), scan


def scan_top(name, base, H, coll=None, rot=0.0):
    """The real pump-tree top (photoscan) standing on deck at `base`, scaled to H above the deck, decimated."""
    import skfab
    if "_scan_cache" not in globals():          # load once, decimate for real (25%), then share the meshes
        r0, ms0 = skfab.model(SCAN_TOP, height=H + 0.05, name="pumpscan_src")
        dg = bpy.context.evaluated_depsgraph_get()
        for o in ms0:
            d = o.modifiers.new("dec", "DECIMATE"); d.ratio = 0.25
            bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); o.modifiers.clear(); old = o.data; o.data = me
            bpy.data.meshes.remove(old)
        globals()["_scan_cache"] = (r0, ms0)
        r, ms = r0, ms0; r.name = name + "_scan"
    else:
        r0, ms0 = globals()["_scan_cache"]
        r = bpy.data.objects.new(name + "_scan", None); bpy.context.scene.collection.objects.link(r)
        r.matrix_world = Matrix()
        ms = []
        for o in ms0:
            c = o.copy(); c.data = o.data; bpy.context.scene.collection.objects.link(c)
            c.parent = r; c.matrix_parent_inverse = o.matrix_parent_inverse.copy(); ms.append(c)
    for o in ms:
        if coll:
            ship._move(o, coll)
    if coll:
        ship._move(r, coll)
    r.matrix_world = Matrix.Translation(Vector(base) + Vector((0, 0, -0.05))) @ Matrix.Rotation(rot, 4, 'Z')
    return [r] + ms


def pump(name, base, intact=True, coll=None, brake_angle=0.0, scan=True):
    """One pump at world point `base` on deck. intact=False: spear out, brake unshipped (laid on deck).
    scan=True uses the museum photoscan of a real pump-tree top for the part above the deck."""
    base = Vector(base)
    m = materials(); out = []
    H = 1.05
    if scan:
        out += scan_top(name, base, H, coll, rot=math.pi)
    else:
        out += _tree(name, base, H, m, coll)
    # crutch (two iron cheeks) and pin for the brake, on the fore side of the tree
    for sg in (1, -1):
        out.append(ship.box(f"{name}_cheek", base + Vector((-TREE - 0.05, sg * 0.05, H + 0.12)), (0.06, 0.018, 0.34), m["iron"], coll=coll))
    pin = base + Vector((-TREE - 0.05, 0, H + 0.24))
    out.append(ship.cyl(f"{name}_pin", pin + Vector((0, -0.08, 0)), pin + Vector((0, 0.08, 0)), 0.012, mat=m["iron"], verts=10, coll=coll))
    if intact:
        a = math.radians(brake_angle)
        d = Vector((math.cos(a), 0, math.sin(a)))
        b0 = pin - d * 0.35; b1 = pin + d * 1.9
        out.append(ship.box(f"{name}_brake", (b0 + b1) / 2, ((b1 - b0).length, 0.07, 0.08), m["brake"], rot=(0, -a, 0), bevel=0.01, coll=coll))
        hook = pin - d * 0.3
        out += spear(f"{name}", Matrix.Translation(base + Vector((0, 0, H - 2.55 + 0.25))), m, coll, length=2.55 + (hook.z - (base.z + H)) - 0.25)
    return out


def dismantled_parts(name, M, coll=None, grit=1.0):
    """Parts laid out on deck in the frame M (deck surface at local z=0, x fore-aft):
    the spear (2.6 m), the upper box off it on its side with the valve lifted, the brake, a hammer."""
    m = materials(); out = []
    sp = spear(f"{name}_out", M @ Matrix.Translation((0.4, -0.5, 0.025)) @ Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Rotation(0.04, 4, 'X'),
               m, coll, box_on=False)
    out += sp
    out += upper_box(f"{name}_ub", M @ Matrix.Translation((0.05, -0.18, BORE * 0.97)) @ Matrix.Rotation(math.radians(80), 4, 'X') @ Matrix.Rotation(0.4, 4, 'Z'),
                     m, coll, valve_open=55, grit=grit)
    br = ship.box(f"{name}_brake_off", (0, 0, 0), (2.25, 0.07, 0.08), m["brake"], bevel=0.01, coll=coll)
    br.matrix_world = M @ Matrix.Translation((1.0, 0.55, 0.04)) @ Matrix.Rotation(0.08, 4, 'Z')
    out.append(br)
    hm, hms = ph.model("cross_pein_hammer")
    hm.matrix_world = M @ Matrix.Translation((-0.35, -0.05, 0.016)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Rotation(0.6, 4, 'Y')
    out += [hm] + hms
    return out
