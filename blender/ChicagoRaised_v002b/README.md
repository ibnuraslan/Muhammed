# B27 ChicagoRaised v002b: How Chicago Raised Its Buildings

Vertical 1080×1920 / 60 fps explainer, Cycles, hard cuts, built to the client VO (`ChicagoRaised_v002b_VO.mp3`, 32.2 s).
Reference order: workers crank jackscrews under a building → it rises with people inside → cribbing is stacked → new
foundations are built → Chicago was built on a swamp, streets flooded, disease spread → they raised the city; it still stands on those foundations.

- `beats.json`: shot start frames at `1 + round(VO word seconds × 60)` (22 shots).
- `review/preview.mp4`: every 5th frame, 270×480, Cycles 4 spp + OIDN, rendered from this exact package, with the VO.
- `review/pages/`: contact pages of every preview frame. `review/*.json`: check results.
- Build scripts: `blender/ChicagoRaised_v001/scripts/` (01_chars → 02_sets → 03_anim [timing.json] → pipeline/anim_look --no-sky → 04_post_look → 05_package → pipeline/package_for_farm).
- Logo: DA KRAS FILMS (dark) on the shop sign of the hero building (S2, S9, S13). No other text or logos.
- Credits: CREDITS.md (4 CC-BY models must be credited in the video description).
