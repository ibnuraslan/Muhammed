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


def torch(name="torch", on=True, energy=40.0):
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
