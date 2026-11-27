# Seldom on-screen graphics kit v1

Animated overlay templates for the new film style: a dark amber-gold 3D world, pale faceless mannequins, and one
yellow accent. Every element is a Python/PIL template that takes text and images and returns a 1920x1080 RGBA overlay
per frame, plus a background treatment (blur, dim) for that moment, so it composites over any shot.

- `seldom_kit.py`: the engine and the 15 templates. Run `python3 seldom_kit.py list` to see them.
- `demo.py`: renders every template over the v3 vault live-test clip and writes `demos/NN_name.mp4` (3.5–8 s,
  1080p, 24 fps), `demos/NN_name_still.jpg` and `contact_sheet.jpg`.
- `assets/`: placeholder photos cut from our own renders (faceless mannequins, the vault), plus the line-art source.
- `data/benelux_10m.json`: country outlines for the map card. Natural Earth (public domain), taken from world-atlas 2.0.2 (ISC).
- `fonts/`: see below.

## Using a template

```bash
# alpha PNG sequence plus meta.json (fps, background blur/dim per frame, SFX cues)
python3 seldom_kit.py render quote --params '{"text": "They knew every sensor in that room.", "who": "LEAD INVESTIGATOR"}' --out /tmp/q
python3 seldom_kit.py render phrase --params '{"text": "“nothing was broken”"}' --out /tmp/p --dur 4
```

From Python: `fr = seldom_kit.TEMPLATES["quote"](t, text=..., who=...)` gives `fr.rgba` (the overlay) and `fr.bg`
(`{"blur": px, "dim": 0..1}`). `seldom_kit.composite(shot_rgb, fr)` applies both. For ffmpeg compositing, apply the
blur and dim from `meta.json` to the plate, then overlay the PNGs (straight alpha).

## Templates (default length, layout, motion)

| # | Template | Default | Where (user layout) | Motion |
|---|---|---|---|---|
| 01 | `datestamp` (top, big) | 3.5 s | lower-left of centre | Rules slide out from the centre with ease-out-expo over 0.9 s. The small line tracks in, the year sharpens from a blur, then a 0.35 s fade. A yellow tick sits under the year. |
| 02 | `quote` (text, who) | 5.0 s | upper right of centre | The yellow serif quote mark drops in (ease-out-back, 0.45 s). The dashed rounded box draws round (0.2–1.1 s). Words fade up one by one (75 ms apart). The attribution follows with a yellow dash. |
| 03 | `phrase` (text, cps) | 4.0 s | centred, with the shot blurred (14 px) and dimmed (55 %) | Typewriter at 16 chars/s from 0.55 s, slower on spaces and punctuation. Each new key jitters a little, a yellow block cursor stays solid while typing and blinks at 2.2 Hz after. **Typing SFX cue times: `seldom_kit.phrase_cues(text)`, written to `meta.json` and `demos/03_phrase_typing_cues.json`.** |
| 04 | `section` (text, index) | 3.8 s | bottom-left | A yellow bar rises, the hairline frame draws, and the label wipes in behind a mask (0.35–0.95 s). A mono index sits on the left. It wipes out to the left in 0.45 s. |
| 05 | `title` (text, sub) | 5.5 s | centred, with the shot dimmed and blurred | **Creepy:** the serif caps bleed up out of the dark like wet ink: a growing blur run through a falling threshold, plus noise, over 0.2–2.4 s. They flicker like a failing tube until 2.6 s and carry a VHS jitter with a red/cyan split and faint scanlines. A low amber flare crawls behind them (1.2–4.6 s). The mono subtitle types on (2.6–3.8 s), and the title ends on a hard flicker-out. |
| 06 | `person` (photo, name, role) | 4.5 s | bottom-left | The card rises 30 px while the gold-duotone photo comes into focus. White frame, inner yellow keyline and yellow corner ticks. The name (condensed bold) and role (mono, yellow) follow. |
| 07 | `person_pair` (photos, names, roles) | 5.0 s | centred low, with the shot blurred and dimmed | The second card follows 0.25 s after the first, then a yellow link with nodes draws between them. |
| 08 | `place` (photo, name, country, coords) | 4.5 s | bottom-right, landscape | A card like the person card. A yellow pin drops onto the corner, and the coordinates tick in, in mono. |
| 09 | `disclaimer` (discretion, discretion_head, discretion_text, text, title) | 8.0 s (6.0 s without discretion) | full frame, with the shot sunk to 90 % black; standalone, so it can sit at the start or after the cold open | A two-part card titled **THINGS TO KNOW BEFORE YOU WATCH**. The title tracks in between two hairlines that draw out from the centre. **Paragraph 1 (optional, `discretion=True`)** is a yellow mono "VIEWER DISCRETION ADVISED" with the warning line under it ("This film contains descriptions of violence and death that some viewers may find distressing."), then a short yellow divider. **Paragraph 2** is the records note: "This story is told from public records, court documents and news reports. / Some scenes are recreated to show what may have happened." With `discretion=False` only paragraph 2 shows and the block re-centres (demo `09b`). Lines rise in one after the other. |
| 10 | `document` (title, ref, lines, highlight) | 6.5 s | centre, over the dimmed shot | A typed sheet (paper texture, fold, sealed stamp) slides in from below right and rotates to -3°. Yellow highlighter bars sweep the key lines, 0.45 s apart. |
| 11 | `timeline` (events, now) | 6.0 s | lower band | The line draws from the left, then ticks drop in one by one: mono date and time above, condensed label below. The current event gets a pulsing yellow node. |
| 12 | `linkboard` (cards, links, line_dur) | 8.0 s | 2D board: black with a faint perspective grid | **Sequential and data-driven.** The first card appears, a yellow line draws out of it with a bright head on the tip, and the moment the line reaches the next position that card appears (a node pops and rings on arrival). The next line draws from that card, and so on. Time each line to the narration: `cards=[{photo, name, role, pos=(fx, fy), t}]` (`t=None` means "appear when the first line reaches it") and `links=[(from, to, start_time, label[, duration])]` (`start_time=None` means 0.6 s after the source card appears). The optional `label` is a small mono tag on the line ("PARTNER", "BROTHER") that fades in as the head passes the middle. Lines route themselves as elbows: below-to-top between rows, side-to-side on one row. |
| 13 | `map` (route, pin, bbox, route_t, legs) | 6.5 s | centre card | A dark stylised Benelux map: the target country filled near-black with a yellow outline, minor cities in grey. The card scales in, the pin drops and pulses, then the route **draws on leg by leg** as a dashed yellow path with a moving head. Each stop's node and label land the moment the head reaches it. Timing: `route_t=(start, end)` is split by leg length, or set `legs=[(t0, t1), ...]` to time each leg to the narration. A stop is `(lon, lat, name[, "l" or "r" label side])`; an empty name is an unlabelled waypoint. |
| 14 | `lineart` (source, accent_box) | 7.0 s | 2D: black with a faint grid | Any render or photo is turned into white ink line art, with one detail redrawn in yellow (here the red bag). It reveals left to right with a soft edge, then drifts slowly. |
| 15 | `outro` (thanks, subscribe, tuned, logo, guides) | 10.0 s | full frame, the shot sunk to 93 % black over a faint grid | **End card.** The official Seldom logo (`assets/seldom_logo.png`, the logo art, never 3D text) rises out of a soft yellow bloom at the top. "THANKS FOR WATCHING" tracks in between hairlines. Below it is the space for **YouTube end-screen elements**: two 16:9 video slots at x 150 and x 1110, y 470, 660x371 px (corner-tick frames, labelled "WATCH NEXT" and "MORE FROM SELDOM"), and the subscribe circle between them (centre 960,655, r 112), drawn as a yellow ring that pulses, with "SUBSCRIBE" and a small arrow under it. "STAY TUNED FOR MORE" types on at the bottom with the yellow cursor. `guides=False` (demo `15b`) leaves the slots and ring off so YouTube's own elements sit on a clean field. Slot geometry: `OUTRO_SLOTS`, `OUTRO_SUB`. |

