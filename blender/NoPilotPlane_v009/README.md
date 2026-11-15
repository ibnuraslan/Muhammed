# NoPilotPlane_v009: third-person re-stage to the new VO beats

The director rejected v008b and asked for a simpler re-stage rather than more patches. v009 keeps the story, set, characters and ending, but changes how the film is shot and timed.

- `NoPilotPlane_v009_60fps.blend`: packed, plain git file (no LFS), one camera `CAM_Film`, frames 1–3481 (58.0 s at 60 fps).
- `beats.json`: the director's 19 VO beat seconds; beat N starts at frame 1 + round(s × 60). No VO is added.
- `review/preview.mp4` and `review/pages/`: the full preview (every 5th frame, 270×480, 12 fps = real speed). Ranges changed in v009c–v009g were re-rendered from this exact package and spliced in. The close-up (3346–3481) is rendered at 32 samples, everything else at 4. The unchanged ranges were rendered before the last flag change (eye/lash self-shadow off), which only affects the eyes.

## The director's list

| # | Note on v008b | What v009 does |
|---|---|---|
| 1 | 35 s of first-person cockpit POV: hands filling the frame, no face, static panel. | No head-cam. YOU is a visible third-person character for the whole film. The film is a cut list of 35 shots (`scripts/08_camera.py`), none longer than 2.5 s. In the cockpit it cuts between his face through the windscreen (lit by the panel), a front-left three-quarter with his hands on the yoke at normal size, the view out of the window, the radio and the doorway. |
| 2 | Pink/red glare blobs on the windscreen and sky. | They came from the two red alarm point lights (`L_alarm`, `L_alarm_cabin`) strobing at 70 and 150 W during the alarm beats and lighting the canopy and the sky. They now stay off. The small red warning lamps on the panel still flash. |
| 3 | Giant limbs in the lens. | Every camera is placed and checked so that YOU, the captain and the first officer stay at least 1.5 m from the lens when they are in frame (passengers at least 1.0 m). See the check below. |
| 4 | The FO sprawled in a twisted pose, seen from above. | Both pilots now lie on their backs, face up. The captain lies across the doorway; YOU crouches beside him to check him (from between the pilot seats), then steps over him. After the haul, the first officer ends on his back along the right side of the cockpit, face up, and is shown at medium distance (51.1–52.5 s). |
| 5 | Build to the VO beat seconds, no warp. | All action is authored in the old beat seconds and mapped piecewise-linearly onto the new ones in `03_animate.py` (`remap`/`F`), so every beat starts exactly on its new frame. The film ends at 58.0 s. |

The ending close-up of his face (55.72–58.0 s) is kept as it was.

## v009c/v009d: the director's review of v009 (8 items plus 2)

| # | Note on v009 | Fix |
|---|---|---|
| 1 | 3346–3481 close-up: face blown out, eyes black holes, teeth in a grimace | Three-quarter from front-left at his eye level, slow push in. Face fill 25 → 12 for this shot. Jaw 7° → 2.5° (lips just parted), eyes open but not staring, head tilts up with a breath. Eye/lash meshes no longer cast shadows on the eyes. The preview of this shot uses 32 samples, because 4 smears the eyes. |
| 2 | 1441–1491: arm straight like a mannequin, through the seat back | Cause: the FO slides out to the right while YOU stayed put, so the arm hit full reach. YOU now steps and crouches after him, so his elbows stay bent. Shown from the doorway, then high from the front (1411–1550). |
| 3 | Front shots through the windscreen: arms folded into the chest, hands hidden, frozen | No more shots through the windscreen at his front. They are replaced by side shots (face and hands on the yoke), the front-left wide, and an over-the-shoulder view. |
| 3b | Crossed forearms (2871–2971) | He sits in the right seat, so the throttle/pedestal is on his left. His right hand reached across his body to it. Now the left hand works the throttle and the right stays on the yoke. |
| 4 | Lens blocked by frames, the nose, a blue pane and a dark slab | The front cameras are inside the windscreen, left of centre. The dark slab was the sun visors, which are now hidden from the camera. The 13.2 s side camera moved inside, and the 49.6 s shot is now a side shot. |
| 5 | 496–536: passengers' hands at the frame edges | From 8.2 s the camera looks through the cockpit door as he walks up the aisle (no shot from behind over the seats). |
| 6 | Empty window POV shots, about 7 s in total | Each window insert is 1.0 s or less (4 inserts, 3.9 s total). |
| 7 | 1–241: backs of heads; who is "you"? | From 0.9 s (frame 55): a close shot of his face as he wakes. |
| 8 | 3071–3146: 1.3 s static top-down on the FO | 0.7 s. |
| – | Flat green patch | `scripts/09_field.py`: grass with mowing bands, and a 2.9 km × 160 m runway strip with a dashed centreline and edge lines, riding with the terrain. |

## v009h: the client's notes (via the director), patched onto the v009g package

