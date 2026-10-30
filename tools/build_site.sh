#!/usr/bin/env bash
# Build the static demo site into site/ (deployed to the gh-pages branch).
#
#   index.html       Part 1 (first-attempt generators), Part 2 (squeak resyntheses),
#                    Details (summary + links)
#   hinge-lab.html   The physics model: screenshot + preset players
#   analysis/        Full reference analysis, publish mode (no reference audio)
#
# Requires: .venv (uv venv && uv pip install numpy matplotlib), cargo, and the local
# reference recording at references/squeak_yt_mono.wav (not in git; see docs/phases.md).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY=.venv/bin/python
SITE=site
SOURCE_URL="https://www.youtube.com/watch?v=TspuiaFX2YQ"
REFERENCE=references/squeak_yt_mono.wav
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

[ -x "$PY" ] || { echo "Missing .venv: run 'uv venv && uv pip install numpy matplotlib'"; exit 1; }
[ -f "$REFERENCE" ] || { echo "Missing $REFERENCE (see docs/phases.md)"; exit 1; }

rm -rf "$SITE"
mkdir -p "$SITE/audio/part1" "$SITE/audio/hinge" "$SITE/images"
cp site-src/style.css "$SITE/"
touch "$SITE/.nojekyll"

echo "== Part 1: regenerate first-attempt sounds"
for g in thud button_click explosion flying_saucer gravel_footsteps siren siren_3d hinge_creak; do
  "$PY" "${g}_generator.py" > /dev/null
done
# The wind-whistling generator was the first "door creak" attempt
"$PY" -c "from wind_whistling_generator import generate_wind_whistling_wav as g; g('door_creak.wav')" > /dev/null
for wav in thud button_click explosion flying_saucer_doppler gravel_footsteps siren \
           siren_us_wail_doppler siren_eu_hilo_doppler door_creak hinge_creak; do
  cp "$wav.wav" "$SITE/audio/part1/"
done

echo "== Hinge Lab presets and screenshot"
(cd hinge-lab && cargo build --release --quiet)
HL=hinge-lab/target/release/hinge-lab
for p in squeaky oiled horror_slow rusty_groan fast_swing cabinet_tiny; do
  "$HL" render --preset "$p" --out "$SITE/audio/hinge/$p.wav" > /dev/null
done
"$HL" screenshot images/hinge-lab-ui.png squeaky > /dev/null  # renders in the background

echo "== Part 2: reference analysis (publish mode, no reference audio)"
"$PY" tools/squeak_analysis.py "$REFERENCE" "$SITE/analysis" \
  --no-reference-audio --source-url "$SOURCE_URL" > /dev/null 2>&1
sed -i '' "s|<body>|<body><p><a href='../index.html'>← Back to the demo</a></p>|" "$SITE/analysis/index.html"
cp "$SITE/analysis/overview.png" images/analysis-overview.png
cp "$SITE/analysis/ev2.png" images/analysis-stepped.png

echo "== Pages"
"$PY" tools/build_page.py "$SITE"
cp images/screenshot.png images/hinge-lab-ui.png images/analysis-overview.png \
   images/analysis-stepped.png "$SITE/images/"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1280,1600 \
  --screenshot="$ROOT/images/analysis-page.png" \
  "file://$ROOT/$SITE/analysis/index.html" > /dev/null 2>&1
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1100,1500 \
  --screenshot="$ROOT/images/demo-page.png" \
  "file://$ROOT/$SITE/index.html" > /dev/null 2>&1

if find "$SITE" -name '*_ref.wav' | grep -q .; then
  echo "ERROR: reference audio found in $SITE; refusing to continue"; exit 1
fi
echo "Built $SITE/ ($(du -sh "$SITE" | cut -f1))"
