# B28 CrocodileFriend — Phase 1 plan (no VO yet)

1080×1920, 60 fps, Cycles. Hard cuts: one camera per shot, bound to timeline markers (`CAM_Sxx`).
Each shot is its own clip on the timeline, built ~30% longer than the expected beat (21 shots, 3900 frames ≈ 65 s
vs ≈ 37–40 s reference), so Phase 2 only **trims** shot ranges to the VO frames. Nothing will be time-stretched.
Shot ranges are in `shots.json`.

Shot order and subjects follow the reference sheet (`briefs/batch2/B28_CrocodileFriend_reference_1fps.jpg`, 37 s).

## Cast and sets
- **Man:** MPFB "Keeper" from BelugaRescue_v008 (eye fix already applied, elbow IK limit opened to −40°…140°),
  bald (hair hidden), mid-blue shirt and trousers (no skin-tone clothing), relaxed hands from `hand_poses`.
- **Crocodile:** CC-BY "3d High-Poly Alligator" (SDPM Esare), straightened and rigged by `scripts/01_croc_rig.py`
  (spine, neck, head, 8 tail bones, 4 two-bone legs). Belly on the ground (z from a ray cast on the terrain) on land,
  floating with the back and eyes at the surface in water. The same model and colour in every shot.
- **Tourists:** BelugaRescue Spec A–G on the viewing deck. **Funeral guests:** CaveRescue Crowd 1–4 and Spec B/E, **standing** in staggered rows turned toward the singer (seated on benches failed body_prop_cross twice → benches removed, LESSONS §2.15).
- **Sets:** HOME (CC-BY log house with porch and steps, pond behind it, garden plants, palms, wooden viewing deck),
  RIVER (sandy bank sloping into the river, palms), HALL (plastered room, windows, easel portrait, flowers).
  Poly Haven CC0 grass, sand, deck wood, plaster and a partly cloudy sky HDRI.

## Logo (DA KRAS FILMS), 2 placements, never in the sad beats
1. **Wooden crate** in front of the porch steps, seen behind the man in S04 (white logo decal on the crate side).
2. **Sign board on the viewing-deck rail** in S16 (show for tourists), dark logo on a light wood board.
None in S09–S10 (sleeping), S18 (death) or S19–S21 (funeral).

## Beats and shots
| Beat (reference words) | Shot | Frames (P1) | Who / action | Camera | Risky contact → safe staging |
|---|---|---|---|---|---|
| B1 "He pulled a dying crocodile from the riverbank" | S01_RiverPull | 1–190 | Man walks backwards up the sand, facing the croc, holding its raised tail in both hands; the limp croc slides belly-down out of the water | over the water in front of the croc's head, low 3/4, slow drift | Hands on the tail: palms placed on the tail top (`place_hand`), cupped fingers, no wrap through the tail. Croc belly ray-cast onto the sand |
| | S02_CrocCloseLow | 191–340 | Close low on the croc's head sliding toward camera (weak, slow breathing), man pulling behind | ground level at the croc's snout | same |
| B2 "and took it home" | S03_DragHome | 341–510 | Man pulls it by the tail across the yard toward his log house | low front, house behind | same; drag on flat grass, not up the porch steps (avoids steps intersecting the belly) |
| B3 "to treat its wounds" | S04_Treat | 511–700 | On the grass in front of the porch: man kneels beside the lying croc, right palm stroking its back, left hand on his hip | 3/4 front, house + logo crate behind | Palm on the back via `place_hand` (skin offset 12 mm). No bandage or wound shown |
| B4 "For six months he kept it in a secret pond behind his house" | S05_PondWide | 701–900 | Croc swims across the pond (tail undulation, legs tucked); man walks along the bank (arm swing) | high wide from behind the house | none |
| | S06_CrocSwim | 901–1050 | Croc swims toward camera at the water line, man on the bank behind | water level | none |
| B5 "where he would feed it 9 pounds of meat a day" | S07_Feed | 1051–1250 | At the pond edge, bucket in his left hand (Child Of the wrist, handle in the curled fingers), right hand takes meat and tosses it; the meat arcs into the water | 3/4 behind-side, pond and croc ahead | Plain bucket, **no text**. Bucket handle in the fingers; meat follows the right hand until release, then a ballistic arc (no floating) |
| | S08_Snap | 1251–1400 | Croc rises from the water and snaps at the meat; man watches, bucket in hand | low from the water | none |
| B6 "He even slept beside it, thinking his love would heal its wounds" | S09_SleepWide | 1401–1600 | Night (blue moonlight, faces still lit): man lies on the grass beside the resting croc, breathing | slow push-in, high 3/4 | Lying pose: root rotated, legs along the body. Hand rests on the croc's back in S10 |
| | S10_SleepClose | 1601–1770 | Closer: his face (eyes readable), palm on the croc's back | side, low | Palm via `place_hand` |
| B7 "And when he tried to release it back to the wild, the crocodile refused to leave" | S11_Release | 1771–1970 | Man points toward the river; the croc belly-crawls away | 3/4 behind him | Point pose from `hand_poses` |
| | S12_RefuseTurn | 1971–2140 | Croc stops and turns back toward him | low at the croc | none |
| | S13_ComesBack | 2141–2360 | Croc crawls back; man kneels, palm on its head | 3/4 front | Palm on the head top via `place_hand` |
| B8 "staying with him for over 20 years" | S14_WalkSide | 2361–2560 | Man and croc walk side by side along the pond bank | side tracking | none |
| | S15_WalkFront | 2561–2730 | Same walk, front low | front low, ahead of them | none |
| B9 "This time they performed for tourists" | S16_ShowWide | 2731–2950 | Man waist-deep in the pond, turned 3/4 to camera, palm on the croc's head, waving; tourists on the deck behind (clapping, leaning on the rail), **logo sign** on the rail | from the water, tourists behind | Tourists not in a line (staggered, turned); hands on the rail top, not through it |
| | S17_Tourists | 2951–3120 | Tourists' faces, clapping; man and croc in the water below frame | low from the water | same |
| B10 "And when it finally died" | S18_Died | 3121–3340 | Evening light. The croc lies still on the bank; the man kneels beside it, head bowed, palm on its back. No distress close-up | 3/4, gentle push-in | same as S04 |
| B11 "the man held a public funeral, where he sang a song for his crocodile friend" | S19_Portrait | 3341–3510 | Portrait on the easel (plain painting of him and the croc, rendered from the film; no text), flowers | push-in | none |
| | S20_Sing | 3511–3730 | Man stands beside the portrait and sings (soft jaw motion, no teeth), hand on his chest, other hand open; guests' backs in the foreground | medium, over the guests | Hand on chest at 10 cm off the shirt (no press) |
| | S21_HallWide | 3731–3900 | Wide: standing guests' faces, singer, portrait | high wide from the front corner | Guests' hands hang or loosely clasp (wrists apart) |

## Phase 2 (when the VO arrives)
`transcribe.py` → beat frames `1 + round(s × 60)` → trim each shot's range to its beat (move shot clips, never stretch),
`frame_end` ≈ 0.5 s after the last word. Then the four checks, the full `preview.py` and watching every page.
