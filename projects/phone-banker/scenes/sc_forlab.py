"""FORENSIC LAB, Moscow (dramatization). One room, several variants:
  lab95  : 1995, daylight. Light table, a strip-chart recorder, an analyser printing a trace, steel cabinets (Ch1 7, Ch2 4)
  evid   : the evidence bench: the padded case of sealed glass ampoules under a raking lamp; the prosecutor's desk (Ch2 7)
  y2018  : 2018, the same room as an archive: a reporter photographs photocopied pages; two specialists confer (Ch3 8)
  end    : the evidence photograph on the light table; the ampoule case closes, the lights go out (Ch3 10)
No procedure is shown: instruments run, papers move, the vials stay sealed."""
import os, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from kit import *
import ph
from pbkit import joinm, masonry_facade, image_plane
from pbpeople import person, medic, stand, seat, walk_at, nod, look, hold_flat, hand_to, hide, recolor, fwd
from sc_bankoffice import retint, plastic
from sc_hospital import two_tone, fluorescents, window_light

EXPOSURE = 1.0
BOUNCES = 6
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "assets", "generated")
PHOTO = os.path.join(HERE, "..", "assets", "photos", "evidence_handset.jpg")
DUR = {"compare": 5.5, "recorder": 5.5, "gc_print": 5.0, "saratov": 5.0, "ampoules": 5.5, "slide_file": 5.0,
       "photocopies": 5.5, "specialists": 5.5, "photo": 6.0, "case_close": 7.0}
VARIANT_FOR = {"compare": "lab95", "recorder": "lab95", "gc_print": "lab95", "saratov": "lab95", "ampoules": "evid", "slide_file": "evid",
               "photocopies": "y2018", "specialists": "y2018", "photo": "end", "case_close": "end"}
W, D, H = 8.0, 6.0, 3.1
LT = Vector((-1.6, 0.6, 0.86))          # light table top centre
CASE = Vector((1.9, 1.7, 0.86))         # ampoule case on the side bench
REC = Vector((1.6, -1.6, 0.86))         # chart recorder / analyser bench
rng = np.random.default_rng(11)


# ============================================================================ props
def light_table(loc):
    steel = pbr("LTSteel", (0.55, 0.57, 0.58), 0.35, 0.7)
    parts = [box("LTBody", (0, 0, 0.42), (1.3, 0.8, 0.84), steel, bevel=0.01)]
    top = box("LTTop", (loc[0], loc[1], loc[2] + 0.005), (1.15, 0.65, 0.01), None)
    m = bpy.data.materials.new("LTGlow"); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]; p.inputs['Base Color'].default_value = (0.9, 0.92, 0.95, 1); p.inputs['Roughness'].default_value = 0.4
    p.inputs['Emission Color'].default_value = (0.9, 0.95, 1.0, 1); p.inputs['Emission Strength'].default_value = 1.5
    top.data.materials.append(m)
    o = joinm(parts, "LightTable"); o.location = (loc[0], loc[1], 0)
    return o, top, p


