"""Seldom intro films (Part 4 session, films 1-4): shared helpers.

Uses the shared cast and lib (mary_celeste_3d/lib, through mary_celeste_p4/lib/p4.py) as-is.
The logo is ALWAYS the official image (assets/seldom_logo_tight.png, from brand/seldom_logo.png) used as a
texture on a physical prop: an enamel plate, letterpress print, stencil paint. Never 3D text.
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "..", "mary_celeste_p4", "lib"))
sys.path.insert(0, HERE)
import p4                                  # sets sys.path for the shared lib and MH_DATA
import bpy
from mathutils import Vector, Matrix
import ship, human as H, poses as P, deveau as D, briggs as BG

LOGO = os.path.join(ROOT, "assets", "seldom_logo_tight.png")
LOGO_ASPECT = 1326 / 369
HUE_COMP = 0.03
C = p4.C
ease = p4.ease
ANIM = os.environ.get("ANIM")
CAMDUMP = os.environ.get("CAMDUMP")
CAMS = []; ACTORS = []; GRADE = {}
T = 0.0          # shot time 0..1: poses and props read it (stills: the requested t; animation: set per key)
DYN = []         # callbacks f(t, frame): move/animate props; frame is None for a still (no keys)
PEOPLE = []      # (dv, M) of everyone in the shot


def dyn(fn):
    """Register a time-dependent prop update. Stills call it once at T; the animation pass keys it every frame."""
    DYN.append(fn)
    return fn


def run_dyn(t, frame=None):
    for fn in DYN:
        fn(t, frame)


def key(obj, *paths, frame=None):
    if frame is None:
        return
    for p_ in paths:
        obj.keyframe_insert(p_, frame=frame)


def place(obj, Mw, frame=None):
    """Set an object's world matrix (no parent) and key loc/rot/scale on `frame`."""
    obj.matrix_world = Mw
    if frame is not None:
        obj.rotation_mode = 'XYZ'
        obj.keyframe_insert("location", frame=frame); obj.keyframe_insert("rotation_euler", frame=frame)
        obj.keyframe_insert("scale", frame=frame)


def set_value(node_socket, v, frame=None):
    node_socket.default_value = v
    if frame is not None:
        node_socket.keyframe_insert("default_value", frame=frame)


def hand(dv, M, side):
    """World palm position now: from the live rig in the animation pass, from the baked pose in a still."""
    if ANIM:
        arm = dv.h.arm; pb = arm.pose.bones[f"wrist.{side}"]
        return arm.matrix_world @ pb.tail
    return palm(dv, M, side)


def lerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def logo_image():
    for im in bpy.data.images:
        if im.filepath and os.path.basename(im.filepath) == os.path.basename(LOGO):
            return im
    im = bpy.data.images.load(LOGO); im.alpha_mode = 'STRAIGHT'
    im.name = "seldom_logo_alpha"          # "alpha" in the name: the farm export keeps it a PNG with its alpha
    return im


# ----------------------------------------------------------------------------- logo materials
def _logo_nodes(nt, uv_socket, extension='CLIP'):
    """Image Texture node for the logo fed by uv_socket. Returns (color, alpha) sockets."""
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = logo_image(); tx.extension = extension
    tx.interpolation = 'Cubic'
    nt.links.new(uv_socket, tx.inputs["Vector"])
    # the house grade (AgX + warm highlights) pushes lime toward butter-yellow: a small hue shift toward green
    # keeps the printed/fired colour reading as the brand lime (#E3FF00) on screen (measured, see tools/coltest)
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Hue"].default_value = 0.5 + HUE_COMP
    nt.links.new(tx.outputs["Color"], hs.inputs["Color"])
    return hs.outputs["Color"], tx.outputs["Alpha"]


