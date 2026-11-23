"""v010 airport shoes (exec'd from 04_fx_camera.py, shares its namespace: O, bone_w, Carry, foot_mask, V, Matrix, sc, AX).
Director 13-14: every sneaker is held by its collar in the hand (Child Of the wrist from frame 1), set flat on its spot on
the tray floor at the release frame (no pop, no float), then rides with the tray (Child Of the tray from 1506).
Spots / grip offset are the same numbers as airport_v010.py."""
GRIP_OFS = V((0.0, 0.09, -0.24)); TRAY_FLOOR = 0.762
SPOTS = {"Tray_1": (AX + V((-0.96, 0.0, TRAY_FLOOR)), AX + V((-0.74, 0.0, TRAY_FLOOR))),
         "Tray_2": (AX + V((-0.21, 0.0, TRAY_FLOOR)), AX + V((0.01, 0.0, TRAY_FLOOR))),
         "Tray_3": (AX + V((0.54, 0.0, TRAY_FLOOR)), AX + V((0.76, 0.0, TRAY_FLOOR)))}
CARRY = (("Traveller", "Tray_1", 1440, ("Shoe_L_Trav", "Shoe_R_Trav")), ("AirPaxA", "Tray_2", 1486, None), ("AirPaxB", "Tray_3", 1500, None))
RZ = Matrix.Rotation(math.pi, 4, 'Z')          # model toe is -Y: turn it to point +Y (the way they face)
for nm, tray_nm, f_rel, names in CARRY:
    rig = O[nm]
    for s_ in "LR": foot_mask(nm, s_, 1)        # in socks: the feet show the knit sock material
    tray = O[tray_nm]
    for k, s_ in enumerate("LR"):
        if names:
            sh = O[names[k]]
        else:
            src = O["Shoe_%s_Trav" % s_]
            sh = src.copy(); sh.data = src.data; sh.name = "Shoe_%s_%s" % (s_, nm)
            src.users_collection[0].objects.link(sh)
        sh.animation_data_clear()
        for c_ in list(sh.constraints): sh.constraints.remove(c_)
        cr = Carry(sh)
        W = bone_w(rig, "wrist." + s_, 1400)
        Mshoe = Matrix.Translation(W.translation + GRIP_OFS) @ RZ
        cr.hold(rig, "wrist." + s_, 1, Mshoe)
        cr.cons[-1].inverse_matrix = W.inverted() @ Mshoe
        cr.free(f_rel)
        park = bpy.data.objects["Park_%s_%d" % (sh.name, f_rel)]
        park.matrix_world = Matrix.Translation(SPOTS[tray_nm][k] + V((0, 0, 0.002))) @ RZ     # flat on the tray floor
        sc.frame_set(1505); Ms = sh.matrix_world.copy(); Mt = tray.matrix_world.copy()
        c = sh.constraints.new('CHILD_OF'); c.target = tray
        c.inverse_matrix = Mt.inverted() @ Ms
        o_ = cr.cons[-1]
        o_.influence = 1.0; o_.keyframe_insert("influence", frame=1505); o_.influence = 0.0; o_.keyframe_insert("influence", frame=1506)
        c.influence = 0.0; c.keyframe_insert("influence", frame=1505); c.influence = 1.0; c.keyframe_insert("influence", frame=1506)
        cr.cons.append(c)
        cr.done()
print("AIRPORT_SHOES", [o.name for o in bpy.data.objects if o.name.startswith("Shoe_") and ("AirPax" in o.name or "Trav" in o.name)])
