"""BelugaRescue: FX (ocean, caustics, grade, bubbles, explainer card, X-ray calf) and the one continuous camera.
blender -b work/anim.blend --python 03b_fx_camera.py -- <out.blend>"""
import sys, os, math, json, random
import bpy
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
V = lambda *a: Vector(a)
END = sc.frame_end
WATER_Z, DECK_Z = 6.0, 6.25
random.seed(5)

def lin_keys(fc_owner, path, pairs, index=-1):
    for f, v in pairs:
        if index >= 0:
            getattr(fc_owner, path)[index] = v; fc_owner.keyframe_insert(path, index=index, frame=f)
        else:
            setattr(fc_owner, path, v); fc_owner.keyframe_insert(path, frame=f)
def all_fcurves(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action: return []
    out = []
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out
def linear(idblock):
    for fc in all_fcurves(idblock):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ ocean + caustics time
surf = bpy.data.objects["Water_Surface"]; om = surf.modifiers["Ocean"]
om.time = 0.0; om.keyframe_insert("time", frame=1); om.time = END / 60.0 * 1.2; om.keyframe_insert("time", frame=END)
linear(surf)
cau = bpy.data.objects["Caustic_Spot"]
vor = cau.data.node_tree.nodes["CausticVoronoi"]
vor.inputs['W'].default_value = 0.0; vor.inputs['W'].keyframe_insert("default_value", frame=1)
vor.inputs['W'].default_value = END / 60.0 * 0.6; vor.inputs['W'].keyframe_insert("default_value", frame=END)
linear(cau.data.node_tree)
# light shafts sway a little
for i, o in enumerate(o for o in bpy.data.objects if o.name.startswith("Shaft_")):
    r0 = o.rotation_euler.copy()
    for f in range(1, END + 1, 120):
        o.rotation_euler = (r0.x + R_(2.0 * math.sin(f / 90 + i)), r0.y + R_(2.0 * math.cos(f / 110 + i * 1.3)), 0)
        o.keyframe_insert("rotation_euler", frame=f)

# ------------------------------------------------------------------ grade: light dims at depth, brightens on the ascent, blur on "out of breath"
vs = sc.view_settings
vol = bpy.data.materials["M_WaterVolume"].node_tree.nodes["WaterVol"]
GK = [(1, 0.1, 0.008), (80, 0.1, 0.008), (170, 0.15, 0.009), (264, 0.05, 0.011), (520, 0.05, 0.011), (900, 0.1, 0.01), (1213, 0.05, 0.011),
      (1600, 0.1, 0.01), (1800, 0.2, 0.009), (1884, 0.25, 0.008), (1930, 0.1, 0.008), (END, 0.1, 0.008)]      # bright, clear water (animated look)
for f, ex, dens in GK:
    vs.exposure = ex; vs.keyframe_insert("exposure", frame=f)
    vol.inputs['Density'].default_value = dens; vol.inputs['Density'].keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ camera rig
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.lens = 26; cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.02; cam_d.clip_end = 200
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_d.dof.focus_object = aim
D = bpy.data.objects["Diver"]; BR = bpy.data.objects["Beluga_Rig"]
def dv(bone, f, which="head"):
    ev(f); pb = D.pose.bones[bone]; return D.matrix_world @ (pb.head if which == "head" else pb.tail)
def calf(f): return dv("lowerleg01.R", f).lerp(dv("foot.R", f), 0.35)
def wh(f, s=0.1, z=0.0):
    ev(f); hb = BR.pose.bones["head"]
    return BR.matrix_world @ (hb.head.lerp(hb.tail, s / 0.2 if s < 0.2 else 1.0) + Vector((0, 0, z)))
def eye(f):
    ev(f); return bpy.data.objects["Beluga_Eye_L"].matrix_world.translation.copy()
def wbody(f): ev(f); return BR.matrix_world.translation.copy()
X0 = 0.6
def H_(f): return dv("head", f) + Vector((0, 0, 0.05))
def CH(f): return dv("spine02", f)
def PEL(f): return dv("root", f)
ring = bpy.data.objects["RingToy"]
def RG(f): ev(f); return ring.matrix_world.translation.copy()
# framings: (frame, camera position, aim, lens)  — one every ~1 s; positions may depend on the action
FR = []
def K(f, c, a, l): FR.append((f, c, a, float(l)))
# beat 1 — deck, spring, entry, through the surface
K(1, V(X0 + 1.6, -3.7, DECK_Z + 1.7), V(X0, -5.2, DECK_Z + 1.3), 26)
K(40, V(X0 + 1.5, -4.2, DECK_Z + 1.3), PEL(40), 26)
K(66, V(X0 + 1.9, -3.4, 6.9), H_(66), 24)
K(84, V(X0 + 1.3, -3.0, 6.12), CH(84), 22)
K(104, V(X0 + 1.1, -2.6, 5.05), CH(104), 22)
K(138, V(X0 + 0.5, -3.3, 5.0), H_(138), 24)
# beat 2 — under her, then down to floor level
K(178, V(X0 + 1.2, -0.6, 1.5), CH(178), 20)
K(218, V(X0 + 1.7, -0.5, 0.85), PEL(218), 22)
K(255, V(X0 + 1.5, -0.1, 0.32), PEL(255) + V(0, 0, 0.2), 24)
# beat 3 — skim to the legs, macro calf (X-ray), orbit, out
K(292, V(X0 + 1.9, 1.05, 0.22), calf(292), 30)
K(350, calf(350) + V(0.85, 0.2, 0.3), calf(350), 45)
K(405, calf(405) + V(0.35, 0.8, 0.4), calf(405), 50)
K(458, calf(458) + V(0.7, 0.45, 0.65), calf(458), 48)
K(515, V(X0 + 1.7, 0.1, 0.9), CH(515), 32)
# beat 4 — crane up looking down at her reaching, down with her
K(562, V(X0 + 1.0, -0.65, 2.6), CH(562), 26)
K(605, V(X0 + 0.7, -0.4, 3.0), H_(605), 26)
K(650, V(X0 + 1.4, -0.4, 1.25), CH(650), 28)
# beat 5 — face in the mask, arc
K(700, H_(700) + V(0.75, 0.6, 0.1), H_(700), 45)
K(748, H_(748) + V(-0.6, 0.6, 0.45), H_(748), 42)
# beat 6 — rack focus from her face to the whale, orbit the whale's head
def behind_face(f, wf):
    h = H_(f); d = (h - wh(wf)); d.z = 0; d.normalize(); d = Matrix.Rotation(R_(115), 3, 'Z') @ d; return h + d * 0.8 + V(0, 0, 0.2)
K(792, H_(792) + V(0.85, 0.75, 0.2), H_(792), 40)
K(835, H_(835) + V(0.95, 0.55, 0.3), H_(835).lerp(wh(835), 0.35), 34)
K(872, wh(872) + V(1.4, -1.1, 0.4), wh(872), 32)
K(910, wh(910) + V(0.6, -2.4, 0.7), wh(910), 26)
# beat 7 — beside the whale to the window, ring play, keeper nod, whip pan back
K(962, V(2.2, 1.4, 3.3), wh(962), 28)
K(1010, RG(1010) + V(2.8, 1.8, 0.7), RG(1010), 26)
K(1065, wbody(1065) + V(2.6, 2.4, 0.9), wbody(1065), 24)
K(1120, V(0.2, -1.4, 2.1), V(-2.6, -4.3, 1.6), 26)
K(1170, V(-0.4, -2.2, 1.9), V(-2.6, -5.85, 1.55), 30)
K(1200, eye(1200) + V(0.8, 2.6, 0.5), eye(1200), 34)
# beat 8 — eye macro, head turns, surge
K(1230, eye(1230) + V(0.4, 2.4, 0.4), eye(1230), 40)
K(1268, eye(1268) + V(0.6, 3.2, 0.9), eye(1268).lerp(H_(1268), 0.5), 24)
K(1305, wbody(1305) + V(2.2, 1.0, 0.7), wh(1305), 26)
K(1350, wh(1350) + V(1.3, 1.2, 0.3), CH(1350), 28)
# beat 9 — mouth on the ankle, beneath looking up, spiral up
K(1420, dv("foot.R", 1420) + V(1.3, 0.9, 0.5), dv("foot.R", 1420).lerp(CH(1420), 0.4), 30)
K(1480, dv("foot.R", 1480) + V(1.6, -1.0, 0.4), dv("foot.R", 1480).lerp(CH(1480), 0.4), 28)
K(1545, PEL(1545) + V(1.6, 0.9, -1.7), PEL(1545), 22)
K(1605, PEL(1605) + V(-0.6, 1.9, -1.2), PEL(1605), 24)
K(1660, PEL(1660) + V(-1.8, 0.3, -0.6), CH(1660), 26)
# beat 10 — her face, racing alongside, up into the light
K(1720, H_(1720) + V(0.5, 0.8, -0.5), H_(1720), 38)
K(1775, H_(1775) + V(1.3, 1.0, 0.0), H_(1775), 32)
K(1840, H_(1840) + V(1.4, 0.7, -0.3), H_(1840) + V(0, 0, 0.3), 26)
# beat 11 — below the surface looking up, burst out, circle the splash
K(1893, V(X0 + 1.2, -3.1, 5.55), H_(1893) + V(0, 0, 0.3), 24)
K(1925, V(X0 + 1.4, -2.7, 6.45), H_(1925), 26)
K(1965, V(X0 + 1.7, -2.0, 6.9), H_(1965), 28)
K(2010, V(X0 + 0.6, -1.9, 7.0), H_(2010), 30)
# beat 12 — face at the edge, rise and pull back to reveal everything
K(2075, H_(2075) + V(0.7, 0.85, 0.25), H_(2075), 40)
K(2130, H_(2130) + V(1.4, 2.6, 1.6), H_(2130) + V(0, -0.5, 0.2), 30)
K(END, H_(END) + V(2.0, 4.3, 2.8), H_(END) + V(-0.4, -1.0, 0.3), 26)
FR.sort(key=lambda x: x[0])
fc = catmull([(f, c) for f, c, a, l in FR]); fa = catmull([(f, a) for f, c, a, l in FR]); fl = catmull([(f, l) for f, c, a, l in FR])
for f in list(range(1, END + 1, 2)) + [END]:
    cam.location = fc(f); cam.keyframe_insert("location", frame=f)
    aim.location = fa(f); aim.keyframe_insert("location", frame=f)
    cam_d.lens = fl(f); cam_d.keyframe_insert("lens", frame=f)
# clearance: keep the lens >= 0.35 m from the whale and the diver and out of static solids; smooth the corrections
from mathutils.bvhtree import BVHTree

class WB:
    """world-space BVH wrapper (BVHTree.FromObject works in object-local space)"""
    def __init__(self, o, dg):
        self.t = BVHTree.FromObject(o, dg); self.M = o.matrix_world.copy(); self.Mi = self.M.inverted(); self.R = self.M.to_3x3()
    def find_nearest(self, p, dmax=1e9):
        loc, nrm, idx, dist = self.t.find_nearest(self.Mi @ p, dmax)
        if loc is None: return None, None, None, None
        loc = self.M @ loc; nrm = (self.R @ nrm).normalized()
        return loc, nrm, idx, (p - loc).length
BEL = bpy.data.objects["Beluga"]; DBODY = bpy.data.objects["Diver.body"]
SOLID = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("IceBoulder", "FrontWall", "Coping", "Deck", "Acrylic", "IceWall"))]
dg = bpy.context.evaluated_depsgraph_get()
ST = [WB(o, dg) for o in SOLID]
CLR = 0.35
corr = {}
for f in range(1, END + 1, 2):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    p = fc(f); off = Vector((0, 0, 0))
    for o, need in ((BEL, 0.7), (DBODY, 0.3)):
        t = WB(o, dg)
        for _ in range(6):
            loc, nrm, idx, dist = t.find_nearest(p + off, 3.0)
            if loc is None: break
            inside = (p + off - loc).dot(nrm) < 0
            if inside or dist < need:
                push = (need + (dist if inside else -dist)) * 1.05
                off += nrm.normalized() * push
            else: break
    for t in ST:
        loc, nrm, idx, dist = t.find_nearest(p + off, 0.5)
        if loc is not None and ((p + off - loc).dot(nrm) < 0 or dist < 0.4):
            off += nrm.normalized() * (0.42 + (dist if (p + off - loc).dot(nrm) < 0 else -dist))
    if (p + off).z < 0.15: off.z += 0.15 - (p + off).z
    corr[f] = off
