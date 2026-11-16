# B27 ChicagoRaised v002b: changes from v002 (director review, Nov 16)

Same timing, frame range (1–1923) and beats as v002. Only these shots changed. Their ranges were re-rendered from this package and spliced into the v002 preview frames (`preview.mp4`, `pages/`).

| Note | Shot | Frames | What changed |
|---|---|---|---|
| 1 | S21 | 1427–1592 (re-rendered 1426–1596) | The red brick block rises 1.6 m out of the waterline to the new street level: the foundation grows under it and the building lifts. A townsman wades past in front, close to camera. Push-in with a slight tilt-up. |
| 2 | S17 | 1194–1265 (1191–1266) | Knees-up framing: the man wades toward camera, and the camera eases back. |
| 3 | S20 | 1380–1426 (1376–1426) | The woman walks toward camera and fills about half the frame height, with the horse behind her. |
| 4 | S6 | 557–688 (556–691) | She looks around: right, then back toward the window. Her hands leave the book and grip both armrests as the room lifts. 3/4 angle with a slow push-in. |
| 5 | S8 | 689–805 (686–806) | Higher camera, so his hands and arms on the timber are visible over the stack. Push-in. |
| 6 | S12 | 885–952 (881–956) | Low push-in with a tilt-up from the foundation to the facade. The logo sign stays above the frame and is never cut. |

## Checks on the changed ranges (this package)
- `clip_scan` 556–806 and 1426–1596: 0 bad ranges. The 1191–1596 range (S17–S21, before the final S21 camera and walker change) was also 0.
- `body_prop_cross` S6:
  - Seated thighs in the cushion, and the book resting on her lap.
  - Fingertips on the armrests.
  - These are all resting contacts, the kind you accepted as contact.
- `limb_check` S6: 2 points at each shoulder, the known shoulder false positive.
- The crank shots (S1–S7) are unchanged from v002: `body_prop_cross` 0 crossings, see `../ChicagoRaised_v002/review/`.
