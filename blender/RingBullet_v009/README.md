# RingBullet_v009: from-scratch rebuild (batch 1, film 21)

**Status: client-approved, relayed by the director, after the ring fix. Render check: PASS (below).**
Watch `review/preview.mp4` (every 5th frame, 270×480, with the VO) of this exact package.

## Ring fix (the client's one remaining fault)
- The band is fitted to the finger's real cross-section, not the bone axis, which runs about 8 mm off-centre in the finger mesh. The inner radius is the widest skin radius (11.3 mm) plus 1.5 mm. The band encircles the proximal phalanx and is Child Of `finger4-1.L` for the whole film.
- Checked on **every frame (1–1395)**: no ring-finger skin is inside the band on any frame, with a minimum clearance metric of 3.0 (1.0 = touching). The band's edges touch the pressed-together middle and little fingers (at most 3 vertices), as a real ring would.
- Close renders at f300, 518, 560, 700, 1030 and 1100, from 4 angles each: `review/ring_closeups/ring_fit_6frames_4angles.jpg`.
- Knock-on effects: the bigger band moves the impact point 1–2 mm outward, and the split point now sits beside the little-finger edge, so the pieces' paths shifted slightly (f601–700). The dent is 0.8 mm deep, so it never touches the skin. Nothing else changed apart from the samples (20).

## Render check: PASS
On the exact file `RingBullet_v009_60fps.blend` (54 MB), opened with `blender --factory-startup -b`:
- No linked libraries, no unpacked images, the VO sound packed, and no drivers or Python.
- No errors or warnings, apart from one Blender deprecation notice from the check script itself.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1395, PNG to `//render/RingBullet_v009_####.png`, and the VO strip at frame 1.
- Test frames at full resolution, 20 adaptive samples, on a 4-core CPU with no GPU: **f20 in 98 s, f600 in 109 s and f1300 in 101 s**. None is black, empty or pink (`review/render_check_f20_f600_f1300.jpg`).

## Checks on this package
- clip_scan: 0 bad ranges.
- limb_check: ARMBODY only at the 2 shoulder points (known false positive). PROPHEAD is the intended neck graze mark and the fragment entering the neck.
- qa_check: BACKHEAD f1 is intended (the robber is never shown from the front). PROPMOVE is the bullet, sparks and fragments in flight.
- body_prop_cross: no ring-finger crossing. The intended contacts are fragment A lodged in the finger, the neck graze, and the robber's fist on the grip (f1–61). The band edges touch the neighbouring fingers as noted above.

## The film
- A corner shop at night: teal walls, a red and cream chequered floor, wooden shelves of colourful goods, and the DA KRAS FILMS sign.
- The robber is shown from behind only: dark jacket, real MPFB clothes, the pistol in his right fist.
- The owner wears a real MPFB striped shirt and jeans. He stands with his hands up and throws them in front of his face.
- In slow motion the bullet crosses the frame to his left hand and strikes the gold ring (sparks, dented ring). It flattens, then splits: one piece lodges in the finger, and the other passes the hand's edge and grazes his neck.
- He looks at the dented ring. Police lights flash through the door, and he walks toward the door.
- One continuous camera. IK rotation limits are on the knees, elbows and hips. The feet are planted on the floor with the measured shoe-sole offset.

Earlier review history (rounds 1–3) is in git history.
