# HeadsetBullet v007: fixes and checks (director, Nov 14)

Package: `blender/HeadsetBullet_v007/HeadsetBullet_v007_60fps.blend` (74 MB, normal git file, no LFS).
Preview: `blender/HeadsetBullet_v007/HeadsetBullet_v007_preview.mp4`. It is rendered from the packed file with `pipeline/preview.py` (270×480, 4 samples, every 5th frame at 12 fps, frame numbers burned in). I watched every contact page (`pipeline/watch_pages.sh`).

Every story-beat frame is unchanged (1, 133, 241, 355, 571, 697, 835, 949, 1165, 1315), and `beats.json` is identical to v006.

## The five notes
| # | Note | Fix |
|---|---|---|
| 1 | f557–682: sharp, head in frame | A steady side medium close-up at f/8 (35–40 mm). His head and shoulders are in frame throughout, and the bullet approaches the ear cup. |
| 2 | f682–956: medium close-up from the side, the bullet strikes the cup with sparks, readable in about 1 s; no cutaway; nothing through the head | The same side MCU. At f697: a 40-spark burst, a point-light flash, the crack spreads and the RGB ring dies. The sparks, chips and dust fly out behind the cup and inherit his head's jolt, so they never cross his face. The cutaway is removed. The yoke top bar is removed, and the yoke arms sit on the outer half of the cup, clear of the ear and hair. |
| 3 | f991–1123: him in the foreground, the bullet hits the poster behind him | Framed from his right-front, his head and shoulders in the foreground and the print behind him. The bullet hits it: the glass shatters and plaster puffs out. No empty-wall frame. |
| 4 | Black hairline band in the face close-ups | **Packaging bug.** `05_shrink.py` re-encoded textures with `save_render`, which dropped alpha (the hair, brow and lash cards turned solid black) and baked in the view transform. It now uses `Image.save`, writing raw pixels and keeping alpha. Alpha cards stay PNG; everything else, including their normal and rough maps, is JPEG. **This affected every shrunk package from v002 to v006.** |
| 5 | f1413–1498: end on his face, shocked, holding the broken headset, the hole behind him | He glances back over his shoulder at the hole (f1425–1450), then turns back toward the camera. From about f1460 there is a steady three-quarter view of his shocked face from his right-front, with the print's bullet hole on the wall behind him and the broken headset in his hands at the bottom of the frame. |

Also, from watching the preview:
- The orbit at f321–331 was raised so it clears the chair back.
- The close-up of him holding the headset at f1265–1300 keeps the camera in front of the monitor plane.

## Checks (on `work/anim_v007.blend`, the source of the package)
- `clip_scan`: BAD_RANGES []
- `qa_check` (step 6): INSIDE 0, FILL 0, FAN 0, CLAW 0, CAMJUMP 0, ROLL 0.
  - **ATTACH 2** (f1, f25): "RidgeCap 50 cm off Teen's skin". RidgeCap is the house's roof ridge, a name match. The headset has **0** ATTACH flags.
  - **BACKHEAD 3** (f1, 133, 241): the exterior and bullet chase from behind him, by design (beats 1–3).
  - **EMPTY 34:**
    - f43–97: the exterior chase before he is in view.
    - f115 and 229–325: the bullet approach, where he is small in frame.
    - f361 and 385: the orbit over his shoulder onto the keyboard, character about 14%.
    - f1309 and 1315: the broken headset fills the lower frame.
    - f1441 and 1447: the glance back at the hole, character 6–9%, with his head at the frame edge and the hole visible.
  - **PROPMOVE 3680:** FX particles moving without a hand on them (the bullet, glass, debris, sparks, drops, birds, leaves). This is expected.
- `limb_check` (step 2):
  - **PROPHEAD 417:** the ear cushions resting on his head, which is intended contact.
  - **ARMBODY 89:** points 0–1 of upperarm01, the shoulder joint inside the deltoid. Widening the arms made it worse (223), so I left it; it's a limitation of the check.
- `audit.py`: head into the worn headset 0.0 mm. Hands into the desk, keyboard or mouse: at most 3.0 mm. Hands into the headset (cradle grip): at most 3.7 mm.
- `audit_hands.py`: 0 hand overlaps. There are 13 soft wrist-angle flags (|x| > 70°) at f343–357 and 1227–1243, the same as v006 and within the pinned v005 wrist limits.
