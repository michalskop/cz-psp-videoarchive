# Web Publication Plan — Sněmovna Digest

**Goal:** Public-facing site for browsing structured summaries of Czech Parliament (PSP) events — seminars, conferences, committee meetings, round tables. Audience: journalists, researchers, general public.

**Stack:** Next.js (static export) — this repo (`web/`), separate from the datatimes turborepo.  
**Design:** DataTimes / Mahdalová & Škop — `DESIGN.md` in this repo.  
**Data source:** `summaries/json/*.json` (schema v2) committed to git; screenshots served from Backblaze B2 bucket `cz-psp-videoarchive`.  
**Production URL:** `snemovna.datatimes.cz/digest` (via Vercel rewrite on the snemovna project).  
**Testing URL:** GitHub Pages — `https://michalskop.github.io/cz-psp-videoarchive/` ✅ live

---

## Phase 0 — Infrastructure (before first commit)

- [x] **B2 upload script** (`upload_screenshots.py`): upload all `summaries/screenshots/*.jpg` to B2, rewrite `screenshot_path` in the summary JSONs to the public B2 URL, add `summaries/screenshots/` to `.gitignore`.
- [x] **`.gitignore` finalised**: `summaries/screenshots/` excluded (fixed inline-comment bug); `summaries/json/`, `summaries/md/` tracked.
- [x] **`summary.schema.json` committed**: schema is the contract between pipeline and web app.
- [x] **Next.js app scaffold**: `web/` with TypeScript, Tailwind v4, App Router, `output: "export"`.

---

## Phase 1 — Event list + summary detail (MVP)

**What ships:** a browsable, filterable list of events with full summary pages.

### Pages

| Route | Content | Status |
|-------|---------|--------|
| `/` | Redirects to `/events` | ✅ done |
| `/events` | Full filterable event list | ✅ done |
| `/events/[id]` | Full summary detail page | ✅ done |
| `/speakers/[id]` | Speaker page — Phase 2 | ⬜ |

### Event list (`/events`)
- [x] Cards: date (Czech format `28. 5. 2026`), category badge, event name, topic excerpt
- [x] Thumbnail from first highlight screenshot
- [x] Filter by category (buttons with counts)
- [x] Category badge colours from DataTimes palette
- [ ] Filter by date range
- [ ] Sort controls (currently default: date desc)

### Summary detail (`/events/[id]`)
Sections in order:
1. [x] **Header** — event name, date, category badge, quality badge, citace/kontroverze counts
2. [x] **Téma** — `summary.topic`
3. [x] **Hlavní body** — `summary.main_points` with `**bold**` markdown rendered
4. [x] **Výsledek** — `summary.outcome`
5. [x] **Výrazné momenty** — `highlights[]` as social-shareable cards (screenshot, quote, speaker, PspLogotype, context block below card)
6. [x] **Kontroverzní výroky** — `controversial[]` as orange-themed cards (parseStatement strips `**Čas:**` line; context block below)
7. [x] **Poznámky k přepisu** — `summary.notes` in orange InfoBox if non-null
8. [x] **Footer** — event id, transcription ratio, model, created date
9. [ ] **Řečníci** linked to speaker pages (chips rendered, links pending Phase 2)

### Design & components
- [x] DataTimes palette as Tailwind v4 `@theme` tokens (`globals.css`)
- [x] Fonts: Roboto Slab + Work Sans via Google Fonts
- [x] `PspLogotype` universal component (`Sněmovna.DataTimes.cz/digest`)
- [x] `SiteHeader` sticky, `SiteFooter` 4-column
- [x] `CategoryBadge`, `QualityBadge`
- [x] `HighlightCard` — social card with crimson strip, screenshot, quote, logotype
- [x] `ControversyCard` — social card with orange strip, parsed bullet layout

### Data layer
- [x] `lib/summaries.ts` (server-only, uses `fs`) — typed loader, `getAllSummaries`, `getSummaryById`, `getAllIds`
- [x] `lib/types.ts` (client-safe) — pure types + helpers (`formatDate`, `firstThumbnail`, `pluralCitace`, `pluralKontroverze`)
- [x] `EventsList.tsx` is `"use client"` and imports from `lib/types`, not `lib/summaries`

### SEO / metadata
- [x] `layout.tsx` — full `Metadata` with `metadataBase`, OG, Twitter card
- [x] `generateMetadata` per event page
- [x] Favicon (`app/icon.svg`) — crimson→navy badge with "S" in yellow
- [x] Root OG image (`app/opengraph-image.tsx`, 1200×630, force-static)
- [x] Per-event OG image (`app/events/[id]/opengraph-image.tsx`) — event name, date, category badge, first highlight quote or topic

### Analytics
- [x] Matomo JS tracking (`MatomoScript`) with SPA route change support (`usePathname`)
- [x] Matomo noscript pixel (`MatomoNoscript`)
- [x] Config: `{ url: "//matomo.kohovolit.eu/", siteId: "2" }`

---

## Phase 2 — Speaker index

- [ ] `/speakers` — list of all identified speakers, sorted by appearance count
- [ ] `/speakers/[person_id]` — all events a speaker appeared in, with their excerpts
- Requires: aggregate across all summary JSONs at build time
- Note: `person_id` is `psp:person:NNN` (Popolo format) — can link to external PSP profile later

---

## Phase 3 — Search

