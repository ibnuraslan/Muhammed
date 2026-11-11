# DonationBin: changes since checkpoint B

## Contacts and acting
- **Tiptoe (beat 1):** the toe pitch sign was inverted, so both feet hovered 15–19 cm. The toe balls are now planted (about 1 cm) with the heels lifted.
- **Body-relative limbs:** curled, lying and tumble hands and feet were offset from the A-pose rest, which put them about 0.8 m out, through the bin walls. In beat 8 she now curls in a real fetal pose, hands at her chest and knees drawn up.
- **Walkers:** the shover, passer-by and firefighter now swing their arms. Before, their unkeyed IK hands were left at the origin.
- **Scream (beat 7):** the hands are cupped at the corners of her mouth instead of raised above her head.
- **Pushing the flap (beat 5):** her palms sit 2 mm off the flap's inner face (they used to sink in), and she leans less, so her head no longer reads through the x-ray front panel.
- **Passer-by (beat 9):** he walks in facing his direction of travel, as he should; before, his walk yaw was wrong. He stops facing along the wall with his right ear turned to the bin, knocks with his right hand on the steel, steps aside for the firefighters, then watches.
- **Firefighters (beat 10):**
  - Both wear tan turnout colouring with reflective bands, and their helmets now sit on their heads.
  - FireA cuts standing, both hands on the cutter. When the cut finishes he steps aside.
  - FireB grips the panel's top edge and pulls it down. The panel now **folds down onto the asphalt like a ramp**; before, it swung through the camera. Daylight floods into the bin.
- **Blanket (beat 11):** it was a grey cylinder. It's now a copy of her torso and arm skin, masked by bone weights and inflated with folds in grey wool, so it moves with her. Her hands hold it closed at her chest.

## Camera (still one continuous spline; collisions removed)
- **Beat 2:** rises over the shover's head instead of passing through it.
- **Beat 3:** the landing is seen from her head side and from above, not from between her legs. A new key at f470 takes the camera over her as she sits up, so it no longer passes through her body.
- **X-ray fade:** starts at f492 so the right wall is already a ghost as the camera passes through it.
- **Macro (beat 5):** the camera now slides along the stop bar (f805→835→870) instead of holding.
- **Wall pats (beat 6):** the camera orbits from behind her round to her palms.
- **Scream:** the key that sat inside the front wall has been moved out.
- **Beat 9:** exits the chute below the hood and frames the passer-by's face and the knock without touching him.
- **Beats 10 and 11:**
  - The camera stays clear of both firefighters and the folding panel.
  - It pulls back ahead of her as she climbs out.
  - The final crane keeps drifting to the last frame, with no hold longer than 1 s.

## Look
- The interior fill and exposure are lifted. The night time-lapse gets a dim blue fill and a moonlit slot.
- The cut-line glow is now one continuous strip.

## Package (for D)
`04_package_prep.py` drops unused displacement and anisotropy maps and downscales textures to 1K (2K for hero maps), saved as 8-bit JPEG unless the alpha is real. A test package came to 70 MB, opened in factory Blender with 0 unpacked images and one camera, and rendered.
