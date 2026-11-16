# body_prop_cross results (P1, provisional timeline 1–3822)

- **Script:** `pipeline/body_prop_cross.py`. A copy that takes an explicit frame list and prints each body part / prop pair was used.
- **Frames checked:** every 8th frame of the film plus the first, middle and last frame of every shot (540 frames). After the final fixes:
  - 5b and 6a were re-checked on every 2nd frame;
  - 5b, 5c and 5d on every 3rd frame, with the crates added to the prop list.
- **Props checked:**
  - the spoons and the drill copies (motor, fan, bit, cord);
  - the flashlight, both vent grilles, the dummy head, blanket, blanket roll and pillow;
  - the mattress, bunk frame, stool, table, basin and rim;
  - the cell's back wall and bars, the corridor wall and duct pieces, the wooden crates and the corridor's far wall;
  - the stair treads and stringers, the vent pipe;
  - the raft tube, floor and rope.

## Result: 0 visible crossings in all 24 shots

One kind of hit remains and is a known false positive:
- In 6a, 4–6 edges labelled `root` touch a stair tread on some frames.
- `body_prop_cross` turns off the MPFB MASK modifiers, which exposes the hidden helper geometry, and those helper vertices are labelled `root`. LESSONS §3 notes the same for `clip_scan`, which excludes helper vertices.
- Re-checked with the masks on (the rendered mesh), these frames have no body edge crossing any tread.

## Staging changes made to get there
- **1a:** the spoon rests on P1's open palm instead of a pinch or full grip; pinched fingertips went through the 2 mm spoon.
- **1c–2d:** no palm on the wall; the other hand rests on the thigh. The kneelers moved off the bunk and the basin.
- **3a, 3c:** one hand holds the motor (an end cap in 3a, the top in 3c); the other hand rests on the thigh.
- **4b:** the flashlight is held low, below the tighter 55 mm frame.
- **5b:** the hands grip the grille's side frame, then open and pull back before it tips; it falls to the left. The duct floor is lower and the dug hole wider.
- **5c:** re-staged as in the reference: P1 is already out, on hands and knees beside the hole, looking round.
- **5d:** the grille stands against the wall; the crate (logo) moved 0.35 m.
- **6a:** the ladder is replaced by a steep open-tread steel stair, with no hand contacts.
  - Three ladder attempts (rung grips, rail slides, side presses) kept clipping fingers.
  - The camera looks down from the top, so both faces climb toward it.
- **6b:** P1's body is back from the pipe, his hands stacked on its front face and his legs wide.
- **Raft:** the seats moved inward, the feet sit on the floor that bobs with the raft, and the paddle was dropped (the reference has none).
