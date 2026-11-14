# DrunkTrain v006: what changed from v005 (approved), and why

Asked by the director on Nov 14 at 19:04: watch the final film moving (`pipeline/preview.py`, every 5th frame, plus `watch_pages.sh`), fix every fault from `LESSONS_LEARNED.md` section 1, and make sure his body never passes through the rails or the train. Simplify any risky shot. Beat frames are unchanged (`beats.json` is the same as v005) and there is no VO.

How I checked it:
- I watched every page of the moving preview (`review/preview.mp4`, 414 frames).
- `body_prop_cross.py` with the rails, the loco, both wagons and all four wheelsets as props.
- `clip_scan.py`, `qa_check.py` and `limb_check.py` on the packed file.

## His body through the rails and the train (`body_prop_cross`, v005: 6 ranges, about 100 frames)

| Time (frames) | v005 | v006 |
|---|---|---|
| 2.0 s (118–131) | The trip: his toe went about 8 cm into the rail, and the swing foot went through it. | The toe snags against the side of the rail. The swing foot steps over any rail it crosses, and feet plant at least 40 cm from a rail. |
| 5–9 s (304–535) | The back of his skull sank into the rail he passed out on. | His neck is curled a little, so the skull rests on top of the rail. |
| 9.3–9.9 s (556–598) | The impact threw him 0.3 m up into the plough, then a full spin swept his 1.75 m body across the 1.44 m track, through both rails. | A quarter turn only, done while he is still ahead of the pilot tip. He is swept to the track centre above the rail tops, then lies flat under the centre, which has 0.6 m of clearance. |
| 11–13 s (667–763) | His flailing limbs hit the trucks and the wheels. | The limbs are kept within 22 cm of the track centre and 20 cm below the underside. There is less bounce. |
| 19.5–20 s (1171–1198) | He crawled out sideways through the loco's side frame, which has 0.4 m clearance along the whole loco, so it was physically impossible. | The train brakes over 10.4 m more, with the same impact and halt frames and a speed that only falls. It halts with the loco/wagon coupling gap over him, and he crawls out there. His hips are raised so his knees cross on top of the rail, and each hand is planted on the ballast on its shoulder's side, lifted over the rail as the shoulder passes. |

## Faults found by watching the moving preview

| Time (frames) | Fault (LESSONS section 1) | Fix |
|---|---|---|
| 0.7–1.8 s | The rail slid past the lens. | The camera is higher. |
| 5–9 s (306–446) | Mannequin arm: his right arm was held out stiff in the air while he lay on the track. | It flops off his belly and lies along his side on the ballast, with a slight bend. |
| 10.6–10.9 s (641–656) | The camera slid in beside the pilot (17 cm away), with a blurred bar across the lens. | The camera reaches the track centre in open air ahead of the train, and the loco passes over it. |
| 14.3–15.6 s (861–936) | Empty frames: about 1 s of the train side only; he was hidden by the side frames. | The camera stays inside the gauge under the train, on him, through the halt. Then it rises straight up through the empty coupling gap to the wide shot. |
| 19.6 s (1176–1186) | The rail swept across the lens. | The camera crosses the rail higher. |
| 23.5–26 s (1411–1576) | X-ray: the forearm muscles tore away from the glass arm, leaving shards over the belly and a red arm pointing away from the glass arm. | The forearms are glass only: the forearm and hand muscles are masked. |
| 26.5–30.5 s (1591–1831) | X-ray replay: the muscle mesh tore into big jagged shards. A see-through train, rails and arrows (LESSONS rule 13) and big blurred blue shapes passed the lens, and the macro camera filled the frame. | The replay is simplified to the glass body alone, going limp and rolling with the force. The muscles leave before it, the ghost train, rails and arrows are removed, and the camera is wider. |
| 30.6–30.9 s (1836–1851) | Empty white studio for about 0.3 s, and the bubble filled the frame. | Fast collapse: the body is gone for only 5 frames, and the bubble collapses in 9. |
| 33.5–34 s (2016–2031) | His palm filled the lens. | The camera is further back. |
| Whole film | Black-hole eyes risk; f/5.6 blur on close shots. | `eye_fix.py` (LegoInNose a44130b) and f/11 (`08_post.py`). |

## Check results on the packed file
See `README.md` in this folder.
