# DogBuriedAlive_v002b: director fixes on v002 (for director review)

v002b = v002 (commit ae04c77) plus the director's notes of Nov 16:
1. **Wardrobe (every family shot):** separate garments in contrasting colours instead of one-colour suits: Dad a blue check
   shirt over denim jeans with a brown belt; the boy a green top over dark jeans; Mom a white check blouse over denim shorts.
   (No MPFB garment library is installed, so each suit is split at the waist into shirt + jeans/shorts with a belt band,
   and the shirt is lifted 4 mm so it reads as a layer: `scripts/05_wardrobe.py`.)
2. **f1–192:** the camera pushes in on the family; Mom's hand to her face, Dad's arm round the boy, heads bowed; the walk-away
   is framed close.
3. **G02 (f193–364):** slow push to the dog's face, his breathing heaves, one head/ear twitch (~f288).
4. **Y06 (f517–626):** low and close: the dog in the foreground, the family knees-up behind.
5. **Y15 (f1155–1288):** starts close on the car (long lens) and widens as it turns in.
6. **P17 (f1289–1388):** head tilt, stronger tail wag, slow push.
7. **Y20 (f1538–1590):** closer on the family.
8. **Y21 (f1591–1641):** reactions: Mom drops to one knee with her arms open, the dog trots to her, the boy takes a step
   toward him, Dad's hand goes to his head in disbelief (elbows bent).


ConnectB21, branch `claude/connectB21-dog-buried-alive`. Phase 2 of `blender/briefs/CONNECT_BATCH2.md`.

- `DogBuriedAlive_v002b_60fps.blend`: the farm package (48 MB, every image and the VO packed, one camera, frames **1–1641**).
- `DogBuriedAlive_v002b_VO.mp3`: the client recording (`blender/briefs/batch2/B21_DogBuriedAlive_VO.mp3`, commit 57cd226).
- `beats.json`: shot start frames = `1 + round(word_start_s × 60)` from faster-whisper word timestamps (`review/VO.words.json`).
- `review/preview.mp4`: the moving preview (every 5th frame, 270×480, Cycles 4 spp + OIDN, with the VO), rendered from this
  exact package; `review/pages/`: every preview frame on contact pages.
- `scripts/`: the full build (`01_lib.py` assets → `02_build.py` + `02_sets.py` + `03_shots.py` + `shots.py` →
  `04_package.py` → `pipeline/package_for_farm.py`).
- Settings: `SETTINGS.md`. Credits: `CREDITS.md`.

## Shots (VO frames)
| Shot | Frames | Words | Picture |
|---|---|---|---|
| G01 | 1–80 | They buried the dog, | Grave cross-section: dirt falls into the pit over the curled dog; Mom (hand to mouth), Dad (arm round the boy), Son at the edge. |
| G03 | 81–192 | but as they walked away, | The family walk away across the lawn; the dog below. |
| G02 | 193–364 | they didn't notice the dirt starting to move. | Push-in on the dog breathing; the dirt over him heaves, clods trickle. |
| R04 | 365–451 | You see, the dog had been hit | Flashback: he trots along the road, the red pickup behind (tracking shot; cut before any contact). |
| R05 | 452–516 | by a truck, | Soft cut: he lies still at the road edge, the pickup stopped. No wound. |
| Y06 | 517–626 | and his owners thought he was dead. | Lawn: the dog lies curled; Dad bends over him, Mom (hand to mouth) and Son behind. |
| Y07 | 627–694 | So they buried him | The fresh mound; the family stand round it, heads bowed. |
| Y08 | 695–769 | and left for the weekend. | The blue SUV backs out of the driveway; **logo on the door**. |
| U10 | 770–928 | But he was actually only unconscious. | Underground close-up, eyelids closed, breathing; slow push. |
| U11 | 929–1013 | When he woke up underground, | His eyes open and his head lifts. |
| U13 | 1014–1087 | he clawed his way back | One tall tunnel: he climbs, back to camera, paws digging, small clods falling. |
| Y14 | 1088–1154 | to the surface. | His head and front paws push out of the mound in the yard. |
| Y15 | 1155–1288 | And when the family returned a few days later, | The SUV turns in from the street and pulls up the driveway. |
| P17 | 1289–1388 | they found him sitting on the porch, | The dog on the porch in front of the white french doors, tail wagging. |
| P18 | 1389–1463 | wagging his tail. | Side view: tail wagging, a step forward, a head tilt. |
| P19 | 1464–1537 | He was happy. | Face close-up, happy, head tilting. |
| Y20 | 1538–1590 | They were | By the SUV: he trots up to the family; they recoil. |
| Y21 | 1591–1641 | horrified. | The family's horrified faces, hands up, mouths open. |

## Checks (on the packed file)
- `body_prop_cross` (step 3, SUV, pickup, house, mounds, backfill): **0 visible crossings** (`review/body_prop_cross.json`).
- `limb_check` (step 2): only the known 2-point shoulder false positives (`upperarm01` points next to the shoulder); no arm
  through a body, no arm behind the back (`review/limb_check.json`).
- `clip_scan` (step 6): two short ranges left, f91–97 (Dad's first walk steps in G03, forearm against his hip) and the single
  frame f1543 (Y20, Dad's hands rising); both tiny in a wide frame (`review/clip_scan.json`).
- `qa_check` (`review/qa_check.json`, run on the previous build with the same staging): CAMJUMP = only at the 17 hard cuts between the 18 shots;
  PROPMOVE = the falling dirt clods; EMPTY = dog/car shots (the check only counts human characters); FILL = the render-hidden
  pocket cutter near the U10/U11 lens (renders clean); FACEPRESS = Mom's hand-to-mouth in Y06/Y07 (8 cm off the face).
- Camera: a scan of the baked camera found no in-shot jump (after fixing a ±180° Euler wrap in Y15).

## Known issues
- The voiceover says "sitting on the porch"; the dog stands (the quadruped rig's sitting pose deforms badly, as B01 found).
- The closed eyelids read as a soft fur patch with a lid line rather than a crisp closed eye at preview size.
- Porch brought down about half a stop (director note); the deck and trim are still the brightest surfaces in the film.
