"""Build the shared tree library for the farm package: every tree variant as its own collection (base at the origin,
custom property 'height'), materials dyed as in the shots, textures external under //../tex/.
    OUT=<farm>/lib/trees.blend blender -b --python build_treelib.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.pop("TREE_LIB", None)
import bpy, rk, rprops as PR
rk.setup()
for k in PR.TREE_SRC:
    col, h = PR._tree_coll(k)
    bpy.context.scene.collection.children.link(col)
    col.use_fake_user = True
out = os.environ["OUT"]; os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("TREELIB", out, [c.name for c in bpy.data.collections])
