#!/usr/bin/env bash
# Builds coca_cola_new_year_ad.mp4: renders 375 frames (1920x1080, 25 fps), synthesises audio, muxes.
set -euo pipefail
cd "$(dirname "$0")"
WORK="${WORK:-./build}"
mkdir -p "$WORK"
node render.js "$WORK/frames" 25 15
python3 audio.py "$WORK/soundtrack.wav"
ffmpeg -y -framerate 25 -i "$WORK/frames/f_%04d.jpg" -i "$WORK/soundtrack.wav" \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -profile:v high -tune film \
  -c:a aac -b:a 192k -shortest -movflags +faststart coca_cola_new_year_ad.mp4
