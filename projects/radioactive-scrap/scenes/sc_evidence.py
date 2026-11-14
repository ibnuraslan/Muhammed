"""Evidence set: the physical-fact shots of "They Paid $30 for Radioactive Scrap" (STORYBOARD_v2).

Abstract lines of the script become real objects the camera can study, never slides:
  desk_ist  a printed Istanbul street map on a desk under a lamp; a red felt pen draws the packages' route
  desk_tr   a printed map of north-west Turkey: the 1994 export permit stamped over Ankara; later the retraced
            route with pins and a "~90 km" measuring line to the smelting works
  void      objects on black under one hard top light: the container cut open to show its lead lining and the
            source well; the scrap pile as stacked plates lifted off the capsule while a meter needle climbs
  model     a white card architectural model of the yard and the houses around it; red rings spread from the
            containers over the neighbours' roofs
  calendar  the kitchen wall calendar, December 1998, two dates ringed in red pen under a swinging bare bulb
  tally     chalk tally marks on the concrete-block shield wall, the tenth stroke drawn as we watch
  board     the ward bed board: eighteen bed cards, ten get a red magnet
  cork      the investigators' cork board: two printed source lists, red string between rows that disagree
  binders   forty-six binders on a steel shelf, one per radiotherapy centre, each ticked as the camera tracks

No real logos, no real names, no invented numbers: every figure on a prop is in the script.
Everything that moves is a keyed transform or a frame driver (plays in any external render)."""
import math, os
import bpy
from mathutils import Vector, Euler, Quaternion
from kit import *
from rs_kit import *
from durs import dur

EXPOSURE = 0.0
BOUNCES = 6
HERE = os.path.dirname(os.path.abspath(__file__))
STILLS = os.path.join(HERE, "..", "out", "v3")
INK = (0.05, 0.05, 0.06)
RED = (0.62, 0.04, 0.03)


# ------------------------------------------------------------------------------------------------ helpers
def mat_paper(name, col=(0.84, 0.8, 0.7), rough=0.85):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.08
    mx.inputs[6].default_value = (*col, 1); L.new(nz.outputs['Color'], mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.04; L.new(nz.outputs['Fac'], bm.inputs['Height'])
    L.new(bm.outputs['Normal'], p.inputs['Normal']); p.inputs['Roughness'].default_value = rough
    return m


def ink(name, col=INK, rough=0.6):
    return pbr(name, col, rough)


def flat_text(name, s, loc, size, mat, rz=0.0, align='CENTER'):
    o = text_obj(name, s, loc, size, mat, rot=(0, 0, rz), extrude=0.0, align=align)
    return o


def wall_text(name, s, loc, size, mat, align='CENTER'):
    return text_obj(name, s, loc, size, mat, rot=(math.radians(90), 0, 0), extrude=0.0, align=align)


def poly_curve(name, pts, bevel, mat, closed=False, reveal=None):
    """A thin tube through world points. reveal=(frame0, frame1): the line draws itself (bevel_factor_end driver)."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = bevel; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1); sp.use_cyclic_u = closed
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o); cu.materials.append(mat)
    if reveal:
        set_reveal(o, *reveal)
    return o


def set_reveal(o, f0, f1):
    cu = o.data
    try:
        cu.driver_remove("bevel_factor_end")
    except Exception:
        pass
    d = cu.driver_add("bevel_factor_end").driver; d.type = 'SCRIPTED'
    d.expression = f"min(1.0, max(0.0, (frame - {f0:.1f}) / {max(1.0, f1 - f0):.1f}))"
    cu.bevel_factor_mapping_end = 'SPLINE'


def along(pts, k):
    """Point at fraction k (0..1) of a polyline's length."""
    seg = [(Vector(pts[i]), Vector(pts[i + 1])) for i in range(len(pts) - 1)]
    L = sum((b - a).length for a, b in seg); s = max(0.0, min(1.0, k)) * L
    for a, b in seg:
        l = (b - a).length
        if s <= l:
            return a.lerp(b, s / max(l, 1e-9))
        s -= l
    return Vector(pts[-1])


def photo_print(name, img_path, loc, w, rz, border=0.012):
    """A glossy photo print with a white border, lying on the desk (image packed into the .blend)."""
    m = bpy.data.materials.new(name + "M"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    if os.path.exists(img_path):
        tx = N.new("ShaderNodeTexImage"); img = bpy.data.images.load(img_path); img.pack(); tx.image = img
        L.new(tx.outputs['Color'], p.inputs['Base Color']); asp = img.size[1] / max(1, img.size[0])
    else:
        p.inputs['Base Color'].default_value = (0.3, 0.3, 0.3, 1); asp = 0.425
    p.inputs['Roughness'].default_value = 0.25
    h = w * asp
    back = box(name + "Card", (0, 0, 0), (w + 2 * border, h + 2 * border, 0.0008), pbr(name + "W", (0.86, 0.85, 0.82), 0.4))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.00045)); im = bpy.context.active_object
    im.scale = (w, h, 1); im.data.materials.append(m); im.parent = back
    back.location = loc; back.rotation_euler = (0, 0, rz)
    return back


def ll(lon, lat, B):
    """lon/lat -> local paper xy (metres) for map bounds B=(lon0, lon1, lat0, lat1, W)."""
    lon0, lon1, lat0, lat1, W = B
    lonc, latc = (lon0 + lon1) / 2, (lat0 + lat1) / 2
    kx = 111.32 * math.cos(math.radians(latc)); span = (lon1 - lon0) * kx
    s = W / span
    return Vector(((lon - lonc) * kx * s, (lat - latc) * 111.0 * s, 0))


def ngon(name, pts, z, mat):
    me = bpy.data.meshes.new(name); me.from_pydata([(p.x, p.y, z) for p in pts], [], [list(range(len(pts)))]); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(mat)
    return o


def paper_map(name, B, H, seas, roads, labels, ctr=(0, 0, 0.76), rz=0.0):
    """Printed map sheet: cream paper, muted blue-grey water, thin grey roads, small dark labels. Returns
    (root, to_world) where to_world(lon, lat) gives the world point on the sheet."""
    W = B[4]; root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    paper = box(name + "Sheet", (0, 0, 0), (W + 0.04, H + 0.04, 0.0006), mat_paper(name + "Paper")); paper.parent = root
    water = pbr(name + "Water", (0.5, 0.58, 0.63), 0.8)
    for i, poly in enumerate(seas):
        ngon(f"{name}Sea{i}", [ll(a, b, B) for a, b in poly], 0.0004, water).parent = root
    road_m = pbr(name + "Road", (0.6, 0.57, 0.53), 0.8)
    for i, rd in enumerate(roads):
        poly_curve(f"{name}Road{i}", [ll(a, b, B) + Vector((0, 0, 0.0005)) for a, b in rd], 0.0005, road_m).parent = root
    lab_m = ink(name + "Ink")
    for s, lon, lat, size in labels:
        flat_text(f"{name}L", s, ll(lon, lat, B) + Vector((0, 0, 0.0006)), size, lab_m).parent = root
    root.location = ctr; root.rotation_euler = (0, 0, rz); bpy.context.view_layer.update()

    def to_world(lon, lat, dz=0.0):
        return root.matrix_world @ (ll(lon, lat, B) + Vector((0, 0, dz)))
    return root, to_world


