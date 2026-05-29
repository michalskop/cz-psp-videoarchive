# Deployment Plan

**Production target:** `snemovna.datatimes.cz/videoarchiv`  
**Architecture:** Option B — standalone Next.js app in this repo (`web/`), separate from the datatimes turborepo. Shares design system via DESIGN.md; no shared npm packages initially.

---

## Stage 1 — GitHub Pages (testing)

For development validation before production wiring.

### Setup
1. In `web/next.config.js`, use env-controlled `basePath` and `assetPrefix`:
   ```js
   const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
   module.exports = {
     output: 'export',
     basePath,
     assetPrefix: basePath,
     images: { unoptimized: true }, // required for static export
   };
   ```
2. Add GitHub Actions workflow `.github/workflows/deploy.yml`:
   ```yaml
   name: Deploy to GitHub Pages
   on:
     push:
       branches: [main]
       paths: ['web/**', 'summaries/json/**']
   jobs:
     build-deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-node@v4
           with: { node-version: '20' }
         - run: cd web && npm ci && npm run build
           env:
             NEXT_PUBLIC_BASE_PATH: /${{ github.event.repository.name }}
         - uses: actions/deploy-pages@v4
   ```
3. In GitHub repo Settings → Pages: source = GitHub Actions.
4. Testing URL: `https://[username].github.io/[repo-name]/`

### Limitations on GitHub Pages
- No server-side rendering (static export only — already planned)
- `robots.txt` and `llms.txt` use production URLs (canonical), not the GitHub Pages URL
- B2 screenshots work fine (absolute URLs in JSON)
- `basePath` must match the repo name exactly

---

## Stage 2 — Vercel production

Move to `snemovna.datatimes.cz/videoarchiv` once Stage 1 is validated.

### This repo on Vercel
1. Create a new Vercel project pointing at this repo, root directory `web/`.
2. Set environment variable: `NEXT_PUBLIC_BASE_PATH=/videoarchiv`
3. Vercel project domain: assign a temporary Vercel URL (e.g. `psp-videoarchiv.vercel.app`) for initial smoke test.

### Rewrite on the snemovna project
In the datatimes turborepo, add a rewrite to the `snemovna` Vercel project config so `/videoarchiv/*` proxies to this repo's Vercel deployment:

```json
// vercel.json in the snemovna app
{
  "rewrites": [
    {
      "source": "/videoarchiv/:path*",
      "destination": "https://psp-videoarchiv.vercel.app/videoarchiv/:path*"
    }
  ]
}
```

This keeps `snemovna.datatimes.cz/videoarchiv` as the canonical URL while the two apps are deployed independently.

### DNS / domain
No new DNS record needed — `snemovna.datatimes.cz` already resolves. The rewrite handles routing.

### Switch canonical URLs
Once the rewrite is live and tested:
- `SKILL.md` — already uses production URL ✓
- `llms.txt` — already uses production URL ✓  
- `.well-known/mcp-server-card.json` — already uses production URL ✓
- `web/public/robots.txt` sitemap URL — already uses production URL ✓

GitHub Actions workflow: set `NEXT_PUBLIC_BASE_PATH=/videoarchiv` instead of the repo-name value.

---

## Stage 3 — Vercel with Pagefind / API routes (Phase 3+)

When full-text search (Pagefind) or MCP server tools are added:
- Pagefind: runs at build time, works fine on Vercel static export
- MCP server tools: require Vercel Edge Functions — switch from `output: 'export'` to standard Next.js SSR/Edge on Vercel; GitHub Pages will no longer work for those routes (static export of other pages still fine)

---

## Design system sharing with datatimes turborepo

For now: copy relevant tokens and components from the turborepo manually, guided by `DESIGN.md` in this repo.

Later option: publish the shared UI package from the datatimes turborepo to npm (private or public) and import here as a dependency. This removes the copy-paste step but adds a release workflow.
