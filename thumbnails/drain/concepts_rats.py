"""$25M Drain thumbnail v2: the diamond on a stack of bricks in a black drain, rats in the shadows."""
import math
import bpy
from mathutils import Vector
from common import area_light, point_at


def _spot(name, loc, tgt, energy, color, deg=10, blend=0.3, soft=0.01):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color
    l.spot_size = math.radians(deg); l.spot_blend = blend; l.shadow_soft_size = soft
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt)
    return o


def setup(c):
    from kit import haze
    import sc_tdrain as S
    t = c["diamond"].location.copy()
    gem = bpy.data.collections.new("GemOnly"); bpy.context.scene.collection.children.link(gem)
    gem.objects.link(c["diamond"]); gem.hide_render = False
    def only_gem(o):                                  # light linking: these lights and softboxes touch the stone only
        o.light_linking.receiver_collection = gem
    s = bpy.context.scene; s.cycles.max_bounces = 16; s.cycles.transmission_bounces = 16; s.cycles.glossy_bounces = 12
    s.cycles.caustics_refractive = True; s.cycles.caustics_reflective = True
    # one narrow hard beam straight down through a gap above, onto the stone and the top brick
    S_ = t + Vector((0.05, 0.25, 2.2))
    _spot("Beam", S_, t, 2200, (1.0, 0.96, 0.88), 13, 0.12, 0.003)
    # a street grate above: the beam falls through its slots, striping the stack and floor and making shafts in the haze
    from kit import box, pbr
    gm = pbr("GrateIron", (0.02, 0.018, 0.016), 0.6)
    gz = t.z + 1.05; f_ = (gz - t.z) / (S_.z - t.z); P = t + (S_ - t) * f_
    for k in range(-6, 7):
        b_ = box(f"GrateBar{k}", (P.x, P.y + 0.032 + k * 0.064, gz), (0.9, 0.022, 0.03), gm); b_.visible_camera = False
    for k in range(-2, 3):
        b_ = box(f"GrateRib{k}", (P.x + 0.09 + k * 0.18, P.y, gz + 0.02), (0.03, 0.9, 0.012), gm); b_.visible_camera = False
    haze(Vector((P.x, P.y, (gz + 0.0) / 2 + 0.02)), (0.9, 0.9, gz), density=0.035, color=(0.95, 0.95, 1.0), anis=0.55)
    # tiny hard glint sources around the stone for fire in the facets
    for k, (dx, dy, dz, e) in enumerate(((-0.35, -0.5, 0.35, 6), (0.4, -0.45, 0.25, 5), (0.0, -0.7, 0.1, 4), (0.25, 0.3, 0.45, 5))):
        l = bpy.data.lights.new(f"Glint{k}", 'AREA'); l.energy = e * 4; l.size = 0.05
        o = bpy.data.objects.new(f"Glint{k}", l); bpy.context.collection.objects.link(o); o.location = t + Vector((dx, dy, dz)); point_at(o, t)
        o.visible_camera = False; o.visible_volume_scatter = False; only_gem(o)
    # a faint cold light down the tunnel so the bricks and wet floor just read; rim on the rats
    # no back light (it lit a pale square behind the stack); a soft cold fill grazing the walls from each side
    for sx in (-1, 1):
        sd = area_light(t + Vector((0.7 * sx, -0.5, 0.6)), (0, 0, 0), 0.6, 1.0, (0.6, 0.72, 0.9))
        point_at(sd, t + Vector((-0.1 * sx, 0.2, -0.2))); sd.visible_volume_scatter = False; sd.visible_camera = False
    # dim cold fill from behind and above (hidden from the camera, so no glowing square)
    bk = area_light(t + Vector((0.0, 2.2, 0.9)), (0, 0, 0), 1.5, 4.0, (0.55, 0.68, 0.88)); point_at(bk, t + Vector((0, 0, -0.2)))
    bk.visible_camera = False
    top = area_light(t + Vector((0.0, 0.3, 1.4)), (0, 0, 0), 2.0, 3.0, (0.6, 0.7, 0.85)); point_at(top, t + Vector((0, 0.3, -0.3)))
    top.visible_camera = False
    haze(t + Vector((0, 1.8, 0.5)), (3.0, 3.0, 2.0), density=0.005, color=(0.85, 0.9, 1.0), anis=0.6)
    # rats: a cold rim from behind each one (linked to that rat only) so the silhouettes read in the dark
    import ph
    for k, (r, ms) in enumerate(c.get("rats", [])):
        lo, hi = ph.bounds(ms); cen = (lo + hi) / 2
        col = bpy.data.collections.new(f"Rat{k}"); bpy.context.scene.collection.children.link(col)
        for m in ms:
            if m.type == 'MESH':
                col.objects.link(m)
        away = (cen - t); away.z = 0; away.normalize()
        l = bpy.data.lights.new(f"RatRim{k}", 'AREA'); l.energy = 5; l.size = 0.25; l.color = (0.65, 0.78, 0.95)
        o = bpy.data.objects.new(f"RatRim{k}", l); bpy.context.collection.objects.link(o)
        o.location = cen + away * 0.35 + Vector((0, 0.25, 0.3)); point_at(o, cen)
        o.visible_volume_scatter = False; o.light_linking.receiver_collection = col
    # a faint cold glow far down the tunnel, for depth
    # tiny dim lamps far down the tunnel: soft out-of-focus blobs for depth, no big glow
    for k, (x, y, z, e) in enumerate(((-0.45, 3.4, 0.55, 8), (0.45, 3.6, 0.6, 7), (0.0, 4.6, 0.45, 6))):
        l = bpy.data.lights.new(f"Far{k}", 'POINT'); l.energy = e; l.shadow_soft_size = 0.03; l.color = (0.75, 0.82, 0.95)
        o = bpy.data.objects.new(f"Far{k}", l); bpy.context.collection.objects.link(o); o.location = t + Vector((x, y, z))
    # little white softboxes around the stone, seen only in its reflections/refractions, so the facets blaze
    em = bpy.data.materials.new("Softbox"); em.use_nodes = True
    N = em.node_tree.nodes; [N.remove(n) for n in list(N) if n.type != 'OUTPUT_MATERIAL']
    e_ = N.new("ShaderNodeEmission"); e_.inputs['Strength'].default_value = 90
    em.node_tree.links.new(e_.outputs[0], next(n for n in N if n.type == 'OUTPUT_MATERIAL').inputs['Surface'])
    import random
    rnd = random.Random(4)
    for k in range(14):
        th = rnd.uniform(0, 2 * math.pi); ph_ = rnd.uniform(0.15, 1.2); r = rnd.uniform(0.12, 0.22)
        p = t + Vector((r * math.cos(th) * math.cos(ph_), r * math.sin(th) * math.cos(ph_), r * math.sin(ph_)))
        bpy.ops.mesh.primitive_plane_add(size=rnd.uniform(0.012, 0.03), location=p); pl = bpy.context.active_object
        point_at(pl, t); pl.rotation_euler.rotate_axis('X', math.pi); pl.data.materials.append(em)
        pl.visible_camera = False; pl.visible_volume_scatter = False; pl.visible_shadow = False; only_gem(pl)
    s.view_settings.exposure = 0.0


def cam(c):
    t = c["diamond"].location
    return (t + Vector((0.04, -1.0, 0.0)), t + Vector((0.0, 0.3, -0.06)), 50)


def stone(c):
    return [c["diamond"]]


CONCEPTS = {
    "dd_rats": dict(scene="tdrain", cam=cam, focus=lambda c: c["diamond"].location, fstop=2.0, setup=setup, exposure=0.0,
                    shift=(0.0, 0.1), mask=stone),
}
