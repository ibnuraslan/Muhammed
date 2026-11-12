"""CH4 (chat B): the 2000s forensic DNA lab (generic, no crest, no readable text) and an evidence bench.
Variants:
  lab:   cool clinical light, one hard key; the reconstructed box (chat A's model, empty evidence) on a steel platform.
         swab  (A): a technician in a lab gown swabs a corner of the box (medium)
         seq   (B): a capillary sequencer's tray slides in; its monitor draws peaks while she watches
         bags  (A): an analyst lays a bagged screw beside a bagged drinking glass on a light table
         print (B): a printout feeds from the printer; she slides the two bags apart
  evid:  a black evidence bench under a hard top light: the unbadged reel-to-reel recorder.
         orbit (A): slow orbit as its reels begin to turn
         keys  (B): low push across its keys and VU meter, the needle twitching
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import world_flat, ease
from human import reach, fingers_curl
import ph
import b_common as B
import b_props as P

EXPOSURE = 0.2
DUR = {"swab": 5.0, "seq": 5.0, "bags": 5.0, "print": 5.0, "orbit": 6.0, "keys": 5.0}
VARIANT_FOR = {"swab": "lab", "seq": "lab", "bags": "lab", "print": "lab", "orbit": "evid", "keys": "evid"}
BOX_AT = Vector((-1.6, 1.2, 0.0))
LT = Vector((1.6, 1.4, 0.0))          # light table
SEQ = Vector((0.4, 2.55, 0.9))


def peaks_image(path, W=1600, H=900):
    if os.path.exists(path):
        return path
    import skia
    rng = np.random.default_rng(8)
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.Color4f(0.92, 0.93, 0.94, 1))
    p = skia.Paint(AntiAlias=True); p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(3)
    for row, col in enumerate(((0.1, 0.3, 0.8), (0.1, 0.55, 0.2), (0.85, 0.2, 0.1), (0.2, 0.2, 0.2))):
        y0 = 160 + row * 190
        p.setColor4f(skia.Color4f(0.7, 0.7, 0.72, 1)); p.setStrokeWidth(1); cv.drawLine(60, y0, W - 60, y0, p)
        p.setColor4f(skia.Color4f(*col, 1)); p.setStrokeWidth(3)
        pts = []
        for x in range(60, W - 60, 3):
            yv = sum(rng.uniform(0.3, 1.0) * 140 * math.exp(-((x - c_) / 9.0) ** 2) for c_ in (300 + row * 37, 520 + row * 11, 760 + row * 53, 1010, 1250 - row * 29))
            pts.append((x, y0 - yv - rng.uniform(0, 4)))
        path_ = skia.Path(); path_.moveTo(*pts[0])
        for q in pts[1:]:
            path_.lineTo(*q)
        cv.drawPath(path_, p)
    s.makeImageSnapshot().save(path, skia.kPNG)
    return path


def bag(name, loc, content):
    m = pbr("EvBag", (0.92, 0.94, 0.96), 0.12, **{'Transmission Weight': 0.85, 'IOR': 1.4})
    b_ = box(name, (0, 0, 0.012), (0.2, 0.28, 0.024), m, bevel=0.01)
    strip = box(name + "Seal", (0, 0.12, 0.025), (0.2, 0.02, 0.002), pbr("SealRed", (0.6, 0.06, 0.04), 0.5))
    lab = box(name + "Lab", (0, -0.07, 0.025), (0.14, 0.07, 0.001), pbr("BagLab", (0.94, 0.94, 0.92), 0.7))
    root = bpy.data.objects.new(name + "Root", None); bpy.context.collection.objects.link(root)
    for o in (b_, strip, lab, content):
        o.parent = root
    root.location = loc
    return root


def build(variant=None):
    variant = variant or "lab"
    c = {"variant": variant}
    world_flat((0.006, 0.007, 0.01), 1.0)
    if variant == "lab":
        box("Floor", (0, 0, -0.01), (9, 7, 0.02), B.tex_mat("LabFl", "grey_tiles", scale=0.5, tint=(0.65, 0.68, 0.7)))
        wall = B.plaster("LabW", (0.56, 0.6, 0.62), dirt=0.08)
        for (loc, size) in (((0, 3.3, 1.5), (9, 0.1, 3)), ((-4.5, 0, 1.5), (0.1, 7, 3)), ((4.5, 0, 1.5), (0.1, 7, 3)), ((0, -3.3, 1.5), (9, 0.1, 3))):
            box("LabWall", loc, size, wall)
        box("LabCeil", (0, 0, 3.0), (9, 7, 0.05), B.plaster("LabC", (0.6, 0.62, 0.63)))
        steel = brushed_metal("LabSteel", (0.62, 0.63, 0.65), (0.2, 0.35), 0.4)
        # the reconstructed box on a low steel platform under a hard key
        try:
            import sc_box as X
            cx = {}
            X.build_box(cx)
            for o in bpy.data.objects:
                if o.parent is None and o.type in ('MESH', 'EMPTY', 'CURVE', 'LIGHT') and not o.name.startswith(("Floor", "Lab")):
                    o.location += BOX_AT + Vector((0, 0, 0.12))
            c["boxctx"] = cx
            # evidence only: the box stands closed and empty here (contents and the leaning cut-away panel removed)
            for o in bpy.data.objects:
                if o.name.startswith(("Bottle", "BoxRadio", "PR", "Choc", "Book", "Blanket", "FrontPanel", "Muffle", "BulbL", "BulbHolder", "Sphere")):
                    o.hide_render = True; o.hide_viewport = True
            box("FrontClosed", (BOX_AT.x, BOX_AT.y - X.D / 2 + X.T / 2, 0.12 + X.Z0 + X.H / 2), (X.W, X.T, X.H), X.mat("pine") if hasattr(X, "mat") else pbr("Pine", (0.5, 0.38, 0.22), 0.7))
            c["box_w"] = X.W
        except Exception as e:
            print("[dna] box unavailable:", e); c["box_w"] = 0.72
        box("Platform", (BOX_AT.x, BOX_AT.y, 0.06), (1.3, 1.1, 0.12), steel)
        B.key_spot((BOX_AT.x + 1.4, BOX_AT.y - 1.6, 2.8), BOX_AT + Vector((0, 0, 0.9)), 600, 32, (0.92, 0.96, 1.0), soft=0.1, name="BoxKey")
        # benches along the back wall: sequencer, monitor, printer; the light table on the right
        for x in (-0.2, 1.7):
            ph.model("metal_office_desk", loc=(x, 2.75, 0), rot_z=0)
        seq = box("Sequencer", (SEQ.x, SEQ.y, 0.79 + 0.45), (0.75, 0.6, 0.9), pbr("SeqBeige", (0.72, 0.72, 0.7), 0.45), bevel=0.02)
        box("SeqWin", (SEQ.x - 0.12, SEQ.y - 0.302, 0.79 + 0.62), (0.4, 0.01, 0.35), pbr("SeqWinG", (0.05, 0.07, 0.08), 0.05, **{'Coat Weight': 1.0}))
        c["tray"] = box("SeqTray", (SEQ.x + 0.15, SEQ.y - 0.3, 0.79 + 0.25), (0.3, 0.3, 0.04), pbr("Tray", (0.3, 0.32, 0.35), 0.4, 0.5))
        cyl("SeqLED", (SEQ.x + 0.28, SEQ.y - 0.305, 0.79 + 0.82), 0.008, 0.005, emissive("SeqLEDm", (0.3, 1.0, 0.4), 6.0), verts=12, rot=(math.radians(90), 0, 0))
        pk = peaks_image(os.path.join(B.GEN, "b_peaks.png"))
        sm = P.screen_mat("Peaks", pk, 1.1, cursor=True, cursor_speed=0.12, cursor_start=0.04)
        P.lcd_monitor("SeqMon", (-0.55, 2.6, 0.79), math.radians(10), sm, w=0.5, h=0.31)
        c["printer"] = box("LabPrinter", (2.3, 2.7, 0.79 + 0.1), (0.45, 0.38, 0.2), pbr("LabPr", (0.55, 0.56, 0.57), 0.4), bevel=0.01)
        c["sheet"] = B.sheet("PeakPrint", (0, 0, -30), (0.21, 0.297), B.img_mat("PeakPrintM", pk, 0.8))
        box("LightTable", (LT.x, LT.y, 0.45), (1.2, 0.7, 0.9), pbr("LTB", (0.3, 0.31, 0.32), 0.5), bevel=0.01)
        box("LightTop", (LT.x, LT.y, 0.905), (1.1, 0.6, 0.01), emissive("LTGlow2", (0.95, 0.97, 1.0), 2.5))
        screw = cyl("Screw", (0, 0, 0.03), 0.004, 0.05, pbr("ScrewZn", (0.55, 0.55, 0.5), 0.3, 1.0), verts=12, rot=(0, math.radians(90), 0.3))
        glass_o = cyl("Tumbler", (0, 0, 0.045), 0.035, 0.09, glass("Tumb", (0.9, 0.92, 0.92), 0.02), verts=32)
        c["bag_screw"] = bag("BagScrew", (LT.x - 0.18, LT.y - 0.02, 0.912), screw)
        c["bag_glass"] = bag("BagGlass", (LT.x + 0.2, LT.y + 0.02, 0.912), glass_o)
        c["bag_glass"].rotation_euler = (math.radians(90), 0, 0) if False else (0, 0, 0)
        for x in (-2.0, 1.0):
            box("LabTube", (x, 0.5, 2.96), (0.15, 1.4, 0.04), emissive("LabTubeE", (0.88, 0.95, 1.0), 2.0))
            l = area_light((x, 0.5, 2.9), (0, 0, 0), 1.2, 30, (0.86, 0.94, 1.0)); l.visible_camera = False
        B.fill((3.5, -2.5, 2.2), (0, 1.5, 1.0), 20, 2.0, (0.5, 0.6, 0.8))
        tech = B.person("LabTech", 0.0, 38, "female_elegantsuit01", "ponytail01", hue=0.55, sat=0.15, val=2.4, hair_val=0.3)
        ana = B.person("Analyst", 0.0, 45, "female_elegantsuit01", "bob01", hue=0.55, sat=0.12, val=2.2, hair_val=0.6)
        bw = c["box_w"]
        B.stand(tech, (BOX_AT.x + bw / 2 + 0.45, BOX_AT.y - 0.35, 0), -math.pi / 2 + 0.4)      # at the box's +X corner
        B.stand(ana, (LT.x, LT.y - 0.65, 0), math.pi)                                         # at the light table
        B.flat_clothes(tech, (0.62, 0.7, 0.74)); B.flat_clothes(ana, (0.85, 0.86, 0.86))
        c["tech"], c["ana"] = tech, ana
        c["rest"] = {"tech": B.capture(tech), "ana": B.capture(ana)}
        c["swab"] = cyl("Swab", (0, 0, 0), 0.0025, 0.15, pbr("SwabStick", (0.92, 0.92, 0.9), 0.6), verts=8)
        B.room_haze((0, 0, 1.5), (8.8, 6.8, 3.0), density=0.008)
    else:
        box("Floor", (0, 0, -0.01), (8, 8, 0.02), B.tex_mat("EvFl", "concrete_floor_02", scale=0.5, tint=(0.4, 0.4, 0.4)))
        bench = box("EvBench", (0, 0, 0.45), (1.6, 0.9, 0.9), pbr("EvBlack", (0.015, 0.015, 0.017), 0.35, **{'Coat Weight': 0.4}), bevel=0.01)
        c["rec"] = P.reel_recorder("Seized", (0, 0, 0.9), rot_z=0.0, spin=0.4, start_frame=24)
        box("EvTag", (0.3, -0.2, 0.902), (0.07, 0.12, 0.002), pbr("EvTagW", (0.88, 0.85, 0.75), 0.7), rot=(0, 0, 0.3))
        B.key_spot((0.0, 0.0, 3.0), (0, 0, 0.9), 900, 22, (1.0, 0.86, 0.68), soft=0.08, blend=0.25, name="TopKey")
        B.fill((-2.5, -2.5, 1.5), (0, 0, 1.0), 6, 2.0, (0.4, 0.5, 0.75))
        B.room_haze((0, 0, 1.5), (6, 6, 3), density=0.02)
    return c


def anim(c, t, move):
    sec = t * DUR[move]
    if c["variant"] == "lab":
        for k in ("tech", "ana"):
            B.apply_pose(c[k], c["rest"][k])
        tech, ana = c["tech"], c["ana"]
        bw = c["box_w"]
        corner = BOX_AT + Vector((bw / 2 + 0.005, -0.31 + 0.04, 0.12 + 0.95))
        tip = corner + Vector((0.004, 0.02 * math.sin(sec * 2.5), 0.015 * math.sin(sec * 1.7)))
        reach(tech, "R", tip + Vector((0.12, -0.04, -0.03)), Vector((0.3, -0.5, -1)), Vector((-1, 0.2, 0.2)))
        reach(tech, "L", tech.bone_head("spine02") + B.fwd_of(tech) * 0.2 + Vector((0, 0, -0.1)), Vector((0, -0.5, -1)), B.fwd_of(tech))
        fingers_curl(tech, 45, side=("R",), thumb=25)
        tech.rot("head", (0, 0, 1), 5); B.nod(tech, 8)
        sw = c["swab"]; w = tech.bone_tail("wrist.R"); d = tip - w
        sw.location = w + d * 0.55; sw.rotation_mode = 'QUATERNION'; sw.rotation_quaternion = d.to_track_quat('Z', 'Y')
        # tray slides in, the printer feeds a sheet, the analyst moves the bags apart
        c["tray"].location.y = SEQ.y - 0.3 + 0.25 * ease(min(1.0, max(0.0, (sec - 0.8) / 1.5))) if move == "seq" else SEQ.y - 0.3
        if move == "print":
            u = ease(min(1.0, sec / 2.2))
            c["sheet"].location = Vector((2.3, 2.7 - 0.05 - 0.3 * u, 0.79 + 0.18 - 0.06 * u)); c["sheet"].rotation_euler = (math.radians(-20 * (1 - u)), 0, 0)
        mv = ease(min(1.0, max(0.0, (sec - 1.8) / 1.4))) if move in ("print",) else (ease(min(1.0, max(0.0, (sec - 0.5) / 1.6))) if move == "bags" else 0.0)
        if move == "bags":
            c["bag_screw"].location = Vector((LT.x - 0.5, LT.y - 0.15, 0.912)).lerp(Vector((LT.x - 0.18, LT.y - 0.02, 0.912)), mv)
            hand_t = c["bag_screw"].location
        else:
            c["bag_screw"].location = Vector((LT.x - 0.18, LT.y - 0.02, 0.912)).lerp(Vector((LT.x - 0.38, LT.y - 0.05, 0.912)), mv)
            hand_t = c["bag_screw"].location
        reach(ana, "R", hand_t + Vector((0.0, -0.1, 0.05)), Vector((0.4, -0.6, -0.8)), Vector((0, 1, -0.6)))
        reach(ana, "L", Vector((LT.x + 0.15, LT.y - 0.3, 0.95)), Vector((-0.4, -0.6, -0.8)), Vector((0, 1, -0.6)))
        fingers_curl(ana, 30); B.nod(ana, 25)
    else:
        pass
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


def cam_orbit(c, t):
    a = math.radians(-60 + 50 * ease(t)); r = 1.5
    return (Vector((r * math.sin(a), -r * math.cos(a), 1.45)), Vector((0, 0.02, 0.98)), 40)


MOVES = {
    "swab": dict(kind="anim", dof=2.8, cam=cam((1.2, -1.8, 1.6), (0.9, -1.4, 1.55), (BOX_AT.x + 0.5, BOX_AT.y - 0.2, 1.05), 30),
                 anim=lambda c, t: anim(c, t, "swab"), focus=lambda c, t: c["tech"].bone_head("head")),
    "seq": dict(kind="anim", dof=2.8, cam=cam((1.4, 0.2, 1.55), (1.1, 0.6, 1.5), (0.0, 2.6, 1.1), 32),
                anim=lambda c, t: anim(c, t, "seq"), focus=lambda c, t: SEQ + Vector((0, -0.3, 0.3))),
    "bags": dict(kind="anim", dof=2.4, cam=cam((3.4, -0.9, 1.8), (3.1, -0.6, 1.75), (LT.x, LT.y, 0.95), 32),
                 anim=lambda c, t: anim(c, t, "bags"), focus=lambda c, t: LT + Vector((0, 0, 0.92))),
    "print": dict(kind="anim", dof=2.4, cam=cam((0.4, 0.0, 1.6), (0.7, 0.3, 1.55), (2.0, 2.0, 0.95), 32),
                  anim=lambda c, t: anim(c, t, "print"), focus=lambda c, t: Vector((2.2, 2.3, 0.95))),
    "orbit": dict(kind="anim", dof=2.0, cam=cam_orbit, anim=lambda c, t: anim(c, t, "orbit"), focus=lambda c, t: Vector((0, 0.04, 1.0))),
    "keys": dict(kind="anim", dof=1.6, cam=cam((-0.65, -0.75, 1.3), (-0.45, -0.6, 1.24), (0.08, -0.08, 0.98), 45),
                 anim=lambda c, t: anim(c, t, "keys"), focus=lambda c, t: Vector((0.0, -0.13, 1.07))),
}
