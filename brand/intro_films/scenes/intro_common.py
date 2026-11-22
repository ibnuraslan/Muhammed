"""Shared helpers for the Seldom intro films (5-8): logo texture, materials, practical lights, haze."""
import os, math, random
import bpy
from mathutils import Vector, Matrix
import common as C
import ship, ph

LOGO = os.path.join(C.HERE, "..", "assets", "seldom_logo_tex.png")   # official art (brand/seldom_logo_original.webp), cropped
LOGO_AR = 1338 / 381
SHOT = int(os.environ.get("SHOT", "1"))
OUTDIR = os.environ.get("OUTDIR", os.path.join(C.HERE, "..", "out", "intros"))


def setup(spp=48, noise=0.03):
    sc = C.render_setup(samples=int(os.environ.get("SPP", str(spp))), noise=noise, bounces=8, res=(1280, 720))
    sc.render.fps = 24
    sc.cycles.volume_bounces = 0
    return sc


def tex(aid, scale=1.0, tint=None, name=None, fallback=(0.3, 0.3, 0.3), rough=0.7):
    try:
        return ph.texture(aid, scale=scale, tint=tint, name=name or aid)
    except Exception as e:
        print("TEXTURE FALLBACK", aid, e)
        m = bpy.data.materials.new(name or aid); m.use_nodes = True
        p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (*fallback, 1); p.inputs["Roughness"].default_value = rough
        return m


def principled(name, color, rough=0.5, metal=0.0, emit=None, estr=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color[:3], 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*emit[:3], 1); p.inputs["Emission Strength"].default_value = estr
    return m


def grunge(m, scale=12.0, amount=0.35, dark=(0.25, 0.2, 0.15), rough_range=None):
    """Multiply the base colour by a dirt noise, optional roughness variation."""
    nt = m.node_tree; N = nt.nodes; L = nt.links; p = N["Principled BSDF"]
    src = p.inputs["Base Color"].links[0].from_socket if p.inputs["Base Color"].links else None
    n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 10
    r = N.new("ShaderNodeValToRGB"); r.color_ramp.elements[0].position = 0.35; r.color_ramp.elements[1].position = 0.75
    r.color_ramp.elements[0].color = (*dark, 1); r.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(n.outputs["Fac"], r.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = amount
    if src: L.new(src, mx.inputs[6])
    else: mx.inputs[6].default_value = p.inputs["Base Color"].default_value
    L.new(r.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], p.inputs["Base Color"])
    if rough_range:
        mr = N.new("ShaderNodeMapRange"); mr.inputs[3].default_value, mr.inputs[4].default_value = rough_range
        L.new(n.outputs["Fac"], mr.inputs[0]); L.new(mr.outputs[0], p.inputs["Roughness"])
    return m


def logo_layer(m, uv_name=None, kind="paint", wear=0.15, over=None):
    """Lay the official logo art over a material's base colour through the object's UVs (0..1 = the art).
    kind: paint (matte), enamel (glossy, coat), print (ink soaks: matte, slightly darker). wear: chipped/faded patches."""
    nt = m.node_tree; N = nt.nodes; L = nt.links; p = N["Principled BSDF"]
    uv = N.new("ShaderNodeUVMap")
    if uv_name: uv.uv_map = uv_name
    im = N.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(LOGO, check_existing=True); im.extension = 'CLIP'
    im.interpolation = 'Cubic'
    L.new(uv.outputs[0], im.inputs[0])
    base = p.inputs["Base Color"].links[0].from_socket if p.inputs["Base Color"].links else None
    a = im.outputs["Alpha"]
    if wear > 0:
        wn = N.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 18; wn.inputs["Detail"].default_value = 12
        wn.inputs["Roughness"].default_value = 0.75
        wr = N.new("ShaderNodeMapRange"); wr.inputs[1].default_value = 0.30 + 0.25 * wear; wr.inputs[2].default_value = 0.34 + 0.25 * wear
        L.new(wn.outputs["Fac"], wr.inputs[0])
        mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; L.new(a, mm.inputs[0]); L.new(wr.outputs[0], mm.inputs[1]); a = mm.outputs[0]
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    L.new(a, mx.inputs[0])
    if base: L.new(base, mx.inputs[6])
    else: mx.inputs[6].default_value = p.inputs["Base Color"].default_value
    col = im.outputs["Color"]
    if kind == "print":
        mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1.0
        mul.inputs[6].default_value = (0.92, 0.9, 0.86, 1); L.new(col, mul.inputs[7]); col = mul.outputs[2]
    L.new(col, mx.inputs[7]); L.new(mx.outputs[2], p.inputs["Base Color"])
    if kind in ("enamel", "paint"):
        base_r = p.inputs["Roughness"].links[0].from_socket if p.inputs["Roughness"].links else None
        rm = N.new("ShaderNodeMix"); rm.data_type = 'FLOAT'; L.new(a, rm.inputs[0])
        if base_r: L.new(base_r, rm.inputs[2])
        else: rm.inputs[2].default_value = p.inputs["Roughness"].default_value
        rm.inputs[3].default_value = 0.12 if kind == "enamel" else 0.55
        L.new(rm.outputs[0], p.inputs["Roughness"])
        if kind == "enamel":
            L.new(a, p.inputs["Coat Weight"]); p.inputs["Coat Roughness"].default_value = 0.05
        # enamel and paint are dielectric layers: no metal under the art
        mm_ = N.new("ShaderNodeMix"); mm_.data_type = 'FLOAT'; L.new(a, mm_.inputs[0])
        mm_.inputs[2].default_value = p.inputs["Metallic"].default_value; mm_.inputs[3].default_value = 0.0
        L.new(mm_.outputs[0], p.inputs["Metallic"])
    return im