def enamel_material(name, ground=(0.012, 0.016, 0.03), chip=0.25, grime=0.3):
    """Vitreous enamel sign: the logo fired into a glossy ground; chips show dark iron at the edges; light grime.
    Use on a mesh whose UVs map the logo area to 0..1 (see plate())."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    uv = nt.nodes.new("ShaderNodeTexCoord")
    col, a = _logo_nodes(nt, uv.outputs["UV"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (*ground, 1)
    nt.links.new(a, mix.inputs[0]); nt.links.new(col, mix.inputs[7])
    # chips: noise near the plate edge (generated coords) -> iron
    gen = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9.0; nz.inputs["Detail"].default_value = 8
    nt.links.new(gen.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 1.0 - 0.12 * chip; ramp.color_ramp.elements[1].position = 1.0 - 0.1 * chip
    nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
    iron = nt.nodes.new("ShaderNodeMix"); iron.data_type = 'RGBA'; iron.inputs[7].default_value = (0.03, 0.022, 0.016, 1)
    nt.links.new(ramp.outputs["Color"], iron.inputs[0]); nt.links.new(mix.outputs[2], iron.inputs[6])
    # grime in the low spots
    gn = nt.nodes.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 40.0
    nt.links.new(gen.outputs["Object"], gn.inputs["Vector"])
    gm = nt.nodes.new("ShaderNodeMix"); gm.data_type = 'RGBA'; gm.blend_type = 'MULTIPLY'
    gm.inputs[0].default_value = grime; gm.inputs[7].default_value = (0.55, 0.5, 0.42, 1)
    nt.links.new(iron.outputs[2], gm.inputs[6])
    nt.links.new(gm.outputs[2], bs.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.12; rr.inputs[4].default_value = 0.55
    nt.links.new(ramp.outputs["Color"], rr.inputs[0]); nt.links.new(rr.outputs[0], bs.inputs["Roughness"])
    bs.inputs["Coat Weight"].default_value = 0.6; bs.inputs["Coat Roughness"].default_value = 0.08
    return m


def paper_print_material(name, paper=(0.78, 0.73, 0.62), bite=1.0):
    """Letterpress: ink pressed into cotton paper. The inked areas are bitten in (bump), ink a touch glossier."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    uv = nt.nodes.new("ShaderNodeTexCoord")
    col, a = _logo_nodes(nt, uv.outputs["UV"])
    fib = nt.nodes.new("ShaderNodeTexNoise"); fib.inputs["Scale"].default_value = 300; fib.inputs["Detail"].default_value = 12
    nt.links.new(uv.outputs["Object"], fib.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.inputs[6].default_value = (*paper, 1)
    nt.links.new(a, mix.inputs[0]); nt.links.new(col, mix.inputs[7])
    nt.links.new(mix.outputs[2], bs.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.85; rr.inputs[4].default_value = 0.55
    nt.links.new(a, rr.inputs[0]); nt.links.new(rr.outputs[0], bs.inputs["Roughness"])
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(a, inv.inputs[1])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = 'MULTIPLY_ADD'
    nt.links.new(fib.outputs["Fac"], add.inputs[0]); add.inputs[1].default_value = 0.15; nt.links.new(inv.outputs[0], add.inputs[2])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.5 * bite; bump.inputs["Distance"].default_value = 0.0004
    nt.links.new(add.outputs[0], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Sheen Weight"].default_value = 0.3
    return m


def paint_logo(m, proj, wear=0.45, wet=0.0, fade=0.85):
    """Paint the logo INTO an existing material (stencil paint on wood, paint on steel). proj: a Matrix taking
    OBJECT coordinates to logo space (logo 0..1 on its local x/y, painted where 0 < z < 0.02 thick slab).
    The paint wears off with a noise mask and follows the surface (it is the same surface: no decal)."""
    nt = m.node_tree
    bs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    base_link = bs.inputs["Base Color"].links[0].from_socket if bs.inputs["Base Color"].is_linked else None
    base_val = tuple(bs.inputs["Base Color"].default_value)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vm = nt.nodes.new("ShaderNodeVectorTransform") if False else None
    # object coords -> logo space with a mapping (proj given as loc/rot/scale)
    mp = nt.nodes.new("ShaderNodeMapping"); mp.vector_type = 'POINT'
    loc, rot, sca = proj.decompose()
    mp.inputs["Location"].default_value = loc; mp.inputs["Rotation"].default_value = rot.to_euler(); mp.inputs["Scale"].default_value = sca
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    col, a = _logo_nodes(nt, mp.outputs["Vector"])
    # only within the slab |z| < 0.03 in logo space (so the back of the crate is clean)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(mp.outputs["Vector"], sep.inputs[0])
    ab = nt.nodes.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; nt.links.new(sep.outputs[2], ab.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.5; nt.links.new(ab.outputs[0], lt.inputs[0])
    wn = nt.nodes.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 14.0; wn.inputs["Detail"].default_value = 10; wn.inputs["Roughness"].default_value = 0.7
    nt.links.new(tc.outputs["Object"], wn.inputs["Vector"])
    wr = nt.nodes.new("ShaderNodeMapRange"); wr.inputs[1].default_value = wear - 0.08; wr.inputs[2].default_value = wear + 0.08
    nt.links.new(wn.outputs["Fac"], wr.inputs[0])
    f1 = nt.nodes.new("ShaderNodeMath"); f1.operation = 'MULTIPLY'; nt.links.new(a, f1.inputs[0]); nt.links.new(lt.outputs[0], f1.inputs[1])
    f2 = nt.nodes.new("ShaderNodeMath"); f2.operation = 'MULTIPLY'; nt.links.new(f1.outputs[0], f2.inputs[0]); nt.links.new(wr.outputs[0], f2.inputs[1])
    f3 = nt.nodes.new("ShaderNodeMath"); f3.operation = 'MULTIPLY'; f3.inputs[1].default_value = fade; nt.links.new(f2.outputs[0], f3.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    if base_link is not None:
        nt.links.new(base_link, mix.inputs[6])
    else:
        mix.inputs[6].default_value = base_val
    nt.links.new(col, mix.inputs[7]); nt.links.new(f3.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], bs.inputs["Base Color"])
    # paint is a bit smoother than the wood under it
    if not bs.inputs["Roughness"].is_linked:
        rm = nt.nodes.new("ShaderNodeMapRange"); rm.inputs[3].default_value = bs.inputs["Roughness"].default_value
        rm.inputs[4].default_value = max(0.05, 0.45 - 0.35 * wet)
        nt.links.new(f2.outputs[0], rm.inputs[0]); nt.links.new(rm.outputs[0], bs.inputs["Roughness"])
    return m


def plate(name, M, w, thick=0.003, mat=None, margin=0.12, screws=4, screw_mat=None, h=None):
    """A real enamel plate: w wide (m), rounded corners, thickness `thick`, bevelled; logo on the front (local +Z
    face), UVs set so the logo fills it with `margin` round. M places it (local z = out of the wall).
    Returns [plate, screws...]."""
    import bmesh
    if h is None:
        h = w / LOGO_ASPECT * (1 + 2 * margin) / (1 + 2 * margin * 0.6)
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    r = min(w, h) * 0.08; N = 6; pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(N + 1):
            a = math.radians(a0 + 90 * k / N); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    top = [bm.verts.new((x, y, thick)) for x, y in pts]
    bot = [bm.verts.new((x, y, 0)) for x, y in pts]
    ft = bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    n = len(pts)
    for i in range(n):
        bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]))
    uvl = bm.loops.layers.uv.new("UV")
    lw = w - 2 * margin * h * 0.9; lh = lw / LOGO_ASPECT
    for f in bm.faces:
        for l in f.loops:
            x, y, z = l.vert.co
            l[uvl].uv = ((x + lw / 2) / lw, (y + lh / 2) / lh)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = False
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = min(0.0015, thick * 0.45); bv.segments = 3; bv.limit_method = 'ANGLE'
    o.matrix_world = M
    me.materials.append(mat or enamel_material(name + "_enamel"))
    out = [o]
    if screws:
        sm = screw_mat or D.brass_material(name + "_screw")
        for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))[:screws]:
            c = Vector((sx * (w / 2 - h * 0.09), sy * (h / 2 - h * 0.09), thick))
            s = ship.cyl(name + "_screw", M @ c, M @ (c + Vector((0, 0, 0.0018))), h * 0.035, mat=sm, verts=16)
            slot = ship.box(name + "_slot", M @ (c + Vector((0, 0, 0.0019))), (h * 0.06, h * 0.008, 0.0006),
                            p4.mat(name + "_slotm", (0.01, 0.008, 0.005), 0.8))
            slot.matrix_world = M @ Matrix.Translation(c + Vector((0, 0, 0.0019))) @ Matrix.Rotation(0.5 * sx * sy, 4, 'Z')
            out += [s, slot]
    return out


