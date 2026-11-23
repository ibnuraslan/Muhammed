# hand_poses.py: shared hand poses for the MPFB default rig

1. Load it: `exec(open("blender/pipeline/hand_poses.py").read())` after `anim_lib.make_human_ctrl(rig)`.
2. Once per rig, add the STYLE_ANIMATED joint limits: `add_hand_limits(rig)`.
3. To key a pose: `apply_pose(rig, "L", "wrap_grip", frame)`. Use `amount=0.5` to blend from the current pose and `spread=6` (degrees) to fan the fingers.
4. The poses are `relaxed`, `wrap_grip`, `power_fist`, `pinch`, `tripod`, `flat_palm`, `point`, `cup_hold`, `open_alarm`, `shield` and `hold_flat_object`.
5. To place only the hand: `place_hand(rig, "R", f, palm_point, palm_normal, finger_dir)`. `palm_normal` points from the hand toward what it touches.
6. To grip an object: `grip_object(rig, "R", f, obj, contact_point, approach_dir)`. It places IK_hand and closes each finger until it touches the surface, and the thumb opposes. It returns the contacts.
7. Objects thinner than 12 mm (paper, cards, mask edges) get a pinch automatically, with thumb and index on the two faces. Everything else gets a wrap. Pass `finger_dir` to control which way the fingers wrap.
8. Keep the hand inside the wrist limits (±60° flex, ±25° side): palm down or palm toward the body reaches anything. "Fingers up, palm back" will be clamped.
9. Key a pose on every frame where the hand changes (grab, hold, release). In between, Blender interpolates the quaternions, and each one stays within limits.
10. Proof: `hand_poses_sheet.jpg` (every pose, both hands, front and side, plus three `grip_object` demos) and `hand_poses_report.txt` (0 joint violations). Rebuild them with `blender -b --python hand_poses_demo.py -- <out_dir>`.
