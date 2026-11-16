# BatBite_v002: Phase 2, built to the voiceover (for director review)

Phase 1 (BatBite_v001, commit 821869c) laid out to the VO `BatBite_v002_VO.mp3` (22.6 s). Shots are moved to the word
frames and trimmed, never stretched (all character animation plays at 1×). One farm camera, hard cuts baked into it.

- File: `BatBite_v002_60fps.blend` (51 MB, every texture and the VO packed, `package_for_farm` PROBLEMS none)
- Frames **1–1362** at 60 fps (22.7 s). Settings: `SETTINGS.md`. Credits (CC-BY block for the description): `CREDITS.md`.
- Preview watched start to finish (every 5th frame, all 6 contact pages, plus 540×960 zooms of the doubtful frames):
  `review/preview.mp4` (with the VO).

## Cuts and beats (frame = 1 + round(seconds × 60) of the first word)
| Frame | Shot | Words |
|---|---|---|
| 1 | S01 crowd POV, bat flies over the fans | "A fan threw what looked like…" |
| 95 | S02 bat lands on the deck | "…rubber bat onto the stage…" |
| 150 | S03 he notices it | "…during the concert." |
| 276 | S04 steps toward it | "Without thinking," |
| 349 | S05 crouches, reaches | "Ozzy Osbourne picked it up…" |
| 386 | S06 stands holding it | "…and bit into it," |
| 416 | S07 lifts it to his mouth | (continues) |
| 460 | S08 profile bite (cut on contact) | "…believing it was just a toy." |
| 494 | S08c crowd cheering (covers the hold) | |
| 599 | S09 recoil, lets it fall | "But the moment he bit down," |
| 712 | S10 shock close-up | "he realized the bat was real." |
| 843 | S11 stares, hand toward his mouth | "Its blood filled his mouth…" (no blood shown) |
| 929 | S12 wide from the crowd | "and he immediately understood…" |
| 1029 | S13 bends over, hands on his thighs | "…what had happened." |
| 1093 | S14 hospital: doctor with the chart | "After the concert, he was rushed to the hospital," |
| 1239 | S15 oxygen-mask close-up | "where doctors gave him rabies shots." |

## Director notes (Phase 1 pass) — done
- **Grab window cut:** S05 uses source 408–445, S06 starts at source 516 (the 445–515 finger-closing frames are not in the film).
- **Strap deleted:** no `OxyStrap` object in the file.
- **Bite tip 6–8 mm off the lips, cut on contact:** measured every frame on the packed file against the posed face surface
  (`scripts/09_face_clearance.py` → `review/bite_face_clearance.txt`): bite shot f460–493 closes from 12.6 to **7.4–7.7 mm**
  at the cut; minimum anywhere in 400–600 is **7.0 mm** (f588, crowd shot, he is off screen).
- **f679 re-routed:** the folded wing used to graze his chin (0.3 mm). Now ≥ 7.9 mm (edited f456 = source f676, closest pass).
- **In-fist grazes / f540:** the fist round the bat's body still touches the fur (body_prop_cross: finger/metacarpal ↔ Bat
  in f385–415, 460–493, 601–646 only). Zoomed at f410 (= source 540): no fur through the back of the hand.

## Checks on the packed file (all in `review/`)
| Check | Result |
|---|---|
| `clip_scan` (hands into bodies) | **0 bad ranges** (two single-point hits at f997/f1027, under the 25-point limit) |
| `qa_check` | BACKHEAD 5, CAMJUMP 14, PROPMOVE 5, **ATTACH 0** — see below |
| `limb_check` | ARMBODY 1869: every hit is an upper-arm point within 8 cm of the shoulder joint (no forearm/wrist point, no arm in another body) — the documented shoulder false positive, extended by raised fist-pumping arms |
| `body_prop_cross` | Bat: in-fist only (accepted). Clipboard: the doctor's fingertips touch its underside (it rests on his flat hand), f1093–1237. Blanket: patient's fingers touch the blanket top at f1123–1132 (hands resting on it) |
| bat ↔ face | ≥ 7.0 mm on every frame 400–600 |

qa flags explained: **CAMJUMP** = the 15 planned hard cuts (one camera, cuts baked as keys). **BACKHEAD** = the crowd-POV
shots (f1, 277, 931, 1027: front-row fans in the foreground) and the over-the-shoulder reverse at f97. **PROPMOVE** = the
oxygen mask moving with his breathing head (it is carried by the head bone, no hand needed).

## Fixed in Phase 2 (found by the checks and the preview)
- Bat came to 0.2 mm off the lips in the bite (target point sat on the lip surface) → solved on the real face surface to 7 mm.
- Hands sank into his own thighs (after the drop, bent over: 3–8 cm) and under the blanket in bed (up to 11 cm) → palms
  placed on the posed jeans / blanket surface by ray cast; the right hand swings outside the thigh after letting go.
- Doctor's clipboard hand: fingers into his chest, and the board followed the IK target instead of the real wrist (cut
  through his palm) → board carried by the real wrist, 0.50 m out on a flat hand.
- Oxygen-mask cup 7 % lower (qa ATTACH 0).

## Known issues (for your call)
- Bent over (f1029–1092): the right palm sits ~4.5 cm off the jeans (needed to keep the fingers out of the thigh); it reads
  as resting in the preview.
- Doctor's middle fingertip touches the clipboard's underside (intended: the board rests on his hand).

## Scripts
`scripts/01–06` as Phase 1 (05 with the clearance solves), `07_edit.py` (VO edit: shift-only, no retime),
`08_bake_camera.py` (single FilmCam), `09_face_clearance.py`. Rebuild: `work/rebuild.sh` (work/ is not in git).
