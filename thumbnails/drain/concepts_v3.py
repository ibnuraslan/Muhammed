"""$25M Drain v3 ideas: (3) split, jeweller's velvet left / drain right;  (1) looking down a street drain grate at night."""
import math, random
import bpy
from mathutils import Vector
from common import area_light, point_at


def _spot(name, loc, tgt, energy, color, deg=10, blend=0.3, soft=0.01):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color
    l.spot_size = math.radians(deg); l.spot_blend = blend; l.shadow_soft_size = soft
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt)
    return o


def gem_fire(d, n=14, strength=90, seed=4):
    """Light-linked glints and hidden softboxes: they show only in the stone's facets."""
    t = d.location.copy()
    gem = bpy.data.collections.new("GemOnly"); bpy.context.scene.collection.children.link(gem); gem.objects.link(d)
    s = bpy.context.scene; s.cycles.max_bounces = 16; s.cycles.transmission_bounces = 16; s.cycles.glossy_bounces = 12
    for k, (dx, dy, dz, e) in enumerate(((-0.35, -0.5, 0.35, 6), (0.4, -0.45, 0.25, 5), (0.0, -0.7, 0.1, 4), (0.25, 0.3, 0.45, 5))):
        l = bpy.data.lights.new(f"Glint{k}", 'AREA'); l.energy = e * 4; l.size = 0.05
        o = bpy.data.objects.new(f"Glint{k}", l); bpy.context.collection.objects.link(o); o.location = t + Vector((dx, dy, dz)); point_at(o, t)
        o.visible_camera = False; o.light_linking.receiver_collection = gem
    em = bpy.data.materials.new("Softbox"); em.use_nodes = True
    N = em.node_tree.nodes; [N.remove(x) for x in list(N) if x.type != 'OUTPUT_MATERIAL']
    e_ = N.new("ShaderNodeEmission"); e_.inputs['Strength'].default_value = strength
    em.node_tree.links.new(e_.outputs[0], next(x for x in N if x.type == 'OUTPUT_MATERIAL').inputs['Surface'])
    rnd = random.Random(seed)
    for k in range(n):
        th = rnd.uniform(0, 2 * math.pi); ph_ = rnd.uniform(0.15, 1.2); r = rnd.uniform(0.12, 0.22)
        p = t + Vector((r * math.cos(th) * math.cos(ph_), r * math.sin(th) * math.cos(ph_), r * math.sin(ph_)))
        bpy.ops.mesh.primitive_plane_add(size=rnd.uniform(0.012, 0.03), location=p); pl = bpy.context.active_object
        point_at(pl, t); pl.rotation_euler.rotate_axis('X', math.pi); pl.data.materials.append(em)
        pl.visible_camera = False; pl.visible_shadow = False; pl.light_linking.receiver_collection = gem
    return gem


# ---------------------------------------------------------------- (3) left half: the jeweller's display
def setup_velvet(c):
    d = c["diamond"]; t = d.location.copy(); gem_fire(d)
    _spot("Key", t + Vector((0.0, -0.6, 1.6)), t, 900, (1.0, 0.98, 0.95), 16, 0.4, 0.02)
    _spot("RimL", t + Vector((-0.9, 0.7, 0.6)), t, 300, (0.75, 0.85, 1.0), 20, 0.4, 0.05)
    _spot("RimR", t + Vector((0.9, 0.7, 0.6)), t, 300, (0.75, 0.85, 1.0), 20, 0.4, 0.05)
    _spot("Pool", t + Vector((0.0, 1.1, 1.5)), Vector((0, 1.4, 0.3)), 700, (0.55, 0.65, 1.0), 38, 0.9, 0.05)   # grazes the bricks   # glow on the backdrop
    f = area_light(t + Vector((0, -1.2, 0.3)), (0, 0, 0), 1.0, 6, (0.8, 0.85, 1.0)); point_at(f, t); f.visible_camera = False
    # dust in the air so the key reads as a beam
    from kit import haze
    hz = haze(t + Vector((0, -0.28, 0.75)), (0.32, 0.32, 1.5), density=0.035, color=(0.92, 0.94, 1.0), anis=0.5)   # only the key's column
    hz.rotation_euler = (math.atan2(0.6, 1.6), 0, 0)
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name != "Key":
            o.visible_volume_scatter = False
    _spot("Edge", t + Vector((0.0, 0.5, 0.25)), t + Vector((0, 0, -0.08)), 120, (1.0, 0.35, 0.25), 25, 0.6, 0.05)   # a red kiss on the cushion's back edge


def cam_velvet(c):
    t = c["diamond"].location
    return (t + Vector((0.04, -1.05, 0.05)), t + Vector((0.0, 0.3, -0.11)), 42)


# ---------------------------------------------------------------- (1) down the drain
def setup_grate(c):
    import sc_tdrain2 as G
    from kit import haze
    d = c["diamond"]; t = d.location.copy(); gem_fire(d, strength=60)
    s = bpy.context.scene; s.cycles.volume_bounces = 0
    # the flashlight: from just behind the camera, down through the bars; its bar shadows fall across the water and stone
    _spot("Torch", Vector((0.08, -0.22, 1.15)), t, 700, (1.0, 0.95, 0.85), 16, 0.35, 0.012)
    # the street: a sodium lamp, wet asphalt sheen, a cold sky bounce
    _spot("Sodium", Vector((-2.2, 1.8, 3.2)), Vector((0, 0, 0)), 6000, (1.0, 0.62, 0.28), 45, 0.8, 0.3)
    sky = area_light(Vector((1.5, 2.5, 2.5)), (0, 0, 0), 3.0, 8, (0.45, 0.55, 0.85)); point_at(sky, Vector((0, 0, 0))); sky.visible_camera = False
    haze(Vector((0, 0.2, -G.DEPTH / 2)), (G.GW + 0.5, G.GL + 0.9, G.DEPTH), density=0.25, color=(0.9, 0.92, 1.0), anis=0.5)
    # rats: rim from inside the shaft
    import ph
    for k, (r, ms) in enumerate(c.get("rats", [])):
        lo, hi = ph.bounds(ms); cen = (lo + hi) / 2
        col = bpy.data.collections.new(f"Rat{k}"); bpy.context.scene.collection.children.link(col)
        for m in ms:
            if m.type == 'MESH':
                col.objects.link(m)
        l = bpy.data.lights.new(f"RatRim{k}", 'AREA'); l.energy = 6; l.size = 0.2; l.color = (0.7, 0.8, 1.0)
        o = bpy.data.objects.new(f"RatRim{k}", l); bpy.context.collection.objects.link(o)
        o.location = cen + Vector((0, 0.3, 0.25)); point_at(o, cen); o.light_linking.receiver_collection = col


def cam_grate(c):
    return ((0.0, -0.42, 0.88), (0.0, 0.1, -0.62), 28)


CONCEPTS = {
    "dd_velvet": dict(scene="tdrain2", variant="velvet", cam=cam_velvet, focus=lambda c: c["diamond"].location, fstop=2.8,
                      setup=setup_velvet, shift=(0.0, 0.1), mask=lambda c: [c["diamond"]]),
    "dd_grate": dict(scene="tdrain2", variant="grate", cam=cam_grate, focus=lambda c: c["diamond"].location, fstop=5.6,
                     setup=setup_grate, shift=(0.0, 0.0), mask=lambda c: [c["diamond"]]),
}