def logo_card(name, center, width, mat, rot=(0, 0, 0), thick=0.002, segments=1):
    """A flat card/plate whose top face UV spans the logo art exactly (aspect kept)."""
    h = width / LOGO_AR
    bpy.ops.mesh.primitive_plane_add(size=1, location=center, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (width, h, 1)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    if thick:
        s = o.modifiers.new("thick", 'SOLIDIFY'); s.thickness = thick; s.offset = -1
    return o


def point(name, loc, energy, color=(1, 0.8, 0.55), size=0.02):
    l = bpy.data.lights.new(name, 'POINT'); l.energy = energy; l.color = color; l.shadow_soft_size = size
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    return o


def spot(name, loc, target, energy, color=(1, 0.9, 0.8), size_deg=40, blend=0.3, radius=0.02):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color; l.spot_size = math.radians(size_deg)
    l.spot_blend = blend; l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def area(name, loc, target, energy, color=(1, 1, 1), size=1.0):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = color; l.size = size
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    o.visible_camera = False
    return o


def bulb(name, loc, energy=40, color=(1.0, 0.72, 0.42), cord=1.0):
    """Bare filament bulb on a cord: glass + glowing filament + point light."""
    g = principled(name + "_glass", (1, 0.9, 0.8), 0.05, emit=(1.0, 0.75, 0.45), estr=25)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=loc); b = bpy.context.active_object; b.scale = (1, 1, 1.25)
    b.data.materials.append(g); bpy.ops.object.shade_smooth()
    blk = principled(name + "_cord", (0.02, 0.02, 0.02), 0.6)
    ship.cyl(name + "_cap", Vector(loc) + Vector((0, 0, 0.035)), Vector(loc) + Vector((0, 0, 0.075)), 0.016, mat=blk, verts=12)
    ship.cyl(name + "_cord", Vector(loc) + Vector((0, 0, 0.075)), Vector(loc) + Vector((0, 0, cord)), 0.004, mat=blk, verts=6)
    b.visible_shadow = False
    return point(name + "_L", loc, energy, color, size=0.03)


def haze(center, size, density=0.02, color=(0.85, 0.85, 0.9), aniso=0.4, noise_scale=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center); o = bpy.context.active_object; o.name = "haze"; o.scale = size
    m = bpy.data.materials.new("haze"); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled"); v.inputs["Color"].default_value = (*color, 1)
    v.inputs["Density"].default_value = density; v.inputs["Anisotropy"].default_value = aniso
    if noise_scale:
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = noise_scale; n.inputs["Detail"].default_value = 3
        r = nt.nodes.new("ShaderNodeMapRange"); r.inputs[1].default_value = 0.3; r.inputs[2].default_value = 0.75; r.inputs[4].default_value = density * 2
        nt.links.new(n.outputs["Fac"], r.inputs[0]); nt.links.new(r.outputs[0], v.inputs["Density"])
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    o.data.materials.append(m); o.visible_shadow = False
    return o


