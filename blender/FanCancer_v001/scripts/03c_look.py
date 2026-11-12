"""Animated-CG look (client 22:45) + hands pass (client 23:00). Exec'd last, after 04_camera and pipeline/anim_look.py."""
import bpy, math, os
from mathutils import Vector, Euler, Quaternion
sc = bpy.context.scene
def ramp_set(mat, node_type, cols):
    for n in mat.node_tree.nodes:
        if n.type == 'VALTORGB':
            for e, (pos, c) in zip(n.color_ramp.elements, cols):
                e.position = pos; e.color = (*c, 1)
            return
# cutaway: bright sky-blue gradient (bottom near-white, top cyan)
bd = bpy.data.materials["CutawayBackdrop"]; ramp_set(bd, 'VALTORGB', [(0.42, (0.80, 0.93, 1.0)), (0.62, (0.08, 0.55, 0.93))])
for n in bd.node_tree.nodes:
    if n.type == 'EMISSION': n.inputs['Strength'].default_value = 1.7
# section layers: clean colour-coded
sec = bpy.data.materials["SkinSection"]
for n in sec.node_tree.nodes:
    if n.type == 'VALTORGB' and len(n.color_ramp.elements) > 4:
        cols = {0: (0.95, 0.60, 0.12), 1: (0.95, 0.62, 0.15), 2: (0.90, 0.38, 0.40), 3: (0.90, 0.40, 0.42), 4: (0.85, 0.45, 0.42), 5: (0.98, 0.70, 0.55), 6: (0.98, 0.72, 0.58)}
        for i, e in enumerate(sorted(n.color_ramp.elements, key=lambda e: e.position)):
            e.color = (*cols.get(i, (0.9, 0.5, 0.45)), 1)
    if n.type == 'MIX' and n.blend_type == 'MULTIPLY' and n.inputs['Factor'].default_value == 0.35: n.inputs['Factor'].default_value = 0.15
for nm in ("SkinKey", "SkinRim", "SkinFill"):
    bpy.data.lights[nm].energy *= 1.6
# rink: bright, clean
for nm in ("BackWall", "FarBackWall", "EndWallL"):
    o = bpy.data.objects[nm]; o.data.materials.clear()
    m = bpy.data.materials.get("ArenaWall") or mat("ArenaWall", (0.62, 0.70, 0.82), 0.6, noise=0.05, nscale=3); o.data.materials.append(m)
cm = bpy.data.objects["Ceiling"].data.materials[0]; cm.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.42, 0.46, 0.52, 1)
ice = bpy.data.materials["Ice"]
for n in ice.node_tree.nodes:
    if n.type == 'VALTORGB': n.color_ramp.elements[0].color = (0.82, 0.88, 0.93, 1); n.color_ramp.elements[1].color = (0.96, 0.98, 1.0, 1)
for L in bpy.data.lights:
    if L.name.startswith("ArenaL"): L.energy *= 1.6
    if L.name.startswith("StandFill"): L.energy *= 2.0
# riser concrete -> painted light grey
for o in bpy.data.objects:
    if o.name.startswith(("Riser", "FarRiser")):
        o.data.materials.clear(); o.data.materials.append(bpy.data.materials.get("RiserPaint") or mat("RiserPaint", (0.55, 0.58, 0.62), 0.6, noise=0.05, nscale=6))
# city: readable dusk blue
nt = sc.world.node_tree; nt.nodes["WMIX2"].inputs['B'].default_value = (0.20, 0.32, 0.62, 1)
L = bpy.data.lights.new("CityMoon", 'SUN'); L.energy = 5.0; L.color = (0.6, 0.7, 1.0)
lo = bpy.data.objects.new("CityMoon", L); lo.rotation_euler = (math.radians(55), 0, math.radians(200)); bpy.data.collections["CITY"].objects.link(lo)
# NOTE: a sun lights every set; keyed on only while the camera is in the city
for f, e in ((1, 0.0), (F(31.8), 5.0), (F(35.9), 0.0)):
    L.energy = e; L.keyframe_insert("energy", frame=f)
