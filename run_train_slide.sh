#!/bin/bash
cd "$(dirname "$0")"
for s in 0 1 2 3 4; do for m in residualS residual; do
  [ -f done_slide_${m}_s${s} ] && continue
  python3 train_slide.py $m $s 20 >> train_slide.log 2>&1 && touch done_slide_${m}_s${s}
done; done
echo ALLDONE >> train_slide.log