# ----------------------------------------------------------------------------- people
def settle(dv, z_floor, gap=0.002, kind=("boot", "shoe", "Body", "trouser", "body")):
    """Move the person so their lowest point (boots, or a knee on the floor) rests at z_floor."""
    dg = bpy.context.evaluated_depsgraph_get()
    lo = 1e9; per = {}
    for o in dv.objects:
        if o.type != 'MESH' or o.hide_render or o.name.endswith("_body"):     # the body carries unskinned helper verts
            continue
        oe = o.evaluated_get(dg); me = oe.to_mesh(); mw = oe.matrix_world
        for v in me.vertices:
            z = (mw @ v.co).z
            per[o.name] = min(per.get(o.name, 1e9), z)
            if z < lo:
                lo = z
        oe.to_mesh_clear()
    dz = z_floor + gap - lo
    print("SETTLE", round(lo, 3), round(dz, 3), [o.name for o in dv.objects if o.parent is None][:8], flush=True)
    for o in dv.objects:
        if o.parent is None:
            o.matrix_world = Matrix.Translation((0, 0, dz)) @ o.matrix_world
    bpy.context.view_layer.update()
    for o in dv.objects:                                   # the clipping check's grip test follows the hands down
        if "hands" in o:
            hd = list(o["hands"]); o["hands"] = [c + (dz if k % 3 == 2 else 0.0) for k, c in enumerate(hd)]
    return dz


