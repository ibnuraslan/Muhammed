"""B14 MomLiftsCar: all sets in one file.  blender -b --python 02_sets.py -- out.blend
SetDrive x=0 (1960s suburban driveway + car), SetBody x=40 (anatomy on the sky gradient), SetPark x=80 (park lawn + log)."""
import bpy, bmesh, sys, math, random
from mathutils import Vector, Matrix
W = "/tmp/claude-0/b14/"; A = W + "assets/"; BRAND = "/home/user/Muhammed/blender/assets/brand/"
R_ = math.radians
OUT = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
exec(open(W + "scripts/lib_sets.py").read())
random.seed(14)

# ------------------------------------------------------------------ render + world (sky gradient to camera, soft light elsewhere)
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
w = bpy.data.worlds.new("SkyWorld"); sc.world = w; w.use_nodes = True; nt = w.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputWorld"); lp = nt.nodes.new("ShaderNodeLightPath")
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Window"], sep.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(sep.outputs["Y"], ramp.inputs[0])
ramp.color_ramp.elements[0].color = (0.82, 0.93, 1.0, 1); ramp.color_ramp.elements[0].position = 0.05
ramp.color_ramp.elements[1].color = (0.08, 0.52, 0.93, 1); ramp.color_ramp.elements[1].position = 0.95
bgc = nt.nodes.new("ShaderNodeBackground"); nt.links.new(ramp.outputs[0], bgc.inputs[0]); bgc.inputs[1].default_value = 1.0
bgl = nt.nodes.new("ShaderNodeBackground"); bgl.inputs[0].default_value = (0.75, 0.86, 1.0, 1); bgl.inputs[1].default_value = 0.9
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
nt.links.new(bgl.outputs[0], mx.inputs[1]); nt.links.new(bgc.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.data.angle = R_(8); sun.rotation_euler = (R_(48), R_(10), R_(-35)); sun.data.color = (1.0, 0.97, 0.92)

def tex_mat(name, folder, scale=1.0, tint=None, rough_min=0.4, bump=0.3):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    import glob
    d = glob.glob(A + "ph/%s/textures/*_diff_*.jpg" % folder)[0]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    nt.links.new(tc.outputs["UV"], mp.inputs[0])
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(d); nt.links.new(mp.outputs[0], t.inputs[0])
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 1.2; nt.links.new(t.outputs[0], hs.inputs["Color"])
    src = hs.outputs[0]
    if tint:
        mxn = nt.nodes.new("ShaderNodeMix"); mxn.data_type = 'RGBA'; mxn.blend_type = 'MULTIPLY'; mxn.inputs['Factor'].default_value = 1.0
        mxn.inputs['B'].default_value = (*tint, 1); nt.links.new(src, mxn.inputs['A']); src = mxn.outputs['Result']
    nt.links.new(src, P.inputs["Base Color"]); P.inputs["Roughness"].default_value = max(rough_min, 0.6)
    bm_ = nt.nodes.new("ShaderNodeBump"); bm_.inputs["Strength"].default_value = bump
    nt.links.new(t.outputs[0], bm_.inputs["Height"]); nt.links.new(bm_.outputs[0], P.inputs["Normal"])
    return m

def noise_mat(name, c1, c2, scale=8.0, rough=0.7, bump=0.25):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 6
    rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (*c1, 1); rp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(nz.outputs["Fac"], rp.inputs[0]); nt.links.new(rp.outputs[0], P.inputs["Base Color"])
    P.inputs["Roughness"].default_value = rough
    b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = bump; nt.links.new(nz.outputs["Fac"], b.inputs["Height"]); nt.links.new(b.outputs[0], P.inputs["Normal"])
    return m

def uv_box(o):
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT'); o.select_set(False)

def shrub(name, c, loc, size, m):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=loc); o = bpy.context.object; o.name = name
    o.scale = size; link(o, c)
    tx = bpy.data.textures.new(name + "_T", 'VORONOI'); tx.noise_scale = 0.18
    d = o.modifiers.new("D", 'DISPLACE'); d.texture = tx; d.strength = 0.22; d.texture_coords = 'GLOBAL'
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    return o

# ================================================================== SetDrive
cD = col("SetDrive")
m_lawn = noise_mat("Lawn", (0.20, 0.50, 0.12), (0.33, 0.66, 0.18), 3.0, 0.85, 0.2)
m_conc = noise_mat("Concrete", (0.70, 0.69, 0.66), (0.80, 0.79, 0.76), 14.0, 0.75, 0.15)
lawn = plane("DriveLawn", cD, (0, 0, 0), (70, 70), m_lawn)
drive = box("Driveway", cD, (0, -3.0, 0.02), (4.6, 20, 0.04), m_conc, bevel=0.01)
# expansion joints in the driveway
for i in range(-6, 7):
    box("DriveJoint%d" % i, cD, (0, -3.0 + i * 1.6, 0.0405), (4.6, 0.015, 0.002), mat("Joint", (0.45, 0.45, 0.43), 0.8), bevel=0)
