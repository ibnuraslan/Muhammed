# RingBullet_v009: from-scratch rebuild (batch 1, film 21)

**Status: ON HOLD (render check FAIL). The .blend is NOT pushed.** After 2 fix rounds the moving preview still fails a fresh harsh review, and my own watch agrees on the main points. Watch `review/preview.mp4` (every 5th frame, 270×480, with the VO).

Built to the client's VO (the v008 sync), frames 1–1395 at 60 fps. Beats: 1 / 245 / 392 / 518 / 624 / 786 / 894 / 997 / 1175 (`beats.json`).
The scripts in `scripts/` rebuild the package exactly: `01_build.py` (Poly Haven dir), `02_animate.py` (VO), `03_package.py`.

## The film
- A corner shop at night: teal walls, a red and cream chequered floor, wooden shelves of colourful goods, and the DA KRAS FILMS sign.
- The robber is shown from behind only: dark jacket, real MPFB clothes, the pistol in his right fist.
- The owner wears a real MPFB striped shirt and jeans. He stands with his hands up and throws them in front of his face.
- In slow motion the bullet crosses the frame to his left hand and strikes the gold ring (sparks, dented ring). It flattens, then splits: one piece lodges in the finger, and the other passes the hand's edge and grazes his neck.
- He looks at the dented ring. Police lights flash through the door, and he walks toward the door.
- One continuous camera. IK rotation limits are on the knees, elbows and hips. The feet are planted on the floor with the measured shoe-sole offset.

## Checks on this package
- clip_scan: **0 bad ranges**.
- limb_check: ARMBODY only at the 2 shoulder points (known false positive). PROPHEAD is the intended neck graze mark and the fragment entering the neck.
- qa_check: BACKHEAD at f1 is intended (the robber is never shown from the front). PROPMOVE is the bullet, sparks and fragments in flight.
- body_prop_cross: the ring on its finger is intended, and so is the robber's fist on the grip (f1–61). **The flattened slug grazes the ring finger's skin (2–5 edges) at f521–620.**

## Faults still open (fresh reviewer FAIL; my own watch agrees on 1–6)
1. f392–546: the bullet approaching the ring reads as sitting on the palm, in a near-full-frame hand macro (about 1.5 s with no face).
2. f600–690: the split into two pieces does not read. The fragments are tiny and the hand fills the frame.
3. Logo: the glossy sign board catches a lamp highlight that washes out "KRAS FILMS" at the end. It is fully readable only around f1146–1200. Fix: a matte board and the lamp moved.
4. f1180–1365: the walk arms hang slightly out (near A-pose) and the stride is small.
5. The faces are readable but flat. The reviewer calls them doll-like, with few expressions in the slow-motion middle.
6. Near-static stretches in the slow motion (f130–240, f760–890): the camera drifts, but little else moves.
7. Render speed: about 210 s per full-resolution frame on a 4-core CPU, well over the 60 s target.

## Technical render check (on the local, unpushed package; factory startup)
- 0 libraries, 0 unpacked images, the VO sound packed, no drivers.
- `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1395, PNG to `//render/RingBullet_v009_####.png`, VO strip at frame 1.
- f20 took 210 s, f600 221 s and f1300 208 s (64 adaptive samples). None is black, empty or pink.
- Overall verdict: **FAIL** on content (above), so no .blend is pushed.