def person(kind, pos, ang_deg, pose, look, floor_z=0.0, hair=1.0, **kw):
    """kind: deveau | briggs | sarah. pos: world (x, y); faces ang_deg (from +X). pose(h, dv, M, Mi) in rig space.
    look: world point the eyes look at. Returns (dv, M)."""
    M = Matrix.Translation((pos[0], pos[1], floor_z)) @ Matrix.Rotation(math.radians(ang_deg + 90), 4, 'Z')
    if CAMDUMP:
        return None, M
    if kind == "sarah":
        import women as W
        dv = W.Sarah(bonnet=False, shawl=kw.get("shawl", False))
    elif kind == "briggs":
        cls = type("BriggsSB", (BG.Briggs,), {"ASSET_BOOTS": False}) if kw.get("sea_boots") else BG.Briggs
        dv = cls(wet=kw.get("wet", 0.1), cap=kw.get("cap", False))
    else:
        cls = type("DeveauSB", (D.Deveau,), {"ASSET_BOOTS": False}) if kw.get("sea_boots") else D.Deveau
        dv = cls(wet=kw.get("wet", 0.1), cap=kw.get("cap", False))
    h = dv.h; Mi = M.inverted()
    PEOPLE.append((dv, M))
    if ANIM:
        ACTORS.append(dict(kind=kind, dv=dv, M=M, pose=pose, look=Vector(look), hair=hair, floor_z=floor_z,
                           settle=kw.get("settle", True)))
        dark_insides(dv); soft_skin(dv)
        return dv, M
    pose(h, dv, M, Mi)
    dark_insides(dv); soft_skin(dv)
    dv.finish(look_at=Vector(look), place=M, density=hair * float(os.environ.get("HAIR", "1")))
    dv.dz = settle(dv, floor_z) if kw.get("settle", True) else 0.0
    return dv, M


def soft_skin(dv, weight=0.2, radius=(0.7, 0.45, 0.35)):
    """Gentler skin subsurface (as P1 S02): a hand in shade or against a warm lamp otherwise glows deep red."""
    for o in dv.objects:
        for sl in getattr(o, "material_slots", []):
            m = sl.material
            if m and "skin" in m.name.lower() and m.node_tree:
                for n in m.node_tree.nodes:
                    if n.type == 'BSDF_PRINCIPLED':
                        n.inputs['Subsurface Weight'].default_value = weight
                        n.inputs['Subsurface Radius'].default_value = radius


def dark_insides(dv):
    """Kneeling opens the boot shafts: their inner (back-facing) surfaces read as a dark hollow, not lit leather."""
    done = set()
    for o in dv.objects:
        if o.type != 'MESH' or "boot" not in o.name.lower():
            continue
        for sl in o.material_slots:
            m = sl.material
            if not m or m.name in done or not m.node_tree:
                continue
            done.add(m.name); nt = m.node_tree
            bs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
            if not bs:
                continue
            bs = bs[0]; out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
            src = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else bs.outputs[0]
            geo = nt.nodes.new("ShaderNodeNewGeometry")
            dk = nt.nodes.new("ShaderNodeBsdfDiffuse"); dk.inputs["Color"].default_value = (0.008, 0.006, 0.005, 1)
            mx = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new(geo.outputs["Backfacing"], mx.inputs[0]); nt.links.new(src, mx.inputs[1]); nt.links.new(dk.outputs[0], mx.inputs[2])
            nt.links.new(mx.outputs[0], out.inputs["Surface"])


def palm(dv, M, side):
    """World position of the palm (the wrist bone's tail) after finish/settle."""
    return M @ Vector(dv.wrist_rest[side]) + Vector((0, 0, getattr(dv, "dz", 0.0)))


KDZ = 0.345        # how far kneel() + settle() lower the body (measured): world hand targets are lifted by this


def kmi(Mi):
    """World -> rig for a kneeling pose: the rig is posed standing-high and lowered by KDZ afterwards."""
    return Mi @ Matrix.Translation((0, 0, KDZ))


