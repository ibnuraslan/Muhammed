# FanCancer: Checkpoint B (blocking)

- Sheet: `review/B_blocking_1s.jpg` (1 still per second, 270×480, 8 samples)
- Build: `blender -b work/humans.blend --python scripts/00_build.py -- work/anim.blend anim`. First run `01_build_humans.py` to make `work/humans.blend` and `python3 -I scripts/00_textures.py work`.
- `beats.json` holds the 13 beat start frames at the target times.

## Camera path (one camera, `scripts/04_camera.py`)
There is one Catmull-Rom spline per set, keyed every frame, with a new framing about every 0.5–1.0 s. The camera changes sets only while a surface fills the lens (no camera switch, no cut), and the jump frame is CONSTANT-interpolated so no motion blur smears across it.

| t (s) | Move |
|---|---|
| 0.0–2.2 | High over the ice, looking at the packed stands; descend to the bench and the glass; arc in front of the manager to her face through the glass |
| 2.2–3.9 | Crane over the glass; her POV over her shoulder at his neck; rack focus from the glass to the neck |
| 3.9–5.0 | Crane over the glass and dive to the mole on his neck (macro) |
| 5.0 | Skin fills the lens, and the camera passes into the skin cutaway |
| 5.0–8.2 | Glide over the giant mole, drop over the cut edge, and orbit the section as the melanoma cells grow down through the dermis |
| 8.6 | Back out through the skin to his neck |
| 8.6–13.0 | Pull back over his shoulder to her face through the glass; arc low, then to the other side; push in on the nod |
| 13.0–15.8 | Fly through the glass to her right shoulder; top-down on her thumbs and the blurred note; tilt across the screen |
| 15.8–17.8 | Wide on the slap; crane over the glass to his side |
| 17.8–22.2 | Over his shoulder on the phone; his puzzled face; the shrug; track him walking off; overtake him into the tunnel |
| 22.2–23.6 | Whoosh down the tunnel and through the opening door into the clinic |
| 23.6–30.8 | Orbit the exam bed; dermatoscope on the mole; the doctor's serious face; overhead on the hands; side view on the bandage; his relief |
| 30.8–31.8 | Push into his phone screen (share and heart icons) |
| 31.8–35.9 | Out of the glow into the night city; crane up as windows light up; fly alongside the bus of riders on phones; up to a lit window |
| 35.9–37.9 | Through the curtain into her living room; arc to her shock; push into the laptop |
| 37.9–44.0 | Out of the laptop screen onto the ice, low and skimming; orbit her, the cheque, him and both teams; crane up and settle wide over the confetti |

## Known blocking issues (to fix for C)
- Hand orientations on a few poses still read odd (the manager's hands in the clinic 29–30 s, some shrug poses). Finger curls on grips are not done yet.
- The doctor's hands near the neck need contact checking.
- City windows and facades still need more texture variation; the phone-glow cards are sparse.
- Crowd and skater motion is FK keyed every 30 frames and every 4 frames; skaters slide by design (on ice).
- The skin cutaway uses procedural layered tissue; no CC-BY skin cross-section model was found in Objaverse.
