# exec'd from 02_sets.py (shares its namespace): street props + all other sets
# ------------------------------------------------------------------ street props
def parts_by(ms, keys):
    return [o for o in ms if any(k in o.name for k in keys)]

# trash can (lid separate, handle on top)
ms = import_glb("trashcan"); normalize(ms, 0.95)
_lid = [o for o in ms if o.name.split(".")[0] in ("Object_6", "Object_8", "Object_10", "Object_12", "Object_14", "Object_16")]
_can = [o for o in ms if o not in _lid]
lid = join(_lid, "TrashLid"); can = join(_can, "TrashCan")
for o in (can, lid): link(o, STREET)
m_can = mat("GalvSteel", (0.62, 0.64, 0.66), 0.35, metal=0.9)
for o in (can, lid): o.data.materials.clear(); o.data.materials.append(m_can)
TRASH_POS = Vector((-5.55, 23.0, 0.12))
can.location = TRASH_POS; set_origin(lid, Vector((0, 0, 0.84))); lid.location = TRASH_POS + Vector((0, 0, 0.84))
lid.parent = None

# bicycle (kid size): frame + wheels + crank as separate parts under an empty
ms = import_glb("bike"); k_bike = normalize(ms, 0.66, center=False, ground=False)   # 0.6 scale of the 1.1 m adult frame
BIKE = bpy.data.objects.new("Bike", None); STREET.objects.link(BIKE)
_g = {"Bike_wheelB": parts_by(ms, ("wheel_back", "needles_back", "wheel_origin_back")), "Bike_wheelF": parts_by(ms, ("wheel_forward", "needles_forward", "wheel_origin_forward")),
      "Bike_crank": parts_by(ms, ("pedals", "gear_main"))}
_g["Bike_frame"] = [o for o in ms if not any(o in v for v in _g.values())]
_piv = {"Bike_wheelB": (-0.58, 0, 0.38), "Bike_wheelF": (0.73, 0, 0.38), "Bike_crank": (0.0, 0, 0.30), "Bike_frame": (0, 0, 0)}
BP = {}
for nm_, objs_ in _g.items():
    o = join(objs_, nm_); link(o, STREET); set_origin(o, Vector(_piv[nm_]) * k_bike); o.parent = BIKE; BP[nm_] = o
WB, WF, CR, FR = BP["Bike_wheelB"], BP["Bike_wheelF"], BP["Bike_crank"], BP["Bike_frame"]
BIKE["k"] = k_bike

# moving box (plain cardboard) + box truck with the DA KRAS FILMS logo on the roll-up door
ms = import_glb("box"); normalize(ms, 0.45); MBOX = join(ms, "MovingBox"); link(MBOX, STREET)
ms = import_glb("trkB"); normalize(ms, 6.8, axis='max'); TRUCK = join(ms, "BoxTruck"); link(TRUCK, STREET)

