"""Mary Celeste thumbnail, dark premium style: a high 3/4 top-down view of the ship, painted matte Seldom yellow
(#E3FF00, sampled from the brand logo), alone on a deep, dark, moody sea. Sails half furled and torn (as found), the
deck deserted, the boat davits on the quarter EMPTY with their falls hanging slack. Soft key from above so the ship
glows, a gentle rim, low mist patches, a faint moonlit sheen, a few drifting motes. Clean dark sea beside the ship on
the davit side for the user's arrow + word. No text, no people.
    VIEW=A  port quarter   (davits to port, space left of the ship)
    VIEW=B  starboard bow  (davits to starboard, space right of the ship)
    PREVIEW=0.4 SPP=32 VIEW=A blender -b --python mc_dark.py"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
C = T.use("mc")
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
import ship, sea
E = os.environ.get
VIEW = E("VIEW", "B")
sc = T.res_setup(int(E("SPP", "256")), noise=0.012)
rng = random.Random(4)

# ---------------------------------------------------------------- the ship, as found
mc = ship.build("MC", sails="found", wind=Vector((0.4, -1.0, 0)).normalized(), wet=0.3, detail=True,
                boat_chocks=True, bow_wave_h=float(E("BOWW", "0.0")))
HEAD = float(E("HEAD", "0"))
mc["root"].location = (0, 0, float(E("SINK", "-0.8")))
mc["root"].rotation_euler = (math.radians(float(E("HEEL", "-3"))), 0, math.radians(HEAD))
bpy.context.view_layer.update()

# brand yellow, matte paint (sRGB 227,255,0 -> linear)
def s2l(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
BRAND = tuple(s2l(c) for c in (227, 255, 0))
def matte(name, col, rough=0.62, var=0.08):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]; p.inputs['Roughness'].default_value = rough
    p.inputs['Specular IOR Level'].default_value = 0.3
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 6
    mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 1 - var; mr.inputs['To Max'].default_value = 1.0
    L.new(nz.outputs['Fac'], mr.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs[6].default_value = (*col, 1)
    cm = N.new("ShaderNodeCombineColor"); L.new(mr.outputs[0], cm.inputs[0]); L.new(mr.outputs[0], cm.inputs[1]); L.new(mr.outputs[0], cm.inputs[2])
    L.new(cm.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])
    return m
Y_PAINT = matte("brand_yellow", BRAND)
Y_SAIL = matte("brand_yellow_sail", tuple(0.8 * c + 0.2 * 0.9 for c in BRAND), rough=0.85, var=0.12)
Y_DECK = matte("brand_yellow_deck", tuple(c * 0.72 for c in BRAND), rough=0.7, var=0.15)
DARK = matte("rigging_dark", (0.012, 0.012, 0.01), rough=0.7, var=0.05)
def tint_yellow(m, col, lo=0.5, gain=0.8, ao=True, sheen=0.25):
    """Keep the material's own detail (planks, grime, chips) as a luminance pattern, recoloured to the brand
    yellow: base = col * (lo + gain * luma(original)), darkened toward olive in cavities (AO)."""
    m = m.copy(); nt = m.node_tree; N = nt.nodes; L = nt.links
    for p in [n for n in N if n.type == 'BSDF_PRINCIPLED']:
        src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
        bw = N.new("ShaderNodeRGBToBW")
        if src is not None:
            L.new(src, bw.inputs[0])
        else:
            bw.inputs[0].default_value = p.inputs['Base Color'].default_value
        # normalise: stretch the pattern so dark paints (the black topsides) still carry their variation
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.35
        mr.inputs['To Min'].default_value = lo; mr.inputs['To Max'].default_value = lo + gain; L.new(bw.outputs[0], mr.inputs['Value'])
        cc = N.new("ShaderNodeMix"); cc.data_type = 'RGBA'; cc.blend_type = 'MULTIPLY'; cc.inputs['Factor'].default_value = 1.0
        cc.inputs[6].default_value = (*col, 1)
        cm = N.new("ShaderNodeCombineColor")
        for k in range(3):
            L.new(mr.outputs[0], cm.inputs[k])
        L.new(cm.outputs[0], cc.inputs[7]); out = cc.outputs[2]
        if ao:
            aon = N.new("ShaderNodeAmbientOcclusion"); aon.inputs['Distance'].default_value = 1.2; aon.samples = 8
            olive = N.new("ShaderNodeMix"); olive.data_type = 'RGBA'; olive.inputs[7].default_value = (*col, 1)
            olive.inputs[6].default_value = (col[0] * 0.18, col[1] * 0.2, 0.004, 1)        # olive-brown in the cavities
            L.new(aon.outputs['AO'], olive.inputs['Factor'])
            mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
            L.new(out, mul.inputs[6]); L.new(olive.outputs[2], mul.inputs[7]); out = mul.outputs[2]
            # rescale (multiply by yellow twice): divide back by the brand colour so lit faces stay on-brand
            div = N.new("ShaderNodeMix"); div.data_type = 'RGBA'; div.blend_type = 'DIVIDE'; div.inputs['Factor'].default_value = 1.0
            L.new(out, div.inputs[6]); div.inputs[7].default_value = (max(col[0], 0.05), max(col[1], 0.05), 1.0, 1); out = div.outputs[2]
        L.new(out, p.inputs['Base Color'])
        p.inputs['Coat Weight'].default_value = sheen; p.inputs['Coat Roughness'].default_value = 0.25
    return m


CREAM = (1.0, 0.95, 0.62)
cache = {}
for o in mc["coll"].all_objects:
    if o.type not in ('MESH', 'CURVE'):
        continue
    mats = o.data.materials
    for i, m in enumerate(mats):
        if m is None:
            continue
        n = m.name
        if any(k in n for k in ("rope", "iron", "deadeye", "_dark")):
            mats[i] = DARK; continue
        if n not in cache:
            if "canvas" in n:
                cache[n] = tint_yellow(m, CREAM, lo=0.55, gain=0.7, sheen=0.0)
            elif "bottom" in n:
                cache[n] = tint_yellow(m, (0.08, 0.07, 0.03), lo=0.6, gain=0.6, ao=False)
            else:
                cache[n] = tint_yellow(m, BRAND, lo=0.3, gain=1.0)
        mats[i] = cache[n]

# ---------------------------------------------------------------- empty boat davits on the quarter, falls hanging slack
SIDE = 1 if VIEW == "A" else -1          # A: port (+y), B: starboard (-y)
hb = ship.B / 2 - 0.25
def davit(x):
    pts = []
    base = Vector((x, SIDE * hb, ship.zdeck(x) + 0.2))
    for k in range(13):
        a = math.radians(90 * k / 12)
        pts.append(base + Vector((0, SIDE * (3.4 * (1 - math.cos(a))), 6.4 * math.sin(a))))
    for p0, p1 in zip(pts, pts[1:]):
        ship.cyl("davit", p0, p1, 0.26, mat=Y_PAINT, verts=16)
    tip = pts[-1]
    # the falls: two lines down from a block, cut loose, trailing into the water
    ship.cyl("davit_block", tip - Vector((0, 0, 0.15)), tip - Vector((0, 0, 0.9)), 0.22, mat=DARK, verts=12)
    for dx in (-0.14, 0.14):
        a = tip - Vector((0, 0, 0.9)) + Vector((dx, 0, 0))
        b = Vector((a.x + rng.uniform(-0.3, 0.3), a.y + SIDE * 0.2, -0.3))            # straight down into the water
        ship.cyl("davit_fall", a, b, 0.09, mat=DARK, verts=8)
        c = b + Vector((rng.uniform(-2.5, -1.5), SIDE * rng.uniform(0.5, 1.2), 0.05))  # trailing on the surface
        ship.cyl("davit_fall", b, c, 0.09, mat=DARK, verts=8)
for x in (float(E("DAV1", "-6.5")), float(E("DAV2", "-2.3"))):
    davit(x)
dv = [o for o in bpy.data.objects if o.name.startswith(("davit",))]
for o in dv:
    o.parent = mc["root"]; o.matrix_parent_inverse = mc["root"].matrix_world.inverted()

# ---------------------------------------------------------------- the sea: deep, dark, subtle swell
water = sea.water_material(deep=(0.06, 0.08, 0.1), crest=(0.11, 0.14, 0.17), fog_color=(0.06, 0.085, 0.11), foam_attr="nofoam")
water.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.22
water.node_tree.nodes["Principled BSDF"].inputs['Specular IOR Level'].default_value = 0.3
for n_ in water.node_tree.nodes:
    if n_.type == 'MATH' and n_.operation == 'MULTIPLY' and abs(n_.inputs[1].default_value - 0.45) < 1e-6:
        n_.inputs[1].default_value = float(E("WASH_K", "2.6"))
import functools
_hf = sea._hull_foam
sea._hull_foam = lambda o, hulls, reach=1.4, cut=None: _hf(o, hulls, reach=float(E("WASH_R", "3.2")), cut=cut)
sea.ocean(size=160, res=int(E("OCEAN_RES", "12")), scale=1.5, chop=1.5, wind=13, repeat=3, foam=0.0, mat=water,
          direction=-60, hulls=(mc["hull"],), loc=(0, 0, 0), seed=5)
sea.far_sea(240, mat=water, center=(0, 0))

# ---------------------------------------------------------------- light: dark blue-grey night, key from above, rim, moon sheen
w = bpy.data.worlds.new("night"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.05, 0.075, 0.1, 1)
bg.inputs['Strength'].default_value = float(E("WORLD", "1.8"))
cam_az = {"A": 140.0, "B": -40.0}[VIEW]            # where the camera sits, seen from the ship (deg from +x)
T.sun(cam_az + 180, float(E("MOON_EL", "24")), energy=float(E("MOON_E", "0.22")), color=(0.7, 0.8, 1.0), angle=float(E("MOON_ANG", "5")))
ka = math.radians(cam_az + float(E("KEY_AZ", "110")))
KEYP = Vector((math.cos(ka) * 14, math.sin(ka) * 14, 62))
sp = bpy.data.lights.new("key", 'SPOT'); sp.energy = float(E("KEY_E", "400000")); sp.spot_size = math.radians(float(E("KEY_ANG", "30")))
sp.spot_blend = 0.55; sp.shadow_soft_size = 2.0; sp.color = (1.0, 0.96, 0.86)
key = bpy.data.objects.new("key", sp); sc.collection.objects.link(key); key.location = KEYP
key.rotation_euler = (Vector((0, 0, 4)) - KEYP).to_track_quat('-Z', 'Y').to_euler()
# the beam: a cone of fine mist, lit only by the key
L_ = (Vector((0, 0, -2)) - KEYP).length
bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.5, radius2=math.tan(math.radians(float(E("KEY_ANG", "30")) / 2)) * L_ * 1.25,
                                depth=L_, location=(KEYP + Vector((0, 0, -2))) / 2)
cone = bpy.context.active_object; cone.name = "beam_haze"
cone.rotation_euler = (Vector((0, 0, -2)) - KEYP).to_track_quat('-Z', 'Y').to_euler()
bmat = bpy.data.materials.new("beam_haze"); bmat.use_nodes = True; BN = bmat.node_tree.nodes; BN.remove(BN["Principled BSDF"])
bv = BN.new("ShaderNodeVolumePrincipled"); bv.inputs['Color'].default_value = (0.9, 0.9, 0.85, 1); bv.inputs['Anisotropy'].default_value = 0.55
btc = BN.new("ShaderNodeTexCoord"); bnz = BN.new("ShaderNodeTexNoise"); bnz.inputs['Scale'].default_value = 0.08; bnz.inputs['Detail'].default_value = 4
bmat.node_tree.links.new(btc.outputs['Object'], bnz.inputs['Vector'])
bmr = BN.new("ShaderNodeMapRange"); bmr.inputs['From Min'].default_value = 0.3; bmr.inputs['From Max'].default_value = 0.7
bmr.inputs['To Min'].default_value = float(E("BEAM_D", "0.006")) * 0.3; bmr.inputs['To Max'].default_value = float(E("BEAM_D", "0.006")) * 1.6
bmat.node_tree.links.new(bnz.outputs['Fac'], bmr.inputs['Value']); bmat.node_tree.links.new(bmr.outputs[0], bv.inputs['Density'])
bmat.node_tree.links.new(bv.outputs[0], BN["Material Output"].inputs['Volume']); cone.data.materials.append(bmat); cone.visible_shadow = False
rim_az = math.radians(cam_az + 180)
T.area("rim", (math.cos(rim_az) * 40, math.sin(rim_az) * 40, 18), (0, 0, 6), 10, float(E("RIM_E", "30000")), color=(0.75, 0.85, 1.0))
# key and rim light the ship only (no hot reflections on the sea); the moon gives the sea its sheen
shipc = bpy.data.collections.new("ship_lit"); sc.collection.children.link(shipc)
for o in list(mc["coll"].all_objects) + dv:
    shipc.objects.link(o)
bpy.data.objects["rim"].light_linking.receiver_collection = shipc
# a broad, dim fill on the sea only, so it reads dark blue-grey rather than black
seac = bpy.data.collections.new("sea_lit"); sc.collection.children.link(seac)
for o in bpy.data.objects:
    if o.name.startswith(("Ocean", "FarSea", "far_sea")) or (o.type == 'MESH' and o.data.materials and o.data.materials[0] == water):
        seac.objects.link(o)
T.area("sea_fill", (0, 0, 80), (0, 0, 0), 120, float(E("SEAFILL_E", "70000")), color=(0.82, 0.86, 0.92))
bpy.data.objects["sea_fill"].light_linking.receiver_collection = seac
# low mist lying on the water in patches, and a light overall haze
sea.haze((0, 0, 4), (300, 300, 8), density=float(E("HAZE", "0.0025")), color=(0.6, 0.7, 0.8))
for k in range(int(E("NMIST", "7"))):
    a = rng.uniform(0, 6.28); r = rng.uniform(22, 55)
    sea.mist_puff(f"mist{k}", (math.cos(a) * r, math.sin(a) * r, 1.0), (rng.uniform(10, 18), rng.uniform(6, 10), 1.6),
                  density=float(E("MIST_D", "0.09")), seed=k)
# drifting motes in the light
N_MOTE = int(E("NMOTE", "120"))
_r = np.random.default_rng(2); _t = _r.uniform(0.15, 0.95, N_MOTE)
_axis = np.array(Vector((0, 0, -2)) - KEYP); _base = np.array(KEYP)
_rad = np.tan(math.radians(float(E("KEY_ANG", "30")) / 2)) * np.linalg.norm(_axis) * _t * np.sqrt(_r.uniform(0, 1, N_MOTE))
_ph = _r.uniform(0, 2 * np.pi, N_MOTE)
P = _base + _t[:, None] * _axis + np.stack([np.cos(_ph) * _rad, np.sin(_ph) * _rad, np.zeros(N_MOTE)], 1)
me = bpy.data.meshes.new("motes"); me.from_pydata(P.tolist(), [], []); me.update()
mo = bpy.data.objects.new("motes", me); sc.collection.objects.link(mo)
ng = bpy.data.node_groups.new("motes_pts", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput"); mp = ng.nodes.new("GeometryNodeMeshToPoints")
rv = ng.nodes.new("FunctionNodeRandomValue"); rv.inputs["Min"].default_value = 0.02; rv.inputs["Max"].default_value = 0.05
smn = ng.nodes.new("GeometryNodeSetMaterial")
mm = bpy.data.materials.new("mote"); mm.use_nodes = True; MN = mm.node_tree.nodes; MN.remove(MN["Principled BSDF"])
em = MN.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.95, 0.8, 1); em.inputs['Strength'].default_value = float(E("MOTE_E", "2.5"))
mm.node_tree.links.new(em.outputs[0], MN["Material Output"].inputs['Surface']); smn.inputs['Material'].default_value = mm
ng.links.new(gi.outputs[0], mp.inputs['Mesh']); ng.links.new(rv.outputs['Value'], mp.inputs['Radius'])
ng.links.new(mp.outputs['Points'], smn.inputs['Geometry']); ng.links.new(smn.outputs['Geometry'], go.inputs[0])
mo.modifiers.new("pts", "NODES").node_group = ng

for o in sc.objects:
    if o.type == 'LIGHT' and o.name != "key":
        o.visible_volume_scatter = False

# ---------------------------------------------------------------- foam ring round the hull and a short wake
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, float(E("FOAM_Z", "0.25"))))
FOAMPLANE = E("FOAMPLANE", "0") == "1"
fp_ = bpy.context.active_object; fp_.name = "foam_ring"; fp_.scale = (ship.L + 30, ship.B + 14, 1)
fp_.parent = mc["root"]; fp_.matrix_parent_inverse = mc["root"].matrix_world.inverted()
fm_ = bpy.data.materials.new("foam_ring"); fm_.use_nodes = True; FN = fm_.node_tree.nodes; FL = fm_.node_tree.links
fpb = FN["Principled BSDF"]; fpb.inputs['Base Color'].default_value = (0.85, 0.9, 0.92, 1); fpb.inputs['Roughness'].default_value = 0.7
ftc = FN.new("ShaderNodeTexCoord"); fsep = FN.new("ShaderNodeSeparateXYZ"); FL.new(ftc.outputs['Object'], fsep.inputs[0])
fsx = FN.new("ShaderNodeMath"); fsx.operation = 'MULTIPLY'; fsx.inputs[1].default_value = (ship.L + 30) / (ship.L / 2 + 0.6)
FL.new(fsep.outputs['X'], fsx.inputs[0])
fsy = FN.new("ShaderNodeMath"); fsy.operation = 'MULTIPLY'; fsy.inputs[1].default_value = (ship.B + 14) / (ship.B / 2 + 0.5)
FL.new(fsep.outputs['Y'], fsy.inputs[0])
fcmb = FN.new("ShaderNodeCombineXYZ"); FL.new(fsx.outputs[0], fcmb.inputs[0]); FL.new(fsy.outputs[0], fcmb.inputs[1])
flen = FN.new("ShaderNodeVectorMath"); flen.operation = 'LENGTH'; FL.new(fcmb.outputs[0], flen.inputs[0])
fnz = FN.new("ShaderNodeTexNoise"); fnz.inputs['Scale'].default_value = 6; fnz.inputs['Detail'].default_value = 8; FL.new(ftc.outputs['Object'], fnz.inputs['Vector'])
fadd = FN.new("ShaderNodeMath"); fadd.operation = 'MULTIPLY_ADD'; fadd.inputs[1].default_value = 0.35
FL.new(fnz.outputs['Fac'], fadd.inputs[0]); FL.new(flen.outputs['Value'], fadd.inputs[2])
# ring: strongest just outside the hull (len ~1.15), fading to ~1.6
r1 = FN.new("ShaderNodeMapRange"); r1.inputs['From Min'].default_value = 1.12; r1.inputs['From Max'].default_value = 1.22; FL.new(fadd.outputs[0], r1.inputs['Value'])
r2 = FN.new("ShaderNodeMapRange"); r2.inputs['From Min'].default_value = 1.75; r2.inputs['From Max'].default_value = 1.3; FL.new(fadd.outputs[0], r2.inputs['Value'])
ring = FN.new("ShaderNodeMath"); ring.operation = 'MULTIPLY'; FL.new(r1.outputs[0], ring.inputs[0]); FL.new(r2.outputs[0], ring.inputs[1])
# wake: a fading V behind the stern (local x < 0)
wx = FN.new("ShaderNodeMapRange"); wx.inputs['From Min'].default_value = -0.02; wx.inputs['From Max'].default_value = -0.45
FL.new(fsep.outputs['X'], wx.inputs['Value'])
wfade = FN.new("ShaderNodeMapRange"); wfade.inputs['From Min'].default_value = -0.5; wfade.inputs['From Max'].default_value = -0.2
FL.new(fsep.outputs['X'], wfade.inputs['Value'])
wy = FN.new("ShaderNodeMath"); wy.operation = 'ABSOLUTE'; FL.new(fsep.outputs['Y'], wy.inputs[0])
wband = FN.new("ShaderNodeMath"); wband.operation = 'SUBTRACT'; FL.new(wy.outputs[0], wband.inputs[0]); FL.new(wx.outputs[0], wband.inputs[1])
wb2 = FN.new("ShaderNodeMath"); wb2.operation = 'ABSOLUTE'; FL.new(wband.outputs[0], wb2.inputs[0])
wmr = FN.new("ShaderNodeMapRange"); wmr.inputs['From Min'].default_value = 0.06; wmr.inputs['From Max'].default_value = 0.0; FL.new(wb2.outputs[0], wmr.inputs['Value'])
wm2 = FN.new("ShaderNodeMath"); wm2.operation = 'MULTIPLY'; FL.new(wmr.outputs[0], wm2.inputs[0]); FL.new(wfade.outputs[0], wm2.inputs[1])
wm3 = FN.new("ShaderNodeMath"); wm3.operation = 'MULTIPLY'; FL.new(wm2.outputs[0], wm3.inputs[0]); FL.new(fnz.outputs['Fac'], wm3.inputs[1])
fmax = FN.new("ShaderNodeMath"); fmax.operation = 'MAXIMUM'; FL.new(ring.outputs[0], fmax.inputs[0]); FL.new(wm3.outputs[0], fmax.inputs[1])
fpw = FN.new("ShaderNodeMath"); fpw.operation = 'MULTIPLY'; fpw.inputs[1].default_value = float(E("FOAM_K", "0.9")); fpw.use_clamp = True
FL.new(fmax.outputs[0], fpw.inputs[0])
tr_ = FN.new("ShaderNodeBsdfTransparent"); fmix = FN.new("ShaderNodeMixShader")
FL.new(fpw.outputs[0], fmix.inputs[0]); FL.new(tr_.outputs[0], fmix.inputs[1]); FL.new(fpb.outputs[0], fmix.inputs[2])
FL.new(fmix.outputs[0], FN["Material Output"].inputs['Surface']); fp_.data.materials.append(fm_)
shipc.objects.link(fp_)
if not FOAMPLANE:
    bpy.data.objects.remove(fp_)

# ---------------------------------------------------------------- camera: high 3/4 top-down
EL = math.radians(float(E("CAM_EL", "43"))); DIST = float(E("DIST", "128"))
az = math.radians(cam_az)
cam = Vector((math.cos(az) * math.cos(EL) * DIST, math.sin(az) * math.cos(EL) * DIST, math.sin(EL) * DIST))
# aim beside the ship so it sits off-centre, leaving dark sea on the davit side
tgt0 = Vector((float(E("TX", "0")), 0, float(E("TZ", "7"))))
fwd = (tgt0 - cam).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized()
# A: space to the left of the ship (ship on the right) ; B: space to the right
tgt = tgt0 + right * (-1 if VIEW == "A" else 1) * float(E("SPACE", "13"))
C.camera(cam, tgt, lens=float(E("LENS", "50")), fstop=float(E("FSTOP", "11")), focus=(Vector((0, 0, 6)) - cam).length)

T.grade(sc, sat=float(E("SAT", "1.3")), con=float(E("CON", "1.2")), expo=float(E("EXPO", "0.5")), vig=float(E("VIG", "0.45")))
T.render(sc, "mc_dark_" + VIEW)
