#!/bin/bash
# Full pipeline: sync → transcribe → summarize → upload → git push
# Called from cron. Each step logs separately; pipeline stops on fatal errors.

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"

PYTHON="$(which python3)"
LOG="$LOG_DIR/pipeline_$(date '+%Y%m%d').log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

# Count events by state — uses actual files on disk, not metadata flags
counts() {
    $PYTHON - <<'EOF'
import json
from pathlib import Path

meta   = json.load(open("metadata.json"))
events = list(meta["events"].values())

# IDs that have a summary JSON on disk (filename is authoritative)
summary_ids = {p.name.split("_")[1] for p in Path("summaries/json").glob("summary_*.json")}

total       = len(events)
has_final   = sum(1 for e in events if list(Path("final").glob(f'event_{e["id"]}_*.md')))
has_summary = sum(1 for e in events if e["id"] in summary_ids)
pending     = has_final - has_summary

print(f"total={total} transcribed={has_final} summarized={has_summary} pending_summary={pending}")
EOF
}

cd "$DIR"

log "=== Pipeline start ==="
log "$(counts)"

# 1 — Sync: download new events, metadata, documents
log "--- sync.py ---"
$PYTHON sync.py >> "$LOG" 2>&1 || { log "sync.py failed"; exit 1; }
log "After sync: $(counts)"

# 2 — Transcribe: prefer knowledge-order categories; skip already-done
# Uses Groq API (no local model required). GROQ_API_KEY must be in .env or environment.
log "--- transcribe.py ---"
$PYTHON transcribe.py --preset groq-large-v3 --order knowledge >> "$LOG" 2>&1 || log "transcribe.py exited non-zero (may be ok)"
log "After transcribe: $(counts)"

# 3 — Summarize: process transcribed events not yet summarised
log "--- summarize.py ---"
log "Starting summarize — $(counts | grep -oP 'pending_summary=\K\d+') event(s) to process"
$PYTHON summarize.py --model gemini-3.1-flash-lite >> "$LOG" 2>&1 || log "summarize.py exited non-zero (may be ok)"
log "After summarize: $(counts)"

# 4 — Upload screenshots to B2 and rewrite JSON paths
log "--- upload_screenshots.py ---"
$PYTHON upload_screenshots.py >> "$LOG" 2>&1 || log "upload_screenshots.py exited non-zero"

# 5 — Commit and push new/updated summaries
log "--- git push ---"
git add summaries/json/ summaries/md/ >> "$LOG" 2>&1
if git diff --cached --quiet; then
    log "No new summaries to commit"
else
    NEW=$(git diff --cached --name-only | grep -c 'summaries/json/' || true)
    git commit \
        --author="Michal Skop <michal.skop@kohovolit.eu>" \
        -m "Auto: new summaries $(date '+%Y-%m-%d')" >> "$LOG" 2>&1
    git push >> "$LOG" 2>&1
    log "Pushed $NEW new/updated summary JSON(s)"

    # 6 — Rebuild and redeploy web site (only when there are new summaries)
    log "--- vercel deploy ---"
    cd "$DIR/web"
    NEXT_PUBLIC_BASE_PATH=/digest NEXT_PUBLIC_ASSET_PREFIX=https://cz-psp-videoarchive-michalskops-projects.vercel.app npx vercel build --prod >> "$LOG" 2>&1
    npx vercel deploy --prebuilt --prod --archive=tgz >> "$LOG" 2>&1
    cd "$DIR"
    log "Web site redeployed"
fi

log "=== Pipeline done ==="
