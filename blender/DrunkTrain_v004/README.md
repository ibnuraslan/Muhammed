# DrunkTrain_v004: farm package (the animated look + hands, with the x-ray replay fixed)

v004 is v003 with only the director's 27–31 s fix (all else unchanged):
- The slow-motion x-ray replay is framed close: the muscle figure fills at least half the frame height.
- The ghost train is deeper, saturated cyan with a strong fresnel rim and edges.
- The force arrows are smaller, so they no longer fill the frame up close.
- The studio gradient is a more saturated cyan at the top.
- The exit no longer whips through a blank studio. The camera dives into the x-ray body and comes out of Lad's back in the real scene (as at the entry). Beat 12 now starts 4 frames earlier, at frame 1858 (30.95 s); `beats.json` is updated.

This is the client's look change (Nov 11 22:45 UTC), made after v002 was delivered: bright, clean 3D animation instead of photoreal.
- AgX Punchy, a sky-gradient backdrop seen by the camera, and high-key light (`pipeline/anim_look.py` plus hand-tuning).
- Clean saturated surfaces: a clean red locomotive with no grime, and bump around 0.3.
- A bright cyan-to-near-white studio for the x-ray.
- f/5.6 and no motion blur.
- A cool fill light that keeps the under-train beats readable.
- The hit is staged as a stylised orange impact flash, with no injury read.
- The modelled cab numbers on the locomotive are removed.

- **Hands pass (client, 23:00):**
  - Limit Rotation constraints on every finger, thumb and wrist of all four characters (128 constraints).
  - Relaxed curled default hands.
  - Real grips on the bottle.
  - Re-keyed poses: Lad's flung arms stay outward, WitA covers her mouth with one hand and holds the other off her chest, the run arms swing wider, and the worker steadies himself with an arm.
- **Hand audit** (BVH every 2 frames: hand vs hand, own torso/head, own clothes excluding sleeve cuffs, other characters): **1 hit**. WitB's left hand brushes her jacket hem for a single transition frame (f1059). Report: `review/v004_hand_audit.txt`. Close-ups of every hand action: `review/v004_hand_closeups.jpg`.

v002 (the earlier photoreal look) is kept for reference.

This is the full 34.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `DrunkTrain_v004_60fps.blend` (73 MB, compressed, a normal git file with no LFS): the self-contained scene. Every texture is packed.
- `beats.json`: the start frame of each of the 12 beats. There is no voiceover yet, so the film is built to the brief's target beat times. When the VO arrives, retime with `pipeline/retime_to_vo.py`, using these frames as the old anchors and the VO's word times as the new ones.
- `SETTINGS.md`: render settings, test frames and the measured frame cost. `CREDITS.md`: the CC-BY block for the video description (`models_credits.json` has the full metadata).
- `package_check_f760_lowres.jpg` and `package_check_f1700_lowres.jpg`: 25 %, 8-sample frames rendered from this packed file opened in factory Blender. They show the package works; they are not a quality reference.
- `review/`: the 1 s sheet in this look, hand close-ups and the hand audit.

The source is `../DrunkTrain_v001/scripts`. Build order: `01_build_people.py`, then `02_build_scene.py` (which runs `02b_fit_muscles.py`), then `03_animate.py` (which runs `03b_fx_camera.py`), then `pipeline/anim_look.py`, then `05_package.py`. The hand checks are `06_hand_audit.py` and `07_hand_closeups.py`. `04_audit.py` is the audit.

## Beats (frame = 1 + t × 60)
1 stumble 0.0 · 2 head on the rail 2.5 · 3 train rushing 5.5 · 4 impact and spin 9.0 · 5 dragged beneath 11.0 · 6 screech to a stop 14.5 · 7 witnesses 17.0 · 8 stands up 19.5 · 9 flash-back swig 21.0 · 10 x-ray, loose muscles 23.5 · 11 slow-motion replay with force arrows 26.5 · 12 walks off, cuts on his palm 31.0

## Known issues
- **Brief contacts.** He touches the loco under-gear in 5 sampled frames during the drag and the crawl-out (11.1, 12.6, 19.6 s). They are a few centimetres and in dark frames. The camera passes 6 mm from the under-frame at 13.7 s.
- **Under-gear opened up.** To give a body-sized gap between the rails, the locomotive's low centre under-gear and the bottom plate of its pilot were removed, and its wheel discs were replaced by our spinning wheelsets. This is not visible in the shots.
- **Feet in the air.** His feet are in the air for about a second during the sit and flop (3.8–5.0 s). While he lies on the ballast, his heels rest about 3 cm above the base plane, covered by loose stones.
- **Small details.** The final grin is subtle. The three palm cuts are small and only read at full resolution.
- **Studio whip.** The whip out of the x-ray studio (30.6–31.0 s) passes 3 sparse cyan frames.
- **No audio.** There is no audio in the file.
