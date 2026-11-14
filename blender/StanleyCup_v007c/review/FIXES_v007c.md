# StanleyCup v007c: the director's 5 items on v007b (review of 89e21b4)

Builds on v007b (b7569ee: the hold fixes plus the rules 1–4 pass). Same 1530-frame timeline and story-beat frames
(1, 139, 271, 391, 607, 973, 1285, 1417), so the VO warp applies unchanged.
Preview: `review/StanleyCup_v007c_preview.mp4` (every 5th frame, 270×480, Cycles 4 samples + OIDN, 12 fps, 25.5 s).
Before/after on each item: `review/director_items_before_after.jpg` (top: 89e21b4, bottom: v007c).

| # | Item (89e21b4) | Fix in v007c |
|---|---|---|
| 1 | n103–107 (f516–536): his hand swipes past the lens | f455–540: he is framed from his left side, so his reaching right arm is on the far side and never near the lens. A clean cut at f455 goes from her face to his, so the camera no longer swings round his head. |
| 2 | n112–125 (f561–626): the frame goes out of focus and an orange blob crosses the room | The bullet-level shots ride 25 cm above and behind the bullet, so the room stays sharp (sharpness 53–60) and the bullet reads small and crisp. |
| 3 | n33–56 (f166–281): cavity fly-through blur; n91 (f456): only hair and wall | No cavity. The outside bullet-hole shot holds at f/16 and is sharp, with splinters flying. A clean cut at f254 goes inside; the drywall is on screen for 8 frames (2 preview frames, 0.17 s) before the bullet bursts out, then a whip-pan to the couple. f456 is now the clean cut to his face. |
| 4 | n158–162 (f791–811): lid fills the frame out of focus. n188–212 (f941–1061): impact blur and the see-through x-ray cup | f790 is a clean cut from her face to his, with no pass over the lid. Impact: 50/48 mm at f/11, the cup and bullet sharp, macro held f955–1000 (~0.75 s). Then the dent is shown from outside at f/8 (f1040, f1100). The x-ray is removed and the cup stays opaque. The f920 approach is at f/8. The condensation macro (f686–716) is widened to 40 mm at f/8. |
| 5 | n248–249: camera dives through the table edge and cloth | The camera never passes the table. The bullet drop is filmed from her side, then a clean cut at f1292 goes to the floor-level shot under the table. |

## Blur / empty check (every preview frame)
`review/sharpness_check.py` gives each frame the 99th percentile of |Laplacian| on the 270×480 preview (`review/sharpness_v007c.txt`).
- Sharp, readable frames score 40–85. Defocused frames, plain walls and cup-filling macros score 3–21.
- The only run of 3 or more consecutive preview frames (0.25 s or longer) under 25 is f196–261:
  - f196–251 is the outside bullet-hole shot. It is in focus at f/16 and scores low only because the painted siding is smooth (checked by eye; see the before/after).
  - f256–261 is the 2 preview frames (0.17 s) of drywall before the bullet bursts out.
- Every other stretch is 2 preview frames or fewer (f106–111 and f1111–1116 are fast moves; f141, f181 and f951 are single frames).

## Checks on the final build
- `review/rules_check.py`, every 2 frames over the whole film: 0 ARMOVER, 0 DETACHED, 0 BRUSH (`review/rules_v007c.json`).
- qa_check (step 6): EMPTY 107, FILL 0, INSIDE 0, BACKHEAD 0, HOVER/CLAW/FACEPRESS 0 (v007: 148/32/15/1). New EMPTY frames vs v007, all with no character in frame:
  - f679–685: the cup at the start of the condensation shot.
  - f985: the impact macro.
  - f1177–1189: the wide two-shot, with characters at 12–14% of the frame.
  - f1297: the floor shot.
- clip_scan: 0. hand_audit: 0. audit: feet, seat, bullet and camera all 0; fingers 9 mm at most.
- limb_check: ARMBODY 340. All are points within 4 cm of the shoulder joint centre (`review/limb_points_v007c.json`); no point further down the arm.
