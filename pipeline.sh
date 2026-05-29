#!/bin/bash
# Full pipeline: sync → transcribe → summarize → upload → git push
# Called from cron. Each step logs separately; pipeline stops on fatal errors.

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"

PYTHON="$(which python3)"
DATE="$(date '+%Y-%m-%d %H:%M:%S')"
LOG="$LOG_DIR/pipeline_$(date '+%Y%m%d').log"

log() { echo "[$DATE] $*" | tee -a "$LOG"; }

cd "$DIR"

log "=== Pipeline start ==="

# 1 — Sync: download new events, metadata, documents
log "--- sync.py ---"
$PYTHON sync.py >> "$LOG" 2>&1 || { log "sync.py failed"; exit 1; }

# 2 — Transcribe: prefer knowledge-order categories; skip already-done
log "--- transcribe.py ---"
$PYTHON transcribe.py --order knowledge >> "$LOG" 2>&1 || log "transcribe.py exited non-zero (may be ok)"

# 3 — Summarize: process transcribed events not yet summarised
log "--- summarize.py ---"
$PYTHON summarize.py --model gemini-3.1-flash-lite >> "$LOG" 2>&1 || log "summarize.py exited non-zero (may be ok)"

# 4 — Upload screenshots to B2 and rewrite JSON paths
log "--- upload_screenshots.py ---"
$PYTHON upload_screenshots.py >> "$LOG" 2>&1 || log "upload_screenshots.py exited non-zero"

# 5 — Commit and push new/updated summaries
log "--- git push ---"
git add summaries/json/ summaries/md/ >> "$LOG" 2>&1
if git diff --cached --quiet; then
    log "No new summaries to commit"
else
    git commit \
        --author="Michal Skop <michal.skop@kohovolit.eu>" \
        -m "Auto: new summaries $(date '+%Y-%m-%d')" >> "$LOG" 2>&1
    git push >> "$LOG" 2>&1
    log "Pushed new summaries"
fi

log "=== Pipeline done ==="
