"""Period office and communications machines, 1975-85 (generic, unbranded): copier, CRT terminal, teletype
(with paper tape and a printing platen), a cipher machine (rack box with switches and lamps), a burlap crate.
Each returns (root, parts dict). Front = -Y; origin on the floor/desk under the machine centre."""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, join, glass, emissive
import ph

_M = {}


def mats():
    if not _M:
        _M["beige"] = pbr("MachBeige", (0.36, 0.33, 0.27), 0.45, 0.0, **{'Coat Weight': 0.2})
        _M["grey"] = pbr("MachGrey", (0.36, 0.37, 0.36), 0.45, 0.0, **{'Coat Weight': 0.2})
        _M["olive"] = pbr("MachOlive", (0.2, 0.22, 0.17), 0.55, 0.1)
        _M["dark"] = pbr("MachDark", (0.03, 0.03, 0.035), 0.45)
        _M["metal"] = pbr("MachMetal", (0.55, 0.56, 0.57), 0.3, 1.0)
        _M["glassd"] = pbr("CRTGlass", (0.02, 0.03, 0.03), 0.05, 0.0, **{'Coat Weight': 1.0})
        _M["paper"] = pbr("TTYPaper", (0.82, 0.8, 0.72), 0.85)
        _M["tape"] = pbr("PaperTape", (0.8, 0.72, 0.5), 0.8)
        _M["lamp_r"] = pbr("LampRed", (0.3, 0.02, 0.02), 0.3, 0.0, **{'Emission Color': (1, 0.1, 0.05, 1), 'Emission Strength': 0.0})
        _M["lamp_g"] = pbr("LampGreen", (0.05, 0.25, 0.08), 0.3, 0.0, **{'Emission Color': (0.3, 1, 0.4, 1), 'Emission Strength': 0.0})
        _M["platen"] = pbr("TTYPlaten", (0.02, 0.02, 0.022), 0.6)
    return _M


def _root(name, loc, rot_z):
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    r.location = loc; r.rotation_euler = (0, 0, rot_z)
    return r


def _kid(o, r):
    o.parent = r; o.matrix_parent_inverse = Matrix.Identity(4); return o


def copier(name, loc=(0, 0, 0), rot_z=0.0):
    """Floor-standing 1980s copier: cabinet, body, glass platen under a hinged lid, paper trays."""
    M = mats(); r = _root(name, loc, rot_z)
    _kid(box("Cab", (0, 0, 0.35), (1.0, 0.62, 0.7), M["grey"], bevel=0.01), r)
    _kid(box("Body", (0, 0, 0.9), (1.05, 0.65, 0.4), M["beige"], bevel=0.02), r)
    _kid(box("Platen", (0, 0, 1.105), (0.6, 0.4, 0.01), M["glassd"]), r)
    _kid(box("Lid", (0, 0.02, 1.13), (0.66, 0.46, 0.04), M["beige"], bevel=0.008), r)
    _kid(box("Panel", (0.32, -0.27, 1.1), (0.3, 0.1, 0.02), M["dark"]), r)
    _kid(box("Tray", (0.62, 0, 0.88), (0.22, 0.34, 0.02), M["grey"], rot=(0, math.radians(-8), 0)), r)
    _kid(box("OutTray", (-0.62, 0, 0.8), (0.24, 0.36, 0.02), M["grey"], rot=(0, math.radians(8), 0)), r)
    for k in range(2):
        _kid(box("Drawer", (0, -0.315, 0.2 + k * 0.26), (0.9, 0.01, 0.22), M["beige"]), r)
    return r


