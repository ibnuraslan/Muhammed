"""ShoeBomber shared helpers: GLB import + normalise, simple materials."""
import bpy, math
from mathutils import Vector, Matrix
MODELS = "/opt/assets/sb_models/"
PH = "/opt/assets/ph/"

def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c)
    return c

def link(ob, c):
    for u in list(ob.users_collection): u.objects.unlink(ob)
    c.objects.link(ob)

def import_glb(name, target, dim="max", join=True, collection="Props", obname=None):
    """import a GLB, apply all transforms, join meshes, scale so that `dim` extent == target,
    origin at bottom-centre (x,y centre, z min). Returns the mesh object."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=MODELS + name + ".glb")
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    dg = bpy.context.evaluated_depsgraph_get()
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o)
    for o in meshes:
        o.data = o.data.copy() if o.data.users > 1 else o.data
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    if join and len(meshes) > 1:
        with bpy.context.temp_override(active_object=meshes[0], selected_editable_objects=meshes, object=meshes[0]):
            bpy.ops.object.join()
        meshes = [meshes[0]]
    ob = meshes[0]
    vs = [v.co for v in ob.data.vertices]
    mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
    ext = mx - mn
    ref = {"max": max(ext), "x": ext.x, "y": ext.y, "z": ext.z}[dim]
    s = target / ref
    c = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    ob.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-c))
    ob.name = obname or name
    link(ob, coll(collection))
    return ob

def mat(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0, trans=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    if trans: b.inputs["Transmission Weight"].default_value = trans
    return m

def tex_mat(name, folder, scale=1.0, tint=None, rough_mul=1.0, bump=0.3):
    """Poly Haven texture folder -> principled material (box-ish via object coords not needed; uses UV * scale)"""
    import glob, os
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["UV"], mp.inputs["Vector"])
    fs = glob.glob(PH + folder + "/*")
    def img(key, non_color):
        f = [x for x in fs if key in os.path.basename(x).lower()]
        if not f: return None
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(f[0], check_existing=True)
        if non_color: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    d = img("diff", False)
    if d:
        if tint:
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1
            mx.inputs["B"].default_value = (*tint, 1); L.new(d.outputs["Color"], mx.inputs["A"]); L.new(mx.outputs["Result"], b.inputs["Base Color"])
        else:
            L.new(d.outputs["Color"], b.inputs["Base Color"])
    r = img("rough", True)
    if r:
        mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = rough_mul
        L.new(r.outputs["Color"], mm.inputs[0]); L.new(mm.outputs[0], b.inputs["Roughness"])
    n = img("nor_gl", True)
    if n:
        nm = N.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = bump
        L.new(n.outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m

def set_mat(ob, m):
    ob.data.materials.clear(); ob.data.materials.append(m)

def add_box(name, size, loc, m=None, c="Set", bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("bv", 'BEVEL'); bv.width = bevel; bv.segments = 2
    if m: set_mat(o, m)
    link(o, coll(c)); return o
