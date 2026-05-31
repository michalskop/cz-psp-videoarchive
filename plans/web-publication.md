# Web Publication Plan — Sněmovna Digest

**Goal:** Public-facing site for browsing structured summaries of Czech Parliament (PSP) events — seminars, conferences, committee meetings, round tables. Audience: journalists, researchers, general public.

**Stack:** Next.js 16 (static export) — `web/`, separate from the datatimes turborepo.  
**Design:** DataTimes / Mahdalová & Škop — `DESIGN.md` in this repo; full color/component reference in `legislature-dashboard/docs/design.md`.  
**Data source:** `summaries/json/*.json` (schema v2) committed to git; screenshots on Backblaze B2 `cz-psp-videoarchive`.  
**Production URL:** `snemovna.datatimes.cz/digest` ✅ live (Vercel, proxied via legislature-dashboard)  
**Testing URL:** GitHub Pages — `https://michalskop.github.io/cz-psp-videoarchive/` ✅ live  
**Deploy:** prebuilt Vercel deploy from pipeline machine; auto-triggered by `pipeline.sh` — see `plans/deployment.md`.

---

## Phase 0 — Infrastructure ✅ DONE

- [x] B2 upload script (`upload_screenshots.py`) + CORS configured (`set_b2_cors.py`)
- [x] `.gitignore`: `summaries/screenshots/` excluded; `summaries/json/`, `summaries/md/` tracked
- [x] `summary.schema.json` committed — schema contract between pipeline and web app
- [x] Next.js scaffold: TypeScript, Tailwind v4, App Router, `output: "export"`
- [x] Vercel project created, linked, SSO disabled, rootDirectory=null (see `plans/deployment.md`)

---

## Phase 1 — Event list + summary detail ✅ DONE

### Pages

| Route | Content | Status |
|-------|---------|--------|
| `/` | Homepage: recent events + CTA | ✅ |
| `/events` | Full filterable event list | ✅ |
| `/events/[id]` | Full summary detail page | ✅ |
| `/speakers/[id]` | Speaker page | ⬜ Phase 2 |

### Event list (`/events`)
- [x] Cards: date, category badge, event name, topic excerpt, thumbnail
- [x] Toggle-off category filter (all active by default, click to deactivate)
- [ ] Filter by date range
- [ ] Sort controls (default: date desc)
- [ ] Month grouping (needed once list exceeds ~100 events — see backlog)

### Summary detail (`/events/[id]`)
1. [x] Header — name, date, category badge, quality badge, citace/kontroverze counts
2. [x] Téma — `summary.topic`
3. [x] Hlavní body — `summary.main_points` with bold markdown + video deep-links
4. [x] Výsledek — `summary.outcome`
5. [x] Výrazné momenty — `highlights[]` as `HighlightCard` social cards + video links + context
6. [x] Kontroverzní výroky — `controversial[]` as `ControversyCard` + video links + context
7. [x] Poznámky k přepisu — `summary.notes` in orange InfoBox if non-null
8. [x] Footer — event id, transcription ratio, model, created date
9. [ ] Řečníci linked to speaker pages (chips rendered, links pending Phase 2)

### Design & components
- [x] DataTimes palette as Tailwind v4 `@theme` tokens (`globals.css`)
- [x] `rounded-badge` shape: all corners rounded except top-right (plain CSS, not `@utility`)
- [x] Hover shadow elevation on all cards (`hover:shadow-md`)
- [x] Fonts: Roboto Slab + Work Sans (Google Fonts)
- [x] `PspLogotype`, `SiteHeader` (sticky), `SiteFooter` (4-column)
- [x] `CategoryBadge`, `QualityBadge`
- [x] `HighlightCard` — crimson strip, screenshot, blockquote, logotype
- [x] `ControversyCard` — orange strip, parsed bullet layout
- [x] `ShareableCard` — html2canvas PNG copy/download wrapper (see Phase 4)
- [x] `VideoLink` — PSP video deep-link button with `#t=` seek parameter