def yaw(deg, loc):
    """Placement matrix for a rig (rest faces -Y): rotate about Z by deg, then translate."""
    return Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(deg), 4, 'Z')


def facing(dir_xy):
    """Degrees to rotate a -Y facing rig so it faces dir_xy."""
    return math.degrees(math.atan2(dir_xy[0], -dir_xy[1]))


def out(tag):
    return os.path.join(OUTDIR, f"{tag}.png")


# ----------------------------------------------------------------------------- shared poses / props for the intros
def kneel(h, down="R", lean=24):
    """Genuflect: the `down` knee on the ground with the shin flat behind, the other foot planted ahead.
    Returns the z offset to add to the rig placement so the knee and the planted sole touch z=0."""
    import human as H
    up = "L" if down == "R" else "R"; sd = H.SIDE[down]; su = H.SIDE[up]
    for b in ("upperleg01", "upperleg02"):
        h.aim(f"{b}.{down}", (0.06 * sd, -0.12, -1))
        h.aim(f"{b}.{up}", (0.14 * su, -1, -0.08))
    for b in ("lowerleg01", "lowerleg02"):
        h.aim(f"{b}.{down}", (0.02 * sd, 1, -0.06))
        h.aim(f"{b}.{up}", (0.03 * su, 0.05, -1))
    h.aim(f"foot.{down}", (0.0, 0.25, -1)); h.aim(f"foot.{up}", (0.04 * su, -1, -0.25))
    for b, k in (("spine05", 0.15), ("spine04", 0.25), ("spine03", 0.3), ("spine02", 0.3)):
        h.rot(b, (1, 0, 0), lean * k)
    bpy.context.view_layer.update()
    knee = h.bone_head(f"lowerleg01.{down}"); ankle = h.bone_head(f"foot.{up}")
    return -min(knee.z - 0.055, ankle.z - 0.085)


def glove_hands(person, color=(0.035, 0.03, 0.028), rough=0.65):
    """Tight leather/wool gloves: the hand faces of the body take a glove material (no extra shell, no clipping)."""
    import deveau as D
    h = person.h; me = h.body.data
    w = D._w(h, D.HAND)
    import numpy as np
    m = principled("glove", color, rough)
    me.materials.append(m); gi = len(me.materials) - 1
    for p in me.polygons:
        if np.mean([w[v] for v in p.vertices]) > 0.45:
            p.material_index = gi
    return m


def streaks(name, center, size, n, wind=(1.0, 0.2, -0.35), length=(0.03, 0.09), radius=0.0016, seed=1, mat=None):
    """Blowing snow (or dust) as one mesh of thin streaks along the wind (reads like a 1/48 s exposure)."""
    import numpy as np
    r = random.Random(seed)
    wv = Vector(wind).normalized()
    side = wv.cross(Vector((0, 0, 1))); side = side.normalized() if side.length > 1e-4 else Vector((1, 0, 0))
    up = side.cross(wv).normalized()
    V = []; F = []
    for i in range(n):
        c = Vector((center[0] + r.uniform(-size[0], size[0]) / 2, center[1] + r.uniform(-size[1], size[1]) / 2,
                    center[2] + r.uniform(-size[2], size[2]) / 2))
        L = r.uniform(*length); rr = radius * r.uniform(0.6, 1.4)
        a = c - wv * L / 2; b = c + wv * L / 2; k = len(V)
        V += [a, c + side * rr, c + up * rr, c - side * rr, c - up * rr, b]
        F += [[k, k + 1, k + 2], [k, k + 2, k + 3], [k, k + 3, k + 4], [k, k + 4, k + 1],
              [k + 5, k + 2, k + 1], [k + 5, k + 3, k + 2], [k + 5, k + 4, k + 3], [k + 5, k + 1, k + 4]]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in V], [], F); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat or principled(name + "_m", (0.9, 0.93, 1.0), 0.4))
    o.visible_shadow = False
    return o


def head_frame(h):
    """(forehead point, face-forward direction) in the rig's own frame; call after posing, before finish()."""
    pb = h.arm.pose.bones["head"]
    R = pb.matrix.to_3x3() @ h.arm.data.bones["head"].matrix_local.to_3x3().inverted()
    hh = Vector(h.bone_head("head")); ht = Vector(h.bone_tail("head"))
    fwd = (R @ Vector((0, -1, 0))).normalized()
    return hh.lerp(ht, 0.42) + fwd * 0.1, fwd
