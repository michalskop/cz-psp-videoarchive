# PSP Video Archive — Agent Skill

This site provides AI-structured summaries of public Czech Parliament (PSP) events: seminars, conferences, round tables, committee meetings, and press conferences. All data is derived from official PSP recordings and transcripts.

## What this site offers

- **Event summaries** — topic, main points by speaker, outcome, quality notes
- **Highlights** — 3–5 key statements per event (direct citations or paraphrases), each with a video screenshot and timestamp
- **Controversies** — flagged controversial statements with fact-check context and timestamps
- **Speaker index** — all identified speakers with Popolo-compatible person IDs (`psp:person:NNN`)
- **Entity index** — political parties and institutions mentioned

## Data endpoints (static JSON)

All data is available as static JSON files committed to the repository and served as-is.

| Endpoint | Description |
|----------|-------------|
| `/summaries/[id].json` | Full structured summary for one event (schema v2) |
| `/api/events.json` | Index of all events: id, name, date, category, summary status |
| `/api/speakers.json` | Speaker index: name, person_id, event count, affiliation |

## Summary JSON structure (schema v2)

```json
{
  "schema_version": "2",
  "event": {
    "id": "2866",
    "name": "Strategická surovina - české uhlí",
    "classification": "Seminář",
    "start_date": "2026-05-04T10:07"
  },
  "summary": {
    "topic": "...",
    "main_points": ["**Jméno (instituce)** — ..."],
    "outcome": "...",
    "notes": null
  },
  "highlights": [
    {
      "text": "...",
      "type": "citation|paraphrase",
      "speaker": "...",
      "affiliation": "...",
      "timestamp": "1/04:23",
      "screenshot_path": "https://...",
      "context": "Fact-check note..."
    }
  ],
  "controversial": [
    {
      "statement": "...",
      "speaker": "...",
      "timestamp": "2/11:05",
      "context": "Fact-check note..."
    }
  ],
  "entities": {
    "speakers": [{"name": "...", "person_id": "psp:person:123", "affiliation": "..."}],
    "parties": ["ODS", "ANO"],
    "institutions": ["Ministerstvo průmyslu a obchodu"]
  },
  "quality": {
    "transcript_quality": "good|partial|poor",
    "unintelligible_parts": false
  }
}
```

## Timestamp format

Timestamps use format `N/MM:SS` — part number / time within that video file.  
Example: `3/04:23` = part 3 of the event recording, at 4 minutes 23 seconds.

## Event categories

Czech parliamentary event types used in `classification`:
- `Seminář` — expert seminar
- `Konference` — conference
- `Kulatý stůl` — round table
- `Veřejné slyšení` — public hearing
- `Tiskové konference` — press conference
- `Jednání výborů` — committee meeting

## Typical agent use cases

- "What was discussed at the seminar on Czech coal on 4 May 2026?" → fetch `/summaries/2866.json`, read `summary.topic` and `summary.main_points`
- "What controversial things were said?" → read `controversial[]` with `context` fact-check annotation
- "Who spoke and what did they say?" → read `entities.speakers` and `summary.main_points`
- "Find events where [person] spoke" → filter `/api/speakers.json` by name, then fetch their events
- "Show me the key quote from event 2866" → read `highlights[0].text` and `highlights[0].screenshot_path`

## Language

All summary content is in Czech. Event names, speaker names, and party affiliations are in Czech.

## Coverage

Events from the Czech Parliament (Poslanecká sněmovna) recorded and published on the PSP website. Coverage begins 2026 and grows continuously. Not all events are transcribed or summarised — check `transcription.parts_transcribed` vs `transcription.parts_total` for completeness.

## Source

Original recordings: `www.psp.cz`. Transcription: Whisper / Groq. Summarisation: Gemini / Llama via structured prompt. This data is derivative — always verify important claims against the original PSP recording.
