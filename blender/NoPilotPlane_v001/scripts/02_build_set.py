"""Cabin, cockpit, exterior, lights.  blender -b --factory-startup --python 02_build_set.py -- <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
random.seed(12)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = C.scene
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.fps = 60; sc.frame_start, sc.frame_end = 1, 4410
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"

ROW0, PITCH, NROW = -2.4, 0.81, 14
SH_R, SH_Z = 1.45, 0.95
cSet = coll("SET"); cExt = coll("EXTERIOR")

# ------------------------------------------------------------------ materials
M_fab = mat("M_seat_fabric", (0.02, 0.028, 0.06), rough=0.85, noise=0.6, nscale=180, bump=0.25)
M_fab2 = mat("M_seat_headcover", (0.6, 0.6, 0.58), rough=0.8, noise=0.3, nscale=200, bump=0.1)
M_plast = mat("M_cabin_plastic", (0.72, 0.71, 0.67), rough=0.45, noise=0.15, nscale=6)
M_plast_d = mat("M_plastic_grey", (0.22, 0.23, 0.24), rough=0.5, noise=0.2, nscale=30)
M_carpet = mat("M_carpet", (0.07, 0.075, 0.1), rough=0.95, noise=0.7, nscale=300, bump=0.4)
M_carpet2 = mat("M_carpet_aisle", (0.16, 0.06, 0.06), rough=0.95, noise=0.6, nscale=300, bump=0.4)
M_steel = mat("M_steel", (0.55, 0.56, 0.58), rough=0.38, metal=1.0, noise=0.5, nscale=35, bump=0.2)
M_dark = mat("M_cockpit_dark", (0.035, 0.037, 0.04), rough=0.6, noise=0.45, nscale=90, bump=0.35)
M_panel = mat("M_panel", (0.075, 0.08, 0.088), rough=0.55, noise=0.4, nscale=140, bump=0.3)
M_black = mat("M_black_gloss", (0.01, 0.01, 0.012), rough=0.15)
M_white_e = emit_mat("M_light_strip", (1.0, 0.93, 0.82), 6.0)
M_needle = emit_mat("M_needle", (1.0, 1.0, 0.95), 4.0)
M_wing = mat("M_wing", (0.62, 0.64, 0.66), rough=0.35, metal=0.3, noise=0.15, nscale=2)
M_screen = mat("M_seat_screen", (0.01, 0.012, 0.02), rough=0.1, emit=(0.08, 0.12, 0.2), estr=0.6)

def win_shell_mat(name, base, cabin=True):
    m, nt = nodes_mat(name); N, L = nt.nodes, nt.links
    p = N["Principled BSDF"]; p.inputs["Base Color"].default_value = (*base, 1); p.inputs["Roughness"].default_value = 0.5
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    def M(op, a, b=None, v=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b)):
            if x is None: continue
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: L.new(x, n.inputs[i])
        return n.outputs[0]
    X, Y, Z = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    if cabin:
        # periodic windows along y, rounded rect (superellipse) in (y,z), only on side walls
        u = M("SUBTRACT", M("FRACT", M("ADD", M("DIVIDE", M("SUBTRACT", Y, ROW0 - 0.2), PITCH), 0.5)), 0.5)
        dy = M("DIVIDE", M("ABSOLUTE", M("MULTIPLY", u, PITCH)), 0.12)
        dz = M("DIVIDE", M("ABSOLUTE", M("SUBTRACT", Z, 1.2)), 0.18)
        e = M("ADD", M("POWER", dy, 4.0), M("POWER", dz, 4.0))
        side = M("GREATER_THAN", M("ABSOLUTE", X), 1.0)
        inrange = M("MULTIPLY", M("GREATER_THAN", Y, -13.2), M("LESS_THAN", Y, -1.8))
        gate = M("MULTIPLY", side, inrange)
        hole = M("MULTIPLY", M("LESS_THAN", e, 1.0), gate)
        bez = M("MULTIPLY", M("LESS_THAN", e, 2.4), gate)
    else:
        # windscreen: z>1.1, y 1.85..2.9 ; center post ; side windows
        ws = M("MULTIPLY", M("GREATER_THAN", Z, 1.05), M("MULTIPLY", M("GREATER_THAN", Y, 1.95), M("LESS_THAN", Z, 1.78)))
        ws = M("MULTIPLY", ws, M("GREATER_THAN", M("ABSOLUTE", X), 0.035))
        ws = M("MULTIPLY", ws, M("GREATER_THAN", M("ABSOLUTE", M("SUBTRACT", M("ABSOLUTE", X), 0.62)), 0.03))
        sw = M("MULTIPLY", M("MULTIPLY", M("GREATER_THAN", Z, 1.12), M("LESS_THAN", Z, 1.62)),
               M("MULTIPLY", M("GREATER_THAN", Y, 0.95), M("LESS_THAN", Y, 1.88)))
        sw = M("MULTIPLY", sw, M("GREATER_THAN", M("ABSOLUTE", M("SUBTRACT", Y, 1.42)), 0.025))
        hole = M("MINIMUM", M("ADD", ws, sw), 1.0)
        bez = hole
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader"); L.new(hole, mix.inputs[0])
    L.new(p.outputs[0], mix.inputs[1]); L.new(tr.outputs[0], mix.inputs[2])
    # bezel darker
    mc = N.new("ShaderNodeMix"); mc.data_type = 'RGBA'; L.new(bez, mc.inputs["Factor"])
    mc.inputs["A"].default_value = (*base, 1); mc.inputs["B"].default_value = (0.42, 0.42, 0.43, 1)
    L.new(mc.outputs["Result"], p.inputs["Base Color"])
    L.new(mix.outputs[0], N["Material Output"].inputs["Surface"])
    return m
M_shell = win_shell_mat("M_cabin_shell", (0.78, 0.77, 0.73), True)
M_cshell = win_shell_mat("M_cockpit_shell", (0.32, 0.33, 0.35), False)

# ------------------------------------------------------------------ shells
import bmesh
def loft(name, rings, m, seg=56, cap=True):
    bm = bmesh.new(); prev = None; first = None
    for (y, r, cz, sx) in rings:
        ring = [bm.verts.new((sx * r * math.cos(2 * math.pi * k / seg), y, cz + r * math.sin(2 * math.pi * k / seg))) for k in range(seg)]
        if prev:
            for k in range(seg):
                bm.faces.new((prev[k], prev[(k + 1) % seg], ring[(k + 1) % seg], ring[k]))
        else: first = ring
        prev = ring
    if cap: bm.faces.new(prev[::-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); cSet.objects.link(ob); return ob
loft("CABIN_SHELL", [(-13.6, SH_R, SH_Z, 1.0), (-0.02, SH_R, SH_Z, 1.0)], M_shell, seg=64, cap=False)
loft("COCKPIT_SHELL", [(-0.02, SH_R, SH_Z, 1.0), (1.0, 1.40, 0.95, 1.0), (1.9, 1.22, 0.92, 0.95), (2.45, 0.98, 0.85, 0.92),
                       (2.95, 0.62, 0.78, 0.9), (3.3, 0.25, 0.72, 0.9)], M_cshell, seg=64)
bk = MB("CABIN_BACKWALL"); bk.box((0, -13.55, 1.0), (3.0, 0.05, 2.2), M_plast); bk.obj(cSet)

# ------------------------------------------------------------------ cabin interior
mb = MB("CABIN_FIXED")
mb.box((0, -6.0, -0.01), (2.9, 15.5, 0.02), M_carpet)
mb.box((0, -6.6, 0.002), (0.56, 14.0, 0.004), M_carpet2)
for s in (-1, 1):
    # overhead bins (lower face angled) and ceiling light strip
    mb.box((s * 0.99, -7.4, 1.80), (0.56, 12.2, 0.42), M_plast, bevel=0.03)
    mb.box((s * 0.71, -7.4, 1.585), (0.04, 12.2, 0.02), M_white_e)
    mb.box((s * 0.66, -7.4, 1.60), (0.02, 12.2, 0.05), M_plast_d)
    for i in range(NROW):  # bin seams + passenger service units
        y = ROW0 - PITCH * i
        mb.box((s * 0.99, y - 0.4, 1.80), (0.57, 0.01, 0.43), M_plast_d)
        mb.box((s * 0.88, y - 0.05, 1.57), (0.3, 0.22, 0.03), M_plast_d)
        for k in range(2):
            mb.cyl((s * (0.8 + 0.1 * k), y - 0.05, 1.553), 0.018, 0.01, M_white_e if (i + k) % 3 == 0 else M_steel)
    # sidewall dado panel
    mb.box((s * 1.25, -7.4, 0.25), (0.06, 12.2, 0.5), M_plast_d)
mb.box((0, -7.4, 2.08), (1.34, 12.2, 0.03), M_plast)
mb.box((0, -7.4, 2.06), (0.25, 12.2, 0.01), M_white_e)
# galley + bulkhead + door frame
for s in (-1, 1):
    mb.box((s * 0.9, -1.25, 1.0), (0.95, 1.1, 2.0), M_steel, bevel=0.01)
    mb.box((s * 0.9, -1.81, 1.0), (0.95, 0.02, 2.0), M_plast)
    for k in range(4):
        mb.box((s * 0.9, -1.83, 0.25 + k * 0.45), (0.85, 0.01, 0.01), M_plast_d)
    mb.box((s * 0.92, -0.52, 1.0), (1.1, 0.04, 2.1), M_plast)        # bulkhead each side of door
mb.box((0, -0.52, 2.02), (0.76, 0.04, 0.16), M_plast)                 # lintel
mb.box((-0.385, -0.52, 0.97), (0.03, 0.08, 1.94), M_plast_d); mb.box((0.385, -0.52, 0.97), (0.03, 0.08, 1.94), M_plast_d)
mb.obj(cSet)

# seats: one mesh, linked duplicates
def seat_mesh(name, tray_down=False):
    s = MB(name)
    s.box((0, 0, 0.42), (0.44, 0.47, 0.11), M_fab, bevel=0.03)                 # cushion
    s.box((0, -0.25, 0.86), (0.44, 0.09, 0.78), M_fab, rot=(-10, 0, 0), bevel=0.03)   # back
    s.box((0, -0.18, 1.17), (0.40, 0.02, 0.2), M_fab2, rot=(-10, 0, 0))         # headrest cover
    s.box((0, -0.31, 0.95), (0.40, 0.01, 0.3), M_plast_d, rot=(-10, 0, 0))       # back shell
    s.box((0, -0.323, 1.05), (0.2, 0.004, 0.13), M_screen, rot=(-10, 0, 0))     # blank screen
    for x in (-0.235, 0.235):
        s.box((x, -0.02, 0.62), (0.04, 0.42, 0.04), M_plast_d, bevel=0.01)     # armrest
        s.box((x, -0.14, 0.5), (0.03, 0.04, 0.2), M_plast_d)
    s.box((0, 0.0, 0.22), (0.38, 0.4, 0.3), M_plast_d)                          # base/legs block
    s.box((0, 0.0, 0.06), (0.04, 0.45, 0.04), M_steel)
    if tray_down:
        s.box((0, -0.52, 0.72), (0.38, 0.26, 0.018), M_plast)
    else:
        s.box((0, -0.318, 0.86), (0.36, 0.012, 0.24), M_plast, rot=(-10, 0, 0))
    return s.obj(cSet, smooth=False).data
SEAT_UP = seat_mesh("SEAT_tmp"); SEAT_TRAY = seat_mesh("SEATT_tmp", True)
for o in ("SEAT_tmp", "SEATT_tmp"): bpy.data.objects.remove(bpy.data.objects[o])
SEATS = {}
cSeats = coll("SEATS", cSet)
for i in range(NROW):
    y = ROW0 - PITCH * i
    for side, xs in (("L", (-0.55, -1.03)), ("R", (0.55, 1.03))):
        for k, x in enumerate(xs):
            nm = "SEAT_%02d%s%d" % (i + 1, side, k)
            # tray down on the seat *behind* row 3 window (i.e. the back of row 3L1 faces row 4 window passenger)
            me = SEAT_TRAY if (i + 1, side, k) in ((3, "L", 1), (3, "R", 0), (6, "R", 1), (9, "L", 0)) else SEAT_UP
            ob = bpy.data.objects.new(nm, me); ob.location = (x, y, 0); cSeats.objects.link(ob); SEATS[nm] = ob

# real seat model (maximmus, CC-BY) replaces the procedural seat on every row; procedural trays stay where a tray is down
SEAT_GLB = os.path.join(HERE, "..", "work", "models", "seat.glb")
if os.path.exists(SEAT_GLB):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SEAT_GLB)
    new = [o for o in bpy.data.objects if o not in before]
    new_names = [o.name for o in new]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    C.view_layer.objects.active = meshes[0]; bpy.ops.object.join()
    sm = C.active_object; sm.name = "SEAT_MODEL"
    for n_ in new_names:
        if n_ in bpy.data.objects and n_ != sm.name: bpy.data.objects.remove(bpy.data.objects[n_])
    # mm -> m, narrow to the 0.48 m seat pitch across, slightly shallower, face +Y, floor at z=0, cushion centre at origin
    sm.matrix_world = Matrix.Diagonal((0.00085, 0.0009, 0.001, 1.0)) @ sm.matrix_world
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    me = sm.data
    for v in me.vertices: v.co = Vector((-v.co.x, -v.co.y, v.co.z - 0.235))
    for v in me.vertices: v.co.y += 0.27
    me.update()
    for p_ in me.polygons: p_.use_smooth = True
    link(sm, cSet); sm.hide_render = True; sm.hide_viewport = True
    trayM = MB("TRAY_tmp"); trayM.box((0, -0.56, 0.70), (0.38, 0.27, 0.018), M_plast); trayM.box((0, -0.43, 0.70), (0.3, 0.02, 0.01), M_steel)
    tray_me = trayM.obj(cSet).data; bpy.data.objects.remove(bpy.data.objects["TRAY_tmp"])
    for nm, ob in list(SEATS.items()):
        tray = ob.data == SEAT_TRAY
        ob.data = sm.data
        if tray:
            t = bpy.data.objects.new(nm.replace("SEAT", "TRAY"), tray_me); t.location = ob.location; cSeats.objects.link(t)
    # measure for the passenger fit
    dg = C.evaluated_depsgraph_get(); o0 = SEATS["SEAT_05L1"]
    h = o0.ray_cast(Vector((0, 0.0, 2.0)), Vector((0, 0, -1)))
    b = o0.ray_cast(Vector((0, 0.3, 0.85)), Vector((0, -1, 0)))
    print("SEATFIT cushion_top", round(h[1].z, 3) if h[0] else None, "back_front_y@0.85", round(b[1].y, 3) if b[0] else None)

# ------------------------------------------------------------------ door
M_door = mat("M_door", (0.40, 0.40, 0.38), rough=0.5, noise=0.35, nscale=25, bump=0.4)
M_doorp = mat("M_door_panel", (0.55, 0.55, 0.52), rough=0.45, noise=0.3, nscale=18, bump=0.3)
d = MB("DOOR"); d.box((0.36, 0.0, 0.965), (0.72, 0.045, 1.93), M_door, bevel=0.008)
for zc, hh in ((1.42, 0.62), (0.82, 0.42)):
    d.box((0.36, -0.024, zc), (0.56, 0.004, hh), M_doorp, bevel=0.004)
d.box((0.36, -0.027, 1.82), (0.2, 0.003, 0.05), M_steel)
d.cyl((0.62, -0.05, 1.0), 0.012, 0.12, M_steel, rot=(0, 90, 0)); d.cyl((0.62, -0.035, 1.0), 0.012, 0.03, M_steel, rot=(90, 0, 0))
d.cyl((0.36, -0.024, 1.55), 0.012, 0.006, M_steel, rot=(90, 0, 0))
d.box((0.36, -0.024, 0.35), (0.6, 0.004, 0.25), M_steel)                     # kick plate                      # peephole plate (no text)
door = d.obj(cSet); door.location = (-0.36, -0.5, 0.0)

# ------------------------------------------------------------------ cockpit
ck = MB("COCKPIT_FIXED")
ck.box((0, 1.15, -0.01), (2.6, 3.4, 0.02), M_dark)
# pilot seats
for x in (-0.52, 0.52):
    ck.box((x, 1.45, 0.46), (0.5, 0.5, 0.13), M_dark, bevel=0.03)
    ck.box((x, 1.16, 0.95), (0.5, 0.12, 0.85), M_dark, rot=(-12, 0, 0), bevel=0.03)
    ck.box((x, 1.09, 1.47), (0.3, 0.1, 0.2), M_dark, rot=(-12, 0, 0), bevel=0.03)
    ck.cyl((x, 1.45, 0.2), 0.06, 0.4, M_steel)
    for ax in (-0.27, 0.27):
        ck.box((x + ax, 1.38, 0.72), (0.05, 0.35, 0.05), M_dark, bevel=0.01)
    ck.box((x, 1.97, 0.10), (0.42, 0.22, 0.20), M_panel, bevel=0.01)          # footrest under the panel
    ck.box((x, 1.97, 0.202), (0.40, 0.20, 0.006), mat("M_grip", (0.02, 0.02, 0.02), rough=0.8, bump=0.6, nscale=400))
    # rudder pedals
    for px in (-0.1, 0.1):
        ck.box((x + px, 2.3, 0.12), (0.08, 0.03, 0.18), M_steel, rot=(-30, 0, 0))
# pedestal + throttle quadrant
ck.box((0, 1.72, 0.37), (0.36, 0.95, 0.74), M_panel, bevel=0.01)
ck.box((0, 1.72, 0.755), (0.34, 0.93, 0.03), M_dark)
ck.box((0, 1.35, 0.775), (0.3, 0.16, 0.02), M_black)                             # radio panel face
# main instrument panel and glareshield
ck.box((0, 2.32, 0.80), (1.9, 0.12, 0.5), M_panel, rot=(-14, 0, 0))
ck.box((0, 2.33, 1.03), (1.9, 0.38, 0.05), M_dark, bevel=0.01)
ck.box((0, 2.15, 1.005), (1.5, 0.05, 0.06), M_panel)
# overhead panel
ck.box((0, 1.25, 2.08), (0.9, 1.1, 0.08), M_panel, rot=(8, 0, 0))
# side consoles
for s in (-1, 1):
    ck.box((s * 0.98, 1.5, 0.62), (0.18, 1.0, 0.08), M_panel)
ck.obj(cSet)

# overhead buttons / panel lamps (blank symbols only)
bt = MB("COCKPIT_BUTTONS"); M_btn = [mat("M_btn_%d" % i, c, rough=0.4, emit=c, estr=e) for i, (c, e) in
     enumerate((((0.6, 0.6, 0.6), 0.05), ((0.9, 0.55, 0.1), 0.8), ((0.2, 0.9, 0.3), 0.8), ((0.1, 0.4, 1.0), 0.6)))]
for i in range(10):
    for j in range(14):
        x = -0.36 + j * 0.055; y = 0.78 + i * 0.1
        z = 2.03 - (y - 1.25) * math.tan(R_(8))
        bt.box((x, y, z), (0.03, 0.03, 0.02), random.choice(M_btn[:1] * 6 + M_btn[1:]))
bt.obj(cSet)

# gauges: face with ticks (procedural), each has a needle object
def gauge_face_mat():
    m, nt = nodes_mat("M_gauge_face"); N, L = nt.nodes, nt.links
    if nt is None: return m
    p = N["Principled BSDF"]; p.inputs["Base Color"].default_value = (0.01, 0.01, 0.012, 1); p.inputs["Roughness"].default_value = 0.3
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    def Mth(op, a, b):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b)):
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: L.new(x, n.inputs[i])
        return n.outputs[0]
    ux = Mth("SUBTRACT", sep.outputs[0], 0.5); uy = Mth("SUBTRACT", sep.outputs[1], 0.5)
    r = Mth("SQRT", Mth("ADD", Mth("MULTIPLY", ux, ux), Mth("MULTIPLY", uy, uy)), 0)
    a = Mth("ARCTAN2", uy, ux)
    tick = Mth("LESS_THAN", Mth("FRACT", Mth("MULTIPLY", a, 24 / (2 * math.pi)), 0), 0.12)
    ring = Mth("MULTIPLY", Mth("GREATER_THAN", r, 0.36), Mth("LESS_THAN", r, 0.46))
    arc = Mth("MULTIPLY", Mth("MULTIPLY", Mth("GREATER_THAN", r, 0.30), Mth("LESS_THAN", r, 0.34)), Mth("GREATER_THAN", a, 1.2))
    w = Mth("MULTIPLY", tick, ring)
    e = N.new("ShaderNodeEmission"); e.inputs["Strength"].default_value = 3.0
    mc = N.new("ShaderNodeMix"); mc.data_type = 'RGBA'; L.new(arc, mc.inputs["Factor"])
    mc.inputs["A"].default_value = (1, 1, 1, 1); mc.inputs["B"].default_value = (0.1, 0.9, 0.3, 1)
    L.new(mc.outputs["Result"], e.inputs["Color"])
    mx = N.new("ShaderNodeMixShader"); L.new(Mth("MAXIMUM", w, arc), mx.inputs[0])
    L.new(p.outputs[0], mx.inputs[1]); L.new(e.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N["Material Output"].inputs["Surface"])
    return m
M_gface = gauge_face_mat()
cG = coll("GAUGES", cSet)
GAUGES = []
tilt = Matrix.Rotation(R_(-14), 3, 'X')
for side, cx in (("L", -0.52), ("R", 0.52)):
    for gi, (ox, oz, rr) in enumerate(((-0.30, 0.12, 0.036), (0.30, 0.12, 0.036), (-0.30, 0.0, 0.036), (0.29, -0.01, 0.042),
                                        (-0.39, 0.06, 0.03), (0.38, 0.09, 0.028))):
        c = Vector((0, 2.258, 0.82)) + tilt @ Vector((cx + ox, 0, oz)) - Vector((0, 0, 0)) ; c.x = cx + ox
        g = MB("GAUGE_%s%d" % (side, gi)); g.cyl((0, 0, 0), rr, 0.012, M_gface, rot=(90, 0, 0), seg=32)
        g.cyl((0, -0.004, 0), rr * 1.08, 0.008, M_steel, rot=(90, 0, 0), seg=32)
        go = g.obj(cG); go.location = c; go.rotation_euler = (R_(-14), 0, 0)
        # needle pivot = empty-less: mesh with origin at gauge centre, rotates about local Y
        n = MB("NEEDLE_%s%d" % (side, gi)); n.box((0, 0, rr * 0.4), (0.004, 0.003, rr * 0.8), M_needle)
        no = n.obj(cG); no.parent = go; no.location = (0, -0.009, 0)
        GAUGES.append(no.name)
# yokes (origin at column base, rotate about local X)
for side, x in (("L", -0.52), ("R", 0.52)):
    y = MB("YOKE_%s" % side)
    y.cyl((0, 0, 0.38), 0.025, 0.76, M_dark, rot=(14, 0, 0))
    top = Vector((0, -0.18, 0.74))
    y.box(top, (0.12, 0.05, 0.06), M_dark, bevel=0.01)
    y.box(top + Vector((0, -0.02, 0)), (0.30, 0.04, 0.035), M_dark, bevel=0.012)
    for s in (-1, 1):
        y.box(top + Vector((s * 0.16, -0.02, 0.06)), (0.035, 0.04, 0.16), M_dark, rot=(0, s * 12, 0), bevel=0.012)
        y.box(top + Vector((s * 0.16, -0.022, 0.06)), (0.04, 0.03, 0.10), mat("M_grip", (0.02, 0.02, 0.02), rough=0.8, bump=0.6, nscale=400), rot=(0, s * 12, 0))
    y.box(top + Vector((0, -0.045, 0.0)), (0.05, 0.004, 0.03), M_steel)
    yo = y.obj(cSet); yo.location = (x, 2.12, 0.0)

# throttle levers (origin at pivot inside pedestal)
for k, x in enumerate((-0.05, 0.05)):
    t = MB("THROTTLE_%d" % k); t.box((0, 0, 0.09), (0.018, 0.02, 0.18), M_steel)
    t.cyl((0, 0, 0.19), 0.03, 0.05, M_black, rot=(0, 90, 0))
    to = t.obj(cSet); to.location = (x, 1.82, 0.74); to.rotation_euler = (R_(-15), 0, 0)
# radio panel LEDs (keyed later) and handset
cR = coll("RADIO", cSet)
for i in range(6):
    l = MB("LED_%d" % i); l.cyl((0, 0, 0), 0.007, 0.006, emit_mat("M_led_%d" % i, ((0.2, 1, 0.3), (1, 0.6, 0.1))[i % 2], 0.0))
    lo = l.obj(cR); lo.location = (-0.11 + i * 0.044, 1.35, 0.787)
h = MB("HANDSET")
h.box((0, 0, 0), (0.035, 0.17, 0.03), M_black, bevel=0.01)
h.box((0, 0.085, -0.012), (0.045, 0.05, 0.045), M_black, bevel=0.012)
h.box((0, -0.085, -0.012), (0.045, 0.05, 0.045), M_black, bevel=0.012)
h.box((0.018, 0.0, 0.0), (0.004, 0.02, 0.012), mat("M_ptt", (0.5, 0.05, 0.03), rough=0.4))
hs = h.obj(cR); hs.location = (0.12, 1.33, 0.81)
hk = MB("HANDSET_CRADLE"); hk.box((0.12, 1.33, 0.785), (0.06, 0.22, 0.02), M_dark); hk.obj(cR)

# red master warning lamps + red alarm light (strength keyed later)
M_warn = emit_mat("M_warn", (1.0, 0.05, 0.02), 0.0)
for x in (-0.6, 0.6):
    w = MB("WARN_%s" % ("L" if x < 0 else "R")); w.box((0, 0, 0), (0.07, 0.02, 0.04), M_warn, bevel=0.005)
    wo = w.obj(cSet); wo.location = (x, 2.17, 1.05)
ld = bpy.data.lights.new("L_alarm", 'POINT'); ld.color = (1, 0.06, 0.03); ld.energy = 0; ld.shadow_soft_size = 0.3
lo = bpy.data.objects.new("L_alarm", ld); lo.location = (0, 1.7, 1.7); cSet.objects.link(lo)
ld = bpy.data.lights.new("L_alarm_cabin", 'POINT'); ld.color = (1, 0.06, 0.03); ld.energy = 0; ld.shadow_soft_size = 0.3
lo = bpy.data.objects.new("L_alarm_cabin", ld); lo.location = (0, -0.6, 1.9); cSet.objects.link(lo)


# ------------------------------------------------------------------ cockpit density pass (director notes: real airliner clutter)
TEX = os.path.join(HERE, "..", "work", "tex")
def img_mat(name, fn, strength=1.6, emit=True, scroll=False):
    m, nt = nodes_mat(name); N, L = nt.nodes, nt.links
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(TEX, fn)); t.interpolation = 'Linear'
    if scroll:
        tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.name = "SCROLL"
        L.new(tc.outputs["UV"], mp.inputs["Vector"]); L.new(mp.outputs[0], t.inputs["Vector"]); t.extension = 'REPEAT'
    p = N["Principled BSDF"]
    if emit:
        p.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1); p.inputs["Roughness"].default_value = 0.08
        L.new(t.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = strength
    else:
        L.new(t.outputs["Color"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.7
    return m
def quad(name, c, w, h, m, rot=(0, 0, 0), coll_=None):
    me = bpy.data.meshes.new(name); me.from_pydata([(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(); uv = me.uv_layers[0].data
    for i, (u, v) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))): uv[i].uv = (u, v)
    me.materials.append(m); o = bpy.data.objects.new(name, me); (coll_ or cSet).objects.link(o)
    o.location = c; o.rotation_euler = [R_(a) for a in rot]; return o
M_pfd, M_nd, M_eic = img_mat("M_disp_pfd", "disp_pfd.png"), img_mat("M_disp_nd", "disp_nd.png"), img_mat("M_disp_eicas", "disp_eicas.png")
M_tapeA = img_mat("M_tape_alt", "disp_tape.png", 1.4, scroll=True); M_tapeS = img_mat("M_tape_spd", "disp_tape.png", 1.4, scroll=True)
# attitude square: blue over brown split, rotated/offset by keyed mapping (roll / pitch) in 03
m, nt = nodes_mat("M_attitude"); N, L = nt.nodes, nt.links; N.remove(N["Principled BSDF"])
tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.name = "ATT"; mp.vector_type = 'POINT'
mp.inputs["Location"].default_value = (-0.5, -0.5, 0)
L.new(tc.outputs["UV"], mp.inputs["Vector"]); sep = N.new("ShaderNodeSeparateXYZ"); L.new(mp.outputs[0], sep.inputs[0])
gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; L.new(sep.outputs[1], gt.inputs[0]); gt.inputs[1].default_value = 0.0
lad = N.new("ShaderNodeMath"); lad.operation = 'PINGPONG'; L.new(sep.outputs[1], lad.inputs[0]); lad.inputs[1].default_value = 0.06
ln = N.new("ShaderNodeMath"); ln.operation = 'LESS_THAN'; L.new(lad.outputs[0], ln.inputs[0]); ln.inputs[1].default_value = 0.004
cx_ = N.new("ShaderNodeMath"); cx_.operation = 'ABSOLUTE'; L.new(sep.outputs[0], cx_.inputs[0])
cw = N.new("ShaderNodeMath"); cw.operation = 'LESS_THAN'; L.new(cx_.outputs[0], cw.inputs[0]); cw.inputs[1].default_value = 0.12
lw = N.new("ShaderNodeMath"); lw.operation = 'MULTIPLY'; L.new(ln.outputs[0], lw.inputs[0]); L.new(cw.outputs[0], lw.inputs[1])
mc = N.new("ShaderNodeMix"); mc.data_type = 'RGBA'; L.new(gt.outputs[0], mc.inputs["Factor"])
mc.inputs["A"].default_value = (0.32, 0.17, 0.05, 1); mc.inputs["B"].default_value = (0.08, 0.35, 0.85, 1)
mw = N.new("ShaderNodeMix"); mw.data_type = 'RGBA'; L.new(lw.outputs[0], mw.inputs["Factor"]); L.new(mc.outputs["Result"], mw.inputs["A"]); mw.inputs["B"].default_value = (1, 1, 1, 1)
em = N.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.4; L.new(mw.outputs["Result"], em.inputs["Color"])
L.new(em.outputs[0], N["Material Output"].inputs["Surface"]); M_att = m
cD = coll("DISPLAYS", cSet)
tilt = Matrix.Rotation(R_(-14), 3, 'X')
def on_panel(x, z_off, depth=0.0):
    base = Vector((0, 2.262, 0.80)) + tilt @ Vector((0, -depth, z_off)); return Vector((x, base.y, base.z))
WD = 0.17
for side, cx, order in (("L", -0.52, ("pfd", "nd")), ("R", 0.52, ("nd", "pfd"))):
    for k, kind in enumerate(order):
        x = cx + (-0.095 if k == 0 else 0.095)
        q = quad("DISP_%s_%s" % (kind.upper(), side), on_panel(x, 0.03, 0.004), WD, WD, M_pfd if kind == "pfd" else M_nd, (-14, 0, 0), cD)
        ck2 = MB("BEZEL_%s_%s" % (kind, side)); ck2.box((0, 0, 0), (WD + 0.02, 0.012, WD + 0.02), M_black, bevel=0.004)
        bo = ck2.obj(cD); bo.location = on_panel(x, 0.03, -0.003); bo.rotation_euler = (R_(-14), 0, 0)
        for bi in range(5):   # bezel keys
            kb = MB("BK"); kb.box((0, 0, 0), (0.016, 0.008, 0.01), M_btn[(bi + k) % 4] if 'M_btn' in dir() else M_steel); kbo = kb.obj(cD)
            kbo.location = on_panel(x - 0.07 + bi * 0.035, 0.03 - WD / 2 - 0.018, 0.002); kbo.rotation_euler = (R_(-14), 0, 0)
        if kind == "pfd":
            quad("ATT_%s" % side, on_panel(x, 0.03 + WD * 0.09, 0.006), WD * 0.40, WD * 0.46, M_att, (-14, 0, 0), cD)
            quad("TAPE_ALT_%s" % side, on_panel(x + WD * 0.37, 0.03 + WD * 0.04, 0.006), WD * 0.13, WD * 0.58, M_tapeA, (-14, 0, 0), cD)
            quad("TAPE_SPD_%s" % side, on_panel(x - WD * 0.37, 0.03 + WD * 0.04, 0.006), WD * 0.13, WD * 0.58, M_tapeS, (-14, 0, 0), cD)
quad("DISP_EICAS_UP", on_panel(0.0, 0.03, 0.004), WD, WD, M_eic, (-14, 0, 0), cD)
ck2 = MB("BEZEL_EICAS"); ck2.box((0, 0, 0), (WD + 0.02, 0.012, WD + 0.02), M_black, bevel=0.004); bo = ck2.obj(cD); bo.location = on_panel(0, 0.03, -0.003); bo.rotation_euler = (R_(-14), 0, 0)
quad("DISP_EICAS_LOW", (0, 2.205, 0.66), WD, WD * 0.8, M_nd, (-40, 0, 0), cD)
pd = MB("PEDESTAL_FWD"); pd.box((0, 2.18, 0.62), (0.34, 0.16, 0.25), M_panel, rot=(-40, 0, 0), bevel=0.01); pd.obj(cSet)

# glareshield autopilot panel: knobs, segment windows, backlit keys
gp = MB("GLARESHIELD_AP")
gp.box((0, 2.14, 0.975), (0.86, 0.03, 0.07), M_panel, bevel=0.004)
M_seg = emit_mat("M_seg_green", (0.2, 1.0, 0.35), 3.0)
for i, x in enumerate((-0.33, -0.2, -0.06, 0.08, 0.21, 0.33)):
    gp.cyl((x, 2.118, 0.975), 0.014, 0.022, M_black, rot=(90, 0, 0), seg=14)
    gp.cyl((x, 2.106, 0.975), 0.009, 0.006, M_steel, rot=(90, 0, 0), seg=12)
    gp.box((x + 0.05, 2.124, 0.985), (0.05, 0.004, 0.016), M_black)
    for k in range(3): gp.box((x + 0.033 + k * 0.016, 2.121, 0.985), (0.01, 0.002, 0.009), M_seg)
    gp.box((x + 0.05, 2.124, 0.958), (0.03, 0.006, 0.012), M_btn[1 + i % 3])
for s_ in (-1, 1):   # efis control panels at each side
    gp.box((s_ * 0.72, 2.14, 0.975), (0.24, 0.03, 0.07), M_panel, bevel=0.004)
    for k in range(4): gp.cyl((s_ * 0.72 - 0.08 + k * 0.055, 2.118, 0.975), 0.011, 0.02, M_black, rot=(90, 0, 0), seg=12)
gp.obj(cSet)

# overhead: guarded toggles, rotary knobs, annunciator strips
ov = MB("OVERHEAD_SWITCHES"); M_guard = mat("M_guard", (0.55, 0.06, 0.04), rough=0.4); M_amber = emit_mat("M_annun_amber", (1.0, 0.6, 0.1), 1.2)
M_annun_g = emit_mat("M_annun_green", (0.2, 1.0, 0.4), 1.0)
def ovz(y): return 2.03 - (y - 1.25) * math.tan(R_(8))
for j in range(12):
    x = -0.38 + j * 0.069
    for y in (0.72, 1.82):
        ov.cyl((x, y, ovz(y) - 0.02), 0.004, 0.035, M_steel, rot=(30, 0, 0), seg=8)
        ov.sphere((x, y - 0.008, ovz(y) - 0.036), 0.007, M_steel, seg=8)
        if j % 3 == 0:
            ov.box((x - 0.012, y, ovz(y) - 0.02), (0.003, 0.03, 0.03), M_guard); ov.box((x + 0.012, y, ovz(y) - 0.02), (0.003, 0.03, 0.03), M_guard)
    ov.cyl((x, 1.55, ovz(1.55) - 0.015), 0.014, 0.02, M_black, seg=14)
    ov.box((x, 1.64, ovz(1.64) - 0.006), (0.05, 0.016, 0.006), M_amber if j % 4 == 1 else (M_annun_g if j % 5 == 2 else M_black))
for k in range(5): ov.box((0, 0.7 + k * 0.25, ovz(0.7 + k * 0.25) - 0.008), (0.86, 0.004, 0.004), M_steel)
ov.obj(cSet)

# pedestal: radio heads, flap + speedbrake levers, trim wheels, fire handles
pe = MB("PEDESTAL_ITEMS"); M_radio = img_mat("M_radio_head", "disp_radio.png", 1.0)
pe.box((0, 1.56, 0.80), (0.32, 0.20, 0.04), M_panel, bevel=0.004)
pe.box((0.10, 1.96, 0.79), (0.03, 0.12, 0.012), M_black); pe.box((-0.10, 1.96, 0.79), (0.03, 0.12, 0.012), M_black)
for s_ in (-1, 1):
    pe.cyl((s_ * 0.185, 1.72, 0.55), 0.11, 0.035, M_dark, rot=(0, 90, 0), seg=28)
    for k in range(12):
        a = k * 30; pe.box((s_ * 0.185, 1.72 + 0.11 * math.cos(R_(a)), 0.55 + 0.11 * math.sin(R_(a))), (0.04, 0.012, 0.012), M_white_e if k == 0 else M_steel, rot=(a, 0, 0))
for k in range(3): pe.box((-0.08 + k * 0.08, 2.08, 0.82), (0.05, 0.03, 0.03), M_guard)
po = pe.obj(cSet)
for i, y in enumerate((1.51, 1.61)):
    quad("RADIO_HEAD_%d" % i, (0, y, 0.823), 0.28, 0.07, M_radio, (-90, 0, 0))
fl = MB("FLAP_LEVER"); fl.box((0, 0, 0.06), (0.012, 0.012, 0.12), M_steel); fl.box((0, 0, 0.125), (0.05, 0.02, 0.02), M_plast); flo = fl.obj(cSet); flo.location = (0.10, 1.96, 0.79)
sb = MB("SPEEDBRAKE_LEVER"); sb.box((0, 0, 0.06), (0.012, 0.012, 0.12), M_steel); sb.box((0, 0, 0.125), (0.02, 0.05, 0.02), M_dark); sbo = sb.obj(cSet); sbo.location = (-0.10, 1.96, 0.79)

# sun visors, window frames, clipboard, cups (cups/clipboard/pen are loose props, animated in 03)
M_visor = mat("M_visor", (0.05, 0.12, 0.06), rough=0.15); M_visor.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.55
for s_ in (-1, 1):
    v = MB("VISOR_%s" % ("L" if s_ < 0 else "R")); v.box((0, 0, -0.07), (0.42, 0.006, 0.15), M_visor); v.cyl((0, 0, 0), 0.008, 0.44, M_dark, rot=(0, 90, 0))
    vo = v.obj(cSet); vo.location = (s_ * 0.5, 2.18, 1.76); vo.rotation_euler = (R_(-62), 0, 0)
    fr = MB("SIDEWIN_FRAME_%s" % ("L" if s_ < 0 else "R"))
    fr.box((s_ * 1.13, 1.42, 1.62), (0.05, 0.95, 0.03), M_dark); fr.box((s_ * 1.18, 1.42, 1.11), (0.05, 0.95, 0.03), M_dark)
    fr.box((s_ * 1.15, 1.42, 1.37), (0.04, 0.03, 0.52), M_dark); fr.box((s_ * 1.13, 1.20, 1.66), (0.03, 0.03, 0.04), M_steel)
    fr.obj(cSet)
cL = coll("LOOSE", cSet)
M_chk = img_mat("M_checklist", "checklist.png", emit=False)
cb = MB("CLIPBOARD"); cb.box((0, 0, 0), (0.17, 0.24, 0.006), mat("M_clipboard", (0.25, 0.16, 0.08), rough=0.6, noise=0.3, nscale=40)); cbo = cb.obj(cL)
cbo.location = (-0.98, 1.45, 0.665)
q = quad("CHECKLIST_SHEET", (0, 0, 0.0035), 0.15, 0.21, M_chk, (-90, 0, 0), cL); q.parent = cbo
pen = MB("PEN"); pen.cyl((0, 0, 0), 0.005, 0.13, mat("M_pen", (0.05, 0.08, 0.3), rough=0.3), rot=(0, 90, 0), seg=8); peno = pen.obj(cL); peno.location = (-0.95, 1.62, 0.668)
M_mug = mat("M_mug", (0.75, 0.73, 0.7), rough=0.3); M_cof = mat("M_coffee", (0.05, 0.025, 0.01), rough=0.05)
for s_ in (-1, 1):
    u = MB("MUG_%s" % ("L" if s_ < 0 else "R")); u.cyl((0, 0, 0.045), 0.035, 0.09, M_mug, seg=18); u.cyl((0, 0, 0.087), 0.031, 0.004, M_cof, seg=18)
    u.box((0.04, 0, 0.05), (0.012, 0.008, 0.045), M_mug); uo = u.obj(cL); uo.location = (s_ * 1.0, 1.78, 0.665)
    ch = MB("CUPHOLDER_%s" % ("L" if s_ < 0 else "R")); ch.cyl((s_ * 1.0, 1.78, 0.66), 0.045, 0.012, M_steel, seg=18); ch.obj(cSet)
# yoke buttons
for side in ("L", "R"):
    y = bpy.data.objects["YOKE_%s" % side]; b = MB("YOKE_BTN_%s" % side)
    for s_ in (-1, 1):
        b.cyl((s_ * 0.17, -0.205, 0.875), 0.008, 0.012, mat("M_btn_red", (0.6, 0.03, 0.02), rough=0.3), seg=10)
        b.box((s_ * 0.15, -0.215, 0.85), (0.012, 0.01, 0.02), M_black)
    b.cyl((0, -0.225, 0.74), 0.03, 0.006, M_steel, rot=(90, 0, 0), seg=20)
    bo = b.obj(cSet); bo.parent = y
# master caution lamps (amber, keyed in 03)
M_caut = emit_mat("M_caution", (1.0, 0.55, 0.05), 0.2)
for x in (-0.48, 0.48):
    c_ = MB("CAUTION_%s" % ("L" if x < 0 else "R")); c_.box((0, 0, 0), (0.06, 0.02, 0.035), M_caut, bevel=0.004); co = c_.obj(cSet); co.location = (x, 2.15, 1.055)

# ------------------------------------------------------------------ interior lights
for i in range(5):
    ld = bpy.data.lights.new("L_cabin_%d" % i, 'AREA'); ld.shape = 'RECTANGLE'; ld.size, ld.size_y = 0.4, 2.4
    ld.energy = 140; ld.color = (1, 0.95, 0.88)
    lo = bpy.data.objects.new(ld.name, ld); lo.location = (0, -2.6 - 2.6 * i, 2.0); cSet.objects.link(lo)
ld = bpy.data.lights.new("L_cockpit", 'AREA'); ld.size = 0.8; ld.energy = 80; ld.color = (1, 0.97, 0.92)
lo = bpy.data.objects.new("L_cockpit", ld); lo.location = (0, 1.0, 2.0); cSet.objects.link(lo)
ld = bpy.data.lights.new("L_door_fill", 'AREA'); ld.size = 0.6; ld.energy = 45; ld.color = (1, 0.95, 0.9)
lo = bpy.data.objects.new("L_door_fill", ld); lo.location = (0.1, 0.35, 1.95); cSet.objects.link(lo)
ld = bpy.data.lights.new("L_panel_glow", 'AREA'); ld.size = 1.6; ld.size_y = 0.2; ld.shape = 'RECTANGLE'; ld.energy = 8; ld.color = (0.7, 0.85, 1)
lo = bpy.data.objects.new("L_panel_glow", ld); lo.location = (0, 2.0, 0.85); lo.rotation_euler = (R_(-90), 0, 0); cSet.objects.link(lo)

# ------------------------------------------------------------------ wing + engine (fixed to airframe)
for s in (-1, 1):
    wg = MB("WING_%s" % ("L" if s < 0 else "R"))
    bm = wg.bm
    pts = [(s * 1.3, -4.3, -0.15), (s * 1.3, -8.6, -0.1), (s * 15.0, -13.8, 0.9), (s * 15.0, -12.4, 0.95)]
    vs = [bm.verts.new(p) for p in pts]; vt = [bm.verts.new((p[0], p[1], p[2] + (0.32 if abs(p[0]) < 2 else 0.1))) for p in pts]
    bm.faces.new(vs[::-1]); bm.faces.new(vt)
    for k in range(4): bm.faces.new((vs[k], vs[(k + 1) % 4], vt[(k + 1) % 4], vt[k]))
    for f in bm.faces: f.material_index = 0
    wg.mats.append(M_wing)
    wg.cyl((s * 4.6, -5.6, -0.9), 0.75, 2.8, M_wing, rot=(90, 0, 0), seg=32)
    wg.cyl((s * 4.6, -4.18, -0.9), 0.66, 0.05, M_black, rot=(90, 0, 0), seg=32)
    wg.box((s * 4.6, -6.3, -0.3), (0.12, 1.8, 0.6), M_wing)
    wg.box((s * 15.1, -13.2, 1.5), (0.06, 1.0, 1.2), M_wing, rot=(0, 0, 0))
    wg.obj(cSet)
# fuselage outer skin visible from windows (nose-down view etc.)

# ------------------------------------------------------------------ exterior (all under EXT_ROT -> EXT_MOVE)
EXT_ROT = empty("EXT_ROT", (0, 1.5, 1.2), cExt)
EXT_MOVE = empty("EXT_MOVE", (0, 0, -3000), cExt, EXT_ROT)
# ground: patchwork farmland + roads + haze by distance
gm, nt = nodes_mat("M_ground"); N, L = nt.nodes, nt.links; p = N["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.9
tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / 260, 1 / 420, 1)
L.new(tc.outputs["Object"], mp.inputs["Vector"])
nz0 = N.new("ShaderNodeTexNoise"); nz0.inputs["Scale"].default_value = 0.6; nz0.inputs["Detail"].default_value = 2
L.new(mp.outputs[0], nz0.inputs["Vector"])
mixv = N.new("ShaderNodeMix"); mixv.data_type = 'VECTOR'; mixv.inputs["Factor"].default_value = 0.25
L.new(mp.outputs[0], mixv.inputs["A"]); L.new(nz0.outputs["Color"], mixv.inputs["B"])
vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 1.0; vor.inputs["Randomness"].default_value = 0.85
L.new(mixv.outputs["Result"], vor.inputs["Vector"])
vor2 = N.new("ShaderNodeTexVoronoi"); vor2.feature = 'DISTANCE_TO_EDGE'; vor2.inputs["Scale"].default_value = 1.0; vor2.inputs["Randomness"].default_value = 0.85
L.new(mixv.outputs["Result"], vor2.inputs["Vector"])
ramp = N.new("ShaderNodeValToRGB"); L.new(vor.outputs["Color"], ramp.inputs[0])
cr = ramp.color_ramp; cr.interpolation = 'CONSTANT'
cols = [(0.06, 0.12, 0.03), (0.16, 0.2, 0.06), (0.1, 0.16, 0.04), (0.28, 0.24, 0.1), (0.05, 0.1, 0.03), (0.2, 0.18, 0.12), (0.12, 0.19, 0.05), (0.33, 0.3, 0.14)]
cr.elements[0].color = (*cols[0], 1); cr.elements[1].position = 1.0; cr.elements[1].color = (*cols[-1], 1)
for i, c in enumerate(cols[1:-1]):
    el = cr.elements.new((i + 1) / (len(cols) - 1)); el.color = (*c, 1)
# fine noise variation (furrows)
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40.0; nz.inputs["Detail"].default_value = 6; L.new(mp.outputs[0], nz.inputs["Vector"])
mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'OVERLAY'; mul.inputs["Factor"].default_value = 0.35
L.new(ramp.outputs[0], mul.inputs["A"]); L.new(nz.outputs["Color"], mul.inputs["B"])
road = N.new("ShaderNodeMath"); road.operation = 'LESS_THAN'; L.new(vor2.outputs["Distance"], road.inputs[0]); road.inputs[1].default_value = 0.025
mr = N.new("ShaderNodeMix"); mr.data_type = 'RGBA'; L.new(road.outputs[0], mr.inputs["Factor"])
L.new(mul.outputs["Result"], mr.inputs["A"]); mr.inputs["B"].default_value = (0.25, 0.25, 0.22, 1)
cam = N.new("ShaderNodeCameraData")
hz = N.new("ShaderNodeMath"); hz.operation = 'DIVIDE'; L.new(cam.outputs["View Distance"], hz.inputs[0]); hz.inputs[1].default_value = 30000
hz2 = N.new("ShaderNodeMath"); hz2.operation = 'MINIMUM'; L.new(hz.outputs[0], hz2.inputs[0]); hz2.inputs[1].default_value = 0.85
mh = N.new("ShaderNodeMix"); mh.data_type = 'RGBA'; L.new(hz2.outputs[0], mh.inputs["Factor"])
L.new(mr.outputs["Result"], mh.inputs["A"]); mh.inputs["B"].default_value = (0.55, 0.62, 0.72, 1)
L.new(mh.outputs["Result"], p.inputs["Base Color"])
me = bpy.data.meshes.new("GROUND"); S = 40000
me.from_pydata([(-S, -S, 0), (S, -S, 0), (S, S, 0), (-S, S, 0)], [], [(0, 1, 2, 3)]); me.materials.append(gm)
g = bpy.data.objects.new("GROUND", me); cExt.objects.link(g); g.parent = EXT_MOVE

# sky dome (follows attitude, not altitude)
sm, nt = nodes_mat("M_sky"); N, L = nt.nodes, nt.links; N.remove(N["Principled BSDF"])
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); nrm = N.new("ShaderNodeVectorMath"); nrm.operation = 'NORMALIZE'
L.new(tc.outputs["Object"], nrm.inputs[0]); L.new(nrm.outputs[0], sep.inputs[0])
rp = N.new("ShaderNodeValToRGB"); L.new(sep.outputs[2], rp.inputs[0])
rp.color_ramp.elements[0].position = 0.0; rp.color_ramp.elements[0].color = (0.62, 0.7, 0.8, 1)
rp.color_ramp.elements[1].position = 0.6; rp.color_ramp.elements[1].color = (0.12, 0.3, 0.72, 1)
el = rp.color_ramp.elements.new(0.06); el.color = (0.6, 0.72, 0.9, 1)
em = N.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 2.2; L.new(rp.outputs[0], em.inputs["Color"])
L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=45000)
dome = C.active_object; dome.name = "SKY_DOME"; dome.data.materials.append(sm); link(dome, cExt); dome.parent = EXT_ROT
dome.visible_shadow = False
# sun + visible sun disc
ld = bpy.data.lights.new("SUN", 'SUN'); ld.energy = 4.5; ld.angle = R_(1.5); ld.color = (1, 0.95, 0.86)
sun = bpy.data.objects.new("SUN", ld); cExt.objects.link(sun); sun.parent = EXT_ROT
sun.rotation_euler = (R_(-62), 0, R_(200))   # light coming from ahead-left, high
sd = MB("SUN_DISC"); sd.sphere((0, 0, 0), 900, emit_mat("M_sun", (1, 0.95, 0.85), 40.0)); sdo = sd.obj(cExt)
sdo.parent = sun; sdo.location = (0, 0, 40000); sdo.visible_shadow = False

# cloud cards (between plane and ground; follow altitude)
cm, nt = nodes_mat("M_cloud"); N, L = nt.nodes, nt.links; p = N["Principled BSDF"]
p.inputs["Base Color"].default_value = (1, 1, 1, 1); p.inputs["Roughness"].default_value = 1.0
p.inputs["Emission Color"].default_value = (0.9, 0.92, 0.95, 1); p.inputs["Emission Strength"].default_value = 0.6
tc = N.new("ShaderNodeTexCoord"); nzc = N.new("ShaderNodeTexNoise"); nzc.inputs["Scale"].default_value = 2.5; nzc.inputs["Detail"].default_value = 10
nzc.inputs["Roughness"].default_value = 0.6
L.new(tc.outputs["Generated"], nzc.inputs["Vector"])
gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
mpc = N.new("ShaderNodeMapping"); mpc.inputs["Location"].default_value = (-0.5, -0.5, 0); mpc.inputs["Scale"].default_value = (2, 2, 1)
L.new(tc.outputs["Generated"], mpc.inputs["Vector"]); mpc.inputs["Location"].default_value = (-1, -1, 0)
L.new(mpc.outputs[0], gr.inputs["Vector"])
mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; L.new(nzc.outputs["Fac"], mm.inputs[0]); L.new(gr.outputs["Fac"], mm.inputs[1])
mr = N.new("ShaderNodeMapRange"); L.new(mm.outputs[0], mr.inputs["Value"]); mr.inputs["From Min"].default_value = 0.22; mr.inputs["From Max"].default_value = 0.38
L.new(mr.outputs["Result"], p.inputs["Alpha"])
cC = coll("CLOUDS", cExt)
for i in range(70):
    s = random.uniform(1200, 3200)
    me = bpy.data.meshes.new("cloud"); me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(); me.materials.append(cm)
    o = bpy.data.objects.new("CLOUD_%02d" % i, me); cC.objects.link(o); o.parent = EXT_MOVE
    o.location = (random.uniform(-14000, 14000), random.uniform(-6000, 30000), random.uniform(1500, 2100))
    o.rotation_euler = (0, 0, random.uniform(0, 6.3)); o.visible_shadow = False

# world (only for reflections/ambient leaking past the dome)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.45, 0.55, 0.7, 1); w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
