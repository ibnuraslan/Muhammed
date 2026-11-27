# NoPilotPlane_v012: the from-scratch rebuild (film 12)

**Status:** pushed on the director's instruction after the last approved fix round (round 4). The render check below passes. My own watch of the final preview passes, apart from the minor notes listed under "Known minor notes". Watch `review/preview.mp4` (commit ebb1f17) before it goes to the client.

This is one passenger, the two collapsed pilots, a cabin of sleeping passengers, and one continuous camera with no cuts.
- Built to the client's VO (the v009/v011 timing), frames **1–3481** at 60 fps (58 s).
- The render sheet is `SETTINGS.md`.
- Attribution is in `CREDITS.md`. **The two seat models are CC BY 4.0, so the credit line must go in the video description.**
- The scripts are in `scripts/`: 00 textures, 01 build, 02 animate (with the camera clearance pass), 03 package.

## The film
- **0–9 s:** he wakes in his seat among sleeping passengers. The plane flies level (window, wing, horizon). He stands and walks up the aisle; the DA KRAS FILMS logo on his chest reads.
- **9–15 s:** the captain is collapsed on the floor in the cockpit doorway. The first officer is slumped in the right seat, and he shakes him by the shoulder.
- **15–21 s:** he sits in the left seat, takes the radio mic from the hook and screams into it, mic in his fist at his mouth. No one answers.
- **21–26 s:** he gets up, grips the first officer and tries to haul him out. He loses his grip and drops back into the seat.
- **26–30 s:** alarms and red light. The nose drops, the tilted ground shows through the windscreen, and he grabs the yoke at the dive peak.
- **30–41 s:** he flies the plane level. A ~1 s macro shows the altimeter unwinding.
- **41–56 s:**
  - over-the-shoulder views of the long field ahead
  - his right hand to the throttles, pulling them back
  - he looks back at the first officer
  - the field fills the windscreen
- **56–58 s:** it ends on his face.

## Camera clearance (the v012 fix)
`02_animate.py` keeps the lens at least 12 cm from every set mesh: cabin, cockpit, and the keyed yokes, throttles, mic and needles. It also keeps the lens 14 cm from limb capsules and 34 cm from the head bone axis of every character. Pushes are smoothed over ±0.3 s, then re-checked frame by frame.
- On the final animate the pass reported 0 hero-face-blocked frames and the residual push left 1 frame still too close.
- The full camcheck script was last run on the round 1 package (SET 0, BODY 0, FACE 0). It was not re-run on this final file.

## Render check: PASS
On the exact file `NoPilotPlane_v012_60fps.blend` (84 MB), opened with `blender --factory-startup -b`:
- No linked libraries, no unpacked images, and the VO sound is packed (strip `VO` at frame 1).
- No drivers, no Python texts, one camera (`CAM_Film`), and no camera markers.
- Output: 1080×1920 at 100 %, 60 fps, frames 1–3481, PNG to `//render/NoPilotPlane_v012_####.png`.
- Cycles: 14 adaptive samples (threshold 0.1) with OIDN denoise, and AgX Punchy.
- Full-resolution test frames on a 4-core CPU with no GPU: **f20 in 114 s, f1780 in 69 s, f3065 in 73 s**. All are at or under 120 s per frame, and none is black, empty or pink.

## Known minor notes (from the final watch)
- f3056–3076: during the look-back, the first officer's seat back and shoulder pass soft in the near foreground, for about 0.3 s.
- f1251–1281: lowering the mic, his left hand rests near his cheek for about 0.5 s.
- f2213–2221 and f2274–2282: the moves into and out of the altimeter insert are fast (≤ 9°/frame) but continuous.

Reviews of each check are in `review/CHECK1.md` to `review/CHECK4.md`.
