# Part 1 storyboard — notes for the hub

* 53 shots, 2:38 at 147 wpm (VO split across shots is the script verbatim; checked word for word). Median shot 3.0 s.
* Frames: real Cycles renders of the 3D sets (half res, 24 spp), card + Courier Prime caption burned in as they will play.
* Shared library `mary_celeste_3d/lib` used unchanged. New assets in `mary_celeste_p1/p1/`: `smallboat.py` (16 ft ship's
  boat), binnacle compass bowl with smashed glass (`sets.compass_bowl`), galley and mate's cabin sets, logbook + slate props,
  X-ray hold cutaway and the 3D map (`explain.py`), Morehouse + 3 sailors (subclass of the shared Deveau builder).
* Atrium devices used: grey clay figures for the ten people only mentioned (S16), X-ray cutaway with dimension (S39),
  dark map with red hexagons and a dashed route (S43, S51-S53), filled soft orange bands as the only highlight (S11, S33,
  S38, S51, S53), ghost of the missing boat (S12).

## Needs a decision
1. **Card photos**: Wikimedia Commons and the Library of Congress are blocked by this environment's network policy, so the
   five cards (Deveau, Morehouse, Atlantic Ocean, Gibraltar, Santa Maria) show "PHOTO PENDING". Can the hub supply free-licence
   photos (with source + licence), or should I drop cards that have none (as killer-in-house did)?
2. **Render budget**: one full-res frame (2560x1440, 32 spp + OIDN) takes ~4 min on this 4-core CPU box. The part is ~3,800
   frames, so ~250 h in one session. Options: (a) split the shots across several render sessions (e.g. 10 sessions -> ~25 h);
   (b) 1920x1080 internal + upscale to 2560x1440 (~2.3x faster); (c) both.

## Known for the final pass
* Motion per shot: keyframed rigs (`p1/anim.py`: live armature, hair on the head bone, blinks), eased camera moves, ships
  worked by the sea (heave/roll), FFT sea advancing in time. S03 walk will be a short back-view step, not a full cycle.
* Beards read dark at half res; sails come from the shared ship (flat canvas look).
* SFX list per shot in `sfx_cues.csv` (every action has a sound); the delivered MP4 will be silent as asked.
