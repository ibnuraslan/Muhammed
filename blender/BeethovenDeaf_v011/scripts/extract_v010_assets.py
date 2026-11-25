import bpy, sys
out = sys.argv[sys.argv.index("--")+1]
sc = bpy.context.scene
names = ["Piano","Bench","Candelabra_A","XRay_Skull"] + [o.name for o in bpy.data.objects if o.name.startswith("Ear_")]
# pick a frame where ear parts are posed (x-ray beat)
sc.frame_set(900)
keep = []
for n in names:
    o = bpy.data.objects[n]
    if o.type != 'MESH': continue
    dg = bpy.context.evaluated_depsgraph_get()
    M = o.matrix_world.copy()
    c = o.copy(); c.data = o.data.copy(); c.animation_data_clear()
    for k in list(c.constraints): c.constraints.remove(k)
    c.parent = None; c.matrix_world = M
    for m in list(c.modifiers):
        if m.type in ('ARMATURE',): c.modifiers.remove(m)
    c.name = "SRC_" + n
    c.hide_render = False; c.hide_viewport = False
    keep.append(c)
    print("KEEP", c.name, tuple(round(x,3) for x in M.translation), tuple(round(d,3) for d in o.dimensions), [m.name for m in c.data.materials])
bpy.data.libraries.write(out, set(keep), fake_user=True, compress=True)
