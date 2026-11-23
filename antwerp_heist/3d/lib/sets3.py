"""Part 3 sets: the woodland beside the motorway (the dumped rubbish), the forensic lab, the courtroom (2005), the
warehouse with Leonardo's claimed replica vault, an interview room, a supermarket aisle (CCTV), the evidence wall."""
import math, random
import bpy
from mathutils import Vector, Matrix
import ship as S
import ph
from sets import flat, emit, enamel, steel_paint, brushed, tex, paper_mat, gold, box, light_area, light_point, light_spot, world
import sets2 as S2


def _sf_copy(uid, n, places, height=None, width=None, mat=None):
    """Import a Sketchfab model once, join its meshes into one object (world transforms applied), then place linked
    duplicates at places [(x, y, rz, s)] (same mesh data: cheap). mat replaces its materials (e.g. bark)."""
    import sf
    r, ms = sf.model(uid)
    bpy.context.view_layer.update()
    lo, hi = ph.bounds(ms)
    base = (height / (hi.z - lo.z)) if height else (width / max(hi.x - lo.x, hi.y - lo.y)) if width else 1.0
    import bmesh
    bm = bmesh.new()
    for m in ms:
        tmp = m.data.copy(); tmp.transform(m.matrix_world); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new("tree_" + uid[:6]); bm.to_mesh(me); bm.free()
    for v in me.vertices:
        v.co.x -= (lo.x + hi.x) / 2; v.co.y -= (lo.y + hi.y) / 2; v.co.z -= lo.z
    if mat:
        me.materials.clear(); me.materials.append(mat)
    else:
        for m_ in ms[0].data.materials:
            me.materials.append(m_)
    for o in list(r.children_recursive) + [r]:
        bpy.data.objects.remove(o)
    out = []
    for i, (x, y, rz, s) in enumerate(places):
        o = bpy.data.objects.new(f"tree_{uid[:6]}_{i}", me); bpy.context.scene.collection.objects.link(o)
        o.scale = (base * s * 0.42, base * s * 0.42, base * s); o.rotation_euler = (0, 0, rz); o.location = (x, y, 0)   # slender trunks
        out.append(o)
    return out


def bark(name="bark"):
    m = enamel(name, (0.11, 0.095, 0.08), rough=0.85, var=0.35, scale=30.0, bump=0.4)
    return m


LEAFLESS = "ba9c1e89f73d403585f50c56ef455ec2"      # "leafless tree", mr00T, CC-BY
LEAFLESS2 = "aa58d0d7161a4915868673b2b70d0218"     # "ZBrush leafless Tree", hirnlaich, CC-BY
EVIDENCE_BAG = "deee24b1f0cc43728dbde3e137e4bfba"  # "Plastic Evidence Bag", sousinho, CC-BY