# ------------------------------------------------------------------ KITCHEN (300,0,0)
KX = Vector((300, 0, 0)); KIT = coll("SET_kitchen")
M_wallk = mat("KitchenWall", (0.93, 0.9, 0.84), 0.8)
M_counter = mat("CounterTop", (0.88, 0.88, 0.86), 0.25)
M_cab = mat("CabinetWhite", (0.95, 0.95, 0.93), 0.45)
plane("K_floor", (8, 7), KX + Vector((0, 0, 0)), M_floorwood, KIT)
box("K_wallB", (8, 0.12, 2.9), KX + Vector((0, 3.1, 1.45)), M_wallk, KIT)
box("K_wallL", (0.12, 7, 2.9), KX + Vector((-4, 0, 1.45)), M_wallk, KIT)
box("K_wallR", (0.12, 7, 2.9), KX + Vector((4, 0, 1.45)), M_wallk, KIT)
box("K_wallF", (8, 0.12, 2.9), KX + Vector((0, -3.6, 1.45)), M_wallk, KIT)
box("K_ceil", (8, 7.2, 0.1), KX + Vector((0, 0, 2.95)), M_white, KIT)
ms = import_glb("kitchen"); normalize(ms, 2.45); KM = join(ms, "KitchenUnits"); link(KM, KIT)
KM.location = KX + Vector((0, 3.04 - (bbox([KM])[1].y), 0))
box("Island_base", (2.3, 0.9, 0.86), KX + Vector((0, 0.35, 0.43)), M_cab, KIT, bevel=0.01)
box("Island_top", (2.45, 1.05, 0.045), KX + Vector((0, 0.35, 0.882)), M_counter, KIT, bevel=0.008)
for i, x in enumerate((-0.6, 0.6)):
    cyl("Pendant.%d" % i, 0.16, 0.18, KX + Vector((x, 0.35, 2.2)), mat("PendantShade", (0.95, 0.95, 0.9), 0.4, emit=(1, 0.95, 0.85), emit_s=6), KIT)
    cyl("PendantCord.%d" % i, 0.006, 0.66, KX + Vector((x, 0.35, 2.62)), mat("Cord", (0.1, 0.1, 0.1), 0.6), KIT)
win = box("K_window", (0.03, 1.6, 1.1), KX + Vector((-3.93, -0.8, 1.6)), mat("WindowDay", (0.8, 0.9, 1.0), 0.5, emit=(0.85, 0.93, 1.0), emit_s=3.0), KIT)
box("K_winframe", (0.06, 1.72, 1.22), KX + Vector((-3.96, -0.8, 1.6)), M_white, KIT)
box("K_window2", (0.95, 0.03, 1.0), KX + Vector((2.3, 3.03, 1.55)), bpy.data.materials["WindowDay"], KIT)
box("K_winframe2", (1.07, 0.05, 1.12), KX + Vector((2.3, 3.05, 1.55)), M_white, KIT)
box("K_sill2", (1.15, 0.12, 0.04), KX + Vector((2.3, 3.0, 1.03)), M_white, KIT)
a = bpy.data.objects.new("K_light", bpy.data.lights.new("K_light", 'AREA')); KIT.objects.link(a)
a.data.size = 3.5; a.data.size_y = 2.5; a.data.shape = 'RECTANGLE'; a.data.energy = 650; a.location = KX + Vector((0, -0.3, 2.85))
a2 = bpy.data.objects.new("K_fill", bpy.data.lights.new("K_fill", 'AREA')); KIT.objects.link(a2)
a2.data.size = 1.5; a2.data.energy = 120; a2.location = KX + Vector((-3.6, -0.8, 1.6)); a2.rotation_euler = (0, R_(-90), 0)
ms = import_glb("glass"); normalize(ms, 0.15); GLASS = join(ms, "Glass"); link(GLASS, KIT)
GLASS.data.materials.clear(); GLASS.data.materials.append(mat("GlassClear", (0.95, 0.98, 1.0), 0.05))
gm = GLASS.data.materials[0].node_tree.nodes["Principled BSDF"]; gm.inputs["Transmission Weight"].default_value = 1.0; gm.inputs["IOR"].default_value = 1.45
WATER = cyl("GlassWater", 0.031, 0.09, (0, 0, 0.05), mat("WaterCloudy", (0.85, 0.9, 0.6), 0.1), KIT)
wm = WATER.data.materials[0].node_tree.nodes["Principled BSDF"]; wm.inputs["Transmission Weight"].default_value = 0.85; wm.inputs["IOR"].default_value = 1.33
WATER.parent = GLASS
GLASS.location = KX + Vector((0.35, 0.1, 0.905))

