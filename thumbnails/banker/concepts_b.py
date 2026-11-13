"""Banker thumbnail B: the office phone, low and close, the handset tilting up off its cradle (pivoting on its
mouthpiece end, as if just lifted). Dark office, haze, one hard beam; the faint stain on the earpiece is the lime accent.
Built from the film's own set (claude/phone-banker: projects/phone-banker/scenes/sc_bankoffice.py)."""
import math
import bpy
from mathutils import Vector, Matrix
from common import area_light, point_at


def _spot(name, loc, tgt, energy, color, deg=30, blend=0.5, soft=0.05):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color
    l.spot_size = math.radians(deg); l.spot_blend = blend; l.shadow_soft_size = soft
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt)
    return o


def _hs(c):
    from sc_bankoffice import handset_home
    return handset_home(c)


def lift(c, deg=13):
    import sc_bankoffice as b
    M = _hs(c)
    piv = M @ Vector((0, -b.HS_L / 2 + 0.01, -0.01))                 # mouthpiece end stays on the cradle
    R = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(deg), 4, M.to_3x3() @ Vector((1, 0, 0))) @ Matrix.Translation(-piv)
    b.place_handset(c, R @ M)


def setup(c):
    from kit import haze
    lift(c)
    for o in bpy.data.objects:
        if o.name.startswith(("Page", "binder")) or (o.parent and o.parent.name.startswith("binder")):
            o.hide_render = True
    for o in bpy.data.objects:                                          # the film's daylight down to a dim room
        if o.type == 'LIGHT':
            o.data.energy *= 0.12
    w = bpy.context.scene.world
    if w and w.node_tree:
        for n in w.node_tree.nodes:
            if n.type == 'BACKGROUND':
                n.inputs['Strength'].default_value *= 0.1
    bpy.context.scene.view_settings.exposure = -1.0
    p = _hs(c).translation
    haze(p + Vector((0, 0.5, 0.6)), (5.0, 5.0, 2.4), density=0.02, color=(0.95, 0.9, 0.85), anis=0.55)
    _spot("TopBeam", p + Vector((-0.25, 0.35, 1.9)), p, 900, (1.0, 0.93, 0.84), 14, 0.35, 0.03)
    k = area_light(p + Vector((-0.7, -0.7, 0.35)), (0, 0, 0), 0.6, 18, (0.85, 0.9, 1.0)); point_at(k, p)      # faint cool fill
    rim = area_light(p + Vector((0.5, 0.8, 0.3)), (0, 0, 0), 0.4, 25, (1.0, 0.8, 0.6)); point_at(rim, p)       # warm rim
    ear = _hs(c) @ Vector((0, 0.07, 0.03))
    _spot("StainLime", ear + Vector((0.12, -0.12, 0.18)), ear, 30, (0.88, 0.97, 0.0), 6, 0.6, 0.01)            # the one accent


def cam(c):
    p = _hs(c).translation
    return (p + Vector((-0.42, -0.82, 0.2)), p + Vector((0.06, 0.05, 0.06)), 45)


def phone_parts(c):
    root = c["phone"]
    return [o for o in [root] + list(root.children_recursive) + [c["handset"], c["phone_base"], c["cord"]] if o.type == 'MESH']


CONCEPTS = {
    "phone_b": dict(scene="bankoffice", variant="empty", move="handset", t=0.0, cam=cam, shift=(0.0, -0.05),
                    focus=lambda c: _hs(c).translation, fstop=2.8, setup=setup, exposure=0.4, mask=phone_parts),
}
