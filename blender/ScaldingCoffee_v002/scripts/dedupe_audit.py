import bpy, re, hashlib, os
base_of = lambda n: re.sub(r"\.\d{3}$", "", n)
def ck(im):
    if im.packed_file: return hashlib.sha1(im.packed_file.data).hexdigest()
    p = bpy.path.abspath(im.filepath); return hashlib.sha1(open(p,"rb").read()).hexdigest() if os.path.isfile(p) else None
keep = {}; bad = []
for im in bpy.data.images:
    if im.source != 'FILE': continue
    k = (base_of(im.name), tuple(im.size))
    if k in keep:
        if ck(keep[k]) != ck(im): bad.append((im, keep[k]))
    else: keep[k] = im
def users(im):
    out = set()
    for m in bpy.data.materials:
        if m.node_tree and any(n.type=='TEX_IMAGE' and n.image==im for n in m.node_tree.nodes):
            out |= {o.name for o in bpy.data.objects if o.type=='MESH' and any(s.material==m for s in o.material_slots)}
    return out
for im, k in bad:
    print("WRONG", im.name, "->", k.name, sorted(users(im))[:6])