def ampoule():
    """A sealed glass ampoule: a lathe profile (body, neck, sealed tip)."""
    prof = [(0.0, 0.0), (0.0055, 0.0), (0.0065, 0.004), (0.0065, 0.036), (0.004, 0.042), (0.0022, 0.046), (0.0028, 0.05), (0.0026, 0.056), (0.0012, 0.064), (0.0, 0.066)]
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    for a, b in zip(vs, vs[1:]):
        bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=math.radians(360), steps=24)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new("Ampoule"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Ampoule", me); bpy.context.collection.objects.link(o)
    for p_ in me.polygons:
        p_.use_smooth = True
    return o


def ampoule_case(loc, n_slots=9, filled=8):
    """Padded steel case: dark foam with a row of slots; `filled` sealed ampoules, the rest empty. The lid is hinged at the back."""
    steel = pbr("CaseSteel", (0.45, 0.47, 0.48), 0.3, 0.9)
    foam = pbr("CaseFoam", (0.05, 0.05, 0.055), 0.95)
    root = bpy.data.objects.new("AmpouleCase", None); bpy.context.collection.objects.link(root)
    base = joinm([box("CaseBase", (0, 0, 0.025), (0.42, 0.2, 0.05), steel, bevel=0.006), box("CaseFoam", (0, 0, 0.051), (0.4, 0.18, 0.004), foam)], "CaseBase")
    base.parent = root
    gm = glass("AmpGlass", (0.96, 0.95, 0.9), 0.0)
    liq = pbr("AmpLiquid", (0.9, 0.88, 0.75), 0.05, 0.0, **{'Transmission Weight': 1.0})
    amps = []
    for k in range(n_slots):
        x = -0.17 + k * 0.0425
        slot = box("Slot", (x, 0, 0.051), (0.018, 0.09, 0.006), pbr("SlotDark", (0.01, 0.01, 0.01), 1.0)); slot.parent = root
        if k < filled:
            a = ampoule(); a.data.materials.append(gm); a.parent = root
            a.location = (x, 0.035, 0.058); a.rotation_euler = (math.radians(90), 0, 0)       # lying in its slot
            amps.append(a)
    piv = bpy.data.objects.new("CaseHinge", None); bpy.context.collection.objects.link(piv); piv.parent = root; piv.location = (0, 0.1, 0.05)
    lid = joinm([box("Lid", (0, -0.1, 0.012), (0.42, 0.2, 0.024), steel, bevel=0.006), box("LidFoam", (0, -0.1, -0.001), (0.4, 0.18, 0.004), foam)], "CaseLid")
    lid.parent = piv
    root.location = loc
    return root, piv, amps


def chart_recorder(loc, rot_z=0.0):
    """Strip-chart recorder: the paper scrolls out over a platen; the pen arm's trace sinks toward zero (frame drivers)."""
    beige = plastic("RecBeige", (0.62, 0.6, 0.53), 0.45)
    dark = pbr("RecDark", (0.08, 0.08, 0.08), 0.5)
    parts = [box("RecBody", (0, 0, 0.11), (0.48, 0.36, 0.22), beige, bevel=0.012),
             box("RecWindow", (0, -0.12, 0.225), (0.36, 0.12, 0.012), dark)]
    for k in range(3):
        parts.append(cyl("RecKnob", (0.15 - k * 0.05, -0.181, 0.08), 0.012, 0.015, dark, verts=12, rot=(math.radians(90), 0, 0)))
    body = joinm(parts, "Recorder"); body.location = loc; body.rotation_euler = (0, 0, rot_z)
    # paper strip with grid and trace (drawn), scrolling: it hangs from the platen over the front
    path = os.path.join(GEN, "chart_paper.png")
    if not os.path.exists(path):
        from PIL import Image, ImageDraw
        os.makedirs(GEN, exist_ok=True)
        Wp, Hp = 512, 2048
        im = Image.new("RGB", (Wp, Hp), (236, 234, 226)); d = ImageDraw.Draw(im)
        for x in range(0, Wp, 32):
            d.line([(x, 0), (x, Hp)], fill=(214, 180, 170))
        for y in range(0, Hp, 32):
            d.line([(0, y), (Wp, y)], fill=(222, 196, 188))
        pts = []
        for y in range(Hp):
            u = y / Hp                                                    # the trace starts high, then falls to the zero line
            base = 0.82 - 0.74 * min(1.0, max(0.0, (u - 0.25) / 0.45)) ** 0.8
            pts.append((Wp * (0.06 + base * 0.88 + 0.01 * math.sin(y * 0.11)), Hp - y))
        d.line(pts, fill=(20, 40, 120), width=4)
        im.save(path)
    m = bpy.data.materials.new("ChartPaper"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1, 0.3, 1)
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.extension = 'CLIP'
    L.new(tc.outputs['UV'], mp.inputs['Vector']); L.new(mp.outputs[0], t.inputs['Vector']); L.new(t.outputs['Color'], p.inputs['Base Color'])
    d = mp.inputs['Location'].driver_add("default_value", 1).driver; d.type = 'SCRIPTED'; d.expression = "min(0.7, frame * 0.0045)"
    p.inputs['Roughness'].default_value = 0.8
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=12, size=1)
    o = bpy.context.active_object; o.name = "ChartStrip"; o.scale = (0.3, 0.45, 1); bpy.ops.object.transform_apply(scale=True)
    for v in o.data.vertices:                                             # flat on top, then curling over the front edge and down
        u = (v.co.y + 0.225) / 0.45
        if u < 0.4:
            v.co.y, v.co.z = -0.12 + 0.3 * (0.4 - u) / 0.4 * 0.4, 0.235
        else:
            a = (u - 0.4) / 0.6 * math.pi * 0.55
            v.co.y = -0.18 - 0.05 * math.sin(a); v.co.z = 0.235 - 0.27 * (u - 0.4) / 0.6
    o.data.materials.append(m); o.parent = body
    pen = joinm([box("PenArm", (0, 0, 0.0), (0.008, 0.16, 0.006), pbr("PenArmM", (0.7, 0.7, 0.7), 0.3, 1.0)),
                 cyl("PenTip", (0, -0.08, -0.006), 0.004, 0.012, pbr("PenInk", (0.05, 0.1, 0.4), 0.4), verts=10)], "PenArm")
    pen.parent = body; pen.location = (0.0, -0.06, 0.245)
    dd = pen.driver_add("location", 0).driver; dd.type = 'SCRIPTED'
    dd.expression = "-0.13 + 0.26 * (0.82 - 0.74 * min(1, max(0, (frame * 0.0045 / 0.7 - 0.25) / 0.45)) ** 0.8)"
    return body


