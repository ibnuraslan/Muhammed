# PilotSuckedOut_v002 (B17): built to the voiceover

1990: a cockpit windscreen blows out and the captain is pulled out to his waist; a flight attendant holds his legs while the
co-pilot flies; the plane lands about 20 minutes later and he survives.

- `PilotSuckedOut_v002_60fps.blend`: the package (frames **1–1887**, 60 fps, 31.45 s). Farm settings: `SETTINGS.md`.
- `PilotSuckedOut_v002_VO.mp3` (packed in the blend as a sound strip from frame 1) and its word timings `*_VO.words.json`.
- `beats.json`: shot start frames at the VO words (`1 + round(seconds × 60)`).
- `review/preview.mp4`: the moving preview (every 5th frame, 270×480, Cycles 4 spp, with the VO), rendered from this exact package.
- `review/pages/`: every preview frame on contact pages (watched). `review/checks/`: bpc, clip_scan, limb_check, qa_check results.
- Credits: `CREDITS.md`. Built by `../PilotSuckedOut_v001/scripts/` (01 → 02 → 03 → 04, then `pipeline/package_for_farm.py`).

Shots (VO words): 01 "In 1990" · 02–03 sucked out of the cockpit · 04–05 his legs · 06 windscreen · 07–08 depressurize ·
09–10 the attendant grabs his legs · 11–12 the co-pilot · 14 his body against the outside · 15 thought he was dead ·
16 they held on · 17 "Around" · 20 20 minutes later · 21 landed · 22 and somehow · 23 the pilot was (van, logo) ·
24 still alive (he lifts his head). Shots 13, 18 and 19 of the P1 plan were dropped: the VO has no words for them.

Every character's animation is keyed at 1× from its shot's first frame and trimmed at the cut; nothing is time-stretched.
