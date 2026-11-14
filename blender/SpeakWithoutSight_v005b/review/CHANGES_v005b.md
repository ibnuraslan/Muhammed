# v005b: one fix on top of v005 (director review, Nov 14 22:23). Nothing else changed.
- Frames 681–1101 (x-ray throat beat): the parlour now stays visible behind them. Before, they sat in an empty blue void.
  - The ExplainerDome backdrop is hidden for the whole film (`hide_render` and `hide_viewport`).
  - The room light no longer dims over that beat, and the studio lights stay off.
  - The x-ray throat cross-section and the pulse dots are unchanged.
- `review/preview.mp4` and `preview_pages/`: frames 676–1106 were re-rendered from this exact build. The other frames are from v005 and are unchanged, since only the dome and light keys over that range changed.
- `qa_check`: same counts as v005, with INSIDE now 0 (the dome was the cause). clip_scan is unaffected: there were no animation changes, and v005 had BAD_RANGES [].
