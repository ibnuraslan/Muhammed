# v002b clothing (director notes): real clothes for the two burial-party men (belted wool tunic, trousers in another colour,
# shoulder cloak) and a draped wool burial cloak over the deceased (cloth-simulated once onto her fixed curled pose).
# exec'd by 02_build.py after dead_place(1, ...) and before bake_dead(); needs tex_mat, mat, DEAD, BURA, BURB, FLOOR, TOPZ, DEAD_CEN.

LEGB = ("upperleg", "lowerleg", "foot", "toe")
def _dominant(ob):
    gi = {g.index: g.name for g in ob.vertex_groups}
    dom = []
    for v in ob.data.vertices:
        best = None; bw = 0.0
        for g in v.groups:
            n = gi.get(g.group, "")
            if "." in n or n.startswith(("spine", "neck", "head", "root", "pelvis")):
                if g.weight > bw: best, bw = n, g.weight
        dom.append(best or "")
    return dom

def _sub_mesh(src, name, face_ok, offset, thick, m):
    """new object from the faces of src that pass face_ok(poly), pushed out along the normals, same armature"""
    import bmesh as _bm
    me = src.data.copy(); o = bpy.data.objects.new(name, me); src.users_collection[0].objects.link(o)
    for g in src.vertex_groups: o.vertex_groups.new(name=g.name)
    o.parent = src.parent; o.matrix_parent_inverse = src.matrix_parent_inverse.copy(); o.matrix_basis = src.matrix_basis.copy()
    keep = {p.index for p in src.data.polygons if face_ok(p)}
    bm = _bm.new(); bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    _bm.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    bm.to_mesh(me); bm.free()
    me.materials.clear(); me.materials.append(m)
    for md in list(o.modifiers): o.modifiers.remove(md)
    d = o.modifiers.new("push", 'DISPLACE'); d.strength = offset; d.mid_level = 0.0
    so = o.modifiers.new("thick", 'SOLIDIFY'); so.thickness = thick; so.offset = 1.0
    am = o.modifiers.new("Armature", 'ARMATURE'); am.object = src.parent
    o.modifiers.move(len(o.modifiers) - 1, 0)          # deform first, then push out
    for p in me.polygons: p.use_smooth = True
    return o

def dress_burial(rig, tunic_rgb, trouser_rgb, cloak_rgb, tag):
    suit = next(c for c in rig.children if "casualsuit" in c.name)
    tunic = tex_mat("Tunic_" + tag, "rough_linen", 4.0, tunic_rgb, 0.0, 0.0, bump=0.35)
    trous = tex_mat("Trousers_" + tag, "rough_linen", 5.0, trouser_rgb, -0.1, 0.0, bump=0.3)
    cloak = tex_mat("Cloak_" + tag, "rough_linen", 2.5, cloak_rgb, -0.1, 0.0, bump=0.45)
    belt = mat("Belt_" + tag, (0.16, 0.09, 0.05), 0.55)
    BN = rig.data.bones
    hip_z = BN["upperleg01.L"].head_local.z
    waist_z = BN["spine04"].head_local.z if "spine04" in BN else hip_z + 0.12
    dom = _dominant(suit)
    me = suit.data
    me.materials.clear(); me.materials.append(tunic); me.materials.append(trous)
    for p in me.polygons:
        ds = [dom[i] for i in p.vertices]
        legs = sum(1 for d in ds if d.startswith(LEGB)) > len(ds) / 2
        # the tunic skirt reaches 18 cm below the hip joint; below that the trousers show
        p.material_index = 1 if (legs and p.center.z < hip_z - 0.18) else 0
    # belt: a band of the suit around the waist, pushed out a little
    _sub_mesh(suit, rig.name + "_Belt", lambda p: abs(p.center.z - waist_z) < 0.022, 0.006, 0.006, belt)
    # shoulder cloak: shoulders, upper back and chest down to the armpits, pushed out 2 cm
    sh_z = BN["upperarm01.L"].head_local.z
    CL = ("clavicle", "shoulder01", "spine01", "spine02", "neck01", "upperarm01")
    def cloak_ok(p):
        ds = [dom[i] for i in p.vertices]
        if not all(d.startswith(CL) for d in ds): return False
        if p.center.z < sh_z - 0.20: return False
        if p.center.y < 0 and p.center.z < sh_z - 0.08: return False       # open at the front below the collar
        return True
    _sub_mesh(suit, rig.name + "_Cloak", cloak_ok, 0.02, 0.008, cloak)
    print("CLOTHES", rig.name, "waist", round(waist_z, 2), "hip", round(hip_z, 2))