def pin(name, loc, col=RED):
    head = pbr(name + "H", col, 0.3); steel = pbr(name + "S", (0.7, 0.7, 0.72), 0.25, 1.0)
    p = join([cyl("PinShaft", (0, 0, 0.012), 0.0009, 0.024, steel, verts=8),
              cyl("PinHead", (0, 0, 0.028), 0.006, 0.012, head, verts=16)], name)
    p.location = loc
    return p


def desk(name="Desk"):
    top = box(name + "Top", (0, 0, 0.74), (1.8, 1.1, 0.04), wood(name + "Wood", dark=(0.05, 0.028, 0.015), light=(0.16, 0.09, 0.045)), bevel=0.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(name + "Leg", (sx * 0.84, sy * 0.48, 0.36), (0.05, 0.05, 0.72), pbr(name + "LegM", (0.05, 0.03, 0.02), 0.5))
    box("Floor", (0, 0, -0.01), (20, 20, 0.02), pbr("FloorDark", (0.03, 0.028, 0.026), 0.6))
    return top


def lamp_key(loc, target, energy=60, col=(1.0, 0.8, 0.58), size=0.35, name="DeskLamp"):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = col; l.spot_size = math.radians(70); l.spot_blend = 0.6
    l.shadow_soft_size = size
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(loc) - Vector(target)).to_track_quat('Z', 'Y').to_euler()
    return o


def area(loc, target, energy, size, col=(1, 1, 1), name="Area"):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = col
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(loc) - Vector(target)).to_track_quat('Z', 'Y').to_euler()
    return o


def dark_world(strength=0.02, col=(0.05, 0.05, 0.055)):
    w = bpy.data.worlds.new("Dark"); bpy.context.scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs['Color'].default_value = (*col, 1); bg.inputs['Strength'].default_value = strength
    bpy.context.scene.cycles.sample_clamp_indirect = 3.0


def felt_pen(name="Pen", col=RED):
    body = pbr(name + "B", (0.06, 0.06, 0.07), 0.4); cap = pbr(name + "C", col, 0.35)
    return join([cyl("PenBody", (0, 0, 0.075), 0.0055, 0.13, body, verts=16), cyl("PenTip", (0, 0, 0.004), 0.0022, 0.012, cap, verts=12),
                 cyl("PenBand", (0, 0, 0.14), 0.006, 0.02, cap, verts=16)], name)


# ------------------------------------------------------------------------------------------------ maps (approximate, simplified)
IST = (28.6, 29.25, 40.92, 41.2, 0.86)                       # Istanbul sheet: lon0, lon1, lat0, lat1, width (m)
IST_SEAS = [
    [(28.6, 40.92), (28.6, 40.985), (28.75, 40.975), (28.85, 40.975), (28.95, 41.0), (29.0, 41.015), (29.03, 41.0), (29.07, 40.98),
     (29.12, 40.96), (29.2, 40.93), (29.25, 40.92)],                                   # Sea of Marmara (north shore)
    [(29.0, 41.015), (29.02, 41.04), (29.04, 41.08), (29.06, 41.12), (29.08, 41.16), (29.1, 41.2), (29.13, 41.2), (29.11, 41.16),
     (29.08, 41.11), (29.06, 41.07), (29.04, 41.03), (29.03, 41.0)],                  # Bosphorus
    [(28.95, 41.02), (28.97, 41.04), (28.99, 41.05), (28.995, 41.045), (28.975, 41.03), (28.96, 41.017)],   # Golden Horn
    [(28.74, 40.995), (28.73, 41.02), (28.75, 41.045), (28.77, 41.03), (28.775, 41.0)],                     # Küçükçekmece lake
]
IST_ROADS = [[(28.6, 41.03), (28.7, 41.04), (28.8, 41.05), (28.88, 41.04), (28.95, 41.03)],
             [(28.8, 40.98), (28.8, 41.05), (28.82, 41.12), (28.85, 41.2)],
             [(28.65, 40.99), (28.75, 41.0), (28.9, 41.01), (28.98, 41.08), (29.0, 41.15)],
             [(28.88, 41.04), (28.86, 41.08), (28.9, 41.14)]]
IST_LABELS = [("İSTANBUL", 28.95, 40.995, 0.024), ("İKİTELLİ", 28.79, 41.078, 0.016), ("Küçükçekmece", 28.75, 40.985, 0.012),
              ("MARMARA DENİZİ", 28.8, 40.945, 0.018), ("Boğaziçi", 29.12, 41.1, 0.013), ("Bakırköy", 28.87, 40.99, 0.011),
              ("Bağcılar", 28.85, 41.04, 0.011), ("Esenler", 28.88, 41.06, 0.011), ("Avcılar", 28.72, 40.985, 0.011),
              ("Başakşehir", 28.8, 41.1, 0.011), ("Halkalı", 28.77, 41.035, 0.011), ("Eyüp", 28.93, 41.07, 0.011)]
for _i in range(9):            # minor street grid: thin, lighter lines so the sheet reads as a city map
    IST_ROADS.append([(28.62 + _i * 0.07, 40.98 + 0.004 * _i), (28.64 + _i * 0.07, 41.19)])
    IST_ROADS.append([(28.6, 41.0 + _i * 0.022), (29.0, 41.006 + _i * 0.022)])
P_BUILDING = (28.885, 41.045); P_LOT = (28.797, 41.061); P_YARD = (28.789, 41.066); P_SCRAP = (28.705, 41.035)
ROUTE1 = [P_BUILDING, (28.87, 41.045), (28.84, 41.048), (28.81, 41.053), (28.8, 41.058), P_LOT, P_YARD]
ROUTE2 = [P_YARD, (28.78, 41.06), (28.75, 41.05), (28.72, 41.04), P_SCRAP]

TR = (26.4, 33.6, 39.5, 42.1, 0.9)                            # north-west Turkey sheet
TR_SEAS = [
    [(26.4, 42.1), (26.4, 41.9), (27.6, 41.75), (28.2, 41.5), (29.0, 41.25), (29.6, 41.17), (30.4, 41.2), (31.4, 41.3), (32.4, 41.75),
     (33.6, 42.0), (33.6, 42.1)],                                                       # Black Sea
    [(26.7, 40.42), (27.2, 40.65), (27.6, 40.95), (28.2, 41.0), (28.95, 41.0), (29.1, 40.85), (29.5, 40.75), (29.95, 40.75),
     (29.4, 40.6), (28.9, 40.4), (28.0, 40.35), (27.4, 40.3)],                          # Sea of Marmara
    [(26.4, 40.4), (26.7, 40.42), (26.6, 40.1), (26.4, 39.9)],                          # Dardanelles / Aegean edge
]
TR_ROADS = [[(28.95, 41.0), (29.9, 40.78), (30.4, 40.75), (31.6, 40.75), (32.85, 39.93)], [(28.95, 41.0), (27.5, 41.4), (26.6, 41.7)]]
TR_LABELS = [("İstanbul", 28.95, 41.12, 0.014), ("ANKARA", 32.85, 39.82, 0.016), ("Karadeniz", 31.0, 41.8, 0.014),
             ("Marmara", 28.4, 40.68, 0.011)]
