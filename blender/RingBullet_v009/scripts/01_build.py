"""RingBullet v009 stage A (from scratch): a corner shop at night, the owner, the robber, the bullet, the ring.
blender -b --factory-startup --python 01_build.py -- <polyhaven_dir> <out.blend>

SHOP (origin): the owner stands ON the floor (z=0) at the origin facing -Y. Behind him (y=+1.5) a wall of shelves full of
colourful goods with the DA KRAS FILMS sign above them. The counter runs along his right side (-X). The robber stands
at y~-2.0 facing +Y (placed in 02). The front wall (y=-3.2) has the glass door (+X) and a display window (-X); the night
street and the police lights are outside it. The bullet, its flattened shape, two fragments, the muzzle flash and smoke
are built here; the ring is built in 02 (sized to the finger)."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
PH, OUT = a[0], a[1]
BRAND = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"
random.seed(21)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1395
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920

# ================================================================== characters (ONE model each)
OW, OWB = human("Owner", 1.0, 0.68, {"asian": 0.10, "caucasian": 0.55, "african": 0.35}, "short02/short02.mhclo",
                "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow006/eyebrow006.mhclo",
                height=0.55, weight=0.62, muscle=0.5,
                clothes=["male_casualsuit03/male_casualsuit03.mhclo", "shoes02/shoes02.mhclo"])
RB, RBB = human("Robber", 1.0, 0.45, {"asian": 0.05, "caucasian": 0.80, "african": 0.15}, "short03/short03.mhclo",
                "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow002/eyebrow002.mhclo",
                height=0.6, weight=0.5, muscle=0.6,
                clothes=["male_casualsuit05/male_casualsuit05.mhclo", "shoes03/shoes03.mhclo"])
eye_fix(OW); eye_fix(RB); eye_group_fix()
for c in OW.children:                      # dark-brown hair and brows with a touch of grey, warm skin
    if c.type == 'MESH' and any(k in c.name.lower() for k in ("short02", "eyebrow")):
        for m in c.data.materials: tint(m, (0.32, 0.22, 0.16))
for m in OWB.data.materials: tint(m, (0.88, 0.64, 0.50))
for c in RB.children:                      # robber: near-black jacket and jeans, dark hair (never his face on camera)
    if c.type == 'MESH' and "casualsuit" in c.name:
        for m in c.data.materials: tint(m, (0.35, 0.35, 0.38))
    if c.type == 'MESH' and "short03" in c.name:
        for m in c.data.materials: tint(m, (0.25, 0.20, 0.17))
for rig in (OW, RB):
    for c in rig.children:
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.4, 1.38, 1.32))
        if c.type == 'MESH' and ("casualsuit" in c.name or "shoes" in c.name):
            c.name = rig.name + (".clothes" if "casualsuit" in c.name else ".shoes")
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1
            for m in c.data.materials:
                for nd in m.node_tree.nodes:
                    if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = 0.6
# the owner's shirt: deepen the red check so it reads rich, not brown
for m in bpy.data.objects["Owner.clothes"].data.materials: tint(m, (1.25, 0.85, 0.80))

# ================================================================== materials
def plaster(name, c1, c2, scale=40.0, rough=0.85):
    m = mat(name, c1, rough=rough)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 6.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; bp.inputs["Distance"].default_value = 0.002
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def checker(name, c1, c2, mortar, scale=4.0):
    m = mat(name, c1, rough=0.35, coat=0.3)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); ck = nt.nodes.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = scale
    ck.inputs["Color1"].default_value = (*c1, 1); ck.inputs["Color2"].default_value = (*c2, 1)
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = scale / 2; br.offset = 0.0
    br.inputs["Mortar Size"].default_value = 0.006; br.inputs["Brick Width"].default_value = 1.0; br.inputs["Row Height"].default_value = 1.0
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs["B"].default_value = (*mortar, 1)
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(tc.outputs["Object"], ck.inputs["Vector"]); nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Fac"], mx.inputs["Factor"])
    nt.links.new(ck.outputs["Color"], mx.inputs["A"]); nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    return m

def wood(name, c1, c2, scale=3.0, rough=0.4):
    m = mat(name, c1, rough=rough, coat=0.25)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 10, 1)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 3.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m

def thin_glass(name, tint=(0.85, 0.95, 1.0), refl=0.05):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (*tint, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.02
    fr = nt.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
    mm = nt.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = refl / 0.04
    nt.links.new(fr.outputs[0], mm.inputs[0])
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mm.outputs[0], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m

def emis(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m

M_WALL = plaster("M_Wall", (0.012, 0.16, 0.20), (0.020, 0.22, 0.26), scale=8.0)        # deep teal
M_WALL_LOW = wood("M_Wainscot", (0.22, 0.05, 0.02), (0.32, 0.09, 0.03), scale=2.5)       # dark cherry panelling
M_FLOOR = checker("M_Floor", (0.55, 0.05, 0.03), (0.85, 0.78, 0.62), (0.2, 0.18, 0.16), scale=3.0)
M_CEIL = mat("M_Ceiling", (0.55, 0.50, 0.42), rough=0.9)
M_TRIM = mat("M_Trim", (0.90, 0.86, 0.75), rough=0.35, coat=0.3)
M_SHELF = wood("M_ShelfWood", (0.45, 0.20, 0.06), (0.60, 0.30, 0.10), scale=3.0)
M_CTOP = mat("M_CounterTop", (0.55, 0.02, 0.03), rough=0.25, coat=0.6)                    # glossy red counter top
M_CFRONT = wood("M_CounterFront", (0.30, 0.10, 0.03), (0.42, 0.16, 0.05), scale=2.0)
M_GLASS = thin_glass("M_Glass")
M_DOORF = mat("M_DoorFrame", (0.03, 0.10, 0.28), rough=0.35, coat=0.3)                   # deep blue door frame
M_METAL = mat("M_Metal", (0.6, 0.6, 0.62), rough=0.3, metal=1.0)

def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)

# ================================================================== room shell
X0, X1, YB, YF, H = -2.6, 2.6, 1.5, -3.2, 2.9
box("SH_Floor", (X1 - X0 + 0.2, YB - YF + 0.2, 0.05), (0, (YB + YF) / 2, -0.025), M_FLOOR, bevel=0.0)
box("SH_Ceiling", (X1 - X0 + 0.2, YB - YF + 0.2, 0.05), (0, (YB + YF) / 2, H + 0.025), M_CEIL, bevel=0.0)
box("SH_BackWall", (X1 - X0, 0.1, H), (0, YB + 0.05, H / 2), M_WALL, bevel=0.0)
box("SH_SideL", (0.1, YB - YF, H), (X1 + 0.05, (YB + YF) / 2, H / 2), M_WALL, bevel=0.0)
box("SH_SideR", (0.1, YB - YF, H), (X0 - 0.05, (YB + YF) / 2, H / 2), M_WALL, bevel=0.0)
for nm, x in (("SH_WainL", X1 - 0.01), ("SH_WainR", X0 + 0.01)):
    box(nm, (0.02, YB - YF, 0.95), (x, (YB + YF) / 2, 0.475), M_WALL_LOW, bevel=0.0)
# front wall with the door opening (x 0.4..1.4, z 0..2.2) and the display window (x -2.2..-0.3, z 0.9..2.2)
def slab(name, x0, x1, z0, z1):
    return box(name, (x1 - x0, 0.12, z1 - z0), ((x0 + x1) / 2, YF - 0.06, (z0 + z1) / 2), M_WALL, bevel=0.0)
parts = [slab("FW1", X0, -2.2, 0, H), slab("FW2", -2.2, -0.3, 0, 0.9), slab("FW3", -2.2, -0.3, 2.2, H), slab("FW4", -0.3, 0.4, 0, H),
         slab("FW5", 0.4, 1.4, 2.2, H), slab("FW6", 1.4, X1, 0, H)]
bpy.ops.object.select_all(action='DESELECT')
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); bpy.context.active_object.name = "SH_FrontWall"
# door: blue frame + glass, standing open a little outward; window: frame + glass
def frame_rect(name, x0, x1, z0, z1, y, t=0.06, depth=0.08):
    ps = [box(name + "a", (t, depth, z1 - z0), (x0 + t / 2, y, (z0 + z1) / 2), M_DOORF, bevel=0.004),
          box(name + "b", (t, depth, z1 - z0), (x1 - t / 2, y, (z0 + z1) / 2), M_DOORF, bevel=0.004),
          box(name + "c", (x1 - x0, depth, t), ((x0 + x1) / 2, y, z1 - t / 2), M_DOORF, bevel=0.004),
          box(name + "d", (x1 - x0, depth, t), ((x0 + x1) / 2, y, z0 + t / 2), M_DOORF, bevel=0.004)]
    bpy.ops.object.select_all(action='DESELECT')
    for p in ps: p.select_set(True)
    bpy.context.view_layer.objects.active = ps[0]; bpy.ops.object.join(); o = bpy.context.active_object; o.name = name
    bpy.ops.mesh.primitive_plane_add(size=1, location=((x0 + x1) / 2, y, (z0 + z1) / 2), rotation=(math.radians(90), 0, 0))
    g = bpy.context.active_object; g.name = name + "_Glass"; g.scale = (x1 - x0 - 2 * t, z1 - z0 - 2 * t, 1)
    bpy.ops.object.transform_apply(scale=True); g.data.materials.append(M_GLASS)
    return o, g
frame_rect("SH_Window", -2.2, -0.3, 0.9, 2.2, YF - 0.06)
DOOR, DOORG = frame_rect("SH_Door", 0.0, 0.98, 0.0, 2.18, 0.0)
for o in (DOOR, DOORG):
    o.data.transform(Matrix.Translation((0, -0.04, 0)))
DOORG.parent = DOOR
DOOR.location = (0.41, YF - 0.12, 0.0); DOOR.rotation_euler.z = math.radians(-35)   # hinged at x=0.41, open outward

# ================================================================== shelves of goods on the back wall (made here, no readable text)
PALETTE = [(0.85, 0.05, 0.04), (0.05, 0.20, 0.85), (0.98, 0.72, 0.02), (0.05, 0.55, 0.12), (0.95, 0.35, 0.02),
           (0.55, 0.05, 0.55), (0.02, 0.60, 0.70), (0.95, 0.95, 0.92), (0.80, 0.10, 0.35)]
PMATS = []
for i, c in enumerate(PALETTE):
    m = mat("M_Pack%d" % i, c, rough=0.35, coat=0.4)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]           # a two-tone label band (lighter middle band)
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
    c2 = PALETTE[(i + 3) % len(PALETTE)]
    cr.color_ramp.elements[0].color = (*c, 1); cr.color_ramp.elements[1].position = 0.38; cr.color_ramp.elements[1].color = (*c2, 1)
    e3 = cr.color_ramp.elements.new(0.62); e3.color = (*c, 1)
    nt.links.new(sp.outputs["Z"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    PMATS.append(m)
M_GLASSJAR = mat("M_Jar", (0.9, 0.95, 1.0), rough=0.05)
def shelf_unit(name, x0, x1, levels, depth=0.36, y_back=YB):
    ps = []
    yc = y_back - depth / 2
    for z in levels:
        ps.append(box(name + "_p%d" % int(z * 100), (x1 - x0, depth, 0.03), ((x0 + x1) / 2, yc, z), M_SHELF, bevel=0.004))
    top = levels[-1] + 0.40
    for x in (x0, x1):
        ps.append(box(name + "_s%d" % int(x * 100), (0.03, depth, top), (x, yc, top / 2), M_SHELF, bevel=0.004))
    ps.append(box(name + "_back", (x1 - x0, 0.015, top), ((x0 + x1) / 2, y_back - 0.008, top / 2), M_SHELF, bevel=0.0))
    bpy.ops.object.select_all(action='DESELECT')
    for p in ps: p.select_set(True)
    bpy.context.view_layer.objects.active = ps[0]; bpy.ops.object.join(); bpy.context.active_object.name = name
    # goods: boxes, cans and jars sitting ON each level, packed along x
    goods = []
    for li, z in enumerate(levels[:-1] if len(levels) > 4 else levels):
        x = x0 + 0.04
        while x < x1 - 0.10:
            kind = random.choice(("box", "box", "can", "can", "jar"))
            m = random.choice(PMATS)
            if kind == "box":
                w = random.uniform(0.10, 0.18); h = random.uniform(0.18, 0.30); d = random.uniform(0.16, 0.24)
                o = box("G_%s" % name, (w, d, h), (x + w / 2, yc - 0.02, z + 0.015 + h / 2), m, bevel=0.006, segs=2)
                o.rotation_euler.z = random.uniform(-0.06, 0.06)
                x += w + 0.012
            elif kind == "can":
                r = random.uniform(0.035, 0.045); h = random.uniform(0.10, 0.14)
                for k in range(2):
                    o = cyl("G_%s" % name, r, h, (x + r, yc - 0.10 + k * 0.12, z + 0.015 + h / 2), m, verts=24, bevel=0.003)
                    goods.append(o)
                x += 2 * r + 0.01
            else:
                r = 0.05; h = 0.16
                o = cyl("G_%s" % name, r, h, (x + r, yc - 0.04, z + 0.015 + h / 2), M_GLASSJAR, verts=24, bevel=0.004)
                lid = cyl("G_%s" % name, r * 1.02, 0.025, (x + r, yc - 0.04, z + 0.015 + h + 0.012), m, verts=24, bevel=0.003)
                goods.append(lid)
                x += 2 * r + 0.012
            goods.append(o)
    return goods
shelf_unit("SH_ShelfBack", -2.45, 2.45, (0.06, 0.48, 0.90, 1.32, 1.74))
# side wall (+X) shelving: rotate a second unit onto the left wall (x=+2.6), between y=-2.4 and y=0.9
side = shelf_unit("SH_ShelfSide", -1.65, 1.65, (0.06, 0.48, 0.90, 1.32, 1.74), depth=0.34, y_back=0.0)
root = bpy.data.objects.new("SH_ShelfSideRoot", None); sc.collection.objects.link(root)
for o in [bpy.data.objects["SH_ShelfSide"]] + side:
    o.parent = root
root.rotation_euler.z = math.radians(-90); root.location = (X1, -0.75, 0)

# ================================================================== the counter along the owner's right side (-X)
CX0, CX1, CY0, CY1, CH = -2.45, -0.75, -0.32, 0.32, 0.95
box("SH_CounterBody", (CX1 - CX0, CY1 - CY0 - 0.04, CH - 0.04), ((CX0 + CX1) / 2, 0.0, (CH - 0.04) / 2), M_CFRONT, bevel=0.01)
box("SH_CounterTop", (CX1 - CX0 + 0.06, CY1 - CY0 + 0.04, 0.04), ((CX0 + CX1) / 2, 0.0, CH - 0.02), M_CTOP, bevel=0.012)
box("SH_Register", (0.36, 0.34, 0.16), (-1.55, 0.02, CH + 0.08), mat("M_Register", (0.08, 0.08, 0.09), rough=0.4), bevel=0.02)
box("SH_RegisterTop", (0.30, 0.22, 0.04), (-1.55, 0.08, CH + 0.18), mat("M_RegisterKeys", (0.85, 0.80, 0.70), rough=0.5), bevel=0.01)
for i, x in enumerate((-2.15, -1.05)):           # candy jars with coloured sweets
    cyl("SH_Jar%d" % i, 0.09, 0.24, (x, -0.05, CH + 0.12), M_GLASSJAR, verts=32, bevel=0.01)
    for k in range(18):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, segments=12, ring_count=8,
                                             location=(x + random.uniform(-0.05, 0.05), -0.05 + random.uniform(-0.05, 0.05), CH + 0.03 + k * 0.007))
        s_ = bpy.context.active_object; s_.name = "SH_Sweet%d_%d" % (i, k); s_.data.materials.append(random.choice(PMATS))
    cyl("SH_JarLid%d" % i, 0.095, 0.03, (x, -0.05, CH + 0.255), PMATS[i * 2], verts=32, bevel=0.006)

# ================================================================== the sign with the logo above the back shelves
img = bpy.data.images.load(BRAND); img.name = "DaKrasFilms_logo_white"
box("SH_SignBoard", (1.40, 0.04, 0.62), (0.0, YB - 0.03, 2.55), mat("M_SignBoard", (0.03, 0.02, 0.05), rough=0.95), bevel=0.02)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0.0, YB - 0.052, 2.55), rotation=(math.radians(90), 0, 0))
LOGO = bpy.context.active_object; LOGO.name = "SH_Logo"; LOGO.scale = (1.26, 1.26 * 414 / 967, 1)
bpy.ops.object.transform_apply(scale=True)
lm = bpy.data.materials.new("M_Logo"); lm.use_nodes = True; nt = lm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = img; ti.interpolation = 'Cubic'
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 2.2; nt.links.new(ti.outputs["Color"], em.inputs["Color"])
mix_ = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
nt.links.new(ti.outputs["Alpha"], mix_.inputs["Fac"]); nt.links.new(tr.outputs[0], mix_.inputs[1]); nt.links.new(em.outputs[0], mix_.inputs[2])
nt.links.new(mix_.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
LOGO.data.materials.append(lm)
# a warm strip light under the sign (lights the top of the shelves)
box("SH_SignLight", (1.40, 0.04, 0.025), (0.0, YB - 0.10, 1.98), emis("M_SignStrip", (1.0, 0.75, 0.45), 6.0), bevel=0.004)

# ================================================================== Poly Haven props (CC0)
def append_ph(asset, name, loc, rot_z=0.0, scale=1.0, keep=None):
    d = os.path.join(PH, asset); blend = [f for f in os.listdir(d) if f.endswith(".blend")][0]
    with bpy.data.libraries.load(os.path.join(d, blend), link=False) as (src, dst):
        dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o is not None and o.type == 'MESH' and (keep is None or keep(o.name))]
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root)
    for o in objs:
        sc.collection.objects.link(o)
        if o.parent is None or o.parent not in objs: o.parent = root
    root.location = loc; root.rotation_euler.z = rot_z; root.scale = (scale,) * 3
    for o in objs:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = 0.5
    return root, objs
LAMPS = ((-1.45, -0.55), (1.75, 0.55), (-0.9, -2.3))
for i, (x, y) in enumerate(LAMPS):
    append_ph("hanging_industrial_lamp", "SH_Lamp%d" % i, (x, y, H), scale=0.72)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, segments=16, ring_count=8, location=(x, y, H - 1.34 * 0.72 + 0.06))
    b_ = bpy.context.active_object; b_.name = "SH_Bulb%d" % i; b_.data.materials.append(emis("M_Bulb", (1.0, 0.70, 0.40), 25.0))
    b_.visible_shadow = False
append_ph("plastic_crate_01", "SH_Crate1", (-2.25, -1.3, 0.0), rot_z=0.3)
append_ph("plastic_crate_01", "SH_Crate2", (-2.25, -1.3, 0.264), rot_z=0.1)
append_ph("cardboard_box_01", "SH_Box1", (2.15, -2.75, 0.183), rot_z=0.4)
append_ph("potted_plant_02", "SH_Plant", (-1.95, -2.75, 0.097), scale=1.3)
WB_, WBO = append_ph("wine_bottles_01", "SH_Wine", (-1.95, 0.05, CH), rot_z=0.0, scale=0.9)
GUN, GUNP = append_ph("service_pistol", "Pistol", (0, 0, 0), keep=lambda n: n.endswith("_a") or n == "service_pistol")
for o in GUNP:                                              # dark, side-on read
    for m in o.data.materials: tint(m, (0.35, 0.35, 0.38))

# ================================================================== outside: the night street (seen through the door and window)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -7.5, 2.0), rotation=(math.radians(90), 0, 0))
st = bpy.context.active_object; st.name = "OUT_Street"; st.scale = (16, 8, 1)
sm_ = bpy.data.materials.new("M_Street"); sm_.use_nodes = True; nt = sm_.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.02, 0.03, 0.08, 1); cr.color_ramp.elements[1].color = (0.06, 0.12, 0.35, 1)
nt.links.new(sp.outputs["Y"], cr.inputs["Fac"])
e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Strength"].default_value = 1.0; nt.links.new(cr.outputs["Color"], e.inputs["Color"])
nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"]); st.data.materials.append(sm_)
box("OUT_Pavement", (16, 4.2, 0.1), (0, -5.3, -0.06), plaster("M_Pavement", (0.10, 0.10, 0.12), (0.16, 0.16, 0.18), scale=6.0), bevel=0.0)
for i, x in enumerate((-3.0, 2.8)):                         # two warm street-lamp glows and a lit shop window opposite
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(x, -6.6, 3.0)); g_ = bpy.context.active_object
    g_.name = "OUT_StreetLamp%d" % i; g_.data.materials.append(emis("M_StreetGlow", (1.0, 0.65, 0.3), 12.0))
    cyl("OUT_LampPost%d" % i, 0.05, 3.0, (x, -6.6, 1.5), mat("M_Post", (0.05, 0.05, 0.06), rough=0.5))
box("OUT_ShopOpp", (2.6, 0.1, 1.6), (-0.6, -7.4, 1.2), emis("M_OppWindow", (0.9, 0.45, 0.15), 1.5), bevel=0.0)
# police lights (red, blue): emissive bars + area lights outside the door, keyed on in 02
PL = []
for nm, col, x in (("OUT_PoliceRed", (1.0, 0.02, 0.02), 0.1), ("OUT_PoliceBlue", (0.02, 0.15, 1.0), 1.4)):
    o = box(nm, (0.55, 0.18, 0.12), (x, -5.6, 1.55), emis(nm + "_m", col, 0.0), bevel=0.02)
    L = bpy.data.lights.new(nm + "_L", 'AREA'); L.energy = 0.0; L.color = col; L.size = 1.2; L.shape = 'DISK'
    lo = bpy.data.objects.new(nm + "_L", L); sc.collection.objects.link(lo); lo.location = (x, -3.6, 1.9)
    lo.rotation_euler = (math.radians(-80), 0, 0)
    PL.append((o, lo))

# ================================================================== lights inside: warm lamps, cool window fill, rims
def light(name, kind, energy, loc, rot=(0, 0, 0), size=1.0, color=(1, 1, 1)):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size; L.shape = 'DISK'
    if kind in ('POINT', 'SPOT'): L.shadow_soft_size = size
    o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    return o
for i, (x, y) in enumerate(LAMPS):
    light("L_Lamp%d" % i, 'SPOT', 180 if i == 1 else 120, (x, y, H - 1.34 * 0.72), size=0.08, color=(1.0, 0.72, 0.45)).data.spot_size = math.radians(120)
light("L_Key", 'AREA', 90, (0.9, -1.4, 2.3), rot=(math.radians(55), 0, math.radians(30)), size=1.2, color=(1.0, 0.86, 0.70))
light("L_Fill", 'AREA', 45, (-1.3, -1.6, 1.8), rot=(math.radians(65), 0, math.radians(-40)), size=1.4, color=(0.55, 0.70, 1.0))
light("L_Rim", 'AREA', 70, (0.6, 1.0, 2.4), rot=(math.radians(-45), 0, math.radians(160)), size=0.8, color=(1.0, 0.65, 0.40))
light("L_Shelves", 'AREA', 60, (0.0, 0.4, 2.6), rot=(math.radians(-25), 0, 0), size=3.0, color=(1.0, 0.85, 0.65))
light("L_Window", 'AREA', 80, (-1.2, -3.0, 1.6), rot=(math.radians(-90), 0, 0), size=1.6, color=(0.35, 0.50, 1.0))

# ================================================================== the bullet (ONE object), its flattened shape, two fragments
def revolve(name, prof, mat_):
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    for a_, b_ in zip(vs, vs[1:]): bm.edges.new((a_, b_))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], angle=math.radians(360), steps=48, axis=(0, 0, 1), cent=(0, 0, 0), use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat_); o.modifiers.new("ws", 'WEIGHTED_NORMAL')
    return o
M_BUL = mat("M_Bullet", (0.92, 0.42, 0.14), rough=0.30, metal=0.9, coat=0.15)
R = 0.0045; Lc = 0.0075; Ln = 0.0080
prof = [(0.0, 0.0), (R * 0.92, 0.0), (R, 0.0006)] + [(R, Lc * i / 5) for i in range(1, 6)]
prof += [(R * math.cos(t * math.pi / 2) ** 0.9, Lc + Ln * math.sin(t * math.pi / 2) ** 1.05) for t in [i / 16 for i in range(1, 17)]]
BUL = revolve("Bullet", prof, M_BUL)                        # origin at the base, nose along +Z, 15.5 mm long
# flattened (mushroomed) bullet after the ring: shorter, nose flattened and wider, a little skewed
prof2 = [(0.0, 0.0), (R * 0.92, 0.0), (R, 0.0006), (R, 0.004), (R * 1.08, 0.0065), (R * 1.35, 0.0085), (R * 1.45, 0.0095),
         (R * 1.30, 0.0102), (R * 0.8, 0.0106), (0.0, 0.0108)]
BUL2 = revolve("BulletFlat", prof2, M_BUL)
for v in BUL2.data.vertices:                                # crumple the flattened face
    if v.co.z > 0.007:
        v.co.x += random.uniform(-0.0004, 0.0004); v.co.y += random.uniform(-0.0004, 0.0004); v.co.z += random.uniform(-0.0005, 0.0003)
    v.co.x += 0.06 * v.co.z ** 2 / 0.01                        # slight bend
def fragment(name, size, seed):
    rnd = random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=size)
    o = bpy.context.active_object; o.name = name
    for v in o.data.vertices:
        v.co *= rnd.uniform(0.65, 1.25)
    o.scale = (1.5, 0.9, 0.7); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat("M_Frag", (0.95, 0.55, 0.25), rough=0.3, metal=0.6, emit=((1.0, 0.45, 0.10), 6.0)))   # hot metal: reads at preview size
    bpy.ops.object.shade_flat()
    return o
FA = fragment("FragA", 0.0026, 1)
FB = fragment("FragB", 0.0030, 2)
for o in (BUL, BUL2, FA, FB):
    o.location = (0, 0, -5)

# ================================================================== muzzle flash (emissive star) and smoke puffs (no volumes)
bm = bmesh.new()
for k in range(7):
    ang = 2 * math.pi * k / 7
    d = Vector((0.0, math.cos(ang) * 0.35, math.sin(ang) * 0.35)) + Vector((1, 0, 0))
    d.normalize(); ln_ = 0.10 if k % 2 else 0.14
    tip = d * ln_; side = Vector((0, -math.sin(ang), math.cos(ang))) * 0.012
    v0 = bm.verts.new((0, 0, 0)); v1 = bm.verts.new(tip * 0.35 + side); v2 = bm.verts.new(tip); v3 = bm.verts.new(tip * 0.35 - side)
    bm.faces.new((v0, v1, v2, v3))
core = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.025)
me = bpy.data.meshes.new("MuzzleFlash"); bm.to_mesh(me); bm.free()
MF = bpy.data.objects.new("MuzzleFlash", me); sc.collection.objects.link(MF)
MF.data.materials.append(emis("M_Flash", (1.0, 0.75, 0.30), 40.0))
MF.visible_shadow = False
sm = mat("M_Smoke", (0.55, 0.55, 0.58), rough=1.0, alpha=1.0)
nt = sm.node_tree; p = nt.nodes["Principled BSDF"]; p.inputs["Alpha"].default_value = 0.35
for k in range(5):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.03)
    s_ = bpy.context.active_object; s_.name = "Smoke%d" % k
    tx = bpy.data.textures.new("SmokeN%d" % k, 'CLOUDS'); tx.noise_scale = 0.012
    d_ = s_.modifiers.new("n", 'DISPLACE'); d_.texture = tx; d_.strength = 0.012
    s_.data.materials.append(sm); bpy.ops.object.shade_smooth(); s_.location = (0, 0, -5)
    s_.visible_shadow = False

# ================================================================== sparks (thin emissive streaks; animated in 02)
M_SPARK = emis("M_Spark", (1.0, 0.65, 0.20), 30.0)
for k in range(16):
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.0007, radius2=0.0, depth=0.012, location=(0, 0, -5))
    s_ = bpy.context.active_object; s_.name = "Spark%02d" % k; s_.data.materials.append(M_SPARK); s_.visible_shadow = False

# ================================================================== render settings (fast, zero-error) and the look
sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.samples = 40; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.06
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 4; cy.diffuse_bounces = 2; cy.glossy_bounces = 2; cy.transmission_bounces = 4; cy.transparent_max_bounces = 10
cy.caustics_reflective = False; cy.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 1; cy.texture_limit_render = '2048'
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'High Contrast'; sc.view_settings.exposure = 0.0
sc.world = sc.world or bpy.data.worlds.new("World")
w = sc.world; w.use_nodes = True
bgn = [n for n in w.node_tree.nodes if n.type == 'BACKGROUND'][0]
bgn.inputs["Color"].default_value = (0.02, 0.03, 0.06, 1); bgn.inputs["Strength"].default_value = 0.5
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE", OUT)
