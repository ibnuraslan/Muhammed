# Patch for nvidia_ch45.blend: shot c5_17 (Ch5 8A, warehouse lights off)

In the delivered master the high-bay lights in this shot switch off on frame drivers written for the original 5 s
Ch2 cut, so master frames 7651-7875 (9.4 s) render near-black. This patch re-times the lights to the 13.5 s
Ch5 cut (rows off from local frame 40, every 53 frames; dark only for the last ~0.8 s).

- nvidia_ch45_patch_c5_17.blend: scene PATCH_C5_17, frames 1-325, built the same way as the master (factory master
  scene + the baked shot as a sequencer strip) so its colour/brightness matches the master exactly (checked: local
  frame 20 = master 7570, mean 0.348 both). Cycles 32 samples, adaptive 0.05, denoise, motion blur off, PNG.
- In the edit: lay the 325 rendered frames over master frames 7551-7875 (Ch5 2:23.7, 13.5 s). Nothing else changes.
sha256 4537fa936135f7ca16b423b16452d38443aaba1eb7f020832e9436f29c2698e6
