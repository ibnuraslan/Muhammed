"""Concept (a): the Mary Celeste alone on a vast dark Atlantic, torn sails backlit by a break in storm cloud,
a shaft of light falling on her empty deck. Low camera near the water; the glitter path leads the eye to her.
No people, no text."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
T.C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, sea

E = os.environ.get
OUT = E("OUT", os.path.join(T.OUTDIR, "a_ghostship.png"))
sc = T.res_setup(int(E("SPP", "256")), noise=0.02)

SUN_AZ = float(E("SUN_AZ", "82"))       # world azimuth of the light (camera looks roughly +Y = 90 deg)
SUN_EL = float(E("SUN_EL", "10"))
WIND_WORLD = Vector((-0.55, -1.0, 0)).normalized()     # wind blows from behind the ship toward the camera-left

MC_HEAD = float(E("HEAD", "228"))
mc = ship.build("MC", sails="found", rail_gap=(-2.7, -0.6, "S"),
                wind=Matrix.Rotation(math.radians(-MC_HEAD), 3, 'Z') @ WIND_WORLD, wet=0.8, detail=True, bow_wave_h=0.5)
mc_pos = Vector((float(E("SHIPX", "12")), float(E("SHIPY", "62")), 0))
mc["root"].location = mc_pos + Vector((0, 0, -0.7))
mc["root"].rotation_euler = (math.radians(-6.0), math.radians(2.0), math.radians(MC_HEAD))
bpy.context.view_layer.update()

water = sea.water_material(deep=(0.0006, 0.008, 0.014), crest=(0.004, 0.05, 0.055), fog_color=(0.16, 0.15, 0.16))
sea.ocean(size=200, res=int(E("OCEAN_RES", "11")), scale=3.4, chop=1.9, wind=16.0, repeat=3, foam=float(E("FOAM", "0.25")), mat=water,
          direction=math.degrees(math.atan2(WIND_WORLD.y, WIND_WORLD.x)), hulls=(mc["hull"],), loc=(10, 70, 0), seed=11)
sea.far_sea(300, mat=water, center=(10, 70))

SKY = E("SKY", "belfast_sunset_puresky")
rot, el = T.sky_with_sun_at(SKY, SUN_AZ, strength=float(E("SKY_K", "0.55")))
print("sky rot", rot, "hdri sun el", el)
# storm drama: push the clouds darker and the break brighter (gamma on the HDRI before the background)
wn = sc.world.node_tree; env = [n for n in wn.nodes if n.type == 'TEX_ENVIRONMENT'][0]
bgn = [n for n in wn.nodes if n.type == 'BACKGROUND'][0]
gm = wn.nodes.new("ShaderNodeGamma"); gm.inputs['Gamma'].default_value = float(E("SKY_G", "1.7"))
wn.links.new(env.outputs['Color'], gm.inputs['Color']); wn.links.new(gm.outputs['Color'], bgn.inputs['Color'])
sunobj = T.sun(SUN_AZ, SUN_EL, energy=float(E("SUN_E", "4.0")), color=(1.0, 0.78, 0.58), angle=1.2)

# the shaft: a narrow, warm spot from high behind the ship through a haze box around her
if E("SHAFT", "1") == "1":
    sp = bpy.data.lights.new("shaft", 'SPOT'); sp.energy = float(E("SHAFT_E", "1.5e6")); sp.color = (1.0, 0.9, 0.78)
    sp.spot_size = math.radians(float(E("SHAFT_DEG", "13"))); sp.spot_blend = 1.0; sp.shadow_soft_size = 2.0
    so = bpy.data.objects.new("shaft", sp); sc.collection.objects.link(so)
    src = mc_pos + Vector((float(E("SHAFT_X", "50")), 110, 240))
    so.location = src; so.rotation_euler = (mc_pos + Vector((0, 0, 8)) - src).to_track_quat('-Z', 'Y').to_euler()
    # a cone of murk around the beam only (soft: the spot's blend shapes the edge, the cone is wider than the beam)
    axis = (mc_pos + Vector((0, 0, 8)) - src); ln = axis.length
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.1, radius2=ln * math.tan(math.radians(float(E("SHAFT_DEG", "13")) / 2)) * 1.5, depth=ln * 1.15,
                                    location=src + axis * 0.575)
    hz = bpy.context.active_object; hz.name = "shaft_haze"
    hz.rotation_euler = axis.to_track_quat('-Z', 'Y').to_euler()
    hm = bpy.data.materials.new("shaft_haze"); hm.use_nodes = True; HN = hm.node_tree.nodes; HN.remove(HN["Principled BSDF"])
    vv = HN.new("ShaderNodeVolumePrincipled"); vv.inputs['Density'].default_value = float(E("HAZE", "0.05"))
    vv.inputs['Color'].default_value = (0.85, 0.85, 0.85, 1); vv.inputs['Anisotropy'].default_value = 0.5
    hm.node_tree.links.new(vv.outputs[0], HN["Material Output"].inputs['Volume']); hz.data.materials.append(hm)
    # streaky murk: density varies, so the beam breaks into rays
    htc = HN.new("ShaderNodeTexCoord"); hn = HN.new("ShaderNodeTexNoise"); hn.inputs['Scale'].default_value = 0.035
    hn.inputs['Detail'].default_value = 3; hm.node_tree.links.new(htc.outputs['Object'], hn.inputs['Vector'])
    hmr = HN.new("ShaderNodeMapRange"); hmr.inputs['From Min'].default_value = 0.35; hmr.inputs['From Max'].default_value = 0.65
    hmr.inputs['To Min'].default_value = 0.2 * float(E("HAZE", "0.05")); hmr.inputs['To Max'].default_value = float(E("HAZE", "0.05")) * 1.6
    hm.node_tree.links.new(hn.outputs['Fac'], hmr.inputs['Value']); hm.node_tree.links.new(hmr.outputs[0], vv.inputs['Density'])
    hz.visible_shadow = False
    sunobj.visible_volume_scatter = False      # only the shaft lights the haze: a beam, not a fog

cam_loc = Vector((0, 0, float(E("CAMZ", "3.5"))))
tgt = mc_pos + Vector((float(E("TX", "-8")), 0, float(E("TZ", "9"))))
T.C.camera(cam_loc, tgt, lens=float(E("LENS", "40")), fstop=5.6, focus=(mc_pos - cam_loc).length, roll=float(E("ROLL", "1.5")))

T.C.finish(OUT, cine={"sat": 1.15, "exposure": float(E("EXPO", "0.0")), "contrast": 1.12}, bloom=0.5)
print("RENDERED", OUT)
