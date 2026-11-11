"""Four MPFB2 humans (MakeHuman CC0 assets): Girl, Teacher, Mother, Father.
blender -b --python 01_build_humans.py -- <out.blend>"""
import sys
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)

def tint(rig, cloth, rgb):
    for ch in rig.children:
        if ch.type == 'MESH' and ch.name.split(".")[-1] == cloth:
            for m in ch.data.materials:
                nt = m.node_tree
                for nd in list(nt.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                        for lk in list(nd.outputs['Color'].links):
                            hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.0
                            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                            mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                            nt.links.new(nd.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], mx.inputs['A'])
                            mx2 = nt.nodes.new('ShaderNodeMix'); mx2.data_type = 'RGBA'; mx2.inputs['Factor'].default_value = 0.65
                            mx2.inputs['B'].default_value = (*rgb, 1)
                            nt.links.new(mx.outputs['Result'], mx2.inputs['A']); nt.links.new(mx2.outputs['Result'], lk.to_socket)

def human(name, ph, hair, clothes, skin, x, tints):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    base = {"gender": 0.0, "age": 0.5, "muscle": 0.5, "weight": 0.5, "proportions": 0.6, "height": 0.5,
            "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.0, "caucasian": 1.0, "african": 0.0}}
    base.update(ph); info["phenotype"] = base
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = "eyebrow001/eyebrow001.mhclo"
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]; rig.location.x = x
    for c, rgb in tints.items(): tint(rig, c, rgb)
    return rig

human("Girl", {"age": 0.17, "height": 0.5, "proportions": 0.35, "weight": 0.45}, "braid01/braid01.mhclo",
      ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"],
      "young_caucasian_female/young_caucasian_female.mhmat", 0.0, {"female_elegantsuit01": (0.05, 0.09, 0.2)})
human("Teacher", {"age": 0.42, "height": 0.7, "weight": 0.45}, "ponytail01/ponytail01.mhclo",
      ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"],
      "young_caucasian_female2/young_caucasian_female2.mhmat", 1.0, {"female_elegantsuit01": (0.62, 0.58, 0.5)})
human("Mother", {"age": 0.6, "height": 0.65, "weight": 0.55}, "long01/long01.mhclo",
      ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"],
      "middleage_caucasian_female/middleage_caucasian_female.mhmat", 2.0, {"female_elegantsuit01": (0.14, 0.04, 0.045)})
human("Father", {"gender": 1.0, "age": 0.68, "height": 0.5, "weight": 0.6}, "short02/short02.mhclo",
      ["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"],
      "middleage_caucasian_male/middleage_caucasian_male.mhmat", 3.0, {"male_elegantsuit01": (0.05, 0.045, 0.04)})
import math, bmesh
from mathutils import Vector
def floor_clamp_group():
    g = bpy.data.node_groups.get("FloorClamp")
    if g: return g
    g = bpy.data.node_groups.new("FloorClamp", 'GeometryNodeTree')
    g.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    g.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, l = g.nodes, g.links
    gi = n.new('NodeGroupInput'); go = n.new('NodeGroupOutput')
    pos = n.new('GeometryNodeInputPosition'); sep = n.new('ShaderNodeSeparateXYZ'); mx = n.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; mx.inputs[1].default_value = 0.006
    com = n.new('ShaderNodeCombineXYZ'); sp = n.new('GeometryNodeSetPosition')
    l.new(pos.outputs[0], sep.inputs[0]); l.new(sep.outputs['Z'], mx.inputs[0])
    l.new(sep.outputs['X'], com.inputs['X']); l.new(sep.outputs['Y'], com.inputs['Y']); l.new(mx.outputs[0], com.inputs['Z'])
    l.new(gi.outputs[0], sp.inputs['Geometry']); l.new(com.outputs[0], sp.inputs['Position']); l.new(sp.outputs[0], go.inputs[0])
    return g

