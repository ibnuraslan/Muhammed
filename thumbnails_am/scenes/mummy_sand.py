"""Mummy thumbnail B1 v3, "half-buried": the composite skull sunk in sand on the right third, its mismatched jaw lying
apart in front of it, also half-buried. Low dusk sun raking across the sand ripples, the dunes running away into a
dark, warm haze (endless, not pitch black). Left of frame stays open for the title. Real cranium + mandible scans.
    PREVIEW=0.4 SPP=48 blender -b --python mummy_sand.py"""
import os, sys, math, random, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
C = T.use("mummy")
import bpy, bmesh
import numpy as np
from mathutils import Vector
import bones as B, sets as S, ph
E = os.environ.get
sc = T.res_setup(int(E("SPP", "256")), noise=0.01)

SK = Vector((float(E("SKX", "0.0")), float(E("SKY", "0.0")), 0))
# ---------------------------------------------------------------- skull and jaw (placed first; the sand is shaped round them)
cr = B.hero_cranium(tone=((0.66, 0.55, 0.4), (0.36, 0.27, 0.17)))
md = B.hero_mandible(tone=((0.42, 0.3, 0.18), (0.18, 0.12, 0.07)))
cr.rotation_euler = (math.radians(float(E("CRX", "-14"))), math.radians(float(E("CRY", "6"))), math.radians(float(E("CRZ", "-28"))))
cr.location = SK + Vector((0, 0, float(E("CRZ0", "0.075"))))           # sunk: the base well below the sand
md.rotation_euler = (math.radians(float(E("MDRX", "-8"))), math.radians(float(E("MDRY", "16"))), math.radians(float(E("MDRZ", "-70"))))
md.location = SK + Vector((float(E("MDX", "-0.24")), float(E("MDY", "0.12")), float(E("MDZ0", "0.012"))))
bpy.context.view_layer.update()

