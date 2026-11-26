# FrozenTearsGun_v011: from-scratch rebuild, NOT READY (ON HOLD)

**Status: ON HOLD.** The round-4 preview (check 5, director-approved) FAILED a fresh harsh review, so no .blend is pushed.
- `review/preview.mp4` is the check-5 preview: 270x480, every 5th frame, with the VO.
- It was rendered from the exact packed build (77 MB, kept locally).
- The render check on that build PASSED: it opens cleanly, everything is packed, the camera and VO are present, and frames 1, 828 and 1655 rendered at full resolution in 60-74 s each with 16 samples. Copies are in `review/render_check_*.jpg`.

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