Every element carries a soft glow, a drop shadow where it sits over the shot, and fine per-frame film grain
(alpha-modulated, 12-frame cycle). Entries take 0.7–1.8 s and use eased curves (ease-out cubic, ease-out expo,
ease-in-out, ease-out back), and exits are short fades or wipes, in line with the reference overlay study timings.

## Design tokens

| Token | Value | Use |
|---|---|---|
| Yellow | `#E3FF00` | The one accent: quote marks, rules, cursor, highlighter, links, pins, roles |
| Paper white | `#F3F1EA` | All primary text and lines |
| Near-black | `#0B0A08` | Card fills, plates |
| Warm grey | `#969288` | Secondary text (attribution, coordinates, minor cities) |

## Fonts (all free for commercial use; files in `fonts/`, from Google Fonts)

| Role | Font | Licence |
|---|---|---|
| Labels, names, tags (condensed caps) | Oswald Light / Medium / Bold | SIL OFL 1.1 |
| Quotes, disclaimer, title (refined serif) | Cormorant Garamond SemiBold / Medium Italic | SIL OFL 1.1 |
| Typewriter phrases | Special Elite | Apache 2.0 |
| Documents, title subtitle (case-file mono) | Courier Prime Regular / Bold | SIL OFL 1.1 |
| Small technical mono (indices, coordinates, dates) | IBM Plex Mono | SIL OFL 1.1 |

## Speed

PIL only, with no browser or GPU: about 0.1–0.4 s per 1080p frame per template, and the demo renders 4 frames at a
time on 4 cores. All 14 demos (1,800 frames) composite and encode in about 3 minutes.

## Notes

- Photos are placeholders cut from our renders. Any photo works: it is cropped to fill, auto-levelled and gold-duotoned.
- `demo.py` expects clean 1080p plate frames (the vault clip without its burned-in overlay). It ping-pongs the 5 s
  clip for longer demos.
