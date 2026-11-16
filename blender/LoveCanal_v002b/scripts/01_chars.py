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
    ("Father",    "EscapeArtist_v010",  "Father",     {"casualsuit": (0.05, 0.55, 0.42), "shoes": (0.12, 0.09, 0.07)}, []),  # v002b: his own short hair kept (director: no bald heads)
    ("Boy",       "EscapeArtist_v010",  "Boy",        {"casualsuit": (0.62, 0.06, 0.08), "shoes": (0.1, 0.1, 0.12)}, []),            # red top
    ("Mother",    "EscapeArtist_v010",  "Stepmother", {"elegantsuit": (0.55, 0.25, 0.62), "shoes": (0.15, 0.1, 0.1)}, []),          # purple
    ("Neighbour", "StanleyCup_v009",    "Woman_rig",  {"elegantsuit": (0.16, 0.33, 0.58), "shoes": (0.3, 0.2, 0.15)}, []),           # v002b: blue patterned dress, long hair
    ("Dad2",      "EscapeArtist_v010",  "Guard",      {"casualsuit": (0.2, 0.36, 0.7), "shoes": (0.1, 0.08, 0.06)}, []),             # blue shirt
    ("Worker",    "BellyFat_v010",      "Stocker",    {"worksuit": (0.22, 0.32, 0.52), "shoes": (0.1, 0.08, 0.06)}, []),             # blue-grey coveralls, dark boots
]

LOW = {"Father": (0.16, 0.15, 0.14), "Boy": (0.12, 0.16, 0.3), "Dad2": (0.1, 0.12, 0.2)}   # trousers

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
# work gloves for the Worker: dark grey material on the MPFB hand faces (with a clean cuff above the wrist)
wk = bpy.data.objects["Worker"]; wb = bpy.data.objects["Worker.body"]
gl = bpy.data.materials.new("WorkGlove"); gl.use_nodes = True; P_ = gl.node_tree.nodes["Principled BSDF"]
P_.inputs["Base Color"].default_value = (0.08, 0.08, 0.09, 1); P_.inputs["Roughness"].default_value = 0.75
vg = {g.index: g.name for g in wb.vertex_groups}; hand = set()
for v in wb.data.vertices:
    if sum(g.weight for g in v.groups if any(k in vg.get(g.group, "") for k in ("wrist", "finger", "metacarpal", "thumb"))) > 0.5: hand.add(v.index)
wb.data.materials.append(gl); gi = len(wb.data.materials) - 1
wr = [wk.data.bones["wrist." + s_].head_local for s_ in "LR"]; n_ = 0
for p_ in wb.data.polygons:
    if all(v in hand for v in p_.vertices) or min((p_.center - w_).length for w_ in wr) < 0.06: p_.material_index = gi; n_ += 1
print("GLOVE faces", n_)
# hard hat for the worker (CC-BY model), Child Of the head bone
hh_path = os.path.join(ROOT, "LoveCanal_v001", "assets_src", "hardhat.glb")
if os.path.exists(hh_path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=hh_path)
    hh = [o for o in bpy.data.objects if o not in before and o.type == 'MESH'][0]
    for o in [o for o in bpy.data.objects if o not in before and o is not hh]: bpy.data.objects.remove(o, do_unlink=True)
    hh.name = "Worker.hardhat"; hh.parent = None
    bpy.context.view_layer.update(); hh.data.transform(hh.matrix_world); hh.matrix_world.identity()
    bb = [hh.matrix_world @ Vector(c) for c in hh.bound_box]; mn = Vector([min(p[i] for p in bb) for i in range(3)]); mx = Vector([max(p[i] for p in bb) for i in range(3)])
    sc_ = 0.30 / (mx - mn).x; hh.data.transform(__import__('mathutils').Matrix.Translation(-(mn + mx) / 2)); hh.data.transform(__import__('mathutils').Matrix.Scale(sc_, 4))
    m = bpy.data.materials.new("HardHat_yellow"); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (0.95, 0.72, 0.03, 1); P.inputs["Roughness"].default_value = 0.4
    hh.data.materials.clear(); hh.data.materials.append(m)
# ---- v002b: looser trousers (Father) and a looser, patterned dress (Neighbour)
def loosen(ob, z_top, z_bot, amount, flare=0.6):
    """push the garment out along its normals below z_top (rest space), more toward the hem"""
    vg = ob.vertex_groups.new(name="loose")
    for v in ob.data.vertices:
        z = v.co.z
        if z < z_top:
            t = min(1.0, max(0.0, (z_top - z) / max(1e-4, z_top - z_bot)))
            vg.add([v.index], (1 - flare) * min(1.0, t * 4) + flare * t, 'REPLACE')
    d = ob.modifiers.new("loose", 'DISPLACE'); d.direction = 'NORMAL'; d.mid_level = 0.0; d.strength = amount; d.vertex_group = "loose"
    print("LOOSEN", ob.name, len(vg.name), amount)
def add_dots(m, rgb2, scale=55.0, size=0.28):
    """small polka dots over the tinted colour (object coordinates, no UVs needed)"""
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"); s_ = P.inputs["Base Color"]
    src = s_.links[0].from_socket if s_.is_linked else None
    tc = nt.nodes.new("ShaderNodeTexCoord"); vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(vo.outputs["Distance"], mr.inputs[0]); mr.inputs[1].default_value = size; mr.inputs[2].default_value = size + 0.06
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; nt.links.new(mr.outputs[0], mx.inputs[0])
    mx.inputs[6].default_value = (*rgb2, 1)
    if src: nt.links.new(src, mx.inputs[7])
    else: mx.inputs[7].default_value = s_.default_value
    nt.links.new(mx.outputs[2], s_)
fr = bpy.data.objects["Father"]; zc = fr.data.bones["upperleg01.L"].head_local.z + 0.07
for o in [o for o in bpy.data.objects if o.parent == fr and "casualsuit" in o.name]:
    loosen(o, zc, fr.data.bones["lowerleg02.L"].tail_local.z, 0.022, flare=0.5)
nb = bpy.data.objects["Neighbour"]; zh = nb.data.bones["upperleg01.L"].head_local.z + 0.05
for o in [o for o in bpy.data.objects if o.parent == nb and "elegantsuit" in o.name]:
    loosen(o, zh, nb.data.bones["lowerleg01.L"].head_local.z, 0.03, flare=0.8)
    for m in o.data.materials:
        if m: add_dots(m, (0.92, 0.9, 0.82))
bpy.ops.wm.save_as_mainfile(filepath=out)