# sidewalk + street at the rear (+Y)
box("Sidewalk", cD, (0, 8.3, 0.03), (70, 1.6, 0.06), m_conc, bevel=0.01)
box("Street", cD, (0, 13.0, 0.01), (70, 7.6, 0.02), tex_mat("Asphalt", "aerial_asphalt_01", 6.0, (0.85, 0.85, 0.88)), bevel=0)
uv_box(bpy.data.objects["Street"])
# house (pale yellow siding) along +X, garage at the end of the driveway (-Y)
m_sid = mat("Siding", (0.93, 0.85, 0.58), 0.6); m_trim = mat("Trim", (0.97, 0.97, 0.95), 0.45)
m_roof = mat("Roof", (0.36, 0.30, 0.28), 0.8); m_glass = mat("WinGlass", (0.35, 0.55, 0.75), 0.08, metal=0.2)
m_door = mat("GarageDoor", (0.97, 0.96, 0.93), 0.5); m_red = mat("FrontDoor", (0.62, 0.12, 0.10), 0.45)
garage = box("Garage", cD, (0, -15.5, 1.5), (5.6, 5.0, 3.0), m_sid, bevel=0.02)
box("GarageRoof", cD, (0, -15.5, 3.1), (6.2, 5.6, 0.25), m_roof, bevel=0.03)
gd = box("GarageDoorPanel", cD, (0, -12.98, 1.15), (4.2, 0.05, 2.3), m_door, bevel=0.01)
for k in range(4):
    box("GDGroove%d" % k, cD, (0, -12.95, 0.3 + k * 0.57), (4.2, 0.02, 0.03), mat("Groove", (0.82, 0.81, 0.78), 0.5), bevel=0)
box("GarageTrim", cD, (0, -12.99, 2.38), (4.5, 0.06, 0.12), m_trim, bevel=0.005)
house = box("House", cD, (8.5, -6.0, 1.6), (7.0, 14.0, 3.2), m_sid, bevel=0.02)
# gabled roof as a prism
bm = bmesh.new()
pts = [(-3.9, -7.4, 0), (3.9, -7.4, 0), (0, -7.4, 1.9), (-3.9, 7.4, 0), (3.9, 7.4, 0), (0, 7.4, 1.9)]
vv = [bm.verts.new(p) for p in pts]
for f in ((0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)): bm.faces.new([vv[i] for i in f])
me = bpy.data.meshes.new("HouseRoof"); bm.to_mesh(me); bm.free(); ro = bpy.data.objects.new("HouseRoof", me); cD.objects.link(ro)
ro.location = (8.5, -6.0, 3.2); me.materials.append(m_roof)
for i, y in enumerate((-10.5, -6.8, -1.2, 2.2)):
    box("WinFrame%d" % i, cD, (4.97, y, 1.7), (0.08, 1.5, 1.3), m_trim, bevel=0.01)
    box("WinGlass%d" % i, cD, (4.94, y, 1.7), (0.06, 1.3, 1.1), m_glass, bevel=0)
    box("WinBar%d" % i, cD, (4.92, y, 1.7), (0.03, 0.05, 1.1), m_trim, bevel=0)
    box("Shutter%dA" % i, cD, (4.97, y - 0.95, 1.7), (0.05, 0.35, 1.3), mat("Shutter", (0.20, 0.42, 0.33), 0.5), bevel=0.005)
    box("Shutter%dB" % i, cD, (4.97, y + 0.95, 1.7), (0.05, 0.35, 1.3), mat("Shutter", (0.20, 0.42, 0.33), 0.5), bevel=0.005)
box("FrontDoor", cD, (4.97, -3.9, 1.05), (0.08, 1.0, 2.1), m_red, bevel=0.01)
box("Step", cD, (4.7, -3.9, 0.1), (0.7, 1.6, 0.2), m_conc, bevel=0.01)
m_hedge = noise_mat("Hedge", (0.12, 0.36, 0.10), (0.24, 0.52, 0.16), 6.0, 0.8, 0.4)
for i, y in enumerate((-12.0, -8.6, -5.2, -0.6, 3.4)):
    shrub("Bush%d" % i, cD, (4.6, y, 0.35), (0.55, 1.1, 0.6), m_hedge)
# picket fence on the left (-X) lawn edge
m_pick = mat("Picket", (0.97, 0.97, 0.95), 0.5)
for i in range(46):
    y = -14 + i * 0.42
    box("Picket%d" % i, cD, (-7.0, y, 0.5), (0.06, 0.1, 1.0), m_pick, bevel=0.01)
box("FenceRail1", cD, (-7.0, -4.5, 0.35), (0.05, 19.4, 0.08), m_pick, bevel=0.005)
box("FenceRail2", cD, (-7.0, -4.5, 0.8), (0.05, 19.4, 0.08), m_pick, bevel=0.005)
for i, (x, y) in enumerate(((-9.5, -9), (-10.5, -2), (-9.8, 4), (12.5, 4.5), (13, -14))):
    shrub("BgTree%d" % i, cD, (x, y, 2.6), (1.6, 1.6, 2.0), m_hedge)
    box("BgTrunk%d" % i, cD, (x, y, 0.8), (0.25, 0.25, 1.6), mat("Trunk", (0.35, 0.24, 0.16), 0.8), bevel=0.02)