def terminal(name, loc=(0, 0, 0), rot_z=0.0, screen=None):
    """Desk CRT terminal with detached keyboard. screen: an emissive material for the tube face (or dark)."""
    M = mats(); r = _root(name, loc, rot_z)
    _kid(box("Case", (0, 0.06, 0.2), (0.42, 0.42, 0.36), M["beige"], bevel=0.03), r)
    _kid(box("Back", (0, 0.27, 0.19), (0.32, 0.2, 0.28), M["beige"], bevel=0.04), r)
    _kid(box("Bezel", (0, -0.155, 0.22), (0.36, 0.02, 0.28), M["dark"], bevel=0.01), r)
    tube = _kid(box("Tube", (0, -0.163, 0.225), (0.3, 0.01, 0.22), screen or M["glassd"], bevel=0.02), r)
    _kid(box("Keyboard", (0, -0.42, 0.02), (0.46, 0.18, 0.035), M["beige"], bevel=0.008, rot=(math.radians(6), 0, 0)), r)
    _kid(box("Keys", (0, -0.425, 0.04), (0.42, 0.14, 0.012), M["grey"], rot=(math.radians(6), 0, 0)), r)
    return r, tube


def teletype(name, loc=(0, 0, 0), rot_z=0.0, stand=True):
    """Page-printing teletype on its stand: rounded hood with a window, platen and paper, tape punch at the side.
    Returns root and parts: 'paper' (scroll up), 'typebox' (shuttles along the platen), 'tape' (feeds out)."""
    M = mats(); r = _root(name, loc, rot_z)
    p = {}
    z0 = 0.0
    if stand:
        _kid(box("Stand", (0, 0.05, 0.36), (0.75, 0.6, 0.72), M["olive"], bevel=0.01), r)
        z0 = 0.72
    _kid(box("Base", (0, 0.0, z0 + 0.08), (0.7, 0.62, 0.16), M["olive"], bevel=0.02), r)
    _kid(box("Hood", (0, 0.06, z0 + 0.3), (0.68, 0.48, 0.3), M["olive"], bevel=0.06), r)
    _kid(box("Window", (0, -0.12, z0 + 0.34), (0.5, 0.2, 0.14), M["glassd"], bevel=0.02, rot=(math.radians(-30), 0, 0)), r)
    _kid(box("KeyDeck", (0, -0.3, z0 + 0.17), (0.6, 0.22, 0.06), M["olive"], bevel=0.01, rot=(math.radians(10), 0, 0)), r)
    for row in range(4):
        for k in range(11 - row):
            _kid(cyl("TKey", (-0.21 + k * 0.04 + row * 0.02, -0.37 + row * 0.04, z0 + 0.2 + row * 0.008), 0.012, 0.03, M["dark"], verts=12), r)
    pl = _kid(cyl("Platen", (0, 0.12, z0 + 0.46), 0.03, 0.56, M["platen"], verts=24, rot=(0, math.radians(90), 0)), r)
    paper = _kid(box("Paper", (0, 0.13, z0 + 0.62), (0.5, 0.004, 0.3), M["paper"], rot=(math.radians(-12), 0, 0)), r)
    p["paper"] = paper; p["paper_z"] = paper.location.z
    tb = _kid(box("TypeBox", (0, 0.08, z0 + 0.44), (0.05, 0.04, 0.04), M["metal"]), r)
    p["typebox"] = tb
    _kid(box("Punch", (0.42, -0.05, z0 + 0.18), (0.16, 0.3, 0.2), M["olive"], bevel=0.015), r)
    tape = _kid(box("Tape", (0.42, -0.25, z0 + 0.24), (0.025, 0.25, 0.002), M["tape"]), r)
    p["tape"] = tape; p["tape_y"] = tape.location.y
    return r, p


def run_teletype(p, sec, rate=6.0):
    """Typebox shuttles, the paper creeps up a line at a time, the punched tape feeds out."""
    x = -0.22 + (sec * rate * 0.0254 % 0.44)
    p["typebox"].location.x = x
    line = math.floor(sec * rate * 0.0254 / 0.44)
    p["paper"].location.z = p["paper_z"] + 0.0042 * line
    p["tape"].location.y = p["tape_y"] - 0.04 * (sec % 3.0)


