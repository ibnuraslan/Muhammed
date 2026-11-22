"""Film 1 - LAMP ROOM (12 s). A storm night; the keeper climbs to the lamp room, kneels at the lens pedestal
and wipes the salt crust off an old enamel maker's plate. The lens turns; its beam sweeps over him. HOLD on the plate.

    blender -b -P films/run.py -- f1 <shot A|B|C|D|LOGO> [t] [out.png]
"""
import math, random
import bpy
from mathutils import Vector, Matrix
import si, p4, ship, skfab, poses as P, human as H, deveau as D

LENS_UID = "a5678ee7b33c4966ae289f06f6180565"       # "Lighthouse 1st Order Fresnel Lens" (CC BY)
LANTERN_UID = "46528337bec34fa49f2c71577efc7bc0"    # "Vintage Brass Hurricane Lantern - Unlit" (CC BY)
K = 1.28                                            # lens scale (model at 2.5 m -> 3.2 m: a 1st-order lens)
LENS_H = 2.5 * K
BASE_X = 0.207 * K                                  # pedestal (base unit) half-width; the plate is on its +X face
PLATE_Z = 0.25 * K
PLATE_W = 0.34
R_ROOM = 2.15
SHOTS = dict(A=(0.0, 3.0), B=(3.0, 6.0), C=(6.0, 9.0), D=(9.0, 12.0))
FLOOR = 0.0