# ----------------------------------------------------------------------------- woodland beside the motorway
def woodland(hour="day", bags=True):
    """February woodland beside the E19: bare oaks and birches, leaf litter, brambles, a ditch, then a grass verge,
    a steel crash barrier and the motorway. The rubbish (black and white bin bags, papers spilling out) lies just
    inside the trees. Woods: y > 0; verge/barrier at y = -3; carriageway y in [-14, -4]."""
    import look
    A = {}
    rng = random.Random(11)
    floor = tex("forest_floor", 2.0, tint=(0.75, 0.62, 0.48), name="leaf_litter")
    box("w_ground", (0, 15, -0.05), (80, 36, 0.1), floor)
    floor.node_tree.nodes["Mapping"].inputs['Scale'].default_value = (0.6, 0.6, 0.6) if "Mapping" in floor.node_tree.nodes else None
    grass = tex("grass_medium_01" if False else "aerial_grass_rock" if False else "brown_mud_leaves_01" if False else "forest_floor", 3.0, tint=(0.5, 0.6, 0.35), name="verge")
    box("w_verge", (0, -2.0, -0.04), (80, 3.0, 0.1), grass)
    box("w_road", (0, -9.0, -0.06), (80, 11.0, 0.1), tex("asphalt_02", 3.0, tint=(0.55, 0.53, 0.5), name="w_asphalt"))
    white = flat("lane", (0.75, 0.75, 0.72), 0.6)
    for k in range(-20, 21):
        box("lane_dash", (k * 4.0, -9.0, 0.0), (2.4, 0.15, 0.005), white)
    box("lane_edge", (0, -3.95, 0.0), (80, 0.2, 0.005), white)
    # crash barrier: posts and a W-beam rail
    galv = brushed("galv", (0.5, 0.5, 0.5), 0.45)
    for k in range(-20, 21):
        box("barrier_post", (k * 2.0, -3.3, 0.35), (0.1, 0.1, 0.7), galv)
    box("barrier_rail", (0, -3.38, 0.6), (80, 0.06, 0.32), galv, bevel=0.01)
    # trees: two bare models, scattered, none on the path where the shots look
    places = []
    for i in range(60):
        x = rng.uniform(-24, 24); y = rng.uniform(2.0, 26)
        if abs(x) < 2.5 and y < 5.5:
            continue
        places.append((x, y, rng.uniform(0, 6.28), rng.uniform(0.8, 1.3)))
    bk = bark()
    _sf_copy(LEAFLESS2, len(places), places, height=9.0, mat=bk)
    # understory: real low plants (shrubs, nettles, dry branches, ferns) from Poly Haven, scattered between the trees
    for aid, n, sc in (("shrub_02", 10, 1.0), ("nettle_plant", 14, 1.0), ("dry_branches_medium_01", 12, 1.0), ("fern_02", 8, 0.8), ("shrub_04", 8, 1.0)):
        for i in range(n):
            x = rng.uniform(-14, 14); y = rng.uniform(0.8, 14)
            if abs(x) < 2.2 and y < 4.5:
                continue
            try:
                ph.model(aid, loc=(x, y, 0), rot_z=rng.uniform(0, 6.28), scale=sc * rng.uniform(0.7, 1.3))
            except Exception as e:
                print("plant", aid, e); break
    try:
        for (x, y, rz) in ((5.0, 4.5, 0.4), (-6.0, 7.0, 2.1), (2.5, 11.0, 1.2)):
            ph.model("dead_tree_trunk", loc=(x, y, 0), rot_z=rz)
    except Exception as e:
        print("trunk", e)
    # the rubbish: bin bags (some split), papers, a few household things, just inside the tree line
    A["dump"] = Vector((0.4, 2.4, 0))
    if bags:
        cols = [(0.01, 0.01, 0.012), (0.012, 0.012, 0.014), (0.7, 0.7, 0.68), (0.02, 0.03, 0.08)]
        for i, (x, y, rz) in enumerate(((0.0, 2.2, 0.3), (0.8, 2.6, 1.4), (-0.6, 2.9, 2.2), (0.4, 3.3, 0.8), (1.3, 2.0, 2.9))):
            try:
                r, ms = ph.model("trashbag", loc=(x, y, 0), rot_z=rz, scale=rng.uniform(0.9, 1.2))
                m = flat(f"binbag{i}", cols[i % 4], 0.35); m.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.5
                for o in ms:
                    o.data.materials.clear(); o.data.materials.append(m)
            except Exception as e:
                print("bag", e)
        pm = paper_mat(); env = paper_mat("w_env", (0.62, 0.48, 0.3)); dp = paper_mat("w_dpaper", (0.86, 0.85, 0.8))
        for i in range(40):
            p = A["dump"] + Vector((rng.gauss(0, 0.9), rng.gauss(0, 0.7), 0))
            m = (pm, env, dp)[i % 3]
            box("w_paper", (p.x, p.y, 0.004 + 0.001 * (i % 4)), (0.15 if m is dp else 0.21, 0.1 if m is dp else 0.28, 0.0008), m,
                rot=(rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), rng.uniform(0, 6.28)))
        A["bag_open"] = Vector((0.0, 2.2, 0.3))
    # light: low February sun through bare trees, mist
    if hour == "day":
        look.day_light("mist", azim=150, exposure=0.6)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 12, 5))
        hz = bpy.context.active_object; hz.name = "w_haze"; hz.scale = (70, 50, 10)
        hm = bpy.data.materials.new("w_haze"); hm.use_nodes = True; N = hm.node_tree.nodes; N.remove(N["Principled BSDF"])
        vs = N.new("ShaderNodeVolumeScatter"); vs.inputs['Density'].default_value = 0.0025; vs.inputs['Anisotropy'].default_value = 0.6
        vs.inputs['Color'].default_value = (0.78, 0.79, 0.76, 1)
        hm.node_tree.links.new(vs.outputs[0], N["Material Output"].inputs['Volume']); hz.data.materials.append(hm)
        hz.visible_shadow = False
    else:
        look.day_light("dusk", azim=120)
    A["road"] = Vector((0, -9, 0))
    return A


