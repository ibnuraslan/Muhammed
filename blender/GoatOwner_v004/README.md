# GoatOwner_v004: acting pass (Connect32)

`GoatOwner_v004_60fps.blend` is **69 MB**: packed, compressed, and a plain git file (no LFS). It is 1080×1920 at 60 fps, frames 1–2190. Every story-beat frame is unchanged from v002/v003 (`beats.json`), so the director's VO re-sync applies as is.

It is built on v003. The director's mouth fix is kept: strong reds on `M_Goat` are pulled to a dark grey-pink.

## What changed: see `review/ACTING_notes.md` (18 items)
- **Stick:** held in a closed fist, not lying on the back of his hand.
- **Arms:** no stiff T-pose or sideways-reaching arms. After the hits his arms hang toward his stomach instead of flung-out claws.
- **Goat:**
  - legs no longer cross while it backs away
  - beat-4 head-down stance and charge bend are about halved
  - the time-lapse is a continuous fast-forward walk, with no teleports
  - the owner's pop-in visits are removed
- **Camera:**
  - Beat 2 frames the goat with the passer-by beyond it.
  - No frame filled by his jeans (15.5 s) or his back (20 s).
  - No near-empty time-lapse frame.
  - No official's hand at the lens (31 s).
  - The lane crane looks at the tree line.
- **Death beat:** he lies with his arms close to his body, not spread like a star.
- **Rescuer:** kneels closer. The goat raises its head to eat from her open palm while her other hand strokes its head and neck.

## Checks
- **Sheets:** `review/before_v003_0.5s.jpg` and `review/after_v004_0.5s.jpg`, one still every 30 frames.
- **Hand close-ups:** `review/hand_closeups_v004.jpg`.
- **clip_scan** (`review/clip_scan_v004.json`, step 6): 2 single-sample hits.
  - f943 (15.7 s): the owner's raised hand dips into his own shoulder region while the stick goes up.
  - f1849 (30.8 s): official B's free hand crosses her own body while she walks beside the goat.

  Both are one sample long and not yet fixed.
- **qa_check** (`review/qa_check_v004.json`, step 6): BACKHEAD 3, EMPTY 264, FILL 5, INSIDE 3.
  - **EMPTY 264:** mostly goat-only framings. The check counts only MPFB humans as characters, so shots of the goat alone (beats 2–4, the charge, the porch chase) register as empty.
  - **FILL / INSIDE, f439–445:** the camera is in the goat's neck at the end of beat 2. A real fault, not yet fixed.
  - **INSIDE / FILL, f1291:** the camera passes through a dust volume.
  - **INSIDE, f1999:** a single sample during the pasture descent.
  - **BACKHEAD:**
    - f1: the owner is seen from behind the fence.
    - f1519: he lies face down.
    - f1735: an official is seen from behind as the team arrives.

The source is `../GoatOwner_v001/scripts/` (01–05). The look pass uses `pipeline/anim_look.py --no-sky --exposure 0.15` from the director branch.
