# body_prop_cross results (P1 after director round 1, provisional timeline 1–3822)

- **Script:** `pipeline/body_prop_cross.py`. A copy that takes an explicit frame list and prints each body part / prop pair was used.
- **Frames checked:** every 8th frame of the film plus the first, middle and last frame of every shot (540 frames).
- **Earlier, denser runs on the re-staged shots:**
  - every 2nd frame: 5b and 6a;
  - every 3rd frame: 5b, 5c and 5d;
  - every 5th frame: 1c;
  - every 10th frame: the cell shots.
- **Props checked:**
  - **Handled props:** the spoons, the drill copies (motor, fan, bit, cord), the flashlight, both grilles.
  - **Bed and furniture:** the dummy head, blanket, roll and pillow; the mattress, bunk frame, stool, table, basin and rim.
  - **Cell and corridor:** the cell's back wall and bars, the corridor's vent wall, far wall and duct, the crates.
  - **Shaft and outside:** the stair treads and stringers, the vent pipe.
  - **Raft:** tube, floor and rope.
  - **Floors:** the cell, corridor and shaft floors.

## Result: 0 visible crossings in all 24 shots

The only hits left are 4–8 edges labelled `root` in 1a, 1b, 1c, 5d and 6a. They are a known false positive:
- `body_prop_cross` turns off the MPFB MASK modifiers, which exposes the hidden helper geometry, and those helper vertices are labelled `root`. LESSONS §3 notes the same for `clip_scan`.
- Re-checked with the masks on (the rendered mesh) on those frames against the floors, the stool and the stair treads: no body edge crosses anything.

## Staging changes behind the result
- **Feet and floors:**
  - All feet are lifted 1.5 cm, because MPFB shoe soles sit below the rest ankle height. P3's shoes03 get 3 cm.
  - Kneelers' knees and tucked toes sit about 1 cm off the floor.
- **1a:** the spoon rests on P1's open palm. P1 sits slightly higher on the stool; P2 and P3 stand 8 cm further back.
- **1c (wide):** P1 kneels at the vent and studies it, hands on his thighs; the scraping starts in 2a. No spoon grip at this angle passed the check.
- **2a–2d:**
  - The spoon is pinched. The grip stops 1.3 cm off the spoon, and the spoon is seated 1.7 cm along the wall (tested to 0 crossings).
  - P1 kneels clear of the bunk blanket.
  - In 2a, P2 kneels 70 cm to his right.
- **3a / 3c:** one hand on the motor (an end cap in 3a, a flat palm on top in 3c); the other hand rests on the thigh.
- **4b:** the guard stands 2.75 m away (70 mm lens), so his face sits between two bars. The flashlight is held low.
- **5b:**
  - The hands grip the grille's side frame, open, and come back through the middle of the opening before it tips; it falls left.
  - The corridor floor now stops at the vent wall, and the duct floor sits 5 cm lower.
  - The camera stops its push-in short of the hands.
- **5c:** P1 kneels up beside the hole and looks round. A hands-and-knees crawl needs about 85° of wrist extension, against the 60° limit.
- **5d:** the walkers have bent, swinging arms and walk with their soles on the floor.
- **6a:** a steep open-tread stair with no hand contacts. The feet step up with the swing pulled back.
- **6b:** P1's hands are stacked on the pipe's front face. After landing he turns and walks two steps toward the camera.
- **Raft:** the seats are inside the tube and the hands rest on the thighs. The feet are keyed every 6 frames on the bobbing floor. There is no paddle.
