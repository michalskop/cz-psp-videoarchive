#!/usr/bin/env python3
"""
PSP Transcription Script
Transcribes downloaded videos using faster-whisper and merges them into
per-event Markdown files.

Usage:
    python3 transcribe.py                        # transcribe all ready videos
    python3 transcribe.py --status               # show per-event progress
    python3 transcribe.py --event 2798           # process one specific event
    python3 transcribe.py --merge-only           # only (re-)merge, no Whisper
    python3 transcribe.py --preset medium        # use a named quality preset
    python3 transcribe.py --model large-v2       # override model, keep preset settings
    python3 transcribe.py --list-presets         # show all available presets
    python3 transcribe.py --order knowledge      # Seminář→Konference→…→Jednání výborů
    python3 transcribe.py --order parliament     # reverse: Jednání výborů first

Presets (from fastest to best quality):
    small        faster-whisper small,  beam 5  — quick smoke-test
    medium       faster-whisper medium, beam 5  — good balance
    medium-best  faster-whisper medium, beam 10 — better quality, slower
    large-v2     faster-whisper large-v2, beam 10
    large-v3     faster-whisper large-v3, beam 10 — default, best tested
    groq-turbo   Groq API whisper-large-v3-turbo  — fast cloud transcription
    groq-large-v3 Groq API whisper-large-v3       — best cloud transcription

Groq backend:
    export GROQ_API_KEY=your_key_here
    python3 transcribe.py --preset groq-turbo --event 2798
    Files > 25 MB are automatically downsampled to audio via ffmpeg.

Dependencies:
    pip install faster-whisper      # for local presets
    export GROQ_API_KEY=...         # for groq presets
    # or activate the transcribe-cs venv:
    source /home/michal/dev/psp/transcribe-cs/.venv/bin/activate

Output files:
    transcriptions/**/*.json   per-segment Whisper data (precise timestamps)
    final/<slug>.md            merged human+LLM-readable event transcript
"""

import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Load .env (if present) ────────────────────────────────────────────────────
# Allows setting GROQ_API_KEY locally without exporting it in the shell.
# In CI / production, set the variable in the environment directly.
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ── Configuration ─────────────────────────────────────────────────────────────

METADATA_FILE = Path("metadata.json")
FINAL_DIR = Path("final")

# Named presets — correspond to the configurations tested in compare_advanced.py.
# Each preset overrides only the keys that differ from the base settings below.
# "large-v3" is the default and best-tested preset.
PRESETS: dict[str, dict] = {
    # ── faster-whisper (local) ────────────────────────────────────────────────
    "small": {
        "backend": "faster-whisper",
        "model_size": "small",
        "beam_size": 5,
        "compression_ratio_threshold": 2.4,
        "log_prob_threshold": -1.0,
        "no_speech_threshold": 0.6,
    },
    "medium": {
        "backend": "faster-whisper",
        "model_size": "medium",
        "beam_size": 5,
        "compression_ratio_threshold": 2.4,
        "log_prob_threshold": -1.0,
        "no_speech_threshold": 0.6,
    },
    "medium-best": {
        "backend": "faster-whisper",
        "model_size": "medium",
        "beam_size": 10,
        "compression_ratio_threshold": 2.2,
        "log_prob_threshold": -0.8,
        "no_speech_threshold": 0.5,
    },
    "large-v2": {
        "backend": "faster-whisper",
        "model_size": "large-v2",
        "beam_size": 10,
        "compression_ratio_threshold": 2.2,
        "log_prob_threshold": -0.8,
        "no_speech_threshold": 0.5,
    },
    "large-v3": {
        "backend": "faster-whisper",
        "model_size": "large-v3",
        "beam_size": 10,
        "compression_ratio_threshold": 2.2,
        "log_prob_threshold": -0.8,
        "no_speech_threshold": 0.5,
    },
    # ── Groq API ──────────────────────────────────────────────────────────────
    # Requires GROQ_API_KEY env var.  Files > 25 MB are downsampled to audio
    # via ffmpeg before upload; ffmpeg must be on PATH.
    "groq-turbo": {
        "backend": "groq",
        "model_size": "whisper-large-v3-turbo",
    },
    "groq-large-v3": {
        "backend": "groq",
        "model_size": "whisper-large-v3",
    },
}

DEFAULT_PRESET = "large-v3"