T_IST = (28.95, 41.02); T_ANK = (32.85, 39.93); T_SMELT = (29.95, 40.82)


# ------------------------------------------------------------------------------------------------ build
def build(variant=None):
    v = variant or "void"
    c = {"v": v}
    bpy.context.scene.view_settings.exposure = 0.0
    if v in ("desk_ist", "desk_tr"):
        dark_world(0.04)
        top = desk()
        if v == "desk_ist":
            root, W = paper_map("IstMap", IST, 0.56, IST_SEAS, IST_ROADS, IST_LABELS, ctr=(0, 0, 0.761), rz=math.radians(-4))
            c["W"] = W
            ink_r = pbr("RouteInk", RED, 0.55)
            r1 = [W(a, b, 0.0008) for a, b in ROUTE1]; r2 = [W(a, b, 0.0008) for a, b in ROUTE2]
            c["route1"] = poly_curve("Route1", r1, 0.0016, ink_r, reveal=(1, 2)); c["r1"] = r1
            c["route2"] = poly_curve("Route2", r2, 0.0016, ink_r, reveal=(1, 2)); c["r2"] = r2
            for nm, p in (("PinBuilding", P_BUILDING), ("PinYard", P_YARD), ("PinScrap", P_SCRAP)):
                c[nm] = pin(nm, W(*p)); c[nm + "_z"] = c[nm].location.z
            ph1 = os.path.join(STILLS, "building_ch1_2b", "plate.png"); ph2 = os.path.join(STILLS, "ikitelli_ch1_4a", "plate.png")
            c["photo1"] = photo_print("Photo1", ph1, (0.52, 0.28, 0.7625), 0.24, math.radians(8))
            c["photo2"] = photo_print("Photo2", ph2, (0.56, -0.12, 0.7625), 0.22, math.radians(-6))
        else:
            root, W = paper_map("TrMap", TR, 0.33, TR_SEAS, TR_ROADS, TR_LABELS, ctr=(0, 0.05, 0.761), rz=math.radians(3))
            c["W"] = W
            ink_r = pbr("RouteInk", RED, 0.55)
            ank = W(*T_ANK, 0.0008)
            ring = bpy.ops.mesh.primitive_torus_add(major_radius=0.022, minor_radius=0.0012, location=ank)
            c["ank_ring"] = bpy.context.active_object; c["ank_ring"].data.materials.append(ink_r); c["ank_ring"].scale = (1, 0.85, 0.3)
            # the export permit, a rubber stamp and its red imprint
            perm = box("Permit", (0, 0, 0), (0.21, 0.297, 0.0008), mat_paper("PermitPaper", (0.9, 0.88, 0.82)))
            perm.location = (0.12, -0.18, 0.7625); perm.rotation_euler = (0, 0, math.radians(-11)); c["permit"] = perm
            pm = ink("PermitInk")
            flat_text("PermitHead", "EXPORT PERMIT", (0, 0.115, 0.0006), 0.016, pm).parent = perm
            flat_text("PermitYear", "1994", (0.06, 0.088, 0.0006), 0.012, pm).parent = perm
            grey = pbr("PermitLines", (0.35, 0.34, 0.33), 0.7)
            for k in range(11):
                box("PermLine", (-0.005 + (0.01 if k % 3 == 2 else 0), 0.06 - k * 0.014, 0.0005), (0.16 - (0.05 if k % 3 == 2 else 0), 0.0025, 0.0002), grey).parent = perm
            imp_m = pbr("StampInk", (0.6, 0.05, 0.06), 0.7)
            imp = join([box("ImpTop", (0, 0.022, 0), (0.12, 0.003, 0.0002), imp_m), box("ImpBot", (0, -0.022, 0), (0.12, 0.003, 0.0002), imp_m),
                        box("ImpL", (-0.0585, 0, 0), (0.003, 0.047, 0.0002), imp_m), box("ImpR", (0.0585, 0, 0), (0.003, 0.047, 0.0002), imp_m)], "Imprint")
            t1 = flat_text("ImpText", "APPROVED  1994", (0, 0, 0.0001), 0.011, imp_m); t1.parent = imp
            imp.parent = perm; imp.location = (0.0, -0.075, 0.0006); imp.rotation_euler = (0, 0, math.radians(4)); c["imprint"] = imp
            stamp = join([box("StampPad", (0, 0, 0.006), (0.125, 0.05, 0.012), pbr("Rubber", (0.12, 0.08, 0.07), 0.8)),
                          box("StampBlock", (0, 0, 0.025), (0.13, 0.055, 0.026), wood("StampWood")),
                          cyl("StampHandle", (0, 0, 0.07), 0.016, 0.07, wood("StampWood2"), verts=20)], "Stamp")
            c["stamp"] = stamp
            # retrace pins (ch4_5a) and the ~90 km measuring line
            for nm, p in (("PinIst", T_IST), ("PinSmelt", T_SMELT)):
                c[nm] = pin(nm, W(*p)); c[nm + "_z"] = c[nm].location.z
            a, b = W(*T_IST, 0.001), W(*T_SMELT, 0.001)
            c["measure"] = poly_curve("Measure", [a, b], 0.0009, pbr("MeasureInk", INK, 0.6), reveal=(1, 2))
            mid = (a + b) / 2 + Vector((0, 0.018, 0))
            c["km"] = flat_text("Km", "~ 90 km", mid, 0.013, ink("KmInk"), rz=math.atan2((b - a).y, (b - a).x))
            for nm, p in (("TagIst", T_IST), ("TagSmelt", T_SMELT)):
                tg = box(nm, W(p[0], p[1] - 0.12, 0.002), (0.07, 0.022, 0.0006), mat_paper(nm + "P", (0.95, 0.93, 0.86)))
                flat_text(nm + "T", "BACKGROUND", (0, 0, 0.0005), 0.0075, ink(nm + "I")).parent = tg
                c[nm] = tg
            c["photo1"] = photo_print("Photo1", os.path.join(STILLS, "therapy_ch2_9a", "plate.png"), (-0.62, -0.3, 0.7625), 0.22, math.radians(12))
        c["pen"] = felt_pen()
        c["pen"].location = (0.6, -0.35, 0.77); c["pen"].rotation_euler = (math.radians(80), 0, math.radians(30))
        lamp_key((-0.55, 0.45, 1.45), (0.0, 0.0, 0.76), energy=95)
        area((0.9, -0.9, 1.6), (0, 0, 0.76), 18, 1.4, (0.75, 0.82, 1.0), "WindowFill")
        box("LampShade", (-0.55, 0.45, 1.5), (0.2, 0.2, 0.14), pbr("ShadeM", (0.1, 0.12, 0.1), 0.4, 0.6))
    elif v == "void":
        dark_world(0.0)
        fl = box("VoidFloor", (0, 0, -0.01), (30, 30, 0.02), pbr("VoidFloorM", (0.012, 0.012, 0.013), 0.32))
        key = area((0.3, -0.4, 3.2), (0, 0, 0.5), 230, 1.6, (1.0, 0.97, 0.92), "TopKey")
        area((6.4, -0.6, 3.0), (6.4, 0, 0.3), 260, 1.4, (1.0, 0.97, 0.92), "TopKey2")
        area((7.6, -1.6, 1.2), (7.05, -0.25, 0.4), 40, 0.6, (1.0, 0.95, 0.88), "MeterLight")
        area((-2.5, 2.0, 1.6), (0, 0, 0.6), 120, 1.0, (0.85, 0.9, 1.0), "Rim")
        # (1) the container, cut open: steel shell, lead lining, the source well with the capsule
        steel = painted_steel("CutSteel", (0.34, 0.35, 0.35), 0.5, 0.35); lead = pbr("CutLead", (0.27, 0.28, 0.3), 0.55, 0.2)
        cutm = pbr("CutFace", (0.5, 0.5, 0.52), 0.35, 0.6)
        shell = cyl("Shell", (0, 0, 0.55), 0.38, 0.82, steel, verts=64)
        core = cyl("Lead", (0, 0, 0.55), 0.355, 0.78, lead, verts=64)
        well = cyl("Well", (0, 0, 0.6), 0.035, 0.5, pbr("WellM", (0.03, 0.03, 0.03), 0.6), verts=24)
        for o_ in (shell, core):
            bo = o_.modifiers.new("Cut", 'BOOLEAN'); cutter = box(o_.name + "Cutter", (0.3, -0.3, 0.6), (0.6, 0.6, 1.2)); cutter.hide_render = True
            cutter.hide_viewport = True; bo.object = cutter; bo.operation = 'DIFFERENCE'
        bh = shell.modifiers.new("Hollow", 'BOOLEAN'); hc = cyl("ShellHollow", (0, 0, 0.55), 0.358, 0.79, None, verts=64)
        hc.hide_render = True; hc.hide_viewport = True; bh.object = hc; bh.operation = 'DIFFERENCE'
        bw = core.modifiers.new("WellBore", 'BOOLEAN'); wc = cyl("WellBore", (0, 0, 0.62), 0.036, 0.52, None, verts=24)
        wc.hide_render = True; wc.hide_viewport = True; bw.object = wc; bw.operation = 'DIFFERENCE'
        cap = cyl("Capsule", (0, 0, 0.6), 0.012, 0.05, pbr("CapsuleM", (0.72, 0.72, 0.74), 0.22, 1.0), verts=24)
        grp = bpy.data.objects.new("Cutaway", None); bpy.context.collection.objects.link(grp)
        for o_ in (shell, core, well, cap):
            o_.parent = grp
        well.hide_render = True
        lab = pbr("LabelInk", (0.85, 0.84, 0.8), 0.6)
        c["lab_lead"] = wall_text("LabLead", "LEAD", (0.62, -0.38, 0.74), 0.06, lab, align='LEFT')
        c["lab_src"] = wall_text("LabSrc", "SOURCE", (0.62, -0.38, 0.6), 0.04, lab, align='LEFT')
        c["lead_line"] = poly_curve("LeadLine", [(0.6, -0.36, 0.76), (0.25, -0.12, 0.76)], 0.0025, lab, reveal=(1, 2))
        c["src_line"] = poly_curve("SrcLine", [(0.6, -0.36, 0.615), (0.02, -0.02, 0.6)], 0.0018, lab, reveal=(1, 2))
        c["cut"] = grp
        # (2) the pile as plates over the capsule, with a meter (placed 6 m to the side)
        P = Vector((6.0, 0, 0)); c["P"] = P
        cap2 = cyl("Capsule2", P + Vector((0, 0, 0.03)), 0.012, 0.05, pbr("CapsuleM2", (0.72, 0.72, 0.74), 0.22, 1.0), verts=24)
        cap2.rotation_euler = (math.radians(90), 0, math.radians(30))
        rust = rust_mat("PlateRust")
        c["plates"] = []
        for k in range(6):
            pl = box(f"Plate{k}", P + Vector((0.02 * math.sin(k * 2.1), 0.03 * math.cos(k * 1.3), 0.09 + k * 0.075)), (0.9 - k * 0.04, 0.7 - k * 0.03, 0.05), rust, bevel=0.006)
            pl.rotation_euler = (math.radians(1.5 * math.sin(k)), math.radians(1.2 * math.cos(k * 1.7)), math.radians(9 * math.sin(k * 3.1)))
            c["plates"].append((pl, pl.location.copy(), pl.rotation_euler.copy()))
        # survey meter: a dark housing with a cream dial facing the camera, red needle on a pivot
        M = P + Vector((0.95, -0.35, 0.0)); yaw = math.radians(-18)
        hous = box("MeterHousing", (0, 0, 0.17), (0.34, 0.16, 0.3), pbr("MeterHousingM", (0.09, 0.09, 0.1), 0.45, 0.2), bevel=0.02)
        dial = box("MeterDial", (0, -0.081, 0.2), (0.26, 0.002, 0.16), pbr("MeterDialM", (0.86, 0.84, 0.76), 0.5))
        grp_m = bpy.data.objects.new("Meter", None); bpy.context.collection.objects.link(grp_m)
        hous.parent = grp_m; dial.parent = grp_m
        for k in range(7):
            a = math.radians(-50 + k * 100 / 6)
            box("Tick", (0.1 * math.sin(a), -0.083, 0.15 + 0.1 * math.cos(a)), (0.003, 0.001, 0.018), pbr("TickM", INK, 0.6), rot=(0, a, 0)).parent = grp_m
        piv = bpy.data.objects.new("NeedlePivot", None); bpy.context.collection.objects.link(piv); piv.parent = grp_m; piv.location = (0, -0.085, 0.14)
        needle = box("Needle", (0, 0, 0.05), (0.004, 0.002, 0.1), pbr("NeedleM", RED, 0.4)); needle.parent = piv; c["needle"] = piv
        grp_m.location = M; grp_m.rotation_euler = (0, 0, yaw)
    elif v == "model":
        dark_world(0.03)
        tbl = box("ModelTable", (0, 0, 0.36), (2.6, 1.8, 0.04), pbr("TableBoard", (0.18, 0.17, 0.16), 0.7))
        box("Floor", (0, 0, -0.01), (20, 20, 0.02), pbr("FloorDark", (0.03, 0.028, 0.026), 0.6))
        card = pbr("Card", (0.86, 0.85, 0.82), 0.75); grey = pbr("CardGrey", (0.55, 0.55, 0.55), 0.8)
        z0 = 0.38
        box("Base", (0, 0, z0 + 0.005), (2.2, 1.4, 0.01), pbr("BaseCard", (0.7, 0.69, 0.66), 0.85))
        box("Street", (0, -0.42, z0 + 0.011), (2.2, 0.22, 0.002), pbr("StreetCard", (0.4, 0.39, 0.38), 0.85))
        yard = [(-0.25, -0.3), (0.25, -0.3), (0.25, 0.15), (-0.25, 0.15)]
        poly_curve("YardLine", [(x, y, z0 + 0.012) for x, y in yard], 0.0015, pbr("YardInk", INK, 0.6), closed=True)
        houses = [(-0.55, -0.05, 0.36, 0.42, 0.14), (0.55, -0.05, 0.36, 0.42, 0.14), (0.0, 0.42, 0.5, 0.3, 0.16),
                  (-0.95, 0.05, 0.3, 0.45, 0.12), (0.95, 0.0, 0.32, 0.4, 0.2), (-0.5, -0.75, 0.42, 0.3, 0.14), (0.45, -0.75, 0.38, 0.3, 0.18),
                  (-0.6, 0.45, 0.32, 0.3, 0.13), (0.62, 0.45, 0.32, 0.3, 0.13)]
        for i, (x, y, w, d, h) in enumerate(houses):
            box(f"House{i}", (x, y, z0 + 0.01 + h / 2), (w, d, h), card, bevel=0.002)
            for wx in (-0.25, 0.25):          # punched windows: dark card rectangles on the street-facing side
                box(f"Win{i}", (x + wx * w, y - d / 2 - 0.0008, z0 + 0.01 + h * 0.55), (w * 0.16, 0.002, h * 0.28), pbr("WinCard", (0.12, 0.12, 0.13), 0.8))
        for k, x in enumerate((-0.08, 0.08)):
            box(f"Pkg{k}", (x, -0.08, z0 + 0.025), (0.06, 0.06, 0.03), grey)
        # spreading rings from the containers (scaled per frame in the shot)
        rm = pbr("RingInk", RED, 0.45)
        c["rings"] = []
        for k in range(4):
            bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.004, location=(0, -0.08, z0 + 0.013))
            r = bpy.context.active_object; r.data.materials.append(rm); r.scale = (0.01, 0.01, 1); c["rings"].append(r)
        lamp_key((-1.2, -1.0, 2.0), (0, 0, 0.4), energy=260, col=(1.0, 0.86, 0.68), size=0.6, name="ModelKey")
        area((1.5, 1.2, 1.6), (0, 0, 0.4), 40, 1.5, (0.8, 0.86, 1.0), "ModelFill")
    elif v == "calendar":
        dark_world(0.02)
        wallm = pbr("KitchenWall", (0.52, 0.48, 0.4), 0.85)
        box("KWall", (0, 0.05, 1.5), (4, 0.1, 3), wallm)
        box("KTile", (0, 0.0, 0.5), (4, 0.02, 1.0), pbr("KTileM", (0.55, 0.57, 0.55), 0.35))
        cal = box("Calendar", (0, -0.002, 1.55), (0.42, 0.004, 0.56), mat_paper("CalPaper", (0.9, 0.88, 0.83)))
        pm = ink("CalInk"); red = pbr("CalRed", RED, 0.55)
        box("CalPhoto", (0, -0.005, 1.7), (0.38, 0.002, 0.2), pbr("CalPhotoM", (0.38, 0.42, 0.36), 0.6))
        wall_text("CalMonth", "ARALIK 1998", (0, -0.006, 1.565), 0.03, pm)
        days = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        X0, DX, Y0, DY = -0.165, 0.055, 1.52, 0.048
        for i, dname in enumerate(days):
            wall_text("CalDay", dname, (X0 + i * DX, -0.006, Y0), 0.012, red if i == 6 else pm)
        c["cells"] = {}
        for d in range(1, 32):
            idx = d + 0                                 # 1 December 1998 was a Tuesday (column 1)
            col = idx % 7; row = idx // 7
            p = Vector((X0 + col * DX, -0.006, Y0 - (row + 1) * DY))
            wall_text("CalNum", str(d), p, 0.02, red if col == 6 else pm); c["cells"][d] = p
        c["circles"] = []
        for d in (10, 13):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.019, minor_radius=0.0013, location=c["cells"][d] + Vector((0, -0.002, 0.007)),
                                             rotation=(math.radians(90), 0, 0))
            r = bpy.context.active_object; r.data.materials.append(red); r.scale = (1.15, 1.0, 1.0); c["circles"].append(r)
        nail = cyl("Nail", (0, -0.01, 1.85), 0.003, 0.02, pbr("NailM", (0.4, 0.4, 0.4), 0.3, 1), rot=(math.radians(90), 0, 0))
        pen = felt_pen("CalPen"); piv = bpy.data.objects.new("PenString", None); bpy.context.collection.objects.link(piv)
        piv.location = (0.25, -0.03, 1.8); pen.parent = piv; pen.location = (0, 0, -0.32); pen.rotation_euler = (0, 0, 0)
        poly_curve("String", [(0.25, -0.03, 1.8), (0.25, -0.03, 1.66)], 0.0008, pbr("StringM", (0.75, 0.72, 0.66), 0.8)).parent = piv
        c["penpiv"] = piv
        bulb = bpy.data.lights.new("Bulb", 'POINT'); bulb.energy = 260; bulb.color = (1.0, 0.75, 0.45); bulb.shadow_soft_size = 0.02
        bo = bpy.data.objects.new("Bulb", bulb); bpy.context.collection.objects.link(bo)
        bpiv = bpy.data.objects.new("BulbCord", None); bpy.context.collection.objects.link(bpiv); bpiv.location = (-0.35, -0.9, 2.9)
        bo.parent = bpiv; bo.location = (0, 0, -0.75); c["bulb"] = bpiv
        glob = cyl("BulbGlass", (0, 0, -0.75), 0.03, 0.08, emissive("BulbGlow", (1.0, 0.75, 0.45), 6.0), verts=16); glob.parent = bpiv
        bo.visible_camera = False
        area((1.2, -1.4, 1.4), (0, 0, 1.5), 25, 1.2, (0.7, 0.78, 0.95), "NightWindow")
    elif v == "tally":
        dark_world(0.05, (0.35, 0.38, 0.42))
        blk = ph_mat("concrete_wall_008", 0.5, (0.5, 0.5, 0.48), name="BlockWall")
        for r_ in range(6):
            for k in range(7):
                off = 0.2 if r_ % 2 else 0.0
                box(f"Blk{r_}_{k}", (-1.2 + k * 0.4 + off, 0.1, 0.1 + r_ * 0.2), (0.39, 0.2, 0.19), blk, bevel=0.004)
        chalk = noisy("Chalk", (0.74, 0.73, 0.7), 1.0, dirt=0.8, scale=60, dark=0.45)
        c["strokes"] = []
        for k in range(10):
            g, j = divmod(k, 5)
            if j < 4:
                x = -0.42 + g * 0.42 + j * 0.06; a, b = Vector((x, -0.002, 0.82)), Vector((x + 0.008, -0.002, 1.04))
            else:
                x = -0.42 + g * 0.42; a, b = Vector((x - 0.03, -0.002, 0.86)), Vector((x + 0.215, -0.002, 1.0))
            d = b - a
            st = box(f"Stroke{k}", (0, 0, 0.5), (0.0042 + 0.001 * math.sin(k * 2.3), 0.0008, 1.0), chalk)
            b = b + Vector((0.006 * math.sin(k * 1.7), 0, 0.02 * math.cos(k * 2.9))); d = b - a
            piv = bpy.data.objects.new(f"StrokePiv{k}", None); bpy.context.collection.objects.link(piv); piv.location = a
            st.parent = piv; piv.rotation_euler = (0, math.atan2(d.x, d.z), 0); piv.scale = (1, 1, d.length)
            c["strokes"].append(piv)
        c["chalk"] = cyl("ChalkStick", (0, 0, 0), 0.006, 0.06, chalk, verts=12)
        sun = bpy.data.lights.new("Overcast", 'AREA'); sun.energy = 900; sun.size = 4.0; sun.color = (0.95, 0.96, 1.0)
        so = bpy.data.objects.new("Overcast", sun); bpy.context.collection.objects.link(so); so.location = (-2.5, -2.5, 2.4)
        so.rotation_euler = (Vector(so.location) - Vector((0, 0, 0.8))).to_track_quat('Z', 'Y').to_euler()
        box("Ground", (0, -1, -0.01), (10, 6, 0.02), ph_mat("brown_mud_02", 0.6, (0.3, 0.24, 0.18), name="TallyMud"))
        gl = box("Gloves", (0.6, 0.07, 1.21), (0.16, 0.1, 0.03), pbr("GloveM", (0.2, 0.15, 0.1), 0.85))
    elif v == "board":
        dark_world(0.03)
        box("WardWall", (0, 0.06, 1.5), (4, 0.1, 3), pbr("WardWallM", (0.5, 0.56, 0.52), 0.8))
        board = box("BedBoard", (0, 0.0, 1.45), (1.3, 0.02, 0.8), pbr("Whiteboard", (0.85, 0.86, 0.85), 0.25), bevel=0.004)
        box("BoardFrame", (0, 0.004, 1.45), (1.34, 0.016, 0.84), pbr("BoardAlu", (0.6, 0.6, 0.62), 0.3, 0.9))
        pm = ink("BoardInk")
        wall_text("BoardHead", "SERVİS  -  YATAK", (0, -0.012, 1.79), 0.034, pm)
        c["magnets"] = []
        cardm = pbr("BedCard", (0.93, 0.92, 0.88), 0.6); mag = pbr("Magnet", (0.7, 0.05, 0.04), 0.35)
        ill = [1, 2, 4, 5, 7, 9, 11, 12, 14, 17]
        for i in range(18):
            r_, k = divmod(i, 6)
            p = Vector((-0.52 + k * 0.208, -0.012, 1.62 - r_ * 0.24))
            box(f"Card{i}", p, (0.17, 0.003, 0.17), cardm)
            wall_text(f"Bed{i}", str(i + 1), p + Vector((0, -0.003, 0.02)), 0.05, pm)
            for ln in range(2):
                box("CardLine", p + Vector((0, -0.003, -0.035 - ln * 0.022)), (0.12, 0.001, 0.004), pbr("CardLineM", (0.4, 0.4, 0.42), 0.7))
            if (i + 1) in ill:
                m_ = cyl(f"Mag{i}", p + Vector((0.058, -0.012, 0.058)), 0.018, 0.014, mag, verts=24, rot=(math.radians(90), 0, 0))
                c["magnets"].append(m_)
        c["nurse"] = person("BoardNurse", 0.0, 34, "nurse", "ponytail01", hv=0.1, hat="nurse", hat_col=(0.92, 0.92, 0.9))
        tube_light((0, -0.6, 2.9), 1.2, 45)
        area((-1.5, -1.6, 2.2), (0, 0, 1.45), 60, 1.5, (1.0, 0.95, 0.88), "WardWindow")
        box("Floor", (0, -1, -0.01), (10, 6, 0.02), pbr("WardFloor", (0.35, 0.36, 0.34), 0.5))
    elif v == "cork":
        dark_world(0.02)
        box("OfficeWall", (0, 0.06, 1.5), (4, 0.1, 3), pbr("OfficeWallM", (0.45, 0.48, 0.5), 0.8))
        cork = pbr("Cork", (0.48, 0.33, 0.2), 0.95)
        box("CorkBoard", (0, 0.0, 1.5), (1.4, 0.02, 0.9), cork, bevel=0.003)
        box("CorkFrame", (0, 0.004, 1.5), (1.44, 0.016, 0.94), wood("CorkFrameW"))
        pm = ink("ListInk"); rows = 8
        c["rowsL"], c["rowsR"] = [], []
        for side, (x, head) in enumerate(((-0.36, "COMPANY RECORDS"), (0.36, "SUPPLIER RECORDS"))):
            sh = box(f"List{side}", (x, -0.012, 1.48), (0.42, 0.002, 0.6), mat_paper(f"ListP{side}", (0.92, 0.91, 0.87)))
            wall_text(f"Head{side}", head, (x, -0.014, 1.73), 0.022, pm)
            for r_ in range(rows):
                y = 1.66 - r_ * 0.06
                wall_text("Row", f"SOURCE {r_ + 1:02d}", (x - 0.06, -0.014, y), 0.017, pm)
                stat = ["RETURNED", "IN TURKEY"][(r_ + side + (1 if r_ in (2, 5) else 0)) % 2]
                wall_text("Stat", stat, (x + 0.11, -0.014, y), 0.014, pm)
                (c["rowsL"] if side == 0 else c["rowsR"]).append(Vector((x + (0.2 if side == 0 else -0.2), -0.02, y + 0.006)))
            pin(f"ListPin{side}", (x, -0.02, 1.77)).rotation_euler = (math.radians(90), 0, 0)
        strm = pbr("RedString", RED, 0.7)
        c["strings"] = []
        for r_ in (2, 5):                                # the two rows whose status disagrees
            a, b = c["rowsL"][r_], c["rowsR"][r_]
            mid = (a + b) / 2 + Vector((0, -0.01, -0.03))
            c["strings"].append(poly_curve(f"String{r_}", [a, mid, b], 0.0012, strm, reveal=(1, 2)))
            for p in (a, b):
                pin(f"SPin{r_}", p).rotation_euler = (math.radians(90), 0, 0)
        q = box("QCard", (0.0, -0.014, 1.12), (0.12, 0.002, 0.08), mat_paper("QCardP", (0.95, 0.93, 0.8)))
        wall_text("Q", "?", (0.0, -0.016, 1.1), 0.06, pbr("QInk", RED, 0.5))
        c["qcard"] = q
        lamp_key((0.9, -1.4, 2.4), (0, 0, 1.45), energy=180, col=(1.0, 0.86, 0.66), size=0.4, name="OfficeLamp")
        area((-1.8, -1.2, 1.8), (0, 0, 1.4), 50, 1.4, (0.8, 0.87, 1.0), "OfficeWindow")
        box("Floor", (0, -1, -0.01), (10, 6, 0.02), pbr("OfficeFloor", (0.2, 0.13, 0.08), 0.6))
    elif v == "binders":
        dark_world(0.03)
        box("ArchWall", (0, 0.45, 1.5), (14, 0.1, 3), pbr("ArchWallM", (0.5, 0.52, 0.5), 0.85))
        steel = pbr("ShelfSteel", (0.42, 0.44, 0.43), 0.45, 0.6)
        for z in (0.95, 1.4):
            box("Shelf", (0, 0.2, z), (9.6, 0.4, 0.02), steel)
        for x in (-4.8, -2.4, 0, 2.4, 4.8):
            box("Upright", (x, 0.2, 1.0), (0.03, 0.42, 2.0), steel)
        cols = [(0.05, 0.07, 0.13), (0.15, 0.04, 0.035), (0.04, 0.09, 0.05), (0.07, 0.07, 0.07), (0.12, 0.1, 0.05)]
        c["ticks"] = []
        labm = mat_paper("SpineLabel", (0.9, 0.88, 0.82)); pm = ink("SpineInk"); tick = pbr("TickGreen", (0.1, 0.42, 0.14), 0.5)
        for i in range(46):
            row, k = divmod(i, 23)
            x = -4.5 + k * 0.4 + (0.2 if row else 0); z = 0.96 + row * 0.45
            box(f"Binder{i}", (x, 0.17, z + 0.16), (0.075, 0.28, 0.32), pbr(f"BinderM{i % 5}", cols[i % 5], 0.55), bevel=0.004)
            box(f"Label{i}", (x, 0.028, z + 0.2), (0.055, 0.002, 0.09), labm)
            text_obj(f"No{i}", f"{i + 1}", (x, 0.026, z + 0.19), 0.03, pm, rot=(math.radians(90), 0, 0), extrude=0.0)
            tk = join([box("TickA", (-0.007, 0, -0.004), (0.004, 0.0015, 0.014), tick, rot=(0, math.radians(40), 0)),
                       box("TickB", (0.006, 0, 0.002), (0.004, 0.0015, 0.028), tick, rot=(0, math.radians(-30), 0))], f"Tick{i}")
            tk.location = (x, 0.026, z + 0.085); tk.scale = (0.001, 0.001, 0.001); c["ticks"].append(tk)      # a green check mark
        for k in range(4):
            tube_light((-3.6 + k * 2.4, -0.6, 2.9), 1.2, 40)
        box("Floor", (0, -1, -0.01), (14, 6, 0.02), pbr("ArchFloor", (0.3, 0.3, 0.29), 0.5))
    import rs_env as _rs_env
    _rs_env.cinematic(c, __name__)
    return c


