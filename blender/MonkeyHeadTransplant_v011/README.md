# MonkeyHeadTransplant_v011: fixed and synced to your voiceover (READY TO RENDER)

This is Connect02's version **MonkeyHeadTransplant_v008e** (branch `claude/connect02-monkey-head-transplant`, commit 4a4179b), retimed so each story beat lands on its words in your recording `MonkeyHeadTransplant_v011_VO.mp3`. It replaces v009 and v010. v011 also puts the forceps and needle holder IN the fingers during the stitching (measured: at most 0.6 cm from the fingertips on every frame).

What was wrong in v009, and is now fixed:
- **Marker pen:** it floated upright and drew by itself. It is now IN the surgeon's right-hand pinch on every frame, and its tip touches the skin where each dash appears. He then sets it down on the drape.
- **Masks:** they hung off the faces. All three masks are now bound to the head and fitted onto the face.
- **Tools:** the forceps and needle holder floated 4–7 cm from the fingers. They now sit in the pinch, 0 cm from the fingertips.
- **Trolley:** it is pushed by the nurse's hands, and the tray, instruments and bowl ride on it.
- **Cause:** the hand rotation limits were applied after the grips were solved, which twisted the hands away from what they held. The limits are now applied first.
- **Checks:** the automatic checks now include props moving without a hand (PROPMOVE) and worn items off the face (ATTACH). Both are 0 here, apart from the wall-clock hands.
- **Director check:** the director checked the pen, mask and beat frames in this synced file.

Render:
- Frames **1–1656** at 60 fps (27.6 s).
- The voiceover is packed into the .blend as a sound strip (channel 1), and the same mp3 is next to it.
