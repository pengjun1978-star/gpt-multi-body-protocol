#!/bin/zsh
set -euo pipefail
mode="${1:-dry-run}"
root="${2:-$HOME/.codex/multi-body-v1}"
case "$mode" in dry-run|install|repair|upgrade) ;; *) print -u2 "usage: $0 {dry-run|install|repair|upgrade} [root]"; exit 64;; esac
dirs=(tasks/inbox tasks/running tasks/completed tasks/failed tasks/orphaned callbacks/outbox callbacks/pending callbacks/sent callbacks/failed receipts leases logs)
print "mode=$mode root=$root"
print "protected=AI/Ollama/CUDA business configs, model parameters, user projects, business services"
for d in $dirs; do print "ensure $root/$d"; done
[[ "$mode" == dry-run ]] && exit 0
for d in $dirs; do mkdir -p "$root/$d"; done
mkdir -p "$root"/schemas "$root"/registries
print "installed_or_repaired=$root"