# ------------------------------------------------------------------------------------------------ shots
def S(shot, t):
    sec = t * dur(shot); bpy.context.scene.frame_current = 1 + int(round(sec * 24))
    return sec


def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def C(p0, p1, tgt, lens, tgt1=None):
    def f(c, t):
        e = ease(t); tg = Vector(tgt) if tgt1 is None else Vector(tgt).lerp(Vector(tgt1), e)
        return (Vector(p0).lerp(Vector(p1), e), tg, lens)
    return f


def pen_on(c, pts, k, lift=0.0):
    p = along(pts, k); pen = c["pen"]
    pen.location = p + Vector((0, 0, 0.002 + lift)); pen.rotation_euler = (math.radians(18), math.radians(-10), math.radians(30))


def drop_pin(c, nm, sec, t0):
    k = ease((sec - t0) / 0.4); c[nm].location.z = c[nm + "_z"] + 0.06 * (1 - k)
    c[nm].hide_render = sec < t0 - 0.05


def s_ch1_3b(c, t):         # the red pen draws the route from the building to İkitelli across the street map
    sec = S("ch1_3b", t); n = dur("ch1_3b") * 24
    set_reveal(c["route1"], 8, n * 0.85); c["route2"].hide_render = True
    k = ease(max(0.0, (sec * 24 - 8) / (n * 0.85 - 8)))
    pen_on(c, c["r1"], k)
    drop_pin(c, "PinBuilding", sec, 0.0); drop_pin(c, "PinYard", sec, dur("ch1_3b") * 0.85); c["PinScrap"].hide_render = True
    c["focus"] = c["pen"].location