fr_ = sorted(corr)
env = {}
for f in fr_:      # envelope: the strongest correction within +-20 frames
    env[f] = max((corr[g] for g in fr_ if abs(g - f) <= 20), key=lambda v: v.length)
for f in list(range(1, END + 1, 2)) + [END]:
    acc = Vector((0, 0, 0)); wsum = 0
    for g in fr_:
        if abs(g - f) <= 30:
            w_ = math.exp(-((g - f) / 14.0) ** 2); acc += env[g] * w_; wsum += w_
    cam.location = fc(f) + acc / max(wsum, 1e-6); cam.keyframe_insert("location", frame=f)
print("CAMERA clearance corrected frames:", sum(1 for v in corr.values() if v.length > 1e-4))
# out-of-breath blur: open the aperture wide
for f, st in ((1, 6.0), (330, 6.0), (360, 4.0), (480, 4.0), (510, 6.0), (1700, 6.0), (1740, 2.0), (1800, 2.0), (1870, 6.0), (END, 6.0)):   # shallow only on the calf macro and her blurring vision
    cam_d.dof.aperture_fstop = st; cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
json.dump([(f, list(c), list(a), l) for f, c, a, l in FR], open(os.path.join(HERE, "..", "camera_path.json"), "w"), indent=0)

# ------------------------------------------------------------------ explainer gradient card behind the calf (beat 3)
bpy.ops.mesh.primitive_plane_add(size=1)
card = bpy.context.active_object; card.name = "Explainer_Backdrop"
card.parent = cam; card.location = (0, 0, -1.6); card.scale = (2.2, 2.2, 1)
cm = bpy.data.materials.new("M_ExplainerGradient"); cm.use_nodes = True
cn, cl = cm.node_tree.nodes, cm.node_tree.links; cn.clear()
co = cn.new('ShaderNodeOutputMaterial'); em = cn.new('ShaderNodeEmission'); tr = cn.new('ShaderNodeBsdfTransparent'); mx = cn.new('ShaderNodeMixShader')
tc = cn.new('ShaderNodeTexCoord'); gr = cn.new('ShaderNodeTexGradient'); gr.gradient_type = 'LINEAR'
mp = cn.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, -1.5708); mp.inputs['Location'].default_value = (0.5, 0, 0)
rp = cn.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (0.8, 0.94, 1.0, 1); rp.color_ramp.elements[1].color = (0.077, 0.54, 0.93, 1)
val = cn.new('ShaderNodeValue'); val.name = "CardFade"
cl.new(tc.outputs['Object'], mp.inputs['Vector']); cl.new(mp.outputs['Vector'], gr.inputs['Vector']); cl.new(gr.outputs['Fac'], rp.inputs['Fac'])
cl.new(rp.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 1.6
cl.new(val.outputs[0], mx.inputs['Fac']); cl.new(tr.outputs[0], mx.inputs[1]); cl.new(em.outputs[0], mx.inputs[2]); cl.new(mx.outputs[0], co.inputs['Surface'])
card.data.materials.append(cm)
card.visible_shadow = False; card.visible_diffuse = False; card.visible_glossy = False; card.visible_transmission = False; card.visible_volume_scatter = False
for f, v in ((1, 0.0), (330, 0.0), (352, 1.0), (470, 1.0), (500, 0.0)):
    val.outputs[0].default_value = v; val.outputs[0].keyframe_insert("default_value", frame=f)
for f, h in ((1, True), (329, False), (501, True)):
    card.hide_render = h; card.keyframe_insert("hide_render", frame=f)
    card.hide_viewport = h; card.keyframe_insert("hide_viewport", frame=f)
# card distance follows the focus distance + 0.5 m
for f in range(326, 506, 6):
    d_ = (fc(f) - fa(f)).length
    card.location = (0, 0, -(d_ + 0.45)); card.keyframe_insert("location", frame=f)
    s_ = (d_ + 0.45) * 36 / fl(f) * 1.1
    card.scale = (s_, s_ * 1.8, 1); card.keyframe_insert("scale", frame=f)

# ------------------------------------------------------------------ X-ray calf: porthole in the wetsuit + knotted muscle that pulses red
DB = bpy.data.objects["Diver.body"]
xc = bpy.data.objects.new("XRay_Center", None); sc.collection.objects.link(xc)
ev(1); lb = D.pose.bones["lowerleg01.R"]
xc.parent = D; xc.parent_type = 'BONE'; xc.parent_bone = "lowerleg01.R"
xc.matrix_parent_inverse = (D.matrix_world @ lb.matrix @ Matrix.Translation(Vector((0, lb.length, 0)))).inverted()
xc.matrix_world = Matrix.Translation(D.matrix_world @ (lb.head.lerp(lb.tail, 0.6) + Vector((0, 0.03, 0))))
XK = ((1, 0.0), (340, 0.0), (360, 1.0), (468, 1.0), (492, 0.0))
_gn = {g.index: g.name for g in DB.vertex_groups}
_leg = [0.0] * len(DB.data.vertices)
for i_, v_ in enumerate(DB.data.vertices):
    gs = [(_gn[g.group], g.weight) for g in v_.groups if _gn[g.group] in D.data.bones]
    if gs:
        nm_ = max(gs, key=lambda x: x[1])[0]
        _leg[i_] = 1.0 if nm_ in ("lowerleg01.R", "lowerleg02.R", "foot.R", "upperleg02.R") else 0.0
_la = DB.data.attributes.new("legmask", 'FLOAT', 'POINT'); _la.data.foreach_set("value", _leg)
done = set()
for ob in [DB] + [o for o in D.children if o.name.endswith("FootPocket_R")]:
    for m in ob.data.materials:
        if not m or m.name in done or not m.node_tree: continue
        done.add(m.name)
        nt = m.node_tree; n, l = nt.nodes, nt.links
        out = next((x for x in n if x.type == 'OUTPUT_MATERIAL' and x.is_active_output), None)
        if not out or not out.inputs['Surface'].links: continue
        src = out.inputs['Surface'].links[0].from_socket
        tcx = n.new('ShaderNodeTexCoord'); tcx.object = xc
        ln = n.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
        mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.10; mr.inputs['From Max'].default_value = 0.14
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        v_ = n.new('ShaderNodeValue'); v_.name = "XRayFade"
        mu = n.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'
        trn = n.new('ShaderNodeBsdfTransparent'); trn.inputs['Color'].default_value = (0.7, 0.92, 1.0, 1)
        mxs = n.new('ShaderNodeMixShader')
        l.new(tcx.outputs['Object'], ln.inputs[0]); l.new(ln.outputs['Value'], mr.inputs['Value'])
        lg = n.new('ShaderNodeAttribute'); lg.attribute_name = "legmask"
        mu2 = n.new('ShaderNodeMath'); mu2.operation = 'MULTIPLY'
        l.new(mr.outputs['Result'], mu2.inputs[0]); l.new(lg.outputs['Fac'], mu2.inputs[1])
        if ob is not DB: mu2.inputs[1].default_value = 1.0; l.remove(mu2.inputs[1].links[0])
        l.new(mu2.outputs[0], mu.inputs[0]); l.new(v_.outputs[0], mu.inputs[1])
        l.new(mu.outputs[0], mxs.inputs['Fac']); l.new(src, mxs.inputs[1]); l.new(trn.outputs['BSDF'], mxs.inputs[2])
        l.new(mxs.outputs['Shader'], out.inputs['Surface'])
        for f, v in XK:
            v_.outputs[0].default_value = v; v_.outputs[0].keyframe_insert("default_value", frame=f)
# real calf muscles: right lower leg cut from "Female Body Muscular System - Anatomy Study" (Ruslan Gadzhiev, CC-BY), fitted inside her shin
import bmesh as _bm
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, "..", "assets", "objv", "muscles_f.glb"))
_new = [o for o in bpy.data.objects if o not in _before]
_meshes = [o for o in _new if o.type == 'MESH']
for o in _meshes:
    mw_ = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw_
