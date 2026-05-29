# Deployment Plan

**Production target:** `snemovna.datatimes.cz/digest`  
**Architecture:** Option B — standalone Next.js app in this repo (`web/`), separate from the datatimes turborepo. Shares design system via DESIGN.md; no shared npm packages initially.

---

## Stage 1 — GitHub Pages (testing) ✅ DONE

Live at `https://michalskop.github.io/cz-psp-videoarchive/`

### Setup
- [x] `web/next.config.ts` — env-controlled `basePath` and `assetPrefix` (`NEXT_PUBLIC_BASE_PATH`)
- [x] `output: "export"`, `images: { unoptimized: true }`
- [x] `.github/workflows/deploy.yml`:
  - Node 24, `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true`
  - Copies `summaries/json/*.json`, `summary.schema.json`, `SKILL.md` to `web/public/`
  - Builds with `NEXT_PUBLIC_BASE_PATH: /${{ github.event.repository.name }}`
  - Deploys via `actions/upload-pages-artifact@v3` + `actions/deploy-pages@v4`
- [x] GitHub repo Settings → Pages: source = GitHub Actions

### Known limitations on GitHub Pages
- No server-side rendering (static export only — already planned)
- No server-side request logs → bots/AI crawlers not tracked (see bot tracking section in `web-publication.md`)
- `robots.txt` and `llms.txt` use production canonical URLs, not the GitHub Pages URL
- B2 screenshot URLs work fine (absolute)

### Pipeline automation
- [x] `pipeline.sh` — full local pipeline: sync → transcribe → summarize → upload_screenshots → git push
- [x] `crontab.txt` — twice daily at 02:00 and 14:00

---

## Stage 2 — Vercel production ⬜ TODO

Move to `snemovna.datatimes.cz/digest` once Stage 1 is validated.

### This repo on Vercel
1. Create a new Vercel project pointing at this repo, root directory `web/`.
2. Set environment variable: `NEXT_PUBLIC_BASE_PATH=/digest`
3. Vercel project domain: assign a temporary Vercel URL (e.g. `psp-videoarchiv.vercel.app`) for initial smoke test.

### Rewrite on the snemovna project
In the datatimes turborepo, add a rewrite to the `snemovna` Vercel project config so `/videoarchiv/*` proxies to this repo's Vercel deployment:

```json
// vercel.json in the snemovna app
{
  "rewrites": [
    {
      "source": "/digest/:path*",
      "destination": "https://psp-videoarchiv.vercel.app/digest/:path*"
    }
  ]
}
```

### DNS / domain
No new DNS record needed — `snemovna.datatimes.cz` already resolves. The rewrite handles routing.

### Switch canonical URLs
Once the rewrite is live and tested, update GitHub Actions workflow:
- `NEXT_PUBLIC_BASE_PATH=/digest` (instead of repo-name value)
- `SKILL.md`, `llms.txt`, `.well-known/mcp-server-card.json`, `web/public/robots.txt` — already use production URL ✓

### Bot/AI tracking benefit
Vercel logs all HTTP requests server-side. Use Matomo Log Analytics against Vercel logs to track GPTBot, ClaudeBot, PerplexityBot, etc. by user-agent string.

---

## Stage 3 — Vercel with Pagefind / API routes (Phase 3+)

When full-text search (Pagefind) or MCP server tools are added:
- Pagefind: runs at build time, works fine on Vercel static export
- MCP server tools: require Vercel Edge Functions — switch from `output: 'export'` to standard Next.js SSR/Edge on Vercel; GitHub Pages will no longer work for those routes (static export of other pages still fine)

---

## Design system sharing with datatimes turborepo

For now: copy relevant tokens and components from the turborepo manually, guided by `DESIGN.md` in this repo.

Later option: publish the shared UI package from the datatimes turborepo to npm (private or public) and import here as a dependency. This removes the copy-paste step but adds a release workflow.
