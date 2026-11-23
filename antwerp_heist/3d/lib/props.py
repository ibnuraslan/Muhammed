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


def fire_glass(name="diamond_fire"):
    """Diamond: three clear glass BSDFs at IOR 2.407 / 2.419 / 2.451 (red / green / blue), summed per channel:
    real dispersion (fire), near-zero roughness."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"])
    add1 = N.new("ShaderNodeAddShader"); add2 = N.new("ShaderNodeAddShader")
    gs = []
    for ior, col in ((2.407, (1, 0, 0)), (2.419, (0, 1, 0)), (2.451, (0, 0, 1))):
        g = N.new("ShaderNodeBsdfGlass"); g.inputs['IOR'].default_value = ior; g.inputs['Roughness'].default_value = 0.0
        g.inputs['Color'].default_value = (*col, 1); gs.append(g)
    L.new(gs[0].outputs[0], add1.inputs[0]); L.new(gs[1].outputs[0], add1.inputs[1])
    L.new(add1.outputs[0], add2.inputs[0]); L.new(gs[2].outputs[0], add2.inputs[1])
    L.new(add2.outputs[0], N["Material Output"].inputs['Surface'])
    return m


def brilliant(name="brilliant", d=0.006, mat=None):
    """A round brilliant (girdle diameter d) as the closed convex hull of its real proportions: table 57 %,
    crown 34.5 deg (bezel + star points), 16-point girdle with a little thickness, pavilion 40.75 deg (main + lower
    girdle points) to a culet. Flat shaded so every facet flashes. Origin at the girdle centre, table up."""
    import bmesh
    r = d / 2; t = 0.57 * r
    hc = math.tan(math.radians(34.5)) * (r - t); hp = math.tan(math.radians(40.75)) * r; gt = 0.02 * d
    pts = []
    for k in range(16):
        a = 2 * math.pi * k / 16
        pts += [(r * math.cos(a), r * math.sin(a), gt / 2), (r * math.cos(a), r * math.sin(a), -gt / 2)]
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        pts.append((t * math.cos(a), t * math.sin(a), hc + gt / 2))                                     # table
        a2 = 2 * math.pi * k / 8
        pts.append((0.8 * r * math.cos(a2), 0.8 * r * math.sin(a2), gt / 2 + hc * (1 - (0.8 * r - t) / (r - t)) * 0.98))  # bezel
        pts.append((0.5 * r * math.cos(a2), 0.5 * r * math.sin(a2), -gt / 2 - hp * 0.5))                # pavilion mains
    pts.append((0, 0, -gt / 2 - hp))                                                                     # culet
    bm = bmesh.new()
    for p_ in pts:
        bm.verts.new(p_)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(mat or fire_glass())
    return o


def brilliants(name="diamonds", n=40, spread=0.05, seed=2, table_up=0.85):
    """Loose brilliants (2-9 mm) lying on a surface: most on their pavilion side (tilted, as stones fall), some
    table-down; one shared fire material."""
    import random as _r
    rng = _r.Random(seed); mat = fire_glass(name + "_fire"); parts = []
    for i in range(n):
        d = rng.choice((0.0025, 0.003, 0.004, 0.005, 0.0065, 0.009)) * rng.uniform(0.9, 1.1)
        o = brilliant(f"{name}_{i}", d, mat)
        x, y = rng.gauss(0, spread), rng.gauss(0, spread)
        if rng.random() < table_up:            # table up, as a dealer lays stones out on a paper (culet set into the fold)
            o.rotation_euler = (rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), rng.uniform(0, 6.28)); z = d * 0.42
        else:                                  # tipped on its side
            o.rotation_euler = (math.radians(70), 0, rng.uniform(0, 6.28)); z = d * 0.42
        o.location = (x, y, z); parts.append(o)
    return _root(name, parts)


def sf_put(uid, loc, width=None, height=None, rz=0.0, name=None):
    """Import a vetted Sketchfab model (lib/sf.py) scaled to a real size and set on the surface at loc."""
    import sf, ph
    from mathutils import Vector as _V
    r, ms = sf.model(uid, loc=(0, 0, 0), rot_z=rz)
    lo, hi = ph.bounds(ms)
    s = (width / max(hi.x - lo.x, hi.y - lo.y)) if width else (height / (hi.z - lo.z))
    r.scale = (s, s, s); bpy.context.view_layer.update(); lo, hi = ph.bounds(ms)
    r.location = _V(loc) - _V(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)) + _V((0, 0, loc[2] if len(loc) > 2 else 0))
    if name:
        r.name = name
    return r


EURO_STACK = "23603d130e684401be3ed7c482c3076e"      # "#Euro Banknote Stack Tied With Rubber", Dakta.Grower.Nzl, CC-BY
GOLD_BAR = "87e4e0a9da7f4c8a9561a932d09279bd"        # "gold bar", alex.yefremov, CC-BY
GOLD_BARS = "0d1ff6b3e6d045cba78889caf7f5bc6e"       # "Fine Gold Bar", incg5764, CC-BY
RING_DIAMOND = "5a03949eea904d6989f87aaf5d172722"    # "Ring, Gold with Diamond", lucasjosemone, CC-BY
USD_STACKS = "1ef927f0bd924a62883f0dd026d80f40"     # "Stacks of US dollar bills", Chenzoss, CC-BY (strapped $100 stacks)
USD_LOOSE = "7e54bc39435f459a921370caa7e21090"      # "A stack of 100 dollar bills.", hocza, CC-BY (loose spill)
RING_CARAT = "378f6df2c4f444399b83db2037258470"      # "The Ring: 1 carat", Evanz, CC-BY


def document(name="doc", w=0.21, h=0.297, torn=False, seed=0, lines=22, color=(0.86, 0.85, 0.8)):
    """A printed page (rows of grey type as thin bars, no legible words) - torn=True gives it a ragged edge and
    leaves only a scrap. Origin at its centre, lying flat."""
    import random as _r, bmesh
    rng = _r.Random(seed)
    pm = paper_mat(name + "_paper", color); ink = flat(name + "_ink", (0.12, 0.12, 0.13), 0.7)
    bm = bmesh.new()
    if torn:
        pts = []
        n = 24
        for k in range(n):
            a = 2 * math.pi * k / n
            rr = rng.uniform(0.75, 1.0)
            pts.append((math.cos(a) * w / 2 * rr, math.sin(a) * h / 2 * rr * 0.6, 0))
        f = bm.faces.new([bm.verts.new(p) for p in pts])
    else:
        f = bm.faces.new([bm.verts.new(p) for p in ((-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0))])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(pm)
    so = o.modifiers.new("t", "SOLIDIFY"); so.thickness = 0.0006
    parts = [o]
    hh = h * (0.6 if torn else 1.0)
    for k in range(lines):
        y = -hh / 2 + 0.02 + k * (hh - 0.04) / max(1, lines - 1)
        lw = w * rng.uniform(0.45, 0.8) * (0.7 if torn else 1.0)
        parts.append(box(name + "_line", (-w * 0.05, y, 0.0008), (lw, 0.0035, 0.0002), ink))
    return _root(name, parts)


def receipt(name="receipt", length=0.2, seed=1):
    """A supermarket till receipt: narrow thermal paper strip, curled, columns of faint type."""
    return document(name, w=0.08, h=length, torn=False, seed=seed, lines=26, color=(0.9, 0.9, 0.87))


def fax(name="fax"):
    """A 1990s office fax machine with a page curling out of it."""
    body = flat(name + "_body", (0.75, 0.74, 0.7), 0.4)
    parts = [box(name + "_body", (0, 0, 0.06), (0.32, 0.28, 0.12), body, bevel=0.02),
             box(name + "_keys", (0.08, -0.08, 0.121), (0.1, 0.08, 0.004), flat(name + "_keys", (0.2, 0.2, 0.2), 0.5)),
             box(name + "_screen", (-0.05, -0.1, 0.121), (0.08, 0.025, 0.003), emit(name + "_lcd", (0.4, 0.6, 0.3), 1.0))]
    pg = document(name + "_page", 0.21, 0.2, seed=4); pg.location = (0, 0.15, 0.13); pg.rotation_euler = (math.radians(-35), 0, 0)
    parts.append(pg)
    return _root(name, parts)


def lightbox(name="lightbox", w=0.6, h=0.45):
    m = emit(name + "_glow", (1.0, 0.98, 0.94), 4.0)
    parts = [box(name + "_frame", (0, 0, 0.025), (w + 0.04, h + 0.04, 0.05), flat(name + "_frame", (0.2, 0.2, 0.2), 0.4)),
             box(name + "_panel", (0, 0, 0.0505), (w, h, 0.002), m)]
    return _root(name, parts)


def swab(name="swab"):
    """A DNA swab: thin plastic shaft with a cotton tip; origin at the grip end, tip along +x."""
    parts = [S.cyl(name + "_shaft", (0, 0, 0), (0.15, 0, 0), 0.0015, mat=flat(name + "_shaft", (0.9, 0.9, 0.9), 0.3), verts=8)]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.004, location=(0.155, 0, 0))
    t = bpy.context.active_object; t.scale = (2.0, 1, 1); t.data.materials.append(flat(name + "_cotton", (0.95, 0.95, 0.93), 0.95)); parts.append(t)
    return _root(name, parts)


def rug(name="rug", w=2.4, h=1.7, color=(0.35, 0.12, 0.08)):
    """A thick wool rug (pile shown with a strong bump and a little displacement)."""
    m = flat(name + "_wool", color, 0.95)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 900; nz.inputs['Detail'].default_value = 4
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.9; L.new(nz.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 4; br.inputs['Color1'].default_value = (*color, 1)
    br.inputs['Color2'].default_value = (color[0] * 0.6, color[1] * 0.8, color[2] * 1.4, 1); br.inputs['Mortar'].default_value = (0.6, 0.5, 0.35, 1)
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['Object'], br.inputs['Vector']); L.new(br.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Sheen Weight'].default_value = 0.6
    o = box(name, (0, 0, 0.006), (w, h, 0.012), m)
    return o
