# ToucanBeak v006: director review of v005 (Connect28)

- **File:** `ToucanBeak_v006_60fps.blend`, packed, normal git file (no LFS). Same format as v005 (`SETTINGS.md`).
- **Unchanged:** story-beat frames (`beats.json`). No voiceover has been added.
- **Moving preview:** `review/preview.mp4`, rendered from this packed file (`preview.py`, every 5th frame, then `watch_pages.sh`). Every page was watched.
- **QA:** `review/qa_v006.json`.

## Director notes on v005 and the changes
1. **The "computer rebuild" (751–1546) was 3D models floating in a void, with blank frames.** It now plays on the clinic monitor.
   - **Camera:** in the room, beside the assistant at the desk. He turns his head to the monitor, so his face reads in three-quarter profile on beats 847 and 1063.
   - **On screen, in sequence:** the scan, the new beak, the heavy/light-beak demo bird, then the hollow cutaway (beat 1351).
   - **How:** the monitor's screen looks through the wall onto the void set. Every frame, the void set is moved so the old shot sits behind the screen, as seen from that camera. It works as a live 3D display, with no void and no blank frames.
   - **Then a cut at 1421** to the real 3D printer, standing at real size on the clinic side bench and printing the beak (1421–1545).
   - **Timing:** the section keeps its length. The beat frames 847, 1063 and 1351 lie inside it and must not move, because the VO is synced to them. It is now one continuous shot in the room plus one printer shot.
2. **606–746 showed only hands, and the desk push ended on a black frame edge.** The 636–672 framing now looks over VetB's shoulder at VetA's face and the bird. The camera then turns to the assistant at the monitor and stays in the room, so the black edge is gone.
3. **1546 showed a grey arm and an empty room.** Hard cut at 1546 straight to a framing of both vets.
4. **1756–1846 had giant gloves and a dark forearm in the frame.** The camera now stands beside VetA. VetB's hand, the syringe or tweezers, the beak and his face read together.
5. **FAN (splayed fingers on the grips).** `grip_object` places the hand, then a closed, even preset with spread 0 is keyed: `wrap_grip` for the scanner and the prosthetic, `pinch` for the syringe and the tweezers.
6. **1946–1971: the camera flew through the door frame.** Clean cut at 1962 to the garden.

The intended cuts are at 1421, 1546 and 1962, as the director asked. qa_check's CAMJUMP flags these frames and no others.

## Found while watching the first v006 preview, also fixed
- **Packaging bug: the assistant's hair rendered as a bald, spotted scalp.** This was also in earlier packages. `06_package.py` de-duplicated images by hashing only their first 4096 pixel values, which is the transparent corner of every hair or lash cut-out. Different cut-outs were therefore merged. The hash now samples the whole image, and alpha mode is part of the key. To stay under 95 MB, JPEG textures are now saved at quality 78.
- **The horizon tilted up to 37° at 682–703 (qa ROLL).** The v004b flip fix (660–710) carried an old orientation into the new camera path. It has been removed, since the new keys never look straight down.
- **Beat 679 showed the back of VetB's head (qa BACKHEAD).** The 672 framing is now from beside VetA, with VetB's face and the bird in frame.
- **An unintended camera flip at 1566 (qa CAMJUMP, 121°).** The old high key at 1575 looked straight down at the seam. It now frames the seam from the front-left.

## Found while watching the second v006 preview, also fixed
- **A black frame at 686.** The move from the vets to the desk ran straight through VetB's body. It now holds VetB's face through the 679 beat, then moves over the table and clear of both vets (keys 681/693/706).
- **The prosthetic grip.** The closed `wrap_grip` read as a fist on the bird's head while the beak was seated. It is now the library's `cup_hold` (spread 0). The scanner keeps `wrap_grip`; the syringe and tweezers keep `pinch`.

## Checks on the packed file
- **Size:** 94.88 MB.
- **Factory-startup open:** 0 unpacked images, 0 libraries, frames 1–2250 at 60 fps.
- **Check still:** `package_check_lowres.jpg`, frame 1063 (the beat, with the model on the monitor).
- **qa_check** (`review/qa_v006.json`):
  - 0: CLAW, FAN, HOVER, FACEPRESS, BACKHEAD, ROLL.
  - CAMJUMP 3: only the three intended cuts (1421, 1546, 1962).
  - PROPMOVE: intended moves (the beak shards, the falling fig, the fig in the bird's beak, the printer nozzle, the glue bead), plus the two small tweezers and pin flags reported in v005.
  - EMPTY / FILL / INSIDE: the qa counts only human rigs, and the camera sits inside the non-rendering dust-mote volume. These are the same causes as before.
