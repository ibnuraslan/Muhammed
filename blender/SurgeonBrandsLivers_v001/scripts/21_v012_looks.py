"""v012 looks pass (client rejection, Nov 21: items 1, 10, 12, 13, 16, 20, 31; RECURRING_FAULTS 6, 7).
blender -b in.blend --python 21_v012_looks.py -- <out.blend>

- Soft cloth bouffant caps (gathered edge, wrinkles, fabric sheen) that sit above the hairline: real hair shows at the
  forehead, temples and nape. Every OR person now has hair.
- The woman (Patient): real clothes at home - a mustard knit top and blue jeans (two garments, seam at the waist,
  slightly loose) - and a ponytail with the face clear. Same hair in every scene.
- The clerk (PanelB): hair tied back, nothing over the eyes.
- Surgeon 2: loose two-piece scrubs (top + darker trousers), soft cap.
- Eyes: batch-2 eye fix (cornea as straight transparency) + a camera-only catchlight."""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
from bl_ext.user_default.mpfb.services.humanservice import HumanService
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v12lib as VL
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
V = lambda *a: Vector(a)
MP = "/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data"

def copy_vis(src, dst):
    """dst gets src's hide_render keys (or its static state)"""
    VL.clear_keys(dst, ("hide_render",))
    fc = [f for f in VL.fcurves(src) if f.data_path == "hide_render"]
    if not fc:
        dst.hide_render = src.hide_render; return
    for kp in fc[0].keyframe_points:
        dst.hide_render = bool(kp.co.y); dst.keyframe_insert("hide_render", frame=int(kp.co.x))
    VL.constant(dst, ("hide_render",))

def add_asset(rig_name, rel, kind):
    body = bpy.data.objects[rig_name + ".body"]
    ob = HumanService.add_mhclo_asset(os.path.join(MP, rel), body, asset_type=kind, subdiv_levels=1, material_type="MAKESKIN")
    copy_vis(body, ob)
    print("ADDED", ob.name, "to", rig_name)
    return ob

def remove(name):
    o = bpy.data.objects.get(name)
    if o: bpy.data.objects.remove(o, do_unlink=True)

