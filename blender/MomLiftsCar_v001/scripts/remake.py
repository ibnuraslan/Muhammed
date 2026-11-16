"""Append a finished MPFB character from an earlier film, give it a new phenotype and refit every proxy + the rig.
(MakeHuman asset server was down: this rebuilds mhclo fitting data from the already-fitted proxies.)
remake(src_blend, donor, new, pheno, drop=(suffixes), extra=[(src2, donor2, suffix)]) -> rig"""
import bpy
from bl_ext.user_default.mpfb.services.targetservice import TargetService
from bl_ext.user_default.mpfb.services.clothesservice import ClothesService
from bl_ext.user_default.mpfb.services.rigservice import RigService
from bl_ext.user_default.mpfb.entities.objectproperties import HumanObjectProperties
KEEP = ("ARMATURE", "MASK", "SUBSURF")

def _load(src, donor, only=None):
    with bpy.data.libraries.load(src, link=False) as (fd, td):
        td.objects = [n for n in fd.objects if n == donor or (n.startswith(donor + ".") and (only is None or n[len(donor)+1:] in only))]
    objs = [o for o in td.objects if o]
    for o in objs:
        o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
        for m in list(o.modifiers):
            if m.type not in KEEP: o.modifiers.remove(m)
        for c in list(o.constraints): o.constraints.remove(c)
    return objs

def _mods_off(obs):
    saved = []
    for o in obs:
        for m in o.modifiers: saved.append((m, m.show_viewport)); m.show_viewport = False
    bpy.context.view_layer.update(); return saved

def remake(src, donor, new, pheno, drop=(), extra=()):
    objs = _load(src, donor)
    col = bpy.data.collections.new("CH_" + new); bpy.context.scene.collection.children.link(col)
    rig = bpy.data.objects[donor]; body = bpy.data.objects[donor + ".body"]
    for o in objs:
        if o.type == 'EMPTY' or (o.type == 'MESH' and o.name[len(donor)+1:] in drop) or (o.parent != rig and o != rig):
            bpy.data.objects.remove(o); continue
        col.objects.link(o)
    for d in drop:
        for m in list(body.modifiers):
            if m.type == 'MASK' and m.name == "Delete." + d: body.modifiers.remove(m)
    for pb in rig.pose.bones:
        for c in list(pb.constraints): pb.constraints.remove(c)
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    rig.hide_viewport = False; rig.hide_set(False); bpy.context.view_layer.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in list(rig.data.edit_bones):
        if eb.name.startswith(("IK_", "Pole_")): rig.data.edit_bones.remove(eb)
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
    proxies = [o for o in col.objects if o.type == 'MESH' and o != body]
    saved = _mods_off([body] + proxies)
    mh = {}
    for p in proxies:
        try: mh[p] = ClothesService.create_mhclo_from_clothes_matching(body, p)
        except Exception as e: print("MHCLO_FAIL", p.name, e)
    # extra proxies from other donors: match against their own body
    for src2, donor2, suf in extra:
        o2 = _load(src2, donor2, only=("body", suf))
        b2 = next(o for o in o2 if o.name.endswith(".body")); p2 = next(o for o in o2 if o.name.endswith("." + suf))
        for o in o2:
            if o.name not in bpy.context.scene.collection.objects: bpy.context.scene.collection.objects.link(o)
        b2.parent = None; p2.parent = None
        s2 = _mods_off([b2, p2])
        mh[p2] = ClothesService.create_mhclo_from_clothes_matching(b2, p2)
        # delete group from donor2 body -> target body (same basemesh topology)
        vg = b2.vertex_groups.get("Delete." + suf)
        if vg and len(b2.data.vertices) == len(body.data.vertices):
            ng = body.vertex_groups.get("Delete." + suf) or body.vertex_groups.new(name="Delete." + suf)
            idx = [v.index for v in b2.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
            ng.add(idx, 1.0, 'REPLACE')
            mm = body.modifiers.new("Delete." + suf, 'MASK'); mm.vertex_group = ng.name; mm.invert_vertex_group = True; mm.show_viewport = False
            saved.append((mm, True))
        bpy.context.scene.collection.objects.unlink(p2); col.objects.link(p2)
        p2.name = donor + "." + suf
        for m, sv in s2: m.show_viewport = sv
        bpy.data.objects.remove(b2)
        proxies.append(p2)
    for k, v in pheno.items():
        if k == "race":
            for rk, rv in v.items(): HumanObjectProperties.set_value(rk, rv, entity_reference=body)
        else: HumanObjectProperties.set_value(k, v, entity_reference=body)
    TargetService.reapply_macro_details(body)
    bpy.context.view_layer.update()
    for p in proxies:
        if p in mh: ClothesService.fit_clothes_to_human(p, body, mh[p], set_parent=False)
    RigService.refit_existing_armature(rig, body)
    for m, sv in saved: m.show_viewport = sv
    for p in proxies:
        p.parent = rig; p.matrix_parent_inverse.identity()
        am = next((m for m in p.modifiers if m.type == 'ARMATURE'), None) or p.modifiers.new("Armature", 'ARMATURE')
        am.object = rig
        if p.modifiers[0] != am:
            with bpy.context.temp_override(object=p): bpy.ops.object.modifier_move_to_index(modifier=am.name, index=0)
    for o in list(col.objects):
        if o.name == donor: o.name = new; o.data.name = new
        elif o.name.startswith(donor + "."): o.name = new + o.name[len(donor):]
    print("REMADE", new, "from", donor, pheno, sorted(o.name for o in col.objects))
    return rig

def tint(rig, key, rgb, mix=1.0):
    """multiply the diffuse texture of every child mesh whose name contains `key` (as CaveRescue 01_build_chars)"""
    for ch in rig.children:
        if ch.type == 'MESH' and key in ch.name:
            for i, m in enumerate(ch.data.materials):
                if not m: continue
                m = m.copy(); ch.data.materials[i] = m
                for nd in list(m.node_tree.nodes):
                    if nd.type == 'TEX_IMAGE' and nd.image and "normal" not in nd.image.name.lower() and nd.outputs['Color'].links:
                        for lk in list(nd.outputs['Color'].links):
                            if lk.to_node.type == 'MIX' and lk.to_node.get("tint"): continue
                            mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx["tint"] = 1
                            mx.inputs['Factor'].default_value = mix; mx.inputs['B'].default_value = (*rgb, 1)
                            m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)
