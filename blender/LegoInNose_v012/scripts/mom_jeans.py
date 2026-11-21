"""v012 (found by watching): Mom's knees poked through the slim skirt on her stride. She now wears the blouse over JEANS:
 - the leg part of female_casualsuit01 (build_jeans.py) is added (vertices dominated by pelvis/leg/foot bones below the hips)
 - the skirt part of the blouse outfit is removed (everything below the hip line, rest z 0.88)
 - the body's Delete mask for female_casualsuit01 (skin under the jeans) is on again
blender -b in.blend --python mom_jeans.py -- newjeans.blend out.blend"""
import bpy, sys, bmesh
a = sys.argv[sys.argv.index("--") + 1:]; SRC, OUT = a[0], a[1]
rig = bpy.data.objects["Mom"]; body = bpy.data.objects["Mom_Body"]
def keep_only(o, test):
    gi = {g.index: g.name for g in o.vertex_groups}; bm = bmesh.new(); bm.from_mesh(o.data); dl = bm.verts.layers.deform.active
    kill = []
    for v in bm.verts:
        ws = v[dl]; g = max(ws.items(), key=lambda kv: kv[1], default=(None, 0))[0]; nm = gi.get(g, "")
        if not test(nm, v.co): kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(o.data); bm.free(); return len(kill)
LEG = ("pelvis", "upperleg", "lowerleg", "foot", "toe")
# 1. blouse only
bl = bpy.data.objects["Mom_female_elegantsuit01"]
if "SkirtRoom" in bl.modifiers: bl.modifiers.remove(bl.modifiers["SkirtRoom"])
k1 = keep_only(bl, lambda nm, co: co.z >= 0.88)          # the whole skirt (everything below the hip line)
# 2. jeans
with bpy.data.libraries.load(SRC, link=False) as (fr, to): to.objects = ["NEW_Mom_female_casualsuit01"]
j = to.objects[0]; bpy.context.scene.collection.objects.link(j)
loc = j.matrix_local.copy(); j.parent = rig; j.matrix_parent_inverse.identity(); j.matrix_basis = loc; j.name = "Mom_jeans"
for m in j.modifiers:
    if m.type == "ARMATURE": m.object = rig
k2 = keep_only(j, lambda nm, co: nm.startswith(LEG) and co.z < 0.92)
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if o.animation_data and o.animation_data.action else []
for fc in [c for c in fcs(body) if c.data_path == "hide_render"]:
    for k in fc.keyframe_points: j.hide_render = bool(k.co.y); j.keyframe_insert("hide_render", frame=k.co.x)
for img in bpy.data.images:
    if "casualsuit01" in img.name and not img.packed_file:
        try: img.pack()
        except Exception: pass
# 3. skin under the jeans
for md in body.modifiers:
    if md.type == "MASK" and md.vertex_group == "Delete.female_casualsuit01": md.show_render = True; md.show_viewport = True
print("MOMJEANS blouse verts removed", k1, "jeans verts removed", k2, "left", len(j.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
