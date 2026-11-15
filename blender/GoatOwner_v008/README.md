# GoatOwner_v008: director notes on v007 (Connect32)

This is v007 (17e669c) with the four director notes fixed. Beat frames (`beats.json`) are unchanged and no VO was added.

## 1. The ending (f1906–2190)
- **Her stroking hand rests on the goat.** Her left palm lies flat on the fur on top of its head and strokes back toward the neck and forward again, with the elbow bent and relaxed.
  - The palm is placed on the goat's real surface each key, not a hover point.
  - Before this, her arm was held straight out, hovering above its head.
- **Her other hand rests on her raised front knee**, palm down with the fingers over the knee. Before this, it was held up near the goat's chin.
- **Her face reads.**
  - Her head is lifted. The camera now settles three-quarter front (keys 2140 and 2190) with her face and the goat's head both in frame.
  - She has a soft, closed-mouth smile: the mouth corners are back and up, the cheeks lifted, and the lips closed.
  - On this rig the mouth controls are weak, so the smile reads as calm and content rather than a broad grin (see `face_2150.jpg`). A stronger smile would need face shape keys.
- **Brighter.** The golden-pasture sun and sky are about a third stronger (sun 3.6→4.8, sky 1.0→1.4), and the sun sits slightly higher.

## 2. Goat alone (f281–716)
The owner now reads in the background for most of this stretch.
- On the porch he turns back and raises the stick at the goat again, shaking it (f398–436). Then he goes inside (f437–460).
- The camera at f390–445 is behind the goat looking past it at the porch. A new tracker (`go`) frames the goat in front and the owner behind it.
- His walk to the porch is a little brisker, so that it ends by f392.
- A new key at f355 keeps the camera wide round the goat and clear of the shed.
- The goat is briefly cut at the right edge at f361–376, as the camera turns to the porch.

## 3. The dark square on the ground (f501–596)
These were the hard shadows of the **shed and house** under the low time-lapse sun, sliding across the yard.
- Shadow casting from the shed, the house and the porch is keyed off during the time-lapse only (f464–628). Hiding all large objects in a test render removed the patch, and bringing back the shed group alone brought it back.
- A low drifting-dust volume in the time-lapse was also removed, and the drift puffs no longer cast shadows.

## 4. f801
The whip turn's path passed 0.35 m from the goat's head. A new key at f803 swings the camera wide round it, so it now stays 1.1–1.8 m away. The turn is now slow enough that it no longer needs whip easing.

`GoatOwner_v008_60fps.blend` is 69 MB: packed, compressed, and a plain git file.

## Files in `review/`
- `preview.mp4`: the moving preview, every 5th frame at 12 fps (real speed), 270×480 with 8 samples.
- `pages/p01–p09.jpg`: contact pages of every preview frame.
- `ending_2000_2120_2189.jpg`: the ending at 540×960.
- `face_2150.jpg`: a close-up of her smile.

## QA (qa_check on the packaged file)
- CAMJUMP 0. BACKHEAD 4 and INSIDE 3 are the same as v007.
- EMPTY fell from 224 to 207.
- PROPMOVE 228 is dust puffs and clods waiting under the ground (see v006c). The stick is never flagged in the air.
