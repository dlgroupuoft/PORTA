#!/usr/bin/env bash
set -uo pipefail
export PATH=/usr/bin:/usr/local/bin:/usr/sbin:/sbin:$PATH

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
cd "$FUZZER_DIR"

for EXP in exp1 exp2 exp3; do
    echo "============================================================"
    echo "Starting evaluation $EXP at $(date -Iseconds)"
    echo "============================================================"
    
    PROFILE_ARGS=""
    for f in src/profiles/*evaluation-${EXP}_*.json; do
        base=$(basename "$f" | sed "s/_evaluation-${EXP}_[0-9_]*.json//")
        plat=$(echo "$base" | sed 's/_\(oidc_jwt\|saml\)$//')
        proto=$(echo "$base" | grep -oP '(oidc_jwt|saml)$' | sed 's/oidc_jwt/oidc/')
        PROFILE_ARGS="$PROFILE_ARGS --profile ${plat}:${proto}=$f"
    done
    
    bash scripts/run_all_experiments.sh \
        --exp-name "evaluation/${EXP}" \
        --seq-per-inv 10 \
        $PROFILE_ARGS
    
    echo "============================================================"
    echo "Finished evaluation $EXP at $(date -Iseconds)"
    echo "============================================================"
    echo ""
done

echo "ALL EVALUATIONS COMPLETE at $(date -Iseconds)"
