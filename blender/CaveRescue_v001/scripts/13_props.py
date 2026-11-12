"""v006d props pass (director: qa_check e7b25f7 PROPMOVE / ATTACH).
- Worn gear and carried props that followed a bone through a Child Of constraint (head torches, dive masks, tanks,
  tow harness, the boy's full-face mask) are re-attached as true bone children. The world motion is baked frame by
  frame where the constraint's influence is animated, so nothing moves differently; the prop now IS parented to the bone.
- Masks sit ON the skin: a shrinkwrap (6 mm above the surface) to the wearer's body. On the boy's full-face mask it
  switches on once the fitting is done (2366); during the fitting the mask is in DiverB's hands.
blender -b in.blend --python 13_props.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
def fcurves(o):
    ad = o.animation_data
    if not ad or not ad.action: return []
    return [fc for lay in ad.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves]
def animated_influence(o):
    return any(fc.data_path.startswith("constraints") or fc.data_path in ("location", "rotation_euler", "rotation_quaternion") for fc in fcurves(o))
def shown(o, f):
    for fc in fcurves(o):
        if fc.data_path == "hide_render": return fc.evaluate(f) < 0.5
    return not o.hide_render
def vis_range(o):
    fr = [f for f in range(sc.frame_start, sc.frame_end + 1, 1)]
    return fr
conv = []
for o in list(bpy.data.objects):
    cs = [c for c in o.constraints if c.type == 'CHILD_OF' and c.target and c.target.type == 'ARMATURE' and c.subtarget]
    if len(cs) != 1 or o.parent is not None: continue
    c = cs[0]; rig = c.target; bone = c.subtarget
    if animated_influence(o):
        # bake: world matrix on every frame where it is shown (plus a margin), keyed in the bone's space
        hidden_keys = None
        W = {}
        for f in range(sc.frame_start, sc.frame_end + 1):
            if not shown(o, f): continue
            sc.frame_set(f); W[f] = o.matrix_world.copy()
        if not W: continue
        o.constraints.remove(c)
        if o.animation_data and o.animation_data.action:
            ad = o.animation_data
            for lay in ad.action.layers:
                for st in lay.strips:
                    for cb in st.channelbags:
                        for fc in list(cb.fcurves):
                            if fc.data_path in ("location", "rotation_euler", "rotation_quaternion", "scale") or fc.data_path.startswith("constraints"):
                                cb.fcurves.remove(fc)
        o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bone
        o.rotation_mode = 'XYZ'; prev = None
        for f in sorted(W):
            sc.frame_set(f); bpy.context.view_layer.update()
            o.matrix_world = W[f]
            if prev is not None: o.rotation_euler.make_compatible(prev)
            prev = o.rotation_euler.copy()
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f); o.keyframe_insert("scale", frame=f)
        conv.append((o.name, "baked", len(W)))
    else:
        sc.frame_set(sc.frame_start); bpy.context.view_layer.update()
        Wm = o.matrix_world.copy()
        o.constraints.remove(c)
        o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bone
        bpy.context.view_layer.update(); o.matrix_world = Wm
        conv.append((o.name, "parented", bone))
print("PROPS_PARENTED", len(conv), conv[:6])
# masks on the skin
def body_of(rig): return bpy.data.objects.get(rig.name + ".body")
sw = 0
for o in bpy.data.objects:
    if o.type != 'MESH' or o.parent is None or o.parent.type != 'ARMATURE': continue
    nm = o.name
    if nm.endswith("_Mask") or nm == "Prop_FullFaceMask":
        b = body_of(o.parent)
        if not b: continue
        m = o.modifiers.new("OnSkin", 'SHRINKWRAP'); m.target = b; m.wrap_method = 'NEAREST_SURFACEPOINT'; m.wrap_mode = 'OUTSIDE_SURFACE'; m.offset = 0.006
        if nm == "Prop_FullFaceMask":
            for f, on in ((1, False), (2365, False), (2366, True)):
                m.show_render = on; m.show_viewport = on
                m.keyframe_insert("show_render", frame=f); m.keyframe_insert("show_viewport", frame=f)
        sw += 1
# the visor glass sits inside the rim: also on the skin once the mask is on
b2 = bpy.data.objects.get("Boy2.body")
for nm_, off_ in (("Prop_MaskVisor", 0.008), ("Prop_MaskRegulator", 0.012)):    # visor glass and the regulator at the mouth
    vz = bpy.data.objects.get(nm_)
    if not (vz and b2): continue
    m = vz.modifiers.new("OnSkin", 'SHRINKWRAP'); m.target = b2; m.wrap_method = 'NEAREST_SURFACEPOINT'; m.wrap_mode = 'OUTSIDE_SURFACE'; m.offset = off_
    for f, on in ((1, False), (2365, False), (2366, True)):
        m.show_render = on; m.show_viewport = on; m.keyframe_insert("show_render", frame=f); m.keyframe_insert("show_viewport", frame=f)
    sw += 1
print("MASKS_ON_SKIN", sw)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("PROPS_OK")
