# GameBoxBullet_v011: farm package (rebuild after the Nov 21 frame-by-frame rejection)

Built to the director's VO (`GameBoxBullet_v011_VO.mp3`, the same file as v010). **Frames 1–1311**, 1080×1920, 60 fps. v009 and v010 are untouched.
The film is now **20 hard-cut shots**, each cut on a VO word (`beats.json`, frame = 1 + round(sec × 60)). It still uses one camera, with the cuts baked into constant-interpolation keys and no markers.

- `GameBoxBullet_v011_60fps.blend`: self-contained and packed (72 MB, plain git, opens clean with `--factory-startup`, no unpacked images).
- `review/preview.mp4`: every 5th frame from the **packed file**, 270×480, with the VO. `review/preview_page_p01–p06.jpg` are its contact pages; I watched every page.
- `review/*_v011.json`: clip_scan, qa_check, limb_check and body_prop_cross run on the packed file.
- `beats.json` (VO beats), `shots.json` (shot table), `scripts/` (how it is built), `SETTINGS.md`, `CREDITS.md`.

Build: `scripts/01c_build_shooter.py`, then `scripts/10_shots.py` (on `GameBoxBullet_v001/work/scene.blend`), then `pipeline/anim_look.py`, then `scripts/11_look_fix.py`, then `GameBoxBullet_v001/scripts/05_prepack.py`, then `pipeline/package_for_farm.py`.

## Shots (frames)
| # | Frames | VO | Shot |
|---|---|---|---|
| 1 | 1–54 | "A stray bullet" | Side medium of the shooter across the street: the gun, the muzzle flash at f10, the recoil. The bullet leaves screen right; +Y is screen right in every side shot. |
| 2 | 55–96 | "ripped through" | Tracked bullet close-up over the lawn. The bullet holds a constant size and the house grows ahead. |
| 3 | 97–140 | "the wall of his house" | Static exterior on the siding: the bullet punches through at f99 and splinters and dust kick out. |
| 4 | 141–168 | | Static interior: the drywall bursts at f141 and debris falls into the room. |
| 5 | 169–222 | "flying straight for his chest" | Bullet POV from behind and beside it. He stands ahead holding the box, which shows the approach path. |
| 6 | 223–276 | | Medium (chest and face): he turns the box in his hands and smiles. The logo poster is behind him. |
| 7 | 277–353 | "But he was holding…" | Close on the box in his hands: palms on the sides, forearms connected. He lifts and tilts it. |
| 8 | 354–432 | "…brand new video game collector's box" | Face medium: happy, then he hears the noise and looks up (eye and head motion). |
| 9 | 433–496 | | Tracked bullet from the side, with the box ahead (screen right). |
| 10 | 497–551 | "The bullet slammed into it" | Static side profile: the bullet flies in from screen left and hits the box front at f519. His hand is on the side and his face is in frame. |
| 11 | 552–602 | | Reaction: eyes wide, brows up, head jerk. The box top and the hole are in frame. |
| 12 | 603–674 | "The case cracked" | Front of the box with both hands gripping it and his whole face. Cracks grow from the impact only (one decal, r ≤ 6 cm, no tiling). |
| 13 | 675–754 | "the discs shattered" | Cross-section of the same box, cut in half on a sky-blue card, with solid layers. Disc lines break and shards fly. |
| 14 | 755–830 | "and layer by layer" | Cross-section: the bullet ploughs through the manual pages, with energy rings at each layer. |
| 15 | 831–890 | "they ate up the bullet's energy" | Face: he stares down at the box, breathing hard, with small shakes of the head. |
| 16 | 891–940 | | Cross-section: the bullet slows in the card insert. |
| 17 | 941–1092 | "It stopped halfway through… buried inside the box" | Cross-section of the whole box. The bullet stops at exactly half depth (f962), then a slow push-in shows it stuck in the console box. |
| 18 | 1093–1136 | | He tilts the box up and peers into the hole. |
| 19 | 1137–1212 | "His game collection" | He looks up at the hole in the wall, then back. Face and box are in frame. |
| 20 | 1213–1311 | "just saved his life" | Payoff: he's alive with a relieved exhale and smile, holding up the box with the bullet hole. The logo poster is behind him. |

