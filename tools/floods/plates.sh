#!/bin/sh
# Dev tool (floods series, d1): build every plate of regions/richmond-floods-d1.json into $1,
# as SVG and a 3400 px PNG, without archiving. Usage: tools/floods/plates.sh <out-dir> [flood:year ...]
out=${1:?out dir}; shift
plates=${*:-"1771:1788 1771-range:1788 1936:1936 1969:1969 1972:1972 1985:1985 1996:1996 2020:2020 agnes-today:2026 gaston-a:2004 gaston-b:2004"}
for p in $plates; do
  f=${p%%:*}; y=${p##*:}
  node bin/isoscape.js build richmond-floods-d1 --year "$y" --flood "$f" --png --width 3400 --no-archive --out "$out" 2>&1 | grep -E "ms|rror"
done
