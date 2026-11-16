"""v002c post-fix applied to the built film blend (same change as 02_sets.py M_DimeTable):
the club-table DimePile10 gets a darker grey-silver metal so it doesn't read white under the club lights.
blender -b TenDimes_v002c_60fps.blend --python scripts/dime_table_mat.py"""
import bpy
m = bpy.data.materials.get("M_DimeTable") or bpy.data.materials["M_Dime"].copy()
m.name = "M_DimeTable"; P = m.node_tree.nodes["Principled BSDF"]
P.inputs['Base Color'].default_value = (0.12, 0.124, 0.132, 1); P.inputs['Roughness'].default_value = 0.30; P.inputs['Metallic'].default_value = 1.0
ob = bpy.data.objects["DimePile10"]; ob.data.materials[0] = m
bpy.ops.wm.save_mainfile(compress=True)
print("DIME_TABLE_OK", ob.data.materials[0].name)
