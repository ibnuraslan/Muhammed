# B05 LoveCanal v002: The Love Canal Disaster (built to the client VO)

Vertical explainer, 1080×1920, 60 fps, 32.75 s (frames 1–1966), Cycles. 20 shots with hard cuts on one camera, timed to the client's VO (`LoveCanal_v002_VO.mp3`, transcribed with faster-whisper; `beats.json` lists every shot's start frame and first words).

## Files
- `LoveCanal_v002_60fps.blend`: the RenderStreet package (see SETTINGS.md)
- `LoveCanal_v002_VO.mp3`: the client VO
- `beats.json`: shot start/end frames at `1 + round(seconds × 60)` of the VO words
- `review/preview.mp4`: moving preview of the exact package (every 5th frame, 270×480, Cycles 4 spp + OIDN, with the VO)
- `review/pages/`: contact pages of every preview frame
- `review/*_check.json`, `review/clip_scan.json`, `review/body_prop_cross.json`: check outputs
- `scripts/`: the full build (01 chars → 02 sets → 03 animation/camera → anim_look → 04_shrink → package_for_farm)

## Shot list (VO words)
S1 neighbourhood, boy on bike ("People living in this neighborhood") · S2 neighbour at the fence smells it ("started noticing strange smells") · S3 neighbour lifts the trash lid ("during the 1970s") · S4 father tastes the water ("Their water tasted odd") · S5 kitchen, father sick, family watching ("and residents began getting sick") · S6 house, neighbour walks by ("But what they didn't know") · S7 ground cut-away under the homes ("was that their entire neighborhood had been built") · S8 the toxic pocket ("on top of a toxic waste dump") · S9 worker rolls a drum ("Decades earlier") · S10 dump trucks, worker waves ("a chemical company had") · S11 trucks tip, drums slide off ("buried more than 20,000") · S13 the drum heap ("tons of hazardous chemicals") · S14 bulldozer buries it ("there") · S15 house frames rise on the cut-away ("Once houses were built above it") · S16 basement seep ("the chemicals began leaking into basements") · S17 backyard puddle ("backyards") · S18 water tower ("and the water supply") · S19 box to the moving truck, logo ("Eventually") · S20 truck leaves ("families were evacuated") · S22 hospital, father and son ("and many residents suffered long-term health problems").

The VO is 10 s shorter than the reference. S12 (top-down pile) and S21 (wide street) are folded into their neighbours, and S4's action was re-keyed at 1× to fit its 1.7 s (nothing time-stretched).
