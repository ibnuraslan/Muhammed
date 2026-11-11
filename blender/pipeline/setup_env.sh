#!/bin/bash
# Studio setup for the Connect chats: Blender 5.2.2, MPFB2 + MakeHuman CC0 assets, Git LFS, faster-whisper.
# Idempotent; every step is skipped when already done. Paths can be overridden for testing.
set -euo pipefail
PREFIX=${PREFIX:-/opt}; BHOME=${BHOME:-/root}
BV=5.2.2; BD=$PREFIX/blender/blender-$BV-linux-x64; DL=$PREFIX/assets/dl
MPFB_URL="https://extensions.blender.org/download/sha256:c075b3e9b94b8e5556a5f03f4653602d02ea306de08126e8f55ed6dee28a2dad/add-on-mpfb-v2.0.18.zip"
MH_URL="https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip"
mkdir -p "$PREFIX/blender" "$DL" "$PREFIX/bin"
if [ ! -x "$BD/blender" ]; then
  curl -fsSL --retry 4 "https://download.blender.org/release/Blender5.2/blender-$BV-linux-x64.tar.xz" | tar -xJ -C "$PREFIX/blender"
fi
ln -sf "$BD/blender" "$PREFIX/bin/blender"
MPFB_DIR=$BHOME/.config/blender/5.2/extensions/user_default/mpfb
if [ ! -d "$MPFB_DIR" ]; then
  curl -fsSL --retry 4 -o "$DL/mpfb.zip" "$MPFB_URL"
  HOME=$BHOME "$BD/blender" -b --factory-startup --command extension install-file -r user_default -e "$DL/mpfb.zip"
  rm -f "$DL/mpfb.zip"
fi
UD=$BHOME/.config/blender/5.2/extensions/.user/user_default/mpfb/data
if [ ! -d "$UD/clothes" ]; then
  for i in 1 2 3 4 5; do curl -fsSL -C - -o "$DL/mh.zip" "$MH_URL" && break; sleep $((i*4)); done
  mkdir -p "$UD" && unzip -q -o "$DL/mh.zip" -d "$UD" && rm -f "$DL/mh.zip"
fi
git lfs install --skip-repo >/dev/null 2>&1 || true
if [ ! -x "$PREFIX/venv/whisper/bin/python" ]; then
  python3 -m venv "$PREFIX/venv/whisper" && "$PREFIX/venv/whisper/bin/pip" -q install faster-whisper
fi
echo "STUDIO_READY blender=$BD"