# ------------------------------------------------------------------ UNDERGROUND cut-away blocks (600,0,0) and (600,60,0)
def cut_soil_mat():
    m = bpy.data.materials.get("CutSoil")
    if m: return m
    m = pbr("CutSoil", "excavated_soil_wall", 0.25, tint=(0.95, 0.7, 0.5), coords="Object").copy(); m.name = "CutSoil"
    nt = m.node_tree; P = nt.nodes["Principled BSDF"]; src = P.inputs["Base Color"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord"); sz = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sz.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'; nt.links.new(nz.outputs["Fac"], ad.inputs[0]); ad.inputs[1].default_value = 1.2
    nt.links.new(sz.outputs["Z"], ad.inputs[2])
    rp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(ad.outputs[0], rp.inputs[0])
    cr = rp.color_ramp; cr.elements[0].position = 0.0; cr.elements[0].color = (0.75, 0.55, 0.38, 1); cr.elements[1].position = 1.0; cr.elements[1].color = (0.62, 0.42, 0.28, 1)
    e = cr.elements.new(0.45); e.color = (0.9, 0.7, 0.5, 1); e2 = cr.elements.new(0.8); e2.color = (0.5, 0.36, 0.25, 1)
    mr = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(sz.outputs["Z"], mr.inputs[0]); mr.inputs[1].default_value = 12.5; mr.inputs[2].default_value = 21.0   # object z: 0 bottom .. 5 top half
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
    nt.links.new(src, mx.inputs[6]); nt.links.new(rp.outputs[0], mx.inputs[7]); nt.links.new(mx.outputs[2], P.inputs["Base Color"])
    nt.links.new(sz.outputs["Z"], rp.inputs[0])
    return m
M_cut = cut_soil_mat()
M_rock = mat("CaveRock", (0.1, 0.075, 0.055), 0.9)

def soil_block(name, origin, c, pocket=True):
    o = box(name, (30, 14, 30), origin + Vector((0, 0, -15.0)), M_cut, c)
    set_origin(o, origin + Vector((0, 0, -30)))
    top = plane(name + "_lawn", (30, 14), origin + Vector((0, 0, 0.005)), M_lawn, c)
    edge = box(name + "_turf", (30.02, 14.02, 0.18), origin + Vector((0, 0, -0.09)), mat("TurfEdge", (0.18, 0.4, 0.08), 0.9), c)
    glow = []
    if pocket:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=1, location=origin + Vector((0, -7.2, -5.6)))
        cut = bpy.context.active_object; cut.name = name + "_pocketcutter"; cut.scale = (11, 6.5, 2.7); link(cut, LIB)
        tx = bpy.data.textures.new(name + "_ptex", 'CLOUDS'); tx.noise_scale = 3.0; tx.noise_depth = 0
        d = cut.modifiers.new("disp", 'DISPLACE'); d.texture = tx; d.strength = 0.9; d.texture_coords = 'GLOBAL'
        bpy.ops.object.shade_smooth()
        b = o.modifiers.new("pocket", 'BOOLEAN'); b.object = cut; b.operation = 'DIFFERENCE'; b.solver = 'EXACT'
        bpy.context.view_layer.objects.active = o
        o.data.materials.append(M_rock)     # carved surface gets the cave rock colour
        b.material_mode = 'TRANSFER'; cut.data.materials.append(M_rock)
        bpy.context.view_layer.update()
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], selected_editable_objects=[o]):
            bpy.ops.object.modifier_apply(modifier="pocket")
        ri = list(o.data.materials).index(M_rock)
        for p_ in o.data.polygons: p_.use_smooth = (p_.material_index == ri)
        sl = plane(name + "_sludge", (19, 6.0), origin + Vector((0, -4.0, -7.2)), M_tox, c, subdiv=40)
        tx2 = bpy.data.textures.new(name + "_stex", 'CLOUDS'); tx2.noise_scale = 1.2
        d2 = sl.modifiers.new("ripple", 'DISPLACE'); d2.texture = tx2; d2.strength = 0.15; d2.texture_coords = 'GLOBAL'
        glow.append(sl)
        for i in range(10):     # small glowing pockets in the cut face (embedded, flattened)
            x = random.uniform(-13, 13); z = random.uniform(-9.2, -1.8)
            if abs(x) < 10 and -9 < z < -3: continue
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=origin + Vector((x, -7.0, z)))
            g = bpy.context.active_object; g.name = name + "_glow.%d" % i; g.scale = (random.uniform(0.6, 1.6), 0.25, random.uniform(0.25, 0.5))
            g.data.materials.append(M_toxd); link(g, c); bpy.ops.object.shade_smooth(); glow.append(g)
    return o, glow

