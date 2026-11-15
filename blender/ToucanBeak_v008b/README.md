# ToucanBeak v008b: beats 7–8 are no longer static (Connect28)

This is the same film and VO timing as v008: frames 1–1932 at 60 fps, with `beats.json` unchanged (1, 114, 266, 512, 625, 780, 913, 1159, 1394, 1501, 1634). No VO has been added. Only beats 7 and 8 changed.

1. **Beat 7 (913–1158).**
   - **Weighing gag, 913–1040 (2.1 s):** VetB bounces the solid metal beak on his open palm and frowns. Two more bounces have been added; it plays at normal speed.
   - **Hard cut to the screen, 1041–1158 (2 s):** the monitor fills about 80% of the frame. On the dark display is a toucan silhouette in profile (pale blue) with a solid orange beak. The beak drags the head down: the bird tips about 25° and settles there.
2. **Beat 8 (1159–1393).**
   - **The build, 1159–1368:** the camera sits at the printer bed. The beak builds up layer by layer from the first visible layer to full height, with the print head moving above it. The camera pushes in slowly the whole time.
   - **Hollow cut-in, 1369–1393:** kept from v008.
   - **Fixed along the way:** the print had sat about 6 cm inside the bed, hidden. That came from the bed height after the printer was scaled to real size. The print and the hollow cut-in now rest on the bed top.

- **Preview:** `review/preview.mp4`, rendered from this exact package.
- **QA:** `review/qa_v008b.json`.

## Checks on the packed file
- **Size:** 94.79 MB.
- **Factory-startup open:** 0 unpacked images, 0 libraries, frames 1–1932.
- **Check still:** `package_check_lowres.jpg`, frame 1110 (the head dragged down).
- **qa_check:**
  - CAMJUMP 11: intended single-frame cuts only (505, 623, 719, 858, 912, 1041, 1159, 1394, 1501, 1587, 1634).
  - 0: CLAW, FAN, HOVER, FACEPRESS, BACKHEAD, ROLL.
