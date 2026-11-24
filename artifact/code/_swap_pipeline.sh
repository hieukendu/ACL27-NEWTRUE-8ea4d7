#!/bin/bash
# helper used once during the run: when the main grid of mistral-7b is complete, stop pipeline 1 (by PID) and start pipeline 2
cd "$(dirname "$0")/.."
P1=$1; P2=$2
while ! grep -q "mistral-7b 2450 / 2450" results/pipeline.log; do sleep 20; done
kill $P1; kill $P2; sleep 1
for c in $(pgrep -P $P2); do pkill -P $c; kill $c; done
sleep 8
nohup ./code/run_pipeline2.sh > results/pipeline2.log 2>&1 &
echo swapped
