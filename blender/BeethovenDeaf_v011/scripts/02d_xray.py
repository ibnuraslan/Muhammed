# 02d: the x-ray window on the right side of his face (camera side). Skin, hair and brows inside a soft sphere turn to clear
# glass with a cyan rim; inside sits a real skull (CC-BY) fitted to his head with the jaw opened on the rod, and the
# middle/inner ear (CC-BY) at his right ear. Vibration pulses run teeth -> jawbone -> skull -> inner ear; the skull lights up
# in a travelling wave; a red pulse in the ear canal dies at the torn eardrum while the cyan path bypasses it; the cochlea
# lights up on "hear clearly". Anatomy only renders inside the window and only while it is open.
def vis(o, f, show):
    key_vis([o], f, show)
    for fc in iter_fcurves(o.animation_data.action):
        if "hide" in fc.data_path:
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
with bpy.data.libraries.load(SRC) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith(("SRC_XRay_Skull", "SRC_Ear_"))]
XR_C = bpy.data.collections["XRay"]
HR = BN["head"].matrix_local.copy(); HRi = HR.inverted()
def head_child(o):
    """o placed in armature REST space; follows the head bone"""
    c = o.constraints.new('CHILD_OF'); c.target = COMP; c.subtarget = "head"; c.inverse_matrix = HRi
    return c
# ---- rest-space landmarks from the body mesh
dom = {}
gi = {g.index: g.name for g in CB.vertex_groups}
BONESET = {b.name for b in BN}
HELP = {i for i, n in gi.items() if n in ("HelperGeometry", "JointCubes")}
for v in CB.data.vertices:
    gs = [g for g in v.groups if gi.get(g.group) in BONESET]
    best = max(gs, key=lambda g: g.weight, default=None)
    dom[v.index] = None if any(g.group in HELP and g.weight > 0.5 for g in v.groups) else (gi.get(best.group) if best else None)
FACE = ("head", "jaw", "special", "oris", "levator", "orbicularis", "oculi", "temporalis", "risorius", "eye", "tongue")
headv = [v.co.copy() for v in CB.data.vertices if (dom[v.index] or "").startswith(FACE)]
earR = [p for p in headv if p.x < -0.068 and -0.05 < p.y < 0.04 and 1.50 < p.z < 1.64]
EAR_C = sum(earR, Vector()) / max(1, len(earR))
log("right ear centre (rest)", tuple(round(x, 3) for x in EAR_C), len(earR))
BITE_REST = HR @ BITE_HEAD
# ---- skull: fit width + incisal edge to his teeth, open its jaw on the rod
sk = [o for o in dst.objects if o.name == "SRC_XRay_Skull"][0]; sk.name = "XR_Skull"; XR_C.objects.link(sk)
me = sk.data
xs = [v.co for v in me.vertices]
mn = Vector([min(p[i] for p in xs) for i in range(3)]); mx = Vector([max(p[i] for p in xs) for i in range(3)])
H_CHIN = min(p.z for p in headv if abs(p.x) < 0.02 and p.y < -0.06)
s_ = ((max(p.z for p in headv) - 0.012) - (H_CHIN + 0.010)) / (mx.z - mn.z)
for v in me.vertices: v.co = (v.co - Vector(((mn.x + mx.x) / 2, 0, 0))) * s_
xs = [v.co for v in me.vertices]
H_TOP = max(p.z for p in headv); H_FRONT = min(p.y for p in headv if abs(p.x) > 0.02)     # face front beside the nose
off = Vector((0, (H_FRONT + 0.010) - min(p.y for p in xs), (H_TOP - 0.012) - max(p.z for p in xs)))
for v in me.vertices: v.co += off
xs = [v.co for v in me.vertices]
log("skull bbox rest", [round(min(p[i] for p in xs), 3) for i in range(3)], [round(max(p[i] for p in xs), 3) for i in range(3)], "head top/front", round(H_TOP, 3), round(H_FRONT, 3))
# jaw opening: smooth rotation of the mandible about the TMJ (front-down), same angle as his jaw
yt = BITE_REST.y + 0.082; zt = BITE_REST.z + 0.030
ang = -math.radians(JAW_OPEN + 1.0)
for v in me.vertices:
    zr = v.co.z - BITE_REST.z; 
    if zr > 0.004 or v.co.y > yt + 0.01: continue
    w = smoothstep((0.004 - zr) / 0.014) * smoothstep((yt + 0.01 - v.co.y) / 0.025)
    a_ = ang * w; dy, dz = v.co.y - yt, v.co.z - zt
    v.co.y = yt + dy * math.cos(a_) - dz * math.sin(a_); v.co.z = zt + dy * math.sin(a_) + dz * math.cos(a_)