def analyser(loc, rot_z=0.0):
    """A beige laboratory analyser with a small printer: the paper tape feeds out (frame driver)."""
    beige = plastic("AnBeige", (0.66, 0.64, 0.57), 0.45)
    dark = pbr("AnDark", (0.1, 0.1, 0.1), 0.5)
    parts = [box("AnBody", (0, 0, 0.3), (0.7, 0.55, 0.6), beige, bevel=0.015),
             box("AnPanel", (0.0, -0.28, 0.42), (0.5, 0.01, 0.22), dark),
             box("AnPrinter", (0.42, -0.05, 0.12), (0.22, 0.3, 0.24), beige, bevel=0.01),
             box("AnSlot", (0.42, -0.2, 0.2), (0.16, 0.01, 0.01), dark)]
    for k in range(5):
        parts.append(cyl("AnKnob", (-0.18 + k * 0.09, -0.29, 0.25), 0.015, 0.02, dark, verts=12, rot=(math.radians(90), 0, 0)))
    body = joinm(parts, "Analyser"); body.location = loc; body.rotation_euler = (0, 0, rot_z)
    led = box("AnLED", (-0.2, -0.29, 0.5), (0.03, 0.005, 0.015), None); led.parent = body
    lm = bpy.data.materials.new("AnLED"); lm.use_nodes = True
    N = lm.node_tree.nodes; N.clear(); o = N.new("ShaderNodeOutputMaterial"); e = N.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (1.0, 0.25, 0.1, 1)
    v = N.new("ShaderNodeValue"); dd = v.outputs[0].driver_add("default_value").driver; dd.type = 'SCRIPTED'; dd.expression = "5 * (1 if (frame % 20) < 10 else 0.1)"
    lm.node_tree.links.new(v.outputs[0], e.inputs['Strength']); lm.node_tree.links.new(e.outputs[0], o.inputs['Surface']); led.data.materials.append(lm)
    import paper_tex
    tape = image_plane("PrintTape", paper_tex.make_all()["pages"][3], (0, 0, 0), (0.15, 0.3), (0, 0, 0), rough=0.8)
    tape.parent = body; tape.location = (0.42, -0.21, 0.2); tape.rotation_euler = (math.radians(100), 0, 0)
    dt = tape.driver_add("scale", 1).driver; dt.type = 'SCRIPTED'; dt.expression = "0.05 + min(0.95, frame * 0.008)"
    dl = tape.driver_add("location", 2).driver; dl.type = 'SCRIPTED'; dl.expression = "0.2 - 0.15 * (0.05 + min(0.95, frame * 0.008))"
    return body


def manila_file(name, page_k=0, label=None):
    import paper_tex
    pages = paper_tex.make_all()["pages"]
    f = joinm([box(name + "Cover", (0, 0, 0), (0.24, 0.32, 0.006), pbr("FileManila", (0.6, 0.48, 0.28), 0.8), bevel=0.001)], name)
    if label:
        t = text_obj(name + "Tab", label, (0.0, 0.08, 0.0035), 0.022, pbr("FileInk", (0.05, 0.05, 0.08), 0.5), rot=(0, 0, 0), extrude=0.0)
        t.parent = f; t.location = (0.0, 0.08, 0.0035)
    return f


def photocopy(name, k):
    import paper_tex
    pages = paper_tex.make_all()["pages"]
    return image_plane(name, pages[k % len(pages)], (0, 0, 0), (0.21, 0.297), (0, 0, 0), rough=0.8)


