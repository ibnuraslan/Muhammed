"""Hand-tune after pipeline/anim_look.py (animated-CG look, client 22:45 UTC): keyed world/sun/exposure values the
generic pass can't reach, the camera-ray sky for dusk/night, and a readable blue night inside the station.
blender -b film_anim.blend --python 04_anim_tune.py -- <out.blend>"""
import bpy, sys, math
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; R_ = math.radians
def ob(n): return bpy.data.objects[n]
def rekey(sock, path, keys):
    for f, v in keys:
        setattr(sock, path, v); sock.keyframe_insert(path, frame=f)
nt = sc.world.node_tree
# lighting from the world: brighter, shadows lifted (these are keyed, so the generic x1.6 never applied)
bg = nt.nodes["WorldBG"].inputs["Strength"]
rekey(bg, "default_value", [(1, 1.6), (1150, 1.6), (1235, 0.9), (1560, 0.85)])
# camera-ray sky gradient (added by anim_look): full bright by day, dims to a deep-but-blue evening sky
mix = nt.nodes["anim_look_v1"]
skyb = mix.inputs[2].links[0].from_node
rekey(skyb.inputs["Strength"], "default_value", [(1, 1.0), (1150, 1.0), (1235, 0.42), (1560, 0.4)])
sun = ob("Sun").data
for f, e in ((1, 5.2), (1150, 5.2), (1235, 1.6), (1560, 1.4)):
    sun.energy = e; sun.keyframe_insert("energy", frame=f)
# exposure: high-key day, bright readable blue night inside, readable dusk street
ad = sc.animation_data
if ad and ad.action:
    for layer in ad.action.layers:
        for st in layer.strips:
            for cb in st.channelbags:
                for fc in list(cb.fcurves):
                    if fc.data_path == "view_settings.exposure": cb.fcurves.remove(fc)
for f, ex in ((1, 0.25), (1150, 0.25), (1235, 0.6), (1250, 0.75), (1388, 0.75), (1418, 0.75), (1560, 0.75)):
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)
# station at night: cool blue fill through the windows + a soft key from the front so faces read
moon = ob("StDusk").data; moon.color = (0.45, 0.6, 1.0)
for f, v in ((1, 0), (1214, 0), (1230, 650)):
    moon.energy = v; moon.keyframe_insert("energy", frame=f)
fl = bpy.data.lights.new("StNightKey", "AREA"); fl.size = 3.0; fl.color = (0.55, 0.7, 1.0)
fo = bpy.data.objects.new("StNightKey", fl); sc.collection.objects.link(fo)
fo.location = (-8.3, 57.0, 2.3); fo.rotation_euler = (Vector((-14.0, 57.0, 1.2)) - fo.location).to_track_quat("-Z", "Y").to_euler()
for f, v in ((1, 0), (1214, 0), (1232, 380), (1400, 380), (1430, 0)):
    fl.energy = v; fl.keyframe_insert("energy", frame=f)
torch = ob("PhoneTorch").data; torch.energy = 220
# the station-at-dusk exterior windows read as dark-blue glass rather than black
ff = ob("FaceFill").data
for f, e in ((1, 0), (1430, 0), (1470, 70), (1560, 70)):
    ff.energy = e; ff.keyframe_insert("energy", frame=f)
print("TUNED")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
