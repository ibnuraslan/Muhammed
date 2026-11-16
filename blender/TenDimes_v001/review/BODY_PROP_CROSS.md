# body_prop_cross: B26 TenDimes P1b

Tool: `scripts/bpc_run.py` → `scripts/bpc_nohelpers.py`. This is `pipeline/body_prop_cross.py` with one change: MPFB helper
vertices (HelperGeometry / JointCubes) are skipped, as clip_scan does (LESSONS §3). Why: the pipeline version reported
109 "head|Handset" frames that were the hidden helper-hair cube under the hat (vertices 18951–19020 of Singer.body,
groups HelperGeometry + helper-hair; masked by the rig's "Hide helpers" modifier, never rendered).

Props: DimePile10, DimePile2, DimePileD, Handset, HandsetCord, Club_Mic, Club_SideTableTop/Stem, Street_PayLedge,
Street_Payphone, Street_Wall, Room_Door, Room_DoorFrameL/R, Room_Bed, Cem_Casket, Cem_CasketLid, Cem_BierTop, Cem_Skirt, Sub_Car.
Rigs: Singer, Son, Kidnapper, Daughter. Step 3.

| Run | Frames | Visible crossings | Any crossing (incl. off-camera) |
|---|---|---|---|
| full film, build 6 | 1–2784 | **0** | 15 frames: son's right foot in the bed, S04 (off-camera) → fixed below |
| phone shots, build 6 | 992–1445 (S08–S11) | **0** | 0 |
| room, build 9 (son 25 cm off the bed) | 438–727 (S04–S05) | **0** | **0** |
| S04, build 10 (final arm pose) | 438–555 | **0** | 0 |

Builds 6 → 10 changed only: S04 (son's mark and arms), S04/S11 cameras, lawn extents, and lights hidden from the camera.
No other animation changed.

Handset (S08–S11): a modelled handset. `grip_object` closes the right hand on it at the first frame, then it rides in the
hand (Child Of the wrist) while the wrist keeps it at the ear. The hand cannot pass through it. Hair cards at the
right ear are trimmed under the earpiece.
