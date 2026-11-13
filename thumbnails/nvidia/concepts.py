"""Nvidia thumbnail concepts, built from the film's own sets (nvidia_doc/scenes)."""
import math
import bpy
from mathutils import Vector
from common import area_light, point_at


def _spot(name, loc, tgt, energy, color, size_deg=40, blend=0.6, soft=0.05):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color
    l.spot_size = math.radians(size_deg); l.spot_blend = blend; l.shadow_soft_size = soft
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt)
    return o


# --- 1. DARK EVIDENCE: the accelerator package alone on black, a red raking key, a cold rim ---------------------
def chip_setup(c):
    k = c["key"]; k.data.energy = 0.0
    _spot("RedKey", (-0.11, -0.07, 0.04), (0.0, 0.0, 0.002), 22.0, (1.0, 0.06, 0.04), 26, 0.8, 0.01)
    r = c["rim"]; r.data.color = (0.75, 0.85, 1.0); r.data.energy = 0.5
    r.location = (0.03, 0.12, 0.05); point_at(r, (0, 0, 0.002))
    # a thin top strip so the die's thin-film catches one clean highlight
    t = area_light((0.02, -0.03, 0.12), (0, 0, 0), 0.02, 0.3, (1.0, 0.95, 0.9)); point_at(t, (-0.004, 0, 0.002))
    t.data.shape = 'RECTANGLE'; t.data.size = 0.15; t.data.size_y = 0.006
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.color[0] > 0.9 and o.data.color[2] < 0.8 and o.data.color[1] > 0.5:
            o.data.energy = 0.0                                   # the warm fill would grey the ground
        if o.name.startswith("Ground"):
            pb = o.data.materials[0].node_tree.nodes["Principled BSDF"]
            pb.inputs['Base Color'].default_value = (0.0006, 0.0006, 0.0007, 1)
            pb.inputs['Specular IOR Level'].default_value = 0.35; pb.inputs['Roughness'].default_value = 0.3


# --- 2. MINIMALIST EVIDENCE: the redacted memo in one pool of lamplight -------------------------------------------
def memo_setup(c):
    c["lamp"].energy = 120
    rim = area_light((0.6, 0.8, 0.9), (0, 0, 0), 0.4, 1.2, (1.0, 0.1, 0.06)); point_at(rim, (-0.04, 0.0, 0.75))


# --- 3. INVESTIGATIVE / CINEMATIC: the empty leather chair at the head of the board table ----------------------------
def chair_setup(c):
    import ph
    bpy.data.objects["Chair"].hide_render = True if "Chair" in bpy.data.objects else None
    for o in list(bpy.data.objects):
        if o.name.startswith("Chair"):
            o.hide_render = True                                  # an empty table: only the head chair remains
    for m in bpy.data.materials:
        if m.name.startswith("Windows") and m.node_tree:
            p = m.node_tree.nodes.get("Principled BSDF")
            for l in m.node_tree.links:
                if l.to_socket == p.inputs['Emission Strength']:
                    l.from_node.inputs[1].default_value *= 0.3
    root, ms = ph.model("mid_century_lounge_chair", loc=(0, 3.6, 0), rot_z=math.radians(-28))
    # one cold top light on the chair, a thin red rim from behind
    _spot("ChairTop", (0.5, 2.9, 2.6), (0, 3.6, 0.6), 600, (0.8, 0.88, 1.0), 34, 0.7, 0.2)
    rim = _spot("RedRim", (-0.9, 4.7, 2.0), (0, 3.6, 0.9), 50, (1.0, 0.08, 0.05), 22, 0.5, 0.1)
    bpy.data.objects["Over"].data.energy = 25
    for n in ("Folder", "Paper"):
        bpy.data.objects[n].hide_render = True


CONCEPTS = {
    "chip": dict(scene="chip_macro", exposure=0.3,
                 cam=((0.105, -0.115, 0.075), (0.0, 0.0, 0.002), 66), shift=(0.0, -0.1),
                 focus=(0.0, -0.004, 0.0029), fstop=22.0, setup=chip_setup),
    "memo": dict(scene="memo_desk", exposure=0.0,
                 cam=((0.15, -0.5, 1.02), (-0.06, 0.0, 0.747), 40), shift=(-0.17, 0.0),
                 focus=(-0.04, -0.06, 0.747), fstop=2.8, setup=memo_setup),
    "chair": dict(scene="boardroom", exposure=0.0,
                  cam=((0.3, -0.6, 1.1), (0.0, 3.6, 0.72), 70), shift=(-0.1, 0.0),
                  focus=(0, 3.55, 0.75), fstop=2.0, setup=chair_setup),
}

CONCEPTS["targeted"] = dict(scene="thumb_targeted", exposure=0.0,
                            cam=((0, -2.8, 1.62), (0, 1.0, 1.22), 36), focus=(0, 0.45, 1.2), fstop=4.0,
                            mask=lambda c: c["people"])

CONCEPTS["targeted_head"] = dict(CONCEPTS["targeted"], cam=lambda c: (c["head"] + Vector((0.25, -0.75, 0.15)), c["head"], 50), fstop=None, mask=None)
