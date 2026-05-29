#!/usr/bin/env python3
"""
PSP Summarization Script
Summarizes transcribed events using Groq or Gemini LLM APIs and saves structured
JSON summaries alongside the merged Markdown transcripts.

Usage:
    python3 summarize.py                             # summarize all events with a final/ file
    python3 summarize.py --event 2922                # summarize one specific event
    python3 summarize.py --model gemini-3.1-flash-lite  # use Gemini (single-pass, free tier)
    python3 summarize.py --model llama-3.3-70b-versatile  # use Groq 70B
    python3 summarize.py --force                     # re-summarize even if summary exists
    python3 summarize.py --status                    # show per-event summary status

Output:
    summaries/json/summary_<id>_<date>_<slug>.json   structured JSON summary
    summaries/md/summary_<id>_<date>_<slug>.md       full LLM response (human-readable)

Requires (set in .env or environment):
    export GROQ_API_KEY=your_key_here     # for Groq models
    export GEMINI_API_KEY=your_key_here   # for Gemini models
"""

import csv
import difflib
import hashlib
import json
import logging
import os
import re
import sys
import time
import unicodedata
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ── Load .env (if present) ────────────────────────────────────────────────────

_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ── Configuration ─────────────────────────────────────────────────────────────

METADATA_FILE = Path("metadata.json")
SUMMARIES_DIR = Path("summaries")
CHUNKS_DIR    = Path("summaries/chunks")   # chunk-note cache for resumable multipass
FINAL_DIR     = Path("final")
PROMPT_FILE = Path("prompts/summary.md")
FACTCHECK_PROMPT_FILE = Path("prompts/factcheck.md")
SCHEMA_FILE = Path("summary.schema.json")
MP_CSV = Path("prompts/latest.csv")

GROQ_API_KEY_ENV  = "GROQ_API_KEY"
GROQ_CHAT_URL     = "https://api.groq.com/openai/v1/chat/completions"

GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GEMINI_CHAT_URL    = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

DEFAULT_MODEL = "gemini-3.1-flash-lite"
# Fallback when the primary Gemini model exhausts its daily free-tier quota (500 req/day).
# Gemma on Groq has ~1500 req/day free tier.
DEFAULT_FALLBACK_MODEL = "gemma-4-31b-it"  # Google AI (Gemini endpoint), ~1500 req/day free tier

LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 4096      # minimum output budget for any final-summary call
LLM_CHUNK_MAX_TOKENS = 3000  # output budget for intermediate chunk notes

# Groq counts input + max_tokens against TPM. Czech text tokenizes at ~2.5 chars/token
# (diacritics make it denser than English). Leave headroom for the system prompt (~2500 tokens).
CHARS_PER_TOKEN = 2.5
PROMPT_RESERVE_TOKENS = 2_500

# Per-model TPM limits on the Groq free tier. Unknown models fall back to a
# conservative 6 000 so the script doesn't blindly over-submit.
MODEL_TPM: dict[str, int] = {
    # Groq free tier
    "meta-llama/llama-4-scout-17b-16e-instruct": 30_000,
    "llama-3.3-70b-versatile":                   12_000,
    "llama-3.1-8b-instant":                       6_000,
    "qwen/qwen3-32b":                             6_000,
    # Gemini — 1M context window, single-pass always
    "gemini-3.1-flash-lite":                     500_000,
    "gemini-3.5-flash":                          500_000,
    # Groq Gemma — fallback when Gemini daily quota (~500 req/day) is exhausted
    "gemma-4-31b-it":                      14_400,
}
DEFAULT_TPM = 6_000

# Maximum output tokens each model can actually produce.
# Used to cap the dynamic output budget so we never request more than the model supports.
MODEL_MAX_OUTPUT: dict[str, int] = {
    "meta-llama/llama-4-scout-17b-16e-instruct": 8_192,
    "llama-3.3-70b-versatile":                   8_192,
    "llama-3.1-8b-instant":                      8_192,
    "qwen/qwen3-32b":                             8_192,
    "gemini-3.1-flash-lite":                      8_192,
    "gemini-3.5-flash":                           8_192,
    "gemma-4-31b-it":                      8_192,
}
DEFAULT_MAX_OUTPUT = 8_192


class QuotaExhaustedError(RuntimeError):
    """Raised when the LLM backend signals daily quota exhaustion (not a per-minute rate limit)."""


# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("psp-summarize")

# ── Metadata helpers ──────────────────────────────────────────────────────────

def load_metadata() -> dict:
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


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

# ── File helpers ──────────────────────────────────────────────────────────────

def load_prompt() -> str:
    if not PROMPT_FILE.exists():
        log.error(f"Prompt file not found: {PROMPT_FILE}")
        sys.exit(1)
    return PROMPT_FILE.read_text(encoding="utf-8")


def find_final_file(event_id: str) -> Path | None:
    matches = list(FINAL_DIR.glob(f"event_{event_id}_*.md"))
    return matches[0] if matches else None


def summary_paths(final_path: Path) -> tuple[Path, Path]:
    """Return (json_path, md_path) mirroring the final/ filename."""
    stem = final_path.stem[len("event_"):]  # strip "event_" prefix
    return (
        SUMMARIES_DIR / "json" / f"summary_{stem}.json",
        SUMMARIES_DIR / "md"   / f"summary_{stem}.md",
    )


