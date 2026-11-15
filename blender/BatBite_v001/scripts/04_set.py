"""Sets: rooftop concert stage by the bay (stage top at z=0, singer at origin, audience floor z=-1.3, front edge y=-2.6),
and a hospital bay at x=+60. Real CC-BY props (see CREDITS.md); stage boards, risers and the hospital room shell are built here.
blender -b chars_bat.blend --python 04_set.py -- scene.blend"""
import bpy, sys, math, bmesh
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]
A = "/home/user/Muhammed/blender/BatBite_v001/assets/"
LOGO_W = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"
LOGO_D = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"
sc = bpy.context.scene
COLL = {}
def coll(n):
    if n not in COLL:
        c = bpy.data.collections.new(n); sc.collection.children.link(c); COLL[n] = c
    return COLL[n]
def mat(n, rgb, rough=0.5, metal=0.0, spec=0.5):
    m = bpy.data.materials.new(n); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough; P.inputs["Metallic"].default_value = metal
    P.inputs["Specular IOR Level"].default_value = spec
    return m
def box(n, size, loc, m, c="Stage", bevel=0.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = n; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("B", 'BEVEL'); b.width = bevel; b.segments = 2
    o.data.materials.append(m); move(o, c); return o
def move(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    coll(c).objects.link(o)
def imp(f, name, scale, loc, rotz=0.0, c="Stage", join=True):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=A + f + ".glb")
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH']; others = [o.name for o in new if o.type != 'MESH']
    for o in ms:
        M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if join and len(ms) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name
    for n in others:
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    # origin: bottom centre
    me = o.data; lo = Vector([min(v.co[i] for v in me.vertices) for i in range(3)]); hi = Vector([max(v.co[i] for v in me.vertices) for i in range(3)])
    off = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in me.vertices: v.co = (v.co - off) * scale
    o.location = loc; o.rotation_euler = (0, 0, math.radians(rotz)); move(o, c)
    return o
def dup(o, n, loc, rotz=None):
    d = o.copy(); d.name = n; d.location = loc
    if rotz is not None: d.rotation_euler = (0, 0, math.radians(rotz))
    for c in o.users_collection: c.objects.link(d)
    return d
def logo_mat(n, path):
    m = bpy.data.materials.new(n); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.extension = 'CLIP'
    nt.links.new(t.outputs["Color"], P.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], P.inputs["Alpha"])
    P.inputs["Roughness"].default_value = 0.5
    return m
def plane_decal(n, w, loc, rot, m, c="Stage"):
    """logo decal plane, image aspect 967x414, faces local -Y"""
    h = w * 414 / 967
    me = bpy.data.meshes.new(n); bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    f = bm.faces.new(vs); uv = bm.loops.layers.uv.new()
    for l, u in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uv].uv = u
    bm.to_mesh(me); o = bpy.data.objects.new(n, me); o.location = loc; o.rotation_euler = rot
    me.materials.append(m); coll(c).objects.link(o); return o

# ------------------------------------------------------------------ world: clear blue sky gradient (camera rays), soft sun
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld"); lp = nt.nodes.new("ShaderNodeLightPath"); mix = nt.nodes.new("ShaderNodeMixShader")
bg_cam = nt.nodes.new("ShaderNodeBackground"); bg_amb = nt.nodes.new("ShaderNodeBackground")
geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
neg = nt.nodes.new("ShaderNodeMath"); neg.operation = 'MULTIPLY'; neg.inputs[1].default_value = -1.0
nt.links.new(geo.outputs["Incoming"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], neg.inputs[0]); nt.links.new(neg.outputs[0], ramp.inputs[0])
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.72, 0.88, 1.0, 1)
ramp.color_ramp.elements[1].position = 0.55; ramp.color_ramp.elements[1].color = (0.10, 0.42, 0.92, 1)
nt.links.new(ramp.outputs["Color"], bg_cam.inputs["Color"]); bg_cam.inputs["Strength"].default_value = 1.0
bg_amb.inputs["Color"].default_value = (0.55, 0.7, 0.95, 1); bg_amb.inputs["Strength"].default_value = 0.8
nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); nt.links.new(bg_amb.outputs[0], mix.inputs[1]); nt.links.new(bg_cam.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs["Surface"])
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sun.data.energy = 4.0; sun.data.angle = math.radians(6)
sun.rotation_euler = (math.radians(50), 0, math.radians(-35)); coll("Lights").objects.link(sun)

