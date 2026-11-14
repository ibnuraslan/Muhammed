"""CH4 6B redo (188 f): the boardroom after the meeting. Papers collected into one neat stack beside a closed folder,
a small generic nameplate reading CHAIR at the head of the table, the head chair turned away from the table; the
night city beyond the glass. A slow push along the table onto the folder and the nameplate; the glass reflections
drift with the camera, and one city window behind blinks off."""
import math
import bpy
from mathutils import Vector
from kit import *
import sc_boardroom

EXPOSURE = 0.0
FRAMES = {"folder": 188}


def build(variant=None):
    c = sc_boardroom.build(None)
    for n in ("Folder", "Paper"):
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = True
    # the head chair, turned ~70 degrees away from the table (someone stood up and left)
    for o in bpy.data.objects:
        if o.name.startswith("Chair") and abs(o.location.y - 3.55) < 0.05 and abs(o.location.x) < 0.05:
            o.rotation_euler = (0, 0, math.pi + math.radians(70)); o.location.x += 0.25
    manila = pbr("Manila2", (0.5, 0.38, 0.2), 0.75)
    paper = pbr("Paper2", (0.88, 0.87, 0.83), 0.8)
    box("FolderClosed", (0.18, 2.55, 0.776), (0.24, 0.32, 0.012), manila, bevel=0.002, rot=(0, 0, 0.06))
    box("FolderTab", (0.27, 2.72, 0.776), (0.08, 0.03, 0.012), manila, rot=(0, 0, 0.06))
    for k in range(14):                                           # collected papers, slightly fanned
        box("Stack", (-0.22 + 0.002 * (k % 3), 2.5 + 0.001 * k, 0.772 + k * 0.0012), (0.21, 0.297, 0.001), paper,
            rot=(0, 0, -0.04 + 0.006 * (k % 4)))
    box("Clip", (-0.22, 2.36, 0.79), (0.04, 0.012, 0.012), brushed_metal("Clip", (0.7, 0.7, 0.72), (0.15, 0.3), 0.4))
    # nameplate: a dark acrylic wedge with a brushed plate and the word CHAIR (generic)
    wedge = pbr("Wedge", (0.02, 0.02, 0.022), 0.15, 0.0, **{'Coat Weight': 0.8})
    box("PlateBase", (0.0, 2.95, 0.805), (0.34, 0.07, 0.06), wedge, bevel=0.004, rot=(math.radians(18), 0, 0))
    plate = brushed_metal("Plate", (0.75, 0.62, 0.38), (0.15, 0.3), 0.6)
    box("Plate", (0.0, 2.908, 0.81), (0.3, 0.004, 0.05), plate, rot=(math.radians(18), 0, 0))
    t = text_obj("ChairText", "CHAIR", (0.0, 2.9045, 0.81), 0.032, pbr("Ink", (0.03, 0.03, 0.03), 0.4),
                 rot=(math.radians(90 + 18), 0, 0), extrude=0.0004, spacing=1.25)
    t.data.align_y = 'CENTER'
    cyl("Glass", (-0.45, 2.7, 0.82), 0.035, 0.1, glass("TumblerG", (0.95, 0.97, 0.98), 0.0), verts=24)
    cyl("Pen", (0.42, 2.5, 0.778), 0.005, 0.14, pbr("Pen", (0.03, 0.03, 0.04), 0.2, 0.8), verts=12, rot=(math.radians(90), 0, 0.9))
    c["target"] = Vector((0.0, 2.75, 0.8))
    return c


def cam(c, t):
    e = ease(t)
    return (Vector((0.75, 0.75, 1.3)).lerp(Vector((0.42, 1.65, 1.16)), e), Vector((0.0, 2.8, 0.8)), 40)


MOVES = {"folder": dict(kind="anim", dof=2.2, far=40.0, cam=cam, focus=lambda c, t: c["target"])}
