# AIAsleep: changes since checkpoint B

- **Beat 9 cross-section built**: a sagittal slab through the upper lid near the inner corner, with skin, orbicularis muscle (fibrous), orbital fat (lobular, wet), tarsal plate, orbital rim bone (porous) and eyeball (sclera, vitreous, cornea, lens, iris). It sits on a deep teal-to-navy studio gradient with its own key/rim/fill lights. The camera dives through the skin at the inner corner in ≤6 frames, orbits the section (5 framings), then exits back to the surface macro.
- **Epicanthic fold**: a corrective shape key on the upper-lid skin near the medial canthus (both eyes, 144 verts). The skin droops 2 mm down and toward the nose over the inner corner. Normal aperture, no caricature.
- **Hands on the wheel**: the audit found the arms couldn't reach the rim, so the hands were floating about 11 cm short. The driver now sits 11 cm further forward and the wheel column comes 6 cm toward him. All hand samples are now within 3.5 cm of the rim.
- **Eyeball crumple fixed**: the eye mesh was weighted to the lid bones, so lid animation folded it into a dark scribble at the inner corner. It is now weighted to the head and eye bones only.
- **Face-only scan mesh**: the scan wireframe is masked to the face (no scalp), at lower intensity.
- **Camera**: face-relative keys follow the driver's new head position. A per-frame ray-probe clearance check (`scripts/cam_clearance.py`) now runs. All blank frames are gone (4.2 s, 15.4 s, 27.4–29 s, 41.2 s), and so are the clips through the passenger seat, shirt, rear-view mirror and headliner.
- **Look**: the background seen by the camera is now a dark night gradient plus the CC-BY city model. The HDRI skyline (lit signage) only lights the scene. Skin pore bump is reduced for the macros. Brown irises, black hair and warmer skin are kept.
- **DOF**: f-stop keys are linear (Bezier overshoot was causing extreme blur at 27 s).
