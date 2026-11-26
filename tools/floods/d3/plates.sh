#!/bin/sh
# Floods series d3: build every big plate and its dry twin of one area into $2 (SVG, 3400 px PNG
# and `info` counts), without archiving. Usage: tools/floods/d3/plates.sh shockoe|manchester <out-dir>
area=${1:?area}; out=${2:?out dir}
case $area in
  shockoe) plates="1771:1788 1936:1936 1969:1969 1972:1972 1985:1985 1996:1996 gaston-b:2004 2020:2020 agnes-today:2026" ;;
  manchester) plates="agnes-today:2026 agnes-today-nowall:2026 1996:2026 2020:2026" ;;
esac
mkdir -p "$out"
for p in $plates; do
  f=${p%%:*}; y=${p##*:}
  for v in "$f" "$f-dry"; do
    node bin/isoscape.js build richmond-floods-$area --year "$y" --flood "$v" --png --width 3400 --no-archive --out "$out" 2>&1 | grep -E "ms|rror"
    node bin/isoscape.js info richmond-floods-$area --year "$y" --flood "$v" > "$out/richmond-floods-$area-$y-flood-$v.info.json" 2>/dev/null
  done
done
