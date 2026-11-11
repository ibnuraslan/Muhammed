#!/bin/bash
# One-time setup of the render pipeline on a fresh cloud machine (about 5-10 minutes).
#   bash pipeline/setup.sh            -> creates ~/render_env with venv + MakeHuman data
#   source ~/render_env/env.sh        -> every new shell before running scenes
set -e
W="${RENDER_ENV:-$HOME/render_env}"
mkdir -p "$W"; cd "$W"

# system packages: 7-Zip (MakeHuman installer), EGL (skia), ffmpeg (cuts), Inter + JetBrains Mono fonts (UI/labels)
if command -v apt-get >/dev/null; then
  (apt-get update -qq && apt-get install -y -qq 7zip libegl1 ffmpeg fonts-inter fonts-jetbrains-mono) >/dev/null 2>&1 || \
  (sudo apt-get update -qq && sudo apt-get install -y -qq 7zip libegl1 ffmpeg fonts-inter fonts-jetbrains-mono) >/dev/null 2>&1 || true
fi

# Python 3.13 venv with Blender as a module (bpy 5.2.3 needs Python 3.13)
if [ ! -x venv/bin/python ]; then python3.13 -m venv venv 2>/dev/null || python3 -m venv venv; fi
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q "bpy==5.2.3" "skia-python" "numpy" "scipy" "pillow" "numba" "faster-whisper"

# MakeHuman 1.2 community assets (CC0 base mesh, targets, rigs, clothes, hair, skins) - data only, no executables
if [ ! -d mh/inst ]; then
  mkdir -p mh && cd mh
  for i in 1 2 3 4; do
    curl -sS -C - --max-time 1200 -o mh.zip https://download.tuxfamily.org/makehuman/releases/makehuman-community-1.2.0-windows.zip && break
    sleep $((2 ** i))
  done
  unzip -o -q mh.zip makehuman-community-1.2.0-windows.exe
  7z x -y -oinst makehuman-community-1.2.0-windows.exe -x'!*.exe' -x'!*.dll' -x'!*.pyd' >/dev/null
  rm -f mh.zip makehuman-community-1.2.0-windows.exe
  cd ..
fi
MHD="$W/mh/inst/makehuman/data"

cat > env.sh <<EOF
source "$W/venv/bin/activate"
export MH_DATA="$MHD"
EOF
echo "ready. run:  source $W/env.sh"
