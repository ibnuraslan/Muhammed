# Nvidia Ch4–5 farm master

One self-contained .blend (fade in 1 s, Chapter 4, Chapter 5, fade out 1.5 s), split for git (GitHub 100 MB limit).

Reassemble and check:

    cat nvidia_ch45.blend.part* > nvidia_ch45.blend
    sha256sum -c nvidia_ch45.blend.sha256

Then render the master scene NVIDIA_CH45 (frames 1–10155, 24 fps, 1920×816), e.g. `blender -b nvidia_ch45.blend -a`.
All 46 shot scenes are appended (no linked libraries); images, fonts and both voiceovers are packed.
Cycles 32 samples, adaptive 0.05, denoise, motion blur off, alpha off. Original house grade (look="plain").
Audio for the edit: ../nvidia_ch45_AUDIO_with_voice.wav / _no_voice.wav (423.125 s = 10155 frames).
