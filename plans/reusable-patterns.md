# Reusable Patterns — DataTimes Sites

Extracted from the Sněmovna Digest build. Each pattern is generic enough to apply to other Next.js static sites in this family (snemovna.datatimes.cz, datatimes.cz, kohovolit.eu).

---

## Pattern 1 — Agent-Ready Static Site

Make any static Next.js site discoverable by AI agents. Implementation order matters — earlier items give most bang per hour.

### Checklist (copy per project)

| File | Path | Content | Time |
|------|------|---------|------|
| `robots.txt` | `web/public/robots.txt` | Explicit allow for GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot, anthropic-ai | 5 min |
| `llms.txt` | `web/public/llms.txt` | Structured cheat sheet: what the site is, key routes, data format, language | 20 min |
| `SKILL.md` | `web/public/SKILL.md` | Full capability reference: schema, example queries, contact | 30 min |
| `auth.md` | `public/.well-known/auth.md` (root domain) | "No auth required" declaration listing all public endpoints | 10 min |
| `sitemap.xml` | `web/app/sitemap.ts` | Build-time from data; `export const dynamic = "force-static"` required | 30 min |
| JSON-LD | Every page component | `<script type="application/ld+json" dangerouslySetInnerHTML>` | 1–2 h |
| `/.well-known/mcp/server-card.json` | Root domain `public/` | SEP-1649 format; `serverInfo.name` nested (not top-level `name`) | 20 min |
| `/.well-known/api-catalog` | Root domain `public/` | RFC 9727 `application/linkset+json` listing machine-readable endpoints | 20 min |
| `/api/events.json` (or equivalent) | `web/app/api/events.json/route.ts` | Static array of all records; `force-static` required | 30 min |
| WebMCP | `web/app/components/WebMCP.tsx` | `navigator.modelContext.provideContext()` — graceful no-op if absent | 30 min |

**Score target:** ~67% on isitagentready.com with all above. Ceiling without infra changes:
- **DNS-AID** — blocked until DNS provider supports HTTPS/SVCB record types (draft-mozleywilliams-dnsop-dnsaid). Not available at most registrars yet.
- **OAuth/OIDC** — not applicable for public read-only sites. `/auth.md` covers it.

### Root-domain vs subdirectory — ownership

When a single domain hosts multiple apps (e.g. `snemovna.datatimes.cz` with `/digest` from one repo and `/` from another):

- **Root-domain files** (`/.well-known/`, `/auth.md`, `/robots.txt`, `/llms.txt`) — live in the **root app** repo (e.g. `legislature-dashboard/apps/cz-psp/public/`)
- **Subdirectory files** (`/digest/.well-known/`, `/digest/llms.txt`) — live in the **sub-app** repo (e.g. `web/public/`)
- Add `_source` field to each JSON file and `README.md` to each `.well-known/` dir explaining ownership; prevents accidental overwrites

### JSON-LD types by page type

| Page | Schema types | Key fields |
|------|-------------|-----------|
| Homepage / dataset | `["WebSite", "Dataset"]` | `inLanguage`, `license`, `temporalCoverage`, `about` |
| List / archive | `CollectionPage` | `numberOfItems`, `url` |
| Event detail | `["Event", "Article"]` | `startDate`, `eventStatus`, `performer`, `isBasedOn` |
| Person / speaker | `Person` | `identifier`, `memberOf`, `url` |
| Blog post | `Article` | `datePublished`, `author`, `headline` |

### MCP Server Card (SEP-1649) template

```json
{
  "serverInfo": {
    "name": "Your Site Name",
    "version": "1.0.0",
    "description": "One sentence for AI agents."
  },
  "transport": null,
  "capabilities": {
    "tools": ["list_events", "get_event_summary"]
  },
  "auth": { "type": "none" },
  "contact": { "url": "https://your-site.example.com" },
  "humanUrl": "https://your-site.example.com"
}
```
`transport: null` until a live MCP server exists. Update to `{ "type": "http", "url": "..." }` when live.

### WebMCP component (copy-paste)

