"""ChicagoRaised cast. Dressed MPFB2 characters are appended from earlier studio packages (same MPFB 'default' rig + anim_lib IK
controls), stripped of animation and film props, reset to rest, re-dressed in new solid colours and renamed.
The horse is the rigged quadruped from our WW1 package.
blender -b --factory-startup --python 01_chars.py -- <out.blend>"""
import sys, os, math
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
exec(open(os.path.join(ROOT, "pipeline", "hand_poses.py")).read())
exec(open(os.path.join(ROOT, "pipeline", "anim_lib.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)

# new name, source package, source rig, outfit colours {cloth key: rgb}, drop (child-name keys to delete), trousers rgb
CAST = [   # workers: 1850s labourers (long-sleeve shirt, wool trousers, braces, most with a flat cap); shirt rgb / trousers rgb / cap
    ("W1",      "EscapeArtist_v010",     "Guard",      {"casualsuit": (0.86, 0.84, 0.76), "shoes": (0.10, 0.07, 0.05)}, [], (0.20, 0.14, 0.09)),   # linen shirt, brown trousers
    ("W2",      "EscapeArtist_v010",     "Guard2",     {"casualsuit": (0.30, 0.42, 0.66), "shoes": (0.10, 0.07, 0.05)}, [], (0.12, 0.12, 0.13)),   # faded blue, charcoal
    ("W3",      "DonationBin_v009",      "Passerby",   {"casualsuit": (0.58, 0.14, 0.10), "shoes": (0.10, 0.07, 0.05)}, [], (0.10, 0.12, 0.22)),   # brick red, navy
    ("W4",      "DonationBin_v009",      "Shover",     {"casualsuit": (0.36, 0.44, 0.30), "shoes": (0.10, 0.07, 0.05)}, [], (0.22, 0.16, 0.10)),   # grey-green, brown
    ("W5",      "BellyFat_v010",         "ShopperA",   {"casualsuit": (0.80, 0.78, 0.66), "shoes": (0.10, 0.07, 0.05)}, [], (0.10, 0.12, 0.22)),   # cream, navy
    ("W6",      "CaveRescue_v010",       "Coach",      {"casualsuit": (0.20, 0.28, 0.48), "shoes": (0.10, 0.07, 0.05)}, [], (0.25, 0.20, 0.12)),   # dark blue, tan-brown
    ("Mason",   "EscapeArtist_v010",     "Father",    {"casualsuit": (0.74, 0.72, 0.62), "shoes": (0.12, 0.08, 0.05)}, [], (0.16, 0.13, 0.10)),   # off-white, dark brown
    ("Foreman", "WW1Assassination_v007", "NerveA",     {"elegantsuit": (0.22, 0.14, 0.08), "shoes": (0.05, 0.04, 0.03)}, [], None),     # dark brown suit
    ("Lady",    "StanleyCup_v009",       "Woman_rig",  {"elegantsuit": (0.12, 0.30, 0.22), "shoes": (0.10, 0.06, 0.05)}, [], None),     # deep green dress
    ("SickMan", "EscapeArtist_v010",     "Judge",      {"elegantsuit": (0.30, 0.32, 0.38), "shoes": (0.06, 0.05, 0.04)}, [], None),     # grey suit
    ("TownMan", "WW1Assassination_v007", "Bomber",     {"elegantsuit": (0.15, 0.17, 0.25), "shoes": (0.05, 0.04, 0.03)}, [], None),     # navy suit, fedora
    ("TownWoman", "WW1Assassination_v007", "Duchess",  {"elegantsuit": (0.50, 0.18, 0.25), "shoes": (0.08, 0.05, 0.04)}, [], None),     # plum dress, wide hat
]
CAPS = {"W1": (0.30, 0.26, 0.20), "W3": (0.18, 0.18, 0.20), "W4": (0.35, 0.30, 0.22), "W6": (0.22, 0.20, 0.18), "Mason": (0.30, 0.26, 0.20)}

def append(pkg, rig_name):
    path = [os.path.join(ROOT, pkg, f) for f in os.listdir(os.path.join(ROOT, pkg)) if f.endswith(".blend")][0]
    pre = rig_name.replace("_rig", "") + "."
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [rig_name] + [n for n in src.objects if n.startswith(pre) or n.startswith(rig_name + ".")]
    rig = dst.objects[0]
    for o in [o for o in dst.objects if o]:
        if o.name not in bpy.context.scene.collection.objects: bpy.context.scene.collection.objects.link(o)
    # objects that are not children of the rig (stray props with the prefix) go
    for o in [o for o in dst.objects if o and o is not rig and o.parent is not rig]:
        bpy.data.objects.remove(o, do_unlink=True)
    return rig

def tint_mat(m, rgb, low=None):
    """multiply the cloth texture's luminance by rgb; low=(trouser rgb, waist z) puts a second colour below the waist and
    dark braces (two straps over the shoulders) above it, in the cloth's own rest-space (Object) coordinates"""
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    s_ = P.inputs["Base Color"]
    src = None
    if s_.is_linked:
        src = s_.links[0].from_socket; nd = src.node
        while nd.type in ("MIX", "MIX_RGB") and any(i.is_linked for i in nd.inputs):
            lk = next((i.links[0] for i in nd.inputs if i.is_linked and i.links[0].from_node.type == "TEX_IMAGE"), None)
            if not lk: break
            src = lk.from_socket; nd = src.node
        if nd.type != "TEX_IMAGE": src = None
    def shade(col):
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
        if src is not None:
            bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
            mr = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(bw.outputs[0], mr.inputs[0])
            mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 0.6; mr.inputs[3].default_value = 0.75; mr.inputs[4].default_value = 1.08
            cc = nt.nodes.new("ShaderNodeCombineColor")
            for i in range(3): nt.links.new(mr.outputs[0], cc.inputs[i])
            nt.links.new(cc.outputs[0], mx.inputs[6])
        else:
            mx.inputs[6].default_value = (1, 1, 1, 1)
        mx.inputs[7].default_value = (*[v * 0.62 for v in col], 1); return mx.outputs[2]
    out_ = shade(rgb)
    if low:
        lrgb, zc = low
        tc = nt.nodes.new("ShaderNodeTexCoord"); sz = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sz.inputs[0])
        mz = nt.nodes.new("ShaderNodeMapRange"); mz.interpolation_type = 'SMOOTHSTEP'; nt.links.new(sz.outputs["Z"], mz.inputs[0])
        mz.inputs[1].default_value = zc - 0.01; mz.inputs[2].default_value = zc + 0.01
        sw = nt.nodes.new("ShaderNodeMix"); sw.data_type = 'RGBA'; nt.links.new(mz.outputs[0], sw.inputs[0])
        nt.links.new(shade(lrgb), sw.inputs[6]); nt.links.new(out_, sw.inputs[7]); out_ = sw.outputs[2]
        # braces: |x| in [0.065, 0.095], above the waist
        ab = nt.nodes.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; nt.links.new(sz.outputs["X"], ab.inputs[0])
        d_ = nt.nodes.new("ShaderNodeMath"); d_.operation = 'SUBTRACT'; nt.links.new(ab.outputs[0], d_.inputs[0]); d_.inputs[1].default_value = 0.08
        a2 = nt.nodes.new("ShaderNodeMath"); a2.operation = 'ABSOLUTE'; nt.links.new(d_.outputs[0], a2.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; nt.links.new(a2.outputs[0], lt.inputs[0]); lt.inputs[1].default_value = 0.015
        up = nt.nodes.new("ShaderNodeMath"); up.operation = 'GREATER_THAN'; nt.links.new(sz.outputs["Z"], up.inputs[0]); up.inputs[1].default_value = zc + 0.01
        mu = nt.nodes.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; nt.links.new(lt.outputs[0], mu.inputs[0]); nt.links.new(up.outputs[0], mu.inputs[1])
        br = nt.nodes.new("ShaderNodeMix"); br.data_type = 'RGBA'; nt.links.new(mu.outputs[0], br.inputs[0])
        nt.links.new(out_, br.inputs[6]); br.inputs[7].default_value = (0.10, 0.06, 0.035, 1); out_ = br.outputs[2]
    nt.links.new(out_, s_)
    P.inputs["Roughness"].default_value = max(P.inputs["Roughness"].default_value, 0.6)

def eye_fix():
    g = bpy.data.node_groups.get("EnhancedEye")
    if not g or "CorneaTransparentMix" in g.nodes: return
    P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]; src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; out_sock = ol.to_socket; g.links.remove(ol)
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    print("EYEFIX applied")

KEEP_KEYS = ("body", "eyebrow", "eyelashes", "high-poly", "low-poly", "suit", "shoes", "short", "long", "bob", "ponytail",
             "teeth", "tongue", "fedora", "WideHat")
for i, (new, pkg, src, cols, drop, low) in enumerate(CAST):
    rig = append(pkg, src)
    kids = [o for o in bpy.data.objects if o.parent == rig]
    rig.name = new; rig.data.name = new
    for o in kids:
        if o.animation_data: o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys and o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
        key = o.name.split(".", 1)[-1].split(".")[0]
        if key in drop or not any(k in key for k in KEEP_KEYS) or o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True); continue
        o.name = new + "." + key
        o.data = o.data.copy()
        for j, m in enumerate(o.data.materials):
            if m is None: continue
            m2 = m.copy(); m2.name = new + "." + key + ("" if j == 0 else ".%d" % j); o.data.materials[j] = m2
            zc = rig.data.bones["upperleg01.L"].head_local.z + 0.07
            for ck, rgb in cols.items():
                if ck in key: tint_mat(m2, rgb, (low, zc) if (low and "suit" in ck) else None)
    if rig.animation_data: rig.animation_data_clear()
    for o in [rig] + [o for o in bpy.data.objects if o.parent == rig]:
        o.hide_render = False; o.hide_viewport = False; o.hide_set(False); o.visible_camera = True; o.visible_shadow = True
    if "IK_hand.L" not in rig.data.bones:
        make_human_ctrl(rig); print("CTRL added", new)
    for pb in rig.pose.bones:
        for c in list(pb.constraints):
            if c.type not in ('IK', 'COPY_ROTATION', 'LIMIT_ROTATION'): pb.constraints.remove(c)
            elif c.type == 'COPY_ROTATION' and c.subtarget not in ("IK_foot.L", "IK_foot.R", "IK_hand.L", "IK_hand.R"): pb.constraints.remove(c)
            else: c.influence = 1.0; c.mute = False
        pb.rotation_mode = 'QUATERNION'; pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    rig.location = (i * 1.2, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
    add_hand_limits(rig)
    for s in "LR":
        lo = rig.pose.bones["lowerarm01." + s]
        lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(100)   # MPFB rest elbow ~46 deg: allow straightening
        w = rig.pose.bones["wrist." + s].constraints.get("HandLimit")
        if w: w.euler_order = 'YXZ'; w.use_limit_y = False                                            # forearm twist free
    print("CHAR", new, sorted(o.name for o in bpy.data.objects if o.parent == rig))
eye_fix()
# ---- flat caps (crown + short visor), Child Of the head bone via bone parenting; hair under the cap is hidden; rim above the brows
import bmesh
def flat_cap(n, rgb):
    r = bpy.data.objects[n]; body = bpy.data.objects[n + ".body"]
    eL, eR = r.data.bones["eye.L"].head_local, r.data.bones["eye.R"].head_local
    eye_z = (eL.z + eR.z) / 2; eye_y = (eL.y + eR.y) / 2
    # the evaluated head surface (shape keys applied) gives the real skull size
    _mods = [(m_, m_.show_viewport) for m_ in body.modifiers if m_.type in ('MASK', 'SUBSURF', 'ARMATURE')]
    for m_, _ in _mods: m_.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get(); ev_ = body.evaluated_get(dg); me_ = ev_.to_mesh()
    gi = body.vertex_groups["head"].index
    pts = [me_.vertices[v.index].co.copy() for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups) and me_.vertices[v.index].co.z > eye_z]
    ev_.to_mesh_clear()
    for m_, v_ in _mods: m_.show_viewport = v_
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    c = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0)); wx, wy, top = max(xs) - min(xs), max(ys) - min(ys), max(zs)
    rim = eye_z + 0.05
    for k in r.children:
        if k.type == 'MESH' and any(h in k.name for h in ("short0", "bob", "ponytail", "afro")): k.hide_render = True; k.hide_viewport = True
    m = bpy.data.materials.new(n + ".capmat"); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = 0.85
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=1.0)
    for v in bm.verts:
        z = max(v.co.z, 0.0); v.co = Vector((v.co.x * wx / 2 * 1.16, v.co.y * wy / 2 * 1.14 - (0.012 if v.co.y < 0 else 0), z * (top - rim) * 1.05))
        if v.co.y < -0.02 and z > 0.3: v.co.y -= 0.01 * z     # flat cap: crown pulled forward over the peak
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.0005], context='VERTS')
    me = bpy.data.meshes.new(n + ".cap"); bm.to_mesh(me); bm.free(); cap = bpy.data.objects.new(n + ".cap", me); bpy.context.scene.collection.objects.link(cap)
    cap.location = r.matrix_world @ Vector((c.x, c.y, rim)); me.materials.append(m)
    for p_ in me.polygons: p_.use_smooth = True
    sol = cap.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.008; sol.offset = 1.0
    # visor: a shallow half-disc at the rim, front (-Y)
    bm = bmesh.new(); ri, ro = [], []
    for i in range(21):
        t = math.pi * (0.1 + 0.8 * i / 20); dx, dy = math.cos(t), -math.sin(t)
        ri.append(bm.verts.new((dx * wx / 2 * 1.1, dy * wy / 2 * 1.1, 0.0))); ro.append(bm.verts.new((dx * wx / 2 * 1.1 + dx * 0.02, dy * wy / 2 * 1.1 + dy * 0.055 * math.sin(t), -0.012 * math.sin(t))))
    for i in range(20): bm.faces.new((ri[i], ri[i + 1], ro[i + 1], ro[i]))
    me2 = bpy.data.meshes.new(n + ".visor"); bm.to_mesh(me2); bm.free(); vi = bpy.data.objects.new(n + ".visor", me2); bpy.context.scene.collection.objects.link(vi)
    vi.location = r.matrix_world @ Vector((c.x, c.y, rim + 0.004)); me2.materials.append(m); vi.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.006
    for o in (cap, vi):
        bpy.context.view_layer.update(); Mw = o.matrix_world.copy(); o.parent = r; o.parent_type = 'BONE'; o.parent_bone = "head"
        bpy.context.view_layer.update(); o.matrix_world = Mw
    print("CAP", n, "rim", round(rim, 3), "top", round(top, 3))
