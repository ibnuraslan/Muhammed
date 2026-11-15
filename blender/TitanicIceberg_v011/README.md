# TitanicIceberg_v011: farm package

**v011: director review of v010 (1384db0).** Beat frames, beat order and frame_end 1830 are unchanged, and no VO is added. The preview `review/preview.mp4` was rendered from this exact package file.
1. **Photographer (432–605, and the rail shot 816–905).** He holds the camera one-handed at chest height, his right palm under the base. His left arm hangs relaxed at his side, with the hand visible by his thigh. For the click the camera rises only to chest/shoulder height (498–548), so it never covers his chin.
2. **Darkroom tech (1070–1169).** Nothing reaches across his body any more. Both arms hang relaxed at his sides, below the bench edge, while he leans over the tray and the print comes up. The tongs rest in the tray. His shirt is dark charcoal cloth with a weave, replacing the untextured lilac.

**v010: director review of v009 (52598e8).** Beat frames, beat order and frame_end 1830 are unchanged, and no VO is added. The preview `review/preview.mp4` was rendered from this exact package file. Frames 740–915 were re-rendered from the final package after the rail-shot hand fix.
1. **Photographer, 432–605.** The camera is held in both hands: the left palm under the base, and the right hand on the side, which switches to the index-finger "point" pose to press the shutter at about 520. He lifts it to chin/eye level (498–548), clicks, then lowers it, with a breath and a small lean in. The face goes from concentrated to pleased.
2. **The blue figure (the deckhand) is gone.** He was only ever a cropped body at the frame edge. `04_make_photo.py` used to un-hide everything it had hidden for the photo render, and now restores only what was visible before.
3. **Rail shot, 816–905 (1.5 s).** Three-quarter front: his face is visible as he watches toward the berg, and both hands stay on the camera. The ship push before it is 606–815.
4. **Darkroom.** The refractive developer layer is off the render, and the developing print gives off a faint glow of its own image under the safelight. The camera is at f/11, focused between the tray and his face. The berg and the debris come up from blank as he rocks the tray.
5. **Proof.** A bold red streak is on the photo (both the held copy and the desk copy). The hull model's red band top sits at the streak's height, right next to it. The camera is at f/11, focused on the photo.

**v009: director review of v008 (b265f92).** Beat frames, beat order and frame_end 1830 are unchanged, and no VO is added. The preview `review/preview.mp4` was rendered from this exact package file. Frames 1435–1530 were re-rendered from the final package after the proof-shot fix.

| Frames | Shot |
|---|---|
| 0–120 | The steward with his camera. |
| 121–431 | Cut straight to the berg (no blurred sea frame), then a push-in to the red smear. |
| 432–605 | The photographer on deck framing the shot, face to camera. |
| 606–729 | His steamship past the debris, with the berg beyond, on a visible push-in (2 s). |
| 730–905 | On his deck, over his shoulder: the photographer watching the berg and the debris. |
| 906–1069 | Night: the solid liner scrapes past, and the red paint is revealed on the ice. |
| 1070–1169 | Darkroom, across the tray facing him: the image comes up in the tray in the foreground, and his face is in the safelight. |
| 1170–1259 | Medium: B holds the print up, face clear (push-in). |
| 1260–1339 | Medium: A leans in with the magnifier, face toward camera (push-in). |
| 1340–1437 | Medium: B points at the red streak (push-in). |
| 1438–1529 | The proof on the office desk. The photo is propped beside a hull model whose red band's top edge sits at the streak's height, and the camera pushes in. B and his copy are out of shot, so there is one photo and no hand pointing at nothing. |
| 1530–1614 | A's face reacts. |
| 1615–1699 | B's face with the print. |
| 1700–1830 | Closer (2.2 s): a fast push-in on the lone berg, with the steamer beyond it. |

The explainer backdrop is no longer used.

**v008: director review of v007 (7224935).** Beat frames (0, 120, 348, 612, 912, 1092, 1200, 1338, 1530), the beat order and frame_end 1830 are unchanged. No VO is added. The camera is now a shot list with clean cuts, at the director's request; it is still one camera object, baked on every frame.

