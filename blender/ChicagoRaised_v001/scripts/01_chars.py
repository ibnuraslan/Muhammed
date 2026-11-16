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
CAST = [
    ("W1",      "BellyFat_v010",         "Stocker",    {"worksuit": (0.12, 0.25, 0.55), "shoes": (0.10, 0.07, 0.05)}, [], None),        # blue coveralls
    ("W2",      "EscapeArtist_v010",     "Prisoner",   {"worksuit": (0.10, 0.30, 0.16), "shoes": (0.10, 0.07, 0.05)}, [], None),        # dark green
    ("W3",      "EscapeArtist_v010",     "PrisonerOld", {"worksuit": (0.33, 0.34, 0.37), "shoes": (0.10, 0.07, 0.05)}, [], None),       # grey
    ("W4",      "WW1Assassination_v007", "Driver",     {"worksuit": (0.07, 0.09, 0.24), "shoes": (0.10, 0.07, 0.05)}, ["DriverCap"], None),  # navy
    ("W5",      "CaveRescue_v010",       "DiverA",     {"worksuit": (0.20, 0.30, 0.42), "shoes": (0.10, 0.07, 0.05)}, [], None),        # slate blue
    ("W6",      "CaveRescue_v010",       "DiverB",     {"worksuit": (0.22, 0.26, 0.10), "shoes": (0.10, 0.07, 0.05)}, [], None),        # dark olive
    ("Mason",   "CaveRescue_v010",       "DiverC",     {"worksuit": (0.15, 0.24, 0.45), "shoes": (0.12, 0.08, 0.05)}, [], None),        # denim blue
    ("Foreman", "WW1Assassination_v007", "NerveA",     {"elegantsuit": (0.22, 0.14, 0.08), "shoes": (0.05, 0.04, 0.03)}, [], None),     # dark brown suit
    ("Lady",    "StanleyCup_v009",       "Woman_rig",  {"elegantsuit": (0.12, 0.30, 0.22), "shoes": (0.10, 0.06, 0.05)}, [], None),     # deep green dress
    ("SickMan", "EscapeArtist_v010",     "Judge",      {"elegantsuit": (0.30, 0.32, 0.38), "shoes": (0.06, 0.05, 0.04)}, [], None),     # grey suit
    ("TownMan", "WW1Assassination_v007", "Bomber",     {"elegantsuit": (0.15, 0.17, 0.25), "shoes": (0.05, 0.04, 0.03)}, [], None),     # navy suit, fedora
    ("TownWoman", "WW1Assassination_v007", "Duchess",  {"elegantsuit": (0.50, 0.18, 0.25), "shoes": (0.08, 0.05, 0.04)}, [], None),     # plum dress, wide hat
]

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

def tint_mat(m, rgb):
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    s = P.inputs["Base Color"]
    if s.is_linked:
        src = s.links[0].from_socket; nd = src.node
        while nd.type in ("MIX", "MIX_RGB") and any(i.is_linked for i in nd.inputs):
            lk = next((i.links[0] for i in nd.inputs if i.is_linked and i.links[0].from_node.type == "TEX_IMAGE"), None)
            if not lk: break
            src = lk.from_socket; nd = src.node
        if nd.type != "TEX_IMAGE":
            s.default_value = (*rgb, 1); nt.links.remove(s.links[0])
        else:
            bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
            mr = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(bw.outputs[0], mr.inputs[0])
            mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 0.6; mr.inputs[3].default_value = 0.7; mr.inputs[4].default_value = 1.1
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
            cc = nt.nodes.new("ShaderNodeCombineColor")
            for i in range(3): nt.links.new(mr.outputs[0], cc.inputs[i])
            nt.links.new(cc.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*rgb, 1)
            nt.links.new(mx.outputs[2], s)
    else:
        s.default_value = (*rgb, 1)
    P.inputs["Roughness"].default_value = max(P.inputs["Roughness"].default_value, 0.55)

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
            for ck, rgb in cols.items():
                if ck in key: tint_mat(m2, rgb)
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
