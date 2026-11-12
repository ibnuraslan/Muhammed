# PopeShot: checkpoint C (new animated look + hands)

- `review/C_animlook_1ps.jpg`: 1 still per second in the new look. The director's time-saver dropped the 0.2 s sheet.
- `review/C_hand_closeups*.jpg`: 270×480 close-ups of every hand action (16 shots).
- Audits: `scripts/audit.py` (hover, sink, props, camera, head items) and `scripts/hand_audit.py` (every 2 frames).

## Changes since B
- **Look:** `pipeline/anim_look.py` (AgX Punchy, sky gradient, lower bump, f-stop at least 5.6, no motion blur). The x-ray dome is now the bright cyan-to-near-white gradient. Haze is cut to a trace, and the cell, shrine and theatre are relit high-key.
- **Square:** metal crowd barriers (linked galvanised segments), 80 crowd members in 4 rows each side, window surrounds with sills, lintels and pediments, and an attic balustrade on the facade. The jeep has no insignia.
- **Pope:** white robe, a fitted zucchetto and a gold pectoral cross on a chain. Fitted shells are now built from the shape-key-baked body, which fixed the floating cap.
- **Shot:** the pistol (seen from behind) rises from the crowd and fires one muzzle flash, then the slow-motion bullet travels to the x-ray porthole. There is no blood and no wound. The hand x-ray is framed with the whole raised arm and the aides, so no hand floats on its own.
- **Theatre:** the drape is fitted over the patient. Surgeons have fitted caps and masks, and thin latex gloves that are shells of the MPFB hands, not blobs. The lamp-filled frame was reframed.
- **Cell:** the men now face each other (they faced away in B), and the hand rests on the shoulder.
- **Shrine:** the Pope stands in prayer (the kneeling cassock read as a tube). The bullet sits visibly on the front of the crown. The camera path now goes around the statue.
- **Hands:** Limit Rotation on every finger, thumb and wrist (2,880 constraints) and relaxed default curls. Grips were added for the pistol, the aides' catch, the bullet pinch, the blessing (two fingers up) and the prayer hands. Hands were moved off clothing, thighs and the patient wherever the audit flagged them.

## Audit
- Props/camera audit (every 20 frames): camera inside geometry 0, fingertips inside props 0.
  - 58 "hover" flags are the aides at the jeep bed edge; the bed floor plate has since been enlarged.
  - The head-item flags are small edge-vertex counts on the caps and masks.
- Hand audit (every 2 frames, 801 frames): see the D message for the final count. The first full pass found 1,136 hits, almost all of them:
  - the aides' grip intended to hold the Pope's torso (contact depth)
  - the seated prisoner's hands on his thighs
  - one standing hand into the jacket hem

  These are re-keyed in the build that goes into the D package.
