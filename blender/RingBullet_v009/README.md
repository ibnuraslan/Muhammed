# RingBullet_v009: from-scratch rebuild (batch 1, film 21)

**Status: ON HOLD. The .blend is NOT pushed.** This is after the director-approved final round (round 3). The technical render check is clean, but frames take 136–160 s, over the 120 s target. A fresh harsh reviewer still grades the preview FAIL. Watch `review/preview.mp4` (every 5th frame, 270×480, with the VO).

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
- body_prop_cross: the ring touches only its own finger (intended), and the robber's fist on the grip (f1–61) is intended. The flattened slug grazes the ring finger's skin (2–5 edges) at about f521–600.

## Round 3 (director-approved): what changed
- f392–700 is a wider 3/4 shot with his face, the hand and the bigger gold ring, and the bullet visibly crosses the frame. One split macro (f601–666) shows the ring and two glowing pieces separating.
- The sign is matte and raised and the lamp moved. The logo is fully readable and unobstructed at f1146–1395 (over 4 s).
- The walk has an 8.5 cm arm swing and a longer stride over 1.75 m.
- Brow, mouth and eye acting, blinks and a slight head tremble were added through the slow motion.
- Render settings: 28 adaptive samples (threshold 0.08), 4/2/2/4 bounces, simplify subdivision 1.

## Technical render check (exact local package, factory startup)
- 0 libraries, 0 unpacked images, the VO sound packed, no drivers.
- `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1395, PNG to `//render/RingBullet_v009_####.png`, VO strip at frame 1.
- f20 took 136 s, f600 160 s and f1300 138 s on a 4-core CPU. None is black, empty or pink.
- **Speed target (120 s or less) is missed.** Fix: drop samples to about 20, or turn off skin subsurface.

## Faults still open (fresh reviewer FAIL on round 3; I agree on 1–4)
1. f601–666: the split macro is about 1.1 s, not 0.5 s. A rubbery near-camera thumb dominates it, and the fragments are small glowing dots.
2. f300–480: the slow-motion bullet moves only a little per second and the owner barely moves, so the stretch reads near-static.
3. The finger-lodge (f786) and the neck graze (f894) are small and easy to miss.
4. Faces read flat or doll-like (MPFB face rig). The hand he examines at f997–1110 reads as a curled blob at preview size.
5. The opening (f1–45) shows the logo cropped. That is only a supplement; the main logo window passes.
The reviewer also claimed no arm swing and that he never covers his face. I disagree with both: the swing and the hands in front of his face are visible on pages p05–p06 and p02.
