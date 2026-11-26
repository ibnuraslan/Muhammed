"""DonationBin v010 stage A: from-scratch set, characters (one model each), real garments, props, look.
blender -b --python 01_build.py -- <sketchfab_dl_dir> <out.blend>
Layout (metres, Z up). The hero bin stands at the origin, its FRONT face at y=-0.75 facing -Y (the parking lot).
  chute (one-way flap, hinged at the top, swings INWARD only): x[-0.48,0.48] z[1.20,1.75]
  cut panel (firefighters, beat 10): x[-0.50,0.50] z[0.12,1.10], a separate object that falls outward
  interior: x[-0.87,0.87] y[-0.72,0.72], floor plate top z=0.12, roof inside z=2.87; clothes heap on the floor
Two more bins stand in the row at x=+2.6 and x=+5.2 (static all film: the ending reveal)."""
import bpy, bmesh, sys, math, random, json
from mathutils import Vector, Matrix
HERE = "/home/user/Muhammed/blender/DonationBin_v010/scripts"
exec(open(HERE + "/lib_build.py").read())
a = sys.argv[sys.argv.index("--") + 1:]
DL, OUT = a[0], a[1]
random.seed(9)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 2388
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
LOG = []
def log(*x):
    s = " ".join(str(y) for y in x); LOG.append(s); print("LOG", s)

# ================================================================== characters (MPFB2 CC0 + MakeHuman community CC0 garments)
SWEATER = "toigo_fisherman_sweater/toigo_fisherman_sweater.mhclo"
WOOL = "toigo_wool_pants/toigo_wool_pants.mhclo"
POLO = "namuhekam_male_polo_shirt/namuhekam_male_polo_shirt.mhclo"
WORK = "male_worksuit01/male_worksuit01.mhclo"
WOM, WB = human("Woman", 0.0, 0.42, {"asian": 0.10, "caucasian": 0.65, "african": 0.25}, "ponytail01/ponytail01.mhclo",
                "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo", height=0.45, weight=0.5,
                shoes="shoes01/shoes01.mhclo", clothes=[SWEATER, WOOL], cup=0.25)
MAN, MB = human("Man", 1.0, 0.5, {"asian": 0.10, "caucasian": 0.80, "african": 0.10}, "short02/short02.mhclo",
                "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo", height=0.55, weight=0.5,
                shoes="shoes03/shoes03.mhclo", clothes=[POLO, WOOL])
PAS, PB = human("Passer", 0.0, 0.6, {"asian": 0.6, "caucasian": 0.3, "african": 0.1}, "braid01/braid01.mhclo",
                "young_asian_female/young_asian_female.mhmat", "eyebrow007/eyebrow007.mhclo", height=0.45, weight=0.55,
                shoes="shoes01/shoes01.mhclo", clothes=[SWEATER, WOOL], cup=0.25)
FF1, F1B = human("Fire1", 1.0, 0.55, {"asian": 0.05, "caucasian": 0.15, "african": 0.80}, "short02/short02.mhclo",
                 "middleage_african_male/middleage_african_male.mhmat", "eyebrow004/eyebrow004.mhclo", height=0.55, weight=0.55,
                 muscle=0.6, shoes="shoes03/shoes03.mhclo", clothes=[WORK])
FF2, F2B = human("Fire2", 1.0, 0.45, {"asian": 0.05, "caucasian": 0.90, "african": 0.05}, "short01/short01.mhclo",
                 "young_caucasian_male2/young_caucasian_male2.mhmat", "eyebrow002/eyebrow002.mhclo", height=0.6, weight=0.5,
                 muscle=0.6, shoes="shoes03/shoes03.mhclo", clothes=[WORK])
PEOPLE = [(WOM, WB), (MAN, MB), (PAS, PB), (FF1, F1B), (FF2, F2B)]

def colorize2(obj, rgb, lo=0.42):
    """recolour a garment texture: keep the weave/fold detail as value, map it between rgb*lo and rgb (saturated, never brown)"""
    for m in obj.data.materials:
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        for p in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
            bc = p.inputs["Base Color"]
            if bc.is_linked:
                src = bc.links[0].from_socket
                bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
                cr = nt.nodes.new("ShaderNodeValToRGB")
                cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (*[c * lo for c in rgb], 1)
                cr.color_ramp.elements[1].position = 0.55; cr.color_ramp.elements[1].color = (*rgb, 1)
                nt.links.new(bw.outputs[0], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], bc)
            else:
                bc.default_value = (*rgb, 1)
            p.inputs["Roughness"].default_value = max(0.65, p.inputs["Roughness"].default_value)
            if "Metallic" in p.inputs and not p.inputs["Metallic"].is_linked: p.inputs["Metallic"].default_value = 0.0

