import bpy, sys
P=["Mouse","PCL_Object_11","PCL_Object_13","FamilyPhoto","DoorLeaf+1","DoorLeaf-1","CarrelBack"]
for root in ("LibChair","LibDesk","OffChair","OffDesk","IntTable","IntChairKid","IntChairAgent"):
    P += [c.name for c in bpy.data.objects[root].children if c.type=='MESH']
a=sys.argv[sys.argv.index("--")+1:]
sys.argv=[sys.argv[0],"--",a[0],a[1],",".join(P)]
print("BPC_PROPS",P)
exec(open("/home/user/Muhammed/blender/pipeline/body_prop_cross.py").read())