# ----------------------------------------------------------------------------- forensic lab
def lab():
    """Federal police forensic lab: long benches with brown evidence paper, the rubbish laid out item by item with
    numbered markers, a microscope, a fume hood, sample racks; cool overhead light plus a warm task lamp."""
    import detail as DT
    A = {}
    RX, RY, RZ = 4.0, 3.0, 2.8
    wall = DT.wall_paint("lab_wall", (0.5, 0.52, 0.5), rough=0.7, scuff=0.3)
    box("lab_floor", (0, 0, -0.05), (2 * RX + 0.4, 2 * RY + 0.4, 0.1), tex("rubber_tiles", 1.0, tint=(0.45, 0.46, 0.44), name="lab_floor"))
    box("lab_ceil", (0, 0, RZ + 0.05), (2 * RX + 0.4, 2 * RY + 0.4, 0.1), flat("lab_ceil", (0.5, 0.5, 0.48), 0.9))
    for sg in (1, -1):
        box("lab_wall_x", (sg * (RX + 0.1), 0, RZ / 2), (0.2, 2 * RY + 0.4, RZ), wall)
        box("lab_wall_y", (0, sg * (RY + 0.1), RZ / 2), (2 * RX + 0.4, 0.2, RZ), wall)
    top = flat("bench_top", (0.12, 0.13, 0.13), 0.35)
    body = steel_paint("bench_body", (0.55, 0.56, 0.55), 0.45)
    for y in (-0.6, 1.4):
        box("lab_bench_top", (0, y, 0.9), (4.2, 1.0, 0.04), top)
        box("lab_bench_body", (0, y, 0.44), (4.0, 0.85, 0.88), body)
    kraft = paper_mat("kraft", (0.45, 0.32, 0.2))
    box("evidence_paper", (0, -0.6, 0.921), (3.6, 0.85, 0.002), kraft)
    A["bench"] = Vector((0, -0.6, 0.922)); A["bench2"] = Vector((0, 1.4, 0.922))
    # numbered yellow markers along the bench (number engraved as text: diegetic)
    yel = flat("marker_yellow", (0.8, 0.6, 0.05), 0.5)
    for k in range(7):
        x = -1.5 + k * 0.5
        box("marker", (x, -0.95, 0.94), (0.05, 0.03, 0.035), yel, rot=(math.radians(20), 0, 0))
        DT.number_text(str(k + 1), Matrix.Translation((x, -0.968, 0.945)) @ Matrix.Rotation(math.radians(20), 4, 'X'), size=0.02,
                       mat=flat("num_black", (0.01, 0.01, 0.01), 0.5))
    A["markers_x"] = [-1.5 + k * 0.5 for k in range(7)]
    try:
        ph.model("industrial_microscope", loc=(1.3, 1.45, 0.92), rot_z=math.radians(180))
    except Exception as e:
        print("microscope", e)
    # sample rack with tubes on the second bench
    rack = flat("rack", (0.8, 0.8, 0.78), 0.4); tube = bpy.data.materials.new("tube_glass"); tube.use_nodes = True
    tp = tube.node_tree.nodes["Principled BSDF"]; tp.inputs['Transmission Weight'].default_value = 1.0; tp.inputs['Roughness'].default_value = 0.05
    box("tube_rack", (-0.8, 1.3, 0.96), (0.3, 0.1, 0.06), rack)
    for k in range(8):
        S.cyl("tube", (-0.93 + k * 0.037, 1.3, 0.94), (-0.93 + k * 0.037, 1.3, 1.06), 0.007, mat=tube, verts=12)
        S.cyl("tube_cap", (-0.93 + k * 0.037, 1.3, 1.06), (-0.93 + k * 0.037, 1.3, 1.075), 0.0075, mat=flat(f"cap{k%3}", ((0.6, 0.1, 0.1), (0.1, 0.3, 0.6), (0.8, 0.7, 0.1))[k % 3], 0.4), verts=12)
    A["tubes"] = Vector((-0.8, 1.3, 1.0))
    # fume hood on the back wall
    box("fume_hood", (2.6, RY - 0.4, 1.4), (1.4, 0.7, 1.2), steel_paint("hood", (0.7, 0.72, 0.7), 0.4))
    box("hood_glass", (2.6, RY - 0.76, 1.3), (1.3, 0.02, 0.7), flat("hood_glass", (0.3, 0.35, 0.35), 0.05, metal=0.3))
    # light: cool overhead panels, a warm task lamp over the evidence
    for x in (-2.0, 0.0, 2.0):
        box("lab_panel", (x, 0.4, RZ - 0.02), (1.2, 0.6, 0.03), emit("lab_panel", (0.9, 0.95, 1.0), 6))
        light_area("lab_light", (x, 0.4, RZ - 0.06), (x, 0.4, 0), 1.2, 75, (0.92, 0.96, 1.0), size_y=0.6)
    light_spot("task_lamp", (0.3, -1.3, 1.6), A["bench"], 30, angle=60, color=(1.0, 0.82, 0.6), radius=0.08)
    world((0.02, 0.02, 0.02), 0.3)
    return A


