"use client";

import { useEffect, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import Script from "next/script";

interface Props {
  url: string;
  siteId: string;
}

// Tracks page views on SPA route changes
function MatomoPageView({ url, siteId }: Props) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const initialized = useRef(false);

  useEffect(() => {
    // Skip the very first render — the inline init script already fired trackPageView
    if (!initialized.current) {
      initialized.current = true;
      return;
    }
    const w = window as Window & { _paq?: unknown[][] };
    if (!w._paq) return;
    const fullUrl = pathname + (searchParams.toString() ? `?${searchParams.toString()}` : "");
    w._paq.push(["setCustomUrl", fullUrl]);
    w._paq.push(["setDocumentTitle", document.title]);
    w._paq.push(["trackPageView"]);
  }, [pathname, searchParams, url, siteId]);

  return null;
}

export function MatomoScript({ url, siteId }: Props) {
  const trackerUrl = url.endsWith("/") ? url : `${url}/`;

  return (
    <>
      {/* Inline init — must run before the async matomo.js */}
      <Script id="matomo-init" strategy="afterInteractive">{`
        var _paq = window._paq = window._paq || [];
        _paq.push(['trackPageView']);
        _paq.push(['enableLinkTracking']);
        _paq.push(['setTrackerUrl', '${trackerUrl}matomo.php']);
        _paq.push(['setSiteId', '${siteId}']);
      `}</Script>
      <Script
        id="matomo-js"
        src={`${trackerUrl}matomo.js`}
        strategy="afterInteractive"
        async
      />
      <MatomoPageView url={url} siteId={siteId} />
    </>
  );
}

/** Noscript pixel — fallback for browsers/bots without JS */
export function MatomoNoscript({ url, siteId }: Props) {
  const trackerUrl = url.endsWith("/") ? url : `${url}/`;
  return (
    <noscript>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`${trackerUrl}matomo.php?idsite=${siteId}&rec=1`}
        style={{ border: 0 }}
        alt=""
      />
    </noscript>
  );
}
