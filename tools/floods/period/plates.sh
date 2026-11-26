#!/bin/sh
# Dev tool (floods series, period city): build the dated flood plates of the two areas into $1,
# as SVG and a 3400 px PNG, without archiving, and write each build's counts (`info`) beside it.
# Usage: tools/floods/period/plates.sh <out-dir> [area:flood:year ...]
out=${1:?out dir}; shift
plates=${*:-"shockoe:1969:1969 shockoe:1972:1972 shockoe:1985:1985 shockoe:1996:1996 shockoe:gaston-a:2004 shockoe:2020:2020 manchester:1969:1969 manchester:1972:1972 manchester:1985:1985 manchester:1996:1996 manchester:2020:2020"}
mkdir -p "$out"
for p in $plates; do
  a=${p%%:*}; r=${p#*:}; f=${r%%:*}; y=${r##*:}
  node bin/isoscape.js build richmond-floods-$a --year "$y" --flood "$f" --png --width 3400 --no-archive --out "$out" 2>&1 | grep -E "ms|rror"
  node bin/isoscape.js info richmond-floods-$a --year "$y" --flood "$f" > "$out/richmond-floods-$a-$y-flood-$f.info.json" 2>/dev/null
done
