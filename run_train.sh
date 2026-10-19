#!/bin/bash
# Sequential training (each run uses both cores). Resumable via checkpoints.
cd "$(dirname "$0")"; export PIVOT1_DIR=.
for s in 0 1 2 3 4; do
  for m in residualS residual; do
    [ -f done_${m}_s${s} ] && continue
    python3 train_es.py $m $s 20 >> train.log 2>&1 && touch done_${m}_s${s}
  done
done
echo ALLDONE >> train.log