SUB = "b7aa7644a6f9481b89da16eb2b9ca39b"            # "Sub Sandwich (Game Ready / 2K PBR)", meerschaumdigital, CC-BY


def sandwich(name="sandwich", loc=(0, 0, 0), rz=0.0, length=0.13):
    """The half-eaten salami sandwich: a cut length of baguette with salami (CC-BY asset), 13 cm."""
    import props as PR
    return PR.sf_put(SUB, loc, width=length, rz=rz, name=name)


# ----------------------------------------------------------------------------- courtroom
def courtroom():
    """An Antwerp courtroom (2005): oak panelling, the raised bench for three judges under tall windows, the dock,
    benches for the public; warm daylight from the side windows."""
    import detail as DT
    A = {}
    RX, RY, RZ = 6.0, 7.0, 5.5
    oak = tex("wood_table_worn", 1.5, tint=(0.55, 0.38, 0.24), name="court_oak")
    wall = DT.wall_paint("court_wall", (0.55, 0.5, 0.42), rough=0.85, scuff=0.2)
    box("c_floor", (0, 0, -0.05), (2 * RX, 2 * RY, 0.1), tex("herringbone_brick" if False else "wood_floor", 1.5, tint=(0.6, 0.45, 0.32), name="court_floor"))
    box("c_ceil", (0, 0, RZ + 0.05), (2 * RX, 2 * RY, 0.1), flat("c_ceil", (0.6, 0.57, 0.5), 0.9))
    for sg in (1, -1):
        box("c_wall_x", (sg * (RX + 0.1), 0, RZ / 2), (0.2, 2 * RY, RZ), wall)
        box("c_panel_x", (sg * (RX - 0.02), 0, 1.2), (0.04, 2 * RY, 2.4), oak)
    box("c_wall_back", (0, RY + 0.1, RZ / 2), (2 * RX, 0.2, RZ), wall)
    box("c_wall_front", (0, -RY - 0.1, RZ / 2), (2 * RX, 0.2, RZ), wall)
    box("c_panel_back", (0, RY - 0.02, 1.6), (2 * RX, 0.04, 3.2), oak)
    # the bench: a raised platform and a long desk for three judges
    box("c_dais", (0, RY - 1.4, 0.25), (6.0, 2.6, 0.5), oak)
    box("c_bench_desk", (0, RY - 2.4, 1.05), (5.6, 0.6, 1.1), oak, bevel=0.01)
    A["judges"] = [Vector((x, RY - 1.6, 0.5)) for x in (-1.4, 0.0, 1.4)]
    for x in (-1.4, 0.0, 1.4):
        S2.chair(f"judge_chair{x}", (x, RY - 1.35, 0.5), -90, flat("chair_leather", (0.15, 0.04, 0.03), 0.5), flat("chair_wood", (0.12, 0.07, 0.04), 0.5), seat_h=0.47)
    # the dock (accused) and benches
    box("c_dock_front", (0.0, 0.8, 0.5), (2.4, 0.06, 1.0), oak)
    for sx in (-1.2, 1.2):
        box("c_dock_side", (sx, 1.3, 0.5), (0.06, 1.0, 1.0), oak)
    A["dock"] = Vector((0.0, 1.35, 0))
    for k in range(4):
        y = -1.5 - k * 1.2
        for sx in (-3.0, 3.0):
            box("c_pew_seat", (sx, y, 0.45), (4.0, 0.45, 0.05), oak)
            box("c_pew_back", (sx, y - 0.22, 0.75), (4.0, 0.05, 0.6), oak)
    A["pews"] = [Vector((sx, -1.5 - k * 1.2, 0.47)) for k in range(4) for sx in (-3.0, 3.0)]
    # tall windows on the left wall: light
    for k in range(3):
        y = -4.0 + k * 3.5
        box("c_window", (-RX + 0.01, y, 3.2), (0.02, 1.6, 3.0), emit("c_window", (1.0, 0.95, 0.88), 2.5))
        light_area("c_win_light", (-RX + 0.3, y, 3.2), (0, y, 0.5), 2.0, 900, (1.0, 0.93, 0.82), size_y=3.0)
    light_area("c_fill", (2.0, -3.0, RZ - 0.2), (0, 0, 0), 3.0, 120, (1.0, 0.88, 0.72))
    world((0.04, 0.035, 0.03), 0.3)
    return A