log("skull fitted: scale", round(s_, 3), "incisal z", round(BITE_REST.z, 3))
sk.matrix_world = Matrix.Identity(4); head_child(sk)
# clean bone look + travelling glow wave from the bite point
bm_ = bpy.data.materials.new("M_XR_Bone"); bm_.use_nodes = True; nt = bm_.node_tree; N_ = nt.nodes; Ln = nt.links
p = N_["Principled BSDF"]; p.inputs["Base Color"].default_value = (0.66, 0.50, 0.30, 1); p.inputs["Roughness"].default_value = 0.45
p.inputs["Coat Weight"].default_value = 0.4; p.inputs["Subsurface Weight"].default_value = 0.15
WAVE = empty("XR_WaveCentre", BITE_REST, size=0.01); head_child(WAVE)
tc = N_.new("ShaderNodeTexCoord"); tc.object = WAVE
ln_ = N_.new("ShaderNodeVectorMath"); ln_.operation = 'LENGTH'; Ln.new(tc.outputs["Object"], ln_.inputs[0])
wr_ = N_.new("ShaderNodeValue"); wr_.name = "WaveR"; wr_.outputs[0].default_value = -1.0
sub = N_.new("ShaderNodeMath"); sub.operation = 'SUBTRACT'; Ln.new(ln_.outputs[1], sub.inputs[0]); Ln.new(wr_.outputs[0], sub.inputs[1])
ab = N_.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; Ln.new(sub.outputs[0], ab.inputs[0])
mr = N_.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.022
mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0; Ln.new(ab.outputs[0], mr.inputs["Value"])
gl = N_.new("ShaderNodeValue"); gl.name = "Glow"; gl.outputs[0].default_value = 0.0
ad = N_.new("ShaderNodeMath"); ad.operation = 'ADD'; Ln.new(mr.outputs["Result"], ad.inputs[0]); Ln.new(gl.outputs[0], ad.inputs[1])
st_ = N_.new("ShaderNodeMath"); st_.operation = 'MULTIPLY'; st_.inputs[1].default_value = 3.0; Ln.new(ad.outputs[0], st_.inputs[0])
Ln.new(st_.outputs[0], p.inputs["Emission Strength"]); p.inputs["Emission Color"].default_value = (0.25, 0.9, 1.0, 1)
me.materials.clear(); me.materials.append(bm_)
def keyv(node_out, f, v):
    node_out.default_value = v; node_out.keyframe_insert("default_value", frame=f)
# ---- ear anatomy, mirrored to his RIGHT ear and fitted at the ear canal
ears = [o for o in dst.objects if o.name.startswith("SRC_Ear_")]
canal = [o for o in ears if o.name.endswith("Canal")][0]
cv = [v.co for v in canal.data.vertices]; canal_out = Vector((max(p.x for p in cv), sum(p.y for p in cv) / len(cv), sum(p.z for p in cv) / len(cv)))
target = Vector((EAR_C.x + 0.014, EAR_C.y + 0.004, EAR_C.z - 0.006))
EARS = {}
for o in ears:
    o.name = "XR_" + o.name[4:]; XR_C.objects.link(o)
    for m in list(o.modifiers):
        if m.type == 'SOLIDIFY': pass
    for v in o.data.vertices:
        q = (v.co - canal_out) * 1.9; q.x = -q.x; v.co = target + q
    o.data.flip_normals()
    o.matrix_world = Matrix.Identity(4); head_child(o); EARS[o.name[7:]] = o