def cipher(name, loc=(0, 0, 0), rot_z=0.0, height=0.45, lamps=8):
    """Cipher machine: grey rack box with toggle switches, a key lock, indicator lamps and a tape reader."""
    M = mats(); r = _root(name, loc, rot_z)
    _kid(box("Case", (0, 0, height / 2), (0.55, 0.5, height), M["grey"], bevel=0.008), r)
    _kid(box("Front", (0, -0.252, height / 2), (0.52, 0.01, height - 0.04), M["dark"]), r)
    for k in range(8):
        _kid(box("Toggle", (-0.2 + k * 0.05, -0.27, height * 0.35), (0.01, 0.03, 0.01), M["metal"], rot=(math.radians(25), 0, 0)), r)
    lamp_objs = []
    for k in range(lamps):
        m = M["lamp_g"] if k % 3 else M["lamp_r"]
        lamp_objs.append(_kid(cyl("Lamp", (-0.2 + k * 0.057, -0.262, height * 0.72), 0.008, 0.012, m, verts=12, rot=(math.radians(90), 0, 0)), r))
    _kid(cyl("KeyLock", (0.2, -0.262, height * 0.35), 0.016, 0.015, M["metal"], verts=16, rot=(math.radians(90), 0, 0)), r)
    _kid(box("Reader", (0, -0.1, height + 0.05), (0.3, 0.2, 0.1), M["grey"], bevel=0.008), r)
    return r, lamp_objs


def lamp_blink(mat_names=("LampRed", "LampGreen"), period=24, strength=6.0):
    """Frame-driven blinking for all cipher lamps (driver on the emission strength: plays without scripts)."""
    for k, n in enumerate(mat_names):
        m = bpy.data.materials.get(n)
        if m is None:
            continue
        p = m.node_tree.nodes["Principled BSDF"]
        d = p.inputs['Emission Strength'].driver_add("default_value").driver; d.type = 'SCRIPTED'
        d.expression = f"{strength} * (1 if (frame + {k * 7}) % {period} < {period * 0.6} else 0.25)"


def burlap_crate(name, size=(0.95, 0.75, 0.85), tag=True):
    """A crate sewn into coarse burlap: weave texture, rope lashing both ways, staples along the top seam, a tag."""
    hes = bpy.data.materials.get("BurlapBig") or ph.texture("hessian_230", scale=0.65, name="BurlapBig", tint=(0.72, 0.6, 0.42))
    rope = bpy.data.materials.get("Rope") or ph.texture("hessian_380", scale=6.0, name="Rope", tint=(0.55, 0.45, 0.32))
    stm = bpy.data.materials.get("StapleE") or pbr("StapleE", (0.7, 0.7, 0.72), 0.25, 1.0)
    sx, sy, sz = size
    body = box("Crate", (0, 0, 0), size, hes, bevel=0.04)
    sub = body.modifiers.new("sub", 'SUBSURF'); sub.levels = 2; sub.render_levels = 2; sub.subdivision_type = 'SIMPLE'
    dsp = body.modifiers.new("folds", 'DISPLACE'); tx = bpy.data.textures.get("BurlapFolds") or bpy.data.textures.new("BurlapFolds", 'CLOUDS')
    tx.noise_scale = 0.12; dsp.texture = tx; dsp.strength = 0.02; dsp.mid_level = 0.5
    parts = [body]
    for dx in (-sx * 0.3, sx * 0.3):
        parts.append(cyl("RopeV", (dx, -sy / 2 - 0.008, 0), 0.01, sz + 0.02, rope, verts=8))
        parts.append(cyl("RopeV", (dx, sy / 2 + 0.008, 0), 0.01, sz + 0.02, rope, verts=8))
        parts.append(cyl("RopeT", (dx, 0, sz / 2 + 0.008), 0.01, sy + 0.02, rope, verts=8, rot=(math.radians(90), 0, 0)))
    parts.append(cyl("RopeH", (0, 0, sz / 2 + 0.01), 0.01, sx + 0.02, rope, verts=8, rot=(0, math.radians(90), 0)))
    for k in range(10):
        parts.append(box("Staple", (-sx / 2 + 0.06 + k * (sx - 0.12) / 9, -sy / 2 - 0.004, sz / 2 - 0.035), (0.016, 0.003, 0.003), stm))
    if tag:
        parts.append(box("Tag", (sx * 0.15, -sy / 2 - 0.01, sz * 0.12), (0.16, 0.004, 0.1), pbr("Tag", (0.82, 0.8, 0.72), 0.8)))
    return join(parts, name)