| Frames | Shot |
|---|---|
| 0–431 | The steward with his camera, then over his shoulder to the berg, then a clear push-in to the red smear (the smear fills the waterline by 348). |
| 432–605 | The photographer on deck framing the shot, face to camera: he looks down into the finder, presses the shutter and looks up. |
| 606–905 | The steamship in the foreground, the debris field, and the berg beyond. The water is matte in this shot (no sun-glint discs), and the funnel smoke is off. |
| 906–1069 | Night. A solid black liner with a red waterline band scrapes along the berg at a safe distance. The red paint on the ice is revealed behind its stern, with sparks at the contact. No glass ghost, and no flying into ice. |
| 1070–1169 | Darkroom. Safelight fill and a lamp over the tray, so his face, the tongs in his hand (livelier agitation) and the image coming up in the tray all read. |
| 1170–1437 | Office two-shot with both faces. Expert A bends less, so his face stays readable. From 1340 Expert B lets go with his left hand and points at the red streak on the print, held by his right hand. |
| 1438–1529 | The proof (1.5 s): the hull's red band slides in beside the photo, at the same height as the streak. |
| 1530–1613 | Office: both faces react. |
| 1614–1830 | Closer: a slow, visible push-in on the lone berg, with the steamer passing beyond it. |

The preview `review/preview.mp4` (every 5th frame) was rendered from this exact package file. Frames 400–445, 900–910, 1435–1530 and 1610–1830 were re-rendered after the final package fixes.

Eyes: a wet catch-light (glossy Fresnel layer) is added to the cornea, which read flat and glassy. The glass ghost liner of beat 2 is removed.

**v007: director review of v006 (396a8f5).** Beat frames and frame_end 1830 are unchanged, and no VO is added.
1. **Office, 1300–1613:** there is no headless push any more. Expert B's face, his hands, the print and Expert A's magnifier stay in frame throughout, with a gentle drift.
2. **Beat 2, 140–345:** the ghost-liner panes over the berg are removed. The ghost liner now renders only during the night scrape (905–1100).
3. **Top-down water is gone.** From 580 the camera swings wide round the steamship's bow with the berg and debris always in frame. Beat 4 (700–830) has the steamship in the foreground, the debris behind it and the berg beyond. The camera then rounds the stern to the berg. The detailed wave patch was extended by one tile so the ship's water has no seam.
4. **Clean cut at 1614:** the office (people, print, desk, walls) drops away in one frame, so the camera goes straight from Expert B to the open sea with no blurred-print frames. Then it rushes out and turns to the lone berg (1667–1830).

**v006: director review of v005 (3f218ea).** Beat frames (0, 120, 348, 612, 912, 1092, 1200, 1338, 1530) and frame_end 1830 are unchanged, and no VO is added. Because the beat frames are VO-locked, each fix replaces unreadable footage inside its beat instead of changing the length.
1. **Beat 3, 350–600:** the close slide along the ice face is replaced by a readable mid shot. The whole berg base and the red/black smear are in frame (camera about 28 m off the face), dollying slowly along it. The red/black band is the smear on the ice, not a hull.
2. **Beat 4, 600–900:** top-down water is now about 1 s (a crane-up tilt over the debris at 590–650). Then a high three-quarter shot shows the whole steamship sailing past the debris field (700–860).
3. **Dive, 1050–1070:** a fast punch through the ice skin from mid distance. Only about 4 frames are close to the ice.
4. **Office, 1330–1640:** the explainer void, the floating giant print and the pink match line are **removed**. The camera pushes slowly into the print **in Expert B's hands** while Expert A holds the magnifier in the frame. The experts act until 1640.
5. **End:** the camera crosses the print at 1637, flies out through the hidden berg, and the lone-berg closer is about 2.5 s (1682–1830). It is filmed from the +Y side, where no scrape band or ghost hull can be seen.
6. **Darkroom, 1090–1170:** the camera is higher and looks down across the tray, so the tech's right hand holding the tongs, the tray and his face are all in one frame.

