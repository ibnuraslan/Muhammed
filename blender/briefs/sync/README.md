# VO sync records

`NN.anchors.json` maps source-film frames to delivered (VO-synced) frames for film NN:
`{"fps": 60, "end": <delivered frame_end>, "anchors": [[source_frame, delivered_frame, ...], ...]}`.

- **01–10:** the exact files used for the retime.
- **11, 13–15, 18–21, 24, 27:** rebuilt on Nov 15 from each film's `beats.json` and the VO word times, because the original sync records were deleted. Each beat start is exact; the film ends are approximate.
- **Missing (sync records lost):** 16, 17, 22, 25, 26, 28–35.
  - 28 needed no retime; it was built to the VO.
  - For the others, the delivered package itself is correct.
- **Batch 2:** build to the VO from the start (`pipeline/CONNECT_BRIEF_v2.md`), so no record is needed.
