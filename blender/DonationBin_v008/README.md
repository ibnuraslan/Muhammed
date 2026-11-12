# DonationBin_v008: acting fixed and synced to your voiceover (READY TO RENDER)

This is Connect09's acting-fix version **DonationBin_v007b** (branch `claude/connect09-donation-bin`, commit 6033b0b), retimed so each story beat lands on its words in your recording `DonationBin_v008_VO.mp3`.

What changed against v005 (the previous synced version):
- The whole fall and confinement is re-staged:
  - She is pushed by her shoulder blades.
  - She lands on her back and sits up on the clothes.
  - She stands upright at the walls, with her palms on the walls and the flap.
  - She lies curled in the middle of the clothes for "three days".
  - At the rescue she lifts her head, then pushes up and climbs out.
- Faces read on the beats, including the scream from front three-quarters.
- Hands use the shared hand library: flat palms on the walls, relaxed idle hands.
- **One continuous camera.** The camera passes into and out of the bin by pushing through the wall. The only position jumps are hidden on fully covered wall frames.
- QA on the source package: HOVER 0, CLAW 0, FACEPRESS 0, INSIDE 0. The CAMJUMP flags are only the 3 covered pushes. clip_scan: 0 on camera.

Render:
- Frames **1–2388** at 60 fps (39.8 s).
- The voiceover is packed into the .blend as a sound strip (channel 1), and the same mp3 is next to it.
- Render on RenderStreet as described in SETTINGS.md, then lay `DonationBin_v008_VO.mp3` under the frames starting at frame 1.

Beat anchors (v007b frame → v008 frame): 1→1, 151→115, 295→265, 505→451, 769→673, 961→847, 1321→1285, 1501→1465, 1843→1753, 1981→1867, 2095→1993