def mats():
    g = {}
    g["iron"] = ship.paint("lr_iron", (0.035, 0.04, 0.038), rough=0.5, grime=0.5, scale=10, chips=0.3, under=(0.25, 0.1, 0.05))
    g["iron"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.6
    g["cream"] = p4.mat("lr_cream", (0.12, 0.1, 0.075), rough=0.55)
    g["green"] = ship.paint("lr_green", (0.02, 0.07, 0.04), rough=0.35, grime=0.2, scale=3, chips=0.02, under=(0.5, 0.36, 0.14))
    g["brass"] = D.brass_material("lr_brass")
    g["floor"] = ship.paint("lr_floor", (0.05, 0.045, 0.04), rough=0.55, grime=0.4, scale=2, chips=0.05, under=(0.3, 0.12, 0.05))
    g["floor"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.4
    gl = bpy.data.materials.new("lr_storm_glass"); gl.use_nodes = True; nt = gl.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.5
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (40, 40, 3)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.25
    nt.links.new(nz.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    g["glass"] = gl
    lg = bpy.data.materials.new("lr_lens_glass"); lg.use_nodes = True; b = lg.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1.0, 0.97, 0.9, 1); b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.04; b.inputs["IOR"].default_value = 1.52
    g["lens_glass"] = lg
    return g


def salt_material(name, wipe_x=-1.0):
    """White salt crust, crystalline, alpha-cut where the rag has passed (object x < wipe value, keyable)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.62, 0.6, 0.55, 1); b.inputs["Roughness"].default_value = 0.75
    b.inputs["Subsurface Weight"].default_value = 0.2
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 160; nz.inputs["Detail"].default_value = 10
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.8; bm.inputs["Distance"].default_value = 0.0015
    nt.links.new(nz.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    # patchy crust density
    pn = nt.nodes.new("ShaderNodeTexNoise"); pn.inputs["Scale"].default_value = 22; pn.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], pn.inputs["Vector"])
    pr = nt.nodes.new("ShaderNodeMapRange"); pr.inputs[1].default_value = 0.38; pr.inputs[2].default_value = 0.52
    nt.links.new(pn.outputs["Fac"], pr.inputs[0])
    # wiped: object-local x (across the plate) less than the wipe value -> gone, with a ragged edge
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    edge = nt.nodes.new("ShaderNodeMath"); edge.operation = 'MULTIPLY_ADD'
    nt.links.new(nz.outputs["Fac"], edge.inputs[0]); edge.inputs[1].default_value = 0.03; nt.links.new(sep.outputs[0], edge.inputs[2])
    wv = nt.nodes.new("ShaderNodeValue"); wv.name = "WIPE"; wv.outputs[0].default_value = wipe_x
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'
    nt.links.new(edge.outputs[0], gt.inputs[0]); nt.links.new(wv.outputs[0], gt.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
    nt.links.new(gt.outputs[0], mul.inputs[0]); nt.links.new(pr.outputs[0], mul.inputs[1])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes["Material Output"]
    nt.links.new(mul.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def lens(g, rot=0.0):
    r, ms = skfab.model(LENS_UID, height=LENS_H, name="lens")
    r.matrix_world = Matrix.Rotation(rot, 4, 'Z')
    for o in ms:
        for i, m in enumerate(o.data.materials):
            if m is None:
                continue
            n = m.name
            if "base_unit" in n or "stem" in n or "beam" in n:
                o.data.materials[i] = g["green"]
            elif "strut" in n or "drum" in n or "wheel" in n or "cog" in n or "bolt" in n:
                o.data.materials[i] = g["brass"]
            if "prism" in n or "fresnel" in n or "glass" in n or "structure" in n:
                o.data.materials[i] = g["lens_glass"]
                o.visible_shadow = False                 # the lamp's light gets out through the optic
    return r, ms


def lamp_flame():
    """The paraffin burner inside the optic: a small hot emitter + a point light."""
    z = 1.75 * K
    fm = p4.mat("lr_flame", (1, 0.6, 0.2), emit=(1.0, 0.55, 0.18), strength=60)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(0, 0, z)); f = bpy.context.active_object; f.name = "burner_flame"
    f.scale = (1, 1, 1.8); f.data.materials.append(fm); f.visible_shadow = False
    return p4.light('POINT', "burner", 900, (1.0, 0.62, 0.3), loc=(0, 0, z), size=0.08)


def beams(rot):
    """Two opposed beams from the turning optic (spot lights fixed to its rotation), through a faint haze."""
    out = []
    z = 1.75 * K
    for k in (0, math.pi):
        a = rot + k
        d = Vector((math.cos(a), math.sin(a), -0.02))
        out.append(p4.light('SPOT', "beam", 9000, (1.0, 0.78, 0.5), loc=(0, 0, z), target=Vector((0, 0, z)) + d, size=0.35, spot=11, blend=0.6))
    return out


def room(g):
    """The lantern room: a ten-sided iron lantern, glazed from 1.0 m to 3.9 m, iron chequer floor, cream parapet."""
    n = 10
    ship.cyl("lr_floor", (0, 0, -0.06), (0, 0, 0.0), R_ROOM + 0.2, mat=g["floor"], verts=n * 4)
    for k in range(n):
        a0 = 2 * math.pi * k / n; a1 = 2 * math.pi * (k + 1) / n; am = (a0 + a1) / 2
        w = 2 * R_ROOM * math.sin(math.pi / n)
        c = Vector((R_ROOM * math.cos(am) * math.cos(math.pi / n), R_ROOM * math.sin(am) * math.cos(math.pi / n), 0))
        ship.box("lr_parapet", c + Vector((0, 0, 0.5)), (w + 0.02, 0.08, 1.0), g["cream"], rot=(0, 0, am + math.pi / 2), bevel=0.01)
        ship.box("lr_sill", c + Vector((0, 0, 1.02)) * 1 - Vector((math.cos(am), math.sin(am), 0)) * 0.05, (w + 0.04, 0.2, 0.05), g["iron"], rot=(0, 0, am + math.pi / 2), bevel=0.006)
        gp = ship.box("lr_pane", c + Vector((0, 0, 2.45)), (w - 0.06, 0.012, 2.85), g["glass"], rot=(0, 0, am + math.pi / 2))
        # mullion at the corner a1 and a diagonal astragal (lighthouse helical bar) across the pane
        q = Vector((R_ROOM * math.cos(a1), R_ROOM * math.sin(a1), 0))
        ship.cyl("lr_mullion", q + Vector((0, 0, 1.0)), q + Vector((0, 0, 3.92)), 0.035, mat=g["iron"], verts=8)
        p0 = Vector((R_ROOM * math.cos(a0), R_ROOM * math.sin(a0), 0)) * math.cos(math.pi / n) / math.cos(math.pi / n)
        for zz in (1.95, 2.95):
            ship.cyl("lr_astragal", p0 * 0.985 + Vector((0, 0, zz - 0.45)), q * 0.985 + Vector((0, 0, zz + 0.45)), 0.018, mat=g["iron"], verts=8)
    ship.cyl("lr_ring", (0, 0, 3.9), (0, 0, 4.05), R_ROOM + 0.08, mat=g["iron"], verts=n * 4)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R_ROOM + 0.05, location=(0, 0, 4.0), segments=40, ring_count=20)
    dome = bpy.context.active_object; dome.name = "lr_dome"; dome.scale = (1, 1, 0.45)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for v in dome.data.vertices:
        v.select = v.co.z < 0
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
    dome.data.materials.append(g["cream"]); dome.modifiers.new("s", "SOLIDIFY").thickness = 0.03


def storm_world():
    """Night storm outside: deep blue-grey sky, a little lighter at the horizon (the sea far below is black)."""
    w = bpy.data.worlds.new("storm"); w.use_nodes = True; bpy.context.scene.world = w; nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    rmp = nt.nodes.new("ShaderNodeValToRGB"); cr = rmp.color_ramp
    cr.elements[0].position = 0.45; cr.elements[0].color = (0.0005, 0.0008, 0.0012, 1)
    cr.elements[1].position = 0.55; cr.elements[1].color = (0.012, 0.018, 0.03, 1)
    e = cr.elements.new(0.8); e.color = (0.004, 0.006, 0.011, 1)
    nt.links.new(sep.outputs[2], rmp.inputs[0]); nt.links.new(rmp.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.0
    # cold moonlight through the cloud from one side
    ml = p4.light('AREA', "moon_fill", 220, (0.55, 0.68, 1.0), loc=(-6, 3, 5), target=(0, 0, 1.4), size=6)
    ml.visible_camera = False; ml.visible_glossy = False; ml.visible_transmission = False


def haze(d=0.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.9)); v = bpy.context.active_object; v.name = "lr_haze"
    v.scale = (2 * R_ROOM - 0.3, 2 * R_ROOM - 0.3, 4.0)                 # from below the floor (no surface near people)
    m = bpy.data.materials.new("lr_haze_m"); m.use_nodes = True; nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Density"].default_value = d; vs.inputs["Anisotropy"].default_value = 0.5
    nt.links.new(vs.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    v.data.materials.append(m)
    bpy.context.scene.cycles.volume_bounces = 0
    return v


def hurricane(loc, rot=0.0, lit=True):
    """The keeper's storm lantern (CC-BY scan), lit: its flame and light are parented to it, so it moves as one."""
    r, ms = skfab.model(LANTERN_UID, height=0.33, name="lantern")
    for o in ms:
        if len(o.data.polygons) > 20000:
            dm = o.modifiers.new("dec", "DECIMATE"); dm.ratio = 0.12
        o.visible_shadow = False                         # its glass chimney must not shadow its own flame
    r.matrix_world = Matrix()
    if lit:
        f = Vector((0, 0, 0.15))
        fm = p4.mat("lantern_flame", (1, 0.6, 0.2), emit=(1.0, 0.5, 0.15), strength=40)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=f); fl = bpy.context.active_object; fl.name = "lantern_flame"
        fl.scale = (1, 1, 2.2); fl.data.materials.append(fm); fl.visible_shadow = False
        lt = p4.light('POINT', "lantern_light", 35, (1.0, 0.6, 0.28), loc=f + Vector((0, 0, 0.02)), size=0.02)
        for o in (fl, lt):
            o.parent = r
    r.matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(rot, 4, 'Z')
    return r, ms


def rag(loc, M_hand=None):
    """A wadded cotton rag (grey with salt), crumpled into a pad."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.045, location=loc); o = bpy.context.active_object; o.name = "rag"
    o.scale = (0.55, 1.0, 1.25)
    tx = bpy.data.textures.new("rag_crumple", 'VORONOI'); tx.noise_scale = 0.02
    dm = o.modifiers.new("crumple", "DISPLACE"); dm.texture = tx; dm.strength = 0.012
    m = bpy.data.materials.new("rag_cloth"); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.42, 0.4, 0.36, 1); b.inputs["Roughness"].default_value = 0.95
    b.inputs["Sheen Weight"].default_value = 0.5
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def plate_on_pedestal(wipe):
    """The maker's plate on the pedestal's +X face, crusted with salt; wipe: local x up to which it's clean."""
    R = Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0)))           # columns: plate x -> +Y, plate y -> +Z, face normal -> +X
    M = Matrix.Translation((BASE_X + 0.001, 0.0, PLATE_Z)) @ R.to_4x4()
    em = si.enamel_material("maker_plate_enamel", ground=(0.01, 0.012, 0.022), chip=0.35, grime=0.25)
    objs = si.plate("maker_plate", M, PLATE_W, thick=0.003, mat=em)
    # salt crust: a thin shell over the plate face, cleared by the rag (local x from -W/2 .. +W/2)
    bpy.ops.mesh.primitive_plane_add(size=1); s = bpy.context.active_object; s.name = "salt_crust"
    s.scale = (PLATE_W + 0.03, PLATE_W / si.LOGO_ASPECT * 1.45, 1)
    bpy.ops.object.transform_apply(scale=True)
    sub = s.modifiers.new("sub", "SUBSURF"); sub.subdivision_type = 'SIMPLE'; sub.levels = sub.render_levels = 5
    tx = bpy.data.textures.new("salt_lumps", 'CLOUDS'); tx.noise_scale = 0.01
    dm = s.modifiers.new("lumps", "DISPLACE"); dm.texture = tx; dm.strength = 0.0012; dm.mid_level = 0.0
    s.matrix_world = M @ Matrix.Translation((0, 0, 0.0034))
    s.data.materials.append(salt_material("salt", wipe_x=wipe))
    # salt also crusts the green pedestal round the plate (cleared with it only on the plate)
    return objs + [s], M