def reflective_bands(obj, base, bands, band_col=(0.95, 0.85, 0.08)):
    """turnout-coat look: solid base colour + reflective bands placed in the garment's rest (Generated) z"""
    m = mat("M_" + obj.name + "_turnout", base, rough=0.75, sheen=0.2)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); se = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], se.inputs[0])
    acc = None
    for z0, z1 in bands:
        g1 = nt.nodes.new("ShaderNodeMath"); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = z0
        l1 = nt.nodes.new("ShaderNodeMath"); l1.operation = 'LESS_THAN'; l1.inputs[1].default_value = z1
        nt.links.new(se.outputs["Z"], g1.inputs[0]); nt.links.new(se.outputs["Z"], l1.inputs[0])
        mu = nt.nodes.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; nt.links.new(g1.outputs[0], mu.inputs[0]); nt.links.new(l1.outputs[0], mu.inputs[1])
        if acc is None: acc = mu
        else:
            mx = nt.nodes.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'; nt.links.new(acc.outputs[0], mx.inputs[0]); nt.links.new(mu.outputs[0], mx.inputs[1]); acc = mx
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.inputs["A"].default_value = (*base, 1); mix.inputs["B"].default_value = (*band_col, 1)
    nt.links.new(acc.outputs[0], mix.inputs["Factor"]); nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 300; bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.2
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    obj.data.materials.clear(); obj.data.materials.append(m)

def dress(rig, body, top, bottom, top_col, bot_col):
    """SOLID body (MPFB delete-group masks removed), small seam holes closed, garments floated off the skin, the skin under
    the cloth pulled in (never pokes through, never hollow), trouser waist tucked under the top."""
    n = strip_body_masks(body)
    t = part(rig, top); b = part(rig, bottom) if bottom else None
    for g in [x for x in (t, b) if x]:
        log("holes closed", g.name, close_small_holes(g, 10))
    if top_col: colorize2(t, top_col)
    if b and bot_col: colorize2(b, bot_col)
    garment_offset(t, 0.010)
    if b: garment_offset(b, 0.012)
    log("tuck", rig.name, tuck_body_under(body, [x for x in (t, b) if x], depth=0.010), "masks removed", n)
    if b: log("waist", rig.name, tuck_waist(b, t))
    for g in [x for x in (t, b) if x]:
        g.name = rig.name + "." + ("top" if g is t else "trousers")
        # real cloth thickness with a closed rim at every hem, cuff and collar (no paper-thin edges)
        so = g.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
        i = g.modifiers.find("solid"); j = g.modifiers.find("Subdivision")
        while j >= 0 and i > j:          # after the float/tuck displaces, before the subdivision
            g.modifiers.move(i, i - 1); i -= 1; j = g.modifiers.find("Subdivision")
    return t, b

W_TOP, W_TRS = dress(WOM, WB, "fisherman", "wool_pants", (0.95, 0.16, 0.07), (0.05, 0.16, 0.62))
M_TOP, M_TRS = dress(MAN, MB, "polo", "wool_pants", (0.02, 0.55, 0.42), (0.10, 0.09, 0.12))
P_TOP, P_TRS = dress(PAS, PB, "fisherman", "wool_pants", (0.98, 0.72, 0.04), (0.38, 0.06, 0.48))
F1_SUIT, _ = dress(FF1, F1B, "worksuit", None, None, None)
F2_SUIT, _ = dress(FF2, F2B, "worksuit", None, None, None)
for s in (F1_SUIT, F2_SUIT):
    reflective_bands(s, (0.06, 0.07, 0.10), [(0.10, 0.14), (0.47, 0.51), (0.70, 0.74)])

for r, b in PEOPLE:
    eye_fix(r)
    for m in b.data.materials: tint(m, (1.0, 0.80, 0.68) if r in (WOM, PAS) else (1.0, 0.90, 0.82))
hair_t = {WOM: (0.45, 0.18, 0.08), MAN: (0.25, 0.17, 0.10), PAS: (0.15, 0.10, 0.08), FF1: (0.12, 0.09, 0.07), FF2: (0.55, 0.32, 0.12)}
for r, t in hair_t.items():
    for c in r.children:
        if c.type == 'MESH' and any(k in c.name for k in ("ponytail", "short0", "braid", "eyebrow")):
            for m in c.data.materials: tint(m, t)
# spread them out at the origin area (the animation places every root)
for i, (r, b) in enumerate(PEOPLE):
    r.location = (10 + 1.2 * i, 10, 0)

# ================================================================== look / world / render (fast, zero-error)
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.04
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
try:
    sc.view_layers[0].cycles.denoising_store_passes = False
    cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
except Exception: pass
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 16
cy.caustics_reflective = cy.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2
try: cy.texture_limit_render = '2048'
except Exception: pass
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: log("look name fallback")
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = "//render/DonationBin_v010_####"

