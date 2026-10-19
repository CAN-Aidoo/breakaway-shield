#!/bin/bash
# Wait for sliding training, then run test and mismatch sets (confirm runs only after the test analysis is written).
cd "$(dirname "$0")"
until [ -f done_slide_residual_s4 ]; do sleep 30; done
for s in test mismatch; do
  [ -f results/slide_$s.json ] && continue
  python3 evaluate5.py slide $s >> eval_slide.log 2>&1 || echo "FAILED $s" >> eval_slide.log
done
echo EVALDONE >> eval_slide.log
