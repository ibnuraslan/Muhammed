# StanleyCup v007d: the director's review of b7569ee (6 items)

Builds on v007c (7f3795a), which had already fixed the hand at the lens, the x-ray cup and the lid and impact blur.
The 1530-frame timeline and the story-beat frames are unchanged (1, 139, 271, 391, 607, 973, 1285, 1417).
- Preview: `review/StanleyCup_v007d_preview.mp4` (every 5th frame, 270×480, Cycles 4 samples + OIDN, 12 fps, 25.5 s).
- Before/after: `review/director_items_before_after.jpg` (top: b7569ee, bottom: v007d).

| # | Item | v007d |
|---|---|---|
| 1 | 2.3 s of siding, then 1 s of plain white wall | The house wide shot, then the bullet into the siding and the hit (beat 2 at f139). A clean cut at f150 goes inside: the couple are in the foreground and the window wall is behind them, where the bullet bursts out (f262). A clean cut at f266 reverses onto their faces for beat 3. No plain-wall frames are left. |
| 2 | f501–536: jacket and blurred hands fill the frame | He is framed from his left (his face, hands clear). A clean cut at f541 goes to the wide shot. |
| 3 | 3 s of cup and macro blur, giant bullet, transparent cup | One medium shot, f945–1010 (about 1.1 s): the cup sharp at f/11, the bullet hitting with sparks, her face behind it. A clean cut at f1011 goes to both reactions. No transparent cup, and no macro. |
| 4 | f536–566 head filling the frame; f706 blurred hand-on-cup macro | The f541 cut removes the head-filling transition. The condensation shot is at 40 mm, f/8 (sharp). |
| 5 | 2.7 s under the table: legs and a tiny bullet | About 1 s in total, all after the bullet falls from the table (beat 7, f1285). The bullet drops off the table edge (seen from her side). Then a low close-up of it landing and bouncing on the floor (f1304–1316, sharp at f/16, the bullet clearly visible). Then a clean cut at f1317 to her face reacting (f1317–1350). A clean cut at f1351 goes to the end two-shot. While he half-stands between the bullet and her, no single low angle shows both the bullet and her face, so the beat is two short shots. |
| 6 | f1041–1056 blurred cup bottom over the tablecloth | Gone: that time is the two-shot from f1011. |

## Blur / empty check (every preview frame, `review/sharpness_check.py`, `review/sharpness_v007d.txt`)
- Score: the 99th percentile of |Laplacian|. Sharp, readable frames score 40–85; defocused frames, plain walls and frame-filling cups score 3–21.
- The only run of 3 preview frames under 25 is f1306–1316: the low floor close-up of the bullet bouncing. That is exactly 0.25 s; the bullet is sharp and the plain floor scores low.
- Nothing else is under 25 for more than 1 preview frame, except f106–111, 2 frames of the bullet passing the lens in the exterior chase.

## Checks on the final build
- `review/rules_check.py` (every 2 frames): 0 arm over the other person, 0 floating hands, 0 camera within 12 cm of a body or 10 cm of anything else.
- qa_check (step 6): EMPTY 39, FILL 0, INSIDE 0, BACKHEAD 0, HOVER/CLAW/FACEPRESS 0 (v007: EMPTY 148, FILL 32, INSIDE 15).
- clip_scan: 0. hand_audit: 0. audit: feet, seat, bullet and camera all 0; fingers 9 mm at most.
- limb_check: ARMBODY 465. All are points within 4 cm of the shoulder joint centre (`review/limb_points_v007d.json`).

## Update: the director's review of v007c (three trims)
1. Floor: already about 1 s in v007d. The bullet goes over the edge, a 0.2 s close-up of it landing, then her face, then from f1351 the two-shot of them.
2. Outside: already short in v007d. The wide house shot, then about 0.6 s on the siding through the hit, then the cut inside at f150.
3. f851–1031, cup and forearm close-up: from f880 a clean cut goes to the two-shot from her side wall, with both faces and the cup between them. It holds until the impact medium shot at f945 (cup sharp, her face behind it).
Rules check, qa_check and clip_scan on f780–1020: 0 / no flags / 0. The full-film qa_check is unchanged (EMPTY 39). The preview MP4 and the package are rebuilt.