# ---------------------------------------------------------------- sand: dunes, ripples, heaped up round the bones
sand_id = E("SAND", "coast_sand_01")
ph.texture(sand_id)
SD = os.path.join(T.ROOTS["mummy"], "assets", "polyhaven", sand_id)
m = bpy.data.materials.new("sand"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; pg = N["Principled BSDF"]
tcn = N.new("ShaderNodeTexCoord"); mpn = N.new("ShaderNodeMapping"); mpn.inputs['Scale'].default_value = (1.6, 1.6, 1.6)
L.new(tcn.outputs['Object'], mpn.inputs['Vector'])
def _img(pat, col):
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(glob.glob(os.path.join(SD, pat))[0], check_existing=True)
    t.image.colorspace_settings.name = 'sRGB' if col else 'Non-Color'; t.projection = 'BOX'; t.projection_blend = 0.3
    L.new(mpn.outputs[0], t.inputs['Vector']); return t
dif = _img("*diff*", True); hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = float(E("SSAT", "1.0"))
mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
mul.inputs[7].default_value = (*[float(x) for x in E("STINT", "1.1,0.86,0.62").split(",")], 1)
L.new(dif.outputs['Color'], hs.inputs['Color']); L.new(hs.outputs['Color'], mul.inputs[6]); L.new(mul.outputs[2], pg.inputs['Base Color'])
rg = glob.glob(os.path.join(SD, "*rough*"))
if rg:
    L.new(_img("*rough*", False).outputs['Color'], pg.inputs['Roughness'])
nm = N.new("ShaderNodeNormalMap"); nm.inputs['Strength'].default_value = 1.5
L.new(_img("*nor_gl*", False).outputs['Color'], nm.inputs['Color'])
# wind ripples on top of the texture
wv = N.new("ShaderNodeTexWave"); wv.inputs['Scale'].default_value = float(E("RIPPLE", "9")); wv.inputs['Distortion'].default_value = 6
wv.inputs['Detail'].default_value = 2; L.new(tcn.outputs['Object'], wv.inputs['Vector'])
bmp = N.new("ShaderNodeBump"); bmp.inputs['Strength'].default_value = float(E("RIPS", "0.35")); bmp.inputs['Distance'].default_value = 0.004
L.new(wv.outputs['Fac'], bmp.inputs['Height']); L.new(nm.outputs['Normal'], bmp.inputs['Normal']); L.new(bmp.outputs['Normal'], pg.inputs['Normal'])

# ground mesh: dense near the skull, dunes further out
bpy.ops.mesh.primitive_grid_add(x_subdivisions=400, y_subdivisions=400, size=8, location=(0, 3.2, 0))
g = bpy.context.active_object; g.name = "sand"
bpy.ops.object.transform_apply(location=True)
co = np.empty(len(g.data.vertices) * 3, np.float32); g.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
x, y = co[:, 0], co[:, 1]
rng = np.random.default_rng(3)
z = 0.12 * np.sin(x * 0.9 + 0.5) * np.cos(y * 0.6) + 0.06 * np.sin(x * 2.3 + y * 1.7)          # gentle dunes
z += np.clip((y - 1.0) * 0.12, 0, None) * np.sin(x * 0.7 + y * 0.4)                           # bigger further back
z -= z[np.argmin(x ** 2 + y ** 2)]                                                             # sand level 0 at origin
# heaped round the bones: a soft rim of sand banked up against each one
for (cx, cy, rad, hgt) in ((SK.x, SK.y, 0.16, float(E("HEAP", "0.022"))), (md.location.x, md.location.y, 0.1, 0.02)):
    d2 = (x - cx) ** 2 + (y - cy) ** 2
    z += hgt * np.exp(-d2 / (2 * rad ** 2))
co[:, 2] = z
g.data.vertices.foreach_set("co", co.ravel()); g.data.update()
for pl in g.data.polygons:
    pl.use_smooth = True
g.data.materials.append(m)
# a far plane so the dunes never end
S.box("far_sand", (0, 40, -0.4), (200, 60, 0.1), m)

# ---------------------------------------------------------------- dusk light: low sun behind, warm haze
HD = E("HDRI", "qwantani_dusk_2_puresky")
SUN_AZ = float(E("SUN_AZ", "105"))
ph.world_hdri(HD, strength=float(E("SKY_K", "0.22")), rot_z=T.hdri_sun_rot(HD, SUN_AZ), res="4k")
# what the camera sees of the sky: deep dusk above, a warm glow low down (camera rays only)
wn = sc.world.node_tree; WN = wn.nodes; WL = wn.links
outw = [n for n in WN if n.type == 'OUTPUT_WORLD'][0]; bg_l = outw.inputs['Surface'].links[0].from_socket
lp = WN.new("ShaderNodeLightPath"); tcw = WN.new("ShaderNodeTexCoord"); spw = WN.new("ShaderNodeSeparateXYZ")
WL.new(tcw.outputs['Window'], spw.inputs[0]); rmp = WN.new("ShaderNodeValToRGB"); WL.new(spw.outputs['Y'], rmp.inputs['Fac'])
el = rmp.color_ramp.elements
el[0].position = 0.45; el[0].color = (*[float(x) for x in E("SKY_LO", "1.0,0.42,0.12").split(",")], 1)
el[1].position = 1.0; el[1].color = (*[float(x) for x in E("SKY_HI", "0.05,0.04,0.09").split(",")], 1)
e3 = el.new(0.62); e3.color = (0.45, 0.14, 0.12, 1)
bgc = WN.new("ShaderNodeBackground"); bgc.inputs['Strength'].default_value = float(E("SKYV_K", "0.9"))
WL.new(rmp.outputs['Color'], bgc.inputs['Color'])
mxw = WN.new("ShaderNodeMixShader"); WL.new(lp.outputs['Is Camera Ray'], mxw.inputs[0])
WL.new(bg_l, mxw.inputs[1]); WL.new(bgc.outputs[0], mxw.inputs[2]); WL.new(mxw.outputs[0], outw.inputs['Surface'])
T.sun(SUN_AZ, float(E("SUN_EL", "7")), energy=float(E("SUN_E", "6.0")), color=(1.0, 0.6, 0.3), angle=1.0)
T.area("fill", (-0.8, -1.4, 0.6), (SK.x, SK.y, 0.05), 1.5, float(E("FILL", "12")), color=(0.6, 0.75, 1.0))
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 22, 2.5)); hz = bpy.context.active_object; hz.scale = (60, 40, 6)
hm = bpy.data.materials.new("haze"); hm.use_nodes = True; HN = hm.node_tree.nodes; HN.remove(HN["Principled BSDF"])
vs = HN.new("ShaderNodeVolumeScatter"); vs.inputs['Density'].default_value = float(E("HAZE", "0.008"))
vs.inputs['Anisotropy'].default_value = 0.6; vs.inputs['Color'].default_value = (1.0, 0.7, 0.45, 1)
hm.node_tree.links.new(vs.outputs[0], HN["Material Output"].inputs['Volume']); hz.data.materials.append(hm); hz.visible_shadow = False

# ---------------------------------------------------------------- camera: low over the sand, skull on the right third
cam = Vector((float(E("CAMX", "-0.26")), float(E("CAMY", "-0.72")), float(E("CAMZ", "0.075"))))
tgt = Vector((float(E("AX", "-0.1")), float(E("AY", "0.5")), float(E("AZ", "0.075"))))
C.camera(cam, tgt, lens=float(E("LENS", "45")), fstop=float(E("FSTOP", "2.8")), focus=(SK + Vector((0, 0, 0.08)) - cam).length)

if E("CLIP"):
    import clipcheck
    clipcheck.check("mummy_sand", limit=40); sys.exit(0)
T.grade(sc, sat=float(E("SAT", "1.2")), con=float(E("CON", "1.12")), expo=float(E("EXPO", "0.0")), vig=float(E("VIG", "0.35")))
T.render(sc, "mummy_sand")
