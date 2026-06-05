#!/usr/bin/env bash
# Post-deploy smoke test for snemovna.datatimes.cz/digest
# Usage: ./scripts/smoke-test.sh [base_url]
# Exit code 0 = all checks passed, non-zero = failure.

set -euo pipefail

BASE=${1:-"https://snemovna.datatimes.cz"}
DIGEST="$BASE/digest"
FAIL=0

ok()   { echo "  OK  $1"; }
fail() { echo "FAIL  $1"; FAIL=1; }

echo "Smoke-testing $DIGEST ..."

# 1. Events list page returns 200
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DIGEST/events")
[ "$STATUS" = "200" ] && ok "/events HTTP $STATUS" || fail "/events HTTP $STATUS (expected 200)"

# 2. CSS asset in the page is actually reachable (200)
EVENTS_HTML=$(curl -s "$DIGEST/events")
CSS_URL=$(echo "$EVENTS_HTML" | grep -oP '(?<=href=")[^"]*\.css[^"]*' | head -1)
if [ -z "$CSS_URL" ]; then
  fail "No CSS link found in /events HTML"
else
  # Resolve relative URLs against the digest origin
  if [[ "$CSS_URL" != http* ]]; then CSS_URL="$BASE$CSS_URL"; fi
  CSS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CSS_URL")
  [ "$CSS_STATUS" = "200" ] && ok "CSS asset HTTP $CSS_STATUS ($CSS_URL)" || fail "CSS asset HTTP $CSS_STATUS ($CSS_URL)"
fi

# 3. A known event page returns 200
EVENT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DIGEST/events/2972")
[ "$EVENT_STATUS" = "200" ] && ok "/events/2972 HTTP $EVENT_STATUS" || fail "/events/2972 HTTP $EVENT_STATUS (expected 200)"

# 4. OG title tag is present on event page
EVENT_HTML=$(curl -s "$DIGEST/events/2972")
echo "$EVENT_HTML" | grep -q 'property="og:title"' && ok "og:title present" || fail "og:title missing"

# 5. Search page returns 200
SEARCH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DIGEST/search")
[ "$SEARCH_STATUS" = "200" ] && ok "/search HTTP $SEARCH_STATUS" || fail "/search HTTP $SEARCH_STATUS (expected 200)"

echo ""
if [ $FAIL -eq 0 ]; then
  echo "All checks passed."
else
  echo "One or more checks FAILED."
  exit 1
fi