for fc in _fcurves(L.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# clinic: bright mint walls, exam lamp, poster
for n in bpy.data.materials["ClinicWall"].node_tree.nodes:
    if n.type == 'MIX' and n.blend_type == 'MULTIPLY': n.inputs['B'].default_value = (0.86, 0.97, 0.95, 1)
for nm, k in (("ClinicKey", 2.4), ("ClinicFill", 2.4)): bpy.data.lights[nm].energy *= k
lr, _ = ph_blend("desk_lamp_arm_01", bpy.data.collections["CLINIC"], (-27.6, -2.95, 0.0), rot_z=math.pi, scale=1.6)
pim = bpy.data.images.load(os.path.join(WORK, "poster.png")); pim.pack()
pm = bpy.data.materials.new("Poster"); pm.use_nodes = True; pn = pm.node_tree.nodes; pt = pn.new('ShaderNodeTexImage'); pt.image = pim
pm.node_tree.links.new(pt.outputs['Color'], pn["Principled BSDF"].inputs['Base Color']); pn["Principled BSDF"].inputs['Roughness'].default_value = 0.5
plane("Poster", 0.6, 0.84, (-28.4, 1.49, 1.55), pm, bpy.data.collections["CLINIC"], rot=(math.pi / 2, 0, math.pi))
plane("Poster2", 0.6, 0.84, (-31.09, 0.2, 1.55), pm, bpy.data.collections["CLINIC"], rot=(math.pi / 2, 0, math.pi / 2))
# soft key that travels with the camera (lifts faces, high-key)
cam = sc.camera
L = bpy.data.lights.new("CamFill", 'AREA'); L.energy = 25; L.size = 1.5; L.color = (1.0, 0.97, 0.94)
lo = bpy.data.objects.new("CamFill", L); lo.parent = cam; lo.location = (0.3, 0.4, 0.0); sc.collection.objects.link(lo)
L.cycles.max_bounces = 2
for f, e in ((1, 25), (F(5.0), 0), (F(8.6), 25), (F(31.8), 40)):
    L.energy = e; L.keyframe_insert("energy", frame=f)
for fc in _fcurves(L.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# sticks floated near the hands: removed (players cheer with empty hands)
for o in bpy.data.objects:
    if o.name.startswith("StickSrc"): o.hide_render = True; o.hide_viewport = True
    if o.type == 'MESH' and o.data.name == bpy.data.objects["StickSrc"].data.name: o.hide_render = True
# ---- hands: limits + relaxed curl on every rig
def lim(pb, xr, yr, zr):
    c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
    c.use_limit_x = c.use_limit_y = c.use_limit_z = True
    c.min_x, c.max_x = (math.radians(v) for v in xr); c.min_y, c.max_y = (math.radians(v) for v in yr); c.min_z, c.max_z = (math.radians(v) for v in zr)
nlim = 0
for r in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    for pb in r.pose.bones:
        n = pb.name
        if n.startswith("finger") and n[-2:] in (".L", ".R"):
            thumb = n.startswith("finger1")
            lim(pb, (-15, 70) if thumb else (-2, 95), (-35, 35) if thumb else (-8, 8), (-35, 35) if thumb else (-10, 10)); nlim += 1
            if not (pb.animation_data_ext if hasattr(pb, "animation_data_ext") else False):
                curl = 12 if thumb else (18 if n.endswith(("-1.L", "-1.R")) else 24)
                if r.name in ("Doctor",) and n.endswith(".R"): curl += 25
                q = Euler((math.radians(curl), 0, 0)).to_quaternion()
                if pb.rotation_mode == 'QUATERNION':
                    has_keys = r.animation_data and r.animation_data.action and any(fc.data_path.startswith(f'pose.bones["{n}"]') for fc in _fcurves(r.animation_data.action))
                    if not has_keys: pb.rotation_quaternion = q
                else:
                    pb.rotation_euler = (math.radians(curl), 0, 0)
        elif n.startswith("lowerarm01"):
            pass
print("LOOK_OK limits", nlim)

# knit ribs readable: more colour contrast, real rib displacement
km = bpy.data.materials["BeanieWool"]
for n in km.node_tree.nodes:
    if n.type == 'VALTORGB': n.color_ramp.elements[0].color = (0.30, 0.02, 0.03, 1); n.color_ramp.elements[1].color = (0.90, 0.14, 0.10, 1)
    if n.type == 'TEX_WAVE': n.inputs['Scale'].default_value = 45
    if n.type == 'BUMP': n.inputs['Strength'].default_value = 0.6
bpy.data.objects["BeanieKnitMesh"].modifiers["rib"].strength = 0.006
bpy.data.objects["BeanieKnitMesh"].modifiers["rib"].texture.noise_scale = 0.006

for i in range(5):
    L = bpy.data.lights.new(f"FacadeWash{i}", 'AREA'); L.energy = 0; L.size = 12; L.color = (1.0, 0.85, 0.65)
    lo = bpy.data.objects.new(L.name, L); lo.location = CT + Vector((-40 + i * 20, -6, 2)); lo.rotation_euler = (math.radians(75), 0, 0)
    bpy.data.collections["CITY"].objects.link(lo)
    for f, e in ((1, 0), (F(31.8), 60000), (F(35.9), 0)):
        L.energy = e; L.keyframe_insert("energy", frame=f)

# ceiling light panels: prismatic diffuser grid (detail while it fills the lens)
pm_ = bpy.data.materials["CeilPanel"]; nt_ = pm_.node_tree; pp_ = nt_.nodes["Principled BSDF"]
br = nt_.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 40; br.inputs['Mortar Size'].default_value = 0.03
br.inputs['Color1'].default_value = (1, 0.98, 0.95, 1); br.inputs['Color2'].default_value = (0.85, 0.92, 1.0, 1); br.inputs['Mortar'].default_value = (0.35, 0.4, 0.45, 1)
tcx = nt_.nodes.new('ShaderNodeTexCoord'); nt_.links.new(tcx.outputs['UV'], br.inputs['Vector'])
nt_.links.new(br.outputs['Color'], pp_.inputs['Emission Color']); pp_.inputs['Emission Strength'].default_value = 2.5
# rink glass: crystal clear (no frosting veil), faint reflections only
g = bpy.data.materials["Glass"]; gn = g.node_tree.nodes; gp = gn["Principled BSDF"]
for lk in list(gp.inputs['Roughness'].links): g.node_tree.links.remove(lk)
gp.inputs['Roughness'].default_value = 0.0; gp.inputs['IOR'].default_value = 1.02; gp.inputs['Transmission Weight'].default_value = 1.0
gp.inputs['Base Color'].default_value = (1, 1, 1, 1)

# clinic dressing in the 23-24 s view: cabinet + lamp + poster on the south wall, plant
C_CL = bpy.data.collections["CLINIC"]
ph_blend("drawer_cabinet", C_CL, (-30.5, -2.55, 0), rot_z=0.0)
ph_blend("desk_lamp_arm_01", C_CL, (-30.5, -2.55, 0.84), rot_z=math.radians(40), scale=1.3)
ph_blend("potted_plant_04", C_CL, (-26.2, -2.7, 0), scale=1.3)
plane("Poster3", 0.6, 0.84, (-27.0, -2.99, 1.6), pm, C_CL, rot=(math.pi / 2, 0, 0))
