#!/usr/bin/env bash
# Post-deploy smoke test for snemovna.datatimes.cz/digest
# Usage: ./scripts/smoke-test.sh [base_url]
# Exit code 0 = all checks passed, non-zero = failure.

set -euo pipefail

BASE=${1:-"https://snemovna.datatimes.cz"}
DIGEST="$BASE/digest"
FAIL=0

check() {
  local name="$1"; local result="$2"; local want="$3"
  if echo "$result" | grep -q "$want"; then
    echo "  OK  $name"
  else
    echo "FAIL  $name (expected to contain: $want)"
    FAIL=1
  fi
}

echo "Smoke-testing $DIGEST ..."

# 1. Events list page returns 200
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DIGEST/events")
[ "$STATUS" = "200" ] && echo "  OK  /events HTTP $STATUS" || { echo "FAIL  /events HTTP $STATUS"; FAIL=1; }

# 2. CSS assets use /digest prefix (proves NEXT_PUBLIC_BASE_PATH is correct)
HTML=$(curl -s "$DIGEST/events")
check "asset path has /digest prefix" "$HTML" '/digest/_next/'

# 3. A known event page returns 200
EVENT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DIGEST/events/2972")
[ "$EVENT_STATUS" = "200" ] && echo "  OK  /events/2972 HTTP $EVENT_STATUS" || { echo "FAIL  /events/2972 HTTP $EVENT_STATUS"; FAIL=1; }

# 4. OG title tag is present on event page
EVENT_HTML=$(curl -s "$DIGEST/events/2972")
check "og:title present" "$EVENT_HTML" 'property="og:title"'

# 5. Search page returns 200
SEARCH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DIGEST/search")
[ "$SEARCH_STATUS" = "200" ] && echo "  OK  /search HTTP $SEARCH_STATUS" || { echo "FAIL  /search HTTP $SEARCH_STATUS"; FAIL=1; }

echo ""
if [ $FAIL -eq 0 ]; then
  echo "All checks passed."
else
  echo "One or more checks FAILED."
  exit 1
fi
