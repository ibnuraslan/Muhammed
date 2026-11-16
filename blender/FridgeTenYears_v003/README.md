# FridgeTenYears_v003: director fix round 1

This is v002 (commit eaadb2f) with one change: the contractors' reactions in **S18 (f1431–1480)** and **S20 (f1559–1651)**. The director's note was that they stood frozen side by side with their arms hanging straight.

- **S18:** ConB straightens and throws both hands up in shock at chest height, elbows bent. ConA steps back from the panel, with his head turning toward ConB and back.
- **S20:** ConA steps back and raises his near hand to the side of his hard hat. ConB leans in with both hands up at chest height, palms out. Both turn their heads a little toward each other.
- Everything else is unchanged: framing, timing, frames **1–1651**, the VO, and the logo in S16.
- **Preview:** `review/preview.mp4` is the v002 preview with f1431–1480 and f1556–1651 re-rendered from this exact file and spliced in. `review/pages/` holds the contact pages.
- **Checks on this file, f1431–1651:**
  - clip_scan: 0 bad ranges.
  - body_prop_cross with both hard hats as props: 0 hand/hat or body/prop crossings. The only flag is each head inside its own hat (the hat rests on the head).
  - limb_check: only the known upperarm01 shoulder points.
- Every other check is as in `FridgeTenYears_v002/review/CHECKS.md`.
- **Also fixed:** the last frame of S18 is now keyed, so it no longer blends toward the next shot's pose.
