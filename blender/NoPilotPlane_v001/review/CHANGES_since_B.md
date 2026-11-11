# NoPilotPlane: changes since checkpoint B

## Director notes applied
- **Tail extended to frame 4410 (73.5 s).** The float-out starts at 71.4 s. The face is fully revealed by 72.6 s and settles by 73.5 s, with eyes widening and the jaw dropping.
- **Cockpit density and realism** (`02_build_set.py`, "cockpit density pass" and "realism details"):
  - Displays: six symbol-only screens (2 PFD, 2 ND, 2 EICAS) with no digits and no text. The PFD attitude square rolls and pitches with the flight, and the altitude and speed tapes scroll; both are keyed in `03_animate.py`. The screens have smudge and fingerprint roughness and a soft glow halo.
  - Glareshield: an autopilot panel with knobs, green segment windows and backlit keys, plus EFIS side panels. The top is a fabric texture, with master caution (amber) and master warning (red) lamps.
  - Overhead: enlarged to 1.15 × 1.6 m. It has 266 backlit buttons, 30 toggles (every third one guarded), rotary knobs, annunciator strips, module rails and screws.
  - Pedestal: radio heads, worn throttle knobs, flap and speed-brake levers, trim wheels with a white index mark, fire-handle guards, and a forward display. The paint is scuffed.
  - Yokes: ram's-horn shape with edge wear showing the metal, worn rubber grips, push buttons and a centre hub.
  - Window frames, rubber seals and sun visors. A seamed, grained liner on the cockpit walls. Bevels on all panel modules, plus screws and seams.
  - Props: a clipboard with a blank-lines checklist, a pen, two mugs in cup holders, and footrests under the panel.
- **Real model.** The procedural cabin seats are replaced on all 56 rows with "Seat" by maximmus (CC-BY, Sketchfab via Objaverse). "Airbus Cockpit Interior" was tested and rejected because of logos and readable text.
- **47–64 s dead air:**
  - The head looks around every 0.6–1.1 s: altimeter, side window, hands on the yoke, the empty captain seat, the field, the throttle.
  - Master caution flashes amber from 47.3 to 53.4 s.
  - 18 cloud puffs (54 cards) whip past beside the windows.
  - A flock of 22 birds crosses ahead at 57–64 s.
  - Gentle banks (±7°) sweep the sunlight across the cockpit, and the town and the long field grow closer.
- **Dive chaos (34–46 s):**
  - Stronger shake, with a strain tremor on the yoke.
  - Mugs, clipboard and pen float up, drift across the cockpit, tumble and drop at 40.4 s.
  - 36 oxygen masks drop in the cabin at 34.0 s and sway; they can be seen through the door on the look-back.
  - Master caution and warning lamps strobe red over the cockpit.
- **POV realism:** breathing sway on the camera at all times. The hands tremble on the yoke (4 mm jitter, 39–73 s) and grip the horns with a curl of 60–70°.
- **Door (12–14 s):** a 14 mm lens, YOU stops further back, the hand is in frame, and the door has inset panels, a kick plate and a blank placard.

## Fixes from my own review
- **Camera clipping into the first officer (29–33 s):** YOU now hauls from the left side, and the first officer is dragged to the right-rear corner. There are no black frames.
- **Sitting into the right seat (38–39 s):** YOU now enters from the aisle side, in front of the seat back. The black frame is gone.
- **Handset beat (21–25 s):** the handset is held forward and lower, so it reads in the hand in front of the mouth.
- **Look-back (64.6–68 s):** YOU now turns over the left shoulder. The shot shows the captain on the floor, the open door and the cabin with its masks.
- **Contacts:**
  - Slow foot slides between sparse IK keys are converted into quick lifted steps.
  - Footrests are under the panel, so the seated pilots' feet are planted.
  - Passengers sit 3 cm lower, so their shoes meet the floor.
  - The captain is lowered 4.5 cm onto the floor.
- **Logos:** the emblems are painted out of three MakeHuman shirt textures (`patch_logos.py`).
- **Exterior:** less haze, a wider and brighter long field placed so it fills the windscreen from 53.5 s, and a brighter cockpit fill and doorway fill.
