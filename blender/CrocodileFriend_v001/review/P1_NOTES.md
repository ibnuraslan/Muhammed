# B28 CrocodileFriend — P1 notes

Built from the reference sheet only (no VO yet). 21 shots, 3900 frames on the P1 timeline (each clip ~30% longer than
the reference beat; Phase 2 trims, never stretches). Sheet: `P1_sheet_3frames.jpg` (first / middle / last frame of every
shot, 540×960, Cycles 8 samples, rendered from the final `work/look.blend`, S07/S13 re-rendered after the last fix).

## body_prop_cross (step 3, final file)
Props: Croc_body, Bucket, Meat, Rail posts/top/mid, Crate, Easel, LogoSign_Board, PortraitFrame.
| Cast | Range | Visible crossing frames |
|---|---|---|
| Man (Keeper) | 1–1400 (`body_prop_cross_man_a.json`) → S07 re-run (`bpc_S07.json`) | **16** — S07 1117–1162: the meat sits inside his curled right fingers during the 0.75 s hold before the toss (also brushes spine03 on the wind-up in the older run) |
| Man (Keeper) | 1401–3900 (`body_prop_cross_man_b.json`) → S13 re-run (`bpc_S13.json`) | **0** after the fix (S13 idle hand had dipped into the arriving croc's head) |
| Tourists Spec A–G | S16–S17 (2731–3120) | **0** |
| Funeral guests | S19–S21 (3341–3900) | **0** (seated on benches failed twice → re-staged standing, benches removed) |

Fixed before P1 (found on my own sheets): man walking backwards (walk yaw), bucket rendering as an icosphere and hanging
across his thigh, tourists crouching (pelvis ray fell through deck-plank gaps), camera inside the house (S11) and in the
roof (S05), S10 camera behind his head, portrait upside down and showing the logo sign, singer cut by the frame edge,
skin-toned clothes on the man (now mid-blue).

## Known issues / unsure (frame numbers in the P1 timeline)
1. **S07 1117–1162** meat-in-hand overlap (above). P2 plan: rest it on the open palm (cup_hold, offset along the palm
   normal) or toss straight from the bucket rim.
2. **Logo sign on the deck** is one placement but it is visible in the background of many HOME shots (S05, S06, S09 night,
   S12–S14). Proposal: key it visible only in S16–S17 (show for tourists).
3. **S10 (sleep close)** is dark and his face is small; readable but weak. Alternative: a higher angle over his chest.
4. **S11** we see him mostly from behind while he points (his face is in S12/S13). Could swap to a front 3/4.
5. **S21** the portrait/easel covers part of the frame; the singer is small. **S20** the foreground guest wears salmon-pink:
   reads as clothing at 540 px but I can switch it to a darker colour.
6. **S06** the croc starts as a small shape far away (it swims toward camera).
7. Croc walking is a belly-crawl (legs paddle, belly on the ground); no jaw bone (the snap in S08 is a lunge with the head up).