for o in _new:
    if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
for o in bpy.data.objects: o.select_set(False)
for o in _meshes: o.select_set(True)
bpy.context.view_layer.objects.active = _meshes[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(_meshes) > 1: bpy.ops.object.join()
mus = bpy.context.active_object; mus.name = "XRay_CalfMuscles"
zs = [v.co.z for v in mus.data.vertices]; Z0, Z1 = min(zs), max(zs); HH = Z1 - Z0
KZ, AZ = Z0 + 0.285 * HH, Z0 + 0.045 * HH
bm_ = _bm.new(); bm_.from_mesh(mus.data)
_bm.ops.delete(bm_, geom=[v for v in bm_.verts if not (AZ <= v.co.z <= KZ and v.co.x < -0.15)], context='VERTS')
bm_.to_mesh(mus.data); bm_.free()
vs = mus.data.vertices
def _slice_c(z0, z1):
    sel = [v.co for v in vs if z0 <= v.co.z <= z1]
    return sum(sel, Vector()) / max(1, len(sel))
k_top = _slice_c(KZ - 0.02 * HH, KZ); a_bot = _slice_c(AZ, AZ + 0.02 * HH)
ev(1)
K_ = D.matrix_world @ D.data.bones["lowerleg01.R"].head_local; A_ = D.matrix_world @ D.data.bones["foot.R"].head_local
sc_ = (A_ - K_).length / (a_bot - k_top).length
Rm = (a_bot - k_top).normalized().rotation_difference((A_ - K_).normalized()).to_matrix().to_4x4()
mus.data.transform(Matrix.Translation(-k_top)); mus.data.transform(Matrix.Scale(sc_, 4)); mus.data.transform(Rm)
# radial shrink so the muscle stays inside her skin
axis = (A_ - K_).normalized()
for v in mus.data.vertices:
    along = axis * v.co.dot(axis); v.co = along + (v.co - along) * 0.86
mus.data.transform(Matrix.Translation(K_))
dec = mus.modifiers.new("Dec", 'DECIMATE'); dec.ratio = 0.5
for f_ in mus.data.polygons: f_.use_smooth = True
mus.data.materials.clear()
mm = bpy.data.materials.new("M_CalfMuscle"); mm.use_nodes = True
mn, ml = mm.node_tree.nodes, mm.node_tree.links
mp_ = mn["Principled BSDF"]; mp_.inputs['Roughness'].default_value = 0.28
mp_.inputs['Subsurface Weight'].default_value = 0.45; mp_.inputs['Subsurface Radius'].default_value = (0.9, 0.25, 0.15)
mp_.inputs['Coat Weight'].default_value = 0.35; mp_.inputs['Coat Roughness'].default_value = 0.2
mtc = mn.new('ShaderNodeTexCoord')
wv = mn.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 140; wv.inputs['Distortion'].default_value = 6
wv.inputs['Detail'].default_value = 4
nzm = mn.new('ShaderNodeTexNoise'); nzm.inputs['Scale'].default_value = 60
ml.new(mtc.outputs['Object'], wv.inputs['Vector']); ml.new(mtc.outputs['Object'], nzm.inputs['Vector'])
ramp = mn.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.62, 0.1, 0.12, 1); ramp.color_ramp.elements[1].color = (0.95, 0.38, 0.4, 1)
ml.new(wv.outputs['Fac'], ramp.inputs['Fac'])
# tendon (Achilles) toward the ankle: pale, glossy
geo = mn.new('ShaderNodeNewGeometry'); dz = mn.new('ShaderNodeVectorMath'); dz.operation = 'DOT_PRODUCT'
dz.inputs[1].default_value = tuple(axis)
ml.new(geo.outputs['Position'], dz.inputs[0])
tmr = mn.new('ShaderNodeMapRange'); tmr.inputs['From Min'].default_value = K_.dot(axis) + 0.27; tmr.inputs['From Max'].default_value = K_.dot(axis) + 0.33
ml.new(dz.outputs['Value'], tmr.inputs['Value'])
tmix = mn.new('ShaderNodeMix'); tmix.data_type = 'RGBA'; tmix.inputs['B'].default_value = (0.97, 0.92, 0.8, 1)
ml.new(tmr.outputs['Result'], tmix.inputs['Factor']); ml.new(ramp.outputs['Color'], tmix.inputs['A']); ml.new(tmix.outputs['Result'], mp_.inputs['Base Color'])
bmp = mn.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.6
add_ = mn.new('ShaderNodeMath'); add_.operation = 'ADD'; ml.new(wv.outputs['Fac'], add_.inputs[0]); ml.new(nzm.outputs['Fac'], add_.inputs[1])
ml.new(add_.outputs[0], bmp.inputs['Height']); ml.new(bmp.outputs['Normal'], mp_.inputs['Normal'])
mp_.inputs['Emission Color'].default_value = (1.0, 0.08, 0.04, 1)
# the red pulse rides the fibres (bands light up), keyed strength
emul = mn.new('ShaderNodeMath'); emul.operation = 'MULTIPLY'; ml.new(wv.outputs['Fac'], emul.inputs[0]); emul.name = "PulseMul"
ml.new(emul.outputs[0], mp_.inputs['Emission Strength'])
for f, v in ((1, 0.0), (360, 0.0), (372, 3.0), (384, 0.4), (396, 3.5), (408, 0.4), (420, 4.0), (436, 0.6), (448, 3.5), (465, 0.0)):
    emul.inputs[1].default_value = v; emul.inputs[1].keyframe_insert("default_value", frame=f)