for n, rgb in CAPS.items(): flat_cap(n, rgb)
# every character gets the procedural EnhancedEye material if one exists (image eyes read dark at film size)
eyemats = [m for m in bpy.data.materials if m.node_tree and any(n.type == 'GROUP' and n.node_tree and n.node_tree.name == "EnhancedEye" for n in m.node_tree.nodes)]
print("ENHANCED EYE MATS", [m.name for m in eyemats][:4])
if eyemats:
    for new, *_ in CAST:
        eye = next((o for o in bpy.data.objects if o.parent and o.parent.name == new and ("high-poly" in o.name or "low-poly" in o.name)), None)
        if eye and not any(m and m in eyemats for m in eye.data.materials):
            eye.data.materials[0] = eyemats[0]; print("EYE swapped", new)

# ---- horse (rigged quadruped from WW1Assassination): dark bay
path = os.path.join(ROOT, "WW1Assassination_v007", "WW1Assassination_v007_60fps.blend")
with bpy.data.libraries.load(path, link=False) as (src, dst):
    dst.objects = ["Horse_rig", "Horse_body"]
for o in dst.objects:
    bpy.context.scene.collection.objects.link(o)
    if o.animation_data: o.animation_data_clear()
    o.hide_render = False; o.hide_viewport = False; o.hide_set(False)
hr = bpy.data.objects["Horse_rig"]; hr.location = (0, 6, 0); hr.rotation_euler = (0, 0, 0)
for pb in hr.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
print("HORSE dims", tuple(round(d, 2) for d in bpy.data.objects["Horse_body"].dimensions), [b.name for b in hr.data.bones][:30])
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("CHARS_OK")