def pose_kneel_wipe(plate_M, u, lantern_at=None):
    """Kneeling on the right knee, facing the plate; right hand pushes the rag across it (u: 0..1 along x)."""
    def f(h, dv, M, Mi):
        si.kneel(h, down="R", lean=18, drop=0.42, fwd=0.40)
        Mi = si.kmi(Mi)                                        # targets below are world points
        P.head(h, pitch=18, yaw=4, tilt=3)
        dv.lids(0.35); dv.brow_knit(0.6)
        x = -PLATE_W / 2 + 0.04 + (PLATE_W - 0.08) * u
        pw = plate_M @ Vector((x, 0.005, 0.03 + 0.045))                    # rag centre in front of the plate
        hand = Mi @ (pw + Vector((0.06, 0, 0.0)))
        P.hand_reach(h, "R", hand, elbow=(-0.8, 0.3, -0.6), hand_dir=Vector((-0.15, -0.9, 0.25)))
        P.rest_hand(h, "R", curl=40)
        # left hand braced on his left knee (forearm across it)
        knee = h.bone_head("lowerleg01.L")
        P.hand_reach(h, "L", knee + Vector((-0.02, -0.04, 0.10)), elbow=(0.7, 0.4, -0.2), hand_dir=Vector((-0.2, -0.6, -0.8)))
        P.rest_hand(h, "L", curl=35)
    return f


