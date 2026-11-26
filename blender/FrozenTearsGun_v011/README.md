# FrozenTearsGun_v011: from-scratch rebuild, NOT READY (ON HOLD)

**Status: ON HOLD.** Self-QC check 3 FAILED a fresh harsh review, and the two fix rounds the rebuild brief allows are used up. No .blend is pushed. `review/preview.mp4` is the check-3 preview (270x480, every 5th frame, with the VO), rendered from the packed local build (77 MB).

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