# neighbour houses across the street (+Y), so rear views have a real background
for i, x in enumerate((-12, -2, 9)):
    box("NHouse%d" % i, cD, (x, 22, 1.6), (7.5, 6, 3.2), mat("NSid%d" % i, [(0.80, 0.88, 0.95), (0.95, 0.80, 0.78), (0.86, 0.92, 0.80)][i], 0.6), bevel=0.02)
    box("NRoof%d" % i, cD, (x, 22, 3.35), (8.0, 6.4, 0.3), m_roof, bevel=0.03)
    for j in (-2, 2):
        box("NWin%d_%d" % (i, j), cD, (x + j, 18.98, 1.7), (1.2, 0.06, 1.0), m_glass, bevel=0)
        box("NWinF%d_%d" % (i, j), cD, (x + j, 19.0, 1.7), (1.35, 0.05, 1.15), m_trim, bevel=0)
    box("NDoor%d" % i, cD, (x, 18.98, 1.0), (0.9, 0.06, 2.0), m_red, bevel=0)

# ---- the car: 1953 sedan, pale mint green, scaled 0.82; pivot at the front tyres' contact line so the rear can be lifted
CS = 0.82
root, meshes = import_glb(A + "car.glb", "CarModel", cD, scale=1.0)
for o in meshes:
    for i, m in enumerate(o.data.materials):
        if m and m.name.startswith("Body"):
            m2 = m.copy(); o.data.materials[i] = m2
            for nd in m2.node_tree.nodes:
                if nd.type == 'TEX_IMAGE' and nd.outputs['Color'].links:
                    for lk in list(nd.outputs['Color'].links):
                        if lk.to_socket.name != "Base Color": continue
                        mx_ = m2.node_tree.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.blend_type = 'MIX'
                        # keep chrome/light/tyre texels, repaint the dark body paint mint green
                        sepc = m2.node_tree.nodes.new('ShaderNodeSeparateColor'); sepc.mode = 'HSV'
                        m2.node_tree.links.new(nd.outputs['Color'], sepc.inputs[0])
                        mr = m2.node_tree.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.30; mr.inputs['From Max'].default_value = 0.16
                        m2.node_tree.links.new(sepc.outputs[2], mr.inputs[0])
                        sat = m2.node_tree.nodes.new('ShaderNodeMapRange'); sat.inputs['From Min'].default_value = 0.35; sat.inputs['From Max'].default_value = 0.15
                        m2.node_tree.links.new(sepc.outputs[1], sat.inputs[0])
                        mul = m2.node_tree.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
                        m2.node_tree.links.new(mr.outputs[0], mul.inputs[0]); m2.node_tree.links.new(sat.outputs[0], mul.inputs[1])
                        m2.node_tree.links.new(mul.outputs[0], mx_.inputs['Factor'])
                        m2.node_tree.links.new(nd.outputs['Color'], mx_.inputs['A']); mx_.inputs['B'].default_value = (0.55, 0.78, 0.68, 1)
                        m2.node_tree.links.new(mx_.outputs['Result'], lk.to_socket)
bpy.context.view_layer.update()
mn, mx2 = bounds(meshes)
print("CAR bounds raw", mn, mx2)
piv = bpy.data.objects.new("CarPivot", None); cD.objects.link(piv); piv.empty_display_size = 0.5
FRONT_Y = -2.15 * CS          # front axle line (car faces -Y, rear bumper at +Y)
piv.location = (0, FRONT_Y, 0.0)
root.scale = (0.01 * CS,) * 3
bpy.context.view_layer.update()
mn, mx2 = bounds(meshes)
root.location = (-(mn.x + mx2.x) / 2, -(mn.y + mx2.y) / 2 + 0.4, -mn.z)
bpy.context.view_layer.update()
root.parent = piv; root.matrix_parent_inverse = piv.matrix_world.inverted()
mn, mx2 = bounds(meshes)
print("CAR placed", mn, mx2)
sc["car_rear_y"] = mx2.y
# blank number plate (no text) over the textured one
plate = box("BlankPlate", cD, (0, mx2.y - 0.135, 0.585), (0.47, 0.075, 0.19), mat("PlateBlank", (0.96, 0.92, 0.70), 0.5), bevel=0.004)
# hide the trunk chevron emblem (a brand mark painted in the texture): find its UV rect by ray casts, paint it body colour
bodym = next(o for o in meshes if any(m and m.name.startswith("Body") for m in o.data.materials))
dg_ = bpy.context.evaluated_depsgraph_get(); inv_ = bodym.matrix_world.inverted(); uvl = bodym.data.uv_layers.active.data; us = []; vs = []
for xi in range(-9, 10):
    for zi in range(0, 13):
        o_ = inv_ @ Vector((xi * 0.02, mx2.y + 1.0, 0.64 + zi * 0.017)); d_ = (inv_.to_3x3() @ Vector((0, -1, 0))).normalized()
        hit, loc_, nrm_, fi = bodym.ray_cast(o_, d_)
        if hit:
            for li in bodym.data.polygons[fi].loop_indices: us.append(uvl[li].uv.x); vs.append(uvl[li].uv.y)