UX = Vector((600, 0, 0)); UND = coll("SET_under")
BLK, _ = soil_block("Under", UX, UND)
copy_obj(L_house0, "U_house0", UX + Vector((-7, 2.0, 0)), rz=180, c=UND).scale = (0.85, 0.85, 0.85)
copy_obj(L_house5, "U_house1", UX + Vector((8, 2.5, 0)), rz=180, c=UND).scale = (0.8, 0.8, 0.8)
for i, x in enumerate((-13, 0.5, 13.5)): copy_obj(L_tree, "U_tree.%d" % i, UX + Vector((x, 4.5, 0)), rz=i * 70, c=UND).scale = (0.7, 0.7, 0.7)
for i in range(12): copy_obj(L_fence, "U_fence.%d" % i, UX + Vector((-14 + i * 2.35, -6.2, 0.0)), rz=90, c=UND)
for i, (x, y, z, rx, rz_) in enumerate(((-5, -6.5, -7.25, 75, 10), (-2.2, -8.2, -7.1, 88, 50), (2.5, -5.5, -7.3, 20, 0), (5.5, -7.8, -7.0, 95, -30), (-7.5, -5.0, -7.2, 10, 80), (0.5, -4.0, -7.0, 70, 120))):
    d_ = copy_obj(L_drum, "U_drum.%d" % i, UX + Vector((x, y, z)), c=UND); d_.rotation_euler = (R_(rx), 0, R_(rz_))

# sky-blue gradient backdrop for the cut-away shots (camera rays only: it lights nothing)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=95, location=(600, 30, 0)); BD = bpy.context.active_object
BD.name = "Backdrop_under"; link(BD, UND); bpy.ops.object.shade_smooth()
mb = bpy.data.materials.new("SkyGradient"); mb.use_nodes = True; nt_ = mb.node_tree; nt_.nodes.clear()
o_ = nt_.nodes.new("ShaderNodeOutputMaterial"); em = nt_.nodes.new("ShaderNodeEmission"); tc_ = nt_.nodes.new("ShaderNodeTexCoord"); sx_ = nt_.nodes.new("ShaderNodeSeparateXYZ")
nt_.links.new(tc_.outputs["Object"], sx_.inputs[0]); rp_ = nt_.nodes.new("ShaderNodeValToRGB"); mr_ = nt_.nodes.new("ShaderNodeMapRange")
nt_.links.new(sx_.outputs["Z"], mr_.inputs[0]); mr_.inputs[1].default_value = -60; mr_.inputs[2].default_value = 90; nt_.links.new(mr_.outputs[0], rp_.inputs[0])
rp_.color_ramp.elements[0].color = (0.8, 0.93, 1.0, 1); rp_.color_ramp.elements[1].color = (0.08, 0.55, 0.92, 1)
nt_.links.new(rp_.outputs[0], em.inputs[0]); em.inputs[1].default_value = 1.0; nt_.links.new(em.outputs[0], o_.inputs[0])
BD.data.materials.append(mb)
for a_ in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"): setattr(BD, a_, False)
UX2 = Vector((600, 60, 0))
BLK2, _ = soil_block("Under2", UX2, UND)