# ============================================================================ build
def build(variant=None):
    variant = variant or "lab95"
    c = {"variant": variant}
    y18 = variant == "y2018"
    world_flat((0.5, 0.55, 0.62), 1.0)
    floor = ph.texture("old_linoleum_flooring_01" if not y18 else "worn_tile_floor", scale=0.6)
    walls = two_tone("LabWalls", low=(0.5, 0.55, 0.55), high=(0.74, 0.74, 0.7), dado=1.2)
    box("Floor", (0, 0, -0.01), (W, D, 0.02), floor); box("Ceiling", (0, 0, H), (W, D, 0.04), pbr("LabCeil", (0.7, 0.7, 0.68), 0.9))
    box("WallBack", (0, D / 2 + 0.05, H / 2), (W, 0.1, H), walls); box("WallFront", (0, -D / 2 - 0.05, H / 2), (W, 0.1, H), walls)
    box("WallR", (W / 2 + 0.05, 0, H / 2), (0.1, D, H), walls)
    for (y0, y1) in ((-D / 2, -1.6), (-0.2, 0.6), (2.0, D / 2)):
        box("WallL", (-W / 2 - 0.05, (y0 + y1) / 2, H / 2), (0.1, y1 - y0, H), walls)
    for y in (-0.9, 1.3):
        box("WinUnder", (-W / 2 - 0.05, y, 0.45), (0.1, 1.4, 0.9), walls); box("WinOver", (-W / 2 - 0.05, y, 2.85), (0.1, 1.4, 0.5), walls)
        box("WinGlass", (-W / 2 - 0.06, y, 1.75), (0.01, 1.4, 1.7), glass("LabGlass", (0.92, 0.95, 0.96), 0.02))
        window_light(-W / 2 - 0.5, y, 0, 120 if variant != "end" else 40, (0.88, 0.92, 1.0))
        for k in range(12):                                                   # venetian blinds
            box("Blind", (-W / 2 + 0.06, y, 1.0 + k * 0.13), (0.04, 1.4, 0.005), pbr("BlindM", (0.8, 0.8, 0.78), 0.5), rot=(0, math.radians(-40), 0))
    box("LabOutside", (-W / 2 - 18, 0, 8), (1, 40, 20), masonry_facade("LabOpp", (0.55, 0.52, 0.45), 3.2, 2.6, 1.2, 1.6, 0.0))
    # ceiling lights: driven so the final shot can switch them off
    c["ceiling_lights"] = []
    for x in (-2.0, 1.0):
        for y in (-1.2, 1.4):
            ph.model("mounted_fluorescent_lights", loc=(x, y, H - 0.02), rot_z=math.radians(90))
            l = area_light((x, y, H - 0.12), (0, 0, 0), 1.0, 20, (0.92, 0.97, 1.0)); l.visible_camera = False
            c["ceiling_lights"].append(l)
    # benches and furniture (scanned)
    lt, top, ltp = light_table(LT); c["lt_glow"] = ltp
    for (x, y, rz) in ((1.9, 1.85, 0.0), (1.6, -1.95, math.pi)):
        r, _ = ph.model("painted_wooden_table", loc=(x, y, 0), rot_z=rz, scale=0.9)
    r, fc = ph.model("drawer_cabinet", loc=(W / 2 - 0.3, -0.3, 0), rot_z=math.radians(-90)); retint(fc, (0.7, 0.72, 0.7))
    c["file_drawers"] = sorted([o for o in fc if "_drawer_" in o.name], key=lambda o: o.name)
    for o in c["file_drawers"]:
        o["y0"] = o.location.y
    r, _ = ph.model("vintage_cabinet_01", loc=(-0.6, D / 2 - 0.35, 0))
    # lab dressing: a fume hood, steel shelving with glassware, wall charts, stools, a sink
    from pbkit import fume_hood, wall_chart, ph_instances
    fume_hood((W / 2 - 0.45, 2.1, 0), math.radians(90))
    ph_instances("Shelf_01", [((x, -D / 2 + 0.2, 0), math.pi, 1.0) for x in (-2.8, -1.7)])
    ph_instances("chemistry_set", [((x, -D / 2 + 0.3, z), math.pi, 0.9) for x in (-2.8, -1.7) for z in (0.42, 1.12, 1.62)])
    if not y18:
        ph_instances("metal_stool_01", [((1.0, 1.3, 0), 0.3, 1.0), ((2.3, 1.25, 0), 1.2, 1.0), ((1.2, -1.3, 0), 0.8, 1.0)])
    gen = os.path.join(HERE, "..", "assets", "generated")
    for k, (x, kind) in enumerate(((-2.2, "grid"), (0.3, "mol"), (2.6, "grid"))):
        image_plane(f"WallChart{k}", wall_chart(os.path.join(gen, f"labchart_{kind}{k}.png"), kind, k), (x, D / 2 - 0.02, 1.9), (0.6, 0.82),
                    (math.radians(90), 0, 0), rough=0.7)
    box("Sink", (-W / 2 + 0.45, -2.3, 0.85), (0.6, 0.9, 0.12), pbr("SinkSteel", (0.6, 0.6, 0.62), 0.25, 1.0))
    box("SinkCab", (-W / 2 + 0.45, -2.3, 0.4), (0.6, 0.9, 0.8), pbr("SinkCabM", (0.6, 0.62, 0.6), 0.5))
    if not y18:
        r, _ = ph.model("chemistry_set", loc=(2.4, 1.85, 0.865), rot_z=math.pi)
        r, _ = ph.model("industrial_microscope", loc=(1.0, 1.85, 0.865), rot_z=math.pi)
    for k in range(3):
        ph.model("SchoolChair_01", loc=(-2.5 + k * 1.9, -0.2 + 0.4 * (k % 2), 0), rot_z=rng.uniform(-0.4, 0.4))
    c["recorder"] = chart_recorder((REC.x - 0.45, REC.y, 0.864 + 0.0), math.pi)
    c["analyser"] = analyser((REC.x + 0.35, REC.y, 0.864), math.pi)
    tabz = 0.864 + 0.0
    c["bench_z"] = tabz
    # files and pages on the light table
    import paper_tex
    pages = paper_tex.make_all()["pages"]
    c["fileA"] = manila_file("HospFileA"); c["fileB"] = manila_file("HospFileB")
    c["fileA"].location = (LT.x - 0.28, LT.y - 0.05, LT.z + 0.012); c["fileB"].location = (LT.x + 0.3, LT.y - 0.05, LT.z + 0.012)
    c["saratov"] = manila_file("SaratovFile", label="САРАТОВ")
    c["saratov"].hide_render = True
    # the ampoule case on the side bench (evid / end variants); the evidence photo
    c["case"], c["lid"], c["amps"] = ampoule_case((CASE.x, CASE.y - 0.1, tabz + 0.002), 9, 7)
    c["lid"].rotation_euler = (math.radians(-100), 0, 0)
    c["photo"] = image_plane("EvidencePhoto", PHOTO, (LT.x + 0.05, LT.y + 0.05, LT.z + 0.013), (0.25, 0.185), (0, 0, math.radians(-4)), rough=0.35)
    if variant not in ("end",):
        c["photo"].hide_render = True
    if variant != "end" and variant != "evid":
        c["case"].hide_render = True
        for o in bpy.data.objects:
            if o.parent and (o.parent == c["case"] or o.parent == c["lid"] or (o.parent.parent == c["case"])):
                o.hide_render = True
    # raking lamp over the case
    rl = bpy.data.lights.new("RakeLamp", 'SPOT'); rl.energy = 18 if variant in ("evid", "end") else 0; rl.spot_size = math.radians(40); rl.spot_blend = 0.6; rl.color = (1.0, 0.9, 0.75)
    ro = bpy.data.objects.new("RakeLamp", rl); bpy.context.collection.objects.link(ro); ro.location = (CASE.x - 0.7, CASE.y - 0.5, tabz + 0.35); point_at(ro, (CASE.x, CASE.y - 0.1, tabz))
    c["rake"] = ro
    # people
    P = {}
    if variant == "lab95":
        P["exp1"] = medic("Expert1", 1.0, 52, "short04"); P["exp2"] = medic("Expert2", 0.0, 44, "bob02")
        P["analyst"] = medic("Analyst", 0.0, 33, "ponytail01")
    if variant == "evid":
        P["pros"] = person("Prosecutor", 1.0, 50, "male_elegantsuit01", "short04", cval=0.12, hv=0.4, sat=0.2)
        P["coll"] = person("Colleague", 1.0, 38, "male_elegantsuit01", "short02", cval=0.25, hv=0.2, hue=0.6, sat=0.4)
    if y18:
        for o in c["file_drawers"]:
            pass
        P["reporter"] = person("Reporter", 0.0, 36, "female_casualsuit01", "long01", cval=0.3, hv=0.25)
        P["spec1"] = person("Spec1", 1.0, 68, "male_elegantsuit01", "short04", cval=0.2, hv=0.7, sat=0.0)
        P["spec2"] = person("Spec2", 1.0, 55, "male_casualsuit03", "short02", cval=0.25, hv=0.4, sat=0.2)
        r, cam = ph.model("Camera_01"); c["camera_prop"] = r
        for k in range(5):
            pg = photocopy(f"Copy{k}", k); pg.location = (LT.x - 0.35 + k * 0.17, LT.y + 0.12 - 0.08 * (k % 2), LT.z + 0.012 + k * 0.0005)
            pg.rotation_euler = (0, 0, rng.uniform(-0.15, 0.15))
        dl = bpy.data.lights.new("ReporterLamp", 'SPOT'); dl.energy = 35; dl.spot_size = math.radians(60); dl.color = (1.0, 0.85, 0.65)
        do = bpy.data.objects.new("ReporterLamp", dl); bpy.context.collection.objects.link(do); do.location = (LT.x, LT.y + 0.2, 1.8); point_at(do, (LT.x, LT.y, LT.z))
        c["fileA"].hide_render = True; c["fileB"].hide_render = True
        c["sheetB"] = photocopy("PushPage", 2); c["sheetB"].location = (1.9, 1.75, 0.868); c["sheetB"].rotation_euler = (0, 0, 0.1)
    c["people"] = P
    animate(c, 0.0, None)
    return c


