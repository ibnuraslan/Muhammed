# body_prop_cross: B26 TenDimes P1

Props checked (step 3): DimePile10, DimePile2, DimePileD, Handset, HandsetCord, Club_Mic, Club_SideTableTop/Stem,
Street_PayLedge, Street_Payphone, Street_Wall, Room_Door, Room_DoorFrameL/R, Room_Bed, Cem_Casket, Cem_CasketLid, Cem_BierTop, Sub_Car.
Rigs: Singer, Son, Kidnapper, Daughter.

## Full film (frames 1–2784, build 3)
| Shot | Visible crossing frames | What |
|---|---|---|
| S01–S07, S10, S12, S14–S22 | **0** | — |
| S08 / S09 / S11 | 36 / 31 / 42 | Handset ↔ head, right hand and forearm, hat brim (see below) |
| S13 | 5 (frames 1555–1567) | son's leg ↔ car at the start of his walk |

Fixed in the pushed scripts (build 5): S13 walk starts 0.25 m clear of the car → **0** (re-run on 1554–1694).
Earlier builds also flagged S21 (fingers into the casket lid): re-staged with no hand → **0**.

## Open: handset (S08, S09, S11), 109 visible frames on 992–1445 in build 5
The "Handset" object was joined from the payphone model's loose parts above the cradle. It also picked up the
**cradle hook pieces**, so it is bigger than the real handset (the funnel shape at his chin in S09), and it crosses his
palm, wrist, forearm, the side of the head and the hat brim even with the earpiece 4.8 cm off the ear.
Fix planned before Phase 2: keep only the handset part (loose part .000), or replace it with a clean modelled handset
(earpiece + grip + mouthpiece, ~22 cm), re-fit the palm wrap to it, and re-run the check on the three shots until it
reads 0. If it still fails, fall back to §2.15: frame the phone hand out (CU from his left side) for S08/S09.
