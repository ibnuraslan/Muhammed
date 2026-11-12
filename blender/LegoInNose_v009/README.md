# LegoInNose_v009: acting fixed and synced to your voiceover (READY TO RENDER)

This is Connect03's acting-fix version **LegoInNose_v008c** (branch `claude/connect03-lego-in-nose`, commit 6e93a4a), retimed so each story beat lands on its words in your recording `LegoInNose_v009_VO.mp3`.

What changed against v007 (the render you stopped):
- Every hand uses the shared hand library. The bricks, tweezers, inhaler, tissue, gamepad and phone are held IN the fingers on every frame (the prop check is 0 for held items).
- No camera cuts or tilted frames. Every story beat shows a face.
- Hands out of bodies: Mom's arm no longer passes through her chest, and the boy's resting hands sit on his thighs.
- The walls between rooms are split, so there is no black flicker at 30.5 s.
- The director checked every beat frame in the synced file.

Render:
- Frames **1–2036** at 60 fps (33.9 s).
- The voiceover is packed into the .blend as a sound strip (channel 1), and the same mp3 is next to it.
- Render as described in SETTINGS.md, then lay `LegoInNose_v009_VO.mp3` under the frames starting at frame 1.
