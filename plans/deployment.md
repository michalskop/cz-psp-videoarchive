# Deployment Plan — Sněmovna Digest

**Production URL:** `snemovna.datatimes.cz/digest`  
**Architecture:** Standalone Next.js static export in this repo (`web/`), deployed to Vercel,
proxied through the `legislature-dashboard` (snemovna.datatimes.cz) Next.js app.

---

## Stage 1 — GitHub Pages ✅ DONE (testing only)

Live at `https://michalskop.github.io/cz-psp-videoarchive/` — kept as smoke-test target.

- `web/next.config.ts` — env-controlled `basePath`/`assetPrefix` via `NEXT_PUBLIC_BASE_PATH`
- `.github/workflows/deploy.yml` — builds with repo-name basePath, deploys via Pages actions
- GitHub repo Settings → Pages: source = GitHub Actions

**Limitation:** GitHub Pages build runs on GitHub's servers, which don't have access to `summaries/json/` (data is local). Only works because the workflow copies summaries from the repo before building. Does not support auto-deploy from `pipeline.sh`.

---

## Stage 2 — Vercel production ✅ DONE

### How it works

1. **Data is local** — `summaries/json/*.json` exist only on the pipeline machine (committed to git, but Vercel's build environment doesn't have them when triggered from GitHub because of timing).
2. **Prebuilt deploy** — build runs locally where data is available, then the `.vercel/output/` artifact is pushed to Vercel.

### Vercel project setup

- **Project name:** `cz-psp-videoarchive` (`prj_4Wp0uSWHcB83D7hF0ekdgZflDh9N`)
- **Team:** `michalskops-projects` (`team_ztUFJehWnHDEkqMHTFC6vfPf`)
- **rootDirectory:** `null` (set via REST API — do NOT set to `web/` in dashboard, it causes double-path bug with prebuilt deploys)
- **SSO protection:** disabled (set via REST API)
- **`web/vercel.json`:** rewrites `/digest/:path*` → `/:path*` so static files are found at correct paths
- **`web/.vercelignore`:** excludes `node_modules`, `.next`, `out`, `coverage`

### Deploy command (run from `web/`)

```bash
NEXT_PUBLIC_BASE_PATH=/digest npx vercel build --prod
npx vercel deploy --prebuilt --prod --archive=tgz
```

Both steps run automatically from `pipeline.sh` whenever new summaries are committed (see below).

### Proxy setup in legislature-dashboard

`legislature-dashboard/apps/cz-psp/next.config.ts` — `rewrites()`:
```typescript
const DIGEST_ORIGIN = process.env.DIGEST_ORIGIN ?? "https://cz-psp-videoarchive-michalskops-projects.vercel.app";
// source: "/digest" and "/digest/:path*" → DIGEST_ORIGIN equivalents
```

The Vercel deployment URL (`cz-psp-videoarchive-michalskops-projects.vercel.app`) is the stable alias for the production deployment.

### Auto-deploy from pipeline

`pipeline.sh` step 6 — runs only when new summaries were committed:
```bash
cd "$DIR/web"
NEXT_PUBLIC_BASE_PATH=/digest npx vercel build --prod
npx vercel deploy --prebuilt --prod
cd "$DIR"
```

---

## Stage 3 — Vercel with Pagefind / MCP server (Phase 3+) ⬜

When full-text search (Pagefind) or a live MCP server is added:

- **Pagefind:** runs at build time, compatible with current static export + prebuilt deploy
- **MCP server tools:** require server-side execution (Vercel Functions / Fluid Compute). Switch from `output: "export"` to standard Next.js on Vercel. GitHub Pages fallback stops working for those routes. Consider Cloudflare Workers as an alternative to keep static export.

---

## Known issues / gotchas

| Issue | Root cause | Fix applied |
|-------|-----------|-------------|
| `rootDirectory: web` doubles path on prebuilt deploy | Vercel appends rootDirectory to CWD | Set rootDirectory=null via REST API |
| Build fails on Vercel GitHub integration | `summaries/json/` not available at Vercel build time | Use prebuilt deploy workflow |
| 401 on deployment URL | SSO protection enabled by default | Disabled via REST API |
| `next build` not accepted as custom build command | Vercel requires full command | Use `npm run build` |
| B2 images missing from html2canvas screenshots | B2 had no CORS rules | Run `set_b2_cors.py` once; CORS now configured |
