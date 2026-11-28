"""Romand film: procedural props, built in neutral greys (the world tint comes from the light). Every builder makes
its parts around the origin and returns a group empty (rk.group) you can move/turn; sizes are in metres.
RED accent props (cord, canister, rifle silhouette, rolling pin, petrol can, badge, ankle tag) use P['red']."""
import math, random, os
import bpy
from mathutils import Vector, Matrix
import rk
from rk import box, cyl, sphere, cone, group, M


def _beam_mat(name, color=(1.0, 0.85, 0.55), strength=0.25):
    """Fake visible light beam (no volumes): emission mixed with transparency, brightest along the axis."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"]); out = N["Material Output"]
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs['Blend'].default_value = 0.6
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    L.new(lw.outputs['Facing'], inv.inputs[1])
    pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.0; L.new(inv.outputs[0], pw.inputs[0])
    L.new(pw.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    m.blend_method = 'BLEND' if hasattr(m, "blend_method") else None
    return m


def beam(name, origin, direction, length=9.0, r_end=1.6, color=(1.0, 0.85, 0.55), strength=0.07):
    d = Vector(direction).normalized()
    c = Vector(origin) + d * length / 2
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r_end, radius2=0.06, depth=length, location=c, end_fill_type='NOTHING')
    o = bpy.context.active_object; o.name = name; o.data.materials.append(_beam_mat(name + "_m", color, strength))
    for p_ in o.data.polygons:
        p_.use_smooth = True
    o.rotation_euler = (-d).to_track_quat('Z', 'Y').to_euler()
    o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False
    return o


# ------------------------------------------------------------------------------------------------- car (1990s saloon)
def car(name="car", loc=(0, 0, 0), rz=0.0, boot=0.0, door_l=0.0, door_r=0.0, lights=True, dome=0.0, beams=True,
        brake=0.3):
    """A 1990s four-door saloon, facing +X. boot/door_* in 0..1 (open amount). dome = interior light energy (W).
    Returns dict(root, boot_lid, boot_floor (world pos), seats {driver, passenger}, head (world positions))."""
    P = M(); parts = []
    L, W = 4.45, 1.72
    body = box(name + "_body", (0, 0, 0.55), (L, W, 0.62), P["carpaint"], bevel=0.0); parts.append(body)
    import bmesh   # hollow tub: open top, 4 cm walls, so occupants' legs sit inside a cavity, not inside solid metal
    b = bmesh.new(); b.from_mesh(body.data); b.faces.ensure_lookup_table()
    bmesh.ops.delete(b, geom=[f for f in b.faces if f.normal.z > 0.9], context='FACES'); b.to_mesh(body.data); b.free()
    so = body.modifiers.new("shell", "SOLIDIFY"); so.thickness = 0.04; so.offset = -1
    bv = body.modifiers.new("bev", "BEVEL"); bv.width = 0.03; bv.segments = 2; bv.limit_method = 'ANGLE'
    parts.append(box(name + "_deck_f", (1.6, 0, 0.845), (1.25, W - 0.02, 0.03), P["carpaint"], bevel=0.01))
    parts.append(box(name + "_floor", (0, 0, 0.3), (L - 0.1, W - 0.1, 0.03), P["dark"]))
    # hood and boot decks a touch lower than the belt line
    parts.append(box(name + "_bumper_f", (L / 2 + 0.02, 0, 0.36), (0.12, W * 0.98, 0.18), P["rubber"], bevel=0.04))
    parts.append(box(name + "_bumper_r", (-L / 2 - 0.02, 0, 0.36), (0.12, W * 0.98, 0.18), P["rubber"], bevel=0.04))
    # greenhouse: tapered glass block + roof
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.15, 0, 1.12))
    gh = bpy.context.active_object; gh.name = name + "_glass"; gh.scale = (2.25, W * 0.92, 0.5)
    bpy.ops.object.transform_apply(scale=True)
    for v in gh.data.vertices:
        if v.co.z > 0:
            v.co.x *= 0.62; v.co.x -= 0.1; v.co.y *= 0.9
    gh.data.materials.append(P["glass"]); parts.append(gh)
    parts.append(box(name + "_roof", (-0.24, 0, 1.385), (1.42, W * 0.84, 0.05), P["carpaint"], bevel=0.02))
    for sx in (0.42, -0.25, -0.88):   # pillars
        for sy in (-1, 1):
            parts.append(box(name + "_pillar", (sx, sy * W * 0.44, 1.12), (0.06, 0.05, 0.5), P["carpaint"]))
    # wheels
    for wx in (1.38, -1.38):
        for wy in (-1, 1):
            w = cyl(name + "_tyre", (wx, wy * (W / 2 - 0.08), 0.31), (wx, wy * (W / 2 + 0.06), 0.31), 0.31, P["rubber"], 24)
            hub = cyl(name + "_hub", (wx, wy * (W / 2 + 0.06), 0.31), (wx, wy * (W / 2 + 0.07), 0.31), 0.18, P["chrome"], 16)
            parts += [w, hub]
    # interior: seats, dash, wheel
    seats = {}
    for nm, sy in (("driver", 0.38), ("passenger", -0.38)):
        parts.append(box(name + "_seat_" + nm, (0.0, sy, 0.62), (0.52, 0.5, 0.14), P["cloth"], bevel=0.03))
        parts.append(box(name + "_back_" + nm, (-0.28, sy, 0.98), (0.12, 0.48, 0.62), P["cloth"], bevel=0.03, rot=(0, math.radians(-12), 0)))
        seats[nm] = Vector((0.06, sy, 0.69))
    parts.append(box(name + "_rearseat", (-0.95, 0, 0.62), (0.5, 1.42, 0.14), P["cloth"], bevel=0.03))
    parts.append(box(name + "_dash", (0.72, 0, 0.92), (0.3, W * 0.88, 0.2), P["dark"], bevel=0.03))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.018, location=(0.5, 0.38, 1.0), rotation=(0, math.radians(70), 0))
    sw = bpy.context.active_object; sw.name = name + "_wheel"; sw.data.materials.append(P["dark"]); parts.append(sw)
    # lamps
    hl = []
    for sy in (-0.6, 0.6):
        parts.append(box(name + "_headlamp", (L / 2 - 0.01, sy, 0.62), (0.04, 0.34, 0.14), P["head"] if lights else P["chrome"]))
        parts.append(box(name + "_taillamp", (-L / 2 + 0.01, sy, 0.66), (0.04, 0.34, 0.12), P["tail"]))
        hl.append(Vector((L / 2 + 0.05, sy, 0.62)))
    # boot lid: hinged at the rear window base, swings up
    hinge = rk.empty(name + "_boot_hinge", (-1.32, 0, 0.88))
    lid = box(name + "_boot_lid", (-0.42, 0, 0.0), (0.86, W * 0.9, 0.05), P["carpaint"], bevel=0.02)
    lid.parent = hinge; hinge.rotation_euler.y = math.radians(85 * boot); parts.append(hinge)
    bf = box(name + "_boot_floor", (-1.78, 0, 0.5), (0.8, W * 0.82, 0.03), P["dark"]); parts.append(bf)
    parts.append(box(name + "_bootwall", (-1.36, 0, 0.6), (0.03, W - 0.1, 0.55), P["dark"]))
    if boot > 0.0:
        lamp = rk.point(name + "_bootlamp", (-1.5, 0, 0.84), 6.0, (1.0, 0.8, 0.5)); parts.append(lamp)
    if dome:
        parts.append(rk.point(name + "_dome", (-0.2, 0, 1.3), dome, (1.0, 0.85, 0.6), soft=0.2))
    # doors as panels that swing out (front doors)
    for side, amt in ((1, door_l), (-1, door_r)):
        if amt > 0:
            hh = rk.empty(name + "_door_hinge", (0.55, side * W / 2, 0.75))
            d = box(name + "_door", (-0.52, side * 0.02, 0.0), (1.05, 0.05, 0.62), P["carpaint"], bevel=0.02)
            d.parent = hh; hh.rotation_euler.z = math.radians(side * 60 * amt); parts.append(hh)
            # remove that body side panel: a hole where the open door was
            cut = box(name + "_door_cut", (0.02, side * W / 2, 0.75), (1.06, 0.3, 0.6), None)
            bo = body.modifiers.new("door", "BOOLEAN"); bo.object = cut; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
            cut.hide_render = True; cut.hide_viewport = True; parts.append(cut)
    root = group(name, parts, loc, rz)
    bpy.context.view_layer.update()
    mw = root.matrix_world
    out = dict(root=root, boot_lid=lid, boot_floor=mw @ Vector((-1.78, 0, 0.52)), head=[mw @ h for h in hl],
               seats={k: mw @ v for k, v in seats.items()}, fwd=(mw.to_3x3() @ Vector((1, 0, 0))).normalized())
    if lights:
        for i, h in enumerate(out["head"]):
            rk.spot(name + f"_hl{i}", h, h + out["fwd"] * 10 + Vector((0, 0, -0.9)), 900.0, (1.0, 0.9, 0.7), 50, 0.35, 0.05)
            if beams:
                beam(name + f"_beam{i}", h, out["fwd"] + Vector((0, 0, -0.08)), 9.0, 1.5)
    return out


# ------------------------------------------------------------------------------------------------- nature
# ------------------------------------------------------------------------------------------------- real trees (instanced)
TREE_SRC = {  # kind: (source, id, mesh-name filter) -- Poly Haven CC0 firs, Sketchfab CC-BY leafless trees
    "fir_a": ("ph", "fir_tree_01", "_c_LOD0"), "fir_b": ("ph", "fir_tree_01", "_b_LOD0"),
    "sap_a": ("ph", "fir_sapling_medium", "_a_LOD0"), "sap_b": ("ph", "fir_sapling_medium", "_c_LOD0"),
    "bare_a": ("sf", "4aed7a078d574e1f946a43c31ca16715", ""), "bare_b": ("sf", "09c2c4f4124a4603b37d92a330c89292", ""),
}
_TREES = {}


def _darken(m, k=0.32):
    """Keep the asset's textures and alpha, but dye it dark so trees read as silhouettes that catch the amber rim."""
    if not m.use_nodes or m.get("darkened"):
        return
    nt = m.node_tree; p = nt.nodes.get("Principled BSDF")
    if p is None:
        return
    src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs[7].default_value = (k, k * 0.95, k * 0.85, 1)
    if src is not None:
        nt.links.new(src, mx.inputs[6])
    else:
        mx.inputs[6].default_value = p.inputs['Base Color'].default_value
    nt.links.new(mx.outputs[2], p.inputs['Base Color'])
    m["darkened"] = 1


