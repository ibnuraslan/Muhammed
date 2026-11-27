# Style study v2: 3D "blue-room" true-crime references

Read `STYLE_GUIDE.pdf` first. It has the measurements, the shared style rules, notes on each video, the production cost for our pipeline, and the recommendation with 3 example frames.

| File | What it is |
|---|---|
| `contact_amy.jpg`, `contact_caylee.jpg`, `contact_noida.jpg` | 24 frames per video (mid-shot frames picked evenly across the film), with timecodes |
| `cuts.json` | Detected cut times per video, in seconds |
| `scripts/` | The analysis scripts: shot detection (`cuts2.py`), 2D/label classifier, palette, audio, Whisper, sheet and PDF builders |

The source videos (854x480, 42–56 min each) are **not committed**. They come from the shared Drive folder.
The Amy Bradley copy has a Russian dubbed voice-over. The other two are in English.
