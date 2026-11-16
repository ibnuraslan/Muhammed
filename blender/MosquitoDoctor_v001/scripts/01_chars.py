"""B22 MosquitoDoctor characters. MakeHuman's asset server is down (502), so the MPFB humans are appended from our own earlier
packages (CC0 MakeHuman/MPFB assets), stripped of animation/control bones, eye fix applied.
blender -b --factory-startup --python 01_chars.py -- out.blend"""
import bpy, sys, glob
OUT = sys.argv[sys.argv.index("--") + 1]
B = "/home/user/Muhammed/blender/"
SRC = [("SpeakWithoutSight_v006", {"Father": "Doctor"}), ("CaveRescue_v010", {"Boy1": "Boy"}),
       ("RingBullet_v008", {"Owner": "ColA"}), ("TitanicIceberg_v014", {"ExpertA": "ColB"}),
       ("FanCancer_v011", {"Nurse": "Nurse"}), ("CaveRescue_v010", {"Boy3": "PatA"}), ("Tsunami2004_v012", {"OldM": "PatB"})]
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
CTRL = ("IK_", "Pole_")
for pkg, names in SRC:
    path = glob.glob(B + pkg + "/*_60fps.blend")[0]
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in names or (n.split(".")[0] in names and "." in n)]
    for o in dst.objects:
        if o is None: continue
        base = o.name.split(".")[0]
        if base not in names: continue
        if o.type not in ('ARMATURE', 'MESH'): continue
        bpy.context.scene.collection.objects.link(o)
        new = names[base]
        o.name = new if o.type == 'ARMATURE' else new + "." + o.name.split(".", 1)[1]
for o in list(bpy.data.objects):
    if o.type == 'MESH' and (o.parent is None or o.parent.type != 'ARMATURE'):
        bpy.data.objects.remove(o, do_unlink=True); continue
    o.animation_data_clear()
    if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
    o.hide_render = False; o.hide_viewport = False; o.hide_set(False)
    if o.type == 'ARMATURE':
        bpy.context.view_layer.objects.active = o
        for pb in o.pose.bones:
            for c in list(pb.constraints): pb.constraints.remove(c)
            pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in list(o.data.edit_bones):
            if eb.name.startswith(CTRL): o.data.edit_bones.remove(eb)
        bpy.ops.object.mode_set(mode='OBJECT')
        o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
        for c in list(o.constraints): o.constraints.remove(c)
    for c in list(getattr(o, "constraints", [])):
        if o.type != 'ARMATURE': o.constraints.remove(c)
    o.hide_render = False; o.hide_viewport = False
# eye fix on any EnhancedEye group lacking it (LESSONS 3)
for g in bpy.data.node_groups:
    if g.name.startswith("EnhancedEye") and not any(n.name.startswith("CorneaTransparentMix") for n in g.nodes):
        print("EYEFIX applying to", g.name)
        P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
        tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]; src = tl[0].from_socket if tl else None
        for l in tl: g.links.remove(l)
        P.inputs["Transmission Weight"].default_value = 0.0
        ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; out_sock = ol.to_socket; g.links.remove(ol)
        tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
        if src: g.links.new(src, mx.inputs[0])
        g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
print("EYEFIX groups", [g.name for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")],
      [any(n.name.startswith("CorneaTransparentMix") for n in g.nodes) for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")])
for i, n in enumerate(["Doctor", "Boy", "ColA", "ColB", "Nurse", "PatA", "PatB"]):
    r = bpy.data.objects[n]; r.location.x = 50 + i * 1.2
    print("CHAR", n, round(r.data.bones["head"].tail_local.z, 2), [c.name for c in r.children],
          [ (c.name, [m.name for m in c.data.materials]) for c in r.children if c.name.endswith("eyes") or "high-poly" in c.name])
# eyelashes: thin dark-brown lashes (director: blue eyeliner / lash spikes / doll eyes)
for o in bpy.data.objects:
    if o.type == 'MESH' and "eyelashes" in o.name:
        for sl in o.material_slots:
            m = sl.material.copy(); sl.material = m; nt = m.node_tree
            P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); tx = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
            for l in list(P.inputs["Base Color"].links): nt.links.remove(l)
            for l in list(P.inputs["Alpha"].links): nt.links.remove(l)
            P.inputs["Base Color"].default_value = (0.06, 0.04, 0.03, 1); P.inputs["Roughness"].default_value = 0.6
            mu = nt.nodes.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 0.6
            nt.links.new(tx.outputs["Alpha"], mu.inputs[0]); nt.links.new(mu.outputs[0], P.inputs["Alpha"])
        print("LASH", o.name)
# ColA (bald) gets a copy of the doctor's short02 hair, fitted by the eye frame, tinted grey-brown
def frame(r):
    B = r.data.bones; e = (B["eye.L"].head_local + B["eye.R"].head_local) / 2
    return B["head"].head_local, (B["eye.L"].head_local - B["eye.R"].head_local).length
src = bpy.data.objects["Doctor.short02"]; dst = bpy.data.objects["ColA"]
h0, s0 = frame(bpy.data.objects["Doctor"]); h1, s1 = frame(dst); k = s1 / s0 * 1.03
hair = src.copy(); hair.data = src.data.copy(); bpy.context.scene.collection.objects.link(hair)
for v in hair.data.vertices: v.co = h1 + (v.co - h0) * k
hair.parent = dst; hair.name = "ColA.short02"
for m in hair.modifiers:
    if m.type == 'ARMATURE': m.object = dst
for sl in hair.material_slots:
    m = sl.material.copy(); sl.material = m; nt = m.node_tree; P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    if P.inputs["Base Color"].links:
        s_ = P.inputs["Base Color"].links[0].from_socket; hs = nt.nodes.new("ShaderNodeHueSaturation")
        hs.inputs["Saturation"].default_value = 0.35; hs.inputs["Value"].default_value = 1.15
        nt.links.new(s_, hs.inputs["Color"]); nt.links.new(hs.outputs["Color"], P.inputs["Base Color"])
print("HAIR ColA", round(k, 3))
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