def s_ch1_13b(c, t):        # the line goes on from the yard to the second scrapyard
    sec = S("ch1_13b", t); n = dur("ch1_13b") * 24
    set_reveal(c["route1"], -2, -1); set_reveal(c["route2"], 6, n * 0.8)
    k = ease(max(0.0, (sec * 24 - 6) / (n * 0.8 - 6)))
    pen_on(c, c["r2"], k)
    drop_pin(c, "PinBuilding", 9, 0); drop_pin(c, "PinYard", 9, 0); drop_pin(c, "PinScrap", sec, dur("ch1_13b") * 0.8)
    c["focus"] = c["pen"].location


def s_ch2_12a(c, t):        # the export permit, stamped "1994", lying over the map with Ankara ringed in red
    sec = S("ch2_12a", t); D = dur("ch2_12a")
    st = c["stamp"]; pm = c["permit"]; bpy.context.view_layer.update()
    hit = pm.matrix_world @ Vector((0.0, -0.075, 0.0012))
    tdown = D * 0.35
    if sec < tdown:
        z = 0.12 * (1 - ease(sec / tdown))
    else:
        z = 0.1 * ease((sec - tdown - 0.25) / 0.6) if sec > tdown + 0.25 else 0.0
    st.location = hit + Vector((0, 0, z)); st.rotation_euler = (0, 0, pm.rotation_euler.z + math.radians(4))
    c["imprint"].hide_render = sec < tdown
    for nm in ("PinIst", "PinSmelt", "TagIst", "TagSmelt", "km", "measure"):
        c[nm].hide_render = True
    c["pen"].hide_render = True
    c["focus"] = hit


