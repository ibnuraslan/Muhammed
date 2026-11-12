"""Head-worn items + theatre dressing (director notes 22:41).  blender -b film.blend --python 03d_props.py -- <assets_dir> <out.blend>
- officers: CC-BY peaked cap on the head bone
- surgeons: cap + mask as offset shells of their own body mesh (same armature deform -> no gaps, no clipping)
- patient drape (surgery) and a too-short blanket (beat 10), also body shells
- operating lamp (CC-BY) replaces the industrial lamp"""
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; A, OUT = a[0], a[1]
R_ = math.radians; OB = bpy.data.objects; sc = bpy.context.scene

def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]

def copy_vis(dst, src):
    """same hide_render keys as src"""
    dst.hide_render = src.hide_render
    for fc in fcurves(src):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points:
                dst.hide_render = bool(kp.co.y); dst.keyframe_insert("hide_render", frame=int(kp.co.x))
    for fc in fcurves(dst):
        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"

def vis(o, ranges):
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    for f0, f1 in ranges:
        o.hide_render = False; o.keyframe_insert("hide_render", frame=f0)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=f1 + 1)
    for fc in fcurves(o):
        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"

def cloth(name, rgb, rough=0.7):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Sheen Weight"].default_value = 0.4
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 400; bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.1; nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])
    return m

