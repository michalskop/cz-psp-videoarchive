# Agent-Ready Implementation Plan

Reference: https://www.pinmeto.com/glossary/agent-ready-website/  
Check: https://isitagentready.com/

**Canonical URL:** `https://snemovna.datatimes.cz/digest`  
(GitHub Pages during testing — see `plans/deployment.md`. Agent-facing files always use the production URL as canonical.)

Goal: make the Sněmovna Digest fully discoverable and usable by AI agents — from auto-discovery through structured data to (eventually) a live MCP server.

---

## Layer 1 — Discovery (static, deploy with the site)

Root-domain files (`snemovna.datatimes.cz/...`) live in `legislature-dashboard/apps/cz-psp/public/`.  
Digest-scoped files (`snemovna.datatimes.cz/digest/...`) live in `web/public/`.  
See `web/public/.well-known/README.md` and `legislature-dashboard/apps/cz-psp/public/.well-known/README.md` for ownership map.

### ✅ `/.well-known/mcp/server-card.json`
MCP Server Card per SEP-1649 (new canonical path). Lives in `legislature-dashboard/apps/cz-psp/public/.well-known/mcp/server-card.json`.  
Uses `serverInfo.name` nested format required by SEP-1649 checker.  
`transport: null` until a live MCP server exists (Layer 5 below).  
Old path `/.well-known/mcp-server-card.json` kept at `/digest/.well-known/mcp-server-card.json` for backward compat.

### ✅ `/.well-known/api-catalog`
RFC 9727 API catalog. Lives in `legislature-dashboard/apps/cz-psp/public/.well-known/api-catalog`.  
References digest's `summary.schema.json`, `llms.txt`, and planned `/api/events.json`.

### ✅ `/llms.txt`
Structured cheat sheet for answer engines. `web/public/llms.txt` → served at `/digest/llms.txt`.  
Keep in sync with actual routes and data format as the site evolves.

### ✅ `/robots.txt`
Explicitly allows: GPTBot, OAI-SearchBot, PerplexityBot, ClaudeBot, anthropic-ai.  
`web/public/robots.txt` — references `/digest/sitemap.xml`.

### ✅ `/SKILL.md`
Full capability and data format reference for agents. `web/public/SKILL.md` → served at `/digest/SKILL.md`.

### ✅ `/sitemap.xml`
`web/app/sitemap.ts` — generated at build time from all summary JSONs.  
Covers homepage, `/events`, and all `/events/[id]` pages with `<lastmod>` from `created_at`.  
Served at `/digest/sitemap.xml`, referenced in `robots.txt`.

### ✅ `/auth.md`
Explicit "no authentication required" declaration for AI agents.  
Lives in `legislature-dashboard/apps/cz-psp/public/auth.md` → served at root `snemovna.datatimes.cz/auth.md`.  
States all digest endpoints are publicly accessible; no API key or registration needed.

---

## Layer 2 — Structured Data / JSON-LD (per page) ✅

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

## Layer 6 — WebMCP (browser-embedded agent tools) ✅

Exposes site tools to browser-embedded AI agents via `navigator.modelContext.provideContext()` (Chrome experimental, WebMCP spec).

Component: `web/app/components/WebMCP.tsx` — loaded in `web/app/layout.tsx` (all pages).  
Graceful no-op if API unavailable.

### Tools exposed

| Tool | Input | Output |
|------|-------|--------|
| `list_events` | `category?`, `limit?` | Array of event stubs from `/digest/api/events.json` |
| `get_event_summary` | `id` | JSON-LD structured data extracted from event page |

### Static API required
`web/app/api/events.json/route.ts` — generated at build time.  
Returns: `[{ id, name, date, category, quality, topic, highlights, controversies, url }]`  
Served at `/digest/api/events.json`.

---

## Layer 7 — Validation & submission

- [x] Run https://isitagentready.com/ — **64%** (2026-05-31, up from 50%)
- [ ] Validate JSON-LD: https://validator.schema.org/
- [x] Test `llms.txt` reachable ✅
- [x] Test `.well-known/mcp/server-card.json` valid JSON ✅
- [ ] Submit sitemap to Google Search Console
- [ ] Submit sitemap to Bing Webmaster Tools
- [ ] Submit MCP URL to Glama.ai (Layer 5)

### Remaining isitagentready.com gaps (64% → ?)
- **DNS-AID** — blocked: DNS provider doesn't support HTTPS/SVCB record types ⬜
- **OAuth/OIDC, auth.md** — not applicable (fully public read-only site) ✅ handled by `/auth.md`
- **WebMCP** — implemented ✅

---

## Implementation order

1. **With Phase 1 (MVP site launch):** Layers 1–3 — discovery files, JSON-LD, semantic HTML ✅
2. **With Phase 2 (speaker index):** Layer 4 — static API JSON endpoints (partially done: `/api/events.json`)
3. **With Phase 3 (search):** Layer 5 (MCP search tool, requires Vercel)
4. **Ongoing:** Layer 7 validation after each deploy