def _fix_alpha(aid, objs):
    """Poly Haven glTFs ship the leaf/twig colour as JPG; fetch the separate <part>_alpha map and wire it to Alpha."""
    import ph, os
    files = ph._files(aid)
    for o in objs:
        for m in o.data.materials:
            if m is None or m.get("alpha_fixed"):
                continue
            part = m.name.replace(aid + "_", "")
            key = part + "_alpha"
            if key not in files:
                continue
            info = files[key]["1k"]; fmt = "png" if "png" in info else list(info.keys())[0]
            url = info[fmt]["url"]
            path = ph._get(url, os.path.join(ph.ROOT, aid, "textures", os.path.basename(url)))
            nt = m.node_tree; p = nt.nodes["Principled BSDF"]
            tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(path, check_existing=True)
            tex.image.colorspace_settings.name = 'Non-Color'
            uv = None
            for n in nt.nodes:
                if n.type == 'TEX_IMAGE' and n is not tex and n.inputs['Vector'].links:
                    uv = n.inputs['Vector'].links[0].from_socket; break
            if uv is not None:
                nt.links.new(uv, tex.inputs['Vector'])
            nt.links.new(tex.outputs['Color'], p.inputs['Alpha'])
            m["alpha_fixed"] = 1


TREE_LIB = os.environ.get("TREE_LIB", "")     # farm mode: link the tree collections from this shared .blend


