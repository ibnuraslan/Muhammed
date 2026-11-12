# GoatOwner_v006: acting pass, round 3 (Connect32)

`GoatOwner_v006_60fps.blend` is **69 MB**: packed, compressed, and a plain git file. It is 1080×1920 at 60 fps, frames 1–2190. The story-beat frames are unchanged (`beats.json`), and the director's v003 grey-pink mouth fix is kept.

v006 applies the director's notes on v005 (16:45 and 17:04): items 28–33 in `review/ACTING_notes.md`.
- Official B's hand leaves the goat once it climbs the ramp.
- 7.0 s: wide on the whole goat.
- 32.0 s: the goat and rescuer are in frame.
- Belly clutch: director `hand_poses.py` (`place_hand` + `flat_palm`), so the palm rests on the overalls.
- Ambient dust is smaller and low, so the camera no longer passes through dust spheres.

## Files in `review/`
- **Sheets:** `before_v003_0.5s.jpg` and `after_v006_0.5s.jpg`, one still every 30 frames. Every cell shows the goat or a person.
- **Hand close-ups:** `hand_closeups_v006.jpg`.
- **clip_scan** (`clip_scan_v006.json`): one single-sample hit at f1345 (22.4 s). The owner's flat right palm on his stomach dips slightly into the body under the overalls while he climbs the steps. Pointing the fingers down along the stomach made it worse (a 25-frame range), so the across-the-stomach palm is kept.
- **qa_check** (`qa_check_v006.json`): BACKHEAD 3, EMPTY 242, INSIDE 3. There is no FILL now; the dust and goat-neck FILL flags are gone.
  - EMPTY: goat-only framings. The check counts only MPFB humans as characters.
  - INSIDE f1885, f1915, f1999: during the ramp-to-sanctuary fly-over. A ray trace from the camera there hits only ground and grass from the outside, with no volume, so these look like a grass-instance false positive.
  - BACKHEAD:
    - f1: behind the fence, as intended.
    - f1519: face-down death beat.
    - f1735: an official arriving, seen from behind.
