# v011 check 3: the director's final round (restage), watched start to finish

`preview.mp4` is now the check-3 preview of the packed `BeethovenDeaf_v011_60fps.blend`: every 5th frame, 270x480, with the VO. All 6 pages watched.

## Director's four points
1. **Hands.**
   - One arched pianist pose. The palm sits over the key fronts (1.5-2 cm in, 7 cm up), the fingers are pitched down, and only the fingertip pads touch the white keys.
   - The black keys start 7.2 cm back, so the knuckles never reach them.
   - Small finger presses: each key hinges down 3.6 degrees and its finger follows it.
   - The camera shows the hands in side mid-shots.
   - Mesh audit (`scripts/key_contact_check.py`, every 4th frame, subdivided deformed mesh):
     - worst hand-into-key depth **2.55 mm** (frames 65-81)
     - 47 of 359 sampled frames over 1 mm, most of them 1.0-1.5 mm (fingertip pads at interpolated frames)
     - no knuckle intrusion into the black keys (check 2 had 2-15 mm on every frame)
2. **Mouth.** The lips close round the rod with the jaw slightly clenched, and the incisors grip it inside. There is no dark "O".
3. **Framing.** His face is in frame through 151-196, with headroom on the rod ride 251-330.
4. **Ear close-up (800-950).**
   - Tighter: 70-78 mm, from slightly below to cut the hair.
   - Coloured parts: a warm canal, a dull grey torn eardrum where the red pulse dies, gold ossicles, a violet labyrinth and yellow nerves.
   - The cyan path bypasses the eardrum, and the cochlea lights up on "hear clearly".

## Still visible (honest list)
- At preview size the hands are small and read as compact pianist hands, not open fingers.
- The hair is the CC0 MakeHuman "short messy" card hair, recoloured grey. It reads slightly papery.
- In the x-ray the skull is pale cream. The top half of the 800-950 close-up is still hair, softened by depth of field.
- 101-111: his head sits at the left frame edge for about 0.2 s.
- 1121-1146: candles on the candelabra pass through the foreground (his face stays visible).