def invitation_text(event: dict) -> str:
    """Return extracted text from invitation/agenda documents, or empty string."""
    docs = event.get("documents") or []
    parts = []
    for doc in docs:
        if doc.get("type") not in ("invitation", "agenda", "description"):
            continue
        tp = doc.get("text_path")
        if not tp:
            continue
        p = Path(tp)
        if p.exists():
            parts.append(f"[{doc['type'].upper()}: {doc.get('title', '')}]\n{p.read_text(encoding='utf-8')}")
    return "\n\n---\n\n".join(parts)


# Prompt for intermediate chunk passes.
# Deliberately asks for detail — these notes feed the final merge and must not lose information.
_CHUNK_PROMPT = (
    "Toto je část {n}/{total} delšího přepisu z jednání Poslanecké sněmovny.\n\n"
    "Pro každého identifikovaného řečníka vytvoř záznam přesně v tomto formátu:\n\n"
    "**Jméno (instituce nebo strana)**\n"
    "- konkrétní argument nebo fakt včetně čísel\n"
    "- další argument nebo návrh\n"
    "- případný kontroverzní výrok\n\n"
    "Pokud jméno nelze určit, použij 'Neidentifikovaný řečník [pořadí v této části]'.\n"
    "Nevynechávej žádného řečníka. Tyto záznamy jsou přímým vstupem pro finální shrnutí."
)
_CHUNK_PROMPT_TOKENS = 200   # approximate size of _CHUNK_PROMPT


def _max_input_chars(prompt_tokens: int, output_tokens: int, model: str) -> int:
    """Return the transcript character budget that fits within this model's TPM limit."""
    tpm = MODEL_TPM.get(model, DEFAULT_TPM)
    return int((tpm - prompt_tokens - output_tokens) * CHARS_PER_TOKEN)


