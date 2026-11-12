"""COMMUNICATIONS VAULT (dramatization). A windowless secure room: painted steel walls, a vault door, racks of
cipher machines with indicator lamps, teletypes printing and punching tape.

Intro 7A  push   slow push past a teletype printing and punching tape beside a cipher machine (room lit)
Intro 7B  sweep  the room dark: a Marine's flashlight sweeps across the machines
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import machines as MC

EXPOSURE = 0.0
DUR = {"push": 4.5, "sweep": 5.0, "tape": 4.5, "pouch": 5.0}
TAPE_AT = Vector((-0.38, 0.52, 1.07))
DESK2 = Vector((2.6, -1.8, 0.0))
VARIANT_FOR = {"sweep": "dark"}


def build(variant=None):
    c = {"variant": variant}
    dark = variant == "dark"
    world_flat((0.003, 0.004, 0.006), 1.0)
    box("Floor", (0, 0, -0.01), (8, 6, 0.02), ph.texture("concrete_floor_painted", scale=0.5, name="VaultFloor", tint=(0.6, 0.65, 0.62)))
    steel = pbr("VaultWall", (0.32, 0.35, 0.33), 0.5, 0.3)
    N = steel.node_tree.nodes; L = steel.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = 1.2; br.inputs['Row Height'].default_value = 1.0
    br.inputs['Color1'].default_value = (0.32, 0.35, 0.33, 1); br.inputs['Color2'].default_value = (0.3, 0.33, 0.31, 1); br.inputs['Mortar'].default_value = (0.1, 0.11, 0.1, 1)
    L.new(tc.outputs['Object'], br.inputs['Vector']); L.new(br.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    for (x, y, sx, sy) in ((0, 3.05, 8, 0.1), (0, -3.05, 8, 0.1), (-4.05, 0, 0.1, 6), (4.05, 0, 0.1, 6)):
        box("Wall", (x, y, 1.4), (sx, sy, 2.8), steel)
    box("Ceiling", (0, 0, 2.82), (8, 6, 0.04), pbr("VaultCeil", (0.4, 0.4, 0.39), 0.8))
    # vault door (round-cornered steel slab with a wheel) on the -X wall
    door_m = pbr("VaultDoor", (0.5, 0.52, 0.5), 0.35, 0.9)
    box("VaultDoor", (-3.97, 0.8, 1.05), (0.12, 1.1, 2.0), door_m, bevel=0.04)
    cyl("Wheel", (-3.88, 0.8, 1.1), 0.22, 0.04, door_m, verts=32, rot=(0, math.radians(90), 0))
    for k in range(4):
        box("Spoke", (-3.86, 0.8, 1.1), (0.02, 0.46, 0.03), door_m, rot=(k * math.pi / 4, 0, 0))
    # racks of cipher machines along the back wall, teletypes in front, a terminal desk
    c["lamps"] = []
    for k in range(6):
        x = -3.0 + k * 0.75
        for j in range(3):
            MC.cipher(f"VC{k}{j}", (x, 2.65, j * 0.52), 0.0, height=0.48)
        box("RackFrame", (x, 2.7, 0.78), (0.6, 0.6, 1.58), pbr("Rack", (0.08, 0.08, 0.085), 0.4, 0.6))
    MC.lamp_blink(period=19, strength=8.0)
    c["tty"] = []
    for k, x in enumerate((-1.0, 0.5, 2.0)):
        r, p = MC.teletype(f"VTTY{k}", (x, 0.6, 0), math.radians(5 * (k - 1))); c["tty"].append(p)
    MC.cipher("VCdesk", (-1.0 + 0.62, 0.62, 0.72), 0.0, height=0.3)       # beside the first teletype
    # the punched tape running through the cipher machine's reader: a long strip with a moving hole pattern
    tape_m = bpy.data.materials.new("PunchTape"); tape_m.use_nodes = True
    N = tape_m.node_tree.nodes; L = tape_m.node_tree.links; p_ = N["Principled BSDF"]
    uv = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); L.new(uv.outputs['UV'], mp.inputs['Vector'])
    dv = mp.inputs['Location'].driver_add("default_value", 0).driver; dv.type = 'SCRIPTED'; dv.expression = "frame * 0.004"
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 1.0; L.new(mp.outputs[0], br.inputs['Vector'])
    vn = N.new("ShaderNodeTexWhiteNoise"); vn.noise_dimensions = '2D'
    sx = N.new("ShaderNodeVectorMath"); sx.operation = 'MULTIPLY'; sx.inputs[1].default_value = (180, 8, 1); L.new(mp.outputs[0], sx.inputs[0])
    fl = N.new("ShaderNodeVectorMath"); fl.operation = 'FLOOR'; L.new(sx.outputs[0], fl.inputs[0]); L.new(fl.outputs[0], vn.inputs['Vector'])
    fr = N.new("ShaderNodeVectorMath"); fr.operation = 'FRACTION'; L.new(sx.outputs[0], fr.inputs[0])
    ds = N.new("ShaderNodeVectorMath"); ds.operation = 'DISTANCE'; ds.inputs[1].default_value = (0.5, 0.5, 0); L.new(fr.outputs[0], ds.inputs[0])
    hole = N.new("ShaderNodeMath"); hole.operation = 'LESS_THAN'; hole.inputs[1].default_value = 0.3; L.new(ds.outputs['Value'], hole.inputs[0])
    on = N.new("ShaderNodeMath"); on.operation = 'GREATER_THAN'; on.inputs[1].default_value = 0.45; L.new(vn.outputs['Value'], on.inputs[0])
    hh = N.new("ShaderNodeMath"); hh.operation = 'MULTIPLY'; L.new(hole.outputs[0], hh.inputs[0]); L.new(on.outputs[0], hh.inputs[1])
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(hh.outputs[0], inv.inputs[1])
    L.new(inv.outputs[0], p_.inputs['Alpha']); p_.inputs['Base Color'].default_value = (0.82, 0.74, 0.52, 1); p_.inputs['Roughness'].default_value = 0.8
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); tp = bpy.context.active_object; tp.name = "Tape"
    tp.scale = (0.9, 0.025, 1); bpy.ops.object.transform_apply(scale=True); tp.data.materials.append(tape_m)
    tp.location = TAPE_AT + Vector((0.1, 0, 0.053)); tp.rotation_euler = (0, 0, 0)
    bpy.ops.mesh.primitive_plane_add(size=1); tp2 = bpy.context.active_object; tp2.scale = (0.5, 0.025, 1); bpy.ops.object.transform_apply(scale=True)
    tp2.data.materials.append(tape_m); tp2.location = TAPE_AT + Vector((-0.55, 0, -0.18)); tp2.rotation_euler = (0, math.radians(60), 0)
    # diplomatic pouch on the desk by the terminal: a canvas bag, drawstring, a lead seal on the cord
    canvas = ph.texture("hessian_380", scale=3.0, name="PouchCanvas", tint=(0.55, 0.55, 0.45))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.2, location=(0, 0, 0))
    pouch = bpy.context.active_object; pouch.name = "Pouch"; pouch.scale = (1.3, 0.55, 1.0); bpy.ops.object.shade_smooth(); pouch.data.materials.append(canvas)
    pouch.location = DESK2 + Vector((-0.45, -0.05, 0.8))
    neck = cyl("PouchNeck", DESK2 + Vector((-0.45, -0.05, 1.02)), 0.06, 0.08, canvas, verts=16)
    c["pouch"] = pouch
    seal = join([cyl("PSealCord", (0, 0, 0), 0.003, 0.14, pbr("Cord", (0.5, 0.45, 0.35), 0.8), verts=6),
                 cyl("PSealLead", (0, 0, -0.08), 0.016, 0.014, pbr("PLead", (0.42, 0.43, 0.45), 0.5, 0.8), verts=16, rot=(math.radians(90), 0, 0))], "PouchSeal")
    c["pseal"] = seal
    sealer = twp.person("Courier2", 1.0, 41, "male_casualsuit02", "short03", hv=0.3, cval=0.55, hue=0.6, sat=0.2)
    c["courier"] = sealer
    ph.model("metal_office_desk", loc=(2.6, -1.8, 0), rot_z=0.0, scale=0.8)
    MC.terminal("VTerm", (2.6, -1.8, 0.632), 0.0)
    ph.model("SchoolChair_01", loc=(2.6, -2.4, 0), rot_z=0.0)
    if not dark:
        for x in (-2.0, 1.5):
            ph.model("mounted_fluorescent_lights", loc=(x, 0.5, 2.8), rot_z=math.radians(90))
            l = area_light((x, 0.5, 2.72), (0, 0, 0), 0.9, 45, (0.88, 0.95, 1.0)); l.visible_camera = False
    else:
        corr = area_light((-3.0, 1.9, 2.6), (0, 0, 0), 1.2, 25, (0.55, 0.65, 0.9)); point_at(corr, (-2.6, -0.4, 0.8)); corr.visible_camera = False
    # the Marine with a flashlight (dark variant)
    m = twp.person("Marine", 1.0, 24, "male_casualsuit06", "short01", hv=0.2, cval=0.35, hue=0.12, sat=0.35)
    c["marine"] = m
    fl, _ = ph.model("signal_flashlight")
    c["torch"] = fl
    sp = bpy.data.lights.new("Torch", 'SPOT'); sp.energy = 900 if dark else 0; sp.spot_size = math.radians(24); sp.spot_blend = 0.35
    sp.color = (1.0, 0.92, 0.8); sp.shadow_soft_size = 0.01
    so = bpy.data.objects.new("Torch", sp); bpy.context.collection.objects.link(so); c["beam"] = so
    if dark:
        haze((0, 0, 1.4), (8, 6, 2.8), density=0.05, color=(0.8, 0.85, 0.9), anis=0.6)
    twp.hide(twp.person_objs(m) + [fl] + list(fl.children_recursive), not dark)
    animate(c, 0.0, "sweep" if dark else "push")
    return c


def animate(c, sec, shot="push"):
    from human import reach, fingers_curl
    cou = c["courier"]
    twp.hide(twp.person_objs(cou), shot != "pouch")
    if shot == "pouch":
        twp.stand(cou, (DESK2.x - 0.4, DESK2.y - 0.75, 0), math.pi)
        top = DESK2 + Vector((-0.45, -0.05, 1.08))
        crimp = max(0.0, math.sin(math.pi * min(1.0, max(0.0, (sec - 2.6) / 0.6))))
        draw = ease(min(1.0, sec / 2.0))
        c["pseal"].location = top + Vector((0, -0.04, -0.02 - 0.06 * draw))
        reach(cou, "R", top + Vector((0.08, -0.1, 0.05 - 0.05 * draw - 0.01 * crimp)), Vector((-0.6, -0.3, -0.7)), Vector((0, 1, -0.2)))
        reach(cou, "L", top + Vector((-0.1, -0.1, 0.08 + 0.1 * (1 - draw))), Vector((0.6, -0.3, -0.7)), Vector((0, 1, 0.3)))
        fingers_curl(cou, 50 + 20 * crimp, thumb=30)
        cou.rot("head", (1, 0, 0), 15)
    from human import reach, fingers_curl
    for k, p in enumerate(c["tty"]):
        MC.run_teletype(p, sec + k * 0.7)
    if c["variant"] == "dark":
        m = c["marine"]
        twp.stand(m, (-3.1, -0.6, 0.0), math.radians(-115))                 # just inside the door, facing into the room
        a = math.radians(-60) + math.radians(95) * ease(sec / DUR["sweep"])
        aim = Vector((-3.1 + 4.5 * math.sin(a), -0.6 + 4.5 * math.cos(a), 0.9))
        sh = m.bone_head("upperarm01.R")
        hand_p = sh + (aim - sh).normalized() * 0.55 + Vector((0, 0, -0.05))
        reach(m, "R", hand_p, Vector((0.6, -0.4, -0.6)), aim - sh)
        fingers_curl(m, 60, thumb=30)
        d = (aim - hand_p).normalized()
        fl = c["torch"]; fl.location = hand_p + d * 0.05
        fl.rotation_mode = 'QUATERNION'; fl.rotation_quaternion = d.to_track_quat('Z', 'Y')
        b = c["beam"]; b.location = hand_p + d * 0.2
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
        m.rot("head", (0, 0, 1), 10 * math.sin(sec * 0.4))
    bpy.context.view_layer.update()


MOVES = {
    "tape": dict(kind="anim", dof=1.2, anim=lambda c, t: animate(c, t * DUR["tape"], "tape"),
                 cam=lambda c, t: (TAPE_AT + Vector((0.55, -0.35, 0.32)).lerp(Vector((0.42, -0.28, 0.26)), ease(t)), TAPE_AT + Vector((-0.05, 0, 0.0)), 45),
                 focus=lambda c, t: TAPE_AT + Vector((0.05, 0, 0))),
    "pouch": dict(kind="anim", dof=2.0, anim=lambda c, t: animate(c, t * DUR["pouch"], "pouch"),
                  cam=lambda c, t: (DESK2 + Vector((-2.4, 0.9, 1.6)).lerp(Vector((-2.2, 0.8, 1.55)), ease(t)), DESK2 + Vector((-0.4, -0.3, 1.0)), 32),
                  focus=lambda c, t: DESK2 + Vector((-0.45, -0.05, 1.0))),
    "push": dict(kind="anim", dof=2.0, anim=lambda c, t: animate(c, t * DUR["push"], "push"),
                 cam=lambda c, t: (Vector((-2.0, -0.9, 1.25)).lerp(Vector((-1.45, -0.35, 1.18)), ease(t)), Vector((-0.6, 0.8, 1.0)), 35),
                 focus=lambda c, t: Vector((-1.0, 0.6, 1.1))),
    "sweep": dict(kind="anim", dof=None, anim=lambda c, t: animate(c, t * DUR["sweep"], "sweep"),
                  cam=lambda c, t: (Vector((2.2, -2.6, 1.6)).lerp(Vector((1.9, -2.45, 1.6)), ease(t)), Vector((-1.6, 0.4, 1.1)), 28)),
}
