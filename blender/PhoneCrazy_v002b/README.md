# B18 PhoneCrazy v002b: "Why Did This Phone Go Crazy"

Built to the client VO (`PhoneCrazy_v002b_VO.mp3`, 32.1 s). Beat frames = 1 + round(word seconds × 60), in `beats.json`.
21 shots, hard cuts, one camera. Build scripts: `blender/PhoneCrazy_v001/scripts/` (`build_all.sh work/timing.json`), plan in `../PhoneCrazy_v001/PLAN.md`.

| Shot | Frames | VO |
|---|---|---|
| S1 wide site, excavator digging, crew watching | 1–56 | The moment they started |
| S2 bucket bites the pit wall | 57–112 | digging |
| S3 phone on the case unlocks itself | 113–242 | one of their phones suddenly unlocked itself |
| S4 low reaction over the case | 243–359 | without anyone touching it |
| S6 apps open (top close) | 360–476 | Then it began opening apps |
| S7 reaction, screenshots flashing | 477–552 | taking screenshots |
| S8 keypad 9-1-1, calling, buzzing | 553–710 | and repeatedly trying to call 911 |
| S5 crew watching, logo on the case | 711–786 | They stopped digging and |
| S9 crew over the case, calling again | 787–871 | watched it happen |
| S10 pit full of water | 872–1022 | You see, they were standing inside a pit that had |
| S11 whirlpool starts | 1023–1099 | mysteriously swallowed |
| S13 water drains away, crane up | 1100–1254 | around 45,000 gallons of water |
| S14 empty pit, drain hole | 1255–1385 | without leaving any trace |
| S15 excavator digs in the pit | 1386–1439 | They were trying to discover |
| S16 cross-section: shaft, cavern, stream | 1440–1513 | where the water had gone |
| S17 Foreman stares at the phone | 1514–1559 | when the phone |
| S18 screen glitches, buzzing | 1560–1662 | suddenly started acting possessed |
| S19 low reaction | 1663–1739 | almost like something |
| S20 dark ripple screen, push-in | 1740–1795 | underground was |
| S21 keypad / calling again | 1796–1859 | desperately trying to |
| S22 crew at the pit rim looking into the hole | 1860–1931 | send them a message |

S12 (separate "swallowed" shot) was dropped: at the VO pace it would be 0.6 s; S11 carries "mysteriously swallowed".
Logo: DA KRAS FILMS (white) on the orange site case, S5 and S9. No other text; phone screens are pictures only.
Review: `review/preview.mp4` (every 5th frame at 270×480 with the VO), check results in `review/`.

## v002b vs v002 (fixed after watching the v002 preview, before review)
- Phone-screen schedules no longer run past their cut (S7 screenshots leaked into the start of S8; S18/S19 glitches leaked into S20/S21; S20 now shows the dark ripple as planned). Buzz and jitter also stop at the cut.
- S16: the cavern pool has its own steady material (the flowing-band material flashed on the flat pool).
- S14: stronger push-in to the drain hole (was nearly static for 2.2 s).
- S22: camera moved so the case no longer sits behind the Foreman's head.
Changed ranges re-rendered and spliced into `review/preview.mp4`: f553–786, 1255–1385, 1440–1513, 1663–1931.

## Checks (on this exact package)
- clip_scan: 0 bad ranges.
- body_prop_cross (Case, Phone, step 3): 0.
- limb_check: 697 ARMBODY, all "(2 pts)" = the known upperarm points 0–2 at the shoulder false positive; no other hits.
- qa_check: EMPTY 323 (phone, pit, excavator and cross-section shots have no person, by design), FILL 24 (the case lid / screen fills the phone close-ups), CAMJUMP 19 (the cuts), PROPMOVE 28 (the whirlpool cone), FAN 59 (Mate's pointing hand: index out, others curled), BACKHEAD 3 (Digger in the S1 wide and the last S10 frame, crew watching the excavator).
Watched: the full v002 preview (8 pages) start to finish, then every changed range in the v002b splice.
