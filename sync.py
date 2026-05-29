#!/usr/bin/env python3
"""
PSP Video Archive Sync
Fetches and downloads videos from https://videoarchiv.psp.cz/
Run via cron several times a day.

Usage:
    python3 sync.py                    # sync metadata + download new videos
    python3 sync.py --dry-run          # sync metadata only, no downloads
    python3 sync.py --status           # print summary of metadata
    python3 sync.py --event 2804       # sync + download one specific event only
    python3 sync.py --event 2804 --dry-run  # check what would be downloaded
"""

import difflib
import html as _html
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, date
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

BASE_URL = "https://videoarchiv.psp.cz"
METADATA_FILE = Path("metadata.json")
VIDEOS_DIR = Path("videos")
SUBTITLES_DIR = Path("subtitles")
TRANSCRIPTIONS_DIR = Path("transcriptions")
DOC_DIR = Path("docs")
FINAL_DIR = Path("final")

PSP_BASE = "https://www.psp.cz"
_CALENDAR_URL = PSP_BASE + "/sqw/hp.sqw?k=699&dx={dx}"

# Only include events on or after this date
CUTOFF_DATE = date(2026, 3, 15)

# Categories to skip entirely
EXCLUDE_CATEGORIES = {"Jednání Poslanecké sněmovny"}

# Seconds to wait between API requests (be polite)
API_DELAY = 0.3

# Seconds to wait between file downloads
DOWNLOAD_DELAY = 1.0

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("psp-sync")

# ── Metadata helpers ─────────────────────────────────────────────────────────

def load_metadata() -> dict:
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": 1,
        "cutoff_date": CUTOFF_DATE.isoformat(),
        "last_sync": None,
        "events": {},
    }


def save_metadata(meta: dict) -> None:
    tmp = METADATA_FILE.with_suffix(".json.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(METADATA_FILE)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


# ── Document fetching (invitations / agendas from PSP calendar) ──────────────

def _fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "psp-videoarchive/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(charset, errors="replace")


def _fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "psp-videoarchive/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _dehtml(text: str) -> str:
    """Strip HTML tags and decode entities to plain text."""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", _html.unescape(text)).strip()


def _page_text(html: str) -> str:
    """Extract readable plain text from a PSP event/document page."""
    # Drop scripts and styles before stripping tags
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "\n", html)
    text = _html.unescape(text)
    # Collapse runs of blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _abs_url(href: str) -> str:
    if href.startswith("http"):
        return href
    return PSP_BASE + ("" if href.startswith("/") else "/") + href


def _find_doc_page_urls(calendar_html: str, event_name: str) -> list[str]:
    """Find document page URLs on the calendar that best match event_name.

    Handles two link types:
      - /zprava/NNN          seminars/conferences: link text IS the event title
      - text2.sqw?idd=NNN   committee meetings:   link text is generic ("Pořad jednání"),
                             so we match against surrounding HTML context instead
    """
    pattern = re.compile(
        r'<a\s[^>]*href=["\']([^"\']*?(?:/zprava/\d+|text2\.sqw\?idd=\d+)[^"\']*?)["\'][^>]*>(.*?)</a>',
        re.DOTALL | re.IGNORECASE,
    )
    matches = list(pattern.finditer(calendar_html))
    if not matches:
        return []

    name_norm = event_name.lower().strip()

    for m in matches:
        url = _abs_url(m.group(1))
        href = m.group(1)
        link_text = _dehtml(m.group(2)).lower()

        # /zprava/ links: link text IS the event title — only match on text, never on context
        # (context bleeds into adjacent links on busy calendar pages)
        if "/zprava/" in href:
            if name_norm in link_text:
                return [url]
            continue

        # text2.sqw links (committee meetings): link text is generic, match on context before the link
        ctx_start = max(0, m.start() - 600)
        ctx = _dehtml(calendar_html[ctx_start: m.start()]).lower()
        if name_norm in ctx:
            return [url]

    # Fuzzy fallback for /zprava/ links only (by link text similarity)
    best_url, best_score = None, 0.0
    for m in matches:
        if "/zprava/" not in m.group(1):
            continue
        url = _abs_url(m.group(1))
        link_text = _dehtml(m.group(2)).lower()
        score = difflib.SequenceMatcher(None, name_norm, link_text).ratio()
        if score > best_score:
            best_score, best_url = score, url

    return [best_url] if best_score >= 0.35 else []