# Base settings shared by all presets.
# Override preset or individual keys via --preset / --model on the command line.
WHISPER_CONFIG = {
    # Which backend to use: "faster-whisper" or "groq"
    "backend": "faster-whisper",
    # faster-whisper hardware settings (ignored by Groq)
    "device": "cpu",        # "cuda" for GPU (set compute_type to "float16")
    "compute_type": "int8",
    "cpu_threads": 8,
    # Where to cache downloaded models.  None = faster-whisper default
    # (~/.cache/huggingface/hub/).  Set to an absolute path to use a shared
    # location or a different disk.  Models are downloaded once and reused.
    "model_cache_dir": None,
    # Transcription parameters (ignored by Groq except language)
    "language": "cs",
    "vad_filter": True,
    "temperature": 0.0,
    "condition_on_previous_text": False,
    "word_timestamps": False,
    # These are overridden by presets:
    "model_size": "large-v3",
    "beam_size": 10,
    "compression_ratio_threshold": 2.2,
    "log_prob_threshold": -0.8,
    "no_speech_threshold": 0.5,
}

# ── Groq settings ─────────────────────────────────────────────────────────────

# API key is read from this environment variable at runtime.
GROQ_API_KEY_ENV = "GROQ_API_KEY"
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
# Groq's hard limit per request.  Files larger than this are downsampled
# to a small mono MP3 via ffmpeg before uploading.
GROQ_MAX_BYTES = 25 * 1024 * 1024  # 25 MB


def apply_preset(preset_name: str) -> None:
    """Merge a named preset into WHISPER_CONFIG."""
    if preset_name not in PRESETS:
        print(f"Unknown preset '{preset_name}'. Available: {', '.join(PRESETS)}", file=sys.stderr)
        sys.exit(1)
    WHISPER_CONFIG.update(PRESETS[preset_name])

# How often (in seconds of audio) to inject a `[MM:SS]` source marker into
# the merged Markdown.  Markers are placed at the nearest segment boundary
# at or after this interval.
MARKER_INTERVAL_SEC = 120
# Silence gap (seconds between end of one segment and start of the next) that
# triggers a new paragraph in the merged Markdown output.
PARAGRAPH_GAP_SEC = 3.0
# Whisper hallucination patterns — segments matching these are dropped from output.
_JUNK_SEGMENT = re.compile(
    r'titulky\s+vytvo',
    re.IGNORECASE,
)

# Czech event-type descriptions used to build the initial_prompt for Whisper.
# The prompt primes the model with domain vocabulary and register.
CATEGORY_PROMPTS = {
    "Kulatý stůl":        "kulatý stůl v Poslanecké sněmovně",
    "Tiskové konference": "tisková konference poslanců Poslanecké sněmovny",
    "Seminář":            "odborný seminář v Poslanecké sněmovně",
    "Konference":         "konference pořádaná Poslaneckou sněmovnou",
    "Veřejné slyšení":    "veřejné slyšení výboru Poslanecké sněmovny",
    "Jednání výborů":     "jednání výboru Poslanecké sněmovny",
    "Debata":             "parlamentní debata v Poslanecké sněmovně",
}

# knowledge order: richest public-interest content first
# parliament order: procedural/committee content first (reverse)
KNOWLEDGE_ORDER = [
    "Seminář",
    "Konference",
    "Kulatý stůl",
    "Veřejné slyšení",
    "Tiskové konference",
    "Jednání výborů",
    "Ostatní",
]

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("psp-transcribe")

# ── Metadata helpers ──────────────────────────────────────────────────────────

def load_metadata() -> dict:
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_metadata(meta: dict) -> None:
    tmp = METADATA_FILE.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    tmp.replace(METADATA_FILE)


# ── Prompt generation ─────────────────────────────────────────────────────────

def build_initial_prompt(event: dict) -> str:
    """Build a Czech initial_prompt from the event category and name.

    The prompt steers Whisper towards parliamentary Czech vocabulary and
    helps it handle proper nouns from the event title.
    """
    category = event.get("category", "")
    name = event.get("name", "")
    desc = CATEGORY_PROMPTS.get(category, "jednání v Poslanecké sněmovně")
    # Truncate the name so the prompt stays concise
    short_name = name[:120] if len(name) > 120 else name
    return (
        f"Toto je záznam {desc}. "
        f"Téma: {short_name}. "
        f"Přepis je v češtině, obsahuje odbornou terminologii a jména."
    )


# ── VTT caption parser ────────────────────────────────────────────────────────

