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
DARK = matte("rigging_dark", (0.03, 0.03, 0.025), rough=0.7, var=0.05)
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
            aon = N.new("ShaderNodeAmbientOcclusion"); aon.inputs['Distance'].default_value = 0.6; aon.samples = 8
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
                cache[n] = tint_yellow(m, BRAND)
        mats[i] = cache[n]

# ---------------------------------------------------------------- empty boat davits on the quarter, falls hanging slack
SIDE = 1 if VIEW == "A" else -1          # A: port (+y), B: starboard (-y)
hb = ship.B / 2 - 0.25
def davit(x):
    pts = []
    base = Vector((x, SIDE * hb, ship.zdeck(x) + 0.2))
    for k in range(13):
        a = math.radians(90 * k / 12)
        pts.append(base + Vector((0, SIDE * (2.0 * (1 - math.cos(a))), 3.6 * math.sin(a))))
    for p0, p1 in zip(pts, pts[1:]):
        ship.cyl("davit", p0, p1, 0.14, mat=Y_PAINT, verts=14)
    tip = pts[-1]
    # the falls: two lines down from a block, cut loose, trailing into the water
    ship.cyl("davit_block", tip - Vector((0, 0, 0.1)), tip - Vector((0, 0, 0.45)), 0.11, mat=DARK, verts=12)
    for dx in (-0.06, 0.06):
        a = tip - Vector((0, 0, 0.45)) + Vector((dx, 0, 0))
        b = a + Vector((rng.uniform(-0.4, 0.4), SIDE * 0.3, -(a.z + 0.6)))
        ship.cyl("davit_fall", a, b, 0.04, mat=DARK, verts=8)
for x in (float(E("DAV1", "-6.5")), float(E("DAV2", "-2.3"))):
    davit(x)
dv = [o for o in bpy.data.objects if o.name.startswith(("davit",))]
for o in dv:
    o.parent = mc["root"]; o.matrix_parent_inverse = mc["root"].matrix_world.inverted()

# ---------------------------------------------------------------- the sea: deep, dark, subtle swell
water = sea.water_material(deep=(0.012, 0.024, 0.036), crest=(0.03, 0.06, 0.075), fog_color=(0.04, 0.055, 0.07), foam_attr="nofoam")
water.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.14
water.node_tree.nodes["Principled BSDF"].inputs['Specular IOR Level'].default_value = 0.3
sea.ocean(size=160, res=int(E("OCEAN_RES", "12")), scale=1.5, chop=1.5, wind=13, repeat=3, foam=0.0, mat=water,
          direction=-60, hulls=(mc["hull"],), loc=(0, 0, 0), seed=5)
sea.far_sea(240, mat=water, center=(0, 0))

# ---------------------------------------------------------------- light: dark blue-grey night, key from above, rim, moon sheen
w = bpy.data.worlds.new("night"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.05, 0.075, 0.1, 1)
bg.inputs['Strength'].default_value = float(E("WORLD", "1.8"))
cam_az = {"A": 140.0, "B": -40.0}[VIEW]            # where the camera sits, seen from the ship (deg from +x)
T.sun(cam_az + 180, float(E("MOON_EL", "24")), energy=float(E("MOON_E", "0.22")), color=(0.7, 0.8, 1.0), angle=float(E("MOON_ANG", "5")))
T.area("key", (0, 0, 45), (0, 0, 0), float(E("KEY_SIZE", "18")), float(E("KEY_E", "30000")), color=(1.0, 0.97, 0.9))
rim_az = math.radians(cam_az + 180)
T.area("rim", (math.cos(rim_az) * 40, math.sin(rim_az) * 40, 18), (0, 0, 6), 10, float(E("RIM_E", "30000")), color=(0.75, 0.85, 1.0))
# key and rim light the ship only (no hot reflections on the sea); the moon gives the sea its sheen
shipc = bpy.data.collections.new("ship_lit"); sc.collection.children.link(shipc)
for o in list(mc["coll"].all_objects) + dv:
    shipc.objects.link(o)
for ln in ("key", "rim"):
    bpy.data.objects[ln].light_linking.receiver_collection = shipc
# low mist lying on the water in patches, and a light overall haze
sea.haze((0, 0, 4), (300, 300, 8), density=float(E("HAZE", "0.0025")), color=(0.6, 0.7, 0.8))
for k in range(int(E("NMIST", "7"))):
    a = rng.uniform(0, 6.28); r = rng.uniform(22, 55)
    sea.mist_puff(f"mist{k}", (math.cos(a) * r, math.sin(a) * r, 1.0), (rng.uniform(10, 18), rng.uniform(6, 10), 1.6),
                  density=float(E("MIST_D", "0.09")), seed=k)
# drifting motes in the light
N_MOTE = int(E("NMOTE", "70"))
P = np.stack([np.random.default_rng(2).uniform(-30, 30, N_MOTE), np.random.default_rng(3).uniform(-30, 30, N_MOTE),
              np.random.default_rng(4).uniform(3, 30, N_MOTE)], 1)
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

T.grade(sc, sat=float(E("SAT", "1.15")), con=float(E("CON", "1.12")), expo=float(E("EXPO", "0.5")), vig=float(E("VIG", "0.45")))
T.render(sc, "mc_dark_" + VIEW)
