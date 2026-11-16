# v002b checks (all on the packed KidHacker_v002_60fps.blend)

- clip_scan (step 6): 0 bad ranges.
- body_prop_cross (step 3; keyboard, mouse, desks, chairs, carrel panel, door leaves, jack/plug): 2 visible hits, S11 f1015-1021, the pressing fingertip on the key top (the intended 0-0-0-0 press).
- qa_check (step 6, beats.json):
  - CAMJUMP 18: every one is on a hard cut (one per shot boundary).
  - EMPTY 350: object shots that show what the VO names (jack S03-S04, screens S05-S07, S10, S13-S14, S17, S19, clock S18) and S11 keyboard macro (hands only).
  - FILL: S04 wall jack on its panel (close-up by design); S01/S09 a little hair at the frame edge.
  - BACKHEAD 2: S17/S19 over-the-shoulder shots onto the screen (her face is in the adjacent shots).
  - INSIDE 12 (S21): false positive. The office walls are single-sided planes, and the camera looks at their back faces. The preview shows the room correctly.
- limb_check (step 2):
  - ARMBODY "2 pts": the known shoulder false positive (upperarm01 points next to the shoulder).
  - Kid 3-6 pts: probed. Only upper-arm axis points 2-7 sit under the shoulder/deltoid skin of the child's short upper arm; no forearm or wrist point is ever inside. No arm passes through the body in the preview.
  - ARMBACK 13 (S17 f1481-1505): false positive. The wrist is 25 cm IN FRONT of the shoulder, on the mouse (verified from the bones). The check takes the facing direction from the jaw, which flips while her head is pitched down.