def s_ch4_5a(c, t):         # the route retraced: pins drop at Istanbul and the smelting works, "~90 km", BACKGROUND tags
    sec = S("ch4_5a", t); D = dur("ch4_5a"); n = D * 24
    for nm in ("permit", "imprint", "stamp"):
        c[nm].hide_render = True
    drop_pin(c, "PinIst", sec, 0.3); drop_pin(c, "PinSmelt", sec, D * 0.45)
    set_reveal(c["measure"], 12, n * 0.45)
    c["km"].hide_render = sec < D * 0.45
    c["TagIst"].hide_render = sec < D * 0.55; c["TagSmelt"].hide_render = sec < D * 0.7
    c["pen"].hide_render = True
    c["focus"] = (c["W"](*T_IST) + c["W"](*T_SMELT)) / 2


def s_ch2_4a(c, t):         # the container cut open on black; the camera pushes in and focus pulls from the steel to the well
    sec = S("ch2_4a", t); D = dur("ch2_4a")
    c["cut"].rotation_euler = (0, 0, math.radians(-18))
    for nm in ("lab_lead", "lab_src", "lead_line", "src_line"):
        c[nm].hide_render = True
    c["focus"] = Vector((0.3, -0.25, 0.75)).lerp(Vector((0.0, 0.0, 0.6)), ease((sec - 0.6) / (D * 0.6)))


