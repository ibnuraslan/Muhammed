# ScaldingCoffee_v003 (B09)

Vertical true-story short: the 1992 scalding-coffee case. 1080×1920, 60 fps, Cycles, frames 1–1808 (30.1 s),
hard cuts, built to the client's VO (`ScaldingCoffee_v003_VO.mp3`). Phase-1 plan, scripts and review sheets are in
`../ScaldingCoffee_v001/`.

## v002b changes (director review of v002)
- Older woman (car + hospital): hazel-brown eyes, grey strand hair; car outfit is a loose lavender blouse over a slate skirt.
- No one-colour skin-tight suits: doctor (blue scrub top / navy trousers), nurse (teal top / charcoal trousers),
  café woman (mustard top / denim); suits split at the hip and set 8–10 mm off the body (`scripts/looks_v002b.py`).
- No stiff hanging arms: doctor holds a blank clipboard and gestures to the patient, the nurse gestures to her; in the café
  three people in the queue check phones, the man with the logo cup sips (4d), the woman at the table talks with both forearms bent (`scripts/b2_b6.py`, `arms_bent`, `gesture`, `hold_flat`).
- 2c macro is 1.0 s (667–726), sharp, thinner steam, push-in; 2b starts earlier in its own crane (no stretch).
- 4b: the stainless counter top mirrored the queue as a big blurred blob; it is matte now, and the lens tilts up at f/22.

## Contents
- `ScaldingCoffee_v003_60fps.blend`: the farm package (see SETTINGS.md)
- `ScaldingCoffee_v003_VO.mp3`: the client VO
- `beats.json`: beat start frames on the VO words (frame = 1 + round(seconds × 60))
- `review/preview.mp4`: moving preview of this exact file (every 5th frame, 270×480, with the VO)
- `review/checks.md`: clip_scan, qa_check, limb_check and body_prop_cross results on this exact file
- `review/VO.words.json`: word timestamps (faster-whisper small.en)

## Shots (VO frames)
| Frames | Shot | VO |
|---|---|---|
| 1–64 | 1a Woman in the passenger seat, door open, plain cup between her knees | "A woman accidentally spilled…" |
| 65–224 | 1b She leans in, the cup tips, coffee pools on her lap, steam | "…a McDonald's coffee into her lap…" |
| 225–301 | 1c Her face: she flinches | "…in 1992." |
| 302–444 | 2a Coffee urn tap pours into the DA KRAS FILMS cup | "At the time, the coffee was being served at around 190 degrees," |
| 445–666 | 2b The served cup, crane up from the counter to a 45° view over the rim | "only about 22 degrees…" |
| 667–726 | 2c Top-down macro (1.0 s): sharp simmering surface, bubbles, push-in | "…below boiling." |
| 727–810 | 3a She lies in a hospital bed, clean bandages on her legs | "The burns were so severe" |
| 811–949 | 3b Doctor (blank badge, blank clipboard) and nurse gesture toward her at the foot of the bed | "that she needed skin grafts and spent eight" |
| 950–1043 | 3c Her face on the pillow | "days in the hospital." |
| 1044–1134 | 4a A customer holds a steaming logo cup | "And she wasn't the only one." |
| 1135–1280 | 4b From behind the counter: queue (phones) + standing-table pair, counter a low matte strip | "McDonald's had already received more than 700" |
| 1281–1390 | 4c The queue checks phones; the man with the logo cup behind | "complaints about customers being" |
| 1391–1481 | 4d The standing-table pair | "burned by its coffee." |
| 1482–1569 | 5a Boardroom: the boss leans over a cup | "The case created massive backlash" |
| 1570–1642 | 5b Close on the boss: looks up, exhales | "and eventually" |
| 1643–1732 | 6a An employee turns the machine's temperature knob down | "pushed the company to lower" |
| 1733–1808 | 6b Dial insert: the needle drops from red to the middle | "the serving temperature." |

No time-stretch: each beat's 1× animation clip is only shifted onto its VO words (B2's pour and served-cup shots
shifted separately). Logo: DA KRAS FILMS on the paper cups in 2a/2b and 4a only. No other text or brands.
