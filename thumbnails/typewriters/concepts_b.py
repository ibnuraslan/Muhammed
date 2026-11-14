"""Typewriters thumbnail B: one cream golf-ball typewriter on the night desk, its lower case X-ray clear, the hidden
bar inside glowing Seldom lime. Dark office, haze, one hard beam. Built from the film's own set
(claude/typewriters: projects/typewriters/scenes/sc_twoffice.py, typewriter.py)."""
import math
import bpy
from mathutils import Vector
from common import area_light, point_at

CREAM = (0.62, 0.58, 0.50)
LIMEC = (0.88, 0.97, 0.0)


def _spot(name, loc, tgt, energy, color, deg=30, blend=0.5, soft=0.05):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color
    l.spot_size = math.radians(deg); l.spot_blend = blend; l.shadow_soft_size = soft
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt)
    return o


def _w(c, p):
    import typewriter as T
    return T.world(c["tw"], p)


def _emit(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N):
        if n.type != 'OUTPUT_MATERIAL':
            N.remove(n)
    e = N.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    L.new(e.outputs[0], next(n for n in N if n.type == 'OUTPUT_MATERIAL').inputs['Surface'])
    return m


def swap_machine(c):
    """Replace the film's desk machine with a cream, bugged one in the same spot."""
    import typewriter as T, sc_twoffice as S
    old = c["tw"]["root"]
    loc, rz = old.location.copy(), old.rotation_euler.z
    for o in [old] + list(old.children_recursive):
        o.hide_render = True; o.hide_viewport = True
    tw = T.make("TWX", loc=tuple(loc), rot_z=rz, color=CREAM, bugged=True, text=S.TEXT_P, dpi=400, seed=0)
    c["tw"] = tw
    for o in tw["root"].children_recursive:          # no sheet: it would cover the title
        if any(k in o.name for k in ("Paper", "Page", "Bail")) or o is tw.get("paper"):
            o.hide_render = True
    return tw


def setup(c, xray=True):
    from kit import haze
    import typewriter as T
    tw = swap_machine(c)
    if not xray:
        return _rest(c, tw, xray)
    # X-ray: the lower case and side towers go mostly clear, so the bar inside shows; keys and platen stay solid
    lower = [o for o in tw["shell"] if o.name.startswith(("TWX_Lower", "TWX_Side"))]
    T.xray_shell(tw, expr="0.93", objs=lower, tint=LIMEC)
    glow = _emit("BugGlow", LIMEC, 10.0); hot = _emit("BugHot", (0.95, 1.0, 0.55), 20.0)
    for o in tw["bug_parts"]:
        o.data = o.data.copy(); o.data.materials.clear(); o.data.materials.append(hot if "Chip" in o.name else glow)
    for o in (tw["bar"], tw["bar_lid"]):
        o.data = o.data.copy(); o.data.materials.clear(); o.data.materials.append(_emit("BarGlow", LIMEC, 5.0))
    _rest(c, tw, xray)


def _rest(c, tw, xray):
    from kit import haze
    import typewriter as T
    bl = bpy.data.lights.new("BugLight", 'AREA'); bl.energy = 10; bl.size = 0.3; bl.shape = 'RECTANGLE'; bl.size_y = 0.03
    bl.color = LIMEC; bo = bpy.data.objects.new("BugLight", bl); bpy.context.collection.objects.link(bo)
    bo.location = _w(c, (0, T.BAR_Y, T.BAR_Z + 0.03)) if xray else _w(c, (0, -0.1, 0.004))
    if not xray:                                     # solid machine: the glow leaks out from under it onto the desk
        bl.energy = 25; bl.size = 0.42; bl.size_y = 0.3; bo.rotation_euler = (0, 0, 0); bo.rotation_euler = c["tw"]["root"].rotation_euler
    p0 = _w(c, (0, 0, 0))
    for o in bpy.data.objects:                       # chairs and clutter between the camera and the machine
        n = o.name.lower()
        if o.type == 'MESH' and ("chair" in n or "stationery" in n or "notepad" in n or "pen" in n.split("_")[0]):
            if (o.matrix_world.translation - p0).length < 3.5:
                o.hide_render = True
    bpy.context.scene.view_settings.exposure = -1.2
    # night room down, one hard beam, haze
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and not o.name.startswith("BugLight"):
            o.data.energy *= 0.15
    w = bpy.context.scene.world
    if w and w.node_tree:
        for n in w.node_tree.nodes:
            if n.type == 'BACKGROUND':
                n.inputs['Strength'].default_value *= 0.05
    p = _w(c, (0, 0, 0.1))
    haze(p + Vector((0, 0, 0.6)), (5.0, 5.0, 2.4), density=0.02, color=(0.95, 0.9, 0.85), anis=0.55)
    _spot("TopBeam", p + Vector((0.2, 0.3, 1.9)), p, 700, (1.0, 0.93, 0.84), 16, 0.35, 0.03)
    k = area_light(_w(c, (-0.7, -0.8, 0.4)), (0, 0, 0), 0.6, 10, (0.85, 0.9, 1.0)); point_at(k, p)
    rim = area_light(_w(c, (0.6, 0.7, 0.35)), (0, 0, 0), 0.4, 25, (1.0, 0.8, 0.6)); point_at(rim, p)


def cam(c):
    return (_w(c, (0.38, -0.98, 0.36)), _w(c, (0.0, -0.02, 0.07)), 40)


def machine(c):
    r = c["tw"]["root"]
    return [o for o in r.children_recursive if o.type in ('MESH', 'CURVE', 'FONT') and not o.hide_render]


CONCEPTS = {
    "tw_solid": dict(scene="twoffice", variant="night", cam=cam, shift=(0.0, 0.15), focus=lambda c: _w(c, (0, -0.06, 0.08)),
                     fstop=2.8, setup=lambda c: setup(c, xray=False), exposure=-1.2, mask=machine),
    "tw_b": dict(scene="twoffice", variant="night", cam=cam, shift=(0.0, 0.15), focus=lambda c: _w(c, (0, -0.06, 0.08)),
                 fstop=2.8, setup=setup, exposure=-1.2, mask=machine),
}