### SEO / metadata
- [x] `layout.tsx` — `metadataBase`, OG, Twitter card
- [x] `generateMetadata` per event page
- [x] Favicon (`app/icon.svg`) — crimson→navy badge with "S" in yellow
- [x] Root OG image (`app/opengraph-image.tsx`, 1200×630)
- [x] Per-event OG image (`app/events/[id]/opengraph-image.tsx`)
- [x] JSON-LD structured data on all pages (see `plans/agent-ready.md` Layer 2)

### Analytics
- [x] Matomo JS (`MatomoScript`) + noscript pixel (`MatomoNoscript`)
- [x] SPA route change support via `usePathname`
- [x] Config: `{ url: "//matomo.kohovolit.eu/", siteId: "2" }`
- **Bot/AI tracking:** Vercel logs all HTTP requests server-side. Use Matomo Log Analytics against Vercel access logs to track GPTBot, ClaudeBot, PerplexityBot etc. by user-agent string. *(Not yet configured — low priority)*

---

## Phase 2 — Speaker index ⬜

- [ ] `/speakers` — all identified speakers sorted by appearance count
- [ ] `/speakers/[person_id]` — events a speaker appeared in, with their excerpts
- Requires: build-time aggregation across all summary JSONs
- `person_id` is `psp:person:NNN` (Popolo format) — can link to PSP profile later
- Unblocks: speaker chip links on event detail pages

---

## Phase 3 — Search ⬜

- [ ] Client-side full-text search via [Pagefind](https://pagefind.app/) (preferred — handles Czech diacritics, build-time index) or Fuse.js
- Index: event name + topic + main_points + speaker names
- Enables: `search_events` MCP tool (see `plans/agent-ready.md` Layer 5)

---

## Phase 4 — Social card export ✅ DONE

- [x] `HighlightCard` and `ControversyCard` styled as social-ready cards
- [x] `ShareableCard` wrapper: copy-to-clipboard PNG + download PNG via `html2canvas`
- [x] B2 CORS configured (`set_b2_cors.py`) — required for html2canvas to capture remote images
- [x] `w-fit self-start` on capture div — prevents transparent right-side strip
- [x] `leading-none` on badge text — fixes text sitting low within badge padding

---

## Phase 5 — Social network publishing ⬜ (semi-automatic)

Goal: share highlights/controversies to Bluesky and X with one-click approval.

| Option | Effort | Control |
|--------|--------|---------|
| Manual: copy card + draft from site | Zero | Full |
| Pipeline hook → approval queue | Medium | Full |
| Zapier/Make on git push | Low | Limited |

**Platforms:** Bluesky (`@atproto/api`) + X v2 API. Post from `@datatimes_cz`.  
**Prerequisites:** Bluesky app password, X API key with write access, approval UI.

---

## Phase 1 backlog

### Pagination by month
- Needed when list exceeds ~200 events
- **Approach A** (recommended first): month groups in `EventsList.tsx`, accordion/collapse, JS show/hide, category filter works across months
- **Approach B** (later): static routes `/events/2026-05`, `/events/2026-04` — separate pages per month

### Party affiliation badges on speaker chips
- `sp.affiliation` already in JSON; map → party slug → `partyface` icon set
- Apply on: event detail chips, `HighlightCard`, `ControversyCard`, Phase 2 speaker pages

### Cross-links to snemovna.datatimes.cz
- Speaker chips → `snemovna.datatimes.cz/osoby/[person_id]`
- Footer "Více dat o sněmovně" CTA

### Link to original PSP video (event-level)
- URL pattern: `https://www.psp.cz/eknih/[term]/video/[video_id]`
- Requires mapping event id → PSP video id (add field to pipeline output)
- Timestamp deep-links (`#t=secs`) already implemented for parts with known URLs
