# StanleyCup acting review (v005 → v007)

Half-second sheet of v005: `before_0p5s_a.jpg`, `before_0p5s_b.jpg` (270×480, 8 samples, frame = 1 + 30·n).
Story-beat frames stay fixed: 1, 139, 271, 391, 607, 973, 1285, 1417.

| v005 time / frames | Problem | Fix in v007 |
|---|---|---|
| 0.0–2.3 s (1–139) | OK: bullet-cam on the street, birds lift off. | – |
| 2.5 s (~151) | Frame filled by splinters right on the lens; nothing readable. | Camera starts 3 cm further back on the impact so the bullet + splintering siding read. |
| 4.5–6.0 s (271–361) beat 3 "a woman and her fiancé" | The couple are tiny in a wide frame for 1.5 s; faces unreadable on the beat; they barely move. | Camera pushes in across the room so both faces read by ~5.2 s; they are mid-conversation (he talks with one hand, she laughs and leans). |
| 6.5–10.5 s (391–631) | **He holds both hands palms-up in front of his chest for 4 s** (frozen "shrug" gesture). | Left hand flat on the table, right hand talks → then grips the table edge as he turns toward the sound → reaches toward her. |
| whole film | **Resting hands lie palm-UP on the table** (her at 0–10 s, him at the start) — not how people rest hands. | All resting hands re-keyed palm-down on the cloth. |
| 7.8–8.2 s (~470–500) | Frame shows only a wall/shelf and his hand: the orbit from her face to his looks at nothing. | Re-staged orbit: both faces stay in frame (two-shot over the table), then onto his face. |
| 13.0 s (~781) | Frame filled by a blurred tablecloth/napkin on the way from her face to the lid shot. | Extra framing keeps the camera high over the table between the two. |
| 14.0 s (~841) | His sleeve fills the lower half; the hand is a blur. | His reaching hand is framed from her side, with his face behind it. |
| 14.5–17 s (871–1021) | Her raised palms are held still. | Hands keep moving: they come up toward her face and flinch on impact. |
| 19.0 s (~1141) | Blurred floor and debris: no subject. | Wider framing on the flattened bullet with his reaching hand and her in the background. |
| 19.5–21.0 s (1171–1261) | His arm stays straight and rigid, reaching toward empty air for ~3 s. | His hand keeps travelling toward her forearm in slow motion, fingers opening. |
| 21.5 s (1285) beat 7, 23.5 s (~1411) | Frame filled by a table leg. | Camera stays outside the table legs; the bullet drop, his legs and her feet read. |
| 22.0–23.5 s (1321–1411) | His shoe dominates the floor shots. | Floor camera looks along the floor away from his feet. |
| 23.6–24.0 s (1417–1441) beat 8 "saving her life" | His jeans leg fills the frame; her face is unreadable on the beat. | Crane rises clear of him; her face is readable from 1417. |
| 24–25.5 s (1441–1530) | **He hovers in a half-squat over the table for 2 s**, and his hand floats near her arm without touching it. | He stands up properly (legs straight, feet planted), leans over the corner and holds her forearm. |
| 16.2–18.6 s | OK: impact, sparks, x-ray ripples. | – |
| 0.0–1.0 s | OK. | – |

## Also fixed after the director's self-check / QA rules (Nov 12, 14:40–15:45)
| Item | Fix |
|---|---|
| Resting hands hovered 5–6 cm above the cloth (QA HOVER) | Palms placed ON the cloth with `hand_poses.place_hand` + `flat_palm`; her right hand rests on her lap (her wrist can't lie flat that far away). Her chair moved 10 cm closer to the table so her forearms are not steep. |
| His left hand beside his plate, her right hand beside her glass (QA HOVER) | Hands moved clear; her plate, glass and napkin moved. |
| Their hands touching on the table (f423–445) | His right and her left hand moved apart. |
| Her alarm hands bent like claws (~17 s) | `hand_poses` `open_alarm`, palms out, in front of her (not on her face). |
| Hand pressed into her nose/face at impact | Hands in front of the body; no face contact. |
| Hand-set finger angles | Replaced everywhere by `pipeline/hand_poses.py` poses (relaxed, flat_palm, open_alarm, wrap_grip) with its `add_hand_limits`. |
| Cup lifted into her blouse at the end | Shorter lift. |
| Back of his head on beat 7 (f1285) | Camera at the table end: his profile, her face, the falling bullet. |

## qa_check.py exceptions kept (qa_v007.json; EMPTY 166, FILL 36, INSIDE 15, BACKHEAD 1; HOVER 0, CLAW 0, FACEPRESS 0)
| Frames | Flag | Why it is intended |
|---|---|---|
| 1–270 | EMPTY / FILL / INSIDE | Beats 1–2: the subject is the bullet. Street bullet-cam, then the camera flies with it through the siding hole, the stud bay and the drywall hole (the "inside" and "surface < 12 cm" flags are the fly-through). The house and the couple, through the window and the hole, are in shot. |
| 691–703, 769–811, 943–1135 | EMPTY (character < 15 %) / FILL Tumbler_Inner / INSIDE (1093–1105) | Beats 5–6: the hero is the tumbler. Macro on the condensation, the lid and ice, the impact and sparks, and the x-ray dive into the cup (the camera passes through the ghosted steel by design). Her or his face is in the back of most of these. |
| 1309–1399 | EMPTY / FILL RoomFloor | Beat 7, "dropped harmlessly to the floor": floor-level close-up of the bullet bouncing and rolling to a stop. |
| 445–451, 733–739 | FILL hair 25–31 % | Close-ups of her frightened face. Her long hair fills the top of the frame, and the face is fully readable. |
| 1417 | BACKHEAD Fiance | Beat 8 "saving her life": the subject is her (face to camera, readable). He is leaning in over the corner in the foreground; his head is at the frame edge. |

## clip_scan.py (clip_v007.json): 2 single frames, not real contact
f889 and f907 (his right hand, "other"). At those frames none of his finger or wrist points is within 8 cm of her body or blouse (checked with a nearest-surface query); the hits come from an inward-facing open clothing surface inside clip_scan's 0.5 m search. Not visible on camera.

## Note on the after sheet
`after_0p5s_a/b.jpg` were rendered from the package built at 15:50. The final package (16:03) differs only in his slow-motion reach (13–17 s), which is 4–5 cm shorter. Hand close-ups and every audit/QA file are from the final build.

## 6-point self-check (ACTING_FIX_04-10.md)
1. Hands touch what they hold: checked (handle wrap, forearm hold, chest, flat palms on the cloth, hand on lap).
2. No claws: checked (alarm hands open_alarm, idle hands relaxed/flat_palm).
3. Nothing pressed into a face: checked (no hand on face; QA FACEPRESS 0).
4. No empty, blurred or black cells and no back-of-head on beats: checked by eye on the after sheets. The bullet- and cup-only cells and the 1417 foreground head are listed above as intended.
5. Close-ups show hands: checked (`hand_closeups.jpg`, all aimed at the hand).
6. hand_poses.py used: checked (all finger poses, limits and table palms come from the library).
