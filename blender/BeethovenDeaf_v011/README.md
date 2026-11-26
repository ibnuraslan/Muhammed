# BeethovenDeaf_v011: the batch 1 rebuild of film 08, the director's final round

This is a from-scratch rebuild of *Beethoven heard through his jaw*:
- one continuous camera
- timed to the client's voiceover (`BeethovenDeaf_v011_VO.mp3`, also packed)

Render frames **1–1435** at 60 fps (23.9 s). The farm settings are in `SETTINGS.md` and the attribution is in `CREDITS.md`. The review history is in `review/` (CHECK1–3), and `review/preview.mp4` is the check-3 preview of this exact file.

**Status: delivered for the director's review. Not client-approved yet.** See "Known issues" below.

## What is in the film
| Frames | VO | What you see |
|---|---|---|
| 1–205 | "He would bite down on a metal rod attached to his piano…" | His face with the brass rod held in his teeth, lips closed round it. The camera follows the rod down to its clamp on the piano case. |
| 206–403 | "…while playing. The piano's vibrations traveled through the rod…" | He plays (side mid-shots); cyan rings leave the clamp and travel up the rod to his teeth. |
| 404–593 | "…into his jawbone and reached his inner ear." | An x-ray window opens on his right cheek. The skull is fitted to his head, the rod is held in the skull's teeth, and pulses run teeth → jaw → ear. |
| 594–797 | "This sent the sound vibrations directly through his skull…" | A glow wave sweeps over the skull. |
| 798–1025 | "…completely bypassing the eardrum and allowing him to hear clearly." | Ear close-up: a red pulse dies at the dull, torn eardrum while the cyan path goes round it. The cochlea lights up and his eyes close. |
| 1026–1435 | "Using this method, Beethoven was able to keep composing music…" | The x-ray closes, and the camera cranes up over the piano, then orbits down to his side. The DA KRAS FILMS print on the wall reads at 19.2–22.5 s (frames 1150–1350). |

## How it was built (scripts in `scripts/`)
- **Composer** (`char.py`):
  - an MPFB/MakeHuman CC0 body
  - a real loose suit garment (`toigo_male_suit_3`): navy coat, white shirt, red neckcloth. Its cloth is thickened.
  - the skin under the clothes is **kept and pulled 8 mm inward** (`solid_inset`), not deleted, so every cuff, collar and trouser opening shows a solid body
  - wild grey hair, and the eye fix
- **Hands** (`02b_hands.py`):
  - one arched pianist pose, posed by hand. The palm sits over the key fronts, and each finger's curl and spread is solved so that its fingertip pad rests on its own white key, following the key down 3.6° when pressed.
  - the black keys start 7.2 cm back, so the knuckles stay clear of them
  - mesh audit: `scripts/key_contact_check.py`
- **Rod** (`02c_rod.py`):
  - its end is held 10 mm behind the incisor fronts (the jaw opens 5.5 mm), and the lips close round it
  - it passes through a brass collar on the case, sliding slightly as he sways
- **Rebuild:** `scripts/fetch_assets.sh`, then `scripts/extract_v010_assets.py` (the CC-BY piano, bench, candelabra, skull and ear meshes from v010), then `scripts/build_all.sh <scratch>`.

## Audits on this file
- **Hands vs keys:** this is the subdivided, deformed mesh, sampled every 4th frame.
  - The worst depth of a hand inside a key is **2.55 mm** (frames 65–81, a fingertip pad between solved frames).
  - 47 of 359 samples exceed 1 mm; most of those are 1.0–1.5 mm.
  - There is no knuckle intrusion into the black keys.
- **Hand solver:** pad-to-key contact is within ±1 mm on more than 97 % of solved finger frames.

## Known issues (honest list)
- **Hands:**
  - At small size the hands read as compact.
  - The little fingers hover 2–5 mm above their keys on about 5 % of solved frames.
- **X-ray look:**
  - The hair is CC0 card hair recoloured grey, and reads slightly papery.
  - In the x-ray the skull is pale cream.
  - In the 800–950 ear close-up the top of the frame is soft hair.
- **Framing:**
  - Frames 101–111: his head touches the left frame edge for about 0.2 s.
  - Frames 1121–1146: candles pass through the foreground.

## Render check: PASS
These checks ran on this exact file, `BeethovenDeaf_v011_60fps.blend` (33 MB), with Blender 5.2.2 `--factory-startup`:
- It opens with no errors and no missing files: 0 linked libraries, 0 unpacked images, the sound is packed, and there are 0 drivers.
- Settings: camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1435, output `//render/BeethovenDeaf_v011_####.png`, and the VO strip is present.
- Three full-resolution test frames rendered from the packed file, none of them black, empty or pink:

| Frame | Render time (4-core cloud CPU) | Mean RGB |
|---|---|---|
| 100 | 3 min 6 s | 102/117/111 |
| 700 | about 6 min (x-ray) | 102/119/118 |
| 1400 | 3 min | 97/99/91 |
