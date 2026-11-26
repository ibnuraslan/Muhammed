# NukedWell_v009: from-scratch rebuild (batch 1, film 18)

**Status: ON HOLD.** Two fix rounds are done (the brief's limit), and the fresh reviewer still marks the film FAIL. The `.blend` is **not** pushed (it stays git-ignored until there is a PASS). Watch `review/preview.mp4` (270×480, every 5th frame, with the VO), which was rendered from the exact package.

It is built to the client's VO (v008 timing, `blender/briefs/sync/18.anchors.json`): frames **1–1541** at 60 fps. The beats are in `beats.json` (1/156/282/387/507/777/875/1023/1131/1202/1341). The scripts are in `scripts/`: 01 build, 02 animate, 03 package.

## The film (one continuous camera, a desert diorama with a clean side cut-away)
- **Opening:** a red A-frame headframe lowers the plain green device on a visible cable (sheave and winch). A worker signals "lower slowly" and the engineer watches. A DA KRAS FILMS crate reads at f1–95. The camera follows the device down the cut face of the strata.
- **The pour:** a concrete stream falls down the bore and the plug fills above the device.
- **"Three years earlier":** the shot rewinds (the plug drains and the device rises), and the camera travels underground to the gas well. Gas surges up the casing and erupts into a turbulent fire column. No volumes are used: the fire is nested noise-emission shells.
- **Day and night:** the sky goes from day to dusk to night and back with the two men watching. Two Soviet ZIL-131 fire trucks spray water arcs, which steam and fail.
- **The cap:** a steel cap is lowered on its cable and the main fire dies. Cracks open and fissure fires burst out; they keep burning into the present.
- **The detonation:** the camera dives to the device under its concrete, and a wide cross-section shows the detonation flash (exposure-controlled, never a white frame), a cavity, a pressure ring, a surface jolt and a dust ring.
- **The squeeze:** the strata are compressed radially and the gas casing pinches shut. The gas above the pinch dies.
- **The end:** the camera rises up the dead pipe as the fissure fires sputter out. The crew cheer by the capped wellhead, with the second logo crate behind them.

## Remaining faults (fresh reviewer, round 2; times = preview seconds = frame/60)
1. **f1381–1541:** the cap's top ring reads as a thin disc hovering above the cap body in the low end shot (seen edge-on). Fix: one merged cap mesh, or raise the end camera.
2. **f1401–1426:** an orange glow shows inside the capped wellhead. It is the smoke-wisp shader's warm base emission and should be set to 0.
3. **f286:** while the plug drains, a gap opens between the top of the pour stream and the plug. f216–246: the pour reads as a block more than a stream. Fix: a thicker stream that is longer and continuous.
4. **f441–860:** the past-day sky is a flat beige band with a seam at the horizon. Fix: a saturated warm-blue gradient.
5. **f460–900:** the fire still reads pale yellow in its lower half. Fix: a hotter orange-red ramp and darker smoke.
6. Other notes: the closing camera drift is small (f1445–1541), and the second logo crate is partly clipped by the collar.

## Checks on this package (round 1 file; round 2 changed only timing and visibility)
- `clip_scan`: 0 bad ranges.
- `limb_check`: ARMBODY only on CrewB's pointing gesture (f559–637). That gesture was removed in round 2.
- `qa_check`: EMPTY on the character-free cross-section frames (by design). The camera-INSIDE flag at f1417–1477 came from the oversized dust torus, which is hidden after f1320 in round 2. ATTACH on the cap and PROPMOVE on the steam are not hand props.
- The full-resolution render check was **not** run, because there is no PASS yet.