# ============================================================================ animation
def animate(c, sec, move):
    fn = ANIM.get(move)
    if fn:
        fn(c, sec)
    bpy.context.view_layer.update()


def a_compare(c, sec):
    """Two experts at the light table: she lays the second hospital file beside the first; he leans in."""
    e1, e2 = c["people"]["exp1"], c["people"]["exp2"]
    hide(c["people"]["analyst"], True)
    stand(e1, (LT.x - 0.35, LT.y - 0.75, 0), math.radians(180 - 10))                 # faces +Y, the table
    stand(e2, (LT.x + 0.4, LT.y - 0.72, 0), math.radians(180 + 15))
    k = ease(min(1.0, max(0.0, (sec - 0.5) / 2.2)))
    fb = c["fileB"]; fb.location = Vector((LT.x + 0.55, LT.y - 0.45, LT.z + 0.15)).lerp(Vector((LT.x + 0.3, LT.y - 0.05, LT.z + 0.012)), k)
    fb.rotation_euler = (math.radians(20 * (1 - k)), 0, 0)
    hand_to(e2, "R", fb.location + Vector((0.08, -0.12, 0.04)), curl=30); hand_to(e2, "L", fb.location + Vector((-0.08, -0.12, 0.04)), curl=30)
    nod(e2, "spine04", 14); nod(e2, "head", 18)
    nod(e1, "spine04", 18 + 4 * k); nod(e1, "head", 20)
    hand_to(e1, "R", Vector((LT.x - 0.2, LT.y - 0.25, LT.z + 0.05)), hand_dir=Vector((0, 0.6, -0.8)), curl=15)
    hand_to(e1, "L", Vector((LT.x - 0.5, LT.y - 0.3, LT.z + 0.05)), hand_dir=Vector((0, 0.6, -0.8)), curl=15)