# visible only inside the porthole sphere (never pokes through the skin elsewhere)
xtc = mn.new('ShaderNodeTexCoord'); xtc.object = xc
xln = mn.new('ShaderNodeVectorMath'); xln.operation = 'LENGTH'; ml.new(xtc.outputs['Object'], xln.inputs[0])
xmr = mn.new('ShaderNodeMapRange'); xmr.inputs['From Min'].default_value = 0.12; xmr.inputs['From Max'].default_value = 0.14
xmr.inputs['To Min'].default_value = 0.0; xmr.inputs['To Max'].default_value = 1.0; ml.new(xln.outputs['Value'], xmr.inputs['Value'])
xtr = mn.new('ShaderNodeBsdfTransparent'); xmx = mn.new('ShaderNodeMixShader')
mout = mn["Material Output"]
ml.new(xmr.outputs['Result'], xmx.inputs['Fac']); ml.new(mp_.outputs['BSDF'], xmx.inputs[1]); ml.new(xtr.outputs[0], xmx.inputs[2]); ml.new(xmx.outputs[0], mout.inputs['Surface'])
mus.data.materials.append(mm)
# ride the shin bone
mw_ = mus.matrix_world.copy(); ev(1)
mus.parent = D; mus.parent_type = 'BONE'; mus.parent_bone = "lowerleg01.R"
_bl = D.data.bones["lowerleg01.R"]
mus.matrix_parent_inverse = (D.matrix_world @ _bl.matrix_local @ Matrix.Translation(Vector((0, _bl.length, 0)))).inverted()
mus.location = (0, 0, 0); mus.rotation_euler = (0, 0, 0); mus.scale = (1, 1, 1)
for f, h in ((1, True), (345, False), (490, True)):
    mus.hide_render = h; mus.keyframe_insert("hide_render", frame=f)
