# Changes since checkpoint B

- **Arms:** the hanging-arm pose moved 5 cm forward and 3 cm out, so hands no longer tuck behind the hips on stocky bodies. The would-be assassin's hand-in-coat moved up to the chest and now reads in close-up.
- **Map:** the fire-front glow is a narrow band (about 28 frames per spot) instead of a wash. Burned land is dark scorched red-brown with sparse glowing embers. Smoke plumes are lighter and thinner.
- **Packaging:** `07_slim_textures.py` sets skins to 2K JPEG and scales other textures above 1K down to 1K. The packed file is 168 MB → 119 MB.
- **Camera** (from B round 3): the rewind now passes over the reversing car before sweeping east, the bomb landing is framed from the north side, and the post-blast orbit is wider.
- **Parasol:** it is now furled, tilted back and held in her left hand, so it no longer covers faces.
- **Camera:** new keys arc over the driver (3.4 s), in front of the car (4.95 s) and around the gunman's head (24.55 s), so the camera no longer passes through people. Push-in to 65 mm behind the gunman. Post-blast orbit is low at 17.1 s and high at 18.1 s. The map end orbits instead of holding.
- **Explosion:** smaller orange fireball, lighter smoke that rises faster, debris hidden below the ground until the blast.
- **Map:** dark scorched land with saturated orange fire patches. Flags are 5× larger. Plumes are soft alpha wisps instead of volumes: the volumes cost about 85 s per preview still versus 9 s now.

## Audit (review/C_audit.txt)
- **Camera vs. café:** the café "CAM_IN" flags at 5.3–6 s are false positives. That building's bounding box includes its roof cornice overhang, and the camera is 35 cm outside the wall.
- **Foot sink:** worst 4.4 cm, on three crowd people at frames 1591+. Everything else is within 2.5 cm.
- **Wheels and hands:** wheels are within 3 cm of the road. The driver's and the couple's hands meet their IK targets within 6 cm at every sampled frame.
