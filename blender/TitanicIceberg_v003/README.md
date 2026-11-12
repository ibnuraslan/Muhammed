# TitanicIceberg_v003: farm package

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
| `TitanicIceberg_v003_60fps.blend` | Packed, compressed .blend. Opens in factory Blender 5.2.2 with no add-ons. Normal git file, no LFS. |
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