| # | Note | Fix |
|---|---|---|
| 1 | 1036–1221: the handset pressed into his forehead and temple | The handset-to-head action is deleted. The handset stays on its hook for the whole film. From 931 to 1266 he braces with both hands on the tops of the two seat backs, leaning toward the windscreen. Nothing touches his head. Done by `scripts/10_v009h_patch.py` on the packaged file (it deletes his arm and finger keys in that window and re-keys both hands with the `relaxed` finger preset), followed by `08_camera.py`. |
| 2 | 1451–1511: the FO's body passes through the seat back; the boy's head merges into him | The haul is now a cut. From behind the boy, his hands on the FO's shoulders (23.3–23.8 s, 0.5 s). Then the window (23.8–25.3 s, two angles). Then the FO already on the floor beside the seat, with the boy standing over him (from 25.3 s). |
| 3 | Twisted hands and wrists while he sits and walks (56–241 and later) | `scripts/11_v009h_hands.py`: on every frame where his hands are idle (1–528 seated and the aisle walk, 562–1290 walking, crouching, hanging and braced on the seat backs, 1545–1700 hanging and braced on the pedestal), the wrist limit is keyed to zero twist and ±25°/±12° bend, and the fingers take the hand_poses `relaxed` preset. Grips are unchanged: the door push, the haul, the yoke and the throttle. |

Package md5 001cf8c3 (v009g package, then `10_v009h_patch.py`, `08_camera.py` and `11_v009h_hands.py`). Ranges re-rendered from it and spliced into the preview: 1–528, 561–1291, 1391–1556 and 1546–1701. Hands checked at 540×960 on every 10th frame of the whole film (`review/hands540/`, contact sheets). The cam/clip/limb checks were not re-run on this package. Seen in the check but not changed: at the lunge into the seat (about 1801–1831) his left arm reaches out straight. The wrist is not twisted.

## v009g: the director's review of v009f (9 items)

| # | Note on v009f | Fix |
|---|---|---|
| 1 | 2976–3066: his left arm reads as missing (a stub) | The side shot ends at 49.3 s (frame 2959). From there his left arm points at the side camera, so 49.3–50.3 s is shot high between the seats, where both arms read. |
| 2 | 2066–2151, 2326–2406, 2821–2901: a seat back blocks the lens | The over-the-shoulder camera moved up between the seats (`OTS2`), so only the edge of a seat back is in frame. |
| 3 | 661–701: an arm enters from the left edge | The follow shot through the door ends at 656. The crouch and step-over play from the inside-front camera. |
| 4 | Mannequin arms at 561–601 (through the door) and 721–791 (in the cockpit) | After the door push both arms hang relaxed with a slight bend. At the step-over he no longer holds the seat backs with his arms out; his hands come down beside his hips. In the crouch his left hand rests on his knee (on the door frame the arm went straight up). On the handset his free arm hangs at his side. |
| 5 | 1491–1511: the FO's legs and shoes in the lens | The high front shot starts at 1516. |
| 6 | 521–531: an extra arm at the bottom-left | The follow shot is cut at 517. |
| 7 | 931–1056: back view frozen 2.1 s | 1.0 s of the back view, then a side shot of his face at the panel. |
| 8 | 1341–1436, 1706–1816: static doorway wides | Each doorway wide is 0.8 s. The haul continues from a side view of his face (24.1–25.25 s). |
| 9 | 1571–1641: stiff horizontal right forearm | Both palms rest on the throttle pedestal top (the hand targets were 0.2 m above it, so the forearms floated). |

## Build chain
`03_animate.py` → `pipeline/anim_look.py` → `05_look_tune.py` → `06_pov_split.py` (the head split now runs only with `pov`; v009 does not use it) → `04_package.py` → `08_camera.py` (cut list, re-keys `CAM_Film` on the packaged file) → `09_field.py` (landing field and runway).

## Fixes after the first v009 build (v009b)
- Handset: it went into the jaw. The wrist target now sits in front of the mouth.
- Hands at the step-over, the radio and the alarm beat: they hung in mid-air at the headrests. They now hold the sides of the seat backs.
- Haul and post-haul hands: they went into the body. The targets are now in front of or beside the torso.
- Captain's elbows and the seated grips: elbows sank into the sides. The arms are opened and the grips widened.
- Camera:
  - The step-over shot is aimed higher.
  - The rear shot at 23.5 s is split, with a new high front shot from 24.9 to 25.82 s.
  - The FO-on-floor shot runs from 51.1 to 52.48 s.
  - The cut list is now 36 shots.

## Checks on the packaged file (v009g, md5 5176a019)
- `cam_dist_check` (`review/camdist_v009.json`): 46 shots, every one 2.5 s or shorter. The director asked for cameras inside the cockpit, and the cockpit is about 2.2 m wide, so many cockpit shots are 1.1–1.5 m from YOU, and the FO is 1.3 m away at 13.3–23.3 s. The 1.5 m target is not met in those shots. In the preview no limb fills the frame.
- `clip_scan` (`review/clip_scan_v009.json`): single frames 679 and 1741, and two short ranges during the haul, 1429–1441 and 1471–1477, where his hands are on the FO's jacket.
- `limb_check` (`review/limb_v009.json`): 257 ARMBODY flags, mostly the known false positive (the check counts the shoulder groups as torso), and 38 PROPHEAD flags (the hanging oxygen drops touching seated passengers' heads).
- `qa_check` was not re-run in this round (the director said not to wait for it).
- Preview: the ranges changed in v009g (491–1061, 1271–1821, 2061–2156, 2321–2411, 2816–3071) were re-rendered from this package and spliced in.

## Open
- No conscious passenger kneels beside the FO. The FO is shown face up at medium distance (51.1–51.8 s); the crouch-and-check beat is played by YOU beside the captain.
- The eyes in the close-up read correctly at 32 samples. At the 4-sample preview level they still darken, so the final render needs normal samples.
- About 0.4 s at 8.7 s (frames 521–541): the closed cockpit door fills the frame just before he opens it.
- Cockpit camera distances: see above.
