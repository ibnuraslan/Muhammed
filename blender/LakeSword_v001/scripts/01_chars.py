"""LakeSword characters: MPFB2 rigs re-used from our own packages (the MakeHuman asset server is down), re-dressed.
blender -b --factory-startup --python 01_chars.py -- <repo_blender_dir> <out.blend>
Girl   = BelugaRescue "SpecC" (blonde ponytail, pink-purple T-shirt, pale grey-blue trousers, pink shoes)
Dad    = EscapeArtist "Father" (grey T-shirt, navy jeans)
ExpM   = EscapeArtist "Judge" (charcoal suit)       ExpF = EscapeArtist "Stepmother" (black suit, auburn bob)
Warrior= EscapeArtist "Guard2" (green wool tunic, brown trousers, leather belt + sheathed sword on the left hip)
Comp   = EscapeArtist "Protester2" (blue-grey tunic, brown trousers) - background companion at the camp"""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, OUT = a[0], a[1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
CR = os.path.join(ROOT, "CaveRescue_v010/CaveRescue_v010_60fps.blend")
EA = os.path.join(ROOT, "EscapeArtist_v010/EscapeArtist_v010_60fps.blend")
BR = os.path.join(ROOT, "BelugaRescue_v008/BelugaRescue_v008_60fps.blend")
GIRL_SRC = os.environ.get("GIRL_SRC", "BR:SpecC")
SRC = [({"BR": BR, "CR": CR}[GIRL_SRC.split(":")[0]], GIRL_SRC.split(":")[1], "Girl"), (EA, "Father", "Dad"), (EA, "Judge", "ExpM"), (EA, "Protester1", "ExpF"),
       (EA, "Guard2", "Warrior"), (EA, "Protester2", "Comp")]
RIGS = {}
for path, src, new in SRC:
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        dt.objects = [n for n in df.objects if n == src or n.startswith(src + ".")]
    objs = [o for o in dt.objects if o is not None]
    rig = next(o for o in objs if o.type == 'ARMATURE')
    kids = [o for o in objs if o.parent == rig and o.type == 'MESH' and "." in o.name]
    for o in [o for o in objs if o not in kids and o is not rig]:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in [rig] + kids:
        sc.collection.objects.link(o)
        o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
        o.hide_render = o.hide_viewport = False; o.hide_set(False)
        for c in list(o.constraints): o.constraints.remove(c)
    rig.name = new; rig.data.name = new
    for k in kids:
        k.name = new + "." + k.name.split(".", 1)[1]; k.data = k.data.copy(); k.data.name = k.name
        for m in k.modifiers:
            if m.type == 'SUBSURF': m.levels = 0; m.render_levels = 1
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
    for pb in rig.pose.bones:
        for c in list(pb.constraints): pb.constraints.remove(c)
        pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    RIGS[new] = rig
    print("CHAR", new, "from", src, [k.name for k in kids])
bpy.ops.outliner.orphans_purge(do_recursive=True)

for r in RIGS.values():           # single-user materials per character
    for k in r.children:
        if k.type != 'MESH': continue
        for i, m in enumerate(k.data.materials):
            if m: k.data.materials[i] = m.copy(); k.data.materials[i].name = k.name

def P_of(m): return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)

def two_tone(k, top, bottom, split, rough=0.6):
    """flat clean colours: `top` above rest height `split` (metres, rig space), `bottom` below; follows the body (Object coords at rest)"""
    for m in k.data.materials:
        nt = m.node_tree; P = P_of(m)
        src = P.inputs['Base Color'].links[0].from_socket if P.inputs['Base Color'].links else None
        for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
        for l in list(P.inputs['Roughness'].links): nt.links.remove(l)
        P.inputs['Roughness'].default_value = rough
        attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = "rest_z"
        lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'GREATER_THAN'; lt.inputs[1].default_value = split
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        mx.inputs['A'].default_value = (*bottom, 1); mx.inputs['B'].default_value = (*top, 1)
        nt.links.new(attr.outputs['Fac'], lt.inputs[0]); nt.links.new(lt.outputs[0], mx.inputs['Factor'])
        if src is None: nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
        else:      # keep the cloth's folds and seams: old texture luminance x new colour
            bw = nt.nodes.new('ShaderNodeRGBToBW'); mr = nt.nodes.new('ShaderNodeMapRange')
            mr.inputs['To Min'].default_value = 0.7; mr.inputs['To Max'].default_value = 1.15
            mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.6
            mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
            cr = nt.nodes.new('ShaderNodeCombineColor')
            nt.links.new(src, bw.inputs[0]); nt.links.new(bw.outputs[0], mr.inputs['Value'])
            for ch in ('Red', 'Green', 'Blue'): nt.links.new(mr.outputs['Result'], cr.inputs[ch])
            nt.links.new(mx.outputs['Result'], mul.inputs['A']); nt.links.new(cr.outputs[0], mul.inputs['B'])
            nt.links.new(mul.outputs['Result'], P.inputs['Base Color'])
    # rest height stored per vertex (the deformed mesh keeps it)
    me = k.data
    at = me.attributes.get("rest_z") or me.attributes.new("rest_z", 'FLOAT', 'POINT')
    for i, v in enumerate(me.vertices): at.data[i].value = v.co.z