def _tree_coll(kind):
    """Load one tree variant once into a hidden collection, base at the origin; returns (collection, height).
    With TREE_LIB set (farm packaging) the collection is LINKED from the shared lib/trees.blend instead, so every
    shot file references one copy of the heavy tree meshes."""
    if kind in _TREES and _TREES[kind][0].name in bpy.data.collections:
        return _TREES[kind]
    if TREE_LIB:
        with bpy.data.libraries.load(TREE_LIB, link=True) as (src_, dst_):
            dst_.collections = ["tree_" + kind]
        col = dst_.collections[0]
        _TREES[kind] = (col, float(col.get("height", 6.0)) if hasattr(col, "get") else 6.0)
        return _TREES[kind]
    src, aid, filt = TREE_SRC[kind]
    before = set(bpy.data.objects)
    if src == "ph":
        import ph
        bpy.ops.import_scene.gltf(filepath=ph.fetch_model(aid, "1k"))
    else:
        import sf
        bpy.ops.import_scene.gltf(filepath=sf.fetch(aid))
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    keep = [o for o in new if o.type == 'MESH' and filt in o.name]
    if src == "sf":     # drop ground patches / bases that come with some tree scans (flat, wide meshes)
        def _hz(o):
            zs = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]
            return max(zs) - min(zs)
        H = max(_hz(o) for o in keep)
        keep = [o for o in keep if _hz(o) > 0.15 * H]
    col = bpy.data.collections.new("tree_" + kind)
    for o in keep:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in keep for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for o in keep:
        o.matrix_world = Matrix.Translation(-base) @ o.matrix_world
        for us in list(o.users_collection):
            us.objects.unlink(o)
        col.objects.link(o)
        for m in o.data.materials:
            if m:
                _darken(m, 0.12 if src == "sf" else 1.0)
    if src == "ph":
        _fix_alpha(aid, keep)
    for o in new:
        if o not in keep and o.name in bpy.data.objects:
            bpy.data.objects.remove(o)
    col["height"] = hi.z - lo.z
    _TREES[kind] = (col, hi.z - lo.z)
    return _TREES[kind]


def tree(name, kind, loc, h, rz=0.0):
    col, h0 = _tree_coll(kind)
    o = bpy.data.objects.new(name, None); o.instance_type = 'COLLECTION'; o.instance_collection = col
    bpy.context.scene.collection.objects.link(o)
    s = h / h0; o.scale = (s, s, s); o.location = loc; o.rotation_euler.z = rz
    return o


def pine(name, loc, h=7.0, seed=0):
    rng = random.Random(seed)
    kind = rng.choice(["fir_a", "fir_b", "fir_b", "sap_a", "sap_b", "sap_b"])
    return tree(name, kind, loc, h * rng.uniform(0.9, 1.15), rng.uniform(0, 6.28))


def bare_tree(name, loc, h=6.0, seed=0):
    rng = random.Random(seed)
    return tree(name, rng.choice(["bare_a", "bare_a", "bare_b"]), loc, h * rng.uniform(0.9, 1.15), rng.uniform(0, 6.28))


def bush(name, loc, r=0.5, seed=0):
    P = M(); rng = random.Random(seed)
    o = sphere(name, (0, 0, r * 0.3), r, P["foliage"], (1.0, rng.uniform(0.8, 1.2), 0.45), seg=16)
    return group(name, [o], loc)


# ------------------------------------------------------------------------------------------------- buildings
def window(name, c, w, h, normal_axis="y", lit=False, sign=1):
    """A window on a wall face: dark glass or warm lit pane, with a frame. normal along ±x or ±y."""
    P = M(); m = P["win"] if lit else P["dark"]
    if normal_axis == "y":
        pane = box(name, c, (w, 0.04, h), m)
        fr = [box(name + "_f", (c[0], c[1] + sign * 0.03, c[2] + h / 2), (w + 0.08, 0.05, 0.05), P["light"]),
              box(name + "_f", (c[0], c[1] + sign * 0.03, c[2] - h / 2), (w + 0.12, 0.08, 0.06), P["light"]),
              box(name + "_f", (c[0], c[1] + sign * 0.03, c[2]), (0.04, 0.05, h), P["light"])]
    else:
        pane = box(name, c, (0.04, w, h), m)
        fr = [box(name + "_f", (c[0] + sign * 0.03, c[1], c[2] + h / 2), (0.05, w + 0.08, 0.05), P["light"]),
              box(name + "_f", (c[0] + sign * 0.03, c[1], c[2] - h / 2), (0.08, w + 0.12, 0.06), P["light"]),
              box(name + "_f", (c[0] + sign * 0.03, c[1], c[2]), (0.05, 0.04, h), P["light"])]
    return [pane] + fr


