"""Small-boat helpers for the shared FFT sea (lib/sea.py):

* `float_on(ocean, root, L, W, draft)`  sit a boat on the evaluated wave surface (height + pitch + roll fitted
  to the sea under its footprint), so it rides the swell instead of floating through it.
* `cut_and_wash(ocean, hull_root, L, W, reach)`  geometry nodes on the ocean: delete the sea inside the boat's
  footprint (in the boat's own frame, so it follows its heading) and store 'hullfoam' as a narrow wash.
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix


def _ocean_points(ocean):
    for md in ocean.modifiers:
        if md.type == 'OCEAN':
            md.viewport_resolution = md.resolution      # heights from the same grid that renders
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ocean.evaluated_get(dg); me = oe.to_mesh()
    P = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", P)
    oe.to_mesh_clear()
    P = P.reshape(-1, 3)
    M = np.array(ocean.matrix_world)
    return P @ M[:3, :3].T + M[:3, 3]


def surface_z(ocean, x, y, P=None, r=1.2):
    P = _ocean_points(ocean) if P is None else P
    d = np.hypot(P[:, 0] - x, P[:, 1] - y)
    m = d < r
    if not m.any():
        return 0.0
    w = 1.0 / (d[m] + 0.05)
    return float((P[m, 2] * w).sum() / w.sum())


def float_on(ocean, root, heading_deg, x, y, L=6.0, W=1.8, draft=0.30, P=None):
    """Place `root` at (x, y) heading `heading_deg`, on the wave surface."""
    P = _ocean_points(ocean) if P is None else P
    h = math.radians(heading_deg)
    fwd = Vector((math.cos(h), math.sin(h), 0)); side = Vector((-math.sin(h), math.cos(h), 0))
    c = Vector((x, y, 0))
    zb = surface_z(ocean, *(c + fwd * L * 0.4).xy, P=P); zs = surface_z(ocean, *(c - fwd * L * 0.4).xy, P=P)
    zp = surface_z(ocean, *(c + side * W * 0.45).xy, P=P); zst = surface_z(ocean, *(c - side * W * 0.45).xy, P=P)
    z0 = (zb + zs + zp + zst) / 4
    pitch = math.atan2(zb - zs, L * 0.8) * 0.7          # a boat damps the short waves a little
    roll = math.atan2(zp - zst, W * 0.9) * 0.6
    root.matrix_world = (Matrix.Translation((x, y, z0 - draft)) @ Matrix.Rotation(h, 4, 'Z')
                         @ Matrix.Rotation(-pitch, 4, 'Y') @ Matrix.Rotation(roll, 4, 'X'))
    bpy.context.view_layer.update()
    return z0


def cut_and_wash(ocean, hulls, frames, L=6.0, W=1.8, reach=0.45):
    """hulls: hull objects for the wash; frames: list of boat root objects to cut the sea out of (local ellipse)."""
    ng = bpy.data.node_groups.new("BoatSea", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; Lk = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    acc = None
    for h in hulls:
        oi = N.new("GeometryNodeObjectInfo"); oi.inputs['Object'].default_value = h; oi.transform_space = 'RELATIVE'
        px = N.new("GeometryNodeProximity"); px.target_element = 'FACES'; Lk.new(oi.outputs['Geometry'], px.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Max'].default_value = reach
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        Lk.new(px.outputs['Distance'], mr.inputs['Value'])
        if acc is None:
            acc = mr.outputs[0]
        else:
            mx = N.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'; Lk.new(acc, mx.inputs[0]); Lk.new(mr.outputs[0], mx.inputs[1]); acc = mx.outputs[0]
    last = gi.outputs[0]
    if acc is not None:
        st = N.new("GeometryNodeStoreNamedAttribute"); st.data_type = 'FLOAT'; st.domain = 'POINT'
        st.inputs['Name'].default_value = "hullfoam"; Lk.new(last, st.inputs['Geometry']); Lk.new(acc, st.inputs['Value'])
        last = st.outputs['Geometry']
    pos = N.new("GeometryNodeInputPosition")
    for fr in frames:
        # boat-local position = inverse(boat world) * ocean world * p  (Object Info 'RELATIVE' gives boat in ocean space)
        oi = N.new("GeometryNodeObjectInfo"); oi.inputs['Object'].default_value = fr; oi.transform_space = 'RELATIVE'
        inv = N.new("FunctionNodeInvertMatrix"); Lk.new(oi.outputs['Transform'], inv.inputs[0])
        tp = N.new("FunctionNodeTransformPoint"); Lk.new(pos.outputs[0], tp.inputs['Vector']); Lk.new(inv.outputs[0], tp.inputs['Transform'])
        sp = N.new("ShaderNodeSeparateXYZ"); Lk.new(tp.outputs[0], sp.inputs[0])
        # lens-shaped footprint, pointed at the ends like a waterline: |y| < ry (1 - (x/rx)^2)
        rx, ry = L / 2 - 0.2, W / 2 * 0.76
        xs = N.new("ShaderNodeMath"); xs.operation = 'DIVIDE'; xs.inputs[1].default_value = rx; Lk.new(sp.outputs['X'], xs.inputs[0])
        x2 = N.new("ShaderNodeMath"); x2.operation = 'POWER'; x2.inputs[1].default_value = 2.0; Lk.new(xs.outputs[0], x2.inputs[0])
        lim = N.new("ShaderNodeMath"); lim.operation = 'MULTIPLY_ADD'; lim.inputs[1].default_value = -ry; lim.inputs[2].default_value = ry
        Lk.new(x2.outputs[0], lim.inputs[0])
        ay = N.new("ShaderNodeMath"); ay.operation = 'ABSOLUTE'; Lk.new(sp.outputs['Y'], ay.inputs[0])
        lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; Lk.new(ay.outputs[0], lt.inputs[0]); Lk.new(lim.outputs[0], lt.inputs[1])
        # push the sea inside the waterline down under the keel (no holes: the faces at the edge slope away
        # under the hull, where the planking hides them)
        sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(pos.outputs[0], sep.inputs[0])
        lz = N.new("ShaderNodeSeparateXYZ"); Lk.new(oi.outputs['Location'], lz.inputs[0])
        zz = N.new("ShaderNodeMath"); zz.operation = 'SUBTRACT'; zz.inputs[1].default_value = 0.35; Lk.new(lz.outputs['Z'], zz.inputs[0])
        cmb = N.new("ShaderNodeCombineXYZ"); Lk.new(sep.outputs['X'], cmb.inputs['X']); Lk.new(sep.outputs['Y'], cmb.inputs['Y'])
        Lk.new(zz.outputs[0], cmb.inputs['Z'])
        ax = N.new("ShaderNodeMath"); ax.operation = 'LESS_THAN'; ax.inputs[1].default_value = 1.0
        axa = N.new("ShaderNodeMath"); axa.operation = 'ABSOLUTE'; Lk.new(xs.outputs[0], axa.inputs[0]); Lk.new(axa.outputs[0], ax.inputs[0])
        both = N.new("ShaderNodeMath"); both.operation = 'MULTIPLY'; Lk.new(lt.outputs[0], both.inputs[0]); Lk.new(ax.outputs[0], both.inputs[1])
        spn = N.new("GeometryNodeSetPosition"); Lk.new(last, spn.inputs['Geometry']); Lk.new(both.outputs[0], spn.inputs['Selection'])
        Lk.new(cmb.outputs[0], spn.inputs['Position']); last = spn.outputs[0]
    Lk.new(last, go.inputs[0])
    md = ocean.modifiers.new("BoatSea", "NODES"); md.node_group = ng
    return md
