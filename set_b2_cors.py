#!/usr/bin/env python3
"""
One-time script: set CORS rules on the B2 bucket so browsers can fetch
screenshots with fetch(url, { mode: "cors" }) — required for html2canvas
to include photos in card screenshots.

Usage:
    python3 set_b2_cors.py

Reads B2_KEY_ID, B2_APP_KEY, B2_BUCKET, B2_BUCKET_ID from .env (same as upload_screenshots.py).
"""

import json
import logging
import os
import sys
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("set-b2-cors")

CORS_RULES = [
    {
        "corsRuleName": "allowPublicGet",
        "allowedOrigins": ["*"],
        "allowedHeaders": ["*"],
        "allowedOperations": ["b2_download_file_by_id", "b2_download_file_by_name"],
        "exposeHeaders": [],
        "maxAgeSeconds": 3600,
    }
]


def _load_env() -> None:
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    _load_env()
    key_id = os.environ.get("B2_KEY_ID", "")
    app_key = os.environ.get("B2_APP_KEY", "")
    bucket_name = os.environ.get("B2_BUCKET", "")
    bucket_id = os.environ.get("B2_BUCKET_ID") or None

    if not key_id or not app_key or not bucket_name:
        log.error("B2_KEY_ID, B2_APP_KEY and B2_BUCKET must be set in .env")
        sys.exit(1)

    log.info("Authorizing with B2...")
    r = requests.get(
        "https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
        auth=(key_id, app_key), timeout=30,
    )
    r.raise_for_status()
    auth = r.json()

    if not bucket_id:
        log.info("Resolving bucket ID...")
        r = requests.post(
            f"{auth['apiUrl']}/b2api/v2/b2_list_buckets",
            headers={"Authorization": auth["authorizationToken"]},
            json={"accountId": auth["accountId"]},
            timeout=30,
        )
        r.raise_for_status()
        for b in r.json().get("buckets", []):
            if b["bucketName"] == bucket_name:
                bucket_id = b["bucketId"]
                break
        if not bucket_id:
            log.error(f"Bucket not found: {bucket_name}")
            sys.exit(1)

    log.info(f"Setting CORS rules on bucket {bucket_name} ({bucket_id})...")
    r = requests.post(
        f"{auth['apiUrl']}/b2api/v2/b2_update_bucket",
        headers={"Authorization": auth["authorizationToken"]},
        json={
            "accountId": auth["accountId"],
            "bucketId": bucket_id,
            "corsRules": CORS_RULES,
        },
        timeout=30,
    )
    r.raise_for_status()
    result = r.json()
    log.info("CORS rules set successfully:")
    log.info(json.dumps(result.get("corsRules", []), indent=2, ensure_ascii=False))
    log.info("Done. Verify with:")
    log.info("  curl -sI -H 'Origin: https://snemovna.datatimes.cz' 'https://f003.backblazeb2.com/file/cz-psp-videoarchive/screenshots/event_2753_highlight_00.jpg' | grep -i access-control")


if __name__ == "__main__":
    main()