def gable_house(name, loc=(0, 0, 0), rz=0.0, w=9.0, d=7.0, h=5.2, roof=2.6, lit=(), door_lit=False, snow=False,
                floors=2, chimney=True):
    """A two-storey pitched-roof house (Pays de Gex / Jura style), front facing -Y. lit: indices of lit windows."""
    P = M(); parts = []
    parts.append(box(name + "_walls", (0, 0, h / 2), (w, d, h), P["light"], bevel=0.02))
    # roof: two slabs
    ang = math.atan2(roof, d / 2); sl = math.hypot(roof, d / 2) + 0.3
    for s in (-1, 1):
        r = box(name + "_roof", (0, s * d / 4, h + roof / 2), (w + 0.6, sl, 0.16), P["snow"] if snow else P["grey"],
                rot=(s * -ang, 0, 0) if True else (0, 0, 0))
        r.rotation_euler = (-s * ang, 0, 0); parts.append(r)      # both slabs rise to the ridge
    # gable fill
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=1, radius2=0, depth=1, location=(0, 0, 0))
    gb = bpy.context.active_object
    me = bpy.data.meshes.new(name + "_gable")
    vs = [(-w / 2, -d / 2, h), (-w / 2, d / 2, h), (-w / 2, 0, h + roof), (w / 2, -d / 2, h), (w / 2, d / 2, h), (w / 2, 0, h + roof)]
    me.from_pydata(vs, [], [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1)]); me.update()
    bpy.data.objects.remove(gb)
    go = bpy.data.objects.new(name + "_gable", me); bpy.context.scene.collection.objects.link(go); me.materials.append(P["light"])
    parts.append(go)
    if chimney:
        parts.append(box(name + "_chimney", (w * 0.28, d * 0.15, h + roof * 0.8), (0.5, 0.5, 1.4), P["grey"]))
    k = 0
    per = 3
    for fl in range(floors):
        z = 1.35 + fl * 2.5
        for i in range(per):
            x = -w / 2 + w * (i + 0.5) / per
            if fl == 0 and i == 1:
                parts.append(box(name + "_door", (x, -d / 2 - 0.02, 1.05), (1.0, 0.06, 2.1), P["win"] if door_lit else P["wood"]))
                parts.append(box(name + "_step", (x, -d / 2 - 0.35, 0.08), (1.6, 0.7, 0.16), P["grey"]))
                continue
            parts += window(name + f"_w{k}", (x, -d / 2 - 0.01, z), 1.1, 1.3, "y", lit=(k in lit), sign=-1); k += 1
    # back and side windows (dark)
    for fl in range(floors):
        for i in range(2):
            parts += window(name + f"_sw{fl}{i}", (w / 2 + 0.01, -d / 4 + i * d / 2, 1.35 + fl * 2.5), 1.0, 1.2, "x", lit=False, sign=1)
    return group(name, parts, loc, rz)


