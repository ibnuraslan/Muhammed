"""v002c (director): friend's eyes read as glowing white -> darker brown irises, sclera 0.8. Shader only.
blender -b SafetyPin_v002b_60fps.blend --python 07_v002c_eyes.py -- out.blend   (also exec'd by 03_anim for rebuilds)"""
import bpy, sys
def pal_eyes():
    o = bpy.data.objects["Pal.high-poly"]; n_ = 0
    for m in o.data.materials:
        for nd in m.node_tree.nodes:
            if nd.type == 'GROUP' and nd.node_tree and nd.node_tree.name.startswith("EnhancedEye"):
                nd.inputs["IrisMajorColor"].default_value = (0.30, 0.17, 0.07, 1)
                nd.inputs["IrisMinorColor"].default_value = (0.13, 0.07, 0.03, 1)
                nd.inputs["EyeWhiteColor"].default_value = (0.80, 0.80, 0.80, 1)
                n_ += 1
    print("PAL_EYES", n_)
if __name__ == "__main__" and "--" in sys.argv:
    pal_eyes()
    bpy.context.scene.render.filepath = "//render/SafetyPin_v002c_"; bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--") + 1], compress=True)
