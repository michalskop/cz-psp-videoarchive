import type { Metadata } from "next";
import { getAllSummaries } from "@/lib/summaries";
import { EventsList } from "./EventsList";

export const metadata: Metadata = {
  title: "Archiv akcí",
  description: "Přehled všech zaznamenaných a shrnutých akcí Poslanecké sněmovny — semináře, konference, výbory, kulaté stoly.",
  openGraph: {
    title: "Archiv akcí | Sněmovna Digest",
    description: "Přehled všech zaznamenaných a shrnutých akcí Poslanecké sněmovny.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Archiv akcí | Sněmovna Digest",
  },
};

const CANONICAL = "https://snemovna.datatimes.cz/digest";

export default function EventsPage() {
  const summaries = getAllSummaries();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "Archiv akcí PSP",
    "description": "Přehled všech zaznamenaných a shrnutých akcí Poslanecké sněmovny",
    "url": `${CANONICAL}/events`,
    "numberOfItems": summaries.length,
  };

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <EventsList summaries={summaries} />
    </>
  );
}