world = bpy.data.worlds.new("Sky"); sc.world = world; world.use_nodes = True
nt = world.node_tree; N = nt.nodes; L = nt.links
bg = N["Background"]; lp = N.new("ShaderNodeLightPath")
tc = N.new("ShaderNodeTexCoord"); se = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], se.inputs[0])
ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.48; ramp.color_ramp.elements[0].color = (0.30, 0.66, 1.0, 1)
ramp.color_ramp.elements[1].position = 0.85; ramp.color_ramp.elements[1].color = (0.02, 0.28, 0.95, 1)
L.new(se.outputs["Z"], ramp.inputs["Fac"])
bg2 = N.new("ShaderNodeBackground"); bg2.inputs["Strength"].default_value = 1.0; L.new(ramp.outputs["Color"], bg2.inputs["Color"])
bgl = N.new("ShaderNodeBackground"); bgl.inputs["Color"].default_value = (0.55, 0.72, 1.0, 1); bgl.inputs["Strength"].default_value = 0.9
mx = N.new("ShaderNodeMixShader"); L.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); L.new(bgl.outputs[0], mx.inputs[1]); L.new(bg2.outputs[0], mx.inputs[2])
L.new(mx.outputs[0], N["World Output"].inputs["Surface"])
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10)); SUN = bpy.context.active_object; SUN.name = "Sun"
SUN.data.energy = 4.0; SUN.data.color = (1.0, 0.93, 0.80); SUN.data.angle = math.radians(4)
SUN.rotation_euler = (math.radians(50), 0, math.radians(-35))   # from the front-left: lights the bin front and faces

# ================================================================== materials
paint = mat("M_BinPaint", (0.03, 0.20, 0.85), rough=0.38, coat=0.35)        # saturated royal blue enamel
paint_in = mat("M_BinInside", (0.02, 0.36, 0.55), rough=0.45, coat=0.15)     # deep teal inside
trim = mat("M_BinTrim", (1.0, 0.72, 0.02), rough=0.35, coat=0.3)             # true yellow trim
steel = mat("M_Steel", (0.62, 0.66, 0.72), rough=0.28, metal=1.0)
paintB = mat("M_BinPaintB", (0.05, 0.62, 0.18), rough=0.38, coat=0.35)       # green bin
paintC = mat("M_BinPaintC", (0.50, 0.08, 0.62), rough=0.38, coat=0.35)       # purple bin
logo_dark = bpy.data.images.load("/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png")

