"""Pre-rendered graphics: (1) the remembered closet (for the memory cloud), (2) the brain-scan screen image (clean graphic:
glowing blue head profile + brain, red/yellow tumour). blender -b work/sets.blend --python 02b_graphics.py"""
import bpy, math
from mathutils import Vector
HERE = "/home/user/Muhammed/blender/ClosetBathroom_v001/"
R_ = math.radians
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'ARMATURE': o.location.x += 200
for c in ("DRESS_Bath", "DRESS_Prank"): bpy.data.collections[c].hide_render = True
bpy.data.objects["DoorPivot"].rotation_euler.z = R_(95)
cam = bpy.data.objects.new("GCam", bpy.data.cameras.new("GCam")); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0.0, -0.9, 1.45); cam.data.lens = 22
cam.rotation_euler = (Vector((0, 1.6, 1.25)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x, sc.render.resolution_y = 640, 640; sc.cycles.samples = 32
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = HERE + "assets/closet_memory.png"
bpy.ops.render.render(write_still=True)

# ---------------- brain scan graphic, own scene
S2 = bpy.data.scenes.new("Scan"); bpy.context.window.scene = S2 if bpy.context.window else None
S2.render.engine = 'CYCLES'; S2.cycles.device = 'CPU'; S2.cycles.samples = 24; S2.cycles.use_denoising = True
S2.render.resolution_x, S2.render.resolution_y = 1280, 768
S2.view_settings.view_transform = 'Standard'
S2.world = bpy.data.worlds.new("ScanW"); S2.world.use_nodes = True; S2.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
def emit_mat(name, col, strength, rim=True, alpha_core=0.25):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.35
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (*col, 1)
    ma = nt.nodes.new("ShaderNodeMath"); ma.operation = 'MULTIPLY_ADD'; ma.inputs[1].default_value = strength; ma.inputs[2].default_value = strength * alpha_core
    nt.links.new(lw.outputs["Facing"], ma.inputs[0]); nt.links.new(ma.outputs[0], em.inputs[1])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(em.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], o.inputs[0])
    return m
# head profile: a copy of Tom's body mesh (rest pose), only the head/neck kept
body = bpy.data.objects["Tom.body"]
me = body.data.copy(); hd = bpy.data.objects.new("ScanHead", me); S2.collection.objects.link(hd)
for g in body.vertex_groups: hd.vertex_groups.new(name=g.name)
for m_ in list(hd.modifiers): hd.modifiers.remove(m_)
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
gi = {g.index for g in hd.vertex_groups if g.name.startswith(("HelperGeometry", "JointCubes")) or "helper" in g.name.lower()}
dl = bm.verts.layers.deform.active
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 1.30 or (dl and any(k in gi and w > 0.5 for k, w in v[dl].items()))], context='VERTS'); bm.to_mesh(me); bm.free()
me.materials.clear(); me.materials.append(emit_mat("ScanSkin", (0.25, 0.7, 1.0), 0.9, alpha_core=0.06))
hd.location = (0, 0, 0)
# brain: the anatomical model, glowing blue, sized and placed inside the skull
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=HERE + "assets/brain.glb")
new = [o for o in bpy.data.objects if o not in before]
for o in new:
    for c in o.users_collection: c.objects.unlink(o)
    S2.collection.objects.link(o)
br_meshes = [o for o in new if o.type == 'MESH']
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in br_meshes for c in o.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
d = mx - mn; print("BRAIN dims", tuple(round(v, 3) for v in d))
root = [o for o in new if o.parent is None]
piv = bpy.data.objects.new("BrainPiv", None); S2.collection.objects.link(piv)
for o in root: o.parent = piv
# fit: longest horizontal axis -> 0.165 m front-back
L = max(d.x, d.y); s = 0.165 / L
c0 = (mn + mx) / 2
for o in root: o.location = (o.location - c0)
piv.scale = (s, s, s)
if d.x > d.y: piv.rotation_euler = (0, 0, R_(90))
BM = emit_mat("ScanBrain", (0.3, 0.75, 1.0), 1.1, alpha_core=0.3)
for o in br_meshes:
    o.data.materials.clear(); o.data.materials.append(BM)
# head bbox -> brain position (upper back of the skull)
vs = [hd.matrix_world @ v.co for v in me.vertices]
hz1 = max(v.z for v in vs); hy0 = min(v.y for v in vs); hy1 = max(v.y for v in vs)
print("HEAD z top", round(hz1, 3), "y", round(hy0, 3), round(hy1, 3))
piv.location = (0, (hy0 + hy1) / 2 + 0.018, hz1 - 0.098)
# tumour: hot core + soft halo
for nm, r, col, st in (("TumourHalo", 0.02, (1.0, 0.03, 0.0), 0.9), ("TumourCore", 0.011, (1.0, 0.35, 0.0), 0.8)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(0.2, piv.location.y + 0.035, piv.location.z + 0.005))
    t = bpy.context.object; t.name = nm
    for c in t.users_collection: c.objects.unlink(t)
    S2.collection.objects.link(t); tm = emit_mat(nm + "M", col, st, alpha_core=0.9 if "Core" in nm else 0.5); t.data.materials.append(tm)
    if "Core" in nm:   # opaque hot core (no additive blue from the layers behind)
        ntt = tm.node_tree; emn = next(n for n in ntt.nodes if n.type == 'EMISSION'); outn = next(n for n in ntt.nodes if n.type == 'OUTPUT_MATERIAL')
        ntt.links.new(emn.outputs[0], outn.inputs[0])
    bpy.ops.object.shade_smooth()
# backdrop: dark navy panel with a faint glow
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.6, (hy0 + hy1) / 2, hz1 - 0.2)); bp = bpy.context.object
for c in bp.users_collection: c.objects.unlink(bp)
S2.collection.objects.link(bp); bp.scale = (1, 1.4, 1); bp.rotation_euler = (0, R_(90), 0)
bm_ = bpy.data.materials.new("ScanBG"); bm_.use_nodes = True; nt = bm_.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); tc = nt.nodes.new("ShaderNodeTexCoord")
gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'; mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Location"].default_value = (0.5, 0.5, 0)
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.005, 0.01, 0.03, 1); cr.color_ramp.elements[1].color = (0.02, 0.08, 0.2, 1)
nt.links.new(tc.outputs["Generated"], mp.inputs[0]); nt.links.new(mp.outputs[0], gr.inputs[0]); nt.links.new(gr.outputs[1], cr.inputs[0])
nt.links.new(cr.outputs[0], em.inputs[0]); em.inputs[1].default_value = 1.0; nt.links.new(em.outputs[0], o_.inputs[0])
bp.data.materials.append(bm_)
# camera: ortho side view (from +X looking -X), face to the left of the frame
cam2 = bpy.data.objects.new("ScanCam", bpy.data.cameras.new("ScanCam")); S2.collection.objects.link(cam2); S2.camera = cam2
cam2.data.type = 'ORTHO'; cam2.data.ortho_scale = 0.62
cam2.location = (1.0, (hy0 + hy1) / 2 + 0.07, hz1 - 0.2); cam2.rotation_euler = (R_(90), 0, R_(90))
S2.render.image_settings.file_format = 'PNG'; S2.render.filepath = HERE + "assets/brain_scan.png"
with bpy.context.temp_override(scene=S2):
    bpy.ops.render.render(write_still=True, scene=S2.name)
print("GRAPHICS_DONE")
