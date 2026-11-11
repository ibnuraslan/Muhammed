# Checkpoint C: polish
- Sheets (one still every 0.2 s, 270×480, 8 samples): `review/C_polish_0.2s_part1.jpg` (0–8.2 s), `part2` (8.4–16.6 s), `part3` (16.8–24.8 s).
- Audit output: `review/C_audit.txt`, from `scripts/audit.py`, sampled every 10 frames.

## Audit summary (numeric)
| Check | Result |
|---|---|
| Head into headset (band pad and cushions, while worn) | **0.0 mm** max. No body × headset triangle overlaps before the grab. |
| Hair × headset | 102 triangle overlaps in **one** sample (f1231), as the band passes over the hair while he lifts it off. Zero while worn. |
| Hands into desk, keyboard or mouse (depth) | **2.8 mm** max (fingertips pressing keys). |
| Hands into headset (depth) | **4.6 mm** max (fingers pressing the soft ear cushion while cradling it). Counted as grasp contact. |
| Feet | Sinking fixed. Five samples show a "hover" of 1.5–2.5 cm. Three are the intended heel-lift fidget (f221–241); two are f1261–1281 as the chair rolls back (open item). |
| Camera inside geometry | 0 frames (ray-parity test against the walls, desk, bed, PC and body). |
| Bullet on screen during the chase stretches (f1–700, f949–1078) | Out of frame in 7 of 280 samples, at the frame edge only. |

## Changes since B
- **Bullet chase:** the camera follows the bullet by offset, the focus is on the bullet, and the chase keys are tighter. The bullet now reads in every chase framing, including the whole ricochet flight (side view → behind → wall).
- **Contact:** hands raised onto the key tops and the mouse, and feet raised 1.6 cm (no sink). The headset is cradled under the cups after the rip, instead of an outer-face grip that crossed his arms through the cups.
- **Headset:** bevelled and smooth-shaded cups, a steel trim ring, and an RGB ring on each cup; the hit cup's ring flickers and dies on impact. The crack is now jagged, noise-distorted and local to the rim. The cutaway foam is warm yellow, so the shell, foam and steel layers read apart.
- **Set:** books on the shelf. The posters had rendered black because their frame sat in front of them; fixed. The grass tufts were removed (they rendered as dark balls). The eyes' refractive outer layer rendered black without caustics; it is now a thin coat.
- **Effects:** the dust puff is smaller and more transparent, and the bullet hole is larger. The air trail is off after the impact.
- **Camera:** new keys at 100, 1008 and 1418, the face → over-shoulder swing goes round his right (it no longer passes through the bookshelf), and the last framing pushes to 55 mm on the hole.

## Open items
- The impact-to-cutaway stretch (12.4–13.6 s) holds similar macro framings of the cup for about 1.2 s.
- The stunned face uses the jaw, head and breathing only; no brow or eyelid controls.
- The chair roll-back leaves the right heel about 2 cm up for about 0.3 s.
