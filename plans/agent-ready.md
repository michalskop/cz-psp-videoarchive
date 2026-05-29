# Agent-Ready Implementation Plan

Reference: https://www.pinmeto.com/glossary/agent-ready-website/  
Check: https://isitagentready.com/

**Canonical URL:** `https://snemovna.datatimes.cz/digest`  
(GitHub Pages during testing — see `plans/deployment.md`. Agent-facing files always use the production URL as canonical.)

Goal: make the Sněmovna Digest fully discoverable and usable by AI agents — from auto-discovery through structured data to (eventually) a live MCP server.

---

## Layer 1 — Discovery (static, deploy with the site)

These files go in `web/public/` and are served at the root domain.

### ✅ `/.well-known/mcp-server-card.json`
Auto-discovery card per SEP-2127. Already created at `web/public/.well-known/mcp-server-card.json`.  
Update `site_url` and `data_url` when the real domain is known.  
`mcp_url` is `null` until a live MCP server exists (Phase 4 below).

### ✅ `/llms.txt`
Structured cheat sheet for answer engines. Already created at `web/public/llms.txt`.  
Keep in sync with actual routes and data format as the site evolves.

### ✅ `/robots.txt`
Explicitly allows: GPTBot, OAI-SearchBot, PerplexityBot, ClaudeBot, anthropic-ai.  
Already created at `web/public/robots.txt`.

### ✅ `/SKILL.md`
Full capability and data format reference for agents. Already created at repo root `SKILL.md`.  
Copy or symlink to `web/public/SKILL.md` so it's served at the root URL.

### `/sitemap.xml`
Generated at Next.js build time from all `summaries/json/*.json` files.  
Include: `/events/[id]`, `/speakers/[id]`, `/events`, `/speakers`.  
Add `<lastmod>` from `summary.created_at`.

---

## Layer 2 — Structured Data / JSON-LD (per page)

Add `<script type="application/ld+json">` blocks to every page. This is how AI search engines classify pages as structured data sources rather than blog posts.

### Homepage (`/`)
```json
{
  "@context": "https://schema.org",
  "@type": ["WebSite", "Dataset"],
  "name": "Sněmovna Digest",
  "description": "AI-structured summaries of Czech Parliament events — seminars, conferences, committee meetings.",
  "url": "https://snemovna.datatimes.cz/digest",
  "inLanguage": "cs",
  "creator": { "@type": "Organization", "name": "DataTimes / Mahdalová & Škop" },
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "temporalCoverage": "2026/..",
  "about": { "@type": "GovernmentOrganization", "name": "Poslanecká sněmovna Parlamentu ČR" }
}
```

### Event detail page (`/events/[id]`)
```json
{
  "@context": "https://schema.org",
  "@type": ["Event", "Article"],
  "name": "<event.name>",
  "startDate": "<event.start_date>",
  "eventStatus": "https://schema.org/EventScheduled",
  "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
  "location": {
    "@type": "Place",
    "name": "Poslanecká sněmovna Parlamentu ČR",
    "address": { "@type": "PostalAddress", "addressLocality": "Praha", "addressCountry": "CZ" }
  },
  "organizer": { "@type": "GovernmentOrganization", "name": "Poslanecká sněmovna" },
  "description": "<summary.topic — first 200 chars>",
  "about": "<event.classification>",
  "performer": [ { "@type": "Person", "name": "<speaker.name>" } ],
  "recordedIn": { "@type": "VideoObject", "name": "<event.name> — záznam", "url": "<psp.cz source>" },
  "isBasedOn": { "@type": "URL", "url": "<event.sources[0]>" }
}
```

### Speaker page (`/speakers/[id]`)
```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "<speaker.name>",
  "identifier": "<person_id>",
  "memberOf": { "@type": "GovernmentOrganization", "name": "<affiliation>" },
  "url": "https://www.psp.cz/sqw/detail.sqw?id=<NNN>"
}
```

