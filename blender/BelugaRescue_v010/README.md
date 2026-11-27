# BelugaRescue_v010: the final fix round (batch 1, film 22)

**Status: ON HOLD for the director's and the client's watch.** The six fixes the client authorised for this round are in, and the render check below passes. Before anyone pays for a render, watch `review/preview.mp4` (270×480, every 5th frame, with the VO) from start to finish. The faults that are still known are listed below.

This is built from v009 (commit 2184d57), and v009 is untouched. One diver, one beluga, two spectators, one continuous camera. It is built to the client's VO (word timings in `BelugaRescue_v010_VO.words.json`), frames **1–1736** at 60 fps, with no retime. The render sheet is `SETTINGS.md` and the credits are in `CREDITS.md`.

Scripts are in `scripts/`:
- `00_tee_texture.py` and `00_caustics_texture.py`: the tee and caustics textures
- `01_build.py`: the build, `blender -b --python 01_build.py -- <beluga scene.gltf> <a.blend>`
- `02_animate.py`: the animation
- `03_package.py`: packing the delivered file

## The fixes in this round (film frames)
| Fix | What changed |
|---|---|
| **Lift** (f1112–1515) | The camera orbits the whale's mouth at mouth level, from front 3/4 (f1150) round to past the side (f1460). The whale now lies 14° flatter than her shin, 38–57° from vertical, and slides 80 cm up its own axis onto her foot (f1140–1192). Her foot visibly passes into the open lips, and the lips close round her ankle from f1192. A camera-riding fill light (f1100–1505 only) keeps the whale white. The mouth interior is a soft grey-pink, no longer red. |
| **Ending** (f1516–1736) | She is chest-up, with the water at mid-chest and her body centred in frame. On the gasp (f1538–1600) her head is thrown back with the jaw wide open (26°). She then breathes, looks to the whale and smiles. Her arms scull with her hands in the water. The whale spy-hops beside her, behind her left shoulder. **Root cause of v009's weak gasp:** the head-pitch sign was measured in world space at f1 while she is upside-down in the dive, so every "chin up" key tipped her chin down. The sign is now solved per bone in her own body frame. This also corrects the head direction everywhere else in the film. |
| **Floats** | Relaxed swim poses with bent elbows: the wrist is kept 0.30–0.35 m from the shoulder, where a straight arm would be 0.42 m. The arms change mode through the film: sculling, then panic clawing (f500–690), limp (f1390–1500), then treading at the surface. There is a flutter kick with the legs in opposition (knees bend, feet go back and up), at a period that changes per beat (30–70 frames). In the lift, her left leg kicks, and her body sways and bobs from f1196, so the pose never freezes. |
| **Surface** | The lens goes from 46 cm under the water (f1508) to 30 cm above it (f1514), so it crosses within 6 frames (between f1511 and f1512). No frame is within 12 cm of the water, the water's underside is darker, and its mirror reflection is fainter. Her head breaks the surface about f1520, after the camera is up. There is no milky frame. |
| **Calf grip** (f330–470) | Both hands use the relaxed hand pose. Every finger and thumb point is solved per keyed frame to sit 15.1–15.6 mm off the leggings, and clip_scan is now clean, where v009 had f331–469 bad. |
| **Render time** | The settings are: 24 adaptive samples, transparent bounces 8, static caustics texture, no beluga subdivision (which had cost about 60 s per frame), fast GI, light tree off, filter glossy 1.0, and no subsurface scattering. Measured at 1080×1920 on 4 CPU threads, every test frame is at or under 120 s (see below). |

## Known faults still in this version (preview frames)
These were not on this round's list, and most are carried over from v009.
- f716–1046: there is no human face on screen. The whale passes the window with two small, static spectators, and her arm only enters at the edge at f1046. qa_check flags EMPTY at f877–1039.
- f1001–1021: a close-up of the whale's head fills the frame.
- f1116–1146: the camera turns fast from the whale swimming away to the orbit start under its open mouth. It reads as a quick swing, not a cut.
- f251–311: she lands upright on the floor with her legs straight. This is the "sank to the bottom" beat, before the cramp.
- f1513–1519: open water for about 0.1 s between the camera crossing and her head breaking the surface.
- f1531–1566: splash droplets above the water use the same bubble look.

## Checks on this package
- **clip_scan:** no bad ranges.
- **qa_check:**
  - INSIDE flags appear whenever the camera looks up at the water from below. This is the back-facing water sheet, a known false positive.
  - EMPTY at f877–1039 (see above).
  - PROPMOVE for the whale's bubble ring.
  - BACKHEAD at f1, where she is a dot in the far distance.
- **limb_check:** the ARMBODY hits are points on her upper-arm axis within 7 cm of the shoulder joint (the shoulder mass, the documented false positive). The one exception is a single point 11 cm out on the left upper arm at f541 and f1401, with the arm raised. That point is inside the armpit volume, and I saw no arm through the body on the watched pages.
- **body_prop_cross:** her right foot and lower leg are inside the beluga's mouth at f1177–1519. This is the intended contact.

## Render check: PASS
On the exact file `BelugaRescue_v010_60fps.blend` (43 MB), opened with `blender --factory-startup -b`:
- **Packing:** no linked libraries, no unpacked images, and the VO sound is packed. No drivers or text blocks. The only warning is Blender's no-GPU CUDA notice.
- **Output:** camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1736. PNG to `//render/BelugaRescue_v010_####.png`, with the VO strip at frame 1.
- **Cycles settings:**
  - 24 adaptive samples, threshold 0.05, OpenImageDenoise
  - transparent bounces 8
  - fast GI on, light tree off
  - compositor on (CPU)
- **Caustics:** the tank-floor caustics node is an image texture with no animation.

**Measured frame times** at full resolution, 4 CPU threads, no GPU:

| Frame | Shot | Time |
|---|---|---|
| f20 | the dive | 112.2 s |
| f400 | the cramp | 99.0 s |
| f900 | the window vignette | 74.1 s |
| f1250 | the foot in the mouth | 114.8 s |
| f1400 | the lift | 107.0 s |
| f1700 | the surface | 52.0 s |

All six are at or under 120 s per frame. None is black or empty. For comparison, v009 at 64 samples took 644 s, 547 s and 297 s on its test frames.

## Review
- **Self-watch:** I watched all 7 contact pages of `review/preview.mp4`, and the pages are in `review/pages/`.
- **Independent review:** a fresh reviewer marked the previous build FAIL for these faults:
  - a red "raw-flesh" mouth
  - a near-black whale in the lift
  - a frozen lift pose and a kick too small to see
  - hands planted on the water in the ending

  Those faults are fixed in this build, which was then re-previewed and re-watched. The reviewer's points on legacy frames are listed under "Known faults" above.
