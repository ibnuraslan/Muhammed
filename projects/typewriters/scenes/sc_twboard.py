"""THE INVESTIGATORS' BOARD (Ch4 8B): what is known, pinned up; what is not, left as empty pins.

Ch4 8B  board  "The full list ... is beyond what investigators can reconstruct." - a cork board under a raking desk
               lamp: printed photos of earlier scenes (the evidence hall, customs, the attache's office, the TV tower,
               the X-ray film), red string drawing itself between pins, and the string running on to three empty pins
               with torn paper corners. The camera drifts along the string and settles on the empty pins.
"""
import math, os, shutil
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import typewriter as T
import look

DUR = {"board": 7.0}
EXPOSURE = 0.0
STILLS = ["twlab_tags", "twhangar_customs_torch", "twoffice_attache", "twcity_tower", "twmeade_film", "twambassador_talks_wide",
          "twvault_tape", "twembassy_street_push"]
PHOTO_DIR = os.path.join(T.GEN, "board_photos")


def photo_mat(name, path):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path)
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs['Factor'].default_value = 0.12          # a little faded print
    mx.inputs[7].default_value = (0.75, 0.68, 0.55, 1); L.new(t.outputs[0], mx.inputs[6]); L.new(mx.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.45; p.inputs['Coat Weight'].default_value = 0.3
    return m


def build(variant=None):
    c = {}
    os.makedirs(PHOTO_DIR, exist_ok=True)
    for nm in STILLS:                                   # our own renders, printed out as the investigators' photos
        src = f"/tmp/claude-0/st/{nm}.png"; dst = os.path.join(PHOTO_DIR, nm + ".png")
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy(src, dst)
    w = bpy.context.scene.world or bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.01
    box("Wall", (0, 0.05, 1.5), (5, 0.1, 3), ph.texture("painted_plaster_wall", scale=0.5, name="BoardWall", tint=(0.5, 0.48, 0.44)))
    cork = ph.texture("oriented_strand_board", scale=0.6, name="Cork", tint=(0.8, 0.6, 0.4))
    box("Cork", (0, -0.01, 1.45), (2.2, 0.03, 1.2), cork)
    frame = ph.texture("dark_wood", scale=1.0, name="BoardFrame")
    for (x, z, sx, sz) in ((0, 2.07, 2.3, 0.05), (0, 0.83, 2.3, 0.05), (-1.13, 1.45, 0.05, 1.29), (1.13, 1.45, 0.05, 1.29)):
        box("Frame", (x, -0.02, z), (sx, 0.05, sz), frame)
    rng = np.random.default_rng(11)
    pins_m = pbr("PinRed", (0.55, 0.04, 0.03), 0.3)
    spots = [(-0.82, 1.78), (-0.35, 1.62), (0.12, 1.84), (-0.7, 1.15), (-0.15, 1.2), (0.38, 1.38), (0.62, 1.8), (-0.42, 0.98)]
    c["pins"] = []
    for k, (x, z) in enumerate(spots):
        nm = STILLS[k]; path = os.path.join(PHOTO_DIR, nm + ".png")
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, -0.03, z), rotation=(math.radians(90), rng.uniform(-0.06, 0.06), 0))
        ph_o = bpy.context.active_object; ph_o.scale = (0.3, 0.13, 1)
        if os.path.exists(path):
            ph_o.data.materials.append(photo_mat(f"Photo{k}", path))
        else:
            ph_o.data.materials.append(pbr("PhotoBlank", (0.5, 0.48, 0.44), 0.6))
        pin = cyl(f"Pin{k}", (x, -0.045, z + 0.05), 0.008, 0.02, pins_m, verts=12, rot=(math.radians(90), 0, 0))
        c["pins"].append(Vector((x, -0.055, z + 0.05)))
    # the trail runs on to empty pins: torn paper corners left where a photo was taken down
    paper = pbr("TornCorner", (0.75, 0.72, 0.64), 0.8)
    for k, (x, z) in enumerate(((0.78, 1.18), (0.95, 1.55), (0.85, 0.98))):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x - 0.01, -0.031, z - 0.02), rotation=(math.radians(90), 0.4 * k, 0))
        o = bpy.context.active_object; o.scale = (0.045, 0.035, 1); o.data.materials.append(paper)
        cyl(f"EmptyPin{k}", (x, -0.045, z), 0.008, 0.02, pins_m, verts=12, rot=(math.radians(90), 0, 0))
        c["pins"].append(Vector((x, -0.055, z)))
    # red string through the pins in order, drawn on by animating the curve's bevel end
    order = [0, 1, 4, 3, 7, 4, 5, 2, 6, 5, 8, 9, 10]
    cu = bpy.data.curves.new("String", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0018; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(len(order) - 1)
    for i, k in enumerate(order):
        p = c["pins"][k]; sp.points[i].co = (p.x, p.y, p.z, 1)
    so = bpy.data.objects.new("String", cu); bpy.context.collection.objects.link(so)
    so.data.materials.append(pbr("RedString", (0.6, 0.04, 0.03), 0.6))
    c["string"] = cu
    # a desk lamp low and to the side: raking light across the cork, the far end falls into shadow
    l = bpy.data.lights.new("BoardLamp", 'SPOT'); l.energy = 260; l.spot_size = math.radians(70); l.spot_blend = 0.6; l.color = (1.0, 0.8, 0.55)
    lo = bpy.data.objects.new("BoardLamp", l); bpy.context.collection.objects.link(lo); lo.location = (-1.6, -1.0, 1.0); point_at(lo, (0.0, 0.0, 1.45))
    f = area_light((1.5, -2.0, 2.2), (0, 0, 0), 1.5, 8, (0.85, 0.88, 0.95)); point_at(f, (0, 0, 1.4)); f.visible_camera = False
    animate(c, 0.0, "board")
    return c


def animate(c, sec, shot):
    c["string"].bevel_factor_end = min(1.0, 0.15 + sec / 5.0)
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_board(c, t):
    e = ease(t)                           # drifts along the string, ends on the empty pins
    x = -0.55 + 1.3 * e
    return (Vector((x * 0.6 - 0.2, -2.6 + 0.4 * e, 1.5)), Vector((x * 0.6, 0.0, 1.42)), 35)


MOVES = {"board": dict(kind="anim", dof=3.0, cam=cam_board, focus=lambda c, t: Vector((-0.55 + 1.3 * ease(t), -0.04, 1.42)), anim=anim("board"), dur=DUR["board"])}
