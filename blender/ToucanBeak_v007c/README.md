# ToucanBeak v007c: the stick is held (Connect28)

This is the same film as v007b, frames 1–1750 at 60 fps. The beats in `beats.json` are unchanged and no VO has been added. Only the stick changed.

**The stick no longer hangs or swings by itself.**
- **Frames 1–92:** the shot opens on the bird with no stick in view.
- **From frame 93:** the stick enters already held. A generic person's forearm and hand grip it, with the sleeve running off the top or left frame edge.
  - The person is a copy of the clinic assistant's body in a plain brown jacket (no scrubs). It shares the existing mesh data, so the package size barely changes.
  - The grip is `hand_poses.grip_object`: the hand is placed on the stick's surface and the fingers close round it.
  - The holder is parented to the stick's swing pivot, so the grip stays rigid through the strike.
- **The swing is unchanged.** The stick is slimmed to a hand-held thickness of about 4–6 cm.
- **Visibility:** the holder is visible only at 93–130. Its body stays off-frame; only the forearm and hand are seen.

**Files:**
- **Preview:** `review/preview.mp4`, rendered from this exact package.
- **QA:** `review/qa_v007c.json`.

## Checks on the packed file
- **Size:** 94.76 MB, normal git file.
- **Factory-startup open:** 0 unpacked images, 0 libraries, frames 1–1750.
- **Check still:** `package_check_lowres.jpg`, frame 104 (the held stick at the strike).
- **qa_check:** 0 for CLAW, FAN, HOVER, FACEPRESS, BACKHEAD and ROLL. CAMJUMP 9, all of them the intended cuts.
