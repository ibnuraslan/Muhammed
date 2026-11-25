# 02c: the brass rod is clamped between the incisors (its end 10 mm behind the incisor fronts, the jaw opened just for it)
# and passes through the collar of the clamp on the piano case; it slides a little in the collar as the head moves.
# Cyan rings leave the collar and travel up the rod to the teeth at constant size and speed.
BITE = empty("Bite", BITE_HEAD, size=0.01)
c = BITE.constraints.new('CHILD_OF'); c.target = COMP; c.subtarget = "head"; c.inverse_matrix = Matrix.Identity(4)
ROD = O["Rod"]; CLAMP = O["RodClamp_Point"]
ROD.location = (0, 0, 0); ROD.rotation_euler = (0, 0, 0)
cl = ROD.constraints.new('COPY_LOCATION'); cl.target = BITE
dt = ROD.constraints.new('DAMPED_TRACK'); dt.target = CLAMP; dt.track_axis = 'TRACK_Z'
ds = []
for f in range(1, END + 1, 6):
    sc.frame_set(f); ds.append((BITE.matrix_world.translation - CLAMP.matrix_world.translation).length)
DMIN, DMAX = min(ds), max(ds)
L = DMAX + 0.022
for v in ROD.data.vertices: v.co.z = v.co.z * (L / 0.92)
log("rod: mouth-collar distance", round(DMIN, 3), "-", round(DMAX, 3), "rod length", round(L, 3))
# where the rod meets the head: it must enter between the lips (check the lip clearance later in the audits)
DAVG = (DMIN + DMAX) / 2
# ---- rings
RINGS = sorted([o for o in O if o.name.startswith("RodRing")], key=lambda o: o.name)
for r_ in RINGS:
    r_.parent = ROD; r_.matrix_parent_inverse = Matrix.Identity(4); r_.location = (0, 0, 0); r_.scale = (0, 0, 0)
    for k in ("location", "scale"): r_.keyframe_insert(k, frame=1)
TRAVEL = 66
spawn = list(range(T["pianos"] - 8, T["into"] + 24, 13))
col = O["RodClamp_Collar"]; cm = O["M_Brass"] if "M_Brass" in O else None
flash = bpy.data.materials["M_Brass"].copy(); flash.name = "M_CollarFlash"; col.data.materials[0] = flash
fp = flash.node_tree.nodes["Principled BSDF"]; fp.inputs["Emission Color"].default_value = (0.25, 0.92, 1.0, 1)
fp.inputs["Emission Strength"].default_value = 0.0; fp.inputs["Emission Strength"].keyframe_insert("default_value", frame=1)
for i, f0 in enumerate(spawn):
    r_ = RINGS[i % len(RINGS)]
    z0 = DAVG - 0.004; z1 = 0.006
    def kk(fr, z, s):
        r_.location = (0, 0, z); r_.scale = (s, s, s)
        r_.keyframe_insert("location", frame=fr); r_.keyframe_insert("scale", frame=fr)
    kk(f0 - 1, z0, 0.0); kk(f0, z0, 0.55); kk(f0 + 5, z0 - (z0 - z1) * 5 / TRAVEL, 1.0)
    kk(f0 + TRAVEL - 6, z1 + (z0 - z1) * 6 / TRAVEL, 1.0); kk(f0 + TRAVEL, z1, 0.0)
    for fr, v in ((f0 - 2, 0.0), (f0 + 1, 6.0), (f0 + 8, 0.0)):
        fp.inputs["Emission Strength"].default_value = v; fp.inputs["Emission Strength"].keyframe_insert("default_value", frame=fr)
for r_ in RINGS:
    if r_.animation_data:
        for fc in iter_fcurves(r_.animation_data.action):
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
RING_LAST = spawn[-1] + TRAVEL
log("rings", len(spawn), "spawned", spawn[0], "-", spawn[-1])