def slab_block(name, loc, w, d, h, rows, cols, lit_frac=0.2, seed=0, rz=0.0, mat_key="grey", pilotis=0.0):
    """An apartment / office block: box with a grid of windows on the -Y face, some lit."""
    P = M(); rng = random.Random(seed); parts = [box(name + "_body", (0, 0, pilotis + h / 2), (w, d, h), P[mat_key], bevel=0.02)]
    if pilotis:
        for i in range(int(w // 3) + 1):
            parts.append(box(name + "_pil", (-w / 2 + 0.3 + i * (w - 0.6) / max(1, int(w // 3)), 0, pilotis / 2), (0.35, d * 0.6, pilotis), P["light"]))
    for r in range(rows):
        for c in range(cols):
            x = -w / 2 + w * (c + 0.5) / cols; z = pilotis + h * (r + 0.55) / rows
            parts.append(box(name + "_win", (x, -d / 2 - 0.02, z), (w / cols * 0.62, 0.04, h / rows * 0.55),
                             P["win"] if rng.random() < lit_frac else P["dark"]))
    return group(name, parts, loc, rz)


# ------------------------------------------------------------------------------------------------- furniture
def table(name, loc, w=1.6, d=0.9, h=0.75, rz=0.0, cloth=False):
    P = M(); parts = [box(name + "_top", (0, 0, h - 0.025), (w, d, 0.05), P["paper"] if cloth else P["wood"], bevel=0.01)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box(name + "_leg", (sx * (w / 2 - 0.06), sy * (d / 2 - 0.06), (h - 0.05) / 2), (0.05, 0.05, h - 0.05), P["wood"]))
    return group(name, parts, loc, rz)


def chair(name, loc, rz=0.0, h=0.46):
    """Faces -Y (the sitter faces -Y)."""
    P = M(); parts = [box(name + "_seat", (0, 0, h - 0.02), (0.44, 0.44, 0.04), P["wood"]),
                      box(name + "_back", (0, 0.2, h + 0.4), (0.44, 0.04, 0.8), P["wood"])]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box(name + "_leg", (sx * 0.19, sy * 0.19, (h - 0.04) / 2), (0.035, 0.035, h - 0.04), P["wood"]))
    return group(name, parts, loc, rz)


def sofa(name, loc, rz=0.0, w=2.0):
    P = M(); c = P["cloth"]
    parts = [box(name + "_base", (0, 0, 0.22), (w, 0.85, 0.44), c, bevel=0.05), box(name + "_back", (0, 0.34, 0.62), (w, 0.2, 0.5), c, bevel=0.06)]
    for s in (-1, 1):
        parts.append(box(name + "_arm", (s * (w / 2 - 0.1), 0, 0.5), (0.2, 0.85, 0.28), c, bevel=0.05))
    return group(name, parts, loc, rz)


def tv(name, loc, rz=0.0, on=True):
    P = M(); parts = [box(name + "_stand", (0, 0, 0.25), (1.0, 0.45, 0.5), P["wood"]),
                      box(name + "_set", (0, 0, 0.8), (0.72, 0.5, 0.56), P["dark"], bevel=0.04),
                      box(name + "_screen", (0, -0.252, 0.8), (0.56, 0.01, 0.42), P["tv"] if on else P["dark"])]
    g = group(name, parts, loc, rz)
    if on:
        l = rk.area(name + "_glow", g.matrix_world @ Vector((0, -0.5, 0.8)), g.matrix_world @ Vector((0, -3, 0.6)), 0.6, 60.0, (0.55, 0.75, 1.0))
    return g


def shelf(name, loc, w=1.6, h=2.0, rz=0.0, seed=0):
    P = M(); rng = random.Random(seed); parts = [box(name + "_back", (0, 0.15, h / 2), (w, 0.04, h), P["wood"])]
    n = 5
    for i in range(n + 1):
        parts.append(box(name + "_plank", (0, 0, i * h / n + 0.02), (w, 0.32, 0.03), P["wood"]))
    for i in range(n):
        x = -w / 2 + 0.03
        while x < w / 2 - 0.05:
            bw = rng.uniform(0.025, 0.06); bh = rng.uniform(0.2, 0.33)
            parts.append(box(name + "_book", (x + bw / 2, 0, i * h / n + 0.035 + bh / 2), (bw, 0.24, bh),
                             rng.choice([P["paper"], P["grey"], P["light"], P["dark"]])))
            x += bw + 0.004
    return group(name, parts, loc, rz)


def frame(name, loc, w=0.5, h=0.38, rz=0.0, empty=True):
    """A picture/diploma frame hanging on a wall facing -Y (back on y=0)."""
    P = M(); parts = [box(name + "_frame_t", (0, -0.02, h / 2), (w, 0.03, 0.035), P["wood"]),
                      box(name + "_frame_b", (0, -0.02, -h / 2), (w, 0.03, 0.035), P["wood"]),
                      box(name + "_frame_l", (-w / 2, -0.02, 0), (0.035, 0.03, h), P["wood"]),
                      box(name + "_frame_r", (w / 2, -0.02, 0), (0.035, 0.03, h), P["wood"]),
                      box(name + "_mount", (0, -0.01, 0), (w - 0.04, 0.01, h - 0.04), P["paper"]),
                      box(name + "_glass", (0, -0.035, 0), (w - 0.04, 0.004, h - 0.04), rk.mat("frame_glass", (0.8, 0.8, 0.78), 0.03, alpha=0.08))]
    return group(name, parts, loc, rz)


def boots(name, loc, rz=0.0, s=0.6):
    """A pair of small boots (children's when s<0.7)."""
    P = M(); parts = []
    for sx in (-0.07, 0.07):
        parts.append(box(name + "_sole", (sx * s / 0.6, 0, 0.015 * s / 0.6), (0.09 * s / 0.6, 0.24 * s / 0.6, 0.03 * s / 0.6), P["rubber"], bevel=0.01))
        parts.append(box(name + "_shaft", (sx * s / 0.6, 0.05 * s / 0.6, 0.11 * s / 0.6), (0.085 * s / 0.6, 0.11 * s / 0.6, 0.2 * s / 0.6), P["coat"], bevel=0.02))
        parts.append(box(name + "_toe", (sx * s / 0.6, -0.05 * s / 0.6, 0.05 * s / 0.6), (0.085 * s / 0.6, 0.12 * s / 0.6, 0.08 * s / 0.6), P["coat"], bevel=0.03))
    return group(name, parts, loc, rz)


def notes_stack(name, loc, n=6, rz=0.0, hot=False):
    P = M(); parts = []
    for i in range(n):
        parts.append(box(name + f"_b{i}", (0, 0, 0.012 * i + 0.006), (0.16, 0.075, 0.012), P["hot"] if hot else P["paper"]))
        parts.append(box(name + f"_band{i}", (0, 0, 0.012 * i + 0.006), (0.03, 0.077, 0.013), P["grey"]))
    return group(name, parts, loc, rz)


def cord_coil(name, loc, r=0.12, turns=5, thick=0.007):
    """The nylon cord: a loose coil (RED accent)."""
    P = M()
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = thick; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); pts = []
    rng = random.Random(4)
    for i in range(turns * 24 + 1):
        a = i / 24 * 2 * math.pi; rr = r * (1 + 0.08 * math.sin(i * 0.7)) * rng.uniform(0.96, 1.04)
        pts.append((math.cos(a) * rr, math.sin(a) * rr * 0.9, thick + i * thick * 0.12))
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (*c, 1)
    o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o); cu.materials.append(P["red"])
    return group(name + "_g", [o], loc)


def canister(name, loc, rz=0.0, lying=True, red=True):
    """Tear-gas canister: a small aerosol can (RED accent)."""
    P = M(); m = P["red"] if red else P["grey"]
    parts = [cyl(name + "_can", (0, 0, 0), (0, 0, 0.2), 0.034, m, 24), cyl(name + "_shoulder", (0, 0, 0.2), (0, 0, 0.215), 0.028, m, 24),
             cyl(name + "_cap", (0, 0, 0.215), (0, 0, 0.245), 0.012, P["dark"], 16), box(name + "_nozzle", (0.012, 0, 0.237), (0.014, 0.008, 0.008), P["dark"])]
    g = group(name, parts, (0, 0, 0))
    if lying:
        g.rotation_euler = (math.radians(90), 0, rz); g.location = Vector(loc) + Vector((0, 0, 0.034))
    else:
        g.location = loc; g.rotation_euler.z = rz
    return g


def doctor_bag(name, loc, rz=0.0, stetho=True):
    P = M(); parts = [box(name + "_bag", (0, 0, 0.13), (0.42, 0.2, 0.26), P["cloth"], bevel=0.06),
                      box(name + "_clasp", (0, 0, 0.265), (0.44, 0.05, 0.02), P["chrome"])]
    bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.012, location=(0, 0, 0.3), rotation=(math.radians(90), 0, 0))
    h = bpy.context.active_object; h.name = name + "_handle"; h.data.materials.append(P["cloth"]); parts.append(h)
    if stetho:
        bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.006, location=(0.05, -0.05, 0.27), rotation=(math.radians(8), 0, 0))
        s = bpy.context.active_object; s.name = name + "_stetho"; s.data.materials.append(P["dark"]); parts.append(s)
        parts.append(cyl(name + "_chest", (0.18, -0.12, 0.262), (0.18, -0.12, 0.282), 0.025, P["chrome"], 20))
    return group(name, parts, loc, rz)


def flagpoles(name, loc, n=6, gap=1.2, h=6.0, rz=0.0):
    P = M(); parts = []
    for i in range(n):
        x = (i - (n - 1) / 2) * gap
        parts.append(cyl(name + "_pole", (x, 0, 0), (x, 0, h), 0.03, P["steel"], 8))
        parts.append(box(name + "_flag", (x + 0.45, 0, h - 0.35), (0.85, 0.01, 0.55), P["light"]))
    return group(name, parts, loc, rz)


def letterbox(name, loc, rz=0.0):
    P = M(); parts = [cyl(name + "_post", (0, 0, 0), (0, 0, 1.0), 0.04, P["steel"], 8),
                      box(name + "_box", (0, 0, 1.12), (0.3, 0.4, 0.26), P["grey"], bevel=0.02)]
    return group(name, parts, loc, rz)


def candle(name, loc):
    P = M(); parts = [cyl(name + "_c", (0, 0, 0), (0, 0, 0.18), 0.012, P["paper"], 10),
                      sphere(name + "_flame", (0, 0, 0.2), 0.008, P["candle"], (1, 1, 2.0), seg=8)]
    g = group(name, parts, loc)
    rk.point(name + "_l", Vector(loc) + Vector((0, 0, 0.22)), 1.2, (1.0, 0.6, 0.2), 0.02)
    return g


def place_setting(name, loc, rz=0.0):
    P = M(); parts = [cyl(name + "_plate", (0, 0, 0), (0, 0, 0.012), 0.12, P["paper"], 24),
                      cyl(name + "_glass", (0.16, -0.12, 0), (0.16, -0.12, 0.14), 0.03, P["glass"], 12)]
    return group(name, parts, loc, rz)


def pawn(name, loc, s=1.0, hot=False):
    P = M(); m = P["hot"] if hot else P["pawn"]
    parts = [cyl(name + "_base", (0, 0, 0), (0, 0, 0.04 * s), 0.11 * s, m, 24),
             cone(name + "_body", (0, 0, 0.2 * s), 0.09 * s, 0.035 * s, 0.32 * s, m, 24),
             sphere(name + "_head", (0, 0, 0.42 * s), 0.07 * s, m, seg=20)]
    return group(name, parts, loc)


# ------------------------------------------------------------------------------------------------- the Peugeot 405 (CC-BY)
CAR405 = "b9b69099434c45bdb3265417dd720752"   # "1994 Peugeot 405 GLX (facelift version)" by Mehrdad995GTa, CC-BY 4.0


def _split(o, pred, name):
    """Move the faces of mesh o for which pred(world_center, world_normal) is true into a new object."""
    import bmesh
    mw = o.matrix_world; R = mw.to_3x3().normalized()
    b = bmesh.new(); b.from_mesh(o.data); b.faces.ensure_lookup_table()
    sel = [f for f in b.faces if pred(mw @ f.calc_center_median(), (R @ f.normal).normalized())]
    if not sel:
        b.free(); return None
    nb = bmesh.new()
    vmap = {}
    for f in sel:
        vs = []
        for v in f.verts:
            if v not in vmap:
                vmap[v] = nb.verts.new(v.co)
            vs.append(vmap[v])
        try:
            nb.faces.new(vs)
        except ValueError:
            pass
    bmesh.ops.delete(b, geom=sel, context='FACES'); b.to_mesh(o.data); b.free()
    me = bpy.data.meshes.new(name); nb.to_mesh(me); nb.free()
    n = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(n); n.matrix_world = mw.copy()
    return n


def _bisect(o, co, no):
    """Cut mesh o along a world-space plane (clean straight seams before splitting panels off)."""
    import bmesh
    mw = o.matrix_world; inv = mw.inverted()
    pc = inv @ Vector(co); pn = (inv.to_3x3().transposed().inverted() @ Vector(no)).normalized() if False else (mw.to_3x3().transposed() @ Vector(no)).normalized()
    b = bmesh.new(); b.from_mesh(o.data)
    bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=pc, plane_no=pn)
    b.to_mesh(o.data); b.free()


def car405(name="car", loc=(0, 0, 0), rz=0.0, boot=0.0, lights=True, dome=0.0, beams=True, hl_energy=300.0, door_l=0.0, door_r=0.0):
    """The Romand car: a 1994 Peugeot 405 (Sketchfab CC-BY), scaled to 4.41 m, front facing +X, windows cut into
    see-through glass, boot lid separated on a hinge (boot 0..1), a simple interior (seats, dash, wheel, floor).
    Same return dict as car()."""
    import sf
    P = M()
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=sf.fetch(CAR405))
    new = [o for o in bpy.data.objects if o not in before]
    for o in list(new):
        if o.type == 'MESH' and any(k in o.name for k in ("Collision", "ShadowCaster", "Shadows")):
            new.remove(o); bpy.data.objects.remove(o)
    pivot = rk.empty(name)
    for o in new:
        if o.parent is None:
            o.parent = pivot
    s = 4.41 / 2.82
    pivot.scale = (s, s, s); pivot.rotation_euler.z = math.pi / 2          # model front (-Y) -> +X; canonical frame = world now
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == 'MESH']
    body = [o for o in meshes if "Body" in o.name][0]
    plast = [o for o in meshes if "Plastics" in o.name][0]
    lights_o = [o for o in meshes if "Lights" in o.name][0]
    # window glass lives in the plastics mesh, above the belt line
    def is_win(c, n):
        return c.z > 0.98 and abs(n.z) < 0.97 and abs(c.y) < 0.86
    win = _split(plast, is_win, name + "_windows")
    roofwin = _split(plast, lambda c, n: c.z > 1.05 and n.z > 0.3, name + "_screens")
    for w_ in (win, roofwin):
        if w_ is not None:
            w_.parent = top.parent if False else None
            w_.data.materials.clear(); w_.data.materials.append(rk.mat("car_glass", (0.05, 0.05, 0.05), 0.04, alpha=0.18))
            mwk = w_.matrix_world.copy(); w_.parent = pivot; w_.matrix_world = mwk
    # boot lid: body faces on the rear deck behind the rear screen
    lid = _split(body, lambda c, n: c.x < -1.55 and c.z > 0.84 and n.z > 0.25, name + "_boot_lid")
    # front doors: cut the door skin (and its window glass) out of the body and hang each on a hinge at its front edge
    doors = {}
    if door_l or door_r:
        for o in [x for x in (body, plast, win) if x is not None]:
            for co, no in (((-0.42, 0, 0), (1, 0, 0)), ((0.98, 0, 0), (1, 0, 0)), ((0, 0, 0.3), (0, 0, 1))):
                _bisect(o, co, no)
    for side, amt in ((1, door_l), (-1, door_r)):
        if not amt:
            continue
        def in_door(c, n, side=side):
            return side * c.y > 0.55 and -0.42 < c.x < 0.98 and 0.3 < c.z < 1.42 and side * n.y > 0.35
        pieces = [x for x in (_split(body, in_door, name + f"_door{side}"),
                              _split(plast, lambda c, n, f=in_door: f(c, n) and c.z < 0.98, name + f"_doortrim{side}"),
                              _split(win, in_door, name + f"_doorwin{side}") if win is not None else None) if x is not None]
        card = box(name + f"_doorcard{side}", (0.28, side * 0.74, 0.68), (1.3, 0.03, 0.62), P["cloth"])
        pieces.append(card)
        if not pieces:
            continue
        bpy.context.view_layer.update()
        vs = [p.matrix_world @ v.co for p in pieces for v in p.data.vertices]
        hx = max(v.x for v in vs); hy = sum(v.y for v in vs) / len(vs)
        h = rk.empty(name + f"_door_hinge{side}", (hx, hy, 0.7)); bpy.context.view_layer.update()
        for p in pieces:
            p.parent = h; p.matrix_parent_inverse = h.matrix_world.inverted()
        h.rotation_euler.z = math.radians(-side * 62 * amt)   # swing outward
        doors[side] = (h, pieces)
    # paint everything neutral (the world tint comes from the light)
    for o in [body, lid] + [p for d in doors.values() for p in d[1] if "_door" in p.name and ("win" not in p.name and "trim" not in p.name and "card" not in p.name)]:
        if o is not None:
            o.data.materials.clear(); o.data.materials.append(P["carpaint"])
    for d in doors.values():
        for p in d[1]:
            if "_doorwin" in p.name:
                p.data.materials.clear(); p.data.materials.append(rk.mat("car_glass", (0.05, 0.05, 0.05), 0.04, alpha=0.18))
    parts_doors = [d[0] for d in doors.values()]
    # lamps: front half headlamps, rear half tail lamps
    hl_ = _split(lights_o, lambda c, n: c.x > 0, name + "_headlamps")
    tl_ = lights_o
    if hl_ is not None:
        hl_.data.materials.clear(); hl_.data.materials.append(P["head"] if lights else P["chrome"])
        mwk = hl_.matrix_world.copy(); hl_.parent = pivot; hl_.matrix_world = mwk
    tl_.data.materials.clear(); tl_.data.materials.append(P["tail"])
    parts = []
    if lid is not None:
        bpy.context.view_layer.update()
        vs = [lid.matrix_world @ v.co for v in lid.data.vertices]
        hx = max(v.x for v in vs); hz = max(v.z for v in vs if v.x > hx - 0.08)
        hinge = rk.empty(name + "_boot_hinge", (hx, 0, hz)); bpy.context.view_layer.update()
        mwk = lid.matrix_world.copy(); lid.parent = hinge; lid.matrix_parent_inverse = hinge.matrix_world.inverted()
        bpy.context.view_layer.update()
        hinge.rotation_euler.y = math.radians(80 * boot)
        parts.append(hinge)
        # boot cavity: dark well under the lid
        parts.append(box(name + "_boot_tub", (-1.86, 0, 0.62), (0.62, 1.3, 0.04), P["dark"]))
        parts.append(box(name + "_boot_back", (-1.55, 0, 0.75), (0.03, 1.3, 0.3), P["dark"]))
        if boot > 0:
            parts.append(rk.point(name + "_bootlamp", (-1.7, 0, 0.9), 3.0 + 40.0 * min(1.0, 0.15 / max(boot, 0.01)) * (boot < 0.5), (1.0, 0.8, 0.5)))
    # interior
    seats = {}
    for nm, sy in (("driver", 0.36), ("passenger", -0.36)):
        parts.append(box(name + "_seat_" + nm, (-0.12, sy, 0.42), (0.5, 0.48, 0.12), P["cloth"], bevel=0.03))
        bk = box(name + "_back_" + nm, (-0.42, sy, 0.78), (0.1, 0.46, 0.6), P["cloth"], bevel=0.03); bk.rotation_euler.y = math.radians(-14)
        parts.append(bk); seats[nm] = Vector((-0.08, sy, 0.48))
    parts.append(box(name + "_rearseat", (-1.05, 0, 0.42), (0.5, 1.3, 0.12), P["cloth"], bevel=0.03))
    parts.append(box(name + "_rearback", (-1.32, 0, 0.75), (0.1, 1.3, 0.55), P["cloth"], bevel=0.03))
    parts.append(box(name + "_dash", (0.62, 0, 0.82), (0.36, 1.4, 0.22), P["dark"], bevel=0.04))
    parts.append(box(name + "_floor", (-0.4, 0, 0.27), (2.4, 1.4, 0.03), P["dark"]))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.018, location=(0.4, 0.36, 0.92), rotation=(0, math.radians(65), 0))
    sw = bpy.context.active_object; sw.name = name + "_wheel"; sw.data.materials.append(P["dark"]); parts.append(sw)
    if dome:
        parts.append(rk.point(name + "_dome", (-0.3, 0, 1.3), dome, (1.0, 0.85, 0.6), soft=0.2))
    parts += parts_doors
    bpy.context.view_layer.update()
    for p_ in parts:
        p_.parent = pivot; p_.matrix_parent_inverse = pivot.matrix_world.inverted()
    bpy.context.view_layer.update()
    # re-base: a clean unscaled root so callers can place the car like any other prop
    root = rk.empty(name + "_root")
    pivot.parent = root
    root.location = loc; root.rotation_euler.z = rz
    bpy.context.view_layer.update()
    mw = root.matrix_world; pivot = root
    hl = [Vector((2.2, 0.55, 0.62)), Vector((2.2, -0.55, 0.62))]
    out = dict(root=pivot, boot_lid=lid, boot_floor=mw @ Vector((-1.86, 0, 0.65)), head=[mw @ h for h in hl],
               seats={k: mw @ v for k, v in seats.items()}, fwd=(mw.to_3x3() @ Vector((1, 0, 0))).normalized())
    if lights:
        for i, h in enumerate(out["head"]):
            rk.spot(name + f"_hl{i}", h, h + out["fwd"] * 10 + Vector((0, 0, -0.9)), hl_energy, (1.0, 0.9, 0.7), 50, 0.35, 0.05)
            if beams:
                beam(name + f"_beam{i}", h, out["fwd"] + Vector((0, 0, -0.06)), 7.0, 1.3, strength=0.03)
    return out


