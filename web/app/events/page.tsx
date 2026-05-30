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

export default function EventsPage() {
  const summaries = getAllSummaries();
  return <EventsList summaries={summaries} />;
}
