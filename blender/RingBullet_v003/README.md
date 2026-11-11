# RingBullet v003: farm package (optional polish pass after D)

| | |
|---|---|
| File | `RingBullet_v003_60fps.blend` (48 MB, packed, compressed; a normal git file, no LFS) |
| Format | 1080×1920, 60 fps, frames 1–1410 (23.5 s), Cycles CPU, 48 samples + OIDN, motion blur 0.5 |
| Camera | one camera (`Cam`) on one continuous move, no cuts, no markers |
| Output | `//render/RingBullet_v003_####.png` |
| Beats | `beats.json` (9 beats, start frames at the brief's target times) |
| Sources | `../RingBullet_v001/scripts/` (rebuild steps in `../RingBullet_v001/README.md`) |

## What changed from v002
- **Subtle camera shake** throughout: a handheld micro-jitter of about 0.1° (sum of sines, smooth, deterministic), with decaying bursts on the muzzle flash, the impact, the split, the fragment's wall hit and the police-light flare.
- **Second fragment's landing:**
  - After grazing the neck, fragment B hits the side panel of the bookshelf behind him (upper left of frame, about 16.85 s).
  - A volumetric dust puff blows out of the hit, with 14 wood chips falling ballistically and a brief warm light flick at the hit point.
- **Smaller tweaks:** the skin sheen is toned down, the bullet-orbit range is narrowed, and the walk-out ends on a push-in to the doorway.
- The audit still reports 0 flags (`../RingBullet_v001/review/audit_v003.txt`).

## Story beats as built
| # | Frame | Line | On screen |
|---|---|---|---|
| 1 | 1 | The robber fired the gun… | Over the robber's shoulder (he's only seen from behind), then the muzzle flash and smoke. The camera rides the bullet in slow motion, orbiting it. |
| 2 | 163 | …threw his hands up… | The camera peels off to the reverse as his hands snap up, the backs of his hands out and the gold ring facing the bullet, in a look of terror. |
| 3 | 409 | …instead of going through his skull | Macro from behind the bullet, with a rack focus from the bullet to the ring. |
| 4 | 541 | …hit his wedding ring | A rim glint, then impact with sparks, a flash, the hand jolting, the lamp flickering and a camera shake. |
| 5 | 661 | …split into two pieces | The bullet squashes, the ring dents and two fragments fly apart, with an orbit macro. |
| 6 | 865 | One piece lodged in his finger | Fragment A lodges in the middle finger, leaving a small dark nick with no blood. He winces with eyes squeezed and mouth open. |
| 7 | 979 | …the other went into his neck | A whip-pan with fragment B. It grazes his neck, leaving a small mark, and his hand flies to his neck. The fragment then hits the bookshelf behind him in a puff of dust and splinters. |
| 8 | 1075 | …minor injuries and a dented ring | He looks at the dented ring in disbelief (slow blink, brows up) as the camera orbits close and police light washes in. |
| 9 | 1249 | …walked away okay | Bandage and plaster on. He walks out (IK walk, planted feet) toward a red/blue strobe and an officer beckoning at the door, as the camera pushes into the doorway. |

## Voiceover
No VO mp3 has been supplied yet, so this package contains no VO strip. To retime when it arrives:
1. Get the word timestamps with `pipeline/transcribe.py`.
2. Build an anchors file from `beats.json` (old frame → the second the beat's first word is spoken).
3. Run `blender -b RingBullet_v003_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 RingBullet_v003_60fps.blend`.

The world-time slow-motion curve (`TimeCtl["wt"]`) is keyframed, so it warps with everything else.

## Known issues
- In some macro frames (about 8–9 s and 13 s), skin fills most of the frame. It shows pore and normal detail, and the director has accepted these as macro.
- Around 3.0 s there's about one soft, dark frame as the camera peels off the bullet to the reverse.
- The bandaged hand mostly turns away from camera during the walk. The bandage reads at 20.8–21.2 s.
- Facial acting uses MPFB face bones (jaw, brows, lids, mouth corners) and no shape keys. It's readable, but not film-grade.
- The officer is a plain MPFB figure in a navy work uniform with no markings, and is only seen as a backlit figure through the door.
- The audit (`../RingBullet_v001/review/audit_C.txt`) reports 0 flags. It checks:
  - feet hover and sink
  - ring and body penetration depth
  - body against props
  - bandage and plaster gap
  - camera inside geometry
  - gun aimed at camera while in frame
  - robber face in view
