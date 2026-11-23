# SurgeonBrandsLivers_v012: rebuilt against the client's 34-item rejection list

Built on the approved and synced `SurgeonBrandsLivers_v011` (left untouched on the director branch). The voiceover, beat timing and frame range are the same: **frames 1–1644 at 60 fps**, with the VO `SurgeonBrandsLivers_v012_VO.mp3` packed as a sound strip from frame 1. As agreed with the director, locations change with **hard cuts**, and the stamp prints a **red X with no text**.

Scripts: `blender/SurgeonBrandsLivers_v001/scripts/build_v012.sh` runs `20_v012_or.py`, `21_v012_looks.py`, `22_v012_anim.py` and `23_v012_camera.py` on the v011 file, then `pipeline/package_for_farm.py`.

## Shots (v011 timing)
| Frames | Shot |
|---|---|
| 1–135 | Surgeon 1 at the open patient, argon pen held in his fingers, its tip at the liver |
| 136–275 | Close-up (f/8): a visible blue argon beam burns S then B into the liver **inside the opened abdomen** |
| 276–429 | He stitches the closed incision (same orientation all shot; needle driver in his fingers; left hand flat on the drape) |
| 430–570 | His arm lifts to the mask, pulls it down (ear loops stay on his ears); smirk, blinks, eye moves |
| 571–640 | A week later: he walks past the wall calendar as its pages flip (teal scrubs, swinging arms) |
| 641–775 | At home: she walks in (top + jeans, ponytail), the pain hits, her hand presses her shirt as the liver glows **inside her abdomen** |
| 776–915 | The nurse pushes her bed down the corridor to the OR doors; her face is visible |
| 916–1060 | The new doctor walks in (loose two-piece scrubs, soft cap, arms swinging), upper-body framing |
| 1061–1175 | Close-up (f/8): her hands lift the branded liver out of the patient's open abdomen |
| 1176–1240 | Her eyes widen (blink, eye moves, brows), mask fitted to her face |
| 1241–1310 | Hearing room, wide shot over the defendant's shoulder: the panel's faces and the defendant at the lectern |
| 1311–1445 | The defendant, hands resting on the lectern, the translucent livers behind him |
| 1446–1575 | The judge picks up the gavel (fingers wrapped round the handle) and strikes the block |
| 1576–1644 | The clerk picks up the stamp, presses it and a red X prints; she holds it over the certificate to the last frame |

## The 34 items
1. Caps are soft cloth bouffant caps (folds, gathered band, printed cotton). Hair shows below the edge at the forehead, temples and nape. Hair under the cap is masked so nothing pokes through.
2. His arm bends naturally. The pen is gripped in a pinch, solved from his own forearm (wrist limits respected), and its tip is at the liver.
3. The branding is shown inside the open patient (no skin close-up, no studio).
4. The patient's whole body lies on the table, under a drape fitted to her body by ray casting, with an abdominal window, an open cavity, retractors and the liver in place. Her head with the anaesthesia mask is visible.
5. One liver, one material, always inside the body (branding and reveal). The studio and its lights are gone, so there is no colour flicker.
6. The S and B burn (the original burn mask) in sync with the pen tip. A blue argon beam and sparks show while burning.
7. 276–429 is one shot. The incision runs across the body in every frame of that shot.
8. These are Surgeon 1's own hands at normal size (the hands-only glove rig is gone). His left hand rests on top of the drape, and the needle driver is held in his fingers.
9. His right arm visibly rises to the mask (≈441–476) and pulls it down.
10. His face emotes (smile, brows, blinks, eye moves). The ear loops are hooked to his ears when the mask is down. Soft cap. No hold over 1 s.
11. Scrubs are teal in every shot. The calendar shot has him walking through it while the pages flip.
12. Mustard knit top and blue jeans (two garments, slightly loose). She walks in naturally. The glow comes from inside her right upper abdomen, through the shirt. Her right hand presses the shirt there.
13. Ponytail (no hair over the eyes). Her face and head stay in frame.
14. The bed shot shows the patient (face up) and the nurse pushing in scrubs, cap and mask. It moves the whole time.
15. No glass or other object in front of the lens.
16. The new doctor has loose two-piece scrubs, a natural walk with arm swing and a soft cap, framed from the upper body.
17. The anaesthetist (green) no longer swings his arms. His hands rest on his cart all film.
18. The new doctor's face stays in frame.
19. Patient body, drape and open abdomen are visible in the reveal. Her hands come in and lift the liver.
20. Natural eyes (blinks, eye moves, no frozen stare). The mask is sized to her face.
21. The hearing room opens on a readable wide shot with the panel's faces and the defendant.
22. The defendant's body is in frame.
23. His hands rest on the lectern top. The lectern was moved 15 cm so no arm passes through it.
24. Arms rest on the lectern, with elbow poles set out and back, and no stretched shoulder.
25. Same as 24: no extreme reach, so no shoulder deformation.
26. No bench or desk edge in front of the judge's camera.
27. The gavel is baked from the judge's hand (fingers wrapped round the handle) at one constant scale. Its head hits the block top, then a small second tap.
28. The water glass in front of the block is removed. Nothing on the desk moves except the gavel.
29. The clerk's hand closes round the stamp handle on the desk, then lifts it.
30. The stamp is always in her hand once picked up. It is never floating.
31. The clerk's hair is tied back (ponytail), with her face readable and her head in frame.
32. A bold red X prints where the stamp came down (no text).
33. The film is frames 1–1644 only. The last shot runs to frame 1644, with no black frames.
34. Each shot has one continuous camera move. The cuts fall at the shot boundaries above, which follow the client's cut points.

## Review
- `review/preview.mp4`: every 5th frame (329 frames, 270×480, Cycles 4 samples + denoise), from the packed file, at real speed with the VO. Every frame was watched.
- `review/checks.md`: clip_scan, qa_check, limb_check and body_prop_cross results.
