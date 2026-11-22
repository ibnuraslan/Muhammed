# LegoInNose v012 — review notes

Package: `LegoInNose_v012_60fps.blend` (packed, ~65 MB) + `LegoInNose_v012_VO.mp3` (relative sidecar). Frames 1–2036, same VO and
timing as v011. v011 is untouched.

Preview: `review/preview.mp4` — every 5th frame at 270x480 from the exact package (`pipeline/preview.py` + `watch_pages.sh`,
with the VO). All 9 contact pages were watched. Ranges touched by the last fixes were re-rendered from the final package into
the same preview (frame files overwritten), then the MP4 and pages were rebuilt.

Scripts (in order): `strand_hair.py`, `build_clothes.py`/`import_clothes.py`, `clothes_fix.py`, `cut_tunnels.py`,
`restage_sink.py`, `final_touch.py`, `build_jeans.py`/`mom_jeans.py`, `v12_global.py`, `v12_opening.py`, `v12_boy.py`,
`plant_man.py`, `v12_sink.py`, `settle_tub.py`, `v12_age.py`, `v12_nostril.py`, `v12_fix2.py`, `v12_fix3.py`, `pack_v012.py`.

## Client flags
- **A** opening: plays, picks one red brick off the rug (fingers pinch it, 38–44), lifts and looks at it, then the nose. Natural
  hand path, no stiff pose, camera kept off his knee/shoe.
- **B** the fingers carry the brick into the nostril (120–131); it is turned lengthwise along the nostril and pushed in so only
  its 3.5 mm end shows; same pose to 1229 (no size change, no decal look, no poke-through).
- **C** tub bricks dropped onto the tub floor / each other (no hovering); the yellow brick he grabs rests on the pile and his
  hand reaches down to it.
- **D** the floating dream bricks are deleted; that beat frames his face with the yellow brick in his hand (level camera).
- **E** the brick blob over his face is gone.
- **F** adult: planted ON the bench seat (+19 cm, feet on the floor) and ON the mattress (+10 cm); hands, props and camera carried
  with him. Bed: hands resting on his chest/belly (clip scan clean), level camera with no roll; he lies, sneezes, then sits up.

## 44-point list (short)
1 order play → pick → nose; strand hair on everyone · 2 camera ≥ 0.5 m, off his knee · 3 dark irises, glossy cornea catchlights,
52 blinks · 4 brick goes to the nostril, one brick at a time · 5 white teeth · 6 see B · 7 framing on faces · 8 see C ·
9/14/38 arms bent (flail hands pulled in; boy's hands on knees in the time-lapse) · 10 brick stays visible on the boy to 1229 ·
11 f-stop ≥ 5.6, f/16 on the 355–390 close-up · 12/13 see D/E · 15 the 496–575 shot is level at his eye height, no sleeve over
the lens · 16 cutaway tunnels hidden (no flying through skin) · 17 cutaway backdrop, brain and floor fixed; both bricks in the
passage · 18 one red + one yellow brick throughout · 19 chest-up framing at the sink · 20/21 Mom in blouse and jeans with strand
hair (walk still somewhat stiff, see below) · 22 tweezers thicker · 23 Mom fails, the brick stays in · 24 no white patch ·
25 exposure lowered on the washed-out sections · 26 window view locked; hard cuts between ages (1230 / 1267 / 1292) ·
27 teen in a navy top, the phone a dark screen held in both hands · 28/29 no empty floor frame, no pop-in · 30 window bar
z-fight fixed · 31 tissue held at the nose · 32 bench hold has camera movement and expressions · 33 inhaler baked to his hand ·
34 camera holds the bench framing to 1477, hard cut to the bed (no wall in the lens) · 35/36 see F · 37 gown/blanket cover him in
bed · 39 hands rest on the counter, no forearm through the face · 40 the sneeze expels the SAME red brick, which lands in his
palm · 41 camera above the counter · 42 the brick rides rigidly on his palm, visible · 43 ends on a close-up of his face and the
red brick in his open palm · 44 strand hair.

## Checks (final package)
See `body_prop_cross.json`, `limb_check.json`, `qa_check.json`, `clip_scan.json`, and the summary in the director message.

## Known limits
- Mom's walk (801–846) still reads a little stiff/bow-legged.
- The tub bricks are ray-settled (straight drop), not physics-simulated; a few rest tilted on another brick's corner.
- In some bed frames his shoulder shows next to the gown.
