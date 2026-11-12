# DwarfGiant_v002 — farm package

The story of the man who lived as both a dwarf and a giant (1917 Austria; generic face, no real likeness). 39.0 s, one continuous camera.

- `DwarfGiant_v002_60fps.blend`: packed and compressed, 92.5 MB. Opens in factory-startup Blender 5.2.2. Render settings are in SETTINGS.md.
- `beats.json`: beat start frames for the VO retime (`pipeline/retime_to_vo.py`).
- `CREDITS.md`: CC-BY block for the video description.
- Build scripts and review sheets: `../DwarfGiant_v001/scripts`, `../DwarfGiant_v001/review` (`D_package_1s.jpg`, `D_hand_closeups.jpg`, `D_hand_audit.txt`).

## Look and hands (client 22:45 / 23:00)
- `pipeline/anim_look.py` was run with `--no-sky`. The cutaways use a cyan to near-white gradient card.
- Limit Rotation (local space) is on every finger and thumb, plus FK wrists. Elbows use IK hinge limits (0–145°, no twist).
  - On IK-driven hands the wrist limit is muted, because the solved orientation is set explicitly and a clamp folded the hand into a mitten.
- Fingers have a relaxed curl. The hero's hand is flat on the desk in beat 5.
- The BVH hand audit runs every 2 frames: hand vs hand, own torso/head/clothes, and other characters. The result is in `D_hand_audit.txt`.

## Known issues
- **No officer caps in this version.** The CC-BY peaked cap lost its glTF axis conversion on import and read as a disc over the face, so it was removed rather than shipped broken. Fix: keep the import parent's rotation, then Child Of the head bone.
- Growth is a uniform armature scale plus extra scale on the hands, feet, jaw and tongue. Sleeves and trouser hems do not ride up.
- The ear-cup gesture at about 23–24 s is a large hand close to the lens. It's readable, but not elegant.
- Surgeon 2's reaching hand is fairly open. It has a relaxed curl, but not a grip.
- The skin dive (≈3.0 s), wall pass (≈25 s) and lying-head dive (≈28 s) are each kept to a few frames. At 1 still per second one of them can still land on a soft macro frame.
- No VO is in the file yet.
