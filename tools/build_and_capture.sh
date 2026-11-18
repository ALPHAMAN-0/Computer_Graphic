#!/bin/bash
# Builds both programs, saves a screenshot of each first frame and the
# console output of Problem 1 into Report/. Run from the repository root:
#     bash tools/build_and_capture.sh
set -e
cd "$(dirname "$0")/.."

OUT=Report
BIN=build
mkdir -p "$OUT/screenshots" "$BIN"

if [ "$(uname)" = "Darwin" ]; then
    LIBS="-framework OpenGL -framework GLUT"
    FLAGS="-DGL_SILENCE_DEPRECATION"
else
    LIBS="-lGL -lGLU -lglut"
    FLAGS=""
fi

build_and_shoot() {     # $1 = scene source, $2 = short name
    c++ $FLAGS -Wall "$1" $LIBS -o "$BIN/$2"
    c++ $FLAGS -DSCENE_FILE="\"../$1\"" tools/capture_frame.cpp $LIBS -o "$BIN/${2}_capture"
    SHOT="$BIN/$2.ppm" "./$BIN/${2}_capture" > "$OUT/${2}_console_output.txt"
    python3 -c "from PIL import Image; Image.open('$BIN/$2.ppm').save('$OUT/screenshots/$2.png')"
    echo "built $BIN/$2, screenshot $OUT/screenshots/$2.png"
}

build_and_shoot Problem1_Bangladesh_Tribute_Scene/bangladesh_tribute_scene.cpp problem1
build_and_shoot Problem2_Village_Scenery/village_scenery.cpp problem2
