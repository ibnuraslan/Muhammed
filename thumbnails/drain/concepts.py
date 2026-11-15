"""$25M Drain thumbnail: a police evidence photo. Looking down at the drilled-open patch beside the rainwater grate,
the grimy tub out of the hole with the rings inside and the big diamond on top; yellow numbered evidence markers, a
forensic scale, a hard on-camera flash. Built from the film's own yard (claude/drain-diamond: sc_drain.py)."""
import math, os
import bpy
from mathutils import Vector
from common import point_at

HERE = os.path.dirname(os.path.abspath(__file__))


def _S():
    import sc_drain as S
    return S


def ruler_image(path):
    from PIL import Image, ImageDraw, ImageFont
    W_, H_ = 2000, 140
    im = Image.new("RGB", (W_, H_), (238, 236, 228)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 34)
    for k in range(0, 41):                                     # 20 cm, a tick every 5 mm, numbers every cm
        x = 40 + k * (W_ - 80) / 40
        L = 70 if k % 2 == 0 else 38
        d.line([(x, 0), (x, L)], fill=(15, 15, 15), width=5 if k % 2 == 0 else 3)
        if k % 2 == 0 and 0 < k < 40:
            d.text((x - 10 if k < 20 else x - 18, 78), str(k // 2), font=f, fill=(15, 15, 15))
    for k in range(0, 10):                                     # black/white checks along the bottom edge
        if k % 2 == 0:
            d.rectangle([40 + k * (W_ - 80) / 10, H_ - 18, 40 + (k + 1) * (W_ - 80) / 10, H_], fill=(15, 15, 15))
    im.save(path); return path


def marker(num, loc, rot_z, mat_y, mat_k):
    """A folded yellow evidence tent (two plates leaning together) with a black number on the face toward camera."""
    import bmesh
    w, hgt, lean = 0.10, 0.11, 0.032
    verts = [(-w / 2, -lean, 0), (w / 2, -lean, 0), (w / 2, 0, hgt), (-w / 2, 0, hgt), (-w / 2, lean, 0), (w / 2, lean, 0)]
    me = bpy.data.meshes.new(f"Tent{num}"); me.from_pydata(verts, [], [(0, 1, 2, 3), (3, 2, 5, 4)]); me.update()
    o = bpy.data.objects.new(f"Marker{num}", me); bpy.context.collection.objects.link(o); me.materials.append(mat_y)
    o.modifiers.new("thick", 'SOLIDIFY').thickness = 0.003
    o.location = loc; o.rotation_euler.z = rot_z
    bpy.ops.object.text_add(location=(0, 0, 0)); t = bpy.context.active_object
    t.data.body = str(num); t.data.size = 0.07; t.data.align_x = 'CENTER'; t.data.align_y = 'CENTER'
    t.data.font = bpy.data.fonts.load("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", check_existing=True)
    t.data.materials.append(mat_k)
    ang = math.atan2(hgt, lean)                              # the front plate's slope
    t.parent = o; t.location = (0, -lean / 2 - 0.0035, hgt / 2); t.rotation_euler = (ang, 0, 0)
    return o


def setup(c):
    from kit import pbr
    S = _S()
    for o in bpy.data.objects:                                 # no people, no rain sheets
        if o.name.startswith("Stand"):
            o.hide_render = True
        if o.type == 'MESH' and any(m and m.name.startswith("Rain") for m in o.data.materials):
            o.hide_render = True
    # cut a real hole through the slab where the patch was, a muddy floor in it, and set the tub down inside
    slab = bpy.data.objects.get("YardSlab")
    hx, hy = S.PATCH_SIZE[0] - 0.08, S.PATCH_SIZE[1] - 0.08
    bpy.ops.mesh.primitive_cube_add(size=1, location=S.PATCH); cut = bpy.context.active_object; cut.scale = (hx, hy, 0.4)
    cut.hide_render = True; cut.hide_viewport = True
    if slab:
        bm_ = slab.modifiers.new("hole", 'BOOLEAN'); bm_.operation = 'DIFFERENCE'; bm_.object = cut
    for o in bpy.data.objects:
        if o.name.startswith("Hole"):
            o.hide_render = True
    mud = pbr("HoleMud", (0.03, 0.024, 0.018), 0.8)
    bpy.ops.mesh.primitive_plane_add(size=1, location=S.PATCH + Vector((0, 0, -0.095))); fl_ = bpy.context.active_object
    fl_.scale = (hx + 0.02, hy + 0.02, 1); fl_.data.materials.append(mud)
    tub = c["box"]; old = tub.location.copy()
    new = S.PATCH + Vector((0.02, 0.0, -0.095 + S.CONT_SIZE[2] / 2))
    d = new - old
    tops = [o for o in bpy.data.objects if o.parent is None and o.name.startswith(("Ring", "Ear", "HeroRing"))]
    tub.location = new
    for o in tops:
        o.location += d
    c["tub_at"] = new
    for o in bpy.data.objects:                                   # the film's sparkle lights follow the tub
        if o.type == 'LIGHT' and o.name.startswith("Spark"):
            o.location += d
    # the big stone on top of the pile, a touch larger so it reads in a thumbnail
    h = c["hero"]; h.scale = tuple(v * 2.4 for v in h.scale); h.location.z += 0.012
    g = c["glint"]; hp = h.matrix_world.translation
    g.location = hp + Vector((0.12, -0.3, 0.4)); point_at(g, hp); g.data.energy = 10
    my = pbr("TentYellow", (0.92, 0.66, 0.02), 0.45); mk = pbr("TentBlack", (0.01, 0.01, 0.01), 0.5)
    marker(1, S.PATCH + Vector((-0.27, -0.13, 0)), 0.35, my, mk)
    marker(2, S.PATCH + Vector((0.27, -0.06, 0)), -0.25, my, mk)
    marker(3, S.DRAIN + Vector((-0.22, -0.2, 0)), 0.1, my, mk)
    # forensic scale along the tub
    rm = bpy.data.materials.new("Ruler"); rm.use_nodes = True
    t = rm.node_tree.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(ruler_image(os.path.join(HERE, "plates", "ruler.png")))
    rm.node_tree.links.new(t.outputs[0], rm.node_tree.nodes["Principled BSDF"].inputs['Base Color'])
    rm.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.5
    bpy.ops.mesh.primitive_plane_add(size=1, location=S.PATCH + Vector((-0.02, -0.235, 0.003)))
    r = bpy.context.active_object; r.name = "Ruler"; r.scale = (0.2, 0.014, 1); r.rotation_euler.z = 0.0; r.data.materials.append(rm)
    # the evidence flash: hard, small, from just above the lens; the ambient way down
    s = bpy.context.scene; s.view_settings.exposure = -1.3
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name not in ("Glint",) and not o.name.startswith("Spark"):
            o.data.energy *= 0.12
    w = bpy.context.scene.world
    if w and w.node_tree:
        for n in w.node_tree.nodes:
            if n.type == 'BACKGROUND':
                n.inputs['Strength'].default_value *= 0.3
    loc, tgt, _ = cam(c)
    fl = bpy.data.lights.new("EvidenceFlash", 'AREA'); fl.size = 0.08; fl.energy = 45; fl.color = (0.97, 0.98, 1.0)
    fo = bpy.data.objects.new("EvidenceFlash", fl); bpy.context.collection.objects.link(fo)
    fo.location = Vector(loc) + Vector((0.05, 0.0, 0.12)); point_at(fo, tgt); fo.visible_camera = False


def cam(c):
    S = _S()
    mid = S.PATCH + Vector((0.08, 0.0, 0))
    return (mid + Vector((0.03, -0.42, 0.78)), mid + Vector((0.0, 0.05, -0.04)), 30)


def stone(c):
    h = c["hero"]
    return [o for o in [h] + list(h.children_recursive) if o.type == 'MESH']


CONCEPTS = {
    "dd_evidence": dict(scene="drain", variant="open", cam=cam, focus=lambda c: _S().PATCH + Vector((0, 0, -0.03)), fstop=5.6,
                        setup=setup, exposure=-0.9, shift=(0.0, 0.1), mask=stone),
}