def _vtt_time_to_sec(t: str) -> float:
    """Parse VTT timestamp (HH:MM:SS.mmm or MM:SS.mmm) → seconds."""
    t = t.strip().replace(",", ".")
    parts = t.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(t)


def parse_vtt(vtt_path: Path) -> list[dict]:
    """Parse a VTT file into a list of segment dicts compatible with Whisper output."""
    segments = []
    text = vtt_path.read_text(encoding="utf-8")
    # Split on blank lines; skip the WEBVTT header
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        # Find the --> line
        arrow_idx = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if arrow_idx is None:
            continue
        times = lines[arrow_idx].split("-->")
        if len(times) != 2:
            continue
        start = _vtt_time_to_sec(times[0])
        end = _vtt_time_to_sec(times[1].split()[0])  # strip optional cue settings
        caption_text = " ".join(lines[arrow_idx + 1:]).strip()
        if caption_text:
            segments.append({"start": start, "end": end, "text": caption_text})
    return segments


# ── Whisper transcription ─────────────────────────────────────────────────────

_whisper_model = None  # lazy-loaded singleton

def _get_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            log.error(
                "faster-whisper not found.  Install it:\n"
                "  pip install faster-whisper\n"
                "or activate the transcribe-cs venv:\n"
                "  source /home/michal/dev/psp/transcribe-cs/.venv/bin/activate"
            )
            sys.exit(1)
        cfg = WHISPER_CONFIG
        cache = cfg.get("model_cache_dir")
        log.info(f"Loading Whisper model '{cfg['model_size']}' ({cfg['device']}/{cfg['compute_type']}) "
                 f"cache={cache or '~/.cache/huggingface/hub'}")
        kwargs = dict(
            device=cfg["device"],
            compute_type=cfg["compute_type"],
            cpu_threads=cfg["cpu_threads"],
        )
        if cache:
            kwargs["download_root"] = cache
        _whisper_model = WhisperModel(cfg["model_size"], **kwargs)
        log.info("Model loaded.")
    return _whisper_model


def transcribe_file(video_path: Path, initial_prompt: str) -> tuple[list[dict], dict]:
    """
    Run Whisper on a video file.
    Returns (segments, info_dict) where each segment is
    {"start": float, "end": float, "text": str}.
    """
    model = _get_model()
    cfg = WHISPER_CONFIG
    params = {
        "language":                    cfg["language"],
        "beam_size":                   cfg["beam_size"],
        "vad_filter":                  cfg["vad_filter"],
        "temperature":                 cfg["temperature"],
        "condition_on_previous_text":  cfg["condition_on_previous_text"],
        "compression_ratio_threshold": cfg["compression_ratio_threshold"],
        "log_prob_threshold":          cfg["log_prob_threshold"],
        "no_speech_threshold":         cfg["no_speech_threshold"],
        "word_timestamps":             cfg["word_timestamps"],
        "initial_prompt":              initial_prompt,
    }
    raw_segments, info = model.transcribe(str(video_path), **params)
    segments = [
        {"start": float(s.start), "end": float(s.end), "text": s.text.strip()}
        for s in raw_segments
        if s.text.strip()
    ]
    info_dict = {
        "language": info.language,
        "language_probability": float(info.language_probability),
        "duration_sec": float(info.duration),
    }
    return segments, info_dict


# ── Groq API transcription ────────────────────────────────────────────────────

def _extract_audio(video_path: Path) -> Path:
    """Downsample video to a small mono MP3 via ffmpeg.

    Used when the source file exceeds Groq's 25 MB limit.
    Output is written next to the source file as <name>.groq_audio.mp3
    and deleted after upload.
    """
    import subprocess
    out = video_path.with_suffix(".groq_audio.mp3")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn",              # drop video stream
        "-ar", "16000",     # 16 kHz — sufficient for speech
        "-ac", "1",         # mono
        "-b:a", "48k",      # 48 kbps → ~3.6 MB per 10 min
        str(out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg not found on PATH.  Install it to handle files > 25 MB:\n"
            "  sudo apt install ffmpeg"
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()[:300]}")
    return out


