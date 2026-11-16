"""BalconyToddler: asset library. Characters are re-dressed copies of MPFB characters from ToddlerWell_v008
(MakeHuman's asset server is down from this container). Everything at the origin; 02_build.py places it.
blender -b --factory-startup --python 01_lib.py -- <polyhaven_dir> <out_lib.blend>"""
import bpy, sys, math, os
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
PH, OUT = a
B = "/home/user/Muhammed/blender/"
R_ = math.radians
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    return c
def move_to(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)

SRC = B + "ToddlerWell_v008/ToddlerWell_v008_60fps.blend"
def append_char(rn, new, drop=()):
    with bpy.data.libraries.load(SRC) as (src, dst):
        dst.objects = [n for n in src.objects if n == rn or (n.startswith(rn + ".") and "_dup" not in n)]
    c = coll("CHAR_" + new); rig = None
    for o in dst.objects:
        if o is None: continue
        if any(d in o.name for d in drop):
            bpy.data.objects.remove(o, do_unlink=True); continue
        c.objects.link(o)
        if o.type == 'ARMATURE': rig = o
    for o in list(c.objects):
        if o.type != 'ARMATURE' and o.parent is not rig: bpy.data.objects.remove(o, do_unlink=True)
    for o in [rig] + list(rig.children):
        if o.animation_data: o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys and o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
        for cns in list(o.constraints): o.constraints.remove(cns)
    for pb in rig.pose.bones:
        for cns in list(pb.constraints): pb.constraints.remove(cns)
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1); rig.name = new
    # remove extra bones added by an earlier control pass (IK_/Pole_), make_human_ctrl adds them again
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in list(rig.data.edit_bones):
        if eb.name.startswith(("IK_", "Pole_")): rig.data.edit_bones.remove(eb)
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in rig.children:
        o.name = new + "." + o.name.split(".", 1)[1]
        o.hide_render = o.hide_viewport = False
    print("LIB char", new, [o.name for o in rig.children], tuple(round(v, 3) for v in rig.scale))
    return rig

def tint(rig, key, rgb, rough=0.6, keep_tex=0.25):
    for ch in rig.children:
        if ch.type != 'MESH' or key not in ch.name: continue
        for i, m in enumerate(ch.data.materials):
            m = m.copy(); ch.data.materials[i] = m
            nt = m.node_tree
            P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image and 'diffuse' in n.image.name.lower()), None)
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
            if tex:
                hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
                bc = nt.nodes.new('ShaderNodeBrightContrast'); bc.inputs['Bright'].default_value = 0.25; bc.inputs['Contrast'].default_value = -0.3
                nt.links.new(tex.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], bc.inputs['Color'])
                nt.links.new(bc.outputs['Color'], mx.inputs['A'])
            else:
                mx.inputs['A'].default_value = (1, 1, 1, 1)
            for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
            nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
            P.inputs['Roughness'].default_value = rough
            for l in list(P.inputs['Roughness'].links): nt.links.remove(l)

TOD = append_char("Toddler", "Toddler")
tint(TOD, "casualsuit", (0.98, 0.90, 0.62))     # pale-yellow sleepsuit (reference: cream pyjamas)
tint(TOD, "shoes", (0.30, 0.55, 0.85))
MAN = append_char("Teen", "Man", drop=("Torch", "torch"))
tint(MAN, "casualsuit", (0.22, 0.32, 0.55))     # navy T-shirt + trousers
tint(MAN, "shoes", (0.15, 0.12, 0.10))
GMA = append_char("Crowd1", "Grandma")
tint(GMA, "casualsuit", (0.92, 0.50, 0.50))     # pink top (reference)
tint(GMA, "bob02", (0.42, 0.42, 0.44), 0.55)    # grey hair
# part the fringe: lift the central fringe (between the eyes) to a line above the brows so both eyes show
eyes = bpy.data.objects["Grandma.high-poly"]; hair = bpy.data.objects["Grandma.bob02"]
ev_ = [v.co for v in eyes.data.vertices]; EZ = sum(p.z for p in ev_) / len(ev_); EY = min(p.y for p in ev_)
n_ = 0
for v in hair.data.vertices:
    if abs(v.co.x) < 0.085 and v.co.y < EY + 0.07 and v.co.z < EZ + 0.06:
        v.co.z = EZ + 0.06 + (abs(v.co.x) * 0.25); n_ += 1
