# PSP Video Archive

Downloads and tracks videos from the Czech Parliament video archive at
[videoarchiv.psp.cz](https://videoarchiv.psp.cz/).  The long-term goal is to
produce transcriptions of parliamentary events that are not already transcribed
by the parliament itself.

## Directory layout

```
videoarchive/
├── sync.py            # sync + download script (run by cron)
├── transcribe.py      # transcription + merge script
├── status_report.py   # generate human-readable status overview
├── setup_cron.sh      # installs the cron job
├── metadata.json      # single source of truth — shared by both scripts
├── videos/            # downloaded MP4 files (cache — may be deleted)
│   ├── video/         #   live-stream recordings (K48/, 106/, 107/, A108/, …)
│   └── vuploads/      #   uploaded recordings (press conferences, etc.)
├── subtitles/         # VTT caption files downloaded from the server
│   └── titulky/
├── transcriptions/    # per-segment Whisper JSON (permanent)
│   ├── video/
│   └── vuploads/
└── final/             # merged per-event Markdown transcripts (primary output)
```

`videos/` is a **cache**: files may be deleted to reclaim disk space once a
transcription exists.  `metadata.json`, `subtitles/`, `transcriptions/`, and
`final/` are the permanent record.

## Quick start

```bash
# First run — populates metadata.json, downloads nothing
python3 sync.py --dry-run

# Start downloading
python3 sync.py

# Install cron job (runs every 2 hours by default)
bash setup_cron.sh

# Check current state
python3 sync.py --status
```

No dependencies beyond the Python standard library.

## Status reporting (`status_report.py`)

Generate a human-readable overview of all events and their transcription progress:

```bash
# Display report on screen
python3 status_report.py

# Display on screen AND save to CSV
python3 status_report.py --csv status.csv

# Save to CSV only (no screen output)
python3 status_report.py --csv-only status.csv
```

The report shows for each event:
- Event ID, date, and current status
- Total number of video files
- Download and transcription progress (as percentages)
- Category and event name

Example output:
```
    ID  Date        Status        Files   Down  Trans  Category              Event Name
----------------------------------------------------------------------------------------------------
  2798  2026-04-02  transcribed       10  100%  100%  Kulatý stůl           Jak na spravedlivé a efektivní zdanění…
  2795  2026-04-01  downloaded        8   100%    0%  Tiskové konference    Tisková konference poslanců…
  2790  2026-03-28  partial           12   75%   25%  Seminář               Odborný seminář k novele…
  2785  2026-03-25  available         5     0%    0%  Veřejné slyšení       Veřejné slyšení výboru…
  2780  2026-03-20  planned           0    —     —     Konference            Konference o digitalizaci…

Summary by status:
  available   :  15 (25%)
  downloaded  :  12 (20%)
  partial     :  18 (30%)
  planned     :   5 ( 8%)
  transcribed :  10 (17%)
```

The CSV export includes all fields plus full event names and timestamps for further analysis in spreadsheet software.

## What is tracked

Only events that meet all of these criteria are included:

| Criterion | Value |
|-----------|-------|
| Date | `ts >= 2026-03-15` |
| Category | anything **except** `Jednání Poslanecké sněmovny` |

Parliament plenary sessions (`Jednání Poslanecké sněmovny`) are excluded
because official transcripts are already published by the parliament.

Categories currently tracked: `Tiskové konference`, `Kulatý stůl`, `Seminář`,
`Jednání výborů`, `Veřejné slyšení`, `Konference`, and others.

Future events (no recording yet) are tracked with status `planned` and
re-checked on every sync until videos appear.

## metadata.json schema

The file is written atomically (via a `.tmp` rename) and is safe to read
concurrently from other scripts.

```jsonc
{
  "version": 1,
  "cutoff_date": "2026-03-15",
  "last_sync": "2026-04-02T12:24:39",
  "events": {
    "<event_id>": {
      "id": "2798",
      "name": "Jak na spravedlivé a efektivní zdanění…",
      "category": "Kulatý stůl",
      "ts": "2026-04-02 10:31:40",   // recording start (null if not yet started)
      "tp": "2026-04-02 12:30:00",   // recording stop
      "total_start": "02.04.2026 10:31",
      "total_stop":  "02.04.2026 12:30",
      "deafst": "f",                 // "t" if event-level subtitles exist
      "subakce_count": "1",          // number of sub-events per the API
      "status": "available",         // see Status values below
      "last_checked": "2026-04-02T12:20:38",
      "subevents": {
        "<subevent_id>": {
          "id": "5169",
          "name": "",
          "deafs": "f",              // "t" if this sub-event has subtitles
          "start": "02.04.2026 10:31",
          "stop":  "02.04.2026 12:30",
          "isactive": "1",
          "files": [ /* see File record below */ ]
        }
      }
    }
  }
}
```

### File record

Each `~10-minute` MP4 segment is one file record:

```jsonc
{
  // ── Source ────────────────────────────────────────────────────────────
  "remote_path": "video/K48/2026/04/02/_20260402103009.mp4",
  "url":         "https://videoarchiv.psp.cz/video/K48/2026/04/02/_20260402103009.mp4",
  "from_sec": 91,   // seconds offset into the segment where content starts
  "to_sec":   0,    // seconds offset where content ends (0 = end of file)

  // ── Video cache ───────────────────────────────────────────────────────
  "local_path":    "videos/video/K48/2026/04/02/_20260402103009.mp4",
  "downloaded_at": "2026-04-02T13:00:00",  // null if not yet downloaded
  "size_bytes":    17277937,               // null if not yet downloaded

  // ── Captions (from the archive, VTT format) ───────────────────────────
  "captions_remote":       "titulky/5172_TK_KDU_20260402.vtt",  // null if none
  "captions_local":        "subtitles/titulky/5172_TK_KDU_20260402.vtt",
  "captions_downloaded_at": null,  // set when the VTT file is downloaded

  // ── Our transcription (written by the transcription script) ───────────
  "transcription_local":   "transcriptions/video/K48/2026/04/02/_20260402103009.json",
  "transcription_done_at": null   // set by the transcription script when done
}
```

### Status values

| Status | Meaning |
|--------|---------|
| `planned` | Event known, no video files available yet |
| `available` | Video files exist on server, none downloaded or transcribed |
| `partial` | Some files downloaded/transcribed, some still needed |
| `downloaded` | All files on disk, transcription not yet done |
| `transcribed` | All files have a transcription; video cache not required |

An event moves back from `downloaded` → `partial`/`available` if its cached
video files are deleted before transcription is complete.  Once an event
reaches `transcribed` it is never re-checked for new files.

## Transcription (`transcribe.py`)

### Quick start

```bash
# Activate the venv that has faster-whisper installed
source /home/michal/dev/psp/transcribe-cs/.venv/bin/activate

# Show what is ready to transcribe
python3 transcribe.py --status

# Transcribe everything and produce final/ Markdown files
python3 transcribe.py

# Process one specific event (replace 2798 with your event ID)
python3 transcribe.py --event 2798

# Use a different quality preset
python3 transcribe.py --preset medium --event 2798

# List all available presets
python3 transcribe.py --list-presets

# Re-merge final/ files without re-running Whisper
python3 transcribe.py --merge-only
```

### Available presets

| Preset | Backend | Model | Beam | Speed | Quality |
|--------|---------|-------|------|-------|---------|
| `small` | faster-whisper | small | 5 | Fastest | Quick smoke-test |
| `medium` | faster-whisper | medium | 5 | Fast | Good balance |
| `medium-best` | faster-whisper | medium | 10 | Medium | Better quality |
| `large-v2` | faster-whisper | large-v2 | 10 | Slow | High quality |
| `large-v3` | faster-whisper | large-v3 | 10 | Slow | **Default, best tested** |
| `groq-turbo` | Groq API | whisper-large-v3-turbo | — | Very fast | Fast cloud transcription |
| `groq-large-v3` | Groq API | whisper-large-v3 | — | Fast | Best cloud transcription |

**Groq backend:** Requires `GROQ_API_KEY` environment variable. Files > 25 MB are automatically downsampled to audio via ffmpeg.

```bash
# Using Groq API for fast cloud transcription
export GROQ_API_KEY=your_key_here
python3 transcribe.py --preset groq-turbo --event 2798
```

### Workflow

For each video file the script:

1. **Checks for existing captions** (`captions_downloaded_at` set and VTT on
   disk) — if present, parses the VTT directly instead of running Whisper.
2. **Runs faster-whisper** on the MP4 otherwise.
3. **Saves a per-segment JSON** to `f["transcription_local"]` and sets
   `f["transcription_done_at"]` in `metadata.json`.
4. After all files of an event have a transcription, **merges them** into a
   single Markdown file under `final/`.

`sync.py` reads `transcription_done_at` to decide whether to re-download a
deleted video — it won't if the transcription already exists.

### Configuration

All settings live at the top of `transcribe.py`:

```python
WHISPER_CONFIG = {
    "model_size":  "large-v3",   # best tested; change to "medium" for speed
    "device":      "cpu",        # "cuda" for GPU (needs float16 compute_type)
    "compute_type": "int8",
    "cpu_threads": 8,
    # Transcription quality settings (from 06_large_v3_best in compare_advanced.py)
    "beam_size":                   10,
    "vad_filter":                  True,
    "temperature":                 0.0,
    "condition_on_previous_text":  False,
    "compression_ratio_threshold": 2.2,
    "log_prob_threshold":          -0.8,
    "no_speech_threshold":         0.5,
}
```

The `initial_prompt` is generated automatically from the event category and
name using `CATEGORY_PROMPTS` (also at the top of the script):

| Category | Prompt context |
|----------|---------------|
| Kulatý stůl | kulatý stůl v Poslanecké sněmovně |
| Tiskové konference | tisková konference poslanců … |
| Seminář | odborný seminář v Poslanecké sněmovně |
| Veřejné slyšení | veřejné slyšení výboru … |
| Jednání výborů | jednání výboru Poslanecké sněmovny |
| *(default)* | jednání v Poslanecké sněmovně |

### Output format

#### Per-segment JSON (`transcriptions/**/*.json`)

Written for every ~10-minute video file.  Contains full Whisper metadata and
all segments with timestamps:

```jsonc
{
  "source": "whisper",           // or "captions" if from VTT
  "transcribed_at": "2026-04-02T15:00:00",
  "model": "large-v3",
  "initial_prompt": "Toto je záznam …",
  "language": "cs",
  "language_probability": 0.999,
  "duration_sec": 598.4,
  "processing_time_sec": 1820.3,
  "num_segments": 47,
  "segments": [
    { "start": 1.5, "end": 4.2, "text": "Vítám vás na dnešním semináři." },
    { "start": 4.2, "end": 8.1, "text": "Dnes budeme diskutovat o …" }
  ]
}
```

Timestamps are **relative to the start of that MP4 file**.  The `from_sec`
field in the file record (in `metadata.json`) gives the offset within the file
where actual content begins.

#### Merged Markdown (`final/event_<id>_<date>_<slug>.md`)

One file per event, combining all segments.  Designed for both LLM processing
(summaries, Q&A) and human review.

```markdown
# Jak na spravedlivé a efektivní zdanění příjmů nízkopříjmových poplatníků?

| Pole | Hodnota |
|------|---------|
| Kategorie | Kulatý stůl |
| Datum | 2026-04-02 |
| Čas | 02.04.2026 10:31 – 02.04.2026 12:30 |
| ID | 2798 |
| Části | 10/10 přepsáno |

> *Přepis byl vytvořen automaticky modelem faster-whisper `large-v3`. …*

---

### Část 1/10 — `_20260402103009.mp4`
*Zdroj: Whisper `large-v3`, od `01:31` v souboru*

Vítám vás na dnešním kulatém stole. Dnes se budeme zabývat otázkou
spravedlivého zdanění...

`[02:00]` Podívejme se nejprve na základní principy...

---

### Část 2/10 — `_20260402104009.mp4`
…
```

**Quote verification:** find the part number and nearest `[MM:SS]` marker
before the quote.  Open the corresponding JSON in `transcriptions/` and search
for segments near that timestamp for the exact start/end seconds.

`MARKER_INTERVAL_SEC = 120` (top of `transcribe.py`) controls how often inline
time markers are injected.

### Speaker identification

Not yet implemented — left for a future step.  The segment JSON is the right
place to add a `speaker` field once diarisation is added.

## API notes

The archive API lives at `https://videoarchiv.psp.cz/`.  Relevant endpoints:

| Endpoint | Purpose |
|----------|---------|
| `akce_data.php` | Returns all events as JSON (offset/limit params are ignored — always returns everything) |
| `subakce_data.php?Id=<id>` | Sub-events for one event |
| `subfiles.php?subakce=<id>` | Video file list for one sub-event |
| `video/<path>.mp4` | Direct MP4 download (supports HTTP Range) |
| `vuploads/<file>.mp4` | Uploaded MP4 download |
| `titulky/<file>.vtt` | VTT caption file |

The API can be slow and occasionally times out; `sync.py` retries up to 3
times with exponential back-off (5 s, 10 s).