def s_ch3_8a(c, t):         # the pile as plates over the capsule: each plate lifted away, the meter needle climbs
    sec = S("ch3_8a", t); D = dur("ch3_8a"); P = c["P"]
    gone = 0
    for k, (pl, loc0, rot0) in enumerate(reversed(c["plates"])):
        t0 = 0.4 + k * (D - 1.0) / 6
        e = ease((sec - t0) / 0.7)
        dest = P + Vector((-1.15, 0.35, 0.03 + k * 0.055))           # lifted plates pile up beside the capsule
        arc = Vector((0, 0, 0.6 * math.sin(math.pi * e)))
        pl.location = loc0.lerp(dest, e) + arc; pl.rotation_euler = (rot0.x, rot0.y, rot0.z + 0.5 * e)
        gone += e
    c["needle"].rotation_euler = (0, math.radians(-50 + 100 * (gone / 6) ** 1.6 + 1.5 * math.sin(sec * 11)), 0)
    c["focus"] = P + Vector((0, 0, 0.2))


def s_ch1_7a(c, t):         # card model of the yard and the houses; red rings spread from the containers over the roofs
    sec = S("ch1_7a", t); D = dur("ch1_7a")
    for k, r in enumerate(c["rings"]):
        ph = ((sec / D) * 1.6 + k * 0.25) % 1.0
        s = 0.05 + 1.15 * ph; r.scale = (s, s, 1)
    c["focus"] = Vector((0, -0.08, 0.4))


