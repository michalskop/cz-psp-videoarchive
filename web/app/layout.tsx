import type { Metadata } from "next";
import { Suspense } from "react";
import "./globals.css";
import { SiteHeader } from "./components/SiteHeader";
import { SiteFooter } from "./components/SiteFooter";
import { MatomoScript, MatomoNoscript } from "./components/MatomoScript";

const BASE_URL = "https://snemovna.datatimes.cz";
const MATOMO = { url: "//matomo.kohovolit.eu/", siteId: "2" };

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: {
    default: "PSP Video Archive | Sněmovna.DataTimes.cz",
    template: "%s | PSP Video Archive",
  },
  description:
    "Strukturované souhrny akcí Poslanecké sněmovny ČR — semináře, konference, výbory. Přepisy a souhrny zpracovány pomocí AI.",
  icons: { icon: "/videoarchiv/icon.svg" },
  openGraph: {
    siteName: "Sněmovna.DataTimes.cz/videoarchiv",
    locale: "cs_CZ",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    site: "@datatimes_cz",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="cs" className="h-full">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@400;500;600;700&family=Work+Sans:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col bg-surface-1 text-foreground font-slab antialiased">
        <MatomoNoscript {...MATOMO} />
        <SiteHeader />
        <main className="flex-1">{children}</main>
        <SiteFooter />
        <Suspense>
          <MatomoScript {...MATOMO} />
        </Suspense>
      </body>
    </html>
  );
}
