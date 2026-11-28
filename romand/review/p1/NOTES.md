# Romand Part 1: storyboard v1 (for hub review)

- `contact_sheet.jpg` (all 33 shots with captions), `contact_sheet_small.jpg`, `storyboard.pdf` (6 per page),
  `frames/P1-xx.jpg` (1920x1080: 960x540 plate upscaled + kit_v1 overlay at its settled moment).
- Preview settings: 960x540, 10 spp, adaptive, OIDN, 4 bounces. Key frame = one still per shot; the camera move and the
  action are in each caption (from `romand/SHOTLIST.md`). **No final animation has been rendered.**
- Reusable sets: `../sets/sets_sheet.jpg` (14 sets, one establishing frame each).

## Measured mean luma (0–255, plate without overlay)

| Kind | Frames | Luma |
|---|---|---|
| Cinematic / macro | 26 | 11.7–15.8, mean 14.3 (exposure found per shot by a probe; the final pass will trim every shot to 12–14) |
| Explainer slab (EXP) | P1-14, P1-15, P1-30 | 26–33 by design: dark blue-grey ground, never pitch black (ENGAGEMENT_RULES 3) |
| 2D cards | P1-24 title, P1-25 disclaimer, P1-27 link board, P1-32 timeline | kit cards over a dimmed plate or black |

## What is new in the kit (romand/3d, romand/graphics)

- The car is a real period model: Sketchfab CC-BY "1994 Peugeot 405 GLX (facelift version)" (Mehrdad995GTa), with the
  windows cut to see-through glass, the boot lid on a hinge (0–1 open), and a simple interior with seats, dash and wheel
  so the figures sit inside it.
- Mannequins: the approved look-test rig, now with sit, sit-at-table, car-seat, drive, walk, carry, bow and reach-into-boot
  poses, woman (skirt shell), child and elderly variants, all faceless egg heads in clay clothes.
- `rmap.py`: the kit `map` card generalised to France / Switzerland (Natural Earth 10m), for Part 2 onward.

## Deviations from the shot list, and known gaps

1. P1-04: the tail lights are amber, not red, so the red accent stays unique to the cord. Shot list updated.
2. P1-08/09: the macro is taken from above with no hand in frame. The final adds his hand closing on the cord.
3. P1-10/12: the 405's doors are part of its body mesh and don't open yet. I'll cut door panels before the
   animation pass (same method as the boot lid).
4. P1-21: the children's boots are simple blocks. I'll replace them with a scanned boot asset (Sketchfab CC-BY, already
   in the Antwerp catalogue) for the final.
5. P1-23: both houses float side by side and read as "two houses, lights off", but the snow slabs fall into black.
6. Person cards use crops of our own mannequin renders (Chantal from P1-13, Romand and Florence from P1-26). The
   children's card shows their boots by the door, not a figure.
7. Title card: "THE ADVERSARY?" is a placeholder until the hub names the film.

## Animation plan once approved

Each shot is built by a function in `sb_p1.py`. The animation pass keyframes the camera move from the caption, adds the
walk and drive cycles (planted feet, root motion solved from the stance foot, as in the live test), and runs the
per-frame clip check on every frame. Then it renders natively at 1920x1080, 16 spp, OIDN, upscales to 2560x1440, and
packs the MASTER.blend per FARM_DELIVERY_RULES.
