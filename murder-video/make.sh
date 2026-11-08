#!/usr/bin/env bash
# One-command build:  ./make.sh crippen      (uses stories/crippen.json)
#                     ./make.sh crippen --stills   (quick preview: one image per shot)
set -euo pipefail
cd "$(dirname "$0")"
STORY="${1:-crippen}"; shift || true

# first-time setup
[ -d node_modules/three ] || npm install
python3 -c "import piper, scipy, numpy" 2>/dev/null || pip install piper-tts scipy numpy
VOICES=assets/voices
HF=https://huggingface.co/rhasspy/piper-voices/resolve/main/en
for v in en_US/ryan/high/en_US-ryan-high en_US/joe/medium/en_US-joe-medium \
         en_GB/northern_english_male/medium/en_GB-northern_english_male-medium \
         en_GB/alan/medium/en_GB-alan-medium en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium; do
  n=$(basename "$v")
  [ -f "$VOICES/$n.onnx" ] || { mkdir -p "$VOICES"; curl -sSL -o "$VOICES/$n.onnx" "$HF/$v.onnx"; curl -sSL -o "$VOICES/$n.onnx.json" "$HF/$v.onnx.json"; }
done

python3 tools/build_audio.py "stories/$STORY.json"
node tools/render.js "$STORY" "$@"
