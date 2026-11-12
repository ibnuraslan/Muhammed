# FanCancer: Checkpoint C (polish)

- Sheets: `review/C_polish_0.2s_a.jpg` (0–22 s) and `review/C_polish_0.2s_b.jpg` (22–44 s), one still every 0.2 s at 270×480 and 8 samples.
- Hand audit: `review/C_hand_audit.txt` (BVH every 2 frames).

## Changed since B
- **Look (client, 22:45).** `pipeline/anim_look.py` (AgX Punchy, saturation, bump down, roughness at least 0.35, f-stop at least 5.6, motion blur off) and then a hand pass in `scripts/03c_look.py`:
  - The rink is high-key: white ice, light blue-grey walls and risers, a lighter ceiling, arena lights ×2 and the stand fill ×2.
  - The glass is crystal clear; the earlier frosted veil is gone.
  - The skin cutaway sits on the sky-blue gradient (cyan to near-white) with colour-coded layers: peach epidermis, pink dermis, yellow-orange fat, red vessels.
  - Clinic: bright mint walls, an exam lamp, two wordless anatomy posters, ceiling diffuser panels with a prismatic grid, and the nurse walking.
  - City: dusk-blue world with a moon key and facade wash lights (city beats only); windows lit at random warm or blue; the bus lit inside.
  - A soft fill light rides with the camera (off in the cutaway).
- **Beanie.** It is now a ribbed red knit mesh fitted over the hair, sitting about 7 cm above the eyes, and parented to the head bone. It comes off indoors at home.
- **Clothes.** Every MPFB suit is rebuilt print-free: solid shirt and trouser colours split on rest height, with AO and fabric normals. Each crowd fan has a clothed solid-colour top.
- **Crowd.** Duplicate rigs now pose: they sit, sway and cheer, then stand and cheer in the finale. Twelve per row.
- **Hands.**
  - Limit Rotation on all 2,820 finger and thumb bones across every rig (fingers −2° to 95° curl, ±8° twist, ±10° spread; thumb in a cone).
  - Relaxed curl (12–24°) on every unanimated finger, more on the doctor's instrument hand.
  - Her hands to her mouth at home now face her (palms in).
  - Phones have a screen on both faces; the camera picks the face not covered by the hand.
  - Hockey sticks are removed. They floated; now the players cheer with empty hands.
- **Camera.**
  - Beat 5 is framed from her right side.
  - The slap is shown from her side, with the phone flat on the glass.
  - Beat 10 now pushes up into the clinic's ceiling light panel (grid detail) and comes out into the city, instead of the hand-covered phone.
  - DOF is f/8 except in macro.
- **ManagerB** sits on the exam bed with his feet hanging.

## Still open
- Beat 5: her head bows over the phone, so the note screen is only partly visible.
- The beanie reads as a smooth red knit cap; the ribs show only up close.
- Skaters glide and lean on FK legs; they are on ice, so the sliding is intended.