log("ear parts", sorted(EARS))
coch = EARS["Labyrinth"]
cm_ = coch.data.materials[0].copy(); coch.data.materials[0] = cm_; cp_ = cm_.node_tree.nodes.get("Principled BSDF") or [n for n in cm_.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
cp_.inputs["Emission Color"].default_value = (1.0, 0.75, 0.2, 1); cp_.inputs["Emission Strength"].default_value = 0.0
cvs = [v.co for v in coch.data.vertices]; COCH_C = sum(cvs, Vector()) / len(cvs)
CUT = empty("XR_EarCut", target + Vector((0.004, 0, 0)), size=0.01); head_child(CUT)
_o = [n for n in N_ if n.type == 'OUTPUT_MATERIAL'][0]; _src = _o.inputs["Surface"].links[0].from_socket
tcc = N_.new("ShaderNodeTexCoord"); tcc.object = CUT
lc = N_.new("ShaderNodeVectorMath"); lc.operation = 'LENGTH'; Ln.new(tcc.outputs["Object"], lc.inputs[0])
rc = N_.new("ShaderNodeMapRange"); rc.inputs["From Min"].default_value = 0.040; rc.inputs["From Max"].default_value = 0.044
rc.inputs["To Min"].default_value = 1.0; rc.inputs["To Max"].default_value = 0.0; Ln.new(lc.outputs[1], rc.inputs["Value"])
trc = N_.new("ShaderNodeBsdfTransparent"); mxc = N_.new("ShaderNodeMixShader")
Ln.new(rc.outputs["Result"], mxc.inputs["Fac"]); Ln.new(_src, mxc.inputs[1]); Ln.new(trc.outputs["BSDF"], mxc.inputs[2]); Ln.new(mxc.outputs["Shader"], _o.inputs["Surface"])
drum = EARS["Eardrum"]; dvs = [v.co for v in drum.data.vertices]; DRUM_C = sum(dvs, Vector()) / len(dvs)
# ---- the x-ray window shader (approved LegoInNose v013 recipe): glass skin with a cyan rim inside a soft sphere
at = CB.data.attributes.get("xr") or CB.data.attributes.new("xr", 'FLOAT', 'POINT')
for v in CB.data.vertices: at.data[v.index].value = 1.0 if (dom[v.index] or "").startswith(FACE + ("neck03",)) else 0.0
XC = empty("XR_Window", (EAR_C.x + 0.02, (EAR_C.y + BITE_REST.y) / 2 + 0.005, (EAR_C.z + BITE_REST.z) / 2 - 0.005), size=0.02); head_child(XC)
XC.scale = (0.092, 0.092, 0.092)
g = bpy.data.node_groups.new("XRayWin", 'ShaderNodeTree')
g.interface.new_socket("Shader", in_out='INPUT', socket_type='NodeSocketShader')
g.interface.new_socket("Mask", in_out='INPUT', socket_type='NodeSocketFloat')
g.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
gi_ = g.nodes.new("NodeGroupInput"); go_ = g.nodes.new("NodeGroupOutput"); L_ = g.links
tc = g.nodes.new("ShaderNodeTexCoord"); tc.object = XC
ln2 = g.nodes.new("ShaderNodeVectorMath"); ln2.operation = 'LENGTH'; L_.new(tc.outputs["Object"], ln2.inputs[0])
mr2 = g.nodes.new("ShaderNodeMapRange"); mr2.interpolation_type = 'SMOOTHSTEP'
mr2.inputs["From Min"].default_value = 0.72; mr2.inputs["From Max"].default_value = 1.0; mr2.inputs["To Min"].default_value = 1.0; mr2.inputs["To Max"].default_value = 0.0
L_.new(ln2.outputs["Value"], mr2.inputs["Value"])
stv = g.nodes.new("ShaderNodeValue"); stv.name = "XStrength"; stv.outputs[0].default_value = 0.0
m1 = g.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L_.new(mr2.outputs["Result"], m1.inputs[0]); L_.new(gi_.outputs["Mask"], m1.inputs[1])
m2 = g.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L_.new(m1.outputs[0], m2.inputs[0]); L_.new(stv.outputs[0], m2.inputs[1])
tr = g.nodes.new("ShaderNodeBsdfTransparent")
lw = g.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.12
em = g.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.35, 0.85, 1.0, 1); em.inputs["Strength"].default_value = 1.2
rim = g.nodes.new("ShaderNodeMixShader"); L_.new(lw.outputs["Facing"], rim.inputs["Fac"]); L_.new(tr.outputs["BSDF"], rim.inputs[1]); L_.new(em.outputs["Emission"], rim.inputs[2])
geo = g.nodes.new("ShaderNodeNewGeometry"); tr2 = g.nodes.new("ShaderNodeBsdfTransparent")
inner = g.nodes.new("ShaderNodeMixShader"); L_.new(geo.outputs["Backfacing"], inner.inputs["Fac"]); L_.new(rim.outputs["Shader"], inner.inputs[1]); L_.new(tr2.outputs["BSDF"], inner.inputs[2])
fin = g.nodes.new("ShaderNodeMixShader"); L_.new(m2.outputs[0], fin.inputs["Fac"]); L_.new(gi_.outputs["Shader"], fin.inputs[1]); L_.new(inner.outputs["Shader"], fin.inputs[2])
L_.new(fin.outputs["Shader"], go_.inputs[0])
XS = stv.outputs[0]
done = set()
for c_ in COMP.children:
    if c_.type != 'MESH' or "high-poly" in c_.name or "suit" in c_.name or "boots" in c_.name: continue
    for m in c_.data.materials:
        if not m or m.name in done: continue
        done.add(m.name); nt = m.node_tree
        outs = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']; out = ([n for n in outs if n.is_active_output] or outs)[0]
        if not out.inputs["Surface"].links: continue
        src_ = out.inputs["Surface"].links[0].from_socket
        gn = nt.nodes.new("ShaderNodeGroup"); gn.node_tree = g
        nt.links.new(src_, gn.inputs[0]); nt.links.new(gn.outputs[0], out.inputs["Surface"])
        if c_ == CB:
            an = nt.nodes.new("ShaderNodeAttribute"); an.attribute_name = "xr"; nt.links.new(an.outputs["Fac"], gn.inputs["Mask"])
        else:
            gn.inputs["Mask"].default_value = 1.0
