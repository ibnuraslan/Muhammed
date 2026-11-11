"""Film-specific animated-CG look fixes, run AFTER pipeline/anim_look.py (STYLE_ANIMATED.md, client Nov 11 22:45 + hands rule 23:00).
blender -b look_base.blend -P 05_look.py -- <out.blend>"""
import bpy, sys, math
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; OB = bpy.data.objects; R_ = math.radians
def srgb(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1,)
# ---- void backdrop -> bright sky-blue gradient (#4FC3F7 top -> #E8F7FF bottom)
mv = bpy.data.materials["Void_gradient"]
for n in mv.node_tree.nodes:
    if n.type == 'VALTORGB':
        n.color_ramp.elements[0].color = srgb("#E8F7FF"); n.color_ramp.elements[0].position = 0.3
        n.color_ramp.elements[1].color = srgb("#4FC3F7"); n.color_ramp.elements[1].position = 0.8
    if n.type == 'MIX': n.inputs[0].default_value = 0.04
    if n.type == 'EMISSION': n.inputs[1].default_value = 1.0
for L in [o for o in OB if o.name.startswith("Void_light_")]:
    L.data.energy *= 2.2; L.data.color = (1, 1, 1)
# ---- explainer materials readable on a light background
def bsdf(m): return next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
b = bsdf(bpy.data.materials["Scan_points"]); b.inputs["Base Color"].default_value = (0.0, 0.2, 0.75, 1)
b.inputs["Emission Color"].default_value = (0.0, 0.25, 1.0, 1); b.inputs["Emission Strength"].default_value = 1.2
b = bsdf(bpy.data.materials["CAD_new"]); b.inputs["Base Color"].default_value = (0.95, 0.55, 0.12, 1); b.inputs["Emission Strength"].default_value = 0.0
b.inputs["Roughness"].default_value = 0.35
b = bsdf(bpy.data.materials["Ref_holo"]); b.inputs["Base Color"].default_value = (0.2, 0.75, 0.3, 1)
b.inputs["Emission Color"].default_value = (0.2, 0.8, 0.3, 1); b.inputs["Emission Strength"].default_value = 0.4; b.inputs["Alpha"].default_value = 0.55
for nm in ("PLA_print",):
    b = bsdf(bpy.data.materials[nm]); b.inputs["Base Color"].default_value = (0.93, 0.85, 0.66, 1); b.inputs["Roughness"].default_value = 0.4
gm = bpy.data.materials["Ghost"]
for n in gm.node_tree.nodes:
    if n.type == 'EMISSION': n.inputs[0].default_value = (0.02, 0.25, 0.85, 1); n.inputs[1].default_value = 2.0
    if n.type == 'LAYER_WEIGHT': n.inputs[0].default_value = 0.55
b = bsdf(bpy.data.materials["Heavy_beak"]); b.inputs["Base Color"].default_value = (0.25, 0.25, 0.28, 1)
# ---- bright clinic
for o in OB:
    if o.type == 'LIGHT' and (o.name.startswith("Lamp_") or o.name.startswith("Exam_")): o.data.energy *= 1.8
b = bsdf(bpy.data.materials["Light_panel"]); b.inputs["Emission Strength"].default_value = 10
fill = bpy.data.objects.new("Clinic_fill", bpy.data.lights.new("Clinic_fill", 'AREA')); sc.collection.objects.link(fill)
fill.data.size = 3.0; fill.data.energy = 260; fill.location = (5.2, -1.8, 2.2)
fill.rotation_euler = (Vector((7.0, 0.0, 1.0)) - fill.location).to_track_quat('-Z', 'Y').to_euler()
# ---- bright outdoor / zoo: stronger sun + sky fill, lighter forest floor
OB["Sun"].data.energy = 6.0; OB["Sun"].rotation_euler = (R_(38), R_(12), R_(-110))
skyfill = bpy.data.objects.new("Sky_fill", bpy.data.lights.new("Sky_fill", 'SUN')); sc.collection.objects.link(skyfill)
skyfill.data.energy = 1.5; skyfill.data.color = (0.75, 0.88, 1.0); skyfill.data.angle = R_(60); skyfill.rotation_euler = (R_(-30), 0, R_(60))
for nm in ("Forest_floor", "Bark", "Bark_willow"):
    m = bpy.data.materials[nm]
    for n in m.node_tree.nodes:
        if n.type == 'MIX' and n.blend_type == 'MULTIPLY': n.inputs[7].default_value = (1.1, 1.0, 0.8, 1)
OB["Enclosure_sky"].data.energy *= 1.5
# ---- toucan: clean plumage, glossy bill
b = bsdf(bpy.data.materials["Toucan_feathers"]); b.inputs["Roughness"].default_value = 0.42
# ---- hands rule: joint limits on fingers / thumbs / wrists (local space), elbows no hyper-extension
for nm in ("VetA", "VetB", "Assist"):
    rig = OB[nm]
    for pb in rig.pose.bones:
        n = pb.name
        if n.startswith("finger") and "-" in n:
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            if n.startswith("finger1"):
                c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z = R_(-10), R_(60), R_(-30), R_(30), R_(-30), R_(30)
            else:
                c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z = R_(0), R_(90), R_(-5), R_(5), R_(-10), R_(10)
        elif n.startswith("wrist."):
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
            c.use_limit_x = c.use_limit_z = True
            c.min_x, c.max_x, c.min_z, c.max_z = R_(-60), R_(60), R_(-25), R_(25)
# ---- camera: deep focus except true macros (anim_look sets >=5.6); macros 1580-1830 stay at 5.6
sc["look"] = "animated_cg_v1"
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
print("LOOK_DONE", out)
