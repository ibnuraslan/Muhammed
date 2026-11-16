# WhaleSwallow_v004 (the director's "v003b": 8a/8b replaced; everything else as approved in v003)

A vertical 1080×1920, 60 fps Cycles film: a diver is scooped up by a humpback whale and spat out, and ends up in hospital.
It is built to the client's voiceover (`WhaleSwallow_v004_VO.mp3`, 28.45 s) and uses hard cuts.

| File | What |
|---|---|
| `WhaleSwallow_v004_60fps.blend` | The farm file: packed, compressed, 27 MB, frames 1–1715, one camera `CAM` (see `SETTINGS.md`) |
| `WhaleSwallow_v004_VO.mp3` | The voiceover; it is also packed into the .blend as a sound strip at frame 1 |
| `WhaleSwallow_v004_VO.words.json` | Word timings (faster-whisper), 84 words, speech from 0.00 to 28.06 s |
| `beats.json` | Each beat's frame (`1 + round(s × 60)`) and first words |
| `shots.json` | Each shot's start frame, length and nominal clip length; dropped shots are parked after frame 3000 |
| `review/preview.mp4` | The moving preview of the whole film at 270×480, every 5th frame held, with the VO |
| `scripts/01–05` | The build: characters, whale, sets, animation, packaging |
| `SETTINGS.md`, `CREDITS.md` | The farm render sheet and credits |

## Rebuild
```
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b -P scripts/01_chars.py ... ; 02_whale.py ; 03_sets.py      # see the v001 PLAN for the inputs (unchanged steps)
$B -b sets.blend -P scripts/04_anim.py -- <repo>/blender shots.json work/anim.blend
$B -b work/anim.blend -P scripts/05_package.py -- WhaleSwallow_v004_VO.mp3 WhaleSwallow_v004_60fps.blend
```
`05_package.py` bakes the per-shot cameras into one camera, keyed on every frame with constant interpolation. The baked
camera matches the per-shot cameras exactly on all 1715 frames (max error 0). It also sets the render settings, packs
everything and saves the file compressed.

## Shots (frame ranges)
| shot | frames | shot | frames |
|---|---|---|---|
| 1a breach, diver in the jaws | 1–95 | 6b spat out, splash, comes up treading | 876–982 |
| 1b jaws close | 96–191 | 7a hospital, front | 983–1038 |
| 2 inside the mouth, lying | 192–284 | 7b hospital, 3/4 | 1039–1132 |
| 3a humpback head-on, jaws open, him inside | 285–371 | 8a face and shoulders close-up | 1133–1181 |
| 3b feels the tongue (no teeth), 3c touches the baleen | 372–533 | 8b insert: bruised shin and foot | 1182–1240 |
| 4a–4b whale underwater | 534–671 | 9 nurse and doctor | 1241–1312 |
| 5a hand on the baleen | 672–733 | 10 doctors at the bed | 1313–1403 |
| 5b pushing the baleen | 734–808 | 11a–11b whale underwater | 1404–1531 |
| 6a whale bursts up | 809–875 | 12a lunge breach (no man) | 1532–1649 |
| | | 13 treading water, end | 1650–1715 |

Merged against the plan: 1c→1b, 5c→5b, 6c→6b, 12b→12a (the VO had no time for them). The life vest and the clipboard are
dropped. In the hospital he wears a plain shirt, with a blanket over his lap and legs. In 8b his hand is not on the knee:
it rests on the mattress, because a hand on the blanket crossed it.

## v004 changes (director notes on v003)
- **8a (1133–1181)**: medium close-up on his face and shoulders, looking up; no blanket in view.
- **8b (1182–1240)**: tight insert from above on the bruised left shin and foot; nothing above the knee, blanket out of frame.
  The shin bruise moved to the mid-lower shin (clear of the blanket edge) and is a little darker/stronger in all hospital shots.
- The preview's hospital range (981–1403) is re-rendered from this package; everything else is identical to the approved v003.

## v003 changes (director notes on v002)
1. **No shark, no teeth.** 3a is the humpback head-on underwater, pitched up with its jaws open (pink mouth, baleen),
   with him crouched inside. 3b and 3c are in the approved mouth set: he feels the tongue for teeth, then touches the
   baleen. The shark is deleted from the file and its credit removed. The whale's baleen is now one dark curtain
   per side; the separate tapered plates read as teeth.
2. **Eyes.** The irises are dark brown, not pale blue, and the whites are soft, not pure white. A face fill light,
   light-linked to the diver only so the sea is untouched, lights him at the end of 6b and in 13.
3. **8b** now frames from the foot end: the bruised shin in front, his face in frame. **8a/hospital:** the blanket can't
   reach his waist without crossing his torso and resting hands (measured), so in the hospital he wears pale-blue
   pyjama shorts instead of the red trunks. No red shows at his lap. Blanket rendered crossings: 0.
4. **9/10** push in from the wide; in 10 the doctor nods and the nurse points at him with her left hand.

## Checks (on the packed file)
- **clip_scan**: `BAD_RANGES` 985–1177 and 1243–1399 (hospital) are an artefact of the ShirtMask modifier, which deletes
  the body under the shirt so the evaluated vertex labels no longer match. Rerun with the mask removed: `BAD_RANGES []`.
- **qa_check**: FAN/CLAW in 10 (1333–1393) is the nurse's intended pointing hand. 21 CAMJUMP, one at each cut (intended hard cuts).
  - EMPTY: in 4a–4b, 6a and 11a–12a there is no person by design (whale only). In 5b and 8b the wall or blanket
    fills the frame by design (baleen push, shin close-up). In 6b, 949–979, he is under the splash for about 0.15 s, then
    small in the water as he surfaces.
  - INSIDE: 5a, 673–733. The camera sees the inside of the one-sided mouth shell from within the mouth. It is not inside
    any geometry: the preview shows a clean view.
- **limb_check**: ARMBODY with 2–4 points per arm, the shoulder and upper-arm points, on every character, the doctors
  with relaxed arms included. The 12–14-point hospital counts are the ShirtMask label artefact; with the mask removed they
  drop to 4–6 points. The preview shows no arm going through a body.
- **body_prop_cross**: 3a, 298–349: 3–4 cage verts where his seat meets the jaw floor in the deep crouch (wide
  shot, him small; the same class as the accepted 1 cm seat contact). Hospital frames 985–1403: These are cage and label artefacts: on the rendered
  (subdivided) body, the blanket crossing measure is 0, and seat contact with the mattress is 1 cm or less (accepted).