print("EMBLEM_UV", min(us), max(us), min(vs), max(vs), len(us))
RECTS = [(min(us), max(us), min(vs), max(vs))]
# the number-plate texture ("ROH3D.COM"): rays from behind and from both rear quarters, plate area only
for dirv in (Vector((0, -1, 0)), Vector((0.6, -0.8, 0)), Vector((-0.6, -0.8, 0))):
    pu, pv = [], []
    for xi in range(-12, 13):
        for zi in range(0, 14):
            tgt = Vector((xi * 0.02, mx2.y - 0.12, 0.46 + zi * 0.02))
            o_ = inv_ @ (tgt - dirv * 1.2); d_ = (inv_.to_3x3() @ dirv).normalized()
            hit, loc_, nrm_, fi = bodym.ray_cast(o_, d_)
            if hit:
                wl = bodym.matrix_world @ loc_
                if abs(wl.x) < 0.26 and 0.44 < wl.z < 0.74 and wl.y > mx2.y - 0.3:
                    for li in bodym.data.polygons[fi].loop_indices: pu.append(uvl[li].uv.x); pv.append(uvl[li].uv.y)
    if pu: print("PLATE_UV (not used)", (min(pu), max(pu), min(pv), max(pv)), len(pu))
u0, u1, v0, v1 = RECTS[0]
for m2 in bodym.data.materials:
    if not (m2 and m2.name.startswith("Body")): continue
    nt2 = m2.node_tree; mixn = next(n for n in nt2.nodes if n.type == 'MIX' and n.data_type == 'RGBA')
    mul_ = mixn.inputs['Factor'].links[0].from_node
    uvn = nt2.nodes.new('ShaderNodeUVMap'); sp_ = nt2.nodes.new('ShaderNodeSeparateXYZ'); nt2.links.new(uvn.outputs[0], sp_.inputs[0])
    def rng(sock, lo, hi):
        a1 = nt2.nodes.new('ShaderNodeMath'); a1.operation = 'GREATER_THAN'; a1.inputs[1].default_value = lo; nt2.links.new(sock, a1.inputs[0])
        a2 = nt2.nodes.new('ShaderNodeMath'); a2.operation = 'LESS_THAN'; a2.inputs[1].default_value = hi; nt2.links.new(sock, a2.inputs[0])
        a3 = nt2.nodes.new('ShaderNodeMath'); a3.operation = 'MULTIPLY'; nt2.links.new(a1.outputs[0], a3.inputs[0]); nt2.links.new(a2.outputs[0], a3.inputs[1]); return a3.outputs[0]
    ru = rng(sp_.outputs[0], u0, u1); rv = rng(sp_.outputs[1], v0, v1)
    inb = nt2.nodes.new('ShaderNodeMath'); inb.operation = 'MULTIPLY'; nt2.links.new(ru, inb.inputs[0]); nt2.links.new(rv, inb.inputs[1])
    mxm = nt2.nodes.new('ShaderNodeMath'); mxm.operation = 'MAXIMUM'; nt2.links.new(mul_.outputs[0], mxm.inputs[0]); nt2.links.new(inb.outputs[0], mxm.inputs[1])
    last = mxm
    for (a0, a1, b0, b1) in RECTS[1:]:
        r1 = rng(sp_.outputs[0], a0, a1); r2 = rng(sp_.outputs[1], b0, b1)
        ib = nt2.nodes.new('ShaderNodeMath'); ib.operation = 'MULTIPLY'; nt2.links.new(r1, ib.inputs[0]); nt2.links.new(r2, ib.inputs[1])
        mm = nt2.nodes.new('ShaderNodeMath'); mm.operation = 'MAXIMUM'; nt2.links.new(last.outputs[0], mm.inputs[0]); nt2.links.new(ib.outputs[0], mm.inputs[1]); last = mm
    nt2.links.new(last.outputs[0], mixn.inputs['Factor'])
plate.parent = root; plate.matrix_parent_inverse = root.matrix_world.inverted(); sc["car_front_y"] = mn.y

# ---- toppled scissor jack beside the rear-left wheel (why the car fell)
m_jack = mat("JackPaint", (0.75, 0.12, 0.08), 0.45, metal=0.3)
jk = bpy.data.objects.new("Jack", None); cD.objects.link(jk)
for i, (L, z, a) in enumerate(((0.36, 0.05, 0), (0.30, 0.13, 25), (0.30, 0.13, -25), (0.26, 0.20, 0))):
    b_ = box("JackBar%d" % i, cD, (0, 0, z), (L, 0.06, 0.03), m_jack, bevel=0.005, rot=(0, R_(a), 0)); b_.parent = jk
bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.42, location=(0, 0, 0.13), rotation=(0, R_(90), 0))
sc_ = bpy.context.object; sc_.name = "JackScrew"; sc_.data.materials.append(mat("JackSteel", (0.6, 0.6, 0.62), 0.3, metal=0.9)); link(sc_, cD); sc_.parent = jk
jk.location = (-1.05, 1.05, 0.04); jk.rotation_euler = (R_(90), 0, R_(70))

# ================================================================== SetBody (x=40): kidneys + adrenal glands, vessels, muscle
cB = col("SetBody")
kroot, kmeshes = import_glb(A + "kidney.glb", "KidneyModel", cB)
bpy.context.view_layer.update(); mn, mx2 = bounds(kmeshes); s = 0.9 / max((mx2 - mn)[:])
kroot.scale = (s,) * 3; bpy.context.view_layer.update(); mn, mx2 = bounds(kmeshes)
kroot.location = (40 - (mn.x + mx2.x) / 2, -(mn.y + mx2.y) / 2, 1.0 - (mn.z + mx2.z) / 2); bpy.context.view_layer.update()
mn, mx2 = bounds(kmeshes); print("KIDNEY", mn, mx2, [o.name for o in kmeshes])
for o in kmeshes:
    for i, m in enumerate(o.data.materials):
        if m:
            P = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if P: P.inputs["Roughness"].default_value = max(0.35, P.inputs["Roughness"].default_value); P.inputs["Coat Weight"].default_value = 0.3
sc["kid_min"] = mn; sc["kid_max"] = mx2

def tube_curve(name, c, pts, r, m, res=12):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 4; cu.use_fill_caps = True
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1); sp.order_u = min(4, len(pts)); sp.use_endpoint_u = True
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    o = bpy.data.objects.new(name, cu); c.objects.link(o); cu.materials.append(m); return o

# vessel bed (x=40, y=10): a clean muscle surface with branching, cut-open arteries (clean cross-section) and blood cells inside
m_musc = noise_mat("MuscleBed", (0.72, 0.22, 0.24), (0.86, 0.38, 0.36), 18.0, 0.45, 0.35)
bed = plane("VesselBed", cB, (40, 10, 0), (6, 6), m_musc)
bed.modifiers.new("Sub", 'SUBSURF').levels = 3
txb = bpy.data.textures.new("BedT", 'STUCCI'); txb.noise_scale = 0.4
d_ = bed.modifiers.new("D", 'DISPLACE'); d_.texture = txb; d_.strength = 0.03
fat = noise_mat("FatBed", (0.95, 0.70, 0.30), (0.98, 0.80, 0.42), 30.0, 0.4, 0.4)
m_vwall = mat("VesselWall", (0.80, 0.08, 0.10), 0.35, coat=0.4)
m_vin = mat("VesselLumen", (0.45, 0.03, 0.05), 0.5)
SPLIT = (40, 10.6, 0.10)
paths = {"Trunk": [(40, 7.2, 0.10), (40, 8.4, 0.10), (40, 9.6, 0.10), SPLIT],
         "BrA": [SPLIT, (39.7, 11.2, 0.10), (39.3, 11.9, 0.10), (38.9, 12.8, 0.10)],
         "BrB": [SPLIT, (40.3, 11.2, 0.10), (40.7, 11.9, 0.10), (41.1, 12.8, 0.10)]}
