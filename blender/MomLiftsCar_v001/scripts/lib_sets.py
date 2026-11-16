def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c

def mat(name, rgb, rough=0.5, metal=0.0, emit=None, alpha=1.0, coat=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    P.inputs["Metallic"].default_value = metal
    P.inputs["Coat Weight"].default_value = coat
    if emit: P.inputs["Emission Color"].default_value = (*emit[0], 1); P.inputs["Emission Strength"].default_value = emit[1]
    if alpha < 1: P.inputs["Alpha"].default_value = alpha
    return m

def alive(lst):
    out = []
    for o in lst:
        try: o.name; out.append(o)
        except ReferenceError: pass
    return out

def link(o, c):
    for cc in o.users_collection: cc.objects.unlink(o)
    c.objects.link(o)

def box(name, c, loc, size, m, bevel=0.01, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    o.data.materials.append(m); link(o, c)
    for p in o.data.polygons: p.use_smooth = True
    return o

def plane(name, c, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); link(o, c); return o

def import_glb(path, name, c, scale=1.0, loc=(0, 0, 0), rotz=0.0, keep=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name, None); c.objects.link(root)
    for o in new:
        link(o, c)
        if o.parent is None: o.parent = root
    meshes = [o for o in new if o.type == 'MESH']
    if keep is not None:
        for o in meshes:
            if not keep(o): bpy.data.objects.remove(o)
        meshes = alive(meshes)
    root.scale = (scale,) * 3; root.location = loc; root.rotation_euler.z = rotz
    bpy.context.view_layer.update()
    return root, meshes

def bounds(obs):
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in obs:
        for cc in o.bound_box:
            w = o.matrix_world @ Vector(cc); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    return mn, mx

def lathe(name, c, prof, m, loc, segs=48, cap_bottom=True):
    """prof: list of (r, z) bottom->top; returns mesh object revolved around Z"""
    bm = bmesh.new(); rings = []
    for r, z in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            bm.faces.new((a[i], a[(i + 1) % segs], b[(i + 1) % segs], b[i]))
    if cap_bottom and prof[0][0] > 0: bm.faces.new(list(reversed(rings[0])))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.location = loc
    for p in me.polygons: p.use_smooth = True
    me.materials.append(m); return o

def logo_mat(name, dark=True):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(BRAND + ("DaKrasFilms_logo_dark.png" if dark else "DaKrasFilms_logo_white.png"))
    t.extension = 'CLIP'
    nt.links.new(t.outputs["Color"], P.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], P.inputs["Alpha"])
    P.inputs["Roughness"].default_value = 0.4
    m.blend_method = 'HASHED' if hasattr(m, "blend_method") else None
    return m

