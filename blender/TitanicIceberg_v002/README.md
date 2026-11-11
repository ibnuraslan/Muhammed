# TitanicIceberg_v002: farm package

Vertical short, 1080×1920 at 60 fps, frames 0–1830 (30.5 s). Cycles. One continuous camera (`Camera_Main`).

## Files
| File | What |
|---|---|
| `TitanicIceberg_v002_60fps.blend` | Packed, compressed .blend. Opens in factory Blender 5.2.2 with no add-ons. Normal git file, no LFS. |
| `beats.json` | Beat start frames for the voiceover retime (`pipeline/retime_to_vo.py`). |
| `SETTINGS.md` | Farm render settings, read back from the file. |
| `CREDITS.md` | CC-BY block for the video description, plus the CC0 sources. |
| `package_check_*.jpg` | Low-res stills rendered from the packed file with factory startup. |

The build scripts are in `blender/TitanicIceberg_v001/scripts/`, run in order 01 → 05. Review sheets are in `blender/TitanicIceberg_v001/stills/`.

## Story beats (target times, no VO yet)
| # | frame | line | on screen |
|---|---|---|---|
| 1 | 0 | He took a photo of an iceberg | A steward on a steamship deck at dawn raises a bellows camera; a deckhand coils rope behind him. |
| 2 | 120 | the exact one that sank the Titanic | Push over the rail to the berg; a translucent ghost four-funnel liner glides past. |
| 3 | 348 | streaked with red, with one big smear | Macro skim along the red hull-paint smear at the waterline. |
| 4 | 612 | his ship was sailing near where… | Crane-up aerial over the debris field (deck chairs, crates, lifebuoys, planks), then arc to the steamship. |
| 5 | 912 | So it was most likely the same iceberg | Night ghost replay: the liner scrapes the berg with sparks and falling ice, and red paint sweeps onto the ice. |
| 6 | 1092 | When the film was developed | Dive through the smear into a red-safelight darkroom; the print develops in the tray. |
| 7 | 1200 | experts studied the image carefully | Through the door into a 1912 office: one expert holds the print, the other the magnifier. |
| 8 | 1338 | The red streaks lined up… | Teal→navy explainer: the giant photo, the ghost hull slides in, the red band lights, and a match line sweeps across. |
| 9 | 1530 | leading many to believe… | Through the photo into the real fog, then a slow orbit around the drifting berg. |

## How the no-cut transitions work
The darkroom, office and explainer cyc are closed rooms built inside the iceberg's volume. The camera flies through surfaces in this order:
1. The ice skin at the smear (frame 1084).
2. The darkroom door.
3. The held print in the office (frame 1329).
4. The giant explainer print (frame 1552).

Each surface is switched off for the camera only after the camera has passed it, using keyed `visible_camera` or `hide_render` with constant interpolation. Don't bake or flatten this animation.

## Known issues
- No voiceover yet. The timing follows the brief's target beat times; retime with `beats.json` once the VO arrives.
- The gulls were removed (the available model read as a blob). Background life comes from smoke, mist drift, bobbing ice and debris, the deckhand, the drying prints and the moving experts.
- Finger grips on the magnifier and the print are close-fitting. The audit reports a few verts touching or inside the thin handle or paper edge (see `stills/C_audit.txt`).
- The procedural berg is a displacement sculpt, not a scan. Very close macro frames show the 1K snow texture.
- Ghost liner model: a CC-BY "Titanic" model rendered only as an emissive ghost. Nothing on it shows a name or text.