def a_recorder(c, sec):
    """The strip-chart recorder runs; a technician in the background writes in a log."""
    for k in ("exp1", "exp2"):
        hide(c["people"][k], True)
    an = c["people"]["analyst"]
    seat(an, (REC.x + 0.95, REC.y + 0.8, 0), math.radians(180 + 70), lean=16)
    nod(an, "head", 16)
    hand_to(an, "R", an.bone_head("spine03") + fwd(an) * 0.35 + Vector((0, 0, -0.3)), curl=40)


def a_gc(c, sec):
    """She watches the analyser print its tape."""
    for k in ("exp1", "exp2"):
        hide(c["people"][k], True)
    an = c["people"]["analyst"]
    stand(an, (REC.x + 0.35, REC.y + 0.75, 0), 0.0)                                   # faces -Y, the instrument
    nod(an, "spine04", 10); nod(an, "head", 14)
    look(an, c["analyser"].matrix_world @ Vector((0.42, -0.25, 0.15)), 0.6)
    hand_to(an, "L", Vector((REC.x + 0.1, REC.y + 0.2, 0.84)), hand_dir=Vector((0, -0.6, -0.8)), curl=15)


def a_saratov(c, sec):
    """She pulls a file marked SARATOV from the cabinet drawer and turns with it."""
    for k in ("exp1", "exp2"):
        hide(c["people"][k], True)
    an = c["people"]["analyst"]
    stand(an, (W / 2 - 1.2, -0.3, 0), math.radians(90))                            # faces +X, the cabinet
    dr = c["file_drawers"][1]; dr.location.y = dr["y0"] - 0.34
    bpy.context.view_layer.update()
    lo, hi = ph.bounds([dr]); top = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))
    k = ease(min(1.0, max(0.0, (sec - 0.8) / 2.0)))
    f = c["saratov"]; f.hide_render = False
    p = (top + Vector((0, 0, 0.05))).lerp(an.bone_head("spine03") + fwd(an) * 0.3 + Vector((0, 0, 0.0)), k)
    f.location = p; f.rotation_euler = (math.radians(90 - 30 * k), 0, math.radians(90))
    nod(an, "spine04", 10 * (1 - k)); nod(an, "head", 18)
    hand_to(an, "R", p + Vector((0, -0.1, 0.1)), curl=45); hand_to(an, "L", p + Vector((0, 0.1, 0.05)), curl=35)


def a_ampoules(c, sec):
    """The case of sealed ampoules; the raking lamp drifts slowly along it."""
    for k in ("pros", "coll"):
        hide(c["people"][k], True)
    r = c["rake"]; z = c["bench_z"]
    r.location = Vector((CASE.x - 0.75 + 0.25 * ease(sec / DUR["ampoules"]), CASE.y - 0.55, z + 0.35)); point_at(r, (CASE.x, CASE.y - 0.1, z))