def _groq_multipart(fields: dict, filename: str, file_data: bytes, mime: str) -> tuple[bytes, bytes]:
    """Build a multipart/form-data body.  Returns (body, content_type_header)."""
    import os
    boundary = b"PspGroqBoundary" + os.urandom(6).hex().encode()
    parts = []
    for name, value in fields.items():
        parts.append(
            b"--" + boundary + b"\r\n"
            b'Content-Disposition: form-data; name="' + name.encode() + b'"\r\n\r\n'
            + str(value).encode() + b"\r\n"
        )
    parts.append(
        b"--" + boundary + b"\r\n"
        b'Content-Disposition: form-data; name="file"; filename="'
        + filename.encode() + b'"\r\n'
        b"Content-Type: " + mime.encode() + b"\r\n\r\n"
        + file_data + b"\r\n"
    )
    parts.append(b"--" + boundary + b"--\r\n")
    return b"".join(parts), b"multipart/form-data; boundary=" + boundary


def _groq_parse_retry_after(body: str, headers) -> float:
    """Return seconds to wait from a Groq 429 response.  Adds a 5 s safety buffer."""
    # Standard HTTP header takes priority
    for h in ("Retry-After", "retry-after"):
        val = headers.get(h)
        if val:
            try:
                return float(val) + 5
            except ValueError:
                pass
    # Parse Groq message: "Please try again in 2m51s" / "in 30s" / "in 1h2m3s"
    m = re.search(r"try again in\s+((?:\d+h\s*)?(?:\d+m\s*)?(?:\d+(?:\.\d+)?s)?)", body)
    if m:
        t = m.group(1)
        h = int(re.search(r"(\d+)h", t).group(1)) if "h" in t else 0
        mn = int(re.search(r"(\d+)m", t).group(1)) if "m" in t else 0
        s = float(re.search(r"(\d+(?:\.\d+)?)s", t).group(1)) if "s" in t else 0
        return h * 3600 + mn * 60 + s + 5
    return 65.0  # fallback: 60 s + buffer


def _fmt_wait(seconds: float) -> str:
    """Human-readable wait duration: '2m 51s', '1h 30m', etc."""
    seconds = int(seconds)
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}h {m}m" if m else f"{h}h"
    if m:
        return f"{m}m {s}s" if s else f"{m}m"
    return f"{s}s"


def groq_transcribe_file(audio_path: Path, prompt: str) -> tuple[list[dict], dict]:
    """Transcribe a file via the Groq audio API.

    Automatically extracts audio via ffmpeg when the file exceeds 25 MB.
    Returns (segments, info_dict) in the same format as transcribe_file().
    """
    import urllib.request
    import urllib.error

    api_key = os.environ.get(GROQ_API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError(
            f"Groq API key not set.  Export it before running:\n"
            f"  export {GROQ_API_KEY_ENV}=your_key_here"
        )

    tmp_audio: Path | None = None
    upload_path = audio_path

    if audio_path.stat().st_size > GROQ_MAX_BYTES:
        size_mb = audio_path.stat().st_size / 1_000_000
        log.info(f"  File is {size_mb:.0f} MB > 25 MB limit — extracting audio via ffmpeg")
        tmp_audio = _extract_audio(audio_path)
        upload_path = tmp_audio
        log.info(f"  Audio extracted: {upload_path.stat().st_size / 1_000_000:.1f} MB")

    def _groq_send(path: Path) -> dict:
        mime = "audio/mpeg" if path.suffix == ".mp3" else "video/mp4"
        file_data = path.read_bytes()
        fields = {
            "model":           WHISPER_CONFIG["model_size"],
            "language":        WHISPER_CONFIG["language"],
            "response_format": "verbose_json",
            "prompt":          prompt,
        }
        body, ct = _groq_multipart(fields, path.name, file_data, mime)
        req = urllib.request.Request(
            GROQ_API_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  ct.decode(),
                "User-Agent":    "psp-videoarchive/1.0",
            },
        )
        while True:
            try:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                err_body = e.read().decode()
                if e.code == 429:
                    wait = _groq_parse_retry_after(err_body, e.headers)
                    log.warning(
                        f"  Groq rate limit — waiting {_fmt_wait(wait)} before retry "
                        f"({path.name})"
                    )
                    time.sleep(wait)
                else:
                    raise urllib.error.HTTPError(e.url, e.code, err_body, e.headers, None)

    try:
        try:
            data = _groq_send(upload_path)
        except urllib.error.HTTPError as e:
            if e.code == 400 and "valid media" in str(e.reason) and tmp_audio is None:
                log.warning(f"  Groq rejected file as invalid media — extracting audio via ffmpeg")
                tmp_audio = _extract_audio(audio_path)
                upload_path = tmp_audio
                log.info(f"  Audio extracted: {upload_path.stat().st_size / 1_000_000:.1f} MB")
                data = _groq_send(upload_path)
            else:
                raise RuntimeError(f"Groq API error {e.code}: {str(e.reason)[:300]}")
    finally:
        if tmp_audio and tmp_audio.exists():
            tmp_audio.unlink()

    segments = [
        {"start": float(s["start"]), "end": float(s["end"]), "text": s["text"].strip()}
        for s in data.get("segments", [])
        if s.get("text", "").strip()
    ]
    info_dict = {
        "language": data.get("language", WHISPER_CONFIG["language"]),
        "language_probability": 1.0,   # Groq doesn't expose this
        "duration_sec": float(data.get("duration", 0)),
    }
    return segments, info_dict