def long_skirt(rig, rgb, flare=0.12, hem_z=0.03, shin=1.0, wrap_low=0.0):
    SHIN = shin
    """period skirt: a measured cone from the waist, weighted root -> thighs -> shins (no hem bone), floor-clamped by geometry nodes"""
    body = next(c for c in rig.children if c.name.endswith(".body"))
    B = rig.data.bones
    zw = B["spine04"].head_local.z + 0.02
    cx, cy = B["root"].head_local.x, B["root"].head_local.y
    dg = bpy.context.evaluated_depsgraph_get(); em = body.evaluated_get(dg).to_mesh()
    V = [v.co.copy() for v in em.vertices]
    NS, NR = 48, 20
    bm = bmesh.new(); rings = []; rr = []
    for r in range(NR):
        t = r / (NR - 1); z = zw - t * (zw - hem_z)
        band = [v for v in V if abs(v.z - z) < 0.02 and abs(v.x - cx) < 0.21 and abs(v.y - cy) < 0.2]
        rx = 1.12 * max([abs(v.x - cx) for v in band] or [0.12]); ry = 1.12 * max([abs(v.y - cy) for v in band] or [0.1])
        if rr: rx = max(rx, rr[-1][0]); ry = max(ry, rr[-1][1])
        rr.append((rx, ry))
        ex = 0.02 + flare * t ** 1.3
        rings.append([bm.verts.new((cx + (rx + ex) * math.sin(2 * math.pi * k / NS), cy - (ry + ex * 0.85) * math.cos(2 * math.pi * k / NS), z)) for k in range(NS)])
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(NS):
            bm.faces.new((a_[k], a_[(k + 1) % NS], b_[(k + 1) % NS], b_[k]))
    me = bpy.data.meshes.new(rig.name + "_LongSkirt"); bm.to_mesh(me)
    for p in me.polygons: p.use_smooth = True
    uv = me.uv_layers.new()
    for i, lp in enumerate(me.loops):
        co = me.vertices[lp.vertex_index].co; uv.data[i].uv = (math.atan2(co.x - cx, co.y - cy) / math.pi, co.z)
    ob = bpy.data.objects.new(rig.name + ".long_skirt", me); bpy.context.scene.collection.objects.link(ob)
    ob.parent = rig
    names = ("root", "upperleg02.L", "upperleg02.R", "lowerleg01.L", "lowerleg01.R")
    G = {n: ob.vertex_groups.new(name=n) for n in names}
    zk = B["lowerleg01.L"].head_local.z
    for v in me.vertices:
        side = max(-1, min(1, (v.co.x - cx) / 0.1)); wl = 0.5 + 0.5 * side
        wr = max(0.0, min(1.0, (v.co.z - (zw - 0.22)) / 0.2))          # waist band follows the pelvis
        wk = SHIN * max(0.0, min(1.0, ((zk + 0.06) - v.co.z) / 0.18))   # below the knee drapes part-way after the shins
        wt = max(0.0, 1 - wr - wk)
        G["root"].add([v.index], wr, 'REPLACE')
        G["upperleg02.L"].add([v.index], wt * wl, 'REPLACE'); G["upperleg02.R"].add([v.index], wt * (1 - wl), 'REPLACE')
        G["lowerleg01.L"].add([v.index], wk * wl, 'REPLACE'); G["lowerleg01.R"].add([v.index], wk * (1 - wl), 'REPLACE')
    WR = ob.vertex_groups.new(name="wrap")
    for v in me.vertices:
        above_knee = max(0.0, min(1.0, (v.co.z - (zk - 0.02)) / 0.1))
        waist = max(0.0, min(1.0, (zw - 0.05 - v.co.z) / 0.1))
        WR.add([v.index], waist * (above_knee + (1 - above_knee) * wrap_low), 'REPLACE')
    # keep the legs under a long skirt (MPFB deletes body under the knee-length suit skirt)
    dg_ = body.vertex_groups.get("Delete." + next(c for c in rig.children if c.name.endswith("elegantsuit01")).name.split(".")[-1])
    if dg_:
        dg_.remove([v.index for v in body.data.vertices if v.co.z < zw - 0.08])
    am = ob.modifiers.new("Armature", 'ARMATURE'); am.object = rig
    sw = ob.modifiers.new("DrapeOnLegs", 'SHRINKWRAP'); sw.target = body; sw.wrap_method = 'NEAREST_SURFACEPOINT'
    sw.wrap_mode = 'OUTSIDE_SURFACE'; sw.offset = 0.022; sw.vertex_group = "wrap"
    sw2 = ob.modifiers.new("DrapeIn", 'SHRINKWRAP'); sw2.target = body; sw2.wrap_method = 'NEAREST_SURFACEPOINT'
    sw2.wrap_mode = 'ON_SURFACE'; sw2.offset = 0.03; sw2.vertex_group = "wrap"
    smo = ob.modifiers.new("Bridge", 'SMOOTH'); smo.factor = 0.7; smo.iterations = 8; smo.vertex_group = "wrap"
    sw3 = ob.modifiers.new("KeepOut", 'SHRINKWRAP'); sw3.target = body; sw3.wrap_method = 'NEAREST_SURFACEPOINT'
    sw3.wrap_mode = 'OUTSIDE_SURFACE'; sw3.offset = 0.012
    gn = ob.modifiers.new("FloorClamp", 'NODES'); gn.node_group = floor_clamp_group()
    ob.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.006
    ob.modifiers.new("Sub", 'SUBSURF').levels = 1
    suit = next(c for c in rig.children if c.name.endswith("elegantsuit01"))
    vg = suit.vertex_groups.new(name="upper_only")
    vg.add([v.index for v in suit.data.vertices if v.co.z > zw - 0.06], 1.0, "REPLACE")
    mk = suit.modifiers.new("HideSkirt", 'MASK'); mk.vertex_group = "upper_only"
    suit.modifiers.move(len(suit.modifiers) - 1, 0)
    m = bpy.data.materials.new(rig.name + "_SkirtFabric"); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.8
    p.inputs["Sheen Weight"].default_value = 0.25; p.inputs["Sheen Tint"].default_value = (*rgb, 1)
    # woven texture: fine twill bands + noise so it never reads as clay
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (60, 60, 60)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'DIAGONAL'; wv.inputs["Scale"].default_value = 3.0
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.4; nz.inputs["Detail"].default_value = 6
    nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeMix"); cr.data_type = 'RGBA'; cr.inputs["A"].default_value = (*[c * 0.7 for c in rgb], 1); cr.inputs["B"].default_value = (*rgb, 1)
    mixf = nt.nodes.new("ShaderNodeMath"); mixf.operation = 'MULTIPLY'
    nt.links.new(wv.outputs["Fac"], mixf.inputs[0]); nt.links.new(nz.outputs["Fac"], mixf.inputs[1]); nt.links.new(mixf.outputs[0], cr.inputs["Factor"])
    nt.links.new(cr.outputs["Result"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25
    nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    me.materials.append(m)
    # petticoat / stockings: body below the waist gets a fabric material, so any drape gap shows cloth, never skin
    stock = bpy.data.materials.new(rig.name + "_Stockings"); stock.use_nodes = True
    sp = stock.node_tree.nodes["Principled BSDF"]; sp.inputs["Base Color"].default_value = (*[c * 0.6 for c in rgb], 1); sp.inputs["Roughness"].default_value = 0.7
    sp.inputs["Sheen Weight"].default_value = 0.5
    bm_ = body.data; bm_.materials.append(stock); idx = len(bm_.materials) - 1
    LEG = {g.index for g in body.vertex_groups if any(k in g.name for k in ("upperleg", "lowerleg", "foot", "toe", "pelvis"))}
    def legw(v): return sum(g.weight for g in bm_.vertices[v].groups if g.group in LEG)
    for p in bm_.polygons:
        if p.center.z < zw - 0.03 and all(legw(v) > 0.5 for v in p.vertices): p.material_index = idx
    return ob
long_skirt(bpy.data.objects["Teacher"], (0.06, 0.07, 0.12), flare=0.04, shin=1.0, wrap_low=1.0)
long_skirt(bpy.data.objects["Mother"], (0.17, 0.05, 0.06))
long_skirt(bpy.data.objects["Girl"], (0.07, 0.13, 0.28), flare=0.07, hem_z=0.2)

for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("HUMAN", ob.name, [(c.name, tuple(round(d, 2) for d in c.dimensions)) for c in ob.children])
bpy.ops.wm.save_as_mainfile(filepath=out)