def shell(char, name, keep, offset, mat, thick=0.003):
    body = OB[char + ".body"]; rig = OB["RIG_" + char]
    o = body.copy(); o.data = body.data.copy(); o.name = name; body.users_collection[0].objects.link(o)
    o.animation_data_clear()
    for md in [m for m in o.modifiers if m.type == "MASK" and m.name.startswith("Delete")]: o.modifiers.remove(md)
    me = o.data; B = rig.data.bones
    if me.shape_keys:   # bake the phenotype targets first so the region test uses the real (morphed) head
        import numpy as np
        kb = me.shape_keys.key_blocks; n = len(me.vertices); base = np.empty(n * 3); kb[0].data.foreach_get("co", base); mix = base.copy()
        for k in kb[1:]:
            if k.mute or k.value == 0: continue
            c = np.empty(n * 3); k.data.foreach_get("co", c); ref = np.empty(n * 3); (k.relative_key or kb[0]).data.foreach_get("co", ref)
            mix += k.value * (c - ref)
        o.shape_key_clear(); me.vertices.foreach_set("co", mix); me.update()
    vg_body = me.vertices and o.vertex_groups.get("body")
    bm = bmesh.new(); bm.from_mesh(me); dl = bm.verts.layers.deform.active
    gi = vg_body.index if vg_body else None
    kill = [v for v in bm.verts if not keep(v.co, B) or (gi is not None and dl and v[dl].get(gi, 0.0) < 0.5)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(me); bm.free()
    if me.shape_keys:
        o.shape_key_clear()
    me.materials.clear(); me.materials.append(mat)
    d = o.modifiers.new("offset", "DISPLACE"); d.strength = offset; d.mid_level = 0.0; d.direction = "NORMAL"
    with bpy.context.temp_override(object=o): bpy.ops.object.modifier_move_to_index(modifier="offset", index=0)
    so = o.modifiers.new("thick", "SOLIDIFY"); so.thickness = thick; so.offset = 1.0
    for m in o.modifiers:
        if m.type == "MASK" and m.name == "Hide helpers": o.modifiers.remove(m); break
    copy_vis(o, body)
    return o

# ---------------------------------------------------------------- surgeons: cap + mask
CAPM = cloth("M_SurgCap", (0.45, 0.7, 0.66)); MASKM = cloth("M_SurgMask", (0.85, 0.9, 0.88))
for ch in ("Surgeon1", "Surgeon2", "Nurse"):
    B = OB["RIG_" + ch].data.bones
    eye = B["eye.L"].head_local; top = B["head"].tail_local
    brow = eye.z + 0.022
    shell(ch, ch + "_Cap", lambda co, B, brow=brow, eye=eye: co.z > brow + 0.008 or (co.z > eye.z + 0.005 and co.y > eye.y + 0.09), 0.009, CAPM, 0.003)
    if ch != "Nurse":
        chin = B["jaw"].tail_local
        shell(ch, ch + "_Mask", lambda co, B, eye=eye, chin=chin: (chin.z - 0.01 < co.z < eye.z - 0.012) and co.y < eye.y + 0.045, 0.008, MASKM, 0.003)
    hair = next((o for o in OB if o.parent == OB["RIG_" + ch] and o.name.split(".")[-1].startswith(("short", "bob"))), None)
    if hair: hair.hide_render = True; [setattr(hair, "hide_render", True)]
    for fc in fcurves(hair) if hair else []:
        for kp in fc.keyframe_points: kp.co.y = 1.0
# ---------------------------------------------------------------- patient drape + short blanket (hero)
HB = OB["RIG_Hero"].data.bones
sh_z = HB["upperarm01.L"].head_local.z; knee_z = HB["lowerleg01.L"].head_local.z; ank_z = HB["foot.L"].head_local.z
DRAPE = cloth("M_Drape", (0.42, 0.62, 0.55)); BLANKET = cloth("M_Blanket", (0.82, 0.78, 0.68), 0.85)
dr = shell("Hero", "Hero_Drape", lambda co, B: ank_z + 0.05 < co.z < sh_z - 0.06 and abs(co.x) < 0.22 + (0.1 if co.z < 0.5 else 0), 0.035, DRAPE, 0.004)
bl = shell("Hero", "Hero_Blanket", lambda co, B: knee_z - 0.02 < co.z < sh_z - 0.1 and abs(co.x) < 0.24, 0.04, BLANKET, 0.006)
for o in (dr, bl): o.animation_data_clear()
vis(dr, [(1482, 1712)]); vis(bl, [(1713, 1857)])
# ---------------------------------------------------------------- officer peaked caps (CC-BY) on the head bone
def imp(path):
    before = set(OB); bpy.ops.import_scene.gltf(filepath=path); return [o for o in OB if o not in before]
for ch in ():   # officer caps disabled for v002: see README known issues
    new = imp(f"{A}/models/ofcap.glb"); ms = [o for o in new if o.type == "MESH"]
    for o in new:
        if o.type != "MESH": bpy.data.objects.remove(o, do_unlink=True)
    cap = ms[0]
    for o in ms[1:]: bpy.data.objects.remove(o, do_unlink=True)
    me = cap.data; me.transform(cap.matrix_world); cap.matrix_world = Matrix.Identity(4)
    bb = [v.co for v in me.vertices]; mn = Vector([min(c[i] for c in bb) for i in range(3)]); mx = Vector([max(c[i] for c in bb) for i in range(3)])
    s = 0.255 / (mx - mn).x
    me.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    rig = OB["RIG_" + ch]; hb = rig.data.bones["head"]
    cap.parent = rig; cap.parent_type = "BONE"; cap.parent_bone = "head"
    eye = rig.data.bones["eye.L"].head_local
    # bone space: +Y along the bone (up); cap base 1.5 cm above the brows
    cap.matrix_parent_inverse = Matrix.Identity(4)
    cap.location = (0.0, (eye.z + 0.05) - hb.tail_local.z, 0.0); cap.rotation_euler = (R_(-90), 0, 0)   # verified in close-up: crown up, visor forward; cap.name = ch + "_Cap"
    for m in me.materials:
        b = m.node_tree.nodes.get("Principled BSDF")
        if b: b.inputs["Roughness"].default_value = 0.6
    copy_vis(cap, OB[ch + ".body"])
# ---------------------------------------------------------------- operating lamp (CC-BY) replaces the industrial lamp
for o in [o for o in OB if o.name.startswith("hanging_industrial_lamp")]: bpy.data.objects.remove(o, do_unlink=True)
new = imp(f"{A}/models/orlamp.glb"); root = bpy.data.objects.new("ORLamp", None); OB["Bed"].users_collection[0].objects.link(root)
pts = [o.matrix_world @ Vector(b) for o in new if o.type == "MESH" for b in o.bound_box]
mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
s = 1.6 / (mx - mn).x
for o in new:
    if o.parent is None: o.parent = root; o.matrix_parent_inverse = Matrix.Scale(s, 4) @ Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mx.z)))
root.location = (6.9, 0.9, 3.2)
for o in new:
    if o.type == "MESH":
        for m in o.data.materials:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b: b.inputs["Roughness"].default_value = max(0.3, b.inputs["Roughness"].default_value)
print("PROPS done", (mx - mn) * s)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
