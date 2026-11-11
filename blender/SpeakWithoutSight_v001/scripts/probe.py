import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
info = HumanService._create_default_human_info_dict()
info["name"]="Girl"
info["phenotype"]={"gender":0.0,"age":0.19,"muscle":0.5,"weight":0.5,"proportions":0.5,"height":0.5,"cupsize":0.5,"firmness":0.5,"race":{"asian":0.0,"caucasian":1.0,"african":0.0}}
info["rig"]="default"; info["clothes"]=["female_elegantsuit01/female_elegantsuit01.mhclo","shoes02/shoes02.mhclo"]
info["eyes"]="high-poly/high-poly.mhclo"; info["hair"]="braid01/braid01.mhclo"
info["skin_mhmat"]="young_caucasian_female/young_caucasian_female.mhmat"
st=HumanService.get_default_deserialization_settings(); st["subdiv_levels"]=0
HumanService.deserialize_from_dict(info, st)
rig=bpy.data.objects["Girl"]
print("BONES", len(rig.data.bones), [b.name for b in rig.data.bones])
for o in bpy.data.objects:
    print("OBJ",o.name,o.type,tuple(round(d,3) for d in o.dimensions), len(o.data.shape_keys.key_blocks) if o.type=='MESH' and o.data.shape_keys else 0)
