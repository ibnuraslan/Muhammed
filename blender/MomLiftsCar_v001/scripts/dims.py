import bpy
for o in bpy.data.objects: print("DIM", o.name, o.type, tuple(round(x,2) for x in o.dimensions), o.parent.name if o.parent else None)