OPTIC = ("Object_10", "Object_2", "Object_9")          # the turning optic (prisms, frame, bull's-eye panels)
TURN = math.radians(9)                                   # optic turns 9 deg/s (clockwork), in every shot of the room
SHOT_T0 = dict(A=0.0, B=3.0, C=6.0, D=9.0, LOGO=12.0)


def turning(lms, beam_lights, t0, dur):
    """The clockwork turns the optic; the two beams turn with it (keyed per frame)."""
    base = {o.name: o.matrix_world.copy() for o in lms if any(o.name.startswith(n) for n in OPTIC)}
    objs = [o for o in lms if o.name in base]
    z = 1.75 * K

    @si.dyn
    def _(t, frame):
        a = TURN * (t0 + t * dur) + math.radians(-35)
        R = Matrix.Rotation(a, 4, 'Z')
        for o in objs:
            si.place(o, R @ base[o.name], frame)
        for k, L in enumerate(beam_lights):
            d = Vector((math.cos(a + k * math.pi), math.sin(a + k * math.pi), -0.02))
            q = d.to_track_quat('-Z', 'Y')
            L.matrix_world = Matrix.Translation((0, 0, z)) @ q.to_matrix().to_4x4()
            if frame is not None:
                L.rotation_mode = 'XYZ'; L.keyframe_insert("location", frame=frame); L.keyframe_insert("rotation_euler", frame=frame)


