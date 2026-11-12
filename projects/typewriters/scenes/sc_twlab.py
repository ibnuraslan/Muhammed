"""THE LAB (dramatization). One electronics lab used twice:
  variant "french"  a French security service workshop, Paris 1983: warmer light, a teleprinter on the bench, an oscilloscope
  variant "meade"   the NSA lab at Fort Meade, 1984 (Chapter Two): long benches, lightboxes, an X-ray cabinet (built later)
Steel benches, pegboard of tools, scanned microscopes, multimeters, desk lamps, shelving of parts, fluorescent panels.

Ch1 1A  cover   a technician lifts a teleprinter's cover for two visitors (chapter title over this shot)
Ch1 1B  scope   on the bench an oscilloscope shows a short burst, then a flat line
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import machines as MC

EXPOSURE = 0.0
DUR = {"cover": 6.0, "scope": 4.5, "sixteen": 6.0, "tags": 4.5}
VARIANT_FOR = {"cover": "french", "scope": "french", "sixteen": "evidence", "tags": "evidence"}
BENCH_Y = 1.8                 # the main bench along the back wall (front edge faces -Y)


def scope_material(name="ScopeTrace"):
    """Oscilloscope tube: dark green screen, graticule, a bright trace. A burst of high-frequency wiggle travels across
    the screen once per 48 frames, otherwise a flat line (frame-driven: plays in any render)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); uv = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs['UV'], sp.inputs[0])
    tv = N.new("ShaderNodeValue"); d = tv.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = "(frame % 48) / 48"
    # burst envelope centred at x = t*1.6 - 0.3, width 0.12
    c0 = N.new("ShaderNodeMath"); c0.operation = 'MULTIPLY_ADD'; c0.inputs[1].default_value = 1.6; c0.inputs[2].default_value = -0.3; L.new(tv.outputs[0], c0.inputs[0])
    dx = N.new("ShaderNodeMath"); dx.operation = 'SUBTRACT'; L.new(sp.outputs[0], dx.inputs[0]); L.new(c0.outputs[0], dx.inputs[1])
    sq = N.new("ShaderNodeMath"); sq.operation = 'MULTIPLY'; L.new(dx.outputs[0], sq.inputs[0]); L.new(dx.outputs[0], sq.inputs[1])
    ex = N.new("ShaderNodeMath"); ex.operation = 'MULTIPLY'; ex.inputs[1].default_value = -180.0; L.new(sq.outputs[0], ex.inputs[0])
    env = N.new("ShaderNodeMath"); env.operation = 'EXPONENT'; L.new(ex.outputs[0], env.inputs[0])
    sx = N.new("ShaderNodeMath"); sx.operation = 'MULTIPLY'; sx.inputs[1].default_value = 260.0; L.new(sp.outputs[0], sx.inputs[0])
    sn = N.new("ShaderNodeMath"); sn.operation = 'SINE'; L.new(sx.outputs[0], sn.inputs[0])
    amp = N.new("ShaderNodeMath"); amp.operation = 'MULTIPLY'; L.new(sn.outputs[0], amp.inputs[0]); L.new(env.outputs[0], amp.inputs[1])
    yv = N.new("ShaderNodeMath"); yv.operation = 'MULTIPLY_ADD'; yv.inputs[1].default_value = 0.32; yv.inputs[2].default_value = 0.5; L.new(amp.outputs[0], yv.inputs[0])
    dy = N.new("ShaderNodeMath"); dy.operation = 'SUBTRACT'; L.new(sp.outputs[1], dy.inputs[0]); L.new(yv.outputs[0], dy.inputs[1])
    ady = N.new("ShaderNodeMath"); ady.operation = 'ABSOLUTE'; L.new(dy.outputs[0], ady.inputs[0])
    tr = N.new("ShaderNodeMapRange"); tr.inputs['From Min'].default_value = 0.004; tr.inputs['From Max'].default_value = 0.03
    tr.inputs['To Min'].default_value = 1.0; tr.inputs['To Max'].default_value = 0.0; L.new(ady.outputs[0], tr.inputs['Value'])
    # graticule
    gx = N.new("ShaderNodeMath"); gx.operation = 'MULTIPLY'; gx.inputs[1].default_value = 10; L.new(sp.outputs[0], gx.inputs[0])
    gy = N.new("ShaderNodeMath"); gy.operation = 'MULTIPLY'; gy.inputs[1].default_value = 8; L.new(sp.outputs[1], gy.inputs[0])
    fx = N.new("ShaderNodeMath"); fx.operation = 'PINGPONG'; fx.inputs[1].default_value = 0.5; L.new(gx.outputs[0], fx.inputs[0])
    fy = N.new("ShaderNodeMath"); fy.operation = 'PINGPONG'; fy.inputs[1].default_value = 0.5; L.new(gy.outputs[0], fy.inputs[0])
    mn = N.new("ShaderNodeMath"); mn.operation = 'MINIMUM'; L.new(fx.outputs[0], mn.inputs[0]); L.new(fy.outputs[0], mn.inputs[1])
    gl = N.new("ShaderNodeMath"); gl.operation = 'LESS_THAN'; gl.inputs[1].default_value = 0.03; L.new(mn.outputs[0], gl.inputs[0])
    gm = N.new("ShaderNodeMath"); gm.operation = 'MULTIPLY'; gm.inputs[1].default_value = 0.12; L.new(gl.outputs[0], gm.inputs[0])
    tot = N.new("ShaderNodeMath"); tot.operation = 'ADD'; L.new(tr.outputs[0], tot.inputs[0]); L.new(gm.outputs[0], tot.inputs[1])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'; L.new(tot.outputs[0], col.inputs['Factor'])
    col.inputs[6].default_value = (0.004, 0.012, 0.008, 1); col.inputs[7].default_value = (0.45, 1.0, 0.6, 1)
    em = N.new("ShaderNodeEmission"); em.inputs['Strength'].default_value = 3.0; L.new(col.outputs[2], em.inputs['Color'])
    gls = N.new("ShaderNodeBsdfGlossy"); gls.inputs['Roughness'].default_value = 0.08
    ad = N.new("ShaderNodeAddShader"); L.new(em.outputs[0], ad.inputs[0]); L.new(gls.outputs[0], ad.inputs[1])
    L.new(ad.outputs[0], out.inputs['Surface'])
    return m


