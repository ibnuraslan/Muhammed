# ShoeBomber: checkpoint C (polish)

Look at these files:
- `review/C_polish_0p2s_part1.jpg`, `part2` and `part3`: a still every 0.2 s (0–9 s, 9–18 s, 18–27 s), 270×480, 8 samples.
- `review/C_audit.txt`: output of `scripts/audit.py`. It samples every 10 frames and groups the flags into frame runs.

## What changed since B
- **Beat 1:** the camera is restaged from the empty middle seat (the passenger who was there moved to the aisle seat). The match hand now sits above the shoe tongue. The flame burns upward in world space at twice the old size and warm-lights his hands. The sneakers are on his feet, with the foot mesh masked inside them (in B they rendered behind his heels).
- **Beat 4:** the trolley gets bumped forward in the lunge. The tackle and pin now use high angles over the pile instead of floor level, which looked up the skirt and hit bodies in B.
- **Beat 5:** the steward faces the bomber and kneels on the seat-row side. The syringe is held in his hand at the bomber's evaluated upper-arm position, where in B it floated near the head. The camera shows his sleeve and the needle from the side, then rises.
- **Beat 6:**
  - The attendant walks to his feet with a real walk cycle (no slide).
  - The extras clear the aisle: one passenger backs off and one sits back.
  - The fuse cords are light tan and poke out of each heel sole. She holds the shoes sole-up to camera.
- **Beat 7:** the grey putty slab is lightened and raised so it reads in the cutaway. Its highlight is a thin glowing wire edge, where in B a glossy shell covered it.
- **Beat 8:** the opening framing was inside an engine nacelle in B. It now starts forward of the wing, beside the fuselage. The cloud puffs no longer pass through the camera.
- **Beat 9:** the airport is darkened (floor, ceiling and light levels). The ending now settles on the traveller's face from above the belt.
- **Contact:**
  - An automatic reach pass slides each helper's body (horizontal only) so their IK hand targets are reached at every keyed frame.
  - MPFB shoe soles are lifted 2.4 cm off the floor.
  - The lying bomber is raised so his chest doesn't sink into the floor.
  - The PaxC and PaxD hands hold their pose until the hidden cut to the airport (in B they drifted across the gap).

## Audit summary (`C_audit.txt`)
- **Camera inside geometry:** none.
- **Sink:** the steward, 10 cm for f541–561 only, mid-run as he arrives.
- **Hover:** the lying bomber is now a few cm too high (f531–1061, max 18 cm during the fall itself), and the kneeling attendant's knees sit 4.5 cm up. Both are being corrected now.
- **Reach:**
  - The biggest misses are in fast transitions: the running steward (f451–521) and PaxB standing up (f461–581).
  - In holds, the attendant's grip on his raised wrist misses by up to 0.2–0.4 m (f501–761).
  - The bomber's own left hand behind his back misses by 0.18 m.
  - The officer at the desk misses by 0.17 m.
  - The traveller reaching his heel misses by 0.22 m.
- **Prop:** the traveller's right shoe is 0.35 m from his wrist while he carries it (f1451–1511). It reads as a lift-and-drop. Being fixed.

## Known issues / unsure
- The traveller ends barefoot rather than in socks.
- The cabin smoke is a low-density volume; at 8 samples it shows as grain on skin.
- The trolley reads dark.
- The cloud puffs in the sky beat are still lumpy.
