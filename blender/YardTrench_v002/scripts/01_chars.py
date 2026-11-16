"""YardTrench cast (adapted from LoveCanal_v001 01_chars.py). The MakeHuman CC0 asset host was down (502) when this film was built, so the dressed MPFB2 characters
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
    ("Boy", "HeadsetBullet_v008", "Teen", {"casualsuit": (0.10, 0.16, 0.36)}, []),   # navy T-shirt, blue jeans (LOW)
    ("Man", "WaterTubes_v006",   "Hero", {"casualsuit": (0.93, 0.93, 0.91)}, []),     # white top (logo), blue jeans (LOW)
]
LOW = {"Boy": (0.26, 0.40, 0.66), "Man": (0.22, 0.34, 0.58)}

def append(pkg, rig_name):
    path = [os.path.join(ROOT, pkg, f) for f in os.listdir(os.path.join(ROOT, pkg)) if f.endswith(".blend")][0]
    pre = rig_name.replace("_rig", "") + "."
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [rig_name] + [n for n in src.objects if n.startswith(pre) or n.startswith(rig_name + ".")]
    rig = dst.objects[0]
    for o in [rig] + list(dst.objects):
        if o.name not in bpy.context.scene.collection.objects: bpy.context.scene.collection.objects.link(o)
    return rig

def tint_mat(m, rgb, low=None, TL=None, TS=None):
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
            # REST-space position (Generated = undeformed coords): the split must not move when the body is posed or lowered
            tc = nt.nodes.new("ShaderNodeTexCoord"); va = nt.nodes.new("ShaderNodeVectorMath"); va.operation = 'MULTIPLY_ADD'
            nt.links.new(tc.outputs["Generated"], va.inputs[0]); va.inputs[1].default_value = TS * 2; va.inputs[2].default_value = TL - TS
            sz = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(va.outputs[0], sz.inputs[0])
            mz0 = nt.nodes.new("ShaderNodeMapRange"); mz0.interpolation_type = 'SMOOTHSTEP'; nt.links.new(sz.outputs["Z"], mz0.inputs[0])
            mz0.inputs[1].default_value = zc - 0.01; mz0.inputs[2].default_value = zc + 0.01
            ax = nt.nodes.new("ShaderNodeMath"); ax.operation = 'ABSOLUTE'; nt.links.new(sz.outputs["X"], ax.inputs[0])
            arm = nt.nodes.new("ShaderNodeMath"); arm.operation = 'GREATER_THAN'; nt.links.new(ax.outputs[0], arm.inputs[0]); arm.inputs[1].default_value = 0.3   # arms/cuffs keep the top colour
            mz = nt.nodes.new("ShaderNodeMath"); mz.operation = 'MAXIMUM'; nt.links.new(mz0.outputs[0], mz.inputs[0]); nt.links.new(arm.outputs[0], mz.inputs[1])
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
                    if ck in key:
                        o.data.use_auto_texspace = True
                        tint_mat(m2, rgb, (LOW[new], zc) if (new in LOW and "suit" in ck) else None, Vector(o.data.texspace_location), Vector(o.data.texspace_size))
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
    print("IKBONES", new, "IK_foot.L" in rig.data.bones, "Pole_elbow.L" in rig.data.bones)
    print("CHAR", new, sorted(o.name for o in bpy.data.objects if o.parent == rig))

eye_fix()
bpy.ops.wm.save_as_mainfile(filepath=out)