def _output_tokens(input_chars: int, model: str, min_tokens: int = LLM_MAX_TOKENS) -> int:
    """Scale output token budget with input size, capped at the model's output limit.

    Ratio: 1 output token per 8 input chars (Czech summaries are ~10–15% of source in tokens).
    Always at least min_tokens so short events still get a full response.
    """
    cap = MODEL_MAX_OUTPUT.get(model, DEFAULT_MAX_OUTPUT)
    return min(cap, max(min_tokens, input_chars // 8))


def chunk_transcript(text: str, max_chars: int) -> list[str]:
    """Split transcript into chunks at --- section boundaries, each ≤ max_chars.

    If a single section is larger than max_chars (can happen with very long
    10-minute blocks), it is further split at paragraph boundaries (\n\n).
    """
    def _split_section(sec: str) -> list[str]:
        """Break an oversized section at paragraph boundaries."""
        if len(sec) <= max_chars:
            return [sec]
        parts: list[str] = []
        current: list[str] = []
        current_len = 0
        for para in sec.split("\n\n"):
            para_len = len(para) + 2
            if current and current_len + para_len > max_chars:
                parts.append("\n\n".join(current))
                current, current_len = [para], para_len
            else:
                current.append(para)
                current_len += para_len
        if current:
            parts.append("\n\n".join(current))
        return parts

    sections = text.split("\n---\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for section in sections:
        sub_sections = _split_section(section)
        for sub in sub_sections:
            sub_len = len(sub) + 5
            if current and current_len + sub_len > max_chars:
                chunks.append("\n---\n".join(current))
                current, current_len = [sub], sub_len
            else:
                current.append(sub)
                current_len += sub_len
    if current:
        chunks.append("\n---\n".join(current))
    return chunks


def _chunk_cache_path(event_id: str, model: str, i: int, total: int) -> Path:
    model_safe = re.sub(r"[^\w-]", "_", model)
    return CHUNKS_DIR / f"event_{event_id}_{model_safe}_{i}of{total}.txt"


def _chunk_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


def multipass_summarize(transcript: str, prompt: str, model: str, event: dict) -> str:
    """
    Summarize a transcript that exceeds the single-call TPM limit:
    1. Split into chunks at 10-min section boundaries (never mid-sentence).
    2. Summarise each chunk into detailed Czech notes (no JSON).
    3. Feed an explicit metadata preamble + all notes to a final call with the full prompt.

    Chunk notes are cached to disk so a resumed run skips already-completed chunks.
    Cache files are removed after the final merge succeeds.
    """
    chunk_budget = _max_input_chars(_CHUNK_PROMPT_TOKENS, LLM_CHUNK_MAX_TOKENS, model)
    chunks = chunk_transcript(transcript, chunk_budget)
    total = len(chunks)
    log.info(f"  Multipass: {total} chunks (budget {chunk_budget:,} chars/chunk)")

    event_id = event["id"]
    header = transcript.split("\n---\n")[0]  # event metadata table + disclaimer

    # Phase 1 — detailed notes per chunk (with disk cache for resumability)
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        cache = _chunk_cache_path(event_id, model, i, total)
        chunk_h = _chunk_hash(chunk)
        if cache.exists():
            first, _, body = cache.read_text(encoding="utf-8").partition("\n")
            if first.strip() == chunk_h:
                log.info(f"  Chunk {i}/{total}: resumed from cache")
                notes.append(f"## Část {i}/{total}\n\n{body}")
                continue
        log.info(f"  Chunk {i}/{total} ({len(chunk):,} chars)")
        note = llm_chat(
            system=_CHUNK_PROMPT.format(n=i, total=total),
            user=chunk,
            model=model,
            max_tokens=LLM_CHUNK_MAX_TOKENS,
        )
        cache.write_text(f"{chunk_h}\n{note}", encoding="utf-8")
        notes.append(f"## Část {i}/{total}\n\n{note}")

    # Phase 2 — final structured summary from merged notes.
    # Prepend an explicit metadata block so the model can reliably populate
    # the event.* fields in the JSON regardless of how the header is formatted.
    ts = event.get("ts") or ""
    start_date = f"{ts[:10]}T{ts[11:16]}" if len(ts) >= 16 else ts[:10]
    end_ts = event.get("tp") or ""
    end_date = f"{end_ts[:10]}T{end_ts[11:16]}" if len(end_ts) >= 16 else (end_ts[:10] or None)
    preamble = (
        f"METADATA UDÁLOSTI (použij pro vyplnění polí event.* v JSON):\n"
        f"ID: {event['id']}\n"
        f"Název: {event.get('name', '')}\n"
        f"Klasifikace (classification): {event.get('category', '')}\n"
        f"start_date: {start_date}\n"
        f"end_date: {end_date}\n\n"
    )
    log.info("  Final merge pass")
    merged_notes = preamble + header + "\n\n---\n\n" + "\n\n---\n\n".join(notes)
    out_tokens = _output_tokens(len(merged_notes), model)
    log.info(f"  Output budget: {out_tokens} tokens")
    result = llm_chat(system=prompt, user=merged_notes, model=model, max_tokens=out_tokens)

    # Clean up chunk cache now that the merge succeeded
    for i in range(1, total + 1):
        _chunk_cache_path(event_id, model, i, total).unlink(missing_ok=True)

    return result


_schema_cache: dict | None = None

# ── MP name matching ──────────────────────────────────────────────────────────

# Czech honorifics and parliamentary role prefixes to strip before matching.
_STRIP_TITLES = re.compile(
    r"\b(ing|mgr|judr|phdr|rndr|mudr|mba|bc|prof|doc|dr|ph\.d|csc)\b\.?",
    re.IGNORECASE,
)
_STRIP_ROLES = re.compile(
    r"\b(poslanec|poslankyně|ministr|ministryně|předseda|předsedkyně|"
    r"místopředseda|místopředsedkyně|senátor|senátorka|hejtman|primátor|"
    r"vicepremiér|premiér|premiérka)\b",
    re.IGNORECASE,
)

_mp_entries: list[tuple[str, dict]] | None = None   # (search_key, mp_info)


def _load_mp_entries() -> list[tuple[str, dict]]:
    """Load latest.csv and build a flat list of (normalised_name_form, mp_info) pairs."""
    global _mp_entries
    if _mp_entries is not None:
        return _mp_entries
    _mp_entries = []
    if not MP_CSV.exists():
        return _mp_entries
    with open(MP_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fn = row["given_name"].strip()
            ln = row["family_name"].strip()
            # id format: "psp:person:1" — store as-is for Popolo person_id
            info = {"person_id": row["id"].strip()}
            # Index three name forms per MP: "Jana Nováková", "Nováková Jana", "Nováková"
            for form in (f"{fn} {ln}", f"{ln} {fn}", ln):
                if form.strip():
                    _mp_entries.append((form.lower(), info))
    return _mp_entries


def _normalise(name: str) -> str:
    """Strip titles, role words, and extra whitespace for matching."""
    name = _STRIP_ROLES.sub("", name)
    name = _STRIP_TITLES.sub("", name)
    return " ".join(name.split()).lower()


def _match_mp(name: str, entries: list[tuple[str, dict]]) -> dict | None:
    """Return the best MP match for a speaker name, or None if below threshold."""
    needle = _normalise(name)
    if not needle:
        return None
    keys = [e[0] for e in entries]
    # difflib cutoff 0.82 keeps false positives low for Czech names
    matches = difflib.get_close_matches(needle, keys, n=1, cutoff=0.82)
    if not matches:
        return None
    return next(info for key, info in entries if key == matches[0])


def enrich_speakers(summary_json: dict) -> None:
    """Fill in person_id and affiliation for matched MPs. Modifies summary_json in place."""
    speakers = (summary_json.get("entities") or {}).get("speakers") or []
    if not speakers:
        return
    entries = _load_mp_entries()
    if not entries:
        return
    matched = 0
    for speaker in speakers:
        if speaker.get("person_id"):
            continue
        mp = _match_mp(speaker.get("name", ""), entries)
        if mp:
            speaker["person_id"] = mp["person_id"]
            matched += 1
    if matched:
        log.info(f"  MP enrichment: matched {matched}/{len(speakers)} speakers")


# ── Screenshot extraction ─────────────────────────────────────────────────────

_TS_RE = re.compile(r"^(\d+)/(\d{1,2}:\d{2})$")


def _sorted_event_files(event: dict) -> list[dict]:
    """All downloaded video files for an event, sorted chronologically by remote path."""
    files = [
        f for sub in event["subevents"].values()
        for f in sub.get("files", [])
        if f.get("local_path") and f.get("downloaded_at")
    ]
    return sorted(files, key=lambda f: f.get("remote_path", ""))


_PSP_VIDEO_BASE = "https://videoarchiv.psp.cz/"


def _extract_video_parts(event: dict) -> list[dict]:
    """Build video_parts list (part→URL) for injection into the summary JSON.

    Ordering matches the part numbering in the transcript (same sort key: remote_path,
    same subset: files with completed transcription).
    """
    files = sorted(
        (
            f for sub in event.get("subevents", {}).values()
            for f in sub.get("files", [])
            if f.get("remote_path") and f.get("transcription_done_at")
        ),
        key=lambda f: f["remote_path"],
    )
    parts = []
    for i, f in enumerate(files, 1):
        entry: dict = {
            "part": i,
            "url": _PSP_VIDEO_BASE + f["remote_path"].lstrip("/"),
        }
        if f.get("from_sec"):
            entry["from_sec"] = f["from_sec"]
        parts.append(entry)
    return parts


def _extract_frame(video_path: Path, time_str: str, out_path: Path) -> bool:
    """Extract a JPEG frame from video_path at time_str using ffmpeg.

    Uses output seeking (-ss after -i) for frame-accurate extraction.
    Timeout is generous because output seeking decodes from the start of the file.
    """
    import subprocess
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path), "-ss", time_str,
             "-vframes", "1", "-q:v", "2", str(out_path)],
            capture_output=True, timeout=120,
        )
        return r.returncode == 0 and out_path.exists()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        log.warning(f"  ffmpeg error: {e}")
        return False


def extract_screenshots(summary_json: dict, event: dict) -> None:
    """Extract video frames for highlights and controversial items. Modifies summary_json in place."""
    files = _sorted_event_files(event)
    if not files:
        return

    event_id = event["id"]
    screenshots_dir = SUMMARIES_DIR / "screenshots"

    def _process(item: dict, label: str, idx: int) -> None:
        ts = (item.get("timestamp") or "").strip()
        if not ts:
            return
        m = _TS_RE.match(ts)
        if not m:
            log.warning(f"  Screenshot: unrecognised timestamp format {ts!r}")
            return
        part = int(m.group(1))
        time_str = m.group(2)
        if part < 1 or part > len(files):
            log.warning(f"  Screenshot: part {part} out of range (event has {len(files)} files)")
            return
        video_path = Path(files[part - 1]["local_path"])
        if not video_path.exists():
            log.warning(f"  Screenshot: video not found: {video_path}")
            return
        out_path = screenshots_dir / f"event_{event_id}_{label}_{idx:02d}.jpg"
        if _extract_frame(video_path, time_str, out_path):
            item["screenshot_path"] = str(out_path)
            log.info(f"  Screenshot: {out_path.name}")
        else:
            log.warning(f"  Screenshot: ffmpeg failed for {video_path.name} at {time_str}")

    for i, item in enumerate(summary_json.get("highlights") or []):
        _process(item, "highlight", i)
    for i, item in enumerate(summary_json.get("controversial") or []):
        _process(item, "controversy", i)


def validate_summary(data: dict) -> list[str]:
    """
    Validate a summary dict against summary.schema.json.
    Returns a list of error strings (empty = valid).
    Silently skips validation if jsonschema is not installed.
    """
    global _schema_cache
    try:
        import jsonschema
    except ImportError:
        return []
    if _schema_cache is None:
        if not SCHEMA_FILE.exists():
            return []
        _schema_cache = json.loads(SCHEMA_FILE.read_text())
    errors = [
        f"{e.json_path}: {e.message}"
        for e in jsonschema.Draft202012Validator(_schema_cache).iter_errors(data)
    ]
    return errors


_SOURCE_MAP = {
    "whisper":   "whisper",
    "groq":      "groq",
    "mixed":     "mixed",
    "captions":  "captions",
    "caption":   "captions",
    "titulky":   "captions",
    "vtt":       "captions",
    "srt":       "captions",
    "subtitl":   "captions",
}

def _normalize_source(raw: str) -> str:
    """Map LLM-generated source strings to the schema enum values."""
    lower = raw.lower()
    for key, val in _SOURCE_MAP.items():
        if key in lower:
            return val
    return raw  # leave as-is; schema validator will flag it if still invalid


def _normalize_highlight_type(raw: str) -> str:
    """Map Czech/misspelled highlight type strings to schema enum values."""
    lower = raw.lower().strip()
    if "paraf" in lower:   # parafrase, parafraze, paráfraze, paraphrase
        return "paraphrase"
    if "cit" in lower:     # citace, citát, citation
        return "citation"
    return raw


def extract_json_block(text: str) -> dict | None:
    """Extract and parse the last ```json … ``` block from an LLM response."""
    matches = list(re.finditer(r"```json\s*(.*?)\s*```", text, re.DOTALL))
    if not matches:
        return None
    raw = matches[-1].group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        log.warning(f"  JSON parse error in LLM output: {e}")
        log.debug(f"  Raw block:\n{raw[:500]}")
        return None

# ── LLM API (Groq + Gemini via OpenAI-compatible endpoints) ──────────────────

def _backend(model: str) -> tuple[str, str]:
    """Return (chat_url, api_key_env_var) for the given model."""
    if model.startswith("gemini") or model.startswith("gemma"):
        return GEMINI_CHAT_URL, GEMINI_API_KEY_ENV
    return GROQ_CHAT_URL, GROQ_API_KEY_ENV


def _parse_retry_after(body: str, headers) -> float:
    """Return seconds to wait from a 429 response."""
    for h in ("Retry-After", "retry-after"):
        val = headers.get(h)
        if val:
            try:
                return float(val) + 5
            except ValueError:
                pass
    m = re.search(r"try again in\s+((?:\d+h\s*)?(?:\d+m\s*)?(?:\d+(?:\.\d+)?s)?)", body)
    if m:
        t = m.group(1)
        h = int(re.search(r"(\d+)h", t).group(1)) if "h" in t else 0
        mn = int(re.search(r"(\d+)m", t).group(1)) if "m" in t else 0
        s = float(re.search(r"(\d+(?:\.\d+)?)s", t).group(1)) if "s" in t else 0
        return h * 3600 + mn * 60 + s + 5
    return 65.0


def llm_chat(system: str, user: str, model: str, max_tokens: int = LLM_MAX_TOKENS) -> str:
    """Call an OpenAI-compatible chat completions endpoint. Returns assistant content."""
    chat_url, key_env = _backend(model)
    api_key = os.environ.get(key_env, "").strip()
    if not api_key:
        raise RuntimeError(
            f"API key not set. Export it before running:\n"
            f"  export {key_env}=your_key_here"
        )

    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": LLM_TEMPERATURE,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        chat_url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "psp-videoarchive/1.0",
        },
    )

    rate_limits = 0
    server_errors = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            if e.code == 429:
                lower = err_body.lower()
                # Daily quota exhaustion: only possible on Google backend (Gemini/Gemma).
                # Groq 429s are always per-minute TPM limits and must go through retry/backoff.
                is_google = model.startswith(("gemini", "gemma"))
                if is_google and ("day" in lower or "daily" in lower or "per_day" in lower):
                    raise QuotaExhaustedError(
                        f"Daily quota exhausted ({model}): {err_body[:200]}"
                    )
                rate_limits += 1
                base = _parse_retry_after(err_body, e.headers)
                # Add 30 s per consecutive hit so repeated 429s space out
                extra = min(rate_limits - 1, 4) * 30   # 0, 30, 60, 90, 120 s
                wait = base + extra
                log.warning(f"  Rate limit (hit {rate_limits}) — waiting {wait:.0f}s before retry")
                time.sleep(wait)
            elif e.code in (500, 503, 529):
                server_errors += 1
                if server_errors <= 5:
                    wait = 10 * (2 ** (server_errors - 1))  # 10, 20, 40, 80, 160 s
                    log.warning(f"  Server error {e.code} (attempt {server_errors}/5) — retrying in {wait}s")
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"API error {e.code} after 5 retries: {err_body[:300]}")
            else:
                raise RuntimeError(f"API error {e.code}: {err_body[:300]}")
        except (TimeoutError, urllib.error.URLError, ConnectionError) as e:
            server_errors += 1
            if server_errors <= 5:
                wait = 10 * (2 ** (server_errors - 1))  # 10, 20, 40, 80, 160 s
                log.warning(f"  Network error (attempt {server_errors}/5) — retrying in {wait}s: {e}")
                time.sleep(wait)
            else:
                raise RuntimeError(f"Network error after 5 retries: {e}")