```tsx
"use client";
import { useEffect } from "react";

const CANONICAL = "https://your-site.example.com";
type AnyObj = Record<string, unknown>;

export function WebMCP() {
  useEffect(() => {
    if (typeof navigator === "undefined") return;
    const ctx = (navigator as unknown as AnyObj & { modelContext?: AnyObj }).modelContext;
    if (typeof ctx?.provideContext !== "function") return;

    (ctx.provideContext as (opts: AnyObj) => void)({
      tools: [
        {
          name: "list_items",
          description: "List all items from the site.",
          inputSchema: { type: "object", properties: { limit: { type: "number" } } },
          execute: async ({ limit = 20 }: { limit?: number }) => {
            const res = await fetch(`${CANONICAL}/api/items.json`);
            if (!res.ok) return { error: "Could not load items" };
            const items = await res.json() as AnyObj[];
            return items.slice(0, Math.min(limit, 100));
          },
        },
      ],
    });
  }, []);
  return null;
}
```
Add `<WebMCP />` to `app/layout.tsx` before `</body>`.  
TypeScript requires double cast (`as unknown as`) — there is no type for `navigator.modelContext`.

---

## Pattern 2 — Prebuilt Vercel Deploy for Data-Local Static Sites

**Problem:** Build-time data (`summaries/json/`, CSV files, etc.) exists only on the pipeline machine. Vercel's GitHub integration builds on Vercel's servers which don't have the data.

**Solution:** Build locally, ship the artifact.

### Setup (one-time)

```bash
# Link project (run from the web/ directory)
cd web
npx vercel link

# Set rootDirectory to null — critical for prebuilt deploys
# If set to web/ in the dashboard, prebuilt paths are doubled (web/web/...)
curl -X PATCH "https://api.vercel.com/v9/projects/YOUR_PROJECT_ID" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rootDirectory": null}'

# Disable SSO protection (for public sites)
curl -X PATCH "https://api.vercel.com/v9/projects/YOUR_PROJECT_ID" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ssoProtection": null}'
```

### Deploy command (run from `web/`)

```bash
NEXT_PUBLIC_BASE_PATH=/your-path npx vercel build --prod
npx vercel deploy --prebuilt --prod
```

If your site is at the root (no basePath), omit `NEXT_PUBLIC_BASE_PATH`.

### `web/vercel.json` — rewrite for subdirectory deploy

```json
{
  "rewrites": [
    { "source": "/your-path/:path*", "destination": "/:path*" }
  ]
}
```

### `web/.vercelignore`

```
node_modules
.next
out
coverage
```

### Pipeline auto-deploy (add to your cron script)

```bash
# Only runs when new data was committed (saves build minutes)
if ! git diff --cached --quiet; then
    git commit -m "Auto: new data $(date '+%Y-%m-%d')"
    git push

    cd "$DIR/web"
    NEXT_PUBLIC_BASE_PATH=/your-path npx vercel build --prod
    npx vercel deploy --prebuilt --prod
    cd "$DIR"
fi
```

### Proxy setup in parent app (`legislature-dashboard` pattern)

```typescript
// next.config.ts
const CHILD_ORIGIN = process.env.CHILD_ORIGIN ?? "https://your-vercel-deployment.vercel.app";
async rewrites() {
  return [
    { source: "/your-path", destination: `${CHILD_ORIGIN}/your-path` },
    { source: "/your-path/:path*", destination: `${CHILD_ORIGIN}/your-path/:path*` },
  ];
}
```

### Known gotchas

| Issue | Root cause | Fix |
|-------|-----------|-----|
| Double-path `web/web/` | `rootDirectory: web` + prebuilt deploy from `web/` | Set rootDirectory=null via REST API |
| 401 on deployment URL | SSO protection enabled by default | Disable via REST API |
| `next build` not accepted | Vercel needs full command | Use `npm run build` |
| Static export route handler error | Missing `export const dynamic = "force-static"` | Add to every route.ts and sitemap.ts |

---

## Pattern 3 — Social Card Export with Remote Images

Export styled DOM cards (highlights, quotes, data cards) as PNG for social sharing, even when images come from a CORS-restricted CDN (B2, S3, Cloudflare).

### Problem

`html2canvas` taints the canvas if cross-origin images load without CORS headers. `useCORS: true` only helps if the server sends `Access-Control-Allow-Origin`. B2 / S3 buckets send no CORS headers by default.

### Solution — two steps

**Step 1: Enable CORS on B2 bucket** (one-time, see `set_b2_cors.py`):
```python
# Key fields in b2_update_bucket payload:
"corsRules": [{
    "corsRuleName": "allowPublicGet",
    "allowedOrigins": ["*"],
    "allowedOperations": ["b2_download_file_by_id", "b2_download_file_by_name"],
    "allowedHeaders": ["*"],
    "exposeHeaders": [],
    "maxAgeSeconds": 3600
}]
```
Verify: `curl -sI -H "Origin: https://your-site.example.com" https://your-b2-url | grep access-control`

