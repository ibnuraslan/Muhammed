# DrunkTrain: acting review of v004 (approved final) and v005 fix list

Source: `BEFORE_v004_sheet_0.5s.jpg` (every 30 frames, 270×480, 8 samples) and `clip_scan.py` on v004. Frames are film frames (frame = 1 + t × 60). Story-beat start frames are unchanged in v005.

| # | Time (frames) | What is wrong in v004 | Fix in v005 |
|---|---|---|---|
| 1 | 3.9–4.5 s (235–271) | Sitting on the ballast, his hands go *into* his shins and knees (`clip_scan` bad range), and it reads as clutching his feet. | Forearms rest on top of his knees, wrists loose, palms down; hands clear of the legs. |
| 2 | 5.0–9.0 s (301–540) | Lying on his back with both arms stretched straight above his head (a stiff "T"); not how a passed-out drunk lies. | Left forearm rests across his belly. The right arm lies bent, its hand draped over the rail beside his head. Legs slightly bent and turned out. |
| 3 | 5.0–9.0 s | Apart from the chest, it is a frozen hold for 4 s. | Snoring life: the head lolls, the jaw drops on the breath, and a sleepy twitch of the hand and leg every ~1.5 s. |
| 4 | 11.0 s (661) | The frame is filled by a wheel and the bogie, and he is not visible. | From the side the wheels always hide him, so by 11.0 s the camera is low between the rails, ahead of his head, under the loco: he is in frame as the train goes over him. |
| 5 | 14.3–19.2 s (859–1153) | Lying prone and completely frozen for 5 s. | Shallow breathing (the back rises), a twitch at 18.3 s, then he stirs. |
| 6 | 15.5 s (931) | Half the frame is the dark end of the locomotive. | The camera rises higher and further out as the train stops. |
| 7 | 17.0–18.5 s (1021–1111) | Beat 7 ("witnesses were sure he was dead"): the witnesses are seen from above or from behind; no faces readable. | The camera moves in front of them, between them and the train, at face height: horrified faces, hands to mouths, the worker crouching. |
| 8 | 19.0–19.5 s (1141–1171) | Beat 8 ("he stood up"): the frame is ballast or the dark underside of the loco; he is barely visible. | Low front camera at the gap: he stirs, lifts his head toward the camera and crawls out toward it. |
| 9 | 20.5 s (1231) | The top of his head fills the frame. | The camera is in front at face height as he rises: stunned face, blinking. |
| 10 | 22.0 s (1321) | Beat 9 swig: his own shoulder and arm block his face. | The camera is to his left front, slightly high: face, bottle and lips readable. |
| 11 | 23.4–23.6 s (1405–1416) | The camera dives inside his chest (camera inside a body). | Bubble transition: a cyan bubble grows out of his chest and swallows the camera, which stays outside his body. Inside the bubble is the x-ray studio. |
| 12 | 24.4–25.9 s (1465–1555) | X-ray loose arms swing *into* his torso and legs (`clip_scan` bad ranges). | The loose arm swing stays outside the body (the pendulum swings outward and forward). |
| 13 | 26.0 s (1561) | The camera is so close to the x-ray body that the frame is all torso. | Slightly wider macro on the swinging arm. |
| 14 | 30.85–30.95 s (1852–1858) | The camera dives inside the x-ray body, then out of his back (camera inside a body twice). | Reverse bubble: the camera pulls back, the studio bubble collapses into his chest, and the real scene is around him. The bubble is fully gone by 31.0 s (frame 1861), so it never covers him at the beat 12 start. |
| 15 | 20.3–20.8 s (1219–1249) | The witnesses "stagger back" with both feet sliding at once. | Two real steps back, one foot after the other, with a weight shift. |
| 16 | 4.0–4.5 s | Landing in the sit: both feet sit 4–10 cm above the ballast for a moment. | The feet are planted on the ballast throughout the sit. |
| 17 | 4.4–4.8 s (266–286) | Going from the sit to the flop back, his hands pass through his legs (frame 271, `clip_scan`). | An in-between: his hands come off the knees out to the sides before he tips back. |
| 18 | 3.0–21.0 s (179–1252) | The dropped bottle slowly drifts along the track toward where the flash-back starts (a prop moving by itself). | It stays where it fell until it is hidden; the flash-back bottle is in his hand from the first frame it is seen. |
| 19 | 18.5 s (1111) | The camera pans across an empty ramp between the witnesses. | It holds WitA and WitB together, then turns to a close front view of the worker's face as he peers under the train. |

