"""Banker thumbnail concepts, built from the film's own sets (claude/phone-banker: projects/phone-banker/scenes)."""
import math
import bpy
from mathutils import Vector
from common import area_light, point_at


def _spot(name, loc, tgt, energy, color, size_deg=40, blend=0.6, soft=0.05):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color
    l.spot_size = math.radians(size_deg); l.spot_blend = blend; l.shadow_soft_size = soft
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt)
    return o


def _dim_all(k_light=0.04, k_world=0.03):
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            o.data.energy *= k_light
    w = bpy.context.scene.world
    if w and w.node_tree:
        for n in w.node_tree.nodes:
            if n.type == 'BACKGROUND':
                n.inputs['Strength'].default_value *= k_world
    for n in ("Sun", ):
        pass


def _hs(c):
    from sc_bankoffice import handset_home
    return handset_home(c).translation.copy()


# --- A. DARK EVIDENCE: the phone alone in the dark office, one hard raking light finds the stain ---------------------
def phone_setup(c):
    _dim_all()
    h = _hs(c)
    _spot("Key", h + Vector((-0.9, -0.35, 0.55)), h, 300, (0.95, 0.97, 1.0), 16, 0.35, 0.04)
    _spot("RedRim", h + Vector((0.5, 1.0, 0.45)), h + Vector((0, 0, 0.06)), 45, (1.0, 0.07, 0.04), 10, 0.4, 0.05)


def phone_cam(c):
    h = _hs(c)
    return (h + Vector((-0.40, -0.80, 0.24)), h + Vector((0.02, 0.0, -0.01)), 55)


# --- B. MINIMAL: the padded case of sealed ampoules, one empty slot, from above -----------------------------------------
def amp_setup(c):
    _dim_all(0.05, 0.05)
    from sc_forlab import CASE
    _spot("Key", CASE + Vector((-0.5, -0.3, 1.0)), CASE, 45, (1.0, 0.96, 0.9), 16, 0.5, 0.05)
    _spot("RedRim", CASE + Vector((0.7, 0.5, 0.2)), CASE, 30, (1.0, 0.07, 0.04), 25, 0.5, 0.1)


def amp_cam(c):
    from sc_forlab import CASE
    return (CASE + Vector((-0.2, -0.62, 0.75)), CASE + Vector((0.0, 0.0, 0.0)), 50)


# --- C. CINEMATIC: years later, dust sheets over everything; only the phone left uncovered -----------------------------
def dust_setup(c):
    _dim_all(0.25, 0.25)
    h = _hs(c)
    _spot("Shaft", h + Vector((-1.2, -0.6, 1.8)), h, 260, (0.92, 0.95, 1.0), 9, 0.4, 0.03)


def dust_cam(c):
    import sc_bankoffice as b
    h = _hs(c)
    return (Vector((b.ROOM_X - 0.45, b.DOOR_Y + 0.1, 1.5)), h + Vector((0.0, 0.0, -0.02)), 60)


CONCEPTS = {
    "phone": dict(scene="bankoffice", variant="empty", move="handset", t=0.0, cam=phone_cam, shift=(-0.14, 0.02),
                  focus=lambda c: _hs(c), fstop=2.8, setup=phone_setup, exposure=0.6),
    "ampoules": dict(scene="forlab", variant="evid", move="ampoules", t=0.5, cam=amp_cam, shift=(0.12, 0.0),
                     focus=lambda c: __import__("sc_forlab").CASE, fstop=3.5, setup=amp_setup, exposure=0.6),
    "dust": dict(scene="bankoffice", variant="empty", move="handset", t=0.0, cam=dust_cam, shift=(0.12, 0.0),
                 focus=lambda c: _hs(c), fstop=2.2, setup=dust_setup, exposure=0.8),
}
