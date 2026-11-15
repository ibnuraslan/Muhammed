# ToucanBeak v008c: the director's v008b notes (Connect28)

This is the same film and VO timing as v008b: frames 1–1932 at 60 fps. `beats.json` is unchanged and no VO has been added.

1. **Printer (1159–1368):** there is now one bed and no floating block.
   - **Second plate:** the original clinic printer object stood on the same bench, under the real-size printer. That produced the second, tilted bed plate. It is now hidden for the whole film.
   - **Floating block:** the separate animated hot-end block and nozzle beside the print are hidden during the printer shot. The printer's own head stays overhead while the beak builds.
2. **Cut into the lab (505–520):** the camera no longer starts behind the shelf. The move now begins from the clear position at old frame 521 and eases on, with no slabs in the lens.
3. **Minor (1513–1586):** the glue syringe sits in VetB's left-hand pinch while he glues, between the thumb and index tips. The pinch is no longer around nothing.

- **Preview:** `review/preview.mp4`, rendered from this exact package.
- **QA:** `review/qa_v008c.json`.

## Checks on the packed file
- **Size:** 94.78 MB.
  - The duplicate printer is deleted; it shared its mesh with the real-size printer.
  - Packaging fix: `06_package.py` now unhides an object while decimating it. Hidden objects were not evaluated, so the printer was never actually decimated.
- **Factory-startup open:** 0 unpacked images, 0 libraries, frames 1–1932.
- **Check still:** `package_check_lowres.jpg`, frame 1311 (the print building on the bed).
- **qa_check:**
  - CAMJUMP 11: intended single-frame cuts only (505, 623, 719, 858, 912, 1041, 1159, 1394, 1501, 1587, 1634).
  - 0: CLAW, FAN, HOVER, FACEPRESS, BACKHEAD, ROLL.
