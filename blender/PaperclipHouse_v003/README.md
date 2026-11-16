# PaperclipHouse_v003: director fixes on v002 (B36, Connect B36)

**How did a man trade a paperclip for a house.** 33.3 s, 1080×1920, 60 fps, Cycles. Every beat starts on its word in `PaperclipHouse_v003_VO.mp3` (`beats.json`, frame = 1 + round(seconds × 60)); nothing is retimed.

## Changes from v002b (director notes, three ranges)
- **f122–251 (pen close-up):**
  - His arms are in with bent elbows, and both hands rest on the counter close to his body. No A-pose.
  - The fish pen lies at the counter edge, in the foreground and fully in frame.
  - He looks down at the pen, then up, and smiles.
- **f681–760 (garage, snowmobile):**
  - Knees-up two-shot with a slow push-in.
  - SledGuy presents the snowmobile with an open hand. The hero turns to him and nods with a grin.
- **f1908–2000 (house reveal):**
  - Starts wide on the house, then pushes in to knees-up, with him at about half the frame height.
  - He raises both arms in a V, with the house behind him.
- **Preview:** only these three ranges were re-rendered and spliced into the v002b preview. Every other frame is identical to the v002b package. Those other frames are the complete final-v002b render.

## Changes from v002 (director notes)
1. **No mannequin arms.**
   - Every standing arm now hangs with a clearly bent elbow and the hand forward of the thigh, instead of the straight hang.
   - Both people in each trade shift their weight throughout the shot.
   - The partner rests the free hand on the hip after presenting.
   - The hero looks at the items only briefly, then at his partner (no more floor stares).
2. **Sleeve stripe removed.** The hero's top is now a solid purple; the source texture's printed stripe no longer shows.
3. **Wide shots tightened:**
   - Snow-trail walk, f761–895: the camera tracks backward ahead of him as he walks.
   - Walk to the house, f1622–1787: a tracking camera keeps him at about 40% of the frame height.
   - Film set, f1346–1420: a closer side angle, with the hero moved clear of the armchair and gesturing toward the movie camera.
4. **Pen close-up, f122–251:** a low camera with the fish pen in the lower foreground and his whole face above it.

## Shots (frames on the VO timeline)
| Frames | VO words | Picture |
|---|---|---|
| 1–121 | He traded a single red paperclip | Kitchen: paperclip and fish pen lie on the counter; the hero (behind the counter) and PenLady shake hands across it |
| 122–251 | for a fish-shaped pen | Close-up: the fish pen on the counter, the hero leaning over it, smiling |
| 252–414 | Then he traded the pen for a custom doorknob | Classroom: pen and doorknob on a side table; KnobMan presents them, then they shake hands |
| 415–529 | The doorknob became a camp stove | Camp meadow (tent, firs): the open camp stove on the grass; Camper presents it, then a handshake |
| 530–613 | which became a generator | Street drive: the red generator on the ground; Worker presents it |
| 614–680 | then a keg party | Garage party: bulbs, balloons, the keg on the party table; everyone cheers. Logo box on the shelf |
| 681–760 | then a snowmobile | Garage: SledGuy presents the blue snowmobile; the hero steps up, fists up |
| 761–895 | He kept trading upward until he eventually had | Snow trail with mountains: the hero walks toward the camera past the parked snowmobile |
| 896–979 | a trip across Canada | Close-up: the hero looks out over the mountain range and smiles |
| 980–1031 | a van | The hero beside the blue van; the white DA KRAS FILMS logo on its side is front-on |
| 1032–1100 | a recording contract | Studio: van keys and the contract on a side table; the Exec presents them |
| 1101–1249 | and even a year of free rent | The brick house: contract and keys on a side table; the hero and Landlady shake hands |
| 1250–1420 | Eventually, one trade gave him a movie role | Film corner: snow globe and clapperboard on a side table, a handshake with the Director; then the hero acts in the lights while the Director cues with the clapper |
| 1421–1621 | By then, people around the world were following the story | Neighbours on the sidewalk point down the street; then the hero's close-up on the sky stage |
| 1622–1787 | Exactly one year after starting with one paperclip | The hero walks along the front path to the blue house |
| 1788–1907 | he traded that movie role for | Clapperboard and house keys on a side table in front of the porch; a handshake with the Mayor |
| 1908–2000 | an entire house | The house reveal: the hero in front of it with both fists up; the camera cranes up and back |

## Staging (director, Nov 16)
No item is held against a body. Each trade is staged in three steps:
- The items rest on the counter, a side table, or the ground (the big items).
- The partner presents them with an open hand.
- The two shake hands. Shots shorter than 1.5 s skip the handshake.

Close-ups show items resting on a surface. The vehicles are parked. The rock star and snow globe beats are not in the final VO, so they are not in the film.

## Logo
- White DA KRAS FILMS logo on the van sides (frames 980–1031, front-on, fully in frame).
- Dark logo on a cardboard box in the garage (frames 614–760).

## Files
- `PaperclipHouse_v003_60fps.blend`: the package (see `SETTINGS.md`).
- `PaperclipHouse_v003_VO.mp3`, `PaperclipHouse_v003_VO.words.json`, `beats.json`, `timing.json`.
- `review/preview.mp4`: the moving preview (every 5th frame, 270×480, with the VO), rendered from this exact package.
- `review/checks.md`: results of `body_prop_cross`, `clip_scan`, `qa_check` and `limb_check`.
- `scripts/`: the full rebuild chain:
  1. `01_chars.py`
  2. `02_sets.py`
  3. `10_props.py`
  4. `03_anim.py -- ../timing.json`
  5. `04_lights.py`
  6. `pipeline/anim_look.py --no-sky`
  7. `05_package.py`
  8. `06_shrink.py`
  9. `07_farm_check.py`
- `CREDITS.md`: the CC-BY block for the video description.