# anatomy is only drawn inside the window
def mask_anat(obj):
    for i, m in enumerate(obj.data.materials):
        if m is None: continue
        if m.get("anat_masked"): continue
        m["anat_masked"] = 1
        nt = m.node_tree; out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
        if not out.inputs["Surface"].links: continue
        src_ = out.inputs["Surface"].links[0].from_socket
        tc = nt.nodes.new("ShaderNodeTexCoord"); tc.object = XC
        l3 = nt.nodes.new("ShaderNodeVectorMath"); l3.operation = 'LENGTH'; nt.links.new(tc.outputs["Object"], l3.inputs[0])
        r3 = nt.nodes.new("ShaderNodeMapRange"); r3.interpolation_type = 'SMOOTHSTEP'
        r3.inputs["From Min"].default_value = 0.78; r3.inputs["From Max"].default_value = 0.98; r3.inputs["To Min"].default_value = 1.0; r3.inputs["To Max"].default_value = 0.0
        nt.links.new(l3.outputs["Value"], r3.inputs["Value"])
        tr3 = nt.nodes.new("ShaderNodeBsdfTransparent"); mx3 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(r3.outputs["Result"], mx3.inputs["Fac"]); nt.links.new(tr3.outputs["BSDF"], mx3.inputs[1]); nt.links.new(src_, mx3.inputs[2])
        nt.links.new(mx3.outputs["Shader"], out.inputs["Surface"])
ANAT = [sk] + list(EARS.values())
# ---- vibration path inside the head (rest space): teeth -> jawbone -> angle -> ramus -> TMJ -> cochlea
PATH = [BITE_REST + Vector((-0.004, 0.004, -0.006)), BITE_REST + Vector((-0.030, 0.022, -0.026)), BITE_REST + Vector((-0.050, 0.060, -0.036)),
        BITE_REST + Vector((-0.056, 0.080, -0.008)), BITE_REST + Vector((-0.054, 0.086, 0.022)), COCH_C]
def along(path, u):
    segs = [(path[i], path[i + 1]) for i in range(len(path) - 1)]; Ls = [(b - a).length for a, b in segs]; tot = sum(Ls); d = u * tot
    for (a, b), l in zip(segs, Ls):
        if d <= l: return a.lerp(b, d / l)
        d -= l
    return path[-1]