VR = {"Trunk": 0.16, "BrA": 0.12, "BrB": 0.12}
for k, pts in paths.items():
    # half-pipe: a full tube clipped open on top by a boolean -> a clean cut-open vessel showing its inside
    o = tube_curve("Vessel_" + k, cB, pts, VR[k], m_vwall)
    o.data.bevel_resolution = 6; o.data.extrude = 0
    o.data.materials.append(m_vin)
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.convert(target='MESH'); o.select_set(False)
    sol = o.modifiers.new("Wall", 'SOLIDIFY'); sol.thickness = 0.018; sol.offset = 1; sol.material_offset = 1
    o.data.materials[0] = m_vwall
    cut = box("VesselCut_" + k, cB, (40, 10, 0.10 + 1.0 + 0.02), (8, 8, 2.0), mat("CutTool", (1, 1, 1)), bevel=0)
    bo = o.modifiers.new("Open", 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
    cut.hide_render = True; cut.hide_viewport = True; cut.display_type = 'WIRE'
# smaller capillaries running into the muscle bed
for i in range(10):
    a = random.uniform(0, 2 * math.pi); x0 = 40 + random.uniform(-2.2, 2.2); y0 = 10 + random.uniform(-2.2, 2.2)
    pts = [(x0 + 0.5 * k * math.cos(a) + 0.08 * math.sin(k * 2), y0 + 0.5 * k * math.sin(a), 0.03) for k in range(5)]
    tube_curve("Capillary%d" % i, cB, pts, 0.025, mat("Capillary", (0.70, 0.07, 0.12), 0.4, coat=0.3))
# red blood cell (biconcave disc via lathe); instanced and animated later along the vessel paths
prof = [(0.0, -0.012), (0.03, -0.018), (0.055, -0.02), (0.07, -0.01), (0.072, 0.0), (0.07, 0.01), (0.055, 0.02), (0.03, 0.018), (0.0, 0.012)]
rbc = lathe("RBC_Proto", cB, prof, mat("RBC", (0.85, 0.06, 0.08), 0.3, coat=0.5), (40, 0, -20), segs=24, cap_bottom=False)
rbc.scale = (0.85,) * 3
# oxygen / energy dots (bright green-yellow), as in the reference
o2 = bpy.data.meshes.new("O2Dot")
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.022); bm.to_mesh(o2); bm.free()
o2o = bpy.data.objects.new("O2_Proto", o2); cB.objects.link(o2o); o2o.location = (40, 0, -20)
o2.materials.append(mat("O2Glow", (0.55, 1.0, 0.25), 0.3, emit=((0.55, 1.0, 0.2), 4.0)))
for p in o2.polygons: p.use_smooth = True
# adrenaline drop (amber) prototype
ad = bpy.data.meshes.new("AdrDot"); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.018); bm.to_mesh(ad); bm.free()
ado = bpy.data.objects.new("Adr_Proto", ad); cB.objects.link(ado); ado.location = (40, 0, -20)
ad.materials.append(mat("AdrGlow", (1.0, 0.78, 0.15), 0.3, emit=((1.0, 0.75, 0.1), 5.0)))
for p in ad.polygons: p.use_smooth = True

# muscle (x=40, y=20): a spindle-shaped muscle belly made of fibre bundles, cream tendons at both ends
m_fib = noise_mat("MuscleFibre", (0.78, 0.16, 0.20), (0.92, 0.36, 0.38), 40.0, 0.4, 0.35)
m_ten = mat("Tendon", (0.95, 0.90, 0.80), 0.35, coat=0.3)
mus = bpy.data.objects.new("Muscle", None); cB.objects.link(mus); mus.location = (70, 30, 1.0)
for i in range(19):
    ring = 0 if i == 0 else (1 if i < 7 else 2); k = 0 if i == 0 else (i - 1 if i < 7 else i - 7)
    n_ring = 6 if ring == 1 else 12
    ang = 2 * math.pi * k / n_ring + (0.3 if ring == 2 else 0); rr = (0, 0.07, 0.14)[ring]
    pts = []
    for j in range(9):
        t = j / 8; zz = -0.75 + 1.5 * t; bulge = math.sin(math.pi * t) ** 0.8
        tw = ang + 0.7 * t   # a slight spiral, like the reference's twisted muscle
        pts.append((rr * bulge * math.cos(tw) * 1.6, rr * bulge * math.sin(tw) * 1.6, zz))
    f = tube_curve("Fibre%d" % i, cB, pts, 0.075 if ring else 0.08, m_fib); f.parent = mus
    f.data.bevel_resolution = 3
    # taper: radius follows the bulge
    for p, j in zip(f.data.splines[0].points, range(9)):
        p.radius = 0.25 + 0.75 * math.sin(math.pi * j / 8)
for zz in (-0.95, 0.95):
    t_ = tube_curve("Tendon%s" % ("Lo" if zz < 0 else "Hi"), cB, [(0, 0, zz * 0.78), (0, 0, zz), (0, 0, zz * 1.18)], 0.06, m_ten); t_.parent = mus

# adrenal glands: yellow-orange caps sitting on top of each kidney
m_adr = noise_mat("AdrenalGland", (0.98, 0.70, 0.18), (1.0, 0.82, 0.32), 25.0, 0.4, 0.3)
kmn, kmx = Vector(sc["kid_min"]), Vector(sc["kid_max"])
for i, xx in enumerate((kmn.x + 0.17, kmx.x - 0.17)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.11, location=(xx, 0, kmx.z - 0.06))
    g = bpy.context.object; g.name = "Adrenal%d" % i; g.scale = (1.0, 0.55, 0.55); g.rotation_euler.y = R_(-25 if i == 0 else 25)
    tx = bpy.data.textures.new("AdrT%d" % i, 'CLOUDS'); tx.noise_scale = 0.06
    dm = g.modifiers.new("D", 'DISPLACE'); dm.texture = tx; dm.strength = 0.015
    g.data.materials.append(m_adr); link(g, cB)
    for p in g.data.polygons: p.use_smooth = True
# lift the whole anatomy set into open sky (z+100) so no lawn shows behind it
for o in list(cB.objects):
    if o.parent is None: o.location.z += 100
    if o.parent is None and o.name.startswith(("Vessel", "Capillary")): o.location.y -= 22
bpy.context.view_layer.update()