def flat(k, rgb, rough=0.6):
    for m in k.data.materials:
        nt = m.node_tree; P = P_of(m)
        for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
        P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = rough

def tint_hair(k, rgb, lo=0.30, hi=1.35):
    """recolour a hair card texture: the old texture's luminance, stretched over its real range (so strands stay visible),
    x the new colour; alpha untouched; a strand bump from the same texture"""
    import numpy as np
    for m in k.data.materials:
        nt = m.node_tree; P = P_of(m)
        ln = P.inputs['Base Color'].links
        if not ln: P.inputs['Base Color'].default_value = (*rgb, 1); continue
        src = ln[0].from_socket; nt.links.remove(ln[0])
        img = next((nd.image for nd in nt.nodes if nd.type == 'TEX_IMAGE' and nd.image), None)
        a0, a1 = 0.0, 1.0
        if img:
            px = np.empty(len(img.pixels), dtype=np.float32); img.pixels.foreach_get(px); px = px.reshape(-1, 4)
            sel = px[px[:, 3] > 0.5]
            if len(sel):
                lum = sel[:, 0] * 0.3 + sel[:, 1] * 0.59 + sel[:, 2] * 0.11
                a0, a1 = float(np.percentile(lum, 3)), float(np.percentile(lum, 97))
            print("HAIRTEX", k.name, img.name, round(a0, 3), round(a1, 3))
        bw = nt.nodes.new('ShaderNodeRGBToBW'); mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['From Min'].default_value = a0; mr.inputs['From Max'].default_value = max(a1, a0 + 0.02)
        mr.inputs['To Min'].default_value = lo; mr.inputs['To Max'].default_value = hi
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
        mul.inputs['B'].default_value = (*rgb, 1)
        nt.links.new(src, bw.inputs[0]); nt.links.new(bw.outputs[0], mr.inputs['Value'])
        cr = nt.nodes.new('ShaderNodeCombineColor')
        for ch in ('Red', 'Green', 'Blue'): nt.links.new(mr.outputs['Result'], cr.inputs[ch])
        nt.links.new(cr.outputs[0], mul.inputs['A']); nt.links.new(mul.outputs['Result'], P.inputs['Base Color'])
        if not P.inputs['Normal'].links:
            bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.002
            nt.links.new(mr.outputs['Result'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], P.inputs['Normal'])
        P.inputs['Roughness'].default_value = 0.42
        for l in list(P.inputs['Roughness'].links): nt.links.remove(l)

def part(r, key): return next((k for k in r.children if k.type == 'MESH' and key in k.name), None)
def waist(r): return r.data.bones["pelvis.L"].head_local.z + 0.075 * r.data.bones["head"].head_local.z / 1.6

G = RIGS["Girl"]
two_tone(part(G, "casualsuit"), (0.72, 0.12, 0.66), (0.16, 0.27, 0.50), waist(G))     # pink-purple tee, mid-blue denim
def loosen(k, r, top_push=0.016, leg_push=0.018, split=None):
    """loose clothes: push the cloth out along its normals (more on the lower legs: straight-leg jeans; the tee hangs loose)"""
    vg = k.vertex_groups.new(name="Loose"); me = k.data
    hz = r.data.bones["head"].head_local.z; knee = r.data.bones["lowerleg01.L"].head_local.z
    for v in me.vertices:
        z = v.co.z
        if z > split: w = 0.9 if z < hz * 0.78 else 0.35            # tee body loose, shoulders/neck close
        elif z > knee: w = 0.75                                     # thighs
        else: w = 1.0                                               # lower legs widest
        vg.add([v.index], w, 'REPLACE')
    d = k.modifiers.new("Loose", 'DISPLACE'); d.direction = 'NORMAL'; d.mid_level = 0.0; d.strength = top_push; d.vertex_group = "Loose"
    sm = k.modifiers.new("LooseSmooth", 'CORRECTIVE_SMOOTH'); sm.iterations = 6; sm.scale = 1.0
    # keep modifier order: armature first, then the loosening
