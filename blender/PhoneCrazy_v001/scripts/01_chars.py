"""Love Canal cast. The MakeHuman CC0 asset host was down (502) when this film was built, so the dressed MPFB2 characters
are appended from earlier studio packages (same MPFB 'default' rig + anim_lib IK controls), stripped of their animation,
reset to rest, re-dressed in new solid colours and renamed.
blender -b --factory-startup --python 01_chars.py -- <out.blend>"""
import sys, os, math
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
exec(open(os.path.join(ROOT, "pipeline", "hand_poses.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)

# new name, source package, source rig, outfit colours {cloth key: rgb}, drop (meshes to delete)
CAST = [
    ("Foreman", "EscapeArtist_v010", "Guard",   {"casualsuit": (0.55, 0.38, 0.78), "shoes": (0.12, 0.09, 0.07)}, []),   # lilac/purple shirt (phone owner, as in the reference)
    ("Digger",  "EscapeArtist_v010", "Father",  {"casualsuit": (0.08, 0.08, 0.09), "shoes": (0.1, 0.1, 0.12)}, ["short01"]), # black shirt
    ("Mate",    "BellyFat_v010",     "Stocker", {"worksuit": (0.12, 0.42, 0.40), "shoes": (0.1, 0.08, 0.06)}, []),          # teal work shirt
]
LOW = {"Foreman": (0.78, 0.70, 0.55), "Digger": (0.32, 0.30, 0.26)}   # trousers

def append(pkg, rig_name):
    path = [os.path.join(ROOT, pkg, f) for f in os.listdir(os.path.join(ROOT, pkg)) if f.endswith(".blend")][0]
    pre = rig_name.replace("_rig", "") + "."
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [rig_name] + [n for n in src.objects if n.startswith(pre) or n.startswith(rig_name + ".")]
    rig = dst.objects[0]
    for o in [rig] + list(dst.objects):
        if o.name not in bpy.context.scene.collection.objects: bpy.context.scene.collection.objects.link(o)
    return rig

def tint_mat(m, rgb, low=None):
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    s = P.inputs["Base Color"]
    if s.is_linked:
        src = s.links[0].from_socket
        # walk back to the image if an earlier tint mix exists
        nd = src.node
        while nd.type in ("MIX", "MIX_RGB") and nd.inputs and any(i.is_linked for i in nd.inputs):
            lk = next((i.links[0] for i in nd.inputs if i.is_linked and i.links[0].from_node.type == "TEX_IMAGE"), None)
            if not lk: break
            src = lk.from_socket; nd = src.node
        bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(bw.outputs[0], mr.inputs[0])
        mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 0.6; mr.inputs[3].default_value = 0.7; mr.inputs[4].default_value = 1.1
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
        cc = nt.nodes.new("ShaderNodeCombineColor")
        for i in range(3): nt.links.new(mr.outputs[0], cc.inputs[i])
        nt.links.new(cc.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*rgb, 1)
        out_ = mx.outputs[2]
        if low:   # trousers: darker colour below the waist (object space z, origin at the feet)
            lrgb, zc = low
            tc = nt.nodes.new("ShaderNodeTexCoord"); sz = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sz.inputs[0])
            mz = nt.nodes.new("ShaderNodeMapRange"); mz.interpolation_type = 'SMOOTHSTEP'; nt.links.new(sz.outputs["Z"], mz.inputs[0])
            mz.inputs[1].default_value = zc - 0.01; mz.inputs[2].default_value = zc + 0.01
            mx2 = nt.nodes.new("ShaderNodeMix"); mx2.data_type = 'RGBA'; mx2.blend_type = 'MULTIPLY'; mx2.inputs[0].default_value = 1
            nt.links.new(cc.outputs[0], mx2.inputs[6]); mx2.inputs[7].default_value = (*lrgb, 1)
            sw = nt.nodes.new("ShaderNodeMix"); sw.data_type = 'RGBA'; nt.links.new(mz.outputs[0], sw.inputs[0])
            nt.links.new(mx2.outputs[2], sw.inputs[6]); nt.links.new(mx.outputs[2], sw.inputs[7]); out_ = sw.outputs[2]
        nt.links.new(out_, s)
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

for i, (new, pkg, src, cols, drop) in enumerate(CAST):
    rig = append(pkg, src)
    kids = [o for o in bpy.data.objects if o.parent == rig]
    rig.name = new; rig.data.name = new
    for o in kids:
        if o.animation_data: o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys and o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
        key = o.name.split(".", 1)[-1].split(".")[0]
        if key in drop: bpy.data.objects.remove(o, do_unlink=True); continue
        o.name = new + "." + key
        if o.type == 'MESH':
            o.data = o.data.copy()
            for j, m in enumerate(o.data.materials):
                if m is None: continue
                m2 = m.copy(); m2.name = new + "." + key + ("" if j == 0 else ".%d" % j); o.data.materials[j] = m2
                zc = rig.data.bones["upperleg01.L"].head_local.z + 0.07
                for ck, rgb in cols.items():
                    if ck in key: tint_mat(m2, rgb, (LOW[new], zc) if (new in LOW and "suit" in ck) else None)
    if rig.animation_data: rig.animation_data_clear()
    for o in [rig] + [o for o in bpy.data.objects if o.parent == rig]:
        o.hide_render = False; o.hide_viewport = False; o.hide_set(False); o.visible_camera = True; o.visible_shadow = True
    # keep only the IK / copy-rotation controls (anim_lib.make_human_ctrl); drop film-specific constraints
    for pb in rig.pose.bones:
        for c in list(pb.constraints):
            if c.type not in ('IK', 'COPY_ROTATION'): pb.constraints.remove(c)
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
# yellow hard hats (CC-BY model), one per worker; bone-parented to the head in 03_anim
hh_path = os.path.join(ROOT, "PhoneCrazy_v001", "assets_src", "hardhat.glb")
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=hh_path)
new = [o for o in bpy.data.objects if o not in before]
bpy.context.view_layer.update()
ms = [o for o in new if o.type == 'MESH']
for o in ms:
    mw = o.matrix_world.copy(); o.parent = None; o.data = o.data.copy(); o.data.transform(mw); o.matrix_world.identity()
for o in new:
    if o not in ms: bpy.data.objects.remove(o, do_unlink=True)
if len(ms) > 1:
    with bpy.context.temp_override(active_object=ms[0], selected_editable_objects=ms, selected_objects=ms): bpy.ops.object.join()
hh = ms[0]
from mathutils import Matrix
def vb(o):
    co = [v.co.copy() for v in o.data.vertices]
    return co, Vector([min(p[i] for p in co) for i in range(3)]), Vector([max(p[i] for p in co) for i in range(3)])
co, mn, mx = vb(hh); ext = mx - mn; print("HAT raw", ext)
ax = min(range(3), key=lambda i: ext[i])            # the shortest extent is the height
if ax == 1: hh.data.transform(Matrix.Rotation(math.radians(90), 4, 'X'))
elif ax == 0: hh.data.transform(Matrix.Rotation(math.radians(-90), 4, 'Y'))
co, mn, mx = vb(hh); hh.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
co, mn, mx = vb(hh); h = mx.z - mn.z
lo = [c for c in co if c.z < mn.z + 0.15 * h]; hi = [c for c in co if c.z > mx.z - 0.15 * h]
rl = sum(c.to_2d().length for c in lo) / len(lo); rh = sum(c.to_2d().length for c in hi) / len(hi)
if rh > rl: hh.data.transform(Matrix.Rotation(math.pi, 4, 'X'))      # brim must be at the bottom
co, mn, mx = vb(hh); hh.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
co, mn, mx = vb(hh)
if mx.x - mn.x > mx.y - mn.y: hh.data.transform(Matrix.Rotation(math.radians(90), 4, 'Z'))   # peak axis along Y
co, mn, mx = vb(hh)
dome = [c for c in co if c.z > mn.z + 0.5 * (mx.z - mn.z)]; dc = sum((c for c in dome), Vector()) / len(dome)
if (mx.y - dc.y) > (dc.y - mn.y): hh.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))       # longer peak toward -Y (the face side)
co, mn, mx = vb(hh)
dome = [c for c in co if c.z > mn.z + 0.5 * (mx.z - mn.z)]; dc = sum((c for c in dome), Vector()) / len(dome)
hh.data.transform(Matrix.Translation(-Vector((dc.x, dc.y, mn.z))))   # origin under the dome centre, at the brim
co, mn, mx = vb(hh); k = 0.205 / (max(c.x for c in dome) - min(c.x for c in dome)); hh.data.transform(Matrix.Scale(k, 4))
co, mn, mx = vb(hh); print("HAT fixed", mn, mx)
m = bpy.data.materials.new("HardHat_yellow"); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
P.inputs["Base Color"].default_value = (0.95, 0.75, 0.03, 1); P.inputs["Roughness"].default_value = 0.4
hh.data.materials.clear(); hh.data.materials.append(m)
for p in hh.data.polygons: p.use_smooth = True
for i, (new_, *_r) in enumerate(CAST):
    h = hh if i == 0 else hh.copy()
    if i: bpy.context.scene.collection.objects.link(h)
    h.name = new_ + ".hardhat"
bpy.ops.wm.save_as_mainfile(filepath=out)
