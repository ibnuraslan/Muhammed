"""Radioactive Scrap thumbnails, built from the film's own Ikitelli yard (claude/radioactive-scrap: sc_ikitelli.py).
  rs_cut   the peeled container alone on a transparent background, studio-lit (for the hazard poster, style A)
  rs_yard  the same container in the night yard, low and close (for the detector view, style C)"""
import math
import bpy
from mathutils import Vector
from common import area_light, point_at


def _peel(c, deg=58):
    import sc_ikitelli as S
    S.set_shell(c["hinge"], deg)
    t = c["k1"]["trefoil"]; t.scale = (1.25, 1.25, 1.25); t.location.y -= 0.012                  # the mark, big enough to read on a phone
    bpy.context.view_layer.update()


def _c1():
    import sc_ikitelli as S
    return S.C1


def parts(c):
    root = c["cont1"]
    return [o for o in [root] + list(root.children_recursive) if o.type == 'MESH']


def setup_cut(c):
    _peel(c)
    keep = set(parts(c))
    for o in bpy.data.objects:
        if o.type in ('MESH', 'CURVE') and o not in keep:
            o.hide_render = True
        if o.type == 'LIGHT':
            o.hide_render = True
    w = bpy.context.scene.world
    if w and w.node_tree:
        for n in w.node_tree.nodes:
            if n.type == 'BACKGROUND':
                n.inputs['Strength'].default_value = 0.25
    s = bpy.context.scene; s.render.film_transparent = True; s.render.image_settings.color_mode = 'RGBA'
    s.view_settings.exposure = 0.0
    p = _c1() + Vector((0, 0, 0.55))
    k = area_light(p + Vector((-1.6, -1.4, 1.4)), (0, 0, 0), 1.2, 80, (1.0, 0.96, 0.9)); point_at(k, p)
    f = area_light(p + Vector((-1.8, 1.4, 0.3)), (0, 0, 0), 1.5, 18, (0.85, 0.9, 1.0)); point_at(f, p)
    r = area_light(p + Vector((1.4, 0.4, 1.2)), (0, 0, 0), 0.8, 70, (1.0, 0.85, 0.6)); point_at(r, p)


def setup_yard(c):
    _peel(c)
    from kit import haze
    p = _c1() + Vector((0, 0, 0.5))
    s = bpy.context.scene; s.view_settings.exposure = -0.3
    haze(p + Vector((0, 0, 1.0)), (14, 14, 4), density=0.012, color=(0.9, 0.95, 1.0), anis=0.4)
    from common import area_light as al
    top = al(p + Vector((-0.4, -0.3, 2.6)), (0, 0, 0), 0.5, 400, (1.0, 0.95, 0.85)); point_at(top, p)
    w = bpy.context.scene.world                             # proper night: sky and sun way down
    if w and w.node_tree:
        for n in w.node_tree.nodes:
            if n.type == 'BACKGROUND':
                n.inputs['Strength'].default_value *= 0.25
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'SUN':
            o.data.energy *= 0.25
    import sc_ikitelli as S                                 # the torch gas bottles beside the containers: a little light on them
    g = Vector((S.C2.x - 1.84, S.C2.y - 1.4, 0.8))
    gl = al(g + Vector((-1.2, -0.6, 1.0)), (0, 0, 0), 0.6, 120, (1.0, 0.95, 0.9)); point_at(gl, g)


def cam_cut(c):
    p = _c1()
    return (p + Vector((-3.3, -1.5, 1.35)), p + Vector((0, 0, 0.5)), 45)


def cam_yard(c):
    p = _c1()
    return (p + Vector((-3.6, -1.8, 1.35)), p + Vector((0.3, 1.25, 0.62)), 27)


CONCEPTS = {
    "rs_cut": dict(scene="ikitelli", variant="night", cam=cam_cut, setup=setup_cut, exposure=0.0),
    "rs_yard": dict(scene="ikitelli", variant="night", cam=cam_yard, shift=(0.0, -0.05), setup=setup_yard, exposure=-0.3, mask=parts),
}
