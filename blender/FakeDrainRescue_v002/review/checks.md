# v002 checks (all run on the exact package FakeDrainRescue_v002_60fps.blend)

| Check | Result |
|---|---|
| `body_prop_cross` (per shot, step 3: phone, desk, stool, forms, drain walls, end wall, pipe, truck, all trash near people) | **21 of 23 shots: 0 visible.** Residual: S19 (12 checked frames) and S20 (11). See the phone grip note below. |
| `clip_scan` (step 6) | **0 bad ranges** |
| `limb_check` (step 4) | 62 ARMBODY hits, all with only 2 points, in S02 (pointing arm) and S22 (hanging arms). A direct per-point test finds them only at the shoulder joint, where the torso test mesh is open (a point 2 cm from the shoulder reads as 10 cm deep). They match the shoulder false positive described in LESSONS §4. The real S03 hit (forearm in the hip, frames 151–229) is fixed. |
| `qa_check` (step 6) | EMPTY appears on the no-character shots (S14 clog, S17 clog, S23 truck, S25 top view), which show the thing the VO names. It also appears, falsely, on character shots where people are clearly visible in the preview (qa camera binding). CAMJUMP = the 22 hard cuts. FAN/CLAW on S02 frames 115–139 come from the pointing pose itself: the index finger is extended and the other fingers are curled. I checked it at 1080×1920 and it reads as a clean point. |

## Known issues
- **Phone grip (S19, S20):** `grip_object` wraps the fingers around the phone's edges. The pinky side of the palm sits a few mm into the back face of the phone. That face points away from both cameras, and the hand reads clean at 540×960 and 1080×1920. Raising the phone to chest height broke the grip (fist through the screen), so S20 is framed chest-up instead, with the phone just below frame.
- **At 1080×1920 only:** the shoe collars poke slightly through the fitted trouser cuffs at both ankles, and the top-to-trouser colour line at the hip is stepped. Neither is visible at preview size. If wanted, the fix is a darker shoe collar and a smoothed colour split.
- **Clerk's hair:** short MPFB hair that reads close to a cap. It's left as is, because fitting another hair to this body risks a worse result.

## Preview
`review/preview.mp4`: frames 1–1752, every 5th frame at 270×480, Cycles 4 spp, with the VO.
The full render came from the package. Frames 146–232 (S03) and 1266–1366 (S19–S20) were re-rendered from the final package after their fixes and spliced in. All other shots are unchanged by those fixes.
