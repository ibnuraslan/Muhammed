"""Romand film: core 3D kit (Seldom style v2). Reuses the approved look-test pipeline (thumbnails_am/scenes/style_yellow.py
on branch claude/thumbs-antwerp-mummy) and the antwerp_heist 3D library it depends on.

    ANTWERP3D = checkout of claude/antwerp-heist, folder antwerp_heist/3d   (lib/: sf, grade, ...; scenes/common.py)
    AM_SCENES = checkout of claude/thumbs-antwerp-mummy, folder thumbnails_am/scenes (crew.py)

Look: diorama slabs in a black void, world lit amber-gold, faceless pale-clay mannequins in clay clothes lit by a
cool-white key + warm rim (light-linked to the figures only), ONE red accent with its own tight spot, AgX + house grade
with a heavy vignette, mean luma ~12-14 (checked by luma())."""
import os, sys, math, random
import importlib.util as _iu
E = os.environ.get
HERE = os.path.dirname(os.path.abspath(__file__))
SCR = E("SCRATCH", "")
ANT = E("ANTWERP3D", os.path.join(SCR, "wt_antwerp", "antwerp_heist", "3d"))
AMS = E("AM_SCENES", os.path.join(SCR, "am", "thumbnails_am", "scenes"))
for p in (os.path.join(ANT, "lib"), AMS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
_spec = _iu.spec_from_file_location("film_common", os.path.join(ANT, "scenes", "common.py"))
C = _iu.module_from_spec(_spec); _spec.loader.exec_module(C)

AMBER = (1.0, 0.5, 0.1)          # world fill (shadows go brown-black)
GOLD = (1.0, 0.82, 0.0)
YEL = (0.78, 1.0, 0.0)           # #E3FF00 linear-ish
COOL = (0.92, 0.96, 1.0)
WARM_RIM = (1.0, 0.55, 0.12)
RED = (0.75, 0.02, 0.02)
STATE = dict(figs=[], accent=[], mats={})


# ----------------------------------------------------------------------------------------------------------- setup
def setup(res=(960, 540), spp=8, fps=24):
    C.reset()
    sc = C.render_setup(samples=spp, noise=0.05, res=res)
    sc.render.resolution_percentage = 100; sc.cycles.samples = spp
    sc.cycles.sample_clamp_indirect = 4.0; sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
    sc.render.fps = fps
    w = bpy.data.worlds.new("void"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs['Color'].default_value = (0, 0, 0, 1)
    STATE.update(figs=[], accent=[], mats={}); STATE.pop("pal", None)
    return sc


def world_color(rgb, strength=1.0):
    w = bpy.context.scene.world
    bg = w.node_tree.nodes["Background"]; bg.inputs['Color'].default_value = (*rgb, 1); bg.inputs['Strength'].default_value = strength


# ----------------------------------------------------------------------------------------------------------- materials
def mat(name, c, rough=0.6, metal=0.0, coat=0.0, emit=None, estr=0.0, alpha=1.0):
    key = (name, tuple(c), rough, metal, coat, emit, estr, alpha)
    if key in STATE["mats"]:
        return STATE["mats"][key]
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*c, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal; p.inputs['Coat Weight'].default_value = coat
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = estr
    if alpha < 1.0:
        p.inputs['Alpha'].default_value = alpha
    STATE["mats"][key] = m
    return m


def emission(name, c, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (*c, 1); e.inputs['Strength'].default_value = strength
    m.node_tree.links.new(e.outputs[0], N["Material Output"].inputs['Surface'])
    return m


def glass(name="glass", tint=(0.6, 0.6, 0.55), rough=0.05):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*tint, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['IOR'].default_value = 1.45
    return m


def M():
    """The shared palette: the world is built in neutral greys; the yellow comes from the light."""
    if "pal" in STATE:
        return STATE["pal"]
    wet = mat("wet_floor", (0.1, 0.1, 0.09), 0.3, coat=1.0)
    N_ = wet.node_tree.nodes; L_ = wet.node_tree.links; pw = N_["Principled BSDF"]
    nz = N_.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 6
    mr = N_.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.45; mr.inputs['From Max'].default_value = 0.6
    mr.inputs['To Min'].default_value = 0.02; mr.inputs['To Max'].default_value = 0.5
    L_.new(nz.outputs['Fac'], mr.inputs['Value']); L_.new(mr.outputs[0], pw.inputs['Roughness']); L_.new(mr.outputs[0], pw.inputs['Coat Roughness'])
    P = dict(
        grey=mat("set_grey", (0.32, 0.31, 0.29), 0.7), light=mat("set_light", (0.5, 0.49, 0.46), 0.7),
        steel=mat("set_steel", (0.4, 0.39, 0.36), 0.35, 0.6), dark=mat("set_dark", (0.02, 0.02, 0.018), 0.8),
        wet=wet, wood=mat("wood", (0.22, 0.19, 0.15), 0.55), soil=mat("soil", (0.06, 0.055, 0.045), 0.9),
        foliage=mat("foliage", (0.09, 0.085, 0.06), 0.85), bark=mat("bark", (0.07, 0.06, 0.05), 0.9),
        snow=mat("snow", (0.75, 0.74, 0.7), 0.5), asphalt=mat("asphalt", (0.05, 0.05, 0.048), 0.35, coat=0.6),
        carpaint=mat("car_paint", (0.2, 0.2, 0.19), 0.25, 0.3, coat=1.0), chrome=mat("chrome", (0.6, 0.6, 0.58), 0.15, 1.0),
        rubber=mat("rubber", (0.02, 0.02, 0.02), 0.8), glass=glass("glass", (0.3, 0.3, 0.28), 0.02),
        cloth=mat("upholstery", (0.12, 0.11, 0.1), 0.9), paper=mat("paper", (0.7, 0.69, 0.65), 0.8),
        clay=mat("mannequin", (0.86, 0.85, 0.81), 0.72),
        jacket=mat("jacket", (0.8, 0.79, 0.75), 0.8), trousers=mat("trousers", (0.74, 0.73, 0.7), 0.8),
        gloves=mat("gloves", (0.6, 0.59, 0.57), 0.6), coat=mat("coat", (0.7, 0.69, 0.66), 0.85),
        red=mat("accent_red", RED, 0.45, coat=0.4),
        win=emission("window_warm", (1.0, 0.62, 0.22), 6.0), lamp=emission("lamp", (1.0, 0.6, 0.18), 25.0),
        head=emission("headlight", (1.0, 0.92, 0.75), 40.0), tail=emission("taillight", (0.9, 0.25, 0.04), 4.0),
        tv=emission("tv_glow", (0.55, 0.75, 1.0), 8.0), candle=emission("candle", (1.0, 0.6, 0.2), 30.0),
        slab=mat("explainer_slab", (0.11, 0.085, 0.055), 0.6), pawn=mat("pawn", (0.8, 0.79, 0.76), 0.6),
        hot=mat("seldom_yellow", (0.78, 1.0, 0.0), 0.4, emit=(0.78, 1.0, 0.0), estr=1.5),
    )
    STATE["pal"] = P
    return P


def fade_to_void(mats, center=(0, 0), r0=3.0, r1=5.0):
    """Darken these set materials radially away from center (x, y) so the slab's edges fall off into black."""
    for m_ in mats:
        N2 = m_.node_tree.nodes; L2 = m_.node_tree.links; p2 = N2.get("Principled BSDF")
        if p2 is None or N2.get("void_fade"):
            continue
        geo = N2.new("ShaderNodeNewGeometry"); sep = N2.new("ShaderNodeSeparateXYZ"); L2.new(geo.outputs['Position'], sep.inputs[0])
        ax = N2.new("ShaderNodeMath"); ax.operation = 'SUBTRACT'; ax.inputs[1].default_value = center[0]; L2.new(sep.outputs['X'], ax.inputs[0])
        ay = N2.new("ShaderNodeMath"); ay.operation = 'SUBTRACT'; ay.inputs[1].default_value = center[1]; L2.new(sep.outputs['Y'], ay.inputs[0])
        cx = N2.new("ShaderNodeCombineXYZ"); L2.new(ax.outputs[0], cx.inputs[0]); L2.new(ay.outputs[0], cx.inputs[1])
        ln2 = N2.new("ShaderNodeVectorMath"); ln2.operation = 'LENGTH'; L2.new(cx.outputs[0], ln2.inputs[0])
        fr = N2.new("ShaderNodeMapRange"); fr.name = "void_fade"
        fr.inputs['From Min'].default_value = r0; fr.inputs['From Max'].default_value = r1
        fr.inputs['To Min'].default_value = 1.0; fr.inputs['To Max'].default_value = 0.0; fr.interpolation_type = 'SMOOTHSTEP'
        L2.new(ln2.outputs['Value'], fr.inputs['Value'])
        src = p2.inputs['Base Color'].links[0].from_socket if p2.inputs['Base Color'].links else None
        mx2 = N2.new("ShaderNodeMix"); mx2.data_type = 'RGBA'; mx2.blend_type = 'MULTIPLY'
        inv = N2.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L2.new(fr.outputs[0], inv.inputs[1])
        L2.new(inv.outputs[0], mx2.inputs['Factor'])
        if src is not None:
            L2.new(src, mx2.inputs[6])
        else:
            mx2.inputs[6].default_value = p2.inputs['Base Color'].default_value
        mx2.inputs[7].default_value = (0, 0, 0, 1)
        L2.new(mx2.outputs[2], p2.inputs['Base Color'])
        sp_ = N2.new("ShaderNodeMath"); sp_.operation = 'MULTIPLY'; L2.new(fr.outputs[0], sp_.inputs[0]); sp_.inputs[1].default_value = 0.5
        L2.new(sp_.outputs[0], p2.inputs['Specular IOR Level'])


# ----------------------------------------------------------------------------------------------------------- geometry
def box(name, c, size, m, rot=(0, 0, 0), bevel=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    if m is not None:
        o.data.materials.append(m)
    if parent is not None:
        o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


def cyl(name, p0, p1, r, m, verts=24, caps=True):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p0 + p1) / 2,
                                        end_fill_type='NGON' if caps else 'NOTHING')
    o = bpy.context.active_object; o.name = name
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    if m is not None:
        o.data.materials.append(m)
    return o


def sphere(name, c, r, m, scale=(1, 1, 1), seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=c, segments=seg, ring_count=seg // 2)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    for p in o.data.polygons:
        p.use_smooth = True
    if m is not None:
        o.data.materials.append(m)
    return o


def cone(name, c, r1, r2, h, m, verts=24, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=h, location=c, rotation=rot)
    o = bpy.context.active_object; o.name = name
    if m is not None:
        o.data.materials.append(m)
    return o


def empty(name, loc=(0, 0, 0), rz=0.0):
    o = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler.z = rz
    return o


def group(name, objs, loc=(0, 0, 0), rz=0.0):
    """Parent objs (built around the origin) to a new empty, then move/turn the empty."""
    g = empty(name)
    for o in objs:
        if o.parent is None:
            o.parent = g
    g.location = loc; g.rotation_euler.z = rz
    bpy.context.view_layer.update()
    return g


def set_mat(objs, m):
    for o in objs:
        if o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(m)


# ----------------------------------------------------------------------------------------------------------- figures
ERIC = "a46bc9f67aaa415bb4f3241eef900e7f"


def _rot(arm, bone, axis, deg):
    pb = arm.pose.bones[bone]
    bpy.context.view_layer.update()
    mw = arm.matrix_world; head_w = mw @ pb.head
    R = Matrix.Translation(head_w) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-head_w)
    pb.matrix = mw.inverted() @ R @ mw @ pb.matrix
    bpy.context.view_layer.update()


# Poses: (bone, axis in CHARACTER space (faces -Y, left = +X), degrees), applied in order on the A-pose rest.
ARMS_DOWN = [("upperarm_l_024", Y, 38), ("upperarm_r_049", Y, -38), ("lowerarm_l_025", X, -10), ("lowerarm_r_050", X, -10)]
POSES = {
    "stand": ARMS_DOWN + [("neck_06", X, 4)],
    "stand_bow": ARMS_DOWN + [("spine_02_04", X, 6), ("neck_06", X, 22), ("head_07", X, 10)],
    "stand_hug": [("upperarm_l_024", Y, 30), ("upperarm_r_049", Y, -30), ("upperarm_l_024", X, -25), ("upperarm_r_049", X, -25),
                  ("lowerarm_l_025", Z, -70), ("lowerarm_r_050", Z, 70), ("neck_06", X, 18)],
    "walk": [("upperleg_l_074", X, -24), ("lowerleg_l_075", X, 8), ("foot_l_076", X, 10),
             ("upperleg_r_081", X, 16), ("lowerleg_r_082", X, 22), ("foot_r_083", X, -8),
             ("upperarm_l_024", Y, 40), ("upperarm_r_049", Y, -40), ("upperarm_l_024", X, 14), ("upperarm_r_049", X, -16),
             ("lowerarm_l_025", X, -8), ("lowerarm_r_050", X, -20), ("spine_01_03", X, 3)],
    "walk_carry": [("upperleg_l_074", X, -24), ("lowerleg_l_075", X, 8), ("foot_l_076", X, 10),
                   ("upperleg_r_081", X, 16), ("lowerleg_r_082", X, 22), ("foot_r_083", X, -8),
                   ("upperarm_l_024", Y, 40), ("upperarm_r_049", Y, -36), ("upperarm_l_024", X, 14),
                   ("lowerarm_l_025", X, -8), ("lowerarm_r_050", X, -4), ("spine_01_03", X, 3)],
    "sit": [("upperleg_l_074", X, -88), ("upperleg_r_081", X, -88), ("lowerleg_l_075", X, 88), ("lowerleg_r_082", X, 88),
            ("upperarm_l_024", Y, 40), ("upperarm_r_049", Y, -40), ("upperarm_l_024", X, -12), ("upperarm_r_049", X, -12),
            ("lowerarm_l_025", X, -62), ("lowerarm_r_050", X, -62), ("lowerarm_l_025", Z, -18), ("lowerarm_r_050", Z, 18),
            ("spine_01_03", X, -4)],
    "sit_table": [("upperleg_l_074", X, -88), ("upperleg_r_081", X, -88), ("lowerleg_l_075", X, 88), ("lowerleg_r_082", X, 88),
                  ("upperarm_l_024", Y, 40), ("upperarm_r_049", Y, -40), ("upperarm_l_024", X, -22), ("upperarm_r_049", X, -22),
                  ("lowerarm_l_025", X, -70), ("lowerarm_r_050", X, -70), ("lowerarm_l_025", Z, -12), ("lowerarm_r_050", Z, 12),
                  ("spine_01_03", X, 6)],
    "drive": [("upperleg_l_074", X, -78), ("upperleg_r_081", X, -78), ("lowerleg_l_075", X, 62), ("lowerleg_r_082", X, 62),
              ("upperarm_l_024", Y, 36), ("upperarm_r_049", Y, -36), ("upperarm_l_024", X, -30), ("upperarm_r_049", X, -30),
              ("lowerarm_l_025", X, -45), ("lowerarm_r_050", X, -45), ("spine_01_03", X, -6)],
    "car_drive": [("upperleg_l_074", X, -96), ("upperleg_r_081", X, -96), ("lowerleg_l_075", X, 42), ("lowerleg_r_082", X, 42),
                  ("foot_l_076", X, 20), ("foot_r_083", X, 20),
                  ("upperarm_l_024", Y, 36), ("upperarm_r_049", Y, -36), ("upperarm_l_024", X, -30), ("upperarm_r_049", X, -30),
                  ("lowerarm_l_025", X, -45), ("lowerarm_r_050", X, -45), ("spine_01_03", X, -6)],
    "car_sit": [("upperleg_l_074", X, -96), ("upperleg_r_081", X, -96), ("lowerleg_l_075", X, 42), ("lowerleg_r_082", X, 42),
                ("foot_l_076", X, 20), ("foot_r_083", X, 20),
                ("upperarm_l_024", Y, 40), ("upperarm_r_049", Y, -40), ("upperarm_l_024", X, -12), ("upperarm_r_049", X, -12),
                ("lowerarm_l_025", X, -62), ("lowerarm_r_050", X, -62), ("lowerarm_l_025", Z, -18), ("lowerarm_r_050", Z, 18),
                ("spine_01_03", X, -4)],
    "boot": [("spine_01_03", X, 22), ("spine_02_04", X, 14), ("spine_03_05", X, 6), ("neck_06", X, 10),
             ("upperleg_l_074", X, -10), ("upperleg_r_081", X, 4), ("lowerleg_l_075", X, 12), ("lowerleg_r_082", X, 6),
             ("upperarm_l_024", Y, 30), ("upperarm_r_049", Y, -30), ("upperarm_l_024", X, -40), ("upperarm_r_049", X, -55),
             ("lowerarm_l_025", X, -20), ("lowerarm_r_050", X, -20)],
}
KINDS = {  # height scale, clothes, skirt
    "man": dict(s=1.0, skirt=False), "woman": dict(s=0.93, skirt=True), "child": dict(s=0.6, skirt=False, headk=1.18),
    "girl": dict(s=0.62, skirt=True, headk=1.18), "old_man": dict(s=0.97, skirt=False), "old_woman": dict(s=0.9, skirt=True),
}


def _template():
    before = set(bpy.data.objects)
    import sf
    bpy.ops.import_scene.gltf(filepath=sf.fetch(ERIC))
    new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.name.startswith("Icosphere")]:
        new.remove(o); bpy.data.objects.remove(o)
    return new


def person(name, loc=(0, 0, 0), heading=0.0, pose="stand", kind="man", extra=(), seed=0, jitter=2.0, clothes=True, hip_at=None):
    """A faceless pale-clay mannequin in pale-clay clothes. heading: degrees; 0 = facing -Y. Feet on loc.z.
    Returns dict(pivot, arm, body, parts)."""
    rng = random.Random(seed)
    K = KINDS[kind]
    objs = _template()
    arm = [o for o in objs if o.type == 'ARMATURE'][0]
    root = [o for o in objs if o.parent is None and o.name.startswith("Sketchfab_model")][0]
    ms = [o for o in objs if o.type == 'MESH']
    P = M()
    for o in ms:
        o.data.materials.clear(); o.data.materials.append(P["clay"])
    for (b, ax, d) in list(POSES[pose]) + list(extra):
        _rot(arm, b, ax, d + rng.uniform(-jitter, jitter))
    bpy.context.view_layer.update()
    root.scale = root.scale * (1.82 * K["s"] / 186.0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    pts = []
    for o in ms:
        oe = o.evaluated_get(dg); me = oe.to_mesh()
        pts.append(np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])); oe.to_mesh_clear()
    pts = np.concatenate(pts)
    hip = arm.matrix_world @ arm.pose.bones["hip_02"].head
    root.location -= Vector((hip.x, hip.y, pts[:, 2].min()))
    piv = empty(name); root.parent = piv
    parts = list(ms)
    if clothes:
        CL = dict(jacket=P["jacket"], trousers=P["trousers"], gloves=P["clay"])
        for cl in _add_clothes(ms[0], CL, name):
            cl.parent = ms[0].parent; cl.matrix_parent_inverse = ms[0].matrix_parent_inverse.copy(); parts.append(cl)
    bpy.context.view_layer.update()
    # blank egg head on the head bone (no face, ever)
    hb = arm.pose.bones["head_07"]; base = arm.matrix_world @ hb.head; top = arm.matrix_world @ arm.pose.bones["head_end_08"].head
    up = (top - base).normalized(); fwd_ = (arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
    hk = K.get("headk", 1.0); hs = 0.1 * K["s"] * hk
    hd = sphere(name + "_blankhead", base + (top - base) * 0.5 + fwd_ * 0.012 * K["s"], hs, P["clay"], (0.98, 1.12, 1.22), seg=48)
    hd.rotation_euler = up.to_track_quat('Z', 'Y').to_euler()
    mw_ = hd.matrix_world.copy(); hd.parent = arm; hd.parent_type = 'BONE'; hd.parent_bone = "head_07"
    bpy.context.view_layer.update(); hd.matrix_world = mw_; parts.append(hd)
    if K["skirt"] and pose not in ("sit", "sit_table", "drive", "car_drive", "car_sit"):
        hz = (arm.matrix_world @ arm.pose.bones["hip_02"].head).z
        sk = cone(name + "_skirt", (0, 0, hz - 0.3 * K["s"]), 0.27 * K["s"], 0.17 * K["s"], 0.62 * K["s"], P["coat"], verts=32)
        sk.modifiers.new("sol", "SOLIDIFY").thickness = 0.01
        for p_ in sk.data.polygons:
            p_.use_smooth = True
        sk.data.polygons.foreach_set("use_smooth", [True] * len(sk.data.polygons))
        bm_del_caps(sk)
        mw_ = sk.matrix_world.copy(); sk.parent = arm; sk.parent_type = 'BONE'; sk.parent_bone = "hip_02"
        bpy.context.view_layer.update(); sk.matrix_world = mw_; parts.append(sk)
    piv.location = loc; piv.rotation_euler.z = math.radians(heading)
    bpy.context.view_layer.update()
    if hip_at is not None:      # seat the figure: move so its hip joint sits exactly on hip_at
        hw = arm.matrix_world @ arm.pose.bones["hip_02"].head
        piv.location += Vector(hip_at) - hw
        bpy.context.view_layer.update()
    STATE["figs"].append(piv)
    return dict(pivot=piv, arm=arm, body=ms[0], parts=parts)


def bm_del_caps(o):
    import bmesh
    b = bmesh.new(); b.from_mesh(o.data); b.faces.ensure_lookup_table()
    bmesh.ops.delete(b, geom=[f for f in b.faces if len(f.verts) > 4], context='FACES'); b.to_mesh(o.data); b.free()


def _add_clothes(body, mats, name):
    import crew
    return crew.add_clothes(body, mats, name=name)


def bone_world(fig, bone):
    return fig["arm"].matrix_world @ fig["arm"].pose.bones[bone].head


def attach(obj, fig, bone):
    """Parent obj to a bone of fig, keeping its world transform (props ride on hands)."""
    mw = obj.matrix_world.copy(); obj.parent = fig["arm"]; obj.parent_type = 'BONE'; obj.parent_bone = bone
    bpy.context.view_layer.update(); obj.matrix_world = mw


# ----------------------------------------------------------------------------------------------------------- light
def area(name, loc, target, size, energy, color=(1, 1, 1), size_y=None):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = color
    if size_y:
        l.shape = 'RECTANGLE'; l.size = size; l.size_y = size_y
    else:
        l.size = size
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def spot(name, loc, target, energy, color, size_deg=30, blend=0.4, soft=0.1):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color; l.spot_size = math.radians(size_deg)
    l.spot_blend = blend; l.shadow_soft_size = soft
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def point(name, loc, energy, color, soft=0.1):
    l = bpy.data.lights.new(name, 'POINT'); l.energy = energy; l.color = color; l.shadow_soft_size = soft
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    return o


def look(center=(0, 0, 0), extent=8.0, fill=120.0, moon=150.0, key=300.0, rim=260.0, key_from=(-3, -5, 4.5),
         rim_from=(1.5, 1.5, 2.2), fig_target=None):
    """The amber world light (overhead fill + low moon), plus the figures' cool key and warm rim (light-linked)."""
    c = Vector(center)
    k = max(1.0, (extent / 7.0) ** 2)     # same irradiance on bigger sets (energies are tuned on the 7 m vault test)
    fill, moon = fill * k, moon * k
    area("fill", c + Vector((0, 0, extent * 0.9)), c, extent, fill, AMBER, size_y=extent * 1.2)
    area("moon", c + Vector((-extent * 0.5, -extent * 0.75, extent * 0.6)), c + Vector((0, 0, 0.5)), extent * 0.4, moon, AMBER)
    if STATE["figs"]:
        figc = bpy.data.collections.get("figures") or bpy.data.collections.new("figures")
        if figc.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(figc)
        for pv in STATE["figs"]:
            for o in [pv] + list(pv.children_recursive):
                if o.type == 'MESH' and figc not in o.users_collection:
                    figc.objects.link(o)
        ft = Vector(fig_target) if fig_target else c + Vector((0, 0, 0.9))
        fk = area("fig_key", ft + Vector(key_from), ft, 2.0, key, COOL); fk.light_linking.receiver_collection = figc
        fr = area("fig_rim", ft + Vector(rim_from), ft, 1.0, rim, WARM_RIM); fr.light_linking.receiver_collection = figc


def accent(obj_or_loc, energy=300.0, size_deg=16, offset=(-0.6, -1.2, 2.6), color=(1.0, 0.15, 0.1)):
    at = obj_or_loc.matrix_world.translation.copy() if hasattr(obj_or_loc, "matrix_world") else Vector(obj_or_loc)
    return spot("accent", at + Vector(offset), at, energy, color, size_deg)


# ----------------------------------------------------------------------------------------------------------- camera / grade / render
def camera(loc, target, lens=35, fstop=None, focus=None, roll=0.0):
    cam = C.camera(Vector(loc), Vector(target), lens=lens, roll=roll)
    if fstop:
        cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop
        cam.data.dof.focus_distance = focus if focus else (Vector(target) - Vector(loc)).length
    return cam


def orbit_cam(target, az_deg, el_deg, dist, lens=35, **kw):
    t = Vector(target); az, el = math.radians(az_deg), math.radians(el_deg)
    loc = t + Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * dist
    return camera(loc, t, lens=lens, **kw)


def grade(sc=None, expo=-2.6, vig=0.85, bloom=0.25, contrast=1.15, sat=1.1):
    import grade as G
    sc = sc or bpy.context.scene
    G.add_grade(sc, bloom=bloom, vignette=vig, look="cinematic",
                cine={"exposure": expo, "contrast": contrast, "sat": sat, "knee": 0.6, "span": 1.4})


def set_exposure(expo):
    sc = bpy.context.scene
    nt = sc.compositing_node_group if hasattr(sc, "compositing_node_group") else None
    sc.view_settings.exposure = expo + 2.6   # fine trim on top of the grade (the grade carries -2.6)


def render(path):
    sc = bpy.context.scene
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
    bpy.ops.render.render(write_still=True)
    return path


def luma(path):
    im = bpy.data.images.load(path, check_existing=False)
    a = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
    bpy.data.images.remove(im)
    # byte PNGs come back as their stored (sRGB-encoded) values: Rec.709 luma on those, like ffmpeg/PIL
    y = (0.2126 * a[:, 0] + 0.7152 * a[:, 1] + 0.0722 * a[:, 2]) * 255
    return float(y.mean())


def render_to_luma(path, target=13.0, lo=11.0, hi=15.0, tries=4, max_ev=5.0):
    """Find the view exposure that puts the mean luma in the house range on a quarter-res 4-spp probe, then render
    the frame once at full settings and report its luma."""
    sc = bpy.context.scene
    pct, spp = sc.render.resolution_percentage, sc.cycles.samples
    sc.render.resolution_percentage = 25; sc.cycles.samples = 4
    probe = path.replace(".png", "_probe.png")
    for _ in range(tries):
        render(probe); L = luma(probe)
        if lo <= L <= hi:
            break
        sc.view_settings.exposure += max(-3.0, min(3.0, math.log2(target / max(L, 0.15)) * 1.1))
        sc.view_settings.exposure = min(sc.view_settings.exposure, max_ev)
    try:
        os.remove(probe)
    except OSError:
        pass
    sc.render.resolution_percentage = pct; sc.cycles.samples = spp
    render(path); L = luma(path)
    if not (lo - 1 <= L <= hi + 1) and sc.view_settings.exposure < max_ev:   # the probe misjudged: one corrective final
        sc.view_settings.exposure = min(max_ev, sc.view_settings.exposure + math.log2(target / max(L, 0.15)))
        render(path); L = luma(path)
    print(f"LUMA {os.path.basename(path)} {L:.1f} (view exposure {sc.view_settings.exposure:+.2f})")
    return L