pulse_m = mat("M_Pulse", (0.3, 0.95, 1.0), emit=((0.25, 0.92, 1.0), 14.0))
red_m = mat("M_PulseRed", (1.0, 0.1, 0.08), emit=((1.0, 0.08, 0.05), 10.0))
PULSES = []
for i in range(8):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0042, segments=16, ring_count=8)
    pu = bpy.context.active_object; pu.name = "XR_Pulse%02d" % i; pu.data.materials.append(pulse_m); bpy.ops.object.shade_smooth()
    for u_ in list(pu.users_collection): u_.objects.unlink(pu)
    XR_C.objects.link(pu); head_child(pu); pu.scale = (0, 0, 0); pu.keyframe_insert("scale", frame=1); PULSES.append(pu)
PT = 54
pstarts = list(range(T["into"] - 4, T["hear"] + 6, 12))
for i, f0 in enumerate(pstarts):
    pu = PULSES[i % len(PULSES)]
    for j in range(0, PT + 1, 3):
        pu.location = along(PATH, j / PT); pu.keyframe_insert("location", frame=f0 + j)
    for fr, s in ((f0 - 1, 0), (f0, 0.6), (f0 + 4, 1.0), (f0 + PT - 4, 1.0), (f0 + PT, 0.0)):
        pu.scale = (s, s, s); pu.keyframe_insert("scale", frame=fr)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0045, segments=16, ring_count=8)
RED = bpy.context.active_object; RED.name = "XR_RedPulse"; RED.data.materials.append(red_m); bpy.ops.object.shade_smooth()
for u_ in list(RED.users_collection): u_.objects.unlink(RED)
XR_C.objects.link(RED); head_child(RED)
r0 = target + Vector((-0.004, 0, 0)); 
for rep, f0 in enumerate((T["bypass"] - 6, T["eardrum"] - 14)):
    for fr, u, s in ((f0 - 1, 0.0, 0.0), (f0, 0.0, 0.8), (f0 + 26, 1.0, 1.0), (f0 + 34, 1.0, 1.25), (f0 + 44, 1.0, 0.0)):
        RED.location = r0.lerp(DRUM_C, u); RED.scale = (s, s, s)
        RED.keyframe_insert("location", frame=fr); RED.keyframe_insert("scale", frame=fr)
RED.scale = (0, 0, 0); RED.keyframe_insert("scale", frame=1)
# ---- timeline
X_ON0, X_ON1 = T["into"] - 10, T["into"] + 26
X_OFF0, X_OFF1 = T["using"] - 34, T["using"] + 4
keyv(XS, 1, 0.0); keyv(XS, X_ON0, 0.0); keyv(XS, X_ON1, 1.0); keyv(XS, X_OFF0, 1.0); keyv(XS, X_OFF1, 0.0)
for o in ANAT + PULSES + [RED]:
    vis(o, 1, False); vis(o, X_ON0, True); vis(o, X_OFF1 + 1, False)
    mask_anat(o)
TEETHS = [c_ for c_ in COMP.children if "teeth" in c_.name or "tongue" in c_.name]
for o in TEETHS:
    vis(o, 1, True); vis(o, X_ON0 + 16, False); vis(o, X_OFF1 - 12, True)
WR = wr_.outputs[0]; GLOW = gl.outputs[0]
keyv(WR, 1, -1.0); keyv(WR, T["sent"] - 6, -0.01); keyv(WR, T["skull"] + 30, 0.20); keyv(WR, T["skull"] + 31, -1.0)
keyv(WR, T["bypass"] + 60, -1.0); 
keyv(GLOW, 1, 0.0); keyv(GLOW, T["sent"], 0.0); keyv(GLOW, T["skull"] + 20, 0.22); keyv(GLOW, T["bypass"] + 10, 0.08); keyv(GLOW, X_OFF0, 0.05)
cs_ = cp_.inputs["Emission Strength"]
keyv(cs_, 1, 0.0); keyv(cs_, T["hear"] - 22, 0.0); keyv(cs_, T["hear"] + 4, 7.0); keyv(cs_, X_OFF1, 5.0)
log("xray on", X_ON0, X_ON1, "off", X_OFF0, X_OFF1, "pulses", len(pstarts))