def stud_house(name, origin, w=8.0, d=6.5, h=2.6, rz=0.0):
    """timber frame: sill + studs every 0.4 m + top plates per wall, plus gable trusses; returns [floor, wall panels..., roof]"""
    M_wood = mat("Lumber", (0.86, 0.68, 0.45), 0.6)
    panels = []
    plat = box(name + "_deck", (w, d, 0.2), (0, 0, 0.1), mat("Plywood", (0.8, 0.62, 0.4), 0.7)); panels.append(plat)
    for wi, (cx, cy, L, ax) in enumerate(((0, -d / 2 + 0.05, w, 'X'), (0, d / 2 - 0.05, w, 'X'), (-w / 2 + 0.05, 0, d, 'Y'), (w / 2 - 0.05, 0, d, 'Y'))):
        parts = []
        n = int(L / 0.4)
        for k in range(n + 1):
            t = -L / 2 + k * L / n
            p = (cx + (t if ax == 'X' else 0), cy + (t if ax == 'Y' else 0), 0.2 + h / 2)
            parts.append(box("st", (0.05 if ax == 'X' else 0.1, 0.1 if ax == 'X' else 0.05, h), p, M_wood))
        for zz in (0.225, 0.2 + h - 0.025, 0.2 + h + 0.025):
            parts.append(box("pl", (L if ax == 'X' else 0.1, 0.1 if ax == 'X' else L, 0.05), (cx, cy, zz), M_wood))
        pn = join(parts, name + "_wall%d" % wi); panels.append(pn)
    tr = []
    for k in range(int(w / 0.6) + 1):
        x = -w / 2 + k * w / int(w / 0.6)
        for sgn in (-1, 1):
            r = box("raf", (0.05, d / 2 * 1.2, 0.12), (x, sgn * d / 4, 0.2 + h + 0.95), M_wood)
            r.rotation_euler = (R_(-34 * sgn), 0, 0); tr.append(r)
        tr.append(box("tie", (0.05, d, 0.1), (x, 0, 0.2 + h + 0.06), M_wood))
    for o in tr:
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    panels.append(join(tr, name + "_roof"))
    root = bpy.data.objects.new(name, None); root.location = origin; root.rotation_euler = (0, 0, R_(rz))
    for p in panels:
        link(p, UND); p.parent = root
    UND.objects.link(root)
    return root, panels
FRAMES = []
for i, (x, y) in enumerate(((-8, 1.5), (7.5, 1.0))):
    r, pn = stud_house("Frame%d" % i, UX2 + Vector((x, y, 0)), rz=0)
    FRAMES.append((r, pn))

# ------------------------------------------------------------------ DUMP (900,0,0): dirt plain with a pit
DX = Vector((900, 0, 0)); DMP = coll("SET_dump")
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=150, y_segments=150, size=60)
for v in bm.verts:
    r = math.hypot(v.co.x, v.co.y); pit = 1.6 * (1 - smooth((r - 3.0) / 5.5))
    v.co.z = -pit + 0.08 * math.sin(v.co.x * 0.9) * math.cos(v.co.y * 0.7)
me = bpy.data.meshes.new("DumpGround"); bm.to_mesh(me); bm.free()
G = bpy.data.objects.new("DumpGround", me); DMP.objects.link(G); G.location = DX; G.data.materials.append(M_mud)
for p in G.data.polygons: p.use_smooth = True
bpy.ops.mesh.primitive_plane_add(size=1); bg_ = bpy.context.active_object
bg_.name = "DumpGround_far"; bg_.scale = (250, 250, 1); bg_.location = DX + Vector((0, 0, -0.05)); bg_.data.materials.append(M_mud); link(bg_, DMP)

