# ToucanBeak v007b: the two director notes on v007 (Connect28)

Same film as v007 (frames 1–1750, 60 fps). The beats in `beats.json` are unchanged from v007. No VO has been added. Only the two items below changed.

1. **Screen close-up, 736–845:**
   - The display behind the monitor's glass is now dark (#101820), and the camera is close enough that the monitor fills about 80% of the frame width.
   - The beak is shown large, in side view, filling about 70% of the screen width.
   - The scanned stump is solid orange. The missing half draws in as a thick, bright-cyan wireframe (750–800), then fills solid (805–830).
   - The wireframe runs on a decimated copy of the scan, which gives clean CAD triangles with no spikes.
   - The old void display is parked out of view during this shot.
2. **Tree trunk, 81–96:** the 90 camera key is re-placed, so the line of sight to the bird stays clear of the trunk. No bark fills the frame.

3. **Printer ends on the hollow print, 1061–1085 (0.4 s):** a cut-in on the printed beak on the bed, seen from its cut side, showing the thin shell with the gyroid lattice inside. Beat 8 (992) stays on the printer shot.

- **Preview:** `review/preview.mp4`, rendered from this exact package.
- **QA:** `review/qa_v007b.json`.

## Checks on the packed file
- **Size:** 94.77 MB. The CAD overlay shares the existing beak meshes, with materials set per object.
- **Factory-startup open:** 0 unpacked images, 0 libraries, frames 1–1750.
- **Check still:** `package_check_lowres.jpg`, frame 816 (the screen close-up).
- **qa_check:** the same classes and causes as v007.
  - CAMJUMP 9: only the intended cuts (528, 676, 736, 846, 896, 986, 1061, 1086, 1522).
  - 0: CLAW, FAN, HOVER, FACEPRESS, BACKHEAD, ROLL.
