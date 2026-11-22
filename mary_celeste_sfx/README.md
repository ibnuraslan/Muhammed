# Mary Celeste: procedural SFX and ambience

Every sound is synthesised in `sfxlib.py`: no samples, so there are no licence issues (see CREDITS.txt).

    pip install numpy scipy soundfile pyloudnorm   # plus ffmpeg
    python3 -I engine.py spec_p4.py <vo_timings.json> <MaryCeleste_Part4_VO.mp3> 3951 out/P4 P4

Inputs: `vo_timings.json` from claude/mary-celeste-pN (`mary_celeste_pN/vo/`) and the VO from claude/mary-celeste-vo.
Outputs: `MaryCeleste_PN_SFX.wav` (−20 LUFS), `_MIX.wav` (VO ducked 6 dB, −14 LUFS, −1 dBTP) and `_CUES.txt`, all 48 kHz/24-bit stereo at the exact part length.
Done: P1, P4. Not started: P2, P3, P5 (on hold until the user has listened).