# ── Per-file transcription JSON ───────────────────────────────────────────────

def transcribe_one_file(finfo: dict, event: dict) -> bool:
    """
    Transcribe a single video file (or load its captions) and write the
    transcription JSON.  Updates finfo in place.  Returns True on success.
    """
    video_path = Path(finfo["local_path"])
    out_path = Path(finfo["transcription_local"])

    # Already done and file still there → skip
    if finfo.get("transcription_done_at") and out_path.exists():
        return True

    # ── Use existing captions if available ────────────────────────────────────
    cap_local = finfo.get("captions_local")
    cap_done = finfo.get("captions_downloaded_at")
    if cap_local and cap_done and Path(cap_local).exists():
        log.info(f"  Using captions: {Path(cap_local).name}")
        segments = parse_vtt(Path(cap_local))
        result = {
            "source": "captions",
            "captions_file": cap_local,
            "transcribed_at": datetime.now().isoformat(timespec="seconds"),
            "model": None,
            "initial_prompt": None,
            "language": "cs",
            "language_probability": 1.0,
            "duration_sec": segments[-1]["end"] if segments else 0,
            "num_segments": len(segments),
            "segments": segments,
        }
    # ── Run transcription backend ─────────────────────────────────────────────
    elif video_path.exists():
        prompt = build_initial_prompt(event)
        backend = WHISPER_CONFIG.get("backend", "faster-whisper")
        t0 = time.time()

        if backend == "groq":
            log.info(f"  Transcribing via Groq ({WHISPER_CONFIG['model_size']}): {video_path.name}")
            log.debug(f"  Prompt: {prompt}")
            segments, info = groq_transcribe_file(video_path, prompt)
            elapsed = time.time() - t0
            log.info(f"  Done in {elapsed:.0f}s — {len(segments)} segments")
            result = {
                "source": "groq",
                "transcribed_at": datetime.now().isoformat(timespec="seconds"),
                "model": WHISPER_CONFIG["model_size"],
                "initial_prompt": prompt,
                **info,
                "processing_time_sec": round(elapsed, 1),
                "num_segments": len(segments),
                "segments": segments,
            }
        else:
            log.info(f"  Transcribing: {video_path.name}")
            log.debug(f"  Prompt: {prompt}")
            segments, info = transcribe_file(video_path, prompt)
            elapsed = time.time() - t0
            log.info(f"  Done in {elapsed:.0f}s — {len(segments)} segments, lang={info['language']} ({info['language_probability']:.2f})")
            result = {
                "source": "whisper",
                "transcribed_at": datetime.now().isoformat(timespec="seconds"),
                "model": WHISPER_CONFIG["model_size"],
                "model_config": {k: v for k, v in WHISPER_CONFIG.items()
                                 if k not in ("device", "compute_type", "cpu_threads",
                                              "model_cache_dir")},
                "initial_prompt": prompt,
                **info,
                "processing_time_sec": round(elapsed, 1),
                "num_segments": len(segments),
                "segments": segments,
            }
    else:
        log.warning(f"  Video not on disk and no captions: {video_path}")
        return False

    # ── Trim segments to the content window ──────────────────────────────────
    # from_sec: seconds into the file where actual content begins (skip pre-roll)
    # to_sec:   seconds where content ends; 0 or missing means end of file
    from_sec = finfo.get("from_sec") or 0
    to_sec   = finfo.get("to_sec")  or 0
    if from_sec or to_sec:
        before = len(result["segments"])
        result["segments"] = [
            s for s in result["segments"]
            if s["end"] > from_sec and (not to_sec or s["start"] < to_sec)
        ]
        clipped = before - len(result["segments"])
        if clipped:
            log.info(f"  Clipped {clipped} pre/post-roll segments "
                     f"(from_sec={from_sec}, to_sec={to_sec or 'eof'})")
        result["num_segments"] = len(result["segments"])

    # Write JSON atomically
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    tmp.rename(out_path)

    finfo["transcription_done_at"] = result["transcribed_at"]
    return True