# ================================================================== SetPark (x=80): lawn, path, log, bench, hedges
cP = col("SetPark")
plane("ParkLawn", cP, (80, 0, 0), (50, 50), m_lawn)
box("ParkPath", cP, (80, 2.5, 0.015), (30, 1.8, 0.03), m_conc, bevel=0.005)
m_bark = tex_mat("Bark", "bark_brown_02", 2.0, (1.15, 1.0, 0.85), 0.5, 0.35)
# fallen tree trunk along X, with two branch stubs; the man lifts its thick end
log = tube_curve("Log", cP, [(-1.6, 0, 0), (-0.6, 0, 0.02), (0.6, 0, 0.0), (1.8, 0, -0.02)], 0.17, m_bark)
for p, rr in zip(log.data.splines[0].points, (1.15, 1.05, 0.95, 0.8)): p.radius = rr
log.data.bevel_resolution = 6
bpy.context.view_layer.objects.active = log; log.select_set(True); bpy.ops.object.convert(target='MESH'); log.select_set(False)
uv = log.data.uv_layers.new(); uv_box(log)
for i, (x, a) in enumerate(((0.2, 35), (1.1, -40))):
    st = tube_curve("LogBranch%d" % i, cP, [(x, 0, 0.1), (x + 0.15, 0.22 * math.copysign(1, a), 0.32), (x + 0.3, 0.35 * math.copysign(1, a), 0.55)], 0.05, m_bark)
    bpy.context.view_layer.objects.active = st; st.select_set(True); bpy.ops.object.convert(target='MESH'); st.select_set(False)
    st.data.uv_layers.new(); uv_box(st); st.parent = log
end = bpy.data.objects.new("LogEndCap", None)
# light wood cut faces at both ends
for xx, rr in ((-1.6, 0.195), (1.8, 0.136)):
    bpy.ops.mesh.primitive_cylinder_add(radius=rr, depth=0.02, location=(xx, 0, 0), rotation=(0, R_(90), 0))
    cf = bpy.context.object; cf.name = "LogCut%d" % (0 if xx < 0 else 1); cf.data.materials.append(noise_mat("CutWood", (0.86, 0.68, 0.45), (0.93, 0.78, 0.55), 30, 0.6, 0.2))
    link(cf, cP); cf.parent = log
lpiv = bpy.data.objects.new("LogPivot", None); cP.objects.link(lpiv); lpiv.location = (80 + 1.8, 0, 0.0)   # thin end stays on the ground
log.location = (80, 0, 0.19); bpy.context.view_layer.update()
log.parent = lpiv; log.matrix_parent_inverse = lpiv.matrix_world.inverted()
# bench, hedges, trees, a lamp post for depth
m_wood = mat("BenchWood", (0.62, 0.38, 0.20), 0.55); m_iron = mat("Iron", (0.12, 0.14, 0.13), 0.4, metal=0.7)
for j in range(4): box("BenchSlat%d" % j, cP, (84.5, 4.3 + j * 0.12, 0.45), (1.8, 0.1, 0.04), m_wood, bevel=0.005)
for xx in (83.8, 85.2): box("BenchLeg%d" % xx, cP, (xx, 4.48, 0.22), (0.06, 0.45, 0.44), m_iron, bevel=0.005)
for i, (x, y) in enumerate(((74, 6), (77, 9), (84, 8), (88, 5), (73, -6), (89, -7), (80, 12))):
    shrub("ParkTree%d" % i, cP, (x, y, 3.0), (1.8, 1.8, 2.2), m_hedge)
    box("ParkTrunk%d" % i, cP, (x, y, 1.0), (0.28, 0.28, 2.0), mat("Trunk", (0.35, 0.24, 0.16), 0.8), bevel=0.02)
for i in range(6): shrub("ParkHedge%d" % i, cP, (72 + i * 3.2, 7.0, 0.45), (1.6, 0.6, 0.6), m_hedge)
# ---- background dressing behind the man (B4 cameras look toward -Y): second path, benches, lamps, tree rows, hedges, houses
box("ParkPath2", cP, (80, -4.2, 0.015), (34, 1.6, 0.03), m_conc, bevel=0.005)
m_leaf2 = noise_mat("Leaf2", (0.18, 0.45, 0.14), (0.35, 0.62, 0.20), 5.0, 0.8, 0.4)
m_leaf3 = noise_mat("Leaf3", (0.30, 0.52, 0.12), (0.48, 0.70, 0.22), 5.0, 0.8, 0.4)
for i, (x, y, h) in enumerate(((72.5, -6.5, 2.8), (75.8, -7.8, 3.3), (78.6, -6.8, 2.6), (81.7, -8.2, 3.5), (84.6, -6.6, 2.9), (87.4, -7.9, 3.1),
                                (74.2, -11.5, 3.6), (79.9, -12.4, 3.9), (85.8, -11.7, 3.4), (70.5, -2.5, 3.0), (90.0, -2.0, 3.2))):
    shrub("BgParkTree%d" % i, cP, (x, y, h), (1.5 + 0.1 * (i % 3), 1.5, 1.9), m_leaf2 if i % 2 else m_leaf3)
    box("BgParkTrunk%d" % i, cP, (x, y, h / 2 - 0.3), (0.26, 0.26, h - 0.6), mat("Trunk", (0.35, 0.24, 0.16), 0.8), bevel=0.02)