# ----------------------------------------------------------------------------- the claimed replica vault (warehouse)
def replica():
    """What Leonardo later described: a mock-up of the vault built for rehearsals in a warehouse: a plywood door
    frame with a painted steel door, a wall of plywood 'boxes', work lights on stands."""
    A = {}
    RX, RY, RZ = 9.0, 7.0, 6.0
    conc = tex("concrete_floor_02" if False else "concrete_floor_worn_001", 2.0, tint=(0.6, 0.57, 0.52), name="wh_floor")
    box("wh_floor", (0, 0, -0.05), (2 * RX, 2 * RY, 0.1), conc)
    corr = tex("box_profile_metal_sheet", 2.0, tint=(0.45, 0.47, 0.48), name="wh_wall")
    for sg in (1, -1):
        box("wh_wall_x", (sg * (RX + 0.1), 0, RZ / 2), (0.2, 2 * RY, RZ), corr)
        box("wh_wall_y", (0, sg * (RY + 0.1), RZ / 2), (2 * RX, 0.2, RZ), corr)
    box("wh_roof", (0, 0, RZ + 0.05), (2 * RX, 2 * RY, 0.1), corr)
    ply = tex("plywood" if False else "wood_table_worn", 1.0, tint=(0.85, 0.7, 0.5), name="plywood")
    grey = steel_paint("mock_door", (0.2, 0.22, 0.22), 0.4)
    # mock wall with a door opening and a painted door leaf standing open
    box("mock_wall_l", (-2.0, 2.0, 1.25), (3.0, 0.1, 2.5), ply)
    box("mock_wall_r", (2.0, 2.0, 1.25), (3.0, 0.1, 2.5), ply)
    box("mock_wall_top", (0, 2.0, 2.25), (1.0, 0.1, 0.5), ply)
    leaf = box("mock_door", (0.95, 1.45, 1.0), (0.08, 1.0, 2.0), grey)
    # plywood box wall behind with a grid of painted doors
    box("mock_boxwall", (0, 4.5, 1.2), (5.0, 0.4, 2.0), ply)
    door = flat("mock_boxdoor", (0.62, 0.6, 0.55), 0.5)
    for c in range(12):
        for r in range(5):
            box("mock_boxdoor", (-2.2 + c * 0.4, 4.29, 0.35 + r * 0.38), (0.36, 0.01, 0.34), door)
    A["door"] = Vector((0, 2.0, 1.0)); A["boxwall"] = Vector((0, 4.3, 1.2))
    # work lights on stands
    blk = flat("stand", (0.03, 0.03, 0.03), 0.4)
    for x, y in ((-3.0, 0.0), (3.0, 0.5)):
        S.cyl("stand", (x, y, 0), (x, y, 2.0), 0.02, mat=blk, verts=8)
        box("worklight", (x, y, 2.05), (0.3, 0.12, 0.22), flat("wl_yellow", (0.8, 0.6, 0.05), 0.4))
        light_spot("worklight_beam", (x, y + 0.08, 2.05), (0, 3.0, 1.0), 900, angle=70, color=(1.0, 0.86, 0.6), radius=0.1)
    light_area("wh_skylight", (0, 0, RZ - 0.1), (0, 0, 0), 4.0, 200, (0.75, 0.8, 0.9))
    world((0.02, 0.02, 0.025), 0.3)
    return A