def leg_ik(h, s, ankle, pole):
    """Two-segment IK for a leg (thigh = upperleg01+02, shin = lowerleg01+02): ankle lands on `ankle` (rig space),
    knee bends toward `pole`."""
    b = h.arm.data.bones
    a = b[f"upperleg01.{s}"].length + b[f"upperleg02.{s}"].length
    c = b[f"lowerleg01.{s}"].length + b[f"lowerleg02.{s}"].length
    S = h.bone_head(f"upperleg01.{s}"); T = Vector(ankle)
    dv = T - S; d = min(max(dv.length, abs(a - c) + 1e-3), (a + c) * 0.999); u = dv.normalized()
    cosA = (a * a + d * d - c * c) / (2 * a * d); sinA = math.sqrt(max(0.0, 1 - cosA * cosA))
    p = Vector(pole); p = (p - u * p.dot(u)).normalized()
    E = S + u * (a * cosA) + p * (a * sinA)
    h.aim(f"upperleg01.{s}", E - S); h.aim(f"upperleg02.{s}", E - S)
    T2 = S + u * d
    h.aim(f"lowerleg01.{s}", T2 - E); h.aim(f"lowerleg02.{s}", T2 - E)


def b_len(h, s, part):
    b = h.arm.data.bones
    return b[f"{part}01.{s}"].length + b[f"{part}02.{s}"].length


def kneel(h, down="R", lean=10, drop=0.40, fwd=0.42, spread=0.05):
    """One knee on the floor (down side), the other foot planted ahead with its knee up. Rig space (faces -Y).
    The pelvis stays put; the legs fold as if the floor were `drop` higher, then settle() lowers the body."""
    up = "L" if down == "R" else "R"
    zf = drop                                                   # the kneeling floor, in rig space
    hd = h.bone_head(f"upperleg01.{down}"); hu = h.bone_head(f"upperleg01.{up}")
    sd = 1 if hd.x > 0 else -1; su = -sd
    # kneeling leg: thigh near vertical to a knee on the floor, shin back and rising a little to the ankle
    thigh = b_len(h, down, "upperleg"); shin = b_len(h, down, "lowerleg")
    kz = zf + 0.055
    ky = hd.y + math.sqrt(max(0.0, thigh ** 2 - (hd.z - kz) ** 2)) * 0.35
    ky = hd.y - math.sqrt(max(0.0, thigh ** 2 - (hd.z - kz) ** 2 - 0.0))
    knee = Vector((hd.x + sd * spread, ky, kz))
    ankle = knee + Vector((0, shin * math.cos(math.radians(14)), shin * math.sin(math.radians(14))))
    leg_ik(h, down, ankle, (0, -1, -0.2))
    h.aim(f"foot.{down}", Vector((0, 0.25, -1)))                # toes tucked under, on the floor
    leg_ik(h, up, Vector((hu.x + su * spread, hu.y - fwd, zf + 0.09)), (0, -1, 0.4))        # foot ahead, knee up
    h.aim(f"foot.{up}", Vector((0, -1, -0.12)))
    for b_, k in (("spine04", 0.3), ("spine03", 0.35), ("spine02", 0.35)):
        h.rot(b_, (1, 0, 0), lean * k)


# ----------------------------------------------------------------------------- camera / finish
def cam(loc, tgt, lens=35, fstop=None, focus=None, roll=0.0):
    CAMS.append(dict(loc=list(loc), tgt=list(tgt), lens=lens, fstop=fstop, focus=focus, roll=roll))
    if CAMDUMP:
        import json
        json.dump(CAMS[-1], open(CAMDUMP, "w")); sys.exit(0)
    if os.environ.get("NODOF"):
        fstop = None
    return C.camera(tuple(loc), tuple(tgt), lens=lens, fstop=fstop, focus=focus, roll=roll)


def finish(out, sat=1.0, exposure=0.0, bloom=0.3, clip_ok=()):
    GRADE["clip_ok"] = tuple(clip_ok) + ("floor",)
    if ANIM:
        GRADE.update(sat=sat, exposure=exposure, bloom=bloom); return
    run_dyn(T, None)
    if os.environ.get("CLIPONLY"):
        import clipcheck
        clipcheck.OUT = os.path.join(ROOT, "out", "clip")
        clipcheck.check(os.path.splitext(os.path.basename(out))[0], hand_ok=tuple(clip_ok) + ("floor",))
        sys.exit(0)
    C.finish(out, cine={"sat": sat, "exposure": exposure}, bloom=bloom)
    print("RENDERED", out, flush=True)