def logo_mat(name, bgcol):
    m = mat(name, bgcol, rough=0.4, coat=0.3); nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = logo_dark; tx.extension = 'CLIP'
    uv = nt.nodes.new("ShaderNodeUVMap")
    nt.links.new(uv.outputs["UV"], tx.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.inputs["A"].default_value = (*bgcol, 1)
    nt.links.new(tx.outputs["Alpha"], mix.inputs["Factor"]); nt.links.new(tx.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
    return m
LOGO_M = logo_mat("M_LogoPanel", (1.0, 0.78, 0.05))

def plane_uv(name, w, h, loc, rot, material, parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(material)
    if parent is not None:
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = parent.matrix_world @ mw
    return o

# ================================================================== the bins
BX0, BX1, BY0, BY1, BZ1 = -0.90, 0.90, -0.75, 0.75, 2.90
T = 0.03
CH = (-0.48, 0.48, 1.20, 1.90)     # chute x0 x1 z0 z1
CP = (-0.50, 0.50, 0.12, 1.10)     # cut panel x0 x1 z0 z1
FLOOR = 0.12

def slab(name, x0, x1, y0, y1, z0, z1, m, parent, bevel=0.004):
    o = box(name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m, bevel=bevel, segs=2)
    o.parent = parent
    if len(o.data.materials) == 1 and m is paint:
        o.data.materials.append(paint_in)
        # faces pointing into the bin interior get the inside colour
        for p in o.data.polygons:
            c = p.center; n = p.normal
            inside = (BX0 + T - 0.002 < c.x < BX1 - T + 0.002 and BY0 + T - 0.002 < c.y < BY1 - T + 0.002) or \
                     (abs(c.x - (BX0 + T)) < 0.003 and n.x > 0.5) or (abs(c.x - (BX1 - T)) < 0.003 and n.x < -0.5) or \
                     (abs(c.y - (BY0 + T)) < 0.003 and n.y > 0.5) or (abs(c.y - (BY1 - T)) < 0.003 and n.y < -0.5) or \
                     (abs(c.z - (BZ1 - T)) < 0.003 and n.z < -0.5) or (abs(c.z - FLOOR) < 0.003 and n.z > 0.5)
            p.material_index = 1 if inside else 0
    return o

def make_bin(tag, x, body_m, hero=False):
    root = empty("Bin" + tag, loc=(x, 0, 0), size=0.3)
    bpy.context.view_layer.update()
    parts = []
    P = lambda *aa, **kk: parts.append(slab(*aa, **kk)) or parts[-1]
    m = body_m
    # side, back walls, roof plate, floor plate
    P(tag + "_wallL", BX0, BX0 + T, BY0, BY1, FLOOR, BZ1, m, root)
    P(tag + "_wallR", BX1 - T, BX1, BY0, BY1, FLOOR, BZ1, m, root)
    P(tag + "_wallBack", BX0 + T, BX1 - T, BY1 - T, BY1, FLOOR, BZ1, m, root)
    P(tag + "_roofPlate", BX0 + T, BX1 - T, BY0 + T, BY1 - T, BZ1 - T, BZ1, m, root)
    P(tag + "_floor", BX0 + T, BX1 - T, BY0 + T, BY1 - T, 0.06, FLOOR, m, root)
    # front wall around the chute and the cut panel
    fy0, fy1 = BY0, BY0 + T
    P(tag + "_frontL", BX0 + T, CP[0], fy0, fy1, FLOOR, BZ1 - T, m, root)
    P(tag + "_frontR", CP[1], BX1 - T, fy0, fy1, FLOOR, BZ1 - T, m, root)
    P(tag + "_frontMid", CP[0], CP[1], fy0, fy1, CP[3], CH[2], m, root)
    P(tag + "_frontTop", CP[0], CP[1], fy0, fy1, CH[3], BZ1 - T, m, root)
    P(tag + "_chuteSideL", CP[0], CH[0], fy0, fy1, CH[2], CH[3], m, root)
    P(tag + "_chuteSideR", CH[1], CP[1], fy0, fy1, CH[2], CH[3], m, root)
    panel = slab(tag + "_cutPanel", CP[0] + 0.0015, CP[1] - 0.0015, fy0, fy1, CP[2] + 0.0015, CP[3] - 0.0015, m, root, bevel=0.0)
    # plinth (recessed black base) and pitched roof with overhang
    blk = mat("M_Plinth", (0.04, 0.04, 0.06), rough=0.5)
    box(tag + "_plinth", (BX1 - BX0 - 0.06, BY1 - BY0 - 0.06, 0.06), (0, 0, 0.03), blk, bevel=0.005).parent = root
    me = bpy.data.meshes.new(tag + "_roof"); bm = bmesh.new()
    ov = 0.07; zr0 = BZ1; zr1 = BZ1 + 0.22
    vs = [bm.verts.new(v) for v in ((BX0 - ov, BY0 - ov, zr0), (BX1 + ov, BY0 - ov, zr0), (BX1 + ov, 0, zr1), (BX0 - ov, 0, zr1),
                                    (BX0 - ov, BY1 + ov, zr0), (BX1 + ov, BY1 + ov, zr0))]
    bm.faces.new((vs[0], vs[1], vs[2], vs[3])); bm.faces.new((vs[3], vs[2], vs[5], vs[4]))
    bm.faces.new((vs[0], vs[3], vs[4])); bm.faces.new((vs[1], vs[5], vs[2]))
    bm.to_mesh(me); bm.free()
    roof = bpy.data.objects.new(tag + "_roof", me); sc.collection.objects.link(roof); roof.parent = root
    me.materials.append(trim)
    so = roof.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.03; bv = roof.modifiers.new("bev", 'BEVEL'); bv.width = 0.006; bv.segments = 2
    # stamped vertical ribs on the sides and back
    for xs in (BX0 - 0.012, BX1):
        for yy in (-0.45, -0.15, 0.15, 0.45):
            box(tag + "_rib", (0.012, 0.05, 2.4), (xs + 0.006, yy, 1.45), m, bevel=0.004).parent = root
    for xx in (-0.6, -0.2, 0.2, 0.6):
        box(tag + "_ribB", (0.05, 0.012, 2.4), (xx, BY1 + 0.006, 1.45), m, bevel=0.004).parent = root
    # yellow trim bands
    box(tag + "_trimLow", (BX1 - BX0 + 0.024, BY1 - BY0 + 0.024, 0.06), (0, 0, 0.15), trim, bevel=0.004).parent = root
    # chute frame (outer flange = the STOP LIP: overlaps the opening by 18 mm, so the flap cannot swing out)
    lip = 0.018; fr = 0.05; fz = 0.016
    for nm, x0, x1, z0, z1 in (("L", CH[0] - fr, CH[0] + lip, CH[2] - fr, CH[3] + fr), ("R", CH[1] - lip, CH[1] + fr, CH[2] - fr, CH[3] + fr),
                               ("B", CH[0] + lip, CH[1] - lip, CH[2] - fr, CH[2] + lip), ("T", CH[0] + lip, CH[1] - lip, CH[3] - lip, CH[3] + fr)):
        o = box(tag + "_chuteFrame" + nm, (x1 - x0, fz, z1 - z0), ((x0 + x1) / 2, BY0 - fz / 2, (z0 + z1) / 2), trim, bevel=0.004)
        o.parent = root
    # header logo panel (DA KRAS FILMS) above the chute, and on the side wall
    hdr = plane_uv(tag + "_logoFront", 0.86, 0.37, (0, BY0 - 0.003, 2.46), (math.radians(90), 0, 0), LOGO_M, parent=root)
    side = plane_uv(tag + "_logoSide", 0.86, 0.37, (BX0 - 0.016, -0.05, 2.30), (math.radians(90), 0, math.radians(-90)), LOGO_M, parent=root)
    flap = None
    if hero:
        # flap: origin on the hinge line, closed = in the opening plane, rotation_euler.x > 0 swings it INTO the bin
        flap = empty(tag + "_FlapHinge", loc=(x, BY0 + 0.012, CH[3] - 0.012), size=0.05)
        fp = box(tag + "_Flap", (CH[1] - CH[0] - 0.012, 0.018, CH[3] - CH[2] - 0.012), (x, BY0 + 0.012, (CH[2] + CH[3]) / 2 - 0.006), trim, bevel=0.004)
        mw = fp.matrix_world.copy(); fp.parent = flap; fp.matrix_world = mw
        hp = cyl(tag + "_HingePin", 0.012, CH[1] - CH[0] - 0.04, (x, BY0 + 0.012, CH[3] - 0.012), steel, rot=(0, math.radians(90), 0), verts=16)
        # gravity latch: a steel pawl on the inside of the bottom frame + a catch plate on the flap's inside face
        latch = empty(tag + "_LatchPivot", loc=(x, BY0 + T + 0.05, CH[2] - 0.035), size=0.03)
        pawl = box(tag + "_LatchPawl", (0.07, 0.10, 0.016), (x, BY0 + T + 0.015, CH[2] - 0.035), steel, bevel=0.003)
        mw = pawl.matrix_world.copy(); pawl.parent = latch; pawl.matrix_world = mw
        cyl(tag + "_LatchAxle", 0.008, 0.10, (x, BY0 + T + 0.05, CH[2] - 0.035), steel, rot=(0, math.radians(90), 0), verts=12)
        box(tag + "_LatchBracket", (0.12, 0.03, 0.05), (x, BY0 + T + 0.065, CH[2] - 0.045), steel, bevel=0.003)
        cat = box(tag + "_FlapCatch", (0.08, 0.025, 0.02), (x, BY0 + 0.012 + 0.02, CH[2] + 0.02), steel, bevel=0.003)
        mw = cat.matrix_world.copy(); cat.parent = fp; cat.matrix_world = mw
        # light leaks: slit vents high on the side walls (dark slots outside, warm emissive glow inside)
        for xs, nx in ((BX0 + T + 0.001, 1), (BX1 - T - 0.001, -1)):
            for k in range(6):
                yy = -0.5 + k * 0.2
                o = plane_uv(tag + "_ventGlow", 0.14, 0.022, (xs, yy, 2.62), (math.radians(90), 0, math.radians(90 * nx)), mat("M_Vent", (1, 0.8, 0.5), emit=((1.0, 0.82, 0.55), 6.0)))
                o.parent = root
                o2 = plane_uv(tag + "_ventDark", 0.14, 0.022, (xs - nx * (T + 0.003), yy, 2.62), (math.radians(90), 0, math.radians(-90 * nx)), mat("M_VentDark", (0.01, 0.01, 0.02)))
                o2.parent = root
    else:
        fp = box(tag + "_Flap", (CH[1] - CH[0] - 0.012, 0.018, CH[3] - CH[2] - 0.012), (x, BY0 + 0.012, (CH[2] + CH[3]) / 2 - 0.006), trim, bevel=0.004)
        panel_m = panel
    return root, panel, flap

BIN, PANEL, FLAP = make_bin("A", 0.0, paint, hero=True)
make_bin("B", 2.6, paintB); make_bin("C", 5.2, paintC)
log("hero bin built; chute", CH, "cut panel", CP)

# ================================================================== the clothes heap inside the hero bin (bags + clothes)
IX0, IX1, IY0, IY1 = BX0 + T, BX1 - T, BY0 + T, BY1 - T
def heap_h(x, y):
    base = 0.05 + 0.26 * ((y - IY0) / (IY1 - IY0)) ** 0.8      # low at the front (cut panel), higher at the back
    h = 0.0
    for (bx, by, r, a_) in HEAP_BLOBS:
        d2 = ((x - bx) ** 2 + (y - by) ** 2) / (r * r)
        if d2 < 4: h += a_ * math.exp(-d2)
    return FLOOR + base + h
rnd = random.Random(4)
HEAP_BLOBS = [(rnd.uniform(IX0, IX1), rnd.uniform(IY0, IY1), rnd.uniform(0.12, 0.22), rnd.uniform(0.04, 0.09)) for _ in range(40)]
me = bpy.data.meshes.new("Heap"); bm = bmesh.new()
NX, NY = 44, 36; vv = {}
for i in range(NX + 1):
    for j in range(NY + 1):
        x = IX0 + 0.004 + (IX1 - IX0 - 0.008) * i / NX; y = IY0 + 0.004 + (IY1 - IY0 - 0.008) * j / NY
        vv[i, j] = bm.verts.new((x, y, heap_h(x, y)))
for i in range(NX):
    for j in range(NY):
        bm.faces.new((vv[i, j], vv[i + 1, j], vv[i + 1, j + 1], vv[i, j + 1]))
# skirt down to the floor plate on all four sides (no gap under the heap)
bm.to_mesh(me); bm.free()
HEAP = bpy.data.objects.new("Heap", me); sc.collection.objects.link(HEAP)
for p in HEAP.data.polygons: p.use_smooth = True
hm = mat("M_Heap", (0.8, 0.2, 0.3), rough=0.85, sheen=0.3)
nt = hm.node_tree; p = nt.nodes["Principled BSDF"]
tcn = nt.nodes.new("ShaderNodeTexCoord")
# fabric patchwork: noise-warped cells (crumpled garments of many colours) + fold wrinkles
wn = nt.nodes.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 3.0; wn.inputs["Detail"].default_value = 3.0
wm = nt.nodes.new("ShaderNodeMix"); wm.data_type = 'VECTOR'; wm.inputs["Factor"].default_value = 0.35
nt.links.new(tcn.outputs["Object"], wm.inputs["A"]); nt.links.new(wn.outputs["Color"], wm.inputs["B"])
vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 5.0
nt.links.new(wm.outputs["Result"], vo.inputs["Vector"])
hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 1.6; hs.inputs["Value"].default_value = 1.0
nt.links.new(vo.outputs["Color"], hs.inputs["Color"])
fold = nt.nodes.new("ShaderNodeTexWave"); fold.inputs["Scale"].default_value = 14; fold.inputs["Distortion"].default_value = 12; fold.inputs["Detail"].default_value = 4
nt.links.new(wm.outputs["Result"], fold.inputs["Vector"])
dk = nt.nodes.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; dk.inputs["Factor"].default_value = 0.45
nt.links.new(hs.outputs["Color"], dk.inputs["A"]); nt.links.new(fold.outputs["Color"], dk.inputs["B"])
nt.links.new(dk.outputs["Result"], p.inputs["Base Color"])
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.02
nt.links.new(fold.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
HEAP.data.materials.append(hm)
sd = HEAP.modifiers.new("subd", 'SUBSURF'); sd.levels = 1; sd.render_levels = 1
# skirt walls
for nm, x0, x1, y0, y1 in (("F", IX0, IX1, IY0, IY0 + 0.01), ("Bk", IX0, IX1, IY1 - 0.01, IY1), ("L", IX0, IX0 + 0.01, IY0, IY1), ("R", IX1 - 0.01, IX1, IY0, IY1)):
    box("HeapSkirt" + nm, (x1 - x0, y1 - y0, 0.30), ((x0 + x1) / 2, (y0 + y1) / 2, FLOOR + 0.15), hm, bevel=0)
sc["heap_blobs"] = json.dumps(HEAP_BLOBS)

def imp(path, name, size, loc, rot=(0, 0, 0)):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if len(meshes) > 1: bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    for x in new:
        if x != o and x.name in bpy.data.objects: bpy.data.objects.remove(x, do_unlink=True)
    pts = [Vector(c) for c in o.bound_box]; mn = Vector([min(p_[i] for p_ in pts) for i in range(3)]); mx_ = Vector([max(p_[i] for p_ in pts) for i in range(3)])
    s = size / max(mx_ - mn)
    for v in o.data.vertices: v.co = (v.co - Vector(((mn.x + mx_.x) / 2, (mn.y + mx_.y) / 2, mn.z))) * s
    o.location = loc; o.rotation_euler = rot
    log("import", name, "dims", [round(x, 3) for x in o.dimensions])
    return o

# real clothes piles sitting ON the heap in the back corners (she never lies there)
for k, (x, y, s, rz) in enumerate(((-0.55, 0.45, 0.62, 0.3), (0.55, 0.48, 0.66, 2.0), (0.64, -0.10, 0.50, 4.1), (-0.62, -0.05, 0.48, 1.1), (0.05, 0.52, 0.55, 5.0), (-0.60, -0.50, 0.40, 2.6), (0.62, -0.52, 0.40, 3.3))):
    o = imp(DL + "/clothes2/scene.gltf", "ClothesPile%d" % k, s, (x, y, 0), (0, 0, rz))
    bpy.context.view_layer.update()
    zmin = min((o.matrix_world @ v.co).z - heap_h((o.matrix_world @ v.co).x, (o.matrix_world @ v.co).y) for v in o.data.vertices)
    o.location.z -= zmin + 0.01        # rests ON the heap (lowest point 1 cm sunk into the soft pile)
    o.parent = BIN
    for m in o.data.materials:
        if m and m.use_nodes:
            for pn in [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']: pn.inputs["Roughness"].default_value = 0.8

# ================================================================== props
CRATES = []
for k in range(2):
    c = imp(DL + "/crate/scene.gltf", "Crate%d" % k, 0.33, ((0.0, BY0 - 0.30, 0.0), (-0.75, BY0 - 0.42, 0.0))[k], (0, 0, (0, 0.5)[k]))
    c.data.materials.clear(); c.data.materials.append(mat("M_Crate", (0.92, 0.06, 0.08), rough=0.4, coat=0.2))
    CRATES.append(c)
bpy.context.view_layer.update()
CRATE_TOP = max((CRATES[0].matrix_world @ v.co).z for v in CRATES[0].data.vertices)
sc["crate_top"] = CRATE_TOP; log("crate top", round(CRATE_TOP, 3))
# a solid lid board on the top crate (she stands on it; no feet in the crate's open grid)
box("CrateBoard", (0.36, 0.36, 0.02), (0.0, BY0 - 0.30, CRATE_TOP + 0.01), mat("M_Board", (0.95, 0.55, 0.12), rough=0.5), bevel=0.003)
sc["stand_top"] = CRATE_TOP + 0.02

H1 = imp(DL + "/helmet2/scene.gltf", "Helmet1", 0.34, (20, 0, 0)); H2 = H1.copy(); H2.data = H1.data.copy(); H2.name = "Helmet2"; sc.collection.objects.link(H2)
for m in H1.data.materials:
    if m and m.use_nodes:
        for pn in [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']:
            pn.inputs["Roughness"].default_value = max(0.3, pn.inputs["Roughness"].default_value)
SAW = imp(DL + "/saw/scene.gltf", "Saw", 0.31, (20, 2, 0))
SAW.data.materials.clear(); SAW.data.materials.append(mat("M_Saw", (0.95, 0.12, 0.05), rough=0.35, coat=0.3))
# the passer-by's donation bag (plain purple)
bag = imp(DL + "/clothes2/scene.gltf", "DonationBag", 0.30, (20, 4, 0))

# glowing cut line on the inside of the cut panel seam (revealed by a keyed mask in 02_animate) + spark emitter
glow_m = mat("M_CutGlow", (1.0, 0.45, 0.05), emit=((1.0, 0.45, 0.05), 30.0))
CUT = []
for nm, x0, x1, z0, z1 in (("B", CP[0], CP[1], CP[2], CP[2] + 0.012), ("R", CP[1] - 0.012, CP[1], CP[2], CP[3]),
                           ("T", CP[0], CP[1], CP[3] - 0.012, CP[3]), ("L", CP[0], CP[0] + 0.012, CP[2], CP[3])):
    o = box("CutGlow" + nm, (x1 - x0, 0.004, z1 - z0), ((x0 + x1) / 2, BY0 + T + 0.003, (z0 + z1) / 2), glow_m, bevel=0)
    CUT.append(o)
spark_m = mat("M_Spark", (1.0, 0.6, 0.1), emit=((1.0, 0.55, 0.12), 40.0))
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.004, location=(30, 0, 0)); SPK = bpy.context.active_object; SPK.name = "SparkInst"
SPK.data.materials.append(spark_m)
bpy.ops.mesh.primitive_plane_add(size=0.02, location=(0, BY0 + T + 0.01, 0.6)); EM = bpy.context.active_object; EM.name = "SparkEmitter"
EM.rotation_euler = (math.radians(-90), 0, 0)
ps = EM.modifiers.new("sparks", 'PARTICLE_SYSTEM').particle_system; pst = ps.settings
pst.count = 900; pst.frame_start = 1870; pst.frame_end = 1955; pst.lifetime = 22; pst.lifetime_random = 0.5
pst.normal_factor = 2.2; pst.factor_random = 1.4; pst.effector_weights.gravity = 1.0
pst.render_type = 'OBJECT'; pst.instance_object = SPK; pst.particle_size = 1.0; pst.size_random = 0.6
pst.use_rotations = False; EM.show_instancer_for_render = False
pst.physics_type = 'NEWTON'; pst.use_die_on_collision = False

# ================================================================== the parking lot
asph = mat("M_Asphalt", (0.10, 0.10, 0.16), rough=0.8)
nt = asph.node_tree; p = nt.nodes["Principled BSDF"]
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 120
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.07, 0.07, 0.13, 1); cr.color_ramp.elements[1].color = (0.20, 0.17, 0.26, 1)
nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
GROUND = box("Ground", (40, 40, 0.1), (0, -8, -0.05), asph, bevel=0)
line_m = mat("M_Lines", (1.0, 0.82, 0.02), rough=0.5)
for k in range(-4, 6):
    box("ParkLine", (0.10, 4.5, 0.004), (-1.6 + k * 2.7, -4.6, 0.002), line_m, bevel=0)
box("CurbLine", (30, 0.12, 0.004), (0, -1.9, 0.002), line_m, bevel=0)
brick = mat("M_Brick", (0.80, 0.25, 0.10), rough=0.8)
nt = brick.node_tree; p = nt.nodes["Principled BSDF"]
tcb = nt.nodes.new("ShaderNodeTexCoord"); br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0
br.inputs["Color1"].default_value = (0.82, 0.24, 0.09, 1); br.inputs["Color2"].default_value = (0.62, 0.14, 0.06, 1); br.inputs["Mortar"].default_value = (0.85, 0.75, 0.62, 1)
br.inputs["Brick Width"].default_value = 0.24; br.inputs["Row Height"].default_value = 0.075; br.inputs["Mortar Size"].default_value = 0.01
se2 = nt.nodes.new("ShaderNodeSeparateXYZ"); ad = nt.nodes.new("ShaderNodeMath"); co = nt.nodes.new("ShaderNodeCombineXYZ")
nt.links.new(tcb.outputs["Object"], se2.inputs[0]); nt.links.new(se2.outputs["X"], ad.inputs[0]); nt.links.new(se2.outputs["Y"], ad.inputs[1])
nt.links.new(ad.outputs[0], co.inputs["X"]); nt.links.new(se2.outputs["Z"], co.inputs["Y"]); nt.links.new(co.outputs[0], br.inputs["Vector"])
nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; nt.links.new(br.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
WALL = box("BackWall", (24, 0.3, 4.2), (2, 2.2, 2.1), brick, bevel=0)
door_m = mat("M_Door", (0.02, 0.55, 0.60), rough=0.4, coat=0.3)
box("BackDoor", (1.0, 0.06, 2.1), (-2.6, 2.03, 1.05), door_m, bevel=0.01)
box("DoorFrame", (1.16, 0.04, 2.2), (-2.6, 2.04, 1.1), trim, bevel=0.005)
cyl("DoorHandle", 0.015, 0.14, (-2.2, 1.99, 1.0), steel, rot=(0, 0, 0), verts=12)
lamp_m = mat("M_Lamp", (0.05, 0.05, 0.07), rough=0.4)
box("WallLampArm", (0.06, 0.4, 0.06), (-2.6, 1.85, 2.55), lamp_m, bevel=0.005)
box("WallLampHead", (0.3, 0.2, 0.1), (-2.6, 1.68, 2.5), lamp_m, bevel=0.01)
# planters with shrubs on the left of the row (life in the background)
pl_m = mat("M_Planter", (0.95, 0.45, 0.08), rough=0.5, coat=0.2); leaf = mat("M_Leaf", (0.10, 0.62, 0.15), rough=0.6, sheen=0.3)
for k, x in enumerate((-4.2, -5.6)):
    box("Planter%d" % k, (0.9, 0.9, 0.55), (x, 1.2, 0.275), pl_m, bevel=0.02)
    for j in range(7):
        sphere("Shrub%d_%d" % (k, j), 0.22 + 0.06 * (j % 3), (x + 0.25 * math.cos(j), 1.2 + 0.25 * math.sin(j), 0.75 + 0.1 * (j % 2)), leaf, segs=12)
# bollards in front of the lot
for k, x in enumerate((-3.4, 3.6, 7.8)):
    cyl("Bollard%d" % k, 0.09, 0.9, (x, -2.2, 0.45), trim, verts=20)

# ================================================================== inside lights (keyed in 02_animate: day / night cycles)
def area(name, loc, rot, size, energy, color):
    bpy.ops.object.light_add(type='AREA', location=loc, rotation=rot); l = bpy.context.active_object; l.name = name
    l.data.size = size; l.data.energy = energy; l.data.color = color; l.data.shape = 'SQUARE'
    return l
IN_KEY = area("InKey", (0.0, -0.45, 2.70), (0, 0, 0), 0.6, 60.0, (1.0, 0.85, 0.65))         # warm leak from the vents / flap edge
IN_FILL = area("InFill", (0.6, 0.55, 1.6), (math.radians(60), 0, math.radians(140)), 0.5, 25.0, (0.55, 0.75, 1.0))
for l in (IN_KEY, IN_FILL):
    l.visible_camera = False
# catchlight near the camera is added in 02_animate (parented to the camera)

sc["CH"] = list(CH); sc["CP"] = list(CP); sc["BIN"] = [BX0, BX1, BY0, BY1, BZ1, T, FLOOR]
bpy.ops.object.select_all(action='DESELECT')
open(OUT + ".log.txt", "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_OK", OUT)