ms = import_glb("dumptruck"); normalize(ms, 7.2, axis=1)
bed_src = [o for o in ms if "dump_truck_A" in o.name]; rest_src = [o for o in ms if o not in bed_src]
L_tbed = join(bed_src, "LIB_truckbed"); L_tcab = join(rest_src, "LIB_truckcab"); link(L_tbed, LIB); link(L_tcab, LIB)
mn, mx = bbox([L_tbed]); HINGE = Vector((0, mx.y - 0.1, mn.z + 0.08)); set_origin(L_tbed, HINGE)        # hinge at the rear bottom of the bed
M_blue = mat("TruckBlue", (0.08, 0.32, 0.75), 0.4, metal=0.2)
for o in (L_tbed, L_tcab):
    for i, m in enumerate(o.data.materials):
        if m and ("A_01" in m.name or "B_01" in m.name and "1" not in m.name.split("B_01")[-1]): pass
TRUCKS = []
for i, x in enumerate((-4.2, 4.2)):
    root = bpy.data.objects.new("DumpTruck%d" % i, None); DMP.objects.link(root)
    root.location = DX + Vector((x, 12.6, 0)); root.rotation_euler = (0, 0, R_(180))
    cab = copy_obj(L_tcab, "DumpTruck%d_cab" % i, (0, 0, 0), c=DMP); cab.parent = root
    bed = copy_obj(L_tbed, "DumpTruck%d_bed" % i, (0, 0, 0), c=DMP, linked=False); bed.parent = root
    bed.location = HINGE; bed.data.materials.clear(); bed.data.materials.append(M_blue)
    TRUCKS.append((root, cab, bed))
DRUM_Y = mat("DrumYellow", (0.95, 0.78, 0.05), 0.45, metal=0.3)
L_drum.data.materials.clear(); L_drum.data.materials.append(DRUM_Y)
ms = import_glb("dozer"); normalize(ms, 5.6, axis='max'); DOZER = join(ms, "Dozer"); link(DOZER, DMP)
DOZER.location = DX + Vector((-22, -6, 0))

# ------------------------------------------------------------------ BASEMENT (1200,0,0)
BX = Vector((1200, 0, 0)); BAS = coll("SET_basement")
M_bfloor = pbr("BasementFloor", "concrete_tiles", 0.3, tint=(0.75, 0.75, 0.78), coords="Object")
plane("B_floor", (6, 6), BX, M_bfloor, BAS)
# back wall (y=+2.5) with a window opening 1.3 x 0.65 at z 1.65..2.3
for nm, sz, lc in (("B_wallB_lo", (6, 0.2, 1.65), (0, 2.6, 0.825)), ("B_wallB_hi", (6, 0.2, 0.3), (0, 2.6, 2.45)),
                   ("B_wallB_l", (2.35, 0.2, 0.65), (-1.825, 2.6, 1.975)), ("B_wallB_r", (2.35, 0.2, 0.65), (1.825, 2.6, 1.975)),
                   ("B_wallL", (0.2, 6, 2.6), (-3.0, 0, 1.3)), ("B_wallR", (0.2, 6, 2.6), (3.0, 0, 1.3)), ("B_wallF", (6, 0.2, 2.6), (0, -3.1, 1.3))):
    box(nm, sz, BX + Vector(lc), M_block, BAS)
box("B_ceil", (6.4, 6.4, 0.1), BX + Vector((0, 0, 2.65)), mat("Joist", (0.75, 0.6, 0.42), 0.7), BAS)
for i in range(7): box("B_joist.%d" % i, (0.06, 6, 0.2), BX + Vector((-2.7 + i * 0.9, 0, 2.5)), mat("Joist", (0.75, 0.6, 0.42), 0.7), BAS)
fr = []
for nm, sz, lc in (("t", (1.4, 0.12, 0.06), (0, 2.6, 2.3)), ("b", (1.4, 0.12, 0.06), (0, 2.6, 1.65)), ("l", (0.06, 0.12, 0.7), (-0.67, 2.6, 1.975)), ("r", (0.06, 0.12, 0.7), (0.67, 2.6, 1.975)), ("m", (0.04, 0.1, 0.65), (0, 2.6, 1.975))):
    fr.append(box("B_wf_" + nm, sz, BX + Vector(lc), M_white))
