"""Deterministic (no-sim) effects with geometry nodes: rain around the camera, slam spray along the ring, surge-front spray; plate patch.
blender -b anim.blend --python 04_fx.py -- <out.blend>"""
import bpy, sys, math, random
import bmesh
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; R_ = math.radians
def F(t): return 1 + round(t * 60)
C = bpy.data.collections.get("FX")

def rin(node, nm, typ): return next(x for x in node.inputs if x.name == nm and x.type == typ)
def rout(node, typ): return next(x for x in node.outputs if x.type == typ)

def drop_mesh(name, r, h, seg=6):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r * 0.3, depth=h); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me
def mat_water(name, col, alpha_rough):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Transmission Weight"].default_value = 0.6; b.inputs["Roughness"].default_value = alpha_rough
    b.inputs["IOR"].default_value = 1.33; b.inputs["Alpha"].default_value = 0.55
    return m

class G:
    """tiny helper to build GN trees"""
    def __init__(s, name):
        s.g = bpy.data.node_groups.new(name, "GeometryNodeTree")
        s.g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        s.g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        s.N, s.L = s.g.nodes, s.g.links
        s.gi = s.N.new("NodeGroupInput"); s.go = s.N.new("NodeGroupOutput")
        t = s.N.new("GeometryNodeInputSceneTime"); s.time = t.outputs["Seconds"]
    def m(s, op, x, y=None, z=None, clamp=False):
        n = s.N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((x, y, z)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: s.L.new(v, n.inputs[i])
        return n.outputs[0]
    def vm(s, op, x, y=None, scale=None):
        n = s.N.new("ShaderNodeVectorMath"); n.operation = op
        for i, v in enumerate((x, y)):
            if v is None: continue
            if isinstance(v, (tuple, Vector)): n.inputs[i].default_value = v
            else: s.L.new(v, n.inputs[i])
        if scale is not None:
            if isinstance(scale, (int, float)): n.inputs["Scale"].default_value = scale
            else: s.L.new(scale, n.inputs["Scale"])
        return n.outputs[0] if op not in ("DOT_PRODUCT", "LENGTH") else n.outputs["Value"]
    def rand(s, lo, hi, seed, typ="FLOAT"):
        n = s.N.new("FunctionNodeRandomValue"); n.data_type = typ
        t = {"FLOAT": "VALUE", "FLOAT_VECTOR": "VECTOR"}[typ]
        rin(n, "Min", t).default_value = lo; rin(n, "Max", t).default_value = hi; rin(n, "Seed", "INT").default_value = seed
        return rout(n, t)
    def xyz(s, x, y, z):
        n = s.N.new("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: s.L.new(v, n.inputs[i])
        return n.outputs[0]
    def sep(s, v):
        n = s.N.new("ShaderNodeSeparateXYZ"); s.L.new(v, n.inputs[0]); return n.outputs

# ------------------------------------------------------------------ rain: a box of streaks that follows the camera, falling, slanted by wind
cam = sc.camera
g = G("Rain"); N, L = g.N, g.L
pts = N.new("GeometryNodePoints"); pts.inputs["Count"].default_value = 14000
oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = cam
rp = g.rand((-16, -16, 0), (16, 16, 1), 3, "FLOAT_VECTOR"); rx, ry, rz = g.sep(rp)
H = 12.0
fall = g.m("FRACT", g.m("SUBTRACT", rz, g.m("MULTIPLY", g.time, 9.0 / H)))
z = g.m("SUBTRACT", g.m("MULTIPLY", fall, H), 4.0)
x = g.m("ADD", rx, g.m("MULTIPLY", fall, 1.6))
cx, cy, cz = g.sep(oi.outputs["Location"])
pos = g.xyz(g.m("ADD", x, cx), g.m("ADD", ry, cy), g.m("ADD", z, cz))
sp = N.new("GeometryNodeSetPosition"); L.new(pts.outputs[0], sp.inputs["Geometry"]); L.new(pos, sp.inputs["Position"])
# rain amount (keyed): delete a fraction of points
amt = N.new("ShaderNodeValue"); amt.name = "RainAmount"; amt.outputs[0].default_value = 1.0
dl = N.new("GeometryNodeDeleteGeometry"); L.new(sp.outputs[0], dl.inputs["Geometry"])
L.new(g.m("GREATER_THAN", g.rand(0, 1, 9), amt.outputs[0]), dl.inputs["Selection"])
ins = N.new("GeometryNodeInstanceOnPoints"); L.new(dl.outputs[0], ins.inputs["Points"])
streak = bpy.data.objects.new("RainStreakSrc", drop_mesh("RainStreak", 0.0035, 0.32)); streak.data.materials.append(mat_water("RainMat", (0.85, 0.9, 0.95), 0.05))
oi2 = N.new("GeometryNodeObjectInfo"); oi2.inputs["Object"].default_value = streak; L.new(oi2.outputs["Geometry"], ins.inputs["Instance"])
ins.inputs["Rotation"].default_value = (0, R_(10), 0)
rl = N.new("GeometryNodeRealizeInstances"); L.new(ins.outputs[0], rl.inputs[0])
L.new(rl.outputs[0], g.go.inputs[0])
rain = bpy.data.objects.new("Rain", bpy.data.meshes.new("RainBase")); C.objects.link(rain); C.objects.link(streak); streak.hide_render = True; streak.hide_viewport = True
rain.modifiers.new("Rain", "NODES").node_group = g.g
a = amt.outputs[0]
for f, v in ((1, 0.25), (F(3.5), 0.5), (F(8.3), 1.0), (F(14.4), 1.0), (F(14.7), 0.0), (F(20.9), 0.0), (F(21.2), 0.9), (F(24.0), 0.6), (F(25.3), 0.0)):
    a.default_value = v; a.keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ spray strips: points on a strip mesh with an outward direction attribute
def strip(name, pts2d, outward, z=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    lay = bm.verts.layers.float_vector.new("dir")
    for p, d in zip(pts2d, outward):
        v = bm.verts.new((p.x, p.y, z)); v[lay] = (d.x, d.y, 0)
    bm.to_mesh(me); bm.free(); return me
def spray(name, me, t0, t1, count_per, up, out, life, size, seed, mat):
    g = G(name); N, L = g.N, g.L
    dup = N.new("GeometryNodeDuplicateElements"); dup.domain = "POINT"; dup.inputs["Amount"].default_value = count_per
    L.new(g.gi.outputs[0], dup.inputs["Geometry"])
    idx = N.new("GeometryNodeInputIndex")
    # each droplet: own phase; age loops within life
    ph = g.rand(0, 1, seed)
    age01 = g.m("FRACT", g.m("ADD", g.m("DIVIDE", g.time, life), ph))
    age = g.m("MULTIPLY", age01, life)
    dirn = N.new("GeometryNodeInputNamedAttribute"); dirn.data_type = "FLOAT_VECTOR"; dirn.inputs["Name"].default_value = "dir"
    vo = g.rand(out * 0.3, out, seed + 1); vu = g.rand(up * 0.4, up, seed + 2)
    jit = g.rand((-0.6, -0.6, 0), (0.6, 0.6, 0), seed + 3, "FLOAT_VECTOR")
    hv = g.vm("SCALE", g.vm("ADD", dirn.outputs["Attribute"], jit), scale=vo)
    v = g.vm("ADD", hv, g.xyz(0, 0, vu))
    disp = g.vm("ADD", g.vm("SCALE", v, scale=age), g.xyz(0, 0, g.m("MULTIPLY", g.m("MULTIPLY", age, age), -4.9)))
    off = g.vm("ADD", disp, g.rand((-0.3, -0.3, 0), (0.3, 0.3, 0.05), seed + 4, "FLOAT_VECTOR"))
    sp_ = N.new("GeometryNodeSetPosition"); L.new(dup.outputs[0], sp_.inputs["Geometry"]); L.new(off, sp_.inputs["Offset"])
    # visible window (scene seconds) and above-ground
    win = g.m("MULTIPLY", g.m("GREATER_THAN", g.time, t0), g.m("LESS_THAN", g.time, t1))
    zz = g.sep(disp)[2]
    keep = g.m("MULTIPLY", win, g.m("GREATER_THAN", zz, -0.05))
    dl = N.new("GeometryNodeDeleteGeometry"); L.new(sp_.outputs[0], dl.inputs["Geometry"]); L.new(g.m("LESS_THAN", keep, 0.5), dl.inputs["Selection"])
    ins = N.new("GeometryNodeInstanceOnPoints"); L.new(dl.outputs[0], ins.inputs["Points"])
    src = bpy.data.objects.new(name + "Src", drop_mesh(name + "Drop", 1.0, 1.6, 8)); src.data.materials.append(mat); C.objects.link(src); src.hide_render = True; src.hide_viewport = True
    oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = src; L.new(oi.outputs["Geometry"], ins.inputs["Instance"])
    L.new(g.rand(size * 0.3, size, seed + 5), ins.inputs["Scale"])
    L.new(g.rand((0, 0, 0), (3, 3, 3), seed + 6, "FLOAT_VECTOR"), ins.inputs["Rotation"])
    L.new(ins.outputs[0], g.go.inputs[0])
    ob = bpy.data.objects.new(name, me); C.objects.link(ob); ob.modifiers.new(name, "NODES").node_group = g.g
    return ob
MS = mat_water("SprayMat", (0.72, 0.64, 0.52), 0.35); MS.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.9; MS.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.25
# slam spray along the outside of the ring front and corners
RC = Vector((0.0, 0.8)); HX, HY, CR = 10.5, 9.8, 3.2
P2, D2 = [], []
for i in range(160):
    x = -9.6 + 19.2 * i / 159; P2.append(Vector((x, -9.65))); D2.append(Vector((0.15 * (x / 10), -1)))
for sgn in (1, -1):
    for i in range(40):
        a = -math.pi / 2 + (math.pi / 2) * i / 39
        c = Vector((sgn * (HX - CR), RC.y - HY + CR)); d = Vector((sgn * math.cos(a), math.sin(a)))
        P2.append(c + d * (CR + 0.6)); D2.append(d)
    for i in range(50):
        y = RC.y - HY + CR + (2 * HY - 2 * CR) * i / 49; P2.append(Vector((sgn * (HX + 0.6), y))); D2.append(Vector((sgn, 0)))
slam = spray("SlamSpray", strip("SlamStrip", P2, D2, 0.45), 21.3, 24.2, 45, 5.0, 2.0, 0.9, 0.028, 33, MS)
# surge-front spray along the street, x driven by the flood FrontX value
SP, SD = [Vector((0, -20 + 9 * i / 59)) for i in range(60)], [Vector((-1, 0)) for i in range(60)]
surge = spray("SurgeSpray", strip("SurgeStrip", SP, SD, 0.5), 8.3, 15.0, 45, 3.5, 2.6, 0.8, 0.028, 44, MS)
dr = surge.driver_add("location", 0).driver; dr.type = "SCRIPTED"
var = dr.variables.new(); var.name = "fx"; var.targets[0].id_type = "NODETREE"; var.targets[0].id = bpy.data.node_groups["FloodSurface"]
var.targets[0].data_path = 'nodes["FrontX"].outputs[0].default_value'; dr.expression = "fx + 1.0"
# ring spill spray (beat 7 water curling around corners): use the slam object timing (already covers corners)

# ------------------------------------------------------------------ licence plate: plain stamped metal, no characters
for m in bpy.data.materials:
    if m.name.startswith("M_License") and m.node_tree:
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        for l in list(b.inputs["Base Color"].links): m.node_tree.links.remove(l)
        b.inputs["Base Color"].default_value = (0.55, 0.56, 0.55, 1); b.inputs["Metallic"].default_value = 0.8
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
