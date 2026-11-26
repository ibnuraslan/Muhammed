# NukedWell_v009: from-scratch rebuild (batch 1, film 18)

**Status: ON HOLD.** Pushed on the director's instruction after round 3 with the render check PASS. My own watch of round 3 is clean on the 5 director items. The fresh reviewer still marks it FAIL (see "Remaining faults" below). Watch `review/preview.mp4` before it goes to the client.

## Render check: PASS
On the exact file `NukedWell_v009_60fps.blend` (41 MB), opened with `blender --factory-startup -b`:
- No linked libraries, no unpacked images, and the VO sound is packed.
- No drivers and no Python texts. The only warning in the log is a deprecation notice from the check script itself.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1541, PNG to `//render/NukedWell_v009_####.png`, and the VO strip at frame 1.
- Test frames were rendered at full resolution with 64 adaptive samples on a 4-core CPU with no GPU: f30 in 106 s, f700 in 172 s and f1500 in 97 s. None is black, empty or pink. The DA KRAS FILMS crate reads sharply in f30 and f1500.

## Round 3 (director-approved)
1. The cap sits on the wellhead: its rings and eye are fixed to the body (before, a ring floated 0.5 m above it).
2. No glow in the capped wellhead: the smoke wisp has no warm base emission and moved to a fissure.
3. The pour is a thicker, glossy wet-concrete stream. On the rewind its top falls onto the draining plug, so no gap opens.
4. The past sky is a saturated warm-to-blue gradient, and the white horizon strip is gone.
5. The fire is a deep orange-red ramp. The fissure flames are narrower and taller (no cup shapes).

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

## Faults fixed in round 3 (from the round 2 reviewer)
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

## Remaining faults (fresh reviewer, round 3; time = frame/60)
1. **f446–990:** the warm past sky reads as a flat ochre band behind the fire (backdrop-like) with a hard horizon line. Fix: a softer, taller gradient or a dusk HDRI.
2. **f301–346:** after the plug drains, a thin grey disc stays in the empty shaft. Fix: key the plug's visibility off when its scale reaches about 0.
3. **f876–881:** the water arcs break up into chunks as the monitors close. Fix: retract from the nozzle end.
4. **f352–365 (0.2 s):** a strata-only stretch on the underground traverse.
5. **f480–870:** the firemen by the trucks are small (wide fire shots).
Polish notes: the end frame clips the cap and the second crate ("KRA…"), and the opening sky is pale.
