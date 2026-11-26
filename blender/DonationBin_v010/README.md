# DonationBin_v010: the from-scratch rebuild (batch 1, film 09). Status: ON HOLD (FAIL after 2 fix rounds)

**Do not render.** Three previews were checked by a fresh harsh reviewer, and the last one (`review/preview.mp4`, check 3) still fails. The `.blend` is not pushed. The exact remaining faults by frame are in `review/CHECK3.md`.

## The film (built to the client's VO, frames 1–2388 at 60 fps)
- **Parking lot (0–4.4 s):**
  - A woman on a milk crate reaches into a royal-blue donation bin. The DA KRAS FILMS header is on it.
  - A man shoves her and she tumbles in through the one-way flap.
  - The camera follows her through the opening.
- **Inside (4.4–31 s):**
  - The flap slams. She sits up, turns and pushes it; it only swings inward and the latch holds.
  - She feels for a handle and a latch, reaches up the tall walls and screams.
  - Three days pass curled on the clothes, with the light going from day to night.
  - A passer-by pushes the flap in and sees her.
- **The rescue (31–39.8 s):**
  - A cut line and sparks run round the lower front panel, and the panel falls outward.
  - The camera goes out. She sits in the opening, feet on the fallen panel, with two firefighters and the passer-by.
  - The camera rises to the row of bins.

## Client lessons built in
- **Solid bodies:** the MPFB delete-group masks are removed. The skin under the cloth is pulled 1 cm in, so it never pokes through and no opening shows a hollow.
- **Garments:**
  - They are real CC0 MakeHuman garments with 3 mm of cloth thickness.
  - The trouser waist is tucked under the top.
  - The trousers have no crotch hole: the closed meshes were checked.
- **Bin contact:**
  - A per-frame depth audit checks the body, clothes and shoes against every bin wall, the flap, the cut panel and the crate.
  - The flap angle is solved per frame, so it rests on her body as she passes and never cuts into her.
  - She is snapped onto the clothes heap per frame.
  - At the end she sits in the cut opening.

## Files
| File | Contents |
|---|---|
| `DonationBin_v010_VO.mp3` | the client's VO (same as v009) |
| `beats.json` | beat frames (from the v009 sync anchors) |
| `review/preview.mp4` | check-3 preview of the packaged file (every 5th frame, 270x480, VO) |
| `review/CHECK3.md` | the check-3 verdict and the remaining faults by frame |
| `scripts/` | `lib_build` + `01_build` (set, characters, garments), `lib_anim` + `02_animate` / `02b_inside` / `snap_heap` / `02c_fx_camera` (staging, flap, panel, light, camera), `03_package`, `preview_range` |

To rebuild: unpack the CC0 asset packs `shirts01`, `pants01` and `suits01` from files.makehumancommunity.org into MPFB's `data/clothes`, then:
1. Fetch the four Sketchfab models in `CREDITS.md` as glTF into one directory, named `crate/`, `clothes2/`, `helmet2/` and `saw/`.
2. Build: `blender -b --python scripts/01_build.py -- <that dir> base.blend`
3. Animate: `blender -b base.blend --python scripts/02_animate.py -- anim.blend`
4. Package: `blender -b anim.blend --python scripts/03_package.py -- DonationBin_v010_VO.mp3 DonationBin_v010_60fps.blend`
