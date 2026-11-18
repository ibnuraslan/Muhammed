# Competitor 04 · Fern — "Hansa: The Infiltration of the Dark Web"

| | |
|---|---|
| Source | Drive `competitors/…fern (1080p).mp4`, 24:29, **1920×960 = 2:1** (Fern's wide format), 25 fps |
| Shots | 191 detected · median 2.6 s · p90 20.4 s (dark scenes hide some cuts, so the true count is higher) |
| Sound | −14.7 LUFS integrated, LRA 3.5 LU |
| Contact sheet | `04_fern-hansa.jpg` |

## Big finding: Fern films real actors for acting close-ups

| Element | What is on screen |
|---|---|
| **Live-action actors** | The admins, the hacker and the Dutch investigators are **real actors filmed on black sets** with practical desk lamps and monitors (MCU/ECU, faces, hands on keyboards, phone calls, tired gestures) |
| **3D digital humans** | Europol meeting (suits around a long black table), a statue-like presenter, Dutch police ensemble, a silhouette with flying coins: all in the same black-void staging |
| **3D objects on black** | Server racks with green LEDs, lockers, an orange table, Tor/Politie network diagrams, a world of desks with yellow light paths |
| **UI** | Dark-web market pages, chats, spreadsheets, "No Connection", "Uploading…", article quotes with cyan highlights |
| Glue | Everything sits in **black space with one pool of light**, so live action, 3D and UI cut together seamlessly |

## Staging and quality notes

| Item | Obs | Lesson for Seldom |
|---|---|---|
| Acting | All emotional close-ups (stress, relief, a smile on the phone) are real actors | The hardest part (faces, hands, micro-expressions) is done with a camera, not a rig |
| Hands | Real hands on keyboards, a ring, cigarettes; 3D hands only in wides | Same as Yarnhub: 3D hands are kept small or out of frame |
| Walks | Almost none; people sit, stand, gesture | |
| Black-void sets | A desk, a lamp, a monitor: the set ends a metre from the actor | Extremely cheap to build in 3D or with live action |
| Chapter title | "OPERATION…" in yellow bold italic over a 3D boardroom | Cinematic title over a scene |
| Year tag | Yellow italic "2017" bottom-left | |
| Palette (measured) | Luma median **0.14** (darkest of all refs), saturation median 0.16; `#0c0c0e` 17% · `#020101` 16% · `#0d1425` navy 10% · `#c5c4c4`/`#eae9ea` UI whites 16% · warm skin `#7c6462` | Night-office noir: black + navy + warm lamp |
| Long holds | Diagram and UI shots held 20–80 s while the VO explains | |

## What Seldom can take

| # | Technique | Pipeline | Effort |
|---|---|---|---|
| 1 | **Hybrid: film the acting close-ups with real actors on black, do everything else in 3D** | Needs a camera, a black backdrop and 1–2 lamps; composite into the 21:9 grade | Medium (new tool: camera + actors) |
| 2 | Black-void "one pool of light" sets | `look.py` void preset; sets end at the edge of the light | Easy |
| 3 | 2:1 frame (Fern) | Render 1920×960 or letterbox | Easy |
| 4 | Network diagrams (white line icons on navy) | Line-art icons + animated dashed paths | Easy |
| 5 | Article quotes with cyan highlight | Doc card template (our colour instead of cyan) | Easy |
| 6 | 3D crowds only in wides on black with DOF | Instanced MakeHuman, no close-ups | Medium |