# ----------------------------------------------------------------------------- interview room
def interview():
    """A bare interview room: table, two chairs, a high barred window throwing one hard shaft of light."""
    import detail as DT
    A = {}
    RX, RY, RZ = 2.2, 2.0, 2.8
    wall = DT.wall_paint("iv_wall", (0.42, 0.43, 0.42), rough=0.85, scuff=0.6)
    box("iv_floor", (0, 0, -0.05), (2 * RX, 2 * RY, 0.1), tex("concrete_floor_painted", 1.0, tint=(0.4, 0.4, 0.38), name="iv_floor"))
    box("iv_ceil", (0, 0, RZ + 0.05), (2 * RX, 2 * RY, 0.1), flat("iv_ceil", (0.4, 0.4, 0.4), 0.9))
    for sg in (1, -1):
        box("iv_wall_y", (0, sg * (RY + 0.1), RZ / 2), (2 * RX, 0.2, RZ), wall)
    box("iv_wall_xl", (-RX - 0.1, 0, RZ / 2), (0.2, 2 * RY, RZ), wall)
    # right wall with a high window
    box("iv_wall_xr_lo", (RX + 0.1, 0, 0.9), (0.2, 2 * RY, 1.8), wall)
    box("iv_wall_xr_hi", (RX + 0.1, 0, 2.55), (0.2, 2 * RY, 0.5), wall)
    for sy in (-1, 1):
        box("iv_wall_xr_side", (RX + 0.1, sy * 1.2, 2.05), (0.2, 1.6, 0.5), wall)
    for k in range(5):
        S.cyl("iv_bar", (RX + 0.05, -0.36 + k * 0.18, 1.8), (RX + 0.05, -0.36 + k * 0.18, 2.3), 0.012, mat=flat("bar", (0.05, 0.05, 0.05), 0.4), verts=8)
    S2.table("iv_table", (0, 0, 0), (1.2, 0.8), flat("iv_tabletop", (0.25, 0.24, 0.22), 0.4), flat("iv_leg", (0.1, 0.1, 0.1), 0.4, 0.8))
    A["seats"] = {"L": (Vector((-0.85, 0.0, 0.46)), 0), "R": (Vector((0.85, 0.0, 0.46)), 180)}
    for k, (p, yaw) in A["seats"].items():
        S2.chair(f"iv_chair_{k}", (p.x, p.y, 0), yaw, flat("iv_seat", (0.1, 0.1, 0.1), 0.6), flat("iv_frame", (0.2, 0.2, 0.2), 0.4, 0.7))
    l = bpy.data.lights.new("iv_sun", 'SUN'); l.energy = 6.0; l.angle = math.radians(1.0); l.color = (1.0, 0.9, 0.75)
    so = bpy.data.objects.new("iv_sun", l); bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (Vector((-1.0, 0.1, -0.7))).to_track_quat('-Z', 'Y').to_euler()
    light_area("iv_fill", (-1.0, -1.5, 2.6), (0, 0, 0.8), 1.0, 25, (0.8, 0.85, 0.95))
    world((0.5, 0.6, 0.75), 0.25)
    A["table"] = Vector((0, 0, 0.76))
    return A


