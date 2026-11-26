#!/bin/sh
# Dev tool (floods series, period city): prove that published dated views are unchanged by the
# evidence layer. Builds each view in a checkout of the base commit ($1) and in this tree, and
# compares the SVGs byte for byte (cmp). Usage: tools/floods/period/unchanged.sh <base-tree> <scratch>
# VIEWS="region:year[:with[:flood]] ..." overrides the list; a view whose region the base lacks is skipped.
base=${1:?base tree}; tmp=${2:?scratch dir}
here=$(pwd)
views=${VIEWS:-"richmond-downtown-time:1925 richmond-downtown-time:1950 richmond-downtown-time:1960 richmond-downtown-time:1970 richmond-downtown-time:2026 jackson-ward:1925 jackson-ward:1952 jackson-ward:1959 jackson-ward:2026 jackson-ward:1952:count richmond-1937:1937 richmond-streetcars:1925 richmond-floods-d1:1972:-:1972"}
fail=0
for v in $views; do
  r=$(echo $v | cut -d: -f1); y=$(echo $v | cut -d: -f2); w=$(echo $v | cut -d: -f3); f=$(echo $v | cut -d: -f4)
  extra=""; [ -n "$w" ] && [ "$w" != "-" ] && extra="--with $w"; [ -n "$f" ] && extra="$extra --flood $f"
  if [ ! -f "$base/regions/$r.json" ]; then echo "skip  $r $y (no such region in the base)"; continue; fi
  for side in base here; do
    dir=$tmp/$side; mkdir -p $dir
    if [ $side = base ]; then cd "$base"; else cd "$here"; fi
    node bin/isoscape.js build $r --year $y $extra --no-archive --out $dir/$r-$y-$w > /dev/null 2>&1
  done
  cd "$here"
  a=$(ls $tmp/base/$r-$y-$w/*.svg 2>/dev/null | head -1); b=$(ls $tmp/here/$r-$y-$w/*.svg 2>/dev/null | head -1)
  if [ -n "$a" ] && [ -n "$b" ] && cmp -s "$a" "$b"; then echo "same  $r $y $extra ($(wc -c < "$a") bytes, sha256 $(sha256sum < "$a" | cut -c1-16))"; else echo "DIFF  $r $y $extra [$a] [$b]"; fail=1; fi
  rm -rf $tmp/base/$r-$y-$w $tmp/here/$r-$y-$w
done
exit $fail
