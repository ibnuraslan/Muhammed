# SurgeonBrandsLivers_v014: fixes for the director's 18-point v013 notes and the follow-up passes

- **Timing:** same voiceover, timing and frames as v011–v013: **1–1644 at 60 fps**. The VO is packed from frame 1, and the same mp3 is in this folder.
- **Cuts:** hard cuts between locations.
- **Build:** `blender/SurgeonBrandsLivers_v001/scripts/build_v012.sh`, which runs scripts 20, 21, 25, 22, 24 and 23 on the v011 file, then `pipeline/package_for_farm.py`.
- **Review:** `review/preview.mp4` is every 5th frame, rendered from this exact packed file, with the VO. Every frame of the preview was watched. In addition, every single frame of the mask shot (430–570) and of the defendant shot (1311–1445) was checked.
- **Check results** are in `review/`: `clip_scan.json` and `body_prop_cross.json`. Those two checks were run on an earlier build of this package, not this exact file; the frame-by-frame checks above were. What they show is listed under "Known".

## What changed since v013
- **Core beat:** the "SB" is burnt into the liver as crisp, legible charred letters. It is revealed by the burn front, which follows the pen tip, and a bright blue emissive argon jet with its own light shows while burning. The letters stay legible in the reveal, and the camera pushes in on them.
- **Opening:** the camera is reframed below the OR lamps. The drape is lowered, so the patient's body reads under it, and the camera is closer on his hands and the open abdomen.
- **Closing:** the wound visibly draws shut over about 1.3 s, then the stitches go in.
- **Scrubs:** real cloth garments, not body copies.
  - Surgeon 1 wears a top with long sleeves to the wrist, built as one mesh with the top, so no shoulder gap can show.
  - The nurse and the anaesthetist wear soft fitted tops.
  - The second surgeon wears a loose flat-front top with a smooth V-neck.
  - Everyone wears straight-leg trousers.
  - The skin under the clothes is masked, so nothing pokes through.
- **Mask beat:** a face close-up (430–496) as the mask comes down to his chin, then a hard cut to a medium shot (497–570). His hands are already at rest on the drape at the cut, and the mask is at his chin in both shots.
- **Calendar:** no flapping or popping pages.
- **The woman:**
  - Natural arm swing as she walks.
  - The glow fades in inside her abdomen.
  - Her hand presses on her shirt.
  - Her arm no longer clips her body.
- **Bed shot:** she is on the bed from the first frame, in her own clothes. The nurse grips the head rail, and the doctor walks beside the bed.
- **Second surgeon:**
  - Calm arm swing; her hands rest on the drape, then she lifts the liver.
  - Her face is under the cap, with head moves and blinks.
- **Hearing:**
  - A medium shot on the judge as he speaks, with nobody cut at the frame edge.
  - The defendant (the same man as the surgeon) has his arms at his sides and wears a dark navy fitted sweater. He is framed in a tight close-up from the collarbone up, and he talks and blinks.
  - One liver graphic only.
  - The judge's left hand lies flat on the desk.
- **Gavel:** lies across the desk; it is gripped, lifted and struck.
- **Stamp:** gripped, pressed and set down. The red X appears only once the stamp is down.

## Known
- `clip_scan` flags the surgeons' hands inside the open abdomen at 1–7.2 s and 17.6–19 s, which is intended (they are working in the cavity). It also flags one sample frame each of the walks.
- `body_prop_cross` flags the fingers wrapped round the gavel and stamp handles (grips) and the patient against the table pad.
