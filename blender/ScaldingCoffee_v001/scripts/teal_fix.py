import bpy, bmesh
from mathutils import Vector
def strip_teal_text(ob, region=((0.55,1.25),(-9,9),(0.25,0.42))):
    """delete mesh islands lying fully inside region (root-scale-1 coordinates of the teal glb) = the raised brand letters"""
    bm=bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    M=ob.matrix_world
    seen=set(); kill=[]
    def inside(v):
        c=M@v.co; return all(lo<=c[i]<=hi for i,(lo,hi) in enumerate(region))
    for v in bm.verts:
        if v.index in seen: continue
        isl=[]; st=[v]; seen.add(v.index)
        while st:
            a=st.pop(); isl.append(a)
            for e in a.link_edges:
                b=e.other_vert(a)
                if b.index not in seen: seen.add(b.index); st.append(b)
        if all(inside(x) for x in isl): kill+=isl
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(ob.data); bm.free()
    return len(kill)
if __name__=="__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath="assets/coffee_teal.glb")
    ob=[o for o in bpy.data.objects if o.type=='MESH'][0]
    print("PARENT", ob.parent, ob.parent.scale if ob.parent else None, ob.matrix_local.to_scale())
    for o in bpy.data.objects:
        if o.parent is None: o.scale=(1,1,1)
    bpy.context.view_layer.update()
    print("KILLED", strip_teal_text(ob))
    exec(open("scripts/views.py").read().split("sc=bpy.context.scene")[0].split("print(\"BB\"")[0].replace("a=sys.argv","#").replace("bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)","").replace("for o in bpy.data.objects:\n    if o.parent is None: o.scale=(scale,)*3",""))
