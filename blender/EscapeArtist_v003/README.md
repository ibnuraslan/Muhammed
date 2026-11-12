# EscapeArtist v003: farm package (Connect34)

v003 = the approved v002 with two changes only (director, 00:52): night exteriors (fence/yard, protest, building exterior) lifted to a readable blue moonlight (a YardMoon sun light and a brighter blue night world), and the memory-house walls moved from mustard to clean cream plaster (corridor walls neutral). Animation, camera and timing are unchanged. Check: `../EscapeArtist_v001/stills/v003_check_house_yard.jpg`.

- `EscapeArtist_v003_60fps.blend` (59.5 MB, everything packed, normal git file, no LFS). Opens in factory Blender: 0 unpacked images, one camera (`CAM_Main`), no markers.
- `SETTINGS.md`: farm settings. `CREDITS.md`: CC-BY block for the video description. `beats.json`: beat start frames for `pipeline/retime_to_vo.py`.
- `package_check_f1680_lowres.png`: low-res check render from the packed file in factory Blender.
- **No VO mp3:** none was supplied for this film. The timing is built to the brief's target beat times (±0.3 s); retime with `retime_to_vo.py` when the VO arrives.
- Review sheets and scripts: `../EscapeArtist_v001/stills/` and `../EscapeArtist_v001/scripts/` (rebuild order 01→02→03→anim_look→04).

## Look
Bright, clean animated CG per `STYLE_ANIMATED.md`: light painted walls (cream plaster in the memory house, pale blue-grey cells), light wood floors, painted blue steel bars, high-key interiors, AgX Punchy, saturation up, bump down, f-stop 5.6, no motion blur. Night beats (filing, escape, protest) stay readable with a blue-tinted world, moonlight and lit faces.

## Checks at D
- Contact audit (`audit.py`, every 30 f): hover 0, sink 0, camera inside geometry 0, penetration 24 small flags (fingers on the bars and the window reveal, the prisoner at the door bars). None reads in the stills.
- Hand audit (`hand_audit.py`, every 20 f; hand vs own head/torso, vs other hand, vs other characters): 2 flags, both at the fence top (1740–1760), where the hands pass over the razor wire. Fixed from 36: filing hands spread apart, father's hand-on-chin pulled off the face, stepmother re-posed (phone beside her head, elbow out, clear point with the other arm), guards hidden and held at their posts when unkeyed, and the old man's window grip moved closer so his fists close on the bars.
- Finger Limit Rotation constraints (local: 0–95° bend, ±10–12° spread/twist; thumbs a wider cone) on every character.

## Known issues
- Wrist and elbow Limit Rotation not added: the wrists are driven by IK targets, and a hard limit fought the grips. Hand poses were checked in close-ups instead (`stills/D_hand_closeups.jpg`).
- Beat 9 "solitary" mostly reads through the slot light and the darker cell, because the steel door panel is behind camera for most of the beat.
- Beat 1: the key-ring macro on the guard's hip holds about 1.2 s, and the guard's back briefly fills frame at about 2 s.
- The court→corridor and corridor→memory transitions are fly-throughs: the court pass uses a real doorway, while the memory pass goes through the corridor wall (about 4 frames of wall texture).
- The bent toothpaste tube reads as a pale L-shaped object in his hand, kept brief and backlit as a silhouette.
- The 0.2 s polish sheets in v001/stills are from the pre-look-change build. The D 1 s sheet (`stills/D_look_1s.jpg`) is the current look.