def _find_pdf_links(zprava_html: str) -> list[dict]:
    """Return [{url, title, type}] for PDF attachments on a /zprava/NNN page."""
    links = re.findall(
        r'<a\s[^>]*href=["\']([^"\']*?orig2\.sqw\?idd=\d+[^"\']*?)["\'][^>]*>(.*?)</a>',
        zprava_html, re.DOTALL | re.IGNORECASE,
    )
    seen, results = set(), []
    for href, raw_title in links:
        url = _abs_url(href)
        if url in seen:
            continue
        seen.add(url)
        title = _dehtml(raw_title)
        t = title.lower()
        if "pozv" in t:
            doc_type = "invitation"
        elif "pořad" in t or "program" in t or "agenda" in t:
            doc_type = "agenda"
        else:
            doc_type = "material"
        results.append({"url": url, "title": title, "type": doc_type})
    return results


def _doc_extension(data: bytes) -> str:
    """Detect file extension from magic bytes."""
    if data[:4] == b"PK\x03\x04":
        return ".docx"   # DOCX/XLSX/PPTX are all ZIP-based
    if data[:4] == b"%PDF":
        return ".pdf"
    return ".bin"


def _extract_docx_text(data: bytes) -> str:
    """Extract plain text from a DOCX file using stdlib zipfile + XML stripping."""
    import io, zipfile
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if "word/document.xml" not in z.namelist():
                return ""
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
        # Insert newline at paragraph/run boundaries before stripping tags
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<[^>]+>", "", xml)
        import html as _h
        text = _h.unescape(xml)
        return re.sub(r"\n{3,}", "\n\n", text).strip()
    except Exception:
        return ""


def _extract_doc_text(data: bytes) -> str:
    """Extract plain text from PDF or DOCX bytes."""
    ext = _doc_extension(data)
    if ext == ".docx":
        return _extract_docx_text(data)
    if ext != ".pdf":
        return ""
    import io
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        pages = [p.extract_text() or "" for p in reader.pages]
        text = "\n\n".join(p for p in pages if p.strip())
        if text.strip():
            return text
    except Exception:
        pass
    try:
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(data)
            tmp = f.name
        r = subprocess.run(["pdftotext", tmp, "-"], capture_output=True, timeout=30)
        Path(tmp).unlink(missing_ok=True)
        if r.returncode == 0:
            return r.stdout.decode("utf-8", errors="replace")
    except Exception:
        pass
    return ""


