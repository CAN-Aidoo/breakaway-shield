#!/bin/bash
# Resumable chain: finish pivot training, then test and mismatch evaluation (confirm runs after the analysis).
cd "$(dirname "$0")"
./run_train.sh
for s in 0 1 2 3 4; do for m in residualS residual; do [ -f done_${m}_s${s} ] || { echo "TRAIN INCOMPLETE" >> eval_pivot.log; exit 1; }; done; done
for s in test mismatch; do
  [ -f results/pivot_$s.json ] && continue
  python3 evaluate5.py pivot $s >> eval_pivot.log 2>&1 || { echo "FAILED $s" >> eval_pivot.log; exit 1; }
done
echo EVALDONE >> eval_pivot.log
