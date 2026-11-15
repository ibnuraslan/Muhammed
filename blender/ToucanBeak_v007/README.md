# ToucanBeak v007: director review of v006 (Connect28)

- **File:** `ToucanBeak_v007_60fps.blend`, packed, normal git file (no LFS).
- **Length:** frames **1–1750** (29.2 s, 60 fps); v006 was 2250 frames. `SETTINGS.md` has the new range.
- **Beats:** `beats.json` keeps the same order and words. Each beat has a new `frame`, and its old `frame_v006` is listed alongside. No VO has been added; the director syncs it.
- **Moving preview:** `review/preview.mp4`, rendered from this exact packed file.
- **QA:** `review/qa_v007.json`.

## How the re-timing was done
Every keyframe in the film was remapped by one piecewise-linear time map. The remap is in `ToucanBeak_v001/scripts/04_anim.py`, under `TIME REMAP`:

| v006 frames | v007 frames | Content |
|---|---|---|
| 1–676 | 1–676 | Unchanged, apart from the opening fix below |
| 676–1060 | 676–896 | The computer section: three cut shots |
| 1060–1340 | 896–986 | Beat 7 gag |
| 1340–1546 | 986–1106 | The printer (the cut back to the vets is at 1086, beat 9) |
| 1546–2190 | 1106–1750 | Shifted 440 frames earlier. The ending is cut 2 s after the swallow. |

## Director notes on v006 and the changes
1. **The computer section (12 s static) is now about 3.6 s in three cut shots.**
   - (a) 676–735: a medium shot of the vet at the monitor, from beside the screen. His face is visible and his hand is on the mouse. He now wears blue scrubs and stands closer, so his arm bends. Beat 5 lands here.
   - (b) 736–845: the screen fills the frame width. It shows the scanned half-beak with the reference beak, then the mirrored half snapping on, then the full beak turning to wireframe. Beat 6 lands here.
   - (c) 846–895: the vet turns from the monitor toward the printer.
   - **Beat 7 gag, 896–985:** VetB weighs a solid metal beak on his open palm, bouncing it twice and frowning down at it, with small head shakes.
2. **Printer, 986–1085:** a slow push-in while the beak builds up layer by layer on the bed (beat 8). Then a cut.
3. **Opening, 101–186:** the smash is framed at mid-range, so the shards fall away from the lens. The camera no longer drops to the floor. Deep focus is f/11.
4. **Hands, v006 1556–1700 (now about 1116–1260):** the camera is pulled back. Hands are hand-size and attached to visible people.
5. **VetB's stiff hold, v006 1741–1866 (now about 1301–1426):**
   - While gluing, his right hand steadies the new beak with its fingers on it. While pinning, the left hand does.
   - Both use `grip_object` on the prosthetic with a `cup_hold` pose.
   - His head tilts down, so his eyes are no longer rolled.
6. **Ending:** it now ends 2 s after the swallow, through the head-tilt (v006 2190). The 4 s hold is gone.
7. **Jungle cut-out, 491–501:** the shot holds on the bird and makes a clean cut to the clinic at 528. There is no blurred plant or fence fly-through.

## Checks on the packed file
- **Size:** 94.78 MB.
- **Factory-startup open:** 0 unpacked images, 0 libraries, frames 1–1750 at 60 fps.
- **Check still:** `package_check_lowres.jpg`, frame 897 (beat 7, the weighing gag).
- **qa_check** (`review/qa_v007.json`):
  - 0: CLAW, FAN, HOVER, FACEPRESS, BACKHEAD, ROLL.
  - CAMJUMP 8: exactly the intended cuts (528, 676, 736, 846, 896, 986, 1086, 1522).
  - PROPMOVE: intended moves (beak shards, the falling fig, the fig in the bird's beak, the printer nozzle, the glue bead), plus the small tweezers and pin flags reported earlier.
  - EMPTY / FILL / INSIDE: the same causes as before. The qa counts only human rigs as characters, and the camera sits inside the non-rendering dust-mote volume.
