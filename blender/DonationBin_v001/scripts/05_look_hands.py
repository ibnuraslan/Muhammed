"""Animated-CG look (STYLE_ANIMATED.md) + hand limits, applied after 03_animate.
blender -b anim.blend --python 05_look_hands.py -- <out.blend>"""
import bpy, sys, os, math
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
sc = bpy.context.scene
# 1. studio look tool (no save); its x1.25 light boost does not reach keyframed energies, so scale those curves here
sys.argv = [sys.argv[0], "--"]
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_look.py")).read())
def scale_curves(idblock, path, k):
    ad = idblock.animation_data
    if not ad or not ad.action: return 0
    n = 0
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == path:
                        for kp in fc.keyframe_points:
                            kp.co.y *= k; kp.handle_left.y *= k; kp.handle_right.y *= k; n += 1
    return n
for L in bpy.data.lights:
    scale_curves(L, "energy", 1.25)
wn = sc.world.node_tree
scale_curves(wn, 'nodes["BG_HDRI"].inputs[1].default_value', 1.6)
# brighter interior (high-key), no grime: lift exposure keys a little
scale_curves(sc, "view_settings.exposure", 1.0)
# 2. clean painted bins: mix the rusty scan texture mostly towards a flat clean paint
PAINT = {"BinSteel": (0.10, 0.36, 0.16), "BinSteelInner": (0.16, 0.30, 0.20), "BinPaint0": (0.45, 0.10, 0.45), "BinPaint1": (0.04, 0.38, 0.45), "BinPaint2": (0.50, 0.52, 0.56)}
for mn, col in PAINT.items():
    m = bpy.data.materials.get(mn)
    if not m: continue
    nt = m.node_tree
    for p in [x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED']:
        bc = p.inputs['Base Color']
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['Factor'].default_value = 0.8
        mx.inputs['B'].default_value = col + (1,)
        if bc.is_linked:
            nt.links.new(bc.links[0].from_socket, mx.inputs['A'])
        nt.links.new(mx.outputs['Result'], bc)
        rr = p.inputs['Roughness']
        for lk in list(rr.links): nt.links.remove(lk)
        rr.default_value = 0.42; p.inputs['Metallic'].default_value = 0.0 if not mn.endswith("Inner") else 0.3
# 3. hands: Limit Rotation (local) on fingers, thumbs, wrists; relaxed curl is already the default pose
R_ = math.radians
nlim = 0
for rig in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    for pb in rig.pose.bones:
        nm = pb.name.split(".")[0]
        if nm.startswith("finger"):
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            if nm.startswith("finger1"):     # thumb: natural cone
                c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z = R_(-15), R_(60), R_(-30), R_(30), R_(-30), R_(30)
            else:
                c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z = R_(0), R_(90), R_(-5), R_(5), R_(-10), R_(10)
            nlim += 1
        elif nm == "wrist":
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z = R_(-60), R_(60), R_(-45), R_(45), R_(-25), R_(25)
            nlim += 1
        # elbows: bend direction is set by the IK pole targets behind each elbow (no hyper-extension in the keyed poses)
print("[look_hands] limit constraints", nlim)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("LOOK_HANDS_DONE")
