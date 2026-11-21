# LegoInNose_v012: client fixes on v011 (same VO, timing and frames)

This is v011 (`LegoInNose_v011_60fps.blend`, left untouched in `../LegoInNose_v011/`) with the client's notes fixed. It uses the same voiceover (`LegoInNose_v012_VO.mp3`, identical to v011's), the same timing, and frames **1–2036** at 60 fps (33.9 s). `beats.json` lists the beat frames. The review preview is `review/preview.mp4`.

## What changed (scripts in `scripts/`, run in this order on the v011 file)
1. `strand_hair.py`: **real strand hair** on all four characters, so there's no helmet hair.
   - Geometry nodes grow curves from each character's deformed hair-card mesh, so they follow every head move. They're combed back, with a droop and some random spread.
   - They're Cycles curves with a Principled Hair BSDF in dark brown.
   - The old cards stay underneath as a darker root layer.
   - In Blender 5.2, Cycles renders geometry-node curves only on a Curves object, so the hosts are Curves objects.
2. `build_clothes.py` and `import_clothes.py`: new outfits fitted by MPFB on the same body settings.
   - **Mom:** a loose striped blouse (warm mustard) over a grey skirt (`female_elegantsuit01`), replacing the skin-tight blue top and leggings.
   - **Adult son:** a T-shirt over separate blue jeans (`male_casualsuit06`), replacing the one-colour blue outfit.
3. `clothes_fix.py`:
   - The new outfits' "Delete" body groups and masks are added, so no skin pokes through.
   - The T-shirt is a plain sage green. The asset's printed logo is removed by colouring the shirt region from bone weights.
   - In the hospital bed (1478–1586) the shirt region becomes a pale blue **checked hospital gown**, and a **blue blanket** covers him from the waist down.
4. `cut_tunnels.py`: the four nostril-tunnel passes, the **empty blurry pink frames**, become **hard cuts** between the boy's face and the sharp anatomy cutaway: 578, 729, 944 and 1151. Only the camera is re-timed, never the characters.
5. `restage_sink.py`: the shower ending is **re-staged at a bathroom sink**. He wears his T-shirt and jeans behind a vanity (cabinet, stone counter, basin, tap), framed chest-up. The glass stall, shower fittings, water and steam are gone. His acting is unchanged: the nostril press, the sneeze, and the brick landing in his palm over the sink.
6. `final_touch.py`:
   - **Dark brown irises** on every character.
   - In bed, the camera holds the man's **face**, upright and clear, over 1478–1586.

## Checks on the packed file
These are in `review/`: `clip_scan.json`, `qa_check.json`, `limb_check.json` and `body_prop_cross.json`. The results are in the message to the director and in `review/NOTES.md`.