def a_slide(c, sec):
    """At the bench, the prosecutor slides a file across to his colleague."""
    p, q = c["people"]["pros"], c["people"]["coll"]
    stand(p, (-1.6, LT.y - 0.8, 0), math.radians(180))                              # faces +Y
    stand(q, (-1.6, LT.y + 0.85, 0), 0.0)                                           # faces -Y, across the light table
    k = ease(min(1.0, max(0.0, (sec - 0.6) / 2.5)))
    f = c["fileA"]; c["fileB"].hide_render = True
    f.location = Vector((LT.x, LT.y - 0.18, LT.z + 0.012)).lerp(Vector((LT.x, LT.y + 0.22, LT.z + 0.012)), k)
    nod(p, "spine04", 18 * (1 - 0.5 * k) + 6); nod(p, "head", 14)
    hand_to(p, "R", f.location + Vector((0.05, -0.12, 0.04)), hand_dir=Vector((0, 0.7, -0.6)), curl=20)
    hand_to(p, "L", Vector((LT.x - 0.35, LT.y - 0.3, LT.z + 0.04)), hand_dir=Vector((0, 0.7, -0.6)), curl=15)
    nod(q, "spine04", 12); nod(q, "head", 18)
    if k > 0.8:
        hand_to(q, "R", f.location + Vector((-0.05, 0.12, 0.04)), hand_dir=Vector((0, -0.7, -0.6)), curl=20)


def a_photocopies(c, sec):
    """2018: the reporter photographs the photocopied pages under a lamp."""
    for k in ("spec1", "spec2"):
        hide(c["people"][k], True)
    rp = c["people"]["reporter"]
    stand(rp, (LT.x - 0.05, LT.y - 0.62, 0), math.radians(180))
    nod(rp, "spine04", 14); nod(rp, "spine03", 6); nod(rp, "head", 22)
    cam = c["camera_prop"]
    shot = 1.0 if (sec % 1.8) < 0.15 else 0.0
    p = rp.bone_head("head") + fwd(rp) * 0.17 + Vector((0, 0, -0.07 - 0.01 * shot))
    cam.location = p; cam.rotation_euler = (math.radians(-60), 0, 0)
    hand_to(rp, "R", p + Vector((0.075, -0.02, -0.04)), curl=50); hand_to(rp, "L", p + Vector((-0.075, -0.02, -0.05)), curl=40)
    # she slides the next page under the lamp now and then
    pg = bpy.data.objects.get("Copy2")
    if pg:
        k = ease(min(1.0, max(0.0, (sec - 2.5) / 1.2)))
        pg.location.x = LT.x - 0.01 + 0.25 * (1 - k)


def a_specialists(c, sec):
    """Two specialists across a table; one slides a page back across to the other."""
    hide(c["people"]["reporter"], True)
    c["camera_prop"].location = (LT.x + 0.4, LT.y + 0.2, LT.z + 0.02)
    s1, s2 = c["people"]["spec1"], c["people"]["spec2"]
    seat(s1, (1.9, 1.05, 0), math.radians(180), lean=16)                          # faces +Y
    seat(s2, (1.9, 2.55, 0), 0.0, lean=14)                                          # faces -Y (other side of the bench)
    hide(s2, False)
    k = ease(min(1.0, max(0.0, (sec - 1.0) / 2.0)))
    pg = c["sheetB"]; pg.location = Vector((1.9, 1.95, 0.868)).lerp(Vector((1.9, 1.55, 0.868)), k)
    hand_to(s2, "R", pg.location + Vector((0.04, 0.12, 0.04)), hand_dir=Vector((0, -0.7, -0.6)), curl=20)
    nod(s2, "head", 12); nod(s1, "head", 14); look(s1, pg.location, 0.5)
    hand_to(s1, "L", Vector((1.75, 1.45, 0.82)), hand_dir=Vector((0, 0.7, -0.6)), curl=20)


def a_photo(c, sec):
    pass


def a_case_close(c, sec):
    """The lid of the case comes down over the empty slots; then the room's lights go out, one after another."""
    k = ease(min(1.0, max(0.0, (sec - 0.8) / 2.4)))
    c["lid"].rotation_euler = (math.radians(-100 * (1 - k)), 0, 0)
    for i, l in enumerate(c["ceiling_lights"]):
        l.data.energy = 20 if sec < 4.0 + 0.5 * i else 0
    c["rake"].data.energy = 18 if sec < 5.8 else 0
    c["lt_glow"].inputs['Emission Strength'].default_value = 1.5 if sec < 6.2 else 0.0


ANIM = {"compare": a_compare, "recorder": a_recorder, "gc_print": a_gc, "saratov": a_saratov, "ampoules": a_ampoules, "slide_file": a_slide,
        "photocopies": a_photocopies, "specialists": a_specialists, "photo": a_photo, "case_close": a_case_close}