**v005: motion-preview pass** (director, Nov 14). Started from the approved v004 rev 3. Beat frames are unchanged and no VO is added. The whole film was watched as a moving preview (`pipeline/preview.py`, every 5th frame, then `watch_pages.sh`). The MP4 is `blender/TitanicIceberg_v001/review/preview.mp4`, and the pages are in `review/preview_v005_pages/`.
- **Camera IN his hands:** the bellows camera is now a Child Of the steward's right hand bone, resting on his palm, and his left palm supports it underneath too. Before, his open left palm floated beside it around frames 100–120.
- **Photo IN the expert's hands:** the office print sits between Expert B's two thumb-index pinches on every frame.
- **Black-hole eyes:** the EnhancedEye cornea is now a transparent mix (director recipe `eye_fix.py`) on all 5 characters.
- **No blur:** the f-stop is at least f/8 everywhere (the macros were f/4).
- **Macro:** the close ice-wall macro at 8–9.5 s is pulled back to mid distance, so the frame isn't filled for 1.5 s.
- **Office:** the camera no longer skims Expert A's head (his hair filled the frame at 1215–1240). It arcs past at eye level, and his head is level, looking at the print.
- **Ghost liner:** removed from render after the night scrape. It showed as a faint hull at the berg from 1760.
- Hidden objects now also have `hide_viewport` keyed, so they cannot block camera rays.
- Known, minor: at 1235–1245 (about 0.2 s), Expert A leans in to the magnifier and his crown shows above his face.


**v004: acting pass** (client, Nov 12). Started from the approved v003, with every story-beat frame unchanged (0, 120, 348, 612, 912, 1092, 1200, 1338, 1530). The full list is in `blender/TitanicIceberg_v001/review/ACTING_notes.md`.
- Steward: the 1912 folding camera is held at chest height and used with a waist-level finder. He looks down into it, presses the shutter, then looks up at the berg with a reaction, with breathing and a weight shift throughout. (Before, the camera looked like it was resting on his head.)
- Darkroom tech: his face is now readable on beat 6. The camera is at the bench side, and he lifts his head and reacts (brows, jaw) as the image appears, then looks back down.
- Expert B: he was keyed facing away from the print he held, so it was behind his back. He now faces Expert A, holds the print up by its top corners and looks at Expert A. His face is readable on beat 7.
- Expert A: his head tracks the magnifier. The camera orbit swings to the desk side, so both faces show.
- Deckhand: he looks up at the berg once while coiling.
- 11 s crane: the berg and the scrape stay in frame (it was blank sea).
- Rev 2, from the director review:
  - The desks no longer stand side-on. Expert B and the tech were standing inside them, and the lamp and books were floating.
  - The approach to the dive is wider, and the skin is crossed at 1074, so there are no blank ice frames.
  - The tech's face reads in the darkroom (camera over the bench, face fill, earlier reaction).
  - Grips: the steward holds the front standard, the tech's hand is flat on the bench, and Expert A's hand is flat on the desk.
  - The tech's shirt print is removed.
- Rev 3:
  - Every hand now uses the director's `pipeline/hand_poses.py` (limits plus presets).
  - Held props (camera, magnifier, tongs) follow the real, limit-clamped palm.
  - The beat framings have no back-of-head shots.
  - `qa_check.py` reports HOVER, CLAW, FACEPRESS and BACKHEAD all 0. The intended EMPTY, INSIDE and FILL exceptions are listed in `review/ACTING_notes.md`.
- Checks: `clip_scan.py` reports 0 bad ranges in both runs, as saved (2 characters) and at frame 1250 (all 5 characters). Own audit: float 0, hand–hand 0, hand-in-clothes 0, penetration 7, hover/sink 0, camera-in-geometry 0. Hand close-ups are in `review/v004_hand_closeups.jpg`.

**v003 changes from v002** (director notes, 00:53 UTC):
- The paint is now a thin dark oxide-red hull-paint scrape with a black hull band above it, both ON the ice face above the waterline. No red sits at or below the water.
- The 18 s dive now goes through white ice, not a red full frame.
- The beat-3 close-up is pulled back to mid distance.
- Steward grip: the right palm supports the camera from below and the left palm is on its side, so the fingers are off his face.
- 26 s: the camera exits the berg toward floating ice floes, then swings straight back to the berg and ship. There's no blank sea.

Vertical short, 1080×1920 at 60 fps, frames 0–1830 (30.5 s). Cycles. One continuous camera (`Camera_Main`).

The look follows `blender/STYLE_ANIMATED.md`: bright, clean 3D animation. That means a clear morning sky and blue sea, a white-cyan berg, a thin red hull-paint scrape line, a readable blue night, a bright warm office, and a sky-blue gradient explainer cyc. It uses AgX Punchy, with no grain and no motion blur.

