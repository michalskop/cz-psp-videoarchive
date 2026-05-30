# /.well-known — digest-scoped only

Files here are served at `snemovna.datatimes.cz/digest/.well-known/` — a
**digest-scoped** path, not the root domain.

Root-domain discovery files (`snemovna.datatimes.cz/.well-known/`) live in
`legislature-dashboard/apps/cz-psp/public/.well-known/` and are maintained
there. Do NOT add root-domain discovery files (mcp/server-card.json,
api-catalog, oauth-*, etc.) here — they would be served at the wrong URL.

## Files here

| File | Served at | Notes |
|------|-----------|-------|
| `mcp-server-card.json` | `/digest/.well-known/mcp-server-card.json` | Legacy path, kept for backward compat. Canonical root path is `/.well-known/mcp/server-card.json` in legislature-dashboard. |
