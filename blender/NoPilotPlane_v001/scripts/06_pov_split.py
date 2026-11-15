"""v007d: the POV camera sits inside YOU's head. Make YOU's head, neck, shoulders and upper chest invisible to CAMERA rays
(shadows, reflections and indirect light stay) until the float-out; camera clip_start 8 cm, when the camera leaves the head for the face reveal.
blender -b in.blend --python 06_pov_split.py -- out.blend
- YOU.body and YOU.male_casualsuit04 are split: faces touching a head/neck/shoulder/upper-chest vertex go to a new
  object '<name>.headpart' (same armature + modifiers); the rest stay.
- the .headpart objects, eyes, teeth and tongue: visible_camera keyed False from frame 1, True from F(71.4) (CONSTANT)."""
import sys, bpy, bmesh
out = sys.argv[sys.argv.index("--") + 1]
FPS = 60
def F(t): return 1 + round(t * FPS)
REVEAL = F(71.4)
Y = bpy.data.objects["YOU"]; B = Y.data.bones
HEAD = {b.name for b in B["neck01"].children_recursive} | {"neck01"}
HEAD |= {b.name for b in B if b.name.startswith(("shoulder", "clavicle", "upperarm01"))}   # v008b: not the chest (holes in the shirt when looking down)
print("HEADSET bones", len(HEAD))

def key_cam(o):
    o.visible_camera = False; o.keyframe_insert("visible_camera", frame=1)
    o.visible_camera = False; o.keyframe_insert("visible_camera", frame=REVEAL - 1)
    o.visible_camera = True; o.keyframe_insert("visible_camera", frame=REVEAL)
    for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

def split(ob):
    gi = {g.index: g.name for g in ob.vertex_groups}
    me = ob.data
    inset = set()
    for v in me.vertices:
        ws = [(g.weight, gi.get(g.group)) for g in v.groups if gi.get(g.group) in B]
        if ws and max(ws)[1] in HEAD: inset.add(v.index)
    hd = ob.copy(); hd.data = me.copy(); hd.name = ob.name + ".headpart"
    for c in ob.users_collection: c.objects.link(hd)
    hd.parent = ob.parent; hd.matrix_parent_inverse = ob.matrix_parent_inverse.copy()
    for m in hd.modifiers:
        if m.type == 'ARMATURE': m.object = Y
    def keep(mesh, want_head):
        bm = bmesh.new(); bm.from_mesh(mesh)
        kill = [f for f in bm.faces if (any(v.index in inset for v in f.verts)) != want_head]
        bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(mesh); bm.free()
    keep(hd.data, True); keep(me, False)
    print("SPLIT", ob.name, "head verts", len(inset), "->", hd.name, len(hd.data.vertices), "| body keeps", len(me.vertices))
    return hd

# v008b: keep unsplit copies for the face reveal (split seams show at the shoulders); they render only from REVEAL on,
# the split pieces only before it
def key_render(o, before_hidden):
    for f_, h in ((1, before_hidden), (REVEAL - 1, before_hidden), (REVEAL, not before_hidden)):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f_)
origs = []
for nm in ("YOU.body", "YOU.male_casualsuit04"):
    src = bpy.data.objects[nm]; cp = src.copy(); cp.data = src.data.copy(); cp.name = nm + ".reveal"
    for c in src.users_collection: c.objects.link(cp)
    cp.parent = src.parent; cp.matrix_parent_inverse = src.matrix_parent_inverse.copy()
    for m in cp.modifiers:
        if m.type == 'ARMATURE': m.object = Y
    origs.append(cp)
parts = [split(bpy.data.objects["YOU.body"]), split(bpy.data.objects["YOU.male_casualsuit04"])]
for o in origs: key_render(o, True)
for nm in ("YOU.body", "YOU.male_casualsuit04", "YOU.body.headpart", "YOU.male_casualsuit04.headpart"): key_render(bpy.data.objects[nm], False)
for nm in ("YOU.high-poly", "YOU.teeth_base", "YOU.tongue01"):
    parts.append(bpy.data.objects[nm])
for o in parts: key_cam(o)
# Blender 5 layered actions: set CONSTANT on every channelbag curve of these objects
for o in parts:
    act = o.animation_data.action
    for lay in getattr(act, "layers", []):
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == "visible_camera":
                        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# where the 8 cm near clip cuts into YOU's own limb, the camera would see the dark inside of the mesh (black blobs):
# make backfaces transparent to camera rays on all of YOU's materials, so a clipped limb shows the cockpit behind it
done = set()
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith("YOU.") or not any(k in o.name for k in ("body", "casualsuit", "shoes")): continue
    for sl in o.material_slots:
        m = sl.material
        if not m or m.name in done or not m.use_nodes: continue
        done.add(m.name); nt = m.node_tree
        outn = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output] or [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
        if not outn or not outn[0].inputs["Surface"].is_linked: continue
        outn = outn[0]; src = outn.inputs["Surface"].links[0].from_socket
        geo = nt.nodes.new("ShaderNodeNewGeometry"); lp = nt.nodes.new("ShaderNodeLightPath")
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
        nt.links.new(geo.outputs["Backfacing"], mul.inputs[0]); nt.links.new(lp.outputs["Is Camera Ray"], mul.inputs[1])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(mul.outputs[0], mx.inputs[0]); nt.links.new(src, mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], outn.inputs["Surface"])
print("BACKFACE_TRANSPARENT", sorted(done))
# v008b prop hygiene (qa_check PROPMOVE / ATTACH):
# - uniform details followed their bones through a CHILD_OF constraint (parent None, so they read as props moving
#   by themselves): parent them to the bone for real, keeping the frame-1 placement
# - the deployed oxygen masks hang from the ceiling on their tubes: parent them to a fixed ceiling mount, and name
#   them OXYDROP (they are not worn, so the worn-mask check does not apply); the cockpit sun visors become SUNSHADE
sc_ = bpy.context.scene; sc_.frame_set(1)
nb = 0
for o in list(bpy.data.objects):
    cs = [c for c in o.constraints if c.type == 'CHILD_OF' and c.target and c.target.type == 'ARMATURE']
    if not cs: continue
    c = cs[0]; arm, bone = c.target, c.subtarget
    bpy.context.view_layer.update(); W = o.matrix_world.copy()
    o.constraints.remove(c)
    o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = W; nb += 1
mount = bpy.data.objects.new("OXYDROP_CEILING_MOUNT", None); sc_.collection.objects.link(mount)
nm = 0
for o in list(bpy.data.objects):
    if o.name.startswith("MASK_") and o.type == 'MESH':
        o.name = "OXYDROP_" + o.name[5:]; o.parent = mount; nm += 1
    elif o.name.startswith("VISOR_"):
        o.name = "SUNSHADE_" + o.name[6:]
print("PROPFIX bone-parented", nb, "oxygen drops", nm)
# nothing belongs within 8 cm of an eye: clip YOU's own forearm when it crosses under the lens (29.0 s haul)
bpy.context.scene.camera.data.clip_start = 0.08
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("POVSPLIT saved", out, [o.name for o in parts])