def model_house(name, loc, s=1.0, lit=True, rz=0.0):
    """A clean little house model for explainer slabs: block + prism roof, windows as lit squares."""
    P = M(); parts = [box(name + "_block", (0, 0, 0.3 * s), (1.0 * s, 0.8 * s, 0.6 * s), P["pawn"], bevel=0.01)]
    me = bpy.data.meshes.new(name + "_roof")
    w, d, h0, h1 = 0.56 * s, 0.46 * s, 0.6 * s, 0.95 * s
    me.from_pydata([(-w, -d, h0), (w, -d, h0), (w, d, h0), (-w, d, h0), (-w, 0, h1), (w, 0, h1)], [],
                   [(0, 1, 5, 4), (3, 4, 5, 2), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)])
    me.update(); ro = bpy.data.objects.new(name + "_roof", me); bpy.context.scene.collection.objects.link(ro); me.materials.append(P["grey"])
    parts.append(ro)
    for i, x in enumerate((-0.25, 0.25)):
        parts.append(box(name + f"_win{i}", (x * s, -0.401 * s, 0.35 * s), (0.18 * s, 0.01 * s, 0.18 * s), P["hot"] if lit else P["dark"]))
    parts.append(box(name + "_door", (0, -0.401 * s, 0.14 * s), (0.14 * s, 0.01 * s, 0.26 * s), P["dark"]))
    return group(name, parts, loc, rz)


def rubber_boots(name, loc, rz=0.0, h=0.17):
    """A pair of real rubber boots (Poly Haven CC0 'rubber_boots'), scaled so the shaft is h metres tall (child size)."""
    import ph
    root, ms = ph.model("rubber_boots", res="1k")
    lo, hi = ph.bounds(ms)
    s = h / max(hi.z - lo.z, 1e-6)
    piv = rk.empty(name)
    root.parent = piv; root.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
    piv.scale = (s, s, s); piv.location = loc; piv.rotation_euler.z = rz
    bpy.context.view_layer.update()
    for o in ms:                 # pale clay like the rest of the world's small objects
        o.data.materials.clear(); o.data.materials.append(P_coat())
    return piv


def P_coat():
    return M()["coat"]
