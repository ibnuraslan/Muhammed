# ShoeBomber v011, check 1: FAIL (fresh harsh review)

`preview.mp4` at the time of this check was rendered from the packed `ShoeBomber_v011_60fps.blend`, at 270x480, every 5th frame, with the VO.
I watched every contact page, and a fresh reviewer gave a harsh PASS/FAIL on all 13 pages: **FAIL**. No .blend was pushed.

## Faults the reviewer found that I verified (times in seconds; frames are film frames)
- **Fuselage logo missing in the farm/preview settings, 16.4–18.4 s.** The shrinkwrapped decal collapsed under render Simplify. Fix: bake the decal mesh.
- **Skin between the sweater hem and the trousers while he lies prone, 7.6–10.5 s.** This is a nudity read. Fix: the trousers rise higher under the sweater.
- **Grab, 6.6–6.9 s:**
  - PaxA's left arm bends back over his own shoulder.
  - The bomber's hand sits at his hip.
  - Fix: both of PaxA's hands go on the bomber's upper arm, and the bomber's hands come up in front of his chest.
- **The tackle is not shown.** The camera whipped away during the fall. Fix: he turns and drops to his knees on screen (6.9–7.2 s), and the reaction shot then covers only the last part of the fall.
- **The flex cuffs are hidden inside the sweater sleeves.** Fix: bigger loops, placed on the wrist past the sleeve.
- **Tray logo cut by another tray's wall, 19–20.4 s.** The stacked trays overlapped his tray. Fix: the stack moves to the belt start.
- **Match flame small, 0–2.5 s.** Fix: a bigger flame and a stronger glow.
- **Dark eye sockets on the bomber, 0.4–0.7 s.** Fix: a camera catchlight.
- **The explosive reads as butter.** Fix: a grey-olive putty slab (still abstract, per the brief).
- **Socks read as blue skin.** Fix: darker socks.
- **The shrug used splayed fingers.** Fix: relaxed open palms.

## Not reproduced
- **A black shoe silhouette at frame 976 (16.27 s).** Renders of frames 971, 976 and 981 straight from the package (both with and without Simplify) are correct. I'll recheck it in the next preview.

## Known and not changed
- The attendant's face reads doll-like (MPFB face).
- The plane model is plain white with no windows.