# ------------------------------------------------------------------ stage
m_floor = mat("M_StageFloor", (0.42, 0.44, 0.47), rough=0.42)
m_skirt = mat("M_StageSkirt", (0.05, 0.05, 0.06), rough=0.7)
m_black = mat("M_Black", (0.035, 0.035, 0.04), rough=0.45)
m_roof = mat("M_Roof", (0.62, 0.62, 0.6), rough=0.8)
m_rail = mat("M_Rail", (0.92, 0.93, 0.95), rough=0.35, metal=0.3)
m_water = mat("M_Bay", (0.08, 0.32, 0.55), rough=0.25, spec=0.05)
box("StageDeck", (11, 6.0, 0.1), (0, 0.4, -0.05), m_floor)
box("StageSkirt", (11, 6.0, 1.2), (0, 0.4, -0.7), m_skirt, bevel=0)
# deck board seams (thin dark lines) for a real stage-floor read
for i in range(-5, 6):
    box("Seam%d" % i, (0.008, 6.0, 0.002), (i * 1.0 + 0.5, 0.4, 0.001), m_black, bevel=0)
box("Roof", (60, 40, 0.2), (0, -6, -1.4), m_roof, c="Roof", bevel=0)
plane = bpy.ops.mesh.primitive_plane_add(size=6000, location=(0, 0, -40)); o = bpy.context.object; o.name = "Bay"; o.data.materials.append(m_water); move(o, "Roof")
# rooftop railing behind the stage (white posts and two rails) - the reference's white fence line
for y in (12.0,):
    for x in range(-26, 27, 2):
        box("RailPost%d" % x, (0.05, 0.05, 1.1), (x, y, -0.85), m_rail, c="Roof", bevel=0.005)
    for z in (-0.35, -0.8):
        box("Rail%.1f" % z, (54, 0.05, 0.05), (0, y, z), m_rail, c="Roof", bevel=0.005)
# drum riser + drum kit (front of kit faces -Y)
box("Riser", (2.6, 2.2, 0.3), (-2.1, 1.6, 0.15), m_black)
dr = imp("drums", "Drums", 0.00072, Vector((-2.1, 1.35, 0.3)), rotz=0.0)
# amps beside the singer, wedge-like low boxes are real amp models
amp = imp("amp", "Amp", 1.6, Vector((2.2, 1.6, 0.0)), rotz=0.0)
dup(amp, "Amp2", Vector((2.95, 1.6, 0.0)))
# PA speaker wall: real PA cabinets, 2 high, both sides behind
pa = imp("pa", "PA", 0.5, Vector((0, 0, 0)), rotz=0.0)
k = 0
for x in (-4.5, -3.5, 3.4, 4.4):
    for z in (0.0, 1.76):
        d = dup(pa, "PA_%d" % k, Vector((x, 2.85, z))); k += 1
pa.location = (-0.5, 3.0, 50); pa.hide_render = pa.hide_viewport = True
# truss frame: two towers + top span
tr = imp("truss", "Truss", 0.02, Vector((0, 0, 0)))
for x in (-5.3, 5.3):
    t = dup(tr, "TrussT%d" % x, Vector((x, 0.0, 0.0))); t.rotation_euler = (0, math.radians(90), 0); t.location = (x, 0.0, 1.25)
    t2 = dup(tr, "TrussT2%d" % x, Vector((x, 0.0, 0.0))); t2.rotation_euler = (0, math.radians(90), 0); t2.location = (x, 0.0, 3.75)
for x in (-3.75, -1.25, 1.25, 3.75):
    dup(tr, "TrussTop%d" % int(x * 100), Vector((x, 0.0, 5.3)))
tr.hide_render = tr.hide_viewport = True; tr.location = (0, 0, 60)
# logo 2: band banner hung from the top truss (black cloth, white logo)
box("Banner", (3.4, 0.02, 1.45), (0, 0.05, 4.28), mat("M_Banner", (0.03, 0.03, 0.035), rough=0.8), bevel=0)
plane_decal("Logo_Banner", 3.0, (0, 0.035, 4.28), (0, 0, 0), logo_mat("M_LogoWhite2", LOGO_W))
# mic stand at the singer (round base); mic head ~1.66 m; stand at y=-0.42 in front of the singer
mic = imp("micstand", "MicStand", 1.0, Vector((0.0, -0.42, 0.0)), rotz=-90)
# bridge far behind, along X, in the bay
br = imp("bridge", "Bridge", 4.0, Vector((-150, 1400, -40)), rotz=90, c="Roof")
br.data.materials[0] = mat("M_Bridge", (0.78, 0.82, 0.88), rough=0.6)
# logo 1: on the bass drum front head (white logo on a black head disc covering the stock print)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
groups = {}
for zz in [0.32 + 0.015 * i for i in range(50)]:
    for xx in [-2.9 + 0.015 * i for i in range(110)]:
        hit, loc, nrm, idx, ob, M = sc.ray_cast(dg, Vector((xx, -3.0, zz)), Vector((0, 1, 0)))
        if hit and ob.name == "Drums" and abs(nrm.y) > 0.97:
            groups.setdefault(round(loc.y, 2), []).append(loc)
