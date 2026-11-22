"""v009 airport payoff (exec'd from 04_fx_camera.py, shares its namespace: O, bone_w, Carry, foot_mask, V, Matrix, sc, AX).
Two passengers in socks carry a sneaker flat on each palm, set them into a tray (released over the tray, they settle onto
its floor), and the tray rides the belt toward the X-ray with the traveller's tray from 1506."""
AIRPAX = (("AirPaxA", "Tray_2", 1462), ("AirPaxB", "Tray_3", 1500))
for nm, tray_nm, f_rel in AIRPAX:
    rig = O[nm]
    for s_ in "LR":
        foot_mask(nm, s_, 1)                     # never masked: knit sock material on the feet (shoes are off)
    tray = O[tray_nm]
    for s_, src in (("L", "Shoe_L_Trav"), ("R", "Shoe_R_Trav")):
        sh = O[src].copy(); sh.data = O[src].data.copy(); sh.name = "Shoe_%s_%s" % (s_, nm)
        sh.animation_data_clear()
        for c_ in list(sh.constraints): sh.constraints.remove(c_)
        O[src].users_collection[0].objects.link(sh)
        cr = Carry(sh)
        W = bone_w(rig, "wrist." + s_, 1400)
        hd = (W.to_3x3() @ V((0, 1, 0))).normalized()              # wrist bone axis ~ the hand's direction
        Mshoe = Matrix.Translation(W.translation + hd * 0.07 + V((0, 0, 0.035)))   # sole on the palm, toe forward (+Y)
        cr.hold(rig, "wrist." + s_, 1, Mshoe)
        cr.cons[-1].inverse_matrix = W.inverted() @ Mshoe
        cr.free(f_rel)                           # let go over the tray
        park = bpy.data.objects["Park_%s_%d" % (sh.name, f_rel)]
        sc.frame_set(f_rel - 1); Mw = sh.matrix_world.copy()
        sc.frame_set(f_rel); Mt = tray.matrix_world.copy()
        floor_z = Mt.translation.z + 0.012
        zmin = min((Mw @ V(c)).z for c in sh.bound_box)
        park.keyframe_insert("location", frame=f_rel)
        park.location = park.location - V((0, 0, max(0.0, zmin - floor_z))); park.keyframe_insert("location", frame=f_rel + 6)
        # rides with the tray once the belt starts (no pop: inverse taken at the switch frame)
        sc.frame_set(1505); Ms = sh.matrix_world.copy(); Mt = tray.matrix_world.copy()
        c = sh.constraints.new('CHILD_OF'); c.target = tray
        c.inverse_matrix = Mt.inverted() @ Ms
        o_ = cr.cons[-1]
        o_.influence = 1.0; o_.keyframe_insert("influence", frame=1505); o_.influence = 0.0; o_.keyframe_insert("influence", frame=1506)
        c.influence = 0.0; c.keyframe_insert("influence", frame=1505); c.influence = 1.0; c.keyframe_insert("influence", frame=1506)
        cr.cons.append(c)
        cr.done()
print("AIRPAX_SHOES", [o.name for o in bpy.data.objects if o.name.startswith("Shoe_") and "AirPax" in o.name])