link(join(fr, "B_winframe"), BAS)
box("B_winglass", (1.3, 0.02, 0.65), BX + Vector((0, 2.66, 1.975)), mat("WindowDayB", (0.85, 0.93, 1.0), 0.5, emit=(0.85, 0.93, 1.0), emit_s=4.0), BAS)
a = bpy.data.objects.new("B_light", bpy.data.lights.new("B_light", 'AREA')); BAS.objects.link(a)
a.data.size = 2.5; a.data.energy = 260; a.location = BX + Vector((0, 0.2, 2.4))
a = bpy.data.objects.new("B_win", bpy.data.lights.new("B_win", 'AREA')); BAS.objects.link(a)
a.data.size = 1.3; a.data.size_y = 0.65; a.data.shape = 'RECTANGLE'; a.data.energy = 120; a.location = BX + Vector((0, 2.45, 1.975)); a.rotation_euler = (R_(-90), 0, 0)
for i, (x, y, s) in enumerate(((-2.4, 1.9, 0.5), (-2.3, 1.3, 0.42), (-2.45, 1.9, 0.4))):
    b = copy_obj(MBOX, "B_box.%d" % i, BX + Vector((x, y, 0.5 * i if i == 2 else 0)), rz=8 * i, c=BAS); b.scale = (s / 0.45,) * 3

# ------------------------------------------------------------------ BACKYARD (1500,0,0)
YX = Vector((1500, 0, 0)); YRD = coll("SET_yard")
plane("Y_lawn", (80, 80), YX, M_lawn, YRD)
copy_obj(L_house5, "Y_house", YX + Vector((0, 15, 0)), rz=180, c=YRD)
for i in range(14): copy_obj(L_fence, "Y_fence.%d" % i, YX + Vector((-9 + 0.0, -12 + i * 2.27, 0)), c=YRD)
for i in range(9): copy_obj(L_fence, "Y_fenceb.%d" % i, YX + Vector((-8 + i * 2.27, -12.6, 0)), rz=90, c=YRD)
copy_obj(L_tree, "Y_tree", YX + Vector((-5, 3, 0)), rz=30, c=YRD)
copy_obj(L_tree, "Y_tree2", YX + Vector((6, 9, 0)), rz=130, c=YRD).scale = (0.8, 0.8, 0.8)

# ------------------------------------------------------------------ WATER TOWER (1800,0,0)
TX = Vector((1800, 0, 0)); TWR = coll("SET_tower")
plane("T_lawn", (400, 400), TX, M_farg, TWR)
ms = import_glb("wt_junk"); ms = [o for o in ms]
normalize(ms, 22.0); TOWER = join(ms, "WaterTower"); link(TOWER, TWR); TOWER.location = TX
for i in range(8):
    a_ = i * 45 + 20; r_ = 30 + (i % 3) * 8
    copy_obj(L_house0 if i % 2 else L_house5, "T_house.%d" % i, TX + Vector((r_ * math.cos(R_(a_)), r_ * math.sin(R_(a_)), 0)), rz=a_ + 90, c=TWR)
    copy_obj(L_tree, "T_tree.%d" % i, TX + Vector(((r_ - 9) * math.cos(R_(a_ + 18)), (r_ - 9) * math.sin(R_(a_ + 18)), 0)), rz=i * 40, c=TWR)

