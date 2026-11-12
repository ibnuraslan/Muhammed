# MonkeyHeadTransplant_v009: ON HOLD, DO NOT RENDER (floating pen and mask; fix in progress)

This is Connect02's acting-fix version **MonkeyHeadTransplant_v008c** (branch `claude/connect02-monkey-head-transplant`, commit faa47bf), retimed so each story beat lands on its words in your recording `MonkeyHeadTransplant_v009_VO.mp3`.

What changed against v007 (the render you stopped):
- Every hand goes through the shared hand library:
  - real grips on the head carry, the needle holder, forceps, bowl, gas knob and breathing bag
  - a pen pinch
  - a flat palm on the shoulder
  - relaxed idle hands
- The mimed clipboard is gone. The nurse no longer stands in the camera's path.
- Beat framings show faces: the surgeon at beat 1, the monkey in the chair at the last beat. The camera no longer goes inside the x-ray void.
- QA: HOVER, CLAW, FACEPRESS, INSIDE and CAMJUMP are all 0, and clip_scan is 0. The only roll is the intended tilt that keeps the lying monkey's face upright.

Render:
- Frames **1–1656** at 60 fps (27.6 s).
- The voiceover is packed into the .blend as a sound strip (channel 1), and the same mp3 is next to it.
- Render on RenderStreet as described in SETTINGS.md, then lay `MonkeyHeadTransplant_v009_VO.mp3` under the frames starting at frame 1.

Beat anchors (v008c frame → v009 frame): 1→1, 259→205, 391→379, 673→607, 889→817, 1027→949, 1207→1093, 1393→1267, 1561→1447