best = (max(groups.values(), key=len), None)
pts = best[0]; cx = sum(p.x for p in pts) / len(pts); cz = sum(p.z for p in pts) / len(pts); fy = min(p.y for p in pts)
rad = (max(p.x for p in pts) - min(p.x for p in pts)) / 2
print("SET BassHead", round(cx, 3), round(fy, 3), round(cz, 3), "r", round(rad, 3), len(pts))
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=rad * 1.0, depth=0.004, location=(cx, fy - 0.003, cz), rotation=(math.radians(90), 0, 0))
hd = bpy.context.object; hd.name = "BassHeadCover"; hd.data.materials.append(mat("M_BassHead", (0.03, 0.03, 0.035), rough=0.4)); move(hd, "Stage")
lg = plane_decal("Logo_BassDrum", rad * 1.7, (cx, fy - 0.0055, cz), (0, 0, 0), logo_mat("M_LogoWhite", LOGO_W))
lg.parent = None
# ------------------------------------------------------------------ hospital bay at x=+60
HX = 60.0
m_wall = mat("M_HospWall", (0.55, 0.72, 0.70), rough=0.8)
m_hfloor = mat("M_HospFloor", (0.45, 0.5, 0.58), rough=0.4)
box("H_Floor", (6, 6, 0.1), (HX, 0, -0.05), m_hfloor, c="Hospital", bevel=0)
box("H_WallBack", (6, 0.12, 3.0), (HX, 2.6, 1.5), m_wall, c="Hospital", bevel=0)
box("H_WallLeft", (0.12, 6, 3.0), (HX - 2.9, 0, 1.5), m_wall, c="Hospital", bevel=0)
box("H_Ceil", (6, 6, 0.1), (HX, 0, 3.0), m_wall, c="Hospital", bevel=0)
# window strip on the back wall: bright panel (sky) with a frame
m_win = bpy.data.materials.new("M_Window"); m_win.use_nodes = True
em = m_win.node_tree.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.75, 0.88, 1.0, 1); em.inputs["Strength"].default_value = 1.5
m_win.node_tree.links.new(em.outputs[0], m_win.node_tree.nodes["Material Output"].inputs["Surface"])
box("H_Window", (1.6, 0.02, 1.1), (HX + 1.2, 2.53, 1.7), m_win, c="Hospital", bevel=0)
bed = imp("bed", "Bed", 0.0068, Vector((HX, 0.6, 0.0)), rotz=0.0, c="Hospital")
vit = imp("vitals", "Vitals", 0.27, Vector((HX - 0.2, 1.5, 0.0)), rotz=0, c="Hospital")
iv = imp("ivstand", "IVStand", 1.6, Vector((HX + 1.05, 1.5, 0.0)), rotz=0, c="Hospital")
for k_, L in (("H_Key", (HX - 1.5, -2.0, 2.6)), ("H_Fill", (HX + 2.0, -1.5, 2.2))):
    l = bpy.data.objects.new(k_, bpy.data.lights.new(k_, "AREA")); l.data.energy = 160 if k_ == "H_Key" else 60; l.data.size = 1.5
    l.location = L; l.rotation_euler = (Vector((HX, 0.6, 0.8)) - Vector(L)).to_track_quat('-Z', 'Y').to_euler(); coll("Lights").objects.link(l)
# report bounding boxes for placement
for n in ("Drums", "Amp", "PA_0", "MicStand", "Bed", "Vitals", "IVStand", "Bridge"):
    o = bpy.data.objects[n]; bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    print("SET", n, tuple(round(min(p[i] for p in bb), 3) for i in range(3)), tuple(round(max(p[i] for p in bb), 3) for i in range(3)))
sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = 1080, 1920, 60
sc.render.engine = 'CYCLES'
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