def s_ch1_12a(c, t):        # December 1998 on the kitchen wall: the 10th and 13th ringed; the bulb sways
    sec = S("ch1_12a", t)
    c["bulb"].rotation_euler = (math.radians(4 * math.sin(sec * 1.3)), math.radians(3 * math.sin(sec * 0.9 + 1)), 0)
    c["penpiv"].rotation_euler = (0, math.radians(5 * math.sin(sec * 1.7)), 0)
    c["focus"] = c["cells"][13]


def s_ch3_14a(c, t):        # chalk tally on the shield wall: nine strokes there, the tenth drawn as we watch
    sec = S("ch3_14a", t); D = dur("ch3_14a")
    for k, piv in enumerate(c["strokes"]):
        if k < 9:
            continue
        e = ease((sec - D * 0.25) / (D * 0.35))
        st = piv.children[0]; st.scale = (1, 1, max(1e-3, e))
        bpy.context.view_layer.update()
        tip = piv.matrix_world @ Vector((0, 0, e))
        c["chalk"].location = tip + Vector((0, -0.03, 0)); c["chalk"].rotation_euler = (math.radians(70), 0, math.radians(20))
        c["chalk"].hide_render = e >= 0.999 and sec > D * 0.75
    c["focus"] = Vector((0, 0, 0.93))


def s_ch4_1b(c, t):         # nine red magnets on the bed board; a nurse puts up the tenth, then steps back
    sec = S("ch4_1b", t); D = dur("ch4_1b")
    from human import reset_pose
    h = c["nurse"]; mags = c["magnets"]; last = mags[-1]
    if "mag_home" not in c:
        c["mag_home"] = last.location.copy()
    home = c["mag_home"]
    stand = Vector((home.x + 0.42, -0.62, 0)); reset_pose(h); stand_pose(h)
    place(h, stand, face_angle(stand, Vector((home.x + 0.1, 0.0, 0))))
    fw = forward(h); sd = fw.cross(Vector((0, 0, 1))).normalized()
    k = ease(min(1.0, max(0.0, (sec - 0.4) / (D * 0.4))))             # hand travels from her side to the card
    back = ease(min(1.0, max(0.0, (sec - D * 0.62) / (D * 0.3))))      # then drops back down
    side_pt = h.bone_head("upperarm01.R") + fw * 0.2 + Vector((0, 0, -0.45))
    at_card = home + Vector((0.0, -0.035, -0.01))
    tgt = side_pt.lerp(at_card, k).lerp(side_pt, back)
    reach(h, "R", tgt, Vector((sd.x, sd.y, -1.0)), Vector((0, 0.9, 0.35)))
    fingers_curl(h, 60, side=("R",), thumb=45)
    bpy.context.view_layer.update()
    if back <= 0.0 and k < 0.999:                                     # carried between finger and thumb
        last.location = tgt + Vector((0, 0.03, 0.01))
    else:
        last.location = home
    h.rot("head", sd, -4)
    c["focus"] = home


def s_ch4_8b(c, t):         # cork board: red string between the rows the two records disagree on, then the "?" card
    sec = S("ch4_8b", t); D = dur("ch4_8b"); n = D * 24
    for k, s_ in enumerate(c["strings"]):
        set_reveal(s_, n * (0.1 + 0.3 * k), n * (0.35 + 0.3 * k))
    c["focus"] = Vector((0, 0, 1.4))


def s_ch4_10a(c, t):        # forty-six binders, one per centre; a green tick goes on each as the camera tracks
    sec = S("ch4_10a", t); D = dur("ch4_10a")
    for i, tk in enumerate(c["ticks"]):
        e = ease((sec - 0.2 - i * (D - 0.8) / 46) / 0.2); tk.scale = (max(1e-3, e),) * 3
    c["focus"] = Vector((0, 0.03, 1.2))


SHOTS = {
    "ch2_4a": ("void", s_ch2_4a, C((1.9, -2.3, 1.45), (1.55, -1.9, 1.25), (0.1, -0.05, 0.62), 40), 5.6),
    "ch4_1b": ("board", s_ch4_1b, C((-0.55, -2.1, 1.55), (-0.35, -1.85, 1.52), (0.4, -0.2, 1.3), 34), 5.6),
}
VARIANT_FOR = {k: v[0] for k, v in SHOTS.items()}
DUR = {k: dur(k) for k in SHOTS}


def _focus(c, t):
    return c.get("focus", Vector((0, 0, 0.8)))


MOVES = {k: dict(kind="anim", far=60.0, anim=v[1], cam=v[2], dof=v[3], focus=_focus) for k, v in SHOTS.items()}
