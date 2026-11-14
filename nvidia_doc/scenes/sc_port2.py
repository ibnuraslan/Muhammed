"""CH5 redo port shots (built on the sc_port yard at dusk).
  stacks  CH5 6A (197 f) low in an aisle between container stacks at dusk: tall light masts throw sodium pools on the
          yard, an RTG gantry crane with its work lights rolls slowly along the row ahead; slow push down the aisle
  xray    CH5 9A (227 f) a realistic container X-ray portal at the port gate: a massive clad steel portal (source
          housing on top, detector columns), radiation-warning signs (generic trefoil), a lit control booth, traffic
          lights, kerbs and lane markings; a tractor unit pulls a 40 ft container slowly through the portal
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from PIL import Image, ImageDraw
from kit import *
from common import area_light
import sc_port
from sc_port import L20, W8, H8

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "assets", "generated")
EXPOSURE = 0.0
VARIANT_FOR = {"stacks": "stacks", "xray": "xray"}
FRAMES = {"stacks": 197, "xray": 227}


def trefoil_sign(path, W=512):
    """Generic radiation-warning sign: black trefoil on yellow, black border; one line of grey bars below."""
    im = Image.new("RGB", (W, int(W * 1.3)), (235, 190, 20)); d = ImageDraw.Draw(im)
    d.rectangle([8, 8, W - 9, int(W * 1.3) - 9], outline=(15, 15, 15), width=14)
    cx, cy, R, r = W // 2, int(W * 0.48), int(W * 0.36), int(W * 0.07)
    for k in range(3):
        a0 = -90 + k * 120 - 30
        d.pieslice([cx - R, cy - R, cx + R, cy + R], a0, a0 + 60, fill=(15, 15, 15))
    d.ellipse([cx - int(R * 0.28), cy - int(R * 0.28), cx + int(R * 0.28), cy + int(R * 0.28)], fill=(235, 190, 20))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(15, 15, 15))
    d.rectangle([60, int(W * 1.08), W - 60, int(W * 1.15)], fill=(15, 15, 15))
    im.save(path); return path


def img_mat(name, path, rough=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path)
    L.new(t.outputs['Color'], N["Principled BSDF"].inputs['Base Color']); N["Principled BSDF"].inputs['Roughness'].default_value = rough
    return m


def tractor(paint):
    """A cab-over tractor unit + 40 ft skeletal chassis (local +Y forward). Returns (root, chassis)."""
    dark = pbr("TruckDark", (0.02, 0.02, 0.022), 0.5); tyre = pbr("Tyre", (0.015, 0.015, 0.015), 0.85)
    chrome = brushed_metal("Chrome", (0.8, 0.8, 0.82), (0.1, 0.2), 0.3)
    gl = glass("CabGlass", (0.35, 0.4, 0.45), 0.02)
    parts = [box("Cab", (0, 2.6, 2.05), (2.5, 2.2, 2.5), paint, bevel=0.12),
             box("Roof", (0, 2.4, 3.45), (2.4, 1.8, 0.4), paint, bevel=0.15),
             box("Bumper", (0, 3.75, 0.75), (2.5, 0.25, 0.45), dark, bevel=0.04),
             box("Grille", (0, 3.71, 1.35), (1.6, 0.06, 0.7), chrome),
             box("Frame", (0, -1.2, 0.95), (1.0, 7.0, 0.35), dark),
             box("Tank", (-1.05, 0.6, 0.95), (0.55, 1.3, 0.6), chrome, bevel=0.2),
             box("Fifth", (0, -2.2, 1.18), (1.2, 1.2, 0.12), dark)]
    for s in (-1, 1):
        parts.append(cyl("Exhaust", (s * 1.0, 1.4, 2.9), 0.09, 2.2, chrome, verts=16))
    for y in (2.9, -1.6, -2.9):
        for s in (-1, 1):
            parts.append(cyl("Wheel", (s * 1.05, y, 0.52), 0.52, 0.4 if y > 0 else 0.6, tyre, verts=28, rot=(0, math.radians(90), 0)))
    cab = join(parts, "Tractor")
    ws = box("Windscreen", (0, 3.705, 2.55), (2.2, 0.04, 1.0), gl); ws.parent = cab
    for s in (-1, 1):
        sw = box("SideWin", (s * 1.255, 2.95, 2.55), (0.04, 1.0, 0.9), gl); sw.parent = cab
        hl = box("HeadL", (s * 0.95, 3.76, 0.95), (0.35, 0.05, 0.18), emissive("HeadLamp", (1.0, 0.92, 0.8), 25)); hl.parent = cab
    ch_parts = [box("Rail", (s * 0.5, -10.5, 1.25), (0.25, 12.4, 0.3), dark) for s in (-1, 1)]
    for y in (-14.5, -15.8):
        for s in (-1, 1):
            ch_parts.append(cyl("TWheel", (s * 1.05, y, 0.52), 0.52, 0.6, tyre, verts=28, rot=(0, math.radians(90), 0)))
    for s in (-1, 1):
        ch_parts.append(box("Tail", (s * 1.0, -16.7, 1.0), (0.3, 0.05, 0.12), emissive("TailLamp", (1.0, 0.08, 0.04), 12)))
    chassis = join(ch_parts, "Chassis"); chassis.parent = cab
    return cab


def build(variant=None):
    c = sc_port.build(None)
    os.makedirs(GEN, exist_ok=True)
    for n in [o.name for o in bpy.data.objects]:                    # drop sc_port's simple scanner + toy truck
        o = bpy.data.objects[n]
        if n.split(".")[0] in ("GatePost", "GateTop", "ScanBar", "Beam", "Truck") or (o.parent and o.parent.name == "Truck"):
            o.hide_render = True
    sodium = emissive("Sodium2", (1.0, 0.62, 0.3), 45)
    steel = pbr("MastSteel", (0.12, 0.12, 0.13), 0.5, 0.6)
    if variant == "stacks":
        for k, (x, y) in enumerate(((-40, 38.2), (0, 38.2), (40, 38.2), (-20, 79.4), (20, 79.4))):
            cyl("Mast", (x, y, 16), 0.35, 32, steel, verts=12)
            for j in range(4):
                box("Flood", (x - 1.5 + j, y, 32.2), (0.8, 0.5, 0.4), sodium)
            l = bpy.data.lights.new("Flood", 'SPOT'); l.energy = 60000; l.spot_size = math.radians(115); l.spot_blend = 0.5
            l.color = (1.0, 0.68, 0.38)
            o = bpy.data.objects.new("Flood", l); bpy.context.collection.objects.link(o); o.location = (x, y, 31.5); point_at(o, (x, y, 0))
        # an RTG gantry crane straddling the next row, rolling slowly along x, with work lights
        yel = pbr("RTG", (0.75, 0.55, 0.06), 0.45, 0.2)
        parts = []
        for s in (-1, 1):
            for dx in (-3.5, 3.5):
                parts.append(box("RTGLeg", (dx, s * 12.0, 9.0), (0.9, 0.9, 18.0), yel))
            parts.append(box("RTGSill", (0, s * 12.0, 0.6), (8.5, 1.2, 1.0), yel))
        for dx in (-3.5, 3.5):
            parts.append(box("RTGBeam", (dx, 0, 18.4), (1.0, 25.0, 1.4), yel))
        parts.append(box("RTGCab", (3.0, 6.0, 16.4), (1.6, 2.0, 1.8), pbr("RTGCab", (0.2, 0.2, 0.22), 0.4)))
        parts.append(box("Spreader", (0, 2.0, 11.0), (L20 + 0.4, W8 + 0.3, 0.6), yel))
        rtg = join(parts, "RTG")
        for dx in (-3.5, 3.5):
            lt = box("RTGLamp", (dx, 0, 17.6), (0.5, 20.0, 0.15), emissive("RTGLamp", (1.0, 0.92, 0.8), 20)); lt.parent = rtg
        sl = bpy.data.lights.new("RTGWork", 'AREA'); sl.energy = 9000; sl.shape = 'RECTANGLE'; sl.size = 6; sl.size_y = 22; sl.color = (1.0, 0.9, 0.75)
        so = bpy.data.objects.new("RTGWork", sl); bpy.context.collection.objects.link(so); so.parent = rtg; so.location = (0, 0, 17.0)
        rtg.location = (30, 58, 0); c["rtg"] = rtg
        c["aisle_y"] = 36.8
        return c
    # ------------------------------------------------------------------ X-ray portal at the gate road (y = 150)
    GX, GY = -120.0, 150.0
    clad = pbr("PortalClad", (0.78, 0.79, 0.8), 0.45, 0.3)
    ylw = pbr("PortalYellow", (0.82, 0.6, 0.05), 0.45, 0.2)
    dark = pbr("PortalDark", (0.08, 0.085, 0.09), 0.45, 0.4)
    for s in (-1, 1):                                                    # two massive clad columns with detector bays
        box("Column", (GX + s * 4.6, GY, 4.5), (1.6, 3.0, 9.0), clad, bevel=0.05)
        box("Detector", (GX + s * 3.75, GY, 4.4), (0.12, 1.4, 7.4), dark)
        box("Plinth", (GX + s * 4.6, GY, 0.3), (2.2, 3.6, 0.6), pbr("Plinth", (0.4, 0.4, 0.4), 0.8))
        for k in range(6):                                               # yellow/black hazard banding at the base
            box("Hazard", (GX + s * 3.78, GY - 1.45, 0.35 + k * 0.3), (0.06, 0.02, 0.15), ylw if k % 2 == 0 else dark)
    box("Lintel", (GX, GY, 9.6), (10.8, 3.4, 1.6), clad, bevel=0.05)
    box("SourceHousing", (GX, GY, 10.9), (3.2, 2.4, 1.2), ylw, bevel=0.06)
    box("Canopy", (GX, GY, 10.45), (11.4, 4.2, 0.12), dark)
    sign = trefoil_sign(os.path.join(GEN, "radiation_sign.png"))
    sm = img_mat("RadSign", sign)
    for s in (-1, 1):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(GX + s * 4.6, GY - 1.52, 5.6), rotation=(math.radians(90), 0, 0))
        o = bpy.context.active_object; o.scale = (0.8, 1.04, 1); o.data.materials.append(sm)
    # flashing amber beacons on the lintel + "scan in progress" red lamps
    for k, (sx, ph) in enumerate(((-4.0, 0), (4.0, 12))):
        bm = bpy.data.materials.new(f"Beacon{k}"); bm.use_nodes = True
        Nn = bm.node_tree.nodes; Ll = bm.node_tree.links; Nn.clear()
        o_ = Nn.new("ShaderNodeOutputMaterial"); em = Nn.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.55, 0.08, 1)
        v = Nn.new("ShaderNodeValue"); dd = v.outputs[0].driver_add("default_value").driver; dd.type = 'SCRIPTED'
        dd.expression = f"40 * (1 if ((frame + {ph}) % 24) < 10 else 0.03)"
        Ll.new(v.outputs[0], em.inputs['Strength']); Ll.new(em.outputs[0], o_.inputs['Surface'])
        cyl("Beacon", (GX + sx, GY - 1.0, 10.65), 0.2, 0.35, bm, verts=16)
        bl = bpy.data.lights.new(f"BeaconL{k}", 'POINT'); bl.color = (1.0, 0.55, 0.1); bl.shadow_soft_size = 0.15
        dl = bl.driver_add("energy").driver; dl.type = 'SCRIPTED'; dl.expression = f"1500 * (1 if ((frame + {ph}) % 24) < 10 else 0.03)"
        bo = bpy.data.objects.new(f"BeaconL{k}", bl); bpy.context.collection.objects.link(bo); bo.location = (GX + sx, GY - 1.6, 10.7)
    # control booth with lit windows, traffic lights, kerbs, lane markings, barrier arm
    box("Booth", (GX - 10.5, GY - 4.0, 1.6), (3.4, 4.2, 3.2), clad, bevel=0.04)
    box("BoothRoof", (GX - 10.5, GY - 4.0, 3.3), (3.9, 4.7, 0.2), dark)
    box("BoothWin", (GX - 8.78, GY - 4.0, 1.9), (0.04, 3.4, 1.1), emissive("BoothWin", (1.0, 0.88, 0.7), 2.5))
    area_light((GX - 8.4, GY - 4.0, 1.9), (0, math.radians(90), 0), 2.5, 200, (1.0, 0.85, 0.65)).visible_camera = False
    box("TLPole", (GX + 6.5, GY - 6.0, 2.0), (0.2, 0.2, 4.0), dark)
    box("TLHead", (GX + 6.5, GY - 6.1, 3.8), (0.4, 0.3, 1.1), dark)
    box("TLRed", (GX + 6.5, GY - 6.27, 4.1), (0.22, 0.02, 0.22), emissive("TLRed", (1.0, 0.1, 0.05), 25))
    box("Barrier", (GX + 5.0, GY - 7.5, 1.1), (6.0, 0.15, 0.15), pbr("BarrierArm", (0.9, 0.9, 0.88), 0.5))
    for s in (-1, 1):
        box("Kerb", (GX + s * 6.3, GY, 0.12), (0.4, 120, 0.25), pbr("Kerb", (0.5, 0.5, 0.48), 0.8))
    paint = pbr("RoadPaint", (0.8, 0.8, 0.75), 0.5)
    for k in range(-12, 12):
        box("Dash", (GX, GY + k * 6.0, 0.02), (0.15, 3.0, 0.02), paint)
    box("Stop", (GX, GY - 8.0, 0.02), (11.0, 0.4, 0.02), paint)
    for k in range(4):                                                   # yard floodlights around the portal
        x = GX + (-14 if k % 2 else 14); y = GY + (-12 if k < 2 else 12)
        cyl("Mast", (x, y, 9), 0.25, 18, dark, verts=10)
        box("Flood", (x, y, 18.2), (1.2, 0.6, 0.4), sodium)
        l = bpy.data.lights.new("Flood", 'SPOT'); l.energy = 25000; l.spot_size = math.radians(100); l.color = (1.0, 0.7, 0.42)
        o = bpy.data.objects.new("Flood", l); bpy.context.collection.objects.link(o); o.location = (x, y, 17.8); point_at(o, (GX, GY, 0))
    truck = tractor(pbr("TruckPaint", (0.08, 0.2, 0.42), 0.35, 0.3))
    cont = instance(bpy.data.objects["ContP2"], (0, 0, 0))
    cont.parent = truck; cont.location = (0, -10.4, 1.4 + H8 / 2); cont.rotation_euler = (0, 0, math.radians(90))
    truck.location = (GX, GY - 40, 0); c["truck"] = truck; c["gate"] = Vector((GX, GY, 4.5))
    return c


def anim_stacks(c, t):
    c["rtg"].location.x = 30 - 14 * t


def anim_xray(c, t):
    c["truck"].location.y = 108 + 40.0 * t                  # approaches, the cab passes the portal ~2/3 in, container in the scan


def cam_stacks(c, t):
    e = ease(t)
    y = c["aisle_y"]
    return (Vector((-78, y, 2.1)).lerp(Vector((-60, y, 2.5)), e), Vector((40, y + 9, 10)), 28)


def cam_xray(c, t):
    e = ease(t)
    return (Vector((-99.0, 108.0, 3.0)).lerp(Vector((-100.5, 112.0, 3.2)), e), Vector((-120, 140, 4.0)), 26)


MOVES = {"stacks": dict(kind="anim", far=1200.0, anim=anim_stacks, cam=cam_stacks),
         "xray": dict(kind="anim", far=1200.0, anim=anim_xray, cam=cam_xray)}