def build(shot, t, out):
    sc = si.C.render_setup(samples=64, noise=0.03, bounces=8)
    E = si.ease
    g = mats()
    if shot == "A":
        return stair(g, t, out)
    room(g); storm_world()
    lr, lms = lens(g, rot=0.0)
    lamp_flame()
    bl = beams(0.0)
    t0 = SHOT_T0[shot]; dur = 3.0
    turning(lms, bl, t0, dur)
    haze(0.004)
    pl, pM = plate_on_pedestal(-1.0 if shot == "B" else 1.0)
    salt_wipe = bpy.data.materials["salt"].node_tree.nodes["WIPE"].outputs[0]
    hurricane(Vector((0.62, -0.62, 0.0)), rot=0.4)
    look = pM @ Vector((0, 0, 0))
    if shot in ("B", "C"):
        def rag_at(u):
            """B: small circles on the housing above the plate; C: one stroke across the plate (u = E(T))."""
            if shot == "B":
                a = 2 * math.pi * 1.3 * u
                return pM @ Vector((0.03 * math.cos(a), 0.085 + 0.025 * math.sin(a), 0.028))
            x = -PLATE_W / 2 + 0.04 + (PLATE_W - 0.08) * u
            return pM @ Vector((x, 0.005, 0.028))

        def wiping(h, dv, M, Mi):
            u = si.ease(si.T) if shot == "C" else si.T
            si.kneel(h, down="R", lean=18, drop=0.42, fwd=0.40)
            Mi = si.kmi(Mi)                                        # targets below are world points
            P.head(h, pitch=18, yaw=4, tilt=3)
            dv.lids(0.35); dv.brow_knit(0.6)
            rw = rag_at(u)
            P.hand_reach(h, "R", Mi @ (rw + Vector((0.06, 0, 0.0))), elbow=(-0.8, 0.3, -0.6), hand_dir=Vector((-0.15, -0.9, 0.25)))
            P.rest_hand(h, "R", curl=40)
            knee = h.bone_head("lowerleg01.L")
            P.hand_reach(h, "L", knee + Vector((-0.02, -0.04, 0.10)), elbow=(0.7, 0.4, -0.2), hand_dir=Vector((-0.2, -0.6, -0.8)))
            P.rest_hand(h, "L", curl=35)
        dv, M = si.person("briggs", (BASE_X + 0.62, -0.05), 180, wiping, look, wet=0.45)
        rg = rag(Vector((0, 0, 0)))

        @si.dyn
        def _(t, frame):
            u = si.ease(t) if shot == "C" else t
            si.place(rg, Matrix.Translation(rag_at(u)), frame)
            if shot == "C":
                si.set_value(salt_wipe, -PLATE_W / 2 + (PLATE_W + 0.02) * u, frame)
    elif shot == "D":
        def leanback(h, dv, M, Mi):
            u = si.ease(min(1.0, si.T * 1.6))                     # he sits back on his heel, then holds
            si.kneel(h, down="R", lean=18 - 16 * u, drop=0.42, fwd=0.40)
            Mi = si.kmi(Mi)                                        # targets below are world points
            P.head(h, pitch=18 - 4 * u, yaw=2, tilt=1); dv.lids(0.3 - 0.2 * u); dv.brow_knit(0.6 + 0.3 * u)
            knee = h.bone_head("lowerleg01.L")
            P.hand_reach(h, "L", knee + Vector((-0.02, -0.03, 0.10)), elbow=(0.7, 0.4, -0.2), hand_dir=Vector((-0.2, -0.6, -0.8)))
            P.rest_hand(h, "L", curl=35)
            P.hand_reach(h, "R", knee + Vector((-0.2, 0.06, 0.1)), elbow=(-0.6, 0.4, -0.5), hand_dir=Vector((0.1, -0.5, -0.8)))
            P.grip(h, "R", 0.6)
        dv, M = si.person("briggs", (BASE_X + 0.72, -0.05), 180, leanback, look, wet=0.45)
    if shot == "B":       # medium over his shoulder: lens fills the frame, prisms throw light
        c = Vector((1.55, 0.9, 0.95)) + Vector((-0.08, -0.04, 0.0)) * E(t)
        si.cam(c, (0.0, -0.1, 1.2), lens=20, fstop=4.0, focus=(c - Vector((BASE_X + 0.3, 0, 0.5))).length)
    elif shot == "C":     # close over his right shoulder: the rag drags across the plate
        c = Vector((1.3, 0.38, 1.22)) + Vector((-0.06, -0.03, -0.03)) * E(t)
        tgt = pM @ Vector((0, 0, 0))
        si.cam(c, tgt, lens=60, fstop=2.8, focus=(c - tgt).length)
    elif shot == "D":     # locked off: him and the plate, the beam sweeping over him
        c = Vector((1.42, 1.25, 0.95))
        si.cam(c, (BASE_X + 0.25, -0.1, 0.86), lens=22, fstop=4.0, focus=(c - Vector((BASE_X, 0, PLATE_Z))).length)
    elif shot == "LOGO":  # logo check: straight on, close, plate clean
        tgt = pM @ Vector((0, 0, 0)); c = tgt + Vector((0.62, 0.0, 0.02))
        p4.light('AREA', "check_key", 4, (1.0, 0.97, 0.92), loc=tgt + Vector((0.6, -0.35, 0.4)), target=tgt, size=0.6)
        si.cam(c, tgt, lens=60, fstop=8.0, focus=(c - tgt).length)
    si.finish(out, sat=1.08, exposure=0.0, bloom=0.4, clip_ok=("rag", "lantern", "maker_plate", "salt", "lr_floor"))


