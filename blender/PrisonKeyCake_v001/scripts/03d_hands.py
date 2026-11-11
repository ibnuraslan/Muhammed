# Hands pass (client, Nov 11 23:00): joint limits on every finger/thumb/wrist, relaxed curl on FK rigs. Exec'd at the end of 03_animate.py.
def limit(pb, x, y, z):
    c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.name = "HandLimit"
    c.use_limit_x = c.use_limit_y = c.use_limit_z = True
    c.min_x, c.max_x = R_(x[0]), R_(x[1]); c.min_y, c.max_y = R_(y[0]), R_(y[1]); c.min_z, c.max_z = R_(z[0]), R_(z[1])
    c.euler_order = 'XYZ'
NLIM = 0
for arm in [o for o in bpy.data.objects if o.type == 'ARMATURE' and "finger2-1.L" in o.pose.bones]:
    for s_ in "LR":
        for k in range(1, 6):
            for j in range(1, 4):
                n = "finger%d-%d.%s" % (k, j, s_)
                if n not in arm.pose.bones: continue
                if k == 1: limit(arm.pose.bones[n], (-15, 80), (-40, 40), (-40, 40))      # thumb: natural cone
                else: limit(arm.pose.bones[n], (0, 90), (-10, 10), (-10, 10) if j == 1 else (-3, 3))   # fingers: forward only
                NLIM += 1
        limit(arm.pose.bones["wrist." + s_], (-60, 60), (-35, 35), (-25, 25)); NLIM += 1
# relaxed curled hands on FK rigs (president, crowd): constant keys
for arm in [o for o in bpy.data.objects if o.type == 'ARMATURE' and "IK_hand.L" not in o.pose.bones and "finger2-1.L" in o.pose.bones]:
    R_fk = Rig(arm)
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s_ in "LR": curl(R_fk, s_, 1, 28, thumb=16)
print("HANDS limits", NLIM)