loosen(part(G, "casualsuit"), G, 0.014, 0.016, split=waist(G))
flat(part(G, "shoes"), (0.85, 0.35, 0.55), 0.5)
tint_hair(part(G, "ponytail"), (0.95, 0.74, 0.42))
tint_hair(part(G, "eyebrow"), (0.75, 0.55, 0.32), 0.6, 1.0)
D = RIGS["Dad"]
two_tone(part(D, "casualsuit"), (0.42, 0.44, 0.46), (0.06, 0.09, 0.18), waist(D) - 0.09)   # grey tee, navy jeans
flat(part(D, "shoes"), (0.18, 0.13, 0.09), 0.5)
tint_hair(part(D, "short01"), (0.80, 0.62, 0.38))
EM = RIGS["ExpM"]
# ExpM keeps his own dark suit + white shirt texture
EF = RIGS["ExpF"]
tint_hair(part(EF, "ponytail"), (0.75, 0.25, 0.08))
tint_hair(part(EF, "eyebrow"), (0.55, 0.22, 0.10), 0.6, 1.0)
W = RIGS["Warrior"]
two_tone(part(W, "casualsuit"), (0.16, 0.30, 0.14), (0.28, 0.18, 0.10), waist(W) - 0.09, 0.8)   # green wool tunic to the hips
flat(part(W, "shoes"), (0.20, 0.12, 0.06), 0.6)
tint_hair(part(W, "short"), (0.55, 0.35, 0.18))
C = RIGS["Comp"]
two_tone(part(C, "casualsuit"), (0.25, 0.32, 0.42), (0.30, 0.22, 0.13), waist(C) - 0.09, 0.8)
flat(part(C, "shoes"), (0.20, 0.12, 0.06), 0.6)

# ---- eye fix (EnhancedEye cornea -> transparent mix) on every EnhancedEye group that lacks it
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    if any(nd.name.startswith("CorneaTransparentMix") for nd in g.nodes): print("EYEFIX already", g.name); continue
    P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; out_sock = ol.to_socket; g.links.remove(ol)
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    print("EYEFIX applied", g.name)
for n, r in RIGS.items():
    eye = part(r, "high-poly"); print("EYE", n, [m.name for m in eye.data.materials],
                                       [nd.node_tree.name for m in eye.data.materials for nd in m.node_tree.nodes if nd.type == 'GROUP'])

# ---- open the elbow IK limit (MPFB rest elbow ~46 deg: min 0 kept arms in an A-pose)
for r in RIGS.values():
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]
        lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(100)

def parent_to_bone(o, r, bone):
    Mw = o.matrix_world.copy(); o.parent = r; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = Mw

# ---- warrior: leather belt (shrinkwrapped ring at the waist) + the sheathed sword hanging on the left hip
def mat(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Metallic'].default_value = metal
    return m
def belt(r, z, name, rgb):
    body = part(r, "body"); suit = part(r, "suit")
    bm = bmesh.new(); seg = 64; ring = []
    for zz in (z - 0.025, z + 0.025):
        ring.append([bm.verts.new((0.25 * math.cos(2 * math.pi * i / seg), 0.25 * math.sin(2 * math.pi * i / seg), zz)) for i in range(seg)])
    for i in range(seg): bm.faces.new((ring[0][i], ring[0][(i + 1) % seg], ring[1][(i + 1) % seg], ring[1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.location = (r.data.bones["root"].head_local.x, r.data.bones["root"].head_local.y, 0)
    me.materials.append(mat("M_" + name, rgb, 0.55))
    sw = o.modifiers.new("Fit", 'SHRINKWRAP'); sw.target = suit; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.offset = 0.006
    so = o.modifiers.new("Solid", 'SOLIDIFY'); so.thickness = 0.008; so.offset = 1.0
    for p_ in me.polygons: p_.use_smooth = True
    bpy.context.view_layer.update(); parent_to_bone(o, r, "root")
    return o
WZ = waist(RIGS["Warrior"]) - 0.04
belt(RIGS["Warrior"], WZ, "Warrior.belt", (0.17, 0.09, 0.04))
belt(RIGS["Comp"], waist(RIGS["Comp"]) - 0.04, "Comp.belt", (0.17, 0.09, 0.04))
for n, r in RIGS.items():
    print("RIG", n, tuple(round(d, 2) for d in r.dimensions), "head z", round(r.data.bones["head"].head_local.z, 3),
          "spine01 z", round(r.data.bones["spine01"].head_local.z, 3), "pelvis.L", tuple(round(c, 3) for c in r.data.bones["pelvis.L"].head_local))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("CHARS_OK")