def sync_event_documents(event: dict) -> int:
    """Find and download invitation/agenda PDFs for one event. Returns count of new docs."""
    ts = event.get("ts", "")
    if not ts or len(ts) < 10:
        return 0

    existing_urls = {d["url"] for d in event.get("documents", [])}
    dx = ts[:10].replace("-", "")

    try:
        cal_html = _fetch_html(_CALENDAR_URL.format(dx=dx))
        time.sleep(API_DELAY)
    except Exception as e:
        log.warning(f"  Calendar fetch failed for event {event['id']}: {e}")
        return 0

    doc_page_urls = _find_doc_page_urls(cal_html, event.get("name", ""))
    if not doc_page_urls:
        log.info(f"  No calendar match for event {event['id']} ({event.get('name', '')[:50]})")
        return 0
    log.info(f"  Found {len(doc_page_urls)} doc page(s) for event {event['id']}")

    docs_dir = DOC_DIR / f"event_{event['id']}"
    docs_dir.mkdir(parents=True, exist_ok=True)

    if "documents" not in event:
        event["documents"] = []

    all_pdf_links: list[dict] = []
    new_count = 0
    for page_idx, page_url in enumerate(doc_page_urls):
        try:
            page_html = _fetch_html(page_url)
            time.sleep(API_DELAY)
        except Exception as e:
            log.warning(f"  doc page fetch failed ({page_url}): {e}")
            continue

        # Always save the page text itself as a description document
        if page_url not in existing_urls:
            page_text = _page_text(page_html).strip()
            if page_text:
                txt_path = docs_dir / f"description_{page_idx:02d}.txt"
                txt_path.write_text(page_text, encoding="utf-8")
                event["documents"].append({
                    "url": page_url,
                    "title": f"Popis akce ({page_url.split('/')[-1]})",
                    "type": "description",
                    "local_path": None,
                    "text_path": str(txt_path),
                    "downloaded_at": datetime.now().isoformat(timespec="seconds"),
                })
                existing_urls.add(page_url)
                log.info(f"  [description] {page_url}")
                new_count += 1

        links = _find_pdf_links(page_html)
        log.info(f"  {page_url} → {len(links)} PDF link(s)")
        all_pdf_links.extend(links)

    for i, doc in enumerate(all_pdf_links):
        if doc["url"] in existing_urls:
            continue
        try:
            doc_bytes = _fetch_bytes(doc["url"])
            time.sleep(API_DELAY)
        except Exception as e:
            log.warning(f"  Document download failed: {e}")
            continue

        ext = _doc_extension(doc_bytes)
        doc_path = docs_dir / f"{doc['type']}_{i:02d}{ext}"
        doc_path.write_bytes(doc_bytes)

        text = _extract_doc_text(doc_bytes)
        text_path = None
        if text.strip():
            text_path = doc_path.with_suffix(".txt")
            text_path.write_text(text, encoding="utf-8")

        event["documents"].append({
            "url": doc["url"],
            "title": doc["title"],
            "type": doc["type"],
            "local_path": str(doc_path),
            "text_path": str(text_path) if text_path else None,
            "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        })
        existing_urls.add(doc["url"])
        log.info(f"    [{doc['type']}] {doc['title'][:70]} ({ext})")
        new_count += 1

    return new_count


# ── API helpers ───────────────────────────────────────────────────────────────

def api_get(path: str, params: dict = None, retries: int = 3) -> object:
    """Fetch JSON from API endpoint with retries."""
    url = f"{BASE_URL}/{path}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.URLError as e:
            if attempt < retries:
                wait = attempt * 5
                log.warning(f"API error for {url}: {e} — retrying in {wait}s")
                time.sleep(wait)
            else:
                log.warning(f"API error for {url}: {e} — giving up")
                return None
        except json.JSONDecodeError as e:
            log.warning(f"JSON decode error for {url}: {e}")
            return None


def parse_ts(ts_str: str | None) -> date | None:
    """Parse 'YYYY-MM-DD HH:MM:SS' → date, or None."""
    if not ts_str:
        return None
    try:
        return datetime.strptime(ts_str[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_total_start(s: str | None) -> date | None:
    """Parse 'DD.MM.YYYY HH:MM' → date, or None."""
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%d.%m.%Y").date()
    except ValueError:
        return None


# ── Event filtering ───────────────────────────────────────────────────────────

def event_date(row: dict) -> date | None:
    """Best-effort date from event row."""
    return parse_ts(row.get("ts")) or parse_total_start(row.get("total_start"))


def should_include_event(row: dict) -> bool:
    """Return True if this event should be tracked.

    We require a determinable date >= CUTOFF_DATE.  Events with no date at all
    are skipped — they are either old stubs or future events whose date we
    cannot yet verify.  Future events will appear with a date once they are
    scheduled/started and will be picked up then.
    """
    if row.get("catname") in EXCLUDE_CATEGORIES:
        return False
    d = event_date(row)
    if d is None:
        return False
    return d >= CUTOFF_DATE


# ── Metadata update from API row ──────────────────────────────────────────────

def upsert_event(meta: dict, row: dict) -> dict:
    """Insert or update event in metadata from API row. Returns event dict."""
    eid = str(row["Id"])
    existing = meta["events"].get(eid, {})
    ev = {
        "id": eid,
        "name": row.get("Name", ""),
        "category": row.get("catname", ""),
        "ts": row.get("ts"),
        "tp": row.get("tp"),
        "total_start": row.get("total_start"),
        "total_stop": row.get("total_stop"),
        "deafst": row.get("deafst"),
        "subakce_count": row.get("subakce_count"),
        # Preserve existing subevents, status, and summary results
        "subevents": existing.get("subevents", {}),
        "status": existing.get("status", "planned"),
        "last_checked": existing.get("last_checked"),
        "summary_done_at": existing.get("summary_done_at"),
        "summary_local": existing.get("summary_local"),
        "summary_model": existing.get("summary_model"),
        "summary_schema_version": existing.get("summary_schema_version"),
    }
    meta["events"][eid] = ev
    return ev


# ── Subevent/file fetching ────────────────────────────────────────────────────

def refresh_subevents(event: dict) -> bool:
    """
    Fetch subevents and their file lists from API.
    Returns True if anything changed.
    """
    eid = event["id"]
    data = api_get("subakce_data.php", {"Id": eid})
    time.sleep(API_DELAY)
    if not data or not isinstance(data, list):
        return False

    changed = False
    for sub_row in data:
        sid = str(sub_row["Id"])
        existing_sub = event["subevents"].get(sid, {})

        files_data = api_get("subfiles.php", {"subakce": sid})
        time.sleep(API_DELAY)
        files = []
        if files_data and isinstance(files_data, list):
            for f in files_data:
                remote = f.get("name", "")
                cap = f.get("captions")
                # Find existing file record to preserve download info
                existing_file = next(
                    (x for x in existing_sub.get("files", [])
                     if x["remote_path"] == remote),
                    {}
                )
                files.append({
                    "remote_path": remote,
                    "url": f"{BASE_URL}/{remote}",
                    "local_path": str(VIDEOS_DIR / remote),
                    "downloaded_at": existing_file.get("downloaded_at"),
                    "size_bytes": existing_file.get("size_bytes"),
                    "captions_remote": cap,
                    "captions_local": str(SUBTITLES_DIR / cap) if cap else None,
                    "captions_downloaded_at": existing_file.get("captions_downloaded_at"),
                    # Our transcription (written by the transcription script)
                    "transcription_local": transcription_path(remote),
                    "transcription_done_at": existing_file.get("transcription_done_at"),
                    "from_sec": f.get("from", 0),
                    "to_sec": f.get("to", 0),
                })

        new_sub = {
            "id": sid,
            "name": sub_row.get("Name", ""),
            "deafs": sub_row.get("deafs"),
            "start": sub_row.get("start"),
            "stop": sub_row.get("stop"),
            "isactive": sub_row.get("isactive"),
            "files": files,
        }
        if new_sub != existing_sub:
            changed = True
        event["subevents"][sid] = new_sub

    event["last_checked"] = datetime.now().isoformat(timespec="seconds")
    return changed


def reconcile_file_states(event: dict) -> None:
    """Clear stale downloaded_at when the file is no longer on disk.

    This prevents the metadata getting stuck in 'downloaded' state after
    a video is deleted without a transcription being present.
    """
    for sub in event["subevents"].values():
        for f in sub.get("files", []):
            if f.get("downloaded_at") and not _file_exists(f["local_path"]):
                if not file_has_transcription(f):
                    log.debug(f"  Clearing stale downloaded_at for {Path(f['local_path']).name}")
                    f["downloaded_at"] = None
                    f["size_bytes"] = None


def compute_event_status(event: dict) -> str:
    """Derive status from subevent/file state.

    Possible values (in order of progress):
      planned     – no video files known yet
      available   – files exist on server, none downloaded or transcribed
      partial     – some files downloaded/transcribed, some still needed
      downloaded  – all files on disk (transcription not yet done)
      transcribed – all files have a transcription; video cache not required
    """
    if not event["subevents"]:
        return "planned"

    all_files = [
        f for sub in event["subevents"].values()
        for f in sub.get("files", [])
    ]
    if not all_files:
        return "planned"

    transcribed = [f for f in all_files if file_has_transcription(f)]
    if len(transcribed) == len(all_files):
        return "transcribed"

    on_disk = [f for f in all_files if f.get("downloaded_at") and _file_exists(f["local_path"])]
    # A file is "covered" if it's on disk OR already transcribed
    covered = {id(f) for f in on_disk} | {id(f) for f in transcribed}
    if len(covered) == len(all_files):
        return "downloaded"
    if covered:
        return "partial"
    return "available"


def _file_exists(path: str) -> bool:
    return Path(path).exists()


def transcription_path(remote_path: str) -> str:
    """Canonical path for our transcription of a video file.

    Mirrors the video path under TRANSCRIPTIONS_DIR with a .json extension.
    Example: video/K48/2026/04/02/_file.mp4 → transcriptions/video/K48/2026/04/02/_file.json
    The transcription script writes to this path; we check it for existence.
    """
    p = Path(remote_path)
    return str(TRANSCRIPTIONS_DIR / p.parent / (p.stem + ".json"))


def file_has_transcription(finfo: dict) -> bool:
    """True if this video file already has a usable transcription.

    Either:
    - The existing captions (VTT) were downloaded, or
    - Our own transcription script has produced a file.
    In both cases the video does not need to be (re-)downloaded.
    """
    if finfo.get("captions_downloaded_at") and _file_exists(finfo.get("captions_local", "")):
        return True
    if finfo.get("transcription_done_at") and _file_exists(finfo.get("transcription_local", "")):
        return True
    return False


# ── Downloading ───────────────────────────────────────────────────────────────

def download_file(url: str, dest: Path) -> int:
    """
    Download url → dest (via temp file). Returns size in bytes, or -1 on error.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            with open(tmp, "wb") as f:
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
        tmp.rename(dest)
        return downloaded
    except Exception as e:
        log.error(f"Download failed {url}: {e}")
        if tmp.exists():
            tmp.unlink()
        return -1


def sync_event_files(event: dict, dry_run: bool = False) -> int:
    """Download missing video and caption files. Returns count of new downloads.

    A video file is skipped (not re-downloaded) if it already has a transcription
    — either from existing captions or from our transcription script.  Captions
    are always downloaded when available, even after transcription, because they
    may be used directly.
    """
    count = 0
    for sub in event["subevents"].values():
        for finfo in sub.get("files", []):
            dest = Path(finfo["local_path"])
            on_disk = finfo.get("downloaded_at") and dest.exists()

            if not on_disk:
                if file_has_transcription(finfo):
                    log.debug(f"  Skipping (transcription exists): {dest.name}")
                else:
                    url = finfo["url"]
                    if dry_run:
                        log.info(f"  [dry-run] would download: {dest}")
                    else:
                        log.info(f"  Downloading: {dest.name}")
                        size = download_file(url, dest)
                        if size >= 0:
                            finfo["downloaded_at"] = datetime.now().isoformat(timespec="seconds")
                            finfo["size_bytes"] = size
                            count += 1
                            time.sleep(DOWNLOAD_DELAY)
                        else:
                            log.warning(f"  Failed: {url}")

            # Captions — download regardless of transcription status
            cap_remote = finfo.get("captions_remote")
            cap_dest = finfo.get("captions_local")
            if cap_remote and cap_dest:
                cap_path = Path(cap_dest)
                cap_ok = finfo.get("captions_downloaded_at") and cap_path.exists()
                if not cap_ok:
                    cap_url = f"{BASE_URL}/{cap_remote}"
                    if dry_run:
                        log.info(f"  [dry-run] would download captions: {cap_path.name}")
                    else:
                        log.info(f"  Downloading captions: {cap_path.name}")
                        cap_path.parent.mkdir(parents=True, exist_ok=True)
                        size = download_file(cap_url, cap_path)
                        if size >= 0:
                            finfo["captions_downloaded_at"] = datetime.now().isoformat(timespec="seconds")
                            count += 1
                            time.sleep(API_DELAY)

    return count


# ── Status report ─────────────────────────────────────────────────────────────

def print_status(meta: dict) -> None:
    events = meta["events"]
    by_status: dict[str, list] = {}
    for ev in events.values():
        s = ev.get("status", "?")
        by_status.setdefault(s, []).append(ev)

    all_files = [
        f for ev in events.values()
        for sub in ev["subevents"].values()
        for f in sub.get("files", [])
    ]
    n_on_disk = sum(1 for f in all_files if f.get("downloaded_at") and _file_exists(f["local_path"]))
    n_captions = sum(1 for f in all_files if f.get("captions_downloaded_at") and _file_exists(f.get("captions_local", "")))
    n_transcribed = sum(1 for f in all_files if f.get("transcription_done_at") and _file_exists(f.get("transcription_local", "")))
    n_has_any_transcription = sum(1 for f in all_files if file_has_transcription(f))

    print(f"\nTotal events tracked: {len(events)}")
    print(f"Last sync: {meta.get('last_sync', 'never')}\n")
    print("Events by status:")
    for status, evs in sorted(by_status.items()):
        print(f"  {status:12s} {len(evs):4d}")
    print(f"\nFiles: {len(all_files)} total")
    print(f"  on disk:            {n_on_disk:4d}")
    print(f"  captions (VTT):     {n_captions:4d}")
    print(f"  our transcriptions: {n_transcribed:4d}")
    print(f"  any transcription:  {n_has_any_transcription:4d}  (captions or ours)")
    print()

    # List events needing action
    need_dl = [
        ev for ev in events.values()
        if ev.get("status") in ("available", "partial")
    ]
    if need_dl:
        print(f"Events with files still needed ({len(need_dl)}):")
        for ev in need_dl:
            ev_files = [
                f for sub in ev["subevents"].values()
                for f in sub.get("files", [])
            ]
            missing = [
                f for f in ev_files
                if not (_file_exists(f["local_path"]) or file_has_transcription(f))
            ]
            print(f"  [{ev['id']}] {ev['name'][:60]}  ({len(missing)}/{len(ev_files)} files needed)")


# ── Main sync loop ────────────────────────────────────────────────────────────

def sync_events(meta: dict, dry_run: bool = False, event_filter: str | None = None) -> None:
    """Full sync: update event list, refresh subevents, download files.

    If event_filter is set (an event ID string), only that event's subevents
    are refreshed and its files downloaded.  The global event list is still
    fetched so that the filtered event's metadata is up to date.
    """
    log.info("=== PSP sync started ===")
    events = meta["events"]

    # 1. Fetch full event list (API returns all events in one response)
    log.info("Fetching event list from API...")
    data = api_get("akce_data.php")
    time.sleep(API_DELAY)
    if not data or not data.get("rows"):
        log.error("Failed to fetch event list")
        return

    new_events = 0
    updated_events = 0
    for row in data["rows"]:
        if not should_include_event(row):
            continue
        eid = str(row["Id"])
        is_new = eid not in events
        upsert_event(meta, row)
        if is_new:
            new_events += 1
            log.debug(f"  New event {eid}: {row.get('Name', '')[:50]}")
        else:
            updated_events += 1

    log.info(f"Events: {new_events} new, {updated_events} refreshed, {len(events)} total tracked")

    # 2. Refresh subevents for events that need it
    candidate_events = (
        [events[event_filter]]
        if event_filter and event_filter in events
        else list(events.values())
    )
    needs_refresh = []
    for ev in candidate_events:
        cnt = ev.get("subakce_count")
        status = ev.get("status", "planned")
        last_checked = ev.get("last_checked")

        # Refresh if:
        #   - Has subevents declared but we haven't fetched them yet
        #   - Is "planned" (might now have videos)
        #   - Is "available"/"partial" and was not checked recently
        should_refresh = False
        if cnt and not ev["subevents"]:
            should_refresh = True
        elif status in ("planned", "available", "partial", "downloaded"):
            should_refresh = True
        # "transcribed" events are complete — no need to re-check

        if should_refresh:
            needs_refresh.append(ev)

    if needs_refresh:
        log.info(f"Refreshing subevents for {len(needs_refresh)} events...")
        for ev in needs_refresh:
            changed = refresh_subevents(ev)
            reconcile_file_states(ev)
            ev["status"] = compute_event_status(ev)
            if changed:
                log.debug(f"  [{ev['id']}] {ev['name'][:50]} → {ev['status']}")

    save_metadata(meta)

    # 3. Download files
    to_download = [
        ev for ev in candidate_events
        if ev.get("status") in ("available", "partial")
    ]
    if not to_download:
        log.info("No new files to download.")
    else:
        log.info(f"Downloading files for {len(to_download)} events...")
        total_dl = 0
        for ev in to_download:
            log.info(f"  Event [{ev['id']}] {ev['name'][:60]}")
            count = sync_event_files(ev, dry_run=dry_run)
            total_dl += count
            ev["status"] = compute_event_status(ev)
            save_metadata(meta)  # save after each event in case we're interrupted
        log.info(f"Downloaded {total_dl} file(s) total.")

    # 4. Fetch invitation/agenda documents from PSP calendar.
    # Only for events that have a transcript (worth summarising) and no docs yet.
    # Skipped in dry-run mode.
    if not dry_run:
        needs_docs = [
            ev for ev in candidate_events
            if not ev.get("documents")
            and any(
                FINAL_DIR.glob(f"event_{ev['id']}_*.md")
            )
        ]
        if needs_docs:
            log.info(f"Fetching documents for {len(needs_docs)} events...")
            total_docs = 0
            for ev in needs_docs:
                n = sync_event_documents(ev)
                if n:
                    log.info(f"  Event [{ev['id']}]: {n} doc(s)")
                    total_docs += n
                    save_metadata(meta)
            if total_docs:
                log.info(f"Downloaded {total_docs} document(s) total.")

    meta["last_sync"] = datetime.now().isoformat(timespec="seconds")
    save_metadata(meta)
    log.info("=== PSP sync done ===")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    status_only = "--status" in args

    event_filter = None
    if "--event" in args:
        idx = args.index("--event")
        if idx + 1 < len(args):
            event_filter = args[idx + 1]
        else:
            log.error("--event requires an event ID argument")
            sys.exit(1)

    meta = load_metadata()

    if status_only:
        print_status(meta)
        return

    if dry_run:
        log.info("DRY RUN - no files will be downloaded")
    if event_filter:
        log.info(f"Filtering to event {event_filter}")

    sync_events(meta, dry_run=dry_run, event_filter=event_filter)

    if "-v" in args:
        print_status(meta)


if __name__ == "__main__":
    main()