# ----------------------------------------------------------------------------- shot A: the spiral stair
R_ST = 1.55; RISE = 0.19; STEP_A = math.radians(22); K0 = 5; STEPS = 2.0
R_WALK = R_ST * 0.62


def stair_root(t):
    """The keeper's root on the spiral after climbing STEPS * t steps from tread K0 (rig frame: faces the way up)."""
    s = K0 + STEPS * t
    a = s * STEP_A
    pos = Vector((math.cos(a) * R_WALK, math.sin(a) * R_WALK, (s + 1) * RISE + 0.0125))
    return Matrix.Translation(pos) @ Matrix.Rotation(a + math.pi, 4, 'Z'), a, pos     # rig -Y along the tangent


def stair(g, t, out):
    """Inside the tower: a cast-iron spiral stair round a central column, whitewashed walls, rain at a slit window.
    The camera follows low behind; the keeper climbs two steps with the storm lantern, his other hand on the rail."""
    E = si.ease
    R = R_ST; rise = RISE; step_a = STEP_A
    import ph
    wm = ph.texture("painted_plaster_wall") if hasattr(ph, "texture") else p4.mat("tower_wall", (0.5, 0.47, 0.4), 0.9)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=R + 0.35, depth=9, location=(0, 0, 4.0)); tw = bpy.context.active_object
    tw.name = "tower_wall"; tw.data.materials.append(wm)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
    ship.cyl("stair_floor", (0, 0, -0.1), (0, 0, 0.0), R + 0.4, mat=g["floor"], verts=48)
    ship.cyl("stair_column", (0, 0, 0), (0, 0, 8.5), 0.09, mat=g["iron"], verts=16)
    for k in range(40):
        a = k * step_a; z = (k + 1) * rise
        c = Vector((math.cos(a) * (R / 2 + 0.05), math.sin(a) * (R / 2 + 0.05), z))
        ship.box("tread", c, (R - 0.12, 0.30, 0.025), g["iron"], rot=(0, 0, a), bevel=0.005)
        q = Vector((math.cos(a) * (R - 0.04), math.sin(a) * (R - 0.04), z))
        ship.cyl("baluster", q, q + Vector((0, 0, 0.88)), 0.011, mat=g["iron"], verts=8)
    pts = [Vector((math.cos(k * step_a / 4) * (R - 0.04), math.sin(k * step_a / 4) * (R - 0.04), (k / 4 + 1) * rise + 0.9)) for k in range(160)]
    ship.rope("handrail", pts, 0.02, g["brass"])
    wa = math.radians(150); wc = Vector((math.cos(wa) * (R + 0.34), math.sin(wa) * (R + 0.34), 2.6))
    ship.box("window_glass", wc, (0.02, 0.32, 0.9), g["glass"], rot=(0, 0, wa))
    p4.light('AREA', "window_moon", 160, (0.55, 0.68, 1.0), loc=wc + Vector((math.cos(wa), math.sin(wa), 0)) * 0.3, target=(0, 0, 1.6), size=0.4)
    p4.world_color((0.002, 0.003, 0.005))
    d = R_WALK * step_a                                                    # tread to tread along his path

    def climb(h, dv, M, Mi):
        """Gait on the stair: each step the trailing foot swings up past the planted one onto the next tread."""
        s = STEPS * si.T; k = int(min(s, STEPS - 1e-6)); p = s - k
        lead, trail = ("L", "R") if k % 2 == 0 else ("R", "L")
        q = si.ease(p)
        P.stand(h, lean=10, weight=lead, twist=-4)
        for side, rel in ((trail, Vector((0.0, d * p, -rise * p))),
                          (lead, Vector((0.0, d - 2 * d * q + d * p, -rise + 2 * rise * q - rise * p)) + Vector((0, 0, 0.09 * math.sin(math.pi * q))))):
            hp = h.bone_head(f"upperleg01.{side}")
            si.leg_ik(h, side, Vector((hp.x * 0.85, rel.y - 0.05, rel.z + 0.09)), (0, -1, 0.3))
            h.aim(f"foot.{side}", Vector((0, -1, -0.15)))
        P.head(h, pitch=-12, yaw=-8, tilt=0)
        dv.lids(0.0); dv.brow_knit(0.5)
        Mt, a, pos = stair_root(si.T)
        Mti = Mt.inverted()
        rail_pt = Vector((math.cos(a + 0.22) * (R - 0.04), math.sin(a + 0.22) * (R - 0.04), (K0 + STEPS * si.T + 1 + 1.0) * rise + 0.9))
        P.hand_reach(h, "R", Mti @ rail_pt + Vector((0, 0, 0.035)), elbow=(-0.8, 0.4, -0.4), hand_dir=Vector((0.2, -0.8, -0.3)))
        P.grip(h, "R", 0.9)
        P.hand_reach(h, "L", Vector((0.32, -0.12, 0.85)), elbow=(0.6, 0.2, -1), hand_dir=Vector((0.1, -0.1, -1)))
        P.grip(h, "L", 1.0)
    M0, a0, pos0 = stair_root(si.T)
    facing = math.degrees(a0 + math.pi) - 90
    dv, M = si.person("briggs", (pos0.x, pos0.y), facing, climb, pos0 + Vector((0, 0, 4)), floor_z=pos0.z, wet=0.6, settle=False)
    lant, _ = hurricane(Vector((0, 0, 0)), rot=0.0)

    @si.dyn
    def _(tt, frame):
        Mt, a, pos = stair_root(tt)
        if si.ANIM and dv is not None:                     # the whole rig climbs (meshes ride its armature)
            si.place(dv.h.arm, Mt, frame)
        if dv is not None:
            si.place(lant, Matrix.Translation(si.hand(dv, M, "L") - Vector((0, 0, 0.36))) @ Matrix.Rotation(a, 4, 'Z'), frame)
    M_c, ac_, pc = stair_root(0.0)
    ac = ac_ - 4.3 * step_a
    c = Vector((math.cos(ac) * 1.05, math.sin(ac) * 1.05, pc.z - 2 * rise + 0.75)) + Vector((0, 0, STEPS * rise * 0.8)) * E(t)
    Mt, a_, pt = stair_root(t)
    si.cam(c, pt + Vector((0, 0, 1.5)), lens=18, fstop=5.6, focus=(c - pt).length)
    si.finish(out, sat=1.05, exposure=0.0, bloom=0.4, clip_ok=("lantern", "handrail", "tread", "baluster"))
