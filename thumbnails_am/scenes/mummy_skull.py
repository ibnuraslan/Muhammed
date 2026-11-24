"""Mummy thumbnail: the composite skull on a table, bright and clean, no text.
VARIANT=b1  the cranium with the mismatched lower jaw set down beside it, turned the wrong way (it is not its jaw)
VARIANT=b2  skull and jaw assembled, but plainly from two people: pale cranium, dark old jaw, a visible misfit
Real cranium + mandible scans (mummy/3d lib/bones.py). Daylight from a window, vivid painted wall behind, shallow focus,
the skull in the right third, the left half kept clean for the title.
    PREVIEW=0.5 SPP=48 VARIANT=b1 blender -b --python mummy_skull.py"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
C = T.use("mummy")
import bpy
from mathutils import Vector
import bones as B, sets as S, ph
E = os.environ.get
V = E("VARIANT", "b1")
sc = T.res_setup(int(E("SPP", "256")), noise=0.01)

# ---------------------------------------------------------------- table and wall
wood = S.tex("wood_table_worn", 1.6, tint=(1.0, 0.78, 0.55), name="table_wood")
BG = E("BG", "endless" if V == "b1" else "wall")
if BG == "endless":
    # no wall: the tabletop runs on out of focus into a soft coloured haze, no edge, no horizon line
    S.box("table", (0, 15.0, -0.025), (40.0, 32.0, 0.05), wood)
else:
    S.box("table", (0, 0.3, -0.025), (4.0, 2.2, 0.05), wood)
    WALL = {"b1": (0.0, 0.33, 0.36), "b2": (0.02, 0.12, 0.5)}[V]
    S.box("wall", (0, 1.25, 1.0), (6.0, 0.05, 3.0), S.flat("wall", WALL, 0.85))

# ---------------------------------------------------------------- skull and jaw
cr_tone = ((0.62, 0.53, 0.40), (0.34, 0.27, 0.18))          # pale, clean cranium
md_tone = {"b1": ((0.50, 0.38, 0.24), (0.24, 0.16, 0.09)),   # the other person's jaw: browner
           "b2": ((0.25, 0.165, 0.095), (0.085, 0.055, 0.03))}[V]   # b2: plainly darker, much older-looking
cr = B.hero_cranium(tone=cr_tone)
md = B.hero_mandible(tone=md_tone)
SX, SY = float(E("SX", "0.2")), float(E("SY", "0.0"))
if V == "b1":
    # cranium resting on its base, face turned toward camera-left; jaw set down in front of it, askew
    cr.rotation_euler = (math.radians(-8), math.radians(4), math.radians(float(E("CRZ", "-28"))))
    cr.location = (SX, SY, 0.0)
    md.rotation_euler = (math.radians(0), 0, math.radians(float(E("MDZ", "205"))))
    md.location = (SX + float(E("MDX", "-0.16")), SY + float(E("MDY", "-0.06")), 0.0)
else:
    # articulated (as found: jaw under the skull) but off-true: the jaw is shifted, twisted and tipped, with a gap
    grp = bpy.data.objects.new("skull_grp", None); sc.collection.objects.link(grp)
    cr.parent = grp; md.parent = grp
    cr.location = (0, 0, 0.07)                       # articulation offset from tests/t_skull.py
    md.location = (float(E("JX", "0.006")), 0.012, -0.004)
    md.rotation_euler = (math.radians(float(E("JTX", "-3"))), math.radians(float(E("JTY", "-6"))), math.radians(float(E("JTZ", "6"))))
    grp.rotation_euler.z = math.radians(float(E("CRZ", "-28")))
    grp.location = (SX, SY, 0.0)

def zmin(o):
    bpy.context.view_layer.update(); mw = o.matrix_world
    return min((mw @ v.co).z for v in o.data.vertices)


def settle(o, z0=0.0):
    """Drop an object so its lowest vertex touches z0."""
    o.location.z += z0 - zmin(o) + 0.0005


if V == "b2":
    # the jaw carries the skull (as a real skull with its jaw rests: on the chin and the jaw's lower border)
    grp.rotation_euler.x = math.radians(float(E("PITCH", "-4")))
    grp.location.z -= min(zmin(cr), zmin(md)) - 0.0005
else:
    settle(md); settle(cr)

# ---------------------------------------------------------------- daylight
sky = E("HDRI", "kloofendal_48d_partly_cloudy_puresky")
try:
    ph.world_hdri(sky, strength=float(E("SKY_K", "0.6")), rot_z=math.radians(40), res="2k")
except Exception as e:
    print("hdri", e); S.world((0.6, 0.7, 0.85), 0.6)
if BG == "endless":
    # what the camera sees beyond the table: a vertical gradient (camera rays only; the HDRI still lights the set)
    wn = sc.world.node_tree; WN = wn.nodes; WL = wn.links
    outw = [n for n in WN if n.type == 'OUTPUT_WORLD'][0]; bg_l = outw.inputs['Surface'].links[0].from_socket
    lp = WN.new("ShaderNodeLightPath"); tc = WN.new("ShaderNodeTexCoord"); sp_ = WN.new("ShaderNodeSeparateXYZ")
    WL.new(tc.outputs['Window'], sp_.inputs[0])
    rmp = WN.new("ShaderNodeValToRGB"); WL.new(sp_.outputs['Y'], rmp.inputs['Fac'])
    cols = [tuple(float(x) for x in E(k, d).split(",")) for k, d in
            (("BG_LO", "1.0,0.62,0.32"), ("BG_MID", "0.35,0.75,0.78"), ("BG_HI", "0.02,0.32,0.45"))]
    el = rmp.color_ramp.elements; el[0].position = 0.25; el[0].color = (*cols[0], 1); el[1].position = 1.0; el[1].color = (*cols[2], 1)
    e3 = el.new(0.55); e3.color = (*cols[1], 1)
    bgc = WN.new("ShaderNodeBackground"); bgc.inputs['Strength'].default_value = float(E("BG_K", "1.0"))
    WL.new(rmp.outputs['Color'], bgc.inputs['Color'])
    mx = WN.new("ShaderNodeMixShader"); WL.new(lp.outputs['Is Camera Ray'], mx.inputs[0])
    WL.new(bg_l, mx.inputs[1]); WL.new(bgc.outputs[0], mx.inputs[2]); WL.new(mx.outputs[0], outw.inputs['Surface'])
    # aerial haze over the far table so it melts into the gradient
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 16.5, 1.0)); hz = bpy.context.active_object; hz.scale = (40, 30, 2.4)
    hm = bpy.data.materials.new("haze"); hm.use_nodes = True; HN = hm.node_tree.nodes; HN.remove(HN["Principled BSDF"])
    va = HN.new("ShaderNodeVolumeAbsorption"); vs = HN.new("ShaderNodeVolumeScatter"); ad = HN.new("ShaderNodeAddShader")
    dens = float(E("HAZE", "0.35"))
    vs.inputs['Density'].default_value = dens; vs.inputs['Color'].default_value = (*cols[0], 1)
    va.inputs['Density'].default_value = dens * 0.5; va.inputs['Color'].default_value = (*cols[0], 1)
    hm.node_tree.links.new(vs.outputs[0], ad.inputs[0]); hm.node_tree.links.new(va.outputs[0], ad.inputs[1])
    hm.node_tree.links.new(ad.outputs[0], HN["Material Output"].inputs['Volume']); hz.data.materials.append(hm)
    hz.visible_shadow = False
T.sun(float(E("SUN_AZ", "-160")), float(E("SUN_EL", "28")), energy=float(E("SUN_E", "4.5")), color=(1.0, 0.92, 0.8), angle=3)
# soft fill from camera side so the shadow side of the bone stays clean
T.area("fill", (-0.6, -1.4, 0.5), (SX, SY, 0.08), 1.2, float(E("FILL", "25")), color=(0.85, 0.92, 1.0))
T.area("rim", (0.5, 1.0, 1.0), (SX, SY, 0.1), 0.5, float(E("RIM", "18")), color=(1.0, 0.9, 0.75))

# ---------------------------------------------------------------- camera
tgt = Vector((SX + float(E("TX", "-0.07")), SY, float(E("TZ", "0.09"))))
cam = Vector((float(E("CAMX", "-0.1")), float(E("CAMY", "-1.15")), float(E("CAMZ", "0.24"))))
C.camera(cam, tgt + Vector((float(E("AIMX", "0.0")), 0, 0)), lens=float(E("LENS", "85")),
         fstop=float(E("FSTOP", "2.8")), focus=(Vector((SX, SY, 0.08)) - cam).length)

if E("CLIP"):
    import clipcheck
    clipcheck.check("mummy_" + V, limit=40); sys.exit(0)

T.grade(sc, sat=float(E("SAT", "1.3")), con=float(E("CON", "1.1")), expo=float(E("EXPO", "0.0")), vig=float(E("VIG", "0.2")))
T.render(sc, "mummy_" + V)
