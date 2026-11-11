#!/bin/bash
# full rebuild: humans -> scene -> anim
set -e
cd "$(dirname "$0")"
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b --python scripts/01_build_woman.py -- humans.blend > /tmp/claude-0/b01.log 2>&1
$B -b humans.blend --python scripts/02_build_scene.py -- scene.blend > /tmp/claude-0/b02.log 2>&1
$B -b scene.blend --python scripts/03_animate.py -- anim.blend > /tmp/claude-0/b03.log 2>&1
grep -h -E "Traceback|Error:|DONE" /tmp/claude-0/b0[123].log | grep -v nodeservice || true
