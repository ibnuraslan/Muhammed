# ToucanBeak v007d: the strike with no hand (director option A) (Connect28)

This is the same film as v007c, frames 1–1750 at 60 fps. `beats.json` is unchanged and no VO has been added. Only the strike changed.

## The strike
- **Before the strike (frames 1–92):** the opening stays on the toucan on its branch, with no stick and no hand.
- **The strike (93–115):** the stick whooshes in from the top edge of the frame and hits the beak, at frame 102, then leaves. It is on screen for about 0.4 s. Motion blur is off, so there is no blur.
- **After the strike (from 116):** the beak is broken and the stick lies on the ground below the perch.
- **The holder:** the holder from v007c is fully hidden, so no hand or arm appears anywhere.

## Files
- **Preview:** `review/preview.mp4`, rendered from this exact package.
- **QA:** `review/qa_v007d.json`.

## Checks on the packed file
- **Size:** 94.77 MB, normal git file.
- **Factory-startup open:** 0 unpacked images, 0 libraries, frames 1–1750.
- **Check still:** `package_check_lowres.jpg`, frame 102 (the impact).
- **qa_check:**
  - 0 for CLAW, FAN, HOVER, FACEPRESS, BACKHEAD and ROLL.
  - CAMJUMP 9, all of them the intended cuts.
  - PROPMOVE flags the stick's whoosh at 93–115. This is intended: it is the strike the director asked for.