# ── Merged Markdown output ────────────────────────────────────────────────────

def _fmt_sec(sec: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02}:{m:02}:{s:02}"
    return f"{m:02}:{s:02}"


def _slug(text: str, max_len: int = 50) -> str:
    """Make a filesystem-safe slug from a Czech string."""
    table = str.maketrans({
        'á':'a','č':'c','ď':'d','é':'e','ě':'e','í':'i','ň':'n',
        'ó':'o','ř':'r','š':'s','ť':'t','ú':'u','ů':'u','ý':'y','ž':'z',
        'Á':'a','Č':'c','Ď':'d','É':'e','Ě':'e','Í':'i','Ň':'n',
        'Ó':'o','Ř':'r','Š':'s','Ť':'t','Ú':'u','Ů':'u','Ý':'y','Ž':'z',
    })
    s = text.translate(table)
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s[:max_len].lower()


def _segments_to_paragraphs(segments: list[dict], marker_interval: float) -> str:
    """
    Convert a list of Whisper/caption segments into Markdown text with
    periodic `[MM:SS]` source markers and silence-based paragraph breaks.

    A new paragraph is started when:
    - the gap between the end of the previous segment and the start of the
      next is >= PARAGRAPH_GAP_SEC (natural speech pause / topic change), or
    - the next marker_interval boundary is reached (injects a `[MM:SS]` tag).
    """
    if not segments:
        return ""

    lines = []
    next_marker_at = marker_interval
    current_para: list[str] = []
    prev_end: float | None = None

    for seg in segments:
        # Silence gap → paragraph break (without a time marker)
        if prev_end is not None and (seg["start"] - prev_end) >= PARAGRAPH_GAP_SEC:
            if current_para:
                lines.append(" ".join(current_para))
                current_para = []

        # Marker interval → paragraph break + time marker
        if seg["start"] >= next_marker_at:
            if current_para:
                lines.append(" ".join(current_para))
                current_para = []
            lines.append(f"`[{_fmt_sec(seg['start'])}]`")
            while next_marker_at <= seg["start"]:
                next_marker_at += marker_interval

        if _JUNK_SEGMENT.search(seg["text"]):
            continue
        current_para.append(seg["text"])
        prev_end = seg["end"]

    if current_para:
        lines.append(" ".join(current_para))

    return "\n\n".join(lines)


def merge_event(event: dict) -> Path | None:
    """
    Merge all transcription JSONs for an event into a single Markdown file.
    Returns the output path, or None if nothing to merge.
    """
    # Collect all file records that have a transcription, ordered by filename
    # (filenames contain timestamps so lexicographic order = chronological)
    file_records = sorted(
        (
            f for sub in event["subevents"].values()
            for f in sub.get("files", [])
            if f.get("transcription_done_at") and Path(f["transcription_local"]).exists()
        ),
        key=lambda f: f["remote_path"],
    )

    if not file_records:
        return None

    total = sum(
        1
        for sub in event["subevents"].values()
        for f in sub.get("files", [])
    )

    FINAL_DIR.mkdir(exist_ok=True)
    date_str = (event.get("ts") or "")[:10] or "unknown-date"
    slug = _slug(event.get("name", f"event-{event['id']}"))
    out_path = FINAL_DIR / f"event_{event['id']}_{date_str}_{slug}.md"

    lines = []

    # ── Header ────────────────────────────────────────────────────────────────
    lines.append(f"# {event.get('name', 'Nepojmenovaná akce')}\n")
    lines.append("| Pole | Hodnota |")
    lines.append("|------|---------|")
    lines.append(f"| Kategorie | {event.get('category', '–')} |")
    lines.append(f"| Datum | {date_str} |")
    start_t = (event.get("total_start") or "")
    stop_t  = (event.get("total_stop")  or "")
    if start_t or stop_t:
        lines.append(f"| Čas | {start_t} – {stop_t} |")
    lines.append(f"| ID | {event['id']} |")
    lines.append(f"| Části | {len(file_records)}/{total} přepsáno |")
    lines.append("")
    # Collect sources used across all segments for the disclaimer
    _sources = {
        json.loads(Path(f["transcription_local"]).read_text()).get("source")
        for f in file_records
    }
    _models = {
        json.loads(Path(f["transcription_local"]).read_text()).get("model")
        for f in file_records
        if json.loads(Path(f["transcription_local"]).read_text()).get("source") in ("whisper", "groq")
    } - {None}
    if _models:
        _model_note = f" modelem `{'`, `'.join(sorted(_models))}`"
    else:
        _model_note = ""
    lines.append(
        f"> *Přepis byl vytvořen automaticky{_model_note}. Může obsahovat chyby. "
        "Pro ověření citace hledejte podle čísla části a časové značky `[MM:SS]` "
        "v souboru `transcription_local` uvedeném v metadata.json.*"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── One section per video file ────────────────────────────────────────────
    for idx, finfo in enumerate(file_records, start=1):
        json_path = Path(finfo["transcription_local"])
        data = json.loads(json_path.read_text(encoding="utf-8"))
        segments = data.get("segments", [])

        filename = Path(finfo["remote_path"]).name
        from_sec = finfo.get("from_sec", 0)
        source_note = (
            f"od `{_fmt_sec(from_sec)}` v souboru"
            if from_sec
            else "od začátku souboru"
        )

        lines.append(f"### Část {idx}/{len(file_records)} — `{filename}`")
        src = data.get("source")
        if src == "captions":
            lines.append(f"*Zdroj: titulky (VTT), {source_note}*")
        elif src == "groq":
            lines.append(f"*Zdroj: Groq API `{data.get('model', '?')}`, {source_note}*")
        else:
            lines.append(f"*Zdroj: Whisper `{data.get('model', '?')}`, {source_note}*")
        lines.append("")

        body = _segments_to_paragraphs(segments, MARKER_INTERVAL_SEC)
        if body:
            lines.append(body)
        else:
            lines.append("*(žádný přepis — tichá část nebo prázdný soubor)*")
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"  Merged → {out_path}")
    return out_path


