# GoatOwner_v006c: stick drop fix (Connect32)

This is v006b (approved, d05f079) with one change. The director's PROPMOVE check found the stick standing upright in the air behind the owner at f961–973, then sinking to the ground by about f1008 with no hand near it.

Now he drops it at the first hit (f960):
- It leaves his raised right hand.
- It falls under gravity, flung down by the impact (about 0.4 s, 24 frames), tipping over as it falls.
- It lands flat near his feet by f984, with a small bounce, then lies still.

Nothing else changed: animation, camera (including the v006b whip), look and beat frames are identical.

`GoatOwner_v006c_60fps.blend` is 69 MB: packed, compressed, and a plain git file.

## Files in `review/`
- `stick_drop_f930-1010.jpg`: frames 930, 945, 958, 962, 966, 970, 974, 980, 990 and 1010.
- `qa_check_v006c.json`: added when the scan finishes (PROPMOVE expected only on the falling frames f960–984).