## Files
| File | What |
|---|---|
| `TitanicIceberg_v011_60fps.blend` | Packed, compressed .blend. Opens in factory Blender 5.2.2 with no add-ons. Normal git file, no LFS. |
| `beats.json` | Beat start frames for the voiceover retime (`pipeline/retime_to_vo.py`). |
| `SETTINGS.md` | Farm render settings, read back from the file. |
| `CREDITS.md` | CC-BY block for the video description, plus the CC0 sources. |
| `package_check_*.jpg` | Low-res stills rendered from the packed file with factory startup. |

The build scripts are in `blender/TitanicIceberg_v001/scripts/`. Run them in this order: `01_build_humans`, `02_build_scene`, `03_animate`, `04_make_photo`, `pipeline/anim_look.py --no-sky`, `06_look_fix`, `05_package`. Review sheets are in `blender/TitanicIceberg_v001/stills/`.

## Story beats (target times, no VO yet)
| # | frame | line | on screen |
|---|---|---|---|
| 1 | 0 | He took a photo of an iceberg | A steward on a steamship deck on a clear April morning raises a bellows camera; a deckhand coils rope behind him. |
| 2 | 120 | the exact one that sank the Titanic | Push over the rail to the berg; a translucent ghost four-funnel liner glides past. |
| 3 | 348 | streaked with red, with one big smear | Mid-distance glide along the thin red hull-paint scrape line at the waterline, with about 2 s of close-up. |
| 4 | 612 | his ship was sailing near where… | Crane-up aerial over the debris field (deck chairs, crates, lifebuoys, planks), then arc to the steamship. |
| 5 | 912 | So it was most likely the same iceberg | Night ghost replay: the liner scrapes the berg with sparks and falling ice, and red paint sweeps onto the ice. |
| 6 | 1092 | When the film was developed | Dive through the smear into a red-safelight darkroom; the print develops in the tray. |
| 7 | 1200 | experts studied the image carefully | Through the door into a 1912 office: one expert holds the print, the other the magnifier. |
| 8 | 1338 | The red streaks lined up… | Sky-blue gradient explainer: the giant photo, the ghost hull slides in, the red band lights, and a match line sweeps across. |
| 9 | 1530 | leading many to believe… | Through the photo back out to the open sea, then a slow wide orbit around the lone drifting berg. |

## How the no-cut transitions work
The darkroom, office and explainer cyc are closed rooms built inside the iceberg's volume. The camera flies through surfaces in this order:
1. The ice skin at the smear (frame 1084).
2. The darkroom door.
3. The held print in the office (frame 1329).
4. The giant explainer print (frame 1552).

Each surface is switched off for the camera only after the camera has passed it, using keyed `visible_camera` or `hide_render` with constant interpolation. Don't bake or flatten this animation.

## Hands (client rule, Nov 11 23:00)
- Limit Rotation (local space) is on all 30 finger and thumb bones of every character. Fingers bend 0–95° forward only (the direction is measured from the keyed poses) with ±12° side, and the thumb has a ±50° cone.
- Wrist limits (±65/45/30°) are on the two experts. On the steward, tech and deckhand they fought the IK grip orientation, so the grip there comes from IK and the close-up check instead.
- Hand audit every 2 frames (`scripts/audit.py`): hand–hand 0, hand inside own clothes 0, hand float 0, and finger penetration 7. The 7 are fingers wrapping the 1.5 cm magnifier handle in 5 frames, plus 2 frames on the camera body. Camera inside geometry: 0. Feet hover/sink: 0.
- Close-ups of every hand action are in `blender/TitanicIceberg_v001/stills/V3_hand_closeups.jpg`.

## Known issues
- No voiceover yet. The timing follows the brief's target beat times; retime with `beats.json` once the VO arrives.
- The gulls were removed (the available model read as a blob). Background life comes from smoke, mist drift, bobbing ice and debris, the deckhand, the drying prints and the moving experts.
- Finger grips on the magnifier and the print are close-fitting. The audit reports a few verts touching or inside the thin handle or paper edge (see `stills/V3_audit.txt`).
- The procedural berg is a displacement sculpt, not a scan; it is shaded as clean animated ice.
- The steward's fedora shows 4 verts of the scalp poking through under the brim (not visible at review size).
- Expert B's face is partly hidden behind the print he holds up. Expert A carries the reaction (brows, jaw).
- Ghost liner model: a CC-BY "Titanic" model rendered only as an emissive ghost. Nothing on it shows a name or text.
