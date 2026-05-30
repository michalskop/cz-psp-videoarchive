import type { MetadataRoute } from "next";
import { getAllSummaries } from "@/lib/summaries";

export const dynamic = "force-static";

const CANONICAL = "https://snemovna.datatimes.cz/digest";

export default function sitemap(): MetadataRoute.Sitemap {
  const summaries = getAllSummaries();
  const mostRecent = summaries.length > 0 ? new Date(summaries[0].created_at) : new Date();

  return [
    { url: CANONICAL, lastModified: mostRecent, changeFrequency: "daily", priority: 1.0 },
    { url: `${CANONICAL}/events`, lastModified: mostRecent, changeFrequency: "daily", priority: 0.9 },
    ...summaries.map((s) => ({
      url: `${CANONICAL}/events/${s.event.id}`,
      lastModified: new Date(s.created_at),
      changeFrequency: "monthly" as const,
      priority: 0.8,
    })),
  ];
}
