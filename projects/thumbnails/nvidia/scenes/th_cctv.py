"""Thumbnail 4 - THE WATCHER WATCHED. The film's rainy shophouse street, red-lit. The woman in her dark coat walks toward
us under an umbrella. In the foreground, big and sharp on an arcade pillar, a CCTV camera points at her, its red
record light on. Right third: the dark wet street for the title."""
import math
import bpy
from mathutils import Vector
import sc_street
from sc_street import STREET_W, place_walker_toward
from kit import pbr, emissive, box, cyl
from thumbkit import *

EXPOSURE = 0.3
VIGNETTE = 0.7


def build(variant=None):
    c = sc_street.build("haze")
    strip_lettering()
    p = place_walker_toward(c, 0.55)              # she walks toward -X along her pavement
    sc_street.move_traffic(c, 1.0)
    for v in c["traffic"]:
        if v.get("bus"):
            v["o"].location = (-200, 0, -50)
    h = c["h"]
    look = Vector((p.x - 6, p.y - 0.6, 1.5))
    gaze(h, look)
    # the CCTV camera on a pillar, foreground left of frame
    cam_loc = Vector((p.x - 7.2, c["walk_y"] - 0.45, 1.75))
    cc, cm, lo, hi = asset("security_camera_02", (0, 0, 0), 0)
    size = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    k = 0.42 / size; cc.scale = (k, k, k)
    vcam = Vector((p.x - 9.2, c["walk_y"] - 1.35, 1.45))
    cc.location = vcam + Vector((1.15, 0.36, 0.2))
    cc.rotation_euler = (math.radians(10), 0, math.radians(97))       # lens (-Y) turned to +X: down the pavement at her
    bpy.context.view_layer.update()
    clo, chi = ph_bounds(cm)
    bm = pbr("BracketM", (0.05, 0.05, 0.055), 0.5, 0.6)
    cx, cy = (clo.x + chi.x) / 2, (clo.y + chi.y) / 2
    box("Bracket", (cx - 0.08, cy, chi.z + 0.02), (0.22, 0.05, 0.04), bm)
    box("Pole", (cx - 0.18, cy, (chi.z + 3.6) / 2), (0.05, 0.05, 3.6 - chi.z), bm)
    for mt in bpy.data.materials:                 # lanterns calmer: the right third stays dark for the title
        if mt.name.startswith("Lantern") and mt.use_nodes:
            mt.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = 1.5
    rec = point(Vector(((clo.x + chi.x) / 2 + 0.02, (clo.y + chi.y) / 2, chi.z + 0.01)), 0.6, (1.0, 0.03, 0.02), 0.005, "RecLed")
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.008, location=rec.location)
    bpy.context.active_object.data.materials.append(emissive("Rec", (1.0, 0.02, 0.01), 60))
    # red wash: a lit red sign beside her and red light spilling on the wet pavement; a cool rim on the camera body
    point((p.x + 2.0, p.y + 1.4, 3.2), 700, (1.0, 0.06, 0.04), 0.6, "RedSpill")
    spot((p.x - 2.5, p.y - 2.5, 3.0), Vector((p.x, p.y, 1.3)), 300, (1.0, 0.12, 0.08), 30, 0.7, 0.3, "RedKey")
    rim = soft(cc.location + Vector((-0.6, -0.9, 0.5)), cc.location, 30, (0.55, 0.7, 1.0), size=0.5, name="CamRim")
    light_only(rim, cm)
    rain_curtains([p.y - 2.2, p.y - 4.8], width=30, height=9, x0=p.x - 4, density=0.94, strength=0.5)
    c["cam"] = (vcam, Vector((p.x, p.y - 1.2, 1.55)), 45)
    c["focus"] = Vector((p.x, p.y, 1.5))
    c["fstop"] = 3.5
    c["cctv"] = cc
    return c


def ph_bounds(meshes):
    import ph
    return ph.bounds(meshes)