## The 20 rejection items: what changed
1. Shot 1 shows the shooter, the gun (a plain silhouette with no mechanism detail) and the muzzle flash for 0.9 s before the flight.
2. The flight is a tracked close-up (shots 2, 5 and 9). The bullet fills ~25 % of the frame width at a constant size, and the camera is locked to it.
3. One straight path from the muzzle through the wall hole to the impact point. Every side shot moves screen right.
4. No fly-through. A static exterior (splinters and dust out) and a static interior (drywall burst in) show the wall break. Debris within 0.6 m of the lens is hidden per shot.
5. One bullet mesh, never scaled. The section shot uses the same mesh data.
6. The ceiling fan is removed. All his shots are medium or close, on chest and face.
7. He turns, lifts and tilts the box, with weight shifts, nods and head turns. The box sits at chest height (top just under his collar).
8. Shot 5 shows the approach, and in shot 10 the bullet crosses the frame for ~0.4 s before it hits.
9. Both palms are on the box sides in every man shot (shots 7, 10, 12, 18, 19, 20).
10. Expression changes: smile → listening → shock (wide eyes, brows, slight parted mouth, jaw ≤ 6°) → concern → curiosity → relief and smile. There are 16 blinks, eye saccades and head motion. The mouth is never a gaping "O".
11. One box model, 30 × 26 × 17 cm, never swapped. A contact pass on every keyed frame keeps the palm skin 1.5–2 mm off the box sides. Measured on the rendered skin: 0 vertices inside the box.
12. Face framing was checked on the first and last frame of every shot.
13. The bullet scale is constant (see 5). After the hit it stays inside the box; only its base shows in the hole.
14. The box is a solid console box. The cross-section is a separate model of the same box: solid cut layers (cover, two disc trays with discs, divider, manual, sleeve and disc, card insert, art book, back) plus the shell walls, seen at an angle so the front face reads.
15. Every visible hand has its arm. The section shots have no hands at all.
16. See 12.
17. No long static holds. The crack decal is fixed at the impact and grows to 6 cm, with no tiled crazing. His actions are staring down, shaking his head, tilting the box to peer in, looking up at the wall, exhaling and smiling.
18. Framing is chest-up, with the box in his hands at the bottom of the frame. The face changes expression in every man shot.
19. Hand contact as in 11. Face framing as in 12.
20. Shot 17 shows the bullet stuck halfway in the box. Shots 19–20 show him alive with the holed box.

Brand: the DA KRAS FILMS logo is on a framed poster on the back wall, in shots 6, 15 and 20 (≥ 30 % of frame width, ~25° to camera, f/8, never on the box or face). There is no other text.
Eyes: a camera-only catchlight (a small light, glossy only) rides with the camera. Face key 10 W.

## Checks (packed file)
- clip_scan: **0 bad ranges**.
- limb_check (step 2): only `Gamer arm.L/R inside own torso (2 pts)` remains. These are the shoulder-joint points of the upper arm while the arms reach forward to the box. Nothing passes through the body on screen.
- body_prop_cross (step 3, Box_body, Box_cover, Gun parts): hits remain on the middle fingertips touching the box side (4 skin edges per frame), and the shooter's thumb on the pistol slide in shot 1 (1–54, seen from 2 m). There are no palm or arm crossings.
- qa_check: EMPTY on the bullet, wall and cross-section shots (intended: no character in them), PROPMOVE for the flying bullet and debris, and CAMJUMP at the hard cuts (15 of the 19 fall on a sampled frame). FILL: 0.

## Known issues
- Frames 1–54: the shooter's thumb tip overlaps the top of the pistol slide by a few mm (only ~40 px at review size).
- Shots 7, 10 and 12: the middle fingertip rests on the box side with the skin touching (0–2 mm).
- The shooter's face is generic MPFB in profile and small in the frame.
- 941–1092: the cross-section holds 2.5 s. The bullet stops at f962, shards settle and the camera pushes in slowly, so nothing else moves on screen in the last ~1.5 s.
- Shot 9 is the bullet against a plain wall until the box enters frame right.