# ── Status report ─────────────────────────────────────────────────────────────

def print_status(meta: dict) -> None:
    events = meta["events"]
    print(f"\nTranscription status  (last sync: {meta.get('last_sync', '?')})\n")
    print(f"{'ID':>6}  {'Stav':12}  {'Části':>10}  Název")
    print("-" * 80)

    for ev in sorted(events.values(), key=lambda e: e.get("ts") or ""):
        all_files = [
            f for sub in ev["subevents"].values()
            for f in sub.get("files", [])
        ]
        if not all_files:
            done, total = 0, "?"
            status = "planned"
        else:
            done = sum(
                1 for f in all_files
                if f.get("transcription_done_at") and Path(f["transcription_local"]).exists()
            )
            cap = sum(
                1 for f in all_files
                if f.get("captions_downloaded_at") and Path(f.get("captions_local", "")).exists()
            )
            total = len(all_files)
            if done + cap == total:
                status = "✓ done"
            elif done + cap > 0:
                status = "partial"
            elif ev.get("status") == "downloaded":
                status = "ready"
            else:
                status = ev.get("status", "?")

        parts_str = f"{done}/{total}" + (f" (+{cap}cap)" if cap else "")
        name = ev.get("name", "")[:55]
        print(f"{ev['id']:>6}  {status:12}  {parts_str:>10}  {name}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def _category_key(event: dict, reverse: bool) -> tuple:
    cat = event.get("category", "")
    try:
        rank = KNOWLEDGE_ORDER.index(cat)
    except ValueError:
        # Unknown/new categories always sort last regardless of direction
        return (1, event.get("ts") or "")
    n = len(KNOWLEDGE_ORDER)
    ordered_rank = (n - 1 - rank) if reverse else rank
    return (0, ordered_rank, event.get("ts") or "")


def run(event_filter: str | None = None, merge_only: bool = False,
        order: str | None = None) -> None:
    meta = load_metadata()
    events = meta["events"]

    if event_filter and event_filter in events:
        targets = [events[event_filter]]
    else:
        targets = list(events.values())
        if order == "knowledge":
            targets.sort(key=lambda e: _category_key(e, reverse=False))
        elif order == "parliament":
            targets.sort(key=lambda e: _category_key(e, reverse=True))

    for event in targets:
        all_files = [
            f for sub in event["subevents"].values()
            for f in sub.get("files", [])
        ]
        if not all_files:
            continue

        needs_transcription = [
            f for f in all_files
            if not (f.get("transcription_done_at") and Path(f["transcription_local"]).exists())
        ]

        if needs_transcription and not merge_only:
            log.info(f"Event [{event['id']}] {event.get('name', '')[:60]}")
            log.info(f"  {len(needs_transcription)}/{len(all_files)} files need transcription")
            for i, finfo in enumerate(needs_transcription, 1):
                if not (Path(finfo["local_path"]).exists()
                        or (finfo.get("captions_downloaded_at") and Path(finfo.get("captions_local", "")).exists())):
                    log.warning(f"  [{i}/{len(needs_transcription)}] Skipping {Path(finfo['local_path']).name}: not on disk")
                    continue
                log.info(f"  [{i}/{len(needs_transcription)}] {Path(finfo['local_path']).name}")
                try:
                    ok = transcribe_one_file(finfo, event)
                except Exception as exc:
                    log.warning(f"  [{i}/{len(needs_transcription)}] Failed: {exc} — marking for redownload")
                    local = Path(finfo["local_path"])
                    if local.exists():
                        local.unlink()
                    finfo["downloaded_at"] = None
                    event["status"] = _compute_status(event)
                    save_metadata(meta)
                    continue
                if ok:
                    # Recompute event status
                    event["status"] = _compute_status(event)
                    save_metadata(meta)

        # Merge if all files now have a transcription (or captions)
        transcribed = [
            f for f in all_files
            if (f.get("transcription_done_at") and Path(f["transcription_local"]).exists())
            or (f.get("captions_downloaded_at") and Path(f.get("captions_local", "")).exists())
        ]
        if transcribed:
            merge_event(event)


def _compute_status(event: dict) -> str:
    """Minimal status recomputation (mirrors sync.py logic)."""
    all_files = [
        f for sub in event["subevents"].values()
        for f in sub.get("files", [])
    ]
    if not all_files:
        return "planned"
    transcribed = [
        f for f in all_files
        if (f.get("transcription_done_at") and Path(f["transcription_local"]).exists())
        or (f.get("captions_downloaded_at") and Path(f.get("captions_local", "")).exists())
    ]
    on_disk = [f for f in all_files if f.get("downloaded_at") and Path(f["local_path"]).exists()]
    if len(transcribed) == len(all_files):
        return "transcribed"
    covered = len({id(f) for f in transcribed} | {id(f) for f in on_disk})
    if covered == len(all_files):
        return "downloaded"
    if covered:
        return "partial"
    return "available"


def _arg(args: list[str], flag: str) -> str | None:
    """Return the value after `flag` in args, or None."""
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
        print(f"{flag} requires an argument", file=sys.stderr)
        sys.exit(1)
    return None


def main() -> None:
    args = sys.argv[1:]

    if "--list-presets" in args:
        print(f"\nAvailable presets (default: {DEFAULT_PRESET}):\n")
        print(f"  {'NAME':<14} {'BACKEND':<14} {'MODEL':<24} DETAILS")
        print(f"  {'-'*14} {'-'*14} {'-'*24} -------")
        for name, overrides in PRESETS.items():
            cfg = {**WHISPER_CONFIG, **overrides}
            marker = " ← default" if name == DEFAULT_PRESET else ""
            backend = cfg.get("backend", "faster-whisper")
            model = cfg["model_size"]
            if backend == "groq":
                details = "cloud API  (GROQ_API_KEY required)"
            else:
                details = f"beam={cfg['beam_size']}  vad={cfg['vad_filter']}  device={cfg['device']}"
            print(f"  {name:<14} {backend:<14} {model:<24} {details}{marker}")
        print()
        return

    if "--status" in args:
        print_status(load_metadata())
        return

    # Apply preset first, then --model can override just the model size
    preset_name = _arg(args, "--preset") or DEFAULT_PRESET
    apply_preset(preset_name)

    model_override = _arg(args, "--model")
    if model_override:
        WHISPER_CONFIG["model_size"] = model_override

    event_id = _arg(args, "--event")
    merge_only = "--merge-only" in args
    order = _arg(args, "--order")
    if order and order not in ("knowledge", "parliament"):
        print(f"--order must be 'knowledge' or 'parliament'", file=sys.stderr)
        sys.exit(1)

    if merge_only:
        log.info("Merge-only mode — skipping transcription")
    else:
        log.info(f"Preset: {preset_name}  model: {WHISPER_CONFIG['model_size']}  "
                 f"beam: {WHISPER_CONFIG['beam_size']}  device: {WHISPER_CONFIG['device']}")
    if order:
        log.info(f"Category order: {order}")

    run(event_filter=event_id, merge_only=merge_only, order=order)


if __name__ == "__main__":
    main()
