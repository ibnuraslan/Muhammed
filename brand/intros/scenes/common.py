import bpy, json, math, os, random
from mathutils import Vector
D = os.path.dirname(os.path.abspath(__file__))
POLYS = json.load(open(os.path.join(D, "logo_polys.json")))
LOGO_PNG = os.path.join(D, "logo.png")
YEL = (0.62, 0.85, 0.0, 1)

def reset(res=(1600, 900), samples=64):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.volume_step_rate = 2.0
    sc.cycles.max_bounces = 6
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.fps = 24
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    return sc

def world(color, strength):
    n = bpy.context.scene.world.node_tree.nodes["Background"]
    n.inputs[0].default_value = (*color, 1); n.inputs[1].default_value = strength

def mat(name, color=(0.5,0.5,0.5,1), rough=0.5, metal=0.0, emit=None, estr=0.0, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = color
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = emit
        p.inputs["Emission Strength"].default_value = estr
    return m

def noise_bump(m, scale=40.0, strength=0.15, rough_var=None):
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 12
    b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = strength
    nt.links.new(n.outputs["Fac"], b.inputs["Height"]); nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    if rough_var:
        r = nt.nodes.new("ShaderNodeMapRange")
        r.inputs[3].default_value, r.inputs[4].default_value = rough_var
        nt.links.new(n.outputs["Fac"], r.inputs[0]); nt.links.new(r.outputs[0], p.inputs["Roughness"])
    return m

def color_noise(m, c1, c2, scale=8.0):
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 10
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].color = c1; r.color_ramp.elements[1].color = c2
    nt.links.new(n.outputs["Fac"], r.inputs[0]); nt.links.new(r.outputs[0], p.inputs["Base Color"])
    return m

def _curve(name, polys, depth, bevel=0.0):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
    cu.extrude = depth; cu.bevel_depth = bevel; cu.bevel_resolution = 2
    for poly in polys:
        sp = cu.splines.new('POLY'); sp.points.add(len(poly) - 1)
        for i, (x, y) in enumerate(poly): sp.points[i].co = (x, y, 0, 1)
        sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    return ob

def logo(width=4.0, depth=0.15, loc=(0,0,0), rot=(math.radians(90),0,0), fill_mat=None, edge_mat=None,
         fill_raise=0.02, as_mesh=True):
    """Physical 3D logo: dark outline slab + yellow fill letters raised in front. Origin at centre of the art."""
    fill_mat = fill_mat or mat("LogoFill", YEL, 0.35)
    edge_mat = edge_mat or mat("LogoEdge", (0.02,0.02,0.015,1), 0.5)
    s = _curve("LogoEdge", POLYS["sil"], depth / width)
    f = _curve("LogoFill", POLYS["fill"], depth / width + fill_raise / width)
    s.data.materials.append(edge_mat); f.data.materials.append(fill_mat)
    par = bpy.data.objects.new("Logo", None); bpy.context.collection.objects.link(par)
    for o in (s, f):
        o.parent = par
    par.scale = (width, width, width); par.location = loc; par.rotation_euler = rot
    return par

def logo_mesh_objects():
    return [o for o in bpy.data.objects if o.name.startswith("LogoEdge") or o.name.startswith("LogoFill")]

def image_mat(name, path=LOGO_PNG, emit=0.0, base=None, rough=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.extension = 'CLIP'
    nt.links.new(t.outputs["Color"], p.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
    p.inputs["Roughness"].default_value = rough
    if emit:
        nt.links.new(t.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    return m, t

def plane(name, size, loc=(0,0,0), rot=(0,0,0), m=None, sx=1, sy=1):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (sx, sy, 1)
    if m: o.data.materials.append(m)
    return o

def box(name, dims, loc, m=None, rot=(0,0,0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = dims
    if bevel:
        bpy.ops.object.transform_apply(scale=True)
        b = o.modifiers.new("b", 'BEVEL'); b.width = bevel; b.segments = 2
    if m: o.data.materials.append(m)
    return o

def cyl(name, r, h, loc, m=None, rot=(0,0,0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object; o.name = name
    bpy.ops.object.shade_smooth()
    if m: o.data.materials.append(m)
    return o

def look(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def camera(loc, target, lens=35, fstop=None, focus=None):
    c = bpy.data.cameras.new("Cam"); c.lens = lens; c.sensor_width = 36
    o = bpy.data.objects.new("Cam", c); bpy.context.collection.objects.link(o)
    o.location = loc; look(o, target); bpy.context.scene.camera = o
    if fstop:
        c.dof.use_dof = True; c.dof.aperture_fstop = fstop
        c.dof.focus_distance = focus or (Vector(target) - Vector(loc)).length
    return o

def light(kind, name, loc, target=None, energy=100, color=(1,1,1), size=0.1, spot=30, blend=0.15):
    l = bpy.data.lights.new(name, kind); l.energy = energy; l.color = color
    if kind in ('POINT', 'SPOT'): l.shadow_soft_size = size
    if kind == 'AREA': l.size = size
    if kind == 'SPOT': l.spot_size = math.radians(spot); l.spot_blend = blend
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc
    if target: look(o, target)
    return o

def fog(name, dims, loc, density=0.02, color=(0.8,0.85,0.9), aniso=0.3, noise=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name
    o.scale = dims
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = (*color, 1); v.inputs["Density"].default_value = density
    v.inputs["Anisotropy"].default_value = aniso
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    if noise:
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = noise; n.inputs["Detail"].default_value = 4
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.35; mr.inputs[2].default_value = 0.75
        mr.inputs[3].default_value = 0.0; mr.inputs[4].default_value = density * 2.2
        nt.links.new(n.outputs["Fac"], mr.inputs[0]); nt.links.new(mr.outputs[0], v.inputs["Density"])
    o.data.materials.append(m)
    return o

def text(body, size, loc, rot=(0,0,0), m=None, font=None, extrude=0.0, align='CENTER'):
    cu = bpy.data.curves.new("T", 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude
    cu.align_x = align; cu.align_y = 'CENTER'
    if font: cu.font = bpy.data.fonts.load(font)
    o = bpy.data.objects.new("T", cu); bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    if m: cu.materials.append(m)
    return o

def scatter(n, fn, seed=1):
    rnd = random.Random(seed)
    for i in range(n): fn(i, rnd)

def render(path):
    sc = bpy.context.scene; sc.render.filepath = path
    sc.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
