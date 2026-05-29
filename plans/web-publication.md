# Web Publication Plan — PSP Video Archive

**Goal:** Public-facing site for browsing structured summaries of Czech Parliament (PSP) events — seminars, conferences, committee meetings, round tables. Audience: journalists, researchers, general public.

**Stack:** Next.js (static export) — this repo (`web/`), separate from the datatimes turborepo.  
**Design:** DataTimes / Mahdalová & Škop — `DESIGN.md` in this repo.  
**Data source:** `summaries/json/*.json` (schema v2) committed to git; screenshots served from Backblaze B2 bucket `cz-psp-videoarchive`.  
**Production URL:** `snemovna.datatimes.cz/videoarchiv` (via Vercel rewrite on the snemovna project).  
**Testing URL:** GitHub Pages (temporary, for development validation before production wiring).

---

## Phase 0 — Infrastructure (before first commit)

- [ ] **B2 upload script** (`upload_screenshots.py`): upload all `summaries/screenshots/*.jpg` to B2, rewrite `screenshot_path` in the summary JSONs to the public B2 URL, add `summaries/screenshots/` to `.gitignore`.
- [ ] **`.gitignore` finalised**: confirm `summaries/screenshots/` excluded; `summaries/json/`, `summaries/md/` tracked.
- [ ] **`summary.schema.json` committed**: the schema is the contract between pipeline and web app.
- [ ] **Next.js app scaffold**: `npx create-next-app@latest web --typescript --tailwind --app` inside this repo root. App lives in `web/`, data pipeline stays at root. See `plans/deployment.md` for GitHub Pages → Vercel migration path.

---

## Phase 1 — Event list + summary detail (MVP)

**What ships:** a browsable, searchable list of events with full summary pages.

### Pages

| Route | Content |
|-------|---------|
| `/` | Homepage: intro + recent events (last 10), search bar |
| `/events` | Full paginated/filterable event list |
| `/events/[id]` | Full summary detail page |
| `/speakers/[id]` | Speaker page (all events they appeared in) — Phase 2 |

### Event list (`/events`)
- Cards showing: date, category badge (Seminář / Konference / …), event name, 1-sentence topic excerpt.
- Filter by: category, date range.
- Sort by: date (default), category.
- Category badge colours mapped from DataTimes palette (crimson for Seminář, navy for Jednání výborů, etc.).

### Summary detail (`/events/[id]`)
Sections in order:
1. **Header** — event name, date, category badge, transcription quality indicator.
2. **Téma** — `summary.topic` as a lead paragraph.
3. **Hlavní body** — `summary.main_points` as a structured speaker-by-speaker list.
4. **Highlights** — `highlights[]` cards: screenshot (from B2) + quote/paraphrase + speaker + timestamp link. Type badge: `citace` / `parafráze`.
5. **Kontroverzní body** — `controversial[]`: statement + fact-check context (`context` field) + speaker + timestamp. InfoBox `warning` style for controversial, `info` for fact-check context.
6. **Výsledek** — `summary.outcome`.
7. **Poznámky** — `summary.notes` if non-null (transcript quality caveats), InfoBox `warning`.
8. **Řečníci** — `entities.speakers` chips, linked to speaker pages (Phase 2).

### Data layer
- At build time: `getStaticPaths` + `getStaticProps` (or `generateStaticParams` in App Router) reads all `summaries/json/*.json`.
- Single `lib/summaries.ts` with typed loader — no runtime API needed for Phase 1.
- Types auto-derived from `summary.schema.json` (use `json-schema-to-typescript` or write manually).

---

## Phase 2 — Speaker index

- `/speakers` — list of all identified speakers, sorted by appearance count.
- `/speakers/[person_id]` — all events a speaker appeared in, with their `main_points` excerpts.
- Requires: aggregate across all summary JSONs at build time.
- Note: `person_id` is `psp:person:NNN` (Popolo format) — can link to external PSP profile later.

---

## Phase 3 — Search

- Client-side full-text search using [Pagefind](https://pagefind.app/) (runs on static export, no server needed) or [Fuse.js](https://fusejs.io/) for in-memory fuzzy search.
- Index: event name + topic + main_points + speaker names.
- Pagefind preferred: generates its own index at build time, handles Czech diacritics.

---

## Phase 4 — Social card export

- On each highlight card: "Sdílet" button generates a shareable image (screenshot + quote overlay).
- Implementation options: pre-generate PNGs in pipeline (`summarize.py` + Pillow) or client-side canvas/`html2canvas`.
- The `illustration.md` prompt + B2 screenshot is the visual input; HTML/CSS card layer is the output.

---

## Open questions

- **Monorepo vs. separate repo?** Keeping `web/` inside this repo is simpler for data access at build time; separate repo is cleaner for CI/CD.
- **Vercel timing?** GitHub Pages works for Phase 1–2. Move to Vercel when Phase 3 needs build-time Pagefind indexing or Phase 4 needs an API route.
- **Screenshot `screenshot_path` field:** after B2 upload this becomes a full URL. Web app reads it directly — no mapping needed.
- **Summaries without highlights:** older summaries (pre-schema-v2) have no `highlights` array. Web app should handle gracefully (skip section if empty).
- **Language:** site in Czech throughout. Category names, UI labels, dates — all Czech.