def oscilloscope(name, loc, rot_z=0.0):
    M = MC.mats()
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r); r.location = loc; r.rotation_euler = (0, 0, rot_z)
    def P(o):
        o.parent = r; return o
    P(box("Case", (0, 0.05, 0.16), (0.36, 0.48, 0.3), pbr("ScopeCase", (0.42, 0.44, 0.42), 0.45, 0.2), bevel=0.01))
    P(box("Front", (0, -0.192, 0.16), (0.35, 0.02, 0.29), M["dark"]))
    P(box("Hood", (-0.07, -0.205, 0.19), (0.16, 0.03, 0.14), M["dark"]))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.07, -0.236, 0.19), rotation=(math.radians(90), 0, 0))
    tube = bpy.context.active_object; tube.name = "Tube"; tube.scale = (0.13, 0.105, 1); tube.data.materials.append(scope_material()); P(tube)
    P(box("HoodL", (-0.145, -0.25, 0.19), (0.012, 0.04, 0.13), M["dark"])); P(box("HoodR", (0.005, -0.25, 0.19), (0.012, 0.04, 0.13), M["dark"]))
    for k in range(9):
        P(cyl("Knob", (0.06 + (k % 3) * 0.04, -0.21, 0.08 + (k // 3) * 0.07), 0.011, 0.02, M["metal"] if k % 2 else M["dark"], verts=12, rot=(math.radians(90), 0, 0)))
    for k in range(2):
        P(cyl("Jack", (-0.12 + k * 0.05, -0.205, 0.05), 0.008, 0.015, pbr("JackRed", (0.4, 0.05, 0.03), 0.4), verts=10, rot=(math.radians(90), 0, 0)))
    return r


def build(variant="french"):
    c = {"variant": variant}
    french = variant == "french"
    rng = np.random.default_rng(3)
    w = world_sky(sun_elev_deg=30, sun_rot_deg=100, strength=0.5, tint=(0.95, 0.92, 0.88) if french else (0.86, 0.9, 1.0))
    w.node_tree.nodes["Sky Texture"].sun_disc = False
    # ---------------------------------------------------------------- room x -6..6, y -4..3, h 3.2; windows on -X
    box("Floor", (0, 0, -0.01), (12, 7, 0.02), ph.texture("floor_tiles_06" if french else "old_linoleum_flooring_01", scale=0.5, name="LabFloor",
                                                         tint=(0.75, 0.72, 0.68) if french else (0.55, 0.6, 0.62)))
    wall = ph.texture("painted_plaster_wall", scale=0.5, name="LabWall", tint=(0.86, 0.8, 0.7) if french else (0.76, 0.8, 0.78))
    box("WallBack", (0, 3.05, 1.6), (12, 0.1, 3.2), wall); box("WallFront", (0, -4.05, 1.6), (12, 0.1, 3.2), wall)
    box("WallR", (6.05, -0.5, 1.6), (0.1, 7, 3.2), wall)
    box("Ceiling", (0, -0.5, 3.22), (12, 7, 0.04), ph.texture("ceiling_interior", scale=0.5, name="LabCeil"))
    for z, h in ((0.5, 1.0), (2.95, 0.5)):
        box("WallL", (-6.05, -0.5, z), (0.1, 7, h), wall)
    for y in (-3.6, -1.0, 1.6):
        box("WinPier", (-6.05, y, 1.85), (0.1, 0.8, 1.7), wall)
    for yc in (-2.3, 0.3, 2.4):
        box("LabGlass", (-6.04, yc, 1.85), (0.01, 1.8 if yc < 2 else 0.6, 1.7), glass("LabGlassM", (0.9, 0.93, 0.95)))
        box("LabSashH", (-6.02, yc, 1.85), (0.04, 1.8 if yc < 2 else 0.6, 0.04), pbr("Sash", (0.6, 0.58, 0.54), 0.5))
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 6.0; pt.size_y = 1.7; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (-6.0, -0.5, 1.85); po.rotation_euler = (0, math.radians(90), 0)
    sn = bpy.data.lights.new("Sun", 'SUN'); sn.energy = 2.4; sn.angle = math.radians(2); sn.color = (1.0, 0.9, 0.78) if french else (1.0, 0.95, 0.9)
    so = bpy.data.objects.new("Sun", sn); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(55), math.radians(30), math.radians(90))
    box("Outside", (-30, 0, 8), (1, 60, 20), ph.texture("beige_wall_002", scale=0.2, name="LabOutside"))
    for x in (-3.0, 0.0, 3.0):
        for y in (-2.0, 1.0):
            ph.model("mounted_fluorescent_lights", loc=(x, y, 3.2), rot_z=0)
            l = area_light((x, y, 3.12), (0, 0, 0), 0.9, 35, (1.0, 0.95, 0.85) if french else (0.9, 0.96, 1.0)); l.visible_camera = False
    # ---------------------------------------------------------------- benches, pegboard, shelving, instruments
    bench_top = ph.texture("dark_wood" if french else "oak_veneer_01", scale=1.0, name="BenchTop")
    legm = pbr("BenchLeg", (0.25, 0.27, 0.26), 0.4, 0.7)
    def bench(x, y, L_, rot=0.0):
        box("BenchTop", (x, y, 0.88), (L_, 0.8, 0.05), bench_top, bevel=0.005, rot=(0, 0, rot))
        for dx in (-L_ / 2 + 0.1, L_ / 2 - 0.1):
            for dy in (-0.32, 0.32):
                p = Vector((dx, dy, 0)); p.rotate(__import__('mathutils').Euler((0, 0, rot)))
                box("BenchLeg", (x + p.x, y + p.y, 0.43), (0.05, 0.05, 0.86), legm)
        box("BenchShelf", (x, y, 0.25), (L_ - 0.1, 0.7, 0.02), legm, rot=(0, 0, rot))
    bench(0.0, BENCH_Y + 0.6, 7.0)                        # back wall bench
    if variant == "evidence":
        evidence_row(c, bench)
        c["P"] = {}
        animate(c, 0.0, "sixteen")
        return c
    bench(-1.2, -0.6, 3.4)                                # island bench where the teleprinter sits
    peg = pbr("Pegboard", (0.62, 0.55, 0.42) if french else (0.55, 0.58, 0.56), 0.8)
    box("Pegboard", (0.0, 2.97, 1.65), (5.0, 0.03, 1.0), peg)
    tools = ["screwdriver", "pliers", "combination_wrench", "flathead_screwdriver", "tongue_groove_pliers", "measuring_tape_01"]
    for k in range(14):
        aid = tools[k % len(tools)]
        try:
            r, ms = ph.model(aid, loc=(-2.2 + k * 0.33, 2.94, 1.5 + 0.2 * (k % 2)), rot_z=math.pi)
            r.rotation_euler = (math.radians(90), 0, math.pi)
        except Exception:
            pass
    for k in range(3):
        ph.model("steel_frame_shelves_02", loc=(4.6 + (k % 2) * 0.65, 2.7, 0), rot_z=math.pi)
    for k in range(8):
        ph.model("cardboard_box_01", loc=(4.4 + (k % 2) * 0.65, 2.7, 0.45 + (k // 2) * 0.5), rot_z=rng.uniform(-0.2, 0.2), scale=0.7)
    ph.model("industrial_microscope", loc=(2.4, BENCH_Y + 0.6, 0.905), rot_z=math.pi + 0.3)
    ph.model("retro_multimeter", loc=(1.4, BENCH_Y + 0.5, 0.905), rot_z=math.pi)
    ph.model("vintage_radio_transceiver", loc=(-2.6, BENCH_Y + 0.65, 0.905), rot_z=math.pi)
    ph.model("magnifying_glass_01", loc=(-2.0, -0.35, 0.905), rot_z=0.5)
    ph.model("circuit_board", loc=(-0.3, -0.45, 0.905), rot_z=0.2)
    l_r, l_ms = ph.model("desk_lamp_arm_01", loc=(-2.4, -0.5, 0.905), rot_z=math.radians(-30))
    twp.tint_model(l_ms, (0.2, 0.22, 0.2), keep=0.1)
    ph.model("stationery_supplies", loc=(-0.9, -0.3, 0.905), rot_z=0.3)
    ph.model("SchoolChair_01", loc=(0.8, BENCH_Y - 0.2, 0), rot_z=0.3)
    for k in range(4):
        ph.model("WoodenTable_02", loc=(5.2, -3.2 + k * 0.1, 0), scale=0.0001) if False else None
    ph.model("potted_plant_02", loc=(-5.4, -3.4, 0))
    # ---------------------------------------------------------------- the teleprinter under examination, its cover lifts
    tty, p = MC.teletype("BenchTTY", (-1.4, -0.55, 0.905), 0.0, stand=False)
    c["tty"] = tty
    hood = [o for o in tty.children if o.name.startswith("Hood") or o.name.startswith("Window")]
    piv = bpy.data.objects.new("HoodHinge", None); bpy.context.collection.objects.link(piv); piv.parent = tty; piv.location = (0, 0.3, 0.45)
    for o in hood:
        mw = o.matrix_world.copy(); o.parent = piv; o.matrix_world = mw
    c["hood"] = piv
    bug = box("FoundBoard", (-1.4, -0.5, 1.06), (0.1, 0.06, 0.01), pbr("PCBf", (0.08, 0.16, 0.09), 0.35, 0.0, **{'Coat Weight': 0.8}))
    c["bug"] = bug
    osc = oscilloscope("Scope", (-0.2, -0.45, 0.905), math.radians(-10)); c["scope"] = osc
    cyl("ProbeLead", (-0.6, -0.5, 0.91), 0.004, 0.8, pbr("Lead", (0.02, 0.02, 0.02), 0.5), verts=6, rot=(0, math.radians(90), math.radians(-8)))
    # ---------------------------------------------------------------- people
    P = {}
    P["tech"] = twp.person("FrTech", 1.0, 46, "male_casualsuit05", "short04", hv=0.45, cval=0.6, hue=0.08, sat=0.15)
    P["usA"] = twp.person("Visitor1", 1.0, 50, "male_elegantsuit01", "short02", hv=0.55, cval=0.42, hue=0.6, sat=0.2)
    P["usB"] = twp.person("Visitor2", 1.0, 38, "male_casualsuit02", "short03", hv=0.25, cval=0.5, hue=0.1, sat=0.25)
    c["P"] = P
    animate(c, 0.0, "cover")
    return c


def tag_image(path, word, num):
    import skia
    sf = skia.Surface(400, 260); cv = sf.getCanvas(); cv.clear(skia.Color4f(0.86, 0.82, 0.68, 1))
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(0.1, 0.1, 0.14, 1))
    f = skia.Font(skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"), 44)
    f2 = skia.Font(skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"), 34)
    cv.drawString(word, 200 - f.measureText(word) / 2, 110, f, p)
    cv.drawString(f"No. {num:02d}", 120, 180, f2, p)
    pp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3); pp.setColor4f(skia.Color4f(0.1, 0.1, 0.14, 1))
    cv.drawCircle(40, 130, 14, pp)
    sf.makeImageSnapshot().save(path, skia.kPNG)
    return path


def evidence_row(c, bench):
    """Sixteen altered typewriters in a row on two long benches, each with a paper tag on a string."""
    import os, typewriter as T
    bench(-2.3, -0.6, 4.6); bench(2.4, -0.6, 4.6)
    cols = [(0.11, 0.15, 0.2), (0.32, 0.28, 0.22), (0.2, 0.25, 0.3), (0.42, 0.12, 0.1), (0.22, 0.24, 0.2)]
    c["tws"] = []; c["tags"] = []
    string_m = pbr("TagString", (0.7, 0.68, 0.6), 0.8)
    for k in range(16):
        x = -4.35 + k * 0.58
        tw = T.make(f"EV{k}", loc=(x, -0.55, 0.905), rot_z=0.0, color=cols[k % 5], mechanism=False, glyphs=(k in (3, 4)), legends=False,
                    text=" ", seed=k)
        tw["paper"].hide_render = True
        c["tws"].append(tw)
        word = "LENINGRAD" if k in (2, 9, 14) else "MOSCOW"
        tm = bpy.data.materials.new(f"Tag{k}"); tm.use_nodes = True
        ti = tm.node_tree.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(tag_image(os.path.join(T.GEN, f"tag_{k}.png"), word, k + 1))
        tm.node_tree.links.new(ti.outputs[0], tm.node_tree.nodes["Principled BSDF"].inputs['Base Color'])
        bpy.ops.mesh.primitive_plane_add(size=1); tg = bpy.context.active_object; tg.name = f"TagCard{k}"
        tg.scale = (0.075, 0.048, 1); bpy.ops.object.transform_apply(scale=True); tg.data.materials.append(tm)
        piv = bpy.data.objects.new(f"TagPivot{k}", None); bpy.context.collection.objects.link(piv)
        piv.location = (x + 0.2, -0.75, 0.905 + 0.104)               # tied to the platen knob end
        tg.parent = piv; tg.location = (0, -0.01, -0.06); tg.rotation_euler = (math.radians(80), 0, 0)
        st = cyl("String", (0, 0, -0.02), 0.0012, 0.04, string_m, verts=6); st.parent = piv
        c["tags"].append(piv)
    # evidence clutter: clipboards, a camera on a tripod-less stand, cartons, the X-ray films pinned on a lightbox at the end wall
    ph.model("clipboard", loc=(-4.9, -0.4, 0.905), rot_z=0.4)
    ph.model("Camera_01", loc=(5.0, -0.5, 0.905), rot_z=2.4)
    ph.model("office_notepads", loc=(0.0, -0.8, 0.905), scale=0.4)
    for k in range(6):
        ph.model("cardboard_box_01", loc=(-5.3 + k * 0.5, 2.0 - 3.8, 0), rot_z=0.1 * k, scale=0.8)
    lightbox_wall(c, Vector((5.98, -0.6, 1.6)), -math.pi / 2, 3)


def lightbox_wall(c, at, rot_z, n, film=None):
    """A row of wall X-ray viewers: steel frames, opal glass lit from behind (a real area light inside each), film clips."""
    frame = pbr("LBFrame", (0.6, 0.62, 0.6), 0.35, 0.6)
    opal = pbr("Opal", (0.9, 0.92, 0.95), 0.4, 0.0, **{'Emission Color': (0.85, 0.92, 1.0, 1), 'Emission Strength': 2.2})
    c["lightboxes"] = []
    for k in range(n):
        off = Vector((-(k - (n - 1) / 2) * 0.62, 0, 0)); off.rotate(__import__('mathutils').Euler((0, 0, rot_z)))
        p = at + off
        r = bpy.data.objects.new("Lightbox", None); bpy.context.collection.objects.link(r); r.location = p; r.rotation_euler = (0, 0, rot_z)
        for o in (box("LBCase", (0, 0.06, 0), (0.58, 0.1, 0.46), frame, bevel=0.01), box("LBOpal", (0, 0.0, 0), (0.52, 0.01, 0.4), opal),
                  box("LBClip", (-0.12, -0.012, 0.19), (0.05, 0.01, 0.025), frame), box("LBClip", (0.12, -0.012, 0.19), (0.05, 0.01, 0.025), frame)):
            o.parent = r
        c["lightboxes"].append(r)
    return c["lightboxes"]


def animate(c, sec, shot):
    if c["variant"] == "evidence":
        for k, piv in enumerate(c["tags"]):
            piv.rotation_euler = (0.06 * math.sin(sec * 1.3 + k), 0, 0.15 * math.sin(sec * 0.9 + k * 0.7))      # tags stir in the air from the vents
        bpy.context.view_layer.update()
        return
    from human import reach, fingers_curl
    P = c["P"]
    tty = c["tty"]
    lift = ease(min(1.0, max(0.0, (sec - 1.8) / 1.6))) if shot == "cover" else 1.0
    c["hood"].rotation_euler = (math.radians(-50) * lift, 0, 0)
    t_ = P["tech"]
    twp.stand(t_, (-1.4, -1.35, 0), math.pi)                                # faces +Y, the bench
    hp = c["hood"].matrix_world @ Vector((0, -0.42, -0.05))
    reach(t_, "R", hp + Vector((-0.05, -0.1, -0.03)), Vector((-0.3, -0.6, -0.9)), Vector((0, 1, 0.0)))     # one hand lifts the hood
    reach(t_, "L", Vector((-1.25, -0.75, 0.93)), Vector((0.4, -0.5, -0.8)), Vector((0, 1, -0.6)))          # the other rests on the bench
    fingers_curl(t_, 45, thumb=25)
    t_.rot("head", (1, 0, 0), -12)
    a, b = P["usA"], P["usB"]
    twp.stand(a, (-0.3, -1.3, 0), math.radians(150)); twp.stand(b, (-2.4, -1.2, 0), math.radians(-150))
    a.rot("head", (1, 0, 0), -14); b.rot("head", (1, 0, 0), -10 - 4 * lift)
    for h in (a, b):
        h.rot("head", (0, 0, 1), 3 * math.sin(sec * 0.6))
    bpy.context.view_layer.update()


def anim(shot):
    def f(c, t):
        animate(c, t * DUR[shot], shot)
        bpy.context.scene.frame_set(int(t * DUR[shot] * 24) + 1)          # frame-driven screens follow in stills
    return f


def cam_cover(c, t):
    e = ease(t)
    return (Vector((-3.2, -2.6, 1.7)).lerp(Vector((-2.9, -2.3, 1.62)), e), Vector((-1.2, -0.55, 1.08)), 32)


def cam_scope(c, t):
    e = ease(t); s = c["scope"].matrix_world @ Vector((-0.07, -0.22, 0.19))
    return (s + Vector((0.25, -0.7, 0.18)).lerp(Vector((0.16, -0.5, 0.12)), e), s, 50)


def cam_sixteen(c, t):
    e = ease(t)
    return (Vector((-5.4, -2.6, 1.45)).lerp(Vector((-4.6, -2.3, 1.4)), e), Vector((0.5, -0.5, 1.0)), 28)


def cam_tags(c, t):
    e = ease(t); x = -2.6 + 1.2 * e
    return (Vector((x - 0.3, -1.45, 1.22)), Vector((x + 0.25, -0.75, 0.98)), 45)


MOVES = {
    "sixteen": dict(kind="anim", dof=4.0, cam=cam_sixteen, focus=lambda c, t: Vector((-2.0, -0.6, 1.0)), anim=anim("sixteen"),
                    title=("CHAPTER 4", "WHAT MOSCOW READ", 10, 130)),
    "tags": dict(kind="anim", dof=1.2, cam=cam_tags, focus=lambda c, t: Vector((-2.6 + 1.2 * ease(t) + 0.25, -0.76, 0.96)), anim=anim("tags")),
    "cover": dict(kind="anim", dof=3.0, cam=cam_cover, focus=lambda c, t: Vector((-1.4, -0.5, 1.1)), anim=anim("cover"),
                  title=("CHAPTER 1", "THE SWAP", 10, 130)),
    "scope": dict(kind="anim", dof=1.4, cam=cam_scope, focus=lambda c, t: c["scope"].matrix_world @ Vector((-0.07, -0.22, 0.19)), anim=anim("scope")),
}