- [ ] Client-side full-text search using [Pagefind](https://pagefind.app/) (preferred: build-time index, handles Czech diacritics) or Fuse.js for in-memory fuzzy
- Index: event name + topic + main_points + speaker names

---

## Phase 1 enhancements (backlog)

### Party affiliation on speaker chips
- [ ] Add party badge/icon next to speaker name on event detail and speaker chips
- Use **partyface** icon set (Czech political party logos, standardised) — `partyface` npm package or SVG sprites
- Data source: `sp.affiliation` already present in summary JSON; map affiliation string → party slug → partyface icon
- Show: small party icon + affiliation text in speaker chip; tooltip with full party name
- Apply on: event detail header chips, `HighlightCard` speaker line, `ControversyCard` speaker line, Phase 2 speaker pages

### Link to original PSP video
- [ ] Each event links to the original recording on `psp.cz` (or `mediasport.psp.cz`)
- PSP video archive URL pattern: `https://www.psp.cz/eknih/[term]/video/[video_id]` — needs mapping from event id to PSP video id (add `video_url` field to pipeline output or derive from `event.id`)
- **Timestamp deep-links**: highlights and controversial items already store `timestamp` (e.g. `41/00:01` = part 41 at 00:01). Map to video player seek parameter if PSP player supports it (investigate `#t=` or `?t=` format).
- **Access gating (optional):** timestamp-precise deep-links could be a paid/logged-in feature (see `plans/monetization.md` Tier 2–3); plain event-level links are free.

### Pagination by month
- [ ] As the event list grows, group events by month (e.g. "Květen 2026 (12)", "Duben 2026 (8)")
- Approach A (simpler): single page with month accordion/collapse — all events loaded, JS shows/hides by month group; category filter works across all months
- Approach B (static routes): `/events/2026-05`, `/events/2026-04` etc. — each a separate static page; category filter per page only
- **Recommendation:** Approach A first (no routing changes, just grouping in `EventsList.tsx`); switch to B if page weight becomes an issue (>500 events)
- Default open: current month + previous month; rest collapsed

### Cross-links to snemovna.datatimes.cz
- [ ] Speaker chips link to the matching MP profile on `snemovna.datatimes.cz/osoby/[person_id]` when `person_id` is a known PSP person ID (`psp:person:NNN`)
- [ ] Event category links to the matching section on snemovna (e.g. výbory → příslušný výbor)
- [ ] Footer / "Více dat o sněmovně" CTA pointing to `snemovna.datatimes.cz`

---

## Phase 4 — Social card export

- [x] HighlightCard and ControversyCard styled as ready-to-screenshot social cards
- [ ] "Sdílet" button / copy-to-clipboard / download-as-PNG shortcut

---

## Phase 5 — Social network publishing (semi-automatic)

**Goal:** share notable highlights and controversies to Bluesky and X automatically or with one-click approval.

### Approach
- **Semi-automatic (preferred):** pipeline flags new events; human reviews a draft post and hits "Publish" in a simple UI or replies to a notification
- **Fully automatic:** post immediately after summarization — risky for controversial content, skip for now

### Implementation options
| Option | Effort | Control |
|--------|--------|---------|
| Manual: copy card screenshot + draft text from site | Zero extra | Full |
| Approval queue: admin page lists drafts, one-click post | Medium | Full |
| Pipeline hook: `summarize.py` writes draft to queue file, cron checks for approval | Medium | Full |
| Zapier/Make automation on git push | Low | Limited |

### Content to post
- Per-event: event name + topic excerpt + link + OG image (auto-rendered)
- Per-highlight: quote card screenshot (HighlightCard) + speaker + event link
- Per-controversy: ControversyCard screenshot + event link

### Platforms
- **Bluesky:** AT Protocol API (`@atproto/api`) — image upload + post with facets for links
- **X (Twitter):** v2 API (`/2/tweets`) with media upload — requires Elevated access
- Post from `@datatimes_cz` (existing account)

### Prerequisites
- Bluesky app password for `datatimes_cz.bsky.social`
- X API key with write access
- Approval UI or workflow (could be a simple Next.js admin route behind basic auth, or a Telegram bot)

---

## Analytics: AI agent / bot tracking

Matomo JS **does not** track bots (no JS execution). Options:

| Approach | Effort | Catches AI bots |
|----------|--------|-----------------|
| Matomo "Track known bots" setting (Admin → Privacy) | Low | Partial (only those that fire the noscript pixel — rare) |
| **Cloudflare in front of GitHub Pages** | Medium | Yes — all crawlers visible at network level; use Workers to forward hits to `matomo.php` API |
| Vercel deployment (Stage 2) + Matomo Log Analytics | Medium | Yes — server logs include all UA strings |
| `robots.txt` allow GPTBot/ClaudeBot/PerplexityBot | Zero | No tracking, but increases AI indexing |

**Current state:** noscript pixel only. Cloudflare is the pragmatic path for GitHub Pages; Vercel deployment (Stage 2) gives server-side logs automatically.

---

## Open questions

- **Vercel timing?** GitHub Pages works for Phase 1–2. Move to Vercel when Pagefind is added (Phase 3) or when bot tracking becomes important.
- **Separate Matomo site ID?** Currently using siteId "2" (same as snemovna.datatimes.cz). Create a dedicated site in Matomo admin if separate stats are needed.
- **Summaries without highlights:** handled gracefully (section hidden if array empty).
- **Language:** site in Czech throughout.
