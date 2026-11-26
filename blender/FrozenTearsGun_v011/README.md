# FrozenTearsGun_v011: package for the client's render (CLIENT-APPROVED)

**Status: READY TO RENDER.** The client approved this build as it is (relayed by the director on Nov 26, 2026).
- `FrozenTearsGun_v011_60fps.blend` is that build, the check-7 build.
- `review/preview.mp4` is its moving preview: 270x480, every 5th frame, with the VO. Watch it before paying for the render.
- **One change after approval:** two invalid scripted drivers that came with the Poly Haven tool-chest asset (on the lock's mask modifier) were removed, to meet the zero-error rule. The properties keep the same values. Full-resolution frames 1, 828 and 1655 match the approved build's renders to within render noise (mean difference 0.04 of 255).

## Render check: PASS
Checked on the exact delivered file, `FrozenTearsGun_v011_60fps.blend` (70 MB, compressed, a plain git file):
- **Opens cleanly:** it loads with `blender --factory-startup -b` with no errors or warnings in the console.
  - There are no linked libraries, no unpacked images or fonts, and the VO sound is packed.
  - There are 0 drivers and no scripts, so auto-run is not needed.
- **Scene settings:**
  - one camera, `CAM_Film`, with no camera markers
  - 1080x1920 at 100 %, 60 fps (fps_base 1.0), frames **1-1655**
  - PNG RGB output to `//render/FrozenTearsGun_v011_####.png`
  - the VO strip is present from frame 1
- **Test frames:** frames 1, 828 and 1655 rendered at full 1080x1920 from the packed file.
  - None is black, empty or pink.
  - Each took 49-57 s on 4 CPU cores at 16 samples (the farm setting is 64 adaptive).
  - Copies are in `review/render_check_*.jpg`.
- **Logo:** DA KRAS FILMS framed prints are on the lab wall, fully readable at 1366-1456 (about 1.6 s), and on the office wall.

## Known (last harsh review, check 7), accepted by the client
- Three fast camera moves read close to cuts: 731-736, 851-861 and 1606-1611.
- The index-finger trigger pull is subtle: the trigger turns and the hand tightens.
- The mentor's arms drop to his sides at 1626-1651.
- Her face is edge-cropped at 166-221 and 1101-1116.

## History: check 7 (round 6), what was fixed
- The office lamp is gone.
- The second trigger close-up reuses the left-side angle.
- The pellet chase is replaced by a pull-back to a wide of the range.
- The gas macro is recentred on her face and the chamber.
- A close render of the grip shows a normal palm wrap, with no palm through the grip.
- Fastest camera turn is 33 degrees per frame, with 0 lens blockers and 0 pop-ins.

## Check 7 faults (fresh harsh review, film frames)
1. **Three moves still read as cuts:** 731->736 (bench to range, following the pellets), 851->861 (target to office) and 1606->1611. The 1606->1611 pull-back happens inside the 14-frame pellet flight, so it is too fast.
2. **No visible trigger pull:** the finger pull does not read at 651-700 or 1576-1601. The trigger moves 14 degrees and the hand only tightens. A real keyed index-finger pull, with the finger off the trigger before and squeezing it, is needed.
3. **Mentor's arms:** they drop to straight arms at his sides at 1626-1651, so the film ends on an A-pose read. Keep his hands up or reacting.
4. **Smaller items:**
   - her face is cropped at the left edge at 166-221 and at the right edge at 1101-1116
   - 446-495 is a near-static chamber hold
   - a lamp shade shows at the top edge at 956-996

## Check 6 (round 5): what was fixed
- **No whips:** every whip is now a slow move of 30 frames or more. Between the bench and the range, a high corner view behind her holds both people. The fastest camera turn is 33 degrees per frame, down from 58.
- **Second trigger:** a 30-frame over-the-shoulder close-up of her trigger hand. The shot is retimed to land on "him".
- **Left hand:** it stays in frame until it rests on the bench.
- **Checks:** 0 lens blockers and 0 on-camera pop-ins. All teleports happen off camera.
- **Logo:** readable at 1366-1471 (about 1.8 s).
- **Passing:** the valve turn, the first trigger pull (666-696), the freezing, the target hits, the memory and the ice hit all read.

## Check 6 faults (fresh harsh review, film frames)
1. **861-866:** the office hanging lamp (moved there this round) hangs in front of the mentor's head. This is a regression; the lamp must be moved off his eyeline.
2. **1601-1616:** the chase reads as two jump cuts. The camera snaps from the over-the-shoulder close-up to a wide shot, then to a chest close-up.
3. **1574-1602:** the over-the-shoulder trigger close-up shows a fist; the index-finger pull is not visible. The left-side angle used at 666-696 works and should be reused.
4. **401-496:** her face is cut by the right edge in the gas macro.
5. **Risk at 651-706:** the palm may bulge behind the wooden grip; check it in a close render.

## Check 5 (round 4): what was fixed
- **Valve:** the valve and trigger pivots had been created before their transforms were valid, so they sat at the gun origin. Now she visibly grips the red rim and turns it (291-346), with her face in frame.
- **Trigger:** a close-up of her finger on the trigger at 664-700 before the first shot, and a second one at 1576-1585.
- **Bench shot:** it now drifts and pushes in (1345-1474). The logo is fully readable at 1351-1471, about 2.0 s.
- **Office:** a tighter moving shot, from the lecturing mentor across the desk to her face (880-1000).
- **Automated checks:** 0 lens blockers, 0 pop-ins, and the fastest camera turn is 58 degrees per frame.

## Check 5 faults (fresh harsh review, film frames)
1. **Fast transitions:** each produces 1-2 bare-wall or no-subject tiles and reads as a jump cut or blur in a one-camera film. They are at 656-661, 701-726, 851-861, 946-951, 1301-1306, 1476-1486 and 1556-1596.
2. **Second trigger close-up:** 1576-1581 is only about 0.17 s, and the finger pull is not readable.
3. **Hand at the edge:** at 361-366 her releasing hand shows as fingers at the frame edge with no arm.
4. **Risks:**
   - 371-446 is a nearly static canister and chamber shot, about 1.3 s.
   - The crying close-up at 1001-1191 is long.
   - The sweater reads fitted across the chest at 1001-1031.

## Recommended fix (not started)
- Replace every whip with a slower move of at least 30 frames that keeps a person in frame: an arc or a pull-back through the room, never a pan across walls.
- Give the second trigger close-up at least 30 frames with a visible finger pull.
- Keep her left hand in frame until it is back on the bench.

## Check 4 (round 3): what was fixed
- **Grade:** deep and warm. The skin tint now reaches inside the MPFB skin node group, the light levels are 0.45x and the valve is a true red.
- **Macros:** her face stays in frame through the chamber, gas and freezing macros.
- **Logo:** readable at 611-701 (1.6 s) and at 1341-1471 (2.1 s).
- **Finale:**
  - Two bugs were fixed: the finale pellets had been hidden for the whole film, and the muzzle puffs sat at the gun origin.
  - The shot is restaged: a whip down the range to him, back to her at the bench, then the camera chases the pellets to his chest. The hit reads.
- **Mentor:** his talking arms are now bent, and he holds his palms out on the range.
- **Automated checks:** 0 pop-ins, 0 lens blockers (nothing within 6 cm of the lens), and the fastest camera turn is 49 degrees per frame.

## Render check on the packed build (passed, not delivered)
- **Opens cleanly:** `blender --factory-startup -b` opens it with no unpacked images, no linked libraries and the VO packed.
- **Scene settings:** CAM_Film, 1080x1920 at 100 %, 60 fps, frames 1-1655, PNG output to `//render/FrozenTearsGun_v011_`.
- **Test frames:** frames 1, 828 and 1655 rendered at full resolution with 16 samples in 60-70 s each. None is black, empty or pink. Copies are in `review/render_check_*.jpg`.

## Check 4 faults (fresh harsh review, film frames)
1. **Valve turn not readable:** her hand at 326-346 reads as hovering near the chamber, not gripping the red wheel.
2. **No trigger pull on camera before either shot:** at 711-726 her face leaves the frame and the camera cuts away from the trigger, and at 1576-1586 the trigger is again not shown.
3. **Near-empty whip frames:**
   - 1476-1486 (toolbox and teal wall, 3 tiles)
   - 1561-1571 (a hand at the frame edge, then wall and toolbox)
   - 1306-1311 (2 tiles)
4. **Near-static bench hold:** 1346-1466, about 2 s.
5. **Small items:**
   - the office wide at 876-996 creeps slowly and the faces are small
   - his face is half out of frame at 1301
   - the frozen balls read speckled red at 711-721

## What v011 is
- **Timing:** the client's v010 VO (27.0 s), with frames 1-1655 at 60 fps. It was built to the VO word timestamps from the start, so there is no retime. The beat frames are in `beats.json`.
- **One camera:** `CAM_Film` makes one continuous PCHIP move through one lab room with a bench, a range and the mentor's office corner. There are no cuts or camera markers, and the fastest turn is 26 degrees per frame.
- **People:** one MPFB model per character. She wears a real MakeHuman fisherman sweater and wool pants; the mentor wears a real MakeHuman suit.
  - **Solid bodies:** the delete-group masks are removed. The skin under the clothes is sunk about 7 mm and painted a dark lining colour, so nothing is hollow and there is no crotch hole (checked in close renders).
  - The eye fix is applied to both.
- **Small objects:**
  - The gun rests in a wooden cradle on the bench for the whole film. Her right hand holds the grip with a `grip_object` wrap, her left hand rests on the bench or on the red valve wheel, and the hand turns with the wheel.
  - Tears, the tube drops, the beads and the pellets are each one object moving continuously.
  - Teleports happen only off camera. An automated frustum check found 0 on-camera visibility changes.
- **Logo:** the DA KRAS FILMS framed print sits on the lab wall behind her, and a second print is on the office wall.
- **Build:** run `scripts/01_build.py` (people, set, gun, look), then `scripts/02_animate.py` (acting, effects, camera, VO), then `pipeline/package_for_farm.py`. Before that, install the MakeHuman CC0 asset packs shirts01, pants01 and suits01, and the Poly Haven assets listed in CREDITS.md.

## Render check on the local packed build (not delivered)
- It opens with `--factory-startup`, with no unpacked images and no linked libraries. The VO is packed, the camera is CAM_Film, 1080x1920 at 100 %, 60 fps, frames 1-1655, PNG output.
- Frames 1, 828 and 1655 rendered at full resolution with 16 samples in 72-79 s each. This check passed, but the film did not pass review, so the file is not delivered.

## Check 3 faults (fresh harsh reviewer, film frames)
1. **Logo:** it is fully readable only from 1356 to 1426, about 1.2 s. It is cropped at 1-46, 231-246, 621-701 and 1236-1301. It needs one clean placement for at least 1.5 s.
2. **Empty or plain stretches:** 731-746 (wall with ice balls), 786-856 (target face fills the frame), 1001-1011, 1306-1321 (whip to the bench), 1466-1496 and 1556-1601 (whips through empty rooms).
3. **Static holds:**
   - 881-996: office wide shot, with her cut at the left edge from 951 to 996
   - 1021-1191: her profile close-up, about 2.8 s
   - 621-701: medium wide
   - 1626-1651: end hold
4. **Hand with no arm:** at 366-396 her right hand on the grip shows at the frame edge without its sleeve.
5. **No face in long macro stretches:** 76-111, 151-221 and 351-576 (valve, CO2 and freezing). The freezing at 401-500 reads soft.
6. **Mentor:** his arms hang straight in the office (881-1301) and he does not gesture. His end reaction is a gape rather than a laugh.
7. **Key beat:** her firing at the mentor (1585-1605) is not readable. The camera whips from the mentor to the bench and back through empty rooms, and the gun and shot are never in frame together with him.
8. **Grade and effects:**
   - skin reads chalky and the overall look is pastel; it needs a deeper grade
   - the red valve renders salmon
   - tears are pinhead-sized
   - the ice hit is a soft white blur

## Recommended next step (needs the director's OK)
Restage the finale as one move: a side medium down the range, with her and the gun in the foreground and him at the far end, plus a push along the pellets. Replace the office wide with a moving two-shot and give him gesturing arms. Add a third logo placement, readable for 2 s, in a moving bench shot. Deepen the grade with the BellyFat v018 rebuild (client-approved) as the quality bar.
