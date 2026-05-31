"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";

// Pagefind is a static asset generated at build time — not a bundled module.
// webpackIgnore tells the bundler to skip it and let the browser resolve it at runtime.
const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const LOAD_TIMEOUT = 10;

interface PFResult {
  url: string;
  meta: { title?: string };
  excerpt: string;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PFResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [ready, setReady] = useState(false);
  const [countdown, setCountdown] = useState(LOAD_TIMEOUT);
  const [timedOut, setTimedOut] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const pf = useRef<any>(null);

  useEffect(() => {
    const load = async () => {
      try {
        // Construct an absolute URL using the page's own origin so pagefind.js
        // loads same-origin. Without this, the import() in a cross-origin classic
        // script resolves against the script's CDN origin, making the pagefind
        // WebWorker cross-origin — which browsers block.
        const origin = window.location.origin;
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        pf.current = await import(/* webpackIgnore: true */ `${origin}${BASE}/pagefind/pagefind.js`);
        await pf.current.init();
        setReady(true);
      } catch {
        setTimedOut(true);
      }
    };
    load();
  }, []);

  // Countdown while loading, stops when ready or timed out
  useEffect(() => {
    if (ready || timedOut) return;
    if (countdown <= 0) {
      setTimedOut(true);
      return;
    }
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown, ready, timedOut]);

  const runSearch = useCallback(async (q: string) => {
    if (!pf.current || !q.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const result = await pf.current.search(q);
      const data: PFResult[] = await Promise.all(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        result.results.slice(0, 15).map((r: any) => r.data())
      );
      setResults(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => runSearch(query), 250);
    return () => clearTimeout(timer);
  }, [query, runSearch]);

  return (
    <main className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="font-slab font-bold text-2xl text-navy-9 mb-6">Hledat v archivu</h1>

      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={ready ? "Hledat v souhrnnech akcí PSP…" : "Načítání…"}
        disabled={!ready}
        className="w-full font-sans text-base border border-border rounded-lg px-4 py-2.5 mb-4 focus:outline-none focus:ring-2 focus:ring-teal-6 bg-surface-0 text-foreground placeholder:text-muted-foreground disabled:opacity-50"
        autoFocus
      />

      {!ready && !timedOut && (
        <p className="font-sans text-sm text-muted-foreground">
          Načítání vyhledávání… {countdown}
        </p>
      )}

      {timedOut && !ready && (
        <p className="font-sans text-sm text-muted-foreground">
          Vyhledávání není k dispozici.
        </p>
      )}

      {ready && loading && (
        <p className="font-sans text-sm text-muted-foreground">Hledám…</p>
      )}

      {ready && !loading && query.trim() && results.length === 0 && (
        <p className="font-sans text-sm text-muted-foreground">
          Žádné výsledky pro „{query}"
        </p>
      )}

      <div className="flex flex-col gap-3 mt-2">
        {results.map((r) => (
          <Link
            key={r.url}
            href={r.url}
            className="block p-4 rounded-lg border border-border hover:border-teal-6 hover:shadow-md transition-all bg-surface-0"
          >
            <h2 className="font-slab font-semibold text-navy-9 mb-1.5 leading-snug">
              {r.meta.title ?? "Akce"}
            </h2>
            <p
              className="font-sans text-sm text-foreground leading-relaxed search-excerpt"
              dangerouslySetInnerHTML={{ __html: r.excerpt }}
            />
          </Link>
        ))}
      </div>
    </main>
  );
}