**Step 2: Pre-fetch images as blob URLs before capture**:
```typescript
async function prefetchImages(el: HTMLElement): Promise<Map<string, string>> {
  const imgs = Array.from(el.querySelectorAll<HTMLImageElement>("img[src]"));
  const pairs = await Promise.all(
    imgs.map(async (img) => {
      try {
        const res = await fetch(img.src, { mode: "cors" });
        const blob = await res.blob();
        return [img.src, URL.createObjectURL(blob)] as [string, string];
      } catch {
        return [img.src, img.src] as [string, string];
      }
    })
  );
  return new Map(pairs);
}

// In your capture function:
const blobMap = await prefetchImages(el);
blobMap.forEach((blobUrl, orig) => {
  el.querySelectorAll<HTMLImageElement>(`img[src="${orig}"]`)
    .forEach(img => { img.src = blobUrl; });
});
await html2canvas(el, { useCORS: false, allowTaint: false });
blobMap.forEach((url) => URL.revokeObjectURL(url));
```

### Layout — prevent transparent right strip

```tsx
// WRONG: w-fit alone is overridden by align-self: stretch in flex-col parent
<div ref={cardRef} className="w-fit">

// CORRECT: self-start opts out of stretch
<div ref={cardRef} className="w-fit self-start">
```

### Badge text sitting low

When badge has `py-1` padding, default line-height pushes text down:
```tsx
// Add leading-none to the span:
<span className="px-2.5 py-1 leading-none">BADGE</span>
```

---

## Pattern 4 — Git Config in Automation Contexts

**Problem:** Cron jobs, Bash tool in Claude Code, and CI environments often run without `HOME` set (or with a root home that has no `.gitconfig`). `git commit` picks up the wrong author or fails.

**Always set local config per repo:**
```bash
git -C /path/to/repo config user.name "Your Name"
git -C /path/to/repo config user.email "your@email.example.com"
```

Add this to your repo setup docs and to the README for any automated pipeline.

**To fix already-pushed commits with wrong author:**
```bash
git rebase HEAD~N --exec 'git commit --amend --reset-author --no-edit'
git push --force-with-lease
```

---

## Pattern 5 — Static API Endpoints in Next.js Static Export

Route handlers work in `output: "export"` mode with one required addition:

```typescript
// web/app/api/items.json/route.ts
import { NextResponse } from "next/server";
export const dynamic = "force-static"; // required — without this, build fails

export function GET() {
  const data = loadYourData();
  return NextResponse.json(data);
}
```

The file `app/api/items.json/route.ts` maps to `/api/items.json` at the served path.  
Same pattern applies to `app/sitemap.ts` — add `export const dynamic = "force-static"`.

---

## Validation & Submission Checklist (per site, per deploy)

- [ ] isitagentready.com — target >65%
- [ ] validator.schema.org — paste each JSON-LD block
- [ ] Submit sitemap to Google Search Console
- [ ] Submit sitemap to Bing Webmaster Tools
- [ ] `curl` check: `robots.txt`, `llms.txt`, `auth.md`, `/.well-known/mcp/server-card.json`, `/api/items.json` all return 200
- [ ] `curl -sI -H "Origin: ..." <B2 URL>` shows `access-control-allow-origin: *`
- [ ] PNG card export: copy and download both work; no transparent strip; badge text not low

---

## What Lives Where (multi-app domain summary)

```
snemovna.datatimes.cz/         ← legislature-dashboard/apps/cz-psp/public/
  robots.txt
  llms.txt
  auth.md
  .well-known/
    mcp/server-card.json        ← SEP-1649 (new canonical)
    api-catalog                 ← RFC 9727

snemovna.datatimes.cz/digest/  ← web/public/ and web/app/
  robots.txt                   ← web/public/robots.txt (if digest has its own)
  llms.txt                     ← web/public/llms.txt
  SKILL.md                     ← web/public/SKILL.md
  sitemap.xml                  ← web/app/sitemap.ts (build-time)
  api/events.json              ← web/app/api/events.json/route.ts (build-time)
  .well-known/
    mcp-server-card.json        ← backward-compat copy only
    README.md                   ← ownership map, DO NOT overwrite root files
```

Add `README.md` to each `.well-known/` with the ownership table above.  
Add `_source` string field to any JSON file that might be duplicated across repos.
