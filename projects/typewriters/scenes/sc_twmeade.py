"""FORT MEADE LAB, summer 1984 (dramatization; technicians unnamed). One long room: benches of opened machines,
a wall of lightboxes, an X-ray cabinet, cleared crates by the door, a calendar. Variants: day / night (one lamp on).
Also hosts the 1978 inspection (Ch3 7) with a period-shifted dressing of the same room.

Ch2 1A  team       title over the wide lab: technicians at benches opening machines
Ch2 1B  calendar   a wall calendar page turns; a technician carries a cipher box to a bench
Ch2 2A  clear      a technician closes a cipher machine and hangs a CLEAR tag on it
Ch2 2B  stack      a cleared crate is lowered onto the stack by the door
Ch2 3A  row        a row of typewriters on the long bench; the first cover lifts
Ch2 3B  covers     track down the row as the covers come off one by one
Ch2 4A  lone       night: one figure under the magnifier lamp in the empty lab
Ch2 4B  coil       night: push into the opened machine, to the extra coil beside the power switch
Ch2 5A  cabinet    the typewriter slides into the X-ray cabinet; the red lamp comes on
Ch2 5B  film       the film is clipped onto a lightbox, which flickers on: the bar full of parts
Ch2 7A  debate     morning: three engineers at the lightbox; one taps the film
Ch2 7B  memory     a memory typewriter on the shelf behind them, its cover open
Ch2 8A  pair       two opened machines side by side, both bars lifted out
Ch2 8B  barlid     the altered bar's cover slides off: the radio inside
Ch3 6B  bars       two versions of the bar on the bench: wired-in, and with batteries
Ch3 7A  inspect78  1978: an inspector X-rays a typewriter's motor end
Ch3 7B  motorfilm  the motor film on the lightbox looks normal
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import *
import ph
import twp
import machines as MC
import typewriter as T

EXPOSURE = 0.0
DUR = {k: 5.0 for k in ("team", "calendar", "clear", "stack", "row", "covers", "lone", "coil", "cabinet", "film", "debate", "memory",
                        "pair", "barlid", "bars", "inspect78", "motorfilm")}
DUR["team"] = 6.0
VARIANT_FOR = {"lone": "night", "coil": "night", "film": "night"}
ROW_Y = -0.6                    # the long typewriter bench
LB = Vector((6.9, 1.2, 1.55))   # lightbox wall centre (on the +X wall)
XC = Vector((5.6, 3.1, 0.0))    # X-ray cabinet
PAIR = Vector((-3.0, 2.4, 0.905))


def bench(x, y, L_, top, legm, rot=0.0):
    box("BenchTop", (x, y, 0.88), (L_, 0.8, 0.05), top, bevel=0.005, rot=(0, 0, rot))
    for dx in (-L_ / 2 + 0.1, L_ / 2 - 0.1):
        for dy in (-0.32, 0.32):
            box("BenchLeg", (x + dx, y + dy, 0.43), (0.05, 0.05, 0.86), legm)
    box("BenchShelf", (x, y, 0.25), (L_ - 0.1, 0.7, 0.02), legm)


def film_mat(name, path):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord"); im = N.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(path, check_existing=True); L.new(tc.outputs['UV'], im.inputs['Vector'])
    on = N.new("ShaderNodeValue"); on.name = "On"
    em = N.new("ShaderNodeEmission"); L.new(im.outputs['Color'], em.inputs['Color'])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 2.4; L.new(on.outputs[0], st.inputs[0]); L.new(st.outputs[0], em.inputs['Strength'])
    df = N.new("ShaderNodeBsdfDiffuse"); df.inputs['Color'].default_value = (0.05, 0.06, 0.08, 1)
    ad = N.new("ShaderNodeAddShader"); L.new(df.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], out.inputs['Surface'])
    return m, on


def build(variant=None):
    c = {"variant": variant}
    night = variant == "night"
    rng = np.random.default_rng(41)
    if night:
        world_flat((0.004, 0.005, 0.009), 1.0)
    else:
        w = world_sky(sun_elev_deg=35, sun_rot_deg=110, strength=0.45, tint=(0.86, 0.9, 1.0)); w.node_tree.nodes["Sky Texture"].sun_disc = False
    # ---------------------------------------------------------------- room x -7..7, y -4..4, h 3.2; windows on -X, door on -Y
    box("Floor", (0, 0, -0.01), (14, 8, 0.02), ph.texture("old_linoleum_flooring_01", scale=0.5, name="MeadeFloor", tint=(0.52, 0.58, 0.58)))
    wall = ph.texture("painted_plaster_wall", scale=0.5, name="MeadeWall", tint=(0.74, 0.78, 0.76))
    box("WallBack", (0, 4.05, 1.6), (14, 0.1, 3.2), wall); box("WallR", (7.05, 0, 1.6), (0.1, 8, 3.2), wall)
    for x0, x1 in ((-7, -1.0), (0.2, 7)):
        box("WallFront", ((x0 + x1) / 2, -4.05, 1.6), (x1 - x0, 0.1, 3.2), wall)
    box("DoorHead", (-0.4, -4.05, 2.7), (1.2, 0.1, 1.0), wall)
    box("Ceiling", (0, 0, 3.22), (14, 8, 0.04), ph.texture("ceiling_interior", scale=0.5, name="MeadeCeil"))
    for z, h in ((0.5, 1.0), (2.95, 0.5)):
        box("WallL", (-7.05, 0, z), (0.1, 8, h), wall)
    for y in (-3.8, -1.3, 1.2, 3.8):
        box("WinPierL", (-7.05, y, 1.85), (0.1, 0.6, 1.7), wall)
    for yc in (-2.55, -0.05, 2.5):
        box("MeadeGlass", (-7.04, yc, 1.85), (0.01, 1.9, 1.7), glass("MeadeGlassM", (0.9, 0.93, 0.95)))
        twp.venetian(-6.95, yc, 1.0, 2.68, 1.9, "y", pbr("MeadeBlind", (0.72, 0.71, 0.66), 0.5), tilt=-50 if not night else -10)
    box("MeadeOutside", (-30, 0, 6), (1, 60, 16), ph.texture("concrete_wall_008", scale=0.2, name="MeadeOut"))
    if not night:
        sn = bpy.data.lights.new("Sun", 'SUN'); sn.energy = 2.0; sn.angle = math.radians(2); sn.color = (1.0, 0.95, 0.88)
        so = bpy.data.objects.new("Sun", sn); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(55), math.radians(35), math.radians(90))
        pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 8.0; pt.size_y = 1.7; pt.cycles.is_portal = True
        po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (-7.0, 0, 1.85); po.rotation_euler = (0, math.radians(90), 0)
    for x in (-4.5, -1.5, 1.5, 4.5):
        for y in (-1.8, 1.6):
            ph.model("mounted_fluorescent_lights", loc=(x, y, 3.2), rot_z=0)
            if not night:
                l = area_light((x, y, 3.12), (0, 0, 0), 0.9, 32, (0.9, 0.96, 1.0)); l.visible_camera = False
    # ---------------------------------------------------------------- benches
    top = ph.texture("oak_veneer_01", scale=1.0, name="MeadeBench", tint=(0.8, 0.76, 0.7))
    legm = pbr("MeadeLeg", (0.25, 0.27, 0.26), 0.4, 0.7)
    bench(-1.2, ROW_Y, 8.0, top, legm)                         # the long typewriter bench
    bench(-3.0, 2.4, 3.2, top, legm)                           # the pair bench (side by side)
    bench(1.8, 2.4, 3.2, top, legm)                            # the teletype bench
    bench(-5.6, -2.8, 2.4, top, legm)
    c["row"] = []
    cols = [(0.11, 0.15, 0.2), (0.32, 0.28, 0.22), (0.2, 0.25, 0.3), (0.42, 0.12, 0.1), (0.22, 0.24, 0.2)]
    for k in range(9):
        tw = T.make(f"Row{k}", loc=(-4.6 + k * 0.82, ROW_Y + 0.05, 0.905), rot_z=0.0, color=cols[k % 5], mechanism=(k == 0), glyphs=False,
                    legends=False, text=" ", bugged=(k == 0), seed=k)
        tw["paper"].hide_render = True
        c["row"].append(tw)
    # the side-by-side pair: covers off, bars lifted out and laid in front
    c["pair"] = []
    for k, dx in enumerate((-0.55, 0.55)):
        tw = T.make(f"Pair{k}", loc=(PAIR.x + dx, PAIR.y + 0.08, PAIR.z), rot_z=0.0, color=(0.2, 0.25, 0.3), bugged=(k == 1), glyphs=False,
                    legends=False, text=" ", seed=10 + k)
        tw["paper"].hide_render = True
        T.set_cover(tw, hide=True)
        c["pair"].append(tw)
    # teletype bench, cipher machines, instruments, crates by the door, shelving, calendar
    r_tty, p_tty = MC.teletype("MeadeTTY", (1.2, 2.4, 0.905), math.pi, stand=False); c["tty_p"] = p_tty
    c["ciphers"] = []
    for k in range(3):
        r, lamps = MC.cipher(f"MCipher{k}", (2.2 + k * 0.62, 2.45, 0.905), math.pi, height=0.4); c["ciphers"].append(r)
    MC.lamp_blink()
    ph.model("industrial_microscope", loc=(-5.9, -2.7, 0.905), rot_z=0.4)
    ph.model("retro_multimeter", loc=(-5.2, -2.7, 0.905), rot_z=-0.2)
    import sc_twlab
    sc_twlab.oscilloscope("MeadeScope", (-5.6, -3.0, 0.905), math.radians(10))
    lamp_r, lamp_ms = ph.model("desk_lamp_arm_01", loc=(-4.25, ROW_Y + 0.35, 0.905), rot_z=math.radians(160)); twp.tint_model(lamp_ms, (0.2, 0.22, 0.2), 0.1)
    for k in range(6):
        ph.model("steel_frame_shelves_02", loc=(-6.4 + k * 0.62, 3.75, 0), rot_z=math.pi)
    for k in range(12):
        ph.model("cardboard_box_01", loc=(-6.4 + (k % 6) * 0.62, 3.75, 0.48 + (k // 6) * 0.72), rot_z=rng.uniform(-0.2, 0.2), scale=0.75)
    c["crates"] = []
    for k in range(5):
        o = MC.burlap_crate(f"Cleared{k}", size=(0.8, 0.6, 0.55)); o.location = (-2.4 + (k % 3) * 0.85, -3.55, 0.28 + (k // 3) * 0.56)
        c["crates"].append(o)
    c["new_crate"] = MC.burlap_crate("ClearedNew", size=(0.8, 0.6, 0.55))
    # calendar on the wall: a pad with a page that turns (hinged at the top)
    import skia
    def cal(path, month):
        sf = skia.Surface(500, 700); cv = sf.getCanvas(); cv.clear(skia.Color4f(0.93, 0.92, 0.88, 1))
        p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(0.15, 0.15, 0.18, 1))
        f = skia.Font(skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"), 60)
        cv.drawString(month, 250 - f.measureText(month) / 2, 330, f, p)
        f2 = skia.Font(skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"), 26)
        cv.drawString("1984", 220, 380, f2, p)
        for r in range(5):
            for k in range(7):
                cv.drawString(str(r * 7 + k + 1) if r * 7 + k < 31 else "", 40 + k * 64, 440 + r * 52, f2, p)
        sf.makeImageSnapshot().save(path, skia.kPNG); return path
    pages = []
    for k, mo in enumerate(("JUNE", "JULY")):
        m = bpy.data.materials.new(f"Cal{mo}"); m.use_nodes = True
        t = m.node_tree.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(cal(os.path.join(T.GEN, f"cal_{mo}.png"), mo))
        m.node_tree.links.new(t.outputs[0], m.node_tree.nodes["Principled BSDF"].inputs['Base Color']); pages.append(m)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-1.2, 3.99, 1.75), rotation=(math.radians(90), 0, math.pi))
    o = bpy.context.active_object; o.scale = (0.3, 0.42, 1); o.data.materials.append(pages[1])
    hinge = bpy.data.objects.new("CalHinge", None); bpy.context.collection.objects.link(hinge); hinge.location = (-1.2, 3.975, 1.96)
    bpy.ops.mesh.primitive_plane_add(size=1); pg = bpy.context.active_object; pg.scale = (0.3, 0.42, 1); bpy.ops.object.transform_apply(scale=True)
    pg.data.materials.append(pages[0]); pg.parent = hinge; pg.rotation_euler = (math.radians(90), 0, math.pi); pg.location = (0, 0, -0.21)
    c["cal"] = hinge
    # ---------------------------------------------------------------- lightbox wall and X-ray films
    import sc_twlab as L_
    boxes = L_.lightbox_wall(c, LB, math.pi / 2, 3)
    films = {}
    for nm in ("altered", "ordinary", "motor"):
        pth = os.path.join(T.GEN, f"xray_{nm}.png")
        if not os.path.exists(pth):
            import subprocess, sys as _s
        films[nm] = film_mat(f"Film_{nm}", pth) if os.path.exists(pth) else (pbr("FilmMissing", (0.1, 0.12, 0.15), 0.3), None)
    c["films"] = films
    opal = bpy.data.materials.get("Opal")
    c["opal_val"] = None
    if opal is not None:                                   # the lightboxes switch on by driver for the film shot
        p = opal.node_tree.nodes["Principled BSDF"]
        c["opal"] = p
    c["film_objs"] = []
    for k, lb in enumerate(boxes):
        bpy.ops.mesh.primitive_plane_add(size=1); f = bpy.context.active_object; f.name = f"Film{k}"; f.scale = (0.43, 0.34, 1)
        bpy.ops.object.transform_apply(scale=True)
        nm = ("ordinary", "altered", "motor")[k]
        f.data.materials.append(films[nm][0])
        f.parent = lb; f.location = (0, -0.008, 0); f.rotation_euler = (math.radians(90), 0, 0)
        c["film_objs"].append(f)
    # the X-ray cabinet: a steel box with a sliding drawer, a warning lamp, a control panel
    cab = pbr("XCab", (0.62, 0.64, 0.6), 0.4, 0.3)
    box("XCabinet", (XC.x, XC.y, 0.75), (1.2, 1.0, 1.5), cab, bevel=0.02)
    box("XCabOpening", (XC.x, XC.y - 0.49, 0.75), (0.92, 0.02, 0.5), pbr("XCabDark", (0.01, 0.01, 0.012), 0.6))
    xl = area_light((XC.x, XC.y - 0.9, 1.3), (0, 0, 0), 0.5, 20, (0.9, 0.95, 1.0)); point_at(xl, (XC.x, XC.y - 0.8, 0.6)); xl.visible_camera = False
    tray = join([box("Tray", (0, 0, 0), (0.85, 0.8, 0.03), pbr("TrayM", (0.55, 0.56, 0.57), 0.3, 0.9)),
                 box("TrayFront", (0, -0.41, 0.15), (0.9, 0.03, 0.42), cab)], "XTray")
    tray.location = (XC.x, XC.y, 0.56); c["tray"] = tray
    warn = pbr("XWarnM", (0.4, 0.03, 0.02), 0.3, 0.0, **{'Emission Color': (1.0, 0.08, 0.04, 1), 'Emission Strength': 0.0})
    cyl("XWarnLamp", (XC.x + 0.4, XC.y - 0.3, 1.56), 0.06, 0.1, warn, verts=16)
    c["warn"] = warn.node_tree.nodes["Principled BSDF"]
    box("XPanel", (XC.x - 0.35, XC.y - 0.505, 1.25), (0.35, 0.02, 0.2), pbr("XPanelM", (0.1, 0.1, 0.11), 0.4))
    c["xtw"] = T.make("XrayTW", loc=(0, 0, 0), color=(0.2, 0.25, 0.3), bugged=True, glyphs=False, legends=False, text=" ", mechanism=True)
    c["xtw"]["paper"].hide_render = True
    # a memory typewriter (an electronic model with a one-line display) on the shelf behind the lightboxes
    mem = T.make("MemoryTW", loc=(6.75, 2.75, 1.0), rot_z=math.pi / 2, color=(0.52, 0.5, 0.45), glyphs=False, legends=False, text=" ", mechanism=False)
    mem["paper"].hide_render = True
    T.set_cover(mem, open_deg=-70)
    box("MemShelf", (6.75, 2.75, 0.98), (0.6, 0.9, 0.03), legm)
    box("MemDisplay", (6.75 - 0.06, 2.75, 1.115), (0.02, 0.22, 0.03), pbr("MemLCD", (0.1, 0.14, 0.08), 0.2, 0.0, **{'Emission Color': (0.45, 0.6, 0.3, 1), 'Emission Strength': 0.8}))
    pcb = pbr("MemPCB", (0.08, 0.16, 0.09), 0.35, 0.0, **{'Coat Weight': 0.8})
    box("MemBoard", (6.75, 2.75, 1.06), (0.28, 0.3, 0.004), pcb)
    c["mem"] = mem
    # the two bar versions (Ch3 6B): a mains-wired one and one with a battery pack, on the pair bench's end
    for k, dx in enumerate((-0.12, 0.12)):
        b = box(f"LooseBar{k}", (PAIR.x + 1.25, PAIR.y - 0.2 + dx, PAIR.z + 0.01), (0.36, 0.022, 0.016), bpy.data.materials.get("TW_Alu") or legm)
        bl = box(f"LooseBarLid{k}", (PAIR.x + 1.25, PAIR.y - 0.2 + dx + 0.03, PAIR.z + 0.002), (0.36, 0.022, 0.0015), bpy.data.materials.get("TW_Alu") or legm)
        for j in range(10):
            box("LBChip", (PAIR.x + 1.1 + j * 0.03, PAIR.y - 0.2 + dx, PAIR.z + 0.019), (0.012, 0.008, 0.002), bpy.data.materials.get("TW_Chip") or legm)
        if k == 1:
            for j in range(3):
                cyl("Cell", (PAIR.x + 1.48 + j * 0.03, PAIR.y - 0.2 + dx, PAIR.z + 0.02), 0.012, 0.045, pbr("Cell", (0.3, 0.25, 0.15), 0.4, 0.4),
                    verts=16, rot=(math.radians(90), 0, 0))
        else:
            cyl("MainsLead", (PAIR.x + 1.6, PAIR.y - 0.2 + dx, PAIR.z + 0.01), 0.003, 0.2, pbr("LeadB", (0.03, 0.03, 0.03), 0.5), verts=6, rot=(0, math.radians(90), 0))
    # ---------------------------------------------------------------- people
    P = {}
    specs = [("TechA", 1.0, 34, "male_casualsuit02", "short03", 0.6, 0.55), ("TechB", 0.0, 29, "female_elegantsuit01", "ponytail01", 0.6, 0.1),
             ("TechC", 1.0, 47, "male_worksuit01", "short04", 0.5, 0.58), ("TechD", 1.0, 38, "male_casualsuit04", "short01", 0.55, 0.08),
             ("TechE", 0.0, 41, "female_elegantsuit01", "bob01", 0.6, 0.6), ("Arneson", 1.0, 36, "male_casualsuit03", "short02", 0.55, 0.35)]
    for nm, g, yrs, cl, hr, cv, hu in specs:
        P[nm] = twp.person(nm, g, yrs, cl, hr, hv=0.3, cval=cv, hue=hu, sat=0.25)
    c["P"] = P
    if night:
        lamp = bpy.data.lights.new("MagLamp", 'SPOT'); lamp.energy = 160; lamp.spot_size = math.radians(70); lamp.spot_blend = 0.6; lamp.color = (1.0, 0.82, 0.6)
        lo = bpy.data.objects.new("MagLamp", lamp); bpy.context.collection.objects.link(lo); lo.location = (-4.45, ROW_Y + 0.15, 1.45)
        point_at(lo, (-4.6, ROW_Y, 0.95))
        moon = area_light((-6.8, 0, 2.0), (0, 0, 0), 4.0, 12, (0.45, 0.55, 0.85)); point_at(moon, (0, 0, 0.8)); moon.visible_camera = False
        exitlight = area_light((-0.4, -3.9, 2.4), (0, 0, 0), 0.4, 4, (0.3, 0.9, 0.4)); exitlight.visible_camera = False
    animate(c, 0.0, "lone" if night else "team")
    return c


# ============================================================================ animation
def place(h, loc, face_z):
    twp.stand(h, loc, face_z)


def animate(c, sec, shot):
    from human import reach, fingers_curl
    P = c["P"]
    night = c["variant"] == "night"
    who = {"team": ["TechA", "TechB", "TechC", "TechD", "TechE"], "calendar": ["TechC", "TechB"], "clear": ["TechD"], "stack": ["TechC", "TechA"],
           "row": ["TechB", "TechA"], "covers": ["TechB", "TechA", "TechE"], "lone": ["Arneson"], "coil": [], "cabinet": ["Arneson"],
           "film": ["Arneson"], "debate": ["TechA", "TechC", "TechD"], "memory": ["TechA", "TechC", "TechD"], "pair": ["TechE"], "barlid": [],
           "bars": [], "inspect78": ["TechC"], "motorfilm": ["TechC"]}[shot]
    for k, h in P.items():
        twp.hide(twp.person_objs(h), k not in who)
    # covers: which typewriter lids are up
    n_up = {"row": 1 if sec > 1.8 else 0, "covers": min(9, 1 + int(sec / 0.6))}.get(shot, 0)
    for k, tw in enumerate(c["row"]):
        lift = 0.0
        if shot == "row" and k == 0:
            lift = ease(min(1.0, max(0.0, (sec - 1.2) / 1.6)))
        elif shot == "covers":
            lift = ease(min(1.0, max(0.0, (sec - k * 0.55) / 1.0)))
        elif shot in ("lone", "coil"):
            lift = 1.0 if k == 0 else 0.0
        T.set_cover(tw, open_deg=-95 * lift)
        if shot in ("lone", "coil") and k == 0:
            T.set_cover(tw, hide=True)                              # the machine opened up on the bench, its housing off
    tw0 = c["row"][0]
    # the calendar page
    c["cal"].rotation_euler = (math.radians(-170) * ease(min(1.0, max(0.0, (sec - 1.0) / 1.4))) if shot == "calendar" else 0, 0, 0)
    # X-ray cabinet tray, the typewriter on it, the warning lamp, lightboxes
    xtw = c["xtw"]; tray = c["tray"]
    slide = ease(min(1.0, max(0.0, (sec - 0.8) / 2.0))) if shot in ("cabinet", "inspect78") else 1.0
    tray.location = Vector((XC.x, XC.y - 0.9 * (1 - slide), 0.56))
    xtw["root"].location = tray.location + Vector((0, 0.02, 0.02))
    on = (shot in ("cabinet", "inspect78") and sec > 3.0)
    c["warn"].inputs['Emission Strength'].default_value = 14.0 if on else 0.0
    for o in [xtw["root"]] + list(xtw["root"].children_recursive):
        o.hide_render = shot not in ("cabinet", "inspect78")
    flick = 0.0
    if shot == "film":
        f = sec - 1.4
        flick = 0.0 if f < 0 else (1.0 if f > 0.5 else (1.0 if int(f * 24) % 3 else 0.2))
    elif shot in ("debate", "memory", "motorfilm", "team"):
        flick = 1.0
    for nm, (m, val) in c["films"].items():
        if val is not None:
            val.outputs[0].default_value = flick
    if "opal" in c:
        c["opal"].inputs['Emission Strength'].default_value = 2.2 * flick
    film_place = ease(min(1.0, sec / 1.2)) if shot == "film" else 1.0
    c["film_objs"][1].location = (0, -0.008, 0.25 * (1 - film_place))
    # people and their business
    tA, tB, tC, tD, tE, ar = (P[k] for k in ("TechA", "TechB", "TechC", "TechD", "TechE", "Arneson"))
    if shot == "team":
        place(tA, (-3.8, ROW_Y - 0.75, 0), math.pi); place(tB, (-1.4, ROW_Y - 0.75, 0), math.pi)
        place(tC, (1.6, 1.7, 0), 0.0); place(tD, (2.9, 1.7, 0), 0.0); place(tE, (-3.0, 1.7, 0), 0.0)
        for h, tgt in ((tA, Vector((-3.8, ROW_Y + 0.05, 1.0))), (tB, Vector((-1.35, ROW_Y + 0.05, 1.0))), (tC, Vector((1.4, 2.3, 1.05))),
                       (tD, Vector((2.9, 2.3, 1.0))), (tE, Vector((-3.0, 2.3, 1.0)))):
            for sd, dx in (("L", 0.15), ("R", -0.15)):
                reach(h, sd, tgt + Vector((dx + 0.03 * math.sin(sec * 2 + dx * 9), 0, 0.02 * math.sin(sec * 3))), Vector((dx * 4, 0, -0.8)), Vector((0, 0, -1)))
            h.rot("head", (1, 0, 0), 12)
    elif shot == "calendar":
        twp.walk(tC, (4.0, 0.6), (-2.0, 0.6), sec, speed=0.9)
        box_ = c["ciphers"][2]; box_.location = tC.bone_head("spine03") + twp.forward(tC) * 0.32 + Vector((0, 0, -0.35))
        box_.rotation_euler = (0, 0, tC.arm.rotation_euler.z + math.pi)
        for sd, sg in (("L", 1), ("R", -1)):
            side = twp.forward(tC).cross(Vector((0, 0, 1)))
            reach(tC, sd, box_.location + Vector((0, 0, 0.12)) + side * 0.28 * -sg, Vector((-sg * side.x, -sg * side.y, -0.8)), twp.forward(tC))
        place(tB, (-1.6, ROW_Y - 0.75, 0), math.pi)
    elif shot == "clear":
        cp = c["ciphers"][0]; place(tD, (cp.location.x, cp.location.y - 0.75, 0), math.pi)
        reach(tD, "R", cp.location + Vector((0.05, -0.25, 0.42 + 0.06 * (1 - ease(min(1.0, sec / 1.5))))), Vector((-0.5, -0.4, -0.7)), Vector((0, 1, -0.3)))
        reach(tD, "L", cp.location + Vector((-0.2, -0.28, 0.3)), Vector((0.5, -0.4, -0.7)), Vector((0, 1, 0)))
        tD.rot("head", (1, 0, 0), 14)
    elif shot == "stack":
        nc = c["new_crate"]; k = ease(min(1.0, max(0.0, (sec - 0.6) / 2.6)))
        tgt = Vector((-1.55, -3.55, 0.28 + 0.56)); start = tgt + Vector((0.2, 1.4, 0.35))
        nc.location = start.lerp(tgt, k) + Vector((0, 0, 0.15 * math.sin(math.pi * k)))
        for h, side in ((tC, -1), (tA, 1)):                    # both in front of the stack, lifting from the sides
            pos = Vector((nc.location.x + side * 0.42, nc.location.y + 0.62, 0)); place(h, (pos.x, pos.y, 0), side * 0.35)
            for sd, dy in (("L", 1), ("R", -1)):
                reach(h, sd, nc.location + Vector((side * 0.38, -0.05 * dy, 0.0)), Vector((side, 0.4, -0.7)), Vector((-side, -0.3, 0)))
    elif shot in ("row", "covers"):
        x = -4.6 + (n_up - 1) * 0.82 if shot == "covers" else -4.6
        place(tB, (x, ROW_Y - 0.8, 0), math.pi)
        lid_pt = T.world(c["row"][max(0, n_up - 1)], (0, 0.14, 0.2))
        reach(tB, "R", lid_pt + Vector((0.1, -0.12, 0.05)), Vector((-0.5, -0.4, -0.6)), Vector((0, 1, 0.3)))
        reach(tB, "L", lid_pt + Vector((-0.12, -0.12, 0.05)), Vector((0.5, -0.4, -0.6)), Vector((0, 1, 0.3)))
        place(tA, (x + 1.8, ROW_Y - 0.8, 0), math.pi + 0.3)
        if shot == "covers":
            place(tE, (x - 1.4, ROW_Y - 0.85, 0), math.pi - 0.2)
    elif shot == "lone":
        twp.seat(ar, (-4.6, ROW_Y - 0.62, 0), math.pi, lean=24)
        for sd, dx in (("L", 0.12), ("R", -0.12)):
            reach(ar, sd, Vector((-4.6 + dx + 0.02 * math.sin(sec), ROW_Y - 0.1, 0.98)), Vector((dx * 5, -0.3, -0.8)), Vector((0, 1, -0.5)))
        ar.rot("head", (1, 0, 0), 22)
    elif shot in ("cabinet", "inspect78"):
        h = ar if shot == "cabinet" else tC
        place(h, (XC.x - 0.3, XC.y - 1.45, 0), math.pi)
        reach(h, "R", tray.location + Vector((0.2, -0.45, 0.2)), Vector((-0.5, -0.4, -0.6)), Vector((0, 1, 0)))
        reach(h, "L", tray.location + Vector((-0.2, -0.45, 0.2)), Vector((0.5, -0.4, -0.6)), Vector((0, 1, 0)))
    elif shot == "film":
        place(ar, (LB.x - 0.85, LB.y - 0.1, 0), math.pi / 2)
        fo = c["film_objs"][1].matrix_world.translation
        reach(ar, "R", fo + Vector((-0.08, -0.15, 0.17)), Vector((0, -0.6, -0.6)), Vector((1, 0, 0.2)))
    elif shot in ("debate", "memory", "motorfilm"):
        fo = c["film_objs"][1 if shot != "motorfilm" else 2].matrix_world.translation
        group = (tA, tC, tD) if shot != "motorfilm" else (tC,)
        for k, h in enumerate(group):
            pos = Vector((LB.x - 1.0 - 0.15 * (k == 1), fo.y - 0.6 + k * 0.6, 0)); d = fo - pos
            place(h, (pos.x, pos.y, 0), math.atan2(d.x, -d.y))
        tap = max(0.0, math.sin(sec * 3.0)) if shot == "debate" else 0.0
        reach(group[0], "R", fo + Vector((-0.1 - 0.03 * tap, -0.05, 0.0)), Vector((-0.2, -0.6, -0.6)), Vector((1, 0, 0)))
    elif shot == "pair":
        place(tE, (PAIR.x, PAIR.y - 0.85, 0), math.pi)
        for sd, dx in (("L", 0.45), ("R", -0.45)):
            reach(tE, sd, Vector((PAIR.x + dx, PAIR.y - 0.3, 0.98)), Vector((dx * 2, -0.4, -0.7)), Vector((0, 1, -0.4)))
    # the pair: both bars lifted out and laid in front; the altered bar's lid slides off in "barlid"
    for k, tw in enumerate(c["pair"]):
        bar, lid = tw["bar"], tw["bar_lid"]
        out_ = shot in ("pair", "barlid", "bars")
        base = Vector((0, T.BAR_Y - 0.13, 0.009)) if out_ else Vector((0, T.BAR_Y, T.BAR_Z))
        bar.location = base
        for o in tw["bug_parts"]:
            if not hasattr(o, "_rest"):
                pass
        dz = base - Vector((0, T.BAR_Y, T.BAR_Z))
        for o in tw["bug_parts"]:
            key = o.name
            c.setdefault("_rest", {}).setdefault(key, Vector(o.location))
            o.location = c["_rest"][key] + dz
        slide_ = ease(min(1.0, max(0.0, (sec - 1.0) / 2.2))) if (shot == "barlid" and k == 1) else 0.0
        lid.location = base + Vector((0.0, -0.035 * slide_, 0.0085 + 0.01 * slide_)) + Vector((0.2 * slide_, 0, 0))
    bpy.context.view_layer.update()


def anim(shot):
    def f(c, t):
        animate(c, t * DUR[shot], shot)
        bpy.context.scene.frame_set(int(t * DUR[shot] * 24) + 1)
    return f


def V3(*a):
    return Vector(a)


CAMS = {
    "team": lambda c, t: (V3(5.6, -3.4, 2.3).lerp(V3(5.0, -3.0, 2.2), ease(t)), V3(-1.0, 0.6, 0.9), 24),
    "calendar": lambda c, t: (V3(-0.2, 2.2, 1.65).lerp(V3(-0.5, 2.5, 1.65), ease(t)), V3(-1.2, 3.95, 1.7), 32),
    "clear": lambda c, t: (V3(3.9, 0.3, 1.6).lerp(V3(3.6, 0.5, 1.58), ease(t)), V3(2.2, 2.2, 1.05), 32),
    "stack": lambda c, t: (V3(1.6, -0.6, 1.7).lerp(V3(1.3, -0.8, 1.65), ease(t)), V3(-1.5, -3.5, 0.75), 28),
    "row": lambda c, t: (V3(-5.6, ROW_Y - 1.6, 1.45).lerp(V3(-5.3, ROW_Y - 1.4, 1.42), ease(t)), V3(-3.6, ROW_Y + 0.05, 1.0), 32),
    "covers": lambda c, t: (V3(-4.8 + 4.0 * ease(t), ROW_Y + 1.5, 1.55), V3(-3.6 + 4.0 * ease(t), ROW_Y, 1.0), 30),
    "lone": lambda c, t: (V3(-2.6, ROW_Y - 2.0, 1.55).lerp(V3(-2.9, ROW_Y - 1.8, 1.52), ease(t)), V3(-4.5, ROW_Y - 0.2, 1.0), 32),
    "coil": lambda c, t: (T.world(c["row"][0], (0.34, -0.3, 0.22)).lerp(T.world(c["row"][0], (0.28, -0.22, 0.16)), ease(t)), T.world(c["row"][0], (0.162, -0.067, 0.04)), 55),
    "cabinet": lambda c, t: (XC + V3(-2.0, -1.3, 1.45).lerp(V3(-1.8, -1.2, 1.4), ease(t)), XC + V3(0, -0.7, 0.75), 32),
    "film": lambda c, t: (V3(LB.x - 1.6, LB.y - 0.9, 1.6).lerp(V3(LB.x - 1.3, LB.y - 0.7, 1.58), ease(t)), V3(LB.x, LB.y, 1.55), 35),
    "debate": lambda c, t: (V3(LB.x - 2.9, LB.y + 0.6, 1.7).lerp(V3(LB.x - 2.6, LB.y + 0.45, 1.65), ease(t)), V3(LB.x - 0.4, LB.y, 1.4), 30),
    "memory": lambda c, t: (V3(LB.x - 1.6, 2.2, 1.35).lerp(V3(LB.x - 1.3, 2.35, 1.3), ease(t)), V3(6.75, 2.75, 1.1), 40),
    "pair": lambda c, t: (PAIR + V3(0.4, 1.3, 0.7).lerp(V3(0.3, 1.1, 0.6), ease(t)), PAIR + V3(0, -0.1, 0.03), 34),
    "barlid": lambda c, t: (PAIR + V3(0.95, -0.65, 0.32).lerp(V3(0.85, -0.55, 0.27), ease(t)), PAIR + V3(0.55, -0.16, 0.01), 45),
    "bars": lambda c, t: (PAIR + V3(1.25, -0.6, 0.3).lerp(V3(1.25, -0.5, 0.25), ease(t)), PAIR + V3(1.3, -0.2, 0.0), 45),
    "inspect78": lambda c, t: (XC + V3(1.6, -2.3, 1.5).lerp(V3(1.35, -2.0, 1.45), ease(t)), XC + V3(0, -0.5, 0.8), 32),
    "motorfilm": lambda c, t: (V3(LB.x - 1.2, LB.y - 0.2, 1.55).lerp(V3(LB.x - 1.0, LB.y - 0.3, 1.55), ease(t)), V3(LB.x, LB.y - 0.62, 1.55), 40),
}

MOVES = {k: dict(kind="anim", dof=3.0, cam=fn, anim=anim(k)) for k, fn in CAMS.items()}
MOVES["team"]["title"] = ("CHAPTER 2", "THE X-RAY", 10, 130)
MOVES["team"]["dof"] = None
for k, foc in (("coil", lambda c, t: T.world(c["row"][0], (0.162, -0.07, 0.04))), ("barlid", lambda c, t: PAIR + V3(0.55, -0.12, 0.0)),
               ("bars", lambda c, t: PAIR + V3(1.3, -0.2, 0.0)), ("film", lambda c, t: V3(LB.x, LB.y, 1.55)), ("memory", lambda c, t: V3(6.75, 2.75, 1.1))):
    MOVES[k]["focus"] = foc
    MOVES[k]["dof"] = 4.0
for k in MOVES:
    if "focus" not in MOVES[k]:
        MOVES[k]["dof"] = None
