import bpy
for o in bpy.data.objects:
    if o.type=='MESH':
        for m in o.data.materials:
            if m: print("MAT", o.name, m.name, [ (n.type, n.image.name if n.type=='TEX_IMAGE' and n.image else '') for n in m.node_tree.nodes if n.type in ('TEX_IMAGE','BSDF_PRINCIPLED','MIX')])
