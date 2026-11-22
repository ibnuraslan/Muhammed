"""Hand props for the Antwerp shots, modelled to real size. Each returns its root object (origin = grip point)."""
import math
import bpy
from mathutils import Vector, Matrix
import ship as S
from sets import flat, emit, gold, brushed, box, paper_mat


def _root(name, parts, loc=(0, 0, 0), rot=(0, 0, 0)):
    r = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(r)
    for o in parts:
        o.parent = r
    r.location = loc; r.rotation_euler = rot
    return r


def vault_key_part(name, length=0.24, bit=True, mat=None):
    """One half of the vault key: a long round shank (0.24 m), an oval bow, and (bit=True) the stepped bit;
    the other half is the shank extension that screws on. Origin at the bow, shank along -z (hangs from a hook)."""
    m = mat or gold(name + "_brass", (0.66, 0.5, 0.26))
    parts = [S.cyl(name + "_shank", (0, 0, -0.03), (0, 0, -length), 0.006, mat=m, verts=16)]
    bpy.ops.mesh.primitive_torus_add(major_radius=0.022, minor_radius=0.005, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.active_object; t.name = name + "_bow"; t.scale = (1.0, 1.0, 1.3); t.data.materials.append(m); parts.append(t)
    if bit:
        for k, (dz, w) in enumerate(((0.0, 0.03), (0.012, 0.022), (0.024, 0.034), (0.036, 0.018))):
            parts.append(box(name + "_bit", (w / 2 + 0.004, 0, -length + 0.012 + dz), (w, 0.004, 0.011), m))
    return _root(name, parts)


def handset(name="handset"):
    m = flat(name + "_plastic", (0.06, 0.06, 0.065), 0.4)
    parts = [box(name + "_grip", (0, 0, 0), (0.045, 0.03, 0.2), m, bevel=0.012),
             box(name + "_ear", (0, -0.012, 0.09), (0.055, 0.035, 0.05), m, bevel=0.015),
             box(name + "_mouth", (0, -0.012, -0.09), (0.055, 0.035, 0.05), m, bevel=0.015)]
    return _root(name, parts)


def badge(name="badge"):
    c = flat(name + "_card", (0.75, 0.72, 0.62), 0.35)
    parts = [box(name + "_card", (0, 0, 0), (0.054, 0.0008, 0.0856), c, bevel=0.0003),
             box(name + "_stripe", (0, -0.0006, 0.02), (0.054, 0.0004, 0.015), flat(name + "_blue", (0.05, 0.12, 0.35), 0.4))]
    return _root(name, parts)


def torch(name="torch", on=True, energy=150.0):
    """Police torch: black aluminium body, lit lens, a spot light along local -y. Origin at the grip."""
    m = flat(name + "_body", (0.02, 0.02, 0.022), 0.35, metal=0.6)
    parts = [S.cyl(name + "_body", (0, 0.06, 0), (0, -0.14, 0), 0.016, mat=m, verts=16),
             S.cyl(name + "_head", (0, -0.14, 0), (0, -0.2, 0), 0.016, 0.026, mat=m, verts=16)]
    if on:
        parts.append(S.cyl(name + "_lens", (0, -0.2, 0), (0, -0.203, 0), 0.024, mat=emit(name + "_lens", (1.0, 0.92, 0.8), 60), verts=16))
    r = _root(name, parts)
    if on:
        l = bpy.data.lights.new(name + "_beam", 'SPOT'); l.energy = energy; l.spot_size = math.radians(28); l.spot_blend = 0.5
        l.color = (1.0, 0.93, 0.82); l.shadow_soft_size = 0.02
        o = bpy.data.objects.new(name + "_beam", l); bpy.context.scene.collection.objects.link(o)
        o.parent = r; o.location = (0, -0.21, 0); o.rotation_euler = (math.radians(90), 0, 0)
    return r


def alarm_panel(name="alarm_panel"):
    """An alarm control panel opened up: grey steel box with the lid off, circuit board, terminal strips, wires."""
    st = flat(name + "_steel", (0.5, 0.5, 0.48), 0.4, metal=0.3)
    pcb = flat(name + "_pcb", (0.02, 0.18, 0.06), 0.4)
    parts = [box(name + "_back", (0, 0, 0.005), (0.32, 0.24, 0.01), st),
             box(name + "_side", (0, 0.12, 0.035), (0.32, 0.008, 0.07), st), box(name + "_side2", (0, -0.12, 0.035), (0.32, 0.008, 0.07), st),
             box(name + "_side3", (0.16, 0, 0.035), (0.008, 0.24, 0.07), st), box(name + "_side4", (-0.16, 0, 0.035), (0.008, 0.24, 0.07), st),
             box(name + "_pcb", (0, 0.01, 0.016), (0.24, 0.16, 0.003), pcb)]
    for i in range(10):
        parts.append(box(name + "_chip", (-0.09 + (i % 5) * 0.045, -0.03 + (i // 5) * 0.06, 0.02), (0.025, 0.012, 0.005), flat("chip", (0.01, 0.01, 0.01), 0.4)))
    cols = [(0.6, 0.05, 0.03), (0.05, 0.1, 0.5), (0.7, 0.6, 0.05), (0.05, 0.4, 0.08)]
    for i in range(8):
        a = Vector((-0.1 + i * 0.028, -0.09, 0.02)); b = Vector((-0.2 - 0.03 * i, -0.25 - 0.02 * i, 0.003))
        parts.append(S.cyl(name + "_wire", a, b, 0.0018, mat=flat(f"wire{i}", cols[i % 4], 0.5), verts=6))
    lid = box(name + "_lid", (0.05, -0.35, 0.005), (0.32, 0.24, 0.01), st, rot=(0, 0, 0.3)); parts.append(lid)
    return _root(name, parts)


def loupe(name="loupe"):
    m = flat(name + "_black", (0.02, 0.02, 0.02), 0.4)
    glass = bpy.data.materials.new(name + "_glass"); glass.use_nodes = True
    g = glass.node_tree.nodes["Principled BSDF"]; g.inputs['Transmission Weight'].default_value = 1.0; g.inputs['Roughness'].default_value = 0.0
    parts = [S.cyl(name + "_barrel", (0, 0, 0), (0, -0.018, 0), 0.013, 0.011, mat=m, verts=24),
             S.cyl(name + "_lens", (0, -0.006, 0), (0, -0.009, 0), 0.0115, mat=glass, verts=24)]
    return _root(name, parts)


def mobile(name="mobile"):
    """A 2003 mobile phone (11 x 4.6 x 1.8 cm), dark grey, small lit screen. Origin at its centre; long axis z,
    face toward -x local (turned to the cheek by the caller)."""
    b = flat(name + "_body", (0.06, 0.065, 0.07), 0.35, metal=0.2)
    parts = [box(name + "_body", (0, 0, 0), (0.018, 0.046, 0.11), b, bevel=0.007),
             box(name + "_screen", (0.0092, 0, 0.022), (0.001, 0.03, 0.03), emit(name + "_scr", (0.4, 0.8, 0.5), 2.0))]
    return _root(name, parts)


def holdall(name="holdall", color=(0.03, 0.03, 0.035), full=0.7, open_=True):
    """Nylon holdall (60 x 30 x 30 cm), soft: a rounded box sagging with its load, two strap handles, a zip line;
    open_=True leaves the top gaping. Origin on the floor at its centre."""
    import bmesh
    m = flat(name + "_nylon", color, 0.55); m.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.4
    h = 0.18 + 0.14 * full
    body = box(name + "_body", (0, 0, h / 2), (0.6, 0.3, h), m, bevel=0.06)
    body.modifiers["Bevel"].segments = 4
    sm = body.modifiers.new("Sag", "SIMPLE_DEFORM"); sm.deform_method = 'BEND'; sm.angle = math.radians(8); sm.deform_axis = 'Y'
    parts = [body]
    for sx in (-0.12, 0.12):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.008, location=(sx, 0, h + 0.0),
                                         rotation=(math.pi / 2, 0, math.pi / 2))
        t = bpy.context.active_object; t.name = name + "_strap"; t.scale = (1.0, 0.55, 1.0); t.data.materials.append(m); parts.append(t)
    if open_:
        parts.append(box(name + "_mouth", (0, 0, h - 0.004), (0.42, 0.12, 0.008), flat(name + "_dark", (0.005, 0.005, 0.005), 0.9)))
    return _root(name, parts)


def tape_roll(name="tape"):
    m = flat(name + "_grey", (0.32, 0.32, 0.33), 0.55)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.018, location=(0, 0, 0))
    t = bpy.context.active_object; t.name = name + "_roll"; t.scale = (1, 1, 1.4); t.data.materials.append(m)
    return _root(name, [t])


def stepladder(name="ladder", h=1.6):
    """Aluminium stepladder (A-frame), steps every 25 cm. Origin on the floor centre; front faces -y."""
    al = flat(name + "_alu", (0.62, 0.62, 0.6), 0.35, metal=0.9)
    parts = []
    sp = 0.32
    for sx in (-0.22, 0.22):
        parts.append(S.cyl(name + "_rail", (sx, -sp / 2, 0), (sx, -0.04, h), 0.016, mat=al, verts=8))
        parts.append(S.cyl(name + "_back", (sx, sp / 2 + 0.1, 0), (sx, 0.02, h), 0.014, mat=al, verts=8))
    k = 1
    while k * 0.26 < h - 0.1:
        z = k * 0.26; y = -sp / 2 + (sp / 2 - 0.04) * z / h
        parts.append(box(name + "_step", (0, y - 0.02, z), (0.46, 0.09, 0.025), al)); k += 1
    parts.append(box(name + "_top", (0, -0.01, h + 0.01), (0.48, 0.16, 0.03), flat(name + "_cap", (0.55, 0.06, 0.04), 0.5)))
    A = _root(name, parts); A["top_z"] = h + 0.025; A["steps"] = k - 1
    return A


def forcing_tool(name="tool"):
    """The crew's box-opening tool: a 45 cm hardened steel lever with a hooked, chisel-edged head that bites behind
    the lock, and a taped grip. Origin at the grip centre, head along +x."""
    st = flat(name + "_steel", (0.15, 0.15, 0.16), 0.32, metal=0.95); tp = flat(name + "_tape", (0.05, 0.05, 0.05), 0.7)
    parts = [S.cyl(name + "_shaft", (-0.1, 0, 0), (0.3, 0, 0), 0.011, mat=st, verts=12),
             S.cyl(name + "_grip", (-0.12, 0, 0), (0.06, 0, 0), 0.016, mat=tp, verts=12),
             box(name + "_head", (0.33, 0, 0.012), (0.05, 0.022, 0.04), st, rot=(0, math.radians(-25), 0)),
             box(name + "_hook", (0.355, 0, -0.012), (0.03, 0.02, 0.014), st)]
    return _root(name, parts)


def gold_bar(name="gold_bar", big=False):
    """1 kg bar (11.6 x 5.3 x 0.9 cm) or a 12.5 kg 'good delivery' bar; trapezoid section."""
    au = gold(name + "_au", (0.95, 0.66, 0.24))
    L_, W_, H_ = (0.255, 0.075, 0.04) if big else (0.116, 0.053, 0.009)
    o = box(name, (0, 0, H_ / 2), (L_, W_, H_), au, bevel=H_ * 0.25)
    o.modifiers.new("Taper", "SIMPLE_DEFORM").deform_method = 'TAPER'
    o.modifiers["Taper"].factor = -0.25; o.modifiers["Taper"].deform_axis = 'Z'
    return o


def cash_bundle(name="cash", color=(0.55, 0.45, 0.6)):
    """A strapped bundle of 100 euro-sized notes (14 x 7.5 x 1.1 cm) with a paper band."""
    n = flat(name + "_notes", color, 0.8)
    parts = [box(name + "_stack", (0, 0, 0.0055), (0.14, 0.075, 0.011), n),
             box(name + "_band", (0, 0, 0.0055), (0.03, 0.0765, 0.0115), flat(name + "_band", (0.85, 0.82, 0.72), 0.7))]
    return _root(name, parts)


def diamonds(name="diamonds", n=40, spread=0.06, seed=2):
    """Loose brilliants (2-8 mm) on whatever they lie on: real refractive gems."""
    import random as _r
    from sets import gem
    rng = _r.Random(seed); g = gem(name + "_mat"); parts = []
    for i in range(n):
        r = rng.uniform(0.0015, 0.004)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=r, radius2=r * 0.55, depth=r * 0.45,
                                        location=(rng.gauss(0, spread), rng.gauss(0, spread), r * 0.25))
        a = bpy.context.active_object
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=r, radius2=0.0, depth=r * 0.9,
                                        location=(a.location.x, a.location.y, a.location.z - r * 0.65), rotation=(math.pi, 0, 0))
        b = bpy.context.active_object
        for o in (a, b):
            o.data.materials.append(g); o.rotation_euler.z = rng.uniform(0, 6.28); parts.append(o)
    return _root(name, parts)
