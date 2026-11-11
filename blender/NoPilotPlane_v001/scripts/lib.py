# Shared helpers for NoPilotPlane (exec'd by build/animate scripts).
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler

R_ = math.radians
C = bpy.context

def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        (parent or C.scene.collection).children.link(c)
    return c

def link(ob, c):
    for u in ob.users_collection: u.objects.unlink(ob)
    c.objects.link(ob)
    return ob

# ------------------------------------------------------------------ materials
def nodes_mat(name):
    m = bpy.data.materials.get(name)
    if m: return m, None
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree

def mat(name, col, rough=0.5, metal=0.0, noise=0.0, nscale=40.0, bump=0.0, emit=None, estr=0.0, spec=0.5, coat=0.0):
    m, nt = nodes_mat(name)
    if nt is None: return m
    N, L = nt.nodes, nt.links
    p = N["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if coat: p.inputs["Coat Weight"].default_value = coat
    if noise or bump:
        tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = nscale; nz.inputs["Detail"].default_value = 8
        L.new(tc.outputs["Object"], nz.inputs["Vector"])
        if noise:
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs["Factor"].default_value = noise
            mx.inputs["A"].default_value = (*col, 1)
            L.new(nz.outputs["Fac"], mx.inputs["B"])
            mr = N.new("ShaderNodeMapRange"); L.new(nz.outputs["Fac"], mr.inputs["Value"])
            mr.inputs["To Min"].default_value = 0.6; mr.inputs["To Max"].default_value = 1.4
            L.new(mr.outputs["Result"], mx.inputs["B"])
            L.new(mx.outputs["Result"], p.inputs["Base Color"])
        if bump:
            b = N.new("ShaderNodeBump"); b.inputs["Strength"].default_value = bump; b.inputs["Distance"].default_value = 0.002
            L.new(nz.outputs["Fac"], b.inputs["Height"]); L.new(b.outputs["Normal"], p.inputs["Normal"])
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = estr
    return m

def emit_mat(name, col, strength):
    m, nt = nodes_mat(name)
    if nt is None: return m
    N, L = nt.nodes, nt.links
    N.remove(N["Principled BSDF"]); e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    L.new(e.outputs[0], N["Material Output"].inputs["Surface"])
    return m

# ------------------------------------------------------------------ geometry
class MB:
    """accumulate primitive boxes/cylinders into one mesh object with material slots"""
    def __init__(self, name):
        self.name = name; self.bm = bmesh.new(); self.mats = []
    def _mi(self, m):
        if m not in self.mats: self.mats.append(m)
        return self.mats.index(m)
    def _fin(self, geom, M, m):
        vs = [g for g in geom if isinstance(g, bmesh.types.BMVert)]
        bmesh.ops.transform(self.bm, matrix=M, verts=vs)
        mi = self._mi(m)
        for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
        return vs
    def box(self, c, s, m, rot=(0, 0, 0), bevel=0.0):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        vs = r["verts"]
        M = Matrix.Translation(c) @ Euler([R_(a) for a in rot]).to_matrix().to_4x4() @ Matrix.Diagonal((*s, 1))
        self._fin(vs, M, m)
        if bevel:
            es = list({e for v in vs for e in v.link_edges})
            bmesh.ops.bevel(self.bm, geom=es, offset=bevel, segments=2, affect='EDGES', profile=0.5)
        return vs
    def cyl(self, c, r, depth, m, rot=(0, 0, 0), seg=16, r2=None):
        g = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
        M = Matrix.Translation(c) @ Euler([R_(a) for a in rot]).to_matrix().to_4x4()
        return self._fin(g["verts"], M, m)
    def sphere(self, c, r, m, scale=(1, 1, 1), seg=12):
        g = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=seg // 2 + 2, radius=r)
        M = Matrix.Translation(c) @ Matrix.Diagonal((*scale, 1))
        return self._fin(g["verts"], M, m)
    def obj(self, c=None, smooth=False):
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free()
        for m in self.mats: me.materials.append(m)
        if smooth:
            for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(self.name, me)
        (c or C.scene.collection).objects.link(ob)
        return ob

def empty(name, loc=(0, 0, 0), c=None, parent=None):
    e = bpy.data.objects.new(name, None); e.location = loc
    (c or C.scene.collection).objects.link(e)
    if parent: e.parent = parent
    return e