print("LIB fringe lifted", n_, round(EZ, 3), round(EY, 3))
tint(GMA, "shoes", (0.25, 0.20, 0.18))
OLD = append_char("Crowd2", "OldMan")
tint(OLD, "casualsuit", (0.90, 0.90, 0.88))     # white shirt
tint(OLD, "shoes", (0.18, 0.15, 0.12))
WOM = append_char("Crowd4", "Woman")
tint(WOM, "sportsuit", (0.20, 0.55, 0.45))      # teal-green top (reference)
tint(WOM, "shoes", (0.9, 0.9, 0.9))
YM = append_char("Crowd3", "YoungMan")
tint(YM, "casualsuit", (0.85, 0.55, 0.15))      # mustard jacket
tint(YM, "shoes", (0.15, 0.15, 0.15))
MOM = append_char("Mother", "Lady")
tint(MOM, "elegantsuit", (0.95, 0.80, 0.25))    # yellow
CAST = [TOD, MAN, GMA, OLD, WOM, YM, MOM]

# eye fix (LegoInNose eye_fix.py a44130b) on every EnhancedEye group
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    if any(n.name.startswith("CorneaTransparentMix") for n in g.nodes): continue
    P = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None)
    OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
    if not P or not OUTN: continue
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    srcs = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN]
    if not ol: continue
    out_sock = ol[0].to_socket; g.links.remove(ol[0])
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if srcs: g.links.new(srcs, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    print("LIB eyefix", g.name)
print("LIB eye materials", sorted({m.name for r in CAST for ch in r.children if "high-poly" in ch.name for m in ch.data.materials}))

# ------------------------------------------------------------------ Poly Haven models
def ph_model(pid, keep=None):
    f = f"{PH}/{pid}/{pid}_1k.blend"
    with bpy.data.libraries.load(f) as (src, dst): dst.objects = list(src.objects)
    out = []
    for o in dst.objects:
        if o and o.type == 'MESH' and (keep is None or keep(o.name)):
            coll("PROPS").objects.link(o); o.name = "PH_" + o.name; out.append(o)
            print("LIB ph", o.name, tuple(round(v, 3) for v in o.dimensions), tuple(round(v, 2) for v in o.location))
    return out
for pid in ("painted_wooden_chair_01", "WoodenTable_01", "exterior_aircon_unit", "potted_plant_02", "street_lamp_01", "fire_hydrant"):
    ph_model(pid)
for o in coll("PROPS").objects:
    o.parent = None
# textures
for tid in ("plastered_wall", "laminate_floor", "concrete_pavement", "asphalt_02", "painted_plaster_wall"):
    for fn in sorted(os.listdir(f"{PH}/{tid}/textures")):
        if "disp" in fn: continue
        im = bpy.data.images.load(f"{PH}/{tid}/textures/{fn}"); im.name = f"TX_{tid}_" + fn[len(tid) + 1:].rsplit("_", 1)[0]
        im.use_fake_user = True
        if "nor" in fn or "rough" in fn or "disp" in fn: im.colorspace_settings.name = 'Non-Color'
        print("LIB tex", im.name)
# wooden chair: tint the white paint to warm brown wood
for m in bpy.data.objects["PH_painted_wooden_chair_01"].data.materials:
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); lk = P.inputs['Base Color'].links
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs['B'].default_value = (0.62, 0.36, 0.18, 1)
    if lk: nt.links.new(lk[0].from_socket, mx.inputs['A'])
    nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
bpy.ops.file.make_paths_absolute()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("LIB_OK", OUT)
