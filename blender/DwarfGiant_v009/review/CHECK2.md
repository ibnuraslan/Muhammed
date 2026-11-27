# v009 check 2 (after fix round 2, the last allowed round): FAIL, ON HOLD
`review/preview.mp4` is the preview of the exact packed file (every 5th frame, 270x480, with the VO). I watched all 9 contact pages. Frames are film frames at 60 fps.

## Fixed in rounds 1-2 (confirmed in this preview)
- His right arm no longer crosses his pelvis; the hanging hands are kept outside the hip width.
- The growth reads in the wide: he grows from below the officer's shoulder to the officer's shoulder (f519-680), then shoots past him.
- The hands close-up has hand and finger motion, the hands sit at chest height, and they move forward before dropping (no pass through the bib).
- Spine x-ray from 40 degrees to his side: the S-curve reads, and the rod is off his body.
- Hearing beat: both men whole; he turns his ear to the officer, who talks.
- Pendant lamp removed. A moving arc replaces the static late wide.

## Still wrong (fix list for the next round)
1. **f1886-2083 (end, 3.3 s): his face is cut in half by the right frame edge, and the "DA" of the logo plaque is cut by the left edge.** Fix: end camera about 0.25 m further back (or lens 32 -> 26), aimed at x = -0.35, so the plaque, the photo and his whole head all sit inside the frame.
2. **f1426-1486: in the profile x-ray head the officer's face sits behind his transparent head (two heads merge), and the shrinking tumour can't be seen.** Fix: put the camera on the hero's other side (+X, toward the window) at the same distance, or hide the officer for this beat, and make the tumour larger and brighter (scale x2, emission 6) while it shrinks.
3. f1101-1176: the DA KRAS FILMS plaque shows through his x-ray head (minor). Fix: start the side camera 0.2 m lower.
4. f86-100: the officer slides out at the right edge while the camera pushes in to the hero (minor, a camera move).

## Checks on this package (DwarfGiant_v009_60fps.blend, 26 MB, not pushed)
- clip_scan: 0 bad ranges.
- body_prop_cross (RM_Rod, RM_DeskTop, RM_DoorLeaf): 0 crossings.
- limb_check: the only ARMBODY hits are 2 points at the shoulder (the documented upperarm01 false positive). The PROPHEAD hits are the intended hormone beads inside the x-ray head.
- qa_check: PROPMOVE only for the hormone beads (intended, no hands involved). EMPTY at f85-121 and f445-463 (the hero is fully in frame there per the pages; it is a detector miss).