# ── Timestamp refinement (linear interpolation) ──────────────────────────────

_PART_HEADER_RE = re.compile(r"^### Část (\d+)/\d+", re.MULTILINE)
_TS_MARKER_RE   = re.compile(r"`\[(\d{1,2}):(\d{2})\]`")


def _strip_dia(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm_search(s: str) -> str:
    s = re.sub(r"[^\w\s]", " ", _strip_dia(s.lower()))
    return re.sub(r"\s+", " ", s).strip()


def _parse_part_data(transcript: str) -> dict[int, tuple[str, list[tuple[int, int]]]]:
    """Return {part_num: (part_text, [(char_offset, seconds), ...])}."""
    headers = list(_PART_HEADER_RE.finditer(transcript))
    result = {}
    for i, h in enumerate(headers):
        part_num = int(h.group(1))
        start = h.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(transcript)
        part_text = transcript[start:end]
        markers = [
            (m.start(), int(m.group(1)) * 60 + int(m.group(2)))
            for m in _TS_MARKER_RE.finditer(part_text)
        ]
        result[part_num] = (part_text, markers)
    return result


def _find_text_pos(query: str, part_text: str) -> int | None:
    """Return approximate char offset of query in part_text, or None."""
    words = query.split()
    norm_part = _norm_search(part_text)
    # Try progressively shorter fragments, skipping first word
    for start_w in (1, 0):
        for n in range(min(7, len(words) - start_w), 2, -1):
            frag = _norm_search(" ".join(words[start_w: start_w + n]))
            if not frag:
                continue
            idx = norm_part.find(frag)
            if idx >= 0:
                # Map normalised index back to original via length ratio
                ratio = len(part_text) / max(len(norm_part), 1)
                return int(idx * ratio)
    return None


def _interpolate_secs(pos: int, markers: list[tuple[int, int]]) -> int | None:
    """Linearly interpolate (or extrapolate) seconds at char position pos."""
    if not markers:
        return None
    if len(markers) == 1:
        return markers[0][1]
    if pos <= markers[0][0]:
        p0, t0 = markers[0]; p1, t1 = markers[1]
        rate = (t1 - t0) / max(p1 - p0, 1)
        return max(0, int(t0 - rate * (p0 - pos)))
    if pos >= markers[-1][0]:
        p0, t0 = markers[-2]; p1, t1 = markers[-1]
        rate = (t1 - t0) / max(p1 - p0, 1)
        return int(t1 + rate * (pos - p1))
    for i in range(len(markers) - 1):
        p0, t0 = markers[i]; p1, t1 = markers[i + 1]
        if p0 <= pos <= p1:
            frac = (pos - p0) / max(p1 - p0, 1)
            return int(t0 + frac * (t1 - t0))
    return None


def refine_timestamps(summary_json: dict, transcript: str) -> None:
    """Improve highlight/controversy timestamps using text search + linear interpolation."""
    part_data = _parse_part_data(transcript)
    if not part_data:
        return

    def _refine(item: dict, text_field: str) -> None:
        ts = (item.get("timestamp") or "").strip()
        if not ts:
            return
        m = _TS_RE.match(ts)
        if not m:
            return
        part_num = int(m.group(1))
        entry = part_data.get(part_num)
        if not entry:
            return
        part_text, markers = entry
        if not markers:
            return

        raw = item.get(text_field, "")
        # For controversial (Markdown paragraphs), use only the first sentence
        query = re.split(r"[.!?]\s", raw)[0] if text_field == "statement" else raw

        pos = _find_text_pos(query, part_text)
        if pos is None:
            return
        secs = _interpolate_secs(pos, markers)
        if secs is None:
            return
        new_ts = f"{part_num}/{secs // 60:02d}:{secs % 60:02d}"
        if new_ts != ts:
            log.info(f"  Timestamp refined: {ts} → {new_ts}")
            item["timestamp"] = new_ts

    for item in summary_json.get("highlights") or []:
        _refine(item, "text")
    for item in summary_json.get("controversial") or []:
        _refine(item, "statement")


# ── Fact-check pass ──────────────────────────────────────────────────────────

def factcheck_items(summary_json: dict, model: str) -> None:
    """Second LLM pass: add factual context to highlights and controversies in place."""
    if not FACTCHECK_PROMPT_FILE.exists():
        log.warning("  Fact-check prompt not found — skipping")
        return

    items = []
    for i, h in enumerate(summary_json.get("highlights") or []):
        items.append({"id": f"h{i}", "text": h.get("text", ""),
                      "speaker": h.get("speaker"), "affiliation": h.get("affiliation")})
    for i, c in enumerate(summary_json.get("controversial") or []):
        items.append({"id": f"c{i}", "statement": c.get("statement", "")[:400],
                      "speaker": c.get("speaker"), "affiliation": c.get("affiliation")})
    if not items:
        return

    system = FACTCHECK_PROMPT_FILE.read_text(encoding="utf-8")
    user = json.dumps(items, ensure_ascii=False, indent=2)
    try:
        response = llm_chat(system=system, user=user, model=model, max_tokens=2048)
    except RuntimeError as e:
        log.warning(f"  Fact-check LLM call failed: {e}")
        return

    parsed = extract_json_block(response)
    if parsed is None:
        try:
            parsed = json.loads(response.strip())
        except json.JSONDecodeError:
            log.warning("  Fact-check: could not parse response as JSON — skipping")
            return
    if not isinstance(parsed, list):
        log.warning("  Fact-check: expected JSON array — skipping")
        return

    context_map = {entry["id"]: entry.get("context") for entry in parsed if "id" in entry}
    matched = 0
    for i, h in enumerate(summary_json.get("highlights") or []):
        ctx = context_map.get(f"h{i}")
        if ctx:
            h["context"] = ctx
            matched += 1
    for i, c in enumerate(summary_json.get("controversial") or []):
        ctx = context_map.get(f"c{i}")
        if ctx:
            c["context"] = ctx
            matched += 1
    log.info(f"  Fact-check: annotated {matched}/{len(items)} items")


# ── JSON recovery ────────────────────────────────────────────────────────────

def _json_recovery_pass(response_md: str, prompt: str, model: str) -> dict | None:
    """Try to extract a JSON summary when the main pass produced no code-fenced block.

    Strategy:
    1. Parse the response as raw JSON (model omitted the code fence).
    2. Regex-search for an unfenced JSON object containing 'schema_version'.
    3. LLM recovery: feed the response tail back and ask for just the JSON block.
    """
    # 1. Raw JSON (no code fence)
    stripped = response_md.strip()
    if stripped.startswith("{"):
        try:
            result = json.loads(stripped)
            if isinstance(result, dict):
                log.info("  JSON recovered: unfenced object")
                return result
        except json.JSONDecodeError:
            pass

    # 2. Unfenced JSON object embedded in prose
    m = re.search(r'(\{[^{}]{0,200}"schema_version"[\s\S]*\})\s*$', response_md)
    if m:
        try:
            result = json.loads(m.group(1))
            if isinstance(result, dict):
                log.info("  JSON recovered: extracted from prose")
                return result
        except json.JSONDecodeError:
            pass

    # 3. LLM re-extraction — send the response tail with the original prompt
    log.info("  Attempting JSON recovery pass (LLM re-extraction)")
    tail = response_md[-8000:] if len(response_md) > 8000 else response_md
    recovery_user = (
        "Níže je shrnutí parlamentní akce. Na konci CHYBÍ JSON blok. "
        "Vrať POUZE JSON blok uzavřený do ```json ... ```, žádný jiný text.\n\n"
        + tail
    )
    try:
        recovery_resp = llm_chat(
            system=prompt,
            user=recovery_user,
            model=model,
            max_tokens=LLM_MAX_TOKENS,
        )
        result = extract_json_block(recovery_resp)
        if result:
            log.info("  JSON recovered via LLM re-extraction")
        return result
    except (QuotaExhaustedError, RuntimeError) as e:
        log.warning(f"  JSON recovery pass failed: {e}")
        return None


# ── Per-event summarization ───────────────────────────────────────────────────

def summarize_event(event: dict, prompt: str, model: str, force: bool, feedback: str = "") -> bool:
    """
    Summarize one event. Writes JSON and MD to summaries/.
    Updates event dict in place. Returns True when JSON was saved successfully.
    Pass feedback to inject human corrections into the system prompt.
    """
    event_id = event["id"]
    final_path = find_final_file(event_id)
    if not final_path:
        log.warning(f"  No final/ file for event {event_id} — skipping")
        return False

    json_path, md_path = summary_paths(final_path)

    if not force and json_path.exists():
        # File exists — repair metadata if it got out of sync (e.g. interrupted run)
        if not event.get("summary_done_at"):
            try:
                saved = json.loads(json_path.read_text(encoding="utf-8"))
                event["summary_local"] = str(json_path)
                event["summary_done_at"] = saved.get("created_at") or datetime.now().isoformat(timespec="seconds")
                event["summary_model"] = saved.get("model_hint") or ""
                event["summary_schema_version"] = saved.get("schema_version", "1")
                log.info(f"  Metadata repaired from existing file: {json_path.name}")
            except Exception:
                pass
        return True

    transcript = final_path.read_text(encoding="utf-8")

    invite = invitation_text(event)
    if invite:
        transcript = (
            "## PODKLADOVÉ DOKUMENTY (pozvánka, program)\n\n"
            + invite
            + "\n\n---\n\n"
            + transcript
        )
        log.info("  Prepended invitation/agenda text")

    # Append human corrections to the system prompt so they apply to every LLM call
    effective_prompt = prompt
    if feedback:
        log.info(f"  Feedback injected: {feedback[:80]}{'…' if len(feedback) > 80 else ''}")
        effective_prompt = (
            prompt
            + "\n\n## OPRAVY A UPŘESNĚNÍ (poskytnuté uživatelem — mají přednost před přepisem)\n\n"
            + feedback.strip()
            + "\n"
        )

    single_pass_budget = _max_input_chars(PROMPT_RESERVE_TOKENS, LLM_MAX_TOKENS, model)
    log.info(f"  Summarizing: {final_path.name} ({len(transcript):,} chars)")

    t0 = time.time()
    try:
        if len(transcript) > single_pass_budget:
            response = multipass_summarize(transcript, effective_prompt, model, event)
        else:
            out_tokens = _output_tokens(len(transcript), model)
            response = llm_chat(system=effective_prompt, user=transcript, model=model, max_tokens=out_tokens)
    except QuotaExhaustedError:
        raise  # propagate to run() so it can switch to fallback model
    except RuntimeError as e:
        log.error(f"  LLM call failed: {e}")
        return False
    elapsed = time.time() - t0
    log.info(f"  LLM response in {elapsed:.0f}s")

    summary_json = extract_json_block(response)
    if summary_json is None:
        log.warning("  No JSON block in response — attempting recovery")
        summary_json = _json_recovery_pass(response, effective_prompt, model)
    if summary_json is not None:
        summary_json["model_hint"] = model
        summary_json["created_at"] = datetime.now().isoformat(timespec="seconds")
        # Inject source transcript path so the summary is traceable
        if summary_json.get("event") and not summary_json["event"].get("sources"):
            summary_json["event"]["sources"] = [str(final_path)]
        # Inject video parts for timestamp deep-links (built from metadata, not from LLM)
        video_parts = _extract_video_parts(event)
        if video_parts and summary_json.get("event") is not None:
            summary_json["event"]["video_parts"] = video_parts
        # Normalize transcription.source — LLM may paraphrase the header value
        _src = (summary_json.get("transcription") or {}).get("source", "")
        _src_norm = _normalize_source(_src)
        if _src_norm and summary_json.get("transcription"):
            summary_json["transcription"]["source"] = _src_norm
        # Normalize highlight type strings (LLM sometimes uses Czech spellings)
        for item in (summary_json.get("highlights") or []):
            if "type" in item:
                item["type"] = _normalize_highlight_type(item["type"])
        enrich_speakers(summary_json)
        refine_timestamps(summary_json, transcript)
        extract_screenshots(summary_json, event)
        factcheck_items(summary_json, model)
        errors = validate_summary(summary_json)
        for err in errors:
            log.warning(f"  Schema violation: {err}")

    (SUMMARIES_DIR / "json").mkdir(parents=True, exist_ok=True)
    (SUMMARIES_DIR / "md").mkdir(parents=True, exist_ok=True)

    # Always save full LLM response as Markdown for human review
    tmp_md = md_path.with_suffix(".md.tmp")
    tmp_md.write_text(response, encoding="utf-8")
    tmp_md.rename(md_path)

    if summary_json is None:
        log.warning(f"  No JSON block found — saved MD only: {md_path}")
        return False

    tmp_json = json_path.with_suffix(".json.tmp")
    tmp_json.write_text(json.dumps(summary_json, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_json.rename(json_path)

    event["summary_local"] = str(json_path)
    event["summary_done_at"] = datetime.now().isoformat(timespec="seconds")
    event["summary_model"] = model
    event["summary_schema_version"] = summary_json.get("schema_version", "1")
    log.info(f"  Saved → {json_path}")
    return True

# ── Status report ─────────────────────────────────────────────────────────────

def print_status(meta: dict) -> None:
    events = meta["events"]
    print(f"\nSummary status  (last sync: {meta.get('last_sync', '?')})\n")
    print(f"{'ID':>6}  {'Status':14}  {'Schema':>6}  {'Model':<34}  Name")
    print("-" * 100)
    for ev in sorted(events.values(), key=lambda e: e.get("ts") or ""):
        final = find_final_file(ev["id"])
        if not final:
            status, schema, model_s = "no transcript", "", ""
        elif ev.get("summary_done_at") and Path(ev.get("summary_local", "")).exists():
            status  = "✓ done"
            schema  = ev.get("summary_schema_version", "?")
            model_s = ev.get("summary_model", "?")
        elif final:
            status, schema, model_s = "pending", "", ""
        else:
            status, schema, model_s = "—", "", ""
        name = ev.get("name", "")[:40]
        print(f"{ev['id']:>6}  {status:14}  {schema:>6}  {model_s:<34}  {name}")
    print()

# ── Main ──────────────────────────────────────────────────────────────────────

def run(
    event_filter: str | None,
    model: str,
    force: bool,
    feedback: str = "",
    fallback_model: str = "",
) -> None:
    meta = load_metadata()
    prompt = load_prompt()

    targets = (
        [meta["events"][event_filter]]
        if event_filter and event_filter in meta["events"]
        else list(meta["events"].values())
    )

    active_model = model
    for event in targets:
        if not find_final_file(event["id"]):
            continue
        if (not force and not feedback
                and event.get("summary_done_at")
                and Path(event.get("summary_local", "")).exists()):
            continue

        log.info(f"Event [{event['id']}] {event.get('name', '')[:60]}")
        try:
            ok = summarize_event(event, prompt, active_model, force or bool(feedback), feedback=feedback)
        except QuotaExhaustedError as exc:
            fb = fallback_model or DEFAULT_FALLBACK_MODEL
            if fb and active_model != fb:
                log.warning(f"  {exc}")
                log.warning(f"  Switching to fallback model: {fb}")
                active_model = fb
                try:
                    ok = summarize_event(event, prompt, active_model, force or bool(feedback), feedback=feedback)
                except RuntimeError as e2:
                    log.error(f"  Fallback also failed: {e2}")
                    ok = False
            else:
                log.error(f"  Daily quota exhausted and no fallback available: {exc}")
                break
        if ok:
            save_metadata(meta)


def _arg(args: list[str], flag: str) -> str | None:
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
        print(f"{flag} requires an argument", file=sys.stderr)
        sys.exit(1)
    return None


def main() -> None:
    args = sys.argv[1:]

    if "--status" in args:
        print_status(load_metadata())
        return

    model          = _arg(args, "--model") or DEFAULT_MODEL
    fallback_model = _arg(args, "--fallback-model") or DEFAULT_FALLBACK_MODEL
    event_id       = _arg(args, "--event")
    feedback       = _arg(args, "--feedback") or ""
    force          = "--force" in args

    if feedback and not event_id:
        print("--feedback requires --event <id>", file=sys.stderr)
        sys.exit(1)

    log.info(f"Model: {model}  fallback: {fallback_model}  force: {force}")
    run(event_filter=event_id, model=model, force=force, feedback=feedback, fallback_model=fallback_model)


if __name__ == "__main__":
    main()
