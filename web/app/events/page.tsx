import type { Metadata } from "next";
import { getAllSummaries } from "@/lib/summaries";
import { EventsList } from "./EventsList";

export const metadata: Metadata = {
  title: "Archiv akcí",
  description: "Přehled všech zaznamenaných a shrnutých akcí Poslanecké sněmovny.",
};

export default function EventsPage() {
  const summaries = getAllSummaries();
  return <EventsList summaries={summaries} />;
}
