# ------------------------------------------------------------------ characters
def load_char(cid, new=None):
    with bpy.data.libraries.load(W + "ch_%s.blend" % cid, link=False) as (fd, td): td.objects = list(fd.objects)
    new = new or cid; c = bpy.data.collections.new("CH_" + new); sc.collection.children.link(c)
    rig = None
    objs = [o for o in td.objects if o]
    arms = [o for o in objs if o.type == 'ARMATURE']
    rig = max(arms, key=lambda r: sum(1 for ch in r.children if ch.type == 'MESH'))
    for o in objs:
        if o.type == 'ARMATURE' and o != rig: bpy.data.objects.remove(o); continue
        if o.parent is None and o != rig: bpy.data.objects.remove(o); continue
        c.objects.link(o); o.hide_render = False; o.hide_viewport = False
    if new != cid:
        for o in list(c.objects):
            if o.type == 'ARMATURE': o.name = new
            else: o.name = new + "." + o.name.split(".", 1)[1]
    return rig

def eye_fix_all():
    for g in bpy.data.node_groups:
        if not g.name.startswith("EnhancedEye") or g.nodes.get("CorneaTransparentMix"): continue
        Pn = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None)
        OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
        if not Pn or not OUTN: continue
        tl = [l for l in g.links if l.to_node == Pn and l.to_socket.name == "Transmission Weight"]
        src = tl[0].from_socket if tl else None
        for l in tl: g.links.remove(l)
        Pn.inputs["Transmission Weight"].default_value = 0.0
        ol = [l for l in g.links if l.from_node == Pn and l.to_node == OUTN]
        if not ol: continue
        out_sock = ol[0].to_socket; g.links.remove(ol[0])
        tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
        if src: g.links.new(src, mx.inputs[0])
        else: mx.inputs[0].default_value = 0.0
        g.links.new(Pn.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
        print("EYEFIX", g.name)

def tint(rig, key, rgb, mode='MULTIPLY', fac=1.0):
    for ch in rig.children:
        if ch.type == 'MESH' and key in ch.name:
            for i, m in enumerate(ch.data.materials):
                if not m: continue
                m = m.copy(); ch.data.materials[i] = m; nt = m.node_tree
                done = False
                for nd in list(nt.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "normal" not in nd.image.name.lower() and nd.outputs['Color'].links:
                        for lk in list(nd.outputs['Color'].links):
                            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = mode
                            mx.inputs['Factor'].default_value = fac; mx.inputs['B'].default_value = (*rgb, 1)
                            nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], lk.to_socket); done = True
                if not done:
                    for nd in nt.nodes:
                        if nd.type == 'BSDF_PRINCIPLED' and not nd.inputs["Base Color"].links:
                            nd.inputs["Base Color"].default_value = (*rgb, 1)

RIGS = {}; HUM = {}; CUR_WIN = None
def setup(cid, new=None):
    rig = load_char(cid, new); name = new or cid
    R = make_human_ctrl(rig); add_hand_limits(rig)
    for s in "LR":   # MPFB rest elbow ~46 deg: open the IK limit so arms can straighten (LESSONS 8)
        lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(110)
    H = Human(R); RIGS[name] = rig; HUM[name] = H
    if CUR_WIN:
        f0, f1 = CUR_WIN
        for ob in [rig] + list(rig.children):
            for f, show in ((1, f0 <= 1), (f0, True), (f1 + 1, False)):
                if f < 1: continue
                ob.hide_render = not show; ob.hide_viewport = not show
                ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)
    rig["char"] = name
    return rig, R, H

def catchlight(rig, cam, f_on, f_off):
    """small camera-only point light near the lens for an eye catchlight (LESSONS 8)"""
    l = bpy.data.lights.new("Catch_" + cam.name, 'POINT'); l.energy = 0.6; l.shadow_soft_size = 0.02
    o = bpy.data.objects.new("Catch_" + cam.name, l); sc.collection.objects.link(o); o.parent = cam; o.location = (0.05, 0.06, 0)
    o.visible_diffuse = o.visible_glossy = True
    return o

# ------------------------------------------------------------------ cameras, markers, visibility
CAMS = []
def cam_shot(name, f0, f1, keys, lens=35, fstop=8.0, focus=None):
    """keys: list of (frame, loc, target); smooth Bezier between; horizon level (track-quat with world up)"""
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.data.lens = lens; c.data.clip_start = 0.01; c.data.sensor_fit = 'AUTO'
    c.data.dof.use_dof = True; c.data.dof.aperture_fstop = fstop
    for f, loc, tgt in keys:
        c.location = loc; d = Vector(tgt) - Vector(loc)
        c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
        c.data.dof.focus_distance = d.length if focus is None else focus; c.data.dof.keyframe_insert("focus_distance", frame=f)
    m = sc.timeline_markers.new(name, frame=f0); m.camera = c
    CAMS.append((name, f0, f1, c))
    return c

def vis(o, f, show):
    for ob in [o] + list(o.children_recursive):
        ob.hide_render = not show; ob.hide_viewport = not show
        ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)

def keyconst(fc_owner):
    pass

def set_interp(obj, kind='CONSTANT', path=None):
    ad = obj.animation_data
    if not ad or not ad.action: return
    for fc in _fcurves(ad.action):
        if path is None or fc.data_path == path:
            for k in fc.keyframe_points: k.interpolation = kind

def _fcurves(act):
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out

def breathe(H, f0, f1, base_flex=0.0, twist=0.0, head=(0.0, 0.0), amp=1.6, period=200, extra=None, step=20):
    """slow breathing + small head drift so no hold is frozen (keys every `step` frames)"""
    for f in range(f0, f1 + 1, step):
        ph = math.sin(2 * math.pi * (f - f0) / period)
        hx, hz = head(f) if callable(head) else head
        H.key_spine(f, flex=base_flex + amp * ph, twist=twist, head=(hx + 0.5 * ph, hz))

def pole(R, s, f, W):
    n = "Pole_elbow." + s; pb = R.PB[n]
    pb.location = R.rest(n).to_3x3().inverted() @ (Vector(W) - R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)

def knee_pole(R, s, f, W):
    n = "Pole_knee." + s; pb = R.PB[n]
    pb.location = R.rest(n).to_3x3().inverted() @ (Vector(W) - R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)

def foot_at(R, H, s, f, W, yaw=0.0, pitch=0.0):
    a_ = H.ankle[s]
    M = Matrix.Translation(Vector(W)) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X') @ Matrix.Translation(-a_) @ R.rest("IK_foot." + s)
    R.key_world("IK_foot." + s, f, M)

def child_of_hand(obj, rig, side, f_on, f_off=None):
    """Child Of the hand bone from f_on (grip), off at f_off (release); keyed influence"""
    c = obj.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "wrist." + side; c.name = "Grip_" + side
    sc.frame_set(f_on); bpy.context.view_layer.update()
    c.inverse_matrix = (rig.matrix_world @ rig.pose.bones["wrist." + side].matrix).inverted()
    c.influence = 0.0; c.keyframe_insert("influence", frame=f_on - 1)
    c.influence = 1.0; c.keyframe_insert("influence", frame=f_on)
    if f_off:
        c.influence = 1.0; c.keyframe_insert("influence", frame=f_off - 1); c.influence = 0.0; c.keyframe_insert("influence", frame=f_off)
    return c

