"""SodaMan (BellyFat ShopperA rig) + Scientist (SurgeonBrandsLivers Surgeon1 rig), re-dressed.
blender -b --python 01_chars.py"""
import bpy, sys, math, os
from mathutils import Vector
exec(open(os.path.dirname(__file__) + "/common.py").read())
exec(open(PIPE + "/hand_poses.py").read())
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)

def load(path, rigname):
    with bpy.data.libraries.load(path, link=False) as (fd, td):
        td.objects = [n for n in fd.objects if n == rigname or n.startswith(rigname + ".")]
    for o in td.objects: bpy.context.scene.collection.objects.link(o)
    return bpy.data.objects[rigname]

man = load(SCR + "/man_src.blend", "SodaMan")
sci = load(SCR + "/c01.blend", "C01")
sci.name = "Scientist"
for o in list(sci.children):
    o.name = o.name.replace("C01", "Scientist")
# scientist: drop scrubs mesh (suit worn instead)
for o in list(sci.children):
    if "casualsuit01" in o.name: bpy.data.objects.remove(o, do_unlink=True)
for o in man.children + sci.children:
    o.hide_render = False; o.hide_viewport = False

def child(rig, key): return next(o for o in rig.children if key in o.name)

# ---- scientist suit -> lab coat texture
suit = child(sci, "elegantsuit01")
img = bpy.data.images.load(SCR + "/tex/labcoat_suit_diffuse.png"); img.name = "labcoat_suit_diffuse"
for m in suit.data.materials:
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image and "diffuse" in n.image.name: n.image = img
        if n.type == 'MIX_RGB' or n.type == 'MIX':
            pass

# ---- man shirt -> solid light-blue shirt texture (jeans unchanged)
shirt = child(man, "casualsuit03")
timg = bpy.data.images.load(SCR + "/tex/tshirt_jeans_diffuse.png"); timg.name = "tshirt_jeans_diffuse"
for n in shirt.data.materials[0].node_tree.nodes:
    if n.type == 'TEX_IMAGE' and n.image and "diffuse" in n.image.name: n.image = timg

# ---- short sleeves: delete shirt verts past 45% of shoulder->elbow, un-hide the body skin there
A = man.data.bones
def arm_t(co, s):
    """position along shoulder->elbow (0..1, >1 forearm); -9 if the point is not on that arm (far from the arm axis)"""
    sh = A["upperarm01." + s].head_local; wr = A["wrist." + s].head_local; el = A["lowerarm01." + s].head_local
    ax = el - sh; t = (co - sh).dot(ax) / ax.length_squared
    # distance to the shoulder->wrist polyline
    def seg(a, b):
        d = b - a; u = max(0.0, min(1.0, (co - a).dot(d) / d.length_squared)); return (co - (a + d * u)).length
    if min(seg(sh, el), seg(el, wr)) > 0.085: return -9
    return t
import bmesh
bm = bmesh.new(); bm.from_mesh(shirt.data)
dele = [v for v in bm.verts if (v.co.x > 0 and arm_t(v.co, "L") > 0.42) or (v.co.x < 0 and arm_t(v.co, "R") > 0.42)]
print("SLEEVE delete", len(dele))
bmesh.ops.delete(bm, geom=dele, context='VERTS')
# smooth the jagged cut: relax boundary verts along the boundary (keeps the sleeve length)
for it in range(12):
    bnd = [v for v in bm.verts if v.is_boundary and v.link_edges and abs(v.co.x) > 0.17]
    new = {}
    for v in bnd:
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
        if len(nb) == 2: new[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
    for v, c in new.items(): v.co = c
bm.to_mesh(shirt.data); bm.free()
body = child(man, ".body")
dg = body.vertex_groups.get("Delete.male_casualsuit03") or next(g for g in body.vertex_groups if "casualsuit03" in g.name)
rm = [v.index for v in body.data.vertices if (v.co.x > 0 and arm_t(v.co, "L") > 0.22) or (v.co.x < 0 and arm_t(v.co, "R") > 0.22)]
dg.remove(rm); print("SKIN shown", len(rm))

# ---- DA KRAS FILMS logo decal on the shirt chest (dark logo on light blue)
logo = bpy.data.images.load(REPO + "/assets/brand/DaKrasFilms_logo_dark.png"); logo.name = "DaKrasFilms_logo_dark"
bpy.ops.object.select_all(action='DESELECT')
w = 0.25; h = w * 414 / 967
# chest front: ray from the front at chest height
dep = bpy.context.evaluated_depsgraph_get()
z_chest = A["upperarm01.L"].head_local.z - 0.14
bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=14, size=1)
dec = bpy.context.active_object; dec.name = "SodaMan_ShirtLogo"
dec.scale = (w, h, 1); dec.rotation_euler = (math.radians(90), 0, 0)
dec.location = (0, -0.5, z_chest)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
sw = dec.modifiers.new("sw", 'SHRINKWRAP'); sw.target = shirt; sw.wrap_method = 'PROJECT'
sw.use_project_y = True; sw.use_negative_direction = True; sw.use_positive_direction = True; sw.offset = 0.003
bpy.context.view_layer.objects.active = dec; bpy.ops.object.modifier_apply(modifier="sw")
dt = dec.modifiers.new("dt", 'DATA_TRANSFER'); dt.object = shirt; dt.use_vert_data = True
dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
bpy.ops.object.datalayout_transfer(modifier="dt"); bpy.ops.object.modifier_apply(modifier="dt")
dec.parent = man; am = dec.modifiers.new("Armature", 'ARMATURE'); am.object = man
dm = bpy.data.materials.new("ShirtLogo"); dm.use_nodes = True; nt = dm.node_tree; nt.nodes.clear()
o = nt.nodes.new("ShaderNodeOutputMaterial"); t = nt.nodes.new("ShaderNodeTexImage"); t.image = logo; t.extension = 'CLIP'
pr = nt.nodes.new("ShaderNodeBsdfPrincipled"); pr.inputs["Roughness"].default_value = 0.7
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(t.outputs["Color"], pr.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], mx.inputs[0])
nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(pr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])
dec.data.materials.append(dm)
print("LOGO z", z_chest, "y", min(v.co.y for v in dec.data.vertices))

# ---- eye fix (EnhancedEye cornea), hand limits, open elbows
if "EnhancedEye" in bpy.data.node_groups:
    _NO_SAVE = True; exec(open(SCR + "/eye_fix.py").read())
for rig in (man, sci):
    add_hand_limits(rig)
    for s in "LR":
        lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
    for b in ("IK_hand.L", "IK_hand.R", "IK_foot.L", "IK_foot.R", "Pole_elbow.L", "Pole_knee.L"):
        assert b in rig.pose.bones, b
man.location = (0, 0, 0); sci.location = (3, 0, 0)
for ob in bpy.data.objects: print("OBJ", ob.name, ob.type)
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/chars.blend")
