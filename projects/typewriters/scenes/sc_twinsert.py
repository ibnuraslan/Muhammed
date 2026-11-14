"""HERO INSERTS ON BLACK: one object at a time on a dark stage under a single hard top light (the evidence look).

Intro 5A  copier   "Copiers. Computers." - the camera slides along a dark stage from a copier to a terminal, each in its
                   own pool of light, cut on the words
Intro 5B  cipher   "Encryption machines." - a cipher machine alone in the light, its lamps blinking, a slow push in
Ch1 6B    staple   "The staples and seals carry microscopic markings" - macro: a staple in the burlap seam under a
                   magnifier; the lens slides over it and the engraved marks swim into view
"""
import math
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import machines as MC

DUR = {"copier": 3.2, "cipher": 3.0, "staple": 5.0}
VARIANT_FOR = {"staple": "macro"}
EXPOSURE = 0.0


def stage(radius=2.2):
    """Black world, a dark satin floor that falls off into black, one hard area light from above."""
    w = bpy.context.scene.world or bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes.get("Background"); bg.inputs['Color'].default_value = (0, 0, 0, 1); bg.inputs['Strength'].default_value = 0.0
    m = bpy.data.materials.new("StageFloor"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1 / radius, 1 / radius, 1)
    L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], gr.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.004, 0.004, 0.004, 1); cr.color_ramp.elements[1].color = (0.06, 0.058, 0.055, 1)
    L.new(gr.outputs['Fac'], cr.inputs[0]); L.new(cr.outputs[0], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.35
    fl = box("Stage", (0, 0, -0.01), (12, 12, 0.02), m)
    return fl


def spot(loc, target, energy, size=0.6, color=(1.0, 0.94, 0.86)):
    l = area_light(loc, (0, 0, 0), size, energy, color); point_at(l, target); l.visible_camera = False
    return l


def build(variant=None):
    c = {"variant": variant}
    stage()
    if variant == "macro":
        # a burlap seam, a row of staples, a magnifier sliding over one of them
        hes = MC.burlap_material()
        box("Burlap", (0, 0, 0.0), (0.4, 0.3, 0.01), hes)
        steel = pbr("StapleSteel", (0.62, 0.62, 0.64), 0.28, 1.0)
        # the engraved code: fine bumps along the staple crown (a coded line of ticks)
        eng = bpy.data.materials.new("StapleEngraved"); eng.use_nodes = True
        N = eng.node_tree.nodes; L = eng.node_tree.links; pb = N["Principled BSDF"]
        pb.inputs['Base Color'].default_value = (0.62, 0.62, 0.64, 1); pb.inputs['Metallic'].default_value = 1.0; pb.inputs['Roughness'].default_value = 0.25
        tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
        wv = N.new("ShaderNodeTexWave"); wv.inputs['Scale'].default_value = 4.0; wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
        L.new(tc.outputs['Object'], wv.inputs['Vector'])
        mk = N.new("ShaderNodeTexWhiteNoise"); mk.noise_dimensions = '1D'
        fl_ = N.new("ShaderNodeMath"); fl_.operation = 'FLOOR'; mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 900.0
        L.new(sep.outputs[0], mul.inputs[0]); L.new(mul.outputs[0], fl_.inputs[0]); L.new(fl_.outputs[0], mk.inputs['W'])
        gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.45; L.new(mk.outputs['Value'], gt.inputs[0])
        bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.8; bm.inputs['Distance'].default_value = 0.0004
        L.new(gt.outputs[0], bm.inputs['Height']); L.new(bm.outputs[0], pb.inputs['Normal'])
        c["staples"] = []
        for k in range(5):
            x = -0.12 + k * 0.06
            crown = box(f"StapleCrown{k}", (x, 0.0, 0.0065), (0.012, 0.0014, 0.0008), eng if k == 2 else steel)
            for dx in (-0.006, 0.006):
                box(f"StapleLeg{k}", (x + dx, 0.0, 0.004), (0.0008, 0.0014, 0.005), steel)
            c["staples"].append(crown)
        # magnifier: a glass disc in a dark ring, held just above the seam
        lens = bpy.data.materials.new("Lens"); lens.use_nodes = True
        lp = lens.node_tree.nodes["Principled BSDF"]; lp.inputs['Transmission Weight'].default_value = 1.0; lp.inputs['Roughness'].default_value = 0.0
        lp.inputs['IOR'].default_value = 1.52
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0); g = bpy.context.active_object; g.name = "MagLens"
        g.scale = (0.03, 0.03, 0.006); bpy.ops.object.transform_apply(scale=True); g.data.materials.append(lens)
        ring = cyl("MagRing", (0, 0, 0), 0.032, 0.006, pbr("MagRingM", (0.03, 0.03, 0.03), 0.4, 0.5), verts=48)
        handle = box("MagHandle", (0.0, -0.075, 0.0), (0.012, 0.09, 0.006), pbr("MagHandleM", (0.08, 0.05, 0.03), 0.5))
        rig = bpy.data.objects.new("MagRig", None); bpy.context.collection.objects.link(rig)
        for o in (g, ring, handle):
            o.parent = rig
        c["mag"] = rig
        spot((0.05, -0.08, 0.5), (0, 0, 0), 60, size=0.3)
        spot((-0.3, 0.25, 0.2), (0, 0, 0), 6, size=0.4, color=(0.8, 0.85, 1.0))
    else:
        # the stage: copier, terminal and cipher machine, each in its own pool of light along a line
        c["copier"] = MC.copier("InsCopier", (-1.6, 0.0, 0.0), 0.35)
        c["term"] = MC.terminal("InsTerm", (0.0, 0.0, 0.0), -0.25)[0]
        r, lamps = MC.cipher("InsCipher", (1.6, 0.0, 0.0), 0.3, height=0.45)
        c["cipher"] = r
        MC.lamp_blink()
        for x in (-1.6, 0.0, 1.6):
            spot((x + 0.2, -0.25, 2.4), (x, 0.0, 0.4), 260, size=0.7)
        spot((0.0, 2.5, 1.2), (0, 0, 0.5), 40, size=2.0, color=(0.75, 0.82, 1.0))       # a faint rim from behind
    animate(c, 0.0, "copier" if variant != "macro" else "staple")
    return c


