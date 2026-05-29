#!/usr/bin/env python3
"""
Upload screenshots to Backblaze B2 and rewrite screenshot_path in summary JSONs
from local paths to public B2 URLs.

Usage:
    python3 upload_screenshots.py           # upload all new screenshots
    python3 upload_screenshots.py --dry-run # show what would happen

Requires in .env (or environment):
    B2_KEY_ID=...
    B2_APP_KEY=...
    B2_BUCKET=cz-psp-videoarchive
    B2_BUCKET_ID=...   # optional — avoids needing listBuckets permission
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────────────

SCREENSHOTS_DIR = Path("summaries/screenshots")
SUMMARIES_DIR   = Path("summaries/json")
B2_REMOTE_PREFIX = "screenshots"   # path inside the bucket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("upload-screenshots")

# ── .env loader ───────────────────────────────────────────────────────────────

def _load_env() -> None:
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _b2_creds() -> tuple[str, str, str, str | None]:
    key_id   = os.environ.get("B2_KEY_ID", "")
    app_key  = os.environ.get("B2_APP_KEY", "")
    bucket   = os.environ.get("B2_BUCKET", "")
    bucket_id = os.environ.get("B2_BUCKET_ID") or None
    if not key_id or not app_key or not bucket:
        log.error("B2_KEY_ID, B2_APP_KEY and B2_BUCKET must be set in .env or environment")
        sys.exit(1)
    return key_id, app_key, bucket, bucket_id

# ── B2 API ────────────────────────────────────────────────────────────────────

def _authorize(key_id: str, app_key: str) -> dict:
    r = requests.get(
        "https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
        auth=(key_id, app_key), timeout=30,
    )
    r.raise_for_status()
    return r.json()


def _resolve_bucket_id(auth: dict, bucket_name: str, bucket_id: str | None) -> str:
    if bucket_id:
        return bucket_id
    r = requests.post(
        f"{auth['apiUrl']}/b2api/v2/b2_list_buckets",
        headers={"Authorization": auth["authorizationToken"]},
        json={"accountId": auth["accountId"]},
        timeout=30,
    )
    r.raise_for_status()
    for b in r.json().get("buckets", []):
        if b["bucketName"] == bucket_name:
            return b["bucketId"]
    raise ValueError(f"Bucket not found: {bucket_name}")


def _get_upload_url(auth: dict, bucket_id: str) -> dict:
    r = requests.post(
        f"{auth['apiUrl']}/b2api/v2/b2_get_upload_url",
        headers={"Authorization": auth["authorizationToken"]},
        json={"bucketId": bucket_id},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def _sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _upload_file(upload_info: dict, local_path: Path, remote_name: str) -> None:
    sha1 = _sha1(local_path)
    with open(local_path, "rb") as f:
        r = requests.post(
            upload_info["uploadUrl"],
            headers={
                "Authorization": upload_info["authorizationToken"],
                "X-Bz-File-Name": remote_name,
                "Content-Type": "b2/x-auto",
                "Content-Length": str(local_path.stat().st_size),
                "X-Bz-Content-Sha1": sha1,
            },
            data=f,
            timeout=120,
        )
    r.raise_for_status()

# ── JSON rewriting ────────────────────────────────────────────────────────────

def _build_url_map(download_url: str, bucket: str, uploaded: dict[str, str]) -> dict[str, str]:
    """Map local path string → public B2 URL for all uploaded files."""
    result = {}
    for local_str, remote_name in uploaded.items():
        b2_url = f"{download_url}/file/{bucket}/{remote_name}"
        result[local_str] = b2_url
    return result


def _rewrite_json(json_path: Path, url_map: dict[str, str], dry_run: bool) -> bool:
    """Replace local screenshot_path values with B2 URLs. Returns True if changed."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    changed = False

    def _replace(item: dict) -> None:
        nonlocal changed
        sp = item.get("screenshot_path") or ""
        if sp and not sp.startswith("https://"):
            new_url = url_map.get(sp)
            if new_url:
                item["screenshot_path"] = new_url
                changed = True

    for item in data.get("highlights") or []:
        _replace(item)
    for item in data.get("controversial") or []:
        _replace(item)

    if changed and not dry_run:
        tmp = json_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(json_path)

    return changed

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        log.info("Dry-run mode — no uploads or file writes")

    _load_env()
    key_id, app_key, bucket, bucket_id_env = _b2_creds()

    # Collect local screenshots that haven't been uploaded yet
    # (screenshot_path not yet a URL in any JSON)
    already_uploaded: set[str] = set()
    for jf in SUMMARIES_DIR.glob("*.json"):
        data = json.loads(jf.read_text(encoding="utf-8"))
        for item in (data.get("highlights") or []) + (data.get("controversial") or []):
            sp = item.get("screenshot_path") or ""
            if sp.startswith("https://"):
                already_uploaded.add(Path(sp).name)

    to_upload = [
        p for p in sorted(SCREENSHOTS_DIR.glob("*"))
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
        and p.name not in already_uploaded
    ]

    if not to_upload:
        log.info("All screenshots already uploaded — nothing to do")
        return

    log.info(f"Screenshots to upload: {len(to_upload)}")
    for p in to_upload:
        log.info(f"  {p.name}")

    if dry_run:
        return

    # Authorize and resolve bucket
    log.info("Authorizing with B2...")
    auth = _authorize(key_id, app_key)
    bid = _resolve_bucket_id(auth, bucket, bucket_id_env)
    upload_info = _get_upload_url(auth, bid)
    download_url = auth["downloadUrl"]

    # Upload
    uploaded: dict[str, str] = {}   # local path str → remote name
    for local_path in to_upload:
        remote_name = f"{B2_REMOTE_PREFIX}/{local_path.name}"
        log.info(f"  Uploading {local_path.name} → b2://{bucket}/{remote_name}")
        try:
            _upload_file(upload_info, local_path, remote_name)
            uploaded[str(local_path)] = remote_name
        except requests.HTTPError as e:
            log.warning(f"  Failed: {e} — skipping")
            # Re-fetch upload URL on error (B2 requires a new URL after any failure)
            try:
                upload_info = _get_upload_url(auth, bid)
            except Exception:
                pass

    if not uploaded:
        log.warning("No files were uploaded successfully")
        return

    log.info(f"Uploaded {len(uploaded)} file(s)")

    # Rewrite JSONs
    url_map = _build_url_map(download_url, bucket, uploaded)
    updated = 0
    for jf in sorted(SUMMARIES_DIR.glob("*.json")):
        if _rewrite_json(jf, url_map, dry_run=False):
            log.info(f"  Updated {jf.name}")
            updated += 1

    log.info(f"Updated {updated} summary JSON file(s)")
    log.info("Done. Add summaries/screenshots/ to .gitignore if not already there.")


if __name__ == "__main__":
    main()
