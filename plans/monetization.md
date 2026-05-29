# Monetization Plan — PSP Video Archive

**Principle:** Start with zero infrastructure overhead; add complexity only when demand justifies it.  
**Audience:** journalists, researchers, NGOs, political analysts, media organizations, general public.

---

## Tier 1 — Simple (no extra infrastructure)

### Donation / support link
- Add a "Podpořte projekt" link in `SiteFooter` → Ko-fi, GitHub Sponsors, or bank transfer
- One sentence: "Přepisy a souhrny vznikají automatizovaně — pomoci s provozem můžete zde."
- Effort: 30 min

### DataTimes brand / attribution
- Site is already branded as Sněmovna.DataTimes.cz — strengthens the DataTimes brand
- Indirect value: brand recognition → consulting leads, media partnerships, grant applications

### Grant funding
- Czech journalistic grants: Nadace OSF, fond investigativní žurnalistiky
- EU: Journalism Trust Initiative, Media Freedom Rapid Response
- NGO / civic tech: NKB grants, CEE civic tech funds
- The automated pipeline + open data angle is fundable

---

## Tier 2 — Moderate effort

### Newsletter / mailing list
- Weekly digest of new summaries (top events by category, notable quotes)
- Substack or Buttondown — free tier sufficient at first
- Monetization: paid tier for full archive access, early summaries, or topic filters
- Effort: ~1 week to set up + content workflow

### Video timestamp deep-links (freemium feature)
- Event-level links to PSP video archive: **free** (plain URL, anyone can follow)
- **Timestamp-precise deep-links** (jump to exact moment in the recording): **paid / logged-in only**
  - High value for journalists and researchers who want to verify a quote directly
  - Implementation: show a blurred/locked timestamp link for anonymous users; unlock on subscription or one-time payment
  - Requires auth layer (Stage 2 / Vercel — not possible on static GitHub Pages)

### API access (data licensing)
- Expose `summaries/json/` as a paid data feed for:
  - Media organizations needing structured parliament data
  - Academic research
  - Political monitoring tools
- Simple approach: GitHub releases with versioned JSON archives, sold via Gumroad or direct invoice
- Advanced: rate-limited REST API (Vercel Edge Functions + API key check) — Phase 3+

### Embedded widgets / white-label
- Offer embeddable highlight cards for media websites (iFrame or Web Component)
- Licensing fee per publication, or "powered by DataTimes" free tier

---

## Tier 3 — Advanced (requires real infrastructure)

### Subscription SaaS
- Dashboard for political analysts / PR agencies: search, alerts, export
- Features behind paywall: full-text search (Phase 3), speaker tracking (Phase 2), keyword alerts
- Stack: Vercel + Stripe + Supabase (auth + subscriptions)
- Target price: 500–2 000 Kč/month per organization

### Custom summaries on demand
- User submits a PSP video URL → pipeline runs → summary delivered by email in 24 h
- Price: 200–500 Kč per summary
- Implementation: queue (BullMQ or simple cron), payment via Stripe

### Consulting / bespoke data products
- One-off data analysis for media, NGOs, political parties
- Uses the pipeline as the backbone; billed hourly or per project

---

## Prioritized next step

**Tier 1 first:** add a Ko-fi / GitHub Sponsors link to the footer — zero overhead, signals the project is supported by users. Then apply for one grant (OSF / investigativní žurnalistika) with the site as the portfolio piece.