print("CALF muscles", len(mus.data.vertices), "verts, scale", round(sc_, 4))

# ------------------------------------------------------------------ bubbles (Geometry Nodes: points rising from emitters, burst amount keyable)
def bubble_system(name, parent, bone, rate_keys, spread=0.06, rise=0.55, life=4.0, size=(0.004, 0.018)):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    me.from_pydata([(0, 0, 0)], [], [])
    ng = bpy.data.node_groups.new(name + "_GN", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    nn, nl = ng.nodes, ng.links
    gi = nn.new('NodeGroupInput'); go = nn.new('NodeGroupOutput')
    # a vertical line of N candidate points, each a bubble with its own seed; visible if its "slot" is active
    N = 160
    line = nn.new('GeometryNodeMeshLine'); line.inputs['Count'].default_value = N
    line.inputs['Offset'].default_value = (0, 0, 0)
    idx = nn.new('GeometryNodeInputIndex')
    tm = nn.new('GeometryNodeInputSceneTime')
    # phase = fract(time / life + rand(idx))
    rnd = nn.new('FunctionNodeRandomValue'); rnd.data_type = 'FLOAT'; nl.new(idx.outputs[0], rnd.inputs['ID'])
    div = nn.new('ShaderNodeMath'); div.operation = 'DIVIDE'; nl.new(tm.outputs['Seconds'], div.inputs[0]); div.inputs[1].default_value = life
    add = nn.new('ShaderNodeMath'); add.operation = 'ADD'; nl.new(div.outputs[0], add.inputs[0]); nl.new(rnd.outputs[0], add.inputs[1])
    frc = nn.new('ShaderNodeMath'); frc.operation = 'FRACT'; nl.new(add.outputs[0], frc.inputs[0])
    # position: jitter + rise*life*phase + wobble
    rv = nn.new('FunctionNodeRandomValue'); rv.data_type = 'FLOAT_VECTOR'; rv.inputs['Min'].default_value = (-spread, -spread, 0); rv.inputs['Max'].default_value = (spread, spread, 0)
    nl.new(idx.outputs[0], rv.inputs['ID'])
    up = nn.new('ShaderNodeMath'); up.operation = 'MULTIPLY'; nl.new(frc.outputs[0], up.inputs[0]); up.inputs[1].default_value = rise * life
    wob = nn.new('ShaderNodeMath'); wob.operation = 'SINE'
    wm = nn.new('ShaderNodeMath'); wm.operation = 'MULTIPLY'; nl.new(up.outputs[0], wm.inputs[0]); wm.inputs[1].default_value = 9.0
    nl.new(wm.outputs[0], wob.inputs[0])
    ws = nn.new('ShaderNodeMath'); ws.operation = 'MULTIPLY'; nl.new(wob.outputs[0], ws.inputs[0]); ws.inputs[1].default_value = 0.02
    cmb = nn.new('ShaderNodeCombineXYZ'); nl.new(ws.outputs[0], cmb.inputs['X']); nl.new(up.outputs[0], cmb.inputs['Z'])
    vad = nn.new('ShaderNodeVectorMath'); vad.operation = 'ADD'; nl.new(rv.outputs[0], vad.inputs[0]); nl.new(cmb.outputs[0], vad.inputs[1])
    sp = nn.new('GeometryNodeSetPosition'); nl.new(line.outputs[0], sp.inputs['Geometry']); nl.new(vad.outputs[0], sp.inputs['Position'])
    # keep fraction 'Rate' of the slots (rate keyed 0..1 via the modifier input)
    rate = nn.new('ShaderNodeValue'); rate.name = "Rate"
    rsel = nn.new('FunctionNodeRandomValue'); rsel.data_type = 'FLOAT'; rsel.inputs['Seed'].default_value = 7; nl.new(idx.outputs[0], rsel.inputs['ID'])
    gt = nn.new('FunctionNodeCompare'); gt.data_type = 'FLOAT'; gt.operation = 'GREATER_THAN'
    nl.new(rsel.outputs[0], gt.inputs['A']); nl.new(rate.outputs[0], gt.inputs['B'])
    dele = nn.new('GeometryNodeDeleteGeometry'); nl.new(sp.outputs[0], dele.inputs['Geometry']); nl.new(gt.outputs[0], dele.inputs['Selection'])
    ico = nn.new('GeometryNodeMeshIcoSphere'); ico.inputs['Radius'].default_value = 1.0; ico.inputs['Subdivisions'].default_value = 2
    inst = nn.new('GeometryNodeInstanceOnPoints'); nl.new(dele.outputs[0], inst.inputs['Points']); nl.new(ico.outputs['Mesh'], inst.inputs['Instance'])
    rs = nn.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'; rs.inputs["Min"].default_value = size[0]; rs.inputs["Max"].default_value = size[1]
    nl.new(idx.outputs[0], rs.inputs['ID']); nl.new(rs.outputs[0], inst.inputs['Scale'])
    smat = nn.new('GeometryNodeSetMaterial'); smat.inputs['Material'].default_value = BUBM
    nl.new(inst.outputs[0], smat.inputs['Geometry'])
    jn = nn.new('GeometryNodeRealizeInstances'); nl.new(smat.outputs[0], jn.inputs['Geometry'])
    nl.new(jn.outputs[0], go.inputs[0])
    md = o.modifiers.new("Bubbles", 'NODES'); md.node_group = ng
    for f, v in rate_keys:
        rate.outputs[0].default_value = v; rate.outputs[0].keyframe_insert("default_value", frame=f)
    if parent is not None:
        o.parent = parent
        if bone:
            o.parent_type = 'BONE'; o.parent_bone = bone
            pb = parent.pose.bones[bone]
            o.matrix_parent_inverse = Matrix.Identity(4); o.location = (0, -pb.length, 0)
    return o
BUBM = bpy.data.materials.new("M_Bubble"); BUBM.use_nodes = True
bpp = BUBM.node_tree.nodes["Principled BSDF"]; bpp.inputs['Base Color'].default_value = (1, 1, 1, 1); bpp.inputs['Roughness'].default_value = 0.0
bpp.inputs['Transmission Weight'].default_value = 1.0; bpp.inputs['IOR'].default_value = 0.75
# mouth bubbles: steady trickle, panic bursts in beat 4, last bubbles in beat 5, nothing on "run out of breath"
mouth = bubble_system("Bubbles_Mouth", D, "jaw", [(1, 0.0), (70, 0.0), (80, 0.6), (130, 0.15), (520, 0.12), (540, 0.9), (575, 0.3), (600, 0.9), (640, 0.2),
                                                  (700, 0.55), (740, 0.25), (770, 0.05), (1370, 0.04), (1700, 0.08), (1760, 0.0), (END, 0.0)], spread=0.03, rise=0.6, life=3.0)
# entry burst + trail behind her (big column) and floor vents near the rocks (constant), whale blowhole trickle
trail = bubble_system("Bubbles_Entry", None, None, [(1, 0.0), (74, 0.0), (80, 1.0), (140, 0.25), (200, 0.0), (END, 0.0)], spread=0.35, rise=0.9, life=3.0, size=(0.006, 0.03))
trail.location = (X0, -3.75, 4.2)
for i, (x, y) in enumerate(((-4.6, 3.3), (4.4, 3.0), (-4.9, -2.4), (5.0, -3.0))):
    vb = bubble_system("Bubbles_Vent_%d" % i, None, None, [(1, 0.7)], spread=0.12, rise=0.7, life=8.5, size=(0.004, 0.02)); vb.location = (x, y, 0.3)
splash = bubble_system("Bubbles_Ascent", None, None, [(1, 0.0), (1460, 0.0), (1480, 0.8), (1880, 0.8), (1900, 0.0)], spread=0.5, rise=1.2, life=2.5, size=(0.006, 0.03))
splash.parent = BR; splash.location = (0, 1.2, 0)

# ------------------------------------------------------------------ surface break: ballistic droplet burst (GN), keyed time
ev(1910); hp = dv("head", 1910)
def droplets(name, centre, f0, f1, n=600, speed=(1.2, 3.4), spread=0.35):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    me.from_pydata([(0, 0, 0)], [], []); o.location = centre
    ng = bpy.data.node_groups.new(name + "_GN", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    nn, nl = ng.nodes, ng.links
    go = nn.new('NodeGroupOutput'); nn.new('NodeGroupInput')
    line = nn.new('GeometryNodeMeshLine'); line.inputs['Count'].default_value = n
    idx = nn.new('GeometryNodeInputIndex')
    T = nn.new('ShaderNodeValue'); T.name = "T"
    dirv = nn.new('FunctionNodeRandomValue'); dirv.data_type = 'FLOAT_VECTOR'; dirv.inputs['Min'].default_value = (-1, -1, 0.0); dirv.inputs['Max'].default_value = (1, 1, 0.0)
    nl.new(idx.outputs[0], dirv.inputs['ID'])
    up = nn.new('FunctionNodeRandomValue'); up.data_type = 'FLOAT'; up.inputs['Min'].default_value = speed[0]; up.inputs['Max'].default_value = speed[1]; up.inputs['Seed'].default_value = 3
    nl.new(idx.outputs[0], up.inputs['ID'])
    hs = nn.new('ShaderNodeVectorMath'); hs.operation = 'SCALE'; hs.inputs['Scale'].default_value = 1.4; nl.new(dirv.outputs[0], hs.inputs[0])
    vz = nn.new('ShaderNodeCombineXYZ'); nl.new(up.outputs[0], vz.inputs['Z'])
    vel = nn.new('ShaderNodeVectorMath'); vel.operation = 'ADD'; nl.new(hs.outputs[0], vel.inputs[0]); nl.new(vz.outputs[0], vel.inputs[1])
    vt = nn.new('ShaderNodeVectorMath'); vt.operation = 'SCALE'; nl.new(vel.outputs[0], vt.inputs[0]); nl.new(T.outputs[0], vt.inputs['Scale'])
    t2 = nn.new('ShaderNodeMath'); t2.operation = 'POWER'; nl.new(T.outputs[0], t2.inputs[0]); t2.inputs[1].default_value = 2
    gz = nn.new('ShaderNodeMath'); gz.operation = 'MULTIPLY'; nl.new(t2.outputs[0], gz.inputs[0]); gz.inputs[1].default_value = -4.9
    gv = nn.new('ShaderNodeCombineXYZ'); nl.new(gz.outputs[0], gv.inputs['Z'])
    st = nn.new('ShaderNodeVectorMath'); st.operation = 'SCALE'; st.inputs['Scale'].default_value = spread; nl.new(dirv.outputs[0], st.inputs[0])
    p1 = nn.new('ShaderNodeVectorMath'); p1.operation = 'ADD'; nl.new(vt.outputs[0], p1.inputs[0]); nl.new(gv.outputs[0], p1.inputs[1])
    p2 = nn.new('ShaderNodeVectorMath'); p2.operation = 'ADD'; nl.new(p1.outputs[0], p2.inputs[0]); nl.new(st.outputs[0], p2.inputs[1])
    sp = nn.new('GeometryNodeSetPosition'); nl.new(line.outputs[0], sp.inputs['Geometry']); nl.new(p2.outputs[0], sp.inputs['Position'])
    sep = nn.new('ShaderNodeSeparateXYZ'); nl.new(p2.outputs[0], sep.inputs['Vector'])
    below = nn.new('FunctionNodeCompare'); below.data_type = 'FLOAT'; below.operation = 'LESS_THAN'; nl.new(sep.outputs['Z'], below.inputs['A']); below.inputs['B'].default_value = -0.02
    dl = nn.new('GeometryNodeDeleteGeometry'); nl.new(sp.outputs[0], dl.inputs['Geometry']); nl.new(below.outputs[0], dl.inputs['Selection'])
    ico = nn.new('GeometryNodeMeshIcoSphere'); ico.inputs['Radius'].default_value = 1.0; ico.inputs['Subdivisions'].default_value = 1
    inst = nn.new('GeometryNodeInstanceOnPoints'); nl.new(dl.outputs[0], inst.inputs['Points']); nl.new(ico.outputs['Mesh'], inst.inputs['Instance'])
    rs = nn.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'; rs.inputs['Min'].default_value = 0.006; rs.inputs['Max'].default_value = 0.022
    nl.new(idx.outputs[0], rs.inputs['ID']); nl.new(rs.outputs[0], inst.inputs['Scale'])
    sm = nn.new('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = DROPM; nl.new(inst.outputs[0], sm.inputs['Geometry'])
    rl = nn.new('GeometryNodeRealizeInstances'); nl.new(sm.outputs[0], rl.inputs['Geometry']); nl.new(rl.outputs[0], go.inputs[0])
    o.modifiers.new("Drops", 'NODES').node_group = ng
    for f_, v_ in ((f0, 0.0), (f1, (f1 - f0) / 60.0)):
        T.outputs[0].default_value = v_; T.outputs[0].keyframe_insert("default_value", frame=f_)
    linear(ng)
    for f_, h in ((1, True), (f0, False), (f1, True)):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f_)
    return o
DROPM = bpy.data.materials.new("M_Droplet"); DROPM.use_nodes = True
dp = DROPM.node_tree.nodes["Principled BSDF"]; dp.inputs['Base Color'].default_value = (0.95, 0.98, 1.0, 1); dp.inputs['Roughness'].default_value = 0.05
dp.inputs['Transmission Weight'].default_value = 0.85; dp.inputs['IOR'].default_value = 1.33
droplets("Splash_Break", Vector((hp.x, hp.y, WATER_Z)), 1903, 1985)
droplets("Splash_Spout", Vector((hp.x - 1.4, hp.y + 1.9, WATER_Z)), 2120, 2190, n=300, speed=(2.5, 4.0), spread=0.08)
# ------------------------------------------------------------------ suspended particles in the water (static random cloud drifting slowly)
pme = bpy.data.meshes.new("Water_Particulates"); pobj = bpy.data.objects.new("Water_Particulates", pme); sc.collection.objects.link(pobj)
pts = [(random.uniform(-5.8, 5.8), random.uniform(-4.9, 4.9), random.uniform(0.05, 5.9)) for _ in range(4000)]
pme.from_pydata(pts, [], [])
ng = bpy.data.node_groups.new("Particulates_GN", 'GeometryNodeTree')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
nn, nl = ng.nodes, ng.links
gi = nn.new('NodeGroupInput'); go = nn.new('NodeGroupOutput')
tm = nn.new('GeometryNodeInputSceneTime'); pos = nn.new('GeometryNodeInputPosition')
nz = nn.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 0.4
nl.new(pos.outputs[0], nz.inputs['Vector'])
tmul = nn.new('ShaderNodeMath'); tmul.operation = 'MULTIPLY'; tmul.inputs[1].default_value = 0.05; nl.new(tm.outputs['Seconds'], tmul.inputs[0]); nl.new(tmul.outputs[0], nz.inputs['W'])
sub = nn.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0.5); nl.new(nz.outputs['Color'], sub.inputs[0])
scl = nn.new('ShaderNodeVectorMath'); scl.operation = 'SCALE'; scl.inputs['Scale'].default_value = 0.5; nl.new(sub.outputs[0], scl.inputs[0])
sp = nn.new('GeometryNodeSetPosition'); nl.new(gi.outputs[0], sp.inputs['Geometry']); nl.new(scl.outputs[0], sp.inputs['Offset'])
ico = nn.new('GeometryNodeMeshIcoSphere'); ico.inputs['Radius'].default_value = 1.0; ico.inputs['Subdivisions'].default_value = 1
inst = nn.new('GeometryNodeInstanceOnPoints'); nl.new(sp.outputs[0], inst.inputs['Points']); nl.new(ico.outputs['Mesh'], inst.inputs['Instance'])
rs = nn.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'; rs.inputs['Min'].default_value = 0.0015; rs.inputs['Max'].default_value = 0.005
nl.new(rs.outputs[0], inst.inputs['Scale'])
PM = bpy.data.materials.new("M_Particulate"); PM.use_nodes = True
ppb = PM.node_tree.nodes["Principled BSDF"]; ppb.inputs['Base Color'].default_value = (0.85, 0.95, 1.0, 1); ppb.inputs['Roughness'].default_value = 0.6
ppb.inputs['Alpha'].default_value = 0.6; ppb.inputs['Emission Color'].default_value = (0.6, 0.85, 1.0, 1); ppb.inputs['Emission Strength'].default_value = 0.3
smat = nn.new('GeometryNodeSetMaterial'); smat.inputs['Material'].default_value = PM; nl.new(inst.outputs[0], smat.inputs['Geometry'])
rl = nn.new('GeometryNodeRealizeInstances'); nl.new(smat.outputs[0], rl.inputs['Geometry']); nl.new(rl.outputs[0], go.inputs[0])
pobj.modifiers.new("Particles", 'NODES').node_group = ng

# ------------------------------------------------------------------ hair drifts underwater (noise displace, weighted away from the scalp)
hair = next(o for o in D.children if o.name.endswith("ponytail01"))
ev(1)
hc = D.matrix_world @ D.data.bones["head"].head_local + Vector((0, 0.02, 0.1))
hg = hair.vertex_groups.new(name="drift")
for v in hair.data.vertices:
    w_ = max(0.0, min(1.0, ((hair.matrix_world @ v.co) - hc).length / 0.18 - 0.4))
    if w_ > 0: hg.add([v.index], w_, 'REPLACE')
tx = bpy.data.textures.new("HairDrift", 'CLOUDS'); tx.noise_scale = 0.12
drv = bpy.data.objects.new("HairDrift_Flow", None); sc.collection.objects.link(drv)
for f_, p_ in ((1, (0, 0, 0)), (END, (0.6, 0.9, 2.2))):
    drv.location = p_; drv.keyframe_insert("location", frame=f_)
linear(drv)
for axis, st in (('X', 0.035), ('Y', 0.03), ('Z', 0.02)):
    dm = hair.modifiers.new("Drift" + axis, 'DISPLACE'); dm.texture = tx; dm.direction = axis; dm.strength = st; dm.mid_level = 0.5
    dm.texture_coords = 'OBJECT'; dm.texture_coords_object = drv; dm.vertex_group = "drift"
# above water (deck, last beat) the hair hangs: fade the drift
for o_md in [m for m in hair.modifiers if m.name.startswith("Drift")]:
    st0 = o_md.strength
    for f_, v_ in ((1, 0.0), (76, 0.0), (90, st0), (1900, st0), (1930, 0.004)):
        o_md.strength = v_; o_md.keyframe_insert("strength", frame=f_)

# helpers never render
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("FX_CAM_DONE", OUT)
