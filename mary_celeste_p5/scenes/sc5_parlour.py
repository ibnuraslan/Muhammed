"""Part 5: home. The Briggs house at Marion, Massachusetts, 1873: a front parlour, late winter afternoon sun low
through the window, warm wallpaper and wood. SHOT = S15..S23, S26.

S15 wide: three parcels on the table by the window          S16 closer: parcels, twine, address label
S17 ECU: the consul's red wax seal                           S18 Sarah's reed organ in its opened crate
S19 Benjamin's sword on its paper                            S20 two of Sophia's dolls in tissue
S21 ECU: the doll with the broken arm                        S22 Arthur, 7, at the window, looking out
S23 the letter on the sill beside him (his father's words)   S26 Arthur holding the doll with the broken arm
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p5; C = p5.C
C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, props5 as PR

SHOT = os.environ.get("SHOT", "S15")
OUT = os.environ.get("OUT", os.path.join(p5.OUTDIR, f"{SHOT}.png"))
sc = C.render_setup(samples=int(os.environ.get("SPP", "200")), noise=0.025, bounces=8)
DENS = float(os.environ.get("HAIR", "1.0"))

RX, RY, RZ = 2.6, 2.2, 2.6
WIN = (-RX, 0.0, 1.45, 1.0, 1.35)            # window in the -X wall: x, centre y, centre z, width, height
TABLE = Vector((-1.55, 0.1, 0.74))


def mat(name, col, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    return m


def wallpaper(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 9
    wv.inputs['Distortion'].default_value = 0.0; L.new(tc.outputs['Object'], wv.inputs['Vector'])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs['Scale'].default_value = 22; L.new(tc.outputs['Object'], vo.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (0.20, 0.07, 0.045, 1)
    mx.inputs[7].default_value = (0.32, 0.17, 0.08, 1); L.new(wv.outputs['Fac'], mx.inputs['Factor'])
    m2 = N.new("ShaderNodeMix"); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 0.25
    L.new(mx.outputs[2], m2.inputs[6]); L.new(vo.outputs['Color'], m2.inputs[7]); L.new(m2.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.8
    return m


# ----------------------------------------------------------------------------- the room
paper = wallpaper("wallpaper")
floor = ship.wood("wood_floor_deck", 1.0, wet=0.0, tint=(0.68, 0.55, 0.42), name="floorboards")
trim = mat("trim", (0.16, 0.08, 0.04), 0.45)
ceil = mat("ceiling", (0.55, 0.5, 0.42), 0.9)
ship.box("floor", (0, 0, -0.03), (2 * RX, 2 * RY, 0.06), floor)
ship.box("ceiling", (0, 0, RZ + 0.03), (2 * RX, 2 * RY, 0.06), ceil)
for sg in (1, -1):
    ship.box("wy", (0, sg * (RY + 0.03), RZ / 2), (2 * RX, 0.06, RZ), paper)
ship.box("wx+", (RX + 0.03, 0, RZ / 2), (0.06, 2 * RY, RZ), paper)
wx, wy, wz, ww, wh = WIN
# window wall in pieces round the opening, with a deep sill and sash bars
ship.box("w_l", (wx - 0.03, (wy - ww / 2 - RY) / 2, RZ / 2), (0.12, wy - ww / 2 + RY, RZ), paper)
ship.box("w_r", (wx - 0.03, (wy + ww / 2 + RY) / 2, RZ / 2), (0.12, RY - wy - ww / 2, RZ), paper)
ship.box("w_b", (wx - 0.03, wy, (wz - wh / 2) / 2), (0.12, ww, wz - wh / 2), paper)
ship.box("w_t", (wx - 0.03, wy, (wz + wh / 2 + RZ) / 2), (0.12, ww, RZ - wz - wh / 2), paper)
ship.box("sill", (wx + 0.08, wy, wz - wh / 2 - 0.02), (0.3, ww + 0.16, 0.04), trim, bevel=0.005)
for k in range(1, 3):
    ship.box("sash_v", (wx, wy - ww / 2 + k * ww / 3, wz), (0.04, 0.03, wh), trim)
ship.box("sash_h", (wx, wy, wz), (0.05, ww, 0.04), trim)
for c, s in (((wx, wy, wz - wh / 2), (0.06, ww + 0.1, 0.06)), ((wx, wy, wz + wh / 2), (0.06, ww + 0.1, 0.06)),
             ((wx, wy - ww / 2, wz), (0.06, 0.06, wh)), ((wx, wy + ww / 2, wz), (0.06, 0.06, wh))):
    ship.box("frame", c, s, trim, bevel=0.004)
ship.box("skirting", (0, RY - 0.01, 0.08), (2 * RX, 0.03, 0.16), trim)
ship.box("skirting2", (RX - 0.01, 0, 0.08), (0.03, 2 * RY, 0.16), trim)
# winter outside: snow ground and bare trees beyond the glass (a backdrop plane, lit by the sun)
snow = mat("snow", (0.75, 0.75, 0.78), 0.7)
ship.box("yard", (wx - 25, 0, -0.5), (50, 60, 0.1), snow)
for k, (dx, dy, hh) in enumerate(((-6, -3, 7), (-9, 2.5, 9), (-14, -6, 8))):
    ship.cyl(f"trunk{k}", Vector((wx + dx, dy, -0.5)), Vector((wx + dx, dy, hh)), 0.18, 0.05, mat=mat(f"bark{k}", (0.05, 0.04, 0.035), 0.9), verts=10)
# furniture: a round table by the window, a chair, a mantel clock on a chest
if SHOT not in ("S22", "S23", "S26"):           # Arthur's shots are another day: the parcels and their table are not there
    PR.put("WoodenTable_01", (TABLE.x, TABLE.y, 0), rot_z=math.radians(90), size=TABLE.z, res="1k")
chair, _ = PR.put("WoodenChair_01", (-1.0, -0.75, 0), rot_z=math.radians(-60), size=0.92, res="1k")
PR.put("vintage_wooden_drawer_01", (1.3, RY - 0.35, 0), rot_z=math.pi, size=0.9, res="1k")
PR.put("mantel_clock_01", (1.3, RY - 0.35, 0.9), rot_z=math.pi, size=0.3, res="1k")
PR.put("fancy_picture_frame_01", (0.6, RY - 0.06, 1.55), rot_z=math.pi, size=0.5, res="1k")
T = TABLE + Vector((0, 0, 0.002))

# ----------------------------------------------------------------------------- what came home
label = ["MRS. BRIGGS", "MARION, MASS.", "U.S.A.", "VIA BOSTON"]
if SHOT in ("S15", "S16", "S17"):
    PR.parcel("parcel_a", T + Vector((0.05, -0.12, 0)), (0.5, 0.32, 0.2), rot_z=0.15, label=label)
    PR.parcel("parcel_b", T + Vector((-0.2, 0.28, 0)), (0.26, 0.2, 0.12), rot_z=-0.35)
    PR.parcel("parcel_c", T + Vector((0.28, 0.25, 0)), (0.6, 0.12, 0.1), rot_z=0.55, seal_on=True)
elif SHOT in ("S18", "S19", "S20", "S21"):
    PR.parcel("open_a", T + Vector((0.0, -0.05, 0)), (0.82, 0.46, 0.22), rot_z=0.1, open_top=True)
    R = Matrix.Translation(T + Vector((0.0, -0.05, 0))) @ Matrix.Rotation(0.1, 4, 'Z')
    if SHOT == "S18":
        PR.reed_organ("organ", R @ Vector((0, 0, 0.09)), rot_z=0.1)
    elif SHOT == "S19":
        sw, _ = PR.put("wooden_handle_saber", R @ Vector((0, 0, 0.1)), size=0.75, axis=2, res="1k")
        sw.rotation_euler = (0, math.radians(90), 0.1 + math.radians(4)); bpy.context.view_layer.update()
        import ph
        lo, hi = ph.bounds(_); sw.location.z += (T.z + 0.1) - lo[2]
    else:
        PR.doll("doll_a", R @ Vector((-0.12, 0.0, 0.1)), rot_z=0.1, height=0.34, broken=True, kind="china")
        PR.doll("doll_b", R @ Vector((0.13, 0.0, 0.1)), rot_z=0.1, height=0.3, broken=False, kind="porcelain")
elif SHOT in ("S22", "S23", "S26"):
    import people as PP
    from sitpose import Seat
    import human as H, poses as P
    a = PP.arthur()
    cx, cy = wx + 0.55, wy - 0.05
    chairA, _ = PR.put("WoodenChair_01", (cx + 0.04, cy, 0), rot_z=math.radians(-90), size=0.85, res="1k")
    # the chair's real seat height under its middle (raycast down), so he sits on it, not in it
    bpy.context.view_layer.update()
    import numpy as np
    zs = []
    for o in chairA.children_recursive:
        if o.type == 'MESH':
            for v in o.data.vertices:
                w = o.matrix_world @ v.co
                if abs(w.x - cx) < 0.1 and abs(w.y - cy) < 0.1 and 0.3 < w.z < 0.6:
                    zs.append(w.z)
    seat_pt = Vector((cx, cy, float(np.percentile(zs, 90)) if zs else 0.45))
    print("chair seat", seat_pt)
    st = Seat(a, seat_pt, 180.0 if SHOT != "S26" else 200.0)       # facing the window (-X)
    st.legs({"L": Vector((seat_pt.x - 0.3, seat_pt.y + 0.08, 0.085)), "R": Vector((seat_pt.x - 0.28, seat_pt.y - 0.08, 0.085))}, knees_out=0.06)
    look_out = Vector((wx - 8, wy - 1.5, 1.2))
    if SHOT == "S26":
        # the doll in his hands, on his knees; he looks down at her
        st.lean(fwd=16)
        knees = (st.M @ a.h.bone_tail("upperleg02.L") + st.M @ a.h.bone_tail("upperleg02.R")) / 2
        hipw = (st.M @ a.h.bone_head("upperleg01.L") + st.M @ a.h.bone_head("upperleg01.R")) / 2
        dpos = hipw.lerp(knees, 0.62) + Vector((0, 0, 0.085))       # across his thighs, clear of his body
        d, piece = PR.doll("doll_held", dpos, rot_z=math.radians(0), height=0.26, broken=True, kind="china")
        import sketchfab as SF
        lo, hi = SF.bounds([o for o in d.children_recursive if o.type == 'MESH'])
        mid = (lo + hi) / 2
        st.hand("L", mid + Vector((0.0, 0.1, 0.0)), elbow=(0.6, 0.3, -0.8), grip=0.4)
        st.hand("R", mid + Vector((0.0, -0.1, 0.0)), elbow=(0.6, 0.3, -0.8), grip=0.4)
        st.head(mid, share=0.85)
        a.lids(0.8); a.brow_knit(0.4)
        look = mid
    else:
        st.lean(fwd=6)
        st.hand_on_thigh("L"); st.hand_on_thigh("R")
        st.head(look_out, share=0.7)
        a.brow_knit(0.3)
        look = look_out
    st.place_finish(look, density=DENS)
    import boatcrew
    boatcrew.trim_under_seat(a, seat_pt, r=0.3, boxes=[(seat_pt - Vector((0.2, 0.2, 0.03)), seat_pt + Vector((0.2, 0.2, 0.0)))])
    # his father's letter on the sill (folded open, ink lines)
    lp = PR.text_texture("letter", ["My dear Arthur,", "", "I wish I could find", "room for you", "aboard . . .", "", "  your loving Father"],
                         size=(1024, 1400), font="InstrumentSerifItalic.ttf", bg=(205, 190, 160, 255), ink=(40, 30, 40, 255), px=78,
                         margin=(80, 120), lead=1.45, chalk=False)
    lm = bpy.data.materials.new("letter"); lm.use_nodes = True; N = lm.node_tree.nodes; L_ = lm.node_tree.links
    ti = N.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(lp); L_.new(ti.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    N["Principled BSDF"].inputs['Roughness'].default_value = 0.85
    bpy.ops.mesh.primitive_plane_add(size=1); lt = bpy.context.active_object; lt.name = "letter"
    lt.scale = (0.15, 0.2, 1); lt.location = (wx + 0.1, wy + 0.32, wz - wh / 2 + 0.002); lt.rotation_euler = (0, 0, math.radians(100))
    lt.data.materials.append(lm)

# ----------------------------------------------------------------------------- light: low winter sun through the window
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.22, 0.3, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.6
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 5.5; sun.data.angle = math.radians(1.0); sun.data.color = (1.0, 0.72, 0.48)
d = Vector((-1.0, -0.3, 0.6)).normalized()            # toward the sun: outside, low, a little to the side
sun.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
bounce = bpy.data.objects.new("bounce", bpy.data.lights.new("bounce", 'AREA')); sc.collection.objects.link(bounce)
bounce.location = (0.2, -0.6, 1.5); bounce.data.energy = 160; bounce.data.size = 2.0; bounce.data.color = (1.0, 0.75, 0.55)
bounce.rotation_euler = (0, math.radians(-80), 0)

# ----------------------------------------------------------------------------- cameras
cams = {
    "S15": ((1.4, -1.6, 1.55), (-1.2, 0.2, 0.85), 26, None),
    "S16": ((-0.3, -0.9, 1.25), T + Vector((0.0, 0.05, 0.1)), 40, 1.3),
    "S17": (T + Vector((0.3, -0.42, 0.55)), T + Vector((0.05, -0.12, 0.205)), 85, "auto"),
    "S18": ((-0.45, -0.85, 1.3), T + Vector((0, -0.05, 0.18)), 40, 1.1),
    "S19": ((-0.7, -0.7, 1.35), T + Vector((0, -0.05, 0.12)), 45, 0.95),
    "S20": ((-0.85, -0.55, 1.32), T + Vector((0.0, -0.05, 0.12)), 45, 0.75),
    "S21": (T + Vector((0.02, -0.4, 0.62)), T + Vector((-0.04, -0.06, 0.13)), 45, "auto"),
    "S22": ((wx + 1.35, wy + 1.15, 1.1), (wx + 0.5, wy - 0.1, 0.98), 40, "auto"),
    "S23": ((wx + 0.75, wy - 0.25, 1.15), (wx + 0.1, wy + 0.3, 0.75), 50, 0.75),
    "S26": ((wx + 1.25, wy - 0.75, 1.35), (wx + 0.3, wy - 0.05, 0.62), 40, "auto"),
}
loc, tgt, lens, foc = cams[SHOT]
fst = 2.8
if foc == "auto":                       # macro: focus on the aim point, a deeper stop so the whole object holds
    foc = (Vector(loc) - Vector(tgt)).length; fst = 6.3
C.camera(Vector(loc), Vector(tgt), lens=lens, fstop=fst if foc else None, focus=foc)
if os.environ.get("DEBUGCAM"):
    for o in bpy.data.objects:
        if o.name.startswith("ceiling"):
            o.hide_render = True
    C.camera(Vector((0.5, -1.5, 5.5)), Vector((-1.0, 0.1, 0.5)), lens=24)
C.finish(OUT, cine={"sat": 1.15, "exposure": 0.55 if SHOT == "S15" else 0.05}, bloom=0.4)
print("RENDERED", OUT)
