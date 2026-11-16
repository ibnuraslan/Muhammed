# Checks on the exact package `ScaldingCoffee_v002_60fps.blend` (frames 1–1808)

| Check | Result | Notes |
|---|---|---|
| `body_prop_cross` (step 3, per beat, every held or touched prop) | **0 visible crossings** in B3, B4, B5, B6. B1: only `SpillSteam` (steam volume = gas, not a solid) | Props: B1 cup, lid, car seats, door, dash, floor, wheel, roof lining, door trim; B3 bed, mattress, backrest, pillow, blanket, IV stand, cabinet, badge; B4 cup, counters, bar table, trays; B5 table, chairs, cup, sideboard; B6 knob, dial, machine, counters |
| `limb_check` (no-shoulder variant from CaveRescue, step 4) | **0** | The stock version reports 2–4 axis points per arm right at the shoulder joint (the known upperarm01 false positive in LESSONS §4) |
| `clip_scan` (step 6) | Bad ranges **1–187** and **247–301** (B1, the seated woman, "self") | Her forearm/hand vertices lie within 2 cm of her own thighs/hips while her hands rest on her lap and during the flinch. Checked visually with the car hidden (front + side) and in the preview: no limb passes through her body |
| `qa_check` (step 6, beats.json) | EMPTY / FILL on 302–726 and 1733–1808 | Product inserts by design: the urn pour, the served cup, the coffee macro (steam fills the macro), the dial insert |
| | CAMJUMP ×14 | Exactly the 14 hard cuts between shots (hard cuts are the v2 brief's grammar) |
| | PROPMOVE ×4 (frames 151–163) | The cup tipping between her knees and the coffee pool spreading: the hands-free spill the director approved at P1 |
| | CLAW/FAN on C4.R (1045–1477) and Employee.L (1645–1729) | The C4 wrap grip on the logo cup and the employee's tripod grip on the knob; watched at 540×960 (frames 1090, 1700): fingers wrap the cup / pinch the knob, no starfish or claw read |

## Re-check after the preview review (same results)
Watching the first preview caught two faults, both fixed in this package:
1. **Texture swap from the packager:** `05_package.py` deduped images by *name*. Every GLB asset names its maps `Image_0/1/2`, so the boardroom table (5a/5b) rendered with the black office-chair maps, and the car seats, café brewer and IV stand had wrong maps. Dedupe is now by content hash (sha1 of the packed bytes + size + colour space).
2. **C1's fringe covered one eye in 4c** (LESSONS: fringe off the eyes). The front `bob01` strands are lifted to the brow line (`scripts/fringe_fix.py`); both eyes are clear.

All checks were run again on the rebuilt package (md5 `fa8f756653c2a866e7e45e594ac263ce`, 56 MB) and gave the same results as above: body_prop_cross B1 only SpillSteam and 0 elsewhere, limb_check 0, clip_scan B1 1–187 and 247–301 (self, explained above), qa_check the same flags. `review/preview.mp4` was rendered from this exact file.