# ----------------------------------------------------------------------------- supermarket aisle (CCTV)
def supermarket():
    """A supermarket checkout seen by its ceiling camera: shelf ends with packed products, a checkout counter
    with a belt, strip lights."""
    A = {}
    rng = random.Random(3)
    box("sm_floor", (0, 0, -0.05), (14, 10, 0.1), tex("large_floor_tiles_02", 1.0, tint=(0.75, 0.74, 0.7), name="sm_floor"))
    box("sm_ceil", (0, 0, 3.05), (14, 10, 0.1), flat("sm_ceil", (0.6, 0.6, 0.6), 0.9))
    shelf = steel_paint("shelf", (0.7, 0.7, 0.68), 0.4)
    cols = [(0.6, 0.1, 0.08), (0.1, 0.3, 0.6), (0.8, 0.65, 0.1), (0.15, 0.5, 0.2), (0.85, 0.85, 0.8), (0.5, 0.25, 0.1)]
    for row in range(3):
        y = 1.0 + row * 1.8
        box("shelf_unit", (0, y, 0.85), (8.0, 0.6, 1.7), shelf)
        for lv in range(4):
            for k in range(28):
                c = cols[rng.randrange(len(cols))]
                box("product", (-3.85 + k * 0.28, y - 0.25, 0.15 + lv * 0.42), (0.22, 0.12, rng.uniform(0.15, 0.3)), flat(f"prod{rng.randrange(6)}", c, 0.5))
    box("checkout", (-1.0, -1.5, 0.45), (2.2, 0.7, 0.9), steel_paint("checkout", (0.25, 0.3, 0.35), 0.4))
    box("belt", (-1.2, -1.5, 0.905), (1.6, 0.5, 0.01), flat("belt", (0.03, 0.03, 0.03), 0.6))
    A["checkout"] = Vector((-1.0, -1.5, 0.92))
    for x in (-4, 0, 4):
        box("sm_strip", (x, 0.0, 3.0), (0.15, 8.0, 0.04), emit("sm_strip", (1.0, 0.97, 0.9), 8))
        light_area("sm_light", (x, 0.0, 2.95), (x, 0.0, 0), 0.15, 400, (1.0, 0.97, 0.9), size_y=8.0)
    world((0.2, 0.2, 0.2), 0.3)
    return A


# ----------------------------------------------------------------------------- the evidence wall
def evidence_wall(images):
    """A cork board in the detectives' office with prints pinned up (images: list of image paths) and soft orange
    bands linking them (the house's way of drawing a connection)."""
    import detail as DT
    A = {}
    box("ew_floor", (0, 0, -0.05), (6, 5, 0.1), tex("dirty_carpet", 1.5, tint=(0.35, 0.33, 0.32), name="ew_carpet"))
    box("ew_wall", (0, 1.6, 1.5), (6, 0.2, 3), DT.wall_paint("ew_wall", (0.5, 0.48, 0.44), rough=0.85))
    box("ew_cork", (0, 1.48, 1.55), (2.4, 0.03, 1.3), tex("cork" if False else "wood_table_worn", 2.0, tint=(0.75, 0.52, 0.3), name="cork"))
    pins = []
    xs = [(-0.8, 1.75), (0.0, 1.85), (0.8, 1.7), (-0.4, 1.25), (0.45, 1.25)]
    for i, img in enumerate(images[:len(xs)]):
        x, z = xs[i]
        m = S2.image_mat(f"print{i}", img, emissive=False)
        o = S2.plane(f"print{i}", (x, 1.462, z), (0.5, 0.28), m, rot=(math.radians(90), 0, 0))
        box("pin", (x, 1.455, z + 0.13), (0.012, 0.012, 0.012), flat("pin_red", (0.6, 0.03, 0.02), 0.3))
        pins.append(Vector((x, 1.455, z + 0.13)))
    A["pins"] = pins; A["board"] = Vector((0, 1.46, 1.55))
    light_spot("ew_lamp", (0.6, -0.8, 2.4), A["board"], 260, angle=55, color=(1.0, 0.86, 0.64), radius=0.1)
    world((0.02, 0.02, 0.02), 0.2)
    return A