### Event list (`/events`)
```json
{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "Archiv akcí PSP",
  "description": "Přehled všech zaznamenaných a shrnutých akcí Poslanecké sněmovny",
  "url": "https://snemovna.datatimes.cz/digest/events"
}
```

---

## Layer 3 — Semantic HTML (GEO — Generative Engine Optimization)

These are writing/rendering conventions that make AI search engines "clip" the right content:

- **H2 headings that answer questions directly**  
  Instead of "Hlavní body" use "Co bylo řečeno na semináři [název]"  
  Pattern: `<h2>Výsledek jednání výboru pro [téma], [datum]</h2>`

- **Structured speaker tables**  
  Render `summary.main_points` as a 2-column table (Speaker | Key points) where there are ≥ 4 speakers. AI search engines clip tables reliably.

- **Highlight cards with visible text**  
  Quote text must be in visible HTML (not only in image). `highlights[].text` must be in a `<blockquote>` or `<p>` — not only in the screenshot.

- **Controversy markers**  
  Wrap each `controversial[]` item in a `<section aria-label="Kontroverzní výrok">` so AI parsers classify it correctly.

- **Timestamps as accessible links**  
  Render `1/04:23` as a link to the PSP recording with the `t=` parameter where possible.

---

## Layer 4 — Static API endpoints

Build-time generated JSON files that agents can fetch directly without scraping HTML.

| File | Content | Generated by |
|------|---------|-------------|
| `/api/events.json` | Array of all events: id, name, date, category, quality, summary_available | Next.js build |
| `/api/speakers.json` | Array of all speakers: name, person_id, affiliation, event_count, event_ids | Next.js build |
| `/api/events-by-category.json` | Events grouped by classification | Next.js build |
| `/summaries/[id].json` | Full summary JSON (copy of `summaries/json/` files) | Next.js build or static copy |

These are plain static files — no server needed. Agents can `GET /api/events.json` and get machine-readable data immediately.

---

## Layer 5 — MCP Server (future, needs Vercel or Cloudflare Workers)

A live Model Context Protocol server at `/mcp` that exposes tools agents can call directly.

**Tools to expose:**

| Tool | Input | Output |
|------|-------|--------|
| `list_events` | `category?`, `date_from?`, `date_to?`, `limit?` | Array of event stubs |
| `get_event_summary` | `id` | Full summary JSON |
| `get_highlights` | `id` | highlights[] array with screenshot URLs |
| `get_controversies` | `id` | controversial[] array with fact-check context |
| `search_events` | `query` (Czech text) | Ranked event stubs (Pagefind or embedding search) |
| `list_speakers` | `affiliation?` | Speaker index |
| `get_speaker_events` | `person_id` | All events for this speaker |

**Implementation options:**
- Vercel Edge Functions (free tier, zero cold-start)
- Cloudflare Workers
- Use the `@modelcontextprotocol/sdk` TypeScript package

When live: update `mcp_url` in `/.well-known/mcp-server-card.json`.

**Submit to directories once live:**
- https://glama.ai (MCP server directory)
- https://mcp-get.com

---

## Layer 6 — Validation & submission

- [ ] Run https://isitagentready.com/ against the deployed URL
- [ ] Validate JSON-LD: https://validator.schema.org/
- [ ] Test `llms.txt` is reachable and parses correctly
- [ ] Test `.well-known/mcp-server-card.json` returns valid JSON with correct Content-Type
- [ ] Submit sitemap to Google Search Console
- [ ] Submit sitemap to Bing Webmaster Tools
- [ ] Submit MCP URL to Glama.ai (Phase 5)

---

## Implementation order

1. **With Phase 1 (MVP site launch):** Layers 1–3 — discovery files, JSON-LD, semantic HTML
2. **With Phase 2 (speaker index):** Layer 4 — static API JSON endpoints  
3. **With Phase 3 (search):** Layer 5 (MCP search tool, requires Vercel)
4. **Ongoing:** Layer 6 validation after each deploy