dress_burial(BURA, (0.55, 0.38, 0.22), (0.25, 0.20, 0.16), (0.36, 0.24, 0.14), "A")     # brown tunic, dark trousers, fur-brown cloak
dress_burial(BURB, (0.66, 0.58, 0.40), (0.30, 0.24, 0.15), (0.24, 0.20, 0.17), "B")     # oatmeal tunic, brown trousers, grey cloak

# ------------------------------------------------------------------ the deceased's burial cloak (cloth sim, applied)
TOPZ = DEAD_CEN.z + EXT[1].z
def make_shroud():
    sc.frame_set(1); bpy.context.view_layer.update()
    body = bpy.data.objects["Dead.body"]; dress = next(c for c in DEAD.children if "elegantsuit" in c.name)
    cols = []
    for o in (body, dress):
        cm = o.modifiers.new("coll", 'COLLISION'); cols.append((o, cm))
        o.collision.thickness_outer = 0.006; o.collision.cloth_friction = 8
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    fl = bpy.context.active_object; fl.name = "ShroudFloor"; fl.scale = (3, 3, 1); fl.location = (DEAD_CEN.x, DEAD_CEN.y, FLOOR + 0.004)
    fl.modifiers.new("coll", 'COLLISION')
    # the cloak covers her from the shoulders to past the feet; the head (at -X) stays uncovered
    x0, x1 = DEAD_CEN.x - 0.20, DEAD_CEN.x + 0.56
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=46, y_subdivisions=64, size=1, location=(0, 0, 0))
    sh = bpy.context.active_object; sh.name = "Dead.Shroud"
    sh.scale = (x1 - x0, 1.05, 1); sh.location = ((x0 + x1) / 2, DEAD_CEN.y, TOPZ + 0.06)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cl = sh.modifiers.new("cloth", 'CLOTH'); s = cl.settings
    s.quality = 6; s.mass = 0.25; s.bending_stiffness = 0.3; s.tension_stiffness = 12; s.compression_stiffness = 12
    s.air_damping = 2.0
    cl.collision_settings.distance_min = 0.006; cl.collision_settings.collision_quality = 4
    cl.point_cache.frame_start = 1; cl.point_cache.frame_end = 70
    for f in range(1, 71):
        sc.frame_set(f)
    bpy.context.view_layer.objects.active = sh
    for o in bpy.context.selected_objects: o.select_set(False)
    sh.select_set(True)
    bpy.ops.object.modifier_apply(modifier="cloth")
    sc.frame_set(1)
    for o, cm in cols: o.modifiers.remove(cm)
    bpy.data.objects.remove(fl, do_unlink=True)
    sm = sh.modifiers.new("sub", 'SUBSURF'); sm.levels = 1; sm.render_levels = 1
    so = sh.modifiers.new("thick", 'SOLIDIFY'); so.thickness = 0.006
    bpy.ops.object.shade_smooth()
    wool = tex_mat("BurialWool", "rough_linen", 3.0, (0.62, 0.46, 0.30), 0.0, 0.0, bump=0.4)
    sh.data.materials.append(wool)
    sh.data.uv_layers.new(name="UVMap") if not sh.data.uv_layers else None
    mw = sh.matrix_world.copy(); sh.parent = DEAD; sh.matrix_world = mw
    for c_ in list(sh.users_collection): c_.objects.unlink(sh)
    DEAD.users_collection[0].objects.link(sh)
    zs = [(sh.matrix_world @ v.co).z for v in sh.data.vertices]
    print("CLOTHES shroud z", round(min(zs), 3), round(max(zs), 3))
    return sh
SHROUD = make_shroud()

# wool leg wraps under the cloak: her legs are covered wherever the cloak does not reach (knees, shins)
_body = bpy.data.objects["Dead.body"]; _dom = _dominant(_body)
_lw = tex_mat("LegWool", "rough_linen", 5.0, (0.50, 0.37, 0.25), 0.0, 0.0, bump=0.4)
def _leg_ok(p):
    ds = [_dom[i] for i in p.vertices]
    return sum(1 for d in ds if d.startswith(("upperleg", "lowerleg"))) > len(ds) / 2
LEGW = _sub_mesh(_body, "Dead.LegWool", _leg_ok, 0.010, 0.004, _lw)
print("CLOTHES leg wool faces", len(LEGW.data.polygons))
