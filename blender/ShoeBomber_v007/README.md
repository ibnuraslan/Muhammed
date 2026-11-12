# ShoeBomber_v007: acting fixed and synced to your voiceover (READY TO RENDER)

This is Connect07's acting-fix version **ShoeBomber_v006c** (branch `claude/connect07-shoe-bomber`, commit c423808), retimed so each story beat lands on its words in your recording `ShoeBomber_v007_VO.mp3`.

What changed against v005 (the previous synced version):
- Every beat re-acted to the client's bar: real grips (hand_poses library), no claws, no hands through bodies, faces readable on every beat.
- **One continuous camera.** The cabin framings are joined by real moves over the seat backs. The only jumps are hidden inside the covered wipes: the black push into the shoe and the two cloud banks.
- QA on the source package: HOVER 0, CLAW 0, FACEPRESS 0, BACKHEAD 0. clip_scan reports 0 bad ranges.

Render:
- Frames **1–1469** at 60 fps (24.5 s). The voiceover runs 23.9 s.
- The voiceover is packed into the .blend as a sound strip (channel 1), and the same mp3 is next to it.
- Render on RenderStreet as described in SETTINGS.md, then lay `ShoeBomber_v007_VO.mp3` under the frames starting at frame 1.

Beat anchors (v006c frame → v007 frame): 1→1, 199→157, 373→289, 481→373, 655→505, 769→625, 1069→871, 1249→979, 1393→1135
