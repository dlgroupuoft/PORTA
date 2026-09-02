#!/usr/bin/env bash
# Wait for repeat_run.log to show completion, then start LLM judge runs
set -uo pipefail

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
cd "$FUZZER_DIR"

echo "Waiting for a1_no_examples_r3 to complete..."
while ! grep -q "ALL REPEAT RUNS COMPLETE" results/ablation/repeat_run.log 2>/dev/null; do
    sleep 60
done
echo "Repeat runs completed. Starting LLM-as-judge ablation..."

bash scripts/run_ablation_llm_judge.sh 2>&1 | tee results/ablation/llm_judge_run.log
