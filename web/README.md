# Sněmovna Digest — web frontend

Next.js static-export app for browsing AI-structured summaries of Czech Parliament events.

**Live (testing):** `https://michalskop.github.io/cz-psp-videoarchive/`  
**Production (Stage 2):** `https://snemovna.datatimes.cz/digest`

## Development

```bash
cd web
npm install
npm run dev       # http://localhost:3000
npm run build     # static export → out/
```

Data is read at build time from `../summaries/json/*.json` (one level up).

## Build & deploy

GitHub Actions (`.github/workflows/deploy.yml`) triggers on push to `main` when
`web/**` or `summaries/json/**` change. It copies summary JSONs into
`web/public/summaries/`, builds with `NEXT_PUBLIC_BASE_PATH=/cz-psp-videoarchive`,
and deploys to GitHub Pages.

## Environment

| Variable | Purpose | GitHub Pages value |
|----------|---------|-------------------|
| `NEXT_PUBLIC_BASE_PATH` | URL prefix for all assets and links | `/cz-psp-videoarchive` |

For production (Stage 2 Vercel), set `NEXT_PUBLIC_BASE_PATH=/digest`.

## Design

Design system is documented in the parent project:
[legislature-dashboard/docs/design.md](https://github.com/michalskop/legislature-dashboard/blob/main/docs/design.md#sněmovna-digest-digest)

## Stack

- Next.js App Router, `output: "export"` (static)
- Tailwind CSS v4 with custom DataTimes palette (`app/globals.css`)
- Fonts: Roboto Slab + Work Sans (Google Fonts)
- OG images: `next/og` with `ImageResponse`, pre-rendered at build time
- Analytics: Matomo (`//matomo.kohovolit.eu/`, siteId 2)

## Key files

| Path | Purpose |
|------|---------|
| `app/layout.tsx` | Root layout, metadata, Matomo |
| `app/page.tsx` | Homepage (recent events) |
| `app/events/page.tsx` | Full event list (server component) |
| `app/events/EventsList.tsx` | Client component — category filter + month grouping |
| `app/events/[id]/page.tsx` | Event detail page |
| `app/components/PspLogotype.tsx` | Universal `Sněmovna.DataTimes.cz/digest` logotype |
| `app/components/HighlightCard.tsx` | Social-shareable highlight card |
| `app/components/ControversyCard.tsx` | Social-shareable controversy card |
| `app/components/RenderMd.tsx` | Minimal markdown renderer (bold + bullet lists) |
| `lib/summaries.ts` | Server-only data loader (`fs` → JSON) |
| `lib/types.ts` | Client-safe types and pure helpers |
