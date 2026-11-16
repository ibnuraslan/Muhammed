# Set dressing (director P1 notes): textured truck cab, dressed ambulance, vet/kennel room and hospital room.
# exec'd by 02_build.py after the sets are built (uses its helpers and variables).
PHD = "/tmp/claude-0/-home-user-Muhammed/6d9df9f8-340e-5c72-a05a-162ae5e59d06/scratchpad/ph/"
PHD = os.environ.get("DSO_PH", PHD)

def tex_mat(name, tex, tint=(1, 1, 1), scale=1.0, rough=0.6, sat=1.0, bright=0.0, bump=0.3, metal=0.0):
    """Box-projected Poly Haven texture (object coords), tinted; clean look (low bump, roughness >= 0.35)."""
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    d = PHD + tex + "/textures/"
    files = os.listdir(d)
    dif = next(f for f in files if "_diff_" in f or "_albedo_" in f)
    ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(d + dif, check_existing=True)
    ti.projection = 'BOX'; ti.projection_blend = 0.3; nt.links.new(mp.outputs["Vector"], ti.inputs["Vector"])
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = sat; hs.inputs["Value"].default_value = 1.0 + bright
    nt.links.new(ti.outputs["Color"], hs.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    mx.inputs["B"].default_value = (*tint, 1); nt.links.new(hs.outputs["Color"], mx.inputs["A"]); nt.links.new(mx.outputs["Result"], pr.inputs["Base Color"])
    dsp = next((f for f in files if "_disp_" in f and f.endswith((".png", ".jpg"))), None)
    if dsp and bump > 0:
        di = nt.nodes.new("ShaderNodeTexImage"); di.image = bpy.data.images.load(d + dsp, check_existing=True); di.image.colorspace_settings.name = 'Non-Color'
        di.projection = 'BOX'; di.projection_blend = 0.3; nt.links.new(mp.outputs["Vector"], di.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.002
        nt.links.new(di.outputs["Color"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], pr.inputs["Normal"])
    pr.inputs["Roughness"].default_value = max(0.35, rough); pr.inputs["Metallic"].default_value = metal
    MATS[name] = m; return m

def setmat(o, m):
    o.data.materials.clear(); o.data.materials.append(m)

def remove(*names):
    for n in names:
        o = bpy.data.objects.get(n)
        if o: bpy.data.objects.remove(o, do_unlink=True)

# ================================================================== TRUCK CAB
leath = tex_mat("SeatLeather", "brown_leather", tint=(1.0, 0.86, 0.66), scale=3.0, rough=0.55, sat=0.0, bright=1.6, bump=0.25)
fabric = tex_mat("Headliner", "fabric_leather_02", tint=(0.95, 0.93, 0.90), scale=4.0, rough=0.85, sat=0.2, bright=0.4, bump=0.15)
plast = tex_mat("DashPlastic", "fabric_leather_02", tint=(0.30, 0.30, 0.31), scale=6.0, rough=0.6, sat=0.0, bright=-0.2, bump=0.12)
doorpl = tex_mat("DoorPlastic", "fabric_leather_02", tint=(0.55, 0.52, 0.48), scale=6.0, rough=0.6, sat=0.1, bright=0.0, bump=0.12)
rubber = tex_mat("FloorMat", "rubber_tiles", tint=(0.30, 0.30, 0.32), scale=2.0, rough=0.8, sat=0.0, bump=0.2)
chrome = mat("Chrome", (0.85, 0.86, 0.88), 0.2, metal=1.0)
blackp = mat("BlackPlastic", (0.04, 0.04, 0.045), 0.45)
paint = mat("TruckPaint", (0.55, 0.05, 0.05), 0.25)
belt_m = mat("BeltWebbing", (0.10, 0.10, 0.11), 0.7)
gauge_m = mat("GaugeFace", (0.92, 0.93, 0.95), 0.4, emit=(0.9, 0.95, 1.0), ew=0.6)
needle_m = mat("Needle", (0.95, 0.25, 0.05), 0.4, emit=(1.0, 0.3, 0.05), ew=1.0)

remove("Wheel", "WheelHub", "WheelColumn", "Spoke0", "Spoke120", "Spoke240", "Dashboard", "DashTop",
       "BenchCushion0", "BenchCushion1", "BenchBack0", "BenchBack1", "BenchBase")
for n in ("FloorCab",): setmat(bpy.data.objects[n], rubber)
setmat(bpy.data.objects["Roof"], fabric)
setmat(bpy.data.objects["RearWall"], doorpl)
for sx in (-1, 1):
    setmat(bpy.data.objects[f"DoorLow{sx}"], doorpl); setmat(bpy.data.objects[f"DoorArm{sx}"], leath)
    for y in (-1.45, 0.15, 1.12): setmat(bpy.data.objects[f"Pillar{sx}_{y}"], doorpl)
for nm in ("SeatDriver", "SeatPass"): setmat(bpy.data.objects[nm], leath)
# rear bench: tufted panels (3 per cushion, 3 per back) with piping, two headrests, base
for i, x in enumerate((-0.37, 0.37)):
    for k, dx in enumerate((-0.235, 0.0, 0.235)):
        rbox(f"BenchPad{i}{k}", (0.225, 0.54, 0.13), (x + dx, 0.73, BZ - 0.065), leath, CT, 0.045)
        rbox(f"BenchBackPad{i}{k}", (0.225, 0.13, 0.60), (x + dx, 1.04, BZ + 0.29), leath, CT, 0.045, rot=(R_(-12), 0, 0))
    rbox(f"BenchPipe{i}", (0.72, 0.03, 0.03), (x, 0.46, BZ - 0.01), leath, CT, 0.012)
    hr = rbox(f"BenchHeadrest{i}", (0.26, 0.10, 0.20), (x, 1.13, BZ + 0.70), leath, CT, 0.05, rot=(R_(-12), 0, 0))
    for sx2 in (-1, 1): cyl(f"HRPost{i}{sx2}", 0.007, 0.08, (x + 0.07 * sx2, 1.12, BZ + 0.58), chrome, CT)
rbox("BenchBase", (1.5, 0.5, BZ - 0.14), (0, 0.75, (BZ - 0.14) / 2), doorpl, CT, 0.02)
# seat belts: webbing from the B/C pillars down across each back, buckles on the cushion
def belt(name, p0, p1, w=0.045):
    v = Vector(p1) - Vector(p0); L = v.length
    o = rbox(name, (w, 0.004, L), (Vector(p0) + Vector(p1)) / 2, belt_m, CT, 0.0)
    o.rotation_euler = v.to_track_quat('Z', 'Y').to_euler(); return o
belt("BeltRearL", (0.80, 1.10, 1.22), (0.47, 0.98, BZ + 0.03))
belt("BeltRearR", (-0.80, 1.10, 1.22), (-0.47, 0.98, BZ + 0.03))
for x in (0.47, -0.47, 0.20, -0.20):
    rbox(f"Buckle{x}", (0.03, 0.02, 0.06), (x, 0.92, BZ + 0.02), blackp, CT, 0.006)
belt("BeltDrv", (0.80, 0.14, 1.35), (0.80, 0.14, 0.45), w=0.045)
belt("BeltPas", (-0.80, 0.14, 1.35), (-0.80, 0.14, 0.45), w=0.045)
# door panels: inset upholstery, handle, speaker, switch pod, map pocket
for sx in (-1, 1):
    for y0, y1 in ((-1.25, 0.05), (0.25, 1.05)):
        yc = (y0 + y1) / 2; L = y1 - y0
        rbox(f"DoorInset{sx}{y0}", (0.015, L - 0.12, 0.26), (0.815 * sx, yc, 0.52), leath, CT, 0.01)
        rbox(f"DoorPocket{sx}{y0}", (0.05, L - 0.25, 0.10), (0.80 * sx, yc, 0.20), blackp, CT, 0.015)
        cyl(f"Speaker{sx}{y0}", 0.065, 0.012, (0.812 * sx, y0 + 0.16, 0.24), mat("SpeakerGrille", (0.08, 0.08, 0.09), 0.8), CT, rot=(0, R_(90), 0))
        rbox(f"DoorHandle{sx}{y0}", (0.02, 0.10, 0.03), (0.81 * sx, y1 - 0.18, 0.80), chrome, CT, 0.008)
        rbox(f"SwitchPod{sx}{y0}", (0.05, 0.12, 0.025), (0.79 * sx, y0 + 0.35, 0.745), blackp, CT, 0.008)
    # window frames (black rubber seals) around the openings
    for y0, y1 in ((-1.40, 0.10), (0.20, 1.07)):
        rbox(f"WinSealTop{sx}{y0}", (0.05, y1 - y0, 0.03), (0.84 * sx, (y0 + y1) / 2, 1.50), blackp, CT, 0.008)
        rbox(f"WinSealBot{sx}{y0}", (0.06, y1 - y0, 0.03), (0.84 * sx, (y0 + y1) / 2, 0.84), blackp, CT, 0.008)
# dashboard: shaped dash, instrument hood, gauges, center stack with vents, glovebox, A-pillars, mirror
rbox("DashMain", (1.66, 0.50, 0.30), (0, -1.38, 0.78), plast, CT, 0.08)
rbox("DashTop", (1.66, 0.42, 0.10), (0, -1.45, 0.97), plast, CT, 0.05, rot=(R_(8), 0, 0))
rbox("GaugeHood", (0.46, 0.20, 0.10), (DRV.x, -1.20, 1.00), plast, CT, 0.04, rot=(R_(-10), 0, 0))
for k, gx in enumerate((-0.10, 0.10)):
    g = cyl(f"Gauge{k}", 0.065, 0.01, (DRV.x + gx, -1.115, 0.95), gauge_m, CT, rot=(R_(80), 0, 0))
    cyl(f"GaugeRim{k}", 0.072, 0.012, (DRV.x + gx, -1.118, 0.95), chrome, CT, rot=(R_(80), 0, 0))
    nd = rbox(f"GaugeNeedle{k}", (0.006, 0.004, 0.05), (DRV.x + gx + 0.012, -1.108, 0.965), needle_m, CT, 0.0, rot=(R_(80), 0, R_(-35 + 60 * k)))
rbox("CenterStack", (0.36, 0.08, 0.32), (0, -1.12, 0.78), blackp, CT, 0.02)
for k in range(5):
    rbox(f"VentSlat{k}", (0.30, 0.012, 0.008), (0, -1.08, 0.88 + k * 0.012), chrome, CT, 0.0)
rbox("Radio", (0.22, 0.012, 0.07), (0, -1.075, 0.72), mat("RadioGlass", (0.05, 0.08, 0.1), 0.2, emit=(0.2, 0.5, 0.8), ew=0.4), CT, 0.0)
for k, kx in enumerate((-0.14, 0.14)):
    cyl(f"Knob{k}", 0.018, 0.02, (kx, -1.07, 0.72), chrome, CT, rot=(R_(90), 0, 0))
rbox("Glovebox", (0.45, 0.012, 0.16), (-DRV.x, -1.125, 0.76), plast, CT, 0.01)
rbox("GloveHandle", (0.10, 0.02, 0.02), (-DRV.x, -1.115, 0.80), chrome, CT, 0.005)
rbox("Console", (0.20, 0.70, 0.36), (0, -0.55, 0.18), plast, CT, 0.04)
rbox("ConsoleLid", (0.22, 0.40, 0.05), (0, -0.40, 0.385), leath, CT, 0.02)
for k in range(2): cyl(f"Cupholder{k}", 0.04, 0.02, (0, -0.78 + k * 0.10, 0.365), blackp, CT)
rbox("GearBoot", (0.10, 0.10, 0.06), (0, -0.93, 0.40), blackp, CT, 0.02)
cyl("GearStick", 0.012, 0.18, (0, -0.93, 0.50), chrome, CT)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(0, -0.93, 0.60)); gk = bpy.context.active_object; gk.name = "GearKnob"; gk.data.materials.append(blackp); move_to(gk, CT)
for sx in (-1, 1):
    ap = rbox(f"APillar{sx}", (0.08, 0.10, 0.70), (0.80 * sx, -1.52, 1.22), doorpl, CT, 0.02, rot=(R_(-35), 0, 0))
rbox("WindshieldTop", (1.66, 0.10, 0.06), (0, -1.70, 1.52), doorpl, CT, 0.02)
rbox("MirrorArm", (0.02, 0.02, 0.08), (0, -1.55, 1.50), blackp, CT, 0.005)
rbox("Mirror", (0.24, 0.03, 0.07), (0, -1.55, 1.43), blackp, CT, 0.015)
rbox("MirrorGlass", (0.22, 0.004, 0.055), (0, -1.535, 1.43), chrome, CT, 0.0)
cyl("DomeLight", 0.06, 0.015, (0, -0.2, 1.53), mat("DomeLens", (1, 1, 0.95), 0.3, emit=(1, 0.98, 0.9), ew=2.0), CT)
for sx in (-1, 1):
    for y in (-0.4, 0.75): rbox(f"GrabHandle{sx}{y}", (0.03, 0.22, 0.03), (0.78 * sx, y, 1.47), blackp, CT, 0.01)
# real steering wheel model on its column
SW = dup(bpy.data.objects["SteeringWheel"], "SteerWheel", (DRV.x, -1.02, 1.0), (R_(-25), 0, 0), (0.95, 0.95, 0.95), CT, linked=False)
setmat(SW, blackp)
cyl("SteerColumn", 0.04, 0.38, (DRV.x, -1.18, 0.93), blackp, CT, rot=(R_(65), 0, 0))
# pickup cues outside: red hood through the windshield, the bed through the rear window
rbox("Hood", (1.75, 1.6, 0.10), (0, -2.55, 0.95), paint, CT, 0.12, rot=(R_(4), 0, 0))
rbox("Fender", (1.85, 1.6, 0.40), (0, -2.55, 0.72), paint, CT, 0.10)
for sx in (-1, 1):
    rbox(f"BedSide{sx}", (0.10, 2.0, 0.55), (0.85 * sx, 2.35, 0.75), paint, CT, 0.03)
    rbox(f"BedRail{sx}", (0.14, 2.0, 0.04), (0.85 * sx, 2.35, 1.03), blackp, CT, 0.01)
rbox("BedFloor", (1.6, 2.0, 0.04), (0, 2.35, 0.45), tex_mat("BedLiner", "rubber_tiles", tint=(0.18, 0.18, 0.19), scale=3, rough=0.8, sat=0, bump=0.2), CT, 0.01)
rbox("Tailgate", (1.75, 0.08, 0.58), (0, 3.36, 0.74), paint, CT, 0.02)
rbox("CabBack", (1.75, 0.06, 0.70), (0, 1.22, 0.90), paint, CT, 0.02)
# rear window in the rear wall: cut the rear wall into a frame around an opening
remove("RearWall")
rbox("RearWallLow", (1.7, 0.06, 1.0), (0, 1.17, 0.50), doorpl, CT, 0.01)
rbox("RearWallTop", (1.7, 0.06, 0.12), (0, 1.17, 1.50), doorpl, CT, 0.01)
for sx in (-1, 1): rbox(f"RearWallSide{sx}", (0.35, 0.06, 0.50), (0.68 * sx, 1.17, 1.20), doorpl, CT, 0.01)
remove("CabBack")
# road under and around the truck
road_m = tex_mat("RoadTex", "asphalt_02", tint=(0.55, 0.56, 0.60), scale=0.5, rough=0.7, sat=0.3, bright=0.1, bump=0.2)
plane("TruckRoad", (7.0, 80), (0, 0, -0.44), road_m, CT)
for k in range(-12, 13): plane(f"TruckRoadDash{k}", (0.12, 1.6), (-2.6, k * 3.2, -0.435), line_m, CT)
for i in range(30):
    side = 1 if i % 2 else -1
    src = PLANTS[random.choice(["PH_fir_tree_01_a_LOD2", "PH_fir_tree_01_b_LOD2", "PH_fir_tree_01_c_LOD2"])]
    dup(src, f"TruckFirB{i}", (side * (6 + random.random() * 9), -30 + i * 2.1, -0.45), (0, 0, random.random() * 6), 0.7 + random.random() * 0.3, CT)
for i in range(16):
    side = 1 if i % 2 else -1
    src = PLANTS[random.choice(["PH_shrub_02_a_LOD1", "PH_shrub_02_c_LOD1", "PH_fern_02_b"])]
    dup(src, f"TruckShrub{i}", (side * (4.2 + random.random() * 2), -16 + i * 2.2, -0.45), (0, 0, random.random() * 6), 1.0, CT)

# ================================================================== AMBULANCE INTERIOR
amb_wall = tex_mat("AmbWallTex", "leather_white", tint=(0.95, 0.97, 0.98), scale=2.0, rough=0.45, sat=0.2, bright=0.2, bump=0.08)
for sx in (-1, 1): setmat(bpy.data.objects[f"AmbWall{sx}"], amb_wall)
setmat(bpy.data.objects["AmbFront"], amb_wall); setmat(bpy.data.objects["AmbRoof"], amb_wall)
setmat(bpy.data.objects["AmbFloor"], tex_mat("AmbFloorTex", "rubber_tiles", tint=(0.45, 0.52, 0.58), scale=2.5, rough=0.6, sat=0.3, bump=0.15))
# wall panel seams + grab rail
for sx in (-1, 1):
    for k in range(4): rbox(f"AmbSeam{sx}{k}", (0.004, 0.006, 1.2), (0.948 * sx, -1.4 + k * 0.9, 0.75), mat("Seam", (0.6, 0.62, 0.65), 0.5), CI, 0.0)
cyl("AmbGrabRail", 0.016, 2.8, IX + Vector((0.35, 0, 1.80)), steel, CI, rot=(R_(90), 0, 0))
for y in (-1.2, 0, 1.2): cyl(f"AmbRailPost{y}", 0.01, 0.10, IX + Vector((0.35, y, 1.86)), steel, CI)
# glass-front cabinets with supplies (coloured boxes, no text) replace the plain boxes on both walls
for sx in (-1, 1):
    for k in range(3):
        remove(f"AmbCab{sx}_{k}")
        cx = IX + Vector((0.80 * sx, -1.1 + k * 0.95, 1.52))
        rbox(f"AmbCabBody{sx}{k}", (0.30, 0.88, 0.40), cx, cab_m, CI, 0.015)
        rbox(f"AmbCabGlass{sx}{k}", (0.006, 0.82, 0.34), cx + Vector((-0.152 * sx, 0, 0)), mat("CabGlass", (0.85, 0.92, 0.95), 0.1, alpha=0.25), CI, 0.0)
        rbox(f"AmbCabHandle{sx}{k}", (0.02, 0.10, 0.015), cx + Vector((-0.162 * sx, 0.30, -0.13)), chrome, CI, 0.004)
        for j in range(5):
            col = random.choice([(0.9, 0.3, 0.25), (0.25, 0.5, 0.9), (0.95, 0.8, 0.3), (0.3, 0.7, 0.45), (0.95, 0.95, 0.95)])
            rbox(f"Supply{sx}{k}{j}", (0.12, 0.13, 0.10 + random.random() * 0.08), cx + Vector((0.0, -0.33 + j * 0.165, -0.10)), mat(f"Sup{col}", col, 0.5), CI, 0.008)
# stretcher dressing: white sheet, pillow, two straps with buckles, side rails
sheet = tex_mat("SheetWhite", "fabric_leather_02", tint=(1.05, 1.05, 1.06), scale=5, rough=0.8, sat=0.0, bright=0.6, bump=0.1)
rbox("StretcherSheet", (0.60, 1.86, 0.035), IX + Vector((0.30, 0.0, STR_Z + 0.012)), sheet, CI, 0.015)
rbox("StretcherPillow", (0.45, 0.30, 0.10), IX + Vector((0.30, -0.78, STR_Z + 0.06)), sheet, CI, 0.045)
strap_m = mat("StrapOrange", (0.95, 0.45, 0.08), 0.6)
for k, yy in enumerate((-0.45, 0.62)):
    rbox(f"Strap{k}", (0.62, 0.05, 0.012), IX + Vector((0.30, yy, STR_Z + 0.033)), strap_m, CI, 0.004)
    rbox(f"StrapBuckle{k}", (0.06, 0.06, 0.018), IX + Vector((0.08, yy, STR_Z + 0.036)), chrome, CI, 0.004)
for sx in (0.0,):          # far rail only: the near rail is down (he sits on that edge)
    cyl(f"StrRail{sx}", 0.012, 1.4, IX + Vector((sx, 0.0, STR_Z + 0.10)), steel, CI, rot=(R_(90), 0, 0))
# defibrillator, IV pole + bag, jump bag
rbox("Defib", (0.22, 0.30, 0.26), IX + Vector((-0.80, 0.55, 0.55)), mat("DefibOrange", (0.95, 0.5, 0.1), 0.45), CI, 0.03)
rbox("DefibScreen", (0.005, 0.18, 0.10), IX + Vector((-0.687, 0.55, 0.60)), mat("DefibScreen", (0.05, 0.2, 0.15), 0.3, emit=(0.2, 0.9, 0.5), ew=1.0), CI, 0.0)
rbox("DefibShelf", (0.30, 0.40, 0.03), IX + Vector((-0.80, 0.55, 0.40)), steel, CI, 0.005)
cyl("AmbIVPole", 0.012, 0.9, IX + Vector((0.62, -0.95, 1.45)), steel, CI)
rbox("AmbIVBag", (0.10, 0.03, 0.17), IX + Vector((0.62, -0.95, 1.15)), mat("IVBag", (0.9, 0.95, 1.0), 0.2, alpha=0.6), CI, 0.02)
rbox("JumpBag", (0.45, 0.28, 0.25), IX + Vector((-0.70, -1.30, 0.125)), mat("JumpBagRed", (0.75, 0.08, 0.08), 0.6), CI, 0.06)
cyl("O2Cap", 0.03, 0.06, IX + Vector((-0.85, -1.55, 1.0)), chrome, CI)

# ================================================================== KENNEL / ANIMAL-CONTROL ROOM
k_wall = tex_mat("KennelWallTex", "painted_plaster_wall", tint=(0.88, 0.95, 0.93), scale=1.0, rough=0.6, sat=0.3, bright=0.25, bump=0.15)
k_floor = tex_mat("KennelFloorTex", "floor_tiles_06", tint=(0.85, 0.87, 0.88), scale=1.0, rough=0.5, sat=0.4, bright=0.1, bump=0.15)
setmat(bpy.data.objects["KWall"], k_wall); setmat(bpy.data.objects["KFloor"], k_floor)
rbox("KWallSide", (0.1, 8, 3.5), KX + Vector((-2.4, -1.0, 1.75)), k_wall, CK, 0.0)
rbox("KWallTiles", (8, 0.02, 1.0), KX + Vector((0, 1.545, 0.5)), tex_mat("KTiles", "floor_tiles_06", tint=(0.7, 0.85, 0.9), scale=1.5, rough=0.4, sat=0.6, bright=0.2, bump=0.1), CK, 0.0)
# a row of steel kennel doors along the back wall (bars), left of the table
for k in range(3):
    kx = KX.x - 2.1 + k * 0.62 if False else -2.1 + k * 0.62
    base = KX + Vector((kx, 1.50, 0))
    rbox(f"KDoorFrame{k}", (0.58, 0.04, 0.04), base + Vector((0, 0, 1.30)), steel, CK, 0.005)
    rbox(f"KDoorFrameB{k}", (0.58, 0.04, 0.04), base + Vector((0, 0, 0.10)), steel, CK, 0.005)
    for j in range(9): cyl(f"KBar{k}{j}", 0.008, 1.2, base + Vector((-0.26 + j * 0.065, 0, 0.70)), steel, CK)
    rbox(f"KDoorLatch{k}", (0.05, 0.03, 0.08), base + Vector((0.24, -0.03, 0.75)), chrome, CK, 0.005)
    rbox(f"KDoorDark{k}", (0.58, 0.02, 1.25), base + Vector((0, 0.06, 0.70)), mat("KennelInside", (0.55, 0.60, 0.62), 0.7), CK, 0.0)
# shelves with supplies and the glass cabinet on the right
SC = dup(bpy.data.objects["StorageCab"], "KStorageCab", KX + Vector((1.75, 1.20, 0)), (0, 0, R_(180)), 1.0, CK, linked=False)
GCk = dup(bpy.data.objects["GlassCab"], "KGlassCab", KX + Vector((2.85, 1.20, 0)), (0, 0, R_(180)), 1.0, CK, linked=False)
rbox("KWindowFrame", (1.3, 0.06, 0.9), KX + Vector((0.4, 1.56, 2.05)), mat("WinFrame", (0.95, 0.95, 0.95), 0.4), CK, 0.01)
rbox("KWindowSky", (1.2, 0.02, 0.8), KX + Vector((0.4, 1.53, 2.05)), mat("WinSky", (0.6, 0.85, 1.0), 0.2, emit=(0.6, 0.85, 1.0), ew=1.2), CK, 0.0)
rbox("KWindowSill", (1.4, 0.15, 0.04), KX + Vector((0.4, 1.48, 1.58)), mat("WinFrame", (0.95, 0.95, 0.95), 0.4), CK, 0.01)
rbox("KLeashHook", (0.3, 0.04, 0.04), KX + Vector((-1.1, 1.53, 1.6)), steel, CK, 0.005)
for k in range(3): cyl(f"KLeash{k}", 0.008, 0.45, KX + Vector((-1.2 + k * 0.1, 1.51, 1.38)), mat(f"Leash{k}", [(0.8, 0.1, 0.1), (0.1, 0.3, 0.8), (0.1, 0.6, 0.3)][k], 0.5), CK)
cyl("KBowl", 0.10, 0.05, KX + Vector((-0.9, 0.6, 0.025)), steel, CK, verts=32)
rbox("KTableShelf", (1.9, 0.8, 0.03), KX + Vector((0.2, 0.2, 0.25)), steel, CK, 0.005)
rbox("KTowels", (0.4, 0.3, 0.12), KX + Vector((-0.4, 0.2, 0.33)), mat("TowelBlue", (0.4, 0.6, 0.85), 0.9), CK, 0.04)

# ================================================================== HOSPITAL ROOM
h_wall = tex_mat("HospWallTex", "painted_plaster_wall", tint=(0.85, 0.93, 0.96), scale=1.0, rough=0.6, sat=0.3, bright=0.25, bump=0.12)
setmat(bpy.data.objects["HWallBack"], h_wall); setmat(bpy.data.objects["HWallSide"], h_wall)
setmat(bpy.data.objects["HFloor"], tex_mat("HospFloorTex", "floor_tiles_06", tint=(0.9, 0.9, 0.88), scale=1.0, rough=0.45, sat=0.3, bright=0.15, bump=0.12))
remove("HWindow")
rbox("HWinFrame", (0.08, 1.3, 1.1), HX + Vector((-1.57, 0.2, 1.6)), mat("WinFrame", (0.95, 0.95, 0.95), 0.4), CH, 0.01)
rbox("HWinView", (0.02, 1.2, 1.0), HX + Vector((-1.53, 0.2, 1.6)), mat("WinSky", (0.6, 0.85, 1.0), 0.2, emit=(0.6, 0.85, 1.0), ew=1.2), CH, 0.0)
rbox("HWinMullion", (0.03, 0.04, 1.0), HX + Vector((-1.52, 0.2, 1.6)), mat("WinFrame", (0.95, 0.95, 0.95), 0.4), CH, 0.0)
curt = tex_mat("Curtain", "fabric_leather_02", tint=(0.55, 0.78, 0.80), scale=4, rough=0.85, sat=0.4, bright=0.3, bump=0.2)
for k in range(7):
    rbox(f"Curtain{k}", (0.06, 0.16, 2.1), HX + Vector((-1.45, 0.95 + k * 0.13, 1.25)), curt, CH, 0.03, rot=(0, 0, R_(25 if k % 2 else -25)))
rbox("BedHeadPanel", (2.2, 0.06, 0.35), HX + Vector((0, 1.53, 1.45)), mat("HeadPanel", (0.80, 0.84, 0.86), 0.4), CH, 0.02)
for k in range(3): cyl(f"Outlet{k}", 0.03, 0.02, HX + Vector((-0.4 + k * 0.4, 1.50, 1.45)), mat(f"Outlet{k}", [(0.1, 0.7, 0.3), (0.9, 0.9, 0.9), (0.2, 0.4, 0.9)][k], 0.4), CH, rot=(R_(90), 0, 0))
rbox("HMonitor", (0.40, 0.05, 0.28), HX + Vector((0.95, 1.45, 1.75)), blackp, CH, 0.02)
rbox("HMonitorScreen", (0.34, 0.005, 0.22), HX + Vector((0.95, 1.42, 1.75)), mat("ScreenGreen", (0.05, 0.25, 0.2), 0.3, emit=(0.1, 0.8, 0.5), ew=1.5), CH, 0.0)
GCh = dup(bpy.data.objects["GlassCab"], "HGlassCab", HX + Vector((1.6, 1.20, 0)), (0, 0, R_(180)), 1.0, CH, linked=False)
rbox("HBedTable", (0.45, 0.40, 0.04), HX + Vector((-0.85, 0.9, 0.80)), mat("Laminate", (0.75, 0.62, 0.45), 0.5), CH, 0.01)
cyl("HBedTableLeg", 0.02, 0.78, HX + Vector((-0.85, 0.9, 0.40)), steel, CH)
cyl("HCup", 0.035, 0.10, HX + Vector((-0.80, 0.95, 0.87)), mat("CupWhite", (0.95, 0.95, 0.95), 0.4), CH)
rbox("HChairSeat", (0.48, 0.48, 0.08), HX + Vector((1.15, -0.6, 0.45)), mat("ChairBlue", (0.25, 0.45, 0.70), 0.5), CH, 0.03)
rbox("HChairBack", (0.48, 0.08, 0.50), HX + Vector((1.15, -0.38, 0.75)), mat("ChairBlue", (0.25, 0.45, 0.70), 0.5), CH, 0.03)
for sx in (-1, 1):
    for sy in (-1, 1): cyl(f"HChairLeg{sx}{sy}", 0.015, 0.42, HX + Vector((1.15 + 0.2 * sx, -0.6 + 0.2 * sy, 0.21)), steel, CH)
print("DRESS done")
