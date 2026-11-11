# Checkpoint B — blocking (1 still per second)
Sheet: `review/B_blocking_1s.jpg` (270×480, 8 samples). Build: `scripts/00_plain_shirt.py`, `01_build_teen.py`, `02_build_scene.py`, `03_animate.py` (+`03a_headset.py`, `03b_effects.py`, `03c_camera.py`). `beats.json` written.

Camera: one camera `CAM_Film`, one Catmull-Rom path through 35 framings (see `scripts/03c_camera.py`, list `K`). In the two bullet-chase stretches (f1–330, f955–1078) the camera follows the bullet by interpolated offsets, so it never loses it.
Path: rear 3/4 chase over the fence → side-on over the lawn → behind the bullet into the window → through the shard hole → follow-cam to his head → orbit (behind, over his right shoulder onto hands, low front past the monitor, round to his left) → macro on the cup → down into the cutaway → pull back, whip-pan with the ricochet → push in on the wall hole → swing back to him → hands with the headset → face close-up → over his right shoulder onto the hole.

Known, fixing for C: background too soft in the follow-cam at 4–5 s; the air trail reads orange during the ricochet; the held headset blocks his face at about 22 s; the headset shell is plain; the orbit is dominated by the chair back at 5–6 s; the cutaway needs a clearer read.
