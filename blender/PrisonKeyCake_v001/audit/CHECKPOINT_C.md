# PrisonKeyCake checkpoint C: polish

Sheets: `stills/polish_C_0.jpg` … `polish_C_3.jpg` (one still every 0.2 s, 158 stills, 270×480 at 8 samples; each sheet covers 8 s).

## Audits
- `audit/camera_C.txt` (`scripts/audit_camera.py`, every frame, 14-direction ray casts): **0 frames inside geometry**.
  - Frames 363 and 893 are the deliberate fly-throughs between the window bars (about 5 cm).
  - Frames 935–942 hold the camera 7–8 cm from the cell's east wall during the jam close-up.
- `audit/contacts_C.txt` (`scripts/audit_contacts.py`, every 2nd frame, all 7 IK characters):
  - **No foot sinks or hovers** (sole offset measured per character).
  - What remains are IK reach gaps of 3–16 cm, lasting a few frames during transitions. They are listed in `../PrisonKeyCake_v002/README.md`.
  - The sleeping guard's left hand rests 4 cm off its target.

## Changed since B
- **Bugs fixed:**
  - The lock, bolt and grille had been parented before the door pivot updated, so they sat on the table. They are now on the door.
  - The foundry key path read the cake position after the cake was baked, so it flew toward the yard. It now goes into the cake.
  - The guard's hands were crossed on the box.
  - The second key started from a pocket position while he was across the cell.
- **Contact:**
  - Every character gets a standing height from its own rig and a sole offset from its shoe mesh, so feet no longer sink 2–3 cm.
  - The hanging-arm pose was raised so hands reach their targets.
  - More lean was added where reaches were short: lifting the key, pulling the key from the cake, the crucible, the cake.
- **Beat 7:**
  - The second press is retimed to start after he reaches the table.
  - The tin goes out of the window: he leans over the table, sets it on the sill, and it is taken from outside.
- **Corridor:**
  - Each gate is now a double gate (two 0.88 m leaves), so the open gates no longer block the exit or cut through the sleeping guard. The guard and his stool moved to x = 6.1.
  - The camera now passes over his head instead of through him.
- **Life:**
  - Two prisoners walk the exercise yard and a guard walks the north wall by day.
  - A lantern patrol crosses the night yard.
  - Five pigeons circle the yard; nine burst off the government steps at the reveal.
  - The laundry hangs from a rope, in varied colours.
- **Beat 10:**
  - The government building and its flags are hidden until the reveal. They no longer show over the prison wall at night.
  - The sun was re-aimed onto the facade, the stone brightened and the windows turned to dark glass.
  - The older man's hair is grey and his left arm hangs naturally.
  - The crowd moved forward so it stays in frame, and the end framing was lowered.
- **Light:** the night cell is brighter (candle, fill, moon and window light raised; night exposure +0.9), and the pour glow is reduced.
- **Package:** `05_optimize.py` downscales character textures to 1K (hero skins 2K) and drops dead displacement chains. Size went from 211 MB to 139 MB.
