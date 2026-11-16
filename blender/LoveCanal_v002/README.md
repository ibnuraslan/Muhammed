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

## Checks on the package (review/)
Full-film checks ran on the package before the last S4 hand-path tweak; S4 (frames 325–427) was re-checked on the final package (`review/*_S4_recheck.json`): clip_scan 0 bad ranges, qa 0 flags, Glass crossings = the accepted thumb on the glass only. No other shot changed after the full run.
- body_prop_cross: only the accepted contacts: S1 riding (1–76), S4 thumb on the glass (349–394), S9 fingertips on the drum (952–973), S19 fingertips on the box (1609–1693).
- limb_check ARMBODY: upperarm01 points within 4 cm of the shoulder (known false positive) everywhere except S4 349–385 (the right forearm tucked to his side while he sips; hand and glass read clearly).
- clip_scan, explained ranges:
  - 79–199 (S2 Neighbour), 259–319 (S3 Dad2), 433–613 (S5 Mother): relaxed hanging fingertips touch the side of the thigh; those hands are hidden behind the body, the bin and the kitchen island.
  - 1789–1963 (S22 Father): his fingertips sit under the shirt fold beneath the boy's palm; on screen it reads as hand-on-hand (staging passed in Phase 1).
- qa_check: EMPTY on the no-character shots (S7, S8, S11–S18 are set/prop shots by design), CAMJUMP = the 19 hard cuts, PROPMOVE = intended unaided motion: drums sliding off the tipping beds and tumbling in S11/S13 (1051–1201), the seep streaks growing in S16, the yard puddle growing in S17, the drips running down the tower in S18, the glass set down on the counter at the S4→S5 cut, BACKHEAD on single frames 1 and 565 (back views by design).

## Known issues
- S4 397–410: the left arm swings out briefly as the hand lifts to the chest.
- S10 975–1033: the two trucks sit partly at the frame edges.
- S17 1495–1510: the puddle starts tiny (it grows on the beat).