def _anim(move):
    return lambda c, t: animate(c, t * DUR[move], move)


def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


Z = 0.864
MOVES = {
    "compare": dict(kind="anim", dof=3.2, far=12.0, anim=_anim("compare"), cam=_push((-0.2, 1.9, 1.75), (-0.4, 1.75, 1.7), (LT.x, LT.y - 0.3, 1.1), (LT.x, LT.y - 0.25, 1.05), 32),
                    focus=lambda c, t: LT + Vector((0, -0.3, 0.3))),
    "recorder": dict(kind="anim", dof=2.4, far=10.0, anim=_anim("recorder"), cam=_push((REC.x - 0.9, REC.y + 0.75, Z + 0.55), (REC.x - 0.75, REC.y + 0.6, Z + 0.48), (REC.x - 0.45, REC.y, Z + 0.15), (REC.x - 0.45, REC.y, Z + 0.15), 42),
                     focus=lambda c, t: Vector((REC.x - 0.45, REC.y - 0.1, Z + 0.2))),
    "gc_print": dict(kind="anim", dof=3.2, far=10.0, anim=_anim("gc_print"), cam=_push((REC.x - 1.3, REC.y + 1.6, 1.6), (REC.x - 1.1, REC.y + 1.4, 1.55), (REC.x + 0.3, REC.y, 1.1), (REC.x + 0.35, REC.y + 0.1, 1.1), 32),
                     focus=lambda c, t: Vector((REC.x + 0.35, REC.y + 0.4, 1.2))),
    "saratov": dict(kind="anim", dof=3.2, far=10.0, anim=_anim("saratov"), cam=_push((0.9, 0.9, 1.6), (1.15, 0.8, 1.58), (W / 2 - 0.6, -0.4, 1.15), (W / 2 - 0.9, -0.35, 1.2), 32),
                    focus=lambda c, t: Vector((W / 2 - 1.0, -0.3, 1.25))),
    "ampoules": dict(kind="anim", dof=1.8, far=6.0, anim=_anim("ampoules"),
                     cam=_push((CASE.x - 0.5, CASE.y - 0.75, Z + 0.42), (CASE.x - 0.32, CASE.y - 0.55, Z + 0.32), (CASE.x, CASE.y - 0.1, Z + 0.05), (CASE.x + 0.03, CASE.y - 0.08, Z + 0.05), 50),
                     focus=lambda c, t: Vector((CASE.x, CASE.y - 0.07, Z + 0.06))),
    "slide_file": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("slide_file"), cam=_push((1.3, -1.7, 1.75), (1.05, -1.45, 1.72), (LT.x, LT.y, 1.2), (LT.x, LT.y + 0.05, 1.15), 30),
                       focus=lambda c, t: LT + Vector((0, 0.1, 0.2))),
    "photocopies": dict(kind="anim", dof=3.2, far=10.0, anim=_anim("photocopies"), cam=_push((-0.3, 1.55, 1.75), (-0.42, 1.42, 1.7), (LT.x, LT.y - 0.4, 1.25), (LT.x, LT.y - 0.35, 1.2), 30),
                        focus=lambda c, t: LT + Vector((0, -0.4, 0.5))),
    "specialists": dict(kind="anim", dof=3.6, far=10.0, anim=_anim("specialists"), cam=_push((-0.2, 1.8, 1.4), (0.0, 1.85, 1.38), (1.9, 1.8, 1.1), (1.9, 1.8, 1.1), 30),
                        focus=lambda c, t: Vector((1.9, 1.8, 1.1))),
    "photo": dict(kind="anim", dof=2.0, far=6.0, anim=_anim("photo"), cam=_push((LT.x - 0.35, LT.y - 0.7, 1.55), (LT.x - 0.1, LT.y - 0.28, 1.25), (LT.x + 0.05, LT.y + 0.05, LT.z), (LT.x + 0.05, LT.y + 0.05, LT.z), 40),
                  focus=lambda c, t: LT + Vector((0.05, 0.05, 0.01))),
    "case_close": dict(kind="anim", dof=2.8, far=10.0, anim=_anim("case_close"),
                       cam=_push((CASE.x - 0.8, CASE.y - 1.1, Z + 0.6), (CASE.x - 0.6, CASE.y - 0.85, Z + 0.5), (CASE.x, CASE.y - 0.1, Z + 0.05), (CASE.x, CASE.y - 0.1, Z + 0.05), 40),
                       focus=lambda c, t: Vector((CASE.x, CASE.y - 0.1, Z + 0.05))),
}


_build_set = build


def build(variant=None):
    c = _build_set(variant)
    from pbkit import finish_scene
    finish_scene()
    return c
