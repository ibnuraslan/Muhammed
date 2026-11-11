# Checkpoint C: SwedishCoffee

Sheets: `C_polish_0p2s_part1..4.jpg` (every 0.2 s, 270x480, 8 spp; part1 = 0–12 s, part2 = 12–24 s, part3 = 24–36 s, part4 = 36–44.4 s).
Audit: `C_audit_step30.txt` (every 30 frames, run on the 23:43 build).

## Changed since B
- Portals: set changes now pass through real window/door openings (chamber window, ballroom doorway, bedroom window), with houses outside the windows. The camera approaches walls only for the last ~7 frames (auto keys at f-7 / f / f+18).
- Period costume: long-sleeve MPFB garments recoloured as frock coats with stockings below the knee. Sleeves no longer take the breeches colour (body-centre mask). Townswoman's shorts were replaced by a skirt.
- The king's powdered wig sits on the head (Child Of head bone); props stay on the hands after the set-root parenting fix.
- Finger grip (curl) on cups, pots, coffin handles and toast cups.
- Twin B lies in the bed under a velvet blanket, arms at his sides; twin A at the bedside, chair moved back so the knees clear the bed.
- Lighting: the chamber and bedroom are brighter (fill/rim, window key), and the world strength is keyed per set.
- Camera: fixed the floor-only whip frames at 6.4 s, 20.8 s, 24.2 s and 26.2 s; the camera no longer grazes the servant, the coffin bearers or the bedpost.
- File size: GLB textures go to 512/1K JPEG and props over 25k faces are decimated. MPFB helper shape keys are baked. Beans and snow are deterministic geometry nodes (no particle cache).

## Fixed after these sheets (in the build now, shown at D)
- The young→old twin swap moves to f1440, while the camera is on the doctors (it was visible at 24.6 s).
- Black coffee surface covers the latte-art texture inside the cup model.
- The church façade is now sun-lit; the flash puff is smaller and less white; the armchair now faces the camera (it showed its back at 37–41 s).
- Hands resting on tables are raised (audit HAND_PEN on twins/doctors). The guard holds his position after running out. The square walker no longer walks through a stall.
- Ermine capelet for the king; background walkers in the courtyard, street and square.

## Audit summary (23:43 build)
- CAMERA_INSIDE 0.
- HAND_PEN 203: twins/doctors' fingertips 1–2 cm into the tabletops (fixed above); soldier's hands inside the pot he holds (expected grasp).
- FOOT_HOVER 51: almost all were swing feet of walkers and bearers. The rule now flags only when the lower foot is off the ground. One real case: Guard_S2 after the run (fixed).
- FOOT_SINK 2: the square walker through a stall (fixed).
- HEADITEM_GAP: the metric was wrong (bounding-box corners). It is rewritten as nearest-vertex-to-head-surface for D.