def fabric(name, rgb, scale=60.0, rough=0.8, sheen=0.4, bump=0.25):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = rgb + (1,); b.inputs["Roughness"].default_value = rough
    b.inputs["Sheen Weight"].default_value = sheen
    tc = N.new("ShaderNodeTexCoord")
    w = N.new("ShaderNodeTexWave"); w.inputs["Scale"].default_value = scale; w.inputs["Distortion"].default_value = 2.0
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 3.0
    L.new(tc.outputs["Generated"], w.inputs["Vector"]); L.new(tc.outputs["Generated"], nz.inputs["Vector"])
    mx = N.new("ShaderNodeMath"); mx.operation = 'ADD'; L.new(w.outputs["Fac"], mx.inputs[0]); L.new(nz.outputs["Fac"], mx.inputs[1])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.004
    L.new(mx.outputs[0], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    # soft colour variation (folds catch darker tone)
    cr = N.new("ShaderNodeMapRange"); L.new(nz.outputs["Fac"], cr.inputs[0]); cr.inputs[3].default_value = 0.8; cr.inputs[4].default_value = 1.1
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1.0
    mul.inputs[6].default_value = rgb + (1,)
    cc = N.new("ShaderNodeCombineColor"); [L.new(cr.outputs[0], cc.inputs[i]) for i in range(3)]
    L.new(cc.outputs[0], mul.inputs[7]); L.new(mul.outputs[2], b.inputs["Base Color"])
    return m

def two_piece(ob, rig_name, top, bottom, loose=0.006):
    """faces above the waist get `top`, below get `bottom` (a real seam); pushed out a little so it hangs loose"""
    r = bpy.data.objects[rig_name]
    wz = (r.data.bones["spine05"].head_local.z + r.data.bones["spine04"].head_local.z) / 2 - 0.02
    ob.data.materials.clear(); ob.data.materials.append(top); ob.data.materials.append(bottom)
    for p in ob.data.polygons: p.material_index = 0 if p.center.z > wz else 1
    if loose > 0:
        d = ob.modifiers.new("Loose", 'DISPLACE'); d.strength = loose; d.mid_level = 0.0
        ob.modifiers.move(ob.modifiers.find(d.name), ob.modifiers.find("Armature") + 1)
        sm = ob.modifiers.new("LooseSmooth", 'CORRECTIVE_SMOOTH'); sm.factor = 0.5; sm.iterations = 4
        ob.modifiers.move(ob.modifiers.find(sm.name), ob.modifiers.find(d.name) + 1)

def body_mask_for(rig_name, clothes_ob, like=None):
    """mask the body under new clothes with the Delete.<name> group the asset added (keyed like `like` mask)"""
    body = bpy.data.objects[rig_name + ".body"]
    gname = "Delete." + clothes_ob.name.split(".", 1)[1]
    if gname not in body.vertex_groups: print("no delete group", gname); return
    m = body.modifiers.get(gname) or body.modifiers.new(gname, 'MASK'); m.vertex_group = gname; m.invert_vertex_group = True
    if like:
        for fc in VL.fcurves(body):
            if fc.data_path == 'modifiers["%s"].show_render' % like:
                for kp in fc.keyframe_points:
                    m.show_render = bool(kp.co.y); body.keyframe_insert('modifiers["%s"].show_render' % gname, frame=int(kp.co.x))
        VL.constant(body)

# ------------------------------------------------------------------ woman: real clothes + ponytail
old_home = bpy.data.objects["Patient.female_casualsuit02"]
remove("Patient.bob02")
hair = add_asset("Patient", "hair/ponytail01/ponytail01.mhclo", "Hair")
suit = add_asset("Patient", "clothes/female_casualsuit01/female_casualsuit01.mhclo", "Clothes")
copy_vis(old_home, suit)
two_piece(suit, "Patient", fabric("WomanTop", (0.62, 0.42, 0.07), 90), fabric("WomanJeans", (0.08, 0.14, 0.30), 140, 0.7, 0.1, 0.35), 0.007)
body_mask_for("Patient", suit, like="Delete.female_casualsuit02")
remove("Patient.female_casualsuit02")
VL.clear_keys(bpy.data.objects["Patient.body"], ('modifiers["Delete.female_casualsuit02"]',))
m = bpy.data.objects["Patient.body"].modifiers.get("Delete.female_casualsuit02")
if m: bpy.data.objects["Patient.body"].modifiers.remove(m)

# her ponytail lies under her head on the table: the tail (below the pad top) is masked while she is on the table
sc.frame_set(200); bpy.context.view_layer.update(); dgp = bpy.context.evaluated_depsgraph_get()
sd = [m for m in hair.modifiers if m.type == 'SUBSURF']
for m in sd: m.show_viewport = False
bpy.context.view_layer.update(); dgp = bpy.context.evaluated_depsgraph_get(); eh = hair.evaluated_get(dgp); hm = eh.to_mesh()
low = [v.index for v in hm.vertices if (hair.matrix_world @ v.co).z < 0.957] if len(hm.vertices) == len(hair.data.vertices) else []
eh.to_mesh_clear()
for m in sd: m.show_viewport = True
g = hair.vertex_groups.new(name="OnTable"); g.add(low, 1.0, 'REPLACE')
mt = hair.modifiers.new("OnTable", 'MASK'); mt.vertex_group = "OnTable"; mt.invert_vertex_group = True
hair.modifiers.move(hair.modifiers.find("OnTable"), 0)
for f, on in ((0, True), (601, False), (1000, True), (1263, False)):
    mt.show_render = on; hair.keyframe_insert('modifiers["OnTable"].show_render', frame=f)
VL.constant(hair)
print("PONYTAIL masked on the table", len(low))

# ------------------------------------------------------------------ clerk: hair tied back (ponytail), face clear
remove("PanelB.bob01")
add_asset("PanelB", "hair/ponytail01/ponytail01.mhclo", "Hair")

# ------------------------------------------------------------------ OR staff: hair under the caps
add_asset("Surgeon2", "hair/ponytail01/ponytail01.mhclo", "Hair")
add_asset("Nurse", "hair/short04/short04.mhclo", "Hair")
add_asset("Anaesth", "hair/short01/short01.mhclo", "Hair")
remove("Surgeon1.short02")                                      # v013: read as helmet hair
add_asset("Surgeon1", "hair/short04/short04.mhclo", "Hair")

# ------------------------------------------------------------------ v013: real scrubs - a top and trousers built from each body
# (the MPFB suits read as one-piece onesies). Each garment is the person's own body surface, cut to the garment's shape
# (short sleeves, V-neck, top hem hanging over the trouser waist, trousers to the ankle), pushed out so it hangs loose,
# with folds; it deforms with the same skin weights.
import bmesh as _bm
DEFB = None
def dominant(v, idx, bones):
    best = (0.0, None)
    for g in v.groups:
        n = idx.get(g.group, "")
        if g.weight > best[0] and n in bones: best = (g.weight, n)
    return best[1]
def scrub_piece(rig_name, kind, mat, off, hide_src):
    r = bpy.data.objects[rig_name]; body = bpy.data.objects[rig_name + ".body"]; BN = r.data.bones
    ob = body.copy(); ob.data = body.data.copy(); ob.name = rig_name + ".Scrub" + kind
    bpy.data.collections["Collection"].objects.link(ob)
    for m in list(ob.modifiers): ob.modifiers.remove(m)
    if ob.animation_data: ob.animation_data_clear()
    if ob.data.shape_keys:
        for o in bpy.context.selected_objects: o.select_set(False)
        bpy.context.view_layer.objects.active = ob; ob.select_set(True)
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    idx = {g.index: g.name for g in ob.vertex_groups}; BONES = set(r.data.bones.keys())
    bodyg = ob.vertex_groups.get("body")
    waist = (BN["spine05"].head_local.z + BN["spine04"].head_local.z) / 2
    neck = BN["neck01"].head_local; ua2 = {s: (BN["upperarm02." + s].head_local, BN["upperarm02." + s].tail_local) for s in "LR"}
    ank = {s: BN["foot." + s].head_local.z for s in "LR"}
    keep = set()
    for v in ob.data.vertices:
        if bodyg is not None and not any(g.group == bodyg.index and g.weight > 0.5 for g in v.groups): continue
        d = dominant(v, idx, BONES)
        if d is None: continue
        c = v.co
        if kind == "Top":
            if d.startswith(("spine", "clavicle", "shoulder", "breast", "pectoral", "upperarm01", "pelvis", "neck01")) or d.startswith("upperarm02"):
                if c.z < waist - 0.075: continue
                if d.startswith("upperarm02"):
                    s = d[-1]; a, b = ua2[s]; t = (c - a).dot(b - a) / max((b - a).length_squared, 1e-6)
                    if t > 0.35: continue
                if d.startswith("neck01") or c.z > neck.z + 0.005: continue
                vdepth = 0.11 - 1.3 * abs(c.x)           # V-neck at the front
                if c.y < neck.y - 0.02 and c.z > neck.z - vdepth: continue
                keep.add(v.index)
        else:
            if d.startswith(("pelvis", "upperleg", "lowerleg", "spine05", "spine04", "root")):
                if c.z > waist + 0.02: continue
                if c.z < min(ank.values()) + 0.03: continue
                keep.add(v.index)
    bm = _bm.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    dl = bm.verts.layers.deform.verify()
    def dominant_bm(v):
        best = (0.0, None)
        for gi, w in v[dl].items():
            n = idx.get(gi, "")
            if w > best[0] and n in BONES: best = (w, n)
        return best[1]
    _bm.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
    # v014: loose fit. The top hangs straight down from the chest (boxy, no waist or bust read); trouser legs are
    # loose tubes round each leg's axis. Rest-pose (upright) coordinates; weights unchanged, so it still deforms.
    spz = {n: BN[n].head_local for n in ("spine05", "spine04", "spine03", "spine02", "spine01") if n in BN}
    zs_ = sorted((p_.z, p_.y) for p_ in spz.values())
    def cy_at(z):
        if z <= zs_[0][0]: return zs_[0][1]
        for (z0, y0), (z1, y1) in zip(zs_, zs_[1:]):
            if z0 <= z <= z1: return y0 + (y1 - y0) * (z - z0) / max(z1 - z0, 1e-6)
        return zs_[-1][1]
    if kind == "Top":
        tor = [v for v in bm.verts if (dominant_bm(v) or "").startswith(("spine", "pelvis", "breast", "pectoral"))]
        z_lo, z_hi = BN["spine02"].head_local.z - 0.02, BN["spine01"].head_local.z + 0.03
        front_ = [v for v in tor if z_lo < v.co.z < z_hi and abs(v.co.x) < 0.12]
        zc = min(front_, key=lambda v: v.co.y - cy_at(v.co.z)).co.z if front_ else BN["spine02"].head_local.z   # bust / chest apex
        band = [v for v in tor if abs(v.co.z - zc) < 0.05]
        if band:
            a_ = max(abs(v.co.x) for v in band) + 0.01
            bf = max(cy_at(v.co.z) - v.co.y for v in band) + 0.01; bb = max(v.co.y - cy_at(v.co.z) for v in band) + 0.01
            for v in tor:
                front_up = (v.co.y - cy_at(v.co.z)) < 0 and v.co.z < zc + 0.11
                if v.co.z >= zc and not front_up: continue
                t = min(1.0, (zc - v.co.z) / 0.06) if v.co.z < zc else min(1.0, max(0.0, 1.0 - (v.co.z - zc - 0.05) / 0.06))
                c_ = cy_at(v.co.z); dx, dy = v.co.x, v.co.y - c_
                b_ = bf if dy < 0 else bb
                rn = math.sqrt((dx / a_) ** 2 + (dy / b_) ** 2)
                if rn < 1.0 and rn > 1e-4:
                    k_ = 1.0 + (1.0 / rn - 1.0) * t
                    v.co.x = dx * k_; v.co.y = c_ + dy * k_
    else:
        zh = (BN["upperleg01.L"].head_local.z + BN["upperleg01.R"].head_local.z) / 2
        seat = [v for v in bm.verts if (dominant_bm(v) or "").startswith(("pelvis", "spine05", "spine04", "root", "upperleg01"))]
        hb = [v for v in seat if abs(v.co.z - zh) < 0.05]
        if hb:
            ah = max(abs(v.co.x) for v in hb) + 0.015
            bfh = max(cy_at(v.co.z) - v.co.y for v in hb) + 0.015; bbh = max(v.co.y - cy_at(v.co.z) for v in hb) + 0.015
            for v in seat:
                c_ = cy_at(v.co.z); dx, dy = v.co.x, v.co.y - c_
                if abs(dx) < 0.07 and v.co.z < zh - 0.03: continue                 # leave the inner leg / crotch to the leg tubes
                b_ = bfh if dy < 0 else bbh
                rn = math.sqrt((dx / ah) ** 2 + (dy / b_) ** 2)
                if 1e-4 < rn < 1.0: v.co.x = dx / rn; v.co.y = c_ + dy / rn
        for v in bm.verts:
            d_ = dominant_bm(v) or ""
            if not d_.startswith(("upperleg", "lowerleg")): continue
            sd = d_[-1]
            a0 = BN["upperleg01." + sd].head_local; a1 = BN["foot." + sd].head_local
            ax = (a1 - a0); L_ = ax.length; ax = ax / L_
            t = max(0.0, min(1.0, (v.co - a0).dot(ax) / L_)); pa = a0 + ax * (t * L_)
            rv = v.co - pa; rv = rv - ax * rv.dot(ax); rr_ = rv.length
            rmin = 0.088 - 0.022 * t
            if 1e-4 < rr_ < rmin: v.co = pa + rv * (rmin / rr_) + ax * (v.co - pa).dot(ax)
    for it in range(12):                                  # clean hems: smooth the open edges (no saw-tooth V-neck or sleeve)
        bnd = [v for v in bm.verts if v.is_boundary]
        newp = {}
        for v in bnd:
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2: newp[v] = v.co * 0.4 + (nb[0].co + nb[1].co) * 0.3
        for v, p_ in newp.items(): v.co = p_
    bm.normal_update()
    for v in bm.verts:
        k = off
        if kind == "Top" and v.co.z < waist + 0.02: k = off * 1.6        # hem hangs out over the trousers
        if kind == "Top" and v[dl] is not None:                          # no ballooned shoulders
            dn = dominant_bm(v)
            if dn and dn.startswith(("clavicle", "shoulder", "upperarm")): k = off * 0.6
        v.co = v.co + v.normal * k
    bm.to_mesh(ob.data); bm.free()
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for p in ob.data.polygons: p.material_index = 0; p.use_smooth = True
    am = ob.modifiers.new("Armature", 'ARMATURE'); am.object = r
    tx = bpy.data.textures.get("ScrubFolds") or bpy.data.textures.new("ScrubFolds", 'CLOUDS'); tx.noise_scale = 0.05
    dsp = ob.modifiers.new("Folds", 'DISPLACE'); dsp.texture = tx; dsp.strength = 0.007; dsp.texture_coords = 'LOCAL'
    ob.modifiers.move(ob.modifiers.find("Folds"), 0)
    so = ob.modifiers.new("Cloth", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0
    cs = ob.modifiers.new("Smooth", 'CORRECTIVE_SMOOTH'); cs.factor = 0.5; cs.iterations = 3
    sd = ob.modifiers.new("Subdivision", 'SUBSURF'); sd.levels = 0; sd.render_levels = 1
    copy_vis(hide_src, ob)
    print("SCRUB", ob.name, len(ob.data.vertices))
    return ob
SCRUBS = {"Surgeon1": ("male_casualsuit01", (0.10, 0.42, 0.40)), "Surgeon2": ("female_casualsuit01", (0.10, 0.20, 0.52)),
          "Nurse": ("male_casualsuit01", (0.12, 0.30, 0.50)), "Anaesth": ("male_casualsuit01", (0.18, 0.38, 0.20))}
for nm, (suit, rgb) in SCRUBS.items():
    old = bpy.data.objects[nm + "." + suit]
    scrub_piece(nm, "Top", fabric(nm + "ScrubTop", rgb, 70, 0.85, 0.35, 0.35), 0.012, old)
    scrub_piece(nm, "Trousers", fabric(nm + "ScrubTrousers", tuple(c * 0.72 for c in rgb), 70, 0.85, 0.35, 0.35), 0.016, old)
    old.hide_render = True; VL.clear_keys(old, ("hide_render",)); old.hide_render = True
    b = bpy.data.objects[nm + ".body"]; mk_ = b.modifiers.get("Delete." + suit)
    if mk_:
        VL.clear_keys(b, ('modifiers["Delete.%s"]' % suit,)); mk_.show_render = mk_.show_viewport = False
# gloves: violet nitrile, clearly a glove (not white pieces against the white pen)
for m in bpy.data.materials:
    if m.name.startswith("Glove_") and m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED' and abs(n.inputs["Coat Weight"].default_value - 0.25) < 1e-3:
                n.inputs["Base Color"].default_value = (0.22, 0.20, 0.62, 1); n.inputs["Roughness"].default_value = 0.45

def cap_fabric(name, rgb):
    """printed cotton: small light dots on the colour, weave bump, sheen"""
    m = fabric(name, rgb, 160, 0.9, 0.6, 0.45); nt = m.node_tree; N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]; src = b.inputs["Base Color"].links[0].from_socket
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 140
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["Object"], vo.inputs["Vector"])
    lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.16; L.new(vo.outputs["Distance"], lt.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(lt.outputs[0], mx.inputs[0]); L.new(src, mx.inputs[6])
    mx.inputs[7].default_value = tuple(min(1, c * 0.5 + 0.45) for c in rgb) + (1,)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    return m

# ------------------------------------------------------------------ soft cloth caps (replace the helmet shells)
CAPF = {"Surgeon1": 30, "Surgeon2": 960, "Nurse": 30, "Anaesth": 30}
CAPC = {"Surgeon1": (0.10, 0.42, 0.40), "Surgeon2": (0.42, 0.26, 0.55), "Nurse": (0.12, 0.30, 0.50), "Anaesth": (0.18, 0.38, 0.20)}
for nm, rgb in CAPC.items():
    cap = bpy.data.objects[nm + "_Cap"]; me0 = cap.data
    xs = [v.co.x for v in me0.vertices]; ys = [v.co.y for v in me0.vertices]; zs = [v.co.z for v in me0.vertices]
    rx = max(abs(x) for x in xs); cy = (max(ys) + min(ys)) / 2; ry = (max(ys) - min(ys)) / 2; rz = max(zs)
    rx += 0.008; ry += 0.010; rz += 0.006
    bm = bmesh.new(); NP, NT = 80, 24; rows = []
    top = bm.verts.new((0, cy, rz))
    for t_i in range(1, NT + 1):
        t = t_i / NT; row = []
        for p_i in range(NP):
            ph = 2 * math.pi * p_i / NP
            ze = -0.02375 + 0.0625 * math.cos(ph) - 0.01375 * math.cos(2 * ph)   # edge: above the forehead hairline, ear tops, nape
            z = rz - (rz - ze) * t
            rr = math.sqrt(max(0.0, 1 - (z / (rz + 0.01)) ** 2))
            puff = 1 + 0.035 * math.sin(math.pi * t) - 0.05 * t ** 8      # gathered elastic edge
            wob = 1 + 0.018 * math.sin(ph * 7 + t * 9) * math.sin(math.pi * t) + 0.012 * math.sin(ph * 26) * t ** 4   # folds + pleats at the band
            row.append(bm.verts.new((rx * rr * math.sin(ph) * puff * wob, cy - ry * rr * math.cos(ph) * puff * wob, z)))
        rows.append(row)
    for p_i in range(NP): bm.faces.new((top, rows[0][p_i], rows[0][(p_i + 1) % NP]))
    for t_i in range(NT - 1):
        for p_i in range(NP):
            bm.faces.new((rows[t_i][p_i], rows[t_i + 1][p_i], rows[t_i + 1][(p_i + 1) % NP], rows[t_i][(p_i + 1) % NP]))
    me = bpy.data.meshes.new(nm + "_SoftCap"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(cap_fabric(nm + "_CapFabric", rgb))
    cap.data = me
    for mo in list(cap.modifiers): cap.modifiers.remove(mo)
    # hair under the cap is masked out (only the hairline below the cap edge shows; nothing pokes through)
    hairs = [h for h in set(bpy.data.objects[nm].children) if h.type == 'MESH' and h.name.split(".")[-1].startswith(("short", "ponytail", "bob", "braid", "long", "afro"))]
    for h in hairs:
        sd = [m for m in h.modifiers if m.type == 'SUBSURF']
        for m in sd: m.show_viewport = False
        hv2 = h.hide_viewport; h.hide_viewport = False
        bpy.context.view_layer.update(); dg2 = bpy.context.evaluated_depsgraph_get(); eh = h.evaluated_get(dg2); hm = eh.to_mesh()
        Mi2 = cap.matrix_world.inverted() @ h.matrix_world; under = []
        if len(hm.vertices) == len(h.data.vertices):
            for v in hm.vertices:
                q = Mi2 @ v.co; ph = math.atan2(q.x, -(q.y - cy))
                ze = -0.02375 + 0.0625 * math.cos(ph) - 0.01375 * math.cos(2 * ph)
                if q.z > ze + 0.004: under.append(v.index)
        eh.to_mesh_clear(); h.hide_viewport = hv2
        for m in sd: m.show_viewport = True
        g = h.vertex_groups.new(name="UnderCap"); g.add(under, 1.0, 'REPLACE')
        mm = h.modifiers.new("UnderCap", 'MASK'); mm.vertex_group = "UnderCap"; mm.invert_vertex_group = True
        h.modifiers.move(h.modifiers.find("UnderCap"), 0)
        cfc = [fc for fc in VL.fcurves(cap) if fc.data_path == "hide_render"]      # only while the cap is worn
        if cfc:
            for kp in cfc[0].keyframe_points:
                mm.show_render = not bool(kp.co.y); h.keyframe_insert('modifiers["%s"].show_render' % mm.name, frame=int(kp.co.x))
            VL.constant(h)
        print("HAIR masked under cap", h.name, len(under), "of", len(h.data.vertices))
    tx = bpy.data.textures.new(nm + "_CapWrinkle", 'CLOUDS'); tx.noise_scale = 0.035
    d = cap.modifiers.new("Wrinkle", 'DISPLACE'); d.texture = tx; d.strength = 0.010; d.texture_coords = 'LOCAL'
    # hug the head: every vertex goes to the nearest head-surface point + 1.6 cm (hair room), sampled where visible
    body = bpy.data.objects[nm + ".body"]; hv = body.hide_viewport; body.hide_viewport = False
    sc.frame_set(CAPF[nm]); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); bme = ev.to_mesh(); Mi = cap.matrix_world.inverted() @ body.matrix_world
    pts = [Mi @ v.co for v in bme.vertices]
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromPolygons(pts, [tuple(p.vertices) for p in bme.polygons]); ev.to_mesh_clear(); body.hide_viewport = hv
    for v in me.vertices:
        loc, nrm, i, d = tree.find_nearest(v.co, 0.2)
        if loc is None: continue
        if v.index == 0: ph, t = 0.0, 0.0
        else: ph, t = 2 * math.pi * ((v.index - 1) % NP) / NP, ((v.index - 1) // NP + 1) / NT
        k = 0.015 + 0.006 * max(0.0, v.co.z / max(rz, 1e-3))                    # fuller on top (bouffant)
        k += 0.013 * max(0.0, math.sin(ph * 7 + 3.0 * t)) * math.sin(math.pi * min(1.0, t * 1.1)) + 0.005 * math.sin(ph * 17) * t   # soft folds from the crown
        k += 0.003 * math.sin(ph * 31) * t ** 6                                  # gathered elastic band
        dv = v.co - loc
        v.co = loc + (dv.normalized() if dv.length > 1e-5 else nrm) * k
    # hair under the cap is masked out (only the hairline below the cap edge shows; nothing pokes through)
    hairs = [h for h in set(bpy.data.objects[nm].children) if h.type == 'MESH' and h.name.split(".")[-1].startswith(("short", "ponytail", "bob", "braid", "long", "afro"))]
    for h in hairs:
        sd = [m for m in h.modifiers if m.type == 'SUBSURF']
        for m in sd: m.show_viewport = False
        hv2 = h.hide_viewport; h.hide_viewport = False
        bpy.context.view_layer.update(); dg2 = bpy.context.evaluated_depsgraph_get(); eh = h.evaluated_get(dg2); hm = eh.to_mesh()
        Mi2 = cap.matrix_world.inverted() @ h.matrix_world; under = []
        if len(hm.vertices) == len(h.data.vertices):
            for v in hm.vertices:
                q = Mi2 @ v.co; ph = math.atan2(q.x, -(q.y - cy))
                ze = -0.02375 + 0.0625 * math.cos(ph) - 0.01375 * math.cos(2 * ph)
                if q.z > ze + 0.004: under.append(v.index)
        eh.to_mesh_clear(); h.hide_viewport = hv2
        for m in sd: m.show_viewport = True
        g = h.vertex_groups.new(name="UnderCap"); g.add(under, 1.0, 'REPLACE')
        mm = h.modifiers.new("UnderCap", 'MASK'); mm.vertex_group = "UnderCap"; mm.invert_vertex_group = True
        h.modifiers.move(h.modifiers.find("UnderCap"), 0)
        cfc = [fc for fc in VL.fcurves(cap) if fc.data_path == "hide_render"]      # only while the cap is worn
        if cfc:
            for kp in cfc[0].keyframe_points:
                mm.show_render = not bool(kp.co.y); h.keyframe_insert('modifiers["%s"].show_render' % mm.name, frame=int(kp.co.x))
            VL.constant(h)
        print("HAIR masked under cap", h.name, len(under), "of", len(h.data.vertices))
    tx = bpy.data.textures.new(nm + "_CapWrinkle", 'CLOUDS'); tx.noise_scale = 0.03
    d = cap.modifiers.new("Wrinkle", 'DISPLACE'); d.texture = tx; d.strength = 0.008; d.texture_coords = 'LOCAL'
    so = cap.modifiers.new("t", 'SOLIDIFY'); so.thickness = 0.002
    sub = cap.modifiers.new("s", 'SUBSURF'); sub.levels = 1; sub.render_levels = 1

# v014: her scrub top is a small print (breaks up the shading; no body read)
_st = bpy.data.objects.get("Surgeon2.ScrubTop")
if _st:
    _st.data.materials.clear(); _st.data.materials.append(cap_fabric("Surgeon2ScrubPrint", (0.10, 0.20, 0.52)))
# ------------------------------------------------------------------ v013 masks: pleated masks conformed to each face (no box)
from mathutils.bvhtree import BVHTree as _BVH
for nm, fr in (("Surgeon1", 1), ("Surgeon2", 1100), ("Nurse", 1), ("Anaesth", 1)):
    mk = bpy.data.objects[nm + "_Mask"]; body = bpy.data.objects[nm + ".body"]
    hv = body.hide_viewport; body.hide_viewport = False
    sc.frame_set(fr); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); bme = ev.to_mesh(); Mi = mk.matrix_world.inverted() @ body.matrix_world
    tree = _BVH.FromPolygons([Mi @ v.co for v in bme.vertices], [tuple(p.vertices) for p in bme.polygons]); ev.to_mesh_clear(); body.hide_viewport = hv
    me = mk.data; zs = [v.co.z for v in me.vertices]; z0, z1 = min(zs), max(zs)
    for v in me.vertices:
        loc, nrm, i, d = tree.find_nearest(v.co, 0.06)
        if loc is None: continue
        t = (v.co.z - z0) / max(z1 - z0, 1e-4)
        k = 0.006 + 0.004 * math.sin(math.pi * t) + 0.0015 * math.sin(t * 3 * math.pi * 2)   # pleats, fuller over the mouth
        dv = v.co - loc
        v.co = loc + (dv.normalized() if dv.length > 1e-5 else nrm) * k
    mk.scale = (1, 1, 1)
    print("MASK conformed", mk.name)

# ------------------------------------------------------------------ eyes
if "EnhancedEye" in bpy.data.node_groups:
    _NO_SAVE = True
    exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "eye_fix.py")).read())
else:
    print("NO EnhancedEye group; eye materials:", sorted({m.name for o in bpy.data.objects if o.name.endswith(".high-poly") for m in o.data.materials}))
cam = sc.camera
ld = bpy.data.lights.new("Catchlight", 'POINT'); ld.energy = 0.6; ld.shadow_soft_size = 0.02
cl = bpy.data.objects.new("Catchlight", ld); sc.collection.objects.link(cl)
cl.parent = cam; cl.location = (0.12, 0.10, 0.0)
cl.visible_diffuse = False; cl.visible_transmission = False; cl.visible_volume_scatter = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("LOOKS_DONE", OUT)
