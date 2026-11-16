# shared helpers (exec'd)
import bpy, math
from mathutils import Vector, Matrix
def mat(name, rgb, rough=0.5, emit=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    if emit: P.inputs["Emission Color"].default_value = (*rgb, 1); P.inputs["Emission Strength"].default_value = emit
    return m
def bbox(o, local=False):
    bpy.context.view_layer.update()
    if local: vs = [v.co for v in o.data.vertices]
    else: vs = [o.matrix_world @ v.co for v in o.data.vertices]
    return Vector([min(v[i] for v in vs) for i in range(3)]), Vector([max(v[i] for v in vs) for i in range(3)])
def move_to(o, col):
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o)
def tube(name, pts, r, m, col):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 4; cu.use_fill_caps = True
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    sp.use_endpoint_u = True; sp.order_u = min(4, len(pts))
    o = bpy.data.objects.new(name, cu); col.objects.link(o); cu.materials.append(m)
    return o