for i in range(9): shrub("BgHedge%d" % i, cP, (70.5 + i * 2.6, -9.6, 0.5), (1.3, 0.55, 0.6), m_hedge)
for k, bx in enumerate((76.2, 83.6)):
    for j in range(4): box("Bench2_%d_%d" % (k, j), cP, (bx, -5.35 - j * 0.12, 0.45), (1.8, 0.1, 0.04), m_wood, bevel=0.005)
    for xx in (bx - 0.7, bx + 0.7): box("Bench2Leg_%d_%s" % (k, xx), cP, (xx, -5.53, 0.22), (0.06, 0.45, 0.44), m_iron, bevel=0.005)
    box("Bench2Back_%d" % k, cP, (bx, -5.75, 0.75), (1.8, 0.05, 0.3), m_wood, bevel=0.005)
for k, lx in enumerate((73.0, 80.0, 87.0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=3.2, location=(lx, -3.1, 1.6)); lpo = bpy.context.object; lpo.name = "LampPost%d" % k
    lpo.data.materials.append(m_iron); link(lpo, cP)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(lx, -3.1, 3.3)); lg = bpy.context.object; lg.name = "LampGlobe%d" % k
    lg.data.materials.append(mat("LampGlass", (0.97, 0.96, 0.9), 0.3)); link(lg, cP)
    for pq in lg.data.polygons: pq.use_smooth = True
for i, x in enumerate((70, 79, 88)):
    box("ParkHouse%d" % i, cP, (x, -20, 2.2), (7.0, 6, 4.4), mat("PHs%d" % i, [(0.95, 0.88, 0.72), (0.80, 0.88, 0.96), (0.96, 0.82, 0.80)][i], 0.6), bevel=0.02)
    box("ParkRoof%d" % i, cP, (x, -20, 4.55), (7.6, 6.4, 0.35), mat("Roof", (0.36, 0.30, 0.28), 0.8), bevel=0.03)
    for j in (-2, 0, 2):
        box("PHWin%d_%d" % (i, j), cP, (x + j, -16.98, 2.6), (1.0, 0.06, 1.0), mat("WinGlass", (0.35, 0.55, 0.75), 0.08, metal=0.2), bevel=0)


# ---- director v002 note: swap the park's blob trees for a real tree (Poly Haven CC0 tree_small_02, decimated, linked copies)
spots = []
for o in list(bpy.data.objects):
    if o.name.startswith(("ParkTree", "BgParkTree")):
        spots.append((o.location.x, o.location.y, o.scale.z)); bpy.data.objects.remove(o, do_unlink=True)
    elif o.name.startswith(("ParkTrunk", "BgParkTrunk")):
        bpy.data.objects.remove(o, do_unlink=True)
import glob
tf = glob.glob(A + "ph/tree_small_02/*.blend")[0]
with bpy.data.libraries.load(tf, link=False) as (fd, td): td.objects = list(fd.objects)
tobs = [o for o in td.objects if o and o.type == 'MESH' and not o.name.endswith('LOD0')]
for o in td.objects:
    if o and o not in tobs: bpy.data.objects.remove(o)
troot = bpy.data.objects.new("RealTreeSrc", None); cP.objects.link(troot)
for o in tobs:
    cP.objects.link(o)
    if o.parent is None or o.parent not in tobs:
        mw = o.matrix_world.copy(); o.parent = troot; o.matrix_world = mw
    if len(o.data.vertices) > 150000:
        dm = o.modifiers.new("Dec", 'DECIMATE'); dm.ratio = 60000.0 / len(o.data.vertices)
        dg_ = bpy.context.evaluated_depsgraph_get(); me2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg_))
        o.modifiers.remove(dm); old_me = o.data; o.data = me2; bpy.data.meshes.remove(old_me)
    print("TREE_MESH", o.name, len(o.data.vertices))
bpy.context.view_layer.update(); tmn, tmx = bounds(tobs); TH = tmx.z - tmn.z
print("TREE_SRC height", TH, "spots", len(spots))
def tree_copy(i, x, y, h):
    r2 = troot if i == 0 else bpy.data.objects.new("RealTree%d" % i, None)
    if i > 0:
        cP.objects.link(r2)
        for ch in troot.children:
            c2 = ch.copy(); cP.objects.link(c2); c2.parent = r2; c2.matrix_parent_inverse = ch.matrix_parent_inverse.copy()
    s_ = h / TH; r2.scale = (s_,) * 3; r2.rotation_euler.z = random.uniform(0, 6.3)
    r2.location = (x, y, -tmn.z * s_)
for i, (x, y, sz) in enumerate(spots):
    tree_copy(i, x, y, random.uniform(4.4, 6.0))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SETS_OK", OUT)
