#!/bin/bash
# Rebuild review/storyboard_v2_before_after.jpg (BEFORE = out/ch*/ approved stills, AFTER = out/sbv2/after stills)
cd "$(dirname "$0")/.."; A=out/sbv2/after
python3 tools/sb_sheet.py review/storyboard_v2_before_after.jpg "STORYBOARD v2 · changed shots (stills 25%, 16 samples, ungraded)" \
"1-8B iron stove tool|out/ch1/hint_kitchen_glide|$A/evid_tool_black|Exhibit on black, one top light, red-string tag. Recurring object: 1-7B floor, 1-8B exhibit, 3-6B desk, 3-7B swing." \
"1-9A struggle / no suspect|out/ch1/hint_flash_hall|$A/evid_board|Ch1 LONG TAKE: cork board, floor plan, prints, red string; push + rack focus ends on the empty SUSPECT card. Then 1-9B tilt to the ceiling (kept)." \
"2-8B identified|out/ch2/station_photo|$A/evid_file_card|Faceless file print slides in; record card: false name X'd, real name types in." \
"2-9B eight by fifteen|out/ch2/hint_attic_torch|$A/hint_hatch_measure|The real closet hatch from below: torch settles, chalk lines drawn, 8 in / 15 in chalked on the plaster." \
"2-13B five weeks before|out/ch2/hint_joist_drift|$A/evid_calendar|1941 wall calendar: October (17 circled) flips back to September; red ticks day by day from the 12th; 'five weeks'." \
"3-6B the route|out/ch3/hint_walk_track|$A/evid_plan_route|Red pencil draws kitchen -> front door -> front bedroom on the floor plan, ends in an X. Attack implied, never shown." \
"3-7B heavy iron stove tool|out/ch3/hint_door_closing|$A/evid_tool_swing|Callback: the same exhibit under a swinging, flickering bulb; shadow sweeps." \
"3-9B..11B nine months (autumn)|out/ch3/hx_seasons_push|$A/evid_cutaway|Ch3 HERO LONG TAKE ~36 s, replaces 5 shots: cut-away model of the house; rooms go dark, only the attic glows." \
"   (winter)|out/ch3/hx_attic_vent|$A/w/evid_cutaway|Snow falls and settles; date card counts OCTOBER 1941 -> JULY 1942, day 1 -> day 286." \
"   (summer, push to attic)|out/ch3/hx_summer_still|$A/s/evid_cutaway|Summer green; slow orbit ends pushing into the attic glow: where he lived." \
"3-14A less than two hours|out/ch3/court42_jury_in|$A/evid_clock|Courtroom clock under one top light; minute hand sweeps 1 h 46 m and stops. Then 14B gavel (kept)."