def animate(c, sec, shot):
    if shot == "staple":
        k = ease(min(1.0, max(0.0, (sec - 0.5) / 3.2)))
        c["mag"].location = Vector((0.02 - 0.02 * k, -0.035 + 0.035 * k, 0.018 + 0.004 * math.sin(sec * 1.3)))
        c["mag"].rotation_euler = (0.04 * math.sin(sec * 0.9), 0.03 * math.sin(sec * 1.1), 0.1 * (1 - k))
    bpy.context.scene.frame_set(int(sec * 24) + 1)                                # the cipher lamps blink in stills too
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_copier(c, t):
    e = ease(t)                                  # slides along the stage from the copier to the terminal
    x = -1.55 + 1.55 * e
    return (Vector((x + 0.15, -1.9, 1.05)), Vector((x, 0.0, 0.55)), 40)


def cam_cipher(c, t):
    e = ease(t)
    return (Vector((1.6 + 0.35, -1.4 + 0.35 * e, 0.95 - 0.1 * e)), Vector((1.6, 0.0, 0.32)), 45)


def cam_staple(c, t):
    e = ease(t)
    return (Vector((0.0, -0.085 + 0.012 * e, 0.07 - 0.012 * e)), Vector((0.0, 0.0, 0.006)), 85)


MOVES = {
    "copier": dict(kind="anim", dof=4.0, cam=cam_copier, focus=lambda c, t: Vector((-1.55 + 1.55 * ease(t), 0.0, 0.55)), anim=anim("copier")),
    "cipher": dict(kind="anim", dof=4.0, cam=cam_cipher, focus=lambda c, t: Vector((1.6, 0.0, 0.32)), anim=anim("cipher")),
    "staple": dict(kind="anim", dof=8.0, cam=cam_staple, focus=lambda c, t: Vector((0.0, 0.0, 0.0065)), anim=anim("staple")),
}
for k in MOVES:
    MOVES[k]["dur"] = DUR[k]
