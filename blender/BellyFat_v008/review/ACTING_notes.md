# BellyFat v008: acting review and fixes (brief ACTING_FIX_04-10.md)

These are the review notes on the approved v006, built from `before_v006_sheet_0.5s.jpg` (1 still every 30 frames, 270×480, 8 samples) plus close-ups.
- The story-beat frames are unchanged: `beats.json` 1 / 121 / 181 / 469 / 757 / 889 / 1207.
- The camera path is unchanged, so the VO re-sync applies directly.

People are on camera only from 0 to 2.55 s and from 20.4 to 21.5 s. The rest is the macro cross-section, where nobody acts.

## Problems found in v006, and the fixes
| # | Frames (t) | Problem in v006 | Fix in v008 |
|---|---|---|---|
| 1 | 1–120 (0–2 s) | **Frozen reach.** Her left arm stays stretched out to the shelf for 2 s, touching a box for no reason. A real shopper picks the item up. | She reaches and grips a box's front over its top edge (grip curl, thumb opposed, wrist under 75°). She lifts it off the shelf and draws it toward her; the box follows her wrist from the grasp frame. Her head turns down to read it (1.3–1.95 s). At the hit she lets go and the box drops, tumbles and lands flat on the floor by 2.55 s. |
| 2 | 1207–1290 (20.1–21.5 s) | **Odd end gesture.** A raised right hand with the palm out reads as a "stop" sign, not as shock at being shot. | Her right hand presses flat to her chest (palm on the sternum, fingers relaxed) while her left hand holds the wound. |
| 3 | 1225–1290 | **Unreadable face.** The breathing loop overrode the end head keys, so the head stayed tipped without a reason. | Rewritten head motion: she looks down at her hand on the wound (pitch 28°, 20.4–20.75 s), then lifts her face toward the camera with her mouth open (20.75–21.3 s), breathing. Her face is readable on beat 7. |
| 4 | 1246–1264 | Her left hand travelled from her flank to the wound **through her side**. | Out-and-around arc key (20.84 s); fingers curl during the move, then flatten on the wound. |
| 5 | 1225–1260 | Her chest hand **sank into her chest** on the store's return (clip check). | The hand sits 5 cm further out; verified with 0 hits. |
| 6 | 15–100 | The new box grip had **wrist bends of 76–115°** (grip from above). | Re-staged as a front-over-top grip with an in-between key; all wrists under 75°. |

## Checked and kept (meets the bar)
- **Feet:** all five characters' soles are planted or walking, at about 1 cm (audit), with no slide.
- **Hit reaction (2.0 s):** her hips go back and her torso folds, her hand jerks off the shelf, the basket drops and cans fall. A real flinch with follow-through.
- **Shopper A:**
  - pushes the cart with a wrap grip;
  - raises his hands after the bang;
  - on beat 7, steps sideways round his cart toward her and reaches out.
- **Stocker:** grips the carton and turns at the bang.
- **Shopper B:** crosses the back and turns to look.
- **Shopper C:** browses, then turns.
- **Camera:** never inside a body or prop (audit: 0).
  - Shirt-fabric fills at 2.55 s and 20.4 s: this is the approved continuous dive, with visible weave and the entry hole in frame.
  - The impact speed ramp (f121) is deliberate.

## Round 2 (director review of 85abd2c)
| # | Note | Fix |
|---|---|---|
| R1 | The box looked glued to a fist, with no finger contact. | The box now has its own keyed path, and her hand is placed **relative to the box** each frame.<br>**Lift:** her palm is on the box's near side face, fingers wrapped round its back edge, thumb on the front face (0.45–1.05 s).<br>**Hold:** as she draws it in, the box tips back onto her **cupped hand**, her fingers curled up round its underside and far side.<br>From 1.05 s the box is baked to rest on her evaluated palm, so the two stay in contact.<br>An over-the-top hook was tried and dropped: at shelf height it needs an 85–115° wrist bend, which breaks the wrist rule. |
| R2 | 2.5 s and 20.5 s were flat blue frames. | At both swaps the camera now sits about 4 cm off the shirt, aimed beside the hole, so the frame keeps the weave and shows the dimple and the bullet tail (2.5 s) or the hole rim (20.5 s).<br>The weave bump and contrast are restored on both fabrics after the global bump cut, and focus locks onto the fabric plane. |
| R3 | Close-up tiles 8 and 12 were black. | Re-aimed. The sheet now has 12 labelled tiles, none black. |
| R4 | f1256 needed two angles. | Tiles `f1256front` and `f1256top` show the left hand clear of her body. |

## Checks on v008
- **Hand audit** (`audit_hands_v008.txt`, every 2 frames on all on-camera frames): hand vs hand, own body, own clothes, other characters, and wrist bend.
  - **0 overlaps.**
  - **1 wrist frame at 77°** (f69, the instant the side grip turns into the cup), just over my 75° check and inside the style rule's ±60° flex plus 25° side.
- **Contact / camera audit** (`audit_v008.txt`): 0, apart from the deliberate f121 ramp.
- **Director `clip_scan.py`** (step 2; `clip_scan_v008.json`): **one range, 1255–1257 (20.9 s). This is a false positive.**
  - The flagged probes are her left fingertips at about (0.38, 0.65, 1.04) m, in free air about 15 cm in front of her belly.
  - Their nearest target polygon (spine02 at (0.23, 0.60, 1.03)) has an inward-facing normal, so the normal-side test reads them as inside.
  - I moved the hand through three different arcs and the same polygon was flagged each time. The close-ups (`after_v008_hand_closeups.jpg`, f1256) show the hand clear of her body.
- **Close-ups** of every hand contact: `after_v008_hand_closeups.jpg`. The box grasp/hold (f45/75/105), basket grip (f110), end hands (f1240/1256/1275), cart grip (f60), shopper A reaching (f1290) and stocker carton (f60).
- **Sheets:** `before_v006_sheet_0.5s.jpg` and `after_v008_sheet_0.5s.jpg`.