# ------------------------------------------------------------------ HOSPITAL (2100,0,0)
HX = Vector((2100, 0, 0)); HOS = coll("SET_hospital")
M_hwall = mat("HospWall", (0.78, 0.88, 0.86), 0.8); M_hfloor = mat("HospFloor", (0.62, 0.6, 0.72), 0.45)
plane("H_floor", (7, 6), HX, M_hfloor, HOS)
box("H_wallB", (7, 0.12, 2.9), HX + Vector((0, 2.6, 1.45)), M_hwall, HOS)
box("H_wallL", (0.12, 6, 2.9), HX + Vector((-3.5, 0, 1.45)), M_hwall, HOS)
box("H_wallR", (0.12, 6, 2.9), HX + Vector((3.5, 0, 1.45)), M_hwall, HOS)
box("H_wallF", (7, 0.12, 2.9), HX + Vector((0, -3.1, 1.45)), M_hwall, HOS)
box("H_ceil", (7.2, 6.4, 0.1), HX + Vector((0, 0, 2.95)), M_white, HOS)
box("H_window", (1.8, 0.03, 1.2), HX + Vector((1.6, 2.53, 1.65)), mat("WindowDay", (0.8, 0.9, 1.0), 0.5), HOS)
box("H_winframe", (1.92, 0.05, 1.32), HX + Vector((1.6, 2.56, 1.65)), M_white, HOS)
box("H_panel", (2.6, 0.06, 0.28), HX + Vector((-0.6, 2.52, 1.45)), mat("BedPanel", (0.85, 0.85, 0.82), 0.5), HOS)
ms = import_glb("hbed"); normalize(ms, 2.15, axis='max'); HBED = join(ms, "HospitalBed"); link(HBED, HOS)
_mn, _mx = bbox([HBED])
if (_mx - _mn).y > (_mx - _mn).x: HBED.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))     # long axis along X
HBED.location = HX + Vector((-0.4, 1.2, 0))
ms = import_glb("chair"); normalize(ms, 0.85); HCHAIR = join(ms, "BedsideChair"); link(HCHAIR, HOS); HCHAIR.location = HX + Vector((-0.6, -0.55, 0)); HCHAIR.rotation_euler = (0, 0, R_(0))
M_teal = mat("ChairTeal", (0.1, 0.55, 0.65), 0.6)
for i, m in enumerate(HCHAIR.data.materials):
    if m and "Fabric" in m.name: HCHAIR.data.materials[i] = M_teal
box("H_table", (0.5, 0.45, 0.7), HX + Vector((-2.6, 1.8, 0.35)), mat("TableWood", (0.7, 0.55, 0.4), 0.5), HOS, bevel=0.01)
a = bpy.data.objects.new("H_light", bpy.data.lights.new("H_light", 'AREA')); HOS.objects.link(a)
a.data.size = 3; a.data.size_y = 2; a.data.shape = 'RECTANGLE'; a.data.energy = 260; a.location = HX + Vector((0, 0, 2.85))
a = bpy.data.objects.new("H_win", bpy.data.lights.new("H_win", 'AREA')); HOS.objects.link(a)
a.data.size = 1.8; a.data.size_y = 1.2; a.data.shape = 'RECTANGLE'; a.data.energy = 200; a.location = HX + Vector((1.6, 2.4, 1.65)); a.rotation_euler = (R_(-90), 0, 0)

# park every character far away until the animation script places them
for o in bpy.data.objects:
    if o.type == 'ARMATURE': o.location = (0, -5000, -500)

# greener maple leaves (the scan's leaf colour read as white-speckled)
for m in L_tree.data.materials:
    if m and m.use_nodes and any(k in m.name.lower() for k in ("leaf", "leaves", "foliage", "maple")) and "bark" not in m.name.lower():
        P_ = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if P_ and P_.inputs["Base Color"].is_linked:
            src_ = P_.inputs["Base Color"].links[0].from_socket
            mx_ = m.node_tree.nodes.new("ShaderNodeMix"); mx_.data_type = 'RGBA'; mx_.blend_type = 'MULTIPLY'; mx_.inputs[0].default_value = 1
            m.node_tree.links.new(src_, mx_.inputs[6]); mx_.inputs[7].default_value = (0.45, 0.85, 0.3, 1); m.node_tree.links.new(mx_.outputs[2], P_.inputs["Base Color"])
        print("LEAF tint", m.name)
