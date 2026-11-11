# EscapeArtist — PLAN (Checkpoint A)

Connect34 · branch `claude/connect34-escape-artist` · 1080×1920 @ 60 fps · frame_end 3750 (62.5 s) · Cycles CPU, AgX Medium High Contrast.

One camera (`CAM_Main`) on one continuous path, keyframed framing roughly every 60 frames, Bezier/auto-clamped so velocity never stops. Sets sit side by side on one large stage so the camera can **fly** from one to the next (through a wall, through bars, over the fence, a whip-pan into the memory) and never cut.

## Sets (reused heavily: 62 s film)
| Set | Used in beats | Build |
|---|---|---|
| **CELL** (3×2.2 m, bars front, high barred window back wall, bunk, sink, tally wall) | 2, 3, 9 (as solitary variant: door closed, slot light), 10, 12, 13, 15 | Poly Haven concrete wall/floor scans with displacement, rusty metal bars, Sketchfab bunk/toilet if found |
| **CORRIDOR** (tier of cells, 14 m long, lamps, guards walking) | 1, 3, 7 (gate slam at end), 11 | same materials, instanced cell fronts, 2–3 MPFB guards |
| **FENCE YARD** (chain-link with razor-wire coils, floodlight, field beyond) | 8, 14 (protesters outside the wall) | chain-link via alpha-mask texture on plane + real wire geometry for coils (curve helix w/ barbs), Poly Haven ground scan, night HDRI |
| **MEMORY HOUSE** (warm workshop + living room with phone; police lights through window) | 4, 5, 6 | Poly Haven wood table/workbench, Sketchfab clock/toolbox/phone; warm tungsten grade, soft DOF |
| **COURT** (small corner: bench, gavel) | 7 | gavel + desk models; then camera whips to corridor gate |

## Characters (MPFB2, CC0 MakeHuman assets, generic faces)
- **Prisoner** young (beats 1–11), aging via material/hair grey + slightly stooped pose (12–15). Orange-ish prison clothes, MakeHuman shirt prints patched out.
- **Boy** (~10 y) for 4–5. **Father** (60s). **Stepmother**. **Guards ×3**, **Police ×2**, **Judge**, **Protesters ×6** (crowd reuses guard/extra meshes with different clothes).
- Face bones for expressions: focus (brows down, lids narrowed) beat 1–2, joy beat 4, grief 5, anger stepmother 6, strain 8/10, fear/resolve 11, weary 13, calm 15.

## Beat table (target times; frame = t×60)
| # | t (s) | frame | Line | On screen | Camera (one framing ≈ 1 s) |
|---|---|---|---|---|---|
| 1 | 0.0 | 0 | glance at a guard's key… memorize its pattern | Corridor: guard walks past cell, key ring swings on belt. Prisoner's eyes track it; key teeth glow as a memory overlay (emissive copy of key bitting floating beside eyes). | Low dolly along corridor with guard → swing to key ring macro → whip to eyes ECU through bars → push into iris. |
| 2 | 4.6 | 276 | file scrap metal into the same shape | Cell at night, lamp. Hands with a small file on a scrap strip; sparks/filings; key profile emerges (shape-key morph). | Pull out of iris into cell; orbit down to hands macro; rise over shoulder. |
| 3 | 9.3 | 558 | let himself out | Key turns in cell lock (hand grasps), door swings, he slips into corridor. | Macro on lock → track the door swing → pull back into corridor as he exits. |
| 4 | 11.3 | 678 | autistic child… talent for mechanics | Whip-pan; corridor softens (DOF + warm grade) into memory workshop: boy at workbench, clock open, gears; focused smile. | Whip-pan → slow push over workbench → gear macro → boy's face. |
| 5 | 15.7 | 942 | father died… left his tools | Father's hands pass worn toolbox to boy (both grasp); then rack to the father's empty armchair, rocking slowly. | Two-shot hands → rack focus to empty chair, crane down. |
| 6 | 18.8 | 1128 | stepmother called the police | Stepmother on old phone, angry, pointing; window fills with red/blue police lights, car pulls up outside, officers walk in. | Swing past chair to her → push to phone → drift to window, light sweeps. |
| 7 | 23.7 | 1422 | sentenced to four years | Gavel strikes (squash, dust); whip to prison gate slamming in corridor. | Gavel macro low angle → whip-pan → gate slam push-in. |
| 8 | 25.8 | 1548 | one month… climbed razor wire fence and ran | Night yard: he climbs chain-link (hands/feet on mesh), over razor coils, drops, runs into fields; searchlight sweeps, dogs bark (wind in grass). | Low ground skim to fence → crane up with him → over the fence top → chase behind as he runs. |
| 9 | 31.0 | 1860 | more time… solitary confinement | Recaptured: guards push him into solitary (cell variant, solid door), door slams, slot of light; he sits on bunk. | Fly back in through door slot → settle on him sitting, slow orbit. |
| 10 | 36.2 | 2172 | makeshift saw… cut through the bars | Hands saw a window bar with thin blade, filings fall, bar notch deepens; he glances at the door. | Macro on blade → pull to his face straining → back to bar. |
| 11 | 41.4 | 2484 | toothpaste tube… like a gun | Brief silhouette: bent tube (L-shape) held up, backlit; guards freeze, hands up, then chase him down corridor. | Silhouette profile → swing round to guards → chase dolly down corridor. |
| 12 | 48.3 | 2898 | 13 escape attempts… 34 years | Time-lapse in cell: tally marks multiply on wall, light cycles day/night fast, hair greys. | Locked-in orbit around him with fast light cycle; slide along tally wall. |
| 13 | 53.8 | 3228 | 27 in solitary | Camera slowly circles him in solitary, light shifting across decades. | Slow 180° orbit, slight rise. |
| 14 | 58.3 | 3498 | people have protested | Out through the window: protesters outside the wall, blank placards, candles flicker. | Fly out the window, over wall, low past candles. |
| 15 | 60.3 | 3618 | still in prison to this day | Older man at window looking out; camera pulls back through the bars. Settle. | Push back toward window from outside, then pull back through the bars and settle. |

## Assets & licences (being fetched now)
- Poly Haven (CC0): concrete wall/floor scans, rusty metal, ground/rocks, brick, wood, night HDRI.
- Sketchfab via Objaverse (CC-BY / CC0 only), searched with `find_models.py`: prison cell/bars, bunk, chain-link/razor wire, workbench, toolbox, clock, gavel, police car, rotary phone. All credited in CREDITS.md.
- MPFB2 + MakeHuman system assets (CC0) for all humans.

## Trickiest shots & approach
1. **Fence climb (8):** IK hand/foot targets keyed onto the mesh plane at the wire spacing; razor coil is real curve geometry. Camera cranes with him so the move reads.
2. **Key filing (2) / bar sawing (10):** hands are MPFB hands with IK targets on file/blade handle; grasp first, then strokes with a small cycle; sparks/filings as particles. General shot, no technique detail.
3. **Time-lapse aging (12–13):** shape/material driver: hair colour lerp + skin roughness; tally-mark texture revealed by animated mask; sun light rotates rapidly.
4. **No cuts across 5 sets:** sets laid out on one stage; transitions are whip-pans with motion blur, a fly through the cell slot/window, and rack-focus memory blend.
5. **Time:** compressed schedule; MPFB humans built once and duplicated; corridor and cell are the same geometry module.

## Unsure / flags
- Blank placards and no text everywhere, as briefed.
- Time is tight (~4.5 h to D). Priority: camera + key actions on every beat, then contacts, then secondary life.