## Result in v005
- `clip_scan.py` (director branch; run through a wrapper because this film's rigs sit at the world origin, see below): **0 bad ranges**. v004 had 4: 3.9–4.5 s, 24.4–24.6 s, 25.1–25.3 s and 25.9 s.
- Hand audit (`scripts/06_hand_audit.py`, every 2 frames): **2 single-frame brushes**. Lad's right hand touches his shorts at frame 231, as he lands in the sit. WitB's left hand touches her jacket hem at frame 1059, as she raises her hands. v004 had 1.
- Close-ups of all 17 hand contacts: `v005_hand_closeups.jpg`.
- Story-beat start frames are unchanged from v004 (`beats.json`).

**About the `clip_scan` wrapper.** `clip_scan` keeps a character only when its armature object is within 7 m of the camera. It also lists characters by visibility on the frame the file opens at. In this film all four rigs keep their object at the world origin and move through their root bone. So I ran it unchanged via a wrapper that sets frame 1000, when all four are visible, with `cam_radius_m=200`:

`blender -b DrunkTrain_v005_60fps.blend --python clip_wrap.py -- out.json 6 2.0 200`

## Self-check pass (director rule, Nov 12 14:40)
| # | Where | Fault found on my own images | Fix |
|---|---|---|---|
| 20 | Hand close-ups h04, h05, h11, h14, h15 | Close-ups showed legs, stones or a dark blur, not the hand. | `07_hand_closeups.py` aims at the palm centre and picks the first view angle that ray-casts clear to the hand. |
| 21 | 19.5–20.3 s crawl | Palms sunk into the ballast. | Hands planted 5 cm higher (on the stone tops), with `flat_palm`. |
| 22 | 33.5–34.5 s palm look | Clawed fingers. | `cup_hold` (open palm). |
| 23 | 17–20.7 s WitA | Palm on her nose. | The hand is lower, at the mouth and chin, angled across, with `open_alarm`. |
| 24 | All idle hands | The default curl (20/26/32°) read as claws. | `hand_poses.py` `relaxed` plus `add_hand_limits` on all four rigs. Bottle: `wrap_grip`. Worker hat: `cup_hold`. |
| 25 | 15.5 s | Empty track cell. | The camera aims at the braking train. |
| 26 | 19.5 s (beat 8) | He was hidden under the loco (behind the fuel tank from the side). | The camera is low inside the gauge, in front of him; his face is lit and reads as he crawls toward the camera (19.3–19.6 s). |
| 27 | 31.0–32.5 s (beat 12) | Back of his head at the beat start. | The camera is in front of him, walking back as he walks. |
| 28 | 26.5 s (beat 11) | Torso-only macro. | Wider and higher, so his head is in frame. |

QA: `review/qa_v005.json` (`blender/pipeline/qa_check.py` @ c6240b2, step 6, beats.json), run on the packed file.

## clip_scan and qa_check pass (director, 16:11)
| # | Where | Flag | Fix |
|---|---|---|---|
| 29 | 5.1–5.9 s (307–355) | Stock `clip_scan` (b6d7900): Lad's draped right hand goes into his head as the head lolls. | The arm lies further out to the side over the rail, clear of the head. Stock `clip_scan`: 0 bad ranges. |
| 30 | 13.7 s (823) | `qa_check` INSIDE and FILL (wheelset0): the camera crossed the rail through the front wheelset. | The camera stays inside the gauge while the wheels turn, then crosses ahead of the front wheelset as the train stops. |
| 31 | 19.5 s (beat 8) | His face did not read at the beat start. | The camera is low inside the gauge, in front of him. |

### qa_check flags that stay (intended)
- **BACKHEAD at 331 (beat 3), 541 (beat 4) and 871 (beat 6).** He is passed out, lying on his back and then face down under the train. At beats 3 and 4 the acting subject is the train coming at his head, and at beat 6 his face is down on the ballast. Turning his face to the camera would break the physics the client asked for.
- **EMPTY "wall/prop fills the frame, character only N %".** These are the wide outdoor shots of him lying on the track, the train coming, and the witnesses on the ramp. On the sheet he or the witnesses are always in frame and readable. The flag counts the ballast and the side of the loco within 3 m as a wall. There are no bare-wall, sky or black cells.
