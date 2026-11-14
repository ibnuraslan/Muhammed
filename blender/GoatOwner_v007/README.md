# GoatOwner_v007: preview-pass fixes (Connect32)

This is v006c (approved, 6cbe5e6) after a full moving-preview watch (`pipeline/preview.py`, every 5th frame, then `watch_pages.sh`). These are the faults found and how each was fixed.

## Contact and props
- **Horns in his body.** At both hits the goat's head sank about 30 cm into the owner's body (measured against the evaluated body and overall meshes). The goat now stops short:
  - First hit (f944–964): 2–6 cm gap.
  - Second hit (f1146–1160): 10–15 cm gap.
  - The f1152 head toss is removed; he folds over the goat there.
- **Stick stays in his hand.** He no longer drops it at the first hit. He holds it through both hits, the stagger and the stairs.
  - During the hits (f957–1198) it is angled down and back from his fist. Held in the normal grip it pointed straight ahead, through the goat.
  - It leaves his hand only as he goes over the porch edge (f1452). It falls under gravity and lands visibly beside his body by f1476, not under him.
- **Porch fall.** The side rail on the south porch edge is removed, so he no longer goes over the edge through a rail.
- **Hands.** After the hits his left hand clutches his stomach and his right hand keeps its grip on the stick.

## Camera (framing only; one continuous move as before)
- f151–176: his arm swept past the lens. Key 186 is now a wider absolute position.
- f191–281: the goat's flank filled the frame, or the goat was cut at the edge. Key 250 changed.
- f436–446: the camera passed through the goat's body. A new key at 445 routes it round the goat's head; key 462 changed.
- f601–676: the goat was cut at the edge, then filled the frame. Key 630 is wider and centred on the whole goat.
- f261–291: the goat left the frame, leaving it nearly empty. A new key at 285 keeps it in frame.
- f496–541: the straight path from key 462 to key 540 went through the goat. A new key at 500 routes round its east side.
- f856–896: the owner was half out of frame with the stick raised. Key 880 now frames both him and the goat.
- f1166–1211: his back filled the frame. A new key at 1166 makes a wider arc; key 1182 changed.
- f1876–1906: the spline dipped back behind the shed, which filled the frame, then the camera skimmed the truck. New keys at 1880 and 1895 hold beside the ramp, and the 1905 key rises above the truck before the fly-over.
- Kept as designed: the eye macro (f666–790) and the fast whip turn (f793–807) are close-ups of the goat's head.

## Unchanged
- Beat frames (`beats.json`) are unchanged.
- No VO was added.

## Other
- Render speed: the dust-puff volume objects are now hidden outside their active frames. Before this they cost about 20 s per frame even while parked under the ground.

`GoatOwner_v007_60fps.blend` is 69 MB: packed, compressed, and a plain git file.

## Files in `review/`
- `preview.mp4`: the moving preview, every 5th frame at 12 fps (real speed), 1080×1920 scaled to 270×480 with 8 samples.
- `pages/p01–p09.jpg`: contact pages of every preview frame.
- `qa_check_v007.json`, `clip_scan_v007.json` and `limb_check_v007.json`.
